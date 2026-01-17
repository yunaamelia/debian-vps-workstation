# GitHub Copilot Instructions

**Debian VPS Configurator v2.0 — Code Generation Guidelines**

This file guides GitHub Copilot to produce code consistent with our project's standards, architecture, and technology versions.

---

## Priority Guidelines

When generating code for this repository:

1. **Version Compatibility**: Always respect Python 3.11+ and the exact package versions in `pyproject.toml`
2. **Context Files**: Prioritize patterns in the `.github/` directory and `docs/` documentation
3. **Codebase Patterns**: When context files don't provide guidance, scan existing code for patterns
4. **Architectural Consistency**: Maintain our Modular Plugin-Based Layered architectural style
5. **Code Quality**: Prioritize maintainability, security, testability, and performance

---

## Technology Version Detection

### Language Versions

| Technology   | Version | Source           |
| ------------ | ------- | ---------------- |
| **Python**   | ≥3.11   | `pyproject.toml` |
| **Click**    | ≥8.1.7  | CLI framework    |
| **Rich**     | ≥13.9.4 | Console output   |
| **Pydantic** | ≥2.12.0 | Validation       |
| **pytest**   | ≥8.3.4  | Testing          |

### Framework Compatibility Rules

- ✅ Use type hints (PEP 484, 604)
- ✅ Use `dataclasses` for data containers
- ✅ Use `match` statements (Python 3.10+)
- ✅ Use `X | Y` union syntax (Python 3.10+)
- ✅ Use `Self` return type (Python 3.11+)
- ❌ Do NOT use features from Python 3.12+ unless explicitly listed

---

## Context Files

Prioritize the following documentation in order:

| Priority | File                                          | Purpose                 |
| -------- | --------------------------------------------- | ----------------------- |
| 1        | `docs/architecture.md`                        | System architecture     |
| 2        | `docs/Technology_Stack_Blueprint.md`          | Technology versions     |
| 3        | `docs/exemplars.md`                           | Exemplary code patterns |
| 4        | `docs/Project_Folders_Structure_Blueprint.md` | Project organization    |
| 5        | `docs/Project_Workflow_Analysis_Blueprint.md` | Workflow patterns       |

---

## Architecture Guidelines

### Layered Architecture

All code must respect the 4-layer architecture:

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

**Layer Rules:**

- Higher layers may import from lower layers
- Lower layers MUST NOT import from higher layers
- Modules in the same layer should minimize cross-imports

### Module Pattern

All feature modules MUST:

1. Inherit from `ConfigurationModule` in `modules/base.py`
2. Implement `validate()`, `configure()`, `verify()` methods
3. Include metadata: `name`, `description`, `depends_on`, `priority`
4. Register rollback actions before making state changes

---

## Naming Conventions

### Classes

| Type              | Convention   | Example               |
| ----------------- | ------------ | --------------------- |
| Regular classes   | `PascalCase` | `ConfigManager`       |
| Module classes    | `*Module`    | `DockerModule`        |
| Manager classes   | `*Manager`   | `RollbackManager`     |
| Error classes     | `*Error`     | `ConfiguratorError`   |
| Validator classes | `*Validator` | `RootAccessValidator` |

### Functions/Methods

| Type    | Convention               | Example               |
| ------- | ------------------------ | --------------------- |
| Public  | `snake_case`             | `install_packages()`  |
| Private | `_snake_case`            | `_execute_action()`   |
| Boolean | `is_*`, `has_*`, `can_*` | `is_service_active()` |
| Factory | `create_*`, `make_*`     | `create_breaker()`    |

### Files

| Type   | Convention        | Example              |
| ------ | ----------------- | -------------------- |
| Python | `snake_case.py`   | `circuit_breaker.py` |
| Tests  | `test_*.py`       | `test_rollback.py`   |
| Config | `snake_case.yaml` | `default.yaml`       |

---

## Code Organization

### Import Order (enforced by Ruff)

