# Lazy Loading Architecture

## Overview

The Debian VPS Configurator optimizes CLI startup time by aggressively using lazy loading for heavy dependencies. This ensures that commands like `--help` or `--version`, which don't require the full installation machinery, execute almost instantly (< 200ms).

## Core Concepts

### LazyLoader Proxy

The `configurator.core.lazy_loader.LazyLoader` class acts as a transparent proxy. It defers the actual import of a module or class until an attribute is accessed or the object is called.

**Usage:**

```python
from configurator.core.lazy_loader import LazyLoader

# Defers import of 'configurator.core.installer' until 'Installer' is used
Installer = LazyLoader("configurator.core.installer", "Installer")

def main():
    # Installer is NOT imported yet
    installer = Installer(config=...) # Import happens here
    installer.install()
```

### Module Registry

The `configurator.modules` package uses PEP 562 (`__getattr__`) to lazily load configuration modules.

**Old Way (Slow):**

```python
# Imports ALL modules at startup
from configurator.modules.system import SystemModule
from configurator.modules.docker import DockerModule
...
```

**New Way (Fast):**

```python
# configurator/modules/__init__.py
def __getattr__(name):
    if name in _MODULE_REGISTRY:
        path, class_name = _MODULE_REGISTRY[name]
        return LazyModule(path, class_name)
    ...
```

## Performance Impact

By avoiding top-level imports of heavy libraries (like `rich`, `docker`, `git`, `apt`, etc.) until needed, we achieved a significant reduction in startup time:

- **Before:** ~2.0s
- **After:** ~0.17s
- **Speedup:** ~12x

## Developer Guidelines

1. **Avoid Top-Level Imports:** In `cli.py` or other entry points, verify if a heavy import is strictly necessary at the top level.
2. **Use LazyLoader:** For classes or modules used only in specific subcommands, use `LazyLoader`.
3. **Local Imports:** For one-off functions, consider importing inside the function scope.
4. **LazyModule:** When adding a new configuration module, register it in `configurator/modules/__init__.py` instead of importing it directly.

## Debugging

To verify imports are being deferred, you can inspect `sys.modules` or use the `tools/benchmark_lazy_loading.py` tool.

```bash
python3 tools/benchmark_lazy_loading.py
```
