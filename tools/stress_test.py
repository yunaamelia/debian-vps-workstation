#!/usr/bin/env python3
"""
Stress Test for Parallel Module Execution (Checks 3.1 & 3.2)
Simulates concurrent file writes and state updates with 50 threads.
"""

import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from configurator.core.parallel import ParallelModuleExecutor
from configurator.modules.base import ConfigurationModule
from configurator.utils.file_lock import file_lock


# Check 3.1: Concurrent File Writes
def stress_test_file_writes():
    print("Check 3.1: Concurrent File Writes (50 threads)")
    print("=" * 60)

    test_file = Path("stress_test.log")
    if test_file.exists():
        test_file.unlink()

    # Initialize file
    test_file.write_text("START\n")

    def worker(id):
        # Write 10 times with random sleep
        for i in range(10):
            time.sleep(random.random() * 0.05)
            with file_lock(str(test_file)):
                with open(test_file, "a") as f:
                    # Write atomic line
                    f.write(f"worker-{id}-write-{i}\n")

    start = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in as_completed(futures):
            f.result()  # Check for exceptions

    duration = time.time() - start

    # Verify content
    lines = test_file.read_text().splitlines()
    expected = 1 + (50 * 10)  # START + 500 writes

    print(f"Executed 50 threads x 10 writes in {duration:.2f}s")
    print(f"Lines written: {len(lines)}")

    if len(lines) == expected:
        print("✅ File integrity maintained (Locking works)")
    else:
        print(f"❌ File corruption: {len(lines)} != {expected}")
        return False

    test_file.unlink()
    return True


# Check 3.2: Parallel State Updates
class StressModule(ConfigurationModule):
    def __init__(self, name):
        self.name = name
        self.state = 0

    def validate(self):
        return True

    def configure(self):
        # Simulate work
        time.sleep(random.random() * 0.1)
        return True

    def verify(self):
        return True


def stress_test_state_updates():
    print("\nCheck 3.2: Parallel State Updates")
    print("=" * 60)

    executor = ParallelModuleExecutor(max_workers=20)
    modules = {f"mod-{i}": StressModule(f"mod-{i}") for i in range(50)}
    batches = [[f"mod-{i}" for i in range(50)]]  # Single huge batch

    print("Running 50 modules in parallel...")
    start = time.time()
    results = executor.execute_batches(batches, modules)
    duration = time.time() - start

    # Verify all results collected
    passed = sum(1 for r in results.values() if r)

    print(f"Execution time: {duration:.2f}s")
    print(f"Modules processed: {len(results)}")
    print(f"Successful: {passed}")

    stats = executor.get_execution_stats()
    print(f"Stats collected: {len(stats)}")

    if len(results) == 50 and passed == 50 and len(stats) == 50:
        print("✅ detailed state tracking maintained under load")
        return True
    else:
        print("❌ Lost state updates or results")
        return False


if __name__ == "__main__":
    success_writes = stress_test_file_writes()
    success_state = stress_test_state_updates()

    if success_writes and success_state:
        print("\n✅ All Stress Tests Passed")
        sys.exit(0)
    else:
        print("\n❌ Stress Tests Failed")
        sys.exit(1)
