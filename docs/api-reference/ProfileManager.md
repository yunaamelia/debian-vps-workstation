# ProfileManager

**Module:** `configurator.profiles.manager`

Manage configuration profiles.

Supports:
- Built-in profiles (beginner, developer, fullstack, etc.)
- Custom user profiles
- Profile inheritance
- Profile validation

## Methods

### `__init__(self, logger: Optional[logging.Logger] = None)`


---

### `delete_profile(self, name: str)`

Delete a custom profile.

---

### `get_default_profile(self) -> Optional[str]`

Get the name of the default profile.

---

### `list_profiles(self, category: Optional[str] = None) -> List[configurator.profiles.manager.ProfileInfo]`

List all available profiles.

Args:
    category:  Filter by category (beginner, developer, etc.)

Returns:
    List of profile metadata

---

### `load_profile(self, name: str) -> configurator.profiles.manager.Profile`

Load a profile by name.

Args:
    name: Profile name

Returns:
    Loaded profile

Raises:
    ProfileError: If profile not found or invalid

---

### `save_profile(self, profile: configurator.profiles.manager.Profile, overwrite: bool = False)`

Save a profile.

Args:
    profile: Profile to save
    overwrite: Allow overwriting existing profile

Raises:
    ProfileError: If profile invalid or already exists

---

### `set_default_profile(self, name: str)`

Set the default profile.

---
