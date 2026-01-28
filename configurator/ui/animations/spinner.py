"""
Efficient spinner implementations for terminal UI.
Focuses on low CPU usage and pre-rendered frames.
"""

import time
from enum import Enum
from typing import Optional

from configurator.ui.theme import Theme


class SpinnerStyle(Enum):
    """Available spinner animation styles."""

    ASCII = "ASCII"
    BRAILLE = "BRAILLE"
    DOTS = "DOTS"
    LINE = "LINE"
    BOUNCE = "BOUNCE"
    ARROWS = "ARROWS"
    NONE = "NONE"


class EfficientSpinner:
    """
    Minimal frame spinner with configurable styles.
    Pre-calculated frames to minimize CPU overhead.

    Design:
    - 4 FPS default (250ms per frame) - human-perceivable, low CPU
    - Math-based frame selection - no state mutation per render
    - Thread-safe by design (no shared mutable state in render)
    """

    def __init__(
        self,
        style: SpinnerStyle = SpinnerStyle.ASCII,
        fps: Optional[float] = None,
        auto_detect: bool = True,
    ) -> None:
        """
        Initialize the spinner.

        Args:
            style: Animation style from SpinnerStyle enum
            fps: Frames per second (default from theme)
            auto_detect: Auto-select style based on terminal capabilities
        """
        self._style = style
        self._fps = fps or Theme.ANIMATION["SPINNER_FPS"]
        self._interval = 1.0 / self._fps

        # Auto-detect terminal capabilities
        if auto_detect and style != SpinnerStyle.NONE:
            if not Theme.supports_unicode():
                self._style = SpinnerStyle.ASCII

        # Cache frames for this style
        self._frames = Theme.get_spinner_frames(self._style.value)
        self._frame_count = len(self._frames)

    @property
    def style(self) -> SpinnerStyle:
        """Current spinner style."""
        return self._style

    @style.setter
    def style(self, value: SpinnerStyle) -> None:
        """Change spinner style."""
        self._style = value
        self._frames = Theme.get_spinner_frames(value.value)
        self._frame_count = len(self._frames)

    def render(self) -> str:
        """
        Return current frame based on time.
        Non-blocking, math-based frame selection.
        Thread-safe: no mutable state.
        """
        frame_idx = int(time.time() / self._interval) % self._frame_count
        return self._frames[frame_idx]

    def render_with_message(self, message: str) -> str:
        """
        Render spinner with inline message.

        Args:
            message: Text to display after spinner

        Returns:
            Formatted string: "/ Loading..."
        """
        return f"{self.render()} {message}"

    @classmethod
    def get_static_indicator(cls) -> str:
        """Get a static indicator for non-animated mode."""
        return Theme.get_symbol("RUNNING")


class CompactProgressBar:
    """
    Single-line compact progress indicator.
    [████░░░░░] 50%
    """

    def __init__(
        self,
        width: int = 20,
        ascii_only: bool = False,
    ) -> None:
        """
        Initialize progress bar.

        Args:
            width: Character width of the bar (excluding brackets/percentage)
            ascii_only: Use ASCII characters instead of unicode
        """
        self.width = width
        chars = Theme.get_progress_chars(ascii_only=ascii_only)
        self.fill_char = chars["FILL"]
        self.empty_char = chars["EMPTY"]
        self.left_bracket = chars["LEFT_BRACKET"]
        self.right_bracket = chars["RIGHT_BRACKET"]

    def render(self, current: int, total: int) -> str:
        """
        Return compact progress string.

        Args:
            current: Current progress value
            total: Total/maximum value

        Returns:
            Formatted progress bar string
        """
        if total <= 0:
            return f"{self.left_bracket}{self.empty_char * self.width}{self.right_bracket} 0%"

        ratio = min(1.0, max(0.0, current / total))
        filled = int(self.width * ratio)
        empty = self.width - filled
        percentage = int(ratio * 100)

        bar = f"{self.fill_char * filled}{self.empty_char * empty}"
        return f"{self.left_bracket}{bar}{self.right_bracket} {percentage}%"

    def render_inline(self, current: int, total: int) -> str:
        """
        Render inline progress without bar.

        Returns:
            Format: "(3/10)"
        """
        return f"({current}/{total})"


class PercentageIndicator:
    """
    Minimal percentage-only progress indicator.
    For use in compact/minimal modes.
    """

    @staticmethod
    def render(current: int, total: int) -> str:
        """
        Render percentage only.

        Returns:
            Format: "75%"
        """
        if total <= 0:
            return "0%"
        percentage = int(min(100, max(0, (current / total) * 100)))
        return f"{percentage}%"
