# Installer

**Module:** `configurator.core.installer`

Orchestrates the installation of all enabled modules.

## Methods

### `__init__(self, config: configurator.config.ConfigManager, logger: Optional[logging.Logger] = None, reporter: Optional[configurator.core.reporter.base.ReporterInterface] = None, container: Optional[configurator.core.container.Container] = None)`

Initialize installer.

---

### `install(self, skip_validation: bool = False, dry_run: bool = False, parallel: bool = True) -> bool`

Run the full installation.

---

### `rollback(self) -> bool`

Rollback changes.

---

### `verify(self) -> bool`

Verify installed components.

Returns:
    True if all expected components are working

---
