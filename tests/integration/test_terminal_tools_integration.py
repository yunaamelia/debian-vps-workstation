"""
Integration tests for Terminal Tools Module.

These tests verify the full flow of terminal tools installation.
Note: Some tests require root privileges for actual installation.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTerminalToolsIntegration:
    """Integration tests for terminal tools module."""

    @pytest.fixture
    def temp_home(self):
        """Create a temporary home directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_module(self, temp_home):
        """Create a module with mocked external dependencies."""
        from configurator.core.dryrun import DryRunManager
        from configurator.modules.terminal_tools import TerminalToolsModule

        config = MagicMock()
        config.get.return_value = {}
        logger = MagicMock()
        dry_run_manager = DryRunManager()
        dry_run_manager.enable()

        with patch.object(
            TerminalToolsModule,
            "STATE_FILE",
            temp_home / ".configurator" / "state.json",
        ):
            with patch.object(TerminalToolsModule, "_get_home_dir", return_value=temp_home):
                module = TerminalToolsModule(
                    config=config,
                    logger=logger,
                    dry_run_manager=dry_run_manager,
                )
                yield module

    def test_full_dry_run_flow(self, mock_module, temp_home):
        """Test complete dry-run flow without system changes."""
        module = mock_module

        # Mock command existence checks
        with patch.object(module, "command_exists", return_value=True):
            with patch.object(
                module, "run", return_value=MagicMock(success=True, stdout="zsh 5.9")
            ):
                # Validation should pass
                assert module.validate() is True

                # Configure should work in dry-run
                assert module.configure() is True

                # Verify should pass in dry-run
                assert module.verify() is True

    def test_zshrc_generation_creates_valid_file(self, mock_module, temp_home):
        """Test that generated .zshrc is written correctly."""
        module = mock_module
        module.dry_run = False

        # Mock dependencies
        with patch.object(module, "run", return_value=MagicMock(success=True)):
            with patch.object(module, "install_packages_resilient"):
                with patch.object(module, "command_exists", return_value=True):
                    # Apply config
                    config = {
                        "zsh": {"plugins": ["git"], "set_default_shell": False},
                        "eza": {"icons": True},
                        "bat": {},
                        "zoxide": {},
                    }
                    module._apply_zsh_config(config)

        # Check .zshrc was created
        zshrc = temp_home / ".zshrc"
        assert zshrc.exists()

        # Verify content
        content = zshrc.read_text()
        assert "Oh-My-Zsh" in content
        assert "eza" in content.lower() or "alias ls=" in content

    def test_state_persistence_across_runs(self, temp_home):
        """Test that state is persisted and can be restored."""
        from configurator.core.dryrun import DryRunManager
        from configurator.modules.terminal_tools import TerminalToolsModule

        state_file = temp_home / ".configurator" / "state.json"

        config = MagicMock()
        config.get.return_value = {}
        logger = MagicMock()
        dry_run_manager = DryRunManager()
        dry_run_manager.enable()

        # First run - save state
        with patch.object(TerminalToolsModule, "STATE_FILE", state_file):
            module1 = TerminalToolsModule(
                config=config, logger=logger, dry_run_manager=dry_run_manager
            )
            module1._state["installed_tools"] = ["eza", "bat"]
            module1._state["configured"] = True
            module1._save_state()

        # Verify state file exists
        assert state_file.exists()

        # Second run - load state
        with patch.object(TerminalToolsModule, "STATE_FILE", state_file):
            module2 = TerminalToolsModule(
                config=config, logger=logger, dry_run_manager=dry_run_manager
            )
            assert module2._state.get("configured") is True
            assert "eza" in module2._state.get("installed_tools", [])

    def test_bat_config_creation(self, mock_module, temp_home):
        """Test bat configuration file creation."""
        module = mock_module
        module.dry_run = False

        # Create bat config
        module._apply_bat_config()

        # Check config file
        bat_config = temp_home / ".config" / "bat" / "config"
        assert bat_config.exists()

        content = bat_config.read_text()
        assert "--theme=" in content

    def test_error_handling_on_missing_apt(self, mock_module):
        """Test graceful handling when apt is missing."""
        module = mock_module

        with patch.object(module, "command_exists", return_value=False):
            # Should fail validation when apt-get is missing
            result = module.validate()
            assert result is False

    def test_backup_creation_on_existing_zshrc(self, mock_module, temp_home):
        """Test that existing .zshrc is backed up."""
        module = mock_module
        module.dry_run = False

        # Create existing .zshrc
        existing_zshrc = temp_home / ".zshrc"
        existing_zshrc.write_text("# Original content\n")

        config = {
            "zsh": {"plugins": ["git"], "set_default_shell": False},
            "eza": {},
            "bat": {},
            "zoxide": {},
        }

        # Patch backup_file to use temp directory instead of /var/backups
        def mock_backup_file(path: str) -> None:
            """Create backup in same directory instead of system backup dir."""
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{path}.pre-configurator.{timestamp}"
            shutil.copy2(path, backup_path)

        with patch.object(module, "run", return_value=MagicMock(success=True)):
            with patch("configurator.utils.file.backup_file", side_effect=mock_backup_file):
                module._apply_zsh_config(config)

        # Check backup was created
        backups = list(temp_home.glob(".zshrc.pre-configurator.*"))
        assert len(backups) >= 1

        # Original was preserved in backup
        backup_content = backups[0].read_text()
        assert "Original content" in backup_content


