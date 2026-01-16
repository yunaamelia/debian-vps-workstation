# Advanced Module Development

## Module Inheritance

All modules inherit from `ConfigurationModule`.

## Dependency Management

Use the `@depends_on` decorator to declare dependencies:

```python
@depends_on("system", "security")
class MyModule(ConfigurationModule):
    # ...
```

## Configuration Schema

Define your configuration schema using Pydantic models for validation.

## State Management

Use `self.state_manager` to persist installation state and checkpoints.
