"""
Unit tests for Phase 4 Zsh installation methods.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestZshInstallation:
    """Unit tests for Zsh installation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"zsh": {"enabled": True}}}
        return DesktopModule(
            config=config, logger=Mock(), rollback_manager=Mock(), dry_run_manager=Mock()
        )

    @patch.object(DesktopModule, "install_packages")
    def test_install_zsh_package_installs_zsh(self, mock_install_pkg, module):
        """Test that Zsh package is installed."""
        with patch.object(module, "command_exists", return_value=True):
            with patch.object(module, "run", return_value=Mock(success=True, stdout="zsh 5.8")):
                module._install_zsh_package()

        # Verify zsh package installed
        mock_install_pkg.assert_called_once()
        packages = mock_install_pkg.call_args[0][0]
        assert "zsh" in packages

    @patch.object(DesktopModule, "install_packages")
    def test_install_zsh_package_verifies_installation(self, mock_install_pkg, module):
        """Test that Zsh installation is verified."""
        with patch.object(module, "command_exists", return_value=False):
            # Should raise error if zsh not found after install
            with pytest.raises(Exception):
                module._install_zsh_package()


class TestOhMyZshInstallation:
    """Unit tests for Oh My Zsh installation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"zsh": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_install_oh_my_zsh_for_all_users(self, mock_run, mock_getpwnam, mock_getpwall, module):
        """Test that Oh My Zsh is installed for all regular users."""
        # Mock multiple users
        users = []
        for i in range(3):
            user = Mock()
            user.pw_name = f"user{i}"
            user.pw_uid = 1000 + i
            user.pw_dir = f"/home/user{i}"
            users.append(user)

        mock_getpwall.return_value = users
        mock_getpwnam.side_effect = lambda name: next(u for u in users if u.pw_name == name)

        # Mock run to handle both curl/sha256 checks AND user installs
        # The sha256 check expects specific output
        expected_sha256 = "ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352"

        def run_side_effect(cmd, check=False):
            mock_res = Mock(success=True, stdout="")
            if "sha256sum" in cmd:
                mock_res.stdout = f"{expected_sha256} /tmp/ohmyzsh_install.sh"
            return mock_res

        mock_run.side_effect = run_side_effect

        with patch("configurator.modules.desktop.os.path.exists", return_value=False):
            module._install_oh_my_zsh()

        # Verify installation attempted for each user
        install_calls = [str(c) for c in mock_run.call_args_list if "ohmyzsh" in str(c).lower()]

        # Should have at least 3 installations (plus download/verify steps)
        # Note: The implementation downloads once, then installs per user.
        # We check for the user installation commands
        user_install_calls = [c for c in install_calls if "sudo -u" in c]

        assert len(user_install_calls) >= 3

        # Verify all users mentioned
        all_commands = " ".join(user_install_calls)
        for i in range(3):
            assert f"user{i}" in all_commands

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_oh_my_zsh_skips_existing_installations(
        self, mock_run, mock_getpwnam, mock_getpwall, module
    ):
        """Test that existing Oh My Zsh installations are detected and skipped."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user

        # Pass checksum check
        expected_sha256 = "ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352"

        def run_side_effect(cmd, check=False):
            mock_res = Mock(success=True, stdout="")
            if "sha256sum" in cmd:
                mock_res.stdout = f"{expected_sha256} /tmp/ohmyzsh_install.sh"
            return mock_res

        mock_run.side_effect = run_side_effect

        # Simulate existing installation
        with patch(
            "configurator.modules.desktop.os.path.exists",
            side_effect=lambda path: ".oh-my-zsh" in str(path) or False,
        ):
            # Ensure os.path.exists returns True for the check we care about
            module._install_oh_my_zsh()

        # Should not execute installation script
        install_calls = [str(c) for c in mock_run.call_args_list if "install.sh" in str(c)]
        # Filter for the execution part
        execution_calls = [c for c in install_calls if "sh " in c and "unattended" in c]
        assert len(execution_calls) == 0

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_oh_my_zsh_registers_rollback(self, mock_run, mock_getpwnam, mock_getpwall, module):
        """Test that rollback actions are registered for Oh My Zsh."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user

        # Pass checksum check
        expected_sha256 = "ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352"

        def run_side_effect(cmd, check=False):
            mock_res = Mock(success=True, stdout="")
            if "sha256sum" in cmd:
                mock_res.stdout = f"{expected_sha256} /tmp/ohmyzsh_install.sh"
            return mock_res

        mock_run.side_effect = run_side_effect

        with patch("configurator.modules.desktop.os.path.exists", return_value=False):
            module._install_oh_my_zsh()

        # Verify rollback registered
        assert module.rollback_manager.add_command.called

        # Check rollback includes .oh-my-zsh removal
        rollback_calls = [str(c) for c in module.rollback_manager.add_command.call_args_list]
        assert any(".oh-my-zsh" in str(rollback_call) for rollback_call in rollback_calls)


class TestPluginInstallation:
    """Unit tests for Zsh plugin installation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"zsh": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_install_zsh_plugins_installs_autosuggestions(
        self, mock_run, mock_getpwnam, mock_getpwall, module
    ):
        """Test that zsh-autosuggestions plugin is installed."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user
        mock_run.return_value = Mock(success=True)

        with patch("configurator.modules.desktop.os.path.exists", return_value=False):
            module._install_zsh_plugins()

        # Verify autosuggestions cloned
        git_clones = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]
        assert any("zsh-autosuggestions" in clone_call for clone_call in git_clones)

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_install_zsh_plugins_installs_syntax_highlighting(
        self, mock_run, mock_getpwnam, mock_getpwall, module
    ):
        """Test that zsh-syntax-highlighting plugin is installed."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user
        mock_run.return_value = Mock(success=True)

        with patch("configurator.modules.desktop.os.path.exists", return_value=False):
            module._install_zsh_plugins()

        # Verify syntax-highlighting cloned
        git_clones = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]
        assert any("zsh-syntax-highlighting" in clone_call for clone_call in git_clones)


