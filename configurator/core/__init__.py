"""Core functionality for the configurator."""

from typing import Any

# Lazy imports to avoid circular dependencies
# Import these directly when needed:
# from configurator.core.validator import SystemValidator
# from configurator.core.installer import Installer
# from configurator.core.reporter import ProgressReporter
# from configurator.core.rollback import RollbackManager

__all__ = [
    "SystemValidator",
    "Installer",
    "ProgressReporter",
    "RollbackManager",
]


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular imports."""
    if name == "SystemValidator":
        from configurator.core.validator import SystemValidator

        return SystemValidator
    elif name == "Installer":
        from configurator.core.installer import Installer

        return Installer
    elif name == "ProgressReporter":
        from configurator.core.reporter import ProgressReporter

        return ProgressReporter
    elif name == "RollbackManager":
        from configurator.core.rollback import RollbackManager

        return RollbackManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
