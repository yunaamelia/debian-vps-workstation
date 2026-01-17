---
applyTo: "**/*.py"
---

# Technology Stack Instructions

> Version-agnostic guidelines for consistent technology usage across the codebase.

---

## Technology Stack Overview

### Architecture Layers

| Layer             | Role                                    | Technologies                               |
| ----------------- | --------------------------------------- | ------------------------------------------ |
| **Presentation**  | User interaction (CLI, TUI, output)     | CLI framework, TUI framework, Rich console |
| **Orchestration** | Coordination, DI, state management      | Installer, Container, Managers             |
| **Feature**       | Business logic modules                  | ConfigurationModule implementations        |
| **Foundation**    | Core utilities, security, configuration | Config parsers, cryptography, system utils |

### Technology Roles

| Technology Category   | Role in Architecture                                  |
| --------------------- | ----------------------------------------------------- |
| **CLI Framework**     | Parse commands, options, arguments; route to handlers |
| **TUI Framework**     | Interactive terminal wizard interface                 |
| **Console Output**    | Formatted output, tables, progress indicators         |
| **Configuration**     | Parse YAML/TOML config, validate against schema       |
| **Validation**        | Type coercion, constraint checking, error messages    |
| **Cryptography**      | Secrets encryption, password hashing, key management  |
| **SSH**               | Remote command execution, file transfer               |
| **Graph Library**     | Dependency resolution, execution ordering             |
| **System Monitoring** | Resource usage, process information                   |

---

## Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│            CLI Commands | TUI Wizard | Console Output        │
├─────────────────────────────────────────────────────────────┤
│                   ORCHESTRATION LAYER                        │
│         Installer | DI Container | Rollback Manager          │
├─────────────────────────────────────────────────────────────┤
│                      FEATURE LAYER                           │
│               Configuration Modules (21+)                    │
├─────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                          │
│        Config Parsing | Security | Utilities | Graph         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Pattern

```
User Input → CLI → ConfigManager → Installer
                         ↓
                    Validator ─────────────→ Exit if failed
                         ↓
                    Module.validate()
                         ↓
                    Module.configure() ←──── RollbackManager
                         ↓                        ↑
                    Module.verify() ─────────→ Rollback if failed
                         ↓
                    Success Report
```

### Integration Principles

1. **Layers communicate downward only** — upper layers depend on lower layers, never reverse
2. **Dependencies flow inward** — presentation depends on orchestration, not vice versa
3. **Services are injected** — use dependency injection for cross-cutting concerns
4. **State changes are atomic** — register rollback before any modification

---

## Usage Guidelines per Technology

### CLI Framework

**Role**: Command-line interface definition and argument parsing

**Patterns**:

- Use decorators for command definition
- Group related commands under subcommands
- Provide short (`-v`) and long (`--verbose`) option forms
- Include help text for all options and commands
- Use callbacks for option validation

**Conventions**:

```python
# Command pattern
@cli.command("action-name")
@option("--flag", "-f", is_flag=True, help="Description")
@option("--value", "-v", type=str, default="default", help="Description")
def action_name(flag: bool, value: str) -> None:
    """Command description for help text."""
    # Implementation
```

**Principles**:

- Commands are kebab-case: `check-system`, `install-all`
- Options are kebab-case: `--dry-run`, `--skip-validation`
- Exit with code 0 on success, non-zero on failure
- Always catch domain exceptions at CLI boundary

---

### Configuration Framework

**Role**: Load, parse, and validate configuration files

**Patterns**:

- Use dot notation for nested access: `config.get("system.hostname")`
- Provide sensible defaults for all optional values
- Validate configuration on load, not on access
- Support multiple configuration sources with precedence

**Conventions**:

```python
# Configuration access pattern
class ConfigManager:
    def get(self, key: str, default: Any = None) -> Any:
        """Get value using dot notation."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
```

**Principles**:

- Configuration is immutable after load
- Environment variables override file configuration
- Secrets never appear in configuration files
- Schema validation produces actionable error messages

---

### Validation Framework

**Role**: Type validation, constraint checking, schema enforcement

**Patterns**:

- Define schemas as declarative models
- Return structured error objects, not exceptions for validation failures
- Support strict mode (fail fast) and lenient mode (collect all errors)
- Produce human-readable error messages

**Conventions**:

