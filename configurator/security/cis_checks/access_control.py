import re
import subprocess
from pathlib import Path
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_sshd_config(
    pattern: str, expected_values: List[str], config_path: str = "/etc/ssh/sshd_config"
) -> CheckResult:
    path = Path(config_path)
    if not path.exists():
        return CheckResult(check=None, status=Status.ERROR, message=f"{config_path} not found")

    try:
        content = path.read_text()
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            value = match.group(1).strip().lower()
            # Handle quoted values
            value = value.strip('"').strip("'")

            if value in [v.lower() for v in expected_values]:
                return CheckResult(
                    check=None,
                    status=Status.PASS,
                    message=f"Configuration matches: found {value}",
                    details={"value": value},
                )
            else:
                return CheckResult(
                    check=None,
                    status=Status.FAIL,
                    message=f"Configuration mismatch: found {value}, expected {expected_values}",
                    remediation_available=True,
                    details={"value": value, "expected": expected_values},
                )
        else:
            # Logic for default values if not present?
            # For security, explicit is better usually.
            # But for PermitRootLogin, default depends on version.
            # We'll fail if not explicit for now strict compliance.
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"Setting check failed, pattern not found via regex: {pattern}",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_sshd_config(setting: str, value: str) -> bool:
    try:
        config_path = Path("/etc/ssh/sshd_config")
        if not config_path.exists():
            return False

        # Simple append or sed-like replace?
        # A proper config parser is better but for now regex replace
        content = config_path.read_text()

        # Regex to find the line (commented or not)
        # We look for ^\s*#?\s*Setting\s+.*
        pattern = re.compile(f"^\\s*#?\\s*{setting}\\s+.*$", re.MULTILINE | re.IGNORECASE)

        if pattern.search(content):
            new_content = pattern.sub(f"{setting} {value}", content)
        else:
            new_content = content + f"\n{setting} {value}\n"

        config_path.write_text(new_content)

        # Reload sshd
        subprocess.run(["systemctl", "reload", "ssh"], check=False)
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = [
        CISCheck(
            id="5.2.2",
            title="Ensure SSH PermitRootLogin is disabled",
            description="Disable direct root login via SSH.",
            rationale="Force use of unprivileged accounts.",
            severity=Severity.CRITICAL,
            check_function=lambda: _check_sshd_config(
                r"^\s*PermitRootLogin\s+(.+)$", ["no", "prohibit-password"]
            ),
            remediation_function=lambda: _remediate_sshd_config("PermitRootLogin", "no"),
            category="Access Control",
        ),
        CISCheck(
            id="5.2.3",
            title="Ensure SSH PermitEmptyPasswords is disabled",
            description="Disallow empty passwords.",
            rationale="Prevents password-less login.",
            severity=Severity.HIGH,
            check_function=lambda: _check_sshd_config(r"^\s*PermitEmptyPasswords\s+(.+)$", ["no"]),
            remediation_function=lambda: _remediate_sshd_config("PermitEmptyPasswords", "no"),
            category="Access Control",
        ),
    ]
    return checks
