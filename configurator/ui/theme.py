"""
UI Theme definitions for the configurator.
Defines colors, symbols, styling constants, and animation specifications.
"""

import sys
from typing import Dict, List


class Theme:
    """Application theme constants for high-performance terminal UI."""

    # =========================================================================
    # Color Definitions
    # =========================================================================

    # Rich-compatible color names
    COLORS: Dict[str, str] = {
        "ERROR": "red",
        "WARN": "yellow",
        "INFO": "green",
        "DEBUG": "blue",
        "TRACE": "bright_black",
        "HEADER": "cyan",
        "SUCCESS": "green",
        "PENDING": "cyan",
        "DIM": "dim",
    }

    # ANSI escape codes for direct terminal output (bypasses Rich overhead)
    ANSI_COLORS: Dict[str, str] = {
        "ERROR": "\033[31m",  # Red
        "WARN": "\033[33m",  # Yellow
        "INFO": "\033[32m",  # Green
        "DEBUG": "\033[34m",  # Blue
        "TRACE": "\033[90m",  # Bright Black (Gray)
        "HEADER": "\033[36m",  # Cyan
        "SUCCESS": "\033[32m",  # Green
        "PENDING": "\033[36m",  # Cyan
        "DIM": "\033[2m",  # Dim
        "BOLD": "\033[1m",  # Bold
        "RESET": "\033[0m",  # Reset
    }

    # =========================================================================
    # Symbol Definitions
    # =========================================================================

    # Unicode symbols
    SYMBOLS: Dict[str, str] = {
        "ERROR": "✗",
        "WARN": "⚠",
        "INFO": "✓",
        "DEBUG": "→",
        "TRACE": "└─",
        "PENDING": "⋯",
        "RUNNING": "◌",
        "ARROW": "→",
        "CHECK": "✓",
        "CROSS": "✗",
        "BULLET": "•",
        "ELLIPSIS": "…",
    }

    # ASCII fallbacks for non-unicode terminals
    ASCII_SYMBOLS: Dict[str, str] = {
        "ERROR": "X",
        "WARN": "!",
        "INFO": "OK",
        "DEBUG": "->",
        "TRACE": "  ",
        "PENDING": "...",
        "RUNNING": "*",
        "ARROW": "->",
        "CHECK": "OK",
        "CROSS": "X",
        "BULLET": "*",
        "ELLIPSIS": "...",
    }

    # =========================================================================
    # Animation Configuration
    # =========================================================================

    # Timing constants (optimized for minimal CPU usage)
    ANIMATION: Dict[str, float] = {
        "SPINNER_FPS": 4.0,  # 250ms per frame - human-perceivable, low CPU
        "PROGRESS_FPS": 2.0,  # 500ms per update - for progress bars
        "REFRESH_LIMIT": 10.0,  # Max console updates/sec
        "SPINNER_INTERVAL": 0.25,  # 1/SPINNER_FPS for direct use
    }

    # Pre-defined spinner frame sets
    SPINNER_FRAMES: Dict[str, List[str]] = {
        # Standard ASCII (most compatible, lowest overhead)
        "ASCII": ["/", "-", "\\", "|"],
        # Braille dots (smooth animation, unicode required)
        "BRAILLE": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        # Simple dots (compact)
        "DOTS": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
        # Line rotation
        "LINE": ["—", "\\", "|", "/"],
        # Minimal visual (for reduced distraction)
        "BOUNCE": ["⠁", "⠈", "⠐", "⠠"],
        # Static placeholder (for minimal/no-animation mode)
        "NONE": [" "],
        # Arrow-based (professional look)
        "ARROWS": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
    }

    # =========================================================================
    # Layout Constants
    # =========================================================================

    COLUMN_WIDTHS: Dict[str, int] = {
        "TIMESTAMP": 8,  # HH:MM:SS
        "LEVEL": 2,  # Symbol + space
        "MODULE": 15,  # Module name
        "DURATION": 6,  # XXXms or X.Xs
        "STATUS": 40,  # Status message
    }

    # Progress bar characters
    PROGRESS_CHARS: Dict[str, str] = {
        "FILL": "█",
        "EMPTY": "░",
        "HALF": "▓",
        "LEFT_BRACKET": "[",
        "RIGHT_BRACKET": "]",
    }

    # ASCII fallback for progress bars
    ASCII_PROGRESS_CHARS: Dict[str, str] = {
        "FILL": "#",
        "EMPTY": "-",
        "HALF": "=",
        "LEFT_BRACKET": "[",
        "RIGHT_BRACKET": "]",
    }

    # =========================================================================
    # Class Methods
    # =========================================================================

    @classmethod
    def get_symbol(cls, name: str, ascii_only: bool = False) -> str:
        """Get symbol based on mode."""
        if ascii_only:
            return cls.ASCII_SYMBOLS.get(name, "?")
        return cls.SYMBOLS.get(name, "?")

    @classmethod
    def get_ansi_color(cls, name: str) -> str:
        """Get ANSI escape code for color."""
        return cls.ANSI_COLORS.get(name, "")

    @classmethod
    def get_spinner_frames(cls, style: str = "ASCII") -> List[str]:
        """Get spinner frames for the specified style."""
        return cls.SPINNER_FRAMES.get(style, cls.SPINNER_FRAMES["ASCII"])

    @classmethod
    def get_progress_chars(cls, ascii_only: bool = False) -> Dict[str, str]:
        """Get progress bar characters."""
        if ascii_only:
            return cls.ASCII_PROGRESS_CHARS
        return cls.PROGRESS_CHARS

    @classmethod
    def colorize(cls, text: str, color: str, reset: bool = True) -> str:
        """
        Apply ANSI color to text.

        Args:
            text: Text to colorize
            color: Color name from ANSI_COLORS
            reset: Whether to append reset code

        Returns:
            Colored text string
        """
        color_code = cls.ANSI_COLORS.get(color, "")
        reset_code = cls.ANSI_COLORS["RESET"] if reset else ""
        return f"{color_code}{text}{reset_code}"

    @classmethod
    def supports_unicode(cls) -> bool:
        """Check if terminal likely supports unicode."""
        try:
            # Check stdout encoding
            if hasattr(sys.stdout, "encoding"):
                encoding = sys.stdout.encoding or ""
                return "utf" in encoding.lower()
        except Exception:
            pass
        return False

    @classmethod
    def supports_color(cls) -> bool:
        """Check if terminal likely supports color output."""
        # Check if stdout is a TTY
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False
        # Check for common no-color indicators
        import os

        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM") == "dumb":
            return False
        return True
