from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class ExperienceLevelCard(Static):
    """Card widget for experience level."""

    def __init__(
        self,
        level: str,
        title: str,
        description: str,
        features: list[str],
        time: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.level = level
        self.title = title
        self.description = description
        self.features = features
        self.time = time

    def compose(self) -> ComposeResult:
        icon_map = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}

        content = f"""
{icon_map.get(self.level, "⚪")} {self.title}

{self.description}

What's included:
"""
        for feature in self.features:
            content += f"\n  • {feature}"

        content += f"\n\n⏱  Estimated time: {self.time}"

        yield Static(content, classes="card-content")
        yield Button(f"Select {self.title}", id=f"select-{self.level}", variant="primary")


class ExperienceLevelScreen(Screen[None]):
    """Experience level selection screen."""

    CSS = """
    ExperienceLevelScreen {
        align: center middle;
    }

    #level-container {
        width: 100%;
        height: auto;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    #cards {
        width: 100%;
        height: auto;
    }

    ExperienceLevelCard {
        width: 1fr;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }

    .card-content {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="level-container"):
            yield Static("Select Your Experience Level", id="title")

            with Horizontal(id="cards"):
                yield ExperienceLevelCard(
                    level="beginner",
                    title="Beginner",
                    description="Safe defaults with essential tools",
                    features=[
                        "Desktop environment",
                        "Python + VS Code",
                        "Git basics",
                        "Security essentials",
                    ],
                    time="~30 minutes",
                )

                yield ExperienceLevelCard(
                    level="intermediate",
                    title="Intermediate",
                    description="More tools and customization",
                    features=[
                        "Multiple languages",
                        "Docker containers",
                        "Database tools",
                        "Advanced editors",
                    ],
                    time="~45 minutes",
                )

                yield ExperienceLevelCard(
                    level="advanced",
                    title="Advanced",
                    description="Full control and all features",
                    features=[
                        "Custom module selection",
                        "Advanced configuration",
                        "Networking tools",
                        "DevOps utilities",
                    ],
                    time="~60 minutes",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle level selection."""
        if not event.button.id:
            return

        if event.button.id.startswith("select-"):
            level = event.button.id.replace("select-", "")

            # Store selection in app
            from typing import Any, cast

            app = cast(Any, self.app)
            if not hasattr(app, "wizard_data"):
                app.wizard_data = {}
            app.wizard_data["experience_level"] = level

            # Navigate based on level
            if level == "advanced":
                # Go to custom module selection
                # self.app.push_screen("module_selection")
                self.app.notify("Custom module selection not implemented yet available in preview")
                self.app.push_screen("preview")
            else:
                # Load preset profile and go to preview
                self.app.push_screen("preview")
