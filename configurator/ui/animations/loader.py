"""
Phase transition and loading animations for compact UI.
Low-overhead visual indicators for installation phases.
"""

from datetime import datetime
from typing import Optional

from configurator.ui.theme import Theme


class PhaseBanner:
    """
    Compact phase header display.
    Replaces verbose Rich panels with minimal overhead.
    """

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and Theme.supports_color()

    def render(self, phase_name: str, description: Optional[str] = None) -> str:
        """
        Render a phase banner.

        Args:
            phase_name: Name of the phase (e.g., "Installing Docker")
            description: Optional brief description

        Returns:
            Formatted banner string
        """
        if self.use_colors:
            header_color = Theme.ANSI_COLORS["HEADER"]
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]

            line = f"\n{header_color}{'─' * 60}{reset}"
            title = f"{header_color}▶ {phase_name}{reset}"

            if description:
                desc = f"{dim}  {description}{reset}"
                return f"{line}\n{title}\n{desc}\n"
            return f"{line}\n{title}\n"
        else:
            line = f"\n{'─' * 60}"
            title = f"> {phase_name}"

            if description:
                return f"{line}\n{title}\n  {description}\n"
            return f"{line}\n{title}\n"

    def render_compact(self, phase_name: str) -> str:
        """
        Render a single-line phase indicator.

        Returns:
            Format: "▶ Phase Name"
        """
        if self.use_colors:
            return f"{Theme.ANSI_COLORS['HEADER']}▶ {phase_name}{Theme.ANSI_COLORS['RESET']}"
        return f"> {phase_name}"


class CompletionIndicator:
    """
    Compact success/failure indicators.
    """

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and Theme.supports_color()

    def render_success(self, message: str, duration_ms: Optional[int] = None) -> str:
        """
        Render success indicator.

        Args:
            message: Success message
            duration_ms: Optional duration in milliseconds

        Returns:
            Formatted success string
        """
        duration_str = self._format_duration(duration_ms) if duration_ms else ""
        symbol = Theme.get_symbol("CHECK")

        if self.use_colors:
            color = Theme.ANSI_COLORS["SUCCESS"]
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{color}{symbol}{reset} {message}{dim}{duration_str}{reset}"
        return f"{symbol} {message}{duration_str}"

    def render_failure(self, message: str, duration_ms: Optional[int] = None) -> str:
        """
        Render failure indicator.

        Args:
            message: Failure message
            duration_ms: Optional duration in milliseconds

        Returns:
            Formatted failure string
        """
        duration_str = self._format_duration(duration_ms) if duration_ms else ""
        symbol = Theme.get_symbol("CROSS")

        if self.use_colors:
            color = Theme.ANSI_COLORS["ERROR"]
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{color}{symbol}{reset} {message}{dim}{duration_str}{reset}"
        return f"{symbol} {message}{duration_str}"

    def render_warning(self, message: str) -> str:
        """
        Render warning indicator.

        Returns:
            Formatted warning string
        """
        symbol = Theme.get_symbol("WARN")

        if self.use_colors:
            color = Theme.ANSI_COLORS["WARN"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{color}{symbol}{reset} {message}"
        return f"{symbol} {message}"

    def render_info(self, message: str) -> str:
        """
        Render info indicator.

        Returns:
            Formatted info string
        """
        symbol = Theme.get_symbol("INFO")

        if self.use_colors:
            color = Theme.ANSI_COLORS["INFO"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{color}{symbol}{reset} {message}"
        return f"{symbol} {message}"

    def _format_duration(self, duration_ms: int) -> str:
        """Format duration for display."""
        if duration_ms < 1000:
            return f" ({duration_ms}ms)"
        elif duration_ms < 60000:
            return f" ({duration_ms / 1000:.1f}s)"
        else:
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) / 1000
            return f" ({minutes}m {seconds:.0f}s)"


class TransitionEffect:
    """
    Visual phase separators and transitions.
    Minimal overhead alternatives to Rich animations.
    """

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and Theme.supports_color()

    def separator(self, char: str = "─", width: int = 60) -> str:
        """
        Render a horizontal separator.

        Args:
            char: Character to use for separator
            width: Width of separator

        Returns:
            Separator string
        """
        if self.use_colors:
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{dim}{char * width}{reset}"
        return char * width

    def section_header(self, title: str) -> str:
        """
        Render a section header with separators.

        Returns:
            Formatted section header
        """
        if self.use_colors:
            header = Theme.ANSI_COLORS["HEADER"]
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"\n{dim}{'─' * 20}{reset} {header}{title}{reset} {dim}{'─' * 20}{reset}\n"
        return f"\n{'─' * 20} {title} {'─' * 20}\n"

    def timestamp(self) -> str:
        """
        Get current timestamp in compact format.

        Returns:
            Format: "HH:MM:SS"
        """
        return datetime.now().strftime("%H:%M:%S")

    def timestamped_line(self, message: str) -> str:
        """
        Create a timestamped log line.

        Returns:
            Format: "HH:MM:SS message"
        """
        ts = self.timestamp()
        if self.use_colors:
            dim = Theme.ANSI_COLORS["DIM"]
            reset = Theme.ANSI_COLORS["RESET"]
            return f"{dim}{ts}{reset} {message}"
        return f"{ts} {message}"
