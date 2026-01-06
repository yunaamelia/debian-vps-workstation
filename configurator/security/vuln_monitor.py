import logging
import threading
import time
from typing import Optional

try:
    import schedule

    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

from configurator.security.vuln_report import VulnReportGenerator
from configurator.security.vulnerability_scanner import VulnerabilityManager


class VulnerabilityMonitor:
    """
    Manages scheduled vulnerability scans and alerting.
    """

    def __init__(
        self,
        interval_hours: int = 24,  # Daily default
        auto_remediate: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.interval_hours = interval_hours
        self.auto_remediate = auto_remediate
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        self.scanner_manager = VulnerabilityManager(logger=self.logger)
        self.reporter = VulnReportGenerator()

    def start(self):
        """Start the monitoring thread"""
        if not HAS_SCHEDULE:
            raise RuntimeError(
                "schedule library is required for monitoring. " "Install with: pip install schedule"
            )

        if self.is_running:
            self.logger.warning("Vulnerability monitor already running")
            return

        self.logger.info(f"Starting vulnerability monitor (Every {self.interval_hours}h)")
        self.is_running = True

        # Schedule the scan
        schedule.every(self.interval_hours).hours.do(self._run_scheduled_scan)

        # Start thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the monitoring thread"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.logger.info("Vulnerability monitor stopped")

    def _monitor_loop(self):
        """Main loop for scheduler"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # check every minute

    def _run_scheduled_scan(self):
        """Execute the scan job"""
        self.logger.info("🕒 Starting scheduled vulnerability scan...")

        results = []

        # 1. Scan System
        try:
            sys_result = self.scanner_manager.scan_system()
            results.append(sys_result)
        except Exception as e:
            self.logger.error(f"Scheduled system scan failed: {e}")

        # 2. Scan Docker (if applicable)
        try:
            docker_results = self.scanner_manager.scan_docker_images()
            results.extend(docker_results)
        except Exception as e:
            self.logger.error(f"Scheduled docker scan failed: {e}")

        # 3. Generate Reports
        if results:
            try:
                # Generate JSON & HTML
                self.reporter.generate_json(results)
                html_path = self.reporter.generate_html(results)
                self.logger.info(f"Scheduled scan reports: {html_path}")
            except Exception as e:
                self.logger.error(f"Report generation failed: {e}")

            # 4. Auto-Remediation (if enabled)
            if self.auto_remediate:
                for result in results:
                    if result.target == "system":  # Only safely remediate system packages for now
                        self.scanner_manager.auto_remediate(result)
        else:
            self.logger.warning("Scheduled scan produced no results")
