from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.widgets import Footer, Header, Label

from configurator.ui.components import ActivityLog, ModuleCard, OverallProgress, ResourceGauge


class InstallationDashboard(App):
    """Full-screen installation dashboard."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 3;
        grid-rows: auto 1fr 1fr;
        grid-columns: 2fr 1fr;
    }

    #overall-panel {
        grid-column: 1 / 3;
    }

    #modules-panel {
        grid-row: 2;
        grid-column: 1;
        border: solid white;
        height: 100%;
    }

    #resources-panel {
        grid-row: 2;
        grid-column: 2;
        height: 100%;
    }

    #log-panel {
        grid-row: 3;
        grid-column: 1 / 3;
        height: 100%;
    }
    """

    BINDINGS = [
        ("p", "pause", "Pause"),
        ("s", "skip_current", "Skip"),
        ("l", "view_logs", "Logs"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="overall-panel"):
            yield OverallProgress(id="overall-widget")

        with ScrollableContainer(id="modules-panel"):
            yield Label("Modules", classes="panel-header")
            # Modules added dynamically

        with Container(id="resources-panel"):
            yield ResourceGauge(id="resource-widget")

        with Container(id="log-panel"):
            yield Label("Activity Log", classes="panel-header")
            yield ActivityLog(id="log-widget")

        yield Footer()

    def add_module(self, module_name: str):
        """Add module card to dashboard."""
        card = ModuleCard(id=f"card-{module_name}")
        card.module_name = module_name

        try:
            panel = self.query_one("#modules-panel")
            panel.mount(card)
        except Exception:
            pass

    def update_module(
        self, module_name: str, status: Optional[str] = None, progress: Optional[int] = None
    ):
        """Update module status."""
        try:
            card = self.query_one(f"#card-{module_name}", ModuleCard)
            if status:
                card.status = status
            if progress is not None:
                card.progress = progress
        except Exception:
            pass

    def update_overall(self, percent: int):
        """Update overall progress."""
        try:
            widget = self.query_one("#overall-widget", OverallProgress)
            widget.update_progress(percent)
        except Exception:
            pass

    def log_to_widget(self, message: str):
        """Add log message."""
        try:
            widget = self.query_one("#log-widget", ActivityLog)
            widget.add_line(message)
        except Exception:
            pass

    def action_quit(self):
        """Quit the application."""
        self.exit()
