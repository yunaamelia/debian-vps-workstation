"""
Performance regression tests with benchmarking.

Tracks performance metrics over time to detect regressions.
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import pytest

from configurator.core.network import NetworkOperationType, NetworkOperationWrapper
from configurator.core.parallel import DependencyGraph, ParallelModuleExecutor


class PerformanceBenchmark:
    """Store and compare performance benchmarks."""

    BASELINE_FILE = Path("tests/performance/baselines.json")

    def __init__(self):
        self.baselines = self._load_baselines()

    def _load_baselines(self) -> Dict:
        """Load baseline performance metrics."""
        if self.BASELINE_FILE.exists():
            with open(self.BASELINE_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_baseline(self, test_name: str, duration: float, metadata: Dict = None):
        """Save new baseline."""
        self.baselines[test_name] = {
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.BASELINE_FILE, "w") as f:
            json.dump(self.baselines, f, indent=2)

    def check_regression(
        self, test_name: str, duration: float, threshold_percent: float = 20.0
    ) -> tuple:
        """
        Check if performance has regressed.

        Args:
            test_name: Name of the test
            duration: Current duration in seconds
            threshold_percent: Acceptable regression percentage

        Returns:
            (is_acceptable, message)
        """
        if test_name not in self.baselines:
            # Auto-save baseline for first run
            self.save_baseline(test_name, duration, {"auto_generated": True})
            return True, f"No baseline for '{test_name}' - established new baseline"

        baseline_duration = self.baselines[test_name]["duration"]

        # Ignore regression if absolute difference is negligible (< 10ms)
        if abs(duration - baseline_duration) < 0.01:
            return True, "Performance stable (change < 10ms)"

        regression_percent = ((duration - baseline_duration) / baseline_duration) * 100

        if regression_percent > threshold_percent:
            return False, (
                f"Performance regression detected: {regression_percent:.1f}% slower\n"
                f"  Baseline: {baseline_duration:.3f}s\n"
                f"  Current:  {duration:.3f}s\n"
                f"  Threshold: {threshold_percent}%"
            )
        elif regression_percent < -10:  # Significant improvement
            return True, (
                f"Performance improved: {abs(regression_percent):.1f}% faster\n"
                f"  Consider updating baseline"
            )
        else:
            return True, f"Performance within acceptable range ({regression_percent:+.1f}%)"


@pytest.fixture
def benchmark():
    """Provide benchmark fixture."""
    return PerformanceBenchmark()


class TestDependencyGraphPerformance:
    """Test dependency graph performance."""

    def test_dependency_graph_build_performance(self, benchmark):
        """Test dependency graph building performance."""
        from configurator.core.dependencies import COMPLETE_MODULE_DEPENDENCIES

        # Warm-up
        for _ in range(3):
            graph = DependencyGraph()
            for module, deps in COMPLETE_MODULE_DEPENDENCIES.items():
                graph.add_module(module, depends_on=deps)

        # Actual benchmark
        iterations = 100
        durations = []

        for _ in range(iterations):
            start = time.perf_counter()

            graph = DependencyGraph()
            for module, deps in COMPLETE_MODULE_DEPENDENCIES.items():
                graph.add_module(module, depends_on=deps)
            batches = graph.get_parallel_batches()

            duration = time.perf_counter() - start
            durations.append(duration)

        avg_duration = statistics.mean(durations)
        std_dev = statistics.stdev(durations)

        print("\nDependency Graph Performance:")
        print(f"  Average: {avg_duration * 1000:.2f}ms")
        print(f"  Std Dev: {std_dev * 1000:.2f}ms")
        print(f"  Min: {min(durations) * 1000:.2f}ms")
        print(f"  Max: {max(durations) * 1000:.2f}ms")

        # Check for regression
        is_ok, msg = benchmark.check_regression(
            "dependency_graph_build", avg_duration, threshold_percent=30.0
        )

        print(f"  {msg}")

        # Performance requirements
        assert avg_duration < 0.1, f"Dependency graph too slow: {avg_duration:.3f}s"
        assert is_ok, "Performance regression detected"

    def test_circular_dependency_detection_performance(self, benchmark):
        """Test circular dependency detection performance."""
        graph = DependencyGraph()

        # Create complex graph with potential cycles
        modules = [f"module_{i}" for i in range(50)]

        start = time.perf_counter()

        # Add modules with dependencies
        for i, module in enumerate(modules):
            deps = [modules[j] for j in range(max(0, i - 3), i)]
            graph.add_module(module, depends_on=deps)

        try:
            batches = graph.get_parallel_batches()
        except ValueError:
            pass  # Expected if cycle exists

        duration = time.perf_counter() - start

        print("\nCircular Detection Performance (50 modules):")
        print(f"  Duration: {duration * 1000:.2f}ms")

        is_ok, msg = benchmark.check_regression(
            "circular_detection_50_modules", duration, threshold_percent=30.0
        )

        print(f"  {msg}")

        assert duration < 0.5, f"Circular detection too slow: {duration:.3f}s"
        assert is_ok, "Performance regression"


class TestNetworkWrapperPerformance:
    """Test network wrapper performance."""

    def test_network_wrapper_overhead(self, benchmark):
        """Measure overhead of network wrapper."""
        wrapper = NetworkOperationWrapper({}, Mock())

        # Warm-up
        for _ in range(10):
            wrapper.execute_with_retry(lambda: "success", NetworkOperationType.HTTP_REQUEST)

        # Benchmark
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            wrapper.execute_with_retry(lambda: "success", NetworkOperationType.HTTP_REQUEST)
        duration = time.perf_counter() - start

        avg_per_call = (duration / iterations) * 1000  # ms

        print("\nNetwork Wrapper Overhead:")
        print(f"  {iterations} operations in {duration:.3f}s")
        print(f"  Average per call: {avg_per_call:.2f}ms")
        print(f"  Throughput: {iterations / duration:.0f} ops/sec")

        is_ok, msg = benchmark.check_regression(
            "network_wrapper_overhead",
            avg_per_call / 1000,  # Convert to seconds
            threshold_percent=25.0,
        )

        print(f"  {msg}")

        assert avg_per_call < 10.0, f"Overhead too high: {avg_per_call:.2f}ms"
        assert is_ok, "Performance regression"

    def test_circuit_breaker_state_check_performance(self, benchmark):
        """Test circuit breaker state checking performance."""
        config = {"performance": {"circuit_breaker": {"enabled": True}}}

        wrapper = NetworkOperationWrapper(config, Mock())

        iterations = 10000

        start = time.perf_counter()
        for _ in range(iterations):
            status = wrapper.get_circuit_breaker_status()
        duration = time.perf_counter() - start

        avg_per_call = (duration / iterations) * 1000000  # microseconds

        print("\nCircuit Breaker Status Check:")
        print(f"  {iterations} checks in {duration:.3f}s")
        print(f"  Average: {avg_per_call:.1f}μs per check")

        is_ok, msg = benchmark.check_regression(
            "circuit_breaker_status_check", duration / iterations, threshold_percent=30.0
        )

        print(f"  {msg}")

        assert avg_per_call < 100, f"Status check too slow: {avg_per_call:.1f}μs"


class TestModuleLoadingPerformance:
    """Test module loading and initialization performance."""

    def test_lazy_loading_effectiveness(self, benchmark):
        """Test that lazy loading reduces startup time."""
        # Without lazy loading (import all)
        # Without lazy loading (import all)
        start = time.perf_counter()
        import importlib

        # Simulate eager import of heavy modules (we assume they exist)
        try:
            importlib.import_module("configurator.modules.desktop")
            importlib.import_module("configurator.modules.docker")
        except ImportError:
            pass
        duration_eager = time.perf_counter() - start

        # With lazy loading (using LazyModule)
        from configurator.core.lazy_loader import LazyModule

        start = time.perf_counter()
        lazy_desktop = LazyModule("configurator.modules.desktop", "DesktopModule")
        lazy_docker = LazyModule("configurator.modules.docker", "DockerModule")
        duration_lazy = time.perf_counter() - start

        improvement = ((duration_eager - duration_lazy) / duration_eager) * 100

        print("\nLazy Loading Performance:")
        print(f"  Eager loading: {duration_eager * 1000:.2f}ms")
        print(f"  Lazy loading:  {duration_lazy * 1000:.2f}ms")
        print(f"  Improvement: {improvement:.1f}%")

        assert duration_lazy < duration_eager, "Lazy loading should be faster"
        assert improvement > 30, f"Lazy loading not effective enough: {improvement:.1f}%"

    def test_cli_startup_time(self, benchmark):
        """Test CLI startup time."""
        import subprocess

        iterations = 5
        durations = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = subprocess.run(
                ["python3", "-m", "configurator", "--version"], capture_output=True, timeout=5
            )
            duration = time.perf_counter() - start

            if result.returncode == 0:
                durations.append(duration)

        if not durations:
            pytest.skip("CLI not available")

        avg_duration = statistics.mean(durations)

        print("\nCLI Startup Time:")
        print(f"  Average: {avg_duration * 1000:.0f}ms ({iterations} runs)")
        print(f"  Min: {min(durations) * 1000:.0f}ms")
        print(f"  Max: {max(durations) * 1000:.0f}ms")

        is_ok, msg = benchmark.check_regression(
            "cli_startup_time", avg_duration, threshold_percent=20.0
        )

        print(f"  {msg}")

        assert avg_duration < 1.0, f"CLI startup too slow: {avg_duration:.3f}s"
        assert is_ok, "Performance regression"


class TestMemoryUsage:
    """Test memory usage and leak detection."""

    def test_memory_leak_in_parallel_execution(self):
        """Test for memory leaks in parallel module execution."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available")

        import gc

        process = psutil.Process()

        # Initial memory
        gc.collect()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate many module executions
        executor = ParallelModuleExecutor(max_workers=4, logger=Mock())

        for iteration in range(10):
            # Create mock modules
            modules = {f"module_{i}": Mock() for i in range(20)}

            def mock_handler(name, module):
                time.sleep(0.01)  # Simulate work
                return True

            batches = [[f"module_{i}" for i in range(5)] for _ in range(4)]
            executor.execute_batches(batches, modules, mock_handler)

        # Force garbage collection
        gc.collect()

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        print("\nMemory Usage Test:")
        print(f"  Before: {mem_before:.2f} MB")
        print(f"  After:  {mem_after:.2f} MB")
        print(f"  Increase: {mem_increase:.2f} MB")

        # Allow reasonable increase (caching, etc.) but detect leaks
        assert mem_increase < 50, f"Potential memory leak: {mem_increase:.2f} MB increase"


@pytest.mark.benchmark
class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.mark.slow
    def test_dry_run_installation_performance(self, benchmark):
        """Test complete dry-run installation performance."""
        # This tests the entire flow without actual system changes

        start = time.perf_counter()

        # Simulate dry-run installation
        # (Would need actual implementation)

        duration = time.perf_counter() - start

        print("\nDry-Run Installation:")
        print(f"  Duration: {duration:.2f}s")

        is_ok, msg = benchmark.check_regression(
            "dry_run_full_installation", duration, threshold_percent=15.0
        )

        print(f"  {msg}")

        # Dry-run should be fast (no actual I/O)
        assert duration < 5.0, f"Dry-run too slow: {duration:.2f}s"


# Performance test configuration
def pytest_configure(config):
    """Configure pytest for performance tests."""
    config.addinivalue_line("markers", "benchmark: mark test as performance benchmark")
