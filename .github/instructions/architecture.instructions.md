---
description: "Comprehensive architectural guidelines for Debian VPS Configurator v2.0 - Modular Plugin-Based Layered Architecture"
applyTo: "**/*.py"
---

# Debian VPS Configurator Architecture Instructions

## Overview

The Debian VPS Configurator implements a **Modular Plugin-Based Layered Architecture** with four distinct layers designed for extensibility, testability, parallel execution, and resilience. These instructions guide GitHub Copilot to generate code that adheres to our architectural principles and patterns.

---

## Core Architectural Principles

When generating code for this project, ALWAYS follow these principles:

### 1. Separation of Concerns

- Each layer has distinct responsibilities with well-defined interfaces
- Higher layers may import from lower layers, but NEVER the reverse
- Components should have a single, well-defined responsibility

### 2. Dependency Inversion

- High-level modules depend on abstractions, not concrete implementations
- Use constructor injection for all dependencies
- Provide optional dependencies with sensible defaults

### 3. Fail-Safe Defaults

- Security must be enabled by default
- Dangerous operations require explicit opt-in
- All state-changing operations MUST register rollback actions BEFORE execution

### 4. Thread Safety

- All APT operations MUST use the class-level `_APT_LOCK`
- Shared resources must be protected by appropriate locks
- Use ThreadPoolExecutor for parallelism, NOT async/await

---

## Four-Layer Architecture

```
┌─────────────────────────────────────────┐
│ PRESENTATION: cli.py, wizard.py        │  ← User interaction
├─────────────────────────────────────────┤
│ ORCHESTRATION: core/installer.py        │  ← Coordination
├─────────────────────────────────────────┤
│ FEATURE: modules/*.py                   │  ← Business logic
├─────────────────────────────────────────┤
│ FOUNDATION: utils/, security/           │  ← Shared utilities
└─────────────────────────────────────────┘
```

### Layer 1: Presentation Layer

**Location:** `configurator/cli.py`, `configurator/wizard.py`, `configurator/ui/`

**Responsibilities:**

- User interface (CLI commands, TUI dashboard, setup wizard)
- Input validation and sanitization
- Output formatting with Rich console
- Audit logging for security-sensitive operations

**Import Rules:**

- ✅ May import: Orchestration layer, Foundation layer
- ❌ May NOT import: Feature layer directly (use Installer/Container)

**Example:**

```python
@main.command()
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.pass_context
def install(ctx: click.Context, dry_run: bool):
    """Install configured modules."""
    installer = ctx.obj["container"].get("installer")
    success = installer.install(dry_run=dry_run)

    if success:
        console.print("[green]✓ Installation complete[/green]")
    else:
        console.print("[red]✗ Installation failed[/red]")
        sys.exit(1)
```

### Layer 2: Orchestration Layer

**Location:** `configurator/core/`

**Components:**

- `installer.py` - Module orchestration and execution coordination
- `container.py` - Dependency injection container
- `rollback.py` - Transaction-like rollback capabilities
- `execution/parallel.py` - Concurrent module execution

**Responsibilities:**

- Service registration and resolution
- Module discovery and dependency ordering
- Execution coordination (sequential, parallel, hybrid)
- Rollback coordination

**Import Rules:**

- ✅ May import: Feature layer, Foundation layer
- ❌ May NOT import: Presentation layer

**Example:**

```python
class Installer:
    def __init__(
        self,
        config: ConfigManager,
        logger: Optional[logging.Logger] = None,
        reporter: Optional[ReporterInterface] = None,
        container: Optional[Container] = None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.reporter = reporter or DEFAULT_REPORTER()
        self.container = container or Container()

    def install(self, skip_validation: bool = False, dry_run: bool = False) -> bool:
        """Orchestrate module installation."""
        # Register services, discover modules, execute in order
        pass
```

### Layer 3: Feature Layer (Modules)

