---
applyTo: '**'
description: 'Permanent architectural rules for folder structure, file placement, and naming conventions in the Debian VPS Configurator project.'
---

# Project Structure Instructions

## Purpose

This document defines immutable structural rules for organizing code, tests, documentation, and configuration files in the Debian VPS Configurator project. All code generation, refactoring, and new development **MUST** adhere to these architectural principles.

---

## Architectural Layers

The project follows a **4-layer Modular Plugin-Based Architecture**. All code placement decisions **MUST** respect these boundaries:

### Layer Hierarchy (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (configurator/cli.py, wizard.py)     │
│    → User interaction, CLI commands, TUI interfaces         │
├─────────────────────────────────────────────────────────────┤
│ 2. ORCHESTRATION LAYER (configurator/core/)                │
│    → Execution coordination, dependency injection, rollback │
├─────────────────────────────────────────────────────────────┤
│ 3. FEATURE LAYER (configurator/modules/)                   │
│    → Self-contained configuration modules, business logic   │
├─────────────────────────────────────────────────────────────┤
│ 4. FOUNDATION LAYER (configurator/utils/, security/)       │
│    → Shared utilities, security primitives, validators     │
└─────────────────────────────────────────────────────────────┘
```

### Layer Rules (MANDATORY)

- ✅ **Higher layers MAY import from lower layers**
- ❌ **Lower layers MUST NOT import from higher layers**
- ❌ **Modules within the same layer SHOULD minimize cross-imports**
- ✅ **All layer violations MUST be resolved through dependency injection**

---

## Directory Structure Rules

### Rule 1: Root Directory Organization

**MUST maintain exactly these top-level directories:**

```
debian-vps-workstation/
├── configurator/         # Main Python package (NO other names allowed)
├── tests/                # Test suite (mirrors configurator/ structure)
├── docs/                 # All documentation
├── config/               # YAML configuration files only
├── scripts/              # Shell scripts for automation
├── tools/                # Development tools and utilities
├── .github/              # GitHub Actions, AI prompts, instructions
├── .agent/               # Agent-specific workflows
├── pyproject.toml        # Project metadata and dependencies
├── pytest.ini            # Test configuration
├── mkdocs.yml            # Documentation build configuration
├── README.md             # Project overview
├── requirements.txt      # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

### Rule 2: Main Package Structure

**MUST organize the `configurator/` package as follows:**

```
configurator/
├── __init__.py           # Package exports (REQUIRED)
├── __main__.py           # Entry point for python -m (REQUIRED)
├── __version__.py        # Version info (REQUIRED)
├── cli.py                # Presentation layer: CLI commands
├── wizard.py             # Presentation layer: TUI interface
├── config.py             # Configuration management
├── config_schema.py      # Pydantic schemas for validation
├── exceptions.py         # Custom exception hierarchy
├── logger.py             # Logging configuration
│
├── core/                 # Orchestration layer (REQUIRED)
│   ├── container.py      # Dependency injection container
│   ├── installer.py      # Installation orchestrator
│   ├── rollback.py       # Rollback manager
│   ├── execution/        # Execution strategies (parallel, pipeline)
│   ├── hooks/            # Lifecycle hooks
│   ├── reporter/         # Progress reporting
│   └── state/            # State persistence
│
├── modules/              # Feature layer (REQUIRED)
│   ├── base.py           # Abstract base class (REQUIRED)
│   └── *.py              # Feature modules (inherit from base.py)
│
├── security/             # Foundation layer: Security (REQUIRED)
│   ├── input_validator.py
│   ├── supply_chain.py
│   ├── certificate_manager.py
│   └── cis_checks/       # CIS compliance checks
│
├── validators/           # Foundation layer: Validation (REQUIRED)
│   ├── base.py           # Validator interface (REQUIRED)
│   ├── orchestrator.py   # Validation coordination (REQUIRED)
│   ├── tier1_critical/   # Must-pass validators
│   ├── tier2_high/       # Should-pass validators
│   └── tier3_medium/     # Nice-to-have validators
│
├── utils/                # Foundation layer: Utilities (REQUIRED)
│   ├── command.py        # Command execution
│   ├── file.py           # File operations
│   ├── circuit_breaker.py
│   └── retry.py
│
└── rbac/                 # Foundation layer: Access control (REQUIRED)
    ├── rbac_manager.py
    └── roles.yaml
```

