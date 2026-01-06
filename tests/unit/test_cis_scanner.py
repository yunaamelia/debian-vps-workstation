from unittest.mock import MagicMock, patch

import pytest

from configurator.security.cis_scanner import (
    CheckResult,
    CISBenchmarkScanner,
    CISCheck,
    ScanReport,
    Severity,
    Status,
)


@pytest.fixture
def scanner():
    # Patch the _register_checks to avoid loading real checks during unit test instantiation
    with patch.object(CISBenchmarkScanner, "_register_checks", return_value=None):
        scanner = CISBenchmarkScanner()
        # Manually verify checks are empty or mocked
        scanner.checks = []
        return scanner


def test_scan_logic(scanner):
    # Create mock checks
    check1 = CISCheck(
        id="1.1",
        title="Test Check 1",
        description="desc",
        rationale="rat",
        severity=Severity.HIGH,
        check_function=lambda: CheckResult(check=None, status=Status.PASS, message="OK"),
    )

    check2 = CISCheck(
        id="1.2",
        title="Test Check 2",
        description="desc",
        rationale="rat",
        severity=Severity.MEDIUM,
        check_function=lambda: CheckResult(check=None, status=Status.FAIL, message="Fail"),
    )

    scanner.checks = [check1, check2]

    report = scanner.scan(level=1)

    assert isinstance(report, ScanReport)
    assert len(report.results) == 2
    assert report.results[0].status == Status.PASS
    assert report.results[0].check == check1
    assert report.results[1].status == Status.FAIL
    assert report.results[1].check == check2
    assert report.score == 50.0


def test_remediate_logic(scanner):
    # Mock remediation function
    rem_func = MagicMock(return_value=True)

    check = CISCheck(
        id="2.1",
        title="Remediate Check",
        description="desc",
        rationale="rat",
        severity=Severity.HIGH,
        check_function=lambda: CheckResult(
            check=None, status=Status.FAIL, message="Fail", remediation_available=True
        ),
        remediation_function=rem_func,
    )

    result = CheckResult(
        check=check, status=Status.FAIL, message="Fail", remediation_available=True
    )

    report = ScanReport(
        scan_id="test",
        scan_date=None,
        hostname="test",
        os_version="test",
        benchmark_version="1.0",
        results=[result],
        score=0.0,
        duration_seconds=1.0,
    )

    stats = scanner.remediate(report)

    assert stats["remediated"] == 1
    assert stats["failed"] == 0
    rem_func.assert_called_once()


def test_check_level_filtering(scanner):
    check1 = CISCheck(
        id="L1",
        title="Level 1",
        description="d",
        rationale="r",
        severity=Severity.LOW,
        level=1,
        check_function=lambda: CheckResult(check=None, status=Status.PASS, message="ok"),
    )
    check2 = CISCheck(
        id="L2",
        title="Level 2",
        description="d",
        rationale="r",
        severity=Severity.LOW,
        level=2,
        check_function=lambda: CheckResult(check=None, status=Status.PASS, message="ok"),
    )

    scanner.checks = [check1, check2]

    report = scanner.scan(level=1)
    assert len(report.results) == 1
    assert report.results[0].check.id == "L1"
