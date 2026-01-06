#!/usr/bin/env python3
"""
Benchmark Package Cache Performance.

This script demonstrates the speed improvement of the Package Cache
by simulating package "installation" (copying) with and without cache.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path


def create_dummy_package(path: Path, size_mb: int):
    """Create a dummy file of specified size."""
    print(f"Generating {size_mb}MB dummy package...")
    with open(path, "wb") as f:
        f.seek(size_mb * 1024 * 1024 - 1)
        f.write(b"\0")


def benchmark():
    from configurator.core.package_cache import PackageCacheManager

    print("=" * 60)
    print("Package Cache Benchmark")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        source_dir = temp_dir / "internet_source"
        apt_dir = temp_dir / "apt_archives"
        cache_dir = temp_dir / "custom_cache"

        source_dir.mkdir()
        apt_dir.mkdir()
        cache_dir.mkdir()

        # Determine package size (larger is better for demo)
        PKG_SIZE_MB = 100
        pkg_count = 5
        packages = []

        print(f"Preparing {pkg_count} packages of {PKG_SIZE_MB}MB each...")
        for i in range(pkg_count):
            name = f"pkg_{i}.deb"
            path = source_dir / name
            create_dummy_package(path, PKG_SIZE_MB)
            packages.append(path)

        # Initialize Manager
        manager = PackageCacheManager(cache_dir=cache_dir)

        print("\n--- Phase 1: Cold Install (No Cache) ---")
        start_time = time.time()

        # Simulate download (copy from source to apt)
        # In reality this is network download
        for pkg in packages:
            shutil.copy2(pkg, apt_dir / pkg.name)
            # Add to cache (simulate capture)
            manager.add_package(f"pkg_{pkg.name}", "1.0", apt_dir / pkg.name, "http://fake")

        cold_duration = time.time() - start_time
        print(f"Time taken: {cold_duration:.2f}s")
        print(f"Throughput: {(pkg_count * PKG_SIZE_MB) / cold_duration:.2f} MB/s")

        # Clear APT dir
        for p in apt_dir.glob("*.deb"):
            p.unlink()

        print("\n--- Phase 2: Warm Install (With Cache) ---")
        start_time = time.time()

        # Simulate restore from cache
        cache_hits = 0
        for pkg in packages:
            # We assume manager has it.
            # logic similar to prepare_apt_cache
            # Find in cache (we know the name format we used)
            cached_path = manager.get_package(f"pkg_{pkg.name}", "1.0")
            if cached_path:
                shutil.copy2(cached_path, apt_dir / pkg.name)
                cache_hits += 1

        warm_duration = time.time() - start_time
        print(f"Time taken: {warm_duration:.2f}s")
        print(f"Throughput: {(pkg_count * PKG_SIZE_MB) / warm_duration:.2f} MB/s")
        print(f"Cache Hits: {cache_hits}/{pkg_count}")

        if cold_duration > 0:
            speedup = cold_duration / warm_duration
            print(f"\nSpeedup: {speedup:.2f}x")
            print(f"Bandwidth Saved: {pkg_count * PKG_SIZE_MB} MB")
        else:
            print("Benchmarks too fast to measure.")


if __name__ == "__main__":
    # Setup path to module
    import sys

    sys.path.append(os.getcwd())

    try:
        benchmark()
    except ImportError:
        print("Error: Could not import configurator. Run from project root.")
    except Exception as e:
        print(f"Error: {e}")