### Rule 3: Test Structure Mirroring

**MUST organize tests to mirror source structure:**

```
tests/
├── conftest.py           # Shared fixtures (REQUIRED)
├── __init__.py           # Test package marker
│
├── unit/                 # Unit tests (REQUIRED)
│   └── test_*.py         # One file per module
│
├── integration/          # Integration tests (REQUIRED)
│   └── test_*_integration.py
│
├── security/             # Security-focused tests (REQUIRED)
│   └── test_*.py
│
├── validation/           # Validator tests (REQUIRED)
│   └── test_*.py
│
├── modules/              # Module-specific tests
├── performance/          # Performance benchmarks
├── resilience/           # Resilience pattern tests
├── e2e/                  # End-to-end tests
└── fixtures/             # Test data and fixtures
```

---

## File Placement Rules

### Rule 4: File Type Placement Matrix

**MANDATORY placement for all file types:**

| File Type                    | Location                             | Example                      |
| ---------------------------- | ------------------------------------ | ---------------------------- |
| **CLI commands**             | `configurator/cli.py`                | All Click commands           |
| **TUI interfaces**           | `configurator/wizard.py`             | Interactive setup wizard     |
| **Feature modules**          | `configurator/modules/*.py`          | `docker.py`, `python.py`     |
| **Orchestration logic**      | `configurator/core/*.py`             | `installer.py`, `rollback.py`|
| **Shared utilities**         | `configurator/utils/*.py`            | `command.py`, `retry.py`     |
| **Security features**        | `configurator/security/*.py`         | `input_validator.py`         |
| **Validators**               | `configurator/validators/tier*/*.py` | Tiered validation            |
| **Access control**           | `configurator/rbac/*.py`             | `rbac_manager.py`            |
| **Configuration schemas**    | `configurator/config_schema.py`      | Pydantic models              |
| **Custom exceptions**        | `configurator/exceptions.py`         | `*Error` classes             |
| **Configuration files**      | `config/*.yaml`                      | `default.yaml`, profiles     |
| **Role definitions**         | `configurator/rbac/roles.yaml`       | RBAC configuration           |
| **Unit tests**               | `tests/unit/test_*.py`               | One per module               |
| **Integration tests**        | `tests/integration/test_*.py`        | Feature integration          |
| **Security tests**           | `tests/security/test_*.py`           | Security validation          |
| **Documentation**            | `docs/*.md`                          | User guides, API reference   |
| **Shell scripts**            | `scripts/*.sh`                       | Automation scripts           |
| **Development tools**        | `tools/*.py`                         | Helper utilities             |
| **GitHub Actions**           | `.github/workflows/*.yml`            | CI/CD pipelines              |
| **AI instructions**          | `.github/instructions/*.instructions.md` | Copilot guidance     |

### Rule 5: Model and Entity Placement

**Models and entities MUST be placed according to scope:**

| Entity Type              | Placement                       | Naming Convention     |
| ------------------------ | ------------------------------- | --------------------- |
| **Pydantic models**      | `configurator/config_schema.py` | `*Config` suffix      |
| **Dataclasses**          | Same file as primary usage      | `@dataclass` decorator|
| **Custom exceptions**    | `configurator/exceptions.py`    | `*Error` suffix       |
| **Enums**                | Same file as primary usage      | `PascalCase`          |
| **Type aliases**         | `configurator/__init__.py` or inline | Descriptive names |
| **Abstract base classes**| Same directory, `base.py`       | No prefix/suffix      |

---

## Naming Conventions

### Rule 6: File Naming Standards

**MUST follow these exact naming patterns:**

