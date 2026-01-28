"""
Logging formatters for the compact UI.
High-performance formatters optimized for minimal overhead.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Set

from configurator.ui.logging.levels import LEVEL_SPECS, get_level_color, get_level_symbol
from configurator.ui.theme import Theme


class CompactLogFormatter(logging.Formatter):
    """
    Format logs as compact, structured output.

    Output format:
        HH:MM:SS ✓ module_name    duration  status

    Design:
    - Single line per log entry
    - Fixed column widths for alignment
    - Direct ANSI output (bypasses Rich overhead)
    - Sub-millisecond formatting time
    """

    # Standard LogRecord attributes to ignore when looking for extras
    STANDARD_ATTRS: Set[str] = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def __init__(
        self,
        use_colors: bool = True,
        show_timestamp: bool = True,
        module_width: int = 15,
        duration_width: int = 6,
    ) -> None:
        """
        Initialize the formatter.

        Args:
            use_colors: Enable ANSI color output
            show_timestamp: Include timestamp in output
            module_width: Character width for module name column
            duration_width: Character width for duration column
        """
        super().__init__()
        self.use_colors = use_colors and Theme.supports_color()
        self.show_timestamp = show_timestamp
        self.module_width = module_width
        self.duration_width = duration_width

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        parts = []

        # Timestamp
        if self.show_timestamp:
            time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            if self.use_colors:
                time_str = f"{Theme.ANSI_COLORS['DIM']}{time_str}{Theme.ANSI_COLORS['RESET']}"
            parts.append(time_str)

        # Level Symbol
        level_name = record.levelname
        if level_name == "WARNING":
            level_name = "WARN"
        elif level_name == "CRITICAL":
            level_name = "ERROR"

        symbol = (
            get_level_symbol(level_name)
            if level_name in LEVEL_SPECS
            else Theme.get_symbol(level_name)
        )
        color_key = get_level_color(level_name) if level_name in LEVEL_SPECS else level_name

        if self.use_colors:
            color = Theme.ANSI_COLORS.get(color_key, "")
            reset = Theme.ANSI_COLORS["RESET"]
            symbol_str = f"{color}{symbol}{reset}"
        else:
            symbol_str = symbol
        parts.append(symbol_str)

        # Module Name (truncate or pad)
        module = record.name.split(".")[-1]
        if len(module) > self.module_width:
            module = module[: self.module_width - 3] + "..."
        module_str = module.ljust(self.module_width)

        if self.use_colors:
            color = Theme.ANSI_COLORS.get(color_key, "")
            reset = Theme.ANSI_COLORS["RESET"]
            module_str = f"{color}{module_str}{reset}"
        parts.append(module_str)

        # Duration (if available)
        duration = getattr(record, "duration_ms", None)
        if duration is not None:
            duration_str = self._format_duration(duration)
        else:
            duration_str = " " * self.duration_width

        if self.use_colors:
            duration_str = f"{Theme.ANSI_COLORS['DIM']}{duration_str}{Theme.ANSI_COLORS['RESET']}"
        parts.append(duration_str)

        # Message/Status
        message = record.getMessage()
        parts.append(message)

        return " ".join(parts)

    def _format_duration(self, duration_ms: float) -> str:
        """Format duration for display."""
        if isinstance(duration_ms, (int, float)):
            if duration_ms < 1000:
                return f"{int(duration_ms)}ms".rjust(self.duration_width)
            elif duration_ms < 60000:
                return f"{duration_ms / 1000:.1f}s".rjust(self.duration_width)
            else:
                minutes = int(duration_ms // 60000)
                return f"{minutes}m".rjust(self.duration_width)
        return str(duration_ms)[: self.duration_width].rjust(self.duration_width)


class StructuredLogFormatter(logging.Formatter):
    """
    Enhanced formatter with structured detail output.

    Output format:
        HH:MM:SS ✓ Module Name
                   → Detail line 1
                   → Detail line 2

    Use for verbose mode where additional context is valuable.
    """

    def __init__(
        self,
        use_colors: bool = True,
        indent: int = 11,  # Aligns with after timestamp + symbol
    ) -> None:
        super().__init__()
        self.use_colors = use_colors and Theme.supports_color()
        self.indent = indent
        self._compact = CompactLogFormatter(use_colors=use_colors)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with optional details."""
        # Base line from compact formatter
        base_line = self._compact.format(record)

        # Check for detail fields
        details = getattr(record, "details", None)
        if not details:
            return base_line

        # Format details as indented sub-lines
        lines = [base_line]
        indent_str = " " * self.indent
        arrow = Theme.get_symbol("ARROW")

        if isinstance(details, dict):
            for key, value in details.items():
                detail_line = f"{indent_str}{arrow} {key}: {value}"
                if self.use_colors:
                    detail_line = (
                        f"{Theme.ANSI_COLORS['DIM']}{detail_line}{Theme.ANSI_COLORS['RESET']}"
                    )
                lines.append(detail_line)
        elif isinstance(details, (list, tuple)):
            for item in details:
                detail_line = f"{indent_str}{arrow} {item}"
                if self.use_colors:
                    detail_line = (
                        f"{Theme.ANSI_COLORS['DIM']}{detail_line}{Theme.ANSI_COLORS['RESET']}"
                    )
                lines.append(detail_line)
        else:
            detail_line = f"{indent_str}{arrow} {details}"
            if self.use_colors:
                detail_line = f"{Theme.ANSI_COLORS['DIM']}{detail_line}{Theme.ANSI_COLORS['RESET']}"
            lines.append(detail_line)

        return "\n".join(lines)


class JSONLogFormatter(logging.Formatter):
    """
    Format logs as JSON for machine parsing.
    Alignment with industry standards (CloudWatch, Datadog, etc).
    """

    # Standard LogRecord attributes to exclude from extras
    STANDARD_ATTRS: Set[str] = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def __init__(self, include_extras: bool = True) -> None:
        """
        Initialize JSON formatter.

        Args:
            include_extras: Include extra fields from log record
        """
        super().__init__()
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Add line info for errors
        if record.levelno >= logging.ERROR:
            data["file"] = record.filename
            data["line"] = record.lineno
            data["function"] = record.funcName

        # Add extra fields
        if self.include_extras:
            for key, value in record.__dict__.items():
                if key not in self.STANDARD_ATTRS and key not in data:
                    # Try to serialize, skip if not serializable
                    try:
                        json.dumps(value)
                        data[key] = value
                    except (TypeError, ValueError):
                        data[key] = str(value)

        # Add exception info if present
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        return json.dumps(data, default=str, ensure_ascii=False)


class MinimalLogFormatter(logging.Formatter):
    """
    Absolute minimal formatter for CI/CD and piping.

    Output format:
        [LEVEL] message

    No colors, no timestamps, no special characters.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format with minimal overhead."""
        level = record.levelname[:4].upper()  # INFO, WARN, ERRO, etc.
        return f"[{level}] {record.getMessage()}"
