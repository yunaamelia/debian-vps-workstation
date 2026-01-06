"""
SSL/TLS Certificate Monitoring.

This module provides monitoring and alerting for SSL/TLS certificates,
tracking expiration dates and sending notifications.

Features:
- Certificate expiry monitoring
- Alert notifications (email, webhook)
- Scheduled monitoring checks
- Status dashboard data
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import urllib.error
    import urllib.request

    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertConfig:
    """
    Alert notification configuration.

    Attributes:
        email_enabled: Enable email notifications
        email_recipients: List of email addresses
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        smtp_use_tls: Use TLS for SMTP
        webhook_enabled: Enable webhook notifications
        webhook_url: Webhook URL
        slack_enabled: Enable Slack notifications
        slack_webhook: Slack webhook URL
    """

    email_enabled: bool = False
    email_recipients: List[str] = field(default_factory=list)
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    webhook_enabled: bool = False
    webhook_url: str = ""
    slack_enabled: bool = False
    slack_webhook: str = ""


@dataclass
class CertificateAlert:
    """
    Certificate alert data.

    Attributes:
        domain: Domain name
        level: Alert severity level
        message: Alert message
        days_remaining: Days until expiry
        timestamp: Alert timestamp
    """

    domain: str
    level: AlertLevel
    message: str
    days_remaining: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "level": self.level.value,
            "message": self.message,
            "days_remaining": self.days_remaining,
            "timestamp": self.timestamp.isoformat(),
        }


class CertificateMonitor:
    """
    Monitor SSL/TLS certificate expiration and send alerts.

    Features:
    - Configurable alert thresholds
    - Email notifications
    - Webhook notifications
    - Slack integration
    - Scheduled monitoring

    Usage:
        >>> from configurator.security.certificate_manager import CertificateManager
        >>>
        >>> manager = CertificateManager()
        >>> monitor = CertificateMonitor(manager)
        >>>
        >>> # Check all certificates
        >>> alerts = monitor.check_all_certificates()
        >>>
        >>> # Send alerts
        >>> monitor.send_alerts(alerts)
    """

    DEFAULT_WARNING_DAYS = 30
    DEFAULT_CRITICAL_DAYS = 14

    def __init__(
        self,
        certificate_manager: Any,  # CertificateManager
        alert_config: Optional[AlertConfig] = None,
        warning_threshold_days: int = DEFAULT_WARNING_DAYS,
        critical_threshold_days: int = DEFAULT_CRITICAL_DAYS,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize CertificateMonitor.

        Args:
            certificate_manager: CertificateManager instance
            alert_config: Alert notification configuration
            warning_threshold_days: Days until expiry for warning
            critical_threshold_days: Days until expiry for critical
            logger: Optional logger instance
        """
        self.cert_manager = certificate_manager
        self.alert_config = alert_config or AlertConfig()
        self.warning_days = warning_threshold_days
        self.critical_days = critical_threshold_days
        self.logger = logger or logging.getLogger(__name__)
        self._alert_callbacks: List[Callable[[CertificateAlert], None]] = []

    def add_alert_callback(self, callback: Callable[[CertificateAlert], None]):
        """
        Add a callback function for alerts.

        Args:
            callback: Function to call with alert data
        """
        self._alert_callbacks.append(callback)

    def check_certificate(self, domain: str) -> Optional[CertificateAlert]:
        """
        Check a single certificate for expiry.

        Args:
            domain: Domain name to check

        Returns:
            CertificateAlert if action needed, None otherwise
        """
        try:
            cert = self.cert_manager.get_certificate(domain)
            days = cert.days_until_expiry()

            if days < 0:
                return CertificateAlert(
                    domain=domain,
                    level=AlertLevel.CRITICAL,
                    message=f"Certificate EXPIRED {abs(days)} days ago!",
                    days_remaining=days,
                )
            elif days <= self.critical_days:
                return CertificateAlert(
                    domain=domain,
                    level=AlertLevel.CRITICAL,
                    message=f"Certificate expires in {days} days (CRITICAL)",
                    days_remaining=days,
                )
            elif days <= self.warning_days:
                return CertificateAlert(
                    domain=domain,
                    level=AlertLevel.WARNING,
                    message=f"Certificate expires in {days} days",
                    days_remaining=days,
                )

            return None

        except FileNotFoundError:
            return CertificateAlert(
                domain=domain,
                level=AlertLevel.CRITICAL,
                message="Certificate not found!",
                days_remaining=-1,
            )
        except Exception as e:
            self.logger.error(f"Error checking certificate for {domain}: {e}")
            return None

    def check_all_certificates(self) -> List[CertificateAlert]:
        """
        Check all certificates for expiry.

        Returns:
            List of alerts for certificates needing attention
        """
        alerts = []

        try:
            certificates = self.cert_manager.list_certificates()

            for cert in certificates:
                alert = self.check_certificate(cert.domain)
                if alert:
                    alerts.append(alert)
                    self.logger.info(f"Alert for {cert.domain}: {alert.message}")

        except Exception as e:
            self.logger.error(f"Error checking certificates: {e}")

        return alerts

    def send_alerts(self, alerts: List[CertificateAlert]) -> bool:
        """
        Send alert notifications.

        Args:
            alerts: List of alerts to send

        Returns:
            True if all alerts sent successfully
        """
        if not alerts:
            return True

        success = True

        # Call registered callbacks
        for alert in alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Alert callback error: {e}")

        # Send email notifications
        if self.alert_config.email_enabled:
            try:
                self._send_email_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Email notification failed: {e}")
                success = False

        # Send webhook notifications
        if self.alert_config.webhook_enabled:
            try:
                self._send_webhook_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Webhook notification failed: {e}")
                success = False

        # Send Slack notifications
        if self.alert_config.slack_enabled:
            try:
                self._send_slack_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Slack notification failed: {e}")
                success = False

        return success

    def _send_email_alerts(self, alerts: List[CertificateAlert]):
        """Send email notifications for alerts."""
        if not self.alert_config.email_recipients:
            return

        # Build email content
        subject = f"SSL Certificate Alert - {len(alerts)} certificate(s) need attention"

        body = "SSL Certificate Status Report\n"
        body += "=" * 50 + "\n\n"

        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]

        if critical_alerts:
            body += "🔴 CRITICAL:\n"
            for alert in critical_alerts:
                body += f"  - {alert.domain}: {alert.message}\n"
            body += "\n"

        if warning_alerts:
            body += "🟡 WARNING:\n"
            for alert in warning_alerts:
                body += f"  - {alert.domain}: {alert.message}\n"
            body += "\n"

        body += f"\nGenerated at: {datetime.now().isoformat()}\n"

        # Send email
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = self.alert_config.smtp_user or "ssl-monitor@localhost"
        msg["To"] = ", ".join(self.alert_config.email_recipients)
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self.alert_config.smtp_host, self.alert_config.smtp_port) as server:
            if self.alert_config.smtp_use_tls:
                server.starttls()
            if self.alert_config.smtp_user:
                server.login(self.alert_config.smtp_user, self.alert_config.smtp_password)
            server.send_message(msg)

        self.logger.info(
            f"Email alerts sent to {len(self.alert_config.email_recipients)} recipients"
        )

    def _send_webhook_alerts(self, alerts: List[CertificateAlert]):
        """Send webhook notifications for alerts."""
        if not self.alert_config.webhook_url or not HAS_URLLIB:
            return

        payload = {
            "event": "ssl_certificate_alert",
            "timestamp": datetime.now().isoformat(),
            "alert_count": len(alerts),
            "alerts": [a.to_dict() for a in alerts],
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.alert_config.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            self.logger.info(f"Webhook notification sent: {response.status}")

    def _send_slack_alerts(self, alerts: List[CertificateAlert]):
        """Send Slack notifications for alerts."""
        if not self.alert_config.slack_webhook or not HAS_URLLIB:
            return

        # Build Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔒 SSL Certificate Alert",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(alerts)} certificate(s) need attention*",
                },
            },
            {"type": "divider"},
        ]

        for alert in alerts:
            emoji = "🔴" if alert.level == AlertLevel.CRITICAL else "🟡"
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{alert.domain}*\n{alert.message}",
                    },
                }
            )

        payload = {"blocks": blocks}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.alert_config.slack_webhook,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            self.logger.info(f"Slack notification sent: {response.status}")

    def get_status_dashboard(self) -> Dict[str, Any]:
        """
        Get certificate status dashboard data.

        Returns:
            Dictionary with dashboard data
        """
        try:
            summary = self.cert_manager.get_certificate_status_summary()
            alerts = self.check_all_certificates()

            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "active_alerts": [a.to_dict() for a in alerts],
                "thresholds": {
                    "warning_days": self.warning_days,
                    "critical_days": self.critical_days,
                },
            }

            return dashboard

        except Exception as e:
            self.logger.error(f"Error generating dashboard: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def run_check(self) -> List[CertificateAlert]:
        """
        Run a full certificate check and send alerts.

        Returns:
            List of alerts generated
        """
        self.logger.info("Running certificate expiry check...")

        alerts = self.check_all_certificates()

        if alerts:
            self.logger.warning(f"Found {len(alerts)} certificate(s) needing attention")
            self.send_alerts(alerts)
        else:
            self.logger.info("All certificates are valid")

        return alerts


class ScheduledMonitor:
    """
    Scheduled certificate monitoring with threading.

    Runs periodic checks for certificate expiration.
    """

    def __init__(
        self,
        monitor: CertificateMonitor,
        interval_hours: int = 24,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize scheduled monitor.

        Args:
            monitor: CertificateMonitor instance
            interval_hours: Check interval in hours
            logger: Optional logger instance
        """
        self.monitor = monitor
        self.interval_hours = interval_hours
        self.logger = logger or logging.getLogger(__name__)
        self._running = False
        self._thread = None

    def start(self):
        """Start scheduled monitoring in background thread."""
        import threading

        if self._running:
            self.logger.warning("Monitor already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        self.logger.info(f"Certificate monitoring started (interval: {self.interval_hours}h)")

    def stop(self):
        """Stop scheduled monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Certificate monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        import time

        while self._running:
            try:
                self.monitor.run_check()
            except Exception as e:
                self.logger.error(f"Monitor check failed: {e}")

            # Sleep for interval
            sleep_seconds = self.interval_hours * 3600
            for _ in range(int(sleep_seconds / 10)):
                if not self._running:
                    break
                time.sleep(10)
