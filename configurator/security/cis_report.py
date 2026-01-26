import json
from datetime import datetime
from pathlib import Path

from configurator.security.cis_scanner import ScanReport, Status


class CISReportGenerator:
    """Generates HTML and JSON reports for CIS Scans"""

    def __init__(self, output_dir: str = "/var/log/vps-configurator/cis-reports"):
        self.output_dir = Path(output_dir)

    def _ensure_output_dir(self) -> None:
        if not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Fallback to local dir if not root
                self.output_dir = Path("./cis-reports")
                self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_json(self, report: ScanReport) -> str:
        """Generate JSON report"""
        self._ensure_output_dir()

        filename = f"cis-scan-{report.scan_id}.json"
        filepath = self.output_dir / filename

        data = report.get_summary()
        # Add full results
        data["results"] = [r.to_dict() for r in report.results]

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def generate_html(self, report: ScanReport) -> str:
        """Generate HTML report"""
        self._ensure_output_dir()

        filename = f"cis-scan-{datetime.now().strftime('%Y-%m-%d')}.html"
        filepath = self.output_dir / filename

        report.get_summary()

        # Simple CSS
        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-bottom: 4px solid #007bff; }
        .score-box { font-size: 2.5em; font-weight: bold; }
        .score-good { color: #28a745; }
        .score-warn { color: #ffc107; }
        .score-bad { color: #dc3545; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .severity-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; color: white; }
        .bg-critical { background-color: #dc3545; }
        .bg-high { background-color: #fd7e14; }
        .bg-medium { background-color: #ffc107; color: black; }
        .bg-low { background-color: #17a2b8; }
        .bg-pass { background-color: #28a745; }
        .bg-fail { background-color: #dc3545; }
        .bg-manual { background-color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        tr:hover { background-color: #f5f5f5; }
        .details { font-size: 0.9em; color: #666; }
        """

        # determine score color
        if report.score >= 80:
            pass
        elif report.score >= 60:
            pass

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CIS Security Scan Report</title>
            <style>{css}</style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ CIS Debian Benchmark Scan Report</h1>
                <div class="summary-grid">
                    <div class="card">
                        <h3>Compliance Score</h3>
                        <div class="score-box {score_class}">{report.score}%</div>
                    </div>
                    <div class="card">
                        <h3>Checks</h3>
                        <div>Total: {summary['total_checks']}</div>
                        <div style="color: green">Passed: {summary['passed']}</div>
                        <div style="color: red">Failed: {summary['failed']}</div>
                    </div>
                    <div class="card">
                        <h3>System Info</h3>
                        <div>Host: {report.hostname}</div>
                        <div>OS: {report.os_version}</div>
                        <div>Date: {report.scan_date.strftime('%Y-%m-%d %H:%M:%S')}</div>
                    </div>
                </div>
            </div>

            <h2>Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Severity</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Sort results: Failures first, then by priority
        valid_results = [r for r in report.results if r.check is not None]
        sorted_results = sorted(
            valid_results,
            key=lambda x: (
                0 if x.status == Status.FAIL else 1,
                {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}[
                    x.check.severity.value if x.check else "info"
                ],
            ),
        )

        for res in sorted_results:
            severity_val = res.check.severity.value if res.check else "info"
            status_val = res.status.value.lower()

            # Using f-string for template expansion (variables unused but clearer in intention)
            _bg_sev = f"bg-{severity_val}"
            _bg_status = f"bg-{status_val}"
            if res.status == Status.MANUAL:
                pass

            html += """
                <tr>
                    <td>{res.check.id}</td>
                    <td><span class="severity-badge {sev_class}">{res.check.severity.value.upper()}</span></td>
                    <td>
                        {res.check.title}
                        <div class="details">{res.check.description}</div>
                    </td>
                    <td><span class="severity-badge {status_class}">{res.status.value.upper()}</span></td>
                    <td>{res.message}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        with open(filepath, "w") as f:
            f.write(html)

        return str(filepath)
