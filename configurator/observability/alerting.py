"""
Alerting system for VPS Configurator.

Sends alerts via multiple channels (email, Slack, webhook, file).
"""

import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""

    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class AlertChannel:
    """Base class for alert channels."""

    def send(self, alert: Alert) -> bool:
        """
        Send alert via this channel.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """Send alerts via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_addr: str,
        to_addrs: List[str],
        use_tls: bool = True,
    ):
        """Initialize email channel."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls

    def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Body
            body = f"""
Alert: {alert.title}
Severity: {alert.severity.value}
Source: {alert.source}
Time: {alert.timestamp}

{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2) if alert.metadata else "None"}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
            return False


class SlackAlertChannel(AlertChannel):
    """Send alerts via Slack webhook."""

    def __init__(self, webhook_url: str):
        """Initialize Slack channel."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for Slack alerts")

        self.webhook_url = webhook_url

    def send(self, alert: Alert) -> bool:
        """Send alert via Slack."""
        try:
            # Color by severity
            colors = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#990000",
            }

            # Build Slack message
            payload = {
                "attachments": [
                    {
                        "color": colors.get(alert.severity, "#808080"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {"title": "Severity", "value": alert.severity.value, "short": True},
                            {"title": "Source", "value": alert.source, "short": True},
                            {"title": "Time", "value": alert.timestamp.isoformat(), "short": False},
                        ],
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            logging.error(f"Failed to send Slack alert: {e}")
            return False


class WebhookAlertChannel(AlertChannel):
    """Send alerts via generic webhook."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook channel."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for webhook alerts")

        self.url = url
        self.headers = headers or {}

    def send(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            response = requests.post(
                self.url, json=alert.to_dict(), headers=self.headers, timeout=10
            )
            response.raise_for_status()

            return True

        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")
            return False


class FileAlertChannel(AlertChannel):
    """Write alerts to file."""

    def __init__(self, file_path: Path):
        """Initialize file channel."""
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alert: Alert) -> bool:
        """Write alert to file."""
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")

            return True

        except Exception as e:
            logging.error(f"Failed to write alert to file: {e}")
            return False


class AlertManager:
    """
    Manages alerts and channels.

    Sends alerts to configured channels and enforces threshold rules.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize alert manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.channels: List[AlertChannel] = []
        self.threshold_rules: Dict[str, Dict[str, Any]] = {}

    def add_channel(self, channel: AlertChannel):
        """Add alert channel."""
        self.channels.append(channel)

    def add_threshold_rule(
        self,
        metric_name: str,
        condition: Callable[[Any], bool],
        severity: AlertSeverity,
        message_template: str,
    ):
        """
        Add threshold rule.

        Args:
            metric_name: Metric to monitor
            condition: Function that returns True if threshold exceeded
            severity: Alert severity
            message_template: Message template (can use {value} placeholder)
        """
        self.threshold_rules[metric_name] = {
            "condition": condition,
            "severity": severity,
            "message_template": message_template,
        }

    def check_threshold(self, metric_name: str, value: Any):
        """
        Check if metric exceeds threshold.

        Args:
            metric_name: Metric name
            value: Current value
        """
        if metric_name not in self.threshold_rules:
            return

        rule = self.threshold_rules[metric_name]

        # Check condition
        if rule["condition"](value):
            # Send alert
            message = rule["message_template"].format(value=value)

            self.alert(
                rule["severity"],
                f"Threshold Exceeded: {metric_name}",
                message,
                source="threshold_monitor",
                metadata={"metric": metric_name, "value": value},
            )

    def alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send alert to all channels.

        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            source: Source of alert
            metadata: Additional metadata
        """
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        # Log alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }

        self.logger.log(log_level.get(severity, logging.INFO), f"ALERT: {title} - {message}")

        # Send to all channels
        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel.__class__.__name__}: {e}")
