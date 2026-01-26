from typing import Callable, Optional

from rich.console import Console

from configurator.ui.prompts.base import PromptBase, PromptResult


class InputPrompt(PromptBase):
    """Generic text input prompt."""

    def __init__(
        self,
        message: str,
        default: Optional[str] = None,
        console: Optional[Console] = None,
        validator: Optional[Callable[[str], bool]] = None,
        password: bool = False,
    ) -> None:
        super().__init__(message, default, console)
        self.validator_func = validator
        self.password = password

    def validate(self, value: str) -> bool:
        if self.validator_func:
            return self.validator_func(value)
        return True

    def prompt(self) -> PromptResult:
        while True:
            try:
                prompt_text = f"[bold]{self.message}[/bold]"
                if self.default:
                    prompt_text += f" [dim]({self.default})[/dim]"

                resp = self.console.input(f"{prompt_text}: ", password=self.password)

                if not resp and self.default is not None:
                    resp = self.default

                if self.validate(resp):
                    return PromptResult(value=resp)

                self.console.print(self.format_error("Invalid input"))

            except KeyboardInterrupt:
                return PromptResult(value=None, cancelled=True)


class PasswordPrompt(InputPrompt):
    """Secure password input prompt."""

    def __init__(
        self, message: str, console: Optional[Console] = None, confirm: bool = False
    ) -> None:
        super().__init__(message, None, console, password=True)
        self.confirm = confirm

    def prompt(self) -> PromptResult:
        result = super().prompt()
        if result.cancelled or not self.confirm:
            return result

        # Confirmation
        confirm_result = super().prompt()  # Re-ask
        if confirm_result.cancelled:
            return confirm_result

        if result.value != confirm_result.value:
            self.console.print(self.format_error("Passwords do not match"))
            # Recursively try again? Or just fail? Let's recursively try again
            return self.prompt()

        return result


class NumberPrompt(InputPrompt):
    """Numeric input prompt."""

    def __init__(
        self,
        message: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        console: Optional[Console] = None,
    ) -> None:
        default_str = str(default) if default is not None else None
        super().__init__(message, default_str, console)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: str) -> bool:
        try:
            num = int(value)
            if self.min_value is not None and num < self.min_value:
                return False
            if self.max_value is not None and num > self.max_value:
                return False
            return True
        except ValueError:
            return False

    def prompt(self) -> PromptResult:
        res = super().prompt()
        if res.cancelled:
            return res
        return PromptResult(value=int(res.value))
