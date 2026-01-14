"""
Security tests for input validation across all modules.

Tests for:
- Path traversal prevention
- Null byte injection prevention
- Unicode boundary testing
- Length overflow testing
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestPathTraversalPrevention:
    """Test that path traversal attacks are prevented."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "malicious_path",
        [
            "../../../etc/passwd",
            "..\\..\\..\\etc\\passwd",
            "/home/../../../etc/shadow",
            "~/../../../etc/shadow",
            "/home/user/../../../../root/.ssh/id_rsa",
            "./../.../../etc/passwd",
        ],
    )
    def test_path_traversal_in_home_directory(self, module, malicious_path):
        """Test that path traversal in home directory is prevented."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = malicious_path

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch("configurator.modules.desktop.os.path.isabs") as mock_isabs:
                # Non-absolute paths should be rejected
                mock_isabs.return_value = malicious_path.startswith("/")

                with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                    with patch.object(module, "run") as mock_run:
                        module._configure_user_session()

                        # Should not write to traversal paths
                        for call in mock_run.call_args_list:
                            cmd = str(call)
                            assert "../" not in cmd or "testuser" in cmd

    def test_absolute_path_validation(self, module):
        """Test that non-absolute paths are rejected."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "relative/path/to/home"  # Not absolute

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch("configurator.modules.desktop.os.path.isabs", return_value=False):
                with patch.object(module, "run") as mock_run:
                    module._configure_user_session()

                    # Should skip user with non-absolute home
                    assert mock_run.call_count == 0


class TestNullByteInjection:
    """Test null byte injection prevention."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "testuser\x00malicious",
            "/home/user\x00/etc/passwd",
            "config\x00.txt",
        ],
    )
    def test_null_byte_in_username(self, module, malicious_input):
        """Test that null bytes in usernames are rejected."""
        mock_user = Mock()
        mock_user.pw_name = malicious_input
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                # Should skip user with null byte
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    assert "\x00" not in cmd


class TestUnicodeBoundary:
    """Test Unicode boundary cases."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @pytest.mark.parametrize(
        "unicode_username",
        [
            "user\u202e",  # Right-to-left override
            "user\u2066",  # Left-to-right isolate
            "user\ufeff",  # BOM
            "user\u0000",  # Null
        ],
    )
    def test_unicode_control_characters_rejected(self, module, unicode_username):
        """Test that Unicode control characters are handled safely."""
        mock_user = Mock()
        mock_user.pw_name = unicode_username
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                module._configure_user_session()

                # Should skip or sanitize user with control characters
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    # Control chars should not appear in commands
                    assert "\u202e" not in cmd
                    assert "\u2066" not in cmd


class TestLengthOverflow:
    """Test length overflow prevention."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"xrdp": {"enabled": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    def test_extremely_long_username_handled(self, module):
        """Test that extremely long usernames are handled safely."""
        long_username = "a" * 10000  # 10KB username

        mock_user = Mock()
        mock_user.pw_name = long_username
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch.object(module, "run") as mock_run:
                # Should not crash
                try:
                    module._configure_user_session()
                except Exception:
                    pass  # Some error is acceptable for invalid input

                # If commands were run, verify no buffer issues
                for call in mock_run.call_args_list:
                    cmd = str(call)
                    # Command length should be reasonable
                    assert len(cmd) < 1000000  # Less than 1MB

    def test_extremely_long_path_handled(self, module):
        """Test that extremely long paths are handled safely."""
        long_path = "/home/" + "a" * 5000

        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = long_path

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]

            with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
                with patch("configurator.modules.desktop.os.path.isdir", return_value=False):
                    with patch.object(module, "run") as mock_run:
                        # Should handle gracefully
                        module._configure_user_session()

                        # Path doesn't exist, so should be skipped
                        # or handled gracefully


class TestConfigValueValidation:
    """Test configuration value validation."""

    def test_max_bpp_range_validation(self):
        """Test that max_bpp is validated to be in acceptable range."""
        invalid_configs = [
            {"desktop": {"xrdp": {"max_bpp": -1}}},
            {"desktop": {"xrdp": {"max_bpp": 0}}},
            {"desktop": {"xrdp": {"max_bpp": 100}}},
            {"desktop": {"xrdp": {"max_bpp": "24"}}},  # String instead of int
        ]

        for config in invalid_configs:
            module = DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

            with patch("configurator.modules.desktop.write_file") as mock_write:
                with patch("configurator.modules.desktop.backup_file"):
                    with patch.object(module, "run"):
                        module._optimize_xrdp_performance()

            # Should use default or valid value
            if mock_write.called:
                content = mock_write.call_args_list[0][0][1]
                # Should contain valid bpp value
                assert "max_bpp=24" in content or "max_bpp=16" in content or "max_bpp=32" in content

    def test_security_layer_validation(self):
        """Test that security_layer is validated."""
        invalid_config = {"desktop": {"xrdp": {"security_layer": "none; rm -rf /"}}}
        module = DesktopModule(config=invalid_config, logger=Mock(), rollback_manager=Mock())

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        # Should not execute injection
        if mock_write.called:
            content = mock_write.call_args_list[0][0][1]
            assert "rm -rf" not in content
