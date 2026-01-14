"""
Shared utilities for CIS checks to avoid code duplication.
"""

import shutil
import subprocess
from typing import Dict, Optional, Tuple

from configurator.security.cis_scanner import CheckResult, Status


def check_package_removed(package_name: str) -> CheckResult:
    """Generic check for removed package"""
    if shutil.which("dpkg") is None:
        return CheckResult(check=None, status=Status.ERROR, message="dpkg not found")

    try:
        # dpkg -s returns 0 if installed, 1 if not
        # Check=False because we manually handle returncode
        result = subprocess.run(
            ["dpkg", "-s", package_name], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{package_name} is not installed"
            )
        else:
            # Check if it's actually installed or just config-files (purged vs removed)
            if "Status: install ok installed" in result.stdout:
                return CheckResult(
                    check=None,
                    status=Status.FAIL,
                    message=f"{package_name} is installed",
                    remediation_available=True,
                )
            else:
                return CheckResult(
                    check=None,
                    status=Status.PASS,
                    message=f"{package_name} is not installed (config files may remain)",
                )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def remediate_remove_package(package_name: str) -> bool:
    """Generic remediation to purge a package."""
    try:
        subprocess.run(["apt-get", "purge", "-y", package_name], check=True)
        return True
    except Exception:
        return False


def check_sysctl_param(param: str, expected_value: str) -> CheckResult:
    """Check sysctl parameter"""
    try:
        # sysctl -n param
        # Check=False because we manually handle returncode
        result = subprocess.run(["sysctl", "-n", param], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return CheckResult(check=None, status=Status.ERROR, message=f"Failed to read {param}")

        actual_value = result.stdout.strip()
        # Clean up whitespace
        actual_value = actual_value.split()[0] if actual_value else ""

        if str(actual_value) == str(expected_value):
            return CheckResult(check=None, status=Status.PASS, message=f"{param} is {actual_value}")
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{param} is {actual_value} (expected {expected_value})",
                remediation_available=True,
                details={"actual": actual_value, "expected": expected_value},
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def remediate_sysctl_param(param: str, value: str) -> bool:
    """Remediate sysctl parameter."""
    try:
        subprocess.run(["sysctl", "-w", f"{param}={value}"], check=True)
        # In a real implementation this should write to /etc/sysctl.d/99-cis.conf
        return True
    except Exception:
        return False


def check_service_status(service_name: str, should_be_active: bool = False) -> CheckResult:
    """Check if a service is active or disabled/masked."""
    try:
        res = subprocess.run(
            ["systemctl", "is-enabled", service_name], capture_output=True, text=True, check=False
        )
        status = res.stdout.strip()

        if not should_be_active:
            # We want it disabled/masked
            if status in ["masked", "disabled"]:
                return CheckResult(
                    check=None, status=Status.PASS, message=f"{service_name} is {status}"
                )
            elif res.returncode != 0 and "No such file or directory" in res.stderr:
                return CheckResult(
                    check=None, status=Status.PASS, message=f"{service_name} is not installed"
                )
            else:
                return CheckResult(
                    check=None,
                    status=Status.FAIL,
                    message=f"{service_name} is {status} (should be disabled/masked)",
                    remediation_available=True,
                )
        else:
            # We want it active
            if status == "enabled":
                return CheckResult(
                    check=None, status=Status.PASS, message=f"{service_name} is enabled"
                )
            else:
                return CheckResult(
                    check=None,
                    status=Status.FAIL,
                    message=f"{service_name} is {status} (should be enabled)",
                    remediation_available=True,
                )

    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def remediate_mask_service(service_name: str) -> bool:
    """Mask a service."""
    try:
        # Check=False is acceptable here as service might not be running
        subprocess.run(["systemctl", "disable", "--now", service_name], check=False)
        subprocess.run(["systemctl", "mask", service_name], check=True)
        return True
    except Exception:
        return False
