import shutil
import subprocess
from typing import List

from configurator.security.cis_scanner import CheckResult, CISCheck, Severity, Status


def _check_package_removed(package_name: str) -> CheckResult:
    """Generic check for removed package"""
    if shutil.which("dpkg") is None:
        return CheckResult(check=None, status=Status.ERROR, message="dpkg not found")

    try:
        # dpkg -s returns 0 if installed, 1 if not
        # Use explicit check=False since we handle the return code manually
        result = subprocess.run(["dpkg", "-s", package_name], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{package_name} is not installed"
            )
        else:
            # Check if it's actually installed or just config-files (purged vs removed)
            if "Status: install ok installed" in result.stdout:
                return CheckResult(
                    check=None,
                    status=Status.FAIL,
                    message=f"{package_name} is installed",
                    remediation_available=True,
                )
            else:
                return CheckResult(
                    check=None,
                    status=Status.PASS,
                    message=f"{package_name} is not installed (config files may remain)",
                )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_remove_package(package_name: str) -> bool:
    try:
        subprocess.run(["apt-get", "purge", "-y", package_name], check=True)
        return True
    except Exception:
        return False


def _check_service_masked(service_name: str) -> CheckResult:
    """Check if a service is masked/disabled"""
    try:
        # systemctl list-unit-files | grep service_name
        # OR systemctl is-enabled
        res = subprocess.run(
            ["systemctl", "is-enabled", service_name], capture_output=True, text=True
        )
        status = res.stdout.strip()
        if status in ["masked", "disabled"]:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{service_name} is {status}"
            )
        elif res.returncode != 0 and "No such file or directory" in res.stderr:
            return CheckResult(
                check=None, status=Status.PASS, message=f"{service_name} is not installed"
            )
        else:
            return CheckResult(
                check=None,
                status=Status.FAIL,
                message=f"{service_name} is {status} (should be disabled/masked)",
                remediation_available=True,
            )
    except Exception as e:
        return CheckResult(check=None, status=Status.ERROR, message=str(e))


def _remediate_mask_service(service_name: str) -> bool:
    try:
        # Check=False is acceptable here as service might not be running
        subprocess.run(["systemctl", "disable", "--now", service_name], check=False)
        subprocess.run(["systemctl", "mask", service_name], check=True)
        return True
    except Exception:
        return False


def get_checks() -> List[CISCheck]:
    checks = []

    # 2.1 inetd Services
    legacy_services = [
        ("2.1.1", "inetd", "Ensure inetd is not installed"),
        ("2.1.2", "openbsd-inetd", "Ensure openbsd-inetd is not installed"),
        ("2.1.3", "xinetd", "Ensure xinetd is not installed"),
    ]

    for cid, pkg, title in legacy_services:
        checks.append(
            CISCheck(
                id=cid,
                title=title,
                description=f"Remove {pkg}",
                rationale="Legacy super-server.",
                severity=Severity.HIGH,
                category="Services",
                check_function=lambda p=pkg: _check_package_removed(p),
                remediation_function=lambda p=pkg: _remediate_remove_package(p),
            )
        )

    # 2.2 Special Purpose Services
    special_services = [
        ("2.2.1", "xserver-xorg-core", "Ensure X Window System is not installed", Severity.MEDIUM),
        ("2.2.2", "avahi-daemon", "Ensure Avahi Server is not installed", Severity.LOW),
        ("2.2.3", "cups", "Ensure CUPS is not installed", Severity.LOW),
        ("2.2.4", "isc-dhcp-server", "Ensure DHCP Server is not installed", Severity.LOW),
        ("2.2.5", "slapd", "Ensure LDAP server is not installed", Severity.LOW),
        ("2.2.6", "nfs-kernel-server", "Ensure NFS is not installed", Severity.MEDIUM),
        ("2.2.7", "bind9", "Ensure DNS Server is not installed", Severity.LOW),
        ("2.2.8", "vsftpd", "Ensure FTP Server is not installed", Severity.HIGH),
        ("2.2.9", "tftpd-hpa", "Ensure TFTP Server is not installed", Severity.HIGH),
        ("2.2.10", "smbd", "Ensure Samba is not installed", Severity.HIGH),
        ("2.2.11", "snmpd", "Ensure SNMP Server is not installed", Severity.MEDIUM),
        ("2.2.12", "rsync", "Ensure rsync service is not installed (if not needed)", Severity.LOW),
        ("2.3.1", "nis", "Ensure NIS Server is not installed", Severity.HIGH),
        ("2.3.2", "rsh-client", "Ensure rsh client is not installed", Severity.HIGH),
        ("2.3.3", "rsh-redone-client", "Ensure rsh-redone-client is not installed", Severity.HIGH),
        ("2.3.4", "talk", "Ensure talk client is not installed", Severity.LOW),
        ("2.3.5", "telnet", "Ensure telnet client is not installed", Severity.HIGH),
        ("2.3.6", "ldap-utils", "Ensure LDAP client is not installed", Severity.LOW),
        ("2.3.7", "rpcbind", "Ensure RPC is not installed", Severity.HIGH),
    ]

    for cid, pkg, title, severity in special_services:
        checks.append(
            CISCheck(
                id=cid,
                title=title,
                description=f"Remove {pkg}",
                rationale="Reduce attack surface.",
                severity=severity,
                category="Services",
                check_function=lambda p=pkg: _check_package_removed(p),
                remediation_function=lambda p=pkg: _remediate_remove_package(p),
            )
        )

    return checks
