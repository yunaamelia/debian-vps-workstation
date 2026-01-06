"""
Installation modules for the configurator.
"""

"""
Installation modules for the configurator.
"""
from typing import TYPE_CHECKING

from configurator.core.lazy_loader import LazyModule

# Registry of available modules
# Format: 'ClassName': ('module_path', 'ClassName')
_MODULE_REGISTRY = {
    # Base
    "ConfigurationModule": ("configurator.modules.base", "ConfigurationModule"),
    # Core modules
    "SystemModule": ("configurator.modules.system", "SystemModule"),
    "SecurityModule": ("configurator.modules.security", "SecurityModule"),
    "DesktopModule": ("configurator.modules.desktop", "DesktopModule"),
    "RBACModule": ("configurator.modules.rbac", "RBACModule"),
    # Languages
    "PythonModule": ("configurator.modules.python", "PythonModule"),
    "NodeJSModule": ("configurator.modules.nodejs", "NodeJSModule"),
    "GolangModule": ("configurator.modules.golang", "GolangModule"),
    "JavaModule": ("configurator.modules.java", "JavaModule"),
    "PHPModule": ("configurator.modules.php", "PHPModule"),
    "RustModule": ("configurator.modules.rust", "RustModule"),
    # Tools
    "DockerModule": ("configurator.modules.docker", "DockerModule"),
    "GitModule": ("configurator.modules.git", "GitModule"),
    "DatabasesModule": ("configurator.modules.databases", "DatabasesModule"),
    "DevOpsModule": ("configurator.modules.devops", "DevOpsModule"),
    "UtilitiesModule": ("configurator.modules.utilities", "UtilitiesModule"),
    # Editors
    "VSCodeModule": ("configurator.modules.vscode", "VSCodeModule"),
    "CursorModule": ("configurator.modules.cursor", "CursorModule"),
    "NeovimModule": ("configurator.modules.neovim", "NeovimModule"),
    # Networking
    "WireGuardModule": ("configurator.modules.wireguard", "WireGuardModule"),
    "CaddyModule": ("configurator.modules.caddy", "CaddyModule"),
    # Monitoring
    "NetdataModule": ("configurator.modules.netdata", "NetdataModule"),
}

__all__ = list(_MODULE_REGISTRY.keys())


def __getattr__(name):
    """Lazy load modules when accessed."""
    if name in _MODULE_REGISTRY:
        module_path, class_name = _MODULE_REGISTRY[name]
        return LazyModule(module_path, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_module(name: str):
    """
    Get a module class by name (lazy load).

    Args:
        name: The name of the module class to load

    Returns:
        The module class (proxied)
    """
    if name in _MODULE_REGISTRY:
        return globals()[name]  # Triggers __getattr__
    raise ValueError(f"Unknown module: {name}")


# Type hinting support for IDEs
if TYPE_CHECKING:
    pass
