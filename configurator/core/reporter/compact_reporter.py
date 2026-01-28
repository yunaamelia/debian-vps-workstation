"""
Compact progress reporter for high-performance installation output.
Streaming, append-only output with minimal overhead.
"""

import sys
from datetime import datetime
from typing import Any, Dict, Optional, TextIO

from configurator.core.reporter.base import ReporterInterface
from configurator.ui.theme import Theme


class CompactReporter(ReporterInterface):
    """
    High-performance streaming reporter.

    Design:
    - Zero screen redraws, append-only output
    - Single line per module/phase
    - Duration tracking with human-readable format
    - Status column alignment
    - Thread-safe write operations

    Output format:
        14:30:22 ✓ docker           42s  containerd, buildx installed
        14:30:64 ✓ zsh              28s  plugins loaded
        14:31:02 ⚠ git-lfs          15s  optional (skipped)
        14:31:18 → zoxide               configuring...
    """

    def __init__(
        self,
        use_colors: bool = True,
        show_timestamp: bool = True,
        stream: Optional[TextIO] = None,
        module_width: int = 15,
        duration_width: int = 6,
    ) -> None:
        """
        Initialize compact reporter.

        Args:
            use_colors: Enable ANSI color output
            show_timestamp: Include timestamp in output
            stream: Output stream (defaults to stdout)
            module_width: Character width for module name column
            duration_width: Character width for duration column
        """
        self.stream = stream or sys.stdout
        self.use_colors = use_colors and Theme.supports_color()
        self.show_timestamp = show_timestamp
        self.module_width = module_width
        self.duration_width = duration_width

        # Phase tracking
        self.phase_start_times: Dict[str, datetime] = {}
        self._current_phase: Optional[str] = None
        self._results: Dict[str, bool] = {}

    def _write(self, text: str) -> None:
        """Write text to stream with flush."""
        self.stream.write(text + "\n")
        self.stream.flush()

    def _timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%H:%M:%S")

    def _format_duration(self, start_time: datetime) -> str:
        """Format duration from start time to now."""
        duration = datetime.now() - start_time
        total_seconds = duration.total_seconds()

        if total_seconds < 1:
            return f"{int(total_seconds * 1000)}ms".rjust(self.duration_width)
        elif total_seconds < 60:
            return f"{int(total_seconds)}s".rjust(self.duration_width)
        else:
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes}m{seconds}s".rjust(self.duration_width)

    def _format_module(self, name: str) -> str:
        """Format module name with padding/truncation."""
        if len(name) > self.module_width:
            name = name[: self.module_width - 3] + "..."
        return name.ljust(self.module_width)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color if enabled."""
        if not self.use_colors:
            return text
        return Theme.colorize(text, color)

    def _dim(self, text: str) -> str:
        """Apply dim styling if colors enabled."""
        if not self.use_colors:
            return text
        return f"{Theme.ANSI_COLORS['DIM']}{text}{Theme.ANSI_COLORS['RESET']}"

    def start(self, title: str = "Installation") -> None:
        """Display startup banner."""
        separator = "─" * 60

        if self.use_colors:
            header = Theme.ANSI_COLORS["HEADER"]
            reset = Theme.ANSI_COLORS["RESET"]
            self._write(f"\n{header}{separator}{reset}")
            self._write(f"{header}▶ {title}{reset}")
            self._write(f"{header}{separator}{reset}\n")
        else:
            self._write(f"\n{separator}")
            self._write(f"> {title}")
            self._write(f"{separator}\n")

    def stop(self) -> None:
        """Stop the reporter (no-op for streaming)."""
        pass  # Nothing to stop in streaming mode

    def start_phase(self, name: str, total_steps: int = 0) -> None:
        """
        Start new installation phase/module.

        Args:
            name: Phase/module name
            total_steps: Total steps (unused in compact mode)
        """
        self._current_phase = name
        self.phase_start_times[name] = datetime.now()

        # Output in-progress line
        parts = []

        if self.show_timestamp:
            parts.append(self._dim(self._timestamp()))

        symbol = Theme.get_symbol("RUNNING")
        parts.append(self._colorize(symbol, "PENDING"))
        parts.append(self._colorize(self._format_module(name), "PENDING"))
        parts.append(" " * self.duration_width)  # No duration yet
        parts.append("starting...")

        self._write(" ".join(parts))

    def update(
        self,
        message: str,
        success: bool = True,
        module: Optional[str] = None,
    ) -> None:
        """
        Update progress status.

        In compact mode, updates are printed as new lines.

        Args:
            message: Status message
            success: True for success, False for error
            module: Module name (uses current phase if None)
        """
        target = module or self._current_phase
        if not target:
            return

        parts = []

        if self.show_timestamp:
            parts.append(self._dim(self._timestamp()))

        # Determine symbol and color based on success
        if success:
            symbol = Theme.get_symbol("DEBUG")  # Arrow for in-progress
            color = "DEBUG"
        else:
            symbol = Theme.get_symbol("CROSS")
            color = "ERROR"

        parts.append(self._colorize(symbol, color))
        parts.append(self._colorize(self._format_module(target), color))

        # Duration if available
        if target in self.phase_start_times:
            parts.append(self._dim(self._format_duration(self.phase_start_times[target])))
        else:
            parts.append(" " * self.duration_width)

        parts.append(message)

        self._write(" ".join(parts))

    def update_progress(
        self,
        percent: int,
        current: Optional[int] = None,
        total: Optional[int] = None,
        module: Optional[str] = None,
    ) -> None:
        """
        Update progress percentage.

        In compact mode, progress updates are minimized to reduce output.
        Only major milestones (25%, 50%, 75%, 100%) produce output.
        """
        # Only log at major milestones to avoid spam
        if percent in (25, 50, 75, 100):
            target = module or self._current_phase
            if target:
                if current is not None and total is not None:
                    msg = f"progress: {current}/{total} ({percent}%)"
                else:
                    msg = f"progress: {percent}%"
                self.update(msg, success=True, module=target)

    def complete_phase(
        self,
        success: bool = True,
        module: Optional[str] = None,
    ) -> None:
        """
        Mark current phase as complete.

        Args:
            success: True for success, False for failure
            module: Module name (uses current phase if None)
        """
        target = module or self._current_phase
        if not target:
            return

        # Record result
        self._results[target] = success

        parts = []

        if self.show_timestamp:
            parts.append(self._dim(self._timestamp()))

        # Symbol and color based on success
        if success:
            symbol = Theme.get_symbol("CHECK")
            color = "SUCCESS"
            status = "done"
        else:
            symbol = Theme.get_symbol("CROSS")
            color = "ERROR"
            status = "failed"

        parts.append(self._colorize(symbol, color))
        parts.append(self._colorize(self._format_module(target), color))

        # Duration
        if target in self.phase_start_times:
            parts.append(self._dim(self._format_duration(self.phase_start_times[target])))
        else:
            parts.append(" " * self.duration_width)

        parts.append(status)

        self._write(" ".join(parts))

    def show_summary(self, results: Dict[str, bool]) -> None:
        """Display installation summary."""
        # Merge with tracked results
        all_results = {**self._results, **results}

        success_count = sum(1 for v in all_results.values() if v)
        fail_count = len(all_results) - success_count

        separator = "─" * 60

        self._write("")
        if self.use_colors:
            header = Theme.ANSI_COLORS["HEADER"]
            reset = Theme.ANSI_COLORS["RESET"]
            self._write(f"{header}{separator}{reset}")
            self._write(f"{header}Summary{reset}")
        else:
            self._write(separator)
            self._write("Summary")

        for module, success in all_results.items():
            symbol = Theme.get_symbol("CHECK") if success else Theme.get_symbol("CROSS")
            color = "SUCCESS" if success else "ERROR"
            status = "success" if success else "FAILED"

            line = f"  {self._colorize(symbol, color)} {module}: {status}"
            self._write(line)

        # Overall status
        self._write("")
        if fail_count == 0:
            self._write(
                self._colorize(f"✓ All {success_count} modules completed successfully", "SUCCESS")
            )
        else:
            self._write(
                self._colorize(f"✗ {fail_count} of {len(all_results)} modules failed", "ERROR")
            )

    def error(self, message: str) -> None:
        """Display error message."""
        symbol = Theme.get_symbol("CROSS")
        line = f"{self._colorize(symbol, 'ERROR')} ERROR: {message}"
        self._write(line)

    def warning(self, message: str) -> None:
        """Display warning message."""
        symbol = Theme.get_symbol("WARN")
        line = f"{self._colorize(symbol, 'WARN')} WARNING: {message}"
        self._write(line)

    def info(self, message: str) -> None:
        """Display info message."""
        symbol = Theme.get_symbol("INFO")
        line = f"{self._colorize(symbol, 'INFO')} {message}"
        self._write(line)

    def show_next_steps(
        self,
        reboot_required: bool = False,
        rdp_port: int = 3389,
        **kwargs: Any,
    ) -> None:
        """Display next steps after installation."""
        self._write("")
        if self.use_colors:
            header = Theme.ANSI_COLORS["HEADER"]
            reset = Theme.ANSI_COLORS["RESET"]
            self._write(f"{header}Next Steps:{reset}")
        else:
            self._write("Next Steps:")

        if reboot_required:
            self._write(f"  {Theme.get_symbol('BULLET')} Reboot your system: sudo reboot")

        self._write(f"  {Theme.get_symbol('BULLET')} Verify installation: vps-configurator verify")
        self._write(f"  {Theme.get_symbol('BULLET')} Connect via RDP on port: {rdp_port}")