**Location:** `configurator/modules/`

**All modules MUST:**

1. Inherit from `ConfigurationModule` abstract base class
2. Implement `validate()`, `configure()`, `verify()` methods
3. Define `name`, `description`, `priority` class attributes
4. Register rollback actions BEFORE making state changes

**Critical Rules:**

- ✅ May import: Foundation layer only
- ❌ May NOT import: Other modules (ensures plugin isolation)
- ❌ May NOT import: Orchestration or Presentation layers

**Module Template:**

```python
from configurator.modules.base import ConfigurationModule
from configurator.core.rollback import RollbackManager
from typing import Any, Dict, Optional
import logging

class MyFeatureModule(ConfigurationModule):
    """Configure [feature description]."""

    name = "myfeature"
    description = "Install and configure [feature]"
    priority = 50  # Lower = earlier execution

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        rollback_manager: Optional[RollbackManager] = None,
    ):
        super().__init__(config, logger, rollback_manager)

    def validate(self) -> bool:
        """Check prerequisites before installation."""
        # Check OS compatibility, disk space, network, etc.
        return True

    def configure(self) -> bool:
        """Install and configure the feature."""
        packages = ["package1", "package2"]

        # CRITICAL: Register rollback BEFORE installation
        self.rollback_manager.add_package_remove(packages, "Remove MyFeature packages")

        # Install packages with resilience (circuit breaker, retry)
        if not self.install_packages_resilient(packages):
            return False

        # Configure with rollback registration
        self.run(
            "systemctl enable myservice",
            rollback_command="systemctl disable myservice"
        )

        return True

    def verify(self) -> bool:
        """Verify installation succeeded."""
        if not self.is_service_active("myservice"):
            self.logger.warning("Service myservice not running")
            return False
        return True
```

**Module Priority Guidelines:**

- 10: System fundamentals (hostname, timezone, packages)
- 20: Security hardening (UFW, Fail2ban, SSH)
- 25: RBAC and access control
- 30: Desktop environment, network services
- 40: Version control, Docker
- 50: Programming languages, databases
- 60: Desktop applications (VSCode, Cursor)
- 90: Monitoring and observability

### Layer 4: Foundation Layer

**Location:** `configurator/utils/`, `configurator/security/`, `configurator/rbac/`

**Components:**

- `command.py` - Shell command execution
- `file.py` - File operations
- `network.py` - Network connectivity checks
- `retry.py` - Exponential backoff retry
- `circuit_breaker.py` - Circuit breaker pattern
- Security utilities (SSH, MFA, SSL)
- RBAC system

**Responsibilities:**

- Pure utility functions with no business logic
- Cross-cutting concerns implementation
- Shared infrastructure

**Import Rules:**

- ❌ May NOT import: Any higher layers

**Example:**

```python
def run_command(
    command: str,
    check: bool = True,
    timeout: int = 300,
    capture_output: bool = True,
) -> CommandResult:
    """Execute shell command with timeout and capture."""
    result = subprocess.run(
        command,
        shell=True,
        check=check,
        timeout=timeout,
        capture_output=capture_output,
        text=True,
    )
    return CommandResult(
        command=command,
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
```

---

## Critical Architectural Constraints

### 🚨 Constraint 1: Module Isolation

**NEVER import other modules from within a module:**

```python
# ❌ INCORRECT: Module importing another module
from configurator.modules.docker import DockerModule  # FORBIDDEN

# ✅ CORRECT: Module imports foundation utilities only
from configurator.utils.command import run_command
from configurator.core.rollback import RollbackManager
```

**Why:** This ensures plugin isolation and prevents circular dependencies.

### 🚨 Constraint 2: Rollback Before Action

**ALWAYS register rollback actions BEFORE making state changes:**

```python
# ❌ INCORRECT: Rollback registered after change
self.install_packages(packages)
self.rollback_manager.add_package_remove(packages)  # Too late if install fails

# ✅ CORRECT: Rollback registered before change
self.rollback_manager.add_package_remove(packages, "Remove on failure")
self.install_packages(packages)
```