```python
# Validation result pattern
@dataclass
class ValidationResult:
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
```

**Principles**:

- Validate at API boundaries, not deep in business logic
- Coerce types when safe, reject when ambiguous
- Error messages include: what failed, why, and how to fix

---

### Console Output Framework

**Role**: Formatted terminal output, tables, progress indicators

**Patterns**:

- Use semantic colors: green for success, red for errors, yellow for warnings
- Provide progress bars for long-running operations
- Support both human-readable and machine-readable (JSON) output
- Use status indicators: `✓` success, `✗` failure, `•` info

**Conventions**:

```python
# Output pattern
console.print("[green]✓ Operation succeeded[/green]")
console.print("[red]✗ Operation failed[/red]")
console.print("[yellow]⚠ Warning message[/yellow]")
```

**Principles**:

- Output respects terminal width
- Colors degrade gracefully when terminal doesn't support them
- JSON output is always valid, parseable JSON
- Progress updates don't overwhelm the terminal

---

### Cryptography Framework

**Role**: Encryption, decryption, password hashing, key management

**Patterns**:

- Use high-level APIs, never raw primitives
- Derive keys from passwords using approved KDFs
- Store encrypted data with algorithm metadata for future compatibility
- Use constant-time comparison for secrets

**Principles**:

- Never store plaintext secrets
- Never roll your own crypto—use established libraries
- Keys are derived, not stored directly
- Encrypt then MAC (or use authenticated encryption)
- Secrets have minimum complexity requirements

---

### Dependency Injection

**Role**: Manage service lifecycles and dependencies

**Patterns**:

- Register services with factories, not instances
- Support singleton and transient lifetimes
- Allow mocking for tests without modifying production code
- Resolve dependencies lazily

**Conventions**:

```python
# DI pattern
class Service:
    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[Logger] = None,
        dependency: Optional[Dependency] = None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.dependency = dependency or DefaultDependency()
```

**Principles**:

- Accept optional dependencies with sensible defaults
- Dependencies are interfaces, not implementations
- Constructor injection is preferred over setter injection
- Circular dependencies indicate design problems

---

### Graph Library

**Role**: Dependency resolution, execution ordering

**Patterns**:

- Build dependency graph from module metadata
- Detect cycles before execution
- Compute execution batches for parallelization
- Provide topological ordering

**Principles**:

- Graph construction is separate from graph traversal
- Cycles are always errors, never silently ignored
- Dependencies are declared, not inferred
- Execution batches maximize parallelism within constraints

---

## Code Organization

### Directory Structure

```
project/
├── cli.py                    # CLI entry points
├── config.py                 # Configuration management
├── exceptions.py             # Custom exceptions
├── core/
│   ├── installer.py          # Orchestration
│   ├── container.py          # Dependency injection
│   ├── rollback.py           # State rollback
│   └── execution/            # Execution strategies
├── modules/
│   ├── base.py               # Abstract base class
│   └── <feature>.py          # One file per feature module
├── validators/
│   ├── base.py               # Base validator
│   ├── orchestrator.py       # Validator coordination
│   └── tier<N>_<level>/      # Validators by priority
└── utils/
    ├── command.py            # Shell command execution
    └── <utility>.py          # One file per utility category
```

### File Placement Rules

| Component Type | Location               | Naming Pattern          |
| -------------- | ---------------------- | ----------------------- |
| CLI commands   | `cli.py`               | Function per command    |
| Feature module | `modules/<feature>.py` | `<Feature>Module` class |
| Validator      | `validators/tier<N>/`  | `<Check>Validator`      |
| Manager        | `core/<resource>.py`   | `<Resource>Manager`     |
| Utility        | `utils/<category>.py`  | Utility functions       |
| Exception      | `exceptions.py`        | `<Type>Error` class     |

---

## Common Patterns

### Error Handling Pattern

```python
# Exception with context
class DomainError(Exception):
    def __init__(self, what: str, why: str = "", how: str = ""):
        self.what = what  # What happened
        self.why = why    # Why it happened
        self.how = how    # How to fix it
        super().__init__(f"{what}: {why}. {how}")

# Usage
raise DomainError(
    what="Configuration file not found",
    why="The specified path does not exist",
    how="Check the path and try again"
)
```

### Logging Pattern

