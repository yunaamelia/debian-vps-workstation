#!/usr/bin/env python3
"""
Benchmark Parallel Module Execution
Time sequential vs parallel execution to verify performance improvements.
"""

import sys
import time

from configurator.core.parallel import ParallelModuleExecutor
from configurator.modules.base import ConfigurationModule


class TimedModule(ConfigurationModule):
    """Mock module with configurable execution time"""

    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    def validate(self):
        return True

    def configure(self):
        time.sleep(self.duration)
        return True

    def verify(self):
        return True


def benchmark_parallel_performance():
    """Benchmark parallel vs sequential execution"""

    print("┌─────────────────────────────────────────────────────────┐")
    print("│ PARALLEL EXECUTION BENCHMARK REPORT                     │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│ Profile: Synthetic (10 modules, 1.0s each)              │")
    print("│ System: Simulated                                       │")
    print("├─────────────────────────────────────────────────────────┤")

    # Create 10 modules, each taking 1 second
    modules = {f"module-{i}": TimedModule(f"module-{i}", duration=1.0) for i in range(10)}

    # Test 1: Sequential execution
    print("│ Testing Sequential Execution...                         │")
    start = time.time()
    for module in modules.values():
        module.validate()
        module.configure()
        module.verify()
    sequential_time = time.time() - start

    # Test 2: Parallel execution (3 workers)
    print("│ Testing Parallel Execution (3 workers)...               │")
    executor = ParallelModuleExecutor(max_workers=3)

    # All modules in one batch (independent)
    batches = [list(modules.keys())]

    start = time.time()
    executor.execute_batches(batches, modules)
    parallel_time = time.time() - start

    # Calculate speedup
    speedup = sequential_time / parallel_time
    time_saved = sequential_time - parallel_time
    percent_saved = (time_saved / sequential_time) * 100

    print(f"│ Sequential Execution: {sequential_time:.2f}s                       │")
    print(f"│ Parallel Execution: {parallel_time:.2f}s                         │")
    print(f"│ Time Saved: {time_saved:.2f}s ({percent_saved:.1f}%)                   │")
    print(f"│ Speedup Factor: {speedup:.2f}x                              │")
    print("└─────────────────────────────────────────────────────────┘")

    # Validate performance improvement
    # With 3 workers, 10 modules should take ~4s (ceil(10/3) × 1s = 4s)
    # Allow some overhead, so < 5s
    if parallel_time < 5.0 and percent_saved >= 25.0:
        print(f"\n✅ Performance target met: {parallel_time:.2f}s < 5.0s and > 25% savings")
        return True
    else:
        print(f"\n❌ Performance target missed: {parallel_time:.2f}s >= 5.0s or < 25% savings")
        return False


if __name__ == "__main__":
    sys.exit(0 if benchmark_parallel_performance() else 1)
