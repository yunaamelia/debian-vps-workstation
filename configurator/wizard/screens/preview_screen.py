from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.screen import Screen
from textual.widgets import Button, Static


class PreviewScreen(Screen[None]):
    """Preview screen before installation."""

    CSS = """
    PreviewScreen {
        align: center middle;
    }

    #preview-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    #summary {
        margin-bottom: 2;
    }

    #buttons {
        align: center middle;
        margin-top: 2;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        wizard_data = getattr(self.app, "wizard_data", {})
        level = wizard_data.get("experience_level", "beginner")

        with Container(id="preview-container"):
            yield Static("Configuration Preview", id="title")

            summary_text = f"""
[bold]Selected Profile:[/bold] {level.upper()}

[bold]Modules to Install:[/bold]
• System Core
• Security Hardening
• Desktop Environment
"""
            if level == "intermediate":
                summary_text += "• Docker\n• Additional Languages"
            elif level == "advanced":
                summary_text += "• Full Component Suite\n• Custom Networking"

            summary_text += "\n[bold]Ready to proceed?[/bold]"

            yield Static(summary_text, id="summary")

            with Center(id="buttons"):
                yield Button("Start Installation", id="install", variant="success")
                yield Button("Back", id="back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install":
            # Exit with result to signal installation start
            self.app.exit(
                result={
                    "action": "install",
                    "profile": getattr(self.app, "wizard_data", {}).get(
                        "experience_level", "beginner"
                    ),
                }
            )
        elif event.button.id == "back":
            self.app.pop_screen()
