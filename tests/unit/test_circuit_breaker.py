import time

import pytest

from configurator.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
)


class TestCircuitBreaker:
    def test_initial_state(self):
        breaker = CircuitBreaker("test-service")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_successful_call(self):
        breaker = CircuitBreaker("test-service")
        result = breaker.call(lambda x: x * 2, 5)
        assert result == 10
        assert breaker.total_successes == 1
        assert breaker.failure_count == 0

    def test_failure_counting(self):
        breaker = CircuitBreaker("test-service", failure_threshold=2)

        # First failure
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)
        assert breaker.failure_count == 1
        assert breaker.state == CircuitState.CLOSED

        # Second failure (should open circuit)
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)
        assert breaker.failure_count == 2
        assert breaker.state == CircuitState.OPEN

    def test_circuit_open_behavior(self):
        breaker = CircuitBreaker("test-service", failure_threshold=1)

        # Trigger open
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)
        assert breaker.state == CircuitState.OPEN

        # Subsequent call should raise CircuitBreakerError immediately
        with pytest.raises(CircuitBreakerError) as excinfo:
            breaker.call(lambda: "should not run")

        assert excinfo.value.state == CircuitState.OPEN
        assert excinfo.value.retry_after > 0

    def test_half_open_recovery(self):
        # Short timeout for testing
        breaker = CircuitBreaker("test-service", failure_threshold=1, timeout=0.1)

        # Fail to open
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)

        # Wait for timeout
        time.sleep(0.15)

        # Next call should transition to HALF_OPEN
        # And if successful, to CLOSED
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_half_open_failure(self):
        breaker = CircuitBreaker("test-service", failure_threshold=1, timeout=0.1)

        # Fail to open
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)

        time.sleep(0.15)

        # Fail again in HALF_OPEN
        with pytest.raises(ValueError):
            breaker.call(self._failing_function)

        assert breaker.state == CircuitState.OPEN

    def _failing_function(self):
        raise ValueError("Simulated failure")


class TestCircuitBreakerManager:
    def test_get_breaker(self):
        manager = CircuitBreakerManager()
        breaker1 = manager.get_breaker("service-a")
        breaker2 = manager.get_breaker("service-a")
        breaker3 = manager.get_breaker("service-b")

        assert breaker1 is breaker2
        assert breaker1 is not breaker3
        assert breaker1.name == "service-a"

    def test_metrics(self):
        manager = CircuitBreakerManager()
        breaker = manager.get_breaker("test", failure_threshold=1)

        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Fail")))

        metrics = manager.get_all_metrics()
        assert "test" in metrics
        assert metrics["test"]["state"] == "open"
        assert metrics["test"]["failure_count"] == 1
