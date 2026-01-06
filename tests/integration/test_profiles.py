"""
Integration tests for configuration profiles.

Tests profile loading, merging, and validation.
"""

import pytest

from configurator.config import ConfigManager
from configurator.exceptions import ConfigurationError


@pytest.mark.integration
class TestProfileLoading:
    """Tests for profile loading functionality."""

    def test_all_profiles_load_successfully(self):
        """Test that all built-in profiles load without error."""
        profiles = ["beginner", "intermediate", "advanced"]

        for profile in profiles:
            config = ConfigManager(profile=profile)

            # Should have loaded successfully
            assert config.profile == profile
            assert config.config is not None

    def test_beginner_profile_defaults(self):
        """Test beginner profile has expected defaults."""
        config = ConfigManager(profile="beginner")

        # Core features should be enabled
        assert config.get("languages.python.enabled") is True
        assert config.get("languages.nodejs.enabled") is True
        assert config.get("tools.docker.enabled") is True

        # Advanced features should be disabled
        assert config.get("languages.golang.enabled") is False
        assert config.get("languages.rust.enabled") is False
        assert config.get("networking.wireguard.enabled") is False

    def test_advanced_profile_enables_more_features(self):
        """Test advanced profile enables more features than beginner."""
        beginner = ConfigManager(profile="beginner")
        advanced = ConfigManager(profile="advanced")

        # Count enabled modules
        beginner_modules = len(beginner.get_enabled_modules())
        advanced_modules = len(advanced.get_enabled_modules())

        # Advanced should have more
        assert advanced_modules >= beginner_modules

    def test_security_always_enabled(self):
        """Test that security is enabled in all profiles."""
        for profile in ["beginner", "intermediate", "advanced"]:
            config = ConfigManager(profile=profile)
            assert config.get("security.enabled") is True

    def test_profile_overrides_defaults(self):
        """Test that profile values override defaults."""
        # Default has monitoring disabled
        default = ConfigManager()
        assert default.get("monitoring.netdata.enabled") is False

        # Beginner profile should have it enabled
        beginner = ConfigManager(profile="beginner")
        assert beginner.get("monitoring.netdata.enabled") is True


@pytest.mark.integration
class TestConfigMerging:
    """Tests for configuration merging."""

    def test_custom_config_overrides_profile(self, tmp_path):
        """Test that custom config overrides profile settings."""
        config_content = """
system:
  hostname: custom-hostname

languages:
  python:
    enabled: false
"""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(config_content)

        # Load beginner profile with custom overrides
        config = ConfigManager(
            profile="beginner",
            config_file=config_file,
        )

        # Custom values should override profile
        assert config.get("system.hostname") == "custom-hostname"
        assert config.get("languages.python.enabled") is False

        # Non-overridden values should come from profile
        assert config.get("languages.nodejs.enabled") is True

    def test_deep_merge_preserves_nested_values(self, tmp_path):
        """Test that deep merge preserves nested values."""
        config_content = """
security:
  fail2ban:
    ssh_max_retry: 10
"""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(config_content)

        config = ConfigManager(config_file=config_file)

        # Custom value should be set
        assert config.get("security.fail2ban.ssh_max_retry") == 10

        # Other nested values should remain from defaults
        assert config.get("security.fail2ban.enabled") is True
        assert config.get("security.ufw.enabled") is True

    def test_set_creates_nested_structure(self):
        """Test that set() creates nested structure."""
        config = ConfigManager()

        config.set("custom.deeply.nested.value", "test")

        assert config.get("custom.deeply.nested.value") == "test"


@pytest.mark.integration
class TestConfigValidation:
    """Tests for configuration validation."""

    def test_valid_config_passes_validation(self):
        """Test that valid configurations pass validation."""
        config = ConfigManager(profile="beginner")
        assert config.validate() is True

    def test_invalid_hostname_format(self):
        """Test that invalid hostname format fails validation."""
        config = ConfigManager()
        config.set("system.hostname", "INVALID_HOSTNAME!")

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "hostname" in str(exc_info.value).lower()

    def test_valid_hostname_formats(self):
        """Test various valid hostname formats."""
        valid_hostnames = [
            "web-server",
            "dev1",
            "my-super-long-hostname-with-numbers-123",
            "a",
            "server01",
        ]

        for hostname in valid_hostnames:
            config = ConfigManager()
            config.set("system.hostname", hostname)
            assert config.validate() is True

    def test_security_cannot_be_disabled(self):
        """Test that security module cannot be disabled."""
        config = ConfigManager()
        config.set("security.enabled", False)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "security" in str(exc_info.value).lower()

    def test_negative_swap_size_fails(self):
        """Test that negative swap size fails validation."""
        config = ConfigManager()
        config.set("system.swap_size_gb", -1)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "swap" in str(exc_info.value).lower()


@pytest.mark.integration
class TestEnabledModules:
    """Tests for enabled modules detection."""

    def test_mandatory_modules_always_included(self):
        """Test that mandatory modules are always included."""
        config = ConfigManager(profile="beginner")
        modules = config.get_enabled_modules()

        assert "system" in modules
        assert "security" in modules

    def test_is_module_enabled_checks_multiple_paths(self):
        """Test that is_module_enabled checks various config paths."""
        config = ConfigManager()

        # Test tools path
        config.set("tools.docker.enabled", True)
        assert config.is_module_enabled("docker") is True

        # Test languages path
        config.set("languages.python.enabled", True)
        assert config.is_module_enabled("python") is True

        # Test editors path
        config.set("tools.editors.vscode.enabled", True)
        assert config.is_module_enabled("vscode") is True

    def test_disabled_module_not_included(self):
        """Test that disabled modules are not included."""
        config = ConfigManager(profile="beginner")

        # Rust is disabled in beginner profile
        modules = config.get_enabled_modules()
        assert "rust" not in modules
