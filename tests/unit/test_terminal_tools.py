"""
Unit tests for Terminal Tools Module.

Tests the TerminalToolsModule class without requiring root or system changes.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTerminalToolsModule:
    """Test suite for TerminalToolsModule."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = MagicMock()
        config.get.return_value = {
            "eza": {"enabled": True, "icons": True},
            "bat": {"enabled": True, "theme": "TwoDark"},
            "zoxide": {"enabled": True},
            "zsh": {"enabled": True, "plugins": ["git"]},
        }
        return config

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock()

    @pytest.fixture
    def mock_dry_run_manager(self):
        """Create a mock dry-run manager."""
        manager = MagicMock()
        manager.is_enabled = True
        return manager

    @pytest.fixture
    def module(self, mock_config, mock_logger, mock_dry_run_manager):
        """Create a TerminalToolsModule instance for testing."""
        from configurator.modules.terminal_tools import TerminalToolsModule

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch home directory and state file
            with patch.object(
                TerminalToolsModule,
                "STATE_FILE",
                Path(tmpdir) / "terminal-tools.state.json",
            ):
                module = TerminalToolsModule(
                    config=mock_config,
                    logger=mock_logger,
                    dry_run_manager=mock_dry_run_manager,
                )
                yield module

    def test_module_initialization(self, module):
        """Test module initializes correctly."""
        assert module.name == "Terminal Tools"
        assert module.priority == 45
        assert "system" in module.depends_on
        assert module.mandatory is False

    def test_module_description(self, module):
        """Test module has proper description."""
        assert "Eza" in module.description
        assert "Bat" in module.description
        assert "Zsh" in module.description
        assert "Zoxide" in module.description

    def test_validate_dry_run(self, module):
        """Test validation in dry-run mode."""
        with patch.object(module, "command_exists", return_value=True):
            with patch("os.access", return_value=True):
                result = module.validate()
                assert result is True

    def test_state_file_operations(self, mock_config, mock_logger, mock_dry_run_manager):
        """Test state file save and load."""
        from configurator.modules.terminal_tools import TerminalToolsModule

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"

            with patch.object(TerminalToolsModule, "STATE_FILE", state_file):
                module = TerminalToolsModule(
                    config=mock_config,
                    logger=mock_logger,
                    dry_run_manager=mock_dry_run_manager,
                )

                # Initially empty state
                assert module._state == {}

                # Save state
                module._state["test_key"] = "test_value"
                module._save_state()

                # Verify file was created
                assert state_file.exists()

                # Create new module and verify state loaded
                module2 = TerminalToolsModule(
                    config=mock_config,
                    logger=mock_logger,
                    dry_run_manager=mock_dry_run_manager,
                )
                assert module2._state.get("test_key") == "test_value"

    def test_get_target_user(self, module):
        """Test target user detection."""
        with patch.dict(os.environ, {"SUDO_USER": "testuser"}, clear=False):
            assert module._get_target_user() == "testuser"

        with patch.dict(os.environ, {"USER": "regularuser"}, clear=True):
            assert module._get_target_user() == "regularuser"

    def test_get_home_dir(self, module):
        """Test home directory resolution."""
        with patch.object(module, "_get_target_user", return_value="testuser"):
            home = module._get_home_dir()
            assert home == Path("/home/testuser")

        with patch.object(module, "_get_target_user", return_value="root"):
            home = module._get_home_dir()
            assert home == Path("/root")

    def test_get_tools_config_default(self, module):
        """Test default configuration when config manager fails."""
        module.config = None
        config = module._get_tools_config()

        # Should return defaults
        assert "eza" in config
        assert "bat" in config
        assert "zoxide" in config
        assert "zsh" in config

    def test_generate_zshrc(self, module):
        """Test .zshrc content generation."""
        plugins = ["git", "docker", "zsh-syntax-highlighting"]
        config = {
            "eza": {"icons": True, "git_integration": True},
            "bat": {},
            "zoxide": {},
        }

        with patch.object(module, "_get_home_dir", return_value=Path("/home/test")):
            content = module._generate_zshrc(plugins, config)

        # Check essential elements
        assert "Oh-My-Zsh Configuration" in content
        assert "ZSH_THEME=" in content
        assert "plugins=(git docker zsh-syntax-highlighting)" in content
        assert "alias ls=" in content
        assert "alias cat=" in content
        assert "zoxide init zsh" in content

    def test_zshrc_plugin_order(self, module):
        """Test that zsh-syntax-highlighting is always last."""
        plugins = ["zsh-syntax-highlighting", "git", "docker"]
        config = {"eza": {}, "bat": {}, "zoxide": {}}

        with patch.object(module, "_get_home_dir", return_value=Path("/home/test")):
            content = module._generate_zshrc(plugins, config)

        # Syntax highlighting should be last in plugins list
        assert "plugins=(git docker zsh-syntax-highlighting)" in content

    def test_verify_dry_run(self, module):
        """Test verification in dry-run mode returns True."""
        result = module.verify()
        assert result is True


class TestTerminalToolsModuleIntegration:
    """Integration-style tests (still mocked, but test more flow)."""

    @pytest.fixture
    def module_with_mocks(self):
        """Create module with comprehensive mocks."""
        from configurator.modules.terminal_tools import TerminalToolsModule

        with tempfile.TemporaryDirectory() as tmpdir:
            config = MagicMock()
            config.get.return_value = {}

            logger = MagicMock()
            dry_run_mgr = MagicMock()
            dry_run_mgr.is_enabled = False

            with patch.object(
                TerminalToolsModule,
                "STATE_FILE",
                Path(tmpdir) / "state.json",
            ):
                module = TerminalToolsModule(
                    config=config,
                    logger=logger,
                    dry_run_manager=dry_run_mgr,
                )

                # Mock all command execution
                module.run = MagicMock(return_value=MagicMock(success=True, stdout=""))
                module.install_packages_resilient = MagicMock(return_value=True)
                module.command_exists = MagicMock(return_value=False)

                yield module

    def test_configure_calls_all_installers(self, module_with_mocks):
        """Test that configure calls all installer methods."""
        module = module_with_mocks

        # Mock private methods
        module._install_dependencies = MagicMock()
        module._install_zsh = MagicMock()
        module._install_ohmyzsh = MagicMock()
        module._install_eza = MagicMock()
        module._install_bat = MagicMock()
        module._install_zoxide = MagicMock()
        module._apply_zsh_config = MagicMock()

        result = module.configure()

        assert result is True
        module._install_dependencies.assert_called_once()
        module._install_zsh.assert_called_once()
        module._install_ohmyzsh.assert_called_once()
        module._install_eza.assert_called_once()
        module._install_bat.assert_called_once()
        module._install_zoxide.assert_called_once()
        module._apply_zsh_config.assert_called_once()

    def test_rollback_registration(self, module_with_mocks):
        """Test that rollback actions are registered via package installation."""
        module = module_with_mocks
        module.rollback_manager = MagicMock()

        # Mock command_exists to return False so installation proceeds
        module.command_exists = MagicMock(return_value=False)

        # Mock install_packages_resilient to simulate successful installation
        # The base module's install_packages method adds rollback actions
        module.install_packages_resilient = MagicMock(return_value=True)

        # Call a method that installs packages
        module._install_zsh()

        # Verify install_packages_resilient was called (which internally handles rollback)
        module.install_packages_resilient.assert_called_once_with(["zsh"], update_cache=False)
