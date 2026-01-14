"""
System validation for pre-flight checks.

Verifies that the system meets all prerequisites before installation.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from configurator.exceptions import PrerequisiteError
from configurator.utils.network import check_internet
from configurator.utils.system import (
    get_architecture,
    get_cpu_count,
    get_disk_free_gb,
    get_os_info,
    get_ram_gb,
    is_root,
    is_systemd,
)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    passed: bool
    message: str
    required: bool = True

    def __str__(self) -> str:
        status = "✓" if self.passed else "✗"
        req = "(required)" if self.required else "(recommended)"
        return f"{status} {self.name}: {self.message} {req}"


class SystemValidator:
    """
    Validates system prerequisites before installation.

    Checks:
    - Operating system (Debian 13)
    - Architecture (x86_64)
    - Init system (systemd)
    - Root/sudo access
    - RAM (minimum 2GB, recommended 4GB)
    - Disk space (minimum 20GB free)
    - Internet connectivity
    """

    # Requirements
    MIN_RAM_GB = 2.0
    RECOMMENDED_RAM_GB = 4.0
    MIN_DISK_GB = 20.0
    RECOMMENDED_DISK_GB = 40.0
    MIN_CPU_CORES = 1

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize validator.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.results: List[ValidationResult] = []

    def validate_all(self, strict: bool = True) -> bool:
        """
        Run all validation checks.

        Args:
            strict: Fail on any missing requirement

        Returns:
            True if all required checks pass

        Raises:
            PrerequisiteError if strict=True and a required check fails
        """
        self.results = []

        # Run all checks
        self._check_os()
        self._check_architecture()
        self._check_systemd()
        self._check_root_access()
        self._check_ram()
        self._check_disk_space()
        self._check_internet()
        self._check_cpu()

        # Check for failures
        failed_required = [r for r in self.results if not r.passed and r.required]
        failed_recommended = [r for r in self.results if not r.passed and not r.required]

        # Log results
        self.logger.info("\n" + "=" * 60)
        self.logger.info("SYSTEM VALIDATION REPORT")
        self.logger.info("=" * 60)

        for result in self.results:
            if result.passed:
                self.logger.info(f"  ✓ {result.name}: {result.message}")
            elif result.required:
                self.logger.error(f"  ✗ {result.name}: {result.message} (REQUIRED)")
            else:
                self.logger.warning(f"  ⚠ {result.name}: {result.message} (recommended)")

        self.logger.info("=" * 60 + "\n")

        if failed_required:
            if strict:
                raise PrerequisiteError(
                    what="System validation failed",
                    why=f"{len(failed_required)} required check(s) failed:\n"
                    + "\n".join(f"  • {r.name}: {r.message}" for r in failed_required),
                    how="Please address the issues listed above and try again.\n"
                    "See documentation for system requirements.",
                    docs_link="https://github.com/yunaamelia/debian-vps-workstation#requirements",
                )
            return False

        if failed_recommended:
            self.logger.warning(
                f"{len(failed_recommended)} recommended check(s) failed. "
                "Installation will continue, but you may experience issues."
            )

        return True

    def _check_os(self) -> None:
        """Check if running on Debian 13."""
        os_info = get_os_info()

        if os_info.is_debian_13:
            self.results.append(
                ValidationResult(
                    name="Operating System",
                    passed=True,
                    message=f"{os_info.pretty_name}",
                    required=True,
                )
            )
        elif os_info.is_debian:
            self.results.append(
                ValidationResult(
                    name="Operating System",
                    passed=False,
                    message=f"Found Debian {os_info.version_id}, but Debian 13 is required",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Operating System",
                    passed=False,
                    message=f"Found {os_info.pretty_name}, but Debian 13 is required",
                    required=True,
                )
            )

    def _check_architecture(self) -> None:
        """Check system architecture."""
        arch = get_architecture()

        if arch in ("x86_64", "amd64"):
            self.results.append(
                ValidationResult(
                    name="Architecture",
                    passed=True,
                    message=f"{arch}",
                    required=True,
                )
            )
        elif arch in ("aarch64", "arm64"):
            self.results.append(
                ValidationResult(
                    name="Architecture",
                    passed=True,
                    message=f"{arch} (ARM64 support is experimental)",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Architecture",
                    passed=False,
                    message=f"{arch} is not supported (requires x86_64 or arm64)",
                    required=True,
                )
            )

    def _check_systemd(self) -> None:
        """Check if systemd is the init system."""
        if is_systemd():
            self.results.append(
                ValidationResult(
                    name="Init System",
                    passed=True,
                    message="systemd",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Init System",
                    passed=False,
                    message="systemd is required but not detected",
                    required=True,
                )
            )

    def _check_root_access(self) -> None:
        """Check for root/sudo access."""
        if is_root():
            self.results.append(
                ValidationResult(
                    name="Root Access",
                    passed=True,
                    message="Running as root",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Root Access",
                    passed=False,
                    message="Not running as root. Please run with sudo.",
                    required=True,
                )
            )

    def _check_ram(self) -> None:
        """Check available RAM."""
        ram_gb = get_ram_gb()

        if ram_gb >= self.RECOMMENDED_RAM_GB:
            self.results.append(
                ValidationResult(
                    name="RAM",
                    passed=True,
                    message=f"{ram_gb:.1f} GB (recommended: {self.RECOMMENDED_RAM_GB}+ GB)",
                    required=True,
                )
            )
        elif ram_gb >= self.MIN_RAM_GB:
            self.results.append(
                ValidationResult(
                    name="RAM",
                    passed=True,
                    message=f"{ram_gb:.1f} GB (minimum met, {self.RECOMMENDED_RAM_GB}+ GB recommended)",
                    required=False,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="RAM",
                    passed=False,
                    message=f"{ram_gb:.1f} GB (minimum {self.MIN_RAM_GB} GB required)",
                    required=True,
                )
            )

    def _check_disk_space(self) -> None:
        """Check available disk space."""
        disk_gb = get_disk_free_gb("/")

        if disk_gb >= self.RECOMMENDED_DISK_GB:
            self.results.append(
                ValidationResult(
                    name="Disk Space",
                    passed=True,
                    message=f"{disk_gb:.1f} GB free",
                    required=True,
                )
            )
        elif disk_gb >= self.MIN_DISK_GB:
            self.results.append(
                ValidationResult(
                    name="Disk Space",
                    passed=True,
                    message=f"{disk_gb:.1f} GB free (minimum met, {self.RECOMMENDED_DISK_GB}+ GB recommended)",
                    required=False,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Disk Space",
                    passed=False,
                    message=f"{disk_gb:.1f} GB free (minimum {self.MIN_DISK_GB} GB required)",
                    required=True,
                )
            )

    def _check_internet(self) -> None:
        """Check internet connectivity."""
        if check_internet():
            self.results.append(
                ValidationResult(
                    name="Internet",
                    passed=True,
                    message="Connected",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="Internet",
                    passed=False,
                    message="No internet connection detected",
                    required=True,
                )
            )

    def _check_cpu(self) -> None:
        """Check CPU cores."""
        cores = get_cpu_count()

        if cores >= 2:
            self.results.append(
                ValidationResult(
                    name="CPU",
                    passed=True,
                    message=f"{cores} cores",
                    required=True,
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    name="CPU",
                    passed=True,
                    message=f"{cores} core (2+ recommended for better performance)",
                    required=False,
                )
            )

    def get_summary(self) -> str:
        """Get a summary of validation results."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        return f"Validation: {passed}/{total} checks passed"
