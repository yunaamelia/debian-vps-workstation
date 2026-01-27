# Migration Guide: v1 to v2

This guide helps you migrate from Debian VPS Workstation Configurator v1.x to v2.0.

## Overview of Changes

Version 2.0 is a major release with significant architectural improvements:

| Area              | v1                     | v2                            |
| ----------------- | ---------------------- | ----------------------------- |
| **Validation**    | Single SystemValidator | Tiered ValidationOrchestrator |
| **Execution**     | Sequential only        | Hybrid (Parallel + Pipeline)  |
| **Configuration** | CLI flags only         | Interactive Wizard + Profiles |
| **State**         | File-based             | SQLite with checkpoints       |
| **UI**            | Basic progress         | Rich TUI Dashboard            |

## Breaking Changes

### 1. Configuration File Format

**v1 format (`config.yaml`):**

```yaml
modules:
  - docker
  - python
  - nodejs
options:
  verbose: true
```

**v2 format (`config.yaml`):**

```yaml
version: 2
profile: custom
modules:
  docker:
    enabled: true
  python:
    enabled: true
    version: "3.11"
  nodejs:
    enabled: true
    version: "20"
settings:
  verbosity: info
  parallel_execution: true
```

**Migration steps:**

1. Create a backup of your v1 config
2. Run the migration tool:

   ```bash
   vps-configurator migrate-config --input old-config.yaml --output config.yaml
   ```

### 2. Module Dependencies

v2 uses explicit dependency decorators. If you have custom modules:

**v1:**

```python
class MyModule(ConfigurationModule):
    REQUIRES = ["docker"]
```

**v2:**

```python
from configurator.dependencies.decorators import module, depends_on

@module(name="my_module", description="My custom module")
@depends_on("docker")
class MyModule(ConfigurationModule):
    pass
```

### 3. Validator API

**v1:**

```python
from configurator.core.validator import SystemValidator
validator = SystemValidator()
validator.validate()
```

**v2:**

```python
from configurator.validators.orchestrator import ValidationOrchestrator
orchestrator = ValidationOrchestrator()
results = orchestrator.run_all()
```

### 4. State Management

v2 uses SQLite for state persistence. The old `.state` files are not compatible.

**Migration:**

```bash
# Clear old state (requires re-verification of installed modules)
rm -rf /var/lib/debian-vps-configurator/state/

# Run verification to rebuild state
vps-configurator verify --all
```

## New Features to Adopt

### Interactive Wizard

```bash
vps-configurator wizard
```

### Profiles

```bash
# List available profiles
vps-configurator profiles

# Install using a profile
vps-configurator install --profile fullstack
```

### Parallel Execution

Enabled by default. To disable:

```bash
vps-configurator install --no-parallel
```

### Dependency Visualization

```bash
vps-configurator visualize --format mermaid
```

## Compatibility Mode

v2 includes a compatibility layer for v1 configurations:

```bash
vps-configurator install --compat-v1 --config old-config.yaml
```

This will:

1. Auto-convert the configuration
2. Run with v1-compatible behavior
3. Warn about deprecated features

## Getting Help

- [Documentation](https://docs.example.com)
- [GitHub Issues](https://github.com/ahmadrizal7/debian-vps-workstation/issues)
- [Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions)
