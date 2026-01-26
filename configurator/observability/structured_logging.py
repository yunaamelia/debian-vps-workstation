"""
Structured logging for VPS Configurator.

Provides JSON-formatted logs with correlation IDs and rich context.
"""

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Thread-safe context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class StructuredLogger:
    """
    Logger that outputs structured JSON logs.

    Features:
    - JSON formatted output
    - Correlation ID support
    - Automatic context enrichment
    - Multiple output handlers
    """

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
    ) -> None:
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
            level: Logging level
            log_file: Optional file path for logging
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.name = name

        # Add JSON formatter
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)

    def _build_log_dict(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        """Build structured log dictionary."""
        log_dict: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
            "message": message,
            "correlation_id": correlation_id.get(),
        }

        # Add extra fields
        if kwargs:
            log_dict["extra"] = kwargs

        return log_dict

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        log_dict = self._build_log_dict(message, **kwargs)
        log_dict["level"] = "DEBUG"
        self.logger.debug(json.dumps(log_dict))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        log_dict = self._build_log_dict(message, **kwargs)
        log_dict["level"] = "INFO"
        self.logger.info(json.dumps(log_dict))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        log_dict = self._build_log_dict(message, **kwargs)
        log_dict["level"] = "WARNING"
        self.logger.warning(json.dumps(log_dict))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        log_dict = self._build_log_dict(message, **kwargs)
        log_dict["level"] = "ERROR"
        self.logger.error(json.dumps(log_dict))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        log_dict = self._build_log_dict(message, **kwargs)
        log_dict["level"] = "CRITICAL"
        self.logger.critical(json.dumps(log_dict))

    def correlation_context(self) -> "CorrelationContext":
        """
        Context manager for correlation ID.

        Usage:
            with logger.correlation_context() as corr_id:
                logger.info("Processing request")
        """
        return CorrelationContext()


class CorrelationContext:
    """Context manager for correlation IDs."""

    def __enter__(self) -> str:
        """Generate and set correlation ID."""
        corr_id = str(uuid.uuid4())
        correlation_id.set(corr_id)
        return corr_id

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Clear correlation ID."""
        correlation_id.set(None)


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_dict = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
        }

        # Add exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_dict)


class LogAggregator:
    """
    Aggregates logs from multiple sources.

    Can parse and analyze log files.
    """

    def __init__(self, log_file: Any) -> None:
        """Initialize log aggregator."""
        if isinstance(log_file, str):
            log_file = Path(log_file)
        self.log_file = log_file

    def get_logs(
        self,
        level: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        Get logs with optional filters.

        Args:
            level: Filter by log level
            correlation_id: Filter by correlation ID
            limit: Maximum number of logs to return

        Returns:
            List of log dictionaries
        """
        logs: List[Dict[str, Any]] = []

        if not self.log_file.exists():
            return logs

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line)

                    # Apply filters
                    if level and log_entry.get("level") != level:
                        continue
                    if correlation_id and log_entry.get("correlation_id") != correlation_id:
                        continue

                    logs.append(log_entry)

                    if len(logs) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

        return logs

    def get_logs_by_correlation_id(self, correlation_id: str) -> list[Dict[str, Any]]:
        """
        Get logs by correlation ID.

        Args:
            correlation_id: Correlation ID to filter by

        Returns:
            List of log dictionaries
        """
        return self.get_logs(correlation_id=correlation_id)

    def get_error_summary(self, hours: int = 24) -> Dict[str, int]:
        """
        Get summary of errors in last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary of error counts by type
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        error_counts: Dict[str, int] = {}

        if not self.log_file.exists():
            return error_counts

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line)

                    # Only errors
                    if log_entry.get("level") not in ("ERROR", "CRITICAL"):
                        continue

                    # Check timestamp
                    try:
                        log_time = datetime.fromisoformat(log_entry["timestamp"].replace("Z", ""))
                        if log_time < cutoff:
                            continue
                    except (ValueError, KeyError):
                        continue

                    # Count by message prefix
                    message = log_entry.get("message", "Unknown")
                    error_type = message.split(":")[0] if ":" in message else message[:50]

                    error_counts[error_type] = error_counts.get(error_type, 0) + 1

                except json.JSONDecodeError:
                    continue

        return error_counts
