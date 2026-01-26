from typing import Any, List, Optional

from rich.prompt import Prompt
from rich.table import Table

from configurator.ui.prompts.base import PromptBase, PromptResult


class SelectPrompt(PromptBase):
    """
    Single selection from list of choices.
    """

    def __init__(self, message: str, choices: List[Any], default: Optional[Any] = None, **kwargs):
        super().__init__(message, default, **kwargs)
        self.choices = choices

    def prompt(self) -> PromptResult:
        """Display selection prompt."""
        # Display choices
        self.console.print(f"\n{self.message}\n")

        table = Table(show_header=False, box=None)

        for i, choice in enumerate(self.choices, 1):
            is_default = choice == self.default
            marker = "→" if is_default else " "
            table.add_row(f"{marker} {i}.", str(choice))

        self.console.print(table)

        # Get selection
        while True:
            try:
                response = Prompt.ask(
                    "\nEnter number",
                    console=self.console,
                    default=str(self.choices.index(self.default) + 1) if self.default else None,
                )

                if response is None:
                    continue
                index = int(response) - 1

                if 0 <= index < len(self.choices):
                    return PromptResult(value=self.choices[index])
                else:
                    self.console.print(
                        self.format_error(
                            f"Please enter a number between 1 and {len(self.choices)}"
                        )
                    )

            except (ValueError, KeyboardInterrupt):
                return PromptResult(value=None, cancelled=True)
