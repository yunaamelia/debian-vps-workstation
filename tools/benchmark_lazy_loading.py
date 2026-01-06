import importlib
import os
import subprocess
import sys
import time


def benchmark_startup():
    print(f"Benchmarking CLI startup...")

    times = []
    for _ in range(10):
        start = time.perf_counter()
        subprocess.run(["vps-configurator", "--help"], capture_output=True)
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    min_time = min(times)

    print(f"Average time: {avg_time:.4f}s")
    print(f"Min time: {min_time:.4f}s")

    if avg_time < 0.2:
        print("[PASS] Startup time < 0.2s (Acceptable for Python CLI)")
    else:
        print(f"[WARN] Startup time {avg_time:.4f}s > 0.2s")


def check_imports():
    print("\nChecking imports...")

    # We want to check what modules are loaded when we import configurator.cli
    # We need to run this in a subprocess to avoid our own imports polluting

    code = """
import sys
import time

start_time = time.perf_counter()
import configurator.cli
end_time = time.perf_counter()

print(f"Import time: {end_time - start_time:.4f}s")

# Check if Installer is loaded
if 'configurator.core.installer' in sys.modules:
    print("FAIL: configurator.core.installer IS loaded")
    sys.exit(1)
else:
    print("PASS: configurator.core.installer is NOT loaded")

# Check if PackageCacheManager is loaded (it is lazy in CLI)
if 'configurator.core.package_cache' in sys.modules:
    print("FAIL: configurator.core.package_cache IS loaded")
    sys.exit(1)
else:
    print("PASS: configurator.core.package_cache is NOT loaded")
"""

    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Import check FAILED")
        print(result.stderr)
        sys.exit(1)
    else:
        print("Import check PASSED")


if __name__ == "__main__":
    benchmark_startup()
    check_imports()
