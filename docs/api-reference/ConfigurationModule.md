# ConfigurationModule

**Module:** `configurator.modules.base`

Abstract base class for all configuration modules.

## Methods

### `__init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None, rollback_manager: Optional[configurator.core.rollback.RollbackManager] = None, dry_run_manager: Optional[ForwardRef('DryRunManager')] = None, circuit_breaker_manager: Optional[configurator.utils.circuit_breaker.CircuitBreakerManager] = None, package_cache_manager: Optional[configurator.core.package_cache.PackageCacheManager] = None)`

Initialize the module.

Args:
    config: Module-specific configuration
    logger: Logger instance
    rollback_manager: Rollback manager for tracking changes
    dry_run_manager: Manager for dry-run recording
    circuit_breaker_manager: Manager for circuit breakers
    package_cache_manager: Manager for package caching

---

### `command_exists(self, command: str) -> bool`

Check if a command exists.

Args:
    command: Command name

Returns:
    True if command exists

---

### `configure(self) -> bool`

Execute configuration/installation.

This is the main method that performs the actual work.
Should register rollback actions for any changes made.

Returns:
    True if successful

Raises:
    ModuleExecutionError with helpful message on failure

---

### `enable_service(self, service: str, start: bool = True) -> bool`

Enable and optionally start a systemd service.

Args:
    service: Service name
    start: Also start the service

Returns:
    True if successful

---

### `get_config(self, key: str, default: Any = None) -> Any`

Get a configuration value.

Args:
    key: Configuration key (supports dot notation)
    default: Default value if not found

Returns:
    Configuration value

---

### `install_packages(self, packages: List[str], update_cache: bool = True) -> bool`

Install APT packages.

Args:
    packages: List of package names
    update_cache: Run apt-get update first

Returns:
    True if installation was successful

---

### `install_packages_resilient(self, packages: List[str], update_cache: bool = True) -> bool`

Install packages with network resilience.

This is the preferred method for package installation as it includes:
- Circuit breaker protection
- Automatic retry with exponential backoff
- Proper timeout handling
- Rollback registration

Args:
    packages: List of package names
    update_cache: Update APT cache first

Returns:
    True if successful

---

### `is_service_active(self, service: str) -> bool`

Check if a systemd service is running.

Args:
    service: Service name

Returns:
    True if service is active

---

### `is_service_enabled(self, service: str) -> bool`

Check if a systemd service is enabled.

Args:
    service: Service name

Returns:
    True if service is enabled

---

### `restart_service(self, service: str) -> bool`

Restart a systemd service.

Args:
    service: Service name

Returns:
    True if successful

---

### `rollback(self) -> bool`

Rollback changes made by this module.

Default implementation uses the rollback manager.
Override if custom rollback logic is needed.

Returns:
    True if rollback was successful

---

### `run(self, command: str, check: bool = True, rollback_command: Optional[str] = None, description: str = '', force_execute: bool = False, **kwargs: Any) -> configurator.utils.command.CommandResult`

Run a shell command.

Args:
    command: Command content
    check: Raise exception if command fails
    rollback_command: Command to run if this command needs rollback
    description: Description of the command (for logs/UI)
    force_execute: Execute command even in dry-run mode (use checks)
    **kwargs: Additional arguments for run_command

---

### `validate(self) -> bool`

Validate prerequisites before installation.

Check that all requirements are met before attempting installation.
This might include checking for existing installations, available
disk space, network connectivity, etc.

Returns:
    True if ready to install, False otherwise

Raises:
    PrerequisiteError with helpful message if validation fails

---

### `verify(self) -> bool`

Verify installation was successful.

Check that everything is working correctly after installation.
This might include checking service status, running test commands,
verifying file permissions, etc.

Returns:
    True if verified successfully

---

### `write_file(self, path: str, content: str, mode: int = 420, backup: bool = False, **kwargs) -> None`

Write content to file (with dry-run support).

---
