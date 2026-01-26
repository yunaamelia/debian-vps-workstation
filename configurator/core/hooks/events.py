from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, unique
from typing import Any, Dict, Optional


@unique
class HookEvent(Enum):
    """Enumeration of hook events."""

    BEFORE_INSTALLATION = "before_installation"
    AFTER_INSTALLATION = "after_installation"

    BEFORE_MODULE_VALIDATE = "before_module_validate"
    AFTER_MODULE_VALIDATE = "after_module_validate"

    BEFORE_MODULE_CONFIGURE = "before_module_configure"
    AFTER_MODULE_CONFIGURE = "after_module_configure"

    ON_MODULE_ERROR = "on_module_error"
    ON_INSTALLATION_ERROR = "on_installation_error"


@unique
class HookPriority(Enum):
    """Hook execution priority."""

    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100

    def __lt__(self, other: "HookPriority") -> bool:
        return self.value < other.value


@dataclass
class HookContext:
    """Context passed to hook callbacks."""

    event: HookEvent
    module_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
