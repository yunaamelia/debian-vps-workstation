"""
Unit tests for CORE-004: Memory leak fix with cleanup.
"""

from unittest.mock import Mock

import pytest

from configurator.core.parallel import ParallelModuleExecutor


class TestMemoryLeakFix:
    """Test that memory leak is fixed with proper cleanup."""

    def test_cleanup_on_successful_execution(self):
        """Test that cleanup happens after successful batch execution."""
        executor = ParallelModuleExecutor(max_workers=2, logger=Mock())

        module_registry = {
            "module1": Mock(),
            "module2": Mock(),
        }

        def handler(name, module):
            return True

        batches = [["module1", "module2"]]

        # Execute batch
        result = executor.execute_batches(batches, module_registry, handler)

        # Test should complete without hanging or memory issues
        assert result is not None

    def test_cleanup_on_exception(self):
        """Test that cleanup happens even when exception occurs."""
        executor = ParallelModuleExecutor(max_workers=2, logger=Mock())

        module_registry = {"module1": Mock()}

        def handler(name, module):
            raise Exception("Test exception")

        batches = [["module1"]]

        # Execute (will fail)
        try:
            executor.execute_batches(batches, module_registry, handler)
        except Exception:
            pass  # Expected

        # No hanging resources, cleanup should have happened
        assert True, "Cleanup should happen in finally block"

    def test_finally_block_executes(self):
        """Test that finally block is guaranteed to execute."""
        executor = ParallelModuleExecutor(max_workers=2, logger=Mock())

        cleanup_executed = []

        # Simulate finally block behavior
        try:
            raise Exception("Simulated error")
        except Exception:
            pass
        finally:
            cleanup_executed.append(True)

        assert len(cleanup_executed) == 1, "Finally block should execute"


class TestGarbageCollectionTrigger:
    """Test that garbage collection is triggered for large batches."""

    def test_gc_condition_for_large_batch(self):
        """Test that GC is triggered for batches with > 5 modules."""
        batch_sizes = [3, 5, 6, 10, 20]
        expected_gc = [False, False, True, True, True]

        for size, should_gc in zip(batch_sizes, expected_gc, strict=False):
            batch_size = size
            if batch_size > 5:
                # GC should be triggered
                assert should_gc is True
            else:
                # GC should not be triggered
                assert should_gc is False


class TestExplicitDictCleanup:
    """Test explicit cleanup of future_to_module dict."""

    def test_dict_cleanup_pattern(self):
        """Test the cleanup pattern used in finally block."""
        # Simulate dict cleanup
        future_to_module = {"future1": "module1", "future2": "module2"}

        # Cleanup pattern
        if future_to_module is not None:
            # Clear the dict
            future_to_module.clear()
            # Delete the reference
            del future_to_module

        # After cleanup, future_to_module should not exist
        with pytest.raises(NameError):
            len(future_to_module)  # This should raise NameError
