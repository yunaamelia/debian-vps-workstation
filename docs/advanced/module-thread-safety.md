# Module Thread Safety Guidelines

This document provides guidelines for ensuring thread safety in `ConfigurationModule` implementations when running in parallel execution mode.

## Overview

Configurator 2.0 uses parallel execution to speed up deployment. This means multiple modules may execute their `configure()` methods simultaneously in different threads. To prevent race conditions and data corruption, modules must be thread-safe.

## Core Rules

1. **Avoid Shared Mutable State**: Do not rely on global variables or class-level mutable attributes unless strictly necessary and protected by locks.
2. **Atomic File Operations**: Use `configurator.utils.file_lock` execution for critical file writes.
3. **Use the `depends_on` Attribute**: Correctly declare dependencies to ensure sequential ordering where strict ordering is required.
4. **Use `force_sequential=True`**: If a module is inherently unsafe or interacts with a global resource that cannot be locked (e.g., essentially single-threaded external tools), mark it as sequential.

## Code Examples

### DO: Use Local Variables

```python
def configure(self):
    # Safe: local variable
    config_path = "/tmp/my_config.conf"
    ...
```

### DO: Use File Locking for Shared Files

```python
from configurator.utils.file_lock import file_lock

def configure(self):
    shared_file = "/etc/hosts"
    with file_lock(shared_file):
         with open(shared_file, "a") as f:
             f.write("127.0.0.1 localhost\n")
```

### DON'T: Modify Global State Without Locks

```python
# UNSAFE
global_counter = 0

def configure(self):
    global global_counter
    global_counter += 1  # Race condition!
```

### DON'T: Assume Execution Order Without Dependencies

Do not assume Module A has finished just because it comes alphabetically before Module B. Dependencies must be explicit.

```python
# UNSAFE assumption
def configure(self):
    # Assuming 'system' module created this file, but didn't declare 'system' in depends_on
    with open("/etc/system_config", "r") as f:
        ...
```

### Use Force Sequential for Legacy/Unsafe Modules

```python
class LegacyModule(ConfigurationModule):
    force_sequential = True  # Runs alone in a batch
    ...
```
