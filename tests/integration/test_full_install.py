"""
Integration tests for the full installation flow.

These tests are designed to run on a real Debian 13 VPS.
They use pytest markers for selective execution.

Run integration tests:
    pytest tests/integration/ -v --slow

Skip integration tests in CI:
    pytest tests/unit/ -v
"""

import os

import pytest

from configurator.config import ConfigManager
from configurator.core.installer import Installer
from configurator.core.validator import SystemValidator


# Skip all integration tests if not on Debian 13
def is_debian_13():
    """Check if running on Debian 13."""
    try:
        with open("/etc/os-release") as f:
            content = f.read()
            return 'VERSION_ID="13"' in content and "ID=debian" in content
    except FileNotFoundError:
        return False


def is_root():
    """Check if running as root."""
    return os.getuid() == 0


# Conditional skip decorator
skip_unless_debian = pytest.mark.skipif(
    not is_debian_13(), reason="Integration tests require Debian 13"
)

skip_unless_root = pytest.mark.skipif(not is_root(), reason="Integration tests require root access")


@pytest.mark.integration
@pytest.mark.slow
class TestFullInstallation:
    """
    Integration tests for full installation on a real VPS.

    These tests should be run on a fresh Debian 13 VPS.
    They will make actual changes to the system.

    WARNING: Do not run these on a production system!
    """

    @skip_unless_debian
    def test_system_validation_on_debian(self):
        """Test that system validation passes on Debian 13."""
        validator = SystemValidator()

        # This should not raise on Debian 13
        result = validator.validate_all(strict=False)

        # On Debian 13, OS check should pass
        os_results = [r for r in validator.results if r.name == "Operating System"]
        assert len(os_results) == 1
        assert os_results[0].passed is True

    @skip_unless_debian
    def test_config_loading_with_profiles(self):
        """Test loading all profiles on real system."""
        for profile in ["beginner", "intermediate", "advanced"]:
            config = ConfigManager(profile=profile)

            # Should load without errors
            assert config.get("system.hostname") is not None
            assert config.get("security.enabled") is True

            # Validation should pass
            assert config.validate() is True

    @skip_unless_debian
    @skip_unless_root
    def test_dry_run_installation(self):
        """Test dry-run installation on real system."""
        config = ConfigManager(profile="beginner")
        installer = Installer(config=config)

        # Dry run should complete without errors
        result = installer.install(dry_run=True)

        # Result should be True (dry run always succeeds)
        assert result is True

    @skip_unless_debian
    @skip_unless_root
    @pytest.mark.destructive
    def test_system_module_installation(self):
        """
        Test system module installation.

        WARNING: This makes real changes to the system!
        """
        from configurator.core.rollback import RollbackManager
        from configurator.modules.system import SystemModule

        config = {
            "hostname": "test-workstation",
            "timezone": "UTC",
            "locale": "en_US.UTF-8",
            "swap_size_gb": 0,  # Don't create swap in test
            "kernel_tuning": False,  # Don't tune kernel in test
        }

        rollback = RollbackManager()
        module = SystemModule(
            config=config,
            rollback_manager=rollback,
        )

        # Validate should pass
        assert module.validate() is True

        # Configure should succeed
        assert module.configure() is True

        # Verify should pass
        assert module.verify() is True


@pytest.mark.integration
class TestModuleValidation:
    """Test module validation without making changes."""

    def test_all_modules_can_be_instantiated(self):
        """Test that all modules can be created."""
        from configurator.core.rollback import RollbackManager
        from configurator.modules import (
            DesktopModule,
            DockerModule,
            GitModule,
            NodeJSModule,
            PythonModule,
            SecurityModule,
            SystemModule,
            VSCodeModule,
        )

        rollback = RollbackManager()

        modules = [
            SystemModule,
            SecurityModule,
            DesktopModule,
            PythonModule,
            NodeJSModule,
            DockerModule,
            GitModule,
            VSCodeModule,
        ]

        for module_class in modules:
            module = module_class(
                config={},
                rollback_manager=rollback,
            )

            # Should have required attributes
            assert hasattr(module, "name")
            assert hasattr(module, "validate")
            assert hasattr(module, "configure")
            assert hasattr(module, "verify")

    def test_module_priority_ordering(self):
        """Test that modules have correct priority ordering."""
        from configurator.core.installer import Installer

        priorities = Installer.MODULE_PRIORITY

        # System should run before security
        assert priorities["system"] < priorities["security"]

        # Security should run before everything else
        assert priorities["security"] < priorities["desktop"]
        assert priorities["security"] < priorities["python"]
        assert priorities["security"] < priorities["docker"]

        # Languages before tools
        assert priorities["python"] < priorities["vscode"]


@pytest.mark.integration
class TestConfigurationValidation:
    """Test configuration validation."""

    def test_profile_configurations_are_valid(self):
        """Test that all profile configurations pass validation."""
        for profile in ["beginner", "intermediate", "advanced"]:
            config = ConfigManager(profile=profile)
            assert config.validate() is True

    def test_enabled_modules_match_profile(self):
        """Test that enabled modules match profile expectations."""
        # Beginner should have minimal modules
        beginner = ConfigManager(profile="beginner")
        beginner_modules = beginner.get_enabled_modules()

        assert "system" in beginner_modules
        assert "security" in beginner_modules
        assert "python" in beginner_modules

        # Advanced should have more modules
        advanced = ConfigManager(profile="advanced")
        advanced_modules = advanced.get_enabled_modules()

        # Advanced should have everything beginner has plus more
        for module in beginner_modules:
            assert module in advanced_modules

    def test_custom_config_file_loading(self, tmp_path):
        """Test loading a custom configuration file."""
        config_content = """
system:
  hostname: custom-server
  timezone: Asia/Jakarta

languages:
  python:
    enabled: true
  nodejs:
    enabled: false

tools:
  docker:
    enabled: true
"""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(config_content)

        config = ConfigManager(config_file=config_file)

        assert config.get("system.hostname") == "custom-server"
        assert config.get("system.timezone") == "Asia/Jakarta"
        assert config.get("languages.python.enabled") is True
        assert config.get("languages.nodejs.enabled") is False


@pytest.mark.integration
class TestCLIIntegration:
    """Test CLI commands in isolation."""

    def test_cli_help_command(self):
        """Test that CLI help works."""
        from click.testing import CliRunner

        from configurator.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Debian 13 VPS Workstation Configurator" in result.output

    def test_cli_version_command(self):
        """Test that CLI version works."""
        from click.testing import CliRunner

        from configurator.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "2.0.0" in result.output

    def test_cli_profiles_command(self):
        """Test that profiles command works."""
        from click.testing import CliRunner

        from configurator.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["profiles"])

        assert result.exit_code == 0
        assert "beginner" in result.output
        assert "intermediate" in result.output
        assert "advanced" in result.output

    def test_cli_install_dry_run(self):
        """Test install command with dry-run."""
        from click.testing import CliRunner

        from configurator.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "install",
                "--profile",
                "beginner",
                "--dry-run",
                "--non-interactive",
                "--skip-validation",
            ],
        )

        # Should complete without crashing
        # Exit code 1 is expected on non-Debian systems due to validation
        # But should not have uncaught exceptions
        assert result.exit_code in (0, 1)
