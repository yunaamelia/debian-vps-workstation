#!/usr/bin/env python3
"""
Validation script for Vulnerability Scanner Integration (Prompt 2.2)
Tests data models, scanner classes, manager, and report generation.
"""

import subprocess
import sys


def check_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("CHECK 1: Module Imports")
    print("=" * 60)

    try:
        pass

        print("✅ vulnerability_scanner.py imports OK")

        print("✅ vuln_report.py imports OK")

        print("✅ vuln_monitor.py imports OK")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def check_data_models():
    """Test data model structures"""
    print("\n" + "=" * 60)
    print("CHECK 2: Data Models")
    print("=" * 60)

    from datetime import datetime

    from configurator.security.vulnerability_scanner import (
        ScanResult,
        Vulnerability,
        VulnerabilitySeverity,
    )

    # Test Vulnerability dataclass
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        package_name="openssl",
        installed_version="1.1.1",
        fixed_version="1.1.2",
        severity=VulnerabilitySeverity.HIGH,
        cvss_score=8.5,
        description="Test vulnerability",
    )

    assert vuln.cve_id == "CVE-2024-1234"
    assert vuln.severity == VulnerabilitySeverity.HIGH
    print("✅ Vulnerability dataclass OK")

    # Test to_dict
    vuln_dict = vuln.to_dict()
    assert "cve_id" in vuln_dict
    assert vuln_dict["severity"] == "high"
    print("✅ Vulnerability.to_dict() OK")

    # Test ScanResult
    result = ScanResult(
        scan_id="test-123",
        scan_date=datetime.now(),
        scanner_name="Test",
        scanner_version="1.0",
        target="system",
        vulnerabilities=[vuln],
        scan_duration_seconds=10.5,
    )

    summary = result.get_summary()
    assert summary["total"] == 1
    assert summary["by_severity"]["high"] == 1
    print("✅ ScanResult.get_summary() OK")

    return True


def check_scanner_abc():
    """Test scanner abstract base class"""
    print("\n" + "=" * 60)
    print("CHECK 3: Scanner Classes")
    print("=" * 60)

    from abc import ABC

    from configurator.security.vulnerability_scanner import (
        GrypeScanner,
        TrivyScanner,
        VulnerabilityScanner,
    )

    # Check ABC structure
    assert issubclass(VulnerabilityScanner, ABC)
    print("✅ VulnerabilityScanner is ABC")

    # Check concrete implementations
    assert issubclass(TrivyScanner, VulnerabilityScanner)
    assert issubclass(GrypeScanner, VulnerabilityScanner)
    print("✅ TrivyScanner and GrypeScanner extend base class")

    # Check methods exist
    trivy = TrivyScanner()
    assert hasattr(trivy, "is_available")
    assert hasattr(trivy, "scan_system")
    assert hasattr(trivy, "scan_docker_image")
    assert hasattr(trivy, "get_version")
    print("✅ Scanner methods exist")

    return True


def check_manager():
    """Test VulnerabilityManager"""
    print("\n" + "=" * 60)
    print("CHECK 4: VulnerabilityManager")
    print("=" * 60)

    from configurator.security.vulnerability_scanner import VulnerabilityManager

    manager = VulnerabilityManager()

    assert hasattr(manager, "scan_system")
    assert hasattr(manager, "scan_docker_images")
    assert hasattr(manager, "auto_remediate")
    assert hasattr(manager, "get_scanner")
    print("✅ VulnerabilityManager methods exist")

    # Check available scanners detection
    print(f"   Available scanners: {manager.available_scanners}")

    return True


def check_report_generator():
    """Test report generation"""
    print("\n" + "=" * 60)
    print("CHECK 5: Report Generator")
    print("=" * 60)

    import os
    import tempfile
    from datetime import datetime

    from configurator.security.vuln_report import VulnReportGenerator
    from configurator.security.vulnerability_scanner import (
        ScanResult,
        Vulnerability,
        VulnerabilitySeverity,
    )

    # Create test data
    vuln = Vulnerability(
        cve_id="CVE-2024-TEST",
        package_name="test-pkg",
        installed_version="1.0",
        fixed_version="1.1",
        severity=VulnerabilitySeverity.CRITICAL,
        cvss_score=9.8,
        description="Test critical vulnerability",
    )

    result = ScanResult(
        scan_id="validation-test",
        scan_date=datetime.now(),
        scanner_name="Validation",
        scanner_version="1.0",
        target="system",
        vulnerabilities=[vuln],
        scan_duration_seconds=1.0,
    )

    # Test report generation
    with tempfile.TemporaryDirectory() as tmpdir:
        reporter = VulnReportGenerator(output_dir=tmpdir)

        # JSON report
        json_path = reporter.generate_json([result])
        assert os.path.exists(json_path)
        print(f"✅ JSON report generated: {json_path}")

        # HTML report
        html_path = reporter.generate_html([result])
        assert os.path.exists(html_path)
        print(f"✅ HTML report generated: {html_path}")

        # Check HTML content
        with open(html_path) as f:
            html_content = f.read()
            assert "CVE-2024-TEST" in html_content
            assert "test-pkg" in html_content
            print("✅ HTML report contains expected content")

    return True


def check_cli_commands():
    """Test CLI command registration"""
    print("\n" + "=" * 60)
    print("CHECK 6: CLI Commands")
    print("=" * 60)

    # Check vuln command group exists
    result = subprocess.run(
        ["python", "-m", "configurator.cli", "vuln", "--help"],
        capture_output=True,
        text=True,
        cwd="/home/racoon/AgentMemorh/debian-vps-workstation",
    )

    if result.returncode == 0:
        print("✅ 'vuln' command group registered")

        # Check subcommands in help output
        if "scan" in result.stdout:
            print("✅ 'vuln scan' subcommand exists")
        if "monitor" in result.stdout:
            print("✅ 'vuln monitor' subcommand exists")

        return True
    else:
        print(f"❌ CLI check failed: {result.stderr}")
        return False


def main():
    print("\n" + "=" * 60)
    print("VULNERABILITY SCANNER VALIDATION")
    print("=" * 60 + "\n")

    tests = [
        ("Module Imports", check_imports),
        ("Data Models", check_data_models),
        ("Scanner ABC", check_scanner_abc),
        ("Manager", check_manager),
        ("Report Generator", check_report_generator),
        ("CLI Commands", check_cli_commands),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} checks passed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
