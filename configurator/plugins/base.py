"""
Base class for plugins.

Plugins are similar to modules but loaded from external locations,
allowing users to extend functionality without modifying core code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from configurator.modules.base import ConfigurationModule


@dataclass
class PluginInfo:
    """Metadata about a plugin."""

    name: str
    version: str
    description: str
    author: str = "Unknown"
    website: str = ""
    requires: List[str] = field(default_factory=list)  # Required modules
    provides: List[str] = field(default_factory=list)  # What this plugin provides
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "website": self.website,
            "requires": self.requires,
            "provides": self.provides,
            "tags": self.tags,
        }


class PluginBase(ConfigurationModule, ABC):
    """
    Base class for plugins.

    Plugins extend ConfigurationModule with additional metadata
    and lifecycle methods for plugin-specific behavior.
    """

    # Plugin metadata (subclasses should override)
    plugin_info: PluginInfo = PluginInfo(
        name="Base Plugin",
        version="0.0.0",
        description="Base plugin class",
    )

    def __init__(self, config: Dict[str, Any], *args: Any, **kwargs: Any):
        """
        Initialize plugin.

        Args:
            config: Plugin configuration
        """
        super().__init__(config, *args, **kwargs)
        self._plugin_loaded = False

    @property
    def info(self) -> PluginInfo:
        """Get plugin info."""
        return self.plugin_info

    def on_load(self) -> None:
        """
        Called when plugin is loaded.

        Override to perform initialization when plugin is discovered.
        """
        self._plugin_loaded = True

    def on_unload(self) -> None:
        """
        Called when plugin is unloaded.

        Override to perform cleanup when plugin is removed.
        """
        self._plugin_loaded = False

    def check_requirements(self) -> bool:
        """
        Check if plugin requirements are met.

        Returns:
            True if all required modules are available
        """
        # This would check if required modules are installed
        # For now, just return True
        return True

    @abstractmethod
    def validate(self) -> bool:
        """Validate plugin can run."""

    @abstractmethod
    def configure(self) -> bool:
        """Run plugin configuration."""

    @abstractmethod
    def verify(self) -> bool:
        """Verify plugin completed successfully."""


class PluginError(Exception):
    """Exception raised by plugins."""

    def __init__(
        self,
        message: str,
        plugin_name: str = "",
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.plugin_name = plugin_name
        self.cause = cause
        super().__init__(f"[{plugin_name}] {message}")
