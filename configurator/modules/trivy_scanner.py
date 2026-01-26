"""
Trivy Scanner Module.

Wraps the VulnerabilityManager to provide CVE scanning
as part of the installation process.
"""

import logging
from typing import Any, Dict, List, Optional

from configurator.modules.base import ConfigurationModule
from configurator.security.vulnerability_scanner import (
    ScanResult,
    VulnerabilityManager,
    VulnerabilitySeverity,
)


class TrivyScannerModule(ConfigurationModule):
    """
    Automated Vulnerability Scanning with Trivy.

    Integrates with VulnerabilityManager to perform:
    1. System package scanning
    2. Docker image scanning (if Docker is present)
    3. Optional auto-remediation (package upgrades)
    """

    name = "trivy_scanner"
    description = "Trivy Vulnerability Scanner"
    depends_on = ["system", "security"]  # Scan after basic system/security setup
    priority = 85  # Run very late

    def __init__(
        self, config: Dict[str, Any], logger: Optional[logging.Logger] = None, **kwargs: Any
    ) -> None:
        super().__init__(config, logger, **kwargs)
        self.vuln_manager = VulnerabilityManager(logger=self.logger)
        self.scan_results: List[ScanResult] = []
        self.is_dry_run = False

    def validate(self) -> bool:
        """
        Ensure Trivy is installed.
        """
        # We can't easily detect dry_run in validate without a flag,
        # but module configure/verify usually get passed dry_run if we updated the interface.
        # Actually ConfigurationModule doesn't pass dry_run to validate/configure in standard flow in installer?
        # Installer calls `configure()` directly.
        # But we can check if binary exists.

        try:
            # Check if scanner available
            scanner = self.vuln_manager.get_scanner()
            return True
        except RuntimeError:
            self.logger.info("Trivy not found. Attempting installation...")
            return self._install_trivy()

    def _install_trivy(self) -> bool:
        """Install Trivy using official script."""
        if self.dry_run:
            self.logger.info("[Dry Run] Would install Trivy vulnerability scanner")
            return True

        # Using the script provided in manual or context
        try:
            self.logger.info("Installing Trivy...")

            # Checks based on Manual recommendations (using remote_setup script approach usually better)
            # but we can try basic apt install if repo setup

            # Split setup and install
            setup_cmds = [
                "wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg",
                "echo 'deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main' | tee /etc/apt/sources.list.d/trivy.list",
            ]

            # Execute setup commands with global lock (checking return codes)
            with self._APT_LOCK:
                for cmd in setup_cmds:
                    self.run(cmd, check=True, description=f"Trivy setup: {cmd.split()[0]}")

            # Install using robust install_packages (handles retries and dpkg repair)
            self.install_packages(["trivy"], update_cache=True)

            return True

        except Exception as e:
            self.logger.error(f"Failed to install Trivy: {e}")
            return False

    def configure(self) -> bool:
        """
        Run the scan.
        """
        # Check for dry_run in config if available
        # Note: Installer passes dry_run to execute_module context but explicit arg?
        # Not easily accessible here unless injected.
        # However, `run_command` can be mocked if we use a dry-run aware wrapper.
        # But here run_command is imported.

        # Let's perform the scan.
        self.logger.info("Starting Vulnerability Scan...")

        try:
            # 1. System Scan
            sys_result = self.vuln_manager.scan_system()
            self.scan_results.append(sys_result)
            self._log_summary(sys_result)

            # 2. Docker Scan (if enabled/available)
            docker_results = self.vuln_manager.scan_docker_images()
            self.scan_results.extend(docker_results)
            for res in docker_results:
                self._log_summary(res)

            # 3. Auto-Remediation
            if self.config.get("security.auto_patch", False):
                self.logger.info("Auto-patching enabled for High/Critical vulnerabilities...")
                stats = self.vuln_manager.auto_remediate(
                    sys_result, severity_threshold=VulnerabilitySeverity.HIGH
                )
                self.logger.info(f"Patching complete: {stats}")

        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            # Don't fail the module install just because scan failed?
            # Or maybe yes?
            # Security module usually critical.
            return False

        return True

    def _log_summary(self, result: ScanResult):
        summary = result.get_summary()
        self.logger.info(f"Scan Target: {result.target}")
        self.logger.info(f"  Total Vulnerabilities: {summary['total']}")
        self.logger.info(f"  Critical: {summary['by_severity']['critical']}")
        self.logger.info(f"  High:     {summary['by_severity']['high']}")

    def verify(self) -> bool:
        """
        Verify no critical vulnerabilities exist (if enforced).
        """
        fail_on_critical = self.config.get("security.fail_on_critical", False)

        total_critical = 0
        for res in self.scan_results:
            summary = res.get_summary()
            total_critical += summary["by_severity"]["critical"]

        if fail_on_critical and total_critical > 0:
            self.logger.error(
                f"Verification Failed: Found {total_critical} CRITICAL vulnerabilities."
            )
            return False

        return True
