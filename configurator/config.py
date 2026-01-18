"""
Configuration management for the configurator.

Handles:
- Loading YAML configuration files
- Profile management (beginner, intermediate, advanced)
- Configuration validation
- Default values
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from configurator.exceptions import ConfigurationError

# Default paths
CONFIG_DIR = Path(__file__).parent.parent / "config"
PROFILES_DIR = CONFIG_DIR / "profiles"


class ConfigManager:
    """
    Manages configuration loading and access.

    Configuration is loaded from:
    1. Default configuration (config/default.yaml)
    2. Profile configuration (config/profiles/{profile}.yaml)
    3. User configuration (--config flag)
    4. Command-line overrides

    Later sources override earlier ones.
    """

    # Default configuration values
    DEFAULTS: Dict[str, Any] = {
        "system": {
            "hostname": "dev-workstation",
            "timezone": "UTC",
            "locale": "en_US.UTF-8",
            "swap_size_gb": 2,
            "kernel_tuning": True,
        },
        "security": {
            "enabled": True,  # Cannot be disabled
            "ufw": {
                "enabled": True,
                "default_incoming": "deny",
                "default_outgoing": "allow",
                "ssh_port": 22,
                "ssh_rate_limit": True,
            },
            "fail2ban": {
                "enabled": True,
                "ssh_max_retry": 5,
                "ssh_ban_time": 3600,
            },
            "ssh": {
                "disable_root_password": True,
                "disable_password_auth": False,  # Keep enabled for beginners
            },
            "auto_updates": True,
        },
        "desktop": {
            "enabled": True,
            "xrdp_port": 3389,
            "environment": "xfce4",
        },
        "languages": {
            "python": {
                "enabled": True,
                "version": "system",  # Use Debian's Python
                "dev_tools": ["black", "pylint", "mypy", "pytest", "ipython"],
            },
            "nodejs": {
                "enabled": True,
                "version": "20",  # LTS
                "use_nvm": True,
                "package_managers": ["npm", "yarn", "pnpm"],
            },
            "golang": {"enabled": False},
            "rust": {"enabled": False},
            "java": {"enabled": False},
            "php": {"enabled": False},
        },
        "tools": {
            "docker": {
                "enabled": True,
                "compose": True,
            },
            "git": {
                "enabled": True,
                "github_cli": True,
            },
            "editors": {
                "vscode": {"enabled": True},
                "cursor": {"enabled": False},
                "neovim": {"enabled": False},
            },
        },
        "networking": {
            "wireguard": {"enabled": False},
            "caddy": {"enabled": False},
        },
        "monitoring": {
            "netdata": {"enabled": False},
        },
        "interactive": True,
        "verbose": False,
        "dry_run": False,
    }

    # Profile definitions
    PROFILES: Dict[str, Dict[str, Any]] = {
        "beginner": {
            "name": "🟢 Quick Setup (Recommended for Beginners)",
            "description": "Safe defaults, minimal questions, ~30 minutes",
            "config": {
                "interactive": True,
                "languages": {
                    "golang": {"enabled": False},
                    "rust": {"enabled": False},
                    "java": {"enabled": False},
                    "php": {"enabled": False},
                },
                "tools": {
                    "editors": {
                        "cursor": {"enabled": False},
                        "neovim": {"enabled": False},
                    },
                },
                "networking": {
                    "wireguard": {"enabled": False},
                    "caddy": {"enabled": False},
                },
                "monitoring": {
                    "netdata": {"enabled": True},
                },
            },
        },
        "intermediate": {
            "name": "🟡 Standard Setup",
            "description": "Balanced configuration, ~45 minutes",
            "config": {
                "languages": {
                    "golang": {"enabled": True},
                },
                "tools": {
                    "editors": {
                        "cursor": {"enabled": True},
                        "neovim": {"enabled": True},
                    },
                },
                "networking": {
                    "caddy": {"enabled": True},
                },
                "monitoring": {
                    "netdata": {"enabled": True},
                },
            },
        },
        "advanced": {
            "name": "🔴 Advanced Setup",
            "description": "Full control, all features, ~60 minutes",
            "config": {
                "languages": {
                    "golang": {"enabled": True},
                    "rust": {"enabled": True},
                    "java": {"enabled": True},
                    "php": {"enabled": True},
                },
                "tools": {
                    "editors": {
                        "cursor": {"enabled": True},
                        "neovim": {"enabled": True},
                    },
                },
                "networking": {
                    "wireguard": {"enabled": True},
                    "caddy": {"enabled": True},
                },
                "monitoring": {
                    "netdata": {"enabled": True},
                },
            },
        },
    }

    def __init__(
        self,
        config_file: Optional[Path] = None,
        profile: Optional[str] = None,
    ):
        """
        Initialize configuration manager.

        Args:
            config_file: Optional custom config file path (string or Path)
            profile: Profile name (beginner, intermediate, advanced)
        """
        # Convert config_file to Path if it's a string
        if config_file is not None:
            if isinstance(config_file, str):
                self.config_file = Path(config_file)
            else:
                self.config_file = config_file
        else:
            self.config_file = None

        self.profile = profile
        self._config: Dict[str, Any] = {}

        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources."""
        # Start with defaults
        self._config = self._deep_copy(self.DEFAULTS)

        # Load default.yaml if exists
        default_file = CONFIG_DIR / "default.yaml"
        if default_file.exists():
            self._merge_config(self._load_yaml(default_file))

        # Load profile if specified
        if self.profile:
            if self.profile not in self.PROFILES:
                raise ConfigurationError(
                    what=f"Unknown profile: {self.profile}",
                    why=f"Valid profiles are: {', '.join(self.PROFILES.keys())}",
                    how="Use one of the valid profile names",
                )

            # Load profile defaults
            self._merge_config(self.PROFILES[self.profile]["config"])

            # Load profile file if exists
            profile_file = PROFILES_DIR / f"{self.profile}.yaml"
            if profile_file.exists():
                self._merge_config(self._load_yaml(profile_file))

        # Load custom config file if specified
        if self.config_file:
            if not self.config_file.exists():
                raise ConfigurationError(
                    what=f"Configuration file not found: {self.config_file}",
                    why="The specified configuration file does not exist",
                    how=f"Check the path and try again: {self.config_file}",
                )
            self._merge_config(self._load_yaml(self.config_file))

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load a YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                what=f"Invalid YAML in {path}",
                why=str(e),
                how="Check the YAML syntax and try again",
            )

    def _merge_config(self, override: Dict[str, Any]) -> None:
        """Deep merge override into current config."""
        self._config = self._deep_merge(self._config, override)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = self._deep_copy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = self._deep_copy(value)

        return result

    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a nested structure."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "system.hostname" or "languages.python.enabled")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config

    def is_module_enabled(self, module_name: str) -> bool:
        """
        Check if a module is enabled.

        Args:
            module_name: Name of the module (e.g., "docker", "python", "vscode")

        Returns:
            True if module is enabled
        """
        # Check common paths for module configuration
        paths = [
            f"tools.{module_name}.enabled",
            f"tools.editors.{module_name}.enabled",
            f"languages.{module_name}.enabled",
            f"networking.{module_name}.enabled",
            f"monitoring.{module_name}.enabled",
            f"{module_name}.enabled",
        ]

        for path in paths:
            value = self.get(path)
            if value is not None:
                return bool(value)

        return False

    def get_enabled_modules(self) -> List[str]:
        """
        Get list of all enabled modules.

        Returns:
            List of enabled module names
        """
        enabled = []

        # Check for explicit module override list (e.g. from CLI)
        explicit_modules = self.get("modules.enabled")
        if explicit_modules:
            return explicit_modules

        # Always include mandatory modules
        enabled.extend(["system", "security"])

        # Check desktop
        if self.get("desktop.enabled", True):
            enabled.append("desktop")

        # Check languages
        for lang in ["python", "nodejs", "golang", "rust", "java", "php"]:
            if self.get(f"languages.{lang}.enabled", False):
                enabled.append(lang)

        # Check tools
        if self.get("tools.docker.enabled", False):
            enabled.append("docker")
        if self.get("tools.git.enabled", False):
            enabled.append("git")

        # Check editors
        for editor in ["vscode", "cursor", "neovim"]:
            if self.get(f"tools.editors.{editor}.enabled", False):
                enabled.append(editor)

        # Check networking
        for net in ["wireguard", "caddy"]:
            if self.get(f"networking.{net}.enabled", False):
                enabled.append(net)

        # Check monitoring
        if self.get("monitoring.netdata.enabled", False):
            enabled.append("netdata")

        return enabled

    def validate(self) -> bool:
        """
        Validate the configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError if configuration is invalid
        """
        try:
            from pydantic import ValidationError

            from configurator.config_schema import Config

            # Use Config model to validate
            # This handles type checking, constraints, and custom logic
            Config(**self._config)
            return True

        except ValidationError as e:
            # Convert first Pydantic error to user-friendly ConfigurationError
            error = e.errors()[0]

            # Extract location (e.g., security -> ssh -> port)
            loc_parts = [str(part) for part in error["loc"]]
            loc = " -> ".join(loc_parts)

            msg = error["msg"]
            ctx = error.get("ctx", {})

            # Construct friendly "Why"
            why = f"Validation failed for '{loc}': {msg}"

            # Construct friendly "How"
            how = "Check the configuration file or flags against the schema."

            # Customized advice based on error type
            err_type = error.get("type", "")

            if "int" in err_type:
                how = f"The field '{loc}' requires a whole number (integer)."
            elif "bool" in err_type:
                how = f"The field '{loc}' requires a boolean value (true/false)."
            elif "missing" in err_type:
                how = f"The required field '{loc_parts[-1]}' is missing. Please add it to your configuration."
            elif "greater_than" in err_type:
                limit = ctx.get("gt") or ctx.get("ge")
                how = f"The value must be greater than {limit}."
            elif "less_than" in err_type:
                limit = ctx.get("lt") or ctx.get("le")
                how = f"The value must be less than {limit}."

            raise ConfigurationError(
                what=f"Configuration Error: {loc}",
                why=why,
                how=how,
            )
        except ImportError:
            # Fallback if pydantic not found (should be installed)
            self.validate_legacy()
            return True

    def validate_legacy(self) -> bool:
        """Legacy validation logic."""
        # Security cannot be disabled
        if not self.get("security.enabled", True):
            raise ConfigurationError(
                what="Security module cannot be disabled",
                why="Security is mandatory for all installations",
                how="Remove or set 'security.enabled: true' in your configuration",
            )

        # Validate hostname format
        hostname = self.get("system.hostname", "")
        if hostname:
            import re

            if not re.match(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", hostname):
                raise ConfigurationError(
                    what=f"Invalid hostname: {hostname}",
                    why="Hostname must be lowercase alphanumeric with optional hyphens",
                    how="Use a valid hostname like 'dev-workstation' or 'myserver'",
                )

        # Validate swap size
        swap_size = self.get("system.swap_size_gb", 2)
        if not isinstance(swap_size, (int, float)) or swap_size < 0:
            raise ConfigurationError(
                what=f"Invalid swap size: {swap_size}",
                why="Swap size must be a non-negative number",
                how="Set swap_size_gb to 0 (disabled) or a positive number",
            )
        return True

    @classmethod
    def get_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """Get available profiles with their descriptions."""
        return {
            name: {
                "name": profile["name"],
                "description": profile["description"],
            }
            for name, profile in cls.PROFILES.items()
        }
