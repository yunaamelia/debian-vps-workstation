# StateManager

**Module:** `configurator.core.state.manager`

Manages installation state with SQLite persistence.

Provides:
- State persistence across restarts
- Checkpoint creation and restore
- Resume capability after crashes
- Installation history

## Methods

### `__init__(self, db_path: Optional[pathlib._local.Path] = None, logger: Optional[logging.Logger] = None)`

Initialize state manager.

Args:
    db_path: Path to SQLite database file. If None, uses default location.
            Supports :memory: for in-memory database (testing).
    logger: Logger instance

---

### `can_resume(self) -> bool`

Check if there is an incomplete installation that can be resumed.

Returns:
    True if resumable installation exists

---

### `complete_installation(self, success: bool) -> None`

Mark installation as complete.

Args:
    success: Whether installation succeeded

---

### `create_checkpoint(self, module_name: str, checkpoint_name: str) -> None`

Create a checkpoint for a module.

Args:
    module_name: Module name
    checkpoint_name: Name of checkpoint

---

### `get_installation_history(self, limit: int = 10) -> List[configurator.core.state.models.InstallationState]`

Get installation history.

Args:
    limit: Maximum number of records to return

Returns:
    List of InstallationState objects, most recent first

---

### `resume_installation(self) -> Optional[configurator.core.state.models.InstallationState]`

Resume the most recent incomplete installation.

Returns:
    InstallationState if found, None otherwise

---

### `start_installation(self, profile: str, metadata: Optional[Dict[str, Any]] = None) -> configurator.core.state.models.InstallationState`

Start a new installation.

Args:
    profile: Installation profile name
    metadata: Optional metadata dictionary

Returns:
    New InstallationState

---

### `update_module(self, module_name: str, status: Optional[configurator.core.state.models.ModuleStatus] = None, progress: Optional[int] = None, current_step: Optional[str] = None, error: Optional[str] = None) -> None`

Update module state.

Args:
    module_name: Name of module to update
    status: New status (optional)
    progress: Progress percentage 0-100 (optional)
    current_step: Current execution step (optional)
    error: Error message if failed (optional)

---
