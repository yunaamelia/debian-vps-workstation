"""
Integration tests for Package Cache implementation.
Verifies interaction between Module, Installer, AptCacheIntegration and PackageCacheManager.
"""

import logging
import shutil
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from configurator.config import ConfigManager
from configurator.core.container import Container
from configurator.core.installer import Installer
from configurator.core.package_cache import PackageCacheManager
from configurator.modules.base import ConfigurationModule


class MockModule(ConfigurationModule):
    name = "test-module"

    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


class TestPackageCacheIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.test_dir) / "custom_cache"
        self.apt_dir = Path(self.test_dir) / "apt_archives"
        self.os_cache_dir = Path(self.test_dir) / "os_cache"  # fallback

        # Create mocked directories
        self.cache_dir.mkdir()
        self.apt_dir.mkdir()

        # Patch where apt directory is expected
        self.apt_patch = unittest.mock.patch(
            "configurator.utils.apt_cache.AptCacheIntegration.APT_ARCHIVES_DIR", self.apt_dir
        )
        self.apt_patch.start()

        # Setup config
        self.config = ConfigManager(profile="beginner")
        self.config.set("performance.package_cache.enabled", True)
        self.config.set("performance.package_cache.max_size_gb", 1.0)
        self.config.set("interactive", False)  # disable failing circuit breaker prompt

        # Setup Logger
        self.logger = logging.getLogger("test")

        # Setup Container
        self.container = Container()

    def tearDown(self):
        self.apt_patch.stop()
        shutil.rmtree(self.test_dir)

    def test_cache_integration_in_installer(self):
        """Test that installer correctly initializes cache manager."""
        installer = Installer(config=self.config, logger=self.logger, container=self.container)

        self.assertIsNotNone(installer.package_cache_manager)
        self.assertIsInstance(installer.package_cache_manager, PackageCacheManager)

        # Verify it was registered in container
        self.assertTrue(self.container.has("package_cache_manager"))
        self.assertEqual(
            self.container.get("package_cache_manager"), installer.package_cache_manager
        )

    def test_module_uses_cache_flow(self):
        """Test the full flow in a module's install_packages method."""

        # 1. Setup Installer and Manager manually to control paths
        manager = PackageCacheManager(cache_dir=self.cache_dir, logger=self.logger)

        installer = Installer(config=self.config, logger=self.logger, container=self.container)
        # Force overwrite the manager with our correctly-pathed one
        installer.package_cache_manager = manager
        self.container.singleton("package_cache_manager", lambda: manager)

        # 2. Instantiate a module
        # We use strict factory registration logic or just manual instantiation
        module = MockModule(
            config={},
            logger=self.logger,
            package_cache_manager=manager,
            circuit_breaker_manager=self.container.get("circuit_breaker_manager"),
            dry_run_manager=self.container.get("dry_run_manager"),
        )

        # 3. Mock run_command to verify and simulate side effects
        with unittest.mock.patch.object(module, "run") as mock_run:
            mock_run.return_value.success = True

            # Scenario A: Capture new package
            # Simulate apt-get install creating a file in apt_dir
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if "apt-get install" in cmd:
                    # Create dummy file in apt_dir as if APT downloaded it
                    # Logic in apt_cache looks for *.deb
                    with open(self.apt_dir / "newpkg_1.0_amd64.deb", "wb") as f:
                        f.write(b"downloaded content")
                return unittest.mock.Mock(success=True)

            mock_run.side_effect = side_effect

            # Run install
            success = module.install_packages(["newpkg"])

            self.assertTrue(success)

            # Verify capture happened - file should be in custom cache now
            self.assertTrue(manager.has_package("newpkg", "1.0"))
            pkg_path = manager.get_package("newpkg", "1.0")
            self.assertTrue(pkg_path.exists())
            self.assertEqual(pkg_path.read_bytes(), b"downloaded content")

            # Scenario B: Prepare cache (restore)
            # Remove file from apt dir to simulate clean state
            (self.apt_dir / "newpkg_1.0_amd64.deb").unlink()

            # Verify it's gone
            self.assertFalse((self.apt_dir / "newpkg_1.0_amd64.deb").exists())

            # Verify it's in cache
            print(f"DEBUG: Cache contents: {[p.filename for p in manager.list_packages()]}")
            self.assertTrue(manager.has_package("newpkg", "1.0"))

            # Reset mock
            mock_run.reset_mock()
            mock_run.side_effect = None
            mock_run.return_value.success = True

            # Run install again
            print("DEBUG: Running install_packages again")
            success = module.install_packages(["newpkg"])

            self.assertTrue(success)

            # Verify file was restored to apt dir
            if not (self.apt_dir / "newpkg_1.0_amd64.deb").exists():
                print(f"DEBUG: APT dir contents: {list(self.apt_dir.glob('*'))}")

            self.assertTrue((self.apt_dir / "newpkg_1.0_amd64.deb").exists())
            self.assertEqual(
                (self.apt_dir / "newpkg_1.0_amd64.deb").read_bytes(), b"downloaded content"
            )


if __name__ == "__main__":
    unittest.main()
