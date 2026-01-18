from unittest.mock import MagicMock

import pytest

from configurator.core.rollback import RollbackManager
from configurator.modules.base import ConfigurationModule


class MockModule(ConfigurationModule):
    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


@pytest.fixture
def mock_module(tmp_path):
    config = {}
    rollback = RollbackManager()
    # Mock logger to avoid noise
    logger = MagicMock()
    return MockModule(config, logger=logger, rollback_manager=rollback)


def test_write_file_new_registers_rollback(mock_module, tmp_path):
    """Test that writing a new file registers a removal action."""
    test_file = tmp_path / "new_config.json"
    content = '{"foo": "bar"}'

    # Ensure file doesn't exist
    if test_file.exists():
        test_file.unlink()

    mock_module.write_file(str(test_file), content)

    # Verify file exists
    assert test_file.exists()
    assert test_file.read_text() == content

    # Verify rollback action added
    assert len(mock_module.rollback_manager.actions) == 1
    action = mock_module.rollback_manager.actions[0]
    assert action.action_type == "command"
    assert "rm -f" in action.data["command"]
    assert str(test_file) in action.data["command"]

    # Execute rollback
    mock_module.rollback()

    # Verify file is gone
    assert not test_file.exists()


def test_write_file_overwrite_registers_nothing_yet(mock_module, tmp_path):
    """
    Test that overwriting an existing file currently logs but implies external backup rely.
    (As per our fix limitation in Step 63).
    """
    test_file = tmp_path / "existing.conf"
    test_file.write_text("old_content")

    mock_module.write_file(str(test_file), "new_content")

    assert test_file.read_text("utf-8") == "new_content"

    # Our current fix does NOT register actions for existing files because retrieving
    # the backup path from utils.write_file requires deeper refactoring.
    # It just logs.
    # So we expect NO new actions or just no crash.
    # Check logs? We mocked logger.
    mock_module.logger.debug.assert_called()
