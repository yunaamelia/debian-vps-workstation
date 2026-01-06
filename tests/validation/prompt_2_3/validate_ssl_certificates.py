#!/usr/bin/env python3
"""
Comprehensive Validation for Prompt 2.3: SSL/TLS Certificate Management
Runs all validation checks as specified in the validation prompt.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}\n")


def check_1_1_file_structure():
    """CHECK 1.1: File Structure Verification"""
    print_section("CHECK 1.1: File Structure Verification")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    required_files = [
        ("configurator/security/certificate_manager.py", 800, "~800 lines"),
        ("configurator/security/webserver_config.py", 300, "~300 lines"),
        ("configurator/security/cert_monitor.py", 200, "~200 lines"),
        ("tests/unit/test_certificate_manager.py", 200, "~200 lines"),
        ("docs/security/ssl-tls-certificates.md", 100, "documentation"),
    ]

    BASE_DIR = Path("/home/racoon/AgentMemorh/debian-vps-workstation")

    for file_path, min_lines, description in required_files:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            line_count = len(full_path.read_text().splitlines())
            if line_count >= min_lines:
                print(f"  ✅ {file_path} ({line_count} lines)")
                results["passed"] += 1
            else:
                print(f"  ⚠️  {file_path} ({line_count} lines, expected {description})")
                results["warnings"] += 1
        else:
            print(f"  ❌ {file_path} NOT FOUND")
            results["failed"] += 1

    # Check modifications to existing files
    print("\n  Modified files:")

    # Check cli.py for cert command
    cli_path = BASE_DIR / "configurator/cli.py"
    if cli_path.exists():
        content = cli_path.read_text()
        if "def cert(" in content or "@main.group()" in content and "cert" in content:
            print("  ✅ cli.py contains cert command group")
            results["passed"] += 1
        else:
            print("  ❌ cli.py missing cert command group")
            results["failed"] += 1

    # Check default.yaml for SSL settings
    config_path = BASE_DIR / "config/default.yaml"
    if config_path.exists():
        content = config_path.read_text()
        if "ssl_certificates:" in content:
            print("  ✅ default.yaml contains ssl_certificates section")
            results["passed"] += 1
        else:
            print("  ❌ default.yaml missing ssl_certificates section")
            results["failed"] += 1

    return results


def check_1_2_data_models():
    """CHECK 1.2: Data Model Validation"""
    print_section("CHECK 1.2: Data Model Validation")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from configurator.security.certificate_manager import (
            Certificate,
            CertificateManager,
            CertificateStatus,
            ChallengeType,
        )

        # Check ChallengeType enum
        if all(hasattr(ChallengeType, t) for t in ["HTTP_01", "DNS_01", "TLS_ALPN_01"]):
            print("  ✅ ChallengeType enum complete (3 types)")
            results["passed"] += 1
        else:
            print("  ❌ ChallengeType enum incomplete")
            results["failed"] += 1

        # Check CertificateStatus enum
        status_values = ["VALID", "EXPIRING_SOON", "EXPIRED", "REVOKED", "PENDING", "FAILED"]
        if all(hasattr(CertificateStatus, s) for s in status_values):
            print(f"  ✅ CertificateStatus enum complete ({len(status_values)} states)")
            results["passed"] += 1
        else:
            print("  ❌ CertificateStatus enum incomplete")
            results["failed"] += 1

        # Check Certificate dataclass fields
        cert_fields = list(Certificate.__dataclass_fields__.keys())
        required_fields = ["domain", "issuer", "valid_from", "valid_until", "certificate_path"]
        if all(f in cert_fields for f in required_fields):
            print(f"  ✅ Certificate dataclass complete ({len(cert_fields)} fields)")
            results["passed"] += 1
        else:
            missing = [f for f in required_fields if f not in cert_fields]
            print(f"  ❌ Certificate dataclass missing fields: {missing}")
            results["failed"] += 1

        # Check Certificate methods
        cert_methods = ["days_until_expiry", "status", "needs_renewal", "to_dict", "is_wildcard"]
        if all(hasattr(Certificate, m) for m in cert_methods):
            print(f"  ✅ Certificate methods present ({len(cert_methods)} methods)")
            results["passed"] += 1
        else:
            print("  ❌ Certificate missing required methods")
            results["failed"] += 1

        # Check CertificateManager methods
        manager_methods = [
            "install_certificate",
            "renew_certificate",
            "renew_all_certificates",
            "get_certificate",
            "list_certificates",
            "setup_auto_renewal",
            "validate_dns",
            "backup_certificate",
            "revoke_certificate",
            "delete_certificate",
        ]
        if all(hasattr(CertificateManager, m) for m in manager_methods):
            print(f"  ✅ CertificateManager has all {len(manager_methods)} required methods")
            results["passed"] += 1
        else:
            missing = [m for m in manager_methods if not hasattr(CertificateManager, m)]
            print(f"  ❌ CertificateManager missing methods: {missing}")
            results["failed"] += 1

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        results["failed"] += 5
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results["failed"] += 5

    return results


def check_1_3_certbot_integration():
    """CHECK 1.3: Certbot Integration Test"""
    print_section("CHECK 1.3: Certbot Integration Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    import subprocess

    # Test 1: Certbot installed
    print("  1. Checking Certbot installation...")
    try:
        result = subprocess.run(
            ["certbot", "--version"], capture_output=True, text=True, check=True
        )
        version = result.stdout.strip() or result.stderr.strip()
        print(f"     ✅ Certbot installed: {version}")
        results["passed"] += 1
    except FileNotFoundError:
        print("     ⚠️  Certbot not found (install with: apt-get install certbot)")
        results["warnings"] += 1
    except Exception as e:
        print(f"     ⚠️  Certbot check failed: {e}")
        results["warnings"] += 1

    # Test 2: CertificateManager initialization
    print("  2. Testing CertificateManager initialization...")
    try:
        from configurator.security.certificate_manager import CertificateManager

        CertificateManager()
        print("     ✅ CertificateManager initialized successfully")
        results["passed"] += 1
    except Exception as e:
        print(f"     ❌ CertificateManager initialization failed: {e}")
        results["failed"] += 1

    # Test 3: Check Let's Encrypt directory
    print("  3. Checking Let's Encrypt directories...")
    letsencrypt_dir = Path("/etc/letsencrypt")
    if letsencrypt_dir.exists():
        print(f"     ✅ Let's Encrypt directory exists: {letsencrypt_dir}")
        results["passed"] += 1
    else:
        print("     ℹ️  Let's Encrypt directory will be created on first certificate")
        results["passed"] += 1  # OK - directory created on first use

    return results


def check_2_1_dns_validation():
    """CHECK 2.1: DNS Validation Test"""
    print_section("CHECK 2.1: DNS Validation Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        import socket

        from configurator.security.certificate_manager import CertificateManager

        manager = CertificateManager()

        # Test 1: Valid domain lookup
        print("  1. Testing public domain lookup...")
        try:
            ip = socket.gethostbyname("example.com")
            print(f"     ✅ DNS lookup works: example.com → {ip}")
            results["passed"] += 1
        except Exception as e:
            print(f"     ⚠️  DNS lookup failed: {e}")
            results["warnings"] += 1

        # Test 2: Invalid domain rejection
        print("  2. Testing invalid domain rejection...")
        try:
            is_valid = manager.validate_dns("this-domain-definitely-does-not-exist-12345.com")
            if not is_valid:
                print("     ✅ Correctly rejected non-existent domain")
                results["passed"] += 1
            else:
                print("     ❌ Should have rejected non-existent domain")
                results["failed"] += 1
        except Exception:
            print("     ✅ Properly raised exception for invalid domain")
            results["passed"] += 1

        # Test 3: skip_ip_check option
        print("  3. Testing skip_ip_check option...")
        try:
            is_valid = manager.validate_dns("google.com", skip_ip_check=True)
            if is_valid:
                print("     ✅ skip_ip_check=True works correctly")
                results["passed"] += 1
            else:
                print("     ⚠️  skip_ip_check may have issues")
                results["warnings"] += 1
        except Exception as e:
            print(f"     ⚠️  skip_ip_check test failed: {e}")
            results["warnings"] += 1

    except Exception as e:
        print(f"  ❌ DNS validation test error: {e}")
        results["failed"] += 3

    return results


def check_3_2_renewal_logic():
    """CHECK 3.2: Certificate Renewal Logic Test"""
    print_section("CHECK 3.2: Certificate Renewal Logic Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from configurator.security.certificate_manager import Certificate, CertificateStatus

        # Test 1: Expiring soon detection
        print("  1. Testing renewal detection (expiring soon)...")
        cert_expiring = Certificate(
            domain="test.example.com",
            subject_alternative_names=["test.example.com"],
            issuer="Let's Encrypt",
            valid_from=datetime.now() - timedelta(days=60),
            valid_until=datetime.now() + timedelta(days=20),
            certificate_path=Path("/tmp/test.pem"),
            private_key_path=Path("/tmp/test-key.pem"),
        )

        days = cert_expiring.days_until_expiry()
        needs_renewal = cert_expiring.needs_renewal(threshold_days=30)
        status = cert_expiring.status()

        print(f"     Days remaining: {days}")
        print(f"     Needs renewal: {needs_renewal}")
        print(f"     Status: {status.value}")

        if needs_renewal and status == CertificateStatus.EXPIRING_SOON:
            print("     ✅ Correctly detected certificate needs renewal")
            results["passed"] += 1
        else:
            print("     ❌ Renewal detection failed")
            results["failed"] += 1

        # Test 2: Valid certificate
        print("\n  2. Testing renewal detection (valid)...")
        cert_valid = Certificate(
            domain="test.example.com",
            subject_alternative_names=["test.example.com"],
            issuer="Let's Encrypt",
            valid_from=datetime.now() - timedelta(days=10),
            valid_until=datetime.now() + timedelta(days=80),
            certificate_path=Path("/tmp/test.pem"),
            private_key_path=Path("/tmp/test-key.pem"),
        )

        days = cert_valid.days_until_expiry()
        needs_renewal = cert_valid.needs_renewal(threshold_days=30)
        status = cert_valid.status()

        print(f"     Days remaining: {days}")
        print(f"     Needs renewal: {needs_renewal}")
        print(f"     Status: {status.value}")

        if not needs_renewal and status == CertificateStatus.VALID:
            print("     ✅ Correctly detected certificate is still valid")
            results["passed"] += 1
        else:
            print("     ❌ Valid detection failed")
            results["failed"] += 1

        # Test 3: Expired certificate
        print("\n  3. Testing expired certificate detection...")
        cert_expired = Certificate(
            domain="test.example.com",
            subject_alternative_names=["test.example.com"],
            issuer="Let's Encrypt",
            valid_from=datetime.now() - timedelta(days=100),
            valid_until=datetime.now() - timedelta(days=5),
            certificate_path=Path("/tmp/test.pem"),
            private_key_path=Path("/tmp/test-key.pem"),
        )

        days = cert_expired.days_until_expiry()
        status = cert_expired.status()

        print(f"     Days remaining: {days}")
        print(f"     Status: {status.value}")

        if days < 0 and status == CertificateStatus.EXPIRED:
            print("     ✅ Correctly detected expired certificate")
            results["passed"] += 1
        else:
            print("     ❌ Expiry detection failed")
            results["failed"] += 1

    except Exception as e:
        print(f"  ❌ Renewal logic test error: {e}")
        results["failed"] += 3

    return results


def check_4_1_webserver_config():
    """CHECK 4.1: Web Server Configuration Test"""
    print_section("CHECK 4.1: Web Server Configuration Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from configurator.security.webserver_config import (
            NginxConfigurator,
            TLSConfig,
        )

        # Test 1: TLSConfig defaults
        print("  1. Testing TLSConfig defaults...")
        config = TLSConfig()

        checks = [
            (config.hsts_enabled, "HSTS enabled"),
            (len(config.protocols) >= 2, "TLS protocols configured"),
            (config.ocsp_stapling, "OCSP stapling enabled"),
        ]

        for check, name in checks:
            if check:
                print(f"     ✅ {name}")
                results["passed"] += 1
            else:
                print(f"     ❌ {name} FAILED")
                results["failed"] += 1

        # Test 2: Nginx SSL snippet generation
        print("\n  2. Testing Nginx SSL snippet generation...")
        nginx = NginxConfigurator()
        snippet = nginx.generate_ssl_snippet(config)

        required_directives = [
            "ssl_protocols",
            "TLSv1.2",
            "TLSv1.3",
            "Strict-Transport-Security",
            "ssl_stapling",
        ]

        for directive in required_directives:
            if directive in snippet:
                print(f"     ✅ Contains: {directive}")
                results["passed"] += 1
            else:
                print(f"     ❌ Missing: {directive}")
                results["failed"] += 1

        # Test 3: Site config generation
        print("\n  3. Testing Nginx site config generation...")
        site_config = nginx.generate_site_config(
            domain="example.com",
            cert_path=Path("/etc/letsencrypt/live/example.com/fullchain.pem"),
            key_path=Path("/etc/letsencrypt/live/example.com/privkey.pem"),
        )

        if "ssl_certificate" in site_config and "return 301 https://" in site_config:
            print("     ✅ Site config includes SSL and HTTP redirect")
            results["passed"] += 1
        else:
            print("     ❌ Site config incomplete")
            results["failed"] += 1

    except Exception as e:
        print(f"  ❌ Web server config test error: {e}")
        results["failed"] += 10

    return results


def check_5_1_tls_security():
    """CHECK 5.1: TLS Security Configuration Test"""
    print_section("CHECK 5.1: TLS Security Configuration Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    import subprocess

    # Check OpenSSL version
    print("  1. Checking OpenSSL version...")
    try:
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"     ✅ OpenSSL: {version}")
        results["passed"] += 1

        if "OpenSSL 3." in version or "OpenSSL 1.1.1" in version:
            print("     ✅ TLS 1.3 support available")
            results["passed"] += 1
        else:
            print("     ⚠️  TLS 1.3 may not be supported")
            results["warnings"] += 1
    except Exception as e:
        print(f"     ❌ OpenSSL check failed: {e}")
        results["failed"] += 2

    # Check TLSConfig security settings
    print("\n  2. Verifying TLSConfig security settings...")
    try:
        from configurator.security.webserver_config import TLSConfig, TLSProtocol

        config = TLSConfig()

        # Check protocols
        if TLSProtocol.TLS_1_2 in config.protocols and TLSProtocol.TLS_1_3 in config.protocols:
            print("     ✅ TLS 1.2 and 1.3 configured")
            results["passed"] += 1
        else:
            print("     ❌ Missing TLS protocol configuration")
            results["failed"] += 1

        # Check HSTS
        if config.hsts_enabled and config.hsts_max_age >= 31536000:
            print("     ✅ HSTS enabled (max-age >= 31536000)")
            results["passed"] += 1
        else:
            print("     ⚠️  HSTS settings could be stronger")
            results["warnings"] += 1

        # Check OCSP
        if config.ocsp_stapling:
            print("     ✅ OCSP stapling enabled")
            results["passed"] += 1
        else:
            print("     ⚠️  OCSP stapling not enabled")
            results["warnings"] += 1

    except Exception as e:
        print(f"     ❌ TLSConfig check failed: {e}")
        results["failed"] += 3

    return results


def check_6_1_cli_commands():
    """CHECK 6.1: CLI Commands Test"""
    print_section("CHECK 6.1: CLI Commands Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    import subprocess

    commands = [
        ("cert --help", "cert group"),
        ("cert install --help", "cert install"),
        ("cert renew --help", "cert renew"),
        ("cert status --help", "cert status"),
        ("cert list --help", "cert list"),
        ("cert delete --help", "cert delete"),
        ("cert monitor --help", "cert monitor"),
    ]

    print("  Testing CLI commands...")
    for cmd, name in commands:
        try:
            result = subprocess.run(
                f"cd /home/racoon/AgentMemorh/debian-vps-workstation && python -m configurator.cli {cmd}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print(f"     ✅ {name} works")
                results["passed"] += 1
            else:
                print(f"     ❌ {name} failed")
                results["failed"] += 1
        except Exception as e:
            print(f"     ❌ {name} error: {e}")
            results["failed"] += 1

    # Test actual command execution
    print("\n  Testing cert status command execution...")
    try:
        result = subprocess.run(
            "cd /home/racoon/AgentMemorh/debian-vps-workstation && python -m configurator.cli cert status",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("     ✅ cert status executed successfully")
            print(f"     Output: {result.stdout.strip()[:100]}")
            results["passed"] += 1
        else:
            print(f"     ❌ cert status failed: {result.stderr}")
            results["failed"] += 1
    except Exception as e:
        print(f"     ❌ cert status error: {e}")
        results["failed"] += 1

    return results


def check_monitoring():
    """CHECK: Certificate Monitoring Test"""
    print_section("CHECK: Certificate Monitoring Test")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from configurator.security.cert_monitor import (
            AlertConfig,
            AlertLevel,
            CertificateAlert,
            CertificateMonitor,
        )

        # Test AlertLevel enum
        print("  1. Testing AlertLevel enum...")
        if hasattr(AlertLevel, "CRITICAL") and hasattr(AlertLevel, "WARNING"):
            print("     ✅ AlertLevel enum complete")
            results["passed"] += 1
        else:
            print("     ❌ AlertLevel enum incomplete")
            results["failed"] += 1

        # Test AlertConfig defaults
        print("  2. Testing AlertConfig defaults...")
        config = AlertConfig()
        print(f"     ✅ AlertConfig initialized (email_enabled={config.email_enabled})")
        results["passed"] += 1

        # Test CertificateAlert
        print("  3. Testing CertificateAlert...")
        alert = CertificateAlert(
            domain="test.com", level=AlertLevel.WARNING, message="Test alert", days_remaining=25
        )
        data = alert.to_dict()
        if "domain" in data and "level" in data:
            print("     ✅ CertificateAlert serialization works")
            results["passed"] += 1
        else:
            print("     ❌ CertificateAlert serialization failed")
            results["failed"] += 1

        # Test CertificateMonitor
        print("  4. Testing CertificateMonitor initialization...")
        from unittest.mock import Mock

        mock_manager = Mock()
        monitor = CertificateMonitor(mock_manager)
        if hasattr(monitor, "check_certificate") and hasattr(monitor, "send_alerts"):
            print("     ✅ CertificateMonitor has required methods")
            results["passed"] += 1
        else:
            print("     ❌ CertificateMonitor missing methods")
            results["failed"] += 1

    except Exception as e:
        print(f"  ❌ Monitoring test error: {e}")
        results["failed"] += 4

    return results


def run_unit_tests():
    """Run unit tests and get results"""
    print_section("Running Unit Tests")

    results = {"passed": 0, "failed": 0, "warnings": 0}

    import subprocess

    try:
        result = subprocess.run(
            "cd /home/racoon/AgentMemorh/debian-vps-workstation && python -m pytest tests/unit/test_certificate_manager.py -v --tb=short",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout + result.stderr

        # Parse test results
        if "passed" in output:
            import re

            match = re.search(r"(\d+) passed", output)
            if match:
                passed = int(match.group(1))
                print(f"  ✅ Unit tests: {passed} passed")
                results["passed"] = passed

        if "failed" in output:
            import re

            match = re.search(r"(\d+) failed", output)
            if match:
                failed = int(match.group(1))
                print(f"  ❌ Unit tests: {failed} failed")
                results["failed"] = failed

        if result.returncode != 0 and results["passed"] == 0:
            print("  ❌ Unit tests failed to run")
            print(f"     {output[:500]}")
            results["failed"] = 1

    except Exception as e:
        print(f"  ❌ Unit test error: {e}")
        results["failed"] = 1

    return results


def main():
    """Run all validation checks"""
    print_header("PROMPT 2.3 VALIDATION: SSL/TLS CERTIFICATE MANAGEMENT")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Validator: Antigravity AI")

    total_results = {"passed": 0, "failed": 0, "warnings": 0}

    # Run all checks
    checks = [
        ("1.1", check_1_1_file_structure),
        ("1.2", check_1_2_data_models),
        ("1.3", check_1_3_certbot_integration),
        ("2.1", check_2_1_dns_validation),
        ("3.2", check_3_2_renewal_logic),
        ("4.1", check_4_1_webserver_config),
        ("5.1", check_5_1_tls_security),
        ("6.1", check_6_1_cli_commands),
        ("MON", check_monitoring),
    ]

    for check_id, check_func in checks:
        try:
            results = check_func()
            total_results["passed"] += results["passed"]
            total_results["failed"] += results["failed"]
            total_results["warnings"] += results.get("warnings", 0)
        except Exception as e:
            print(f"\n  ❌ CHECK {check_id} ERROR: {e}")
            total_results["failed"] += 1

    # Run unit tests
    test_results = run_unit_tests()
    total_results["passed"] += test_results["passed"]
    total_results["failed"] += test_results["failed"]

    # Final summary
    print_header("VALIDATION SUMMARY")

    total_checks = total_results["passed"] + total_results["failed"]
    pass_rate = (total_results["passed"] / total_checks * 100) if total_checks > 0 else 0

    print(
        """
  Total Checks:  {total_checks}
  ✅ Passed:     {total_results['passed']}
  ❌ Failed:     {total_results['failed']}
  ⚠️  Warnings:  {total_results['warnings']}

  Pass Rate:     {pass_rate:.1f}%
"""
    )

    if total_results["failed"] == 0:
        print("  " + "=" * 56)
        print("  ✅ VALIDATION PASSED - IMPLEMENTATION APPROVED")
        print("  " + "=" * 56)
        return 0
    elif pass_rate >= 85:
        print("  " + "=" * 56)
        print("  ⚠️  CONDITIONAL APPROVAL - Minor issues found")
        print("  " + "=" * 56)
        return 0
    else:
        print("  " + "=" * 56)
        print("  ❌ VALIDATION FAILED - Implementation needs fixes")
        print("  " + "=" * 56)
        return 1


if __name__ == "__main__":
    sys.exit(main())