### 🚨 Constraint 3: ThreadPoolExecutor, NOT async/await

**Use ThreadPoolExecutor for concurrency:**

```python
# ❌ INCORRECT: Using async/await
async def configure(self) -> bool:
    await self.install_packages(packages)

# ✅ CORRECT: Using ThreadPoolExecutor
class ParallelExecutor:
    def execute(self, contexts: List[ExecutionContext]) -> Dict[str, ExecutionResult]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._execute_module, ctx): ctx for ctx in contexts}
            for future in as_completed(futures):
                yield future.result()
```

**Why:** Many operations are blocking system calls incompatible with async/await.

### 🚨 Constraint 4: APT Lock Protection

**All APT operations MUST use the class-level lock:**

```python
class ConfigurationModule(ABC):
    _APT_LOCK = threading.Lock()  # Class-level lock

    def install_packages(self, packages: List[str]) -> bool:
        with self._APT_LOCK:  # Serialize APT operations
            return self._do_install(packages)
```

**Why:** Prevents concurrent APT operations that can corrupt package database.

---

## Dependency Injection Pattern

### Container Registration

```python
# Singleton services (shared instance, lazy loaded)
container.singleton("config", lambda: ConfigManager())
container.singleton("logger", lambda: logging.getLogger("configurator"))
container.singleton("rollback_manager", lambda: RollbackManager())

# Factory services (new instance per request)
container.factory("docker_module", lambda c: DockerModule(
    config=c.get("config").get("docker", {}),
    logger=c.get("logger"),
    rollback_manager=c.get("rollback_manager"),
))
```

### Module Constructor Pattern

```python
class DockerModule(ConfigurationModule):
    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        rollback_manager: Optional[RollbackManager] = None,
        dry_run_manager: Optional[DryRunManager] = None,
        circuit_breaker_manager: Optional[CircuitBreakerManager] = None,
        package_cache_manager: Optional[PackageCacheManager] = None,
    ):
        """Accept optional dependencies with sensible defaults."""
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.rollback_manager = rollback_manager or RollbackManager()
        self.dry_run_manager = dry_run_manager or DryRunManager()
        self.circuit_breaker_manager = circuit_breaker_manager or CircuitBreakerManager()
        self.package_cache_manager = package_cache_manager or PackageCacheManager()
```

---

## Error Handling Patterns

### Custom Exception Hierarchy

```python
class ConfiguratorError(Exception):
    """Base exception with WHAT/WHY/HOW format."""
    def __init__(self, what: str, why: str, how: str, docs_link: str = None):
        self.what = what
        self.why = why
        self.how = how
        self.docs_link = docs_link
        message = f"{what}\n\nWhy: {why}\n\nHow to fix: {how}"
        if docs_link:
            message += f"\n\nDocumentation: {docs_link}"
        super().__init__(message)

class PrerequisiteError(ConfiguratorError): pass
class ConfigurationError(ConfiguratorError): pass
class ModuleExecutionError(ConfiguratorError): pass
class ValidationError(ConfiguratorError): pass
class RollbackError(ConfiguratorError): pass
```

### Exception Usage

```python
# ✅ CORRECT: User-friendly exception with context
raise ConfiguratorError(
    what="Docker installation failed",
    why="APT repository not accessible",
    how="Check network connectivity and try again",
    docs_link="https://docs.example.com/docker-setup"
)

# ❌ INCORRECT: Generic exception
raise Exception("Docker failed")  # Don't do this
```

### Circuit Breaker Pattern

