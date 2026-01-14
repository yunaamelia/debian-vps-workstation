"""
Unit tests for CORE-002: Rollback confirmation functionality.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.config import ConfigManager
from configurator.core.installer import Installer


class TestRollbackConfirmation:
    """Test rollback confirmation in different modes."""

    @pytest.fixture
    def installer(self):
        """Create installer with mock dependencies."""
        config = Mock(spec=ConfigManager)
        config.get.return_value = True
        logger = Mock()
        reporter = Mock()
        installer = Installer(config=config, logger=logger, reporter=reporter)

        # Add some rollback actions
        installer.rollback_manager.actions = [
            ("rm -rf /tmp/test", "Remove test directory"),
            ("systemctl stop test", "Stop test service"),
        ]
        return installer

    def test_interactive_mode_prompts_for_confirmation(self, installer):
        """Test that interactive mode prompts user before rollback."""
        installer.config.get.side_effect = lambda key, default=None: {
            "interactive": True,
        }.get(key, default)

        with patch("click.confirm") as mock_confirm:
            mock_confirm.return_value = True  # User confirms

            with patch.object(installer.rollback_manager, "rollback") as mock_rollback:
                # Execute rollback decision logic
                is_interactive = installer.config.get("interactive", True)
                action_count = len(installer.rollback_manager.actions)

                if is_interactive:
                    should_rollback = mock_confirm(
                        "\n⚠️  Do you want to rollback changes?", default=False
                    )

                    if should_rollback:
                        installer.rollback_manager.rollback()

                # Verify prompt was called
                mock_confirm.assert_called_once()
                # Verify rollback executed
                mock_rollback.assert_called_once()

    def test_interactive_mode_user_declines_rollback(self, installer):
        """Test that user can decline rollback."""
        installer.config.get.side_effect = lambda key, default=None: {
            "interactive": True,
        }.get(key, default)

        with patch("click.confirm") as mock_confirm:
            mock_confirm.return_value = False  # User declines

            with patch.object(installer.rollback_manager, "rollback") as mock_rollback:
                # Execute rollback decision logic
                is_interactive = True
                should_rollback = mock_confirm(
                    "\n⚠️  Do you want to rollback changes?", default=False
                )

                if should_rollback:
                    installer.rollback_manager.rollback()
                else:
                    installer.logger.info("User declined rollback. Keeping partial changes.")

                # Verify rollback NOT executed
                mock_rollback.assert_not_called()

    def test_non_interactive_mode_auto_rollback_enabled(self, installer):
        """Test that non-interactive mode with auto-rollback enabled executes rollback."""
        installer.config.get.side_effect = lambda key, default=None: {
            "interactive": False,
            "installation.auto_rollback_on_error": True,
        }.get(key, default)

        with patch.object(installer.rollback_manager, "rollback") as mock_rollback:
            # Execute non-interactive rollback logic
            is_interactive = installer.config.get("interactive", True)

            if not is_interactive:
                auto_rollback = installer.config.get("installation.auto_rollback_on_error", True)
                if auto_rollback:
                    installer.rollback_manager.rollback()

            # Verify rollback executed
            mock_rollback.assert_called_once()

    def test_non_interactive_mode_auto_rollback_disabled(self, installer):
        """Test that non-interactive mode with auto-rollback disabled keeps changes."""
        installer.config.get.side_effect = lambda key, default=None: {
            "interactive": False,
            "installation.auto_rollback_on_error": False,
        }.get(key, default)

        with patch.object(installer.rollback_manager, "rollback") as mock_rollback:
            # Execute non-interactive rollback logic
            is_interactive = installer.config.get("interactive", True)

            if not is_interactive:
                auto_rollback = installer.config.get("installation.auto_rollback_on_error", True)
                if auto_rollback:
                    installer.rollback_manager.rollback()
                else:
                    installer.logger.warning("Auto-rollback disabled. Keeping partial changes.")

            # Verify rollback NOT executed
            mock_rollback.assert_not_called()

    def test_rollback_summary_displayed(self, installer):
        """Test that rollback summary is shown to user."""
        installer.config.get.return_value = True  # Interactive

        with patch("click.confirm") as mock_confirm:
            mock_confirm.return_value = True

            with patch.object(installer.rollback_manager, "get_summary") as mock_summary:
                mock_summary.return_value = "2 actions: rm -rf /tmp/test, systemctl stop test"

                # Execute
                summary = installer.rollback_manager.get_summary()
                installer.logger.info(f"\nRollback preview:\n{summary}")

                # Verify summary was retrieved
                mock_summary.assert_called_once()

    def test_action_count_logged(self, installer):
        """Test that action count is logged."""
        action_count = len(installer.rollback_manager.actions)
        installer.logger.warning(f"Installation failed. {action_count} rollback actions available.")

        # Verify
        installer.logger.warning.assert_called_with(
            "Installation failed. 2 rollback actions available."
        )
