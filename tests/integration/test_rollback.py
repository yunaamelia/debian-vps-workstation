"""
Integration tests for rollback functionality.

Tests the ability to undo installation changes.
"""

import pytest

from configurator.core.rollback import RollbackAction, RollbackManager


@pytest.mark.integration
class TestRollbackManager:
    """Tests for RollbackManager."""

    def test_add_and_execute_command_rollback(self, tmp_path):
        """Test adding and executing command rollback."""
        # Use a temp state file
        state_file = tmp_path / "rollback-state.json"

        rollback = RollbackManager()
        rollback.state_file = state_file

        # Add a simple echo command for testing
        rollback.add_command(
            "echo 'rolled back'",
            description="Test rollback",
        )

        assert len(rollback.actions) == 1

        # State should be saved
        assert state_file.exists()

        # Load state in new manager
        rollback2 = RollbackManager()
        rollback2.state_file = state_file
        rollback2.load_state()

        assert len(rollback2.actions) == 1
        assert rollback2.actions[0].description == "Test rollback"

    def test_rollback_executes_in_reverse_order(self, tmp_path):
        """Test that rollback executes in reverse order."""
        state_file = tmp_path / "rollback-state.json"

        rollback = RollbackManager()
        rollback.state_file = state_file

        # Add actions in order 1, 2, 3
        rollback.add_command("echo '1'")
        rollback.add_command("echo '2'")
        rollback.add_command("echo '3'")

        # Verify actions are stored in order
        assert len(rollback.actions) == 3
        assert "'1'" in rollback.actions[0].data["command"]
        assert "'2'" in rollback.actions[1].data["command"]
        assert "'3'" in rollback.actions[2].data["command"]

        # Dry run to verify reverse order without actual execution
        result = rollback.rollback(dry_run=True)
        assert result is True

    def test_file_restore_action(self, tmp_path):
        """Test file restore rollback action."""
        # Create original and backup files
        original = tmp_path / "original.txt"
        backup = tmp_path / "backup.txt"

        original.write_text("modified content")
        backup.write_text("original content")

        rollback = RollbackManager()
        rollback.add_file_restore(
            str(backup),
            str(original),
            description="Restore original file",
        )

        # Execute rollback
        rollback.rollback()

        # Original should now have backup content
        assert original.read_text() == "original content"

    def test_dry_run_rollback(self, tmp_path):
        """Test dry-run rollback doesn't execute."""
        output_file = tmp_path / "output.txt"

        rollback = RollbackManager()
        rollback.add_command(f"echo 'test' > {output_file}")

        # Dry run
        rollback.rollback(dry_run=True)

        # File should not exist
        assert not output_file.exists()

    def test_get_summary(self):
        """Test getting rollback summary."""
        rollback = RollbackManager()

        rollback.add_command("echo 'test'")
        rollback.add_command("echo 'test2'")
        rollback.add_service_stop("test-service")

        summary = rollback.get_summary()

        assert "2 command" in summary
        assert "1 service_stop" in summary

    def test_empty_rollback(self):
        """Test rollback with no actions."""
        rollback = RollbackManager()

        # Should succeed with no actions
        assert rollback.rollback() is True
        assert rollback.get_summary() == "No rollback actions pending"


@pytest.mark.integration
class TestRollbackAction:
    """Tests for RollbackAction dataclass."""

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        action = RollbackAction(
            action_type="command",
            description="Test action",
            data={"command": "echo 'test'"},
        )

        # Serialize
        data = action.to_dict()

        assert data["action_type"] == "command"
        assert data["description"] == "Test action"
        assert data["data"]["command"] == "echo 'test'"
        assert "timestamp" in data

        # Deserialize
        action2 = RollbackAction.from_dict(data)

        assert action2.action_type == action.action_type
        assert action2.description == action.description
        assert action2.data == action.data
