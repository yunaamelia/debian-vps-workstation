import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from .events import HookContext, HookEvent, HookPriority


class HooksManager:
    """Manages registration and execution of hooks."""

    def __init__(self) -> None:
        # Dict[HookEvent, List[Tuple[priority_value, callback]]]
        self.hooks: Dict[HookEvent, List[Tuple[int, Callable[[HookContext], None]]]] = {
            event: [] for event in HookEvent
        }
        self.logger = logging.getLogger(__name__)

    def register(
        self,
        event: HookEvent,
        callback: Callable[[HookContext], None],
        priority: HookPriority = HookPriority.NORMAL,
    ) -> None:
        """Register a callback for an event."""
        if event not in self.hooks:
            self.hooks[event] = []

        self.hooks[event].append((priority.value, callback))
        # Sort by priority (asc)
        self.hooks[event].sort(key=lambda x: x[0])
        self.logger.debug(f"Registered hook for {event.name} with priority {priority.name}")

    def register_from_decorator(self, func: Callable[..., Any]) -> None:
        """Register a decorated function."""
        if not hasattr(func, "_hook_events"):
            return

        priority = getattr(func, "_hook_priority", HookPriority.NORMAL)

        for event in func._hook_events:
            self.register(event, func, priority)

    def execute(
        self,
        event: HookEvent,
        context: Optional[HookContext] = None,
        **kwargs: Any,
    ) -> None:
        """
        Execute all hooks for an event.

        Args:
            event: The event to trigger
            context: Optional pre-built context
            **kwargs: Data to build context if not provided
        """
        if event not in self.hooks:
            return

        if context is None:
            module_name = kwargs.get("module_name")
            context = HookContext(event=event, module_name=module_name, data=kwargs)

        # Ensure context event matches
        context.event = event

        self.logger.debug(f"Executing hooks for {event.name}")

        for _, callback in self.hooks[event]:
            try:
                callback(context)
            except Exception as e:
                self.logger.error(f"Error in hook {callback.__name__}: {e}")
                # Continue execution
