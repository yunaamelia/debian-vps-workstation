# PROMPT 1.4: LAZY LOADING SYSTEM IMPLEMENTATION

## 📋 Context

The configurator has many modules (nginx, postgres, docker, hardening, user_mgmt). Loading ALL of them at startup (`import configurator.modules.docker`, etc.) makes the CLI slow to start, especially for simple commands like `vps-configurator --version`.
We need **Lazy Loading** to import modules only when they are actually needed.

## 🎯 Objective

Implement a `LazyLoader` mechanism or leverage Python's `importlib` for module management in `configurator/core/lazy_loader.py`.

## 🛠️ Requirements

### Functional

1. **On-Demand Import**: Modules are not imported until a function or class from them is accessed.
2. **Registry**: A central registry mapping "module_name" to "file_path" or "python package path".

### Non-Functional

1. **Transparency**: The rest of the code should treat lazy modules as if they were standard imports (proxy pattern).
2. **Startup Speed**: measurable reduction in start time.

## 📝 Specifications

### Class Signature (`configurator/core/lazy_loader.py`)

```python
import importlib
import sys
from types import ModuleType

class LazyModule:
    def __init__(self, module_name):
        self._module_name = module_name
        self._module = None

    def __getattr__(self, item):
        if self._module is None:
            print(f"Lazy loading {self._module_name}...")
            self._module = importlib.import_module(self._module_name)
        return getattr(self._module, item)
```

## 🪜 Implementation Steps

1. **Create Module**: `configurator/core/lazy_loader.py`.
2. **Implement `LazyModule`**: Use the proxy pattern or `sys.meta_path` (Proxy is simpler for this scope).
3. **Refactor `configurator/modules/__init__.py`**:
    - Instead of:

      ```python
      from .docker import DockerModule
      from .nginx import NginxModule
      ```

    - Use:

      ```python
      DockerModule = LazyLoader("configurator.modules.docker", "DockerModule")
      ```

      (You may need a helper that loads the class specifically).
4. **Test**:
    - Create a script that imports the registry but doesn't use the modules. Check `sys.modules`. The sub-modules should NOT be there.

## 🔍 Validation Checklist

- [ ] Importing top-level package does not import sub-modules.
- [ ] Accessing a property triggers the import.
- [ ] Reduces memory footprint on startup.

---

**Output**: Generate `configurator/core/lazy_loader.py` and a demonstration test.