```python
from configurator.utils.circuit_breaker import CircuitBreakerManager

class DockerModule(ConfigurationModule):
    def configure(self) -> bool:
        breaker = self.circuit_breaker_manager.get_breaker("docker-hub")

        try:
            result = breaker.call(
                lambda: self.run("docker pull nginx:latest")
            )
        except CircuitBreakerError as e:
            self.logger.warning(f"Docker Hub unavailable: {e}")
            # Graceful degradation
            return self._use_cached_image("nginx")

        return True
```

---

## Data Architecture Patterns

### Configuration Management

```python
# Configuration hierarchy (merged in order):
# 1. config/default.yaml (base defaults)
# 2. config/profiles/{profile}.yaml (profile overrides)
# 3. CLI arguments (runtime overrides)

class ConfigManager:
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def is_module_enabled(self, name: str) -> bool:
        """Check if module is enabled in configuration."""
        return self.get(f"{name}.enabled", False)
```

### State Persistence

```python
class RollbackManager:
    """Persists rollback state for crash recovery."""

    state_file = Path("/var/lib/debian-vps-configurator/rollback-state.json")

    def _save_state(self) -> None:
        """Save rollback state to disk."""
        state = {
            "actions": [a.to_dict() for a in self.actions],
            "saved_at": datetime.now().isoformat(),
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """Load rollback state from disk."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                state = json.load(f)
            self.actions = [RollbackAction.from_dict(a) for a in state["actions"]]
            return True
        return False
```

### Dataclass Pattern

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

@dataclass
class RollbackAction:
    """Immutable value object for rollback actions."""
    action_type: str  # "command", "file_restore", "package_remove", "service_stop"
    description: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
