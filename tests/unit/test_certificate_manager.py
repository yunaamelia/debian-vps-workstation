"""
Unit tests for SSL/TLS Certificate Manager.

Tests data models, certificate parsing, and manager functionality.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.security.certificate_manager import (
    Certificate,
    CertificateManager,
    CertificateStatus,
    ChallengeType,
    WebServerType,
)


class TestCertificate:
    """Tests for Certificate dataclass."""

    def test_certificate_creation(self):
        """Test creating a Certificate object."""
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com", "www.example.com"],
            issuer="Let's Encrypt Authority X3",
            valid_from=datetime(2026, 1, 6),
            valid_until=datetime(2026, 4, 6),
            certificate_path=Path("/etc/letsencrypt/live/example.com/fullchain.pem"),
            private_key_path=Path("/etc/letsencrypt/live/example.com/privkey.pem"),
        )

        assert cert.domain == "example.com"
        assert len(cert.subject_alternative_names) == 2
        assert cert.issuer == "Let's Encrypt Authority X3"

    def test_days_until_expiry(self):
        """Test days_until_expiry calculation."""
        # Certificate expiring in 30 days
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=60),
            valid_until=datetime.now() + timedelta(days=30),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        days = cert.days_until_expiry()
        assert 29 <= days <= 31  # Allow for timing variance

    def test_status_valid(self):
        """Test status for valid certificate."""
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=10),
            valid_until=datetime.now() + timedelta(days=60),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        assert cert.status() == CertificateStatus.VALID

    def test_status_expiring_soon(self):
        """Test status for certificate expiring soon."""
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=70),
            valid_until=datetime.now() + timedelta(days=15),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        assert cert.status() == CertificateStatus.EXPIRING_SOON

    def test_status_expired(self):
        """Test status for expired certificate."""
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=100),
            valid_until=datetime.now() - timedelta(days=10),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        assert cert.status() == CertificateStatus.EXPIRED

    def test_needs_renewal(self):
        """Test needs_renewal check."""
        # Certificate expiring in 20 days (needs renewal)
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=70),
            valid_until=datetime.now() + timedelta(days=20),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        assert cert.needs_renewal(threshold_days=30) is True
        assert cert.needs_renewal(threshold_days=15) is False

    def test_is_wildcard(self):
        """Test wildcard certificate detection."""
        wildcard = Certificate(
            domain="*.example.com",
            subject_alternative_names=["*.example.com"],
            issuer="Test CA",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        regular = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com"],
            issuer="Test CA",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        assert wildcard.is_wildcard() is True
        assert regular.is_wildcard() is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        cert = Certificate(
            domain="example.com",
            subject_alternative_names=["example.com", "www.example.com"],
            issuer="Let's Encrypt",
            valid_from=datetime(2026, 1, 6, 12, 0, 0),
            valid_until=datetime(2026, 4, 6, 12, 0, 0),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
            auto_renewal_enabled=True,
        )

        data = cert.to_dict()

        assert data["domain"] == "example.com"
        assert len(data["sans"]) == 2
        assert data["issuer"] == "Let's Encrypt"
        assert data["auto_renewal"] is True
        assert "days_remaining" in data
        assert "status" in data


class TestCertificateManager:
    """Tests for CertificateManager class."""

    def test_is_certbot_available(self):
        """Test Certbot availability check."""
        manager = CertificateManager()

        with patch.object(Path, "exists", return_value=True):
            manager._certbot_available = None
            assert manager.is_certbot_available() is True

        with patch.object(Path, "exists", return_value=False):
            manager._certbot_available = None
            assert manager.is_certbot_available() is False

    def test_get_certbot_version(self):
        """Test getting Certbot version."""
        manager = CertificateManager()
        manager._certbot_available = True

        mock_result = MagicMock()
        mock_result.stdout = "certbot 2.8.0"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            version = manager.get_certbot_version()
            assert version == "2.8.0"

    def test_validate_dns_success(self):
        """Test DNS validation success."""
        manager = CertificateManager()

        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            with patch.object(manager, "_get_server_ips", return_value=["192.168.1.1"]):
                assert manager.validate_dns("example.com") is True

    def test_validate_dns_failure(self):
        """Test DNS validation failure."""
        manager = CertificateManager()

        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            with patch.object(manager, "_get_server_ips", return_value=["10.0.0.1"]):
                assert manager.validate_dns("example.com") is False

    def test_validate_dns_skip_ip_check(self):
        """Test DNS validation with IP check skipped."""
        manager = CertificateManager()

        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            assert manager.validate_dns("example.com", skip_ip_check=True) is True

    def test_build_certbot_command_http(self):
        """Test building Certbot command for HTTP-01 challenge."""
        manager = CertificateManager()

        cmd = manager._build_certbot_command(
            domain="example.com",
            email="admin@example.com",
            webserver=WebServerType.NGINX,
            additional_domains=["www.example.com"],
            challenge=ChallengeType.HTTP_01,
            staging=False,
            force=False,
            dns_plugin=None,
            dns_credentials=None,
        )

        assert manager.CERTBOT_PATH in cmd
        assert "certonly" in cmd
        assert "--nginx" in cmd
        assert "-d" in cmd
        assert "example.com" in cmd
        assert "www.example.com" in cmd

    def test_build_certbot_command_dns(self):
        """Test building Certbot command for DNS-01 challenge."""
        manager = CertificateManager()

        cmd = manager._build_certbot_command(
            domain="*.example.com",
            email="admin@example.com",
            webserver=WebServerType.STANDALONE,
            additional_domains=[],
            challenge=ChallengeType.DNS_01,
            staging=True,
            force=False,
            dns_plugin="cloudflare",
            dns_credentials=Path("/etc/cloudflare.ini"),
        )

        assert "--dns-cloudflare" in cmd
        assert "--staging" in cmd

    def test_build_certbot_command_force(self):
        """Test building Certbot command with force renewal."""
        manager = CertificateManager()

        cmd = manager._build_certbot_command(
            domain="example.com",
            email="admin@example.com",
            webserver=WebServerType.NGINX,
            additional_domains=[],
            challenge=ChallengeType.HTTP_01,
            staging=False,
            force=True,
            dns_plugin=None,
            dns_credentials=None,
        )

        assert "--force-renewal" in cmd

    def test_parse_openssl_date(self):
        """Test parsing OpenSSL date format."""
        manager = CertificateManager()

        # Test standard format
        date_str = "Jan  6 14:30:00 2026 GMT"
        result = manager._parse_openssl_date(date_str)

        assert result.year == 2026
        assert result.month == 1
        assert result.day == 6

    def test_get_certificate_not_found(self):
        """Test getting certificate that doesn't exist."""
        manager = CertificateManager()

        with pytest.raises(FileNotFoundError):
            manager.get_certificate("nonexistent.com")

    def test_list_certificates_empty(self):
        """Test listing certificates when none exist."""
        manager = CertificateManager()

        with patch.object(Path, "exists", return_value=False):
            certs = manager.list_certificates()
            assert certs == []

    def test_get_certificate_status_summary_empty(self):
        """Test status summary with no certificates."""
        manager = CertificateManager()

        with patch.object(manager, "list_certificates", return_value=[]):
            summary = manager.get_certificate_status_summary()

            assert summary["total"] == 0
            assert summary["valid"] == 0
            assert summary["health"] == "none"

    def test_get_certificate_status_summary_with_certs(self):
        """Test status summary with certificates."""
        manager = CertificateManager()

        valid_cert = Certificate(
            domain="valid.com",
            subject_alternative_names=["valid.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=10),
            valid_until=datetime.now() + timedelta(days=60),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        expiring_cert = Certificate(
            domain="expiring.com",
            subject_alternative_names=["expiring.com"],
            issuer="Test CA",
            valid_from=datetime.now() - timedelta(days=70),
            valid_until=datetime.now() + timedelta(days=15),
            certificate_path=Path("/test/cert.pem"),
            private_key_path=Path("/test/key.pem"),
        )

        with patch.object(manager, "list_certificates", return_value=[valid_cert, expiring_cert]):
            summary = manager.get_certificate_status_summary()

            assert summary["total"] == 2
            assert summary["valid"] == 1
            assert summary["expiring_soon"] == 1
            assert summary["health"] == "warning"


class TestEnums:
    """Tests for enum classes."""

    def test_challenge_type_values(self):
        """Test ChallengeType enum values."""
        assert ChallengeType.HTTP_01.value == "http-01"
        assert ChallengeType.DNS_01.value == "dns-01"
        assert ChallengeType.TLS_ALPN_01.value == "tls-alpn-01"

    def test_certificate_status_values(self):
        """Test CertificateStatus enum values."""
        assert CertificateStatus.VALID.value == "valid"
        assert CertificateStatus.EXPIRING_SOON.value == "expiring_soon"
        assert CertificateStatus.EXPIRED.value == "expired"
        assert CertificateStatus.REVOKED.value == "revoked"

    def test_webserver_type_values(self):
        """Test WebServerType enum values."""
        assert WebServerType.NGINX.value == "nginx"
        assert WebServerType.APACHE.value == "apache"
        assert WebServerType.CADDY.value == "caddy"


class TestCertificateMonitor:
    """Tests for certificate monitoring."""

    def test_monitor_import(self):
        """Test that monitor module can be imported."""
        from configurator.security.cert_monitor import (
            AlertLevel,
        )

        assert AlertLevel.CRITICAL.value == "critical"
        assert AlertLevel.WARNING.value == "warning"

    def test_alert_to_dict(self):
        """Test CertificateAlert serialization."""
        from configurator.security.cert_monitor import AlertLevel, CertificateAlert

        alert = CertificateAlert(
            domain="example.com",
            level=AlertLevel.WARNING,
            message="Certificate expires in 25 days",
            days_remaining=25,
        )

        data = alert.to_dict()

        assert data["domain"] == "example.com"
        assert data["level"] == "warning"
        assert data["days_remaining"] == 25

    def test_monitor_check_certificate(self):
        """Test checking a single certificate."""
        from configurator.security.cert_monitor import AlertLevel, CertificateMonitor

        mock_manager = Mock()

        # Certificate expiring in 20 days
        mock_cert = Mock()
        mock_cert.days_until_expiry.return_value = 20
        mock_manager.get_certificate.return_value = mock_cert

        monitor = CertificateMonitor(
            certificate_manager=mock_manager,
            warning_threshold_days=30,
            critical_threshold_days=14,
        )

        alert = monitor.check_certificate("example.com")

        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert alert.days_remaining == 20


class TestWebServerConfig:
    """Tests for web server configuration."""

    def test_webserver_config_import(self):
        """Test that webserver config module can be imported."""
        from configurator.security.webserver_config import (
            TLSConfig,
        )

        config = TLSConfig()
        assert config.hsts_enabled is True
        assert len(config.protocols) == 2

    def test_nginx_ssl_snippet_generation(self):
        """Test Nginx SSL snippet generation."""
        from configurator.security.webserver_config import NginxConfigurator, TLSConfig

        configurator = NginxConfigurator()
        config = TLSConfig()

        snippet = configurator.generate_ssl_snippet(config)

        assert "ssl_protocols" in snippet
        assert "TLSv1.2" in snippet
        assert "TLSv1.3" in snippet
        assert "Strict-Transport-Security" in snippet
        assert "ssl_stapling on" in snippet

    def test_nginx_site_config_generation(self):
        """Test Nginx site configuration generation."""
        from configurator.security.webserver_config import NginxConfigurator

        configurator = NginxConfigurator()

        config = configurator.generate_site_config(
            domain="example.com",
            cert_path=Path("/etc/letsencrypt/live/example.com/fullchain.pem"),
            key_path=Path("/etc/letsencrypt/live/example.com/privkey.pem"),
            additional_domains=["www.example.com"],
        )

        assert "server_name example.com www.example.com" in config
        assert "ssl_certificate" in config
        assert "ssl_certificate_key" in config
        assert "return 301 https://" in config  # HTTP redirect


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
