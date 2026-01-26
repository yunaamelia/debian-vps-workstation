"""
Decorators for declarative dependency management.

Provides decorators that can be applied to module classes to define
their dependencies, conflicts, and execution priority.
"""

from typing import Any, Callable, List, Optional

from configurator.dependencies.models import ModuleDependency
from configurator.dependencies.registry import DependencyRegistry


def module(
    name: Optional[str] = None,
    priority: int = 50,
    depends_on: Optional[List[str]] = None,
    optional_deps: Optional[List[str]] = None,
    conflicts_with: Optional[List[str]] = None,
    force_sequential: bool = False,
) -> Callable[[type[Any]], type[Any]]:
    """
    Decorator to define module metadata.

    Sets module attributes and registers dependency information in the global registry.

    Args:
        name: Module name (defaults to class name without "Module" suffix, lowercased)
        priority: Execution priority (0-100, higher runs first within dependency level)
        depends_on: List of required module dependencies
        optional_deps: List of optional module dependencies
        conflicts_with: List of modules this conflicts with
        force_sequential: If True, forces sequential execution (no parallel)

    Returns:
        Decorator function

    Example:
        @module(name="docker", priority=50, depends_on=["system"])
        class DockerModule(ConfigurationModule):
            pass
    """

    def decorator(cls: type[Any]) -> type[Any]:
        # Set attributes on class
        module_name = name or cls.__name__.replace("Module", "").lower()
        cls._module_name = module_name
        cls.priority = priority
        cls.depends_on = depends_on or []
        cls.optional_deps = optional_deps or []
        cls.conflicts_with = conflicts_with or []
        cls.force_sequential = force_sequential

        # Register in global registry
        dependency = ModuleDependency(
            module_name=module_name,
            depends_on=cls.depends_on,
            optional_deps=cls.optional_deps,
            conflicts_with=cls.conflicts_with,
            priority=priority,
            force_sequential=force_sequential,
        )
        DependencyRegistry.register(dependency)

        return cls

    return decorator


def depends_on(*dependencies: str) -> Callable[[type[Any]], type[Any]]:
    """
    Shorthand decorator for defining dependencies.

    Equivalent to @module(depends_on=[...])

    Args:
        *dependencies: Variable number of dependency module names

    Returns:
        Decorator function

    Example:
        @depends_on("system", "security")
        class DockerModule(ConfigurationModule):
            pass
    """
    return module(depends_on=list(dependencies))


def conflicts_with(*modules: str) -> Callable[[type[Any]], type[Any]]:
    """
    Shorthand decorator for defining conflicts.

    Equivalent to @module(conflicts_with=[...])

    Args:
        *modules: Variable number of conflicting module names

    Returns:
        Decorator function

    Example:
        @conflicts_with("podman")
        class DockerModule(ConfigurationModule):
            pass
    """
    return module(conflicts_with=list(modules))
