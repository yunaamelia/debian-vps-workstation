import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.exceptions import ConfiguratorError

logger = logging.getLogger(__name__)


class AuditError(ConfiguratorError):
    """Exception raised for audit logging errors."""


class AuditEventType(str, Enum):
    INSTALL_START = "install_start"
    INSTALL_COMPLETE = "install_complete"
    USER_CREATE = "user_create"
    USER_DELETE = "user_delete"
    PERMISSION_CHANGE = "permission_change"
    FIREWALL_RULE_ADD = "firewall_rule_add"
    FIREWALL_RULE_DELETE = "firewall_rule_delete"
    SSH_CONFIG_CHANGE = "ssh_config_change"
    PACKAGE_INSTALL = "package_install"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    SECURITY_VIOLATION = "security_violation"


class AuditLogger:
    """
    Immutable, append-only security audit logger.

    Logs sensitive system events (installation, user creation, firewall changes)
    to a method-only JSON Lines file used for security auditing.

    Attributes:
        DEFAULT_LOG_PATH: Default location /var/log/debian-vps-configurator/audit.jsonl
    """

    DEFAULT_LOG_PATH = Path("/var/log/debian-vps-configurator/audit.jsonl")

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize the audit logger.

        If the log directory does not exist, it creates it with secure permissions (0700).
        Fallback to local directory if permission denied (for testing).

        Args:
            log_path: Custom path for audit log. Defaults to DEFAULT_LOG_PATH.
        """
        self.log_path = log_path or self.DEFAULT_LOG_PATH

        # Ensure directory exists
        if not self.log_path.parent.exists():
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                os.chmod(self.log_path.parent, 0o700)  # Secure directory
            except PermissionError:
                # Fallback for non-root dev
                self.log_path = Path.cwd() / "audit.jsonl"
                logger.warning(f"Using local audit log: {self.log_path}")

        # Ensure log file exists and has correct permissions
        if self.log_path.exists():
            pass  # Append mode handles existence
        else:
            try:
                self.log_path.touch()
                os.chmod(self.log_path, 0o600)  # Read/Write only by owner
            except OSError:
                pass

    def log_event(
        self,
        event_type: AuditEventType,
        description: str,
        user: str = "root",  # Should ideally detect actual user
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        """
        Log a security event.

        Args:
            event_type: Type of the event
            description: Human-readable description
            user: User who initiated the action
            details: structured details about the event
            success: Whether the action was successful
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "user": user,
            "description": description,
            "details": details or {},
            "success": success,
        }

        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except OSError as e:
            logger.error(f"Failed to write audit log: {e}")

    def query_events(
        self, event_type: Optional[AuditEventType] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit events.

        Args:
            event_type: Filter by event type
            limit: Max number of events to return (most recent first)

        Returns:
            List of event dictionaries
        """
        events = []
        if not self.log_path.exists():
            return []

        try:
            with open(self.log_path, "r") as f:
                # Read all lines (efficient enough for typical usage,
                # but could use reverse reading for huge logs)
                lines = f.readlines()

            for line in reversed(lines):
                if len(events) >= limit:
                    break

                try:
                    event = json.loads(line)
                    if event_type and event.get("event_type") != event_type.value:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue

            return events
        except OSError as e:
            logger.error(f"Failed to read audit log: {e}")
            return []
