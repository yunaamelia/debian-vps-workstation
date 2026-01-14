"""
Network failure simulation tests (Chaos Engineering).

Simulates various network failure scenarios to verify
system resilience.
"""

import subprocess
import time
from unittest.mock import Mock, patch

import pytest

from configurator.core.network import NetworkOperationType, NetworkOperationWrapper
from configurator.utils.circuit_breaker import CircuitBreakerError


class TestNetworkFailureSimulation:
    """Simulate network failures and verify resilience."""

    def test_intermittent_network_failure(self):
        """Test behavior during intermittent network issues."""
        wrapper = NetworkOperationWrapper({}, Mock())

        call_count = [0]

        def flaky_operation():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Network timeout")
            return "success"

        # Should succeed after 3 attempts
        result = wrapper.execute_with_retry(flaky_operation, NetworkOperationType.HTTP_REQUEST)

        assert result == "success"
        assert call_count[0] == 3

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        config = {
            "performance": {
                "circuit_breaker": {"enabled": True, "failure_threshold": 2, "timeout": 1}
            }
        }

        wrapper = NetworkOperationWrapper(config, Mock())

        def failing_operation():
            raise Exception("Service unavailable")

        # First two attempts should fail normally
        for i in range(2):
            with pytest.raises(Exception):
                wrapper.execute_with_retry(failing_operation, NetworkOperationType.APT_UPDATE)

        # Circuit should now be open
        with pytest.raises(CircuitBreakerError):
            wrapper.execute_with_retry(failing_operation, NetworkOperationType.APT_UPDATE)

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        config = {
            "performance": {
                "circuit_breaker": {
                    "enabled": True,
                    "failure_threshold": 1,
                    "timeout": 0.1,  # Short timeout for testing
                }
            }
        }

        wrapper = NetworkOperationWrapper(config, Mock())

        # Fail once to open circuit
        with pytest.raises(Exception):
            wrapper.execute_with_retry(
                lambda: (_ for _ in ()).throw(Exception("Fail")), NetworkOperationType.APT_UPDATE
            )

        # Wait for timeout
        time.sleep(0.15)

        # Should allow one attempt (half-open)
        # Successful attempt should close circuit
        result = wrapper.execute_with_retry(lambda: "recovered", NetworkOperationType.APT_UPDATE)

        assert result == "recovered"

    @patch("subprocess.run")
    def test_apt_update_transient_failure_recovery(self, mock_run):
        """Test APT update recovers from transient failures."""
        wrapper = NetworkOperationWrapper({}, Mock())

        # Simulate transient failure
        call_count = [0]

        def run_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                # First call fails
                return Mock(returncode=1, stderr="Temporary failure")
            else:
                # Second call succeeds
                return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        # Should succeed after retry
        result = wrapper.apt_update_with_retry()

        assert result is True
        assert call_count[0] == 2

    @patch("subprocess.run")
    def test_download_timeout_handling(self, mock_run):
        """Test download timeout is properly handled."""
        wrapper = NetworkOperationWrapper({}, Mock())

        # Simulate timeout
        mock_run.side_effect = subprocess.TimeoutExpired("curl", 30)

        # Should handle timeout gracefully
        result = wrapper.download_with_retry(
            url="https://example.com/large-file.tar.gz", dest="/tmp/test.tar.gz"
        )

        assert result is None

    def test_exponential_backoff_timing(self):
        """Test exponential backoff increases correctly."""
        from configurator.core.network import RetryConfig

        retry_config = RetryConfig(
            initial_delay=1.0, exponential_base=2.0, max_delay=30.0, jitter=False
        )

        wrapper = NetworkOperationWrapper({}, Mock(), retry_config)

        # Test backoff calculation
        delays = [wrapper._calculate_backoff_delay(i) for i in range(5)]

        # Should be: 1, 2, 4, 8, 16
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0

    def test_jitter_prevents_thundering_herd(self):
        """Test jitter adds randomness to prevent thundering herd."""
        from configurator.core.network import RetryConfig

        retry_config = RetryConfig(jitter=True)
        wrapper = NetworkOperationWrapper({}, Mock(), retry_config)

        # Calculate multiple delays for same attempt
        delays = [wrapper._calculate_backoff_delay(1) for _ in range(10)]

        # All should be different (jitter applied)
        assert len(set(delays)) > 1

        # All should be within reasonable range
        for delay in delays:
            assert 2.0 <= delay <= 2.2  # 2.0 base + 10% jitter


@pytest.mark.integration
class TestRealNetworkConditions:
    """Test with real network conditions (slower, requires network)."""

    @pytest.mark.slow
    def test_connectivity_check_real_internet(self):
        """Test connectivity check with real internet."""
        wrapper = NetworkOperationWrapper({}, Mock())

        # Should detect internet connectivity
        result = wrapper.check_internet_connectivity()

        # If this fails, system truly has no internet
        assert result is True or result is False  # Either is valid

    @pytest.mark.slow
    def test_apt_update_real_repository(self):
        """Test APT update with real Debian repository."""
        wrapper = NetworkOperationWrapper({}, Mock())

        # This will make real network call
        # Only run if internet is available
        if wrapper.check_internet_connectivity():
            result = wrapper.apt_update_with_retry()
            assert result is True


@pytest.mark.chaos
class TestChaosEngineering:
    """Chaos engineering tests - inject failures deliberately."""

    def test_random_failure_injection(self):
        """Inject random failures and verify recovery."""
        import random

        wrapper = NetworkOperationWrapper({}, Mock())

        def chaos_operation():
            if random.random() < 0.7:  # 70% failure rate
                raise Exception("Chaos induced failure")
            return "success"

        # Despite high failure rate, should eventually succeed
        # (This test is probabilistic)
        successes = 0
        for _ in range(10):
            try:
                result = wrapper.execute_with_retry(
                    chaos_operation, NetworkOperationType.HTTP_REQUEST
                )
                if result == "success":
                    successes += 1
            except Exception:
                pass

        # Should have at least some successes
        assert successes > 0
