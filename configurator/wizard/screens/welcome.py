from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.screen import Screen
from textual.widgets import Button, Static


class WelcomeScreen(Screen[None]):
    """Welcome screen for configuration wizard."""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    #welcome-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #features {
        margin-top: 1;
        margin-bottom: 2;
    }

    #buttons {
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="welcome-container"):
            yield Static(
                Text("🚀 Debian VPS Workstation Configurator", justify="center"), id="title"
            )

            yield Static(
                """
Welcome to the interactive configuration wizard!

This wizard will guide you through:
  ✓ Selecting your experience level
  ✓ Choosing modules to install
  ✓ Customizing configuration
  ✓ Previewing changes before installation

Features you'll get:
  • Remote desktop environment (XRDP + XFCE)
  • Development tools (Python, Node.js, Docker, etc.)
  • Security hardening (UFW, Fail2ban, SSH keys)
  • IDE integration (VS Code, Cursor, Neovim)
  • And much more!

Estimated time: 5-10 minutes
                """.strip(),
                id="features",
            )

            with Center(id="buttons"):
                yield Button("Let's Start!", id="continue", variant="primary")
                yield Button("Exit", id="exit", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "continue":
            self.app.push_screen("experience_level")
        elif event.button.id == "exit":
            self.app.exit()
