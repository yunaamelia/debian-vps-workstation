"""
Vulnerability Scanner Wrapper

Simplified wrapper around Trivy and Lynis for easy integration.
Uses the full VulnerabilityScanner implementation but provides
a simpler interface for the security module.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SimpleVulnerability:
    """Simplified vulnerability representation."""

    id: str  # CVE-ID or vulnerability ID
    title: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    package: str
    installed_version: str
    fixed_version: Optional[str]
    description: str
    references: List[str]


class VulnScannerWrapper:
    """
    Simplified vulnerability scanner wrapper.

    Integrates Trivy and Lynis for vulnerability scanning.
    """

    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initialize vulnerability scanner.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Scanner configuration
        self.scanner_type = config.get("security_advanced.vulnerability_scanner.scanner", "trivy")
        self.severity_threshold = config.get(
            "security_advanced.vulnerability_scanner.severity_threshold", "HIGH"
        )
        self.report_path = config.get(
            "security_advanced.vulnerability_scanner.report_path",
            "/var/log/vuln-scan-report.json",
        )
        self.auto_update_db = config.get(
            "security_advanced.vulnerability_scanner.auto_update_db", True
        )

        self.vulnerabilities: List[SimpleVulnerability] = []

    def install_scanners(self) -> bool:
        """
        Install vulnerability scanning tools.

        Returns:
            bool: True if installation successful
        """
        self.logger.info("Installing vulnerability scanners...")

        try:
            if "trivy" in self.scanner_type:
                if not self._install_trivy():
                    self.logger.error("Failed to install Trivy")
                    return False

            if "lynis" in self.scanner_type:
                if not self._install_lynis():
                    self.logger.error("Failed to install Lynis")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Scanner installation failed: {e}", exc_info=True)
            return False

    def _install_trivy(self) -> bool:
        """Install Trivy vulnerability scanner."""
        self.logger.info("Installing Trivy...")

        try:
            # Check if already installed
            result = subprocess.run(["which", "trivy"], capture_output=True)
            if result.returncode == 0:
                self.logger.info("Trivy already installed")
                return True

            # Install Trivy from official script
            install_script = """
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | tee -a /etc/apt/sources.list.d/trivy.list
apt-get update
apt-get install -y trivy
"""

            result = subprocess.run(install_script, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Trivy installation failed: {result.stderr}")
                return False

            # Verify installation
            result = subprocess.run(["trivy", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ Trivy installed: {result.stdout.strip()}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Trivy installation error: {e}", exc_info=True)
            return False

    def _install_lynis(self) -> bool:
        """Install Lynis security auditing tool."""
        self.logger.info("Installing Lynis...")

        try:
            # Install via apt
            result = subprocess.run(
                ["apt-get", "install", "-y", "lynis"], capture_output=True, text=True
            )

            if result.returncode != 0:
                self.logger.error(f"Lynis installation failed: {result.stderr}")
                return False

            # Verify installation
            result = subprocess.run(["lynis", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ Lynis installed: {result.stdout.strip()}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Lynis installation error: {e}", exc_info=True)
            return False

    def run_scan(self) -> bool:
        """
        Execute vulnerability scan.

        Returns:
            bool: True if scan completed successfully
        """
        self.logger.info(f"Starting vulnerability scan with {self.scanner_type}...")

        try:
            # Update vulnerability database if configured
            if self.auto_update_db:
                self._update_vulnerability_db()

            # Run scans
            if "trivy" in self.scanner_type:
                if not self._run_trivy_scan():
                    self.logger.warning("Trivy scan had issues")

            if "lynis" in self.scanner_type:
                if not self._run_lynis_scan():
                    self.logger.warning("Lynis scan had issues")

            # Generate report
            self._generate_report()

            # Summary
            critical = sum(1 for v in self.vulnerabilities if v.severity == "CRITICAL")
            high = sum(1 for v in self.vulnerabilities if v.severity == "HIGH")
            medium = sum(1 for v in self.vulnerabilities if v.severity == "MEDIUM")
            low = sum(1 for v in self.vulnerabilities if v.severity == "LOW")

            self.logger.info(
                f"✓ Vulnerability scan complete: "
                f"{critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW"
            )

            # Alert on critical vulnerabilities
            if critical > 0:
                self.logger.warning(
                    f"⚠️  {critical} CRITICAL vulnerabilities found! Review immediately."
                )

            return True

        except Exception as e:
            self.logger.error(f"Vulnerability scan failed: {e}", exc_info=True)
            return False

    def _update_vulnerability_db(self):
        """Update vulnerability databases."""
        self.logger.info("Updating vulnerability databases...")

        try:
            if "trivy" in self.scanner_type:
                result = subprocess.run(
                    ["trivy", "image", "--download-db-only"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    self.logger.info("✓ Trivy database updated")
        except Exception as e:
            self.logger.warning(f"Database update failed: {e}")

    def _run_trivy_scan(self) -> bool:
        """Run Trivy filesystem scan."""
        self.logger.info("Running Trivy filesystem scan...")

        try:
            # Scan root filesystem
            cmd = [
                "trivy",
                "rootfs",
                "--format",
                "json",
                "--severity",
                f"{self.severity_threshold},CRITICAL",
                "--quiet",
                "/",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                self.logger.error(f"Trivy scan failed: {result.stderr}")
                return False

            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                self._parse_trivy_results(data)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Trivy output: {e}")
                return False

            return True

        except subprocess.TimeoutExpired:
            self.logger.error("Trivy scan timed out")
            return False
        except Exception as e:
            self.logger.error(f"Trivy scan error: {e}", exc_info=True)
            return False

    def _parse_trivy_results(self, data: dict):
        """Parse Trivy JSON output and extract vulnerabilities."""

        try:
            # Trivy output structure
            results = data.get("Results", [])

            for result in results:
                target = result.get("Target", "unknown")
                vulnerabilities = result.get("Vulnerabilities", [])

                for vuln in vulnerabilities:
                    vulnerability = SimpleVulnerability(
                        id=vuln.get("VulnerabilityID", "UNKNOWN"),
                        title=vuln.get("Title", "No title"),
                        severity=vuln.get("Severity", "UNKNOWN"),
                        package=vuln.get("PkgName", "unknown"),
                        installed_version=vuln.get("InstalledVersion", "unknown"),
                        fixed_version=vuln.get("FixedVersion"),
                        description=vuln.get("Description", "")[:200],  # Truncate
                        references=vuln.get("References", []),
                    )

                    self.vulnerabilities.append(vulnerability)

                    # Log high/critical vulnerabilities
                    if vulnerability.severity in ["HIGH", "CRITICAL"]:
                        self.logger.warning(
                            f"  {vulnerability.severity}: {vulnerability.id} in "
                            f"{vulnerability.package} {vulnerability.installed_version}"
                        )

        except Exception as e:
            self.logger.error(f"Error parsing Trivy results: {e}", exc_info=True)

    def _run_lynis_scan(self) -> bool:
        """Run Lynis security audit."""
        self.logger.info("Running Lynis security audit...")

        try:
            # Run Lynis audit
            cmd = ["lynis", "audit", "system", "--quick", "--quiet", "--no-colors"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # Lynis always returns 0, check output
            if "Lynis" not in result.stdout:
                self.logger.error("Lynis scan produced no output")
                return False

            # Parse Lynis output (simplified)
            self._parse_lynis_results(result.stdout)

            return True

        except subprocess.TimeoutExpired:
            self.logger.error("Lynis scan timed out")
            return False
        except Exception as e:
            self.logger.error(f"Lynis scan error: {e}", exc_info=True)
            return False

    def _parse_lynis_results(self, output: str):
        """Parse Lynis output for warnings and suggestions."""

        try:
            # Look for warnings and suggestions in output
            lines = output.split("\n")

            for line in lines:
                # Lynis warnings
                if "Warning:" in line:
                    self.logger.warning(f"Lynis: {line.strip()}")

                # Lynis suggestions
                if "Suggestion:" in line:
                    self.logger.info(f"Lynis: {line.strip()}")

            # Note: Full Lynis integration would parse the report file
            # For simplicity, we're just logging notable items

        except Exception as e:
            self.logger.error(f"Error parsing Lynis results: {e}", exc_info=True)

    def _generate_report(self):
        """Generate JSON report of vulnerabilities."""

        try:
            report = {
                "scan_date": datetime.now().isoformat(),
                "scanner": self.scanner_type,
                "severity_threshold": self.severity_threshold,
                "summary": {
                    "total": len(self.vulnerabilities),
                    "critical": sum(1 for v in self.vulnerabilities if v.severity == "CRITICAL"),
                    "high": sum(1 for v in self.vulnerabilities if v.severity == "HIGH"),
                    "medium": sum(1 for v in self.vulnerabilities if v.severity == "MEDIUM"),
                    "low": sum(1 for v in self.vulnerabilities if v.severity == "LOW"),
                },
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "severity": v.severity,
                        "package": v.package,
                        "installed_version": v.installed_version,
                        "fixed_version": v.fixed_version,
                        "description": v.description,
                        "references": v.references,
                    }
                    for v in self.vulnerabilities
                ],
            }

            # Write JSON report
            Path(self.report_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.report_path, "w") as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"✓ Vulnerability report saved: {self.report_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}", exc_info=True)

    def get_summary(self) -> Dict[str, int]:
        """
        Get vulnerability count by severity.

        Returns:
            dict: Counts by severity level
        """
        return {
            "total": len(self.vulnerabilities),
            "critical": sum(1 for v in self.vulnerabilities if v.severity == "CRITICAL"),
            "high": sum(1 for v in self.vulnerabilities if v.severity == "HIGH"),
            "medium": sum(1 for v in self.vulnerabilities if v.severity == "MEDIUM"),
            "low": sum(1 for v in self.vulnerabilities if v.severity == "LOW"),
        }
