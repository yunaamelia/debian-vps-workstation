import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from configurator.exceptions import ProfileError

# If configurator package is not installed in editable mode during dev, relative imports might be tricky
# but we are writing to the file structure so absolute imports should work if run from project root.
from configurator.profiles.validator import ProfileValidator


@dataclass
class ProfileInfo:
    """Profile metadata."""

    name: str
    display_name: str
    description: str
    category: str  # beginner, developer, devops, custom
    builtin: bool
    author: Optional[str] = None
    version: Optional[str] = None


@dataclass
class Profile:
    """Configuration profile."""

    name: str
    display_name: str
    description: str
    category: str

    # Modules configuration
    enabled_modules: List[str] = field(default_factory=list)
    disabled_modules: List[str] = field(default_factory=list)

    # Module-specific config
    module_config: Dict[str, Any] = field(default_factory=dict)

    # System settings
    system_config: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    extends: Optional[str] = None  # Inherit from another profile
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "enabled_modules": self.enabled_modules,
            "disabled_modules": self.disabled_modules,
            "module_config": self.module_config,
            "system_config": self.system_config,
            "extends": self.extends,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            enabled_modules=data.get("enabled_modules", []),
            disabled_modules=data.get("disabled_modules", []),
            module_config=data.get("module_config", {}),
            system_config=data.get("system_config", {}),
            extends=data.get("extends"),
            tags=data.get("tags", []),
        )