@pytest.mark.skipif(os.geteuid() != 0, reason="Requires root for actual installation")
class TestTerminalToolsRootIntegration:
    """Tests that require root privileges."""

    def test_real_eza_installation(self):
        """Test real eza installation (requires root)."""
        # This would test actual installation
        # Skipped in normal test runs
        pass

    def test_real_zsh_installation(self):
        """Test real zsh installation (requires root)."""
        # This would test actual installation
        # Skipped in normal test runs
        pass


class TestValidators:
    """Test terminal tools validators."""

    def test_zsh_installed_validator_when_missing(self):
        """Test validator detects missing zsh."""
        from configurator.validators.tier1_critical.zsh_installed_validator import (
            ZshInstalledValidator,
        )

        validator = ZshInstalledValidator()

        with patch("shutil.which", return_value=None):
            result = validator.validate()
            assert result.passed is False
            assert "not installed" in result.message.lower()

    def test_zsh_installed_validator_when_present(self):
        """Test validator passes when zsh is installed."""
        from configurator.validators.tier1_critical.zsh_installed_validator import (
            ZshInstalledValidator,
        )

        validator = ZshInstalledValidator()

        with patch("shutil.which", return_value="/usr/bin/zsh"):
            with patch("os.access", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout="zsh 5.9 (x86_64-debian-linux-gnu)"
                    )
                    result = validator.validate()
                    assert result.passed is True

    def test_shell_permission_validator(self):
        """Test shell permission validator."""
        from configurator.validators.tier1_critical.shell_permission_validator import (
            ShellPermissionValidator,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create necessary files for the validator
            zshrc = tmp_path / ".zshrc"
            zshrc.write_text("# test")
            config_dir = tmp_path / ".config"
            config_dir.mkdir()

            # Patch the Path class to return our temp path for /home/testuser
            original_path = Path

            def patched_path(path_str):
                if path_str == "/home/testuser":
                    return tmp_path
                return original_path(path_str)

            with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
                with patch(
                    "configurator.validators.tier1_critical.shell_permission_validator.Path",
                    side_effect=patched_path,
                ):
                    validator = ShellPermissionValidator()
                    result = validator.validate()
                    # Should pass with proper permissions
                    assert result.passed is True

    def test_tool_integration_validator(self):
        """Test tool integration validator."""
        from configurator.validators.tier2_high.tool_integration_validator import (
            ToolIntegrationValidator,
        )

        validator = ToolIntegrationValidator()

        # All tools installed
        with patch("shutil.which", side_effect=lambda x: f"/usr/bin/{x}"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="v1.0")
                result = validator.validate()
                assert result.passed is True

        # Some tools missing
        with patch("shutil.which", return_value=None):
            result = validator.validate()
            # Should still pass (tools just not installed)
            assert "Not installed" in result.details

    def test_zsh_performance_validator(self):
        """Test zsh performance validator."""
        from configurator.validators.tier3_medium.zsh_performance_validator import (
            ZshPerformanceValidator,
        )

        validator = ZshPerformanceValidator()

        # No zsh installed
        with patch("shutil.which", return_value=None):
            result = validator.validate()
            assert result.passed is True
            assert "not installed" in result.message.lower()
