import time
import unittest.mock

import pytest

from configurator.core.parallel import ParallelModuleExecutor
from configurator.modules.base import ConfigurationModule


class MockModule(ConfigurationModule):
    def __init__(self, name):
        self.name = name

    def validate(self):
        if getattr(self, "fail_validate", False):
            return False
        return True

    def configure(self):
        if getattr(self, "fail_configure", False):
            return False
        if getattr(self, "raise_error", False):
            raise ValueError("Boom")
        time.sleep(getattr(self, "duration", 0.01))
        return True

    def verify(self):
        if getattr(self, "fail_verify", False):
            return False
        return True


class TestParallelExecutor:
    def test_execution(self):
        executor = ParallelModuleExecutor(max_workers=2)
        registry = {"A": MockModule("A"), "B": MockModule("B")}
        batches = [["A", "B"]]

        results = executor.execute_batches(batches, registry)
        assert results["A"] is True
        assert results["B"] is True

    def test_validation_failure(self):
        executor = ParallelModuleExecutor(max_workers=2)
        mod = MockModule("BadVal")
        mod.fail_validate = True

        batches = [["BadVal"]]
        results = executor.execute_batches(batches, {"BadVal": mod})

        assert results["BadVal"] is False

    def test_verify_failure(self):
        executor = ParallelModuleExecutor(max_workers=2)
        mod = MockModule("BadVer")
        mod.fail_verify = True

        batches = [["BadVer"]]
        results = executor.execute_batches(batches, {"BadVer": mod})

        assert results["BadVer"] is False

    def test_configure_exception(self):
        executor = ParallelModuleExecutor(max_workers=2)
        mod = MockModule("Crash")
        mod.raise_error = True

        batches = [["Crash"]]
        results = executor.execute_batches(batches, {"Crash": mod})

        assert results["Crash"] is False

    def test_stats_collection(self):
        executor = ParallelModuleExecutor(max_workers=2)
        mod = MockModule("Timed")
        mod.duration = 0.1

        batches = [["Timed"]]
        executor.execute_batches(batches, {"Timed": mod})

        stats = executor.get_execution_stats()
        assert "Timed" in stats
        assert stats["Timed"]["duration"] >= 0.1

    def test_execution_cancellation(self):
        """Test that a failure stops subsequent batches"""
        executor = ParallelModuleExecutor(max_workers=2)

        fail_mod = MockModule("Fail")
        fail_mod.fail_configure = True

        skip_mod = MockModule("Skip")

        # Batch 1 fails, Batch 2 should be skipped (or handled)
        # execute_batches returns on first batch failure
        batches = [["Fail"], ["Skip"]]
        module_registry = {"Fail": fail_mod, "Skip": skip_mod}

        results = executor.execute_batches(batches, module_registry)

        assert results["Fail"] is False
        assert "Skip" not in results or results["Skip"] is False

    def test_parallel_batch_exception(self):
        """Test exception in parallel batch execution"""
        executor = ParallelModuleExecutor(max_workers=2)

        # raise_error causes Exception in _execute_module_internal
        # which is caught in _execute_parallel_batch
        crash_mod = MockModule("Crash")
        crash_mod.raise_error = True

        ok_mod = MockModule("OK")

        batches = [["Crash", "OK"]]
        registry = {"Crash": crash_mod, "OK": ok_mod}

        results = executor.execute_batches(batches, registry)

        assert results["Crash"] is False
        # OK might finish or be cancelled depending on timing,
        # but the batch itself fails.