class ProfileManager:
    """
    Manage configuration profiles.

    Supports:
    - Built-in profiles (beginner, developer, fullstack, etc.)
    - Custom user profiles
    - Profile inheritance
    - Profile validation
    """

    BUILTIN_PROFILES_DIR = Path(__file__).parent / "schemas"
    CUSTOM_PROFILES_DIR = Path.home() / ".config" / "debian-vps-configurator" / "profiles"
    DEFAULT_PROFILE_FILE = CUSTOM_PROFILES_DIR / ".default"

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validator = ProfileValidator()

        # Ensure custom profiles directory exists
        self.CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

        # Cache loaded profiles
        self._cache: Dict[str, Profile] = {}

    def list_profiles(self, category: Optional[str] = None) -> List[ProfileInfo]:
        """
        List all available profiles.

        Args:
            category:  Filter by category (beginner, developer, etc.)

        Returns:
            List of profile metadata
        """
        profiles = []

        # Load built-in profiles
        if self.BUILTIN_PROFILES_DIR.exists():
            for profile_file in self.BUILTIN_PROFILES_DIR.glob("*.yaml"):
                try:
                    with open(profile_file) as f:
                        data = yaml.safe_load(f)

                    info = ProfileInfo(
                        name=data["name"],
                        display_name=data.get("display_name", data["name"]),
                        description=data.get("description", ""),
                        category=data.get("category", "general"),
                        builtin=True,
                        author=data.get("author"),
                        version=data.get("version"),
                    )

                    if category is None or info.category == category:
                        profiles.append(info)

                except Exception as e:
                    self.logger.warning(f"Failed to load profile {profile_file}: {e}")

        # Load custom profiles
        if self.CUSTOM_PROFILES_DIR.exists():
            for profile_file in self.CUSTOM_PROFILES_DIR.glob("*.yaml"):
                try:
                    with open(profile_file) as f:
                        data = yaml.safe_load(f)

                    info = ProfileInfo(
                        name=data["name"],
                        display_name=data.get("display_name", data["name"]),
                        description=data.get("description", ""),
                        category=data.get("category", "custom"),
                        builtin=False,
                        author=data.get("author"),
                        version=data.get("version"),
                    )

                    if category is None or info.category == category:
                        profiles.append(info)

                except Exception as e:
                    self.logger.warning(f"Failed to load custom profile {profile_file}: {e}")

        return sorted(profiles, key=lambda p: (not p.builtin, p.category, p.name))

    def load_profile(self, name: str) -> Profile:
        """
        Load a profile by name.

        Args:
            name: Profile name

        Returns:
            Loaded profile

        Raises:
            ProfileError: If profile not found or invalid
        """
        # Check cache
        if name in self._cache:
            return self._cache[name]

        # Try built-in first
        builtin_path = self.BUILTIN_PROFILES_DIR / f"{name}.yaml"
        custom_path = self.CUSTOM_PROFILES_DIR / f"{name}.yaml"

        profile_path = None
        if builtin_path.exists():
            profile_path = builtin_path
        elif custom_path.exists():
            profile_path = custom_path
        else:
            raise ProfileError(
                what=f"Profile '{name}' not found",
                why=f"No profile file found at {builtin_path} or {custom_path}",
                how=f"Available profiles: {', '.join(p.name for p in self.list_profiles())}",
            )

        # Load profile
        try:
            with open(profile_path) as f:
                data = yaml.safe_load(f)

            profile = Profile.from_dict(data)

            # Handle inheritance
            if profile.extends:
                base_profile = self.load_profile(profile.extends)
                profile = self._merge_profiles(base_profile, profile)

            # Validate
            validation_errors = self.validator.validate(profile)
            if validation_errors:
                raise ProfileError(
                    what=f"Profile '{name}' is invalid",
                    why=f"Validation errors: {', '.join(validation_errors)}",
                    how="Fix the profile configuration",
                )

            # Cache
            self._cache[name] = profile

            return profile

        except yaml.YAMLError as e:
            raise ProfileError(
                what=f"Failed to parse profile '{name}'",
                why=f"YAML syntax error: {e}",
                how="Check the YAML syntax in the profile file",
            )

    def save_profile(self, profile: Profile, overwrite: bool = False) -> None:
        """
        Save a profile.

        Args:
            profile: Profile to save
            overwrite: Allow overwriting existing profile

        Raises:
            ProfileError: If profile invalid or already exists
        """
        # Validate
        validation_errors = self.validator.validate(profile)
        if validation_errors:
            raise ProfileError(
                what=f"Cannot save invalid profile '{profile.name}'",
                why=f"Validation errors: {', '.join(validation_errors)}",
                how="Fix the validation errors",
            )

        # Check if already exists
        save_path = self.CUSTOM_PROFILES_DIR / f"{profile.name}.yaml"
        if save_path.exists() and not overwrite:
            raise ProfileError(
                what=f"Profile '{profile.name}' already exists",
                why=f"File exists at {save_path}",
                how="Use overwrite=True to replace it",
            )

        # Save
        try:
            with open(save_path, "w") as f:
                yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)

            self.logger.info(f"Saved profile '{profile.name}' to {save_path}")

            # Invalidate cache to force reload and merge on next access
            if profile.name in self._cache:
                del self._cache[profile.name]

        except Exception as e:
            raise ProfileError(
                what=f"Failed to save profile '{profile.name}'",
                why=str(e),
                how="Check file permissions and disk space",
            )

    def delete_profile(self, name: str) -> None:
        """Delete a custom profile."""
        # Can't delete built-in
        builtin_path = self.BUILTIN_PROFILES_DIR / f"{name}.yaml"
        if builtin_path.exists():
            raise ProfileError(
                what=f"Cannot delete built-in profile '{name}'",
                why="Built-in profiles are read-only",
                how="Create a custom profile instead",
            )

        custom_path = self.CUSTOM_PROFILES_DIR / f"{name}.yaml"
        if not custom_path.exists():
            raise ProfileError(
                what=f"Profile '{name}' not found",
                why=f"No custom profile at {custom_path}",
                how="Check available profiles with list_profiles()",
            )

        custom_path.unlink()
        self.logger.info(f"Deleted profile '{name}'")

        # Remove from cache
        if name in self._cache:
            del self._cache[name]

    def get_default_profile(self) -> Optional[str]:
        """Get the name of the default profile."""
        if self.DEFAULT_PROFILE_FILE.exists():
            return self.DEFAULT_PROFILE_FILE.read_text().strip()
        return None

    def set_default_profile(self, name: str) -> None:
        """Set the default profile."""
        # Verify profile exists
        self.load_profile(name)  # Raises if not found

        self.DEFAULT_PROFILE_FILE.write_text(name)
        self.logger.info(f"Set default profile to '{name}'")

    def _merge_profiles(self, base: Profile, override: Profile) -> Profile:
        """Merge two profiles (for inheritance)."""
        merged = Profile(
            name=override.name,
            display_name=override.display_name,
            description=override.description,
            category=override.category,
        )

        # Merge enabled modules (union)
        merged.enabled_modules = list(set(base.enabled_modules + override.enabled_modules))

        # Merge disabled modules
        merged.disabled_modules = list(set(base.disabled_modules + override.disabled_modules))

        # Remove disabled from enabled
        merged.enabled_modules = [
            m for m in merged.enabled_modules if m not in merged.disabled_modules
        ]

        # Merge configs (override takes precedence)
        merged.module_config = {**base.module_config, **override.module_config}
        merged.system_config = {**base.system_config, **override.system_config}

        # Merge tags
        merged.tags = list(set(base.tags + override.tags))

        return merged
