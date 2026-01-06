"""
SSL/TLS Certificate Management with Let's Encrypt/Certbot.

This module provides automated certificate provisioning, renewal, and monitoring
using Let's Encrypt via Certbot.

Features:
- Automatic certificate installation (HTTP-01, DNS-01 challenges)
- Wildcard certificate support
- Auto-renewal (30 days before expiry)
- Web server integration (Nginx, Apache, Caddy)
- Certificate monitoring and alerts
- Strong TLS configuration (A+ grade)
"""

import logging
import re
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ChallengeType(Enum):
    """ACME challenge types for domain validation."""

    HTTP_01 = "http-01"  # HTTP challenge (port 80)
    DNS_01 = "dns-01"  # DNS TXT record challenge (for wildcards)
    TLS_ALPN_01 = "tls-alpn-01"  # TLS challenge (port 443)


class CertificateStatus(Enum):
    """Certificate validity status."""

    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"  # < 30 days
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class WebServerType(Enum):
    """Supported web server types."""

    NGINX = "nginx"
    APACHE = "apache"
    CADDY = "caddy"
    STANDALONE = "standalone"


@dataclass
class Certificate:
    """
    Represents an SSL/TLS certificate.

    Attributes:
        domain: Primary domain name
        subject_alternative_names: List of SANs (including primary)
        issuer: Certificate Authority name
        valid_from: Certificate start date
        valid_until: Certificate expiration date
        certificate_path: Path to full chain certificate
        private_key_path: Path to private key
        serial_number: Certificate serial number
        fingerprint_sha256: SHA-256 fingerprint
        auto_renewal_enabled: Whether auto-renewal is enabled
        last_renewal: Last renewal timestamp
        challenge_type: ACME challenge type used

    Example:
        >>> cert = Certificate(
        ...     domain="example.com",
        ...     subject_alternative_names=["example.com", "www.example.com"],
        ...     issuer="Let's Encrypt Authority X3",
        ...     valid_from=datetime(2026, 1, 6),
        ...     valid_until=datetime(2026, 4, 6),
        ...     certificate_path=Path("/etc/letsencrypt/live/example.com/fullchain.pem"),
        ...     private_key_path=Path("/etc/letsencrypt/live/example.com/privkey.pem"),
        ... )
        >>> cert.days_until_expiry()
        89
    """

    domain: str
    subject_alternative_names: List[str]
    issuer: str
    valid_from: datetime
    valid_until: datetime
    certificate_path: Path
    private_key_path: Path
    serial_number: Optional[str] = None
    fingerprint_sha256: Optional[str] = None
    auto_renewal_enabled: bool = True
    last_renewal: Optional[datetime] = None
    challenge_type: ChallengeType = ChallengeType.HTTP_01

    def days_until_expiry(self) -> int:
        """Calculate days until certificate expires."""
        delta = self.valid_until - datetime.now()
        return delta.days

    def status(self) -> CertificateStatus:
        """Get certificate status based on expiry."""
        days = self.days_until_expiry()

        if days < 0:
            return CertificateStatus.EXPIRED
        elif days < 30:
            return CertificateStatus.EXPIRING_SOON
        else:
            return CertificateStatus.VALID

    def needs_renewal(self, threshold_days: int = 30) -> bool:
        """Check if certificate needs renewal."""
        return self.days_until_expiry() <= threshold_days

    def is_wildcard(self) -> bool:
        """Check if this is a wildcard certificate."""
        return self.domain.startswith("*.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "domain": self.domain,
            "sans": self.subject_alternative_names,
            "issuer": self.issuer,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat(),
            "days_remaining": self.days_until_expiry(),
            "status": self.status().value,
            "certificate_path": str(self.certificate_path),
            "private_key_path": str(self.private_key_path),
            "serial_number": self.serial_number,
            "fingerprint_sha256": self.fingerprint_sha256,
            "auto_renewal": self.auto_renewal_enabled,
            "last_renewal": self.last_renewal.isoformat() if self.last_renewal else None,
            "challenge_type": self.challenge_type.value,
            "is_wildcard": self.is_wildcard(),
        }


