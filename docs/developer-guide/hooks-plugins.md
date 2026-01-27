# Hooks and Plugins

The configurator supports a powerful hook system allowing you to intervene at various stages of the installation process.

## Hook Types

* `on_init`: Called when the module is initialized.
* `pre_install`: Called before package installation.
* `post_install`: Called after package installation.
* `pre_configure`: Called before configuration.
* `post_configure`: Called after configuration.

## Registering a Hook

You can register hooks in your `plugin.py`:

```python
from configurator.core.hooks import register_hook

@register_hook("post_install")
def my_custom_cleanup(context):
    print(f"Cleaning up after {context.module.name}")
```
