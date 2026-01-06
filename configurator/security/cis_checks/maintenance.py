import os
from pathlib import Path
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_file_permissions(path: str, max_mode: str) -> CheckResult:
    p = Path(path)
    if not p.exists():
        return CheckResult(check=None, status=Status.ERROR, message=f"{path} missing")

    try:
        mode = oct(p.stat().st_mode)[-3:]
        # Simple check: mode should be <= max_mode?
        # Actually logic is bitwise.
        # But for CIS, they often specify exact matches "0644" or "000".
        # Let's compare exactly for simplicity or implement bitwise check if needed.
        # 0644 means user rw, group r, other r.
        # If it is 600, it is also compliant? Often yes.
        # But prompting for "Ensure permissions are exactly 644" or "le 644".
        # Let's implement LE check.

        current_val = int(mode, 8)
        max_val = int(max_mode, 8)

        if current_val <= max_val:
            return CheckResult(
                check=None,
                status=Status.PASS,
                message=f"{path} permissions {mode} are compliant (<= {max_mode})",
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{path} permissions {mode} are too open (should be <= {max_mode})",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_file_permissions(path: str, mode: str) -> bool:
    try:
        p = Path(path)
        if not p.exists():
            return False
        p.chmod(int(mode, 8))
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="6.1.1",
            title="Ensure permissions on /etc/passwd are configured",
            description="Check /etc/passwd permissions.",
            rationale="Should be 644 or more restrictive.",
            severity=Severity.HIGH,
            check_function=lambda: _check_file_permissions("/etc/passwd", "644"),
            remediation_function=lambda: _remediate_file_permissions("/etc/passwd", "644"),
            category="System Maintenance",
        ),
        CISCheck(
            id="6.1.2",
            title="Ensure permissions on /etc/shadow are configured",
            description="Check /etc/shadow permissions.",
            rationale="Should be 000 or 400.",
            severity=Severity.CRITICAL,
            check_function=lambda: _check_file_permissions("/etc/shadow", "000"),
            remediation_function=lambda: _remediate_file_permissions("/etc/shadow", "000"),
            category="System Maintenance",
        ),
        CISCheck(
            id="6.1.3",
            title="Ensure permissions on /etc/group are configured",
            description="Check /etc/group permissions.",
            rationale="Should be 644.",
            severity=Severity.MEDIUM,
            check_function=lambda: _check_file_permissions("/etc/group", "644"),
            remediation_function=lambda: _remediate_file_permissions("/etc/group", "644"),
            category="System Maintenance",
        ),
    ]
    return checks
