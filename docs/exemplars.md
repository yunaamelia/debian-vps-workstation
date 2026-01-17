# Code Exemplars

**Debian VPS Configurator v2.0 — Reference Code Examples**

> High-quality, representative code examples demonstrating coding standards and patterns.

---

## Introduction

This document identifies the best examples of code in our codebase. Use these exemplars when:

- Learning our coding conventions
- Implementing new modules or features
- Reviewing code for consistency
- Onboarding new team members

Each exemplar demonstrates one or more best practices and can be used as a template for similar implementations.

---

## Table of Contents

1. [Abstract Base Class — Module Interface](#1-abstract-base-class--module-interface)
2. [Dependency Injection Container](#2-dependency-injection-container)
3. [Exception Hierarchy](#3-exception-hierarchy)
4. [Circuit Breaker Pattern](#4-circuit-breaker-pattern)
5. [Retry Decorator](#5-retry-decorator)
6. [Rollback Manager](#6-rollback-manager)
7. [Configuration Management](#7-configuration-management)
8. [Input Validation](#8-input-validation)
9. [Feature Module Implementation](#9-feature-module-implementation)
10. [Test Fixtures](#10-test-fixtures)
11. [Integration Tests](#11-integration-tests)

---

## 1. Abstract Base Class — Module Interface

**File:** [base.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/modules/base.py)
**Category:** Interface Design | Pattern Type: Template Method
**Lines:** 662

### Why This Is Exemplary

- **Comprehensive documentation**: Module-level docstring explains purpose clearly
- **Abstract interface**: Uses ABC to define required methods (`validate`, `configure`, `verify`)
- **Default implementation**: Provides sensible defaults for common operations
- **Dependency injection**: Constructor accepts optional dependencies with defaults
- **Thread safety**: Class-level APT lock prevents race conditions
- **Rich utilities**: Provides helper methods for common operations

### Key Principles Demonstrated

1. **Template Method Pattern** — Abstract base class defines the algorithm skeleton
2. **Dependency Inversion** — Accepts interfaces, not concrete implementations
3. **Defensive Programming** — Handles dry-run mode, rollback registration

### Representative Code Snippet

```python
class ConfigurationModule(ABC):
    """Abstract base class for all configuration modules."""

    # Global lock for APT operations to prevent parallel execution failures
    _APT_LOCK = threading.Lock()

    # Module metadata - override in subclasses
    name: str = "Base Module"
    description: str = "Base configuration module"
    priority: int = 100
    depends_on: List[str] = []
    force_sequential: bool = False
    mandatory: bool = False

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        rollback_manager: Optional[RollbackManager] = None,
        dry_run_manager: Optional["DryRunManager"] = None,
        circuit_breaker_manager: Optional[CircuitBreakerManager] = None,
        package_cache_manager: Optional[PackageCacheManager] = None,
    ):
        """Initialize the module with dependency injection."""
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.rollback_manager = rollback_manager or RollbackManager()
        # ... additional initialization

    @abstractmethod
    def validate(self) -> bool:
        """Validate prerequisites before installation."""

    @abstractmethod
    def configure(self) -> bool:
        """Execute configuration/installation."""

    @abstractmethod
    def verify(self) -> bool:
        """Verify installation was successful."""

    def rollback(self) -> bool:
        """Rollback changes made by this module."""
        return self.rollback_manager.rollback()
```

---

## 2. Dependency Injection Container

**File:** [container.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/core/container.py)
**Category:** Architectural Component | Pattern Type: Service Locator + DI
**Lines:** 154

### Why This Is Exemplary

- **Clear responsibility**: Single purpose — manage service lifecycles
- **Flexible registration**: Supports singletons, factories, and mocks
- **Circular dependency detection**: Prevents infinite loops
- **Well-documented API**: Each method has docstring with usage examples
- **Type hints**: Full type annotations for IDE support

### Key Principles Demonstrated

1. **Single Responsibility** — Only handles service registration and resolution
2. **Open/Closed** — Easy to extend with new service types
3. **Dependency Injection** — Central point for wiring dependencies

### Representative Code Snippet

```python
class Container:
    """
    A simple but powerful Dependency Injection (DI) container.

    Usage:
        container = Container()

        # Register a singleton (lazy instantiation)
        container.singleton('config', lambda: ConfigManager())

        # Register a factory
        container.factory('logger', lambda container: logging.getLogger())

        # Resolve
        config = container.get('config')
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Callable[[], Any]] = {}
        self._factories: Dict[str, Callable[["Container"], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._resolving: set = set()  # Circular dependency detection

    def singleton(self, name: str, factory: Callable[..., Any]) -> None:
        """Register a singleton service (created once, cached)."""
        self._singletons[name] = factory

    def mock(self, name: str, instance: Any) -> None:
        """Register a pre-instantiated mock for testing."""
        self._instances[name] = instance

    def get(self, name: str, **kwargs) -> Any:
        """Resolve a service by name with circular dependency detection."""
        if name in self._resolving:
            raise CircularDependencyError(f"Circular dependency detected for '{name}'")
        # ... resolution logic
```

---

## 3. Exception Hierarchy

**File:** [exceptions.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/exceptions.py)
**Category:** Cross-Cutting Concern | Pattern Type: User-Friendly Errors
**Lines:** 277

### Why This Is Exemplary

- **User-centric design**: WHAT/WHY/HOW format for every error
- **Actionable messages**: Tells users exactly how to fix issues
- **Documentation links**: Optional links to relevant docs
- **Proper hierarchy**: Specific exceptions inherit from base
- **Beautiful formatting**: ASCII art for visibility

### Key Principles Demonstrated

1. **User Experience** — Errors designed for humans, not just debugging
2. **Inheritance** — Proper exception hierarchy for catch blocks
3. **Consistency** — All exceptions follow same formatting pattern

### Representative Code Snippet

```python
class ConfiguratorError(Exception):
    """
    Base exception for all configurator errors.

    Provides beginner-friendly error messages with:
    - What happened
    - Why it happened
    - How to fix it
    - Optional documentation link
    """

    def __init__(
        self,
        what: str,
        why: str = "",
        how: str = "",
        docs_link: Optional[str] = None,
    ):
        self.what = what
        self.why = why
        self.how = how
        self.docs_link = docs_link
        message = self._format_message()
        super().__init__(message)

    def _format_message(self) -> str:
        """Format the error message in a user-friendly way."""
        lines = [
            "",
            "╔════════════════════════════════════════════════════════╗",
            "║                  ❌ ERROR OCCURRED                      ║",
            "╚════════════════════════════════════════════════════════╝",
            "",
            "WHAT HAPPENED:",
            f"  {self.what}",
        ]
        # ... WHY and HOW sections
        return "\n".join(lines)


class NetworkError(ConfiguratorError):
    """Raised for network-related errors."""

    def __init__(self, url: str, error_details: str, **kwargs):
        what = "Network operation failed"
        why = f"Cannot access: {url}\nError: {error_details}"
        how = (
            "1. Check internet: ping -c 3 8.8.8.8\n"
            "2. Check DNS: host deb.debian.org\n"
            "3. Check proxy/firewall settings"
        )
        super().__init__(what=what, why=why, how=how, **kwargs)
```

---

## 4. Circuit Breaker Pattern

**File:** [circuit_breaker.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/utils/circuit_breaker.py)
**Category:** Resilience Pattern | Pattern Type: Circuit Breaker
**Lines:** 312

### Why This Is Exemplary

- **Complete implementation**: States (CLOSED, OPEN, HALF_OPEN) with transitions
- **Thread-safe**: Uses RLock for concurrent access
- **Rich metrics**: Tracks calls, failures, success rates
- **User-friendly errors**: Explains what happened and what to do
- **Manager class**: Handles multiple breakers with named lookup

### Key Principles Demonstrated

1. **State Machine** — Clear state transitions with explicit methods
2. **Fail-Fast** — Prevents wasting time on known-failing services
3. **Self-Healing** — Automatically tests recovery after timeout

### Representative Code Snippet

```python
class CircuitState(Enum):
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Too many failures, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        success_threshold: int = 1,
        timeout: float = 60.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.state = CircuitState.CLOSED
        self._state_lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        with self._state_lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerError(...)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise
```

---

## 5. Retry Decorator

**File:** [retry.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/utils/retry.py)
**Category:** Utility | Pattern Type: Decorator
**Lines:** 82

### Why This Is Exemplary

- **Configurable**: All retry parameters are customizable
- **Exponential backoff**: Prevents thundering herd
- **Jitter**: Randomized delays prevent synchronized retries
- **Test-aware**: Reduces delays in test environment
- **Proper logging**: Logs each retry attempt with context

### Key Principles Demonstrated

1. **Decorator Pattern** — Wraps function without modifying it
2. **Configuration over Code** — Behavior controlled by parameters
3. **Production-Ready** — Handles edge cases like test mode

### Representative Code Snippet

```python
def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
) -> Callable:
    """Decorator for retrying a function with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Test mode: reduce delays to prevent hangs
            if os.environ.get("PYTEST_CURRENT_TEST"):
                actual_max_retries = min(max_retries, 2)
                actual_base_delay = min(base_delay, 0.1)

            retries = 0
            delay = actual_base_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > actual_max_retries:
                        raise

                    # Calculate delay with jitter
                    current_delay = delay * (0.5 + random.random()) if jitter else delay
                    time.sleep(min(current_delay, actual_max_delay))
                    delay *= backoff_factor

        return wrapper
    return decorator
```

---

## 6. Rollback Manager

**File:** [rollback.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/core/rollback.py)
**Category:** Core Component | Pattern Type: Command + Memento
**Lines:** 259

### Why This Is Exemplary

- **Dataclass for actions**: Clean, immutable action representation
- **Persistent state**: Survives crashes via JSON file
- **Reverse execution**: Undoes changes in correct order
- **Multiple action types**: Commands, files, packages, services
- **Dry-run support**: Preview rollback without executing

### Key Principles Demonstrated

1. **Command Pattern** — Encapsulates actions as objects
2. **Memento Pattern** — Saves state for later restoration
3. **Transactional Integrity** — All-or-nothing operations

### Representative Code Snippet

```python
@dataclass
class RollbackAction:
    """A single action that can be rolled back."""
    action_type: str  # "command", "file_restore", "package_remove", "service_stop"
    description: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "action_type": self.action_type,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class RollbackManager:
    """Manages rollback of installation changes."""

    def add_package_remove(self, packages: List[str], description: str = "") -> None:
        """Add packages to be removed during rollback."""
        action = RollbackAction(
            action_type="package_remove",
            description=description or f"Remove packages: {', '.join(packages)}",
            data={"packages": packages},
        )
        self.actions.append(action)
        self._save_state()  # Persist immediately for crash recovery

    def rollback(self, dry_run: bool = False) -> bool:
        """Execute rollback actions in reverse order."""
        for action in reversed(self.actions):
            self.logger.info(f"  • {action.description}")
            if not dry_run:
                self._execute_action(action)
        return True
```

---

## 7. Configuration Management

**File:** [config.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/config.py)
**Category:** Core Component | Pattern Type: Configuration Object
**Lines:** 511

### Why This Is Exemplary

- **Layered configuration**: Defaults → Profile → User → CLI
- **Deep merge**: Proper nested dictionary merging
- **Dot notation access**: `config.get("system.hostname")`
- **Profile system**: Built-in presets for different use cases
- **Pydantic validation**: Schema-based validation with helpful errors

### Key Principles Demonstrated

1. **Configuration Layering** — Multiple sources with clear precedence
2. **Fail-Fast Validation** — Catches errors early with helpful messages
3. **Immutable Defaults** — Uses deep copy to prevent mutation

### Representative Code Snippet

```python
class ConfigManager:
    """Manages configuration loading and access."""

    DEFAULTS: Dict[str, Any] = {
        "system": {
            "hostname": "dev-workstation",
            "timezone": "UTC",
        },
        "security": {
            "enabled": True,  # Cannot be disabled
        },
        # ... more defaults
    }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = self._deep_copy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = self._deep_copy(value)
        return result
```

---

## 8. Input Validation

**File:** [input_validator.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/security/input_validator.py)
**Category:** Security | Pattern Type: Validation
**Lines:** 527

### Why This Is Exemplary

- **Comprehensive coverage**: Usernames, paths, commands, emails, IPs, domains
- **Configurable strictness**: Strict mode raises exceptions, non-strict returns False
- **Sanitization methods**: Clean input in addition to validation
- **Security-focused**: Blocks injection attacks, path traversal
- **Convenience functions**: Quick validation without manager instance

### Key Principles Demonstrated

1. **Defense in Depth** — Multiple validation layers
2. **Whitelist over Blacklist** — Allows known-good patterns
3. **Logging Security Events** — Tracks validation failures

### Representative Code Snippet

```python
class InputValidator:
    """Centralized input validation and sanitization."""

    DANGEROUS_CHARS = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]

    def validate_username(self, username: str) -> bool:
        """Validate username format."""
        if not self.username_pattern.match(username):
            return self._handle_failure(
                f"Invalid username format: {username}\n"
                f"Must match pattern: {self.username_pattern.pattern}"
            )
        return True

    def validate_path(self, path: Union[str, Path], must_exist: bool = False) -> bool:
        """Validate file path for safety."""
        path = Path(path)

        # Check for path traversal
        if ".." in str(path):
            return self._handle_failure(f"Path traversal detected: {path}")

        # Check for dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in str(path):
                return self._handle_failure(f"Dangerous character in path: {char}")

        return True

    def escape_shell_arg(self, arg: str) -> str:
        """Escape argument for safe shell execution."""
        return shlex.quote(arg)
```

---

## 9. Feature Module Implementation

**File:** [docker.py](file:///home/racoon/Desktop/debian-vps-workstation/configurator/modules/docker.py)
**Category:** Feature Module | Pattern Type: Module Implementation
**Lines:** 268

### Why This Is Exemplary

- **Clear structure**: validate → configure → verify lifecycle
- **Modular steps**: Private methods for each installation step
- **Security verification**: GPG key fingerprint validation
- **Resilient installation**: Uses `install_packages_resilient`
- **Proper logging**: User-visible progress with checkmarks

### Key Principles Demonstrated

1. **Single Responsibility** — Each method does one thing
2. **Supply Chain Security** — Verifies package sources
3. **User Feedback** — Clear progress messages

### Representative Code Snippet

```python
class DockerModule(ConfigurationModule):
    """Docker installation module."""

    name = "Docker"
    description = "Docker Engine and Docker Compose"
    depends_on = ["system", "security"]
    priority = 50

    def configure(self) -> bool:
        """Install and configure Docker."""
        self.logger.info("Installing Docker...")

        # Step-by-step installation
        self._add_docker_repository()
        self._install_docker()
        self._configure_daemon()
        self._configure_permissions()
        self._start_services()
        self._verify_docker()

        self.logger.info("✓ Docker installed and configured")
        return True

    def _add_docker_repository(self):
        """Add Docker's official GPG key and repository with verification."""
        validator = SupplyChainValidator(self.config, self.logger)

        # Verify fingerprint for security
        if expected_fingerprint and not self.dry_run:
            validator.verify_apt_key_fingerprint(
                "/etc/apt/keyrings/docker.asc",
                expected_fingerprint,
                is_local_file=True,
            )
            self.logger.info("✓ Docker GPG key fingerprint verified")
```

---

## 10. Test Fixtures

**File:** [conftest.py](file:///home/racoon/Desktop/debian-vps-workstation/tests/conftest.py)
**Category:** Testing | Pattern Type: Fixtures
**Lines:** 145

### Why This Is Exemplary

- **Autouse fixture**: Automatically restores dependency registry
- **Minimal mocks**: Just enough to isolate tests
- **Reusable fixtures**: Common patterns for all tests
- **Safety**: Prevents actual shell commands during tests

### Key Principles Demonstrated

1. **Test Isolation** — Each test starts with clean state
2. **DRY Testing** — Shared fixtures prevent duplication
3. **Mock Boundaries** — Mock at edges, not internals

### Representative Code Snippet

```python
@pytest.fixture(autouse=True)
def restore_dependency_registry():
    """Restore default dependencies after tests that clear the registry."""
    yield  # Let the test run

    # After test: ensure defaults are restored
    from configurator.dependencies.registry import DependencyRegistry, ModuleDependencyInfo

    if len(DependencyRegistry.get_all()) < 5:
        defaults = [
            ModuleDependencyInfo("system", priority=10),
            ModuleDependencyInfo("security", depends_on=["system"], priority=20),
            # ... more defaults
        ]
        for dep in defaults:
            DependencyRegistry.register(dep)


@pytest.fixture
def mock_run_command(monkeypatch):
    """Mock the run_command function to avoid actual shell commands."""
    from configurator.utils.command import CommandResult

    def mock_run(command, **kwargs):
        return CommandResult(
            command=command if isinstance(command, str) else " ".join(command),
            return_code=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr("configurator.utils.command.run_command", mock_run)
    return mock_run
```

---

## 11. Integration Tests

**File:** [test_rollback.py](file:///home/racoon/Desktop/debian-vps-workstation/tests/integration/test_rollback.py)
**Category:** Testing | Pattern Type: Integration Test
**Lines:** 148

### Why This Is Exemplary

- **Clear test names**: Describe expected behavior
- **Proper setup**: Uses `tmp_path` for isolation
- **State verification**: Checks both actions and persistence
- **Edge cases**: Tests empty rollback, dry-run mode
- **Test class organization**: Groups related tests

### Key Principles Demonstrated

1. **Arrange-Act-Assert** — Clear test structure
2. **Test Isolation** — Each test independent
3. **Meaningful Assertions** — Tests what matters

### Representative Code Snippet

```python
@pytest.mark.integration
class TestRollbackManager:
    """Tests for RollbackManager."""

    def test_add_and_execute_command_rollback(self, tmp_path):
        """Test adding and executing command rollback."""
        state_file = tmp_path / "rollback-state.json"

        rollback = RollbackManager()
        rollback.state_file = state_file

        rollback.add_command(
            "echo 'rolled back'",
            description="Test rollback",
        )

        assert len(rollback.actions) == 1
        assert state_file.exists()  # State should be saved

        # Load state in new manager
        rollback2 = RollbackManager()
        rollback2.state_file = state_file
        rollback2.load_state()

        assert len(rollback2.actions) == 1
        assert rollback2.actions[0].description == "Test rollback"

    def test_dry_run_rollback(self, tmp_path):
        """Test dry-run rollback doesn't execute."""
        output_file = tmp_path / "output.txt"

        rollback = RollbackManager()
        rollback.add_command(f"echo 'test' > {output_file}")

        rollback.rollback(dry_run=True)

        assert not output_file.exists()  # File should not exist
```

---

## Conclusion

### Maintaining Code Quality

To maintain consistency with these exemplars:

1. **Use the base class** — All modules should inherit from `ConfigurationModule`
2. **Inject dependencies** — Accept optional dependencies via constructor
3. **Handle errors gracefully** — Use custom exceptions with WHAT/WHY/HOW
4. **Add rollback actions** — Register undo operations for all state changes
5. **Write tests** — At least unit tests for new functionality
6. **Document clearly** — Module docstrings and method documentation

### Anti-Patterns to Avoid

| Anti-Pattern            | Instead Do                        |
| ----------------------- | --------------------------------- |
| Importing other modules | Use shared state or orchestration |
| Bare `except:` clauses  | Catch specific exceptions         |
| Hardcoded values        | Use configuration                 |
| Direct system calls     | Use `self.run()` with rollback    |
| Global mutable state    | Use dependency injection          |

### Adding New Exemplars

When adding new exemplars to this document:

1. Verify the file demonstrates best practices
2. Include actual file path and line count
3. Explain why it's exemplary
4. Show a representative code snippet
5. List the key principles demonstrated

---

_This document should be updated when new exemplary patterns emerge in the codebase._
