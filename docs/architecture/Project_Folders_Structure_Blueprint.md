# Project Folder Structure Blueprint

**Generated:** January 16, 2026
**Project Type:** Python 3.12+ CLI Application
**Architecture:** Modular Plugin-Based Layered Architecture
**Version:** 2.0

---

## Table of Contents

1. [Technology Detection & Overview](#1-technology-detection--overview)
2. [Structural Overview](#2-structural-overview)
3. [Directory Visualization](#3-directory-visualization)
4. [Key Directory Analysis](#4-key-directory-analysis)
5. [File Placement Patterns](#5-file-placement-patterns)
6. [Naming and Organization Conventions](#6-naming-and-organization-conventions)
7. [Navigation and Development Workflow](#7-navigation-and-development-workflow)
8. [Build and Output Organization](#8-build-and-output-organization)
9. [Python-Specific Organization](#9-python-specific-organization)
10. [Extension and Evolution](#10-extension-and-evolution)
11. [Structure Templates](#11-structure-templates)
12. [Structure Enforcement](#12-structure-enforcement)

---

## 1. Technology Detection & Overview

### Technology Signatures Detected

**Primary Technology:** Python 3.12+

**Evidence:**

- `pyproject.toml` (PEP 518/621 project configuration)
- `requirements.txt` and `requirements-dev.txt` (pip dependencies)
- `pytest.ini` (pytest configuration)
- `.pre-commit-config.yaml` (pre-commit hooks)
- Python package structure (`configurator/__init__.py`)

**Project Type:** Single Python Package (Not a monorepo)

**Microservices:** Not detected (Monolithic CLI application)

**Frontend:** Not detected (CLI-only application)

### File Statistics

- **Python Source Files:** 104 files in `configurator/`
- **Test Files:** 133 files in `tests/`
- **Documentation Files:** 59 Markdown files in `docs/`
- **Total Directories:** 53 directories (excluding generated)

---

## 2. Structural Overview

### Organizational Principles

The project follows a **hybrid layered + modular architecture** with clear separation:

1. **Layer-Based Organization** (Vertical)

   - Presentation Layer: `configurator/cli.py`, `configurator/wizard.py`
   - Orchestration Layer: `configurator/core/`
   - Module Layer: `configurator/modules/`
   - Foundation Layer: `configurator/utils/`, `configurator/security/`, `configurator/rbac/`

2. **Domain-Based Organization** (Horizontal)

   - Core concerns: `configurator/core/` (installer, container, rollback)
   - Security domain: `configurator/security/` (20 files)
   - RBAC domain: `configurator/rbac/` (5 files)
   - User management: `configurator/users/` (5 files)
   - Observability: `configurator/observability/` (metrics, alerting)

3. **Feature-Based Modules** (Plugins)
   - Each module is self-contained in `configurator/modules/`
   - 24 independent feature modules (docker, git, python, etc.)
   - Plugin system for extensibility

### Architectural Rationale

**Why This Structure:**

- **Dependency Enforcement:** Layers prevent circular dependencies
- **Independent Testing:** Each layer can be tested in isolation
- **Parallel Development:** Modules can be developed independently
- **Clear Boundaries:** Layer separation enforces architectural rules
- **Extensibility:** Plugin architecture allows community contributions

---

## 3. Directory Visualization

### Complete Project Structure

```
debian-vps-workstation/
├── .github/                          # GitHub-specific files
│   ├── copilot-instructions.md      # Copilot guidance (864 lines)
│   ├── prompts/                      # Prompt templates
│   │   ├── architecture-blueprint-generator.prompt.md
│   │   ├── copilot-instructions-blueprint-generator.prompt.md
│   │   └── folder-structure-blueprint-generator.prompt.md
│   └── skills/                       # AI agent skills
│       ├── appinsights-instrumentation/
│       ├── azure-resource-visualizer/
│       └── [8 more skill directories]
│
├── config/                           # Configuration files
│   ├── default.yaml                  # Base configuration (220 lines)
│   └── profiles/                     # User profiles
│       ├── beginner.yaml             # Minimal features
│       ├── intermediate.yaml         # Balanced features
│       └── advanced.yaml             # Full features
│
├── configurator/                     # Main Python package (104 files)
│   ├── __init__.py                   # Package marker, version export
│   ├── __main__.py                   # Entry point (python -m configurator)
│   ├── cli.py                        # CLI commands (3,509 lines, 106 commands)
│   ├── cli_monitoring.py             # Monitoring CLI commands
│   ├── wizard.py                     # Interactive TUI wizard
│   ├── config.py                     # Configuration management (511 lines)
│   ├── config_schema.py              # Configuration schema validation
│   ├── constants.py                  # Global constants
│   ├── exceptions.py                 # Custom exception hierarchy
│   ├── logger.py                     # Logging configuration
│   │
│   ├── core/                         # Orchestration layer (18 files)
│   │   ├── __init__.py
│   │   ├── installer.py              # Module orchestrator (586 lines)
│   │   ├── container.py              # DI container (200 lines)
│   │   ├── dependencies.py           # Dependency graph
│   │   ├── parallel.py               # Parallel execution (468 lines)
│   │   ├── rollback.py               # Transaction rollback (259 lines)
│   │   ├── hooks.py                  # Lifecycle hooks
│   │   ├── lazy_loader.py            # Lazy import system
│   │   ├── package_cache.py          # APT package caching
│   │   ├── dryrun.py                 # Dry-run mode
│   │   ├── validator.py              # System validation
│   │   ├── reporter.py               # Progress reporting
│   │   ├── health.py                 # Health checks
│   │   ├── network.py                # Network utilities
│   │   ├── secrets.py                # Secret management
│   │   ├── audit.py                  # Audit logging
│   │   └── file_integrity.py         # File integrity checks
│   │
│   ├── modules/                      # Feature modules (24 files)
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract base class (662 lines)
│   │   ├── system.py                 # System configuration (priority: 10)
│   │   ├── security.py               # Security hardening (priority: 20)
│   │   ├── rbac.py                   # RBAC setup (priority: 25)
│   │   ├── desktop.py                # Desktop environment (priority: 30)
│   │   ├── python.py                 # Python ecosystem (priority: 40)
│   │   ├── nodejs.py                 # Node.js (priority: 41)
│   │   ├── golang.py                 # Go language (priority: 42)
│   │   ├── rust.py                   # Rust language (priority: 43)
│   │   ├── java.py                   # Java ecosystem (priority: 44)
│   │   ├── php.py                    # PHP (priority: 45)
│   │   ├── docker.py                 # Docker & Compose (priority: 50)
│   │   ├── git.py                    # Git VCS (priority: 51)
│   │   ├── databases.py              # PostgreSQL, MySQL (priority: 52)
│   │   ├── devops.py                 # DevOps tools (priority: 53)
│   │   ├── utilities.py              # System utilities (priority: 54)
│   │   ├── vscode.py                 # VS Code (priority: 60)
│   │   ├── cursor.py                 # Cursor IDE (priority: 61)
│   │   ├── neovim.py                 # Neovim (priority: 62)
│   │   ├── wireguard.py              # VPN (priority: 70)
│   │   ├── caddy.py                  # Web server (priority: 71)
│   │   └── netdata.py                # Monitoring (priority: 80)
│   │
│   ├── observability/                # Monitoring & metrics
│   │   ├── __init__.py
│   │   ├── metrics.py                # Prometheus-style metrics
│   │   ├── tracing.py                # Distributed tracing
│   │   ├── alerting.py               # Alert management (228 lines)
│   │   └── structured_logger.py      # Structured logging
│   │
│   ├── plugins/                      # Plugin system
│   │   ├── __init__.py
│   │   └── loader.py                 # Plugin discovery & loading
│   │
│   ├── rbac/                         # Role-Based Access Control (5 files)
│   │   ├── __init__.py
│   │   ├── rbac_manager.py           # RBAC engine (482 lines)
│   │   ├── permissions.py            # Permission system
│   │   ├── sudo_policy.py            # Sudo policy management
│   │   └── registry.py               # Role registry
│   │
│   ├── security/                     # Security subsystem (20 files)
│   │   ├── __init__.py
│   │   ├── input_validator.py        # Input sanitization
│   │   ├── supply_chain.py           # Supply chain validation (870 lines)
│   │   ├── ssh_manager.py            # SSH key management (205 lines)
│   │   ├── ssh_hardening.py          # SSH hardening (59 lines)
│   │   ├── ssh_manager_wrapper.py    # SSH manager facade
│   │   ├── certificate_manager.py    # SSL/TLS certificates (174 lines)
│   │   ├── ssl_manager.py            # SSL management
│   │   ├── mfa_manager.py            # MFA/2FA (115 lines)
│   │   ├── mfa_manager_wrapper.py    # MFA facade
│   │   ├── vulnerability_scanner.py  # CVE scanning (493 lines)
│   │   ├── firewall.py               # Firewall configuration
│   │   ├── audit_logger.py           # Security audit logging
│   │   ├── encryption.py             # Data encryption utilities
│   │   ├── compliance.py             # Compliance checks
│   │   └── cis_checks/               # CIS benchmark checks
│   │       ├── __init__.py
│   │       ├── level1.py
│   │       └── level2.py
│   │
│   ├── users/                        # User management (5 files)
│   │   ├── __init__.py
│   │   ├── lifecycle_manager.py      # User lifecycle
│   │   ├── registry.py               # User registry
│   │   ├── team_manager.py           # Team management (137 lines)
│   │   └── temp_access.py            # Temporary access (136 lines)
│   │
│   └── utils/                        # Utility functions (9 files)
│       ├── __init__.py
│       ├── command.py                # Command execution wrapper
│       ├── circuit_breaker.py        # Circuit breaker (312 lines)
│       ├── retry.py                  # Retry decorator (100 lines)
│       ├── file_operations.py        # File utilities
│       ├── network.py                # Network utilities
│       ├── system.py                 # System utilities
│       ├── apt.py                    # APT package manager wrapper
│       └── validators.py             # Generic validators
│
├── docs/                             # Documentation (59 files)
│   ├── ARCHITECTURE.md               # High-level architecture
│   ├── CLI-REFERENCE.md              # CLI command reference
│   ├── MIGRATION-v2.md               # Migration guide
│   ├── SECURITY.md                   # Security documentation
│   ├── XRDP-XFCE-ZSH-GUIDE.md        # Desktop setup guide
│   ├── optimized-failfast-workflow.md
│   │
│   ├── 00-project-overview/          # Project overview docs
│   ├── 01-implementation/            # Implementation details
│   │   ├── phase-1-architecture/
│   │   ├── phase-2-security/
│   │   └── phase-3-user-management/
│   ├── 03-operations/                # Operational guides
│   ├── 04-planning/                  # Planning documents
│   ├── advanced/                     # Advanced topics
│   ├── community/                    # Community guidelines
│   ├── configuration/                # Configuration guides
│   ├── implementation/               # Implementation reports
│   ├── implementation-reports/       # Detailed reports
│   ├── installation/                 # Installation guides
│   ├── modules/                      # Module documentation
│   ├── rbac/                         # RBAC documentation
│   ├── reviews/                      # Code reviews
│   ├── security/                     # Security guides
│   ├── testing/                      # Testing guides
│   └── troubleshooting/              # Troubleshooting guides
│
├── scripts/                          # Deployment & validation scripts
│   ├── bootstrap.sh                  # Initial bootstrap
│   ├── deploy.sh                     # Main deployment
│   ├── deploy_and_validate.sh        # Deploy with validation
│   ├── deploy_with_circuit_breaker.sh
│   ├── remote_setup.sh               # Remote server setup
│   ├── diagnose.py                   # Diagnostic tool
│   ├── debug_runner.py               # Debug mode runner
│   ├── verify.sh                     # Verification script
│   ├── validate_phase1.sh            # Phase 1 validation
│   ├── validate_phase2.sh            # Phase 2 validation
│   ├── validate_phase3.sh            # Phase 3 validation
│   ├── validate_phase4_comprehensive.sh
│   ├── run_phase1_tests.sh           # Phase-specific tests
│   ├── run_phase2_tests.sh
│   ├── run_phase3_tests.sh
│   ├── run_phase4_tests.sh
│   ├── run_phase5_tests.sh
│   ├── verify_desktop_standalone.py
│   ├── verify_fix.py
│   ├── file-integrity-check.service  # Systemd service
│   └── file-integrity-check.timer    # Systemd timer
│
├── tests/                            # Test suite (133 files)
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration & fixtures
│   │
│   ├── unit/                         # Unit tests (~350 tests, <1s)
│   │   ├── test_config.py
│   │   ├── test_container.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_retry.py
│   │   ├── test_rollback.py
│   │   └── [30+ more test files]
│   │
│   ├── integration/                  # Integration tests (~50 tests)
│   │   ├── test_docker_integration.py
│   │   ├── test_git_integration.py
│   │   ├── test_security_integration.py
│   │   └── [10+ more test files]
│   │
│   ├── e2e/                          # End-to-end tests
│   │   └── test_full_install.py
│   │
│   ├── modules/                      # Module-specific tests
│   │   ├── test_docker.py
│   │   ├── test_python.py
│   │   └── [20+ module tests]
│   │
│   ├── security/                     # Security tests
│   │   ├── test_input_validation.py
│   │   ├── test_supply_chain.py
│   │   ├── test_ssh_hardening.py
│   │   └── [5+ security tests]
│   │
│   ├── system/                       # System-level tests
│   │   └── test_system_validator.py
│   │
│   ├── performance/                  # Performance benchmarks
│   │   ├── test_parallel_execution.py
│   │   ├── test_lazy_loading.py
│   │   └── test_cache_performance.py
│   │
│   ├── resilience/                   # Resilience tests
│   │   ├── test_circuit_breaker_behavior.py
│   │   ├── test_retry_logic.py
│   │   └── test_rollback_scenarios.py
│   │
│   ├── validation/                   # Validation test suites (400+ checks)
│   │   ├── prompt_2_1/
│   │   ├── prompt_2_2/
│   │   └── prompt_2_3/
│   │
│   ├── manual/                       # Manual test scenarios
│   │   └── desktop_verification.md
│   │
│   ├── visual/                       # Visual regression tests
│   │
│   └── fixtures/                     # Test fixtures & data
│       ├── sample_plugin/
│       ├── test_configs/
│       └── mock_data/
│
├── tools/                            # Development & deployment tools
│   ├── benchmark_cache.py            # Cache benchmarking
│   ├── benchmark_lazy_loading.py     # Lazy load benchmarks
│   ├── benchmark_parallel.py         # Parallel execution benchmarks
│   ├── deploy_local_code.py          # Local deployment
│   ├── deploy_on_server.sh           # Server deployment
│   ├── deploy_with_monitoring.py     # Monitored deployment
│   ├── diagnose_failures.py          # Failure diagnostics
│   ├── failfast_orchestrator.py      # Fail-fast orchestration
│   ├── monitor_install_with_checkpoint.py
│   ├── prepare_manual_deployment.sh
│   ├── prompt.md                     # Prompt templates
│   ├── remote_debug.py               # Remote debugging
│   ├── remote_deploy.py              # Remote deployment
│   ├── retry_deployment.sh           # Retry logic
│   ├── run_remote_test.py            # Remote test execution
│   ├── stress_test.py                # Stress testing
│   └── update_checksums.py           # Checksum updater
│
├── Project_Architecture_Blueprint.md # Architecture documentation (805 lines)
├── Project_Folders_Structure_Blueprint.md # This file
├── exemplars.md                      # Code exemplars (9 patterns)
├── CONTRIBUTING.md                   # Contribution guidelines
├── README.md                         # Project README
├── LICENSE                           # MIT License
├── AUDIT_REPORT.md                   # Security audit report
├── pyproject.toml                    # PEP 518/621 project config
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── quick-install.sh                  # Quick installation script
└── .pre-commit-config.yaml           # Pre-commit hooks

Total: 53 directories, 300+ files
```

---

## 4. Key Directory Analysis

### Root Level (`/`)

**Purpose:** Project metadata and entry points

**Contents:**

- Configuration files (pyproject.toml, pytest.ini)
- Documentation (README.md, CONTRIBUTING.md, LICENSE)
- Quick start scripts (quick-install.sh)
- Architecture blueprints (Project_Architecture_Blueprint.md, exemplars.md)

**Conventions:**

- Root level kept minimal
- Only essential files at top level
- Detailed content in subdirectories

---

### `configurator/` - Main Package

**Purpose:** Primary Python package containing all application code

**Structure:** 104 Python files organized into 8 subpackages

**Key Files:**

- `__init__.py` - Package initialization, exports version
- `__main__.py` - Entry point for `python -m configurator`
- `cli.py` - CLI commands (3,509 lines, 106 commands)
- `wizard.py` - Interactive TUI using Textual
- `config.py` - Multi-layer configuration system
- `exceptions.py` - Custom exception hierarchy

**Organizational Pattern:** Layer-based with domain separation

---

### `configurator/core/` - Orchestration Layer

**Purpose:** Core business logic and orchestration

**Contents:** 18 files, ~5,000 lines of code

**Key Components:**

| File               | Lines | Purpose                                        |
| ------------------ | ----- | ---------------------------------------------- |
| `installer.py`     | 586   | Module orchestrator, main entry point          |
| `parallel.py`      | 468   | Parallel execution engine                      |
| `rollback.py`      | 259   | Transaction-like rollback system               |
| `container.py`     | 200   | Dependency injection container                 |
| `package_cache.py` | -     | APT package caching (50-90% bandwidth savings) |
| `hooks.py`         | -     | Lifecycle hook system                          |
| `lazy_loader.py`   | -     | Lazy import for <100ms startup                 |

**Dependency Rule:** Can import from utils, security, rbac. **CANNOT** import from modules (prevents circular dependencies).

**Pattern:** Composition over inheritance - services composed together

---

### `configurator/modules/` - Feature Modules

**Purpose:** Self-contained feature implementations (plugin architecture)

**Contents:** 24 independent modules + 1 base class

**Module Structure Pattern:**

```python
class <Name>Module(ConfigurationModule):
    name = "Display Name"
    priority = 50  # Execution order (10-90)
    depends_on = ["system", "security"]

    def validate(self) -> bool:
        # Check prerequisites

    def configure(self) -> bool:
        # Execute installation

    def verify(self) -> bool:
        # Verify success
```

**Priority Levels:**

- 10-20: Core system (system, security)
- 25-30: RBAC, desktop
- 40-49: Languages (python, nodejs, golang, rust, java, php)
- 50-59: Tools (docker, git, databases, devops, utilities)
- 60-69: Editors (vscode, cursor, neovim)
- 70-79: Networking (wireguard, caddy)
- 80-89: Monitoring (netdata)

**Isolation:** Modules CANNOT import other modules directly

---

### `configurator/security/` - Security Subsystem

**Purpose:** Security-critical functionality

**Contents:** 20 files, ~2,500 lines of specialized security code

**Key Components:**

| Component                  | Lines | Purpose                         |
| -------------------------- | ----- | ------------------------------- |
| `supply_chain.py`          | 870   | Checksum & signature validation |
| `vulnerability_scanner.py` | 493   | CVE scanning                    |
| `rbac_manager.py`          | 482   | Role-based access control       |
| `ssh_manager.py`           | 205   | SSH key management              |
| `certificate_manager.py`   | 174   | SSL/TLS certificate management  |
| `mfa_manager.py`           | 115   | Multi-factor authentication     |

**Subdirectory:**

- `cis_checks/` - CIS benchmark compliance checks (Level 1 & 2)

**Pattern:** Defense in depth - multiple security layers

---

### `configurator/rbac/` - RBAC Domain

**Purpose:** Role-Based Access Control implementation

**Contents:** 5 files implementing complete RBAC system

**Components:**

- `rbac_manager.py` - Main RBAC engine with wildcard permissions
- `permissions.py` - Permission model (`scope:resource:action`)
- `sudo_policy.py` - Sudo policy generation
- `registry.py` - Role registry persistence

**Permission Format:**

```
system:*:*           # Full system access
service:docker:read  # Read docker service
file:/etc/*:write    # Write to /etc/
```

---

### `configurator/utils/` - Utility Layer

**Purpose:** Reusable utility functions (no dependencies)

**Contents:** 9 files of pure functions

**Key Utilities:**

- `command.py` - Safe command execution wrapper
- `circuit_breaker.py` - Circuit breaker pattern (312 lines)
- `retry.py` - Retry decorator with exponential backoff
- `file_operations.py` - File manipulation utilities
- `apt.py` - APT package manager wrapper with locking

**Pattern:** Pure functions, no state, no upward dependencies

---

### `config/` - Configuration Files

**Purpose:** YAML configuration management

**Structure:**

```
config/
├── default.yaml         # Base configuration (all defaults)
└── profiles/
    ├── beginner.yaml    # Minimal features (cloud VPS)
    ├── intermediate.yaml # Balanced setup
    └── advanced.yaml     # Full development stack
```

**Profile System:**

- `beginner`: Fewer languages, faster install
- `intermediate`: Common tools, balanced
- `advanced`: All features, local workstation

**Precedence:** CLI args > User config > Profile > Default

---

### `tests/` - Test Suite

**Purpose:** Comprehensive test coverage

**Contents:** 133 test files, 400+ test cases

**Organization by Type:**

| Directory      | Purpose               | Test Count | Speed   |
| -------------- | --------------------- | ---------- | ------- |
| `unit/`        | Isolated logic tests  | ~350       | <1s     |
| `integration/` | Component interaction | ~50        | Seconds |
| `e2e/`         | Full workflow         | ~5         | Minutes |
| `modules/`     | Module-specific       | ~24        | Varies  |
| `security/`    | Security validation   | ~15        | Fast    |
| `performance/` | Benchmarks            | ~10        | Slow    |
| `resilience/`  | Failure scenarios     | ~8         | Fast    |
| `validation/`  | System validation     | 400+       | Hours   |

**Test Structure Pattern:**

```python
class Test<ComponentName>:
    """Tests for <ComponentName>."""

    def test_<what_it_tests>(self, fixtures):
        """Test that <specific behavior>."""
        # Given
        # When
        # Then
```

**Fixtures:** Centralized in `conftest.py` and `fixtures/`

---

### `docs/` - Documentation

**Purpose:** Comprehensive project documentation

**Contents:** 59 Markdown files organized by topic

**Organization:**

- **Numbered Phases:** `00-project-overview/`, `01-implementation/`, etc.
- **By Topic:** `security/`, `modules/`, `rbac/`, `testing/`
- **By Audience:** `installation/`, `configuration/`, `advanced/`
- **Living Docs:** `implementation-reports/`, `reviews/`

**Key Documents:**

- `ARCHITECTURE.md` - High-level architecture overview
- `CLI-REFERENCE.md` - Complete CLI command reference
- `MIGRATION-v2.md` - v1 to v2 migration guide
- `SECURITY.md` - Security policies and procedures

**Pattern:** Docs co-located with related features when possible

---

### `scripts/` - Operational Scripts

**Purpose:** Deployment, validation, and maintenance scripts

**Categories:**

**Deployment:**

- `deploy.sh` - Main deployment script
- `deploy_and_validate.sh` - Deploy with full validation
- `bootstrap.sh` - Initial bootstrap
- `remote_setup.sh` - Remote server setup

**Validation:**

- `validate_phase1.sh` through `validate_phase4_comprehensive.sh`
- `verify.sh` - Post-installation verification
- `verify_desktop_standalone.py` - Desktop environment checks

**Diagnostics:**

- `diagnose.py` - Comprehensive diagnostic tool
- `debug_runner.py` - Debug mode execution
- `verify_fix.py` - Verify fixes applied

**Systemd Services:**

- `file-integrity-check.service` - File integrity monitoring
- `file-integrity-check.timer` - Scheduled integrity checks

---

### `tools/` - Development Tools

**Purpose:** Development and debugging utilities

**Categories:**

**Benchmarking:**

- `benchmark_cache.py` - Package cache performance
- `benchmark_lazy_loading.py` - Import time benchmarks
- `benchmark_parallel.py` - Parallel execution benchmarks
- `stress_test.py` - System stress testing

**Deployment:**

- `deploy_local_code.py` - Local code deployment
- `remote_deploy.py` - Remote deployment automation
- `deploy_with_monitoring.py` - Monitored deployments
- `retry_deployment.sh` - Retry failed deployments

**Debugging:**

- `remote_debug.py` - Remote debugging sessions
- `diagnose_failures.py` - Failure analysis
- `failfast_orchestrator.py` - Fail-fast testing

**Utilities:**

- `update_checksums.py` - Update supply chain checksums
- `monitor_install_with_checkpoint.py` - Checkpoint monitoring

---

## 5. File Placement Patterns

### Configuration Files

**Root Level:**

- `pyproject.toml` - Project configuration (PEP 518/621)
- `pytest.ini` - Test configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies

**config/ Directory:**

- `default.yaml` - Base configuration with all options
- `profiles/*.yaml` - Profile-specific overrides

**Pattern:** Global config at root, user config in dedicated directory

---

### Model/Entity Definitions

**Location:** Co-located with their domain

**Examples:**

- User entities: `configurator/users/lifecycle_manager.py`
- Role entities: `configurator/rbac/rbac_manager.py`
- Rollback actions: `configurator/core/rollback.py`

**Pattern:** Use dataclasses for entities

```python
@dataclass
class User:
    username: str
    status: UserStatus
    created_at: datetime = field(default_factory=datetime.now)
```

---

### Business Logic

**Service Layer:**

- Core services: `configurator/core/*_manager.py`
- Security services: `configurator/security/*_manager.py`
- User services: `configurator/users/*_manager.py`

**Module Logic:**

- Feature logic: `configurator/modules/<feature>.py`
- Self-contained within module file

**Utilities:**

- Pure functions: `configurator/utils/*.py`
- No business logic in utils (helpers only)

---

### Interface Definitions

**Abstract Base Classes:**

- `configurator/modules/base.py` - ConfigurationModule ABC
- Protocols defined inline when needed

**Pattern:** ABC for inheritance, Protocol for structural typing

```python
# ABC pattern (inheritance)
class ConfigurationModule(ABC):
    @abstractmethod
    def configure(self) -> bool:
        pass

# Protocol pattern (structural)
class Validator(Protocol):
    def validate(self) -> bool: ...
```

---

### Test Files

**Location Pattern:** Mirror source structure in `tests/`

**Unit Tests:**

```
configurator/core/installer.py
tests/unit/test_installer.py
```

**Integration Tests:**

```
configurator/modules/docker.py
tests/integration/test_docker_integration.py
```

**Naming Convention:**

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_it_tests>`

**Test Fixtures:**

- Shared fixtures: `tests/conftest.py`
- Test data: `tests/fixtures/`
- Sample plugins: `tests/fixtures/sample_plugin/`

---

### Documentation Files

**Root Level:**

- `README.md` - Project introduction
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - MIT license
- `AUDIT_REPORT.md` - Security audit
- `Project_Architecture_Blueprint.md` - Architecture details
- `exemplars.md` - Code examples

**docs/ Directory:**

- Organized by phase, topic, and audience
- Each major feature has its own subdirectory
- Guides in `docs/<topic>/`
- Implementation reports in `docs/implementation-reports/`

**Module Documentation:**

- `docs/modules/<module_name>.md` for each module

---

## 6. Naming and Organization Conventions

### File Naming Patterns

**Python Files:**

- **snake_case** for all Python files
- Descriptive names: `vulnerability_scanner.py`, `lifecycle_manager.py`
- Manager suffix for service classes: `*_manager.py`
- Test prefix: `test_*.py`

**Configuration Files:**

- **kebab-case** for shell scripts: `quick-install.sh`
- **snake_case** for Python config: `config_schema.py`
- **.yaml** extension for YAML files

**Documentation:**

- **UPPERCASE** for important root docs: `README.md`, `CONTRIBUTING.md`
- **kebab-case** for guides: `cli-reference.md`
- **PascalCase** for architecture docs: `Project_Architecture_Blueprint.md`

---

### Folder Naming Patterns

**Primary Pattern:** **snake_case** throughout

**Examples:**

- `configurator/` (package name)
- `implementation-reports/` (hyphenated phrases)
- `00-project-overview/` (numbered phases)
- `cis_checks/` (underscores for multi-word)

**Grouping:**

- Tests grouped by type: `unit/`, `integration/`, `e2e/`
- Docs grouped by topic: `security/`, `modules/`, `rbac/`
- Profiles grouped in: `config/profiles/`

---

### Namespace/Module Patterns

**Package Structure:**

```python
configurator/               # Top-level package
├── core/                   # configurator.core
│   ├── installer.py        # configurator.core.installer
│   └── rollback.py         # configurator.core.rollback
├── modules/                # configurator.modules
│   ├── base.py             # configurator.modules.base
│   └── docker.py           # configurator.modules.docker
└── utils/                  # configurator.utils
    └── command.py          # configurator.utils.command
```

**Import Patterns:**

**Absolute imports** (preferred):

```python
from configurator.core.installer import Installer
from configurator.modules.base import ConfigurationModule
from configurator.exceptions import ModuleExecutionError
```

**Relative imports** (within same package):

```python
from .base import ConfigurationModule
from ..utils.command import run_command
```

**Lazy imports** (for performance):

```python
ConfigManager = LazyLoader("configurator.config", "ConfigManager")
```

---

### Organizational Patterns

**Code Co-location:**

- Keep related code together
- Module = single file unless >700 lines
- Split large modules by responsibility

**Feature Encapsulation:**

- Each module is self-contained
- Dependencies declared explicitly
- No cross-module imports

**Cross-Cutting Concerns:**

- Logging: `configurator/logger.py` + per-module loggers
- Config: `configurator/config.py` (centralized)
- Exceptions: `configurator/exceptions.py` (hierarchy)
- Security: `configurator/security/` (dedicated subsystem)

---

## 7. Navigation and Development Workflow

### Entry Points

**For Users:**

1. `quick-install.sh` - Quick installation script
2. `README.md` - Project introduction
3. `docs/installation/` - Detailed installation guides

**For Developers:**

1. `CONTRIBUTING.md` - Contribution guidelines
2. `Project_Architecture_Blueprint.md` - Architecture overview (805 lines)
3. `exemplars.md` - Code examples (9 patterns)
4. `.github/copilot-instructions.md` - Coding standards (864 lines)

**For Code Execution:**

1. `configurator/cli.py` - CLI entry point (106 commands)
2. `configurator/__main__.py` - Package entry point
3. `configurator/wizard.py` - Interactive wizard

---

### Common Development Tasks

#### Adding a New Module

**1. Create module file:**

```bash
# Location: configurator/modules/redis.py
```

**2. Extend base class:**

```python
from configurator.modules.base import ConfigurationModule

class RedisModule(ConfigurationModule):
    name = "Redis"
    priority = 52
    depends_on = ["system"]

    def validate(self) -> bool:
        # Check prerequisites

    def configure(self) -> bool:
        # Install and configure

    def verify(self) -> bool:
        # Verify installation
```

**3. Register in installer:**

```python
# configurator/core/installer.py
from configurator.modules.redis import RedisModule

def _register_modules(self):
    module_classes = {
        # ... existing modules
        "redis": RedisModule,
    }
```

**4. Add tests:**

```python
# tests/unit/test_redis.py
class TestRedisModule:
    def test_validate(self):
        # Test validation logic

    def test_configure(self):
        # Test configuration logic
```

**5. Add documentation:**

```bash
# docs/modules/redis.md
```

---

#### Extending Existing Functionality

**Location depends on type:**

**Core functionality:**

- Add to `configurator/core/<component>.py`
- Update tests in `tests/unit/test_<component>.py`

**Security feature:**

- Add to `configurator/security/<feature>.py`
- Add tests in `tests/security/test_<feature>.py`

**Utility function:**

- Add to `configurator/utils/<category>.py`
- Keep functions pure (no side effects)

---

#### Adding New Tests

**Unit Test:**

```bash
# Location: tests/unit/test_<component>.py
# Pattern: Mirror source structure
configurator/core/cache.py → tests/unit/test_cache.py
```

**Integration Test:**

```bash
# Location: tests/integration/test_<feature>_integration.py
# Mark as slow: @pytest.mark.integration
```

**Validation Test:**

```bash
# Location: tests/validation/<phase>/
# 400+ validation checks organized by deployment phase
```

---

#### Configuration Modifications

**Add new configuration option:**

**1. Update default config:**

```yaml
# config/default.yaml
new_feature:
  enabled: true
  option: value
```

**2. Update schema (optional):**

```python
# configurator/config_schema.py
```

**3. Update profile configs:**

```yaml
# config/profiles/beginner.yaml
new_feature:
  enabled: false # Disable for beginners
```

**4. Document:**

```markdown
# docs/configuration/new-feature.md
```

---

### Dependency Patterns

**Dependency Flow:**

```
CLI (cli.py)
  ↓
Core (installer.py, container.py)
  ↓
Modules (docker.py, git.py, ...)
  ↓
Foundation (utils, security, rbac)
  ↓
External (APT, systemd, filesystem)
```

**Import Rules:**

- **Never** import upward in the hierarchy
- **Never** import modules from other modules
- **Always** use dependency injection for services

**Container Registration:**

```python
# configurator/core/installer.py
container.singleton('config', lambda: ConfigManager())
container.factory('docker_module',
    lambda c: DockerModule(
        config=c.get('config'),
        logger=c.get('logger'),
        rollback_manager=c.get('rollback_manager')
    )
)
```

---

### Content Statistics

**By Directory:**

| Directory                | Python Files | Lines of Code | Purpose            |
| ------------------------ | ------------ | ------------- | ------------------ |
| `configurator/`          | 104          | ~15,000       | Main application   |
| `configurator/core/`     | 18           | ~5,000        | Orchestration      |
| `configurator/modules/`  | 24           | ~6,000        | Feature modules    |
| `configurator/security/` | 20           | ~2,500        | Security subsystem |
| `tests/`                 | 133          | ~8,000        | Test suite         |
| `docs/`                  | 59 (MD)      | ~25,000       | Documentation      |
| `scripts/`               | 20           | ~2,000        | Deployment scripts |
| `tools/`                 | 15           | ~1,500        | Development tools  |

**Code Distribution:**

- Core orchestration: 33% (5,000 / 15,000)
- Feature modules: 40% (6,000 / 15,000)
- Security: 17% (2,500 / 15,000)
- Other: 10% (1,500 / 15,000)

**Complexity Concentration:**

- Highest: `cli.py` (3,509 lines, 106 commands)
- High: `supply_chain.py` (870 lines), `base.py` (662 lines)
- Medium: Most modules (200-400 lines each)
- Low: Utilities (50-100 lines per file)

---

## 8. Build and Output Organization

### Build Configuration

**Primary Build Tool:** pip/setuptools (via pyproject.toml)

**Build Files:**

- `pyproject.toml` - Modern Python project configuration (PEP 518/621)
- `requirements.txt` - Production dependencies (pinned versions)
- `requirements-dev.txt` - Development dependencies

**Build Commands:**

```bash
# Development install (editable)
pip install -e .

# Production install
pip install .

# With dev dependencies
pip install -e ".[dev]"
```

---

### Output Structure

**Python Bytecode:**

```
configurator/
├── __pycache__/           # Compiled .pyc files (ignored in git)
│   ├── __init__.cpython-312.pyc
│   ├── cli.cpython-312.pyc
│   └── ...
└── ...
```

**Test Artifacts:**

```
.pytest_cache/             # Pytest cache (ignored)
htmlcov/                   # Coverage reports (generated)
.coverage                  # Coverage data file
```

**Distribution Packages:**

```bash
dist/
├── debian_vps_configurator-2.0.0.tar.gz
└── debian_vps_configurator-2.0.0-py3-none-any.whl
```

---

### Environment-Specific Builds

**Development:**

```bash
# Editable install with dev dependencies
pip install -e ".[dev]"

# Environment: Development mode
export VPS_DEBUG=true
export VPS_DRY_RUN=true
```

**Production:**

```bash
# Regular install, production dependencies only
pip install .

# Environment: Production mode
export VPS_PROFILE=beginner
export VPS_LOG_LEVEL=INFO
```

**Testing:**

```bash
# With test dependencies
pip install -e ".[dev]"
pytest

# With coverage
pytest --cov=configurator --cov-report=html
```

---

## 9. Python-Specific Organization

### Package Structure

**Standard Python Package Layout:**

```
debian-vps-workstation/
├── configurator/          # Main package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Make package executable
│   ├── *.py               # Top-level modules
│   └── */                 # Subpackages
├── tests/                 # Test package (separate from src)
├── docs/                  # Documentation
├── scripts/               # Executable scripts
├── tools/                 # Development tools
├── pyproject.toml         # Project metadata (PEP 518/621)
└── README.md
```

**Rationale:**

- Tests separate from source (common in Python)
- Flat is better than nested (Zen of Python)
- Scripts in dedicated directory (not in package)

---

### Module Organization

**Import Hierarchy:**

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
from configurator.exceptions import ModuleExecutionError
from configurator.utils.command import run_command
```

**Enforced by:** ruff (linter)

---

### Resource Organization

**No Embedded Resources Currently**

**Pattern for Future:**

```
configurator/
└── resources/
    ├── templates/         # File templates
    ├── schemas/           # JSON/YAML schemas
    └── data/              # Static data files
```

---

### Package Management

**pyproject.toml Structure:**

```toml
[project]
name = "debian-vps-configurator"
version = "2.0.0"
description = "Automated Debian VPS configuration"
requires-python = ">=3.12"

dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "textual>=0.40.0",
    # ... more dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[project.scripts]
vps-configurator = "configurator.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["configurator*"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
```

**Version Management:**

- Semantic versioning (Major.Minor.Patch)
- Version in `configurator/__init__.py`
- Synced with git tags

---

## 10. Extension and Evolution

### Extension Points

#### Adding New Modules

**Plugin System:**

```
/etc/vps-configurator/plugins/
└── custom_module.py       # User-provided plugin

# Automatically discovered by PluginManager
```

**Structure:**

```python
# custom_module.py
from configurator.modules.base import ConfigurationModule

class CustomModule(ConfigurationModule):
    name = "Custom Feature"
    priority = 55
    depends_on = ["system"]

    def validate(self) -> bool:
        return True

    def configure(self) -> bool:
        # Custom logic
        return True

    def verify(self) -> bool:
        return True
```

**Registration:** Automatic via plugin discovery

---

#### Hook System

**Custom Hooks:**

```bash
# Location: /etc/vps-configurator/hooks.d/
└── pre_install.sh         # Executed before installation
└── post_module_docker.sh  # After docker module
└── post_install.sh        # After all modules
```

**Python Hooks:**

```python
from configurator.core.hooks import hooks_manager, HookType

@hooks_manager.register(HookType.PRE_INSTALL, priority=10)
def custom_validation(context):
    # Custom validation logic
    pass
```

---

### Scalability Patterns

**Breaking Down Large Modules:**

**Before (monolithic):**

```python
# configurator/modules/docker.py (1000+ lines)
class DockerModule(ConfigurationModule):
    # All Docker logic in one file
```

**After (split):**

```python
# configurator/modules/docker/
├── __init__.py
├── base.py                # Main module class
├── engine.py              # Docker engine setup
├── compose.py             # Docker Compose
├── registry.py            # Private registry
└── security.py            # Docker security
```

**Pattern:**

- Keep modules <700 lines
- Split by responsibility when exceeding
- Maintain single public interface

---

### Refactoring Patterns

**Layer Extraction:**

```python
# Before: Logic in module
class DockerModule(ConfigurationModule):
    def _validate_network(self):
        # Complex network validation
        pass

# After: Extract to utility
# configurator/utils/network.py
def validate_network_config(config):
    # Reusable validation
    pass

# configurator/modules/docker.py
from configurator.utils.network import validate_network_config

class DockerModule(ConfigurationModule):
    def _validate_network(self):
        return validate_network_config(self.config)
```

**Service Extraction:**

```python
# Before: Inline in module
class DockerModule(ConfigurationModule):
    def configure(self):
        # Inline rollback logic
        pass

# After: Use RollbackManager service
class DockerModule(ConfigurationModule):
    def __init__(self, rollback_manager):
        self.rollback_manager = rollback_manager

    def configure(self):
        self.rollback_manager.add_command("docker stop")
```

---

## 11. Structure Templates

### New Module Template

**File:** `configurator/modules/<module_name>.py`

```python
"""
<Module Name> module for <purpose>.

Handles:
- <Responsibility 1>
- <Responsibility 2>
- <Responsibility 3>
"""

from typing import Any, Dict, List, Optional
import logging

from configurator.modules.base import ConfigurationModule
from configurator.exceptions import ModuleExecutionError, PrerequisiteError


class <Name>Module(ConfigurationModule):
    """
    <One-line description>.

    <Detailed description>.
    """

    name = "<Display Name>"
    description = "<Brief description>"
    depends_on = ["system", "security"]  # Module dependencies
    priority = 50  # Execution order (10-90)
    mandatory = False  # Stop installation on failure?

    def validate(self) -> bool:
        """
        Validate prerequisites for <module>.

        Returns:
            True if ready to install

        Raises:
            PrerequisiteError: If prerequisites not met
        """
        self.logger.info(f"Validating {self.name} prerequisites...")

        # Check if already installed
        if self._is_installed():
            self.logger.info(f"{self.name} already installed")
            return False

        # Check disk space
        if not self.has_disk_space(5):  # GB
            raise PrerequisiteError(
                what=f"Insufficient disk space for {self.name}",
                why="At least 5GB free space required",
                how="Free up disk space and try again"
            )

        # Check dependencies
        for dep in self.depends_on:
            if not self.is_module_installed(dep):
                raise PrerequisiteError(
                    what=f"Dependency {dep} not installed",
                    why=f"{self.name} requires {dep}",
                    how=f"Install {dep} first"
                )

        return True

    def configure(self) -> bool:
        """
        Execute <module> installation and configuration.

        Returns:
            True if successful

        Raises:
            ModuleExecutionError: If installation fails
        """
        self.logger.info(f"Installing {self.name}...")

        try:
            # Step 1: Install packages
            self._install_packages()

            # Step 2: Configure
            self._configure_service()

            # Step 3: Start service
            self._start_service()

            self.logger.info(f"✓ {self.name} installed successfully")
            return True

        except Exception as e:
            raise ModuleExecutionError(
                what=f"Failed to install {self.name}",
                why=str(e),
                how="Check logs for details"
            )

    def verify(self) -> bool:
        """
        Verify <module> installation.

        Returns:
            True if verified successfully
        """
        self.logger.info(f"Verifying {self.name} installation...")

        # Check service running
        if not self.is_service_running("<service-name>"):
            self.logger.error(f"{self.name} service not running")
            return False

        # Check command available
        if not self.command_exists("<command>"):
            self.logger.error(f"{self.name} command not found")
            return False

        # Run test command
        result = self.run("<test-command>", check=False)
        if not result.success:
            self.logger.error(f"{self.name} test command failed")
            return False

        self.logger.info(f"✓ {self.name} verified")
        return True

    # Private helper methods

    def _is_installed(self) -> bool:
        """Check if already installed."""
        return self.command_exists("<command>")

    def _install_packages(self):
        """Install required packages."""
        packages = ["package1", "package2"]
        self.install_packages_resilient(packages)

    def _configure_service(self):
        """Configure the service."""
        # Write config file with rollback
        config_path = "/etc/<service>/config.conf"
        backup_path = config_path + ".backup"

        # Backup existing config
        if Path(config_path).exists():
            self.run(f"cp {config_path} {backup_path}")
            self.rollback_manager.add_file_restore(backup_path, config_path)

        # Write new config
        config_content = """
        # Configuration for <service>
        option = value
        """
        Path(config_path).write_text(config_content)

    def _start_service(self):
        """Start and enable service."""
        self.enable_service("<service-name>")
```

---

### New Test Template

**File:** `tests/unit/test_<module_name>.py`

```python
"""Tests for <Module Name> module."""

import pytest
from unittest.mock import Mock, patch

from configurator.modules.<module_name> import <Name>Module
from configurator.exceptions import ModuleExecutionError, PrerequisiteError


class Test<Name>Module:
    """Tests for <Name>Module."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "module": {
                "enabled": True,
                "option": "value"
            }
        }

    @pytest.fixture
    def module(self, config):
        """Create module instance."""
        return <Name>Module(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock()
        )

    def test_validate_success(self, module):
        """Test successful validation."""
        with patch.object(module, '_is_installed', return_value=False):
            with patch.object(module, 'has_disk_space', return_value=True):
                assert module.validate() is True

    def test_validate_already_installed(self, module):
        """Test validation when already installed."""
        with patch.object(module, '_is_installed', return_value=True):
            assert module.validate() is False

    def test_validate_insufficient_disk_space(self, module):
        """Test validation with insufficient disk space."""
        with patch.object(module, '_is_installed', return_value=False):
            with patch.object(module, 'has_disk_space', return_value=False):
                with pytest.raises(PrerequisiteError):
                    module.validate()

    def test_configure_success(self, module):
        """Test successful configuration."""
        with patch.object(module, '_install_packages'):
            with patch.object(module, '_configure_service'):
                with patch.object(module, '_start_service'):
                    assert module.configure() is True

    def test_configure_failure(self, module):
        """Test configuration failure."""
        with patch.object(module, '_install_packages', side_effect=Exception("Test error")):
            with pytest.raises(ModuleExecutionError):
                module.configure()

    def test_verify_success(self, module):
        """Test successful verification."""
        with patch.object(module, 'is_service_running', return_value=True):
            with patch.object(module, 'command_exists', return_value=True):
                with patch.object(module, 'run') as mock_run:
                    mock_run.return_value.success = True
                    assert module.verify() is True

    def test_verify_service_not_running(self, module):
        """Test verification when service not running."""
        with patch.object(module, 'is_service_running', return_value=False):
            assert module.verify() is False
```

---

### New Documentation Template

**File:** `docs/modules/<module_name>.md`

````markdown
# <Module Name> Module

## Overview

Brief description of what this module does and why it's useful.

## Prerequisites

- Dependency 1
- Dependency 2
- Minimum X GB disk space

## Features

- Feature 1
- Feature 2
- Feature 3

## Configuration

```yaml
# config/default.yaml
module_name:
  enabled: true
  option1: value1
  option2: value2
```
````

### Configuration Options

| Option    | Type    | Default    | Description            |
| --------- | ------- | ---------- | ---------------------- |
| `enabled` | boolean | `true`     | Enable this module     |
| `option1` | string  | `"value1"` | Description of option1 |

## Installation

### Automatic (Recommended)

```bash
vps-configurator install --module <module_name>
```

### Manual

1. Step 1
2. Step 2
3. Step 3

## Verification

Check if installed correctly:

```bash
vps-configurator verify --module <module_name>
```

## Usage

Example usage scenarios.

## Troubleshooting

### Issue 1

**Symptom:** Description of issue

**Cause:** Why it happens

**Solution:**

1. Step 1
2. Step 2

### Issue 2

...

## Related Modules

- [Module 1](module1.md)
- [Module 2](module2.md)

## References

- [Official Documentation](https://example.com)
- [GitHub Repository](https://github.com/example)

````

---

## 12. Structure Enforcement

### Structure Validation

**Automated Checks:**

**1. Linting (ruff):**
```bash
# Check code style and structure
ruff check configurator/

# Enforces:
# - Import order
# - Unused imports
# - Line length
# - Code style
````

**2. Type Checking (mypy):**

```bash
# Check type hints
mypy configurator/

# Enforces:
# - Type hints on public APIs
# - Correct type usage
# - Protocol compliance
```

**3. Pre-commit Hooks:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

**4. Test Coverage:**

```bash
# Enforce minimum coverage
pytest --cov=configurator --cov-fail-under=85
```

**5. Dependency Analysis:**

```python
# scripts/diagnose.py
def check_circular_dependencies():
    """Check for circular dependencies between modules."""
    # Parse imports
    # Build dependency graph
    # Detect cycles
```

---

### Documentation Practices

**Structural Changes:**

1. Update `Project_Architecture_Blueprint.md`
2. Update `Project_Folders_Structure_Blueprint.md` (this file)
3. Update relevant module documentation in `docs/`
4. Add ADR if significant decision made

**Documentation Requirements:**

- All new modules: Documentation in `docs/modules/`
- All new features: Update relevant guides
- Breaking changes: Update `MIGRATION-v2.md`
- Architecture changes: Update blueprints

**Review Process:**

1. PR must include documentation updates
2. Architecture review for layer changes
3. Test coverage must remain ≥85%
4. All checks must pass

---

### Structure Evolution History

**v1.0 → v2.0 Major Restructuring:**

**Changes Made:**

1. Split `installer.py` into orchestration layer (`core/`)
2. Extracted security into dedicated subsystem (`security/`)
3. Created RBAC domain (`rbac/`)
4. Added observability subsystem (`observability/`)
5. Introduced plugin system (`plugins/`)

**Rationale:**

- Better separation of concerns
- Clearer architectural boundaries
- Improved testability
- Enhanced security posture
- Enabled extensibility

**Migration Impact:**

- Import paths changed (documented in `MIGRATION-v2.md`)
- Configuration schema expanded
- Test structure reorganized
- Documentation restructured

---

## Blueprint Maintenance

**Generated:** January 16, 2026
**Last Updated:** January 16, 2026
**Version:** 2.0

### Keeping This Blueprint Current

**Update Triggers:**

- New directories added
- Significant file relocations
- Organizational pattern changes
- Major refactoring efforts
- Quarterly review (minimum)

**Update Process:**

1. Review new/modified directories since last update
2. Update visualization (section 3)
3. Update key directory analysis (section 4)
4. Update templates if patterns changed (section 11)
5. Document structural changes in section 12
6. Update version and date

**Regeneration Command:**

```bash
# Use the folder structure blueprint generator prompt
# Located in: .github/prompts/folder-structure-blueprint-generator.prompt.md
```

**Contact:**

- Structure questions: Open GitHub Discussion
- Propose changes: Submit PR
- Report issues: GitHub Issues

---

**End of Project Folder Structure Blueprint**
