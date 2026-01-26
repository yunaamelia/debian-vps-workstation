from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ReporterInterface(ABC):
    """Abstract base class for progress reporters."""

    @abstractmethod
    def start(self, title: str = "Installation") -> None:
        """Display startup banner."""
        pass

    @abstractmethod
    def start_phase(self, name: str, total_steps: int = 0) -> None:
        """Start a new installation phase."""
        pass

    @abstractmethod
    def update(self, message: str, success: bool = True, module: Optional[str] = None) -> None:
        """Update current progress with message."""
        pass

    @abstractmethod
    def update_progress(
        self,
        percent: int,
        current: Optional[int] = None,
        total: Optional[int] = None,
        module: Optional[str] = None,
    ) -> None:
        """Update progress percentage."""
        pass

    @abstractmethod
    def complete_phase(self, success: bool = True, module: Optional[str] = None) -> None:
        """Mark current phase as complete."""
        pass

    @abstractmethod
    def show_summary(self, results: Dict[str, bool]) -> None:
        """Display installation summary."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Display error message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Display warning message."""
        pass

    @abstractmethod
    def info(self, message: str) -> None:
        """Display info message."""
        pass

    @abstractmethod
    def show_next_steps(self, reboot_required: bool = False, **kwargs: Any) -> None:
        """Display next steps after installation."""
        pass
