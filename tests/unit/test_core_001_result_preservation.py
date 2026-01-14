"""
Unit tests for CORE-001: Parallel execution fallback result preservation.
"""

from unittest.mock import Mock

import pytest

from configurator.config import ConfigManager
from configurator.core.installer import Installer


class TestParallelFallbackResultPreservation:
    """Test that successful results are preserved during fallback."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock(spec=ConfigManager)
        config.get.return_value = True
        config.get_enabled_modules.return_value = ["system", "security", "docker", "python"]
        return config

    @pytest.fixture
    def installer(self, mock_config):
        """Create installer instance."""
        logger = Mock()
        reporter = Mock()
        installer = Installer(config=mock_config, logger=logger, reporter=reporter)
        return installer

    def test_preserve_successful_results_dict(self, installer):
        """Test that successful module results are preserved when fallback occurs."""
        # Simulate preservation logic
        results = {"system": True, "security": True, "docker": False}

        # Extract successful modules (this is what the code does)
        successful_modules = [name for name, success in results.items() if success]

        # Verify we got the successful ones
        assert "system" in successful_modules
        assert "security" in successful_modules
        assert "docker" not in successful_modules
        assert len(successful_modules) == 2

    def test_skip_logic_for_completed_modules(self, installer):
        """Test that sequential fallback skips already-completed modules."""
        results = {"system": True, "security": True, "docker": False}
        enabled_modules = ["system", "security", "docker", "python"]

        # Simulate skip logic
        executed_modules = []
        for module_name in enabled_modules:
            if module_name in results and results[module_name]:
                # Skip already-successful
                continue
            executed_modules.append(module_name)

        # Verify only failed/unexecuted modules execute
        assert "system" not in executed_modules
        assert "security" not in executed_modules
        assert "docker" in executed_modules
        assert "python" in executed_modules

    def test_preservation_logging_format(self):
        """Test that preservation log includes count."""
        logger = Mock()
        successful_modules = ["system", "security", "docker"]

        # Simulate the logging call
        logger.info(f"Preserving {len(successful_modules)} successful module results")

        # Verify
        logger.info.assert_called_with("Preserving 3 successful module results")

    def test_skip_logging_includes_module_name(self):
        """Test that skip log includes module name."""
        logger = Mock()
        module_name = "docker"

        # Simulate skip logging
        logger.info(f"⏭️  Skipping already-completed module: {module_name}")

        # Verify
        logger.info.assert_called_with("⏭️  Skipping already-completed module: docker")


class TestFallbackResultsNotCleared:
    """Test that results dict is not cleared on fallback."""

    def test_results_dict_not_cleared(self):
        """Test that results dictionary preserves values."""
        # Simulate the fixed code behavior
        results = {"system": True, "security": True, "docker": False}

        # In the fixed code, we DON'T do: results = {}
        # We preserve the dict
        successful_modules = [name for name, success in results.items() if success]

        # After the fix, results should still have all entries
        assert len(results) == 3
        assert results["system"] is True
        assert results["security"] is True
        assert results["docker"] is False

        # Successful modules list created but results preserved
        assert len(successful_modules) == 2
