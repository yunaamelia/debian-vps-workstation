from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass
class DryRunChange:
    type: str  # package, file, service, firewall, user, command
    action: str  # install, create, modify, start, stop, add, delete, exec
    target: str  # package name, file path, service name, etc.
    details: Optional[Dict[str, Any]] = None


class DryRunManager:
    """
    Manages recording of planned changes during a dry run.

    Acts as a centralized registry for all operations that *would* be performed.
    Supports generating both plain text and rich terminal reports (with masking).

    Attributes:
        changes: List of recorded DryRunChange objects.
        _enabled: Boolean flag indicating if recording is active.
    """

    def __init__(self):
        self.changes: List[DryRunChange] = []
        self._enabled = False

    def enable(self):
        """Enable dry-run recording mode."""
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        """Check if dry-run mode is active."""
        return self._enabled

    def record(
        self, change_type: str, action: str, target: str, details: Optional[Dict[str, Any]] = None
    ):
        """
        Record a planned system change.

        Args:
            change_type: Category (package, file, service, etc.)
            action: Action performed (install, write, start, etc.)
            target: The target object (package name, file path, etc.)
            details: Optional dictionary of extra info (e.g. file diffs)
        """
        if not self._enabled:
            return

        change = DryRunChange(type=change_type, action=action, target=target, details=details)
        self.changes.append(change)

    def record_package_install(self, packages: List[str]):
        """Record package installation."""
        for pkg in packages:
            self.record("package", "install", pkg)

    def record_file_write(self, path: str, content: str = "", diff: str = ""):
        """Record file creation or modification."""
        self.record("file", "write", path, {"content_len": len(content), "diff": diff})

    def record_service_action(self, service: str, action: str):
        """Record service state change."""
        self.record("service", action, service)

    def record_firewall_rule(self, rule: str):
        """Record firewall rule addition."""
        self.record("firewall", "add", rule)

    def record_command(self, command: str):
        """Record arbitrary shell command execution."""
        self.record("command", "exec", command)

    def _mask_sensitive_data(self, content: str) -> str:
        """Mask sensitive values in content."""
        import re

        if not content:
            return ""

        patterns = [
            (r'(password|secret|key|token|pass)["\s:=]+([^\s\n"]+)', r'\1: "***MASKED***"'),
            (r'(api[_-]?key)["\s:=]+([^\s\n"]+)', r'\1: "***MASKED***"'),
        ]

        masked = content
        for pattern, replacement in patterns:
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        return masked

    def generate_report(self) -> str:
        """Generate a text report of planned changes."""
        report = []
        report.append("DRY-RUN REPORT")
        report.append("=" * 50)

        # Group by type
        by_type = {}
        for c in self.changes:
            if c.type not in by_type:
                by_type[c.type] = []
            by_type[c.type].append(c)

        for type_name, changes in by_type.items():
            report.append(f"\n{type_name.upper()}S ({len(changes)}):")
            for c in changes:
                target = self._mask_sensitive_data(c.target)
                report.append(f"  {c.action.upper()} {target}")
                if c.details and c.details.get("diff"):
                    masked_diff = self._mask_sensitive_data(c.details["diff"])
                    report.append("    Diff preview available")
                    report.append(
                        masked_diff
                    )  # Also include diff in text report if desired, or just note it

        report.append("\n" + "=" * 50)
        return "\n".join(report)

    def print_report(self):
        """Print a beautiful report using Rich."""
        console = Console()

        console.print("\n[bold cyan]🔍 DRY-RUN REPORT[/bold cyan]")
        console.print("[dim]The following changes would be performed:[/dim]\n")

        # Packages
        pkgs = [c for c in self.changes if c.type == "package"]
        if pkgs:
            table = Table(title=f"Packages to Install ({len(pkgs)})", show_header=False, box=None)
            table.add_column("Package")
            for c in pkgs:
                table.add_row(f"[green]+ {c.target}[/green]")
            console.print(table)
            console.print()

        # Files
        files = [c for c in self.changes if c.type == "file"]
        if files:
            console.print(f"[bold]Files to Modify ({len(files)}):[/bold]")
            for c in files:
                console.print(f"  [yellow]✎ {c.target}[/yellow]")
                if c.details and c.details.get("diff"):
                    masked_diff = self._mask_sensitive_data(c.details["diff"])
                    console.print(Panel(masked_diff, title="Dif", border_style="dim"))
            console.print()

        # Services
        services = [c for c in self.changes if c.type == "service"]
        if services:
            table = Table(title="Service Actions", show_header=True)
            table.add_column("Service")
            table.add_column("Action")
            for c in services:
                color = "green" if c.action in ["start", "enable", "restart"] else "yellow"
                table.add_row(c.target, f"[{color}]{c.action.upper()}[/{color}]")
            console.print(table)
            console.print()

        # Firewall
        fw = [c for c in self.changes if c.type == "firewall"]
        if fw:
            console.print("[bold]Firewall Rules:[/bold]")
            for c in fw:
                console.print(f"  [green]+ {c.target}[/green]")
            console.print()

        # Other commands
        cmds = [c for c in self.changes if c.type == "command"]
        if cmds:
            console.print(f"[dim]Total other commands to run: {len(cmds)}[/dim]")
            for c in cmds:
                masked_cmd = self._mask_sensitive_data(c.target)
                console.print(f"  [dim]> {masked_cmd}[/dim]")

        console.print("\n[yellow]No changes were made to the system.[/yellow]")