class TestTerminalTools:
    """Unit tests for terminal tools installation."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {"zsh": {"tools": {"fzf": True, "bat": True, "eza": True, "zoxide": True}}}
        }
        return DesktopModule(config=config, logger=Mock())

    @patch.object(DesktopModule, "install_packages")
    def test_install_terminal_tools_installs_all_tools(self, mock_install_pkg, module):
        """Test that all terminal tools are installed."""
        module._install_terminal_tools()

        # Verify all tools installed
        all_packages = []
        for pkg_call in mock_install_pkg.call_args_list:
            all_packages.extend(pkg_call[0][0])

        required_tools = ["fzf", "bat", "eza", "zoxide"]
        for tool in required_tools:
            # Note: package names might differ based on OS functionality
            assert tool in all_packages, f"Missing tool: {tool}"

    @patch.object(DesktopModule, "install_packages")
    def test_terminal_tools_respect_config(self, mock_install_pkg, module):
        """Test that tool installation respects configuration."""
        # Disable some tools
        module.config["desktop"]["zsh"]["tools"]["bat"] = False
        module.config["desktop"]["zsh"]["tools"]["eza"] = False

        module._install_terminal_tools()

        all_packages = []
        for pkg_call in mock_install_pkg.call_args_list:
            all_packages.extend(pkg_call[0][0])

        # Should install enabled tools
        assert "fzf" in all_packages
        assert "zoxide" in all_packages

        # Should NOT install disabled tools
        assert "bat" not in all_packages
        assert "eza" not in all_packages


class TestDefaultShellConfiguration:
    """Unit tests for setting Zsh as default shell."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"zsh": {"set_default_shell": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_set_zsh_as_default_shell_changes_shell(
        self, mock_run, mock_getpwnam, mock_getpwall, module
    ):
        """Test that default shell is changed to Zsh."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_user.pw_shell = "/bin/bash"

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user
        mock_run.return_value = Mock(success=True)

        with patch("configurator.modules.desktop.os.path.exists", return_value=True):
            module._set_zsh_as_default_shell()

        # Verify chsh executed
        chsh_calls = [str(c) for c in mock_run.call_args_list if "chsh" in str(c)]
        assert len(chsh_calls) > 0

        # Verify Zsh path
        assert any("/usr/bin/zsh" in chsh_call for chsh_call in chsh_calls)

    @patch("pwd.getpwall")
    @patch("pwd.getpwnam")
    @patch.object(DesktopModule, "run")
    def test_set_zsh_skips_if_already_default(self, mock_run, mock_getpwnam, mock_getpwall, module):
        """Test that shell change is skipped if Zsh already default."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_user.pw_shell = "/usr/bin/zsh"  # Already Zsh

        mock_getpwall.return_value = [mock_user]
        mock_getpwnam.return_value = mock_user

        with patch("configurator.modules.desktop.os.path.exists", return_value=True):
            module._set_zsh_as_default_shell()

        # Should not execute chsh
        chsh_calls = [str(c) for c in mock_run.call_args_list if "chsh" in str(c)]
        assert len(chsh_calls) == 0
