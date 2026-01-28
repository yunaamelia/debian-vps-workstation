"""
Terminal rendering utilities for direct output.
Bypasses Rich overhead for high-performance logging.
"""

import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TextIO

from configurator.ui.theme import Theme


class ColorMode(Enum):
    """Color output mode selection."""

    AUTO = "auto"  # Detect based on terminal capabilities
    ALWAYS = "always"  # Always use colors (force)
    NEVER = "never"  # Never use colors


@dataclass
class TerminalInfo:
    """Terminal capability information."""

    is_tty: bool
    supports_color: bool
    supports_unicode: bool
    width: int
    encoding: str

    @classmethod
    def detect(cls, stream: Optional[TextIO] = None) -> "TerminalInfo":
        """
        Detect terminal capabilities.

        Args:
            stream: Output stream to check (defaults to stdout)

        Returns:
            TerminalInfo with detected capabilities
        """
        stream = stream or sys.stdout

        # TTY detection
        is_tty = hasattr(stream, "isatty") and stream.isatty()

        # Color support
        supports_color = is_tty and not os.environ.get("NO_COLOR")
        if os.environ.get("TERM") == "dumb":
            supports_color = False
        if os.environ.get("FORCE_COLOR"):
            supports_color = True

        # Unicode support
        encoding = getattr(stream, "encoding", "") or ""
        supports_unicode = "utf" in encoding.lower()

        # Terminal width
        try:
            width = os.get_terminal_size().columns
        except (OSError, ValueError):
            width = 80  # Fallback

        return cls(
            is_tty=is_tty,
            supports_color=supports_color,
            supports_unicode=supports_unicode,
            width=width,
            encoding=encoding,
        )


class ANSIRenderer:
    """
    Direct ANSI escape sequence renderer.
    Minimal overhead alternative to Rich for simple output.
    """

    def __init__(
        self,
        color_mode: ColorMode = ColorMode.AUTO,
        stream: Optional[TextIO] = None,
    ) -> None:
        """
        Initialize renderer.

        Args:
            color_mode: Color output mode
            stream: Output stream (defaults to stdout)
        """
        self.stream = stream or sys.stdout
        self.color_mode = color_mode
        self.terminal_info = TerminalInfo.detect(self.stream)

        # Determine if we should use colors
        if color_mode == ColorMode.ALWAYS:
            self._use_colors = True
        elif color_mode == ColorMode.NEVER:
            self._use_colors = False
        else:  # AUTO
            self._use_colors = self.terminal_info.supports_color

    @property
    def use_colors(self) -> bool:
        """Check if colors should be used."""
        return self._use_colors

    @property
    def use_unicode(self) -> bool:
        """Check if unicode should be used."""
        return self.terminal_info.supports_unicode

    def colorize(self, text: str, color: str) -> str:
        """
        Apply color to text if colors are enabled.

        Args:
            text: Text to colorize
            color: Color name from Theme.ANSI_COLORS

        Returns:
            Colored text (or original if colors disabled)
        """
        if not self._use_colors:
            return text
        return Theme.colorize(text, color)

    def dim(self, text: str) -> str:
        """Apply dim styling."""
        if not self._use_colors:
            return text
        return f"{Theme.ANSI_COLORS['DIM']}{text}{Theme.ANSI_COLORS['RESET']}"

    def bold(self, text: str) -> str:
        """Apply bold styling."""
        if not self._use_colors:
            return text
        return f"{Theme.ANSI_COLORS['BOLD']}{text}{Theme.ANSI_COLORS['RESET']}"

    def write(self, text: str) -> None:
        """Write text to stream."""
        self.stream.write(text)
        self.stream.flush()

    def writeln(self, text: str = "") -> None:
        """Write text with newline to stream."""
        self.stream.write(text + "\n")
        self.stream.flush()

    def clear_line(self) -> None:
        """Clear current line (for animations)."""
        if self._use_colors and self.terminal_info.is_tty:
            self.stream.write("\r\033[K")
            self.stream.flush()


class OutputBuffer:
    """
    Buffered output for high-throughput scenarios.
    Batches writes to reduce I/O overhead.
    """

    def __init__(
        self,
        renderer: Optional[ANSIRenderer] = None,
        max_buffer_size: int = 100,
        flush_interval_lines: int = 10,
    ) -> None:
        """
        Initialize output buffer.

        Args:
            renderer: ANSI renderer to use
            max_buffer_size: Maximum buffer size before forced flush
            flush_interval_lines: Flush every N lines
        """
        self.renderer = renderer or ANSIRenderer()
        self.max_buffer_size = max_buffer_size
        self.flush_interval_lines = flush_interval_lines
        self._buffer: List[str] = []
        self._line_count = 0

    def write(self, text: str) -> None:
        """Add text to buffer."""
        self._buffer.append(text)
        if len(self._buffer) >= self.max_buffer_size:
            self.flush()

    def writeln(self, text: str = "") -> None:
        """Add line to buffer."""
        self._buffer.append(text + "\n")
        self._line_count += 1

        if self._line_count >= self.flush_interval_lines:
            self.flush()

    def flush(self) -> None:
        """Flush buffer to stream."""
        if self._buffer:
            self.renderer.write("".join(self._buffer))
            self._buffer.clear()
            self._line_count = 0

    def __enter__(self) -> "OutputBuffer":
        return self

    def __exit__(self, *args) -> None:
        self.flush()
