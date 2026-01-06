import shutil
import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_package_installed(package_name: str) -> CheckResult:
    if shutil.which("dpkg") is None:
        return CheckResult(check=None, status=Status.ERROR, message="dpkg not found")
    try:
        result = subprocess.run(["dpkg", "-s", package_name], capture_output=True, text=True)
        if result.returncode == 0 and "Status: install ok installed" in result.stdout:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{package_name} is installed"
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{package_name} is NOT installed",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _check_service_enabled(service_name: str) -> CheckResult:
    try:
        result = subprocess.run(
            ["systemctl", "is-enabled", service_name], capture_output=True, text=True
        )
        if result.returncode == 0:
            return CheckResult(check=None, status=Status.PASS, message=f"{service_name} is enabled")
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{service_name} is NOT enabled",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_install_package(package_name: str) -> bool:
    try:
        subprocess.run(["apt-get", "install", "-y", package_name], check=True)
        return True
    except Exception:
        return False


def _remediate_enable_service(service_name: str) -> bool:
    try:
        subprocess.run(["systemctl", "enable", "--now", service_name], check=True)
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="4.1.1",
            title="Ensure auditd is installed",
            description="Install the auditd daemon.",
            rationale="Essential for system auditing.",
            severity=Severity.HIGH,
            check_function=lambda: _check_package_installed("auditd"),
            remediation_function=lambda: _remediate_install_package("auditd"),
            category="Logging",
        ),
        CISCheck(
            id="4.1.2",
            title="Ensure auditd service is enabled",
            description="Enable auditd service.",
            rationale="Ensure auditing is running.",
            severity=Severity.HIGH,
            check_function=lambda: _check_service_enabled("auditd"),
            remediation_function=lambda: _remediate_enable_service("auditd"),
            category="Logging",
        ),
    ]
    return checks
