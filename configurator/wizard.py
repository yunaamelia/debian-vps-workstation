"""
Interactive setup wizard using Textual TUI.
"""

from typing import Any, Dict, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, Markdown, Select


class WizardScreen(Screen):
    """Base screen for wizard steps."""

    def compose_header(self, title: str) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label(f"Step: {title}", classes="step-title")


class WelcomeScreen(WizardScreen):
    def compose(self) -> ComposeResult:
        yield from self.compose_header("Welcome")
        yield Vertical(
            Markdown(
                """
# 🚀 Debian VPS Configurator

Transform your VPS into a coding powerhouse!

This wizard will guide you through the setup process.
It handles:
- **System Hardening** (Firewall, SSH, Fail2ban)
- **Dev Tools** (Docker, Git, Python, Node, Go)
- **Productivity** (VS Code, Neovim, Zsh)
- **Remote Access** (XRDP, WireGuard)

*Press 'Start' to begin configuration.*
            """
            ),
            Button("Start Configuration", variant="primary", id="start"),
            classes="content",
        )
        yield Footer()

    @on(Button.Pressed, "#start")
    def action_start(self):
        self.app.push_screen(ProfileScreen())


class ProfileScreen(WizardScreen):
    def compose(self) -> ComposeResult:
        yield from self.compose_header("Select Profile")
        yield Label("Choose your experience level and base configuration:", classes="prompt")

        yield Container(
            Button(
                "🟢 Beginner\nSafe defaults, essential tools (Python, Node, Docker)",
                id="beginner",
                classes="profile-btn",
            ),
            Button(
                "🟡 Intermediate\nMore control. Adds Go, Rust, Neovim, Caddy",
                id="intermediate",
                classes="profile-btn",
            ),
            Button(
                "🔴 Advanced\nFull control. Manual selection of all components",
                id="advanced",
                classes="profile-btn",
            ),
            classes="profile-container",
        )
        yield Footer()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        profile = event.button.id
        if profile in ["beginner", "intermediate", "advanced"]:
            self.app.config_data["profile"] = profile
            self.app.push_screen(BasicConfigScreen())


class BasicConfigScreen(WizardScreen):
    def compose(self) -> ComposeResult:
        yield from self.compose_header("System Settings")

        yield Vertical(
            Label("Hostname:", classes="label"),
            Input(placeholder="dev-workstation", id="hostname"),
            Label("Timezone:", classes="label"),
            Select(
                [
                    ("UTC", "UTC"),
                    ("America/New_York", "America/New_York"),
                    ("America/Los_Angeles", "America/Los_Angeles"),
                    ("Europe/London", "Europe/London"),
                    ("Europe/Berlin", "Europe/Berlin"),
                    ("Asia/Singapore", "Asia/Singapore"),
                    ("Asia/Tokyo", "Asia/Tokyo"),
                ],
                prompt="Select Timezone",
                id="timezone",
            ),
            Button("Next", variant="primary", id="next"),
            classes="form-container",
        )
        yield Footer()

    @on(Button.Pressed, "#next")
    def on_next(self):
        hostname = self.query_one("#hostname", Input).value or "dev-workstation"
        timezone = self.query_one("#timezone", Select).value or "UTC"

        if "system" not in self.app.config_data:
            self.app.config_data["system"] = {}

        self.app.config_data["system"]["hostname"] = hostname
        self.app.config_data["system"]["timezone"] = timezone

        profile = self.app.config_data.get("profile", "beginner")
        if profile == "beginner":
            self.app.push_screen(ReviewScreen())
        else:
            self.app.push_screen(AdvancedOptionsScreen())


