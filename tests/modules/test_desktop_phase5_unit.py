"""
Unit tests for Phase 5 terminal tools configuration methods.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestBatConfigurationMethods:
    """Unit tests for bat configuration methods."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "terminal_tools": {
                    "bat": {"theme": "TwoDark", "line_numbers": True, "git_integration": True}
                }
            }
        }
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch("os.makedirs")
    @patch("shutil.chown")
    @patch.object(DesktopModule, "write_file")
    def test_configure_bat_advanced_logic(
        self, mock_write, mock_chown, mock_makedirs, mock_pwnam, mock_getpwall, module
    ):
        """Test bat advanced configuration logic."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_getpwall.return_value = [mock_user]
        mock_pwnam.return_value = mock_user

        # Disable dry_run to confirm os.makedirs is called
        module.dry_run = False

        module._configure_bat_advanced()

        # Verify mkdir
        mock_makedirs.assert_called()
        args, _ = mock_makedirs.call_args
        assert ".config/bat" in args[0]

        # Verify config write
        mock_write.assert_called()
        args, _ = mock_write.call_args
        assert "config" in args[0]
        assert "TwoDark" in args[1]  # Theme check

        # Verify chown
        mock_chown.assert_called()


class TestEzaInstallation:
    """Unit tests for eza installation and configuration (replaces exa)."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"terminal_tools": {"eza": {"enabled": True}}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "command_exists")
    @patch.object(DesktopModule, "run")
    def test_install_eza_package(self, mock_run, mock_exists, mock_install, module):
        """Test that eza is installed."""
        mock_install.return_value = True
        mock_exists.return_value = True
        mock_run.return_value.success = True
        mock_run.return_value.stdout = "eza 0.18.0"

        assert module._install_eza() is True

        # Verify package installation attempted
        assert mock_install.called
        args, _ = mock_install.call_args
        assert "eza" in args[0]

    def test_configure_eza_aliases(self, module):
        """Test that eza aliases are configured."""
        module._configure_eza_aliases()

        assert hasattr(module, "eza_aliases")
        assert "alias ls='eza" in module.eza_aliases
        assert "--icons" in module.eza_aliases
        assert "--git" in module.eza_aliases


class TestZoxideInstallation:
    """Unit tests for zoxide."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "command_exists")
    @patch.object(DesktopModule, "run")
    def test_install_zoxide(self, mock_run, mock_exists, mock_install, module):
        """Test zoxide installation."""
        mock_run.return_value.success = True
        mock_install.return_value = True
        mock_exists.return_value = True

        assert module._install_zoxide() is True
        mock_install.assert_called_with(["zoxide"])


class TestFzfConfiguration:
    """Unit tests for fzf."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    def test_configure_fzf_keybindings(self, module):
        """Test fzf keybindings configuration."""
        module._configure_fzf_keybindings()

        assert hasattr(module, "fzf_config")
        assert "export FZF_DEFAULT_OPTS" in module.fzf_config


class TestIntegrationScriptCreation:
    """Unit tests for integration script creation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"terminal_tools": {}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "run")
    @patch.object(DesktopModule, "write_file")
    def test_create_tool_integration_scripts_creates_all_scripts(
        self, mock_write, mock_run, module
    ):
        """Test that all three integration scripts are created."""
        # Ensure create_preview etc succeed
        module._create_integration_scripts()

        # Verify write_file called for each script
        # write_file(script_path, content, mode)
        assert mock_write.call_count >= 3

        scripts = [args[0] for args, _ in mock_write.call_args_list]
        assert any("preview.sh" in s for s in scripts)
        assert any("search.sh" in s for s in scripts)
        assert any("goto.sh" in s for s in scripts)
