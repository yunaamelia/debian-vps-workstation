# 🚀 Debian VPS Configurator v2.0

Enterprise-Grade Automated VPS Configuration, Security Hardening, and User Management System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-green.svg)](docs/)
[![Status](https://img.shields.io/badge/status-production--ready-green.svg)](https://github.com/yunaamelia/debian-vps-workstation)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://github.com/yunaamelia/debian-vps-workstation/actions)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Debian VPS Configurator** transforms a fresh Debian 13 VPS into a fully-featured, security-hardened remote desktop coding workstation in under 30 minutes.

### What It Does

- 🔒 **Security Hardening** — CIS benchmarks, UFW, Fail2ban, SSH hardening, 2FA/MFA
- 🖥️ **Desktop Environment** — XFCE + XRDP for remote desktop access
- 💻 **Development Tools** — Python, Node.js, Go, Rust, Java, PHP, Docker
- 👥 **User Management** — RBAC, lifecycle management, team collaboration
- 📊 **Monitoring** — Netdata, audit logging, anomaly detection

---

## Key Features

### 🏗️ Phase 1: Architecture & Performance

| Feature                | Description                 | Benefits                 |
| ---------------------- | --------------------------- | ------------------------ |
| **Parallel Execution** | Concurrent module execution | 5-10x faster             |
| **Circuit Breaker**    | Prevent cascading failures  | Graceful degradation     |
| **Package Caching**    | Local package cache         | 50-90% bandwidth savings |
| **Lazy Loading**       | On-demand module loading    | <100ms startup           |

### 🔒 Phase 2: Security & Compliance

| Feature                   | Description              | Benefits            |
| ------------------------- | ------------------------ | ------------------- |
| **CIS Benchmark Scanner** | 147 security checks      | 90%+ compliance     |
| **Vulnerability Scanner** | CVE integration          | Proactive detection |
| **SSL/TLS Manager**       | Let's Encrypt automation | Free HTTPS          |
| **2FA/MFA System**        | TOTP with backup codes   | Multi-factor auth   |

### 👥 Phase 3: User Management

| Feature              | Description                      | Benefits                |
| -------------------- | -------------------------------- | ----------------------- |
| **RBAC System**      | Role-based access control        | Least privilege         |
| **User Lifecycle**   | Automated onboarding/offboarding | Consistent provisioning |
| **Team Management**  | Shared directories, quotas       | Collaboration           |
| **Temporary Access** | Time-limited accounts            | Contractor management   |

---

## Technology Stack

### Core Technologies

| Component        | Version | Purpose                       |
| ---------------- | ------- | ----------------------------- |
| **Python**       | ≥3.11   | Primary language              |
| **Click**        | ≥8.1.7  | CLI framework (100+ commands) |
| **Rich**         | ≥13.9.4 | Terminal output formatting    |
| **Textual**      | ≥7.0.0  | Interactive TUI wizard        |
| **PyYAML**       | ≥6.0.2  | Configuration management      |
| **Pydantic**     | ≥2.12.0 | Data validation               |
| **Paramiko**     | ≥3.5.0  | SSH operations                |
| **Cryptography** | ≥46.0.0 | Encryption & security         |

### Development Tools

| Tool           | Version  | Purpose                        |
| -------------- | -------- | ------------------------------ |
| **pytest**     | ≥8.3.4   | Testing framework (200+ tests) |
| **Ruff**       | ≥0.14.11 | Linting & formatting           |
| **MyPy**       | ≥1.13.0  | Static type checking           |
| **pytest-cov** | ≥6.0.0   | Coverage reporting             |

### Key Capabilities

- ✅ **Type Hints** — Full type coverage with MyPy validation
- ✅ **Dependency Injection** — Container pattern for testability
- ✅ **Dataclasses** — Used for all data structures
- ✅ **Error Handling** — Custom exceptions with WHAT/WHY/HOW format
- ✅ **Resilience** — Circuit breaker + retry patterns

---

## Project Architecture

### Architectural Pattern: Modular Plugin-Based Layered

```text
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│         cli.py (100+ commands) │ wizard.py (TUI)            │
├─────────────────────────────────────────────────────────────┤
│                   ORCHESTRATION LAYER                        │
│    installer.py │ parallel.py │ rollback.py │ hooks.py      │
├─────────────────────────────────────────────────────────────┤
│                      FEATURE LAYER                           │
│          21+ self-contained ConfigurationModules             │
├─────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                          │
│         utils/ │ security/ │ validators/ │ rbac/            │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

| Pattern                  | Purpose                                          |
| ------------------------ | ------------------------------------------------ |
| **Circuit Breaker**      | Prevent cascading failures                       |
| **Lazy Loading**         | Fast startup (<100ms)                            |
| **Dependency Injection** | Testability & loose coupling                     |
| **Rollback Manager**     | Transaction-like undo                            |
| **Template Method**      | Module lifecycle (validate → configure → verify) |

📖 **Detailed Architecture:** [docs/architecture.md](docs/architecture.md)

---

## Quick Start

### Prerequisites

| Requirement | Minimum                     |
| ----------- | --------------------------- |
| **OS**      | Debian 12+ or Ubuntu 22.04+ |
| **Python**  | 3.11+                       |
| **RAM**     | 4 GB                        |
| **Disk**    | 50 GB SSD                   |

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yunaamelia/debian-vps-workstation.git
cd debian-vps-workstation

# 2. Run quick install (handles everything)
./quick-install.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Run installation
sudo vps-configurator install --profile beginner -y
```

### What Happens

1. ✅ System validation (OS, Python, disk, network)
2. ✅ Security hardening (UFW, Fail2ban, SSH)
3. ✅ Desktop environment (XFCE + XRDP)
4. ✅ Development tools (based on profile)
5. ✅ Verification of all components

**Total time:** ~15-30 minutes depending on network speed.

---

## Project Structure

```text
debian-vps-workstation/
├── configurator/              # Main package
│   ├── cli.py                 # CLI entry point (100+ commands)
│   ├── config.py              # Configuration management
│   ├── core/                  # Orchestration layer
│   │   ├── installer.py       # Main orchestrator
│   │   ├── rollback.py        # Rollback management
│   │   └── execution/         # Parallel/sequential execution
│   ├── modules/               # 21+ feature modules
│   │   ├── base.py            # Abstract base class
│   │   ├── docker.py          # Docker module
│   │   ├── security.py        # Security module
│   │   └── ...                # Other modules
│   ├── security/              # Security subsystem
│   ├── validators/            # Tiered validation
│   └── utils/                 # Utilities
│
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── security/              # Security tests
│
├── config/                    # Configuration
│   ├── default.yaml           # Default settings
│   └── profiles/              # beginner, intermediate, advanced
│
├── docs/                      # Documentation
│   ├── architecture.md        # Architecture blueprint
│   ├── exemplars.md           # Code exemplars
│   ├── Technology_Stack_Blueprint.md
│   ├── Project_Folders_Structure_Blueprint.md
│   └── Project_Workflow_Analysis_Blueprint.md
│
└── .github/                   # GitHub configuration
    ├── copilot-instructions.md
    ├── prompts/               # Prompt templates
    └── agents/                # AI agents
```

📖 **Detailed Structure:** [docs/Project_Folders_Structure_Blueprint.md](docs/Project_Folders_Structure_Blueprint.md)

---

## Development Workflow

### Feature Implementation Process

1. **Plan** — Update blueprints, create design
2. **Code** — Follow [copilot-instructions.md](.github/copilot-instructions.md)
3. **Test** — Unit → Integration → E2E
4. **Review** — Verify against blueprints
5. **Merge** — Update changelog, tag release

### Branch Strategy

| Branch      | Purpose               |
| ----------- | --------------------- |
| `main`      | Production-ready code |
| `develop`   | Integration branch    |
| `feature/*` | Feature development   |
| `hotfix/*`  | Urgent fixes          |

### Commit Convention

```text
feat: add new Docker module
fix: resolve SSH key generation issue
docs: update architecture blueprint
refactor: improve error handling in installer
test: add integration tests for rollback
```

📖 **Detailed Workflows:** [docs/Project_Workflow_Analysis_Blueprint.md](docs/Project_Workflow_Analysis_Blueprint.md)

---

## Coding Standards

### Quick Reference

```python
# ✅ Type hints required on all public APIs
def install_packages(packages: List[str], force: bool = False) -> bool:
    """Install packages with resilience."""
    pass

# ✅ Dependency injection for testability
def __init__(
    self,
    config: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
):
    self.config = config
    self.logger = logger or logging.getLogger(__name__)

# ✅ Custom exceptions with WHAT/WHY/HOW
raise ModuleExecutionError(
    what="Failed to install Docker",
    why="Package repository unavailable",
    how="Check network connection and retry"
)

# ✅ Register rollback BEFORE making changes
self.rollback_manager.add_package_remove(packages)
self.install_packages(packages)
```

### Naming Conventions

| Type      | Convention         | Example               |
| --------- | ------------------ | --------------------- |
| Classes   | `PascalCase`       | `ConfigurationModule` |
| Functions | `snake_case`       | `install_packages()`  |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT`     |
| Files     | `snake_case.py`    | `circuit_breaker.py`  |

📖 **Full Standards:** [.github/copilot-instructions.md](.github/copilot-instructions.md)

---

## Testing

### Test Structure

```text
tests/
├── unit/                  # Fast, isolated tests
├── integration/           # Component interaction tests
├── security/              # Security validation
├── validation/            # System validators
└── conftest.py            # Shared fixtures
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=configurator --cov-report=html

# Specific module
pytest tests/unit/test_rollback.py -v
```

### Coverage Target

- **Minimum:** 80%
- **Target:** 85%+

📖 **Test Exemplars:** [docs/exemplars.md](docs/exemplars.md)

---

## CLI Commands

### Common Commands

```bash
# Installation
vps-configurator install --profile beginner
vps-configurator wizard                    # Interactive mode

# Verification
vps-configurator verify
vps-configurator rollback

# Security
vps-configurator security cis-scan
vps-configurator security vuln-scan

# User Management
vps-configurator user create johndoe --role developer
vps-configurator user list
vps-configurator team create dev-team

# Secrets
vps-configurator secrets set API_KEY
vps-configurator secrets list
```

### Getting Help

```bash
vps-configurator --help
vps-configurator install --help
vps-configurator user --help
```

---

## Documentation

### Blueprint Suite

| Document                                                                              | Lines | Purpose               |
| ------------------------------------------------------------------------------------- | ----- | --------------------- |
| [architecture.md](docs/architecture.md)                                               | 1400+ | Architecture patterns |
| [exemplars.md](docs/exemplars.md)                                                     | 787   | Code exemplars        |
| [Technology_Stack_Blueprint.md](docs/Technology_Stack_Blueprint.md)                   | 946   | Tech stack details    |
| [Project_Folders_Structure_Blueprint.md](docs/Project_Folders_Structure_Blueprint.md) | 786   | Folder organization   |
| [Project_Workflow_Analysis_Blueprint.md](docs/Project_Workflow_Analysis_Blueprint.md) | 1008  | Workflow patterns     |
| [copilot-instructions.md](.github/copilot-instructions.md)                            | 498   | AI code generation    |

### Quick Links

- 📘 [Quick Start Guide](docs/00-project-overview/quick-start-guide.md)
- 📘 [Configuration Reference](docs/03-operations/configuration-reference.md)
- 📘 [Troubleshooting Guide](docs/03-operations/troubleshooting-guide.md)

---

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Follow [coding standards](.github/copilot-instructions.md)
4. Write tests for new functionality
5. Submit a pull request

### Code Review Checklist

- [ ] Follows naming conventions
- [ ] Has type hints on public APIs
- [ ] Includes docstrings
- [ ] Has unit tests
- [ ] Registers rollback actions for state changes
- [ ] No bare `except:` clauses

### Resources

- [Code Exemplars](docs/exemplars.md) — Reference implementations
- [Workflow Patterns](docs/Project_Workflow_Analysis_Blueprint.md) — Implementation templates
- [Architecture](docs/architecture.md) — Design decisions

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/), [Rich](https://rich.readthedocs.io/), [Textual](https://textual.textualize.io/)
- Security benchmarks based on [CIS Benchmarks](https://www.cisecurity.org/)
- Inspired by infrastructure-as-code principles

---

Made with ❤️ for the developer community

_Transform your VPS into a powerful development workstation in minutes, not hours._
