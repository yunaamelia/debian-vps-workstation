"""
Output mode management for the UI.
Handles switching between Compact, Verbose, and Minimal modes.
"""

import logging
import sys
from enum import Enum

from configurator.ui.logging.formatter import CompactLogFormatter


class UIMode(Enum):
    COMPACT = "compact"  # Essential info, single line
    VERBOSE = "verbose"  # Detailed, standard debug
    MINIMAL = "minimal"  # No animations, pure text (CI/CD)
    JSON = "json"  # Machine readable structured logs


class ConsoleManager:
    """Manages console output based on output mode."""

    def __init__(self, mode: UIMode = UIMode.COMPACT):
        self.mode = mode
        # Simple check for TTY
        self.is_interactive = sys.stdout.isatty()

        # If not interactive and standard mode, default to minimal (unless explicitly JSON)
        if not self.is_interactive and self.mode == UIMode.COMPACT:
            self.mode = UIMode.MINIMAL

    def get_formatter(self) -> logging.Formatter | None:
        """Get the appropriate log formatter."""
        if self.mode == UIMode.VERBOSE:
            # Return None to use standard/Rich formatting
            return None

        if self.mode == UIMode.JSON:
            from configurator.ui.logging.formatter import JSONLogFormatter

            return JSONLogFormatter()

        use_colors = self.mode != UIMode.MINIMAL
        return CompactLogFormatter(use_colors=use_colors)

    def should_animate(self) -> bool:
        """Check if animations should be enabled."""
        return self.mode not in (UIMode.MINIMAL, UIMode.JSON) and self.is_interactive
