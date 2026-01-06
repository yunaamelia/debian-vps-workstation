"""
Unit tests for PackageCacheManager.
"""

import hashlib
import json
import shutil
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timedelta
from pathlib import Path

from configurator.core.package_cache import CachedPackage, PackageCacheManager


class TestPackageCacheManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.test_dir) / "cache"
        self.manager = PackageCacheManager(
            cache_dir=self.cache_dir,
            max_size_gb=0.001,  # ~1MB for testing
            logger=unittest.mock.MagicMock(),
        )

        # Create dummy package file
        self.pkg_file = Path(self.test_dir) / "test_pkg.deb"
        with open(self.pkg_file, "wb") as f:
            f.write(b"test content" * 100)  # ~1.2KB

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test cache initialization."""
        self.assertTrue(self.cache_dir.exists())
        self.assertTrue((self.cache_dir / "cache_index.json").exists())
        self.assertTrue((self.cache_dir / "cache_stats.json").exists())
        self.assertEqual(len(self.manager._index), 0)

    def test_add_package(self):
        """Test adding a package to cache."""
        success = self.manager.add_package(
            "test-pkg", "1.0.0", self.pkg_file, "http://example.com/pkg.deb"
        )

        self.assertTrue(success)
        self.assertTrue(self.manager.has_package("test-pkg", "1.0.0"))

        # Verify file in cache
        cached_files = list(self.cache_dir.glob("*.deb"))
        self.assertEqual(len(cached_files), 1)
        self.assertIn("test-pkg_1.0.0", cached_files[0].name)

        # Verify index
        key = self.manager._make_cache_key("test-pkg", "1.0.0")
        self.assertIn(key, self.manager._index)
        self.assertEqual(self.manager._index[key].download_url, "http://example.com/pkg.deb")

    def test_get_package(self):
        """Test retrieving a package."""
        self.manager.add_package("test-pkg", "1.0.0", self.pkg_file, "http://url")

        path = self.manager.get_package("test-pkg", "1.0.0")
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())

        # Verify access updated
        key = self.manager._make_cache_key("test-pkg", "1.0.0")
        self.assertEqual(self.manager._index[key].access_count, 1)

        # Verify stats
        stats = self.manager.get_stats()
        self.assertEqual(stats["total_cache_hits"], 1)

    def test_eviction(self):
        """Test LRU eviction."""
        # Create a manager with very small size limit
        small_manager = PackageCacheManager(
            cache_dir=self.cache_dir, max_size_gb=0.000001, logger=unittest.mock.MagicMock()  # 1KB
        )

        # Create 2 package files, each larger than 1KB
        pkg1 = Path(self.test_dir) / "pkg1.deb"
        with open(pkg1, "wb") as f:
            f.write(b"a" * 2000)  # 2KB

        pkg2 = Path(self.test_dir) / "pkg2.deb"
        with open(pkg2, "wb") as f:
            f.write(b"b" * 2000)  # 2KB

        # Add first package (should succeed but fill cache)
        small_manager.add_package("pkg1", "1.0", pkg1, "url1")
        self.assertTrue(small_manager.has_package("pkg1", "1.0"))

        # Simulate accessing pkg1
        time_access = datetime.now() - timedelta(minutes=10)
        key1 = small_manager._make_cache_key("pkg1", "1.0")
        small_manager._index[key1].last_accessed = time_access

        # Add second package (should force eviction of pkg1)
        small_manager.add_package("pkg2", "1.0", pkg2, "url2")

        # Verify pkg1 gone, pkg2 present
        self.assertFalse(small_manager.has_package("pkg1", "1.0"))
        self.assertTrue(small_manager.has_package("pkg2", "1.0"))

    def test_integrity_verification(self):
        """Test hash verification."""
        self.manager.add_package("test-pkg", "1.0.0", self.pkg_file, "http://url")

        # Corrupt the file
        key = self.manager._make_cache_key("test-pkg", "1.0.0")
        filename = self.manager._index[key].filename
        with open(self.cache_dir / filename, "wb") as f:
            f.write(b"corrupted")

        # Try to get it
        path = self.manager.get_package("test-pkg", "1.0.0")
        self.assertIsNone(path)

        # Should be removed from index
        self.assertFalse(self.manager.has_package("test-pkg", "1.0.0"))

    def test_clear_cache(self):
        """Test clearing cache."""
        self.manager.add_package("test-pkg", "1.0.0", self.pkg_file, "http://url")

        # Clear all
        removed = self.manager.clear_cache()
        self.assertEqual(removed, 1)
        self.assertEqual(len(self.manager._index), 0)
        self.assertEqual(len(list(self.cache_dir.glob("*.deb"))), 0)

    def test_clear_cache_older_than(self):
        """Test clearing old packages."""
        self.manager.add_package("old-pkg", "1.0", self.pkg_file, "url")
        self.manager.add_package("new-pkg", "1.0", self.pkg_file, "url")

        # Manipulate last_accessed
        key_old = self.manager._make_cache_key("old-pkg", "1.0")
        self.manager._index[key_old].last_accessed = datetime.now() - timedelta(days=10)

        # Clear older than 5 days
        removed = self.manager.clear_cache(older_than_days=5)

        self.assertEqual(removed, 1)
        self.assertFalse(self.manager.has_package("old-pkg", "1.0"))
        self.assertTrue(self.manager.has_package("new-pkg", "1.0"))


if __name__ == "__main__":
    unittest.main()
