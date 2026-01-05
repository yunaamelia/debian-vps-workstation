"""
Logging system for the configurator.

Provides structured logging with:
- Console output (colorized with Rich)
- File output (detailed logs)
- Different log levels for different audiences
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from rich.console import Console
from rich.logging import RichHandler

# Default log directory
LOG_DIR = Path("/var/log/debian-vps-configurator")
LOG_FILE = LOG_DIR / "install.log"


def setup_logger(
    name: str = "configurator",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False,
) -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name
        log_file: Path to log file (default: /var/log/debian-vps-configurator/install.log)
        verbose: Enable debug output to console
        quiet: Suppress all but error messages to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set base level (file gets everything, console is filtered)
    logger.setLevel(logging.DEBUG)

    # Console handler with Rich
    console_level = logging.DEBUG if verbose else (logging.ERROR if quiet else logging.INFO)
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        markup=True,
    )
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    # File handler
    log_path = log_file or LOG_FILE
    try:
        # Create log directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    except PermissionError:
        # Fall back to user's home directory if we can't write to /var/log
        fallback_path = Path.home() / ".debian-vps-configurator" / "install.log"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(fallback_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

        logger.debug(f"Using fallback log location: {fallback_path}")

    return logger


def get_logger(name: str = "configurator") -> logging.Logger:
    """
    Get an existing logger or create a new one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set up with defaults
    if not logger.handlers:
        return setup_logger(name)

    return logger


class LogContext:
    """
    Context manager for logging operations with start/end messages.

    Usage:
        with LogContext(logger, "Installing Docker"):
            # ... installation code ...
    """

    def __init__(
        self,
        logger: logging.Logger,
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

        # Don't suppress exceptions
        return False
