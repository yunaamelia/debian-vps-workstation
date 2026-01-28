import threading
from datetime import datetime
from typing import Any, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from configurator.core.reporter.base import ReporterInterface


class RichProgressReporter(ReporterInterface):
    """
    Enhanced progress reporter using Rich library.
    Thread-safe implementation for parallel module execution.

    Features:
    - Multi-line progress bars (one per module)
    - Spinner animations (configurable)
    - Time elapsed/remaining
    - Status messages
    - Thread-safe updates
    - Dry-run mode support
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        refresh_per_second: float = 4.0,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize the Rich progress reporter.

        Args:
            console: Rich console instance (creates new if None)
            refresh_per_second: Screen refresh rate (4.0 = 250ms, optimized for performance)
            dry_run: If True, disables animations for faster output
        """
        self.console = console or Console()
        self.refresh_per_second = refresh_per_second
        self.dry_run = dry_run

        self.start_time: Optional[datetime] = None
        self.current_phase: Optional[str] = None
        self.results: Dict[str, bool] = {}

        # Create Rich Progress instance
        # In dry-run mode, use a static spinner (no animation overhead)
        spinner = SpinnerColumn() if not dry_run else TextColumn("→")

        self.progress = Progress(
            spinner,
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("[dim]{task.fields[status]}[/dim]"),
            console=self.console,
            expand=False,
            # Disable auto-refresh in dry-run mode
            auto_refresh=not dry_run,
        )

        # Thread-safe task management
        self.tasks: Dict[str, TaskID] = {}
        self.task_lock = threading.Lock()

        # Live display
        self.live: Optional[Live] = None

    def start(self, title: str = "Installation") -> None:
        """Display startup banner and start live display."""
        self.start_time = datetime.now()

        banner = Panel(
            f"[bold cyan]🚀 {title}[/bold cyan]\nTransform your VPS into a coding powerhouse!",
            style="cyan",
            expand=False,
        )

        self.console.print(banner)
        self.console.print()

        # Start live display
        # Note: We use the progress object directly in Live
        self.live = Live(
            self.progress,
            console=self.console,
            refresh_per_second=self.refresh_per_second,
            transient=False,  # Keep the progress bars after completion
        )
        self.live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self.live:
            self.live.stop()

    def start_phase(self, name: str, total_steps: int = 100) -> None:
        """
        Start new installation phase/module.
        Thread-safe.
        """
        with self.task_lock:
            # Update current phase for sequential fallback
            self.current_phase = name

            if name not in self.tasks:
                task_id = self.progress.add_task(
                    f"[bold]{name}[/bold]", total=total_steps or 100, status="Starting..."
                )
                self.tasks[name] = task_id
            else:
                # Reset existing task if re-running
                self.progress.update(
                    self.tasks[name],
                    completed=0,
                    total=total_steps or 100,
                    status="Restarting...",
                    visible=True,
                )

    def update(self, message: str, success: bool = True, module: Optional[str] = None) -> None:
        """
        Update progress status.
        Args:
            message: Status message
            success: True for success, False for error
            module: Module name. if None, uses current_phase (for sequential compatibility).
        """
        target_module = module or self.current_phase

        if target_module and target_module in self.tasks:
            task_id = self.tasks[target_module]
            # Assumes intermediate updates don't need checkmarks unless explicit success/fail context
            # But the interface says success=True by default.
            # We'll just update the status text.

            self.progress.update(task_id, status=message)

            # If explicit failure
            if not success:
                self.progress.update(task_id, status=f"❌ {message}")

    def update_progress(
        self,
        percent: int,
        current: Optional[int] = None,
        total: Optional[int] = None,
        module: Optional[str] = None,
    ) -> None:
        """Update progress percentage."""
        target_module = module or self.current_phase

        if target_module and target_module in self.tasks:
            task_id = self.tasks[target_module]
            if current is not None and total is not None:
                self.progress.update(task_id, completed=current, total=total)
            else:
                self.progress.update(task_id, completed=percent, total=100)

    def complete_phase(self, success: bool = True, module: Optional[str] = None) -> None:
        """Mark current phase as complete."""
        target_module = module or self.current_phase

        if target_module and target_module in self.tasks:
            task_id = self.tasks[target_module]
            icon = "✅" if success else "❌"
            msg = "Done" if success else "Failed"
            self.progress.update(task_id, completed=100, status=f"{icon} {msg}")

    def show_summary(self, results: Dict[str, bool]) -> None:
        """Display installation summary."""
        if self.live:
            self.live.stop()

        self.console.print()
        table = Table(title="Installation Summary")
        table.add_column("Module", style="cyan")
        table.add_column("Status", justify="center")

        for module, success in results.items():
            status = "[green]SUCCESS[/green]" if success else "[red]FAILED[/red]"
            table.add_row(module, status)

        self.console.print(table)

    def error(self, message: str) -> None:
        self.console.print(f"[bold red]ERROR:[/bold red] {message}")

    def warning(self, message: str) -> None:
        self.console.print(f"[bold yellow]WARNING:[/bold yellow] {message}")

    def info(self, message: str) -> None:
        self.console.print(f"[blue]INFO:[/blue] {message}")

    def show_next_steps(
        self, reboot_required: bool = False, rdp_port: int = 3389, **kwargs: Any
    ) -> None:
        """Display next steps after installation."""
        self.console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        if reboot_required:
            self.console.print(
                "  • [bold yellow]Reboot your system[/bold yellow] to apply all changes."
            )
            self.console.print("    Run: [bold]sudo reboot[/bold]")

        self.console.print(
            "  • [green]Verify[/green] installation with: [bold]vps-configurator verify[/bold]"
        )
        self.console.print(
            "  • [green]Monitor[/green] system with: [bold]vps-configurator dashboard[/bold]"
        )
        self.console.print(f"  • Connect via RDP on port: [bold]{rdp_port}[/bold]")
