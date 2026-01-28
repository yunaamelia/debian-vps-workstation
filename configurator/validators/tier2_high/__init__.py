"""
Tier 2 High Priority Validators.

These validators check requirements that are strongly recommended but can be
overridden by the user. If these fail, the user will be prompted to confirm.

High priority validators:
- RAMValidator: Checks minimum RAM (4GB)
- DiskSpaceValidator: Checks minimum disk space (20GB)
- NetworkValidator: Checks internet connectivity
- ZshConfigIntegrityValidator: Validates .zshrc syntax
- ToolIntegrationValidator: Validates terminal tools work together
"""

from configurator.validators.tier2_high.disk_space import DiskSpaceValidator
from configurator.validators.tier2_high.network import NetworkValidator
from configurator.validators.tier2_high.ram import RAMValidator
from configurator.validators.tier2_high.tool_integration_validator import (
    ToolIntegrationValidator,
)
from configurator.validators.tier2_high.zsh_config_integrity_validator import (
    ZshConfigIntegrityValidator,
)

__all__ = [
    "RAMValidator",
    "DiskSpaceValidator",
    "NetworkValidator",
    "ZshConfigIntegrityValidator",
    "ToolIntegrationValidator",
]
