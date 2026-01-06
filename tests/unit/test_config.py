"""
Unit tests for the ConfigManager class.
"""

import pytest

from configurator.config import ConfigManager
from configurator.exceptions import ConfigurationError


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_default_values(self):
        """Test that default values are loaded correctly."""
        config = ConfigManager()

        # Check some defaults
        assert config.get("system.hostname") == "dev-workstation"
        assert config.get("security.enabled") is True
        assert config.get("languages.python.enabled") is True

    def test_get_with_dot_notation(self):
        """Test getting values with dot notation."""
        config = ConfigManager()

        assert config.get("system.timezone") == "UTC"
        assert config.get("security.ufw.ssh_port") == 22
        assert config.get("languages.python.dev_tools") is not None

    def test_get_with_default(self):
        """Test getting non-existent key returns default."""
        config = ConfigManager()

        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_value(self):
        """Test setting values."""
        config = ConfigManager()

        config.set("system.hostname", "new-hostname")
        assert config.get("system.hostname") == "new-hostname"

        config.set("custom.new.key", "value")
        assert config.get("custom.new.key") == "value"

    def test_profile_loading(self):
        """Test loading a profile."""
        config = ConfigManager(profile="beginner")

        # Beginner profile should have monitoring enabled
        assert config.get("monitoring.netdata.enabled") is True
        # But not advanced features
        assert config.get("networking.wireguard.enabled") is False

    def test_invalid_profile(self):
        """Test that invalid profile raises error."""
        with pytest.raises(ConfigurationError):
            ConfigManager(profile="nonexistent")

    def test_config_file_loading(self, temp_config_file):
        """Test loading configuration from file."""
        config = ConfigManager(config_file=temp_config_file)

        assert config.get("system.hostname") == "test-server"

    def test_nonexistent_config_file(self, tmp_path):
        """Test that non-existent config file raises error."""
        fake_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigurationError):
            ConfigManager(config_file=fake_path)

    def test_is_module_enabled(self):
        """Test checking if a module is enabled."""
        config = ConfigManager()

        assert config.is_module_enabled("python") is True
        assert config.is_module_enabled("rust") is False

    def test_get_enabled_modules(self):
        """Test getting list of enabled modules."""
        config = ConfigManager(profile="beginner")

        enabled = config.get_enabled_modules()

        assert "system" in enabled
        assert "security" in enabled
        assert "python" in enabled
        assert "desktop" in enabled

    def test_validation_passes(self):
        """Test that valid configuration passes validation."""
        config = ConfigManager()

        assert config.validate() is True

    def test_security_cannot_be_disabled(self):
        """Test that security module cannot be disabled."""
        config = ConfigManager()
        config.set("security.enabled", False)

        with pytest.raises(ConfigurationError):
            config.validate()

    def test_invalid_hostname(self):
        """Test that invalid hostname fails validation."""
        config = ConfigManager()
        config.set("system.hostname", "INVALID_HOSTNAME!")

        with pytest.raises(ConfigurationError):
            config.validate()

    def test_get_profiles(self):
        """Test getting available profiles."""
        profiles = ConfigManager.get_profiles()

        assert "beginner" in profiles
        assert "intermediate" in profiles
        assert "advanced" in profiles

        assert "name" in profiles["beginner"]
        assert "description" in profiles["beginner"]
