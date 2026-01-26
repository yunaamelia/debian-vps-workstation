"""
Plugin loader and manager.

Handles discovery and loading of plugins from various locations.
"""

import importlib.util
import logging
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from configurator.plugins.base import PluginBase, PluginError, PluginInfo


@dataclass
class LoadedPlugin:
    """A loaded plugin instance."""

    info: PluginInfo
    plugin_class: Type[PluginBase]
    source_path: Path
    enabled: bool = True


class PluginLoader:
    """
    Discovers and loads plugins from directories.
    """

    # Default plugin directories
    PLUGIN_DIRS = [
        Path("/etc/debian-vps-configurator/plugins"),
        Path.home() / ".config/debian-vps-configurator/plugins",
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize plugin loader.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._extra_dirs: List[Path] = []

    def add_plugin_dir(self, directory: Path) -> None:
        """
        Add a directory to search for plugins.

        Args:
            directory: Path to plugin directory
        """
        if directory not in self._extra_dirs:
            self._extra_dirs.append(directory)

    def discover(self) -> List[LoadedPlugin]:
        """
        Discover all available plugins.

        Returns:
            List of discovered plugins
        """
        plugins: List[LoadedPlugin] = []
        seen_names: set[str] = set()

        all_dirs = self.PLUGIN_DIRS + self._extra_dirs

        for plugin_dir in all_dirs:
            if not plugin_dir.exists():
                continue

            # Look for plugin packages (directories with __init__.py)
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    plugin = self._load_plugin_package(item)
                    if plugin and plugin.info.name not in seen_names:
                        plugins.append(plugin)
                        seen_names.add(plugin.info.name)

                # Look for single-file plugins
                elif item.suffix == ".py" and not item.name.startswith("_"):
                    plugin = self._load_plugin_file(item)
                    if plugin and plugin.info.name not in seen_names:
                        plugins.append(plugin)
                        seen_names.add(plugin.info.name)

        self.logger.info(f"Discovered {len(plugins)} plugins")
        return plugins

    def _load_plugin_package(self, package_path: Path) -> Optional[LoadedPlugin]:
        """Load a plugin from a package directory."""
        try:
            init_file = package_path / "__init__.py"
            return self._load_from_file(init_file, package_path.name)
        except Exception as e:
            self.logger.warning(f"Failed to load plugin package {package_path}: {e}")
            return None

    def _load_plugin_file(self, file_path: Path) -> Optional[LoadedPlugin]:
        """Load a plugin from a single file."""
        try:
            return self._load_from_file(file_path, file_path.stem)
        except Exception as e:
            self.logger.warning(f"Failed to load plugin file {file_path}: {e}")
            return None

    def _load_from_file(self, file_path: Path, module_name: str) -> Optional[LoadedPlugin]:
        """Load a plugin module from a file."""
        spec = importlib.util.spec_from_file_location(
            f"configurator.plugins.external.{module_name}",
            file_path,
        )
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Find the plugin class
        plugin_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, PluginBase) and obj is not PluginBase:
                plugin_class = obj
                break

        if plugin_class is None:
            self.logger.debug(f"No PluginBase subclass found in {file_path}")
            return None

        return LoadedPlugin(
            info=plugin_class.plugin_info,
            plugin_class=plugin_class,
            source_path=file_path,
            enabled=True,
        )


