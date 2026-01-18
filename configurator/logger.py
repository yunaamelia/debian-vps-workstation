"""
Parallel-safe logging manager.

Uses QueueHandler + QueueListener pattern to prevent log interleaving
in multi-threaded/multi-process environments.
"""

import atexit
import logging
import logging.handlers
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from rich.console import Console
from rich.logging import RichHandler

# Default log directory
LOG_DIR = Path("/var/log/debian-vps-configurator")
LOG_FILE = LOG_DIR / "install.log"


class ParallelLogManager:
    """
    Manages logging for parallel module execution.

    Architecture:
    - Each worker gets a QueueHandler
    - Single QueueListener processes all logs sequentially
    - Optional: Per-module file handlers for isolated logs
    """

    def __init__(
        self,
        base_log_dir: Path = LOG_DIR,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        enable_per_module_logs: bool = True,
    ):
        self.base_log_dir = base_log_dir
        self.console_level = console_level
        self.file_level = file_level
        self.enable_per_module_logs = enable_per_module_logs

        # Create log directory
        try:
            self.base_log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback
            self.base_log_dir = Path.home() / ".debian-vps-configurator"
            self.base_log_dir.mkdir(parents=True, exist_ok=True)

        # Shared queue for all workers
        self.log_queue = queue.Queue(-1)  # Unbounded queue

        # Handlers that will process queued records
        self.handlers: List[logging.Handler] = []

        # QueueListener (starts in background thread)
        self.listener: Optional[logging.handlers.QueueListener] = None

        # Per-module loggers
        self.module_loggers: Dict[str, logging.Logger] = {}

        self._setup_handlers()

    def _setup_handlers(self):
        """Create output handlers (console + files)."""
        # 1. Console handler (Rich)
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=False,
            show_path=False,
            rich_tracebacks=True,
            markup=False,
        )
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        self.handlers.append(console_handler)

        # 2. Main log file (all modules)
        main_log_file = self.base_log_dir / "install.log"
        file_handler = logging.FileHandler(main_log_file, encoding="utf-8")
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self.handlers.append(file_handler)

    def start(self):
        """Start the queue listener."""
        if not self.listener:
            self.listener = logging.handlers.QueueListener(
                self.log_queue, *self.handlers, respect_handler_level=True
            )
            self.listener.start()

    def stop(self):
        """Stop the queue listener and flush logs."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def get_logger(self, module_name: str) -> logging.Logger:
        """
        Get a logger for a specific module.

        Args:
            module_name: Name of the module (e.g., 'docker', 'python')

        Returns:
            Logger configured with QueueHandler
        """
        if module_name in self.module_loggers:
            return self.module_loggers[module_name]

        # Create logger
        logger = logging.getLogger(f"configurator.modules.{module_name}")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Clear any existing handlers
        logger.handlers.clear()

        # Add QueueHandler (sends to shared queue)
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        logger.addHandler(queue_handler)

        # Optional: Add per-module file handler
        if self.enable_per_module_logs:
            module_log_file = self.base_log_dir / f"{module_name}.log"
            module_file_handler = logging.FileHandler(module_log_file, encoding="utf-8")
            module_file_handler.setLevel(logging.DEBUG)
            module_file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(module_file_handler)

        self.module_loggers[module_name] = logger
        return logger

    def set_console_level(self, level: int):
        """
        Dynamically change console log level.

        Args:
            level: logging.DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        for handler in self.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(level)
                break


# Global instance (singleton pattern)
_log_manager: Optional[ParallelLogManager] = None


def get_log_manager(**kwargs) -> ParallelLogManager:
    """Get or create the global log manager."""
    global _log_manager
    if _log_manager is None:
        _log_manager = ParallelLogManager(**kwargs)
        _log_manager.start()
    return _log_manager


def shutdown_log_manager():
    """Shutdown the global log manager."""
    global _log_manager
    if _log_manager:
        _log_manager.stop()
        _log_manager = None


# Register cleanup
atexit.register(shutdown_log_manager)


class DynamicLogger:
    """
    Wrapper for logging.Logger with dynamic level control.

    Allows changing log levels at runtime by communicating with the LogManager.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def set_console_level(self, level: int):
        """
        Dynamically change console output verbosity.

        Args:
            level: logging.DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        get_log_manager().set_console_level(level)

    def enable_verbose(self):
        """Quick enable: DEBUG level on console."""
        self.set_console_level(logging.DEBUG)

    def enable_quiet(self):
        """Quick enable: ERROR level on console."""
        self.set_console_level(logging.ERROR)

    def enable_normal(self):
        """Quick enable: INFO level on console."""
        self.set_console_level(logging.INFO)

    def get_console_level(self) -> int:
        """Get current console log level."""
        # accessing manager directly as handlers are not on the logger proxy
        manager = get_log_manager()
        for handler in manager.handlers:
            if isinstance(handler, RichHandler):
                return handler.level
        return logging.INFO

    # Proxy methods to underlying logger
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        self._logger.log(level, msg, *args, **kwargs)

    def __getattr__(self, name):
        """Delegate other attributes to the underlying logger."""
        return getattr(self._logger, name)


def setup_logger(
    name: str = "configurator",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False,
) -> Union[logging.Logger, DynamicLogger]:
    """
    Legacy setup_logger wrapper around ParallelLogManager.
    Returns a DynamicLogger.
    """
    console_level = logging.DEBUG if verbose else (logging.ERROR if quiet else logging.INFO)

    # Get manager (singleton)
    manager = get_log_manager(console_level=console_level)

    # Return a logger that writes to the queue
    logger = manager.get_logger(name)

    # Wrap in DynamicLogger
    return DynamicLogger(logger)


class LogContext:
    """
    Context manager for logging operations with start/end messages.
    """

    def __init__(
        self,
        logger: Union[logging.Logger, DynamicLogger],
        operation: str,
        show_time: bool = True,
    ):
        self.logger = logger
        self.operation = operation
        self.show_time = show_time
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> "LogContext":
        self.start_time = datetime.now()
        self.logger.info(f"▶ {self.operation}...")
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> Literal[False]:
        if self.start_time and self.show_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = f" ({elapsed.total_seconds():.1f}s)"
        else:
            elapsed_str = ""

        if exc_type is None:
            self.logger.info(f"✓ {self.operation} complete{elapsed_str}")
        else:
            self.logger.error(f"✗ {self.operation} failed{elapsed_str}")

        return False