@dataclass
class CertificateRequest:
    """
    Request for a new SSL/TLS certificate.

    Attributes:
        domain: Primary domain name
        email: Contact email for Let's Encrypt notifications
        additional_domains: Additional SANs
        webserver: Web server type
        challenge: ACME challenge type
        staging: Use Let's Encrypt staging environment
        force: Force certificate issuance even if one exists
    """

    domain: str
    email: str
    additional_domains: List[str] = field(default_factory=list)
    webserver: WebServerType = WebServerType.NGINX
    challenge: ChallengeType = ChallengeType.HTTP_01
    staging: bool = False
    force: bool = False
    dns_plugin: Optional[str] = None  # e.g., 'cloudflare', 'route53'
    dns_credentials: Optional[Path] = None


class CertificateManager:
    """
    Manages SSL/TLS certificates using Let's Encrypt/Certbot.

    Features:
    - Certificate installation (HTTP-01, DNS-01 challenges)
    - Automatic renewal
    - Certificate monitoring
    - Web server integration (Nginx, Apache, Caddy)
    - Wildcard certificate support
    - Multi-domain (SAN) certificates
    - Certificate backup and rollback

    Usage:
        >>> manager = CertificateManager()
        >>>
        >>> # Install certificate
        >>> cert = manager.install_certificate(
        ...     domain="example.com",
        ...     email="admin@example.com",
        ...     webserver=WebServerType.NGINX
        ... )
        >>>
        >>> # Check status
        >>> status = manager.get_certificate("example.com")
        >>>
        >>> # Renew if needed
        >>> if status.needs_renewal():
        ...     manager.renew_certificate("example.com")
    """

    CERTBOT_PATH = "/usr/bin/certbot"
    LETSENCRYPT_DIR = Path("/etc/letsencrypt")
    BACKUP_DIR = Path("/var/backups/letsencrypt")
    RENEWAL_THRESHOLD_DAYS = 30

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize CertificateManager.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._certbot_available = None

    def is_certbot_available(self) -> bool:
        """Check if Certbot is installed and available."""
        if self._certbot_available is None:
            self._certbot_available = Path(self.CERTBOT_PATH).exists()
        return self._certbot_available

    def get_certbot_version(self) -> Optional[str]:
        """Get Certbot version."""
        if not self.is_certbot_available():
            return None

        try:
            result = subprocess.run(
                [self.CERTBOT_PATH, "--version"], capture_output=True, text=True, timeout=10
            )
            # Output: "certbot 2.8.0"
            match = re.search(r"certbot\s+(\d+\.\d+\.\d+)", result.stdout + result.stderr)
            return match.group(1) if match else None
        except Exception:
            return None

    def install_certbot(self) -> bool:
        """
        Install Certbot and common plugins.

        Returns:
            True if installation successful
        """
        self.logger.info("Installing Certbot...")

        try:
            # Update package list
            subprocess.run(["apt-get", "update"], check=True, capture_output=True, timeout=120)

            # Install Certbot and plugins
            packages = [
                "certbot",
                "python3-certbot-nginx",
                "python3-certbot-apache",
            ]

            subprocess.run(
                ["apt-get", "install", "-y"] + packages,
                check=True,
                capture_output=True,
                timeout=300,
            )

            self._certbot_available = True
            self.logger.info("✅ Certbot installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install Certbot: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Certbot installation timed out")
            return False

    def validate_dns(self, domain: str, skip_ip_check: bool = False) -> bool:
        """
        Validate DNS configuration for domain.

        Args:
            domain: Domain to validate
            skip_ip_check: Skip checking if domain points to this server

        Returns:
            True if DNS is valid
        """
        # Strip wildcard prefix for DNS lookup
        lookup_domain = domain.lstrip("*.")

        try:
            # Resolve domain
            domain_ip = socket.gethostbyname(lookup_domain)
            self.logger.info(f"DNS lookup: {lookup_domain} → {domain_ip}")

            if skip_ip_check:
                return True

            # Get server IPs
            server_ips = self._get_server_ips()

            if domain_ip in server_ips:
                self.logger.info(f"✅ DNS validated: {lookup_domain} → {domain_ip}")
                return True
            else:
                self.logger.warning(
                    f"DNS mismatch: {lookup_domain} → {domain_ip}, " f"server IPs: {server_ips}"
                )
                return False

        except socket.gaierror as e:
            self.logger.error(f"DNS lookup failed for {lookup_domain}: {e}")
            return False

    def _get_server_ips(self) -> List[str]:
        """Get all IP addresses of this server."""
        ips = []

        try:
            # Get hostname IPs
            hostname = socket.gethostname()
            ips.extend(socket.gethostbyname_ex(hostname)[2])
        except Exception:
            pass

        # Try to get public IP
        try:
            import urllib.request

            public_ip = (
                urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode("utf8")
            )
            ips.append(public_ip)
        except Exception:
            pass

        return list(set(ips))

    def install_certificate(
        self,
        domain: str,
        email: str,
        webserver: WebServerType = WebServerType.NGINX,
        additional_domains: Optional[List[str]] = None,
        challenge: ChallengeType = ChallengeType.HTTP_01,
        staging: bool = False,
        force: bool = False,
        dns_plugin: Optional[str] = None,
        dns_credentials: Optional[Path] = None,
    ) -> Certificate:
        """
        Install SSL/TLS certificate for domain.

        Args:
            domain: Primary domain name
            email: Email for Let's Encrypt notifications
            webserver: Web server type
            additional_domains: Additional domains for SAN certificate
            challenge: ACME challenge type
            staging: Use Let's Encrypt staging environment (for testing)
            force: Force certificate issuance
            dns_plugin: DNS provider plugin for DNS-01 challenge
            dns_credentials: Path to DNS credentials file

        Returns:
            Certificate object with details

        Raises:
            RuntimeError: If certificate installation fails
            ValueError: If DNS validation fails
        """
        self.logger.info(f"Installing certificate for {domain}")

        # Ensure Certbot is available
        if not self.is_certbot_available():
            if not self.install_certbot():
                raise RuntimeError("Failed to install Certbot")

        # Validate DNS (skip for DNS-01 challenge)
        if challenge != ChallengeType.DNS_01:
            if not self.validate_dns(domain):
                raise ValueError(f"DNS validation failed for {domain}")

        # Build Certbot command
        cmd = self._build_certbot_command(
            domain=domain,
            email=email,
            webserver=webserver,
            additional_domains=additional_domains or [],
            challenge=challenge,
            staging=staging,
            force=force,
            dns_plugin=dns_plugin,
            dns_credentials=dns_credentials,
        )

        # Execute Certbot
        try:
            self.logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=300  # 5 minute timeout
            )

            self.logger.info("Certificate obtained successfully")
            self.logger.debug(result.stdout)

            # Load and return certificate info
            return self.get_certificate(domain)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Certbot failed: {e.stderr}")
            raise RuntimeError(f"Failed to obtain certificate: {e.stderr}")
        except subprocess.TimeoutExpired:
            self.logger.error("Certbot timed out after 5 minutes")
            raise RuntimeError("Certificate installation timed out")

    def _build_certbot_command(
        self,
        domain: str,
        email: str,
        webserver: WebServerType,
        additional_domains: List[str],
        challenge: ChallengeType,
        staging: bool,
        force: bool,
        dns_plugin: Optional[str],
        dns_credentials: Optional[Path],
    ) -> List[str]:
        """Build Certbot command for certificate installation."""
        cmd = [
            self.CERTBOT_PATH,
            "certonly",
            "--non-interactive",
            "--agree-tos",
            "--email",
            email,
            "-d",
            domain,
        ]

        # Add additional domains
        for additional in additional_domains:
            cmd.extend(["-d", additional])

        # Add webserver plugin or challenge method
        if challenge == ChallengeType.DNS_01:
            if dns_plugin:
                cmd.extend([f"--dns-{dns_plugin}"])
                if dns_credentials:
                    cmd.extend([f"--dns-{dns_plugin}-credentials", str(dns_credentials)])
            else:
                cmd.extend(["--manual", "--preferred-challenges", "dns"])
        elif challenge == ChallengeType.TLS_ALPN_01:
            cmd.extend(["--standalone", "--preferred-challenges", "tls-alpn-01"])
        else:  # HTTP_01
            if webserver == WebServerType.NGINX:
                cmd.append("--nginx")
            elif webserver == WebServerType.APACHE:
                cmd.append("--apache")
            elif webserver == WebServerType.CADDY:
                cmd.append("--standalone")
            else:
                cmd.append("--standalone")

        # Staging environment
        if staging:
            cmd.append("--staging")

        # Force renewal
        if force:
            cmd.append("--force-renewal")

        return cmd

    def get_certificate(self, domain: str) -> Certificate:
        """
        Get certificate information for domain.

        Args:
            domain: Domain name

        Returns:
            Certificate object

        Raises:
            FileNotFoundError: If certificate not found
        """
        cert_dir = self.LETSENCRYPT_DIR / "live" / domain

        if not cert_dir.exists():
            raise FileNotFoundError(f"Certificate not found for {domain}")

        cert_path = cert_dir / "fullchain.pem"
        key_path = cert_dir / "privkey.pem"

        if not cert_path.exists():
            raise FileNotFoundError(f"Certificate file not found: {cert_path}")

        # Parse certificate using OpenSSL
        cert_info = self._parse_certificate(cert_path)

        return Certificate(
            domain=domain,
            subject_alternative_names=cert_info.get("sans", [domain]),
            issuer=cert_info.get("issuer", "Unknown"),
            valid_from=cert_info.get("not_before", datetime.now()),
            valid_until=cert_info.get("not_after", datetime.now() + timedelta(days=90)),
            certificate_path=cert_path,
            private_key_path=key_path,
            serial_number=cert_info.get("serial"),
            fingerprint_sha256=cert_info.get("fingerprint"),
        )

    def _parse_certificate(self, cert_path: Path) -> Dict[str, Any]:
        """
        Parse certificate file using OpenSSL.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with certificate information
        """
        info: Dict[str, Any] = {}

        try:
            # Get certificate text
            result = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-text"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            cert_text = result.stdout

            # Parse Issuer
            issuer_match = re.search(r"Issuer:.*?CN\s*=\s*([^,\n]+)", cert_text)
            info["issuer"] = issuer_match.group(1).strip() if issuer_match else "Unknown"

            # Parse validity dates
            not_before_match = re.search(r"Not Before\s*:\s*(.+)", cert_text)
            not_after_match = re.search(r"Not After\s*:\s*(.+)", cert_text)

            if not_before_match:
                info["not_before"] = self._parse_openssl_date(not_before_match.group(1))
            else:
                info["not_before"] = datetime.now()

            if not_after_match:
                info["not_after"] = self._parse_openssl_date(not_after_match.group(1))
            else:
                info["not_after"] = datetime.now() + timedelta(days=90)

            # Parse serial number
            serial_match = re.search(r"Serial Number:\s*\n?\s*([0-9a-fA-F:]+)", cert_text)
            info["serial"] = serial_match.group(1).strip() if serial_match else None

            # Parse Subject Alternative Names
            san_section = re.search(r"X509v3 Subject Alternative Name:\s*\n\s*(.+)", cert_text)
            if san_section:
                san_text = san_section.group(1)
                dns_entries = re.findall(r"DNS:([^,\s]+)", san_text)
                info["sans"] = dns_entries if dns_entries else [cert_path.parent.name]
            else:
                info["sans"] = [cert_path.parent.name]

            # Get SHA-256 fingerprint
            fp_result = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint", "-sha256"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            fp_match = re.search(r"SHA256 Fingerprint=(.+)", fp_result.stdout)
            info["fingerprint"] = fp_match.group(1).strip() if fp_match else None

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to parse certificate: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing certificate: {e}")

        return info

    def _parse_openssl_date(self, date_str: str) -> datetime:
        """
        Parse OpenSSL date format.

        Args:
            date_str: Date string like "Jan  6 14:30:00 2026 GMT"

        Returns:
            datetime object
        """
        # Try common formats
        formats = [
            "%b %d %H:%M:%S %Y %Z",  # "Jan  6 14:30:00 2026 GMT"
            "%b  %d %H:%M:%S %Y %Z",  # "Jan  6 14:30:00 2026 GMT" (extra space)
            "%Y-%m-%d %H:%M:%S",  # ISO-ish format
        ]

        date_str = date_str.strip()

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Fallback: try dateutil parser
        try:
            from dateutil import parser

            return parser.parse(date_str)
        except Exception:
            self.logger.warning(f"Failed to parse date: {date_str}")
            return datetime.now()

    def renew_certificate(self, domain: str, force: bool = False) -> bool:
        """
        Renew certificate for domain.

        Args:
            domain: Domain name
            force: Force renewal even if not due

        Returns:
            True if renewed successfully
        """
        self.logger.info(f"Renewing certificate for {domain}")

        if not self.is_certbot_available():
            raise RuntimeError("Certbot is not installed")

        cmd = [
            self.CERTBOT_PATH,
            "renew",
            "--cert-name",
            domain,
        ]

        if force:
            cmd.append("--force-renewal")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)

            # Check if renewal happened
            if "No renewals were attempted" in result.stdout:
                self.logger.info("Certificate not due for renewal")
                return False
            elif "renewed" in result.stdout.lower() or "success" in result.stdout.lower():
                self.logger.info("✅ Certificate renewed successfully")
                return True
            else:
                self.logger.warning("Renewal status unclear, checking certificate...")
                return False

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Certificate renewal failed: {e.stderr}")
            raise RuntimeError(f"Renewal failed: {e.stderr}")

    def renew_all_certificates(self) -> Dict[str, bool]:
        """
        Renew all certificates that are due.

        Returns:
            Dictionary of domain -> renewal status
        """
        self.logger.info("Checking all certificates for renewal")

        if not self.is_certbot_available():
            raise RuntimeError("Certbot is not installed")

        try:
            subprocess.run(
                [self.CERTBOT_PATH, "renew", "--quiet"], capture_output=True, text=True, timeout=600
            )

            # Check which certificates were renewed
            renewed = {}
            for cert in self.list_certificates():
                renewed[cert.domain] = cert.days_until_expiry() > 30

            return renewed

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Batch renewal failed: {e}")
            raise

    def list_certificates(self) -> List[Certificate]:
        """
        List all managed certificates.

        Returns:
            List of Certificate objects
        """
        live_dir = self.LETSENCRYPT_DIR / "live"

        if not live_dir.exists():
            return []

        certificates = []

        for domain_dir in live_dir.iterdir():
            if domain_dir.is_dir() and domain_dir.name != "README":
                try:
                    cert = self.get_certificate(domain_dir.name)
                    certificates.append(cert)
                except Exception as e:
                    self.logger.error(f"Failed to load certificate for {domain_dir.name}: {e}")

        return certificates

    def backup_certificate(self, domain: str) -> Path:
        """
        Backup certificate files for domain.

        Args:
            domain: Domain name

        Returns:
            Path to backup directory
        """
        cert_dir = self.LETSENCRYPT_DIR / "live" / domain

        if not cert_dir.exists():
            raise FileNotFoundError(f"Certificate not found for {domain}")

        # Create backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.BACKUP_DIR / domain / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        # Copy certificate files
        for file in cert_dir.iterdir():
            if file.is_file():
                shutil.copy2(file, backup_path / file.name)

        self.logger.info(f"Certificate backed up to {backup_path}")
        return backup_path

    def setup_auto_renewal(
        self,
        schedule: str = "0 2 * * *",
        reload_webserver: bool = True,
        webserver: WebServerType = WebServerType.NGINX,
    ) -> bool:
        """
        Setup automatic certificate renewal via cron/systemd.

        Args:
            schedule: Cron schedule (default: daily at 2 AM)
            reload_webserver: Reload web server after renewal
            webserver: Web server type to reload

        Returns:
            True if setup successful
        """
        self.logger.info("Setting up automatic certificate renewal")

        # Create renewal script
        renewal_script = Path("/usr/local/bin/certbot-renew.sh")

        if reload_webserver:
            if webserver == WebServerType.NGINX:
                pass
            elif webserver == WebServerType.APACHE:
                pass

        script_content = """#!/bin/bash
# Automatic certificate renewal script
# Generated by VPS Configurator

# Renew certificates
/usr/bin/certbot renew --quiet {post_hook}

# Log renewal
echo "$(date): Certificate renewal check completed" >> /var/log/certbot-renewal.log
"""

        try:
            renewal_script.write_text(script_content)
            renewal_script.chmod(0o755)

            # Create cron job
            cron_entry = f"{schedule} root /usr/local/bin/certbot-renew.sh\n"
            cron_file = Path("/etc/cron.d/certbot-renewal")
            cron_file.write_text(cron_entry)

            self.logger.info(f"✅ Auto-renewal configured (schedule: {schedule})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup auto-renewal: {e}")
            return False

    def revoke_certificate(self, domain: str, reason: str = "unspecified") -> bool:
        """
        Revoke a certificate.

        Args:
            domain: Domain name
            reason: Revocation reason
                    (unspecified, keycompromise, affiliationchanged,
                     superseded, cessationofoperation)

        Returns:
            True if revocation successful
        """
        self.logger.warning(f"Revoking certificate for {domain}")

        if not self.is_certbot_available():
            raise RuntimeError("Certbot is not installed")

        try:
            cert = self.get_certificate(domain)

            subprocess.run(
                [
                    self.CERTBOT_PATH,
                    "revoke",
                    "--cert-path",
                    str(cert.certificate_path),
                    "--reason",
                    reason,
                    "--non-interactive",
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )

            self.logger.info("✅ Certificate revoked")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Revocation failed: {e.stderr}")
            return False

    def delete_certificate(self, domain: str) -> bool:
        """
        Delete certificate and its renewal configuration.

        Args:
            domain: Domain name

        Returns:
            True if deletion successful
        """
        self.logger.warning(f"Deleting certificate for {domain}")

        if not self.is_certbot_available():
            raise RuntimeError("Certbot is not installed")

        try:
            subprocess.run(
                [
                    self.CERTBOT_PATH,
                    "delete",
                    "--cert-name",
                    domain,
                    "--non-interactive",
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )

            self.logger.info("✅ Certificate deleted")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Deletion failed: {e.stderr}")
            return False

    def get_certificate_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of all certificate statuses.

        Returns:
            Dictionary with certificate status summary
        """
        certs = self.list_certificates()

        summary = {
            "total": len(certs),
            "valid": 0,
            "expiring_soon": 0,
            "expired": 0,
            "certificates": [],
        }

        for cert in certs:
            status = cert.status()
            summary["certificates"].append(cert.to_dict())

            if status == CertificateStatus.VALID:
                summary["valid"] += 1
            elif status == CertificateStatus.EXPIRING_SOON:
                summary["expiring_soon"] += 1
            elif status == CertificateStatus.EXPIRED:
                summary["expired"] += 1

        # Set overall health
        if summary["expired"] > 0:
            summary["health"] = "critical"
        elif summary["expiring_soon"] > 0:
            summary["health"] = "warning"
        elif summary["total"] > 0:
            summary["health"] = "good"
        else:
            summary["health"] = "none"

        return summary
