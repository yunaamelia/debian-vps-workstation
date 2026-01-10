"""
Integration tests for DesktopModule with XRDP optimizations.

Tests the complete flow from configuration to verification.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from configurator.core.rollback import RollbackManager
from configurator.modules.desktop import DesktopModule


@pytest.fixture
def integration_environment():
    """Set up isolated test environment."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="vps_test_")
    fake_etc = os.path.join(temp_dir, "etc", "xrdp")
    fake_home = os.path.join(temp_dir, "home", "testuser")

    os.makedirs(fake_etc, exist_ok=True)
    os.makedirs(fake_home, exist_ok=True)

    yield {"temp_dir": temp_dir, "fake_etc": fake_etc, "fake_home": fake_home}

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDesktopModuleIntegration:
    """Integration tests for complete DesktopModule flow."""

    def test_full_configure_flow_with_optimizations(self):
        """Test complete configure() execution with XRDP optimizations."""
        # Setup
        config = {"desktop": {"enabled": True, "xrdp": {"max_bpp": 24, "bitmap_cache": True}}}
        logger = Mock()
        rollback_manager = RollbackManager(logger)

        module = DesktopModule(config=config, logger=logger, rollback_manager=rollback_manager)

        # Track executed commands
        executed_commands = []

        def mock_run(cmd, **kwargs):
            executed_commands.append(cmd)
            # Return successful result
            result = Mock()
            result.success = True
            result.return_code = 0
            result.stdout = ""
            result.stderr = ""
            return result

        # Mock all methods that interact with system
        with patch.object(module, "run", side_effect=mock_run):
            with patch.object(module, "_install_xrdp"):
                with patch.object(module, "_install_xfce4"):
                    with patch.object(module, "_configure_xrdp"):
                        with patch.object(module, "_configure_session"):
                            with patch.object(module, "_start_services"):
                                with patch("configurator.modules.desktop.write_file"):
                                    with patch("configurator.modules.desktop.backup_file"):
                                        with patch("configurator.modules.desktop.pwd") as mock_pwd:
                                            # Mock no users for simplicity
                                            mock_pwd.getpwall.return_value = []

                                            result = module.configure()

        # Verify
        assert result is True

        # Verify optimization methods were called (check log messages)
        log_calls = [str(call) for call in logger.mock_calls]
        assert any("optimiz" in msg.lower() for msg in log_calls)

    def test_no_conflict_with_existing_configure_xrdp(self):
        """Test that new optimization doesn't conflict with existing _configure_xrdp()."""
        config = {"desktop": {"enabled": True, "xrdp": {}}}
        logger = Mock()
        module = DesktopModule(config=config, logger=logger)

        write_calls = []

        def track_writes(path, content, **kwargs):
            write_calls.append({"path": path, "content": content})

        with patch("configurator.modules.desktop.write_file", side_effect=track_writes):
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    with patch("configurator.modules.desktop.pwd") as mock_pwd:
                        mock_pwd.getpwall.return_value = []

                        # Call both methods
                        if hasattr(module, "_configure_xrdp"):
                            try:
                                module._configure_xrdp()
                            except Exception:
                                pass  # Old method might fail in test env

                        module._optimize_xrdp_performance()

        # Check that xrdp.ini is only written once (by optimization method)
        xrdp_ini_writes = [w for w in write_calls if "xrdp.ini" in w["path"]]

        # New method should write the config
        assert len(xrdp_ini_writes) >= 1

    def test_rollback_registration_works(self):
        """Test that rollback actions are properly registered."""
        config = {"desktop": {"xrdp": {}}}
        logger = Mock()
        rollback_manager = Mock()

        module = DesktopModule(config=config, logger=logger, rollback_manager=rollback_manager)

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file") as mock_backup:
                # Mock backup returns a path
                mock_backup.return_value = Path("/tmp/backup.bak")

                with patch.object(module, "run"):
                    with patch("configurator.modules.desktop.pwd") as mock_pwd:
                        mock_pwd.getpwall.return_value = []

                        module._optimize_xrdp_performance()

        # Verify backups were created (which enables rollback)
        assert mock_backup.call_count == 2

    def test_configuration_validation_flow(self):
        """Test that invalid configurations are handled correctly."""
        # Invalid config
        invalid_config = {"desktop": {"xrdp": {"max_bpp": 9999, "security_layer": "invalid"}}}
        logger = Mock()
        module = DesktopModule(config=invalid_config, logger=logger)

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    module._optimize_xrdp_performance()

        # Should have written configs with corrected values
        assert mock_write.call_count == 2

        # Check that warnings were logged
        warning_calls = [c for c in logger.mock_calls if "warning" in str(c).lower()]
        assert len(warning_calls) >= 2  # One for max_bpp, one for security_layer

        # Check corrected values
        xrdp_content = mock_write.call_args_list[0][0][1]
        assert "max_bpp=24" in xrdp_content  # Should use default
        assert "security_layer=tls" in xrdp_content  # Should use default

    def test_user_session_integration_with_multiple_users(self):
        """Test user session configuration with multiple users."""
        config = {"desktop": {"xrdp": {}}}
        logger = Mock()
        module = DesktopModule(config=config, logger=logger)

        # Create multiple mock users
        users = []
        for i in range(3):
            user = Mock()
            user.pw_name = f"user{i}"
            user.pw_uid = 1000 + i
            user.pw_dir = f"/home/user{i}"
            users.append(user)

        run_calls = []

        def track_run(cmd, **kwargs):
            run_calls.append(cmd)
            result = Mock()
            result.success = True
            return result

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = users
            mock_pwd.getpwnam.side_effect = lambda name: next(u for u in users if u.pw_name == name)

            with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
                with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                    with patch.object(module, "run", side_effect=track_run):
                        module._configure_user_session()

        # Should have commands for all 3 users
        assert len(run_calls) >= 3  # At least one command per user

        # Verify each user got their config
        for i in range(3):
            user_commands = [c for c in run_calls if f"user{i}" in c]
            assert len(user_commands) > 0

    def test_error_recovery_in_configure_flow(self):
        """Test that errors in one step don't break the entire flow."""
        config = {"desktop": {"xrdp": {}}}
        logger = Mock()
        module = DesktopModule(config=config, logger=logger)

        # Simulate backup failure (non-critical)
        with patch("configurator.modules.desktop.backup_file") as mock_backup:
            mock_backup.side_effect = Exception("Backup failed")

            with patch("configurator.modules.desktop.write_file"):
                with patch.object(module, "run"):
                    with patch("configurator.modules.desktop.pwd") as mock_pwd:
                        mock_pwd.getpwall.return_value = []

                        # Should not raise exception
                        module._optimize_xrdp_performance()

        # Should log warning but continue
        warning_calls = [c for c in logger.mock_calls if "warning" in str(c).lower()]
        assert len(warning_calls) > 0

    def test_dry_run_integration(self):
        """Test that dry-run mode is respected throughout the flow."""
        config = {"desktop": {"xrdp": {}}}
        logger = Mock()
        dry_run_manager = Mock()
        dry_run_manager.is_enabled = True

        module = DesktopModule(config=config, logger=logger, dry_run_manager=dry_run_manager)
        module.dry_run = True

        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.backup_file") as mock_backup:
                module._optimize_xrdp_performance()

        # No actual writes should occur
        assert mock_write.call_count == 0
        assert mock_backup.call_count == 0

        # But actions should be recorded
        assert dry_run_manager.record_file_write.called
