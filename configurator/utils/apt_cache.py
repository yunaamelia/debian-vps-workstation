"""
Integration between PackageCacheManager and system APT cache.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional

from configurator.core.package_cache import PackageCacheManager


class AptCacheIntegration:
    """
    Handles interaction between the custom PackageCacheManager and
    the system's APT archive cache (/var/cache/apt/archives).
    """

    APT_ARCHIVES_DIR = Path("/var/cache/apt/archives")

    def __init__(self, cache_manager: PackageCacheManager, logger: Optional[logging.Logger] = None):
        self.cache_manager = cache_manager
        self.logger = logger or logging.getLogger(__name__)

    def prepare_apt_cache(self, package_names: List[str]) -> int:
        """
        Copy cached packages to APT's archive directory to avoid re-downloading.

        Args:
            package_names: List of package names to check in cache

        Returns:
            Number of packages restored to APT cache
        """
        if not self.APT_ARCHIVES_DIR.exists():
            self.logger.warning(f"APT archives directory not found: {self.APT_ARCHIVES_DIR}")
            return 0

        restored_count = 0

        # We need to find matching packages in our cache
        # Since we only have names, we'll have to look for latest versions or
        # just any version that matches.
        # But APT is picky about versions. if we put the wrong version, APT will ignore it
        # or error if it expects a specific version.

        # Strategy:
        # Ideally, we would know the exact version APT wants.
        # Without querying `apt-cache policy`, we can't be sure what version will be installed.
        # However, for a bandwidth optimization, we can try to restore what we have.
        # If APT downloads a newer version, so be it.

        # We'll iterate through our cache and see if we have any of the requested packages
        # This is a bit naive if there are multiple versions, but effective for exact matches.

        # Optimization: Create a lookup from simple package name to cached entries
        # detailed lookup needed?

        # For now, let's just restore *all* versions we have for the requested packages.
        # APT will pick the one it needs if the hash matches what it expects.

        cached_packages = self.cache_manager.list_packages()

        for pkg in cached_packages:
            if pkg.name in package_names:
                source_path = self.cache_manager.cache_dir / pkg.filename
                dest_path = self.APT_ARCHIVES_DIR / pkg.original_filename

                # Check if already exists in APT cache
                if dest_path.exists():
                    # Check sizes to be safe?
                    if dest_path.stat().st_size == pkg.size_bytes:
                        continue

                try:
                    if source_path.exists():
                        shutil.copy2(source_path, dest_path)
                        # Ensure root ownership if possible (running as root usually)
                        # os.chown(dest_path, 0, 0)
                        restored_count += 1
                        self.logger.debug(f"Restored to APT cache: {pkg.filename}")
                except Exception as e:
                    self.logger.warning(f"Failed to copy {pkg.filename} to APT cache: {e}")

        if restored_count > 0:
            self.logger.info(f"Restored {restored_count} packages to APT cache")

        return restored_count

    def capture_new_packages(self) -> int:
        """
        Scan APT's archive directory for new .deb files and add them to cache.
        Should be called after apt-get install commands.

        Returns:
            Number of new packages cached
        """
        if not self.APT_ARCHIVES_DIR.exists():
            return 0

        captured_count = 0

        # Initial scan of .deb files in APT archives
        # We exclude partial downloads
        deb_files = list(self.APT_ARCHIVES_DIR.glob("*.deb"))

        for deb_path in deb_files:
            try:
                # We need to parse package name and version from filename
                # Standard format: name_version_arch.deb
                # Example: python3_3.8.2-1ubuntu1_amd64.deb
                # But sometimes it varies (epoch, etc.)

                # A robust way is to use `dpkg-deb --field` but that requires subprocess
                # For a pure python approach, we can try filename parsing
                # name is everything before the first underscore

                filename = deb_path.name
                parts = filename.split("_")

                if len(parts) >= 2:
                    name = parts[0]
                    # version is parts[1] usually
                    version = parts[1]
                else:
                    # Fallback for weird filenames?
                    # Skip for now to be safe
                    continue

                # Check if we already have it
                if self.cache_manager.has_package(name, version):
                    continue

                # Add to cache
                # We don't know the original URL, so we put 'local-apt-cache'
                success = self.cache_manager.add_package(
                    package_name=name,
                    version=version,
                    file_path=deb_path,
                    download_url="local-apt-cache",
                )

                if success:
                    captured_count += 1

            except Exception as e:
                self.logger.warning(f"Failed to capture {deb_path.name}: {e}")

        if captured_count > 0:
            self.logger.info(f"Captured {captured_count} new packages from APT cache")

        return captured_count
