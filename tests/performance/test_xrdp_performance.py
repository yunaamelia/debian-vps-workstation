"""
Performance tests for XRDP optimization.

Validates that optimizations don't introduce performance regressions.
"""

import time
from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestXRDPPerformance:
    """Performance benchmarks for XRDP optimization."""

    def test_configuration_generation_performance(self):
        """Test that config generation completes within acceptable time."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module, "run"):
                    start = time.time()
                    module._optimize_xrdp_performance()
                    duration = time.time() - start

        # Should complete in under 1 second (config generation only)
        assert duration < 1.0, f"Config generation took {duration:.2f}s (expected <1s)"

    @pytest.mark.parametrize("user_count", [1, 5, 10, 20])
    def test_user_session_setup_scales_linearly(self, user_count):
        """Test that user session setup scales linearly with user count."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # Create mock users
        mock_users = []
        for i in range(user_count):
            mock_user = Mock()
            mock_user.pw_name = f"user{i}"
            mock_user.pw_uid = 1000 + i
            mock_user.pw_dir = f"/home/user{i}"
            mock_users.append(mock_user)

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = mock_users
            mock_pwd.getpwnam.side_effect = lambda name: next(
                u for u in mock_users if u.pw_name == name
            )

            with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
                with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                    with patch.object(module, "run"):
                        start = time.time()
                        module._configure_user_session()
                        duration = time.time() - start

        # Should be roughly linear: ~0.1s per user max
        expected_max = user_count * 0.2  # 200ms per user is generous
        assert (
            duration < expected_max
        ), f"User session setup for {user_count} users took {duration:.2f}s"

    def test_dry_run_mode_has_minimal_overhead(self):
        """Test that dry-run mode doesn't add significant overhead."""
        config = {"desktop": {"xrdp": {}}}

        # Test normal mode
        module_normal = DesktopModule(config=config, logger=Mock())
        module_normal.dry_run = False

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module_normal, "run"):
                    start = time.time()
                    module_normal._optimize_xrdp_performance()
                    normal_duration = time.time() - start

        # Test dry-run mode
        dry_run_manager = Mock()
        dry_run_manager.is_enabled = True
        module_dry = DesktopModule(config=config, logger=Mock(), dry_run_manager=dry_run_manager)
        module_dry.dry_run = True

        start = time.time()
        module_dry._optimize_xrdp_performance()
        dry_run_duration = time.time() - start

        # Dry-run should be as fast or faster (no actual I/O)
        assert dry_run_duration <= normal_duration * 1.5  # Allow 50% overhead max

    def test_validation_overhead_is_acceptable(self):
        """Test that config validation doesn't add significant overhead."""
        # Test with valid values (no validation needed)
        valid_config = {
            "desktop": {"xrdp": {"max_bpp": 24, "bitmap_cache": True, "security_layer": "tls"}}
        }
        module_valid = DesktopModule(config=valid_config, logger=Mock())

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module_valid, "run"):
                    start = time.time()
                    module_valid._optimize_xrdp_performance()
                    valid_duration = time.time() - start

        # Test with invalid values (triggers validation and warnings)
        invalid_config = {
            "desktop": {"xrdp": {"max_bpp": 999, "bitmap_cache": True, "security_layer": "invalid"}}
        }
        module_invalid = DesktopModule(config=invalid_config, logger=Mock())

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file"):
                with patch.object(module_invalid, "run"):
                    start = time.time()
                    module_invalid._optimize_xrdp_performance()
                    invalid_duration = time.time() - start

        # Validation overhead should be minimal (< 100ms difference)
        overhead = invalid_duration - valid_duration
        assert overhead < 0.1, f"Validation added {overhead:.3f}s overhead"

    def test_backup_operations_dont_block(self):
        """Test that backup operations don't significantly slow down config."""
        config = {"desktop": {"xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # Mock backup with small delay (simulating I/O)
        def slow_backup(path):
            time.sleep(0.01)  # 10ms delay per backup
            return None

        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.backup_file", side_effect=slow_backup):
                with patch.object(module, "run"):
                    start = time.time()
                    module._optimize_xrdp_performance()
                    duration = time.time() - start

        # 2 backups × 10ms + overhead should still be fast
        assert duration < 0.5, f"Config with backups took {duration:.2f}s"

    @pytest.mark.slow
    def test_full_module_configure_performance(self):
        """Test complete module configuration completes in reasonable time."""
        config = {"desktop": {"enabled": True, "xrdp": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # Mock all external dependencies
        with patch.object(module, "_install_xrdp"):
            with patch.object(module, "_install_xfce4"):
                with patch.object(module, "_configure_xrdp"):
                    with patch.object(module, "_configure_session"):
                        with patch.object(module, "_start_services"):
                            with patch("configurator.modules.desktop.write_file"):
                                with patch("configurator.modules.desktop.backup_file"):
                                    with patch.object(module, "run"):
                                        start = time.time()
                                        module.configure()
                                        duration = time.time() - start

        # Full configure (mocked) should complete quickly
        assert duration < 5.0, f"Full module configure took {duration:.2f}s (expected <5s)"
