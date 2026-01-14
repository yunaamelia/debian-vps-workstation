import logging
import platform
import socket
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional


class Severity(Enum):
    """Security issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Status(Enum):
    """Check result status"""

    PASS = "pass"
    FAIL = "fail"
    MANUAL = "manual"  # Requires manual verification
    NOT_APPLICABLE = "na"  # Not applicable to this system
    ERROR = "error"  # Check failed to run


@dataclass
class CISCheck:
    """
    Represents a single CIS Benchmark check.
    """

    id: str  # CIS Control ID (e.g., "1.1.2")
    title: str  # Short description
    description: str  # Detailed explanation
    rationale: str  # Why this matters
    severity: Severity  # CRITICAL, HIGH, MEDIUM, LOW
    scored: bool = True  # Counts toward score?
    level: int = 1  # Level 1 or 2 (1 = essential, 2 = defense-in-depth)
    category: str = "General"  # Category (Services, Network, etc.)
    check_function: Optional[Callable] = None  # Function to check compliance
    remediation_function: Optional[Callable] = None  # Function to auto-fix
    manual: bool = False  # Requires manual verification?
    references: List[str] = field(default_factory=list)  # URLs, CVEs, etc.

    def __post_init__(self):
        """Validate check definition"""
        if self.check_function is None and not self.manual:
            raise ValueError(f"Check {self.id} must have check_function or be marked manual")


@dataclass
class CheckResult:
    """Result of running a CIS check"""

    check: CISCheck
    status: Status
    message: str
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    remediation_available: bool = False

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "id": self.check.id,
            "title": self.check.title,
            "status": self.status.value,
            "severity": self.check.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "remediation_available": self.remediation_available,
            "manual": self.check.manual,
        }


@dataclass
class ScanReport:
    """Complete CIS scan report"""

    scan_id: str
    scan_date: datetime
    hostname: str
    os_version: str
    benchmark_version: str
    results: List[CheckResult]
    score: float  # 0-100
    duration_seconds: float

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        scored_results = [r for r in self.results if r.check.scored]
        total = len(scored_results)
        passed = len([r for r in scored_results if r.status == Status.PASS])
        failed = len([r for r in scored_results if r.status == Status.FAIL])

        by_severity = {
            Severity.CRITICAL.value: len(
                [
                    r
                    for r in self.results
                    if r.status == Status.FAIL and r.check.severity == Severity.CRITICAL
                ]
            ),
            Severity.HIGH.value: len(
                [
                    r
                    for r in self.results
                    if r.status == Status.FAIL and r.check.severity == Severity.HIGH
                ]
            ),
            Severity.MEDIUM.value: len(
                [
                    r
                    for r in self.results
                    if r.status == Status.FAIL and r.check.severity == Severity.MEDIUM
                ]
            ),
            Severity.LOW.value: len(
                [
                    r
                    for r in self.results
                    if r.status == Status.FAIL and r.check.severity == Severity.LOW
                ]
            ),
        }

        by_category = {}
        for result in self.results:
            cat = result.check.category
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "total": 0, "failed": 0}
            if result.check.scored:
                by_category[cat]["total"] += 1
                if result.status == Status.PASS:
                    by_category[cat]["passed"] += 1
                elif result.status == Status.FAIL:
                    by_category[cat]["failed"] += 1

        return {
            "scan_id": self.scan_id,
            "scan_date": self.scan_date.isoformat(),
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "score": self.score,
            "by_severity": by_severity,
            "by_category": by_category,
        }


class CISBenchmarkScanner:
    """
    CIS Debian 13 Benchmark compliance scanner.
    """

    BENCHMARK_VERSION = "3.0.0"  # CIS Debian 13 Benchmark version

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.checks: List[CISCheck] = []
        # We will register checks in _register_checks later.
        # For now we start with empty list and expect manual registration or
        # auto-discovery logic to be called.
        self._register_checks()

    def _register_checks(self):
        """
        Register all CIS benchmark checks.
        This method is intended to populate self.checks.
        In the modular implementation, this will import from cis_checks modules.
        """
        # Placeholder for modular registration
        from configurator.security.cis_checks import (
            access_control,
            initial_setup,
            maintenance,
            network,
            services,
        )
        from configurator.security.cis_checks import logging as audit_logging

        # We assume these modules will have a function or list exposed,
        # e.g., get_checks()
        modules = [initial_setup, services, network, audit_logging, access_control, maintenance]

        for module in modules:
            try:
                if hasattr(module, "get_checks"):
                    self.checks.extend(module.get_checks())
            except Exception as e:
                self.logger.warning(f"Failed to load checks from module {module.__name__}: {e}")

        self.logger.info(f"Registered {len(self.checks)} CIS benchmark checks")

    def scan(self, level: int = 1) -> ScanReport:
        """
        Run CIS benchmark scan.

        Args:
            level: CIS level to scan (1 = essential, 2 = defense-in-depth)

        Returns:
            ScanReport with results
        """
        self.logger.info(f"Starting CIS Benchmark scan (Level {level})...")

        scan_start = time.time()
        results = []

        # Filter checks by level
        checks_to_run = [c for c in self.checks if c.level <= level]

        self.logger.info(f"Appplying {len(checks_to_run)} checks...")

        for i, check in enumerate(checks_to_run, 1):
            self.logger.debug(f"[{i}/{len(checks_to_run)}] Checking {check.id}: {check.title}")

            try:
                if check.manual:
                    # Manual check - skip automated testing
                    result = CheckResult(
                        check=check,
                        status=Status.MANUAL,
                        message="Manual verification required",
                    )
                elif check.check_function:
                    # Run automated check
                    result = check.check_function()

                    # Backfill the check object if it's missing (common in modular implementation)
                    if isinstance(result, CheckResult) and result.check is None:
                        result.check = check

                    if not isinstance(result, CheckResult):
                        raise ValueError(
                            f"Check function for {check.id} did not return a CheckResult object"
                        )

                else:
                    result = CheckResult(
                        check=check,
                        status=Status.ERROR,
                        message="No check function defined",
                    )

                results.append(result)

            except Exception as e:
                self.logger.error(f"Error running check {check.id}: {e}", exc_info=True)
                results.append(
                    CheckResult(
                        check=check,
                        status=Status.ERROR,
                        message=f"Check failed: {str(e)}",
                    )
                )

        # Calculate score
        scored_results = [r for r in results if r.check.scored]
        passed = len([r for r in scored_results if r.status == Status.PASS])
        total_scored = len(scored_results)
        score = (passed / total_scored * 100) if total_scored > 0 else 0

        scan_duration = time.time() - scan_start

        report = ScanReport(
            scan_id=str(uuid.uuid4()),
            scan_date=datetime.now(),
            hostname=socket.gethostname(),
            os_version=platform.platform(),
            benchmark_version=self.BENCHMARK_VERSION,
            results=results,
            score=round(score, 1),
            duration_seconds=round(scan_duration, 2),
        )

        self.logger.info(f"Scan complete: {score:.1f}/100 ({passed}/{total_scored} checks passed)")

        return report

    def remediate(self, report: ScanReport, auto_only: bool = True) -> Dict:
        """
        Auto-remediate failed checks.

        Args:
            report: Scan report with failures
            auto_only: Only remediate checks with auto-fix available

        Returns:
            Dictionary with remediation statistics
        """
        failed_checks = [
            r for r in report.results if r.status == Status.FAIL and r.remediation_available
        ]

        if not failed_checks:
            self.logger.info("No auto-remediable issues found")
            return {"remediated": 0, "failed": 0, "skipped": 0}

        self.logger.info(f"Remediating {len(failed_checks)} issues...")

        remediated = 0
        failed = 0

        for result in failed_checks:
            check = result.check

            if not check.remediation_function:
                failed += 1
                continue

            self.logger.info(f"Remediating {check.id}: {check.title}")

            try:
                success = check.remediation_function()
                if success:
                    remediated += 1
                    self.logger.info(f"  ✅ Remediated {check.id}")
                else:
                    failed += 1
                    self.logger.warning(f"  ❌ Failed to remediate {check.id}")

            except Exception as e:
                failed += 1
                self.logger.error(f"  ❌ Error remediating {check.id}: {e}")

        return {
            "remediated": remediated,
            "failed": failed,
            "total": len(failed_checks),
        }
