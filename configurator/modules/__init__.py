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
    from configurator.modules.base import ConfigurationModule
    from configurator.modules.caddy import CaddyModule
    from configurator.modules.cursor import CursorModule
    from configurator.modules.databases import DatabasesModule
    from configurator.modules.desktop import DesktopModule
    from configurator.modules.devops import DevOpsModule
    from configurator.modules.docker import DockerModule
    from configurator.modules.git import GitModule
    from configurator.modules.golang import GolangModule
    from configurator.modules.java import JavaModule
    from configurator.modules.neovim import NeovimModule
    from configurator.modules.netdata import NetdataModule
    from configurator.modules.nodejs import NodeJSModule
    from configurator.modules.php import PHPModule
    from configurator.modules.python import PythonModule
    from configurator.modules.rbac import RBACModule
    from configurator.modules.rust import RustModule
    from configurator.modules.security import SecurityModule
    from configurator.modules.system import SystemModule
    from configurator.modules.utilities import UtilitiesModule
    from configurator.modules.vscode import VSCodeModule
    from configurator.modules.wireguard import WireGuardModule