| File Type           | Convention                    | Example                      | Invalid Example       |
| ------------------- | ----------------------------- | ---------------------------- | --------------------- |
| Python modules      | `snake_case.py`               | `circuit_breaker.py`         | ❌ `circuitBreaker.py`|
| Test files          | `test_<module>.py`            | `test_rollback.py`           | ❌ `rollback_test.py` |
| Configuration files | `snake_case.yaml` or `kebab-case.yaml` | `default.yaml` | ❌ `Default.yaml`  |
| Shell scripts       | `snake_case.sh` or `kebab-case.sh` | `quick-install.sh`    | ❌ `quickInstall.sh`  |
| Documentation       | `kebab-case.md` or `UPPER_CASE.md` | `user-guide.md`, `README.md` | ❌ `User_Guide.md` |

### Rule 7: Class Naming Standards

**MUST use these exact patterns:**

| Class Type          | Convention        | Example               | Purpose                    |
| ------------------- | ----------------- | --------------------- | -------------------------- |
| Regular classes     | `PascalCase`      | `ConfigManager`       | General purpose            |
| Feature modules     | `*Module` suffix  | `DockerModule`        | Feature implementations    |
| Manager classes     | `*Manager` suffix | `RollbackManager`     | Resource management        |
| Error classes       | `*Error` suffix   | `ConfiguratorError`   | Custom exceptions          |
| Validator classes   | `*Validator` suffix | `SystemValidator`   | Validation logic           |
| Abstract classes    | No special suffix | `ConfigurationModule` | Base classes/interfaces    |

### Rule 8: Function and Method Naming

**MUST follow these conventions:**

| Function Type       | Convention           | Example                                   | Notes                      |
| ------------------- | -------------------- | ----------------------------------------- | -------------------------- |
| Public methods      | `snake_case`         | `install_packages()`                      | No leading underscore      |
| Private methods     | `_snake_case`        | `_execute_action()`                       | Single leading underscore  |
| CLI commands        | `kebab-case` (Click) | `@cli.command("check-system")`            | Use Click conventions      |
| Test functions      | `test_<description>` | `test_rollback_executes_in_reverse_order` | Descriptive test names     |

### Rule 9: Directory Naming

**MUST use these patterns:**

| Directory Type      | Convention        | Example               | Invalid Example       |
| ------------------- | ----------------- | --------------------- | --------------------- |
| Python packages     | `snake_case`      | `configurator`        | ❌ `Configurator`     |
| Feature directories | `snake_case`      | `cis_checks`          | ❌ `CIS_Checks`       |
| Tier directories    | `tier<N>_<level>` | `tier1_critical`      | ❌ `critical_tier1`   |
| Test categories     | `snake_case`      | `unit`, `integration` | ❌ `Unit`, `Integration` |

---

## Module Design Rules

### Rule 10: Feature Module Requirements

**ALL feature modules MUST:**

1. ✅ **Inherit from** `ConfigurationModule` in `configurator/modules/base.py`
2. ✅ **Implement three lifecycle methods:**
   - `validate()` → Check prerequisites
   - `configure()` → Execute configuration
   - `verify()` → Verify success
3. ✅ **Define class attributes:**
   - `name` → Module identifier (string)
   - `description` → Purpose description (string)
   - `depends_on` → List of dependency module names
   - `priority` → Execution priority (integer)
4. ✅ **Accept dependencies via constructor** with defaults
5. ✅ **Be placed in** `configurator/modules/<feature>.py`
6. ✅ **Have corresponding tests in** `tests/unit/test_<feature>.py`
7. ✅ **Be registered in** `configurator/modules/__init__.py`
8. ✅ **Have configuration section in** `config/default.yaml`

**Module Template (REQUIRED STRUCTURE):**

```python
"""<Feature> module for <purpose>."""

from configurator.modules.base import ConfigurationModule


class <Feature>Module(ConfigurationModule):
    """<Feature> installation and configuration."""

    name = "<feature>"
    description = "<description>"
    depends_on = ["system"]  # List dependencies
    priority = 50            # Execution priority (10-100)

    def validate(self) -> bool:
        """Validate prerequisites before configuration."""
        # Validation logic
        return True

    def configure(self) -> bool:
        """Execute configuration steps."""
        self.logger.info(f"Configuring {self.name}...")
        # Configuration logic
        return True

    def verify(self) -> bool:
        """Verify configuration was successful."""
        # Verification logic
        return True
```

