import shutil
import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_package_removed(package_name: str) -> CheckResult:
    """Generic check for removed package"""
    if shutil.which("dpkg") is None:
        return CheckResult(check=None, status=Status.ERROR, message="dpkg not found")

    try:
        # dpkg -s returns 0 if installed, 1 if not
        result = subprocess.run(["dpkg", "-s", package_name], capture_output=True, text=True)
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


def _remediate_remove_package(package_name: str) -> bool:
    try:
        subprocess.run(["apt-get", "purge", "-y", package_name], check=True)
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="2.1.1",
            title="Ensure xinetd is not installed",
            description="xinetd is a super-server daemon.",
            rationale="It is rarely needed and increases attack surface.",
            severity=Severity.MEDIUM,
            check_function=lambda: _check_package_removed("xinetd"),
            remediation_function=lambda: _remediate_remove_package("xinetd"),
            category="Services",
        ),
        CISCheck(
            id="2.2.1",
            title="Ensure X Window System is not installed",
            description="GUI environment.",
            rationale="Servers should not run X11.",
            severity=Severity.MEDIUM,
            check_function=lambda: _check_package_removed("xserver-xorg-core"),
            remediation_function=lambda: _remediate_remove_package("xserver-xorg-core"),
            category="Services",
        ),
        CISCheck(
            id="2.2.2",
            title="Ensure Avahi Server is not installed",
            description="mDNS/DNS-SD daemon.",
            rationale="Automatic service discovery is not needed on servers.",
            severity=Severity.LOW,
            check_function=lambda: _check_package_removed("avahi-daemon"),
            remediation_function=lambda: _remediate_remove_package("avahi-daemon"),
            category="Services",
        ),
    ]
    return checks
