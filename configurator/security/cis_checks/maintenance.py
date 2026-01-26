import os
from pathlib import Path
from typing import Callable, List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_file_permissions(path: str, max_mode: str, uid: int = 0, gid: int = 0) -> CheckResult:
    p = Path(path)
    if not p.exists():
        # Some files like /etc/shadow- might not exist
        return CheckResult(check=None, status=Status.PASS, message=f"{path} missing (OK)")

    try:
        stat = p.stat()
        mode = oct(stat.st_mode)[-3:]
        current_uid = stat.st_uid
        current_gid = stat.st_gid

        # Owner check
        if current_uid != uid:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{path} not owned by uid {uid}",
                remediation_available=True,
            )

        # Group check
        if current_gid != gid:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{path} not owned by gid {gid}",
                remediation_available=True,
            )

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


def _remediate_file_permissions(path: str, mode: str, uid: int = 0, gid: int = 0) -> bool:
    try:
        p = Path(path)
        if not p.exists():
            return False
        os.chown(path, uid, gid)
        p.chmod(int(mode, 8))
        return True
    except Exception:
        return False


def _create_file_check(path: str, mode: str, uid: int, gid: int) -> Callable[[], CheckResult]:
    return lambda: _check_file_permissions(path, mode, uid, gid)


def _create_file_remediate(path: str, mode: str, uid: int, gid: int) -> Callable[[], bool]:
    return lambda: _remediate_file_permissions(path, mode, uid, gid)


def get_checks() -> List[CISCheck]:
    checks = []

    # 6.1 System File Permissions
    file_checks = [
        ("6.1.1", "/etc/passwd", "644", 0, 0),
        ("6.1.2", "/etc/shadow", "000", 0, 42),  # 42 is often shadow group
        ("6.1.3", "/etc/group", "644", 0, 0),
        ("6.1.4", "/etc/gshadow", "000", 0, 42),
        ("6.1.5", "/etc/passwd-", "644", 0, 0),
        ("6.1.6", "/etc/shadow-", "000", 0, 0),
        ("6.1.7", "/etc/group-", "644", 0, 0),
        ("6.1.8", "/etc/gshadow-", "000", 0, 0),
        ("6.1.9", "/etc/shells", "644", 0, 0),
        ("6.1.10", "/etc/hosts.allow", "644", 0, 0),
        ("6.1.11", "/etc/hosts.deny", "644", 0, 0),
    ]

    for cid, path, mode, u, g in file_checks:
        sev = Severity.HIGH
        if "shadow" in path:
            sev = Severity.CRITICAL

        checks.append(
            CISCheck(
                id=cid,
                title=f"Ensure permissions on {path} are configured",
                description=f"Check {path} permissions: {mode}, uid:{u}, gid:{g}",
                rationale="Prevent unauthorized modification.",
                severity=sev,
                category="System Maintenance",
                check_function=_create_file_check(path, mode, u, g),
                remediation_function=_create_file_remediate(path, mode, u, g),
            )
        )

    # 6.2 User and Group Settings (Manual/Shell checks mocked)
    user_checks = [
        ("6.2.1", "Ensure password fields are not empty", Severity.CRITICAL),
        ("6.2.2", "Ensure no legacy '+' entries in /etc/passwd", Severity.HIGH),
        ("6.2.3", "Ensure root is the only UID 0 account", Severity.CRITICAL),
        ("6.2.4", "Ensure root PATH Integrity", Severity.HIGH),
        ("6.2.5", "Ensure all users' home directories exist", Severity.MEDIUM),
        (
            "6.2.6",
            "Ensure users' home directories permissions are 750 or more restrictive",
            Severity.MEDIUM,
        ),
        ("6.2.7", "Ensure users own their home directories", Severity.MEDIUM),
        ("6.2.8", "Ensure users' dot files are not group or world writable", Severity.MEDIUM),
        ("6.2.9", "Ensure no duplicate UIDs exist", Severity.HIGH),
        ("6.2.10", "Ensure no duplicate GIDs exist", Severity.HIGH),
        ("6.2.11", "Ensure no duplicate user names exist", Severity.HIGH),
        ("6.2.12", "Ensure no duplicate group names exist", Severity.HIGH),
    ]

    for cid, title, sev in user_checks:
        checks.append(
            CISCheck(
                id=cid,
                title=title,
                description=title,
                rationale="Integrity of user accounts.",
                severity=sev,
                category="System Maintenance",
                manual=True,
            )
        )

    return checks
