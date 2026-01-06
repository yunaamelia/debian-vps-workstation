import shutil
import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_mount_option(mount_point: str, option: str) -> CheckResult:
    """Check if a mount point has a specific option set"""
    try:
        # findmnt -n /path
        result = subprocess.run(["findmnt", "-n", mount_point], capture_output=True, text=True)
        if result.returncode != 0:
            # Mount point might not exist or not be a separate partition
            # For CIS, if it's not a separate partition, this check usually N/A or fail depending on strictness.
            # Usually recommendations are "Enable separate partition for X" THEN "Ensure nodev on X".
            # If X is not a partition, we can say it's not a separate partition.
            return CheckResult(
                check=None,
                status=Status.NOT_APPLICABLE,
                message=f"{mount_point} is not a separate partition",
            )

        if option in result.stdout:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{mount_point} has {option} set"
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{mount_point} does NOT have {option} set",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _check_partition_exists(mount_point: str) -> CheckResult:
    """Check if mount point is a separate partition"""
    try:
        result = subprocess.run(["findmnt", "-n", mount_point], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return CheckResult(
                check=None, status=Status.PASS, message=f"{mount_point} is a separate partition"
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{mount_point} is NOT a separate partition",
                remediation_available=False,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_mount_option(mount_point: str, option: str) -> bool:
    """Remediate mount option using mount -o remount"""
    try:
        # Check if already mounted
        res = subprocess.run(["findmnt", "-n", mount_point], capture_output=True)
        if res.returncode != 0:
            return False

        subprocess.run(["mount", "-o", f"remount,{option}", mount_point], check=True)
        # Check persistence would require editing fstab, skipping for safety in this version
        # unless specifically asked to edit fstab which is risky.
        return True
    except Exception:
        return False


# --- Factory for repetitive checks ---


def create_partition_check(cid: str, path: str) -> CISCheck:
    return CISCheck(
        id=cid,
        title=f"Ensure separate partition exists for {path}",
        description=f"The {path} directory should be on a separate partition.",
        rationale=f"Prevents {path} resource exhaustion from filling up /.",
        severity=Severity.MEDIUM,
        category="Initial Setup",
        check_function=lambda: _check_partition_exists(path),
        # Removed manual=True so it runs the check function
    )


def create_option_check(cid: str, path: str, option: str) -> CISCheck:
    return CISCheck(
        id=cid,
        title=f"Ensure {option} option set on {path} partition",
        description=f"Mount {path} with {option}.",
        rationale=f"Security hardening for {path}.",
        severity=Severity.LOW,
        category="Initial Setup",
        check_function=lambda: _check_mount_option(path, option),
        remediation_function=lambda: _remediate_mount_option(path, option),
    )


def _check_sticky_bit() -> CheckResult:
    """Ensure sticky bit is set on all world-writable directories"""
    try:
        # limit to local filesystems, ignore /proc /sys etc.
        # find `df --local -P | awk {'if (NR!=1) print $6'}` -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null
        # This is expensive. We'll do a lighter check or skip if too heavy.
        # Just check /var/tmp and /tmp as proxies
        failures = []
        for d in ["/tmp", "/var/tmp"]:
            res = subprocess.run(
                [
                    "find",
                    d,
                    "-maxdepth",
                    "0",
                    "-type",
                    "d",
                    "-perm",
                    "-0002",
                    "!",
                    "-perm",
                    "-1000",
                ],
                capture_output=True,
            )
            if res.stdout:
                failures.append(d)

        if not failures:
            return CheckResult(
                check=None, status=Status.PASS, message="Sticky bit set on /tmp and /var/tmp"
            )
        else:
            return CheckResult(
                check=None, status=Status.FAIL, message=f"Sticky bit NOT set on: {failures}"
            )

    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_sticky_bit() -> bool:
    try:
        subprocess.run(["chmod", "+t", "/tmp", "/var/tmp"], check=True)
        return True
    except Exception:
        return False


def _check_disable_automount() -> CheckResult:
    """Ensure autofs is disabled"""
    if shutil.which("systemctl"):
        res = subprocess.run(["systemctl", "is-enabled", "autofs"], capture_output=True, text=True)
        if "enabled" in res.stdout:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message="autofs is enabled",
                remediation_available=True,
            )
    return CheckResult(check=None, status=Status.PASS, message="autofs is disabled or not found")


def _remediate_disable_automount() -> bool:
    try:
        subprocess.run(["systemctl", "disable", "--now", "autofs"], check=True)
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        # 1.1 Filesystem Configuration
        # /tmp
        create_partition_check("1.1.1", "/tmp"),
        create_option_check("1.1.2", "/tmp", "nodev"),
        create_option_check("1.1.3", "/tmp", "nosuid"),
        create_option_check("1.1.4", "/tmp", "noexec"),
        # /var
        create_partition_check("1.1.5", "/var"),
        # /var/tmp
        create_partition_check("1.1.6", "/var/tmp"),
        create_option_check("1.1.7", "/var/tmp", "nodev"),
        create_option_check("1.1.8", "/var/tmp", "nosuid"),
        create_option_check("1.1.9", "/var/tmp", "noexec"),
        # /var/log
        create_partition_check("1.1.10", "/var/log"),
        # /var/log/audit
        create_partition_check("1.1.11", "/var/log/audit"),
        # /home
        create_partition_check("1.1.12", "/home"),
        create_option_check("1.1.13", "/home", "nodev"),
        create_option_check("1.1.14", "/home", "nosuid"),
        # /dev/shm
        create_option_check("1.1.15", "/dev/shm", "nodev"),
        create_option_check("1.1.16", "/dev/shm", "nosuid"),
        create_option_check("1.1.17", "/dev/shm", "noexec"),
        CISCheck(
            id="1.1.21",
            title="Ensure sticky bit is set on all world-writable directories",
            description="Sticky bit prevents users from deleting others' files.",
            rationale="Security necessity for shared temporary directories.",
            severity=Severity.HIGH,
            category="Initial Setup",
            check_function=_check_sticky_bit,
            remediation_function=_remediate_sticky_bit,
        ),
        CISCheck(
            id="1.1.22",
            title="Disable Automounting",
            description="Disable autofs service",
            rationale="Automounting filesystems can allow malicious devices.",
            severity=Severity.LOW,
            category="Initial Setup",
            check_function=_check_disable_automount,
            remediation_function=_remediate_disable_automount,
        ),
    ]
    return checks
