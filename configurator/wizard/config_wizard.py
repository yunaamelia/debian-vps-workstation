from typing import Any, Dict, Optional

from textual.app import App

from configurator.wizard.screens.experience_level import ExperienceLevelScreen
from configurator.wizard.screens.preview_screen import PreviewScreen
from configurator.wizard.screens.welcome import WelcomeScreen


class ConfigWizardApp(App[Optional[Dict[str, Any]]]):
    """Interactive Configuration Wizard Application."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.wizard_data: Dict[str, Any] = {}

    def on_mount(self) -> None:
        self.install_screen(WelcomeScreen(), name="welcome")
        self.install_screen(ExperienceLevelScreen(), name="experience_level")
        self.install_screen(PreviewScreen(), name="preview")
        self.push_screen("welcome")


def run_wizard() -> Optional[Dict[str, Any]]:
    """
    Run the configuration wizard.

    Returns:
        Dictionary containing wizard results (e.g. {'action': 'install', 'profile': 'beginner'})
        or None if cancelled.
    """
    app = ConfigWizardApp()
    result = app.run()
    return result
