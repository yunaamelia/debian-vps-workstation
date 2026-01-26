"""
CIS Compliance Module.

Wraps the CISBenchmarkScanner to provide automated hardening and auditing
as part of the installation process.
"""

import logging
from typing import Any, Dict, Optional

from configurator.modules.base import ConfigurationModule
from configurator.security.cis_scanner import CISBenchmarkScanner, ScanReport, Status


class CISComplianceModule(ConfigurationModule):
    """
    Automated CIS Debian 13 Benchmark compliance.

    Integrates with CISBenchmarkScanner to perform:
    1. Pre-deployment baseline audit
    2. Optional automated remediation
    3. Post-deployment verification
    """

    name = "cis_compliance"
    description = "CIS Benchmark Hardening"
    depends_on = ["system", "security"]  # Run after basic system/security setup
    priority = 80  # Run late in the process

    def __init__(
        self, config: Dict[str, Any], logger: Optional[logging.Logger] = None, **kwargs: Any
    ) -> None:
        super().__init__(config, logger, **kwargs)
        self.scanner = CISBenchmarkScanner(logger=self.logger)
        self.report: Optional[ScanReport] = None

    def validate(self) -> bool:
        """
        Validate prerequisites for CIS scanning.
        """
        # Ensure we have checks registered
        if not self.scanner.checks:
            # Try re-registering if empty (should happen in init but double check)
            self.scanner._register_checks()

        if not self.scanner.checks:
            self.logger.warning("No CIS checks registered. Module will pass but do nothing.")
            return True

        return True

    def configure(self) -> bool:
        """
        Run the CIS configuration/hardening process.

        If 'cis.auto_remediate' is True, it will apply fixes.
        Otherwise, it runs in Audit Mode.
        """
        level = self.config.get("cis.level", 1)  # Default to Level 1
        auto_remediate = self.config.get("cis.auto_remediate", False)

        self.logger.info(f"Running CIS Benchmark Scan (Level {level})...")
        self.report = self.scanner.scan(level=level)

        # Log summary
        summary = self.report.get_summary()
        self.logger.info(f"Initial Scan Score: {summary['score']}/100")
        self.logger.info(f"Passed: {summary['passed']}, Failed: {summary['failed']}")

        if auto_remediate:
            self.logger.info("Auto-remediation enabled. Applying fixes...")

            if self.dry_run:
                self.logger.info("[Dry Run] Would apply CIS remediation fixes...")
                # In dry run, we can't really verify remediation since we didn't do it.
                # So we just log.
            else:
                remediation_stats = self.scanner.remediate(self.report)
                self.logger.info(f"Remediation complete: {remediation_stats}")

                # Re-scan to confirm
                self.logger.info("Verifying remediation...")
                self.report = self.scanner.scan(level=level)
                summary = self.report.get_summary()
                self.logger.info(f"Post-Remediation Score: {summary['score']}/100")

        else:
            self.logger.info("Auto-remediation disabled (Audit Mode).")
            # In audit mode, we strictly don't fail configuration just because findings make it fail.
            # We fail only if the scanner itself crashed.

        return True

    def verify(self) -> bool:
        """
        Verify compliance status.

        If 'cis.enforce_score' is set, fail if score is below threshold.
        """
        if not self.report:
            self.logger.warning("No scan report available during verification.")
            return False

        score_threshold = self.config.get("cis.min_score", 0)  # Default 0 (don't fail)

        if self.report.score < score_threshold:
            self.logger.error(f"CIS Score {self.report.score} is below threshold {score_threshold}")
            return False

        # Also fail if any CRITICAL checks failed and 'cis.fail_on_critical' is True
        fail_on_critical = self.config.get("cis.fail_on_critical", False)
        if fail_on_critical:
            critical_failures = [
                r
                for r in self.report.results
                if r.status == Status.FAIL and r.check and r.check.severity.value == "critical"
            ]
            if critical_failures:
                self.logger.error(f"Found {len(critical_failures)} CRITICAL CIS failures.")
                for failure in critical_failures:
                    check_id = failure.check.id if failure.check else "UNKNOWN"
                    self.logger.error(f"  - {check_id}: {failure.message}")
                return False

        return True
