"""
Unit tests for AptCacheIntegration.
"""

import shutil
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from configurator.core.package_cache import CachedPackage, PackageCacheManager
from configurator.utils.apt_cache import AptCacheIntegration


class TestAptCacheIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.test_dir) / "custom_cache"
        self.apt_dir = Path(self.test_dir) / "apt_archives"

        self.apt_dir.mkdir(parents=True)

        # Mock PackageCacheManager
        self.mock_manager = unittest.mock.MagicMock(spec=PackageCacheManager)
        self.mock_manager.cache_dir = self.cache_dir
        self.cache_dir.mkdir()

        self.integration = AptCacheIntegration(
            cache_manager=self.mock_manager, logger=unittest.mock.MagicMock()
        )
        # Patch the constant to point to our test dir
        self.integration.APT_ARCHIVES_DIR = self.apt_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_prepare_apt_cache(self):
        """Test restoring packages to APT cache."""
        # Setup mock package in custom cache
        pkg_name = "testpackage"
        pkg_version = "1.0"
        filename = "testpackage_1.0_amd64.deb"

        # Create dummy file in custom cache
        pkg_path = self.cache_dir / filename
        with open(pkg_path, "wb") as f:
            f.write(b"content")

        # Mock cached package object
        cached_pkg = unittest.mock.Mock(spec=CachedPackage)
        cached_pkg.name = pkg_name
        cached_pkg.version = pkg_version
        cached_pkg.filename = filename
        cached_pkg.original_filename = filename  # Added
        cached_pkg.size_bytes = 7

        self.mock_manager.list_packages.return_value = [cached_pkg]

        # Run prepare
        count = self.integration.prepare_apt_cache([pkg_name])

        self.assertEqual(count, 1)
        self.assertTrue((self.apt_dir / filename).exists())
        self.assertEqual((self.apt_dir / filename).read_bytes(), b"content")

    def test_prepare_apt_cache_already_exists(self):
        """Test prepare skips if file already exists in APT cache."""
        filename = "pkg_1.0_amd64.deb"

        # Create file in APT cache
        apt_file = self.apt_dir / filename
        with open(apt_file, "wb") as f:
            f.write(b"content")

        # Create file in custom cache
        pkg_path = self.cache_dir / filename
        with open(pkg_path, "wb") as f:
            f.write(b"content")
        # Mock package
        mock_pkg = unittest.mock.Mock()
        mock_pkg.name = "pkg"
        mock_pkg.filename = "pkg_1.0_amd64.deb"
        mock_pkg.original_filename = "pkg_1.0_amd64.deb"  # Added
        mock_pkg.size_bytes = 7

        self.mock_manager.list_packages.return_value = [mock_pkg]

        # Mock shutil.copy2 to see if it gets called
        with unittest.mock.patch("shutil.copy2") as mock_copy:
            count = self.integration.prepare_apt_cache(["pkg"])

            # Should count as 0 restored since we skipped copy, actually logic says:
            # if exists and size match -> continue (not counted)
            # return value is "restored_count"
            self.assertEqual(count, 0)
            mock_copy.assert_not_called()

    def test_capture_new_packages(self):
        """Test capturing new packages from APT cache."""
        # Create a new deb file in APT dir
        filename = "newpkg_2.0_amd64.deb"
        apt_file = self.apt_dir / filename
        with open(apt_file, "wb") as f:
            f.write(b"new content")

        # Mock manager says it doesn't have it
        self.mock_manager.has_package.return_value = False
        self.mock_manager.add_package.return_value = True

        # Run capture
        count = self.integration.capture_new_packages()

        self.assertEqual(count, 1)
        self.mock_manager.add_package.assert_called_once()
        args = self.mock_manager.add_package.call_args
        self.assertEqual(args[1]["package_name"], "newpkg")
        self.assertEqual(args[1]["version"], "2.0")
        self.assertEqual(args[1]["download_url"], "local-apt-cache")

    def test_capture_skips_existing(self):
        """Test capture skips packages already in custom cache."""
        filename = "existing_1.0_amd64.deb"
        apt_file = self.apt_dir / filename
        with open(apt_file, "wb") as f:
            f.write(b"content")

        # Mock manager says it HAS it
        self.mock_manager.has_package.return_value = True

        count = self.integration.capture_new_packages()

        self.assertEqual(count, 0)
        self.mock_manager.add_package.assert_not_called()


if __name__ == "__main__":
    unittest.main()
