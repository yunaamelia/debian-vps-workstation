"""
Load and stress testing suite.

Tests system behavior under high load and resource constraints.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock

import pytest

from configurator.core.execution.parallel import ParallelExecutor
from configurator.core.network import NetworkOperationType, NetworkOperationWrapper


class TestConcurrentOperations:
    """Test system under concurrent load."""

    def test_concurrent_network_operations(self):
        """Test many concurrent network operations."""
        wrapper = NetworkOperationWrapper({}, Mock())

        num_operations = 100
        results = []
        errors = []

        def operation():
            try:
                result = wrapper.execute_with_retry(
                    lambda: "success", NetworkOperationType.HTTP_REQUEST
                )
                return result
            except Exception as e:
                return e

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(operation) for _ in range(num_operations)]

            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, Exception):
                    errors.append(result)
                else:
                    results.append(result)

        duration = time.perf_counter() - start

        print("\nConcurrent Network Operations:")
        print(f"  Operations: {num_operations}")
        print(f"  Success: {len(results)}")
        print(f"  Errors: {len(errors)}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {num_operations / duration:.1f} ops/sec")

        # All should succeed
        assert len(errors) == 0, f"{len(errors)} operations failed"
        assert len(results) == num_operations

    def test_concurrent_circuit_breaker_state_changes(self):
        """Test circuit breaker under concurrent state changes."""
        config = {
            "performance": {
                "circuit_breaker": {"enabled": True, "failure_threshold": 1, "timeout": 1}
            }
        }

        wrapper = NetworkOperationWrapper(config, Mock())

        success_count = [0]
        failure_count = [0]
        breaker_open_count = [0]
        lock = threading.Lock()

        def random_operation():
            import random

            def operation():
                if random.random() < 1.0:  # 100% failure rate to guarantee breaker opens
                    raise Exception("Random failure")
                return "success"

            try:
                result = wrapper.execute_with_retry(operation, NetworkOperationType.APT_UPDATE)

                with lock:
                    success_count[0] += 1
                return result

            except Exception as e:
                with lock:
                    if "ircuit" in str(e):
                        breaker_open_count[0] += 1
                    else:
                        failure_count[0] += 1
                return None

        # Run many operations concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(random_operation) for _ in range(100)]
            for future in as_completed(futures):
                future.result()

        print("\nConcurrent Circuit Breaker Test:")
        print(f"  Successes: {success_count[0]}")
        print(f"  Failures: {failure_count[0]}")
        print(f"  Circuit Open: {breaker_open_count[0]}")

        # Circuit breaker should have opened at some point
        assert breaker_open_count[0] > 0, "Circuit breaker never opened"


class TestResourceConstraints:
    """Test behavior under resource constraints."""

    def test_high_memory_pressure(self):
        """Test system behavior under memory pressure."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available")

        import gc

        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024

        # Allocate large data structures
        large_data = []
        for i in range(1000):
            large_data.append([Mock() for _ in range(100)])

        mem_peak = process.memory_info().rss / 1024 / 1024

        # System should still function
        wrapper = NetworkOperationWrapper({}, Mock())
        result = wrapper.execute_with_retry(lambda: "success", NetworkOperationType.HTTP_REQUEST)

        assert result == "success", "System failed under memory pressure"

        # Cleanup
        large_data.clear()
        gc.collect()

        mem_after = process.memory_info().rss / 1024 / 1024

        print("\nMemory Pressure Test:")
        print(f"  Before: {mem_before:.1f} MB")
        print(f"  Peak: {mem_peak:.1f} MB")
        print(f"  After cleanup: {mem_after:.1f} MB")
        print(f"  Memory recovered: {(mem_peak - mem_after):.1f} MB")

    @pytest.mark.slow
    def test_sustained_load(self):
        """Test system under sustained load for extended period."""
        duration_seconds = 30
        operations_per_second = 10

        wrapper = NetworkOperationWrapper({}, Mock())

        start_time = time.time()
        operation_count = 0
        error_count = 0

        print(f"\nSustained Load Test ({duration_seconds}s):")

        while time.time() - start_time < duration_seconds:
            batch_start = time.time()

            for _ in range(operations_per_second):
                try:
                    wrapper.execute_with_retry(lambda: "success", NetworkOperationType.HTTP_REQUEST)
                    operation_count += 1
                except Exception:
                    error_count += 1

            # Sleep to maintain rate
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

            if operation_count % 50 == 0:
                print(f"  {operation_count} operations completed...")

        total_duration = time.time() - start_time

        print(f"\n  Total operations: {operation_count}")
        print(f"  Errors: {error_count}")
        print(f"  Duration: {total_duration:.1f}s")
        print(f"  Average rate: {operation_count / total_duration:.1f} ops/sec")

        error_rate = (error_count / operation_count) * 100 if operation_count > 0 else 0
        assert error_rate < 1.0, f"Error rate too high: {error_rate:.2f}%"


@pytest.mark.stress
class TestStressScenarios:
    """Extreme stress testing scenarios."""

    @pytest.mark.slow
    def test_rapid_circuit_breaker_cycling(self):
        """Test rapid opening and closing of circuit breakers."""
        config = {
            "performance": {
                "circuit_breaker": {
                    "enabled": True,
                    "failure_threshold": 2,
                    "timeout": 0.5,  # Very short timeout
                }
            }
        }

        wrapper = NetworkOperationWrapper(config, Mock())

        cycles = 0

        for _ in range(10):  # 10 cycles
            # Cause failures to open circuit
            for _ in range(3):
                try:
                    wrapper.execute_with_retry(
                        lambda: (_ for _ in ()).throw(Exception("Fail")),
                        NetworkOperationType.APT_UPDATE,
                    )
                except Exception:
                    pass

            # Wait for half-open
            time.sleep(0.6)

            # Success to close circuit
            try:
                wrapper.execute_with_retry(lambda: "success", NetworkOperationType.APT_UPDATE)
                cycles += 1
            except Exception:
                pass

        print("\nCircuit Breaker Cycling:")
        print(f"  Successful cycles: {cycles}/10")

        assert cycles >= 8, f"Circuit breaker cycling unstable: {cycles}/10"

    def test_thread_pool_exhaustion(self):
        """Test behavior when thread pool is exhausted."""
        from configurator.core.execution.base import ExecutionContext

        executor = ParallelExecutor(max_workers=2, logger=Mock())

        # Create many modules
        contexts = []
        for i in range(100):
            module = Mock()
            module.validate.return_value = True
            module.configure.return_value = True

            # Slow down execution to force queuing
            def slow_configure():
                time.sleep(0.01)
                return True

            module.configure.side_effect = slow_configure

            context = ExecutionContext(
                module_name=f"module_{i}", module_instance=module, config={}, dry_run=False
            )
            contexts.append(context)

        start = time.perf_counter()
        results = executor.execute(contexts)
        duration = time.perf_counter() - start

        print("\nThread Pool Exhaustion Test:")
        print("  Modules: 100")
        print("  Workers: 2")
        print(f"  Duration: {duration:.2f}s")
        # Expected: 100 modules * 0.01s / 2 workers = 0.5s approx
        print("  Expected: ~0.5s")

        # Should complete all modules
        assert len(results) == 100
        assert all(r.success for r in results.values())


# Stress test configuration
def pytest_configure(config):
    """Configure pytest for stress tests."""
    config.addinivalue_line("markers", "stress: mark test as stress/load test")
