# Project Workflow Analysis Blueprint

**Generated:** January 16, 2026
**Project:** Debian VPS Configurator
**Technology Stack:** Python 3.12+ CLI Application
**Architecture:** Modular Plugin Architecture with DevOps Infinity Loop Integration
**Version:** 2.0
**Status:** Production-Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [DevOps Infinity Loop Integration](#2-devops-infinity-loop-integration)
3. [Project Technology Detection](#3-project-technology-detection)
4. [End-to-End Workflow Documentation](#4-end-to-end-workflow-documentation)
5. [CI/CD Pipeline Workflows](#5-cicd-pipeline-workflows)
6. [Testing Workflows](#6-testing-workflows)
7. [Deployment Workflows](#7-deployment-workflows)
8. [Monitoring & Operations Workflows](#8-monitoring--operations-workflows)
9. [Security & Compliance Workflows](#9-security--compliance-workflows)
10. [Implementation Templates](#10-implementation-templates)
11. [Common Patterns & Best Practices](#11-common-patterns--best-practices)
12. [Troubleshooting Workflows](#12-troubleshooting-workflows)

---

## 1. Executive Summary

### Project Overview

**Debian VPS Configurator** is an enterprise-grade automation system that transforms a base Debian 13 VPS into a fully-configured development workstation. The system implements a complete DevOps infinity loop covering all phases from planning through monitoring.

### Key Metrics


| Metric | Value |
|--------|-------|
| **Total Python Files** | 237 files (104 src + 133 tests) |
| **Lines of Code** | ~40,000+ lines |
| **Total Modules** | 24 configuration modules |
| **CLI Commands** | 106+ commands |
| **Test Coverage Target** | 85%+ |
| **Startup Time** | <100ms (lazy loading) |
| **Installation Time** | 15-45 min (profile dependent) |
| **Documentation** | 35 documents (~440 pages) |

### DevOps Maturity Level

- ✅ **Plan**: Comprehensive documentation & architecture blueprints
- ✅ **Code**: Modern Python 3.12+, type hints, modular design
- ✅ **Build**: Automated builds via GitHub Actions
- ✅ **Test**: Unit, integration, E2E tests with 85%+ coverage target
- ✅ **Release**: Automated releases with semantic versioning
- ✅ **Deploy**: Multiple deployment options (PyPI, source, quick-install)
- ✅ **Operate**: Health checks, rollback, dry-run capabilities
- ✅ **Monitor**: Activity monitoring, audit logging, observability

---

## 2. DevOps Infinity Loop Integration

### How This Project Implements the Complete Loop

```
┌────────────────────────────────────────────────────────────┐
│                DEVOPS INFINITY LOOP                        │
│        Debian VPS Configurator Implementation              │
└────────────────────────────────────────────────────────────┘

     ┌─────────┐
     │  PLAN   │  → docs/, Project_Architecture_Blueprint.md
     └────┬────┘    35 implementation & validation prompts
          │
     ┌────▼────┐
     │  CODE   │  → configurator/ (104 Python files)
     └────┬────┘    Git workflows, pre-commit hooks
          │
     ┌────▼────┐
     │  BUILD  │  → GitHub Actions: tests.yml
     └────┬────┘    Automated on every push/PR
          │
     ┌────▼────┐
     │  TEST   │  → tests/ (133 test files)
     └────┬────┘    Unit + Integration + E2E
          │
     ┌────▼────┐
     │ RELEASE │  → GitHub Actions: release.yml
     └────┬────┘    Semantic versioning, automated releases
          │
     ┌────▼────┐
     │ DEPLOY  │  → quick-install.sh, PyPI distribution
     └────┬────┘    Multiple deployment strategies
          │
     ┌────▼────┐
     │ OPERATE │  → RollbackManager, DryRunManager
     └────┬────┘    Health checks, incident response
          │
     ┌────▼────┐
     │ MONITOR │  → ActivityMonitor, AuditLogger
     └────┬────┘    Observability, metrics, alerting
          │
          └──────────────────────────────┐
                                         │
                    Feedback Loop ───────┘
                    (Back to PLAN)
```

### Phase-by-Phase Implementation

#### PLAN Phase

**Tools & Artifacts:**
- 📄 35 comprehensive documentation files
- 📐 Architecture blueprints (Project_Architecture_Blueprint.md)
- 📝 Implementation prompts (15 features)
- ✅ Validation prompts (400+ checks)
- 🗺️ Implementation roadmap (15-20 weeks)

**Workflow:**
1. Feature requests → GitHub Issues
2. Requirements → Implementation prompts
3. Architecture decisions → ADR (Architectural Decision Records)
4. Success criteria → Validation procedures

#### CODE Phase

**Tools & Patterns:**
- **Version Control:** Git with feature branching
- **Code Quality:**
  - Ruff (linting)
  - Mypy (type checking)
  - Pre-commit hooks (automated checks)
- **Patterns:**
  - Plugin architecture (24 modules)
  - Dependency injection (Container pattern)
  - Template method (base.ConfigurationModule)
  - Circuit breaker (resilience)
  - Lazy loading (performance)

**Workflow:**
```python
# Example: Adding a new configuration module
# 1. Create module inheriting from base
class NewModule(ConfigurationModule):
    name = "new-feature"
    priority = 50

    def validate(self) -> bool:
        """Check prerequisites"""

    def configure(self) -> bool:
        """Execute configuration"""

    def verify(self) -> bool:
        """Verify installation"""
```

#### BUILD Phase

**Automated Build Pipeline:**


```yaml
# .github/workflows/tests.yml - Automated on push/PR
jobs:
  lint:  # Code quality checks
    - black (formatting)
    - isort (import ordering)
    - pylint (static analysis)
    - flake8 (style guide)
    - mypy (type checking)

  test:  # Multi-version testing
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - Install dependencies
      - Run pytest with coverage
      - Upload coverage reports

  build:  # Package validation
    - Build wheel/sdist
    - Check with twine
    - Upload artifacts
```

**Build Triggers:**
- Every push to main/develop
- Every pull request
- Manual workflow dispatch

#### TEST Phase

**Test Strategy (Pyramid):**

```
         ┌──────────┐
        ╱  E2E (10) ╲      ← Slow, comprehensive
       ╱──────────────╲
      ╱ Integration(50)╲   ← Medium speed, service boundaries
     ╱────────────────────╲
    ╱   Unit Tests (200)   ╲  ← Fast, isolated
   ╱────────────────────────╲
```

**Test Categories:**
- **Unit Tests** (`tests/unit/`): 200+ tests, <1s each
- **Integration Tests** (`tests/integration/`): 50+ tests, service interactions
- **E2E Tests** (`tests/e2e/`): 10+ tests, full workflows
- **Performance Tests** (`tests/performance/`): Load, stress testing
- **Security Tests** (`tests/security/`): Vulnerability scanning

**Test Execution:**
```bash
# Fast unit tests (CI)
pytest tests/unit/ -v --cov=configurator

# Integration tests (slower)
pytest tests/integration/ -v -m integration

# Full test suite
pytest tests/ -v --cov=configurator --cov-report=xml
```

#### RELEASE Phase

**Semantic Versioning:**
- **Major (v2.0.0)**: Breaking API changes
- **Minor (v1.1.0)**: New features, backward compatible
- **Patch (v1.0.1)**: Bug fixes

**Automated Release Workflow:**

```yaml
# .github/workflows/release.yml - Triggered by git tags
on:
  push:
    tags: ["v*"]

steps:
  1. Build package (wheel + sdist)
  2. Create release bundle (quick-install.sh + config/)
  3. Generate release notes
  4. Create GitHub release
  5. Upload artifacts (dist/ + tarball)
  6. (Future) Publish to PyPI
```

**Release Checklist:**
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Tag created: `git tag v1.0.0`

#### DEPLOY Phase

**Deployment Strategies:**

1. **Quick Install (Recommended):**
```bash
curl -sSL https://raw.githubusercontent.com/yunaamelia/debian-vps-workstation/main/quick-install.sh | bash
```
   - Checks OS compatibility
   - Installs system dependencies
   - Sets up virtual environment
   - Installs Python packages
   - Verifies installation

2. **PyPI Install (Future):**
```bash
pip install debian-vps-configurator
vps-configurator install --profile advanced
```

3. **Source Install:**
```bash
git clone <repo>
./quick-install.sh
source venv/bin/activate
pip install -e .
```

**Deployment Features:**
- ✅ **Dry-run mode**: Preview changes without applying
- ✅ **Rollback**: Automatic rollback on failures
- ✅ **Circuit breaker**: Protects against cascading failures
- ✅ **Health checks**: Pre/post deployment validation

#### OPERATE Phase

**Operational Excellence:**

**1. Health Monitoring:**
```python
# Built-in health checks
class SystemValidator:
    def check_prerequisites(self):
        - OS compatibility (Debian 11+, Ubuntu 20.04+)
        - Python version (3.9+)
        - Disk space (50GB+)
        - Memory (4GB+)
        - Network connectivity
```

**2. Rollback Capabilities:**
```python
class RollbackManager:
    def add_package_remove(packages)      # APT rollback
    def add_service_stop(service)         # Service rollback
    def add_file_restore(backup, original)# File rollback
    def add_command(rollback_cmd)         # Custom rollback
```

**3. Dry-Run Mode:**
```bash
# Preview changes without applying
vps-configurator install --dry-run --profile advanced
```

**4. Circuit Breaker:**
```python
# Protects against repeated failures
class CircuitBreakerManager:
    - Open: Block requests after threshold
    - Half-Open: Test recovery
    - Closed: Normal operation
```

**5. Incident Response:**
```bash
# Troubleshooting tools
vps-configurator verify           # Check installation
vps-configurator rollback         # Undo changes
scripts/diagnose.py               # System diagnostics
scripts/validate_phase*.sh        # Phase validation
```

#### MONITOR Phase

**Observability Stack:**

**1. Activity Monitoring:**
```python
class ActivityMonitor:
    - Track user logins/logouts
    - Monitor sudo command execution
    - Record file access patterns
    - Detect anomalies
    - Generate compliance reports
```

**2. Audit Logging:**
```python
class AuditLogger:
    # Comprehensive audit trail
    - What: Action performed
    - Who: User/system
    - When: Timestamp
    - Where: Location/component
    - Result: Success/failure
    - Details: Full context
```

**3. File Integrity Monitoring:**
```python
class FileIntegrityMonitor:
    - Baseline critical files
    - Detect unauthorized changes
    - Alert on modifications
    - Automatic verification
```

**4. Metrics Collection:**
- Deployment frequency (DORA metric)
- Lead time for changes (DORA metric)
- Time to restore (DORA metric)
- Change failure rate (DORA metric)
- Module success rates
- Execution times
- Resource utilization

**5. Alerting:**
- Failed module installations
- Security anomalies
- Circuit breaker trips
- Rollback triggers
- File integrity violations

---

## 3. Project Technology Detection

### Language & Runtime

**Primary Language:** Python
- **Version**: 3.12+ (minimum 3.11)
- **Type System**: Full type hints with mypy validation
- **Features Used**:
  - Dataclasses for data structures
  - Type annotations (Dict, List, Optional, Any)
  - Context managers (with statements)
  - Decorators (lazy loading, retry logic)
  - Abstract base classes (ABC)
  - ThreadPoolExecutor (not async/await)

### Framework Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **CLI** | Click | 8.1+ | Command-line interface |
| **Terminal UI** | Rich | 13.0+ | Formatted console output |
| **TUI** | Textual | 0.40+ | Interactive terminal UI |
| **Configuration** | PyYAML | 6.0+ | YAML parsing |
| **Validation** | Pydantic | 2.0+ | Data validation |
| **SSH** | Paramiko | 3.3+ | Remote operations |
| **Security** | cryptography | 41.0+ | Encryption/decryption |
| **HTTP** | Requests | 2.31+ | API calls |
| **Templates** | Jinja2 | 3.1+ | Template rendering |
| **Graphs** | NetworkX | 3.0+ | Dependency resolution |
| **System** | psutil | 5.9+ | System metrics |

### Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **pytest** | Testing framework | pytest.ini |
| **ruff** | Linting & formatting | pyproject.toml |
| **mypy** | Type checking | pyproject.toml |
| **pre-commit** | Git hooks | .pre-commit-config.yaml |
| **setuptools** | Package building | pyproject.toml |

### Architecture Patterns Detected

1. **Plugin Architecture**
   - Base class: `ConfigurationModule`
   - 24 concrete modules
   - Dynamic loading via `PluginManager`

2. **Dependency Injection**
   - `Container` class for service resolution
   - Singleton pattern for shared services
   - Factory pattern for module instantiation

3. **Template Method**
   - Lifecycle: `validate()` → `configure()` → `verify()`
   - Base class defines structure
   - Subclasses implement specifics

4. **Circuit Breaker**
   - `CircuitBreakerManager` prevents cascading failures
   - States: Closed → Open → Half-Open
   - Exponential backoff retry

5. **Lazy Loading**
   - `LazyLoader` delays imports
   - Sub-100ms CLI startup time
   - Reduces memory footprint

6. **Command Pattern**
   - CLI commands encapsulate operations
   - Support undo via `RollbackManager`
   - Structured error handling

### Entry Points

**Primary Entry Point:** `configurator/cli.py`
- **Type**: Click-based CLI application
- **Commands**: 106+ commands organized in groups
- **Invocation**: `vps-configurator <command> [options]`

**Entry Point Groups:**
1. **Core Commands**: install, verify, rollback, wizard
2. **Security Commands**: cis-scan, vuln-scan, ssl, ssh-keys, 2fa
3. **User Management**: user, team, temp-access
4. **Activity & Audit**: activity, audit, compliance
5. **Monitoring**: health, metrics, logs

**Example Entry Point Registration:**
```toml
# pyproject.toml
[project.scripts]
vps-configurator = "configurator.cli:main"
```

### Data Persistence

| Type | Technology | Location | Purpose |
|------|-----------|----------|---------|
| **Configuration** | YAML | config/ | User settings |
| **State** | JSON/Pickle | ~/.config/vps-configurator/ | Runtime state |
| **Database** | SQLite | /var/lib/vps-configurator/ | Activity logs |
| **Cache** | Filesystem | /var/cache/vps-configurator/ | Package cache |
| **Logs** | Structured logs | /var/log/vps-configurator/ | Audit trail |

---

## 4. End-to-End Workflow Documentation

### Workflow 1: Module Installation (Primary Workflow)

**Business Purpose:**
Install and configure a complete VPS development environment with security hardening, development tools, and remote desktop access.

**Trigger:**
User runs: `vps-configurator install --profile advanced -v`

**Success Criteria:**
- All enabled modules configured successfully
- System passes health checks
- Remote desktop accessible
- Development tools verified

#### Complete File Flow

```
Entry Point:
└─ configurator/cli.py::install()
   ├─ Parse CLI arguments (Click framework)
   ├─ Setup logging (configurator/logger.py)
   └─ Initialize core services

Configuration Loading:
└─ configurator/config.py::ConfigManager
   ├─ Load profile (config/profiles/advanced.yaml)
   ├─ Merge with defaults (config/default.yaml)
   ├─ Validate with Pydantic (configurator/config_schema.py)
   └─ Return ConfigManager instance

System Validation:
└─ configurator/core/validator.py::SystemValidator
   ├─ check_os_compatibility()
   ├─ check_python_version()
   ├─ check_disk_space()
   ├─ check_memory()
   ├─ check_network()
   └─ Return validation results

Module Loading & Orchestration:
└─ configurator/core/installer.py::Installer
   ├─ _register_modules()
   │  ├─ Import all module classes
   │  └─ Register in container
   ├─ _get_enabled_modules()
   │  ├─ Read config for enabled modules
   │  └─ Filter by profile
   ├─ _resolve_dependencies()
   │  ├─ Build dependency graph (NetworkX)
   │  └─ Topological sort
   ├─ _group_by_priority()
   │  └─ Sort by MODULE_PRIORITY dict
   └─ run()
      └─ Execute modules

Parallel Execution:
└─ configurator/core/parallel.py::ParallelExecutor
   ├─ Group modules by batch (same priority)
   ├─ ThreadPoolExecutor(max_workers=4)
   ├─ Submit futures for parallel execution
   ├─ Collect results with as_completed()
   └─ Handle errors and timeouts

Individual Module Execution:
└─ configurator/modules/base.py::ConfigurationModule
   ├─ validate()
   │  ├─ Check prerequisites
   │  ├─ Verify dependencies
   │  └─ Return bool
   ├─ configure()
   │  ├─ Install packages (with resilience)
   │  ├─ Configure services
   │  ├─ Apply settings
   │  └─ Return bool
   └─ verify()
      ├─ Check installation
      ├─ Test functionality
      └─ Return bool

Package Installation (Example Flow):
└─ configurator/modules/docker.py::DockerModule
   ├─ validate()
   │  └─ Check if Docker already installed
   ├─ configure()
   │  ├─ _add_docker_repository()
   │  │  ├─ Install GPG key
   │  │  ├─ Add APT source
   │  │  └─ Update APT cache
   │  ├─ install_packages_resilient()
   │  │  └─ Call base.install_packages_resilient()
   │  ├─ _configure_docker_daemon()
   │  │  ├─ Create /etc/docker/daemon.json
   │  │  ├─ Register rollback
   │  │  └─ Restart service
   │  └─ _add_user_to_docker_group()
   │     └─ usermod -aG docker
   └─ verify()
      ├─ Check docker command exists
      ├─ Run docker --version
      └─ Test docker ps

Resilient Package Installation:
└─ configurator/modules/base.py::install_packages_resilient()
   ├─ Check package cache
   │  └─ configurator/core/package_cache.py::PackageCacheManager
   ├─ Acquire APT lock (threading.Lock)
   ├─ Circuit breaker check
   │  └─ configurator/utils/circuit_breaker.py::CircuitBreakerManager
   ├─ Retry with exponential backoff
   │  ├─ Attempt 1: apt-get install
   │  ├─ Attempt 2: Wait + retry
   │  └─ Attempt 3: Wait + retry
   ├─ Register rollback action
   │  └─ configurator/core/rollback.py::RollbackManager
   └─ Cache installed packages

Service Management:
└─ configurator/modules/base.py::enable_service()
   ├─ systemctl enable <service>
   ├─ systemctl start <service>
   ├─ Register rollback (systemctl stop)
   └─ Verify service active

Progress Reporting:
└─ configurator/core/reporter.py::ProgressReporter
   ├─ start_module(module_name)
   ├─ update_progress(status, message)
   ├─ complete_module(success, duration)
   └─ generate_summary()

Error Handling & Rollback:
└─ On any module failure
   ├─ Log error with full context
   ├─ Trigger rollback
   │  └─ configurator/core/rollback.py::RollbackManager.rollback()
   │     ├─ Reverse order of actions
   │     ├─ Stop services
   │     ├─ Remove packages
   │     ├─ Restore files
   │     └─ Execute custom rollback commands
   ├─ Generate error report
   └─ Exit with status code

Hooks Execution:
└─ configurator/core/hooks.py::HooksManager
   ├─ pre_install hooks
   ├─ post_module hooks (per module)
   ├─ post_install hooks
   └─ on_error hooks
```

#### Key Implementation Details

**1. Configuration Schema (Pydantic Validation)**

```python
# configurator/config_schema.py
from pydantic import BaseModel, Field

class SystemConfig(BaseModel):
    hostname: str = Field(default="dev-workstation")
    timezone: str = Field(default="UTC")

class ProfileConfig(BaseModel):
    system: SystemConfig
    modules: Dict[str, bool]
    performance: PerformanceConfig
    security: SecurityConfig
```

**2. Module Base Class (Template Method)**

```python
# configurator/modules/base.py
from abc import ABC, abstractmethod

class ConfigurationModule(ABC):
    """Base class for all configuration modules."""

    name: str = "base"
    description: str = ""
    depends_on: List[str] = []
    priority: int = 50
    mandatory: bool = False

    @abstractmethod
    def validate(self) -> bool:
        """Validate prerequisites."""

    @abstractmethod
    def configure(self) -> bool:
        """Execute configuration."""

    @abstractmethod
    def verify(self) -> bool:
        """Verify installation."""

    # Common utility methods
    def run(self, cmd: str, **kwargs) -> CommandResult:
        """Execute shell command with dry-run support."""

    def install_packages_resilient(self, packages: List[str]) -> bool:
        """Install packages with retry and circuit breaker."""

    def enable_service(self, service: str) -> bool:
        """Enable and start systemd service."""
```

**3. Dependency Injection Container**

```python
# configurator/core/container.py
class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services = {}
        self._singletons = {}

    def singleton(self, name: str, factory: Callable):
        """Register singleton service."""
        self._singletons[name] = factory

    def get(self, name: str) -> Any:
        """Resolve service by name."""
        if name in self._services:
            return self._services[name]
        if name in self._singletons:
            self._services[name] = self._singletons[name]()
            return self._services[name]
        raise KeyError(f"Service not found: {name}")
```

**4. Circuit Breaker Implementation**

```python
# configurator/utils/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreakerManager:
    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.circuits = {}

    def call(self, operation: str, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        circuit = self._get_circuit(operation)

        if circuit.state == CircuitState.OPEN:
            if datetime.now() - circuit.opened_at > self.timeout:
                circuit.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError("Circuit is open")

        try:
            result = func(*args, **kwargs)
            circuit.record_success()
            return result
        except Exception as e:
            circuit.record_failure()
            raise
```

**5. Lazy Loading Pattern**

```python
# configurator/core/lazy_loader.py
class LazyLoader:
    """Lazy load modules to improve startup time."""

    def __init__(self, module_name: str, class_name: str):
        self.module_name = module_name
        self.class_name = class_name
        self._cached = None

    def __call__(self):
        if self._cached is None:
            module = importlib.import_module(self.module_name)
            self._cached = getattr(module, self.class_name)
        return self._cached

# Usage in cli.py
Installer = LazyLoader("configurator.core.installer", "Installer")
# Import only happens when Installer() is first called
```

**6. Rollback Manager**

```python
# configurator/core/rollback.py
from dataclasses import dataclass
from typing import List, Callable

@dataclass
class RollbackAction:
    description: str
    action: Callable
    args: tuple = ()
    kwargs: dict = None

class RollbackManager:
    """Manages rollback actions for recovery."""

    def __init__(self, logger):
        self.logger = logger
        self.actions: List[RollbackAction] = []

    def add_package_remove(self, packages: List[str]):
        """Register package removal rollback."""
        self.actions.append(RollbackAction(
            description=f"Remove packages: {', '.join(packages)}",
            action=self._remove_packages,
            args=(packages,)
        ))

    def add_file_restore(self, backup_path: Path, original_path: Path):
        """Register file restoration rollback."""
        self.actions.append(RollbackAction(
            description=f"Restore {original_path}",
            action=shutil.copy2,
            args=(backup_path, original_path)
        ))

    def rollback(self):
        """Execute all rollback actions in reverse order."""
        for action in reversed(self.actions):
            try:
                self.logger.info(f"Rollback: {action.description}")
                action.action(*action.args, **(action.kwargs or {}))
            except Exception as e:
                self.logger.error(f"Rollback failed: {e}")
```

#### Response Construction

**Success Response:**
```python
# Generated by ProgressReporter
{
    "status": "success",
    "duration_seconds": 1834,
    "modules_installed": 18,
    "modules_skipped": 6,
    "summary": {
        "system": {"status": "success", "duration": 45},
        "security": {"status": "success", "duration": 123},
        "docker": {"status": "success", "duration": 234},
        ...
    },
    "next_steps": [
        "Reboot system to apply all changes",
        "Connect via RDP: <IP>:3389",
        "Default user: your-username"
    ]
}
```

**Error Response:**
```python
{
    "status": "error",
    "error_module": "docker",
    "error_type": "ModuleExecutionError",
    "error_message": "Failed to install Docker",
    "error_details": {
        "what": "Failed to add Docker repository",
        "why": "GPG key download failed",
        "how": "1. Check network: ping deb.debian.org\n2. Check firewall\n3. Retry"
    },
    "rollback_executed": true,
    "rollback_status": "success"
}
```

---


### Workflow 2: User Lifecycle Management (Secondary Workflow)

**Business Purpose:**
Automate complete user onboarding process with security best practices, including SSH key generation, 2FA setup, RBAC permissions, and audit trail initialization.

**Trigger:**
User runs: `vps-configurator user create johndoe --full-name "John Doe" --email john@company.com --role developer --enable-2fa --generate-ssh-key`

**Success Criteria:**
- User account created with proper permissions
- SSH key generated and configured
- 2FA enabled with QR code
- RBAC role assigned
- Activity monitoring initialized
- Audit log entry created

#### Complete File Flow

```
Entry Point:
└─ configurator/cli.py::user_create()
   ├─ Parse arguments (username, full-name, email, role, options)
   ├─ Validate inputs
   │  └─ configurator/security/input_validator.py::InputValidator
   │     ├─ validate_username() - regex check
   │     ├─ validate_email() - format check
   │     └─ validate_role() - RBAC role exists
   └─ Call UserLifecycleManager

User Lifecycle Orchestration:
└─ configurator/users/lifecycle_manager.py::UserLifecycleManager
   ├─ create_user_workflow()
   │  ├─ Check if user exists
   │  ├─ Validate prerequisites
   │  └─ Execute 12-step onboarding
   └─ Steps:

Step 1: Create System User
└─ _create_system_user()
   ├─ Run: useradd -m -s /bin/bash johndoe
   ├─ Set password (encrypted)
   ├─ Register rollback: userdel -r johndoe
   └─ Audit log: USER_CREATED

Step 2: Generate SSH Key
└─ configurator/security/ssh_manager.py::SSHKeyManager
   ├─ generate_key_pair()
   │  ├─ Generate RSA 4096-bit key
   │  ├─ Save to ~/.ssh/id_rsa
   │  ├─ Set permissions (600)
   │  └─ Add to authorized_keys
   ├─ set_expiration(days=90)
   └─ Audit log: SSH_KEY_GENERATED

Step 3: Setup 2FA
└─ configurator/security/twofa_manager.py::TwoFactorManager
   ├─ generate_secret()
   ├─ generate_qr_code()
   │  └─ Display in terminal (Rich/Textual)
   ├─ generate_backup_codes(10 codes)
   ├─ Save to ~/.2fa/secret (encrypted)
   └─ Audit log: TFA_ENABLED

Step 4: Assign RBAC Role
└─ configurator/rbac/rbac_manager.py::RBACManager
   ├─ get_role("developer")
   │  └─ Load from config/rbac/roles.yaml
   ├─ assign_role(user, role)
   │  ├─ Create user entry in RBAC database
   │  ├─ Copy permissions from role template
   │  └─ Apply system-level permissions
   └─ Audit log: ROLE_ASSIGNED

Step 5: Configure Sudo Permissions
└─ configurator/rbac/sudo_manager.py::SudoPolicyManager
   ├─ create_sudoers_file()
   │  ├─ /etc/sudoers.d/developer-johndoe
   │  ├─ Apply role-based sudo rules
   │  ├─ Enable 2FA for sudo (if configured)
   │  └─ Set command whitelist
   ├─ Validate syntax (visudo -c)
   └─ Audit log: SUDO_CONFIGURED

Step 6: Setup Home Directory
└─ _setup_home_directory()
   ├─ Create standard directories
   │  ├─ ~/projects
   │  ├─ ~/documents
   │  └─ ~/bin
   ├─ Copy skeleton files (.bashrc, .profile)
   ├─ Set disk quotas (if enabled)
   └─ Set proper ownership

Step 7: Initialize Activity Monitoring
└─ configurator/users/activity_monitor.py::ActivityMonitor
   ├─ create_user_profile()
   ├─ Initialize activity database
   │  └─ SQLite: /var/lib/vps-configurator/activity.db
   ├─ Set baseline metrics
   └─ Audit log: MONITORING_INITIALIZED

Step 8: Configure Development Environment
└─ _configure_dev_environment()
   ├─ Install user-level packages (if configured)
   ├─ Setup Git config
   │  ├─ git config --global user.name
   │  ├─ git config --global user.email
   │  └─ git config --global core.editor
   └─ Setup IDE preferences

Step 9: Email Welcome Message
└─ _send_welcome_email()
   ├─ Generate welcome email (Jinja2 template)
   │  ├─ Account details
   │  ├─ SSH key fingerprint
   │  ├─ 2FA QR code
   │  ├─ Backup codes
   │  └─ Next steps
   └─ Send via SMTP (if configured)

Step 10: Create Team Memberships
└─ configurator/users/team_manager.py::TeamManager
   ├─ add_user_to_default_teams()
   ├─ Apply team permissions
   └─ Audit log: TEAM_MEMBERSHIP_ADDED

Step 11: File Integrity Baseline
└─ configurator/core/file_integrity.py::FileIntegrityMonitor
   ├─ create_user_baseline()
   ├─ Hash critical files
   │  ├─ ~/.ssh/authorized_keys
   │  ├─ ~/.bashrc
   │  └─ ~/.profile
   └─ Store hashes in database

Step 12: Final Verification
└─ verify_user_creation()
   ├─ Test SSH login (optional)
   ├─ Verify 2FA works
   ├─ Check RBAC permissions
   ├─ Verify home directory
   └─ Return success status

Response Generation:
└─ Generate user creation response
   ├─ User details (username, UID, home dir)
   ├─ SSH public key
   ├─ 2FA QR code (base64 image)
   ├─ Backup codes (encrypted)
   ├─ Next steps for user
   └─ Admin summary
```

#### Key Data Models

**User Model:**
```python
# configurator/users/models.py
from dataclasses import dataclass
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

@dataclass
class User:
    username: str
    uid: int
    full_name: str
    email: str
    status: UserStatus
    roles: List[str]
    ssh_key_fingerprint: Optional[str]
    tfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]
    expiration_date: Optional[datetime]

    def to_dict(self) -> Dict:
        return {
            "username": self.username,
            "uid": self.uid,
            "full_name": self.full_name,
            "email": self.email,
            "status": self.status.value,
            "roles": self.roles,
            "ssh_key_fingerprint": self.ssh_key_fingerprint,
            "tfa_enabled": self.tfa_enabled,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
```

**RBAC Role Model:**
```python
# configurator/rbac/models.py
@dataclass
class Permission:
    resource: str  # e.g., "system:packages"
    actions: List[str]  # e.g., ["read", "install"]
    conditions: Optional[Dict] = None

@dataclass
class Role:
    name: str
    description: str
    permissions: List[Permission]
    sudo_rules: List[str]
    inherits_from: Optional[List[str]] = None
```

### Workflow 3: CI/CD Pipeline Execution

**Business Purpose:**
Automatically build, test, and validate code on every push/PR to ensure code quality and catch issues early.

**Trigger:**
- Git push to main/develop
- Pull request opened/updated
- Manual workflow dispatch

**Success Criteria:**
- All linters pass
- All tests pass (unit + integration)
- Code coverage >= 85%
- Package builds successfully

#### GitHub Actions Workflow Files

**File: .github/workflows/tests.yml**

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-lint-${{ hashFiles('**/requirements*.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check configurator/ tests/

      - name: Type check with mypy
        run: mypy configurator/ --ignore-missing-imports

  test:
    name: Test Suite (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-py${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential python3-dev libffi-dev libssl-dev

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install -e .

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v \
            --cov=configurator \
            --cov-report=xml \
            --cov-report=term-missing \
            --tb=short

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}

  build:
    name: Build & Validate Package
    runs-on: ubuntu-latest
    needs: [test]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ github.sha }}
          path: dist/
          retention-days: 7
```

---

## 5. CI/CD Pipeline Workflows

### Pipeline Architecture

```
┌──────────────────────────────────────────────────────────┐
│               CI/CD PIPELINE ARCHITECTURE                │
└──────────────────────────────────────────────────────────┘

Git Push/PR
    │
    ├─→ [Trigger] GitHub Actions
    │
    ├─→ [Job 1: Lint] ────────────────────────┐
    │   ├─ Ruff (linting + formatting)        │
    │   ├─ Mypy (type checking)               │
    │   └─ Exit code 0/1                      │
    │                                          │
    ├─→ [Job 2: Test] ────────────────────────┤
    │   ├─ Matrix: Python 3.11, 3.12          │
    │   ├─ Unit tests (pytest)                │
    │   ├─ Code coverage (pytest-cov)         │ → ALL PASS
    │   └─ Upload coverage report             │
    │                                          │
    └─→ [Job 3: Build] ───────────────────────┘
        ├─ Build wheel + sdist
        ├─ Validate with twine
        └─ Upload artifacts
              │
              ├─→ [On Tag Push] Release Pipeline
              │   ├─ Create GitHub Release
              │   ├─ Attach artifacts
              │   ├─ Generate release notes
              │   └─ (Future) Publish to PyPI
              │
              └─→ [Manual] Deployment
                  ├─ Download artifacts
                  ├─ Deploy to target systems
                  └─ Verify deployment
```

### Build Phase Details

**Stage 1: Code Quality Checks**
- **Duration**: 2-3 minutes
- **Tools**: Ruff, Mypy
- **Fail Fast**: Yes
- **Cacheable**: Pip dependencies

**Stage 2: Multi-Version Testing**
- **Duration**: 5-8 minutes
- **Parallelization**: Python 3.11 & 3.12 in parallel
- **Coverage Target**: 85%+
- **Test Categories**:
  - Unit tests (~200 tests, <5s each)
  - Integration tests (selected, ~30s each)

**Stage 3: Package Build**
- **Duration**: 1-2 minutes
- **Outputs**:
  - Wheel (`.whl`) - binary distribution
  - Source distribution (`.tar.gz`)
- **Validation**: twine check for PyPI compliance

### Continuous Integration Triggers

| Event | Branches | Jobs Run |
|-------|----------|----------|
| **Push** | main, develop | lint + test + build |
| **Pull Request** | → main | lint + test + build |
| **Tag Push** | v* | lint + test + build + release |
| **Manual** | Any | lint + test + build |
| **Schedule** | main | Full test suite (nightly) |

### Deployment Pipeline

**File: .github/workflows/release.yml**

```yaml
name: Release

on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      version:
        description: "Version tag (e.g., v1.0.0)"
        required: true

jobs:
  release:
    name: Build & Release
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for changelog

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Build package
        run: |
          pip install build twine
          python -m build
          twine check dist/*

      - name: Get version
        id: version
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "VERSION=${{ github.event.inputs.version }}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          fi

      - name: Create release bundle
        run: |
          mkdir -p release
          cp quick-install.sh release/
          cp -r config/ release/config/
          tar -czf release/debian-vps-configurator-${{ steps.version.outputs.VERSION }}.tar.gz \
            -C release quick-install.sh config/

      - name: Generate release notes
        run: |
          cat > release/RELEASE_NOTES.md << 'EOF'
          ## Debian VPS Configurator ${{ steps.version.outputs.VERSION }}

          ### Installation
          ```bash
          curl -sSL https://raw.githubusercontent.com/${{ github.repository }}/main/quick-install.sh | bash
          ```

          ### Changelog
          $(git log $(git describe --tags --abbrev=0 HEAD^)..HEAD --pretty=format:"- %s (%an)")
          EOF

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          name: ${{ steps.version.outputs.VERSION }}
          body_path: release/RELEASE_NOTES.md
          draft: false
          prerelease: ${{ contains(steps.version.outputs.VERSION, 'alpha') || contains(steps.version.outputs.VERSION, 'beta') }}
          files: |
            dist/*
            release/debian-vps-configurator-${{ steps.version.outputs.VERSION }}.tar.gz
```

---


## 6. Testing Workflows

### Test Strategy (Test Pyramid)

```
            /\
           /  \          E2E Tests (10 tests)
          /____\         - Full workflows
         /      \        - Real system interactions
        / Integ  \       Integration Tests (50 tests)
       /__________\      - Module interactions
      /            \     - Service boundaries
     /    Unit      \    Unit Tests (200+ tests)
    /________________\   - Fast, isolated
                         - Mock external dependencies
```

### Test Structure

```
tests/
├── unit/                      # Fast, isolated unit tests
│   ├── test_config.py         # Config loading & validation
│   ├── test_container.py      # DI container
│   ├── test_lazy_loader.py    # Lazy loading
│   ├── test_rollback.py       # Rollback manager
│   ├── test_circuit_breaker.py# Circuit breaker
│   └── modules/
│       ├── test_docker.py     # Docker module tests
│       ├── test_python.py     # Python module tests
│       └── test_security.py   # Security module tests
│
├── integration/               # Service integration tests
│   ├── test_installer.py      # Full installer workflow
│   ├── test_parallel.py       # Parallel execution
│   ├── test_package_cache.py  # Cache functionality
│   └── test_rbac_integration.py # RBAC with user management
│
├── e2e/                       # End-to-end workflows
│   ├── test_full_install.py   # Complete installation
│   ├── test_user_lifecycle.py # User onboarding/offboarding
│   └── test_security_scan.py  # Security scanning workflow
│
├── performance/               # Performance & load tests
│   ├── test_parallel_perf.py  # Parallel execution benchmarks
│   └── test_cache_perf.py     # Cache performance
│
├── security/                  # Security-specific tests
│   ├── test_input_validation.py
│   ├── test_ssh_keys.py
│   └── test_2fa.py
│
└── conftest.py                # Shared fixtures
```

### Test Fixtures (Reusable)

```python
# tests/conftest.py
import pytest
from pathlib import Path
from configurator.config import ConfigManager
from configurator.core.container import Container

@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary config file for testing."""
    config = tmp_path / "config.yaml"
    config.write_text("""
system:
  hostname: test-server
  timezone: UTC
modules:
  docker:
    enabled: true
  python:
    enabled: true
    """)
    return config

@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return ConfigManager(profile="beginner")

@pytest.fixture
def container():
    """Provide DI container with test services."""
    c = Container()
    c.singleton("logger", lambda: logging.getLogger("test"))
    return c

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess calls."""
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="success",
            stderr=""
        )
    monkeypatch.setattr("subprocess.run", fake_run)
```

### Unit Test Example

```python
# tests/unit/test_config.py
import pytest
from configurator.config import ConfigManager
from configurator.exceptions import ConfigurationError

class TestConfigManager:
    """Tests for ConfigManager."""

    def test_default_values(self):
        """Test that default values are loaded correctly."""
        config = ConfigManager()
        assert config.get("system.hostname") == "dev-workstation"
        assert config.get("system.timezone") == "UTC"

    def test_profile_loading(self):
        """Test profile-specific config loading."""
        config = ConfigManager(profile="advanced")
        assert config.get("modules.docker.enabled") is True
        assert config.get("modules.netdata.enabled") is True

    def test_invalid_profile(self):
        """Test that invalid profile raises error."""
        with pytest.raises(ConfigurationError):
            ConfigManager(profile="nonexistent")

    def test_dot_notation_access(self):
        """Test nested config access with dot notation."""
        config = ConfigManager()
        assert config.get("system.hostname") == config.data["system"]["hostname"]

    def test_default_value_fallback(self):
        """Test default value when key doesn't exist."""
        config = ConfigManager()
        assert config.get("nonexistent.key", default="fallback") == "fallback"
```

### Integration Test Example

```python
# tests/integration/test_installer.py
import pytest
from configurator.core.installer import Installer
from configurator.config import ConfigManager

@pytest.mark.integration
class TestInstaller:
    """Integration tests for Installer orchestration."""

    def test_dependency_resolution(self, mock_config, container):
        """Test module dependency resolution."""
        installer = Installer(config=mock_config, container=container)
        modules = installer._get_enabled_modules()
        ordered = installer._resolve_dependencies(modules)

        # Security should come before docker
        security_idx = next(i for i, m in enumerate(ordered) if m.name == "security")
        docker_idx = next(i for i, m in enumerate(ordered) if m.name == "docker")
        assert security_idx < docker_idx

    def test_parallel_execution(self, mock_config, container):
        """Test parallel module execution."""
        installer = Installer(config=mock_config, container=container)
        # Mock modules to avoid real installation
        # Test that independent modules run in parallel

    @pytest.mark.slow
    def test_rollback_on_failure(self, mock_config, container):
        """Test rollback when module fails."""
        installer = Installer(config=mock_config, container=container)
        # Inject failing module
        # Verify rollback executed
```

### E2E Test Example

```python
# tests/e2e/test_full_install.py
import pytest
from configurator.cli import main
from click.testing import CliRunner

@pytest.mark.e2e
@pytest.mark.slow
class TestFullInstallation:
    """End-to-end installation tests."""

    def test_beginner_profile_install(self, tmp_path):
        """Test complete beginner profile installation."""
        runner = CliRunner()
        result = runner.invoke(main, [
            'install',
            '--profile', 'beginner',
            '--dry-run',  # Don't actually install
            '--non-interactive'
        ])

        assert result.exit_code == 0
        assert "Installation completed successfully" in result.output

    def test_rollback_recovery(self, tmp_path):
        """Test rollback after partial installation."""
        # Simulate failure mid-installation
        # Trigger rollback
        # Verify system state restored
```

### Running Tests

```bash
# Fast unit tests only (CI)
pytest tests/unit/ -v

# Integration tests (slower)
pytest tests/integration/ -v -m integration

# E2E tests (slowest, use sparingly)
pytest tests/e2e/ -v -m e2e

# All tests with coverage
pytest tests/ -v --cov=configurator --cov-report=html

# Specific test file
pytest tests/unit/test_config.py -v

# Specific test function
pytest tests/unit/test_config.py::TestConfigManager::test_default_values -v

# Skip slow tests
pytest tests/ -v -m "not slow"
```

---

## 7. Deployment Workflows

### Deployment Strategies

#### Strategy 1: Quick Install (Production)

**Target Audience**: Production deployments, first-time users

```bash
# One-command installation
curl -sSL https://raw.githubusercontent.com/yunaamelia/debian-vps-workstation/main/quick-install.sh | bash

# What it does:
# 1. Checks OS compatibility (Debian 11+, Ubuntu 20.04+)
# 2. Verifies Python 3.9+ installed
# 3. Installs system dependencies (build-essential, libffi-dev, libssl-dev)
# 4. Creates Python virtual environment
# 5. Installs Python dependencies
# 6. Installs vps-configurator in development mode
# 7. Verifies installation works
# 8. Displays next steps
```

**Script Breakdown:**

```bash
#!/bin/bash
# quick-install.sh

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check OS
check_os() {
    if [ -f /etc/debian_version ]; then
        echo -e "${GREEN}✓${NC} Debian-based system detected"
    else
        echo -e "${RED}✗${NC} This script requires Debian/Ubuntu"
        exit 1
    fi
}

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        version=$(python3 --version | cut -d' ' -f2)
        major=$(echo $version | cut -d'.' -f1)
        minor=$(echo $version | cut -d'.' -f2)

        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            echo -e "${GREEN}✓${NC} Python $version found"
        else
            echo -e "${RED}✗${NC} Python 3.9+ required, found $version"
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} Python 3 not found"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."
    sudo apt-get update -qq
    sudo apt-get install -y \
        build-essential \
        python3-dev \
        python3-venv \
        libffi-dev \
        libssl-dev \
        git
}

# Create virtual environment
setup_venv() {
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
}

# Install Python packages
install_python_deps() {
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    pip install -e .
}

# Verify installation
verify_install() {
    echo "Verifying installation..."
    if vps-configurator --version; then
        echo -e "${GREEN}✓${NC} Installation successful!"
    else
        echo -e "${RED}✗${NC} Installation verification failed"
        exit 1
    fi
}

# Main execution
main() {
    echo "======================================"
    echo "  Debian VPS Configurator Installer  "
    echo "======================================"

    check_os
    check_python
    install_system_deps
    setup_venv
    install_python_deps
    verify_install

    echo ""
    echo "Next steps:"
    echo "1. Activate venv: source venv/bin/activate"
    echo "2. Run installer: vps-configurator install --profile advanced -v"
}

main
```

#### Strategy 2: PyPI Install (Future)

```bash
# When published to PyPI
pip install debian-vps-configurator

# Upgrade to latest
pip install --upgrade debian-vps-configurator

# Install specific version
pip install debian-vps-configurator==1.0.0
```

#### Strategy 3: Docker Deployment (Future)

```dockerfile
# Dockerfile
FROM debian:13-slim

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install -e .

# Entry point
ENTRYPOINT ["vps-configurator"]
CMD ["--help"]
```

```bash
# Build and run
docker build -t vps-configurator:latest .
docker run -it --privileged vps-configurator install --profile advanced
```

### Deployment Checklist

**Pre-Deployment:**
- [ ] All tests passing (CI green)
- [ ] Documentation updated
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated
- [ ] Tag created and pushed

**Deployment:**
- [ ] Download/build artifacts
- [ ] Backup existing installation (if upgrade)
- [ ] Run deployment script
- [ ] Verify health checks pass

**Post-Deployment:**
- [ ] Smoke tests executed
- [ ] Monitoring alerts configured
- [ ] Rollback plan ready
- [ ] Team notified

### Blue-Green Deployment (Advanced)

```bash
# Terminal 1: Current installation (blue)
/opt/vps-configurator-v1.0.0/

# Terminal 2: New installation (green)
/opt/vps-configurator-v1.1.0/

# Test green deployment
cd /opt/vps-configurator-v1.1.0
./venv/bin/vps-configurator verify

# Switch symlink (atomic operation)
sudo ln -sfn /opt/vps-configurator-v1.1.0 /opt/vps-configurator-current

# Rollback if needed
sudo ln -sfn /opt/vps-configurator-v1.0.0 /opt/vps-configurator-current
```

---

## 8. Monitoring & Operations Workflows

### Observability Architecture

```
┌────────────────────────────────────────────────────────┐
│            OBSERVABILITY ARCHITECTURE                  │
└────────────────────────────────────────────────────────┘

Application Layer
├─ Activity Monitoring (users, commands, file access)
├─ Audit Logging (all operations with full context)
├─ File Integrity Monitoring (critical file changes)
└─ Health Checks (system prerequisites, service status)
     │
     ├→ Metrics Collection
     │  ├─ Deployment frequency
     │  ├─ Lead time for changes
     │  ├─ Module success rates
     │  ├─ Execution times
     │  └─ Resource utilization
     │
     ├→ Log Aggregation
     │  ├─ Structured logs (JSON)
     │  ├─ Log levels (DEBUG, INFO, WARNING, ERROR)
     │  ├─ Centralized storage (/var/log/vps-configurator/)
     │  └─ 7-year retention (compliance)
     │
     └→ Alerting
        ├─ Failed installations
        ├─ Security anomalies
        ├─ Circuit breaker trips
        └─ File integrity violations
```

### Health Check Workflow

```python
# configurator/core/health.py
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]

class HealthChecker:
    """System health monitoring."""

    def check_all(self) -> List[HealthCheckResult]:
        """Run all health checks."""
        return [
            self.check_disk_space(),
            self.check_memory(),
            self.check_services(),
            self.check_network(),
            self.check_security(),
        ]

    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        import psutil
        disk = psutil.disk_usage('/')
        percent_used = disk.percent

        if percent_used > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: Disk {percent_used}% full"
        elif percent_used > 75:
            status = HealthStatus.DEGRADED
            message = f"Warning: Disk {percent_used}% full"
        else:
            status = HealthStatus.HEALTHY
            message = f"OK: Disk {percent_used}% full"

        return HealthCheckResult(
            component="disk",
            status=status,
            message=message,
            details={
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent_used": percent_used
            }
        )
```

### Activity Monitoring Workflow

```python
# configurator/users/activity_monitor.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ActivityType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    SUDO_COMMAND = "sudo_command"
    FILE_ACCESS = "file_access"
    SSH_KEY_USE = "ssh_key_use"
    PACKAGE_INSTALL = "package_install"

@dataclass
class Activity:
    username: str
    activity_type: ActivityType
    timestamp: datetime
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    success: bool = True

class ActivityMonitor:
    """Monitor and track user activities."""

    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(db_path)
        self._create_tables()

    def record_activity(self, activity: Activity):
        """Record an activity to database."""
        self.db.execute("""
            INSERT INTO activities
            (username, type, timestamp, details, source_ip, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            activity.username,
            activity.activity_type.value,
            activity.timestamp.isoformat(),
            json.dumps(activity.details),
            activity.source_ip,
            activity.success
        ))
        self.db.commit()

    def get_user_activity(
        self,
        username: str,
        since: datetime,
        activity_type: Optional[ActivityType] = None
    ) -> List[Activity]:
        """Get user activities since timestamp."""
        # Query database and return activities

    def detect_anomalies(self, username: str) -> List[Dict]:
        """Detect unusual activity patterns."""
        # - Login from unusual IP
        # - Commands at unusual times
        # - Excessive sudo usage
        # - Unusual file access patterns
```

### Audit Logging Workflow

```python
# configurator/core/audit.py
from enum import Enum
from dataclasses import dataclass, asdict
import json
import logging

class AuditEventType(Enum):
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    ROLE_ASSIGNED = "role.assigned"
    PACKAGE_INSTALLED = "package.installed"
    SERVICE_STARTED = "service.started"
    CONFIG_CHANGED = "config.changed"
    SECURITY_SCAN = "security.scan"
    FILE_MODIFIED = "file.modified"

@dataclass
class AuditEvent:
    event_type: AuditEventType
    actor: str  # Who performed the action
    target: str  # What was affected
    timestamp: datetime
    success: bool
    details: Dict[str, Any]
    source_ip: Optional[str] = None

class AuditLogger:
    """Comprehensive audit trail logging."""

    def __init__(self, log_path: Path):
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        # Convert to JSON for structured logging
        event_dict = asdict(event)
        event_dict['event_type'] = event.event_type.value
        event_dict['timestamp'] = event.timestamp.isoformat()

        self.logger.info(json.dumps(event_dict))

    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Query audit events with filters."""
        # Parse log file and filter events
```

### DORA Metrics Collection

```python
# configurator/observability/dora_metrics.py
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class DORAMetrics:
    """DevOps Research and Assessment metrics."""

    deployment_frequency: float  # Deployments per week
    lead_time_for_changes: timedelta  # Commit to production
    time_to_restore_service: timedelta  # Incident resolution
    change_failure_rate: float  # % of changes causing failure

class MetricsCollector:
    """Collect and calculate DORA metrics."""

    def calculate_deployment_frequency(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate deployments per week."""
        deployments = self._get_deployments(start_date, end_date)
        weeks = (end_date - start_date).days / 7
        return len(deployments) / weeks if weeks > 0 else 0

    def calculate_lead_time(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> timedelta:
        """Calculate average lead time for changes."""
        changes = self._get_changes(start_date, end_date)
        lead_times = [
            change.deployed_at - change.committed_at
            for change in changes
        ]
        return sum(lead_times, timedelta()) / len(lead_times)

    def calculate_mttr(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> timedelta:
        """Calculate Mean Time To Recovery."""
        incidents = self._get_incidents(start_date, end_date)
        resolution_times = [
            incident.resolved_at - incident.detected_at
            for incident in incidents
        ]
        return sum(resolution_times, timedelta()) / len(resolution_times)

    def calculate_change_failure_rate(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate percentage of failed changes."""
        changes = self._get_changes(start_date, end_date)
        failures = [c for c in changes if c.caused_incident]
        return len(failures) / len(changes) if changes else 0
```

---


## 9. Security & Compliance Workflows

### Security Architecture

```
┌──────────────────────────────────────────────────────┐
│          SECURITY ARCHITECTURE (Defense in Depth)    │
└──────────────────────────────────────────────────────┘

Layer 1: Input Validation
├─ All user inputs validated
├─ Regex patterns for usernames, emails, paths
├─ Whitelist approach for allowed characters
└─ Parameterized commands (no string concatenation)

Layer 2: Authentication & Authorization
├─ SSH key-based authentication
├─ 2FA/MFA support (TOTP)
├─ RBAC for fine-grained permissions
└─ Sudo policy enforcement

Layer 3: Encryption
├─ Secrets encrypted at rest (cryptography library)
├─ TLS for network communications
├─ SSH keys with strong algorithms (RSA 4096, ED25519)
└─ Password hashing (bcrypt, Argon2)

Layer 4: Network Security
├─ Firewall rules (UFW)
├─ Fail2ban for brute force protection
├─ SSH hardening (disable root, key-only)
└─ Port knocking (optional)

Layer 5: System Hardening
├─ CIS benchmark compliance
├─ Minimal package installation
├─ Service isolation
└─ Kernel parameter hardening

Layer 6: Monitoring & Detection
├─ File integrity monitoring
├─ Activity anomaly detection
├─ Audit logging (7-year retention)
└─ Security event alerting

Layer 7: Incident Response
├─ Automated rollback capabilities
├─ Incident response playbooks
├─ Forensic data collection
└─ Recovery procedures
```

### Input Validation Workflow

```python
# configurator/security/input_validator.py
import re
from typing import Optional
from pathlib import Path

class InputValidator:
    """Validate all user inputs for security."""

    # Dangerous characters that could enable injection
    DANGEROUS_CHARS = [';', '&', '|', '$', '`', '>', '<', '\n', '\r']

    def validate_username(self, username: str) -> bool:
        """
        Validate username format.

        Rules:
        - Must start with lowercase letter
        - 3-32 characters
        - Only lowercase, digits, dash, underscore
        """
        if not re.match(r'^[a-z][a-z0-9_-]{2,31}$', username):
            raise ValidationError(
                f"Invalid username: {username}. "
                "Must be 3-32 chars, start with letter, "
                "contain only lowercase, digits, dash, underscore."
            )
        return True

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(f"Invalid email format: {email}")
        return True

    def validate_path(self, path: str) -> bool:
        """Validate file path for security."""
        # Check for path traversal
        if '..' in path:
            raise ValidationError("Path traversal not allowed")

        # Check for dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in path:
                raise ValidationError(f"Dangerous character in path: {char}")

        # Ensure absolute path or relative to safe directory
        path_obj = Path(path).resolve()
        # Additional checks...

        return True

    def sanitize_shell_arg(self, arg: str) -> str:
        """Sanitize argument for shell command."""
        import shlex
        return shlex.quote(arg)
```

### Secrets Management Workflow

```python
# configurator/core/secrets.py
from cryptography.fernet import Fernet
from pathlib import Path
import base64
import os

class SecretsManager:
    """Manage encrypted secrets."""

    def __init__(self, key_path: Optional[Path] = None):
        """
        Initialize secrets manager.

        Args:
            key_path: Path to encryption key file
                      If not provided, generates new key
        """
        self.key_path = key_path or Path.home() / '.config' / 'vps-configurator' / 'secret.key'
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            self.key_path.write_bytes(key)
            self.key_path.chmod(0o600)  # Owner read/write only
            return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string."""
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt encrypted string."""
        encrypted_bytes = base64.b64decode(encrypted.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()

    def store_secret(self, name: str, value: str):
        """Store encrypted secret to file."""
        secrets_dir = Path.home() / '.config' / 'vps-configurator' / 'secrets'
        secrets_dir.mkdir(parents=True, exist_ok=True)

        secret_file = secrets_dir / f"{name}.enc"
        encrypted = self.encrypt(value)
        secret_file.write_text(encrypted)
        secret_file.chmod(0o600)

    def retrieve_secret(self, name: str) -> Optional[str]:
        """Retrieve and decrypt secret from file."""
        secrets_dir = Path.home() / '.config' / 'vps-configurator' / 'secrets'
        secret_file = secrets_dir / f"{name}.enc"

        if not secret_file.exists():
            return None

        encrypted = secret_file.read_text()
        return self.decrypt(encrypted)
```

### CIS Benchmark Scanning Workflow

```python
# configurator/security/cis_scanner.py (simplified)
from dataclasses import dataclass
from enum import Enum

class ComplianceLevel(Enum):
    PASS = "pass"
    FAIL = "fail"
    MANUAL = "manual"  # Requires manual check

@dataclass
class CISCheck:
    id: str
    title: str
    description: str
    level: int  # 1 or 2
    scored: bool
    check_func: Callable
    remediate_func: Optional[Callable] = None

class CISScanner:
    """CIS Benchmark compliance scanner."""

    def __init__(self):
        self.checks = self._register_checks()

    def _register_checks(self) -> List[CISCheck]:
        """Register all CIS benchmark checks."""
        return [
            CISCheck(
                id="1.1.1.1",
                title="Ensure mounting of cramfs filesystems is disabled",
                description="The cramfs filesystem type is a compressed read-only...",
                level=1,
                scored=True,
                check_func=self._check_cramfs_disabled,
                remediate_func=self._remediate_cramfs
            ),
            # ... 147 total checks
        ]

    def _check_cramfs_disabled(self) -> ComplianceLevel:
        """Check if cramfs is disabled."""
        result = subprocess.run(
            ['modprobe', '-n', '-v', 'cramfs'],
            capture_output=True,
            text=True
        )
        if 'install /bin/true' in result.stdout:
            return ComplianceLevel.PASS
        return ComplianceLevel.FAIL

    def _remediate_cramfs(self):
        """Disable cramfs filesystem."""
        with open('/etc/modprobe.d/cramfs.conf', 'w') as f:
            f.write('install cramfs /bin/true\n')

    def scan_all(self, level: int = 1) -> Dict[str, ComplianceLevel]:
        """Run all CIS checks for specified level."""
        results = {}
        for check in self.checks:
            if check.level <= level:
                results[check.id] = check.check_func()
        return results

    def remediate_failures(self, results: Dict[str, ComplianceLevel]):
        """Automatically remediate failed checks."""
        for check in self.checks:
            if results.get(check.id) == ComplianceLevel.FAIL:
                if check.remediate_func:
                    check.remediate_func()
```

### Compliance Reporting Workflow

```python
# configurator/security/compliance.py
from enum import Enum

class ComplianceStandard(Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    GDPR = "gdpr"

class ComplianceReporter:
    """Generate compliance reports."""

    def generate_soc2_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Generate SOC 2 compliance report."""
        return {
            "standard": "SOC 2 Type II",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "controls": {
                "CC6.1": self._check_access_controls(),
                "CC6.2": self._check_authentication(),
                "CC6.3": self._check_authorization(),
                "CC7.2": self._check_monitoring(),
                "CC7.3": self._check_audit_logs(),
            },
            "compliance_score": self._calculate_score(),
            "findings": self._get_findings(),
            "recommendations": self._get_recommendations()
        }

    def _check_access_controls(self) -> Dict:
        """Check access control implementation."""
        return {
            "status": "compliant",
            "evidence": [
                "RBAC implemented with 5 roles",
                "Principle of least privilege enforced",
                "Access reviews conducted quarterly"
            ]
        }

    def _check_audit_logs(self) -> Dict:
        """Check audit logging compliance."""
        return {
            "status": "compliant",
            "evidence": [
                "All operations logged with full context",
                "7-year retention policy enforced",
                "Logs stored in tamper-proof format",
                "Log integrity verified daily"
            ]
        }
```

---

## 10. Implementation Templates

### Template 1: Adding a New Configuration Module

**Step-by-Step Guide:**

1. **Create Module File**

```python
# configurator/modules/mymodule.py
"""
MyModule configuration module.

Handles:
- Feature installation
- Service configuration
- Verification
"""

from typing import List, Optional
from configurator.modules.base import ConfigurationModule
from configurator.exceptions import ModuleExecutionError

class MyModule(ConfigurationModule):
    """
    Install and configure MyModule.

    This module provides [description of functionality].
    """

    # Module metadata
    name = "mymodule"
    description = "Install and configure MyModule"
    depends_on = ["system", "security"]  # Dependencies
    priority = 50  # Execution order (10-90)
    mandatory = False  # Stop installation on failure?

    def validate(self) -> bool:
        """
        Validate prerequisites before installation.

        Returns:
            True if prerequisites met, False otherwise
        """
        self.logger.info(f"Validating {self.name}...")

        # Check if already installed
        if self.is_command_available("mycommand"):
            self.logger.info(f"{self.name} already installed")
            return False

        # Check disk space
        if not self.check_disk_space(required_gb=5):
            raise ModuleExecutionError(
                what=f"{self.name} validation failed",
                why="Insufficient disk space",
                how="Free up at least 5GB of disk space"
            )

        # Check dependencies
        if not self.is_command_available("dependency-command"):
            raise ModuleExecutionError(
                what=f"{self.name} validation failed",
                why="Required dependency not installed",
                how="Install dependency first: apt-get install dependency"
            )

        return True

    def configure(self) -> bool:
        """
        Execute installation and configuration.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Installing {self.name}...")

        try:
            # Step 1: Add repository (if needed)
            self._add_repository()

            # Step 2: Install packages
            self._install_packages()

            # Step 3: Configure
            self._configure_service()

            # Step 4: Start service
            self._start_service()

            self.logger.info(f"✓ {self.name} installed successfully")
            return True

        except Exception as e:
            self.logger.error(f"✗ {self.name} installation failed: {e}")
            raise ModuleExecutionError(
                what=f"{self.name} installation failed",
                why=str(e),
                how="Check logs for details and retry"
            )

    def verify(self) -> bool:
        """
        Verify installation was successful.

        Returns:
            True if verification passed, False otherwise
        """
        self.logger.info(f"Verifying {self.name}...")

        # Check command exists
        if not self.is_command_available("mycommand"):
            self.logger.error(f"Command 'mycommand' not found")
            return False

        # Check version
        result = self.run("mycommand --version", capture_output=True)
        if result.return_code != 0:
            self.logger.error(f"Version check failed")
            return False

        # Check service running
        if not self.is_service_active("myservice"):
            self.logger.error(f"Service not running")
            return False

        self.logger.info(f"✓ {self.name} verification passed")
        return True

    # Private helper methods

    def _add_repository(self):
        """Add package repository."""
        self.logger.debug("Adding repository...")
        # Implementation

    def _install_packages(self):
        """Install required packages."""
        packages = ["package1", "package2"]
        self.install_packages_resilient(packages)

    def _configure_service(self):
        """Configure the service."""
        config_content = """
        # MyModule configuration
        option1 = value1
        option2 = value2
        """

        config_path = Path("/etc/mymodule/config.conf")
        self.write_file(
            config_path,
            config_content,
            owner="root",
            group="root",
            mode=0o644
        )

    def _start_service(self):
        """Start and enable service."""
        self.enable_service("myservice")
```

2. **Register Module in Installer**

```python
# configurator/core/installer.py
def _register_modules(self):
    """Register all available modules."""
    from configurator.modules.mymodule import MyModule

    module_classes = {
        # ... existing modules ...
        "mymodule": MyModule,
    }
```

3. **Add to Configuration**

```yaml
# config/profiles/advanced.yaml
modules:
  mymodule:
    enabled: true
    option1: value1
    option2: value2
```

4. **Add Tests**

```python
# tests/unit/modules/test_mymodule.py
import pytest
from configurator.modules.mymodule import MyModule

class TestMyModule:
    """Tests for MyModule."""

    def test_validate_success(self, mock_config):
        """Test successful validation."""
        module = MyModule(config=mock_config)
        assert module.validate() is True

    def test_configure_installs_packages(self, mock_config, mock_subprocess):
        """Test package installation."""
        module = MyModule(config=mock_config)
        result = module.configure()
        assert result is True

    def test_verify_checks_service(self, mock_config):
        """Test verification."""
        module = MyModule(config=mock_config)
        assert module.verify() is True
```

### Template 2: Adding a New CLI Command

```python
# configurator/cli.py

@main.group()
def mycommands():
    """My custom commands."""
    pass

@mycommands.command()
@click.argument('name')
@click.option('--option', '-o', help='An option')
@click.pass_context
def mycommand(ctx, name: str, option: Optional[str]):
    """
    Description of what this command does.

    Example:
        vps-configurator mycommands mycommand NAME --option VALUE
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"Executing mycommand for {name}")

        # Implementation
        result = do_something(name, option)

        console.print(f"[green]✓[/green] Success: {result}")

    except Exception as e:
        logger.error(f"Command failed: {e}")
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)
```

### Template 3: Adding a New Security Check

```python
# configurator/security/checks/my_check.py
from configurator.security.base_check import SecurityCheck, CheckResult

class MySecurityCheck(SecurityCheck):
    """Check for [security issue description]."""

    id = "SEC-001"
    title = "Check Title"
    severity = "HIGH"
    category = "Authentication"

    def check(self) -> CheckResult:
        """Perform the security check."""
        # Implementation
        if condition_met:
            return CheckResult(
                passed=True,
                message="Check passed",
                details={}
            )
        else:
            return CheckResult(
                passed=False,
                message="Check failed",
                details={"reason": "..."},
                remediation="Steps to fix..."
            )
```

---

## 11. Common Patterns & Best Practices

### Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| **Modules** | `<name>_module.py` → `<Name>Module` | `docker.py` → `DockerModule` |
| **CLI Commands** | `<verb>-<noun>` | `user-create`, `cis-scan` |
| **Functions** | `snake_case` | `install_packages()` |
| **Classes** | `PascalCase` | `ConfigurationModule` |
| **Constants** | `UPPER_SNAKE_CASE` | `MODULE_PRIORITY` |
| **Private** | `_leading_underscore` | `_install_packages()` |
| **Config Keys** | `dot.notation` | `modules.docker.enabled` |

### Error Handling Pattern

```python
try:
    # Operation
    result = do_something()

except SpecificError as e:
    # Handle specific error
    logger.error(f"Specific error: {e}")
    raise ModuleExecutionError(
        what="What failed",
        why=str(e),
        how="How to fix"
    )

except Exception as e:
    # Handle unexpected errors
    logger.exception("Unexpected error")
    raise

finally:
    # Cleanup (if needed)
    cleanup_resources()
```

### Logging Pattern

```python
# Start of operation
logger.info(f"Starting {operation_name}...")

# Progress updates
logger.debug(f"Step 1: {details}")

# Success
logger.info(f"✓ {operation_name} completed successfully")

# Warning (non-fatal)
logger.warning(f"⚠ {warning_message}")

# Error
logger.error(f"✗ {operation_name} failed: {error}")
```

### Command Execution Pattern

```python
# NEVER use subprocess directly
# ❌ subprocess.run(["apt-get", "install", package])

# ✅ Use self.run() for automatic dry-run, logging, rollback
result = self.run(
    f"apt-get install {package}",
    check=True,  # Raise on failure
    rollback_command=f"apt-get remove {package}"
)
```

### Configuration Access Pattern

```python
# ✅ Use dot notation with defaults
enabled = self.get_config("modules.docker.enabled", default=True)
version = self.get_config("modules.python.version", default="3.12")

# ❌ Don't access dict directly (KeyError risk)
enabled = self.config["modules"]["docker"]["enabled"]
```

### Rollback Registration Pattern

```python
# After installing package
self.rollback_manager.add_package_remove(["package-name"])

# After starting service
self.enable_service("service-name")  # Auto-registers rollback

# After creating file
self.write_file(path, content)  # Auto-registers rollback

# Custom rollback
self.rollback_manager.add_command("custom-cleanup-command")
```

### Testing Patterns

```python
# Fixture for common setup
@pytest.fixture
def module(mock_config):
    return DockerModule(config=mock_config)

# Parametrized tests for multiple inputs
@pytest.mark.parametrize("username,valid", [
    ("john", True),
    ("john_doe", True),
    ("John", False),  # Uppercase not allowed
    ("jo", False),     # Too short
])
def test_validate_username(username, valid):
    if valid:
        assert validate_username(username)
    else:
        with pytest.raises(ValidationError):
            validate_username(username)

# Mock external dependencies
@pytest.fixture
def mock_subprocess(monkeypatch):
    def fake_run(cmd, **kwargs):
        return CommandResult(return_code=0, stdout="", stderr="")
    monkeypatch.setattr("subprocess.run", fake_run)
```

---

## 12. Troubleshooting Workflows

### Common Issues & Solutions

**Issue 1: Module Installation Fails**

```bash
# Symptoms
✗ Module docker installation failed

# Diagnosis
1. Check logs: tail -f /var/log/vps-configurator/install.log
2. Check disk space: df -h
3. Check network: ping deb.debian.org
4. Check APT: sudo apt-get update

# Solutions
- Free disk space if needed
- Fix network connectivity
- Clear APT cache: sudo apt-get clean
- Retry installation: vps-configurator install --module docker
```

**Issue 2: Rollback Needed**

```bash
# Trigger rollback
vps-configurator rollback

# Partial rollback (specific module)
vps-configurator rollback --module docker

# Check rollback status
vps-configurator rollback --status
```

**Issue 3: Performance Degradation**

```bash
# Diagnose
scripts/diagnose.py

# Check metrics
vps-configurator metrics show

# Clear cache
vps-configurator cache clear

# Optimize database
vps-configurator optimize
```

**Issue 4: Security Alert**

```bash
# Check security status
vps-configurator security status

# Run CIS scan
vps-configurator security cis-scan

# Check file integrity
vps-configurator security file-integrity-check

# View security events
vps-configurator audit query --event-type SECURITY_ALERT
```

---

## Conclusion

This workflow analysis blueprint provides a comprehensive guide to understanding and implementing the complete DevOps infinity loop for the Debian VPS Configurator project. The system demonstrates enterprise-grade practices across all phases:

### Key Takeaways

1. **Plan**: Comprehensive documentation with 35 documents and clear implementation guides
2. **Code**: Modern Python 3.12+ with modular plugin architecture and strong typing
3. **Build**: Automated CI/CD with multi-version testing and package validation
4. **Test**: Pyramid strategy with 200+ unit tests, 50+ integration tests, 10+ E2E tests
5. **Release**: Semantic versioning with automated GitHub releases
6. **Deploy**: Multiple deployment strategies with rollback capabilities
7. **Operate**: Health checks, dry-run mode, circuit breakers, and graceful degradation
8. **Monitor**: Activity tracking, audit logging, DORA metrics, and compliance reporting

### Implementation Patterns to Follow

- ✅ Always use dependency injection for testability
- ✅ Register rollback actions for all state changes
- ✅ Validate all inputs with whitelist approach
- ✅ Use circuit breakers for network operations
- ✅ Log with structured format and appropriate levels
- ✅ Test at multiple levels (unit, integration, E2E)
- ✅ Document with what/why/how format
- ✅ Monitor with comprehensive observability

### Next Steps for New Developers

1. Start with [Project_Architecture_Blueprint.md](Project_Architecture_Blueprint.md)
2. Review [exemplars.md](exemplars.md) for code examples
3. Read implementation prompts in docs/01-implementation/
4. Follow templates in this document to add new features
5. Run tests to verify changes: `pytest tests/ -v`
6. Use troubleshooting guide when issues arise

**Remember**: This project embodies the DevOps infinity loop. Every change flows through the complete cycle, with continuous feedback driving improvement.

---

**Document Version:** 1.0
**Last Updated:** January 16, 2026
**Maintained By:** DevOps Expert Agent
**Next Review:** February 16, 2026