```python
# 1. Standard library
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Third-party packages
import yaml
from click import command, option
from rich.console import Console

# 3. Local imports
from configurator.core.rollback import RollbackManager
from configurator.exceptions import ConfiguratorError
```

### Module Structure

```python
"""
Module docstring (required).

Describes what the module does.
"""

# Imports (ordered as above)
import ...

# Constants
CONSTANT_VALUE = "value"

# Type definitions
ConfigDict = Dict[str, Any]

# Classes (one main class per file preferred)
class MainClass:
    """Class docstring (required)."""
    pass

# Module-level functions (if any)
def utility_function():
    """Function docstring (required)."""
    pass
```

---

## Error Handling

### Exception Pattern

Use custom exceptions from `exceptions.py`:

```python
# CORRECT: User-friendly exceptions with WHAT/WHY/HOW
raise ConfiguratorError(
    what="Configuration file not found",
    why="The specified path does not exist",
    how="Check the path and try again"
)

# INCORRECT: Generic exceptions
raise Exception("Config not found")  # ❌ Don't do this
```

### Try/Except Pattern

```python
# CORRECT: Catch specific exceptions
try:
    result = risky_operation()
except SpecificError as e:
    self.logger.error(f"Operation failed: {e}")
    raise

# INCORRECT: Bare except
try:
    result = risky_operation()
except:  # ❌ Never use bare except
    pass
```

---

## Logging Pattern

```python
class MyClass:
    def __init__(self, logger: Optional[logging.Logger] = None):
        # Accept optional logger with default
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def method(self):
        self.logger.info("Starting operation...")
        self.logger.debug("Details: %s", details)  # Use % formatting
        self.logger.error("Failed: %s", error)
```

---

## Dependency Injection

### Pattern

```python
def __init__(
    self,
    config: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
    rollback_manager: Optional[RollbackManager] = None,
):
    """Accept optional dependencies with sensible defaults."""
    self.config = config
    self.logger = logger or logging.getLogger(self.__class__.__name__)
    self.rollback_manager = rollback_manager or RollbackManager()
```

### Container Registration

```python
# Singleton for shared services
container.singleton('config', lambda: ConfigManager())

# Factory for per-request instances
container.factory('module', lambda c, config: ModuleClass(config=config))
```

---

## Testing Requirements

### Test File Location

| Test Type   | Directory            | Naming                |
| ----------- | -------------------- | --------------------- |
| Unit        | `tests/unit/`        | `test_<module>.py`    |
| Integration | `tests/integration/` | `test_<feature>.py`   |
| Security    | `tests/security/`    | `test_<concern>.py`   |
| Validation  | `tests/validation/`  | `test_<validator>.py` |

### Test Structure

```python
@pytest.mark.unit
class TestMyClass:
    """Tests for MyClass."""

    def test_method_does_expected_thing(self):
        """Test that method does X when given Y."""
        # Arrange
        instance = MyClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected
```

### Mocking Pattern

```python
def test_with_mock(self, tmp_path, monkeypatch):
    """Test with mocked dependencies."""
    # Mock external calls
    def mock_run(cmd, **kwargs):
        return CommandResult(command=cmd, return_code=0, stdout="", stderr="")

    monkeypatch.setattr("configurator.utils.command.run_command", mock_run)

    # Test implementation
    result = function_under_test()
    assert result is True
```

---

## Documentation Requirements

### Docstrings

All public classes and methods MUST have docstrings:

```python
def install_packages(packages: List[str], force: bool = False) -> bool:
    """
    Install packages with resilience.

    Args:
        packages: List of package names to install
        force: If True, reinstall even if already installed

    Returns:
        True if all packages installed successfully

    Raises:
        PackageInstallError: If installation fails after retries
    """
```

### Comments

- Use comments to explain WHY, not WHAT
- Avoid redundant comments that restate the code
- Use `# TODO:` for future work (include author if long-term)

---

