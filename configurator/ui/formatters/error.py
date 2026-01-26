from typing import List, Optional

from rich.console import Console
from rich.panel import Panel

from configurator.exceptions import ConfiguratorError


class ErrorFormatter:
    """
    Format error messages with rich styling.

    Features:
    - Color-coded severity
    - WHAT/WHY/HOW structure
    - Code context highlighting
    - Actionable suggestions
    - Documentation links
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console(stderr=True)

    def format_error(self, error: Exception, show_traceback: bool = False) -> None:
        """
        Format and display error message.

        Args:
            error: Exception to format
            show_traceback: Show full Python traceback
        """
        if isinstance(error, ConfiguratorError):
            self._format_configurator_error(error)
        else:
            self._format_generic_error(error, show_traceback)

    def _format_configurator_error(self, error: ConfiguratorError) -> None:
        """Format ConfiguratorError with WHAT/WHY/HOW structure."""
        # Build error panel
        content = []

        # WHAT
        content.append(f"[bold red]❌ {error.what}[/bold red]")
        content.append("")

        # WHY
        if error.why:
            content.append("[yellow]Why this happened:[/yellow]")
            content.append(error.why)
            content.append("")

        # HOW
        if error.how:
            content.append("[green]How to fix:[/green]")
            # Split multi-line how instructions
            for line in error.how.split("\n"):
                if line.strip():
                    content.append(f"  {line.strip()}")
            content.append("")

        # DOCS
        if error.docs_link:
            content.append(f"[blue]📘 Documentation:[/blue] {error.docs_link}")

        # Display in panel
        self.console.print()
        self.console.print(
            Panel(
                "\n".join(content),
                title="[bold red]Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        self.console.print()

    def _format_generic_error(self, error: Exception, show_traceback: bool) -> None:
        """Format generic Python exception."""
        error_type = type(error).__name__
        error_msg = str(error)

        if show_traceback:
            import traceback

            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

            self.console.print()
            self.console.print(
                Panel(
                    f"[bold red]{error_type}: {error_msg}[/bold red]\n\n{tb}",
                    title="[bold red]Exception[/bold red]",
                    border_style="red",
                )
            )
        else:
            self.console.print()
            self.console.print(f"[bold red]❌ {error_type}:[/bold red] {error_msg}")
            self.console.print("[dim]Run with --verbose for full traceback[/dim]")

        self.console.print()

    def format_with_suggestions(self, error: Exception, suggestions: List[str]) -> None:
        """Format error with actionable suggestions."""
        self.format_error(error)

        if suggestions:
            self.console.print("[bold cyan]💡 Suggestions:[/bold cyan]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  {i}. {suggestion}")
            self.console.print()
