from typing import Any

from configurator.ui.prompts.base import PromptBase, PromptResult


class ConfirmPrompt(PromptBase):
    """
    Yes/No confirmation prompt.
    """

    def __init__(self, message: str, default: bool = False, **kwargs: Any) -> None:
        super().__init__(message, default, **kwargs)

    def prompt(self) -> PromptResult:
        """Display confirmation prompt."""
        # Format message with default
        if self.default:
            options = "[Y/n]"
        else:
            options = "[y/N]"

        full_message = f"{self.message} {options}: "

        while True:
            self.console.print(full_message, end="")

            # Using input() is blocking and standard. Textual apps usually shouldn't use input()
            # but this CLI tool might run outside of Textual loop for simple prompts.
            # However, if creating a Wizard, we rely on Textual.
            # This prompt class seems designed for the `cli.py` legacy flow or simple interactions.
            try:
                response = input().strip().lower()
            except (KeyboardInterrupt, EOFError):
                return PromptResult(value=None, cancelled=True)

            # Handle empty (use default)
            if not response:
                return PromptResult(value=self.default)

            # Handle yes/no
            if response in ("y", "yes"):
                return PromptResult(value=True)
            elif response in ("n", "no"):
                return PromptResult(value=False)
            else:
                self.console.print(self.format_error("Please enter 'y' or 'n'"))
