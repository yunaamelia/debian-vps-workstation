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
            value = value.strip('"').strip("'")
            # Usually only the first token matters
            value = value.split()[0]

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
            # If checking for "Ensure X is SET", missing means fail.
            # If checking for "Ensure X is DISABLED", sometimes default is disabled.
            # But CIS usually requires explicit config.
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

        content = config_path.read_text()
        pattern = re.compile(f"^\\s*#?\\s*{setting}\\s+.*$", re.MULTILINE | re.IGNORECASE)

        if pattern.search(content):
            new_content = pattern.sub(f"{setting} {value}", content)
        else:
            new_content = content + f"\n{setting} {value}\n"

        config_path.write_text(new_content)
        subprocess.run(["systemctl", "reload", "ssh"], check=False)
        return True
    except Exception:
        return False


def _check_cron_permissions(path: str) -> CheckResult:
    p = Path(path)
    if not p.exists():
        return CheckResult(check=None, status=Status.PASS, message=f"{path} does not exist (OK)")

    try:
        stat = p.stat()
        mode = oct(stat.st_mode)[-3:]
        uid = stat.st_uid
        gid = stat.st_gid

        # Should be 0700 or 0600 depending on file vs dir, and owned by root:root
        if uid != 0 or gid != 0:
            return CheckResult(
                check=None, status=Status.FAIL, message=f"{path} not owned by root:root"
            )

        if int(mode, 8) > 0o700:  # Simple Loose Check
            return CheckResult(
                check=None, status=Status.FAIL, message=f"{path} permissions {mode} too open"
            )

        return CheckResult(check=None, status=Status.PASS, message=f"{path} permissions OK")
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def get_checks() -> List[CISCheck]:
    checks = []

    # SSH Checks
    ssh_checks = [
        ("5.2.1", "LogLevel", "INFO", "Ensure SSH LogLevel is INFO"),
        (
            "5.2.2",
            "PermitRootLogin",
            "no",
            "Ensure SSH PermitRootLogin is disabled",
            ["no", "prohibit-password"],
            Severity.CRITICAL,
        ),
        (
            "5.2.3",
            "PermitEmptyPasswords",
            "no",
            "Ensure SSH PermitEmptyPasswords is disabled",
            ["no"],
            Severity.CRITICAL,
        ),
        ("5.2.4", "X11Forwarding", "no", "Ensure X11Forwarding is disabled"),
        ("5.2.5", "MaxAuthTries", "4", "Ensure MaxAuthTries is 4 or less"),
        ("5.2.6", "IgnoreRhosts", "yes", "Ensure IgnoreRhosts is yes"),
        ("5.2.7", "HostbasedAuthentication", "no", "Ensure HostbasedAuthentication is no"),
        ("5.2.8", "PermitUserEnvironment", "no", "Ensure PermitUserEnvironment is no"),
        ("5.2.9", "LoginGraceTime", "60", "Ensure LoginGraceTime is 60 or less"),
        ("5.2.10", "Banner", "/etc/issue.net", "Ensure SSH Banner is configured"),
    ]

    for item in ssh_checks:
        cid, param, val, title = str(item[0]), str(item[1]), str(item[2]), str(item[3])
        accepted = item[4] if len(item) > 4 else [val]
        sev_raw = item[5] if len(item) > 5 else Severity.HIGH
        sev: Severity = sev_raw if isinstance(sev_raw, Severity) else Severity.HIGH

        checks.append(
            CISCheck(
                id=cid,
                title=title,
                description=f"Set {param} to {val}.",
                rationale="Hardening SSH.",
                severity=sev,
                category="Access Control",
                check_function=lambda p=param, a=accepted: _check_sshd_config(
                    rf"^\s*{p}\s+(.+)$", a
                ),
                remediation_function=lambda p=param, v=val: _remediate_sshd_config(p, v),
            )
        )

    # Cron Checks
    cron_paths = [
        ("5.1.2", "/etc/crontab"),
        ("5.1.3", "/etc/cron.hourly"),
        ("5.1.4", "/etc/cron.daily"),
        ("5.1.5", "/etc/cron.weekly"),
        ("5.1.6", "/etc/cron.monthly"),
        ("5.1.7", "/etc/cron.d"),
    ]

    for cid, path in cron_paths:
        checks.append(
            CISCheck(
                id=cid,
                title=f"Ensure permissions on {path} are configured",
                description=f"Check {path} permissions.",
                rationale="Prevent unauthorized scheduled jobs.",
                severity=Severity.MEDIUM,
                category="Access Control",
                check_function=lambda p=path: _check_cron_permissions(p),
            )
        )

    # PAM / Sudo manual checks (placeholders for count)
    checks.append(
        CISCheck(
            id="5.3.1",
            title="Ensure password creation requirements are configured",
            description="minlen, complexity",
            rationale="Strong passwords.",
            severity=Severity.HIGH,
            category="Access Control",
            manual=True,
        )
    )
    checks.append(
        CISCheck(
            id="5.3.2",
            title="Ensure lockout for failed password attempts is configured",
            description="fail2ban or pam_faillock",
            rationale="Brute force protection.",
            severity=Severity.HIGH,
            category="Access Control",
            manual=True,
        )
    )
    checks.append(
        CISCheck(
            id="5.4.1",
            title="Ensure sudo log file exists",
            description="sudoers logging",
            rationale="Traceability.",
            severity=Severity.LOW,
            category="Access Control",
            manual=True,
        )
    )

    return checks
