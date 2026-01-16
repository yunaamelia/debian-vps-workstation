#!/usr/bin/env python3
import subprocess
import sys


def run_benchmarks():
    print("Running Suite of Benchmarks...")
    try:
        subprocess.run(
            [sys.executable, "configurator/benchmarks/installation_speed.py"], check=True
        )
        print("\n" + "-" * 40 + "\n")
        subprocess.run([sys.executable, "configurator/benchmarks/test_memory_usage.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_benchmarks()