class PluginManager:
    """
    Manages plugin lifecycle and registration.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize plugin manager.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.loader = PluginLoader(logger)
        self._plugins: Dict[str, LoadedPlugin] = {}
        self._instances: Dict[str, PluginBase] = {}

    def load_plugins(self) -> int:
        """
        Load all available plugins.

        Returns:
            Number of plugins loaded
        """
        discovered = self.loader.discover()

        for plugin in discovered:
            if plugin.info.name not in self._plugins:
                self._plugins[plugin.info.name] = plugin
                self.logger.info(f"Loaded plugin: {plugin.info.name} v{plugin.info.version}")

        return len(self._plugins)

    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            LoadedPlugin or None
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[LoadedPlugin]:
        """
        Get all loaded plugins.

        Returns:
            List of all loaded plugins
        """
        return list(self._plugins.values())

    def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was enabled
        """
        if name in self._plugins:
            self._plugins[name].enabled = True
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was disabled
        """
        if name in self._plugins:
            self._plugins[name].enabled = False
            return True
        return False

    def instantiate(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Optional[PluginBase]:
        """
        Create an instance of a plugin.

        Args:
            name: Plugin name
            config: Configuration to pass to plugin

        Returns:
            Plugin instance or None
        """
        plugin = self._plugins.get(name)
        if plugin is None or not plugin.enabled:
            return None

        try:
            instance = plugin.plugin_class(config)
            instance.on_load()
            self._instances[name] = instance
            return instance
        except Exception as e:
            raise PluginError(
                f"Failed to instantiate plugin: {e}",
                plugin_name=name,
                cause=e,
            )

    def get_instance(self, name: str) -> Optional[PluginBase]:
        """
        Get an existing plugin instance.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._instances.get(name)

    def get_enabled_plugins(self) -> List[LoadedPlugin]:
        """
        Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return [p for p in self._plugins.values() if p.enabled]

    def unload_all(self) -> None:
        """Unload all plugins."""
        for instance in self._instances.values():
            try:
                instance.on_unload()
            except Exception as e:
                self.logger.warning(f"Error unloading plugin: {e}")

        self._instances.clear()
        self._plugins.clear()

    def install_plugin(self, source: str) -> bool:
        """
        Install a plugin from a source (URL, path, zip).

        Args:
            source: URL or path to plugin

        Returns:
            True if successful
        """
        try:
            # Determine install directory (user config dir)
            install_dir = Path.home() / ".config/debian-vps-configurator/plugins"
            install_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Installing plugin from {source}...")

            if source.startswith("http") or source.startswith("git"):
                return self._install_from_remote(source, install_dir)
            else:
                return self._install_from_local(Path(source), install_dir)

        except Exception as e:
            self.logger.error(f"Failed to install plugin: {e}")
            return False

    def _install_from_remote(self, url: str, target_dir: Path) -> bool:
        """Install from remote URL."""
        if url.endswith(".git") or "github.com" in url:
            # Git clone
            name = url.split("/")[-1].replace(".git", "")
            dest = target_dir / name

            if dest.exists():
                self.logger.warning(f"Plugin directory {dest} already exists. Updating...")
                subprocess.run(["git", "-C", str(dest), "pull"], check=True)
            else:
                subprocess.run(["git", "clone", url, str(dest)], check=True)
            return True

        elif url.endswith(".zip") or url.endswith(".tar.gz"):
            # Download and extract
            import urllib.request

            with tempfile.TemporaryDirectory() as temp_dir:
                local_file = Path(temp_dir) / Path(url).name
                self.logger.info(f"Downloading {url}...")
                urllib.request.urlretrieve(url, local_file)
                return self._install_archive(local_file, target_dir)

        else:
            self.logger.error(f"Unsupported remote source: {url}")
            return False

    def _install_from_local(self, path: Path, target_dir: Path) -> bool:
        """Install from local path."""
        path = Path(path).resolve()

        if not path.exists():
            self.logger.error(f"Source path {path} does not exist")
            return False

        if path.is_dir():
            # Copy directory
            dest = target_dir / path.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(path, dest)
            return True

        elif path.suffix in [".zip", ".tar.gz", ".tgz"]:
            return self._install_archive(path, target_dir)

        elif path.suffix == ".py":
            # Copy single file
            dest = target_dir / path.name
            shutil.copy2(path, dest)
            return True

        else:
            self.logger.error(f"Unsupported local source: {path}")
            return False

    def _install_archive(self, archive_path: Path, target_dir: Path) -> bool:
        """Install from archive file."""
        try:
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    # check for common prefix
                    first_file = zip_ref.namelist()[0]
                    if "/" in first_file:
                        root_folder = first_file.split("/")[0]
                        target_path = target_dir / root_folder
                        if target_path.exists():
                            shutil.rmtree(target_path)

                    self._safe_extract(zip_ref, target_dir)
            elif archive_path.suffix in [".tar.gz", ".tgz"]:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(target_dir)

            self.logger.info(f"Extracted {archive_path.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to extract archive: {e}")
            return False

    def _safe_extract(self, zip_ref: zipfile.ZipFile, target_dir: Path) -> None:
        """
        Extract zip file safely preventing Zip Slip vulnerability.

        Args:
            zip_ref: ZipFile object
            target_dir: Destination directory

        Raises:
            PluginError: If malicious path is detected
        """
        target_path = Path(target_dir).resolve()

        for member in zip_ref.namelist():
            # Construct the full path
            member_path = (target_path / member).resolve()

            # Check if the member path is within the target directory
            if not str(member_path).startswith(str(target_path)):
                self.logger.critical(f"Blocked Zip Slip attempt: {member}")
                raise PluginError(
                    f"Malicious path in archive: {member}", plugin_name="unknown", cause=None
                )

        # If all checks pass, extract
        zip_ref.extractall(target_dir)
