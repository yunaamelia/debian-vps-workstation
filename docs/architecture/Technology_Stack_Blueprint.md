# Technology Stack Blueprint

**Generated:** January 16, 2026
**Project:** Debian VPS Configurator v2.0
**Primary Language:** Python 3.11+
**Architecture:** Modular Plugin-Based Layered
**License:** MIT

---

## Table of Contents

1. [Technology Stack Overview](#technology-stack-overview)
2. [Core Dependencies](#core-dependencies)
3. [Development Tools](#development-tools)
4. [Technology Decision Context](#technology-decision-context)
5. [Python-Specific Implementation Details](#python-specific-implementation-details)
6. [Architecture Patterns & Conventions](#architecture-patterns--conventions)
7. [Usage Examples & Implementation Patterns](#usage-examples--implementation-patterns)
8. [Technology Integration Map](#technology-integration-map)
9. [Blueprint for New Code Implementation](#blueprint-for-new-code-implementation)

---

## Technology Stack Overview

### Language & Runtime

| Component      | Version                  | Purpose                      | Status     |
| -------------- | ------------------------ | ---------------------------- | ---------- |
| **Python**     | 3.11+ (3.12 recommended) | Primary programming language | ✅ Current |
| **Setuptools** | ≥61.0                    | Package building             | ✅ Current |
| **Wheel**      | Latest                   | Distribution format          | ✅ Current |

### Framework & Core Technologies

| Layer               | Technology | Version | Purpose                                  |
| ------------------- | ---------- | ------- | ---------------------------------------- |
| **CLI Framework**   | Click      | ≥8.1.0  | Command-line interface (106+ commands)   |
| **Terminal Output** | Rich       | ≥13.0.0 | Beautiful terminal formatting & progress |
| **Terminal UI**     | Textual    | ≥0.40.0 | Interactive TUI wizard interface         |
| **Configuration**   | PyYAML     | ≥6.0    | YAML configuration parsing               |
| **API Client**      | Requests   | ≥2.31.0 | HTTP client for API interactions         |
| **SSH/SFTP**        | Paramiko   | ≥3.3.0  | SSH operations and key management        |
| **Templating**      | Jinja2     | ≥3.1.0  | Template rendering for configurations    |
| **Validation**      | Pydantic   | ≥2.0.0  | Data validation and serialization        |
| **Graph Analysis**  | NetworkX   | ≥3.0    | Dependency graph resolution              |

### Security & Cryptography

| Technology       | Version | Purpose                             |
| ---------------- | ------- | ----------------------------------- |
| **Cryptography** | ≥41.0.0 | SSL/TLS, encryption, key management |
| **bcrypt**       | ≥5.0.0  | Password hashing                    |
| **PyNaCl**       | ≥1.6.0  | Elliptic curve cryptography         |
| **pyotp**        | ≥2.9.0  | TOTP/HOTP for 2FA                   |
| **qrcode**       | ≥8.0    | QR code generation for MFA seeds    |

### Additional Utilities

| Technology     | Version | Purpose                       |
| -------------- | ------- | ----------------------------- |
| **invoke**     | ≥2.2.0  | Task execution and automation |
| **matplotlib** | ≥3.9.3  | Data visualization            |

---

## Core Dependencies

### Detailed Dependency Analysis

#### Click (≥8.1.0) - CLI Framework

```toml
[purpose]
- Command-line interface development
- Command routing and parameter handling
- Help text generation
- Version display

[usage]
- Base framework for all 106+ CLI commands
- Parameter validation and type conversion
- Option and argument handling
- Command grouping and nesting

[location]
- configurator/cli.py (main entry point)
- configurator/cli_monitoring.py (monitoring commands)
```

#### Rich (≥13.0.0) - Terminal Output

```toml
[purpose]
- Formatted terminal output
- Progress bar display
- Table rendering
- Color and style management

[usage]
- Installation progress display
- Multi-column formatted output
- Error and warning messages
- Status indicators

[location]
- configurator/core/reporter.py
- Throughout CLI for user feedback
```

#### Textual (≥0.40.0) - Terminal UI

```toml
[purpose]
- Interactive terminal user interface (TUI)
- Widget-based interface building
- Event handling and reactive updates
- Full-screen terminal applications

[usage]
- Interactive wizard (configurator/wizard.py)
- Configuration selection interface
- Progress and status displays

[location]
- configurator/wizard.py (main TUI wizard)
```

#### PyYAML (≥6.0.0) - Configuration

```toml
[purpose]
- YAML parsing and generation
- Configuration file handling
- Data serialization

[usage]
- Load configuration from YAML files
- Parse default.yaml, profile configs
- Generate configuration output

[files]
- config/default.yaml (220+ lines of configuration)
- config/profiles/beginner.yaml
- config/profiles/intermediate.yaml
- config/profiles/advanced.yaml

[location]
- configurator/config.py (configuration management)
```

#### Paramiko (≥3.3.0) - SSH Operations

```toml
[purpose]
- SSH protocol implementation
- Key-based authentication
- Remote command execution
- SFTP file transfer

[usage]
- SSH key management
- Remote host connections
- Secure command execution
- File synchronization

[location]
- configurator/security/ssh_manager.py (SSH management)
- configurator/security/ssh_hardening.py (SSH hardening)
```

#### Pydantic (≥2.0.0) - Data Validation

```toml
[purpose]
- Data validation using type hints
- Serialization/deserialization
- Settings management
- Error reporting

[usage]
- Validate configuration data
- Type-safe data models
- API request/response validation
- Settings configuration

[location]
- configurator/config_schema.py (schema definitions)
- Throughout for type validation
```

#### Cryptography (≥41.0.0) - Security

```toml
[purpose]
- SSL/TLS certificate handling
- Encryption/decryption
- Key generation and management
- Signature verification

[usage]
- SSL certificate validation
- Data encryption
- SSH key handling
- Checksum verification

[location]
- configurator/security/certificate_manager.py
- configurator/security/supply_chain.py
```

#### NetworkX (≥3.0) - Graph Analysis

```toml
[purpose]
- Dependency graph resolution
- Module dependency analysis
- Topological sorting

[usage]
- Resolve module dependencies
- Detect circular dependencies
- Plan installation order

[location]
- configurator/core/dependencies.py
```

---

## Development Tools

### Testing Framework

| Tool            | Version | Purpose                |
| --------------- | ------- | ---------------------- |
| **pytest**      | ≥7.4.0  | Testing framework      |
| **pytest-cov**  | ≥4.1.0  | Coverage reporting     |
| **pytest-mock** | ≥3.11.0 | Mock/patch utilities   |
| **coverage**    | ≥7.0.0  | Code coverage analysis |

**Configuration:** `pytest.ini` with markers for slow, integration, and destructive tests

**Target Coverage:** 85%+ of codebase

**Test Organization:**

```
tests/
├── unit/          # Fast, isolated logic tests
├── integration/   # Component interaction tests
├── e2e/          # End-to-end workflow tests
├── modules/      # Module-specific tests
├── security/     # Security validation tests
├── validation/   # System validation (400+ checks)
└── fixtures/     # Shared test data and mocks
```

### Code Quality Tools

| Tool           | Version  | Purpose             |
| -------------- | -------- | ------------------- |
| **ruff**       | ≥0.1.0   | Fast Python linter  |
| **mypy**       | ≥1.5.0   | Static type checker |
| **black**      | ≥24.10.0 | Code formatter      |
| **isort**      | ≥5.13.2  | Import sorter       |
| **pylint**     | ≥3.3.2   | Code analyzer       |
| **pre-commit** | ≥4.0.1   | Git hooks framework |

**Ruff Configuration:**

```toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "B", "I"]  # Pycodestyle, Pyflakes, flake8-bugbear, isort
ignore = ["E501", "E203", "F841", "E303"]  # Long lines, whitespace, etc.
```

**MyPy Configuration:**

```toml
python_version = "3.11"
check_untyped_defs = true
disallow_untyped_defs = false
warn_return_any = false
warn_unused_ignores = true
ignore_missing_imports = true
```

### Type Stubs

| Package            | Version |
| ------------------ | ------- |
| **types-PyYAML**   | ≥6.0.0  |
| **types-requests** | ≥2.31.0 |
| **types-paramiko** | ≥3.3.0  |

---

## Technology Decision Context

### Why Python 3.11+?

**Rationale:**

- **Speed:** 10-20% faster than 3.10
- **Type Features:** Enhanced type hint syntax
- **Standard Library:** Better built-in utilities
- **Compatibility:** Wide ecosystem support
- **Production Maturity:** Stable and battle-tested

**Version Constraints:**

- Minimum: 3.11 (required for project structure)
- Target: 3.12+ (recommended for latest features)
- Maximum: No hard upper limit (future compatible)

### Why These Framework Choices?

#### Click for CLI

**Alternatives Considered:** argparse, typer
**Why Click:**

- Mature and battle-tested
- Extensive plugin ecosystem
- Clean decorator-based API
- Excellent documentation
- Large community support

#### Rich for Output

**Alternatives Considered:** colorama, termcolor
**Why Rich:**

- Modern terminal capabilities
- Beautiful default styling
- Progress bars and tables
- Live display updates
- Active maintenance

#### Textual for TUI

**Alternatives Considered:** curses, blessed, urwid
**Why Textual:**

- Built on Rich (consistency)
- Event-driven architecture
- Responsive design
- Widget library
- Modern Python patterns

#### Pydantic for Validation

**Alternatives Considered:** marshmallow, attrs
**Why Pydantic:**

- Type hint first approach
- Excellent error messages
- V2 with breaking changes (intentional modernization)
- Great performance
- Extensive plugins

### Technology Constraints & Boundaries

1. **No Async/Await**

   - Project uses `ThreadPoolExecutor` for parallelism
   - Not based on async event loop
   - Simplifies deployment and debugging

2. **No ORM**

   - Configuration-based (YAML)
   - Filesystem operations
   - SSH commands (not database)
   - Keeps lightweight

3. **No Web Framework**

   - CLI-only application
   - No REST API server
   - Single-machine focus
   - Reduces dependencies

4. **Thread-Safe Only**
   - Uses threading locks for shared resources
   - Not fully async-safe
   - Suitable for current scale

### Technology Upgrade Paths

| Technology   | Current | Upgrade Path         | Timeline |
| ------------ | ------- | -------------------- | -------- |
| **Python**   | 3.11+   | 3.13+ (2025)         | Q2 2025  |
| **Click**    | 8.1.0   | 8.2+ stable          | Q3 2025  |
| **Pydantic** | 2.0+    | 2.2+ (validators v2) | Q4 2025  |
| **Rich**     | 13.0+   | 14.0+ (breaking)     | Q3 2025  |
| **Textual**  | 0.40+   | 1.0 (stable API)     | Q2 2025  |

---

## Python-Specific Implementation Details

### Python Language Features Used

#### Type Hints (100% Coverage Required)

```python
# All public APIs must have type hints
from typing import Any, Dict, List, Optional

def configure(self, config: Dict[str, Any]) -> bool:
    """Configure module with type hints on inputs and output."""
    pass

# Generic types
def process_items(items: List[str]) -> Dict[str, int]:
    """Work with collections with explicit types."""
    pass

# Optional values
def find_user(username: Optional[str] = None) -> Optional[User]:
    """Handle optional parameters and returns."""
    pass
```

#### Dataclasses (Preferred Over Classes)

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    """User data model using dataclass."""
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
```

#### Abstract Base Classes

```python
from abc import ABC, abstractmethod

class ConfigurationModule(ABC):
    """Abstract base for all configuration modules."""

    @abstractmethod
    def validate(self) -> bool:
        """Validate prerequisites."""
        pass

    @abstractmethod
    def configure(self) -> bool:
        """Execute configuration."""
        pass
```

#### Context Managers

```python
from contextlib import contextmanager

@contextmanager
def transaction(self):
    """Transactional context manager."""
    self.logger.info("Starting transaction")
    try:
        yield
        self.logger.info("Committing transaction")
    except Exception as e:
        self.logger.error(f"Rolling back: {e}")
        raise
```

### Project Structure

```
debian-vps-workstation/
├── configurator/           # Main package (104 Python files)
│   ├── __init__.py         # Package initialization + version export
│   ├── __main__.py         # Entry point (python -m configurator)
│   ├── cli.py              # CLI commands (3,509 lines, 106 commands)
│   ├── cli_monitoring.py   # Monitoring commands
│   ├── wizard.py           # Interactive TUI
│   ├── config.py           # Configuration management
│   ├── config_schema.py    # Pydantic schema definitions
│   ├── constants.py        # Global constants
│   ├── exceptions.py       # Custom exception hierarchy
│   ├── logger.py           # Logging configuration
│   ├── core/               # Orchestration layer
│   ├── modules/            # Feature modules (24 modules)
│   ├── security/           # Security subsystem
│   ├── rbac/               # Role-based access control
│   ├── users/              # User management
│   ├── utils/              # Utility functions
│   └── observability/      # Monitoring utilities
│
├── tests/                  # Test package (133 files)
├── docs/                   # Documentation (59 files)
├── scripts/                # Deployment & validation
├── tools/                  # Development utilities
└── config/                 # Configuration files
```

### Virtual Environment & Package Management

**Setup Process:**

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

**Package Installation (pyproject.toml):**

```toml
[project.scripts]
vps-configurator = "configurator.cli:main"
```

Creates CLI command: `vps-configurator` available system-wide

---

## Architecture Patterns & Conventions

### Naming Conventions

#### Classes (PascalCase)

```python
class ConfigurationModule(ABC): ...
class CircuitBreakerManager: ...
class RBACManager: ...
class SSHKeyManager: ...
```

#### Functions/Methods (snake_case)

```python
def install_packages_resilient(self, packages: List[str]) -> bool:
    """Install packages with retry logic."""
    pass

def validate_input(self, value: str) -> bool:
    """Validate user input."""
    pass

def get_config(self, key: str, default: Any = None) -> Any:
    """Get configuration value."""
    pass
```

#### Constants (UPPER_SNAKE_CASE)

```python
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
ROLLBACK_STATE_FILE = Path("/var/lib/vps-configurator/rollback.state")
CIS_BENCHMARK_VERSION = "1.4.0"
```

#### Private Members (Leading Underscore)

```python
def _validate_prerequisites(self) -> bool:
    """Private validation method."""
    pass

_internal_cache = {}

class _InternalHelper:
    """Private helper class."""
    pass
```

#### Module-Level Variables (snake_case)

```python
logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()
config_manager = ConfigManager()
```

### Import Organization

```python
# Standard library (alphabetical)
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party (alphabetical)
import click
import yaml
from rich.console import Console

# Local (by layer, then alphabetical)
from configurator.core.installer import Installer
from configurator.exceptions import ModuleExecutionError, PrerequisiteError
from configurator.utils.command import run_command
```

**Enforced by:** Ruff with isort plugin

### Error Handling Pattern

```python
# Custom exceptions with WHAT/WHY/HOW format
class ModuleExecutionError(Exception):
    """Module execution failed."""

    def __init__(self, what: str, why: str, how: str):
        self.what = what  # What happened
        self.why = why    # Why it happened
        self.how = how    # How to fix
        super().__init__(f"{what}\n\nWhy: {why}\n\nHow: {how}")

# Usage
raise ModuleExecutionError(
    what="Failed to install Docker",
    why="Package repository unreachable",
    how="1. Check network connectivity\n2. Check firewall rules\n3. Try again"
)
```

### Dependency Injection Pattern

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
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.rollback_manager = rollback_manager
        self.dry_run_manager = dry_run_manager
        self.circuit_breaker_manager = circuit_breaker_manager
        self.package_cache_manager = package_cache_manager
```

### Configuration Access Pattern

```python
# Use dot notation for nested access
hostname = self.get_config("system.hostname", default="dev-workstation")
enabled = self.get_config("languages.python.enabled", default=True)
version = self.get_config("software.docker.version", default="latest")

# Raises ConfigurationError if missing (no default)
required = self.get_config("security.admin_user")
```

---

## Usage Examples & Implementation Patterns

### CLI Command Implementation

```python
import click
from configurator.config import ConfigManager
from configurator.core.installer import Installer

@click.command()
@click.option('--profile', type=click.Choice(['beginner', 'intermediate', 'advanced']),
              help='Installation profile')
@click.option('--dry-run', is_flag=True, help='Simulate without changes')
@click.option('-v', '--verbose', count=True, help='Verbosity level')
def install(profile: str, dry_run: bool, verbose: int):
    """Install and configure system."""
    config = ConfigManager(profile=profile)
    installer = Installer(config=config, dry_run=dry_run, verbose=verbose)

    if installer.validate():
        installer.install()
        click.echo("✓ Installation complete")
    else:
        raise click.ClickException("Validation failed")
```

### Module Implementation Pattern

```python
from configurator.modules.base import ConfigurationModule

class DockerModule(ConfigurationModule):
    name = "Docker"
    priority = 50
    depends_on = ["system", "security"]

    def validate(self) -> bool:
        """Validate Docker prerequisites."""
        if self.command_exists("docker"):
            self.logger.info("Docker already installed")
            return False

        if not self.has_disk_space(10):  # GB
            raise PrerequisiteError(
                what="Insufficient disk space",
                why="Docker requires 10GB",
                how="Free up disk space"
            )

        return True

    def configure(self) -> bool:
        """Install and configure Docker."""
        try:
            self._install_packages()
            self._configure_daemon()
            self._setup_permissions()
            return True
        except Exception as e:
            raise ModuleExecutionError(
                what="Docker setup failed",
                why=str(e),
                how="Check logs and retry"
            )

    def verify(self) -> bool:
        """Verify Docker installation."""
        return self.run("docker --version", check=False).success

    def _install_packages(self):
        """Install Docker packages."""
        self.install_packages_resilient(["docker-ce", "docker-compose"])
        self.rollback_manager.add_package_remove(["docker-ce", "docker-compose"])
```

### Service Layer Pattern

```python
class RollbackManager:
    """Transaction-like rollback for system changes."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.actions: List[RollbackAction] = []

    def add_command(self, rollback_cmd: str) -> None:
        """Register command to rollback on failure."""
        self.actions.append(RollbackAction(
            type="command",
            command=rollback_cmd,
            timestamp=datetime.now()
        ))

    def add_package_remove(self, packages: List[str]) -> None:
        """Register packages to remove on rollback."""
        self.actions.append(RollbackAction(
            type="package_remove",
            packages=packages,
            timestamp=datetime.now()
        ))

    def execute_rollback(self) -> bool:
        """Execute all registered rollback actions."""
        for action in reversed(self.actions):
            try:
                if action.type == "command":
                    run_command(action.command)
                elif action.type == "package_remove":
                    self._remove_packages(action.packages)
            except Exception as e:
                self.logger.error(f"Rollback failed: {e}")
                return False

        return True
```

### Validation Pattern

```python
from pydantic import BaseModel, Field, field_validator

class UserConfig(BaseModel):
    """Validated user configuration."""
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    shell: str = Field(default="/bin/bash")
    groups: List[str] = Field(default_factory=list)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be lowercase alphanumeric + dash."""
        if not re.match(r'^[a-z][a-z0-9_-]{2,31}$', v):
            raise ValueError("Invalid username format")
        return v
```

### Logging Pattern

```python
import logging

logger = logging.getLogger(__name__)

def process_installation(module: ConfigurationModule) -> bool:
    """Process module installation with logging."""
    logger.debug(f"Starting {module.name} installation")

    try:
        if module.validate():
            logger.info(f"Prerequisites met for {module.name}")
            module.configure()
            logger.info(f"✓ {module.name} configured")
            return True
        else:
            logger.warning(f"Skipping {module.name} (already installed)")
            return False
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        raise
```

---

## Technology Integration Map

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User Input (CLI/TUI)                                        │
│ ├─ Click: Command parsing                                  │
│ └─ Textual: Interactive selection                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ Configuration Layer                                         │
│ ├─ PyYAML: Load config files                               │
│ ├─ Pydantic: Validate data                                 │
│ └─ ConfigManager: Merge profiles                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ Orchestration Layer                                         │
│ ├─ Installer: Coordinate modules                          │
│ ├─ RollbackManager: Track changes                          │
│ ├─ CircuitBreaker: Prevent cascades                        │
│ └─ ThreadPoolExecutor: Parallel execution                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ Feature Modules (24 modules)                               │
│ ├─ System configuration                                    │
│ ├─ Security hardening                                      │
│ ├─ Developer tools                                         │
│ └─ Infrastructure setup                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ System Operations (via Paramiko/SSH)                        │
│ ├─ Package installation (APT)                              │
│ ├─ System configuration                                    │
│ ├─ Service management                                      │
│ └─ User management                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ Monitoring & Audit                                          │
│ ├─ Rich: Progress reporting                                │
│ ├─ Audit logging                                           │
│ └─ Metrics collection                                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Dependencies

```
Click (CLI)
├─→ ConfigManager (config.py)
│   └─→ PyYAML (parse YAML)
│       └─→ Pydantic (validate)
├─→ Installer (core/installer.py)
│   ├─→ RollbackManager
│   ├─→ CircuitBreakerManager
│   ├─→ ThreadPoolExecutor
│   └─→ ConfigurationModule(s)
│       ├─→ Paramiko (SSH)
│       ├─→ Cryptography (SSL/crypto)
│       └─→ Rich (output)

Textual (TUI Wizard)
└─→ Click (commands)
    └─→ [same as above]
```

---

## Blueprint for New Code Implementation

### Adding a New CLI Command

**Location:** `configurator/cli.py`

```python
@click.group()
def cli_group():
    """Command group for related commands."""
    pass

@cli_group.command()
@click.argument('username')
@click.option('--email', required=True, help='User email address')
@click.option('--shell', default='/bin/bash', help='Login shell')
@click.pass_context
def add_user(ctx, username: str, email: str, shell: str):
    """Add a new user to the system."""
    config = ctx.obj['config']
    user_service = UserLifecycleManager(config=config)

    try:
        user_service.create_user(
            username=username,
            email=email,
            shell=shell
        )
        click.echo(f"✓ User {username} created")
    except ValidationError as e:
        raise click.BadParameter(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to create user: {e}")
```

### Adding a New Module

**Location:** `configurator/modules/<feature>.py`

```python
from configurator.modules.base import ConfigurationModule

class NewFeatureModule(ConfigurationModule):
    name = "New Feature"
    description = "Description of feature"
    depends_on = ["system", "security"]
    priority = 50
    mandatory = False

    def validate(self) -> bool:
        """Validate prerequisites."""
        # Implementation
        pass

    def configure(self) -> bool:
        """Execute configuration."""
        # Implementation
        pass

    def verify(self) -> bool:
        """Verify installation."""
        # Implementation
        pass
```

### Adding a New Service

**Location:** `configurator/core/` or `configurator/security/`

```python
from typing import Optional
import logging

class NewService:
    """Service description."""

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        rollback_manager: Optional[RollbackManager] = None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.rollback_manager = rollback_manager

    def operation(self) -> bool:
        """Perform operation."""
        try:
            # Implementation
            return True
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            raise
```

### Test Implementation Template

**Location:** `tests/unit/test_<module>.py`

```python
import pytest
from unittest.mock import Mock, patch

from configurator.modules.newfeature import NewFeatureModule
from configurator.exceptions import ModuleExecutionError

class TestNewFeatureModule:
    """Tests for NewFeatureModule."""

    @pytest.fixture
    def module(self):
        return NewFeatureModule(
            config={},
            logger=Mock(),
            rollback_manager=Mock()
        )

    def test_validate_success(self, module):
        """Test successful validation."""
        assert module.validate() is True

    def test_configure_success(self, module):
        """Test successful configuration."""
        assert module.configure() is True

    def test_configure_failure(self, module):
        """Test configuration failure."""
        with patch.object(module, '_install', side_effect=Exception("test")):
            with pytest.raises(ModuleExecutionError):
                module.configure()
```

### Code Quality Checklist

Before submitting code:

- ✅ Type hints on all public APIs
- ✅ Docstrings with Google format
- ✅ Ruff linting passes: `ruff check configurator/`
- ✅ Type checking passes: `mypy configurator/`
- ✅ Tests pass: `pytest tests/ -v`
- ✅ Coverage ≥85%: `pytest --cov=configurator --cov-fail-under=85`
- ✅ No circular imports
- ✅ No module-to-module imports
- ✅ Rollback actions registered
- ✅ Error messages follow WHAT/WHY/HOW format

---

## Technology Stack Summary

### Production Dependencies (10 Core)

```
pyyaml (config)
├─ click (CLI)
├─ rich (terminal)
├─ textual (TUI)
├─ requests (HTTP)
├─ paramiko (SSH)
├─ jinja2 (templates)
├─ pydantic (validation)
├─ cryptography (security)
└─ networkx (graphs)
```

### Development Dependencies (10+ Tools)

```
pytest (testing)
├─ pytest-cov (coverage)
├─ pytest-mock (mocking)
├─ coverage (analysis)
├─ ruff (linting)
├─ mypy (typing)
├─ black (formatting)
├─ isort (imports)
├─ pylint (analysis)
└─ pre-commit (git hooks)
```

### Total Footprint

- **Language:** Python 3.11+
- **Core Packages:** 10 production dependencies
- **Development Tools:** 10+ quality tools
- **Code Volume:** 104 Python files (15,000+ LOC)
- **Test Volume:** 133 test files (200+ tests)
- **Virtual Environment Size:** ~150-200 MB

### Installation Time

- Clean venv creation: ~2-3 seconds
- Dependency installation: ~10-15 seconds
- First run (imports): ~500-800 ms
- Total initial setup: ~15-30 seconds

---

## Conclusion

This technology stack represents a carefully selected set of Python tools and libraries optimized for:

✅ **Maintainability:** Type hints, linting, and formatting tools
✅ **Reliability:** Testing framework with 85%+ coverage target
✅ **Performance:** Parallel execution, caching, lazy loading
✅ **Security:** Cryptography, SSH operations, input validation
✅ **Usability:** Rich CLI with interactive TUI wizard
✅ **Extensibility:** Plugin architecture with clear boundaries

The stack prioritizes stability (mature, battle-tested libraries) while enabling modern Python patterns (type hints, dataclasses, async-compatible design).

---

**Document Version:** 1.0
**Last Updated:** January 16, 2026
**Maintainer:** Documentation Team
**Next Review:** April 16, 2026
