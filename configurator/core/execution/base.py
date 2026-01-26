from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ExecutionContext:
    """Context for module execution."""

    module_name: str
    module_instance: Any  # Typed as 'ConfigurationModule' in actual usage, but Any here to avoid circular imports
    config: Dict[str, Any]
    dry_run: bool = False
    force: bool = False
    priority: int = 50
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of module execution."""

    module_name: str
    success: bool
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def status_icon(self) -> str:
        """Get status icon."""
        return "✅" if self.success else "❌"


class ExecutorInterface(ABC):
    """Abstract base class for execution engines."""

    @abstractmethod
    def execute(
        self,
        contexts: List[ExecutionContext],
        callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, ExecutionResult]:
        """
        Execute modules.

        Args:
            contexts: List of execution contexts
            callback: Optional progress callback(module_name, event, data)

        Returns:
            Dict mapping module names to execution results
        """
        pass

    @abstractmethod
    def can_handle(self, contexts: List[ExecutionContext]) -> bool:
        """
        Check if this executor can handle the given contexts.

        Returns:
            True if executor can handle these modules
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get executor name for logging."""
        pass
