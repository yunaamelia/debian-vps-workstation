"""
Tier 1 Critical Validators.

These validators check system requirements that MUST pass for installation to proceed.
If any critical validator fails, the installation will not continue.

Critical validators:
- RootAccessValidator: Checks for root/sudo privileges
- OSVersionValidator: Validates operating system version
- PythonVersionValidator: Validates Python version
- ZshInstalledValidator: Validates zsh shell installation
- ShellPermissionValidator: Validates shell config permissions
"""

from configurator.validators.tier1_critical.os_version import OSVersionValidator
from configurator.validators.tier1_critical.python_version import PythonVersionValidator
from configurator.validators.tier1_critical.root_access import RootAccessValidator
from configurator.validators.tier1_critical.shell_permission_validator import (
    ShellPermissionValidator,
)
from configurator.validators.tier1_critical.zsh_installed_validator import (
    ZshInstalledValidator,
)

__all__ = [
    "RootAccessValidator",
    "OSVersionValidator",
    "PythonVersionValidator",
    "ZshInstalledValidator",
    "ShellPermissionValidator",
]
