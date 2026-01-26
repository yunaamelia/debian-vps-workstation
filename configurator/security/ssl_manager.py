"""
SSL/TLS Certificate Manager

Automates SSL/TLS certificate management using:
- Let's Encrypt (via certbot)
- Self-signed certificates (for development/internal use)

Features:
- Automatic certificate issuance
- Auto-renewal
- Certificate validation
- Web server integration (Nginx/Apache)
"""

import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class Certificate:
    """Represents an SSL certificate."""

    domain: str
    path: str
    expires: datetime
    issuer: str
    valid: bool


class SSLManager:
    """
    SSL/TLS Certificate Manager.

    Manages certificate lifecycle using Let's Encrypt or self-signed certs.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize SSL manager.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # SSL configuration
        self.enabled = config.get("security_advanced.ssl_manager.enabled", False)
        self.provider = config.get("security_advanced.ssl_manager.provider", "letsencrypt")
        self.domains = config.get("security_advanced.ssl_manager.domains", [])
        self.email = config.get("security_advanced.ssl_manager.email", "")
        self.auto_renew = config.get("security_advanced.ssl_manager.auto_renew", True)
        self.renew_days_before = config.get("security_advanced.ssl_manager.renew_days_before", 30)
        self.web_server = config.get("security_advanced.ssl_manager.web_server", "nginx")

        self.certificates: List[Certificate] = []

    def setup(self) -> bool:
        """
        Setup SSL certificate management.

        Returns:
            bool: True if setup successful
        """
        if not self.enabled:
            self.logger.info("SSL manager disabled")
            return True

        self.logger.info("Setting up SSL certificate management...")

        try:
            # Validate configuration
            if not self._validate_config():
                return False

            # Install certbot if using Let's Encrypt
            if self.provider == "letsencrypt":
                if not self._install_certbot():
                    return False

            # Request certificates for configured domains
            if self.domains:
                if not self._request_certificates():
                    return False

            # Setup auto-renewal if configured
            if self.auto_renew:
                if not self._setup_auto_renewal():
                    self.logger.warning("Failed to setup auto-renewal")

            self.logger.info("✓ SSL certificate management configured")
            return True

        except Exception as e:
            self.logger.error(f"SSL setup failed: {e}", exc_info=True)
            return False

    def _validate_config(self) -> bool:
        """Validate SSL configuration."""

        if not self.domains:
            self.logger.error("No domains configured for SSL")
            return False

        if self.provider == "letsencrypt" and not self.email:
            self.logger.error("Email required for Let's Encrypt")
            return False

        return True

    def _install_certbot(self) -> bool:
        """Install certbot (Let's Encrypt client)."""
        self.logger.info("Installing certbot...")

        try:
            # Install certbot and web server plugin
            packages = ["certbot"]

            if self.web_server == "nginx":
                packages.append("python3-certbot-nginx")
            elif self.web_server == "apache":
                packages.append("python3-certbot-apache")

            result = subprocess.run(
                ["apt-get", "install", "-y"] + packages, capture_output=True, text=True
            )

            if result.returncode != 0:
                self.logger.error(f"Certbot installation failed: {result.stderr}")
                return False

            # Verify installation
            result = subprocess.run(["certbot", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ Certbot installed: {result.stdout.strip()}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Certbot installation error: {e}", exc_info=True)
            return False

    def _request_certificates(self) -> bool:
        """Request SSL certificates for configured domains."""
        self.logger.info(f"Requesting certificates for {len(self.domains)} domain(s)...")

        try:
            if self.provider == "letsencrypt":
                return self._request_letsencrypt_certificates()
            elif self.provider == "selfsigned":
                return self._generate_selfsigned_certificates()
            else:
                self.logger.error(f"Unknown SSL provider: {self.provider}")
                return False

        except Exception as e:
            self.logger.error(f"Certificate request failed: {e}", exc_info=True)
            return False

    def _request_letsencrypt_certificates(self) -> bool:
        """Request certificates from Let's Encrypt."""

        try:
            # Build certbot command
            cmd = [
                "certbot",
                "certonly",
                "--non-interactive",
                "--agree-tos",
                "--email",
                self.email,
            ]

            # Add web server plugin
            if self.web_server == "nginx":
                cmd.extend(["--nginx"])
            elif self.web_server == "apache":
                cmd.extend(["--apache"])
            else:
                cmd.extend(["--standalone"])

            # Add domains
            for domain in self.domains:
                cmd.extend(["-d", domain])

            # Run certbot
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                self.logger.error(f"Certbot failed: {result.stderr}")
                return False

            self.logger.info("✓ Let's Encrypt certificates obtained")

            # Load certificate information
            self._load_certificates()

            return True

        except subprocess.TimeoutExpired:
            self.logger.error("Certbot request timed out")
            return False
        except Exception as e:
            self.logger.error(f"Let's Encrypt request error: {e}", exc_info=True)
            return False

    def _generate_selfsigned_certificates(self) -> bool:
        """Generate self-signed certificates."""
        self.logger.info("Generating self-signed certificates...")

        try:
            cert_dir = "/etc/ssl/selfsigned"
            os.makedirs(cert_dir, mode=0o755, exist_ok=True)

            for domain in self.domains:
                key_path = f"{cert_dir}/{domain}.key"
                cert_path = f"{cert_dir}/{domain}.crt"

                # Generate private key and certificate
                cmd = [
                    "openssl",
                    "req",
                    "-x509",
                    "-nodes",
                    "-days",
                    "365",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    key_path,
                    "-out",
                    cert_path,
                    "-subj",
                    f"/CN={domain}/O=Self-Signed/C=US",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    self.logger.info(f"✓ Self-signed certificate generated for {domain}")

                    # Set secure permissions
                    os.chmod(key_path, 0o600)
                    os.chmod(cert_path, 0o644)
                else:
                    self.logger.error(
                        f"Failed to generate certificate for {domain}: {result.stderr}"
                    )

            return True

        except Exception as e:
            self.logger.error(f"Self-signed certificate generation error: {e}", exc_info=True)
            return False

    def _setup_auto_renewal(self) -> bool:
        """Setup automatic certificate renewal."""
        self.logger.info("Setting up automatic certificate renewal...")

        try:
            if self.provider == "letsencrypt":
                # Certbot installs a systemd timer for auto-renewal
                # Verify it's enabled
                result = subprocess.run(
                    ["systemctl", "is-enabled", "certbot.timer"], capture_output=True, text=True
                )

                if result.returncode != 0:
                    # Enable the timer
                    subprocess.run(["systemctl", "enable", "certbot.timer"])
                    subprocess.run(["systemctl", "start", "certbot.timer"])
                    self.logger.info("✓ Certbot auto-renewal timer enabled")
                else:
                    self.logger.info("✓ Certbot auto-renewal already configured")

                return True

            elif self.provider == "selfsigned":
                # Self-signed certs don't expire soon, but we can setup monitoring
                self.logger.info("Self-signed certificates don't require auto-renewal")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Auto-renewal setup error: {e}", exc_info=True)
            return False

    def _load_certificates(self) -> None:
        """Load information about installed certificates."""

        try:
            if self.provider == "letsencrypt":
                cert_base = "/etc/letsencrypt/live"

                for domain in self.domains:
                    cert_path = f"{cert_base}/{domain}/fullchain.pem"

                    if os.path.exists(cert_path):
                        # Get certificate expiration
                        cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"]

                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode == 0:
                            # Parse expiration date
                            # Output: notAfter=Jan  1 00:00:00 2025 GMT
                            expires_str = result.stdout.split("=")[1].strip()
                            expires = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z")

                            cert = Certificate(
                                domain=domain,
                                path=cert_path,
                                expires=expires,
                                issuer="Let's Encrypt",
                                valid=expires > datetime.now(),
                            )

                            self.certificates.append(cert)
                            self.logger.debug(f"Loaded certificate for {domain}, expires {expires}")

        except Exception as e:
            self.logger.error(f"Error loading certificates: {e}", exc_info=True)

    def check_renewal_needed(self) -> List[str]:
        """
        Check if any certificates need renewal.

        Returns:
            list: Domains that need renewal
        """
        needs_renewal = []

        try:
            self._load_certificates()

            threshold = datetime.now() + timedelta(days=self.renew_days_before)

            for cert in self.certificates:
                if cert.expires < threshold:
                    needs_renewal.append(cert.domain)
                    self.logger.warning(
                        f"Certificate for {cert.domain} expires soon: {cert.expires}"
                    )

        except Exception as e:
            self.logger.error(f"Error checking renewal: {e}", exc_info=True)

        return needs_renewal

    def renew_certificates(self, domains: Optional[List[str]] = None) -> bool:
        """
        Manually renew certificates.

        Args:
            domains: Specific domains to renew, or None for all

        Returns:
            bool: True if renewal successful
        """
        self.logger.info("Renewing certificates...")

        try:
            if self.provider == "letsencrypt":
                cmd = ["certbot", "renew", "--quiet"]

                if domains:
                    # Renew specific domains
                    cmd.extend(["--cert-name", domains[0]])  # Simplified

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    self.logger.info("✓ Certificates renewed successfully")
                    return True
                else:
                    self.logger.error(f"Certificate renewal failed: {result.stderr}")
                    return False

            return False

        except Exception as e:
            self.logger.error(f"Certificate renewal error: {e}", exc_info=True)
            return False

    def get_certificate_info(self, domain: str) -> Optional[Certificate]:
        """
        Get information about a specific certificate.

        Args:
            domain: Domain name

        Returns:
            Certificate object or None
        """
        for cert in self.certificates:
            if cert.domain == domain:
                return cert

        return None