class AdvancedOptionsScreen(WizardScreen):
    def compose(self) -> ComposeResult:
        yield from self.compose_header("Select Components")

        yield Grid(
            Label("[bold]Languages[/bold]", classes="section-header"),
            Checkbox("Golang", id="golang", value=True),
            Checkbox("Rust", id="rust", value=True),
            Checkbox("Java", id="java", value=False),
            Checkbox("PHP", id="php", value=False),
            Label("[bold]Editors[/bold]", classes="section-header"),
            Checkbox("Cursor IDE", id="cursor", value=True),
            Checkbox("Neovim", id="neovim", value=True),
            Label("[bold]Networking[/bold]", classes="section-header"),
            Checkbox("Caddy Server", id="caddy", value=True),
            Checkbox("WireGuard VPN", id="wireguard", value=False),
            classes="grid-container",
        )
        yield Button("Review Configuration", variant="primary", id="review")
        yield Footer()

    @on(Button.Pressed, "#review")
    def on_review(self):
        # Collect checkboxes
        if "languages" not in self.app.config_data:
            self.app.config_data["languages"] = {}
        if "tools" not in self.app.config_data:
            self.app.config_data["tools"] = {"editors": {}}
        if "networking" not in self.app.config_data:
            self.app.config_data["networking"] = {}

        for lang in ["golang", "rust", "java", "php"]:
            if self.query_one(f"#{lang}", Checkbox).value:
                self.app.config_data["languages"][lang] = {"enabled": True}

        for tool in ["cursor", "neovim"]:
            if self.query_one(f"#{tool}", Checkbox).value:
                self.app.config_data["tools"]["editors"][tool] = {"enabled": True}

        for net in ["caddy", "wireguard"]:
            if self.query_one(f"#{net}", Checkbox).value:
                self.app.config_data["networking"][net] = {"enabled": True}

        self.app.push_screen(ReviewScreen())


class ReviewScreen(WizardScreen):
    def compose(self) -> ComposeResult:
        yield from self.compose_header("Review & Confirm")

        # Build summary
        cfg = self.app.config_data
        summary = """
## Configuration Summary

**Profile**: {cfg.get('profile', 'Unknown').title()}
**Hostname**: {cfg.get('system', {}).get('hostname')}
**Timezone**: {cfg.get('system', {}).get('timezone')}

### Components to Install:
- System Hardening & Monitoring
- Docker & Git
- Python & Node.js
"""
        # Add dynamic components
        langs = [k for k, v in cfg.get("languages", {}).items() if v.get("enabled")]
        if langs:
            summary += f"- Languages: {', '.join(langs)}\n"

        editors = [
            k for k, v in cfg.get("tools", {}).get("editors", {}).items() if v.get("enabled")
        ]
        if editors:
            summary += f"- Editors: {', '.join(editors)}\n"

        nets = [k for k, v in cfg.get("networking", {}).items() if v.get("enabled")]
        if nets:
            summary += f"- Network: {', '.join(nets)}\n"

        yield Markdown(summary, classes="review-content")

        yield Horizontal(
            Button("Cancel", variant="error", id="cancel"),
            Button("🚀 INSTALL NOW", variant="success", id="install"),
            classes="actions",
        )
        yield Footer()

    @on(Button.Pressed, "#install")
    def action_install(self):
        self.app.confirmed = True
        self.app.exit(self.app.config_data)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self):
        self.app.exit(None)


class VPSWizardApp(App):
    CSS = """
    Screen {
        align: center middle;
        background: $surface-darken-1;
    }

    .step-title {
        text-align: center;
        text-style: bold;
        background: $primary;
        color: $text;
        width: 100%;
        padding: 1;
    }

    .content {
        width: 60%;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }

    .prompt {
        padding: 1;
        text-align: center;
    }

    .profile-container {
        layout: vertical;
        align: center middle;
        height: auto;
    }

    .profile-btn {
        width: 50;
        margin: 1;
        height: 3;
    }

    .form-container {
        width: 50%;
        height: auto;
        border: solid $accent;
        padding: 2;
    }

    .label {
        margin-top: 1;
    }

    .grid-container {
        grid-size: 2;
        grid-gutter: 1 2;
        width: 80%;
        height: 60%;
        border: solid $success;
        padding: 1;
        overflow-y: auto;
    }

    .section-header {
        column-span: 2;
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    .review-content {
        width: 70%;
        height: 60%;
        border: double $warning;
        padding: 1;
        background: $surface;
    }

    .actions {
        width: 70%;
        align: center middle;
        margin-top: 1;
    }

    #install {
        margin-left: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.config_data: Dict[str, Any] = {}
        self.confirmed = False

    def on_mount(self):
        self.push_screen(WelcomeScreen())


class InteractiveWizard:
    def __init__(self, console=None, logger=None):
        pass

    def run(self) -> Optional[Dict[str, Any]]:
        app = VPSWizardApp()
        result = app.run()
        return result
