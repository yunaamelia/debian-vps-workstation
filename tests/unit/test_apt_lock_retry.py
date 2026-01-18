from unittest.mock import patch

import pytest

from configurator.modules.base import ConfigurationModule, ModuleExecutionError
from configurator.utils.command import CommandResult


class MockModule(ConfigurationModule):
    name = "Test"

    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


def test_install_packages_apt_lock_retry():
    """Test that install_packages retries when APT lock is busy."""
    module = MockModule({})

    # Sequence of results:
    # 1. Lock busy
    # 2. Lock busy
    # 3. Success

    busy_result = CommandResult("apt-get", 100, "", "Could not get lock")
    success_result = CommandResult("apt-get", 0, "Installed", "")

    with patch.object(
        module, "run", side_effect=[busy_result, busy_result, success_result]
    ) as mock_run:
        with patch("time.sleep") as mock_sleep:  # Don't actually sleep
            # Mock update_cache=False to skip that part
            result = module.install_packages(["test-pkg"], update_cache=False)

            assert result is True
            assert mock_run.call_count == 3
            assert mock_sleep.call_count == 2  # Slept twice


def test_install_packages_gives_up_on_fatal_error():
    """Test that install_packages gives up on non-lock errors."""
    module = MockModule({})

    fatal_result = CommandResult("apt-get", 1, "", "Package not found")

    with patch.object(module, "run", return_value=fatal_result):
        with pytest.raises(ModuleExecutionError) as exc:
            module.install_packages(["unknown-pkg"], update_cache=False)

        assert "Exit code: 1" in str(exc.value)
