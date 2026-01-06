from configurator.core.dryrun import DryRunManager
from configurator.modules.base import ConfigurationModule


class MockModule(ConfigurationModule):
    name = "Mock Module"

    def validate(self):
        return True

    def configure(self):
        return True

    def verify(self):
        return True


def test_dry_run_manager():
    manager = DryRunManager()
    assert not manager.is_enabled

    manager.enable()
    assert manager.is_enabled

    manager.record_command("echo hello")
    manager.record_package_install(["git", "curl"])

    assert len(manager.changes) == 3
    assert manager.changes[0].type == "command"
    assert manager.changes[1].type == "package"


def test_module_dry_run_integration():
    manager = DryRunManager()
    manager.enable()

    module = MockModule(config={}, dry_run_manager=manager)
    assert module.dry_run is True

    # Test run command
    result = module.run("rm -rf /")
    assert result.success
    assert result.return_code == 0
    # Should not have executed (we can't easily mock run_command global here without patching,
    # but base.py logic skips execution if dry_run is True)

    assert len(manager.changes) == 1
    assert manager.changes[0].target == "rm -rf /"


def test_install_packages_dry_run():
    manager = DryRunManager()
    manager.enable()

    module = MockModule(config={}, dry_run_manager=manager)

    result = module.install_packages(["nginx"])
    assert result is True

    assert len(manager.changes) == 1
    assert manager.changes[0].type == "package"
    assert manager.changes[0].target == "nginx"


def test_dry_run_report():
    manager = DryRunManager()
    manager.enable()
    manager.record_command("test")

    report = manager.generate_report()
    assert "DRY-RUN REPORT" in report
    assert "COMMANDS" in report
    assert "test" in report
