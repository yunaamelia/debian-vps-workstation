import inspect
from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")


class ContainerError(Exception):
    """Base exception for container errors"""


class ServiceNotFoundError(ContainerError):
    """Raised when a service is not found"""


class CircularDependencyError(ContainerError):
    """Raised when a circular dependency is detected"""


class Container:
    """
    A simple but powerful Dependency Injection (DI) container.

    Manages service registration, resolution, and lifecycle (singleton vs factory).
    Supports:
    - Singleton services (created once, shared)
    - Factory services (created fresh each request)
    - Mocking for tests
    - Circular dependency detection
    - Dynamic keyword arguments during resolution

    Usage:
        container = Container()

        # Register a singleton (lazy instantiation)
        container.singleton('config', lambda: ConfigManager())

        # Register a factory
        container.factory('logger', lambda container: logging.getLogger())

        # Resolve
        config = container.get('config')
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Callable[[], Any]] = {}
        self._factories: Dict[str, Callable[["Container"], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._resolving: set = set()

    def singleton(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register a singleton service.

        The factory will be called only once, upon first resolution.
        The resulting instance is cached and returned for all subsequent requests.

        Args:
            name: Unique identifier for the service.
            factory: Callable that returns the service instance. Can optionally accept 'container' or **kwargs.
        """
        self._singletons[name] = factory

    def factory(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register a factory service.

        The factory will be called every time the service is resolved.

        Args:
            name: Unique identifier for the service.
            factory: Callable that returns a new service instance. Can optionally accept 'container' or **kwargs.
        """
        self._factories[name] = factory

    def mock(self, name: str, instance: Any) -> None:
        """
        Register a pre-instantiated mock for testing.

        This overrides any existing singleton or factory registration for the given name.
        Useful for injecting mocks during unit tests.

        Args:
            name: Service identifier to override.
            instance: The mock object instance.
        """
        self._instances[name] = instance

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._singletons or name in self._factories or name in self._instances

    def get(self, name: str, **kwargs) -> Any:
        """
        Resolve a service by name.

        Args:
            name: Service name
            **kwargs: Arguments to pass to the factory

        Returns:
            The resolved service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        if name in self._instances:
            return self._instances[name]

        if name not in self._singletons and name not in self._factories:
            raise ServiceNotFoundError(f"Service '{name}' not found")

        if name in self._resolving:
            raise CircularDependencyError(f"Circular dependency detected for '{name}'")

        self._resolving.add(name)
        try:
            if name in self._singletons:
                if name not in self._instances:
                    # Singletons don't typically take dynamic kwargs on first creation
                    # as they are shared. We ignore kwargs for singletons key logic
                    # or perhaps raise an error if kwargs are provided?
                    # For simplicity, we just pass them if provided, but typically
                    # singletons should be parameterless or depend on other services.
                    factory = self._singletons[name]
                    if self._is_factory_expecting_container(factory):
                        self._instances[name] = factory(self, **kwargs)  # type: ignore
                    else:
                        self._instances[name] = factory(**kwargs)
                return self._instances[name]

            if name in self._factories:
                factory_func = self._factories[name]
                if self._is_factory_expecting_container(factory_func):
                    return factory_func(self, **kwargs)
                else:
                    return factory_func(**kwargs)  # type: ignore

        finally:
            self._resolving.remove(name)

    def make(self, name: str, **kwargs) -> Any:
        """Alias for get() to match common DI patterns."""
        return self.get(name, **kwargs)

    def _is_factory_expecting_container(self, func: Callable) -> bool:
        """Check if the factory function expects an argument (the container)."""
        try:
            sig = inspect.signature(func)
            return len(sig.parameters) > 0
        except ValueError:
            return False
