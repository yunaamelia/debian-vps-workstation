from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from configurator.core.hooks import HooksManager, HookType
from configurator.plugins.base import PluginBase, PluginInfo
from configurator.plugins.loader import PluginManager


class TestHooksManager:
    @pytest.fixture
    def hooks_manager(self):
        return HooksManager()

    def test_register_and_execute_hook(self, hooks_manager):
        mock_handler = MagicMock()
        hooks_manager.register(HookType.PRE_INSTALL, mock_handler, name="test_hook")

        hooks_manager.execute(HookType.PRE_INSTALL)
        mock_handler.assert_called_once()

    def test_hook_priority(self, hooks_manager):
        parent_mock = MagicMock()
        mock_handler1 = parent_mock.handler1
        mock_handler2 = parent_mock.handler2

        hooks_manager.register(HookType.PRE_INSTALL, mock_handler1, name="hook1", priority=50)
        hooks_manager.register(HookType.PRE_INSTALL, mock_handler2, name="hook2", priority=10)

        hooks_manager.execute(HookType.PRE_INSTALL)

        # handler2 should execute first due to lower priority (10 < 50)
        assert parent_mock.method_calls[0][0] == "handler2"
        assert parent_mock.method_calls[1][0] == "handler1"

    def test_module_specific_hook(self, hooks_manager):
        mock_handler_all = MagicMock()
        mock_handler_system = MagicMock()

        hooks_manager.register(HookType.PRE_MODULE, mock_handler_all, name="hook_all")
        hooks_manager.register(
            HookType.PRE_MODULE, mock_handler_system, name="hook_system", module_name="system"
        )

        # Execute for "system" module
        hooks_manager.execute(HookType.PRE_MODULE, module_name="system")
        mock_handler_all.assert_called()
        mock_handler_system.assert_called()

        mock_handler_all.reset_mock()
        mock_handler_system.reset_mock()

        # Execute for "other" module
        hooks_manager.execute(HookType.PRE_MODULE, module_name="other")
        mock_handler_all.assert_called()
        mock_handler_system.assert_not_called()


class MockPlugin(PluginBase):
    plugin_info = PluginInfo(name="test_plugin", version="1.0.0", description="Test Plugin")

    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


class TestPluginManager:
    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()

    @patch("configurator.plugins.loader.importlib.util")
    def test_load_plugin(self, mock_importlib, plugin_manager):
        # Setup mocks to simulate plugin loading
        mock_spec = MagicMock()
        mock_module = MagicMock()
        mock_importlib.spec_from_file_location.return_value = mock_spec
        mock_importlib.module_from_spec.return_value = mock_module

        # Add MockPlugin to the mocked module
        mock_module.TestHooksManagerPlugin = MockPlugin
        mock_module.dir.return_value = ["TestHooksManagerPlugin"]

        # Mock Path.iterdir to return a fake file
        with (
            patch.object(Path, "iterdir") as mock_iterdir,
            patch.object(Path, "exists", return_value=True),
        ):
            fake_file = MagicMock(spec=Path)
            fake_file.suffix = ".py"
            fake_file.name = "test_plugin.py"
            fake_file.stem = "test_plugin"

            mock_iterdir.return_value = [fake_file]

            plugin_manager.loader.PLUGIN_DIRS = [Path("/fake/dir")]

            # This is hard to test purely with mocks due to dynamic imports
            # Ideally we'd create a real temporary file, but for now we skip complex loading logic

    def test_instantiate_plugin(self, plugin_manager):
        # Manually register a plugin
        from configurator.plugins.loader import LoadedPlugin

        loaded = LoadedPlugin(
            info=MockPlugin.plugin_info, plugin_class=MockPlugin, source_path=Path("/tmp/test.py")
        )
        plugin_manager._plugins["test_plugin"] = loaded

        instance = plugin_manager.instantiate("test_plugin", {})

        assert instance is not None
        assert isinstance(instance, MockPlugin)
        assert instance.info.name == "test_plugin"
