# Debian VPS Configurator - AI Agent Instructions

## Architecture

This is a **modular Python automation system** for VPS configuration with parallel execution, circuit breakers, and package caching.

**Core Flow:** `cli.py` → `Installer` → `ConfigurationModule` instances → parallel execution batches

- **Entry Point:** `configurator/cli.py` (126KB, 106 functions) - Click-based CLI
- **Orchestrator:** `configurator/core/installer.py` - Manages module execution order, parallel batches
- **Module Base:** `configurator/modules/base.py` - All modules inherit from `ConfigurationModule`
- **Modules:** `configurator/modules/*` (24 modules) - Each module handles one tool/service (Docker, XRDP, VS Code, etc.)

**Key Patterns:**

- Modules define `name`, `priority`, `depends_on`, `force_sequential`
- Each module has `validate()`, `configure()`, `verify()` lifecycle methods
- Global `_APT_LOCK` prevents parallel apt conflicts
- Circuit breakers protect against network failures
- Lazy loading via `LazyLoader` for faster startup

## Directory Structure

```
configurator/
├── cli.py                  # Main CLI (106 commands)
├── config.py               # Config manager
├── modules/                # 24 modules (docker, xrdp, vscode, etc.)
│   ├── base.py            # ConfigurationModule base class
│   └── *.py               # Individual module implementations
├── core/                   # Core functionality (15 files)
│   ├── installer.py       # Orchestrator
│   ├── parallel.py        # Parallel execution engine
│   ├── package_cache.py   # APT cache manager
│   ├── rollback.py        # Rollback manager
│   ├── container.py       # DI container
│   └── reporter.py        # Rich console reporter
├── utils/                  # Utilities (9 files)
│   ├── command.py         # run_command wrapper
│   ├── circuit_breaker.py # Circuit breaker pattern
│   ├── retry.py           # Retry decorator
│   └── file.py            # File operations
├── security/               # Security features (20 files)
├── users/                  # User management (5 files)
├── rbac/                   # RBAC system (5 files)
└── exceptions.py           # Custom exception hierarchy

tests/
├── unit/                   # Fast isolated tests (41 files)
├── integration/            # Slower system tests (20 files)
├── validation/             # Acceptance tests (53 files)
└── conftest.py             # Pytest fixtures

config/
├── default.yaml            # Default configuration
└── profiles/               # Installation profiles (beginner, advanced, etc.)
```

## Workflows

```bash
# Development Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e .  # Install in dev mode

# Run Tests
pytest tests/unit/ -v                    # Fast unit tests
pytest tests/integration/ -v --slow       # Integration tests (require Debian system)
pytest --cov=configurator --cov-report=html  # With coverage

# Pre-commit Hooks
pre-commit run --all-files               # Fast checks (ruff, yaml)
pre-commit run --all-files --hook-stage pre-push  # Slow (run pytest)

# Run Application
python -m configurator install --profile advanced -v  # Full install
python -m configurator install --dry-run            # Preview actions
vps-configurator wizard  # Interactive mode

# Debug
python -m configurator --verbose install  # Verbose logging
tail -f logs/install.log                  # Watch logs
```

## Key Conventions

**Error Handling:** Always use `ModuleExecutionError` with beginner-friendly messages:

```python
raise ModuleExecutionError(
    what="Failed to install Docker",
    why="Package repository not available",
    how="Check internet: ping deb.debian.org",
)
```

**Module Structure:** New modules go in `configurator/modules/`. Must implement:

```python
class MyModule(ConfigurationModule):
    name = "MyTool"
    priority = 55  # Execution order (lower = earlier)
    depends_on = ["system"]

    def validate(self) -> bool: ...  # Check prerequisites
    def configure(self) -> bool: ...  # Do the work
    def verify(self) -> bool: ...    # Confirm it worked
```

**Parallel Execution:** Modules run in parallel batches unless `force_sequential = True`. Use `self._APT_LOCK` for apt operations.

