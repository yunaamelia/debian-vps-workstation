from pathlib import Path
from unittest.mock import MagicMock, patch

from configurator.core.hooks import HooksManager, HookType


def test_manager_init():
    manager = HooksManager()
    assert manager._hooks
    assert HookType.PRE_INSTALL in manager._hooks


def test_register_hook():
    manager = HooksManager()
    mock_handler = MagicMock()
    mock_handler.__name__ = "mock_handler"

    manager.register(HookType.PRE_INSTALL, mock_handler, name="test_hook")

    assert len(manager.get_hooks(HookType.PRE_INSTALL)) == 1
    assert manager.get_hooks(HookType.PRE_INSTALL)[0].name == "test_hook"


def test_execute_hooks():
    manager = HooksManager()
    mock_handler = MagicMock()
    mock_handler.__name__ = "mock_handler"

    manager.register(HookType.PRE_INSTALL, mock_handler)
    manager.execute(HookType.PRE_INSTALL)

    mock_handler.assert_called_once()


def test_execute_hooks_failure():
    manager = HooksManager()
    mock_handler = MagicMock(side_effect=Exception("Hook failed"))
    mock_handler.__name__ = "mock_handler"

    manager.register(HookType.PRE_INSTALL, mock_handler)
    # Should not raise exception
    success = manager.execute(HookType.PRE_INSTALL)

    assert success is False
    mock_handler.assert_called_once()


@patch("configurator.core.hooks.importlib.util.spec_from_file_location")
@patch("configurator.core.hooks.importlib.util.module_from_spec")
def test_register_python_hook(mock_module_from_spec, mock_spec_from_file):
    manager = HooksManager()
    script_path = Path("/tmp/hooks/10-pre_install-test.py")

    # Mock module
    mock_module = MagicMock()
    mock_module.run = MagicMock()
    mock_module.HOOK_TYPE = "pre_install"
    mock_module.PRIORITY = 20

    mock_spec = MagicMock()
    mock_spec.loader = MagicMock()
    mock_spec_from_file.return_value = mock_spec
    mock_module_from_spec.return_value = mock_module

    manager._register_python_hook(script_path)

    hooks = manager.get_hooks(HookType.PRE_INSTALL)
    assert len(hooks) == 1
    assert hooks[0].name == f"python:{script_path.name}"
    assert hooks[0].priority == 20


def test_module_specific_hooks():
    manager = HooksManager()
    mock_handler_all = MagicMock()
    mock_handler_system = MagicMock()

    manager.register(HookType.PRE_MODULE, mock_handler_all, name="all")
    manager.register(HookType.PRE_MODULE, mock_handler_system, name="system", module_name="system")

    # Run for 'system' module
    manager.execute(HookType.PRE_MODULE, module_name="system")
    assert mock_handler_all.call_count == 1
    assert mock_handler_system.call_count == 1

    # Run for 'other' module
    mock_handler_all.reset_mock()
    mock_handler_system.reset_mock()

    manager.execute(HookType.PRE_MODULE, module_name="other")
    assert mock_handler_all.call_count == 1
    assert mock_handler_system.call_count == 0
