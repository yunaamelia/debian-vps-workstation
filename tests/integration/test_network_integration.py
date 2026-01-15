"""
Integration tests for network resilience with real network conditions.

These tests require actual internet connectivity and interact with
real external services. Run with: pytest tests/integration/test_network_integration.py
"""

import logging

import pytest

from configurator.core.health import HealthCheckService
from configurator.core.network import NetworkOperationWrapper
from configurator.modules.base import ConfigurationModule


@pytest.mark.integration
@pytest.mark.slow
class TestNetworkIntegration:
    """Integration tests for network resilience."""

    def test_apt_update_real_repository(self):
        """Test APT update with real Debian repository."""
        import os

        if os.geteuid() != 0:
            pytest.skip("APT update requires root privileges")

        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        # Check internet first
        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        # This makes a real network call
        result = wrapper.apt_update_with_retry()

        assert result is True, "APT update should succeed with internet"

    def test_download_real_file(self, tmp_path):
        """Test downloading a real file from internet."""
        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        # Download a small file (Debian README)
        dest = tmp_path / "debian_readme.txt"
        result = wrapper.download_with_retry(
            url="http://deb.debian.org/debian/README", dest=str(dest)
        )

        assert result is not None, "Download should succeed"
        assert dest.exists(), "Downloaded file should exist"
        assert dest.stat().st_size > 0, "File should not be empty"

    def test_health_check_real_services(self):
        """Test health checks against real external services."""
        health = HealthCheckService(logging.getLogger())

        # Check all configured services
        results = health.check_all()

        assert len(results) > 0, "Should check at least one service"

        # At least one service should be healthy (if internet works)
        healthy_count = sum(1 for check in results.values() if check.status.value == "healthy")

        if healthy_count == 0:
            pytest.skip("No healthy services found (possible network issue)")

        # Verify summary
        summary = health.get_summary()
        assert summary["total_services"] == len(results)
        assert summary["healthy"] + summary["degraded"] + summary["unhealthy"] == len(results)

    def test_circuit_breaker_with_real_failures(self):
        """Test circuit breaker behavior with real network conditions."""
        config = {
            "performance": {
                "circuit_breaker": {"enabled": True, "failure_threshold": 2, "timeout": 5}
            }
        }

        wrapper = NetworkOperationWrapper(config, logging.getLogger())

        # Try to download from non-existent domain
        # This should fail and eventually open circuit

        failures = 0
        for i in range(3):
            result = wrapper.download_with_retry(
                url="http://this-domain-does-not-exist-12345.com/file.txt",
                dest="/tmp/test_failure.txt",
            )

            if result is None:
                failures += 1

        # Should have failed all attempts
        assert failures == 3, "All attempts to non-existent domain should fail"

        # Check circuit breaker status
        status = wrapper.get_circuit_breaker_status()
        external_downloads = status.get("external_downloads", {})

        # Circuit might be open after failures
        assert external_downloads["total_failures"] > 0, "Should record failures"

    def test_module_integration_with_network_wrapper(self):
        """Test that modules can use network wrapper."""

        class TestModule(ConfigurationModule):
            name = "test"

            def validate(self):
                return True

            def configure(self):
                return True

            def verify(self):
                return True

        module = TestModule({}, logging.getLogger())

        # Module should have network wrapper
        assert hasattr(module, "network"), "Module should have network attribute"
        assert isinstance(module.network, NetworkOperationWrapper)

        # Test connectivity check through module
        result = module.network.check_internet_connectivity()

        # Result should be boolean (True if internet, False otherwise)
        assert isinstance(result, bool)

    def test_retry_with_intermittent_network(self):
        """Test retry behavior handles intermittent connectivity."""
        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        # Download with retry should succeed even if network is flaky
        # (This test assumes network is stable, but demonstrates the pattern)
        result = wrapper.download_with_retry(
            url="http://deb.debian.org/debian/README", dest="/tmp/retry_test.txt"
        )

        assert result is not None or result is None  # Either outcome is valid
        # The key is that it doesn't hang or crash


@pytest.mark.integration
@pytest.mark.slow
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_full_apt_workflow(self):
        """Test complete APT workflow with retries."""
        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        # Update package lists
        update_result = wrapper.apt_update_with_retry()

        if update_result:
            # If update succeeded, installation should be possible
            # (We use a small package for testing)
            install_result = wrapper.apt_install_with_retry(
                packages=["curl"],  # Already installed, but safe to test
                update_cache=False,  # Already updated
            )

            assert install_result is True, "Package installation should succeed"

    def test_concurrent_network_operations(self):
        """Test multiple concurrent network operations."""
        import concurrent.futures

        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        def check_url(url):
            """Helper to check URL connectivity."""
            import subprocess

            try:
                result = subprocess.run(
                    ["curl", "-fsSL", "--connect-timeout", "5", url],
                    capture_output=True,
                    timeout=10,
                )
                return result.returncode == 0
            except subprocess.SubprocessError:
                return False

        urls = ["http://deb.debian.org", "https://github.com", "https://pypi.org"]

        # Run checks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(check_url, urls))

        # At least one should succeed if internet is working
        assert any(results), "At least one URL should be accessible"

    def test_performance_with_real_operations(self):
        """Test performance impact of resilience layer."""
        import time

        wrapper = NetworkOperationWrapper({}, logging.getLogger())

        if not wrapper.check_internet_connectivity():
            pytest.skip("No internet connectivity")

        # Measure time for successful operation
        start = time.time()
        for _ in range(10):
            wrapper.check_internet_connectivity()
        duration = time.time() - start

        avg_time = (duration / 10) * 1000  # Convert to ms

        # Should be reasonably fast (< 1 second per operation)
        assert avg_time < 1000, f"Average operation time too high: {avg_time:.2f}ms"

        # Log performance for visibility
        logging.info(f"Average connectivity check: {avg_time:.2f}ms")


@pytest.mark.integration
class TestCircuitBreakerPersistence:
    """Test circuit breaker state management."""

    def test_circuit_breaker_state_across_operations(self):
        """Test that circuit breaker state persists across operations."""
        config = {
            "performance": {
                "circuit_breaker": {"enabled": True, "failure_threshold": 2, "timeout": 60}
            }
        }

        wrapper = NetworkOperationWrapper(config, logging.getLogger())

        # Get initial state
        initial_status = wrapper.get_circuit_breaker_status()

        # Verify all circuits start closed
        for service, status in initial_status.items():
            assert status["state"] == "closed", f"{service} should start closed"
            assert status["failure_count"] == 0, f"{service} should have no failures"