**Testing:** Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`. Integration tests require real Debian 13 system.

**Commit Messages:** Follow conventional commits (enforced by pre-commit hook):

```
feat(docker): add custom registry support
fix(xrdp): correct audio configuration
docs(readme): add troubleshooting section
```

## Common Pitfalls

1. **APT Lock Conflicts:** Never run apt commands in parallel. Always use `with self._APT_LOCK:` or `self.install_packages()` which handles locking.

2. **Dry Run Checks:** Commands that modify state must check `if self.dry_run: return`. Read-only checks should use `force_execute=True`.

3. **Module Priority:** Lower priority = runs earlier. System (priority 10) runs first, desktop (priority 90) runs last. Check existing modules before assigning.

4. **Rollback Registration:** Every state-changing operation needs rollback: `self.rollback_manager.add_*()`. Otherwise rollback won't work.

5. **Circuit Breaker Manual Reset:** If circuit breaker opens, user must manually reset: `vps-configurator reset circuit-breaker <name>`

6. **Import Errors:** Use `LazyLoader` for heavy imports to avoid startup slowdown. See `cli.py` for examples.

## Debugging Tips

**Module execution order:**

```python
# Check in installer.py or run:
python -m configurator install --dry-run  # Shows execution plan
```

**Why did a module fail?**

```bash
tail -100 logs/install.log  # Last 100 lines
grep "ERROR" logs/install.log  # All errors
```

**APT lock issues:**

```bash
sudo lsof /var/lib/dpkg/lock-frontend  # Who has the lock?
```

**Circuit breaker state:**

```bash
vps-configurator status circuit-breakers  # Show all breakers
```

**Test specific module:**

```python
pytest tests/unit/test_docker.py -v -k test_install
```

## Best Practices

**1. Config Access:** Use `self.get_config("key.nested", default=value)` instead of dict access.

**2. Command Execution:** Always use `self.run()` not `subprocess` directly - handles dry-run, logging, rollback.

**3. Package Installation:** Use `self.install_packages(["pkg1", "pkg2"])` - handles retries, caching, locking.

**4. File Operations:** Use `self.write_file()` for dry-run support. For complex ops, use `configurator.utils.file`.

**5. Service Management:** Use `self.enable_service()` and `self.is_service_active()` for systemd.

**6. Logging:** Use `self.logger.info/debug/error` not `print()`. Logs go to console + file.

**7. Type Hints:** Always add type hints - project uses mypy for type checking.

**8. Docstrings:** Use Google-style docstrings with Examples section when helpful.

## External Dependencies

- **APT Packages:** All packages cached locally in `PackageCacheManager` for offline installs
- **Circuit Breakers:** Network calls protected by `CircuitBreakerManager` - auto-opens on repeated failures
- **Config Files:** `config/default.yaml` for defaults, profile-specific configs in `config/profiles/`
- **Rollback:** All changes tracked by `RollbackManager` - can undo installs
- **Logging:** Uses Python `logging` module - logs to console + `logs/install.log`
- **DI Container:** `Container` in `core/container.py` manages dependency injection for testability

## Security & RBAC

- **Secrets:** Use `SecretManager` for encrypted storage - never hardcode credentials
- **RBAC:** Role-based access in `configurator/rbac/` - check before sensitive operations
- **Audit:** All actions logged to audit trail via `AuditLogger` in `core/audit.py`
- **File Integrity:** FIM checks in `core/file_integrity.py` detect unauthorized changes

## Performance Patterns

**Why Parallel Execution?** Sequential install takes 45+ mins. Parallel reduces to ~15 mins by batching independent modules.

**Why Package Cache?** Saves 50-90% bandwidth by caching .deb files locally. See `core/package_cache.py`.

**Why Lazy Loading?** CLI startup 3-5x faster. Heavy imports (pandas, matplotlib) only load when needed.

**Why Circuit Breakers?** Prevents wasting time on failing network calls. Fast-fails after threshold.
