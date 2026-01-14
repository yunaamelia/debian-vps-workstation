"""
Unit tests for Phase 4: Zsh Environment.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestZshInstallation:
    """Test Zsh installation methods."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "command_exists")
    def test_install_zsh_package_installs_zsh(self, mock_exists, mock_install, module):
        """Test that zsh packages are installed."""
        mock_install.return_value = True
        mock_exists.return_value = True

        assert module._install_zsh_package() is True
        assert mock_install.called
        args, _ = mock_install.call_args
        assert "zsh" in args[0]

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "command_exists")
    def test_install_zsh_package_verifies_installation(self, mock_exists, mock_install, module):
        """Test verification failure."""
        mock_install.return_value = True
        mock_exists.return_value = False  # fail verification

        assert module._install_zsh_package() is False


class TestOhMyZshInstallation:
    """Test Oh My Zsh installation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"zsh": {"enabled": True, "oh_my_zsh": {"enabled": True}}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch.object(DesktopModule, "run")
    def test_install_oh_my_zsh_calls_script(self, mock_run, mock_getpwall, module):
        """Test that OMZ install script is downloaded and run."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwall.return_value = [mock_user]

        mock_run.return_value.success = True
        module.dry_run = False

        module._install_oh_my_zsh()

        # Verify curl download
        download_called = False
        install_called = False

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if "curl" in cmd and "install.sh" in cmd:
                download_called = True
            if "sh /tmp/ohmyzsh_install.sh" in cmd:
                install_called = True

        assert download_called, "OMZ installer download not called"
        assert install_called, "OMZ installer execution not called"


class TestPluginInstallation:
    """Test Zsh Plugin installation."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    @patch("os.path.exists")
    @patch("pwd.getpwall")
    @patch.object(DesktopModule, "run")
    def test_install_zsh_plugins_clones_git(self, mock_run, mock_getpwall, mock_exists, module):
        """Test that plugins are cloned."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwall.return_value = [mock_user]

        mock_run.return_value.success = True

        # Setup side_effect for path checks
        def exists_side_effect(path):
            if ".oh-my-zsh" in path and "plugins" not in path:
                return True  # .oh-my-zsh base dir exists
            if "plugins" in path:
                return False  # plugins don't exist, trigger clone
            return False

        mock_exists.side_effect = exists_side_effect

        module.dry_run = False  # important to pass 'and not self.dry_run' check
        module._install_zsh_plugins()

        # Verify git clone calls for plugins
        autosuggestions_found = False
        syntax_found = False

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if "git clone" in cmd:
                if "zsh-autosuggestions" in cmd:
                    autosuggestions_found = True
                if "zsh-syntax-highlighting" in cmd:
                    syntax_found = True

        assert autosuggestions_found, "zsh-autosuggestions not cloned"
        assert syntax_found, "zsh-syntax-highlighting not cloned"
