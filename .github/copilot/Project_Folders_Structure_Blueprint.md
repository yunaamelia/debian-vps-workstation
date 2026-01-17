# Project Folder Structure Blueprint

**Debian VPS Configurator v2.0 — Comprehensive Folder Organization Guide**

> Definitive guide for maintaining consistent code organization across the codebase.

---

## Table of Contents

1. [Structural Overview](#1-structural-overview)
2. [Directory Visualization](#2-directory-visualization)
3. [Key Directory Analysis](#3-key-directory-analysis)
4. [File Placement Patterns](#4-file-placement-patterns)
5. [Naming and Organization Conventions](#5-naming-and-organization-conventions)
6. [Navigation and Development Workflow](#6-navigation-and-development-workflow)
7. [Build and Output Organization](#7-build-and-output-organization)
8. [Python-Specific Organization](#8-python-specific-organization)
9. [Extension and Evolution](#9-extension-and-evolution)
10. [Structure Templates](#10-structure-templates)
11. [Structure Enforcement](#11-structure-enforcement)

---

## 1. Structural Overview

### Project Type Detection

| Indicator            | Value        | Location           |
| -------------------- | ------------ | ------------------ |
| **Primary Language** | Python 3.11+ | `pyproject.toml`   |
| **Build System**     | setuptools   | `pyproject.toml`   |
| **Package Manager**  | pip          | `requirements.txt` |
| **Test Framework**   | pytest       | `pytest.ini`       |
| **Documentation**    | MkDocs       | `mkdocs.yml`       |
| **Linting**          | Ruff, MyPy   | `pyproject.toml`   |

### Architectural Overview

This is a **Python CLI application** following a **Modular Plugin-Based Layered Architecture** with **4 distinct layers**:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  CLI (cli.py) │ TUI (wizard.py) │ Rich Console Output       │
├─────────────────────────────────────────────────────────────┤
│                   ORCHESTRATION LAYER                        │
│  core/installer.py │ core/execution/ │ core/rollback.py     │
├─────────────────────────────────────────────────────────────┤
│                      FEATURE LAYER                           │
│  modules/ (24 self-contained configuration modules)          │
├─────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                          │
│  utils/ │ security/ │ rbac/ │ validators/                   │
└─────────────────────────────────────────────────────────────┘
```

### Organizational Principles

1. **Separation by Layer** — Each architectural layer has dedicated directories
2. **Feature Encapsulation** — Each module is self-contained with minimal cross-dependencies
3. **Shared Utilities** — Common functionality extracted to foundation layer
4. **Configuration Driven** — Behavior controlled via YAML configuration files
5. **Test Mirroring** — Test structure mirrors source structure by category

---

## 2. Directory Visualization

### Root Directory Structure (Depth 1)

```
debian-vps-workstation/
├── configurator/         # Main Python package (177 items)
├── tests/                # Test suite (178 items)
├── docs/                 # Documentation (112 items)
├── config/               # Configuration files (4 items)
├── scripts/              # Utility scripts (30 items)
├── tools/                # Development tools (17 items)
├── .github/              # GitHub workflows and AI prompts (96 items)
├── .agent/               # Agent workflows (3 items)
├── pyproject.toml        # Project configuration
├── pytest.ini            # Test configuration
├── mkdocs.yml            # Documentation configuration
├── README.md             # Project documentation
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── quick-install.sh      # Quick installation script
└── install_tools.sh      # Tool installation helper
```

### Main Package Structure (Depth 2)

```
configurator/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point for python -m
├── __version__.py        # Version information
├── cli.py                # CLI commands (128KB, 106 commands)
├── cli_monitoring.py     # Monitoring CLI extensions
├── config.py             # Configuration management
├── config_schema.py      # Pydantic configuration schema
├── exceptions.py         # Custom exception hierarchy
├── logger.py             # Logging configuration
├── wizard.py             # Installation wizard TUI
│
├── core/                 # Orchestration layer
│   ├── container.py      # Dependency injection
│   ├── installer.py      # Installation orchestrator
│   ├── rollback.py       # Rollback manager
│   ├── network.py        # Network operations
│   ├── package_cache.py  # Package caching
│   ├── lazy_loader.py    # Lazy loading utilities
│   ├── validator.py      # Pre-flight validation
│   ├── execution/        # Execution strategies
│   ├── hooks/            # Lifecycle hooks
│   ├── reporter/         # Progress reporting
│   └── state/            # State persistence
│
├── modules/              # Feature layer (24 modules)
│   ├── base.py           # Abstract base class
│   ├── system.py         # System configuration
│   ├── security.py       # Security hardening
│   ├── desktop.py        # Desktop environment
│   ├── docker.py         # Docker installation
│   ├── python.py         # Python setup
│   ├── nodejs.py         # Node.js setup
│   └── ...               # Other feature modules
│
├── security/             # Security foundation
│   ├── input_validator.py
│   ├── supply_chain.py
│   ├── certificate_manager.py
│   ├── mfa_manager.py
│   ├── ssh_manager.py
│   ├── cis_checks/       # CIS benchmark checks
│   └── ...
│
├── validators/           # Validation framework
│   ├── base.py           # Validator base class
│   ├── orchestrator.py   # Validation orchestration
│   ├── tier1_critical/   # Critical validators
│   ├── tier2_high/       # High priority validators
│   └── tier3_medium/     # Medium priority validators
│
├── utils/                # Shared utilities
│   ├── command.py        # Command execution
│   ├── file.py           # File operations
│   ├── circuit_breaker.py # Circuit breaker pattern
│   ├── retry.py          # Retry decorator
│   └── ...
│
├── rbac/                 # Role-based access control
│   ├── rbac_manager.py
│   ├── sudo_manager.py
│   └── roles.yaml
│
├── users/                # User management
├── ui/                   # UI components
│   ├── components/
│   ├── prompts/
│   ├── formatters/
│   └── visualizers/
├── ux/                   # User experience utilities
├── observability/        # Metrics and logging
├── dependencies/         # Dependency management
├── plugins/              # Plugin system
├── profiles/             # Configuration profiles
├── benchmarks/           # Performance benchmarks
└── wizard/               # Wizard UI components
```

### Test Structure (Depth 2)

```
tests/
├── conftest.py           # Shared fixtures
├── __init__.py
│
├── unit/                 # Unit tests (65 files)
│   ├── test_config.py
│   ├── test_container.py
│   ├── test_circuit_breaker.py
│   └── ...
│
├── integration/          # Integration tests (26 files)
│   ├── test_rollback.py
│   ├── test_parallel_execution.py
│   ├── test_module_dependency_integration.py
│   └── ...
│
├── security/             # Security tests (11 files)
│   ├── test_command_injection.py
│   ├── test_input_validation.py
│   ├── test_supply_chain.py
│   └── ...
│
├── validation/           # Validation tests (53 files)
├── modules/              # Module-specific tests (5 files)
├── performance/          # Performance tests (6 files)
├── resilience/           # Resilience tests (1 file)
├── manual/               # Manual tests (5 files)
├── visual/               # Visual tests (2 files)
├── system/               # System tests (1 file)
├── e2e/                  # End-to-end tests
├── benchmarks/           # Benchmark tests
└── fixtures/             # Test fixtures (1 file)
```

---

## 3. Key Directory Analysis

### 3.1 Orchestration Layer: `configurator/core/`

| Directory/File | Purpose                        | Key Files                                 |
| -------------- | ------------------------------ | ----------------------------------------- |
| `container.py` | Dependency injection container | Singleton/factory registration            |
| `installer.py` | Module execution orchestrator  | Batch execution, progress tracking        |
| `rollback.py`  | Transaction rollback manager   | State persistence, undo operations        |
| `execution/`   | Execution strategies           | `parallel.py`, `pipeline.py`, `hybrid.py` |
| `hooks/`       | Lifecycle hooks                | Pre/post execution hooks                  |
| `reporter/`    | Progress reporting             | Console, file, and structured reporting   |
| `state/`       | State persistence              | Checkpoint management                     |

### 3.2 Feature Layer: `configurator/modules/`

All modules inherit from `ConfigurationModule` in `base.py` and implement:

- `validate()` — Check prerequisites
- `configure()` — Execute installation
- `verify()` — Verify success
- `rollback()` — Undo changes (optional override)

| Module        | Description             | Priority |
| ------------- | ----------------------- | -------- |
| `system.py`   | System configuration    | 10       |
| `security.py` | Security hardening      | 20       |
| `desktop.py`  | XFCE + xRDP environment | 30       |
| `docker.py`   | Docker Engine + Compose | 50       |
| `python.py`   | Python environment      | 50       |
| `nodejs.py`   | Node.js via NVM         | 50       |
| `git.py`      | Git + GitHub CLI        | 40       |
| `vscode.py`   | VS Code installation    | 60       |

### 3.3 Foundation Layer: `configurator/utils/`

| File                 | Purpose                     | Pattern                   |
| -------------------- | --------------------------- | ------------------------- |
| `command.py`         | Shell command execution     | `CommandResult` dataclass |
| `file.py`            | File operations with backup | Write, copy, restore      |
| `circuit_breaker.py` | Resilience pattern          | State machine             |
| `retry.py`           | Retry with backoff          | Decorator                 |
| `apt_cache.py`       | APT cache integration       | Cache manager             |

### 3.4 Security Layer: `configurator/security/`

| File                     | Purpose                           |
| ------------------------ | --------------------------------- |
| `input_validator.py`     | Input sanitization and validation |
| `supply_chain.py`        | GPG key and checksum verification |
| `certificate_manager.py` | SSL/TLS certificate management    |
| `ssh_manager.py`         | SSH key and configuration         |
| `mfa_manager.py`         | Multi-factor authentication       |
| `cis_checks/`            | CIS benchmark compliance checks   |

### 3.5 Validation Framework: `configurator/validators/`

Tiered validation system with priority-based execution:

```
validators/
├── base.py               # Abstract validator interface
├── orchestrator.py       # Coordinates validator execution
├── tier1_critical/       # Must pass (blocks installation)
│   ├── system_requirements.py
│   ├── network_connectivity.py
│   └── permissions.py
├── tier2_high/           # Should pass (warnings)
│   ├── disk_space.py
│   └── memory.py
└── tier3_medium/         # Nice to have (informational)
    └── recommendations.py
```

---

## 4. File Placement Patterns

### Configuration Files

| File Type        | Location                               | Example                    |
| ---------------- | -------------------------------------- | -------------------------- |
| Project config   | `pyproject.toml`                       | Build, dependencies, tools |
| Default config   | `config/default.yaml`                  | Application defaults       |
| Profile configs  | `config/profiles/*.yaml`               | User profiles              |
| Test config      | `pytest.ini`                           | Test settings              |
| Role definitions | `configurator/rbac/roles.yaml`         | RBAC roles                 |
| Checksums        | `configurator/security/checksums.yaml` | Security checksums         |

### Model/Entity Definitions

| Type            | Location                        | Naming                 |
| --------------- | ------------------------------- | ---------------------- |
| Pydantic models | `configurator/config_schema.py` | `*Config` classes      |
| Dataclasses     | Same file as usage              | `@dataclass` decorator |
| Exceptions      | `configurator/exceptions.py`    | `*Error` suffix        |
| Enums           | Same file as usage              | `PascalCase`           |

### Business Logic

| Type                   | Location                     |
| ---------------------- | ---------------------------- |
| CLI commands           | `configurator/cli.py`        |
| Module implementations | `configurator/modules/*.py`  |
| Core orchestration     | `configurator/core/*.py`     |
| Security operations    | `configurator/security/*.py` |

### Interface Definitions

| Type                  | Location                             |
| --------------------- | ------------------------------------ |
| Abstract base classes | Same directory, named `base.py`      |
| Protocols             | Inline with usage                    |
| Type aliases          | `configurator/__init__.py` or inline |

### Test Files

| Test Type         | Location                      | Naming               |
| ----------------- | ----------------------------- | -------------------- |
| Unit tests        | `tests/unit/test_*.py`        | `test_<module>.py`   |
| Integration tests | `tests/integration/test_*.py` | `test_<feature>.py`  |
| Security tests    | `tests/security/test_*.py`    | `test_<concern>.py`  |
| Fixtures          | `tests/conftest.py`           | Shared fixtures      |
| Module tests      | `tests/modules/test_*.py`     | `test_<module>_*.py` |

### Documentation Files

| Type           | Location                  |
| -------------- | ------------------------- |
| Main README    | `README.md`               |
| Architecture   | `docs/architecture.md`    |
| Code exemplars | `docs/exemplars.md`       |
| API reference  | `docs/api-reference/*.md` |
| User guides    | `docs/user-guide/*.md`    |
| Tutorials      | `docs/tutorials/*.md`     |

---

## 5. Naming and Organization Conventions

### File Naming Patterns

| Type           | Convention                         | Example                      |
| -------------- | ---------------------------------- | ---------------------------- |
| Python modules | `snake_case.py`                    | `circuit_breaker.py`         |
| Test files     | `test_<module>.py`                 | `test_rollback.py`           |
| Configuration  | `snake_case.yaml`                  | `default.yaml`               |
| Shell scripts  | `snake_case.sh`                    | `quick-install.sh`           |
| Documentation  | `kebab-case.md` or `UPPER_CASE.md` | `user-guide.md`, `README.md` |

### Class Naming Patterns

| Type             | Convention        | Example               |
| ---------------- | ----------------- | --------------------- |
| Regular classes  | `PascalCase`      | `ConfigManager`       |
| Module classes   | `*Module` suffix  | `DockerModule`        |
| Manager classes  | `*Manager` suffix | `RollbackManager`     |
| Error classes    | `*Error` suffix   | `ConfiguratorError`   |
| Abstract classes | No prefix         | `ConfigurationModule` |

### Function/Method Naming

| Type            | Convention           | Example                                   |
| --------------- | -------------------- | ----------------------------------------- |
| Public methods  | `snake_case`         | `install_packages()`                      |
| Private methods | `_snake_case`        | `_execute_action()`                       |
| CLI commands    | `kebab-case` (Click) | `@cli.command("check-system")`            |
| Test functions  | `test_<description>` | `test_rollback_executes_in_reverse_order` |

### Directory Naming

| Type                | Convention        | Example               |
| ------------------- | ----------------- | --------------------- |
| Python packages     | `snake_case`      | `configurator`        |
| Feature directories | `snake_case`      | `cis_checks`          |
| Tier directories    | `tier<N>_<level>` | `tier1_critical`      |
| Test categories     | `snake_case`      | `unit`, `integration` |

### Namespace Mapping

```python
# File: configurator/core/rollback.py
# Namespace: from configurator.core.rollback import RollbackManager

# File: configurator/modules/docker.py
# Namespace: from configurator.modules.docker import DockerModule

# File: configurator/utils/circuit_breaker.py
# Namespace: from configurator.utils.circuit_breaker import CircuitBreaker
```

---

## 6. Navigation and Development Workflow

### Entry Points

| Entry Point   | Purpose          | Location                     |
| ------------- | ---------------- | ---------------------------- |
| CLI           | Main application | `configurator/cli.py:main()` |
| Module entry  | `python -m`      | `configurator/__main__.py`   |
| Wizard        | Interactive TUI  | `configurator/wizard.py`     |
| Quick install | Shell bootstrap  | `quick-install.sh`           |

### Common Development Tasks

#### Adding a New Feature Module

1. Create `configurator/modules/<feature>.py`
2. Inherit from `ConfigurationModule`
3. Implement `validate()`, `configure()`, `verify()`
4. Register in `configurator/modules/__init__.py`
5. Add tests in `tests/unit/test_<feature>.py`
6. Update `config/default.yaml` with configuration options

#### Adding a New Utility

1. Create function/class in `configurator/utils/<utility>.py`
2. Export in `configurator/utils/__init__.py`
3. Add unit tests in `tests/unit/test_<utility>.py`

#### Adding a New Validator

1. Choose tier: `tier1_critical`, `tier2_high`, or `tier3_medium`
2. Create `configurator/validators/<tier>/<validator>.py`
3. Inherit from `BaseValidator`
4. Register in tier's `__init__.py`

#### Adding CLI Commands

1. Add command function to `configurator/cli.py`
2. Use `@cli.command()` or `@<group>.command()` decorator
3. Add help text and parameter documentation

### Dependency Patterns

```
┌─────────────────────────────────────────────────────────────┐
│ cli.py ──────────────────────────────────────────────────── │
│    │                                                         │
│    ├── core/installer.py                                    │
│    │      ├── core/container.py (DI)                        │
│    │      ├── core/rollback.py                              │
│    │      └── modules/*.py (feature modules)                │
│    │              └── modules/base.py                       │
│    │                     ├── utils/command.py               │
│    │                     ├── utils/circuit_breaker.py       │
│    │                     └── security/input_validator.py    │
│    │                                                         │
│    └── config.py                                            │
│           └── config_schema.py (Pydantic)                   │
└─────────────────────────────────────────────────────────────┘
```

### Content Statistics

| Directory                | Files | Lines (est.) | Purpose         |
| ------------------------ | ----- | ------------ | --------------- |
| `configurator/`          | 177   | ~25,000      | Main package    |
| `configurator/modules/`  | 24    | ~8,000       | Feature modules |
| `configurator/core/`     | 34    | ~5,000       | Orchestration   |
| `configurator/security/` | 28    | ~7,000       | Security        |
| `tests/`                 | 178   | ~15,000      | Test suite      |
| `docs/`                  | 112   | ~20,000      | Documentation   |

---

## 7. Build and Output Organization

### Build Configuration

| File                      | Purpose                     |
| ------------------------- | --------------------------- |
| `pyproject.toml`          | Package build configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks            |
| `mkdocs.yml`              | Documentation build         |
| `pytest.ini`              | Test configuration          |

### Output Structure

| Output        | Location   | Generated By        |
| ------------- | ---------- | ------------------- |
| Built package | `dist/`    | `python -m build`   |
| Documentation | `site/`    | `mkdocs build`      |
| Test coverage | `htmlcov/` | `pytest --cov`      |
| Type checking | (stdout)   | `mypy configurator` |

### Scripts Organization

| Script Type  | Location                 | Purpose               |
| ------------ | ------------------------ | --------------------- |
| Validation   | `scripts/validate_*.sh`  | Phase validation      |
| Test runners | `scripts/run_*_tests.sh` | Test execution        |
| Deployment   | `scripts/deploy*.sh`     | Deployment automation |
| Tools        | `tools/*.py`             | Development utilities |

---

## 8. Python-Specific Organization

### Package Structure

```python
# configurator/__init__.py
"""Debian VPS Configurator - Main package."""
from configurator.__version__ import __version__
from configurator.config import ConfigManager
from configurator.exceptions import ConfiguratorError

__all__ = ["__version__", "ConfigManager", "ConfiguratorError"]
```

### Import Conventions

```python
# Standard library first
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
import yaml
from rich.console import Console

# Local imports (relative within package)
from configurator.core.rollback import RollbackManager
from configurator.exceptions import ModuleExecutionError
```

### Package Exports

Each subpackage has an `__init__.py` that exports public API:

```python
# configurator/utils/__init__.py
from configurator.utils.command import run_command, CommandResult
from configurator.utils.file import write_file, read_file
from configurator.utils.circuit_breaker import CircuitBreaker

__all__ = ["run_command", "CommandResult", "write_file", "read_file", "CircuitBreaker"]
```

### Resource Organization

| Resource Type | Location                                         |
| ------------- | ------------------------------------------------ |
| YAML configs  | `config/*.yaml`, `configurator/rbac/roles.yaml`  |
| Security data | `configurator/security/checksums.yaml`           |
| Templates     | Inline as strings or `configurator/*/templates/` |

---

## 9. Extension and Evolution

### Extension Points

#### Adding New Modules

```
configurator/modules/
├── base.py              # Inherit from this
├── your_new_module.py   # Add here
└── __init__.py          # Register export
```

#### Adding New Validators

```
configurator/validators/
├── tier1_critical/      # Critical checks
├── tier2_high/          # Important checks
└── tier3_medium/        # Nice-to-have checks
```

#### Adding Plugins

```
configurator/plugins/
├── __init__.py
└── your_plugin/
    ├── __init__.py
    └── implementation.py
```

### Scalability Patterns

1. **Module Decomposition** — Large modules can be split into submodules
2. **Layer Separation** — New layers can be added (e.g., `api/` for REST API)
3. **Configuration Profiles** — New profiles in `config/profiles/`
4. **Test Categories** — New test directories in `tests/`

### Refactoring Approaches

1. **Extract to utils/** — Common code moves to foundation layer
2. **Split large files** — Decompose by responsibility
3. **Create subpackages** — Group related modules

---

## 10. Structure Templates

### New Feature Module Template

```
configurator/modules/<feature>.py
tests/unit/test_<feature>.py
tests/integration/test_<feature>_integration.py
docs/modules/<feature>.md
config/default.yaml (add feature section)
```

**Module File Template:**

```python
"""
<Feature> module for <purpose>.

Handles:
- <Responsibility 1>
- <Responsibility 2>
"""

from configurator.modules.base import ConfigurationModule


class <Feature>Module(ConfigurationModule):
    """<Feature> installation module."""

    name = "<Feature>"
    description = "<Description>"
    depends_on = ["system"]
    priority = 50

    def validate(self) -> bool:
        """Validate prerequisites."""
        return True

    def configure(self) -> bool:
        """Configure <feature>."""
        self.logger.info("Installing <feature>...")
        # Implementation
        return True

    def verify(self) -> bool:
        """Verify installation."""
        return True
```

### New Validator Template

```
configurator/validators/<tier>/<validator_name>.py
tests/validation/test_<validator_name>.py
```

**Validator File Template:**

```python
"""<Validator Name> validator."""

from configurator.validators.base import BaseValidator, ValidationResult


class <ValidatorName>Validator(BaseValidator):
    """Validates <what>."""

    name = "<validator_name>"
    description = "<Description>"

    def validate(self) -> ValidationResult:
        """Run validation."""
        # Implementation
        return ValidationResult(passed=True, message="OK")
```

### New Utility Template

```
configurator/utils/<utility>.py
tests/unit/test_<utility>.py
```

### New Test Template

```python
"""Tests for <module>."""

import pytest
from configurator.<path> import <Class>


class Test<Class>:
    """Tests for <Class>."""

    def test_<behavior>(self):
        """Test <expected behavior>."""
        # Arrange
        # Act
        # Assert
        pass
```

---

## 11. Structure Enforcement

### Structure Validation

| Tool           | Purpose                  | Configuration             |
| -------------- | ------------------------ | ------------------------- |
| **Ruff**       | Import ordering, linting | `pyproject.toml`          |
| **MyPy**       | Type checking            | `pyproject.toml`          |
| **Pre-commit** | Git hooks                | `.pre-commit-config.yaml` |
| **pytest**     | Test discovery           | `pytest.ini`              |

### Linting Rules

```toml
# pyproject.toml
[tool.ruff]
select = ["E", "F", "I", "UP"]  # Includes import sorting
line-length = 100

[tool.ruff.lint.isort]
known-first-party = ["configurator"]
```

### Documentation Practices

1. **Architectural decisions** — `docs/architecture/decisions/`
2. **Structure changes** — Update this blueprint
3. **API changes** — `docs/api-reference/`
4. **Module documentation** — Docstrings + `docs/modules/`

### Structure Evolution History

| Version | Change                                   | Date    |
| ------- | ---------------------------------------- | ------- |
| v1.0    | Initial structure                        | 2024    |
| v2.0    | Added validators/, reorganized security/ | 2025    |
| v2.0    | Added tiered validators                  | 2026-01 |

---

## Appendix: Quick Reference

### Find Files By Purpose

| I need to...         | Look in...                       |
| -------------------- | -------------------------------- |
| Add a CLI command    | `configurator/cli.py`            |
| Add a feature        | `configurator/modules/`          |
| Add a utility        | `configurator/utils/`            |
| Add validation       | `configurator/validators/tier*/` |
| Add security feature | `configurator/security/`         |
| Write tests          | `tests/<category>/`              |
| Update docs          | `docs/`                          |
| Configure build      | `pyproject.toml`                 |

### File Count Summary

| Directory       | Count |
| --------------- | ----- |
| `configurator/` | 177   |
| `tests/`        | 178   |
| `docs/`         | 112   |
| `scripts/`      | 30    |
| `.github/`      | 96    |
| **Total**       | ~600  |

---

_Last updated: 2026-01-17_
_Maintained by: Development Team_
