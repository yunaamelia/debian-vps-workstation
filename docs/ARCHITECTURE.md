# System Architecture

The Debian VPS Configurator is a modular, event-driven system designed to automate the setup of a developer workstation.

## Core Components

### 1. Installer Engine (`configurator.core`)
The heart of the system, responsible for orchestrating the installation process.
- **Installer**: Orchestrates the overall flow (Validate -> Plan -> Install -> Verify).
- **Container**: A lightweight Dependency Injection (DI) container that manages service lifecycles.
- **ConfigManager**: Handles configuration loading, validation, and profile management.
- **RollbackManager**: Tracks changes and executes rollback procedures on failure.

### 2. Module System (`configurator.modules`)
The system functionality is divided into independent modules (e.g., `SystemModule`, `PythonModule`, `DockerModule`).
- **ConfigurationModule (Base)**: The abstract base class defining the `validate`, `configure`, and `verify` lifecycle.
- **Dependency Management**: Modules declare dependencies (`depends_on`), enabling a Directed Acyclic Graph (DAG) for execution order.

### 3. Parallel Execution Engine
Optimizes installation time by executing independent modules concurrently.
- **DependencyGraph**: Builds and validates the DAG of modules.
- **ParallelModuleExecutor**: Executes batches of independent modules using a thread pool.
- **Locking**: Thread-safe mechanisms (e.g., `file_lock`) ensure mutually exclusive access to shared resources like APT.

### Package Cache System
### 6. Package Cache
A local caching layer (`PackageCacheManager`) stores downloaded `.deb` packages and external resources to speed up re-installation and rollback. It uses hash verification and LRU eviction (max 10GB by default).

### 7. Lazy Loading
To optimize CLI responsiveness, the system uses a `LazyLoader` proxy and PEP 562 for the module registry. This defers the loading of heavy dependencies (like `Installer`, `DockerModule`, etc.) until they are actually required by a command, reducing startup time from ~2s to <0.2s.

### CLI (`configurator.cli`)
The user interface built with `click` and `rich`.
- **Commands**: `install`, `wizard`, `verify`, `rollback`, `cache`.
- **Interactive Wizard**: Guides users through configuration profiles.

## Data Flow

1.  **Initialization**: CLI loads `config.yaml` and initializes the `Container`.
2.  **Validation**: `SystemValidator` checks OS version and root privileges.
3.  **Planning**: `Installer` builds the `DependencyGraph` and determines the execution order (Batches).
4.  **Execution**:
    - `ParallelModuleExecutor` processes batches.
    - Each `Module` executes `validate()` -> `configure()` -> `verify()`.
    - `install_packages()` in modules leverages `PackageCacheManager` to optimize downloads.
5.  **Completion**: `ProgressReporter` summarizes results.

## Directory Structure

```
debian-vps-workstation/
├── config/                 # Configuration files (default.yaml, schemas)
├── configurator/
│   ├── core/               # Core logic (Installer, Container, Cache)
│   ├── modules/            # Feature modules (base.py, etc.)
│   ├── plugins/            # Plugin system
│   ├── utils/              # Helper utilities (process, file, net)
│   ├── cli.py              # CLI entry point
│   └── wizard.py           # Interactive wizard
├── docs/                   # Documentation
├── tests/                  # Unit and Integration tests
└── tools/                  # Helper scripts (benchmarks, etc.)
```
