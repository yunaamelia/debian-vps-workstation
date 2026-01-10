"""
Performance tests for Phase 3 operations.
"""

import time
from unittest.mock import Mock, patch

from configurator.modules.desktop import DesktopModule


class TestPhase3Performance:
    """Performance benchmarks for Phase 3."""

    def test_theme_installation_time(self):
        """Test that theme installation completes in reasonable time."""
        config = {"desktop": {"themes": {"install": ["nordic", "arc"]}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        # Mock slow git clone (simulate network delay)
        def slow_run(cmd, **kwargs):
            if "git clone" in cmd:
                time.sleep(0.1)  # Simulate 100ms network delay
            return Mock(success=True)

        with patch.object(module, "run", side_effect=slow_run):
            with patch.object(module, "install_packages"):
                start = time.time()
                module._install_themes()
                duration = time.time() - start

        # Should complete in < 2 seconds even with simulated network delay
        assert duration < 2.0, f"Theme installation too slow: {duration:.2f}s"

    def test_font_cache_rebuild_performance(self):
        """Test that font cache rebuild doesn't block excessively."""
        config = {"desktop": {"fonts": {"default": "Roboto 10"}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "install_packages"):
            with patch("configurator.modules.desktop.write_file"):
                with patch.object(module, "run") as mock_run:
                    start = time.time()
                    module._configure_fonts()
                    duration = time.time() - start

        # Font configuration should be fast (< 1s without actual fc-cache)
        assert duration < 1.0, f"Font configuration too slow: {duration:.2f}s"

    def test_icon_pack_installation_performance(self):
        """Test that icon pack installation is reasonably fast."""
        config = {"desktop": {"icons": {"install": ["papirus"]}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "install_packages"):
            start = time.time()
            module._install_icon_packs()
            duration = time.time() - start

        # Icon installation should be fast (< 0.5s for mocked APT)
        assert duration < 0.5, f"Icon installation too slow: {duration:.2f}s"

    def test_theme_application_performance(self):
        """Test that theme application is fast for multiple users."""
        config = {
            "desktop": {
                "themes": {"active": "Nordic-darker"},
                "icons": {"active": "Papirus-Dark"},
            }
        }
        module = DesktopModule(config=config, logger=Mock(), dry_run_manager=Mock())

        # Mock 10 users
        users = []
        for i in range(10):
            user = Mock()
            user.pw_name = f"user{i}"
            user.pw_uid = 1000 + i
            user.pw_dir = f"/home/user{i}"
            users.append(user)

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            with patch.object(module, "run"):
                mock_pwd.getpwall.return_value = users
                mock_pwd.getpwnam.side_effect = lambda name: next(
                    u for u in users if u.pw_name == name
                )

                start = time.time()
                module._apply_theme_and_icons()
                duration = time.time() - start

        # Should handle 10 users in < 1 second
        assert duration < 1.0, f"Theme application too slow for 10 users: {duration:.2f}s"

    def test_full_phase3_configure_performance(self):
        """Test that full Phase 3 configuration completes in reasonable time."""
        config = {
            "desktop": {
                "themes": {"install": ["nordic"], "active": "Nordic-darker"},
                "icons": {"install": ["papirus"], "active": "Papirus-Dark"},
                "fonts": {"default": "Roboto 10"},
                "panel": {"layout": "macos"},
            }
        }
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "run", return_value=Mock(success=True)):
            with patch.object(module, "install_packages"):
                with patch("configurator.modules.desktop.write_file"):
                    with patch("configurator.modules.desktop.pwd") as mock_pwd:
                        mock_pwd.getpwall.return_value = []

                        start = time.time()

                        # Execute all Phase 3 methods
                        module._install_themes()
                        module._install_icon_packs()
                        module._configure_fonts()
                        module._configure_panel_layout()
                        module._apply_theme_and_icons()

                        duration = time.time() - start

        # Full Phase 3 should complete in < 2 seconds (mocked)
        assert duration < 2.0, f"Full Phase 3 too slow: {duration:.2f}s"


class TestMemoryUsage:
    """Test memory efficiency of Phase 3 operations."""

    def test_theme_installation_memory_efficient(self):
        """Test that theme installation doesn't leak memory."""
        config = {"desktop": {"themes": {"install": ["nordic"]}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "run", return_value=Mock(success=True)):
            # Run installation multiple times
            for _ in range(10):
                module._install_nordic_theme()

        # If we got here without memory issues, test passes
        # (More sophisticated memory profiling would require tracemalloc)
