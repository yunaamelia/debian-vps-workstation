"""
Real-time monitoring dashboard for VPS Configurator.

Displays installation progress, metrics, and system status.
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class InstallationDashboard:
    """
    Real-time dashboard showing installation progress.

    Requires Rich library for display.
    """

    def __init__(self) -> None:
        """Initialize dashboard."""
        if not RICH_AVAILABLE:
            raise ImportError("Rich library required for dashboard")

        self.console = Console()
        self.layout = Layout()
        self.live: Optional[Live] = None

        # State
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.metrics: Dict[str, float] = {}
        self.start_time = time.time()

    def start(self) -> None:
        """Start the dashboard."""
        # Create layout
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        self.layout["body"].split_row(Layout(name="modules"), Layout(name="status", ratio=1))

        # Start live display
        self.live = Live(self.layout, console=self.console, refresh_per_second=2)
        self.live.start()

    def stop(self) -> None:
        """Stop the dashboard."""
        if self.live:
            self.live.stop()

    def update_module(
        self,
        name: str,
        status: str,
        progress: int = 0,
        duration: Optional[float] = None,
    ) -> None:
        """
        Update module status.

        Args:
            name: Module name
            status: Status (running, success, failed)
            progress: Progress percentage (0-100)
            duration: Duration in seconds
        """
        self.modules[name] = {
            "status": status,
            "progress": progress,
            "duration": duration,
            "updated": datetime.now(),
        }
        self._refresh()

    def update_circuit_breaker(self, name: str, state: str, failures: int) -> None:
        """Update circuit breaker status."""
        self.circuit_breakers[name] = {
            "state": state,
            "failures": failures,
            "updated": datetime.now(),
        }
        self._refresh()

    def update_metric(self, name: str, value: float) -> None:
        """Update metric value."""
        self.metrics[name] = value
        self._refresh()

    def _refresh(self) -> None:
        """Refresh the dashboard display."""
        if not self.live:
            return

        # Update header
        elapsed = time.time() - self.start_time
        self.layout["header"].update(
            Panel(
                f"VPS Configurator - Installation Progress | Elapsed: {elapsed:.1f}s",
                style="bold cyan",
            )
        )

        # Update modules section
        self.layout["modules"].update(self._render_modules())

        # Update status section
        # Update status section
        self.layout["status"].update(self._render_status())

    def _render(self) -> Layout:
        """Render the dashboard (for testing)."""
        self._refresh()
        return self.layout

        # Update footer
        completed = sum(1 for m in self.modules.values() if m["status"] == "success")
        failed = sum(1 for m in self.modules.values() if m["status"] == "failed")
        total = len(self.modules)

        footer_text = f"Modules: {completed}/{total} completed"
        if failed > 0:
            footer_text += f" | {failed} failed"

        self.layout["footer"].update(Panel(footer_text, style="dim"))

    def _render_modules(self) -> Panel:
        """Render modules table."""
        table = Table(title="Module Status", show_header=True)
        table.add_column("Module", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Progress", justify="right")
        table.add_column("Duration", justify="right")

        for name, info in self.modules.items():
            # Status icon
            status_icons = {
                "waiting": "⏳",
                "running": "🔄",
                "success": "✅",
                "failed": "❌",
            }
            icon = status_icons.get(info["status"], "❓")

            # Progress bar
            progress = f"{info['progress']}%"

            # Duration
            duration_str = "-"
            if info["duration"]:
                duration_str = f"{info['duration']:.1f}s"

            table.add_row(name, f"{icon} {info['status']}", progress, duration_str)

        return Panel(table, title="Installation Progress")

    def _render_status(self) -> Panel:
        """Render status section."""
        # Circuit breakers table
        cb_table = Table(title="Circuit Breakers", show_header=True, box=None)
        cb_table.add_column("Service", style="cyan")
        cb_table.add_column("State", style="magenta")
        cb_table.add_column("Failures", justify="right", style="red")

        for name, info in self.circuit_breakers.items():
            state_icons = {"CLOSED": "🟢", "HALF_OPEN": "🟡", "OPEN": "🔴"}
            icon = state_icons.get(info["state"], "⚪")

            cb_table.add_row(name, f"{icon} {info['state']}", str(info["failures"]))

        # Metrics table
        metrics_table = Table(title="System Metrics", show_header=True, box=None)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", justify="right")

        for name, value in self.metrics.items():
            metrics_table.add_row(name, f"{value:.1f}")

        # Combine
        from rich.console import Group

        return Panel(Group(cb_table, metrics_table), title="Status")


class SimpleProgressReporter:
    """
    Fallback progress reporter when Rich is not available.

    Uses plain text output.
    """

    def __init__(self) -> None:
        """Initialize reporter."""
        self.modules: Dict[str, str] = {}

    def start(self) -> None:
        """Start reporting (no-op)."""
        print("\n=== Installation Progress ===\n")

    def stop(self) -> None:
        """Stop reporting (no-op)."""
        print("\n=== Installation Complete ===\n")

    def update_module(
        self,
        name: str,
        status: str,
        progress: int = 0,
        duration: Optional[float] = None,
    ) -> None:
        """Update module status."""
        prev_status = self.modules.get(name)

        # Only print on status change
        if prev_status != status:
            status_icons = {
                "waiting": "⏳",
                "running": "🔄",
                "success": "✅",
                "failed": "❌",
            }
            icon = status_icons.get(status, "❓")

            duration_str = f" ({duration:.1f}s)" if duration else ""
            print(f"{icon} {name}: {status}{duration_str}")

            self.modules[name] = status

    def update_circuit_breaker(
        self, name: str, state: str, failure_count: int = 0, failures: Optional[int] = None
    ) -> None:
        """Update circuit breaker (no-op for simple reporter)."""
        pass

    def update_metric(self, name: str, value: float) -> None:
        """Update metric (no-op for simple reporter)."""
        pass
