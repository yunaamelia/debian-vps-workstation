"""
Comprehensive unit tests for XRDP performance optimization in DesktopModule.

Tests cover:
- Configuration generation
- File operations
- User session setup
- Error handling
- Dry-run mode
- Security validation
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from configurator.exceptions import ModuleExecutionError
from configurator.modules.desktop import DesktopModule


class TestXRDPOptimizationUnit(unittest.TestCase):
    """Unit tests for XRDP optimization methods."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.config = {
            "desktop": {
                "enabled": True,
                "xrdp": {
                    "max_bpp": 24,
                    "bitmap_cache": True,
                    "security_layer": "tls",
                    "tcp_nodelay": True,
                },
            }
        }

        self.logger = Mock()
        self.rollback_manager = Mock()
        self.dry_run_manager = Mock()
        self.dry_run_manager.is_enabled = False

        self.module = DesktopModule(
            config=self.config,
            logger=self.logger,
            rollback_manager=self.rollback_manager,
            dry_run_manager=self.dry_run_manager,
        )

    def tearDown(self):
        """Clean up after each test."""
        self.module = None

    # ==================== Configuration Generation Tests ====================

    @patch("configurator.modules.desktop.write_file")
    @patch("configurator.modules.desktop.backup_file")
    @patch.object(DesktopModule, "run")
    def test_optimize_xrdp_performance_creates_valid_config(
        self, mock_run, mock_backup, mock_write
    ):
        """Test that _optimize_xrdp_performance generates valid XRDP config."""
        # Execute
        self.module._optimize_xrdp_performance()

        # Verify backups created
        assert mock_backup.call_count == 2
        mock_backup.assert_any_call("/etc/xrdp/xrdp.ini")
        mock_backup.assert_any_call("/etc/xrdp/sesman.ini")

        # Verify xrdp.ini written
        xrdp_ini_call = [c for c in mock_write.call_args_list if "/etc/xrdp/xrdp.ini" in str(c)][0]
        xrdp_content = xrdp_ini_call[0][1]

        # Validate critical settings
        assert "tcp_nodelay=true" in xrdp_content
        assert "bitmap_cache=true" in xrdp_content
        assert "max_bpp=24" in xrdp_content
        assert "security_layer=tls" in xrdp_content
        assert "bulk_compression=true" in xrdp_content

        # Verify sesman.ini written
        sesman_ini_call = [
            c for c in mock_write.call_args_list if "/etc/xrdp/sesman.ini" in str(c)
        ][0]
        sesman_content = sesman_ini_call[0][1]

        # Validate session settings
        assert "IdleTimeLimit=0" in sesman_content
        assert "DisconnectedTimeLimit=0" in sesman_content
        assert "+extension GLX" in sesman_content
        assert "LogLevel=WARNING" in sesman_content

    @patch("configurator.modules.desktop.write_file")
    @patch("configurator.modules.desktop.backup_file")
    @patch.object(DesktopModule, "run")
    def test_config_values_override_defaults(self, mock_run, mock_backup, mock_write):
        """Test that config values properly override defaults."""
        # Custom config
        custom_config = {
            "desktop": {"xrdp": {"max_bpp": 32, "bitmap_cache": False, "security_layer": "rdp"}}
        }
        custom_module = DesktopModule(
            config=custom_config,
            logger=self.logger,
            rollback_manager=self.rollback_manager,
            dry_run_manager=self.dry_run_manager,
        )

        custom_module._optimize_xrdp_performance()

        xrdp_content = mock_write.call_args_list[0][0][1]
        assert "max_bpp=32" in xrdp_content
        assert "bitmap_cache=false" in xrdp_content
        assert "security_layer=rdp" in xrdp_content

    @patch("configurator.modules.desktop.write_file")
    @patch("configurator.modules.desktop.backup_file")
    @patch.object(DesktopModule, "run")
    def test_invalid_max_bpp_falls_back_to_default(self, mock_run, mock_backup, mock_write):
        """Test that invalid max_bpp value falls back to safe default."""
        invalid_config = {"desktop": {"xrdp": {"max_bpp": 999}}}
        module = DesktopModule(
            config=invalid_config,
            logger=self.logger,
            rollback_manager=self.rollback_manager,
            dry_run_manager=self.dry_run_manager,
        )

        module._optimize_xrdp_performance()

        # Should use default (24) instead of invalid value
        xrdp_content = mock_write.call_args_list[0][0][1]
        assert "max_bpp=24" in xrdp_content
        assert "max_bpp=999" not in xrdp_content

        # Should log warning
        assert any("warning" in str(call).lower() for call in self.logger.mock_calls)

    # ==================== User Session Configuration Tests ====================

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.os.path.isabs", return_value=True)
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    def test_configure_user_session_creates_xsession_for_all_users(
        self, mock_isdir, mock_isabs, mock_run, mock_pwd
    ):
        """Test that .xsession is created for all non-system users."""
        # Mock user database
        mock_user1 = Mock()
        mock_user1.pw_name = "testuser1"
        mock_user1.pw_uid = 1000
        mock_user1.pw_dir = "/home/testuser1"

        mock_user2 = Mock()
        mock_user2.pw_name = "testuser2"
        mock_user2.pw_uid = 1001
        mock_user2.pw_dir = "/home/testuser2"

        mock_system = Mock()
        mock_system.pw_name = "daemon"
        mock_system.pw_uid = 1
        mock_system.pw_dir = "/usr/sbin"

        mock_pwd.getpwall.return_value = [mock_user1, mock_user2, mock_system]
        mock_pwd.getpwnam.side_effect = lambda name: {
            "testuser1": mock_user1,
            "testuser2": mock_user2,
        }[name]

        # Execute
        self.module._configure_user_session()

        # Verify .xsession created for both regular users (not system user)
        assert mock_run.call_count == 6  # 2 users × 3 commands (sudo tee + chmod + chown)

        # Verify content for user1
        user1_tee_call = [
            c for c in mock_run.call_args_list if "testuser1" in str(c) and "cat" in str(c)
        ][0]
        xsession_content = user1_tee_call[1]["input"].decode()

        # Validate critical environment variables
        assert "export NO_AT_BRIDGE=1" in xsession_content
        assert "export XDG_SESSION_DESKTOP=xfce" in xsession_content
        assert "export XCURSOR_THEME=Adwaita" in xsession_content
        assert "xset s off" in xsession_content
        assert "xsetroot -cursor_name left_ptr" in xsession_content
        assert "exec startxfce4" in xsession_content

        # Verify chmod executed
        chmod_calls = [c for c in mock_run.call_args_list if "chmod" in str(c)]
        assert len(chmod_calls) == 2  # One per user

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_configure_user_session_handles_no_users_gracefully(self, mock_run, mock_pwd):
        """Test behavior when no regular users exist."""
        # Only system users
        mock_system = Mock()
        mock_system.pw_name = "daemon"
        mock_system.pw_uid = 1

        mock_pwd.getpwall.return_value = [mock_system]

        # Execute - should not crash
        self.module._configure_user_session()

        # Verify no file operations attempted
        assert mock_run.call_count == 0

        # Verify warning logged
        warning_calls = [c for c in self.logger.mock_calls if "warning" in str(c).lower()]
        assert len(warning_calls) > 0

    # ==================== Security Tests ====================

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_username_validation_rejects_invalid_usernames(self, mock_run, mock_pwd):
        """Test that malicious usernames are rejected."""
        # Malicious username with command injection attempt
        mock_malicious = Mock()
        mock_malicious.pw_name = "user;rm-rf/"
        mock_malicious.pw_uid = 1000
        mock_malicious.pw_dir = "/home/user"

        mock_pwd.getpwall.return_value = [mock_malicious]

        # Execute - should skip invalid username
        self.module._configure_user_session()

        # Verify user was skipped (no commands executed)
        assert mock_run.call_count == 0

        # Verify warning logged
        warning_calls = [c for c in self.logger.mock_calls if "invalid" in str(c).lower()]
        assert len(warning_calls) > 0

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.os.path.isabs", return_value=True)
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    def test_shlex_quote_used_for_shell_safety(self, mock_isdir, mock_isabs, mock_run, mock_pwd):
        """Test that shlex.quote is used for shell command safety."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]
        mock_pwd.getpwnam.return_value = mock_user

        self.module._configure_user_session()

        # Verify shlex.quote was used (command should have quoted strings)
        assert mock_run.call_count > 0
        first_call = str(mock_run.call_args_list[0])
        # Commands should be properly quoted
        assert "'" in first_call or '"' in first_call

    # ==================== Error Handling Tests ====================

    @patch("configurator.modules.desktop.backup_file")
    @patch("configurator.modules.desktop.write_file")
    @patch.object(DesktopModule, "run")
    def test_handles_file_write_failure_gracefully(self, mock_run, mock_write, mock_backup):
        """Test error handling when file writes fail."""
        mock_write.side_effect = ModuleExecutionError(
            what="Write failed", why="Permission denied", how="Check permissions"
        )

        # Execute - should raise exception
        with pytest.raises(ModuleExecutionError):
            self.module._optimize_xrdp_performance()

    @patch("configurator.modules.desktop.backup_file")
    @patch("configurator.modules.desktop.write_file")
    @patch.object(DesktopModule, "run")
    def test_continues_if_backup_fails(self, mock_run, mock_write, mock_backup):
        """Test that backup failure doesn't block configuration."""
        mock_backup.side_effect = Exception("Backup failed")

        # Should log warning but continue
        self.module._optimize_xrdp_performance()

        # Verify write_file was still called
        assert mock_write.call_count == 2

        # Verify warning logged
        warning_calls = [c for c in self.logger.mock_calls if "warning" in str(c).lower()]
        assert len(warning_calls) > 0

    # ==================== Dry-Run Mode Tests ====================

    @patch("configurator.modules.desktop.write_file")
    @patch("configurator.modules.desktop.backup_file")
    def test_dry_run_mode_does_not_write_files(self, mock_backup, mock_write):
        """Test that dry-run mode prevents actual file modifications."""
        self.dry_run_manager.is_enabled = True
        self.module.dry_run = True

        self.module._optimize_xrdp_performance()

        # In dry-run mode, should not write files
        assert mock_write.call_count == 0
        assert mock_backup.call_count == 0

        # Should record actions
        assert self.dry_run_manager.record_file_write.called

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_dry_run_records_user_session_actions(self, mock_run, mock_pwd):
        """Test that user session configuration is recorded in dry-run."""
        self.module.dry_run = True

        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]

        self.module._configure_user_session()

        # Verify actions recorded (not executed)
        assert mock_run.call_count == 0
        assert self.dry_run_manager.record_command.called

    # ==================== Service Restart Tests ====================

    @patch("configurator.modules.desktop.write_file")
    @patch("configurator.modules.desktop.backup_file")
    @patch.object(DesktopModule, "run")
    def test_xrdp_service_restarted_after_config_change(self, mock_run, mock_backup, mock_write):
        """Test that XRDP service is restarted after configuration."""
        self.module._optimize_xrdp_performance()

        # Verify systemctl restart was called
        restart_calls = [c for c in mock_run.call_args_list if "systemctl restart" in str(c)]
        assert len(restart_calls) >= 1

        # Should restart xrdp
        xrdp_restart = [c for c in restart_calls if "xrdp" in str(c)]
        assert len(xrdp_restart) > 0


if __name__ == "__main__":
    unittest.main()