```python
# Logger per class
class Service:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def operation(self):
        self.logger.info("Operation starting...")
        self.logger.debug("Details: %s", details)
        self.logger.error("Failed: %s", error)
```

### Retry Pattern

```python
# Decorator for retries with backoff
@retry(max_retries=3, base_delay=1.0, backoff_factor=2.0)
def unreliable_operation():
    # Operation that may fail transiently
    pass
```

### Circuit Breaker Pattern

```python
# State machine for failure isolation
class CircuitBreaker:
    # States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)

    def call(self, func, *args, **kwargs):
        if self.is_open() and not self.should_attempt_reset():
            raise CircuitBreakerError("Circuit is open")
        # Execute function, track success/failure
```

### Template Method Pattern

```python
# Base class with lifecycle hooks
class ConfigurationModule(ABC):
    @abstractmethod
    def validate(self) -> bool:
        """Check prerequisites (no side effects)."""

    @abstractmethod
    def configure(self) -> bool:
        """Apply changes (register rollback first)."""

    @abstractmethod
    def verify(self) -> bool:
        """Confirm success (independent check)."""
```

---

## Integration Rules

### Cross-Layer Communication

| From Layer    | To Layer      | Allowed Methods           |
| ------------- | ------------- | ------------------------- |
| Presentation  | Orchestration | Direct method calls       |
| Orchestration | Feature       | Interface-based calls     |
| Orchestration | Foundation    | Utility function calls    |
| Feature       | Foundation    | Direct utility calls      |
| Foundation    | Foundation    | Direct calls within layer |

### Forbidden Patterns

- **No upward dependencies**: Foundation must not import from Feature
- **No cross-feature imports**: Modules must not import from each other
- **No circular imports**: Use interfaces or deferred imports
- **No presentation in business logic**: No Rich/Click in modules

### Event Communication

- Use observers/hooks for cross-cutting concerns
- Events are fire-and-forget, not request-response
- Event handlers must be idempotent
- Failed handlers don't break the main flow

---

## Constraints and Principles

### Unchanging Rules

1. **All modules implement validate → configure → verify lifecycle**
2. **All state changes register rollback actions first**
3. **All CLI commands handle exceptions at the boundary**
4. **All configuration is validated before use**
5. **All secrets are encrypted at rest**
6. **All destructive operations support dry-run mode**

### Code Style Principles

| Principle           | Application                                        |
| ------------------- | -------------------------------------------------- |
| Type everything     | All functions have type hints                      |
| Document interfaces | Public APIs have docstrings                        |
| Prefer composition  | Inject dependencies, don't inherit implementation  |
| Fail explicitly     | Raise exceptions with context, not silent failures |
| One responsibility  | Each class/function does one thing well            |

### Naming Conventions

| Element         | Convention         | Example              |
| --------------- | ------------------ | -------------------- |
| Classes         | `PascalCase`       | `ConfigManager`      |
| Module classes  | `*Module` suffix   | `DockerModule`       |
| Manager classes | `*Manager` suffix  | `RollbackManager`    |
| Error classes   | `*Error` suffix    | `ConfiguratorError`  |
| Functions       | `snake_case`       | `install_packages`   |
| Private methods | `_snake_case`      | `_execute_action`    |
| Constants       | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT`    |
| Files           | `snake_case.py`    | `circuit_breaker.py` |

### Import Order

1. Standard library imports
2. Third-party package imports
3. Local package imports

```python
# Standard library
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Third-party
import yaml
from rich.console import Console

# Local
from .exceptions import DomainError
from .utils import run_command
```

---

## Testing Principles

### Test Organization

| Test Type   | Location             | Purpose                  |
| ----------- | -------------------- | ------------------------ |
| Unit        | `tests/unit/`        | Isolated component tests |
| Integration | `tests/integration/` | Cross-component tests    |
| Security    | `tests/security/`    | Security validation      |
| Performance | `tests/performance/` | Benchmarks               |

### Test Patterns

- **Arrange-Act-Assert** structure for all tests
- **Mock external dependencies** (network, filesystem, subprocess)
- **Test error paths** as thoroughly as happy paths
- **Use fixtures** for consistent test data
- **Name tests descriptively**: `test_<method>_<scenario>_<expected>`

---

_These guidelines establish version-agnostic principles for consistent technology usage. Specific versions may change, but these architectural patterns and conventions remain stable._
