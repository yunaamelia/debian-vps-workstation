import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_sysctl(param: str, expected_value: str) -> CheckResult:
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


def _remediate_sysctl(param: str, value: str) -> bool:
    try:
        subprocess.run(["sysctl", "-w", f"{param}={value}"], check=True)
        # In a real implementation this should write to /etc/sysctl.d/99-cis.conf
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = []

    sysctl_checks = [
        # IP Forwarding
        ("3.1.1", "net.ipv4.ip_forward", "0", "Ensure IP forwarding is disabled", Severity.MEDIUM),
        # Packet Redirects
        (
            "3.2.1",
            "net.ipv4.conf.all.send_redirects",
            "0",
            "Disable packet redirect sending (all)",
            Severity.MEDIUM,
        ),
        (
            "3.2.2",
            "net.ipv4.conf.default.send_redirects",
            "0",
            "Disable packet redirect sending (default)",
            Severity.MEDIUM,
        ),
        # Source Routing
        (
            "3.2.3",
            "net.ipv4.conf.all.accept_source_route",
            "0",
            "Disable source routed packets (all)",
            Severity.HIGH,
        ),
        (
            "3.2.4",
            "net.ipv4.conf.default.accept_source_route",
            "0",
            "Disable source routed packets (default)",
            Severity.HIGH,
        ),
        # ICMP Redirects
        (
            "3.2.5",
            "net.ipv4.conf.all.accept_redirects",
            "0",
            "Disable ICMP redirects (all)",
            Severity.MEDIUM,
        ),
        (
            "3.2.6",
            "net.ipv4.conf.default.accept_redirects",
            "0",
            "Disable ICMP redirects (default)",
            Severity.MEDIUM,
        ),
        # Secure Redirects
        (
            "3.2.7",
            "net.ipv4.conf.all.secure_redirects",
            "0",
            "Disable secure redirects (all)",
            Severity.MEDIUM,
        ),
        (
            "3.2.8",
            "net.ipv4.conf.default.secure_redirects",
            "0",
            "Disable secure redirects (default)",
            Severity.MEDIUM,
        ),
        # Log Martians
        (
            "3.2.9",
            "net.ipv4.conf.all.log_martians",
            "1",
            "Log suspicious packets (all)",
            Severity.LOW,
        ),
        (
            "3.2.10",
            "net.ipv4.conf.default.log_martians",
            "1",
            "Log suspicious packets (default)",
            Severity.LOW,
        ),
        # ICMP Echo
        (
            "3.2.11",
            "net.ipv4.icmp_echo_ignore_broadcasts",
            "1",
            "Ignore ICMP broadcasts",
            Severity.MEDIUM,
        ),
        (
            "3.2.12",
            "net.ipv4.icmp_ignore_bogus_error_responses",
            "1",
            "Ignore bogus ICMP responses",
            Severity.LOW,
        ),
        # Reverse Path Filtering
        (
            "3.2.13",
            "net.ipv4.conf.all.rp_filter",
            "1",
            "Enable Reverse Path Filtering (all)",
            Severity.HIGH,
        ),
        (
            "3.2.14",
            "net.ipv4.conf.default.rp_filter",
            "1",
            "Enable Reverse Path Filtering (default)",
            Severity.HIGH,
        ),
        # TCP SYN Cookies
        ("3.2.15", "net.ipv4.tcp_syncookies", "1", "Enable TCP SYN Cookies", Severity.HIGH),
        # IPv6 (Optional to disable)
        # ("3.3.1", "net.ipv6.conf.all.disable_ipv6", "1", "Disable IPv6", Severity.LOW),
    ]

    for cid, param, val, title, sev in sysctl_checks:
        checks.append(
            CISCheck(
                id=cid,
                title=title,
                description=f"Ensure {param} is set to {val}",
                rationale="Network hardening.",
                severity=sev,
                category="Network",
                check_function=lambda p=param, v=val: _check_sysctl(p, v),
                remediation_function=lambda p=param, v=val: _remediate_sysctl(p, v),
            )
        )

    return checks
