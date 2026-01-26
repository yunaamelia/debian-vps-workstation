from functools import wraps
from typing import Any, Callable, List, Union

from .events import HookEvent, HookPriority


def hook(events: Union[HookEvent, List[HookEvent]], priority: HookPriority = HookPriority.NORMAL):
    """
    Decorator to register a function as a hook.

    Args:
        events: Single event or list of events to trigger hook
        priority: Execution priority
    """

    def decorator(func: Callable):
        # Cast to Any to allow dynamic attribute assignment
        f: Any = func
        if not hasattr(f, "_hook_events"):
            f._hook_events = []

        _events = events if isinstance(events, list) else [events]
        for event in _events:
            if event not in f._hook_events:
                f._hook_events.append(event)

        f._hook_priority = priority

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Copy attributes to wrapper
        w: Any = wrapper
        w._hook_events = f._hook_events
        w._hook_priority = f._hook_priority

        return wrapper

    return decorator
