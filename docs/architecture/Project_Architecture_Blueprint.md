# Project Architecture Blueprint

**Generated:** January 16, 2026
**Project Type:** Python 3.12+ CLI Application
**Architecture Pattern:** Modular Plugin Architecture with Layered Core
**Version:** v2.0
**Status:** Production-Ready

---

## Table of Contents

1. [Architecture Detection and Analysis](#1-architecture-detection-and-analysis)
2. [Architectural Overview](#2-architectural-overview)
3. [Architecture Visualization](#3-architecture-visualization)
4. [Core Architectural Components](#4-core-architectural-components)
5. [Architectural Layers and Dependencies](#5-architectural-layers-and-dependencies)
6. [Data Architecture](#6-data-architecture)
7. [Cross-Cutting Concerns](#7-cross-cutting-concerns-implementation)
8. [Service Communication Patterns](#8-service-communication-patterns)
9. [Python-Specific Architectural Patterns](#9-python-specific-architectural-patterns)
10. [Implementation Patterns](#10-implementation-patterns)
11. [Testing Architecture](#11-testing-architecture)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Extension and Evolution Patterns](#13-extension-and-evolution-patterns)
14. [Architectural Pattern Examples](#14-architectural-pattern-examples)
15. [Architectural Decision Records](#15-architectural-decision-records)
16. [Architecture Governance](#16-architecture-governance)
17. [Blueprint for New Development](#17-blueprint-for-new-development)

---

## 1. Architecture Detection and Analysis

### Technology Stack Identification

**Primary Language:** Python 3.12+ (detected via `pyproject.toml`)

**Core Dependencies:**

- **CLI Framework:** Click 8.1+ (command-line interface)
- **Rich Output:** Rich 13.0+ (terminal formatting), Textual 0.40+ (TUI)
- **Configuration:** PyYAML 6.0+ (YAML parsing), Pydantic (validation)
- **SSH/Remote:** Paramiko 3.3+ (SSH operations)
- **Security:** cryptography 41.0+ (encryption), python-gnupg (GPG)
- **Monitoring:** psutil 5.9+ (system metrics)
- **Graphs:** NetworkX 3.1+ (dependency graphs)

**Project Structure Analysis:**

```
configurator/
├── cli.py              # Entry point (3,509 lines, 106 commands)
├── core/               # 18 files - orchestration layer
├── modules/            # 24 files - feature implementations
├── security/           # 20 files - security subsystem
├── rbac/               # 5 files - access control
├── users/              # 5 files - user management
├── utils/              # 9 files - shared utilities
├── observability/      # Monitoring & metrics
└── plugins/            # Plugin system
```

### Architectural Pattern Detection

**Primary Pattern:** **Modular Plugin Architecture** with **Layered Core**

**Evidence:**

1. **Plugin Pattern:** All 24 modules inherit from `ConfigurationModule` base class
2. **Template Method:** Base class defines `validate() → configure() → verify()` lifecycle
3. **Dependency Injection:** `Container` class manages service resolution
4. **Circuit Breaker:** Network operations protected by `CircuitBreakerManager`
5. **Strategy Pattern:** Multiple implementations of package managers, editors, languages
6. **Observer Pattern:** Hooks system allows lifecycle observation
7. **Command Pattern:** CLI commands encapsulate operations with undo (rollback)

**Secondary Patterns:**

- **Repository Pattern:** Abstract data access (user registry, team registry)
- **Factory Pattern:** Module instantiation via container factories
- **Facade Pattern:** Simplified interfaces for complex subsystems (SSHManagerWrapper)
- **Decorator Pattern:** Retry and circuit breaker decorators
- **Singleton Pattern:** Lazy-loaded services via container

---

## 2. Architectural Overview

### High-Level Architecture Description

The Debian VPS Configurator implements a **resilient, modular, plugin-based architecture** designed for automated VPS configuration with enterprise-grade reliability. The system transforms a base Debian 13 installation into a fully-configured development workstation through orchestrated execution of independent modules.

### Guiding Principles

1. **Resilience First**

   - Circuit breakers protect against cascading failures
   - Exponential backoff retry for transient errors
   - Graceful degradation when services unavailable
   - Comprehensive rollback on failure

2. **Fail-Fast with Safety**

   - Validate prerequisites before execution
   - Dry-run mode for testing without changes
   - Transaction-like rollback for state changes
   - Beginner-friendly error messages (WHAT/WHY/HOW)

3. **Performance Optimization**

   - Parallel module execution (45 min → 15 min)
   - Lazy loading (sub-100ms CLI startup)
   - Package caching (50-90% bandwidth savings)
   - Dependency graph optimization

4. **Security by Default**

   - Supply chain validation (checksums, signatures)
   - Input validation (prevent injection attacks)
   - RBAC with principle of least privilege
   - Comprehensive audit logging

5. **Developer Experience**
   - Self-documenting code with docstrings
   - Rich terminal output with progress bars
   - Interactive wizard for beginners
   - Extensive validation (400+ checks)

### Architectural Boundaries

**Strict Boundaries Enforced:**

- Core cannot import specific modules (prevents circular dependencies)
- Modules cannot directly communicate (only via core orchestrator)
- Security layer validates all external inputs
- RBAC enforces permission boundaries

**Abstraction Mechanisms:**

- `ConfigurationModule` abstract base class
- Dependency injection via `Container`
- Interface segregation (small, focused interfaces)
- Configuration-driven behavior

### Hybrid Pattern Adaptations

**Layered + Plugin Hybrid:**

- Core layers (Presentation, Orchestration, Persistence) combined with plugin modules
- Modules can have internal layers but present unified interface
- Allows both vertical (layers) and horizontal (modules) scaling

**Event-Driven + Imperative:**

- Primarily imperative execution flow
- Hooks system provides event-driven extension points
- Observer pattern for lifecycle events

---

## 3. Architecture Visualization

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  CLI (Click)          │  TUI (Textual)    │  Wizard (Interactive)│
│  - 106 commands       │  - Visual UI      │  - Guided setup      │
│  - Lazy loading       │  - Progress bars  │  - Profile selection │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER (Core)                     │
├─────────────────────────────────────────────────────────────────┤
│  Installer           │  DependencyGraph   │  Container (DI)      │
│  - Module ordering   │  - Parallel batches│  - Service registry  │
│  - Execution control │  - Topological sort│  - Lifecycle mgmt    │
├─────────────────────────────────────────────────────────────────┤
│  HooksManager        │  PluginManager     │  ConfigManager       │
│  - Lifecycle hooks   │  - Plugin discovery│  - Multi-layer config│
│  - Pre/post events   │  - Dynamic loading │  - Profile system    │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODULE LAYER (Plugins)                      │
├─────────────────────────────────────────────────────────────────┤
│ 📦 Core          │ 💻 Languages    │ 🛠️  Tools       │ 📝 Editors   │
│ - System (p:10)  │ - Python (p:40) │ - Docker (p:50) │ - VSCode(60) │
│ - Security(p:20) │ - Node.js(p:41) │ - Git (p:51)    │ - Cursor(61) │
│ - RBAC (p:25)    │ - Golang (p:42) │ - Databases(52) │ - Neovim(62) │
│ - Desktop(p:30)  │ - Rust (p:43)   │ - DevOps (p:53) │              │
│                  │ - Java (p:44)   │ - Utils (p:54)  │ 🌐 Network   │
│                  │ - PHP (p:45)    │                 │ - WireGuard  │
│                  │                 │ 📊 Monitor      │ - Caddy      │
│                  │                 │ - Netdata(p:80) │              │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RESILIENCE & SAFETY LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  CircuitBreaker     │  RollbackManager   │  RetryDecorator      │
│  - Fail-fast        │  - Transaction log │  - Exponential       │
│  - Auto recovery    │  - Undo actions    │  - Jitter            │
├─────────────────────────────────────────────────────────────────┤
│  PackageCache       │  LazyLoader        │  ParallelExecutor    │
│  - Local .deb cache │  - Import deferral │  - ThreadPool        │
│  - 50-90% bandwidth │  - Sub-100ms start │  - Batch scheduling  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CROSS-CUTTING CONCERNS                        │
├─────────────────────────────────────────────────────────────────┤
│ 🔒 Security          │ 📝 Logging         │ ⚙️  Configuration    │
│ - Input validation   │ - Structured logs  │ - Multi-source       │
│ - Supply chain check │ - Audit trail      │ - Profile system     │
│ - RBAC enforcement   │ - Metrics/tracing  │ - Environment vars   │
├─────────────────────────────────────────────────────────────────┤
│ 🔐 Authentication    │ 📊 Monitoring      │ ✅ Validation        │
│ - SSH keys           │ - Health checks    │ - System prereqs     │
│ - MFA/2FA            │ - Alerting         │ - Input sanitization │
│ - Certificate mgmt   │ - Performance      │ - Schema validation  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Command
    │
    ▼
┌──────────────┐
│ CLI Parser   │ (Click)
│ (cli.py)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────────┐
│ ConfigManager│─────►│ Profile Loader  │
└──────┬───────┘      └─────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│           Installer                       │
│  ┌────────────────────────────────────┐  │
│  │ 1. Validate System Prerequisites   │  │
│  │    - OS version, RAM, disk space   │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 2. Build Dependency Graph          │  │
│  │    - Kahn's algorithm              │  │
│  │    - Detect circular deps          │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 3. Generate Parallel Batches       │  │
│  │    - Group by priority             │  │
│  │    - Respect dependencies          │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 4. Execute Batches in Parallel     │  │
│  │    - ThreadPoolExecutor            │  │
│  │    - Monitor progress              │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 5. Verify All Modules              │  │
│  │    - Run verify() for each         │  │
│  │    - Generate report               │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Data Flow Diagram

````
Configuration Sources
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│config/       │  │config/       │  │User Config   │  │CLI Args      │
│default.yaml  │  │profiles/*.yaml│  │custom.yaml   │  │--option=value│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                  │                  │                  │
       └──────────────────┴──────────────────┴──────────────────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │ConfigManager │
                          │Merge & Validate│
                          └──────┬───────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌──────────────┐          ┌──────────────┐        ┌──────────────┐
│Module Config │          │Security      │        │RBAC Config   │
│Extract       │          │Config Extract│        │Extract       │
└──────┬───────┘          └──────┬───────┘        └──────┬───────┘
       │                         │                         │
       ▼                         ▼                         ▼
┌──────────────┐          ┌──────────────┐        ┌──────────────┐
│Module        │          │Security      │        │RBAC Manager  │
│Instances     │          │Validators    │        │              │
└──────────────┘          └──────────────┘        └──────────────┘

Runtime State
┌──────────────┐          ┌──────────────┐        ┌──────────────┐
│Rollback      │          │Circuit       │        │Package Cache │
│Actions       │          │Breaker State │        │(.deb files)  │
│(JSON)        │          │(Memory)      │        │(Disk)        │
└──────────────┘          └──────────────┘        └──────────────┘
```

---

## 4. Core Architectural Components

### 4.1 ConfigurationModule (Base Class)

**Location:** `configurator/modules/base.py` (662 lines)

**Purpose:** Abstract base class providing contract and toolkit for all 24 feature modules.

**Key Responsibilities:**
- Define lifecycle template (`validate()` → `configure()` → `verify()`)
- Provide resilient wrapper methods for common operations
- Manage dependency injection of core services
- Thread-safe APT operations via `_APT_LOCK`
- Integrate observability (metrics, structured logging)

**Design Patterns Used:**
- **Template Method:** Defines algorithm skeleton, subclasses fill in steps
- **Dependency Injection:** Constructor accepts all dependencies
- **Facade:** Simplifies complex operations (install_packages_resilient)

**Interface Contract:**
```python
class ConfigurationModule(ABC):
    # Module metadata
    name: str
    description: str
    priority: int                  # Execution order (lower = earlier)
    depends_on: List[str]          # Module dependencies
    force_sequential: bool = False # Must run alone
    mandatory: bool = False        # Failure stops installation

    # Lifecycle methods (must implement)
    @abstractmethod
    def validate(self) -> bool:
        """Check prerequisites"""

    @abstractmethod
    def configure(self) -> bool:
        """Execute installation/configuration"""

    @abstractmethod
    def verify(self) -> bool:
        """Verify success"""
```

**Evolution Patterns:**
- New modules extend `ConfigurationModule`
- Override lifecycle methods
- Use inherited utilities (run, install_packages, enable_service)
- Register rollback actions for state changes

### 4.2 Installer (Orchestrator)

**Location:** `configurator/core/installer.py` (586 lines)

**Purpose:** Central orchestrator managing module execution lifecycle.

**Key Responsibilities:**
- Validate system prerequisites (OS version, RAM, disk)
- Load and register modules via dependency injection
- Build dependency graph and detect circular dependencies
- Generate parallel execution batches
- Execute modules with progress reporting
- Handle errors and trigger rollback

**Internal Structure:**
```python
class Installer:
    def __init__(self, config, logger, reporter, container):
        self.rollback_manager = RollbackManager()
        self.validator = SystemValidator()
        self.hooks_manager = HooksManager()
        self.plugin_manager = PluginManager()
        self.dry_run_manager = DryRunManager()
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.package_cache_manager = PackageCacheManager()

        # Register 24 modules
        self._register_modules()

    def install(self, parallel=True, dry_run=False):
        # 1. Validate system
        # 2. Build dependency graph
        # 3. Generate batches
        # 4. Execute in parallel/sequential
        # 5. Verify all modules
```

**Interaction Patterns:**
- Publishes hooks: `pre_install`, `post_module`, `post_install`
- Creates module instances via container
- Reports progress via `ProgressReporter`
- Coordinates rollback on failure

### 4.3 DependencyGraph & ParallelExecutor

**Location:** `configurator/core/parallel.py` (468 lines)

**Purpose:** Optimize installation time through parallel execution.

**Key Features:**
- **Kahn's Algorithm:** Topological sort with level grouping
- **Circular Dependency Detection:** Prevents deadlocks
- **Force Sequential:** Respects heavy modules (e.g., desktop)
- **Batch Scheduling:** Groups independent modules

**Performance Impact:**
- Sequential: ~45 minutes
- Parallel: ~15 minutes (3x speedup)

**Implementation:**
```python
class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()  # NetworkX directed graph
        self.module_info: Dict[str, ModuleDependency] = {}

    def add_module(self, name, depends_on, force_sequential):
        self.graph.add_node(name)
        for dep in depends_on:
            self.graph.add_edge(dep, name)

    def get_parallel_batches(self) -> List[List[str]]:
        """Use Kahn's algorithm for topological sort"""
        batches = []
        in_degree = dict(self.graph.in_degree())

        while in_degree:
            # Find nodes with no dependencies
            batch = [n for n, d in in_degree.items() if d == 0]
            if not batch:
                raise ValueError("Circular dependency detected")

            # Separate force_sequential modules
            # Add to batches
            # Update in_degree

        return batches
```

### 4.4 Container (Dependency Injection)

**Location:** `configurator/core/container.py` (200 lines)

**Purpose:** Service locator and dependency injection container.

**Key Features:**
- **Singleton Services:** Created once, cached (e.g., ConfigManager)
- **Factory Services:** Created per request (e.g., Module instances)
- **Mock Support:** Override services for testing
- **Circular Dependency Detection:** Prevents resolution loops

**Usage Pattern:**
```python
# Registration (in Installer.__init__)
container.singleton('config', lambda: ConfigManager())
container.factory('docker_module',
    lambda c: DockerModule(
        config=c.get('config'),
        logger=c.get('logger'),
        rollback_manager=c.get('rollback_manager'),
        # ... more dependencies
    )
)

# Resolution
config = container.get('config')
docker = container.get('docker_module')
```

### 4.5 CircuitBreakerManager & RetryDecorator

**Location:** `configurator/utils/circuit_breaker.py` (312 lines), `configurator/utils/retry.py` (100 lines)

**Purpose:** Network resilience and fault tolerance.

**Circuit Breaker States:**
```
CLOSED ─────failure──────► OPEN ────timeout────► HALF_OPEN
  │         (3 failures)      │                      │
  │                           │                      │
  └────success (recovery)◄────┴──success (test ok)──┘
```

**Configuration:**
```python
CircuitBreakerConfig(
    failure_threshold=3,      # Failures before opening
    success_threshold=1,      # Successes to close
    timeout=60.0,            # Seconds before retry
    expected_exceptions=(NetworkError, TimeoutError)
)
```

**Retry Decorator:**
```python
@retry(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,    # Exponential backoff
    jitter=True            # Add randomness
)
def install_package(name):
    # Will retry 3 times with delays: 1s, 2s, 4s
    apt_install(name)
```

### 4.6 RollbackManager

**Location:** `configurator/core/rollback.py` (259 lines)

**Purpose:** Transaction-like rollback for system changes.

**Supported Actions:**
- `add_command(rollback_cmd)` - Execute shell command
- `add_file_restore(backup, original)` - Restore file
- `add_package_remove(packages)` - Uninstall packages
- `add_service_stop(service)` - Stop systemd service

**Execution Model:**
```python
# During installation
rollback_manager.add_command("systemctl stop docker")
rollback_manager.add_package_remove(["docker-ce"])
rollback_manager.add_file_restore("/tmp/backup.conf", "/etc/docker/daemon.json")

# On failure
rollback_manager.execute_rollback()  # Executes in LIFO order
```

**State Persistence:**
- Saves to `/var/lib/debian-vps-configurator/rollback-state.json`
- Survives process crashes
- Can resume partial rollback

### 4.7 ConfigManager

**Location:** `configurator/config.py` (511 lines)

**Purpose:** Multi-layer configuration management with profiles.

**Configuration Sources (precedence order):**
1. `config/default.yaml` - Base defaults
2. `config/profiles/{profile}.yaml` - Profile overrides (beginner/intermediate/advanced)
3. User config file (`--config` flag)
4. CLI arguments (`--option=value`)

**Key Features:**
- Dot notation access: `config.get("system.hostname")`
- Type-safe defaults with comprehensive schema
- Profile system simplifies beginner experience
- Validation ensures consistency

**Profile Differences:**
```yaml
# Beginner profile
languages:
  golang: {enabled: false}
  rust: {enabled: false}
tools:
  neovim: {enabled: false}

# Advanced profile
languages:
  golang: {enabled: true}
  rust: {enabled: true}
tools:
  neovim: {enabled: true}
```

### 4.8 Security Subsystem

**Components:**
- `SupplyChainValidator` - Verify checksums & signatures
- `InputValidator` - Prevent injection attacks
- `SSHKeyManager` - Manage SSH keys
- `CertificateManager` - SSL/TLS certificates
- `MFAManager` - Multi-factor authentication
- `VulnerabilityScanner` - CVE scanning

**Supply Chain Security:**
```python
validator = SupplyChainValidator(config, logger)

# Verify APT key fingerprint
validator.verify_apt_key_fingerprint(
    key_path="/etc/apt/keyrings/docker.asc",
    expected_fingerprint="9DC8..."
)

# Verify download checksum
validator.verify_download(
    url="https://github.com/...",
    expected_sha256="abc123..."
)
```

### 4.9 RBAC System

**Location:** `configurator/rbac/rbac_manager.py` (482 lines)

**Purpose:** Role-based access control with wildcards.

**Permission Model:**
```
Format: scope:resource:action
Examples:
  system:*:*           # Full system access
  service:docker:read  # Read docker service
  file:/etc/*:write    # Write to /etc/
```

**Predefined Roles:**
- `admin` - Full access (system:*:*)
- `developer` - Dev tools (docker, code)
- `operator` - Service management
- `readonly` - Read-only access

**Integration:**
```python
rbac = RBACManager(config, logger)

# Check permission
if rbac.check_permission(user, "service:docker:execute"):
    start_docker()

# Assign role
rbac.assign_role(username, "developer")
    - **Dependency Rule**: Inherits from `core` base classes. Uses `utils`.

4.  **Utility Layer (`configurator/utils/`)**:
    - Pure functions and helpers for low-level system interaction (network, files, apt).
    - **Dependency Rule**: No upward dependencies.

## 6. Data Architecture

- **Configuration**: Uses `Pydantic` models to define and validate the configuration schema. This ensures strong typing and validation of user inputs (`config.yaml`).
- **State Management**: Runtime state (installed packages, started services) is tracked in-memory within Module instances and persisted to the `RollbackManager`.

## 7. Cross-Cutting Concerns Implementation

### Error Handling and Resilience

- **Pattern**: Operations that can fail transiently (network) are wrapped in decorators (`@retry`) or Managers (`CircuitBreakerManager`).
- **Implementation**: `install_packages_resilient` in `base.py` automatically handles APT locks, network timeouts, and retries.

### Logging and Observability

- **Pattern**: Structured Logging.
- **Implementation**: `StructuredLogger` provides context-aware logging. Metrics are collected for operation duration and success rates.

### Extension

- **Pattern**: Hook System.
- **Implementation**: Users can drop shell scripts into `/etc/debian-vps-configurator/hooks.d/` to interfere with the process without modifying code.

## 8. Service Communication Patterns

Since this is a CLI tool, "Service Communication" primarily refers to:

- **Subprocess Calls**: Communicating with the OS via `run_command` (subprocess wrapper).
- **SSH**: Uses `paramiko` for remote execution (if applicable in specific modes).

## 9. Python Architectural Patterns

- **Abstract Base Classes (ABC)**: Used for `ConfigurationModule` to enforce interface implementation.
- **Decorators**: Extensively used for retry logic (`@retry`) and hook registration (`@pre_install`).
- **Context Managers**: Used for resource locking (e.g., `_APT_LOCK`).

## 10. Architectural Pattern Examples

### Base Module Implementation

```python
class ConfigurationModule(ABC):
    def __init__(self, config, ...):
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.rollback_manager = RollbackManager()

    @abstractmethod
    def configure(self) -> bool:
        """Execute configuration."""

    def install_packages_resilient(self, packages: List[str]) -> bool:
        """Installs with circuit breaker and rollback registration."""
        with self._APT_LOCK:
             success = self.network.apt_install_with_retry(packages)
             if success:
                 self.rollback_manager.add_package_remove(packages)
        return success
````

### Hook Registration

```python
@pre_install(priority=10)
def check_requirements(context):
    if not has_internet():
        raise PrerequisiteError("No internet connection")
```

## 11. Testing Architecture

- **Unit Tests**: Mock system calls (subprocess, file system) to test module logic in isolation.
- **Integration Tests**: Run in a containerized environment (Docker/LXC) to verify actual package installation and service startup.
- **Dry Run**: The architecture natively supports a `DryRunManager` which mocks all side-effects (commands, file writes) allowing safe logic verification.

## 12. Extension and Evolution Patterns

### Feature Addition Patterns (Adding a New Module)

To add support for a new tool (e.g., "Kubernetes"):

1.  Create `configurator/modules/kubernetes.py`.
2.  Inherit from `ConfigurationModule`.
3.  Implement `validate()` (check OS version), `configure()` (install kubectl), `verify()` (kubectl version).
4.  Add to the module registry or import in `cli.py`.

### Modification Patterns

- **Hooks**: Prefer using Hooks for site-specific customizations instead of modifying core code.
- **Config**: Add new keys to `config_schema.py` effectively versioning the configuration capability.

## 13. Architecture Governance

- **Linting**: Enforced via `ruff`.
- **Typing**: Enforced via `mypy` (as seen in `pyproject.toml`).
- **Code formatting**: Enforced via `isort` / `ruff`.

## 14. Blueprint for New Development

### Development Workflow

1.  **Define Requirement**: E.g., "Add support for Redis".
2.  **Create Module**: `configurator/modules/redis.py`.
3.  **Implement Lifecycle**:
    - `validate()`: Check if port 6379 is free.
    - `configure()`: `self.install_packages_resilient(["redis-server"])`, `self.enable_service("redis-server")`.
    - `verify()`: `self.run("redis-cli ping")`.
4.  **Register**: Ensure the module is discoverable.
5.  **Test**: Add a test case in `tests/modules/test_redis.py` using `DryRunManager`.

### Common Pitfalls

- **Bypassing Resilient Wrappers**: Do not use `subprocess.run` directly. Use `self.run()`, which handles logging, dry-run, and rollback.
- **Ignoring Rollback**: Always register a rollback action when changing state (creating files, installing packages).
- **Blocking the GI**: For extensive operations, ensure they don't block the UI thread (if using the TUI mode), though mostly this runs sequentially.


---

## Blueprint Maintenance

**Generated:** January 16, 2026
**Last Updated:** January 16, 2026
**Version:** 2.0

### Keeping This Blueprint Current

**Update Triggers:**
- Major architectural changes (new layers, patterns)
- Addition of cross-cutting concerns
- New ADRs (Architectural Decision Records)
- Quarterly review (minimum)

**Update Process:**
1. Review codebase changes since last update
2. Update relevant sections
3. Add new ADRs for significant decisions
4. Regenerate diagrams if structure changed
5. Update version and date

**Regeneration Command:**
```bash
# Use the architecture blueprint generator prompt
# Located in: .github/prompts/architecture-blueprint-generator.prompt.md
```

**Contact:**
- Architecture questions: Open GitHub Discussion
- Propose changes: Submit PR to `.github/prompts/`
- Security concerns: See SECURITY.md

---

**End of Project Architecture Blueprint**
