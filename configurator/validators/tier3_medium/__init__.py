"""
Tier 3 Medium Priority Validators.

These validators check recommended (but not required) settings.
Failures generate warnings but do not block installation.

Medium priority validators:
- RecommendedRAMValidator: Checks recommended RAM (8GB)
- RecommendedDiskValidator: Checks recommended disk space (40GB)
- DNSValidator: Checks DNS resolution
- ZshPerformanceValidator: Checks zsh startup time
"""

from configurator.validators.tier3_medium.dns import DNSValidator
from configurator.validators.tier3_medium.recommended_disk import RecommendedDiskValidator
from configurator.validators.tier3_medium.recommended_ram import RecommendedRAMValidator
from configurator.validators.tier3_medium.zsh_performance_validator import (
    ZshPerformanceValidator,
)

__all__ = [
    "RecommendedRAMValidator",
    "RecommendedDiskValidator",
    "DNSValidator",
    "ZshPerformanceValidator",
]
