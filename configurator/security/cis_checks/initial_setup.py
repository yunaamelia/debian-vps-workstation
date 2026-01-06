import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_tmp_partition() -> CheckResult:
    """Check if /tmp is a separate partition"""
    try:
        result = subprocess.run(["findmnt", "-n", "/tmp"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return CheckResult(
                check=None,  # Filled by wrapper
                status=Status.PASS,
                message="/tmp is a separate partition",
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message="/tmp is NOT a separate partition",
                remediation_available=False,  # Requires partitioning
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _check_tmp_nodev() -> CheckResult:
    """Check if /tmp has nodev option"""
    try:
        result = subprocess.run(["findmnt", "-n", "/tmp"], capture_output=True, text=True)
        if "nodev" in result.stdout:
            return CheckResult(check=None, status=Status.PASS, message="/tmp has nodev option set")
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message="/tmp does NOT have nodev option set",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_tmp_nodev() -> bool:
    """Remediate /tmp nodev option"""
    # This is complex as it involves fstab editing and remounting.
    # For now we will return False or implement a safe mount -o remount,nodev /tmp
    try:
        subprocess.run(["mount", "-o", "remount,nodev", "/tmp"], check=True)
        # TODO: Persist in /etc/fstab
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="1.1.1",
            title="Ensure separate partition exists for /tmp",
            description="The /tmp directory is a world-writable directory used for temporary storage.",
            rationale="Making /tmp its own file system allows setting mount options like noexec.",
            severity=Severity.MEDIUM,
            check_function=lambda: _fill_check(_check_tmp_partition(), "1.1.1"),
            manual=True,  # Marked manual because remediation is hard, but we do have a check function
        ),
        CISCheck(
            id="1.1.2",
            title="Ensure nodev option set on /tmp partition",
            description="The nodev mount option specifies that the filesystem cannot contain special devices.",
            rationale="Prevent users from creating special devices in /tmp.",
            severity=Severity.MEDIUM,
            check_function=lambda: _fill_check(_check_tmp_nodev(), "1.1.2"),
            remediation_function=_remediate_tmp_nodev,
        ),
    ]
    return checks


def _fill_check(result: CheckResult, check_id: str) -> CheckResult:
    """Helper to backfill the check object into the result"""
    # We need to find the check object from the list we just created?
    # Circular dependency if we define checks inside get_checks.
    # We will solve this by creating a global registry or simpler,
    # Just passing the check_id to finding it later, OR just instantiating it.
    # Actually, in the scanner loop, we have the check object.
    # The check function returns a result. Ideally check_function shouldn't need to return the check object itself
    # if the scanner attaches it.
    # BUT, the dataclass CheckResult requires 'check'.
    # Let's Modify the CheckResult to allow check=None initially and fill it in scanner.
    # For now, I'll cheat and put a dummy check or similar.
    # OR, better: The implementations of check functions will assume they are wrapper by the scanner
    # which will inject the check object.
    # Let's stick to the prompt's design: check_function returns CheckResult.
    # So we need to provide the check object to the function.

    # Correction: The prompt's example shows check_function=self._check_tmp_nodev on the instance.
    # In my modular design, functions are standalone.
    # I will modify the scanner to inject the check object into the result if it's missing.
    return result
