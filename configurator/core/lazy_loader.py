"""
Lazy loading utility for optimizing CLI startup time.
"""

import importlib
import importlib.util
import threading
import time
import types
from typing import Any, Optional


class LazyLoader:
    """
    Proxy object that lazily imports a module or object within a module.

    Acts as a proxy, loading the actual object only when an attribute is accessed
    or the object is called.
    """

    def __init__(self, module_name: str, import_object: Optional[str] = None):
        """
        Initialize the lazy loader.

        Args:
            module_name: The name of the module to import.
            import_object: Optional name of an object (class/function) inside the module.
                           If None, the module itself is returned.
        """
        self._module_name = module_name
        self._import_object = import_object
        self._module: Optional[types.ModuleType] = None
        self._object: Any = None
        self._lock = threading.RLock()
        self._import_time = 0.0

    def _load(self) -> Any:
        """Force load the underlying object."""
        if self._module is not None:
            return self._object if self._import_object else self._module

        with self._lock:
            if self._module is not None:
                return self._object if self._import_object else self._module

            start_time = time.perf_counter()
            self._module = importlib.import_module(self._module_name)

            if self._import_object:
                self._object = getattr(self._module, self._import_object)

            self._import_time = time.perf_counter() - start_time

            return self._object if self._import_object else self._module

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying object."""
        obj = self._load()
        return getattr(obj, name)

    def __call__(self, *args, **kwargs) -> Any:
        """Proxy call to the underlying object."""
        obj = self._load()
        return obj(*args, **kwargs)

    def is_loaded(self) -> bool:
        """Check if the object has been loaded."""
        return self._module is not None

    def get_import_time(self) -> float:
        """Get the time taken to import the module/object."""
        return self._import_time

    def preload(self) -> None:
        """Force preload of the object."""
        self._load()


class LazyModule:
    """
    Helper for lazily registering modules in the module registry.
    """

    def __init__(self, module_path: str, class_name: str):
        self.module_path = module_path
        self.class_name = class_name
        self._loader = LazyLoader(module_path, class_name)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._loader, name)

    def __call__(self, *args, **kwargs) -> Any:
        return self._loader(*args, **kwargs)

    @classmethod
    def register_lazy(cls, registry: dict, key: str, module_path: str, class_name: str):
        """
        Register a lazy module in a dictionary registry.

        Args:
            registry: The dictionary to register into.
            key: The key to use in the registry.
            module_path: The dotted python path to the module.
            class_name: The name of the class to load.
        """
        registry[key] = cls(module_path, class_name)


def lazy_import(name: str, package: Optional[str] = None) -> LazyLoader:
    """
    Helper to create a LazyLoader (similar to importlib.import_module usage).
    """
    if package:
        if not name.startswith("."):
            name = "." + name
        name = importlib.util.resolve_name(name, package)

    return LazyLoader(name)