### Rule 11: Validator Requirements

**ALL validators MUST:**

1. ✅ **Be placed in tiered directories:**
   - `tier1_critical/` → Must pass (blocks installation)
   - `tier2_high/` → Should pass (warnings)
   - `tier3_medium/` → Nice to have (informational)
2. ✅ **Inherit from** `BaseValidator` in `configurator/validators/base.py`
3. ✅ **Implement** `validate()` → Returns `ValidationResult`
4. ✅ **Define attributes:**
   - `name` → Validator identifier
   - `description` → What it validates
5. ✅ **Be registered in tier's** `__init__.py`
6. ✅ **Have corresponding test in** `tests/validation/test_<validator>.py`

**Validator Template (REQUIRED STRUCTURE):**

```python
"""<Validator> validator."""

from configurator.validators.base import BaseValidator, ValidationResult


class <ValidatorName>Validator(BaseValidator):
    """Validates <what it checks>."""

    name = "<validator_name>"
    description = "<description>"

    def validate(self) -> ValidationResult:
        """Execute validation check."""
        # Validation logic
        return ValidationResult(
            passed=True,
            message="Validation passed",
            details={}
        )
```

### Rule 12: Utility Function Requirements

**ALL utility functions MUST:**

1. ✅ **Be placed in** `configurator/utils/<utility>.py`
2. ✅ **Be exported from** `configurator/utils/__init__.py`
3. ✅ **Have unit tests in** `tests/unit/test_<utility>.py`
4. ✅ **Include type hints** for parameters and return values
5. ✅ **Have docstrings** explaining purpose and usage
6. ✅ **Be stateless** or accept dependencies via parameters

---

## Dependency Management Rules

### Rule 13: Import Organization

**MUST organize imports in this exact order:**

```python
# 1. Standard library imports (alphabetically sorted)
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Third-party imports (alphabetically sorted)
import yaml
from rich.console import Console

# 3. Local package imports (alphabetically sorted)
from configurator.core.rollback import RollbackManager
from configurator.exceptions import ConfiguratorError
from configurator.utils.command import run_command
```

### Rule 14: Dependency Injection Pattern

**MUST use dependency injection, NOT direct imports between layers:**

```python
# ❌ WRONG: Direct cross-layer import
from configurator.modules.network import NetworkModule

class MyModule:
    def __init__(self):
        self.network = NetworkModule()  # Hard dependency


# ✅ CORRECT: Dependency injection with default
from configurator.core.container import get_dependency

class MyModule:
    def __init__(self, network_module=None):
        self.network = network_module or get_dependency('network')
```

### Rule 15: Package Exports

**MUST define public API in `__init__.py` files:**

```python
# configurator/utils/__init__.py
from configurator.utils.command import run_command, CommandResult
from configurator.utils.file import write_file, read_file
from configurator.utils.circuit_breaker import CircuitBreaker

__all__ = [
    "run_command",
    "CommandResult",
    "write_file",
    "read_file",
    "CircuitBreaker",
]
```

---

## Configuration File Rules

### Rule 16: Configuration Organization

**MUST organize configuration files as:**

```
config/
├── default.yaml          # Default configuration (REQUIRED)
├── profiles/             # User profiles (optional)
│   ├── minimal.yaml
│   ├── standard.yaml
│   └── full.yaml
└── examples/             # Example configurations (optional)
```

**Configuration Structure (REQUIRED):**

```yaml
# config/default.yaml
system:
  hostname: null
  timezone: "UTC"

modules:
  docker:
    enabled: true
    version: "latest"

  python:
    enabled: true
    version: "3.11"
```

### Rule 17: Security Configuration

**Security-related configuration MUST be in:**

```
configurator/
├── rbac/
│   └── roles.yaml        # RBAC role definitions
└── security/
    └── checksums.yaml    # Security checksums
```

---

## Test Organization Rules

### Rule 18: Test File Placement

**MUST place tests according to category:**

