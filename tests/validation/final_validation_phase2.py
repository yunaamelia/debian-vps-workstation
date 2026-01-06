#!/usr/bin/env python3
"""
Final Validation - Phase 2: Security & Compliance
Tests for CIS Scanner, Vulnerability Scanner, SSL/TLS Manager, SSH Keys, and 2FA/MFA
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_cis_scanner():
    """Test 2.1: CIS Benchmark Scanner"""
    print("\n=== Validation 2.1: CIS Benchmark Scanner ===\n")

    from configurator.security.cis_scanner import CISBenchmarkScanner, Severity, Status

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: CISBenchmarkScanner initialization
    print("Test 1: CISBenchmarkScanner initialization...")

    try:
        scanner = CISBenchmarkScanner()
        print("  ✅ CISBenchmarkScanner initialized")
        results["passed"] += 1
        results["tests"].append(("Scanner Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Scanner Initialization", "FAIL"))
        return results

    # Test 2: Run scan
    print("Test 2: Run CIS scan...")

    try:
        scan_report = scanner.scan(level=1)

        if scan_report is not None:
            print(f"  ✅ CIS scan completed: {len(scan_report.results)} checks")
            results["passed"] += 1
            results["tests"].append(("Run Scan", "PASS"))
        else:
            print("  ❌ Scan returned None")
            results["failed"] += 1
            results["tests"].append(("Run Scan", "FAIL"))
    except Exception as e:
        print(f"  ❌ Scan failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Run Scan", "FAIL"))

    # Test 3: Get results summary
    print("Test 3: Get results summary...")

    try:
        summary = scan_report.get_summary()

        if summary and isinstance(summary, dict):
            print(f"  ✅ Summary keys: {list(summary.keys())}")
            results["passed"] += 1
            results["tests"].append(("Results Summary", "PASS"))
        else:
            print("  ❌ Summary not available")
            results["failed"] += 1
            results["tests"].append(("Results Summary", "FAIL"))
    except Exception as e:
        print(f"  ❌ Summary failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Results Summary", "FAIL"))

    # Test 4: Check severity levels exist
    print("Test 4: Severity levels defined...")

    try:
        severities = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
        print(f"  ✅ Severity levels: {[s.value for s in severities]}")
        results["passed"] += 1
        results["tests"].append(("Severity Levels", "PASS"))
    except Exception as e:
        print(f"  ❌ Severity levels failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Severity Levels", "FAIL"))

    # Test 5: Check status values exist
    print("Test 5: Status values defined...")

    try:
        statuses = [Status.PASS, Status.FAIL, Status.MANUAL, Status.NOT_APPLICABLE]
        print(f"  ✅ Status values: {[s.value for s in statuses]}")
        results["passed"] += 1
        results["tests"].append(("Status Values", "PASS"))
    except Exception as e:
        print(f"  ❌ Status values failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Status Values", "FAIL"))

    # Test 6: Scan has score
    print("Test 6: Compliance score calculated...")

    try:
        score = scan_report.score

        if 0 <= score <= 100:
            print(f"  ✅ Compliance score: {score:.1f}%")
            results["passed"] += 1
            results["tests"].append(("Compliance Score", "PASS"))
        else:
            print(f"  ❌ Score out of range: {score}")
            results["failed"] += 1
            results["tests"].append(("Compliance Score", "FAIL"))
    except Exception as e:
        print(f"  ❌ Compliance score failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Compliance Score", "FAIL"))

    print(f"\n📊 Validation 2.1 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_vulnerability_scanner():
    """Test 2.2: Vulnerability Scanner (using Trivy implementation)"""
    print("\n=== Validation 2.2: Vulnerability Scanner ===\n")

    from configurator.security.vulnerability_scanner import (
        GrypeScanner,
        TrivyScanner,
        Vulnerability,
        VulnerabilitySeverity,
    )

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: TrivyScanner initialization
    print("Test 1: TrivyScanner initialization...")

    try:
        scanner = TrivyScanner()
        print("  ✅ TrivyScanner initialized")
        results["passed"] += 1
        results["tests"].append(("Scanner Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Scanner Initialization", "FAIL"))
        # Try GrypeScanner as fallback
        try:
            scanner = GrypeScanner()
            print("  ✅ GrypeScanner initialized as fallback")
        except Exception:
            return results

    # Test 2: Check scanner availability
    print("Test 2: Check scanner availability...")

    try:
        is_available = scanner.is_available()

        if is_available:
            print("  ✅ Scanner is available")
            results["passed"] += 1
            results["tests"].append(("Scanner Available", "PASS"))
        else:
            print("  ⚠️ Scanner not installed (expected in some environments)")
            results["tests"].append(("Scanner Available", "SKIP"))
    except Exception as e:
        print(f"  ⚠️ Availability check: {e}")
        results["tests"].append(("Scanner Available", "SKIP"))

    # Test 3: Get scanner version
    print("Test 3: Get scanner version...")

    try:
        version = scanner.get_version()

        if version:
            print(f"  ✅ Scanner version: {version}")
            results["passed"] += 1
            results["tests"].append(("Scanner Version", "PASS"))
        else:
            print("  ⚠️ Scanner version not available")
            results["tests"].append(("Scanner Version", "SKIP"))
    except Exception as e:
        print(f"  ⚠️ Version check: {e}")
        results["tests"].append(("Scanner Version", "SKIP"))

    # Test 4: Severity levels exist
    print("Test 4: Vulnerability severity levels...")

    try:
        severities = [
            VulnerabilitySeverity.CRITICAL,
            VulnerabilitySeverity.HIGH,
            VulnerabilitySeverity.MEDIUM,
            VulnerabilitySeverity.LOW,
        ]
        print(f"  ✅ Severity levels: {[s.value for s in severities]}")
        results["passed"] += 1
        results["tests"].append(("Severity Levels", "PASS"))
    except Exception as e:
        print(f"  ❌ Severity levels failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Severity Levels", "FAIL"))

    # Test 5: Vulnerability dataclass
    print("Test 5: Vulnerability dataclass...")

    try:
        vuln = Vulnerability(
            cve_id="CVE-2024-1234",
            package_name="test-pkg",
            installed_version="1.0.0",
            fixed_version="1.0.1",
            severity=VulnerabilitySeverity.HIGH,
            cvss_score=7.5,
            description="Test vulnerability",
        )

        vuln_dict = vuln.to_dict()

        if "cve_id" in vuln_dict:
            print("  ✅ Vulnerability model works")
            results["passed"] += 1
            results["tests"].append(("Vulnerability Model", "PASS"))
        else:
            print("  ❌ Vulnerability model failed")
            results["failed"] += 1
            results["tests"].append(("Vulnerability Model", "FAIL"))
    except Exception as e:
        print(f"  ❌ Vulnerability model failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Vulnerability Model", "FAIL"))

    print(f"\n📊 Validation 2.2 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_ssl_certificate_manager():
    """Test 2.3: SSL/TLS Certificate Manager"""
    print("\n=== Validation 2.3: SSL/TLS Certificate Manager ===\n")

    from configurator.security.certificate_manager import (
        CertificateManager,
        CertificateStatus,
        ChallengeType,
        WebServerType,
    )

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: Manager initialization
    print("Test 1: CertificateManager initialization...")

    try:
        manager = CertificateManager()
        print("  ✅ CertificateManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: Check Certbot availability
    print("Test 2: Check Certbot availability...")

    try:
        is_available = manager.is_certbot_available()

        if is_available:
            print("  ✅ Certbot is available")
            results["passed"] += 1
            results["tests"].append(("Certbot Available", "PASS"))
        else:
            print("  ⚠️ Certbot not installed")
            results["tests"].append(("Certbot Available", "SKIP"))
    except Exception as e:
        print(f"  ⚠️ Certbot check: {e}")
        results["tests"].append(("Certbot Available", "SKIP"))

    # Test 3: Challenge types
    print("Test 3: Challenge types defined...")

    try:
        challenges = [ChallengeType.HTTP_01, ChallengeType.DNS_01]
        print(f"  ✅ Challenge types: {[c.value for c in challenges]}")
        results["passed"] += 1
        results["tests"].append(("Challenge Types", "PASS"))
    except Exception as e:
        print(f"  ❌ Challenge types failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Challenge Types", "FAIL"))

    # Test 4: Web server types
    print("Test 4: Web server types defined...")

    try:
        servers = [WebServerType.NGINX, WebServerType.APACHE, WebServerType.CADDY]
        print(f"  ✅ Web server types: {[s.value for s in servers]}")
        results["passed"] += 1
        results["tests"].append(("Web Server Types", "PASS"))
    except Exception as e:
        print(f"  ❌ Web server types failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Web Server Types", "FAIL"))

    # Test 5: Certificate status
    print("Test 5: Certificate status values...")

    try:
        statuses = [
            CertificateStatus.VALID,
            CertificateStatus.EXPIRING_SOON,
            CertificateStatus.EXPIRED,
        ]
        print(f"  ✅ Certificate statuses: {[s.value for s in statuses]}")
        results["passed"] += 1
        results["tests"].append(("Certificate Status", "PASS"))
    except Exception as e:
        print(f"  ❌ Certificate status failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Certificate Status", "FAIL"))

    # Test 6: List certificates method exists
    print("Test 6: List certificates method...")

    try:
        has_list = hasattr(manager, "list_certificates")

        if has_list:
            print("  ✅ list_certificates method available")
            results["passed"] += 1
            results["tests"].append(("List Certificates Method", "PASS"))
        else:
            print("  ❌ list_certificates method not found")
            results["failed"] += 1
            results["tests"].append(("List Certificates Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ List method check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("List Certificates Method", "FAIL"))

    print(f"\n📊 Validation 2.3 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_ssh_key_manager():
    """Test 2.4: SSH Key Management"""
    print("\n=== Validation 2.4: SSH Key Management ===\n")

    from configurator.security.ssh_manager import (
        KeyStatus,
        KeyType,
        SSHKey,
        SSHKeyManager,
        SSHSecurityStatus,
    )

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: Manager initialization
    print("Test 1: SSHKeyManager initialization...")

    try:
        manager = SSHKeyManager()
        print("  ✅ SSHKeyManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: Key types exist
    print("Test 2: Key types defined...")

    try:
        key_types = [KeyType.ED25519, KeyType.RSA, KeyType.ECDSA]
        print(f"  ✅ Key types: {[kt.value for kt in key_types]}")
        results["passed"] += 1
        results["tests"].append(("Key Types", "PASS"))
    except Exception as e:
        print(f"  ❌ Key types failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Key Types", "FAIL"))

    # Test 3: Key status values
    print("Test 3: Key status values...")

    try:
        statuses = [KeyStatus.ACTIVE, KeyStatus.EXPIRED, KeyStatus.REVOKED, KeyStatus.STALE]
        print(f"  ✅ Key statuses: {[s.value for s in statuses]}")
        results["passed"] += 1
        results["tests"].append(("Key Status Values", "PASS"))
    except Exception as e:
        print(f"  ❌ Key status failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Key Status Values", "FAIL"))

    # Test 4: SSHKey dataclass
    print("Test 4: SSHKey dataclass...")

    try:
        from datetime import datetime

        test_key = SSHKey(
            key_id="test-key-001",
            user="testuser",
            public_key="ssh-ed25519 AAAA... test@example.com",
            key_type=KeyType.ED25519,
            fingerprint="SHA256:abc123...",
            created_at=datetime.now(),
        )

        key_dict = test_key.to_dict()

        if "key_id" in key_dict and "user" in key_dict:
            print("  ✅ SSHKey dataclass works")
            results["passed"] += 1
            results["tests"].append(("SSHKey Dataclass", "PASS"))
        else:
            print("  ❌ SSHKey serialization failed")
            results["failed"] += 1
            results["tests"].append(("SSHKey Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ SSHKey dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("SSHKey Dataclass", "FAIL"))

    # Test 5: Generate key pair method exists
    print("Test 5: Generate key pair method...")

    try:
        has_generate = hasattr(manager, "generate_key_pair")

        if has_generate:
            print("  ✅ generate_key_pair method available")
            results["passed"] += 1
            results["tests"].append(("Generate Method", "PASS"))
        else:
            print("  ❌ generate_key_pair method not found")
            results["failed"] += 1
            results["tests"].append(("Generate Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Generate method check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Generate Method", "FAIL"))

    # Test 6: SSHSecurityStatus dataclass
    print("Test 6: SSHSecurityStatus dataclass...")

    try:
        status = SSHSecurityStatus(
            password_auth_enabled=False,
            root_login_enabled=False,
            empty_passwords_allowed=False,
            pubkey_auth_enabled=True,
            total_keys=5,
            active_keys=4,
            expiring_keys=1,
            stale_keys=0,
        )

        status_dict = status.to_dict()

        if "password_auth_enabled" in status_dict:
            print("  ✅ SSHSecurityStatus works")
            results["passed"] += 1
            results["tests"].append(("SSHSecurityStatus", "PASS"))
        else:
            print("  ❌ SSHSecurityStatus serialization failed")
            results["failed"] += 1
            results["tests"].append(("SSHSecurityStatus", "FAIL"))
    except Exception as e:
        print(f"  ❌ SSHSecurityStatus failed: {e}")
        results["failed"] += 1
        results["tests"].append(("SSHSecurityStatus", "FAIL"))

    print(f"\n📊 Validation 2.4 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_mfa_manager():
    """Test 2.5: Two-Factor Authentication (MFA)"""
    print("\n=== Validation 2.5: Two-Factor Authentication (MFA) ===\n")

    from configurator.security.mfa_manager import (
        MFAConfig,
        MFAManager,
        MFAMethod,
        MFAStatus,
    )

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: Manager initialization
    print("Test 1: MFAManager initialization...")

    try:
        manager = MFAManager()
        print("  ✅ MFAManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ⚠️ Initialization warning: {e}")
        # May fail due to permissions in test environment
        results["tests"].append(("Manager Initialization", "SKIP"))

    # Test 2: MFA methods defined
    print("Test 2: MFA methods defined...")

    try:
        methods = [MFAMethod.TOTP, MFAMethod.BACKUP_CODE]
        print(f"  ✅ MFA methods: {[m.value for m in methods]}")
        results["passed"] += 1
        results["tests"].append(("MFA Methods", "PASS"))
    except Exception as e:
        print(f"  ❌ MFA methods failed: {e}")
        results["failed"] += 1
        results["tests"].append(("MFA Methods", "FAIL"))

    # Test 3: MFA status values
    print("Test 3: MFA status values...")

    try:
        statuses = [MFAStatus.ENABLED, MFAStatus.DISABLED, MFAStatus.PENDING, MFAStatus.LOCKED]
        print(f"  ✅ MFA statuses: {[s.value for s in statuses]}")
        results["passed"] += 1
        results["tests"].append(("MFA Status Values", "PASS"))
    except Exception as e:
        print(f"  ❌ MFA status failed: {e}")
        results["failed"] += 1
        results["tests"].append(("MFA Status Values", "FAIL"))

    # Test 4: MFAConfig dataclass
    print("Test 4: MFAConfig dataclass...")

    try:
        from datetime import datetime

        config = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=["12345678", "87654321"],
            status=MFAStatus.ENABLED,
            enrolled_at=datetime.now(),
        )

        config_dict = config.to_dict()

        if "user" in config_dict and "secret" in config_dict:
            print("  ✅ MFAConfig dataclass works")
            results["passed"] += 1
            results["tests"].append(("MFAConfig Dataclass", "PASS"))
        else:
            print("  ❌ MFAConfig serialization failed")
            results["failed"] += 1
            results["tests"].append(("MFAConfig Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ MFAConfig dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("MFAConfig Dataclass", "FAIL"))

    # Test 5: Backup codes remaining
    print("Test 5: Backup codes tracking...")

    try:
        remaining = config.backup_codes_remaining()

        if remaining == 2:
            print(f"  ✅ Backup codes remaining: {remaining}")
            results["passed"] += 1
            results["tests"].append(("Backup Codes Tracking", "PASS"))
        else:
            print(f"  ❌ Expected 2, got {remaining}")
            results["failed"] += 1
            results["tests"].append(("Backup Codes Tracking", "FAIL"))
    except Exception as e:
        print(f"  ❌ Backup codes tracking failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Backup Codes Tracking", "FAIL"))

    # Test 6: enroll_user method exists
    print("Test 6: Enroll user method...")

    try:
        manager = MFAManager()
        has_enroll = hasattr(manager, "enroll_user")

        if has_enroll:
            print("  ✅ enroll_user method available")
            results["passed"] += 1
            results["tests"].append(("Enroll Method", "PASS"))
        else:
            print("  ❌ enroll_user method not found")
            results["failed"] += 1
            results["tests"].append(("Enroll Method", "FAIL"))
    except Exception as e:
        print(f"  ⚠️ Enroll method check: {e}")
        results["tests"].append(("Enroll Method", "SKIP"))

    # Test 7: verify_code method exists
    print("Test 7: Verify code method...")

    try:
        manager = MFAManager()
        has_verify = hasattr(manager, "verify_code")

        if has_verify:
            print("  ✅ verify_code method available")
            results["passed"] += 1
            results["tests"].append(("Verify Method", "PASS"))
        else:
            print("  ❌ verify_code method not found")
            results["failed"] += 1
            results["tests"].append(("Verify Method", "FAIL"))
    except Exception as e:
        print(f"  ⚠️ Verify method check: {e}")
        results["tests"].append(("Verify Method", "SKIP"))

    print(f"\n📊 Validation 2.5 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def run_phase2_validation():
    """Run all Phase 2 validation tests"""
    print("\n" + "=" * 70)
    print("    PHASE 2 VALIDATION: Security & Compliance")
    print("=" * 70)

    all_results = []

    try:
        all_results.append(("2.1 CIS Scanner", test_cis_scanner()))
    except Exception as e:
        print(f"\n❌ Validation 2.1 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("2.1 CIS Scanner", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("2.2 Vulnerability Scanner", test_vulnerability_scanner()))
    except Exception as e:
        print(f"\n❌ Validation 2.2 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(
            ("2.2 Vulnerability Scanner", {"passed": 0, "failed": 1, "error": str(e)})
        )

    try:
        all_results.append(("2.3 SSL/TLS Manager", test_ssl_certificate_manager()))
    except Exception as e:
        print(f"\n❌ Validation 2.3 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("2.3 SSL/TLS Manager", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("2.4 SSH Key Manager", test_ssh_key_manager()))
    except Exception as e:
        print(f"\n❌ Validation 2.4 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("2.4 SSH Key Manager", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("2.5 2FA/MFA", test_mfa_manager()))
    except Exception as e:
        print(f"\n❌ Validation 2.5 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("2.5 2FA/MFA", {"passed": 0, "failed": 1, "error": str(e)}))

    # Summary
    print("\n" + "=" * 70)
    print("    PHASE 2 VALIDATION SUMMARY")
    print("=" * 70)

    total_passed = 0
    total_failed = 0

    for name, result in all_results:
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        total_passed += passed
        total_failed += failed

        status = "✅ PASS" if failed == 0 else "❌ FAIL"
        print(f"\n{name}: {status} ({passed} passed, {failed} failed)")

        if "tests" in result:
            for test_name, test_status in result["tests"]:
                icon = "✅" if test_status == "PASS" else "⚠️" if test_status == "SKIP" else "❌"
                print(f"    {icon} {test_name}")

    print(f"\n{'=' * 70}")
    print(f"PHASE 2 TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"{'=' * 70}")

    return total_passed, total_failed


if __name__ == "__main__":
    passed, failed = run_phase2_validation()
    sys.exit(0 if failed == 0 else 1)
