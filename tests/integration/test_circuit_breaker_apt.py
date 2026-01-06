from unittest.mock import MagicMock, patch

import pytest

from configurator.exceptions import ModuleExecutionError
from configurator.modules.base import ConfigurationModule
from configurator.utils.circuit_breaker import CircuitBreakerError


class MockModule(ConfigurationModule):
    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


@pytest.fixture
def mock_module(mock_config, mock_logger):
    # Ensure fresh manager
    from configurator.utils.circuit_breaker import CircuitBreakerManager

    manager = CircuitBreakerManager()
    module = MockModule(mock_config, mock_logger, circuit_breaker_manager=manager)
    return module


class TestCircuitBreakerAptIntegration:
    """Test integration between CircuitBreaker and install_packages."""

    def test_install_packages_circuit_breaker_activates(self, mock_module):
        """Verify that repeated apt failures trip the circuit breaker."""

        mock_module.circuit_breaker_manager.reset_all()
        # Reduce threshold for testing
        breaker = mock_module.circuit_breaker_manager.get_breaker(
            "apt-repository", failure_threshold=2, timeout=10
        )

        # Bypass retry decorator for precise control over calls
        if hasattr(mock_module.install_packages, "__wrapped__"):
            original_func = mock_module.install_packages.__wrapped__
            # Bind to instance
            mock_module.install_packages = original_func.__get__(mock_module, MockModule)

        # Mock run command to simulate failure
        with patch.object(mock_module, "run") as mock_run:
            mock_run.return_value.success = False
            mock_run.return_value.return_code = 100
            mock_run.side_effect = (
                None  # ensure no exception raised by run itself, just failure result if check=False
            )

            # However, install_packages calls run with check=True usually.
            # If check=True, run_command (or BaseModule.run) raises an Exception if it fails?
            # Looking at base.py, run calls run_command. run_command raises if check=True and retcode != 0.
            # Let's assume run raises Exception when check=True and success=False.
            mock_run.side_effect = Exception("APT Failed")

            # Attempt 1
            with pytest.raises(Exception):
                mock_module.install_packages(["package1"], update_cache=False)

            print(f"DEBUG: Breaker state: {breaker.state}, failures: {breaker.failure_count}")

            # Attempt 2
            with pytest.raises(Exception):
                mock_module.install_packages(["package1"], update_cache=False)

            print(f"DEBUG: Breaker state: {breaker.state}, failures: {breaker.failure_count}")

            # Circuit should be open now
            assert breaker.state.value == "open"

            # Attempt 3 should fail FAST with ModuleExecutionError (wrapping CircuitBreakerError)
            with pytest.raises(ModuleExecutionError) as excinfo:
                mock_module.install_packages(["package1"], update_cache=False)

            assert "APT repository appears to be down" in str(excinfo.value)

            # Verify we didn't call run the 3rd time
            assert mock_run.call_count == 2

    def test_install_packages_success_closes_circuit(self, mock_module):
        """Verify that successful install resets the breaker."""
        mock_module.circuit_breaker_manager.reset_all()
        breaker = mock_module.circuit_breaker_manager.get_breaker("apt-repository")

        with patch.object(mock_module, "run") as mock_run:
            mock_run.return_value.success = True

            assert mock_module.install_packages(["package1"]) is True
            assert breaker.state.value == "closed"
            assert breaker.total_successes == 1
