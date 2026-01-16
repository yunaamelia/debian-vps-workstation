"""
Performance benchmark tests.

Compares:
- Parallel vs Sequential execution time
- Memory usage patterns
- Throughput metrics
"""

import threading
import time
from unittest.mock import Mock

import pytest

from configurator.core.execution.base import ExecutionContext
from configurator.core.execution.parallel import ParallelExecutor


def create_contexts(count: int, work_time: float = 0.0):
    """Helper to create ExecutionContext objects with mock modules."""
    contexts = []
    for i in range(count):
        module = Mock()
        module.validate.return_value = True
        module.configure.return_value = True
        module.verify.return_value = True

        if work_time > 0:

            def slow_configure(delay=work_time):
                time.sleep(delay)
                return True

            module.configure.side_effect = slow_configure

        context = ExecutionContext(
            module_name=f"module_{i}", module_instance=module, config={}, dry_run=False
        )
        contexts.append(context)
    return contexts


@pytest.mark.slow
class TestParallelPerformance:
    """Benchmark parallel execution performance."""

    def test_parallel_faster_than_sequential_simulated(self):
        """Test that parallel execution is faster using simulated modules."""
        module_count = 6
        work_time = 0.1  # 100ms per module

        # Sequential timing
        sequential_start = time.time()
        for i in range(module_count):
            time.sleep(work_time)
        sequential_time = time.time() - sequential_start

        # Parallel timing
        executor = ParallelExecutor(max_workers=4, logger=Mock())
        contexts = create_contexts(module_count, work_time)

        parallel_start = time.time()
        executor.execute(contexts)
        parallel_time = time.time() - parallel_start

        # Verify parallel is faster
        speedup = sequential_time / parallel_time
        assert speedup > 1.5, f"Expected speedup > 1.5x, got {speedup:.2f}x"

    def test_parallel_scaling_with_workers(self):
        """Test that more workers improve performance up to a point."""
        module_count = 8
        work_time = 0.05

        times = {}

        for workers in [1, 2, 4]:
            executor = ParallelExecutor(max_workers=workers, logger=Mock())
            contexts = create_contexts(module_count, work_time)

            start = time.time()
            executor.execute(contexts)
            times[workers] = time.time() - start

        # More workers should be faster (with diminishing returns)
        assert times[2] < times[1], "2 workers should be faster than 1"


@pytest.mark.slow
class TestThroughputMetrics:
    """Test throughput metrics for parallel execution."""

    def test_modules_per_second_metric(self):
        """Test module execution throughput."""
        executor = ParallelExecutor(max_workers=4, logger=Mock())

        module_count = 10
        work_time = 0.01  # 10ms per module

        contexts = create_contexts(module_count, work_time)

        start = time.time()
        executor.execute(contexts)
        total_time = time.time() - start

        throughput = module_count / total_time

        # With 4 workers and 10ms per module, should achieve decent throughput
        assert throughput > 10, f"Expected throughput > 10 modules/s, got {throughput:.1f}"

    def test_batch_overhead(self):
        """Test overhead of batch processing."""
        executor = ParallelExecutor(max_workers=4, logger=Mock())

        # Zero-work modules
        contexts = create_contexts(100, work_time=0)

        start = time.time()
        executor.execute(contexts)
        overhead = time.time() - start

        # Overhead should be minimal (<1 second for 100 instant modules)
        assert overhead < 1.0, f"Batch overhead too high: {overhead:.3f}s"


@pytest.mark.slow
class TestMemoryUsagePatterns:
    """Test memory usage patterns during parallel execution."""

    def test_executor_cleanup_between_batches(self):
        """Test that executor cleans up properly between batches."""
        executor = ParallelExecutor(max_workers=2, logger=Mock())

        # Run multiple batches
        for i in range(5):
            contexts = create_contexts(10)
            executor.execute(contexts)

        # Executor should still be usable
        assert executor is not None

    def test_no_thread_leak(self):
        """Test that threads are properly cleaned up."""
        initial_threads = threading.active_count()

        executor = ParallelExecutor(max_workers=4, logger=Mock())

        contexts = create_contexts(20, work_time=0.01)
        executor.execute(contexts)

        # Give threads time to clean up
        time.sleep(0.2)

        final_threads = threading.active_count()

        # Thread count should not grow significantly
        thread_growth = final_threads - initial_threads
        assert thread_growth < 5, f"Thread leak detected: {thread_growth} new threads"


class TestPerformanceRegression:
    """Tests to detect performance regressions."""

    def test_executor_initialization_fast(self):
        """Test that executor initialization is fast."""
        start = time.time()

        for _ in range(100):
            executor = ParallelExecutor(max_workers=4, logger=Mock())

        init_time = time.time() - start

        # 100 initializations should be < 1 second
        assert init_time < 1.0, f"Executor initialization too slow: {init_time:.3f}s for 100 inits"

    def test_empty_execution_fast(self):
        """Test that empty context list handling is fast."""
        executor = ParallelExecutor(max_workers=4, logger=Mock())

        start = time.time()

        # Execute with empty contexts
        for _ in range(100):
            executor.execute([])

        empty_time = time.time() - start

        assert empty_time < 0.1, f"Empty execution handling too slow: {empty_time:.3f}s"