```

---

## Testing Patterns

### Test Organization

```
tests/
├── unit/           # Fast, isolated tests (~350 tests)
├── integration/    # Component interaction tests (~50 tests)
├── e2e/           # End-to-end workflows (~10 tests)
├── security/      # Security validation tests
├── performance/   # Performance benchmarks
└── validation/    # System validation (400+ checks)
```

### Fixture-Based Testing

```python
import pytest
from unittest.mock import MagicMock
from configurator.core.container import Container
from configurator.core.rollback import RollbackManager

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create minimal test configuration."""
    return {
        "system": {"hostname": "test-workstation"},
        "security": {"enabled": True},
        "interactive": False,
    }

@pytest.fixture
def mock_run_command(monkeypatch):
    """Mock shell commands for isolated testing."""
    def mock_run(command, **kwargs):
        return CommandResult(
            command=command,
            return_code=0,
            stdout="",
            stderr=""
        )
    monkeypatch.setattr("configurator.utils.command.run_command", mock_run)
    return mock_run

def test_module_with_mocks(mock_config, mock_run_command):
    """Test module with mocked dependencies."""
    container = Container()
    container.mock("rollback_manager", MagicMock(spec=RollbackManager))

    module = MyFeatureModule(config=mock_config)
    assert module.configure()
```

---

## Common Patterns and Examples

### Lazy Loading Pattern

```python
class LazyLoader:
    """Proxy object for deferred imports (fast CLI startup)."""

    def __init__(self, module_name: str, import_object: str = None):
        self._module_name = module_name
        self._import_object = import_object
        self._module = None

    def _load(self):
        if self._module is None:
            self._module = __import__(self._module_name, fromlist=[self._import_object])
            if self._import_object:
                self._module = getattr(self._module, self._import_object)
        return self._module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

# Usage in CLI
RBACManager = LazyLoader("configurator.rbac.rbac_manager", "RBACManager")
```

### Retry with Exponential Backoff

```python
from configurator.utils.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, initial_delay=1, backoff_factor=2)
def install_package(package: str) -> bool:
    """Install package with automatic retry."""
    result = run_command(f"apt-get install -y {package}")
    return result.return_code == 0
```

### Input Validation

```python
from configurator.security.input_validator import InputValidator

validator = InputValidator()

# Validate username (pattern: ^[a-z][a-z0-9_-]{2,31}$)
if not validator.validate_username(username):
    raise ValidationError(
        what=f"Invalid username: {username}",
        why="Username must start with lowercase letter",
        how="Use only lowercase letters, numbers, hyphens, underscores"
    )

# Sanitize command to prevent injection
safe_command = validator.sanitize_command(user_input)
```

---

## Module Development Checklist

When creating a new module, ensure:

- [ ] Inherits from `ConfigurationModule`
- [ ] Implements `validate()`, `configure()`, `verify()`
- [ ] Defines `name`, `description`, `priority` attributes
- [ ] Uses constructor injection with optional dependencies
- [ ] Registers rollback actions BEFORE state changes
- [ ] Uses `_APT_LOCK` for APT operations
- [ ] Only imports from Foundation layer
- [ ] Includes comprehensive docstrings
- [ ] Has unit tests in `tests/unit/`
- [ ] Registered in dependency graph
- [ ] Configuration section added to `config/default.yaml`

---

## Architecture Violations to Avoid

### ❌ DON'T: Import other modules

```python
# BAD: Creates tight coupling
from configurator.modules.docker import DockerModule
```

### ❌ DON'T: Use async/await

```python
# BAD: Incompatible with blocking syscalls
async def configure(self) -> bool:
    await self.install_packages(packages)
```

### ❌ DON'T: Skip rollback registration

```python
# BAD: No way to undo on failure
self.run("apt-get install nginx")
```

### ❌ DON'T: Use bare except clauses

```python
# BAD: Catches all exceptions including KeyboardInterrupt
try:
    result = risky_operation()
except:  # Never use bare except
    pass
```

### ❌ DON'T: Create dependencies without injection

```python
# BAD: Hard dependency, not testable
self.rollback_manager = RollbackManager()

# GOOD: Injected dependency
def __init__(self, rollback_manager: Optional[RollbackManager] = None):
    self.rollback_manager = rollback_manager or RollbackManager()
```

---

## State File Locations

When persisting state, use these standard locations:

| Type           | Path                                                    |
| -------------- | ------------------------------------------------------- |
| Rollback State | `/var/lib/debian-vps-configurator/rollback-state.json`  |
| User Registry  | `/var/lib/debian-vps-configurator/users/registry.json`  |
| Activity DB    | `/var/lib/debian-vps-configurator/activity/activity.db` |
| Package Cache  | `/var/cache/debian-vps-configurator/packages/`          |
| Config         | `/etc/debian-vps-configurator/`                         |

---

## Technology Stack

| Category      | Technology | Version | Notes                      |
| ------------- | ---------- | ------- | -------------------------- |
| Language      | Python     | 3.11+   | Use 3.11+ features         |
| CLI Framework | Click      | ^8.1.7  | With Rich integration      |
| TUI Framework | Textual    | ^0.40.0 | For dashboard              |
| Validation    | Pydantic   | ^2.12.0 | Configuration validation   |
| Testing       | pytest     | ^8.3.4  | With coverage requirements |
| Linting       | Ruff       | Latest  | Import order enforcement   |
| Type Checking | mypy       | Latest  | Strict mode enabled        |

---

## Summary

When generating code for Debian VPS Configurator:

1. **Respect the four-layer architecture** - imports only flow downward
2. **Use dependency injection** - all dependencies through constructor
3. **Register rollback before actions** - ensure transactional integrity
4. **Use ThreadPoolExecutor** - not async/await for concurrency
5. **Protect APT operations** - use `_APT_LOCK` class-level lock
6. **Isolate modules** - never import other modules
7. **Handle errors properly** - use custom exception hierarchy
8. **Test comprehensively** - unit, integration, and E2E tests
9. **Document thoroughly** - docstrings for all public APIs
10. **Follow Python 3.11+ standards** - modern type hints and patterns

This architecture enables extensibility, testability, parallel execution, and resilience - the core goals of the Debian VPS Configurator project.

---

_Generated from architecture.md on 2026-01-17_
