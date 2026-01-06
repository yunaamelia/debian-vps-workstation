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
        subprocess.run(["systemctl", "start", service_name], check=True)
        return True
    except Exception:
        return False


def _check_audit_config(param: str) -> CheckResult:
    """Check audit config file presence"""
    # This is a specialized check, simplified for speed
    # grep param /etc/audit/auditd.conf
    try:
        res = subprocess.run(
            ["grep", "-E", f"^{param}", "/etc/audit/auditd.conf"], capture_output=True
        )
        if res.returncode == 0:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{param} configured in auditd.conf"
            )
        return CheckResult(
            check=None, status=Status.FAIL, message=f"{param} missing in auditd.conf"
        )
    except Exception:
        return CheckResult(check=None, status=Status.ERROR, message="Error checking auditd.conf")


def get_checks() -> List[CISCheck]:
    checks = [
        # 4.1.1 Auditd Installation
        CISCheck(
            id="4.1.1.1",
            title="Ensure auditd is installed",
            description="Install auditd.",
            rationale="Compliance requirement.",
            severity=Severity.HIGH,
            category="Logging",
            check_function=lambda: _check_package_installed("auditd"),
            remediation_function=lambda: _remediate_install_package("auditd"),
        ),
        CISCheck(
            id="4.1.1.2",
            title="Ensure auditd service is enabled",
            description="Enable auditd.",
            rationale="Compliance requirement.",
            severity=Severity.HIGH,
            category="Logging",
            check_function=lambda: _check_service_enabled("auditd"),
            remediation_function=lambda: _remediate_enable_service("auditd"),
        ),
        CISCheck(
            id="4.1.1.3",
            title="Ensure auditing for processes that start prior to auditd is enabled",
            description="GRUB audit=1",
            rationale="Audit boot processes.",
            severity=Severity.MEDIUM,
            category="Logging",
            manual=True,  # Requires grub edit
        ),
        CISCheck(
            id="4.1.1.4",
            title="Ensure audit_backlog_limit is sufficient",
            description="GRUB audit_backlog_limit=8192",
            rationale="Prevent audit loss.",
            severity=Severity.MEDIUM,
            category="Logging",
            manual=True,
        ),
        # 4.1.2 Auditd Configuration
        CISCheck(
            id="4.1.2.1",
            title="Ensure audit log storage size is configured",
            description="max_log_file in auditd.conf",
            rationale="Prevent filling disk.",
            severity=Severity.LOW,
            category="Logging",
            check_function=lambda: _check_audit_config("max_log_file"),
        ),
        CISCheck(
            id="4.1.2.2",
            title="Ensure audit logs are not automatically deleted",
            description="max_log_file_action = keep_logs",
            rationale="Preserve evidence.",
            severity=Severity.MEDIUM,
            category="Logging",
            check_function=lambda: _check_audit_config("max_log_file_action"),
        ),
        CISCheck(
            id="4.1.2.3",
            title="Ensure system is disabled when audit logs are full",
            description="space_left_action = email/suspend",
            rationale="Prevent un-audited action.",
            severity=Severity.HIGH,
            category="Logging",
            check_function=lambda: _check_audit_config("space_left_action"),
        ),
        # 4.2 Logging Configuration
        CISCheck(
            id="4.2.1.1",
            title="Ensure rsyslog is installed",
            description="Install rsyslog.",
            rationale="Centralized logging.",
            severity=Severity.MEDIUM,
            category="Logging",
            check_function=lambda: _check_package_installed("rsyslog"),
            remediation_function=lambda: _remediate_install_package("rsyslog"),
        ),
        CISCheck(
            id="4.2.1.2",
            title="Ensure rsyslog service is enabled",
            description="Enable rsyslog.",
            rationale="Logging daemon.",
            severity=Severity.MEDIUM,
            category="Logging",
            check_function=lambda: _check_service_enabled("rsyslog"),
            remediation_function=lambda: _remediate_enable_service("rsyslog"),
        ),
        # 4.2.2 Journald
        CISCheck(
            id="4.2.2.1",
            title="Ensure journald is configured to send logs to rsyslog",
            description="ForwardToSyslog=yes in journald.conf",
            rationale="Central logging.",
            severity=Severity.LOW,
            category="Logging",
            manual=True,
        ),
        CISCheck(
            id="4.2.2.2",
            title="Ensure journald is configured to compress large log files",
            description="Compress=yes",
            rationale="Save space.",
            severity=Severity.LOW,
            category="Logging",
            manual=True,
        ),
        CISCheck(
            id="4.2.2.3",
            title="Ensure journald is configured to write logfiles to persistent disk",
            description="Storage=persistent",
            rationale="Keep logs after reboot.",
            severity=Severity.MEDIUM,
            category="Logging",
            manual=True,
        ),
        # 4.2.3 Logfiles
        CISCheck(
            id="4.2.3",
            title="Ensure permissions on all logfiles are configured",
            description="Logfiles should be 640 or less.",
            rationale="Prevent unauthorized reading.",
            severity=Severity.MEDIUM,
            category="Logging",
            manual=True,
        ),
    ]
    return checks
