"""
Progress reporting with Rich library.
"""

from datetime import datetime
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class ProgressReporter:
    """
    Beautiful progress reporting using Rich library.

    Provides:
    - Phase-based progress tracking
    - Spinner for ongoing tasks
    - Summary table at completion
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize reporter.

        Args:
            console: Rich console instance (created if not provided)
        """
        self.console = console or Console()
        self.phases: List[Dict] = []
        self.current_phase: Optional[str] = None
        self.current_steps: int = 0
        self.total_steps: int = 0
        self.start_time: Optional[datetime] = None
        self.results: Dict[str, bool] = {}

    def start(self, title: str = "Debian VPS Workstation Configurator"):
        """
        Display startup banner.

        Args:
            title: Title to display
        """
        self.start_time = datetime.now()

        banner = """
╔════════════════════════════════════════════════════════╗
║   🚀 Debian 13 VPS Workstation Configurator            ║
║   Transform your VPS into a coding powerhouse!          ║
╚════════════════════════════════════════════════════════╝
        """.strip()

        self.console.print(Panel(banner, style="bold cyan"))
        self.console.print()

    def start_phase(self, name: str, total_steps: int = 0):
        """
        Start a new installation phase.

        Args:
            name: Phase name (e.g., "Installing Docker")
            total_steps: Total number of steps in this phase
        """
        self.current_phase = name
        self.current_steps = 0
        self.total_steps = total_steps

        phase_info = {
            "name": name,
            "start_time": datetime.now(),
            "steps": [],
        }
        self.phases.append(phase_info)

        self.console.print(f"\n[bold blue]▶ {name}[/bold blue]")

    def update(self, message: str, success: bool = True):
        """
        Update current progress.

        Args:
            message: Status message
            success: Whether this step succeeded
        """
        self.current_steps += 1

        if self.phases:
            self.phases[-1]["steps"].append(
                {
                    "message": message,
                    "success": success,
                    "time": datetime.now(),
                }
            )

        if self.total_steps > 0:
            percentage = (self.current_steps / self.total_steps) * 100
            prefix = f"  [{self.current_steps}/{self.total_steps}] ({percentage:.0f}%)"
        else:
            prefix = f"  [{self.current_steps}]"

        status = "✓" if success else "✗"
        style = "green" if success else "red"

        self.console.print(f"{prefix} [{style}]{status}[/{style}] {message}")

    def complete_phase(self, success: bool = True):
        """
        Mark current phase as complete.

        Args:
            success: Whether the phase completed successfully
        """
        if not self.current_phase:
            return

        # Calculate elapsed time
        if self.phases:
            start = self.phases[-1]["start_time"]
            elapsed = datetime.now() - start
            elapsed_str = f" ({elapsed.total_seconds():.1f}s)"
        else:
            elapsed_str = ""

        self.results[self.current_phase] = success

        if success:
            self.console.print(
                f"[bold green]✓ {self.current_phase} complete{elapsed_str}[/bold green]"
            )
        else:
            self.console.print(f"[bold red]✗ {self.current_phase} failed{elapsed_str}[/bold red]")

        self.current_phase = None

    def show_spinner(self, message: str):
        """
        Show a spinner for long-running tasks.

        Args:
            message: Message to display next to spinner

        Returns:
            Context manager for the spinner
        """
        return self.console.status(f"[bold blue]{message}[/bold blue]", spinner="dots")

    def show_summary(self):
        """Display installation summary table."""
        if not self.results:
            return

        # Calculate total time
        if self.start_time:
            total_time = datetime.now() - self.start_time
            total_str = f"{total_time.total_seconds() / 60:.1f} minutes"
        else:
            total_str = "Unknown"

        # Build summary table
        table = Table(title="Installation Summary", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        success_count = 0
        for component, success in self.results.items():
            status = "[green]✅ Installed[/green]" if success else "[red]❌ Failed[/red]"
            table.add_row(component, status)
            if success:
                success_count += 1

        self.console.print()
        self.console.print(table)
        self.console.print()

        # Overall status
        total = len(self.results)
        if success_count == total:
            self.console.print(
                f"[bold green]🎉 All {total} components installed successfully![/bold green]"
            )
        else:
            failed = total - success_count
            self.console.print(
                f"[bold yellow]⚠️  {success_count}/{total} components installed. "
                f"{failed} failed.[/bold yellow]"
            )

        self.console.print(f"[dim]Total time: {total_str}[/dim]")

    def show_next_steps(self, rdp_port: int = 3389, public_ip: Optional[str] = None):
        """
        Display next steps after installation.

        Args:
            rdp_port: RDP port number
            public_ip: Server's public IP
        """
        ip_display = public_ip or "YOUR_SERVER_IP"

        next_steps = f"""
[bold cyan]🎉 Installation Complete! Here's what to do next:[/bold cyan]

[bold]1. Connect via Remote Desktop:[/bold]
   • Windows: Open Remote Desktop Connection
   • Mac: Use Microsoft Remote Desktop from App Store
   • Linux: Use Remmina or rdesktop

   [bold]Connection details:[/bold]
   • Address: {ip_display}:{rdp_port}
   • Username: Your Linux username
   • Password: Your Linux password

[bold]2. Verify installation:[/bold]
   $ vps-configurator verify

[bold]3. View system status:[/bold]
   $ sudo systemctl status xrdp
   $ docker --version
   $ python3 --version
   $ node --version

[bold]4. Read documentation:[/bold]
   • Quick Start: https://github.com/youruser/debian-vps-configurator#quickstart
   • Troubleshooting: https://github.com/youruser/debian-vps-configurator/issues

[dim]Logs are saved to: /var/log/debian-vps-configurator/install.log[/dim]
        """

        self.console.print(Panel(next_steps, title="Next Steps", border_style="green"))

    def error(self, message: str):
        """
        Display an error message.

        Args:
            message: Error message
        """
        from rich.markup import escape

        self.console.print(f"[bold red]❌ Error: {escape(message)}[/bold red]")

    def warning(self, message: str):
        """
        Display a warning message.

        Args:
            message: Warning message
        """
        from rich.markup import escape

        self.console.print(f"[bold yellow]⚠️  Warning: {escape(message)}[/bold yellow]")

    def info(self, message: str):
        """
        Display an info message.

        Args:
            message: Info message
        """
        from rich.markup import escape

        self.console.print(f"[blue]ℹ️  {escape(message)}[/blue]")

    def success(self, message: str):
        """
        Display a success message.

        Args:
            message: Success message
        """
        from rich.markup import escape

        self.console.print(f"[bold green]✅ {escape(message)}[/bold green]")
