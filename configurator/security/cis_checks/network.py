import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_sysctl(param: str, expected_value: str) -> CheckResult:
    """Check sysctl parameter"""
    try:
        # sysctl -n param
        result = subprocess.run(["sysctl", "-n", param], capture_output=True, text=True)
        if result.returncode != 0:
            return CheckResult(check=None, status=Status.ERROR, message=f"Failed to read {param}")

        actual_value = result.stdout.strip()
        # Handle multiple values (e.g. for .all. and .default.) if checked individually
        # But here we usually check one specific key

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


def _remediate_sysctl(param: str, value: str) -> bool:
    try:
        subprocess.run(["sysctl", "-w", f"{param}={value}"], check=True)
        # TODO: Persist in /etc/sysctl.d/
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="3.1.1",
            title="Ensure packet redirect sending is disabled",
            description="Disable sending ICMP redirects.",
            rationale="Prevents malicious routing updates.",
            severity=Severity.MEDIUM,
            check_function=lambda: _check_sysctl("net.ipv4.conf.all.send_redirects", "0"),
            remediation_function=lambda: _remediate_sysctl("net.ipv4.conf.all.send_redirects", "0"),
            category="Network",
        ),
        CISCheck(
            id="3.2.1",
            title="Ensure source routed packets are not accepted",
            description="Disable source routing.",
            rationale="Prevents attackers from steering packets.",
            severity=Severity.HIGH,
            check_function=lambda: _check_sysctl("net.ipv4.conf.all.accept_source_route", "0"),
            remediation_function=lambda: _remediate_sysctl(
                "net.ipv4.conf.all.accept_source_route", "0"
            ),
            category="Network",
        ),
    ]
    return checks
