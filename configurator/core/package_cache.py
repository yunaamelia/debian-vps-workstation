"""
Package Cache Manager for optimizing bandwidth and installation speed.

Handles storage, indexing, retrieval, and eviction of cached packages.
"""

import hashlib
import json
import logging
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CachedPackage:
    """Represents a cached package"""

    name: str
    version: str
    filename: str
    original_filename: str
    size_bytes: int
    download_url: str
    hash_sha256: str
    cached_at: datetime
    last_accessed: datetime
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "size_bytes": self.size_bytes,
            "download_url": self.download_url,
            "hash_sha256": self.hash_sha256,
            "cached_at": self.cached_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedPackage":
        """Deserialize from dictionary"""
        return cls(
            name=data["name"],
            version=data["version"],
            filename=data["filename"],
            original_filename=data.get(
                "original_filename", data["filename"]
            ),  # duplicate filename if missing
            size_bytes=data["size_bytes"],
            download_url=data["download_url"],
            hash_sha256=data["hash_sha256"],
            cached_at=datetime.fromisoformat(data["cached_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
        )


class PackageCacheManager:
    """
    Manages package cache for faster installations.

    Features:
    - Automatic caching of downloaded .deb files
    - Cache size management (configurable limit)
    - LRU (Least Recently Used) eviction
    - SHA256 verification
    - Cache statistics and reporting
    - Thread-safe operations
    """

    DEFAULT_CACHE_DIR = Path("/var/cache/debian-vps-configurator/packages")
    DEFAULT_MAX_SIZE_GB = 10.0
    INDEX_FILE = "cache_index.json"
    STATS_FILE = "cache_stats.json"

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_size_gb: float = DEFAULT_MAX_SIZE_GB,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize package cache manager.

        Args:
            cache_dir: Directory for cached packages
            max_size_gb: Maximum cache size in GB
            logger: Logger instance
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.logger = logger or logging.getLogger(__name__)

        # Thread safety
        self._lock = threading.Lock()

        # Initialize cache
        self._ensure_cache_dir()
        self._index: Dict[str, CachedPackage] = {}
        self._load_index()
        self._stats = self._load_stats()

        # Ensure persistence files exist
        if not (self.cache_dir / self.INDEX_FILE).exists():
            self._save_index()

        if not (self.cache_dir / self.STATS_FILE).exists():
            self._save_stats()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            self.logger.debug(f"Cache directory: {self.cache_dir}")
        except Exception as e:
            self.logger.debug(f"Could not create system cache directory: {e}")
            # Fallback to user cache
            self.cache_dir = Path.home() / ".cache/debian-vps-configurator/packages"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Using fallback cache directory: {self.cache_dir}")

    def _load_index(self) -> None:
        """Load cache index from disk"""
        index_file = self.cache_dir / self.INDEX_FILE

        if not index_file.exists():
            self.logger.debug("No cache index found, starting fresh")
            return

        try:
            with open(index_file, "r") as f:
                data = json.load(f)

            self._index = {key: CachedPackage.from_dict(pkg_data) for key, pkg_data in data.items()}

            self.logger.info(f"Loaded cache index: {len(self._index)} packages")

        except Exception as e:
            self.logger.warning(f"Failed to load cache index, starting fresh: {e}")
            self._index = {}

    def _save_index(self) -> None:
        """Save cache index to disk"""
        index_file = self.cache_dir / self.INDEX_FILE

        try:
            data = {key: pkg.to_dict() for key, pkg in self._index.items()}

            with open(index_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")

    def _load_stats(self) -> Dict[str, Any]:
        """Load cache statistics"""
        stats_file = self.cache_dir / self.STATS_FILE

        if not stats_file.exists():
            return {
                "total_downloads": 0,
                "total_cache_hits": 0,
                "total_bytes_saved": 0,
                "cache_created_at": datetime.now().isoformat(),
            }

        try:
            with open(stats_file, "r") as f:
                stats: Dict[str, Any] = json.load(f)
                return stats
        except Exception as e:
            self.logger.warning(f"Failed to load stats, resetting: {e}")
            return {}

    def _save_stats(self) -> None:
        """Save cache statistics"""
        stats_file = self.cache_dir / self.STATS_FILE

        try:
            with open(stats_file, "w") as f:
                json.dump(self._stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save stats: {e}")

    def _make_cache_key(self, package_name: str, version: str) -> str:
        """Generate cache key for package"""
        return f"{package_name}_{version}"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _get_cache_size(self) -> int:
        """Get total size of cache in bytes"""
        total = 0
        for pkg in self._index.values():
            total += pkg.size_bytes
        return total

    def _evict_lru_packages(self, required_space: int) -> None:
        """
        Evict least recently used packages to free space.

        Args:
            required_space: Bytes needed to free
        """
        if not self._index:
            return

        # Sort by last_accessed (oldest first)
        sorted_packages = sorted(self._index.values(), key=lambda p: p.last_accessed)

        freed = 0
        evicted = []

        for pkg in sorted_packages:
            if freed >= required_space:
                break

            # Remove package file
            pkg_path = self.cache_dir / pkg.filename
            try:
                if pkg_path.exists():
                    pkg_path.unlink()

                # Even if file didn't exist, we count it as freed from our tracking
                freed += pkg.size_bytes
                evicted.append(pkg.name)
                self.logger.debug(f"Evicted: {pkg.name} ({pkg.size_bytes / 1024 / 1024:.1f}MB)")
            except Exception as e:
                self.logger.warning(f"Failed to evict {pkg.name}: {e}")

        # Remove from index
        for pkg_name in evicted:
            # We need to find the key for this package name (a bit inefficient but safe)
            # Actually we iterated over values, we should have kept keys or looked them up
            keys_to_remove = []
            for k, v in self._index.items():
                if v.name == pkg_name:
                    keys_to_remove.append(k)
                    break

            for k in keys_to_remove:
                del self._index[k]

        if evicted:
            self.logger.info(f"Evicted {len(evicted)} packages to free {freed / 1024 / 1024:.1f}MB")
            self._save_index()

    def has_package(self, package_name: str, version: str) -> bool:
        """
        Check if package is in cache.

        Args:
            package_name: Name of package
            version: Version string

        Returns:
            True if package is cached
        """
        with self._lock:
            key = self._make_cache_key(package_name, version)

            if key not in self._index:
                return False

            # Verify file exists
            pkg = self._index[key]
            pkg_path = self.cache_dir / pkg.filename

            if not pkg_path.exists():
                self.logger.warning(f"Cache entry exists but file missing: {pkg.filename}")
                del self._index[key]
                self._save_index()
                return False

            return True

    def get_package(self, package_name: str, version: str) -> Optional[Path]:
        """
        Get cached package path.

        Args:
            package_name: Name of package
            version: Version string

        Returns:
            Path to cached package file, or None if not cached
        """
        with self._lock:
            key = self._make_cache_key(package_name, version)

            if key not in self._index:
                return None

            pkg = self._index[key]
            pkg_path = self.cache_dir / pkg.filename

            if not pkg_path.exists():
                self.logger.warning(f"Cached file missing: {pkg.filename}")
                del self._index[key]
                self._save_index()
                return None

            # Verify hash
            if not self._verify_hash(pkg_path, pkg.hash_sha256):
                self.logger.error(f"Hash mismatch for {pkg.filename}, removing from cache")
                pkg_path.unlink()
                del self._index[key]
                self._save_index()
                return None

            # Update access info
            pkg.last_accessed = datetime.now()
            pkg.access_count += 1
            self._save_index()

            # Update stats
            self._stats["total_cache_hits"] += 1
            self._stats["total_bytes_saved"] += pkg.size_bytes
            self._save_stats()

            self.logger.info(
                f"✅ Cache HIT: {package_name} {version} "
                f"({pkg.size_bytes / 1024 / 1024:.1f}MB saved)"
            )

            return pkg_path

    def _verify_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file hash matches expected"""
        try:
            actual_hash = self._calculate_file_hash(file_path)
            return actual_hash == expected_hash
        except Exception as e:
            self.logger.error(f"Hash verification failed: {e}")
            return False

    def add_package(
        self, package_name: str, version: str, file_path: Path, download_url: str
    ) -> bool:
        """
        Add package to cache.

        Args:
            package_name: Name of package
            version: Version string
            file_path: Path to downloaded package file
            download_url: Original download URL

        Returns:
            True if successfully cached
        """
        with self._lock:
            if not file_path.exists():
                self.logger.error(f"Cannot cache non-existent file: {file_path}")
                return False

            # Get file info
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            filename = f"{package_name}_{version}_{file_path.name}"

            # Check if cache size limit would be exceeded
            current_size = self._get_cache_size()
            if current_size + file_size > self.max_size_bytes:
                required_space = (current_size + file_size) - self.max_size_bytes
                self.logger.info(f"Cache full, evicting {required_space / 1024 / 1024:.1f}MB")
                self._evict_lru_packages(required_space)

            # Copy to cache
            cache_path = self.cache_dir / filename
            try:
                shutil.copy2(file_path, cache_path)
                self.logger.debug(f"Copied to cache: {cache_path}")
            except Exception as e:
                self.logger.error(f"Failed to copy to cache: {e}")
                return False

            # Add to index
            key = self._make_cache_key(package_name, version)
            now = datetime.now()

            self._index[key] = CachedPackage(
                name=package_name,
                version=version,
                filename=filename,
                original_filename=file_path.name,
                size_bytes=file_size,
                download_url=download_url,
                hash_sha256=file_hash,
                cached_at=now,
                last_accessed=now,
                access_count=0,
            )

            self._save_index()

            # Update stats
            self._stats["total_downloads"] += 1
            self._save_stats()

            self.logger.info(
                f"✅ Cached: {package_name} {version} ({file_size / 1024 / 1024:.1f}MB)"
            )

            return True

    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cache (all or packages older than specified days).

        Args:
            older_than_days: Only clear packages older than this many days

        Returns:
            Number of packages removed
        """
        with self._lock:
            if older_than_days is None:
                # Clear everything
                removed = 0
                for pkg in self._index.values():
                    pkg_path = self.cache_dir / pkg.filename
                    try:
                        if pkg_path.exists():
                            pkg_path.unlink()
                            removed += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove {pkg.filename}: {e}")

                self._index.clear()
                self._save_index()

                self.logger.info(f"Cleared entire cache: {removed} packages removed")
                return removed

            else:
                # Clear old packages
                cutoff = datetime.now() - timedelta(days=older_than_days)
                to_remove = []

                for key, pkg in self._index.items():
                    if pkg.last_accessed < cutoff:
                        pkg_path = self.cache_dir / pkg.filename
                        try:
                            if pkg_path.exists():
                                pkg_path.unlink()
                            to_remove.append(key)
                        except Exception as e:
                            self.logger.warning(f"Failed to remove {pkg.filename}: {e}")

                for key in to_remove:
                    del self._index[key]

                self._save_index()

                self.logger.info(
                    f"Cleared packages older than {older_than_days} days: "
                    f"{len(to_remove)} packages removed"
                )

                return len(to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            current_size = self._get_cache_size()

            return {
                "cache_dir": str(self.cache_dir),
                "total_packages": len(self._index),
                "total_size_bytes": current_size,
                "total_size_mb": current_size / 1024 / 1024,
                "max_size_mb": self.max_size_bytes / 1024 / 1024,
                "usage_percent": (
                    (current_size / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0
                ),
                "total_downloads": self._stats.get("total_downloads", 0),
                "total_cache_hits": self._stats.get("total_cache_hits", 0),
                "total_bytes_saved": self._stats.get("total_bytes_saved", 0),
                "total_mb_saved": self._stats.get("total_bytes_saved", 0) / 1024 / 1024,
                "cache_hit_rate": (
                    self._stats.get("total_cache_hits", 0)
                    / (
                        self._stats.get("total_downloads", 0)
                        + self._stats.get("total_cache_hits", 0)
                    )
                    if (
                        self._stats.get("total_downloads", 0)
                        + self._stats.get("total_cache_hits", 0)
                    )
                    > 0
                    else 0.0
                ),
                "cache_created_at": self._stats.get("cache_created_at"),
            }

    def list_packages(self) -> List[CachedPackage]:
        """
        List all cached packages.

        Returns:
            List of CachedPackage objects
        """
        with self._lock:
            return list(self._index.values())
