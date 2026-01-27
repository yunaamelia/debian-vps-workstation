# Sprint 2 Migration Guide

## What Changed

Sprint 2 introduced:

1. **Hybrid Execution Engine** - Intelligent parallel/pipeline routing
2. **Enhanced Progress Reporter** - Rich animations and TUI dashboard
3. **Enhanced Hooks System** - Detailed lifecycle events
4. **Refactored Installer** - Integrates all Sprint 1 + 2 components

## For End Users

### New TUI Dashboard

Enable full-screen dashboard:

```bash
vps-configurator install --tui
```

### Better Progress Reporting

Progress now shows:

- Spinner animations
- Time elapsed/remaining
- Module-specific progress
- Fun facts during installation

## For Developers

### Old Way (Deprecated)

```python
# Direct module execution
module.validate()
module.configure()
module.verify()
```

### New Way

```python
# Use execution engine
from configurator.core.execution.hybrid import HybridExecutor

executor = HybridExecutor(max_workers=4)
results = executor.execute(contexts)
```

### Hook System

Register hooks with decorator:

```python
from configurator.core.hooks.decorators import hook
from configurator.core.hooks.events import HookEvent

@hook(HookEvent.AFTER_MODULE_CONFIGURE)
def my_hook(context):
    print(f"Module {context.module_name} completed")
```

## Breaking Changes

**None** - All changes are backward compatible.

Old progress reporter still works but new RichProgressReporter recommended.
