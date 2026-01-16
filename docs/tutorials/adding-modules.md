# Adding New Modules

Learn how to extend the configurator by adding new modules.

## Module Structure

Modules are located in `configurator/modules/`. Each module must inherit from `ConfigurationModule`.

## Example Module

```python
from configurator.modules.base import ConfigurationModule

class MyNewModule(ConfigurationModule):
    name = "My New Module"

    def configure(self) -> bool:
        self.logger.info("Configuring my new module...")
        # Implementation here
        return True
```

See the [Developer Guide](../developer-guide/module-development.md) for full details.