| Test Category           | Location                      | Purpose                           |
| ----------------------- | ----------------------------- | --------------------------------- |
| **Unit tests**          | `tests/unit/test_*.py`        | Individual function/class tests   |
| **Integration tests**   | `tests/integration/test_*.py` | Module interaction tests          |
| **Security tests**      | `tests/security/test_*.py`    | Security validation tests         |
| **Validation tests**    | `tests/validation/test_*.py`  | Validator tests                   |
| **Performance tests**   | `tests/performance/test_*.py` | Benchmark tests                   |
| **E2E tests**           | `tests/e2e/test_*.py`         | Full workflow tests               |

### Rule 19: Test Structure

**ALL test files MUST follow this structure:**

```python
"""Tests for <module>."""

import pytest
from configurator.<path> import <Class>


class Test<Class>:
    """Tests for <Class> functionality."""

    def test_<specific_behavior>(self):
        """Test that <expected behavior occurs>."""
        # Arrange
        instance = <Class>()

        # Act
        result = instance.method()

        # Assert
        assert result == expected_value
```

### Rule 20: Test Fixtures

**Shared fixtures MUST be in:**

- `tests/conftest.py` → Project-wide fixtures (REQUIRED)
- `tests/<category>/conftest.py` → Category-specific fixtures (optional)

---

## Documentation Rules

### Rule 21: Documentation Structure

**MUST organize documentation as:**

```
docs/
├── index.md              # Documentation home (REQUIRED)
├── architecture.md       # System architecture (REQUIRED)
├── exemplars.md          # Code exemplars (REQUIRED)
│
├── user-guide/           # User documentation
│   ├── installation.md
│   ├── configuration.md
│   └── usage.md
│
├── api-reference/        # API documentation
│   └── <module>.md
│
├── tutorials/            # Step-by-step guides
│   └── <tutorial>.md
│
└── modules/              # Module documentation
    └── <module>.md
```

### Rule 22: Code Documentation

**ALL code MUST include:**

1. ✅ **Module-level docstrings** at file top
2. ✅ **Class docstrings** explaining purpose
3. ✅ **Method docstrings** with parameters and returns
4. ✅ **Type hints** for all function signatures
5. ✅ **Inline comments** for complex logic only

---

## Extension and Evolution Rules

### Rule 23: Adding New Components

**When adding new components, follow these workflows:**

#### Adding a Feature Module

1. Create `configurator/modules/<feature>.py` (inherit from `ConfigurationModule`)
2. Register in `configurator/modules/__init__.py`
3. Create `tests/unit/test_<feature>.py`
4. Create `tests/integration/test_<feature>_integration.py`
5. Add configuration section to `config/default.yaml`
6. Create `docs/modules/<feature>.md`

#### Adding a Validator

1. Choose tier: `tier1_critical`, `tier2_high`, or `tier3_medium`
2. Create `configurator/validators/<tier>/<validator>.py`
3. Register in `configurator/validators/<tier>/__init__.py`
4. Create `tests/validation/test_<validator>.py`

#### Adding a Utility

1. Create `configurator/utils/<utility>.py`
2. Export in `configurator/utils/__init__.py`
3. Create `tests/unit/test_<utility>.py`
4. Add docstrings and type hints

#### Adding a CLI Command

1. Add function to `configurator/cli.py`
2. Use `@cli.command()` or `@<group>.command()` decorator
3. Add comprehensive help text
4. Create integration test

### Rule 24: Refactoring Guidelines

**When refactoring, maintain structure integrity:**

1. ✅ **Extract common code to** `configurator/utils/`
2. ✅ **Split large files** by responsibility
3. ✅ **Create subpackages** for related modules
4. ✅ **Update tests** to match new structure
5. ✅ **Update documentation** to reflect changes
6. ❌ **Never break layer boundaries**
7. ❌ **Never create circular dependencies**

---

## Structural Enforcement

### Rule 25: Validation Tools

**MUST use these tools to enforce structure:**

| Tool           | Purpose                  | Configuration             | Required |
| -------------- | ------------------------ | ------------------------- | -------- |
| **Ruff**       | Import ordering, linting | `pyproject.toml`          | ✅ Yes   |
| **MyPy**       | Type checking            | `pyproject.toml`          | ✅ Yes   |
| **pytest**     | Test discovery           | `pytest.ini`              | ✅ Yes   |
| **Pre-commit** | Git hooks                | `.pre-commit-config.yaml` | ✅ Yes   |