## Security Guidelines

### Input Validation

Always validate user input using `InputValidator`:

```python
from configurator.security.input_validator import InputValidator

validator = InputValidator()
if not validator.validate_username(username):
    raise ValidationError(f"Invalid username: {username}")
```

### Command Execution

Never execute unsanitized user input:

```python
# CORRECT: Use shlex.quote
import shlex
safe_arg = shlex.quote(user_input)
run_command(f"echo {safe_arg}")

# INCORRECT: Direct interpolation
run_command(f"echo {user_input}")  # ❌ Command injection risk
```

### Rollback Registration

Always register rollback BEFORE making changes:

```python
# CORRECT: Register before change
self.rollback_manager.add_package_remove(packages, "Remove on failure")
self.install_packages(packages)

# INCORRECT: Register after change
self.install_packages(packages)
self.rollback_manager.add_package_remove(packages)  # ❌ Too late if install fails
```

---

## CLI Command Pattern

```python
@main.command()
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def my_command(ctx: click.Context, dry_run: bool, verbose: bool):
    """
    Command description.

    Examples:
      vps-configurator my-command
      vps-configurator my-command --dry-run
    """
    logger = ctx.obj["logger"]

    try:
        if dry_run:
            console.print("[yellow]DRY RUN MODE[/yellow]")

        # Implementation
        result = do_something()

        if result:
            console.print("[green]✓ Success[/green]")
        else:
            console.print("[red]✗ Failed[/red]")
            sys.exit(1)

    except Exception as e:
        logger.exception("Command failed")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
```

---

## Version Control Guidelines

- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Update CHANGELOG.md for user-facing changes
- Create feature branches: `feature/<description>`

---

## What NOT to Do

| Anti-Pattern                 | Instead Do                   |
| ---------------------------- | ---------------------------- |
| Bare `except:`               | Catch specific exceptions    |
| Global mutable state         | Use dependency injection     |
| Hardcoded paths              | Use `Path` and config values |
| Direct shell interpolation   | Use `shlex.quote()`          |
| Missing rollback             | Register before changes      |
| Missing docstrings           | Document all public APIs     |
| Importing from higher layers | Respect layer boundaries     |
| Using Python 3.12+ features  | Stick to 3.11 compatibility  |

---

## Quick Reference

### New Module Checklist

- [ ] Inherit from `ConfigurationModule`
- [ ] Implement `validate()`, `configure()`, `verify()`
- [ ] Add `name`, `description`, `depends_on`, `priority`
- [ ] Register in `modules/__init__.py`
- [ ] Add tests in `tests/unit/`
- [ ] Update `config/default.yaml`

### New Command Checklist

- [ ] Add to `cli.py` with `@main.command()` or group
- [ ] Add options with help text
- [ ] Handle exceptions gracefully
- [ ] Use Rich console output
- [ ] Add docstring with examples
- [ ] Add tests

---

## Code Review Guidance

The following applies when performing code reviews for `.github/` files:

### Prompt File Guide (\*.prompt.md)

- [ ] Has markdown front matter with `description` field
- [ ] Description is wrapped in single quotes
- [ ] Filename is lowercase with hyphens

### Instruction File Guide (\*.instructions.md)

- [ ] Has front matter with `description` and `applyTo` fields
- [ ] Description is wrapped in single quotes
- [ ] Filename is lowercase with hyphens

### Agent/Chat Mode Guide (\*.agent.md)

- [ ] Has front matter with `description` field
- [ ] Description is wrapped in single quotes
- [ ] Filename is lowercase with hyphens

### Skills Guide (skills/\*)

- [ ] Folder contains `SKILL.md` file
- [ ] SKILL.md has `name` and `description` in front matter
- [ ] Name matches folder name (lowercase with hyphens)
- [ ] Assets are under 5MB per file

---

_Last updated: 2026-01-17_
_Python version: ≥3.11_
_Architecture: Modular Plugin-Based Layered_
