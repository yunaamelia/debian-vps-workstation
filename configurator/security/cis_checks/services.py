from typing import Callable, List

from configurator.security.cis_checks.utils import (
    check_package_removed,
    remediate_remove_package,
)
from configurator.security.cis_scanner import CheckResult, CISCheck, Severity


def _create_check_func(pkg: str) -> Callable[[], CheckResult]:
    return lambda: check_package_removed(pkg)


def _create_remediate_func(pkg: str) -> Callable[[], bool]:
    return lambda: remediate_remove_package(pkg)


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
                check_function=_create_check_func(pkg),
                remediation_function=_create_remediate_func(pkg),
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
                check_function=_create_check_func(pkg),
                remediation_function=_create_remediate_func(pkg),
            )
        )

    return checks