### Rule 26: Import Sorting Configuration

**MUST configure Ruff for import sorting:**

```toml
# pyproject.toml
[tool.ruff.lint.isort]
known-first-party = ["configurator"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]
```

---

## Anti-Patterns (DO NOT DO)

### Structural Anti-Patterns

❌ **NEVER:**

- Place feature logic in `cli.py` or `wizard.py` (presentation layer)
- Import from higher layers in lower layers
- Create circular dependencies between modules
- Mix test categories (unit tests in integration folder)
- Hardcode configuration values in code
- Use relative imports that break package structure
- Place utilities in the wrong layer
- Skip abstract base class inheritance for modules/validators
- Create modules without corresponding tests
- Mix module types in the same directory

### Naming Anti-Patterns

❌ **NEVER:**

- Use `camelCase` for Python files or functions
- Use `PascalCase` for module files
- Omit `test_` prefix for test files
- Use generic names like `utils.py` at root level
- Create files with spaces in names
- Use inconsistent naming between related files

### Organization Anti-Patterns

❌ **NEVER:**

- Place business logic in utility modules
- Create "misc" or "common" directories for unrelated code
- Mix production and test code in the same directory
- Place configuration in source files
- Skip package `__init__.py` files
- Create nested package structures deeper than necessary

---

## Quick Reference

### Where to Place New Code

| I need to add...         | Place it in...                       | File pattern              |
| ------------------------ | ------------------------------------ | ------------------------- |
| CLI command              | `configurator/cli.py`                | Add function with decorator |
| TUI screen               | `configurator/wizard.py`             | Add class/function        |
| Feature module           | `configurator/modules/<feature>.py`  | `<Feature>Module` class   |
| Orchestration logic      | `configurator/core/<component>.py`   | Appropriate core file     |
| Utility function         | `configurator/utils/<utility>.py`    | Function with docstring   |
| Security feature         | `configurator/security/<feature>.py` | Class or functions        |
| Critical validator       | `configurator/validators/tier1_critical/` | `<Name>Validator` |
| Unit test                | `tests/unit/test_<module>.py`        | `Test<Class>` class       |
| Integration test         | `tests/integration/test_<feature>.py` | `Test<Feature>Integration` |
| Configuration option     | `config/default.yaml`                | YAML section              |
| Documentation            | `docs/<category>/<topic>.md`         | Markdown file             |

### Common Path Mappings

| Namespace                                     | File Path                                |
| --------------------------------------------- | ---------------------------------------- |
| `configurator.config.ConfigManager`           | `configurator/config.py`                 |
| `configurator.core.rollback.RollbackManager`  | `configurator/core/rollback.py`          |
| `configurator.modules.docker.DockerModule`    | `configurator/modules/docker.py`         |
| `configurator.utils.circuit_breaker.CircuitBreaker` | `configurator/utils/circuit_breaker.py` |
| `configurator.security.input_validator.InputValidator` | `configurator/security/input_validator.py` |
| `configurator.validators.base.BaseValidator`  | `configurator/validators/base.py`        |

---

## Summary: Golden Rules

1. ✅ **Respect the 4-layer architecture** → No cross-layer violations
2. ✅ **Use dependency injection** → No direct imports between layers
3. ✅ **Follow naming conventions** → snake_case for files, PascalCase for classes
4. ✅ **Inherit from base classes** → All modules/validators use base classes
5. ✅ **Mirror test structure** → Tests match source organization
6. ✅ **Place files by purpose** → Use the placement matrix
7. ✅ **Export public API** → Use `__init__.py` files
8. ✅ **Write comprehensive tests** → Every module needs tests
9. ✅ **Document everything** → Docstrings and markdown docs
10. ✅ **Enforce with tools** → Use Ruff, MyPy, pytest, pre-commit

---

_This document defines permanent structural rules. Any changes to these rules require architectural review._

_Last updated: 2026-01-17_
