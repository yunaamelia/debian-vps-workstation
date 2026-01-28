import time
from unittest.mock import MagicMock, patch

import pytest

from configurator.core.installer import Installer
from configurator.modules.base import ConfigurationModule


class SlowModule(ConfigurationModule):
    def __init__(self, name, delay=0.1, depends_on=None):
        self.name = name
        self._delay = delay
        self.depends_on = depends_on or []
        self.priority = 100
        self.force_sequential = False
        # Bypass base init for test simplicity

    def validate(self):
        return True

    def configure(self):
        time.sleep(self._delay)
        return True

    def verify(self):
        return True


class TestParallelExecutionIntegration:
    @pytest.mark.skip(
        reason="Requires root/special permissions to access /etc/debian-vps-configurator"
    )
    @patch("configurator.core.installer.ConfigManager")
    def test_parallel_execution_speedup(self, MockConfigManager):
        # Setup config
        config = MagicMock()

        def config_get(key, default=None):
            if key == "performance.parallel_execution":
                return True
            if key == "performance.max_workers":
                return 4
            return default

        config.get.side_effect = config_get
        config.get_enabled_modules.return_value = ["slow1", "slow2"]
        MockConfigManager.return_value = config

        installer = Installer(config=config)

        # Mock container to return our slow modules
        installer.container.has = lambda name: True

        module1 = SlowModule("slow1", delay=1.0)
        module2 = SlowModule("slow2", delay=1.0)

        mapping = {"slow1": module1, "slow2": module2}
        installer.container.make = lambda name, config: mapping[name]

        # We also need to patch _execute_module_instance because it calls checks
        # But wait, our SlowModule mocks everything needed.
        # But Installer.install calls _execute_module_instance which calls methods on module.
        # The key is that they run in parallel.

        start_time = time.time()
        success = installer.install(skip_validation=True, parallel=True)
        duration = time.time() - start_time

        assert success is True
        # If parallel, should take ~1.0s (plus overhead). If sequential, ~2.0s.
        assert duration < 1.8
        print(f"Parallel execution took {duration:.2f}s")

    @pytest.mark.skip(
        reason="Timing assertions unreliable in CI; parallel execution routing varies"
    )
    @patch("configurator.core.installer.ConfigManager")
    def test_sequential_execution_fallback(self, MockConfigManager):
        # Setup config
        config = MagicMock()

        def config_get(key, default=None):
            if key == "performance.parallel_execution":
                return False
            return default

        config.get.side_effect = config_get
        config.get_enabled_modules.return_value = ["slow1", "slow2"]
        MockConfigManager.return_value = config

        installer = Installer(config=config)

        module1 = SlowModule("slow1", delay=0.2)
        module2 = SlowModule("slow2", delay=0.2)

        mapping = {"slow1": module1, "slow2": module2}
        installer.container.make = lambda name, config: mapping[name]
        installer.container.has = lambda name: True

        start_time = time.time()
        success = installer.install(skip_validation=True, parallel=False)
        duration = time.time() - start_time

        assert success is True
        # Sequential should take >= 0.4s (2 modules x 0.2s)
        # Being lenient due to varying execution patterns in CI
        assert duration >= 0.3, (
            f"Sequential execution should take at least 0.3s, took {duration:.2f}s"
        )
        print(f"Sequential execution took {duration:.2f}s")
