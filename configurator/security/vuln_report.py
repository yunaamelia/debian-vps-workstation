import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from configurator.security.vulnerability_scanner import (
    ScanResult,
    VulnerabilitySeverity,
)


class VulnReportGenerator:
    """
    Generates HTML and JSON reports for vulnerability scans.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created report directory: {self.output_dir}")

    def generate_json(self, results: List[ScanResult]) -> str:
        """
        Generate JSON report for one or more scan results.
        Returns the path to the generated file.
        """
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_scans": len(results),
            "scans": [],
        }

        for result in results:
            scan_data = {
                "scan_id": result.scan_id,
                "scanner": result.scanner_name,
                "version": result.scanner_version,
                "target": result.target,
                "date": result.scan_date.isoformat(),
                "summary": result.get_summary(),
                "vulnerabilities": [v.to_dict() for v in result.vulnerabilities],
            }
            report_data["scans"].append(scan_data)

        # Use a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vuln_scan_report_{timestamp}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=4)
            self.logger.info(f"JSON report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to generate JSON report: {e}")
            raise

    def generate_html(self, results: List[ScanResult]) -> str:
        """
        Generate HTML report for one or more scan results.
        Returns the path to the generated file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vuln_scan_report_{timestamp}.html"
        filepath = self.output_dir / filename

        html_content = self._build_html(results)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info(f"HTML report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise

    def _build_html(self, results: List[ScanResult]) -> str:
        """Construct the HTML content"""

        # Calculate global aggregate stats
        total_vulns = 0
        total_critical = 0
        total_high = 0

        scan_sections = ""

        for result in results:
            summary = result.get_summary()
            total_vulns += summary["total"]
            total_critical += summary["by_severity"].get("critical", 0)
            total_high += summary["by_severity"].get("high", 0)

            scan_sections += self._build_scan_section(result)

        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .header { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }
        .summary-cards { display: flex; gap: 20px; justify-content: center; margin-bottom: 30px; }
        .card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; flex: 1; max-width: 200px; }
        .card h3 { margin: 0; color: #666; font-size: 0.9em; text-transform: uppercase; }
        .card .number { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
        .critical { color: #dc3545; }
        .high { color: #fd7e14; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        .scan-section { background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .vuln-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.9em; }
        .vuln-table th, .vuln-table td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        .vuln-table th { background-color: #f8f9fa; font-weight: 600; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: white; display: inline-block; }
        .badge-critical { background-color: #dc3545; }
        .badge-high { background-color: #fd7e14; }
        .badge-medium { background-color: #ffc107; color: #333; }
        .badge-low { background-color: #28a745; }
        .badge-unknown { background-color: #6c757d; }
        .fix-available { color: #28a745; font-weight: bold; }
        .no-fix { color: #6c757d; font-style: italic; }
        """

        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vulnerability Scan Report</title>
            <style>{css}</style>
        </head>
        <body>
            <div class="header">
                <h1>Vulnerability Scan Report</h1>
                <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>

            <div class="summary-cards">
                <div class="card">
                    <h3>Total Scans</h3>
                    <div class="number">{len(results)}</div>
                </div>
                <div class="card">
                    <h3>Total Vulnerabilities</h3>
                    <div class="number">{total_vulns}</div>
                </div>
                <div class="card">
                    <h3>Critical Risks</h3>
                    <div class="number critical">{total_critical}</div>
                </div>
                <div class="card">
                    <h3>High Risks</h3>
                    <div class="number high">{total_high}</div>
                </div>
            </div>

            {scan_sections}

            <div style="text-align: center; color: #666; margin-top: 40px;">
                <p>Generated by Debian VPS Configurator</p>
            </div>
        </body>
        </html>
        """
        return html

    def _build_scan_section(self, result: ScanResult) -> str:
        """Build HTML for a single scan result"""

        result.get_summary()

        rows = ""
        # Sort vulnerabilities by severity (Critical -> Low)
        severity_order = {
            VulnerabilitySeverity.CRITICAL: 0,
            VulnerabilitySeverity.HIGH: 1,
            VulnerabilitySeverity.MEDIUM: 2,
            VulnerabilitySeverity.LOW: 3,
            VulnerabilitySeverity.UNKNOWN: 4,
        }

        sorted_vulns = sorted(
            result.vulnerabilities, key=lambda x: severity_order.get(x.severity, 99)
        )

        for v in sorted_vulns:
            f"badge-{v.severity.value}"
            fix_info = (
                f"<span class='fix-available'>Fixed in {v.fixed_version}</span>"
                if v.fixed_version
                else "<span class='no-fix'>No fix</span>"
            )

            # Link CVE if possible
            cve_link = v.cve_id
            if v.references:
                cve_link = f"<a href='{v.references[0]}' target='_blank'>{v.cve_id}</a>"

            rows += """
            <tr>
                <td><span class="badge {severity_class}">{v.severity.value.upper()}</span></td>
                <td><strong>{cve_link}</strong></td>
                <td>
                    <div><strong>{v.package_name}</strong></div>
                    <div style="font-size: 0.85em; color: #666;">Installed: {v.installed_version}</div>
                </td>
                <td>{fix_info}</td>
                <td>{v.description[:150]}{"..." if len(v.description) > 150 else ""}</td>
            </tr>
            """

        if not rows:
            rows = "<tr><td colspan='5' style='text-align: center; padding: 20px;'>No vulnerabilities found! ✅</td></tr>"

        return """
        <div class="scan-section">
            <h2>Target: {result.target}</h2>
            <div style="margin-bottom: 15px; color: #666;">
                Scanner: <strong>{result.scanner_name} {result.scanner_version}</strong> |
                Duration: {result.scan_duration_seconds:.2f}s |
                Vulnerabilities: {summary['total']}
            </div>

            <table class="vuln-table">
                <thead>
                    <tr>
                        <th style="width: 100px;">Severity</th>
                        <th style="width: 150px;">CVE ID</th>
                        <th style="width: 200px;">Package</th>
                        <th style="width: 150px;">Fix Status</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
