"""User activity monitoring and auditing system."""

import json
import logging
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ActivityType(Enum):
    """Types of user activities."""

    SSH_LOGIN = "ssh_login"
    SSH_LOGOUT = "ssh_logout"
    COMMAND = "command"
    SUDO_COMMAND = "sudo_command"
    FILE_ACCESS = "file_access"
    FILE_MODIFY = "file_modify"
    PERMISSION_CHANGE = "permission_change"
    AUTH_FAILURE = "auth_failure"


class RiskLevel(Enum):
    """Risk levels for activities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies."""

    UNUSUAL_TIME = "unusual_time"
    NEW_LOCATION = "new_location"
    UNUSUAL_COMMAND = "unusual_command"
    BULK_DOWNLOAD = "bulk_download"
    PERMISSION_ESCALATION = "permission_escalation"
    FAILED_AUTH_SPIKE = "failed_auth_spike"


@dataclass
class ActivityEvent:
    """
    Represents a single user activity event.

    Example:
        ActivityEvent(
            user="johndoe",
            activity_type=ActivityType.SSH_LOGIN,
            timestamp=datetime.now(),
            source_ip="203.0.113.50",
            details={"login_method": "ssh_key"},
        )
    """

    user: str
    activity_type: ActivityType
    timestamp: datetime
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    command: Optional[str] = None
    file_path: Optional[Path] = None
    details: Dict = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "user": self.user,
            "activity_type": self.activity_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "session_id": self.session_id,
            "command": self.command,
            "file_path": str(self.file_path) if self.file_path else None,
            "details": self.details,
            "risk_level": self.risk_level.value,
        }


@dataclass
class SSHSession:
    """SSH session information."""

    session_id: str
    user: str
    source_ip: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    commands_executed: int = 0

    def duration(self) -> Optional[timedelta]:
        """Calculate session duration."""
        if self.logout_time:
            return self.logout_time - self.login_time
        return None


@dataclass
class Anomaly:
    """Detected anomaly."""

    anomaly_id: str
    user: str
    anomaly_type: AnomalyType
    detected_at: datetime
    risk_score: int  # 0-100
    details: Dict = field(default_factory=dict)
    resolved: bool = False

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "anomaly_id": self.anomaly_id,
            "user": self.user,
            "anomaly_type": self.anomaly_type.value,
            "detected_at": self.detected_at.isoformat(),
            "risk_score": self.risk_score,
            "details": self.details,
            "resolved": self.resolved,
        }


class ActivityMonitor:
    """
    Monitors and tracks all user activities.

    Features:
    - SSH session tracking
    - Command execution logging
    - File access monitoring
    - Sudo command tracking
    - Failed authentication tracking
    - Anomaly detection
    - Real-time alerts
    - Compliance reporting
    """

    DB_FILE = Path("/var/lib/debian-vps-configurator/activity/activity.db")
    AUDIT_LOG = Path("/var/log/activity-audit.log")

    def __init__(
        self,
        db_file: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.DB_FILE = db_file or self.DB_FILE
        self.AUDIT_LOG = audit_log or self.AUDIT_LOG

        self._ensure_database()
        self._init_tables()

    def _ensure_database(self):
        """Ensure database directory and file exist."""
        try:
            self.DB_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            self.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        except PermissionError:
            self.logger.debug("No permission to create directories; will use temp")

    def _init_tables(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        # Activity events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source_ip TEXT,
                session_id TEXT,
                command TEXT,
                file_path TEXT,
                details TEXT,
                risk_level TEXT
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user
            ON activity_events(user)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON activity_events(timestamp)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_type
            ON activity_events(activity_type)
        """
        )

        # SSH sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ssh_sessions (
                session_id TEXT PRIMARY KEY,
                user TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                login_time TEXT NOT NULL,
                logout_time TEXT,
                commands_executed INTEGER DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_session_user
            ON ssh_sessions(user)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_session_login_time
            ON ssh_sessions(login_time)
        """
        )

        # Anomalies table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS anomalies (
                anomaly_id TEXT PRIMARY KEY,
                user TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                details TEXT,
                resolved INTEGER DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_anomaly_user
            ON anomalies(user)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_anomaly_detected_at
            ON anomalies(detected_at)
        """
        )

        conn.commit()
        conn.close()

    def log_activity(
        self,
        user: str,
        activity_type: ActivityType,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        command: Optional[str] = None,
        file_path: Optional[Path] = None,
        details: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> ActivityEvent:
        """
        Log a user activity event.

        Args:
            user: Username
            activity_type: Type of activity
            source_ip: Source IP address
            session_id: SSH session ID
            command: Command executed (if applicable)
            file_path: File accessed (if applicable)
            details: Additional details
            timestamp: Custom timestamp (default: now)

        Returns:
            ActivityEvent object
        """
        event = ActivityEvent(
            user=user,
            activity_type=activity_type,
            timestamp=timestamp or datetime.now(),
            source_ip=source_ip,
            session_id=session_id,
            command=command,
            file_path=file_path,
            details=details or {},
        )

        # Calculate risk level
        event.risk_level = self._calculate_risk_level(event)

        # Store in database
        self._store_activity(event)

        # Write to audit log
        self._write_audit_log(event)

        # Check for anomalies
        if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._check_for_anomalies(event)

        return event

    def _calculate_risk_level(self, event: ActivityEvent) -> RiskLevel:
        """Calculate risk level for activity."""
        risk_score = 0

        # Check activity type
        if event.activity_type == ActivityType.SUDO_COMMAND:
            risk_score += 20
        elif event.activity_type == ActivityType.PERMISSION_CHANGE:
            risk_score += 30
        elif event.activity_type == ActivityType.AUTH_FAILURE:
            risk_score += 40

        # Check time (outside business hours)
        hour = event.timestamp.hour
        if hour < 6 or hour > 22:
            risk_score += 20

        # Check command patterns (if command activity)
        if event.command:
            suspicious_patterns = [
                r"rm\s+-rf\s+/",
                r"chmod\s+777",
                r"wget.*\.sh",
                r"curl.*\|.*bash",
                r"nc\s+-l",
                r"/etc/passwd",
                r"/etc/shadow",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, event.command):
                    risk_score += 30
                    break

        # Map score to level
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _store_activity(self, event: ActivityEvent):
        """Store activity in database."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO activity_events (
                user, activity_type, timestamp, source_ip, session_id,
                command, file_path, details, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.user,
                event.activity_type.value,
                event.timestamp.isoformat(),
                event.source_ip,
                event.session_id,
                event.command,
                str(event.file_path) if event.file_path else None,
                json.dumps(event.details),
                event.risk_level.value,
            ),
        )

        conn.commit()
        conn.close()

    def _write_audit_log(self, event: ActivityEvent):
        """Write activity to audit log file."""
        try:
            with open(self.AUDIT_LOG, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

    def get_user_activity(
        self,
        user: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_type: Optional[ActivityType] = None,
        limit: Optional[int] = None,
    ) -> List[ActivityEvent]:
        """Get activities for a user."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        query = "SELECT * FROM activity_events WHERE user = ?"
        params = [user]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if activity_type:
            query += " AND activity_type = ?"
            params.append(activity_type.value)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        # Convert rows to ActivityEvent objects
        events = []
        for row in rows:
            try:
                event = ActivityEvent(
                    user=row[1],
                    activity_type=ActivityType(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    source_ip=row[4],
                    session_id=row[5],
                    command=row[6],
                    file_path=Path(row[7]) if row[7] else None,
                    details=json.loads(row[8]) if row[8] else {},
                    risk_level=RiskLevel(row[9]),
                )
                events.append(event)
            except Exception as e:
                self.logger.error(f"Failed to parse activity event: {e}")
                continue

        return events

    def _check_for_anomalies(self, event: ActivityEvent):
        """Check if activity represents an anomaly."""
        # Get user's normal behavior
        baseline = self._get_user_baseline(event.user)

        anomalies = []

        # Check login time
        if event.activity_type == ActivityType.SSH_LOGIN:
            if self._is_unusual_time(event.timestamp, baseline):
                anomaly = self._create_anomaly(
                    user=event.user,
                    anomaly_type=AnomalyType.UNUSUAL_TIME,
                    details={"time": event.timestamp.isoformat()},
                    risk_score=60,
                )
                anomalies.append(anomaly)

        # Check new source IP
        if event.source_ip and not self._is_known_ip(event.user, event.source_ip):
            anomaly = self._create_anomaly(
                user=event.user,
                anomaly_type=AnomalyType.NEW_LOCATION,
                details={"ip": event.source_ip},
                risk_score=70,
            )
            anomalies.append(anomaly)

        # Check suspicious commands
        if event.command and self._is_suspicious_command(event.command):
            anomaly = self._create_anomaly(
                user=event.user,
                anomaly_type=AnomalyType.UNUSUAL_COMMAND,
                details={"command": event.command},
                risk_score=80,
            )
            anomalies.append(anomaly)

        # Store and alert on anomalies
        for anomaly in anomalies:
            self._store_anomaly(anomaly)
            if anomaly.risk_score >= 70:
                self._send_alert(anomaly)

    def _get_user_baseline(self, user: str) -> Dict:
        """Get user's baseline behavior."""
        # Get last 30 days of activity
        start_date = datetime.now() - timedelta(days=30)
        activities = self.get_user_activity(user, start_date=start_date)

        # Calculate normal hours
        login_hours = []
        source_ips = set()

        for activity in activities:
            if activity.activity_type == ActivityType.SSH_LOGIN:
                login_hours.append(activity.timestamp.hour)
                if activity.source_ip:
                    source_ips.add(activity.source_ip)

        return {
            "login_hours": login_hours,
            "source_ips": source_ips,
        }

    def _is_unusual_time(self, timestamp: datetime, baseline: Dict) -> bool:
        """Check if time is unusual based on baseline."""
        hour = timestamp.hour
        login_hours = baseline.get("login_hours", [])

        if not login_hours:
            return False

        # Calculate normal hour range
        if hour < min(login_hours) - 2 or hour > max(login_hours) + 2:
            return True

        return False

    def _is_known_ip(self, user: str, ip: str) -> bool:
        """Check if IP is known for user."""
        baseline = self._get_user_baseline(user)
        return ip in baseline.get("source_ips", set())

    def _is_suspicious_command(self, command: str) -> bool:
        """Check if command is suspicious."""
        suspicious_patterns = [
            r"rm\s+-rf\s+/",
            r"chmod\s+777",
            r"wget.*\.sh",
            r"curl.*\|.*bash",
            r"nc\s+-l",
            r"(passwd|shadow)",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, command):
                return True

        return False

    def _create_anomaly(
        self,
        user: str,
        anomaly_type: AnomalyType,
        details: Dict,
        risk_score: int,
    ) -> Anomaly:
        """Create anomaly object."""
        anomaly_id = f"ANO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        return Anomaly(
            anomaly_id=anomaly_id,
            user=user,
            anomaly_type=anomaly_type,
            detected_at=datetime.now(),
            risk_score=risk_score,
            details=details,
        )

    def _store_anomaly(self, anomaly: Anomaly):
        """Store anomaly in database."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO anomalies (
                anomaly_id, user, anomaly_type, detected_at, risk_score, details, resolved
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                anomaly.anomaly_id,
                anomaly.user,
                anomaly.anomaly_type.value,
                anomaly.detected_at.isoformat(),
                anomaly.risk_score,
                json.dumps(anomaly.details),
                0,
            ),
        )

        conn.commit()
        conn.close()

    def _send_alert(self, anomaly: Anomaly):
        """Send alert for high-risk anomaly."""
        self.logger.warning(
            f"🚨 ANOMALY DETECTED: {anomaly.anomaly_type.value} "
            f"for user {anomaly.user} (risk: {anomaly.risk_score}/100)"
        )

    def get_anomalies(
        self,
        user: Optional[str] = None,
        start_date: Optional[datetime] = None,
        resolved: Optional[bool] = None,
    ) -> List[Anomaly]:
        """Get detected anomalies."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        query = "SELECT * FROM anomalies WHERE 1=1"
        params: List[Any] = []

        if user:
            query += " AND user = ?"
            params.append(user)

        if start_date:
            query += " AND detected_at >= ?"
            params.append(start_date.isoformat())

        if resolved is not None:
            query += " AND resolved = ?"
            params.append(1 if resolved else 0)

        query += " ORDER BY detected_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        # Convert rows to Anomaly objects
        anomalies = []
        for row in rows:
            try:
                anomaly = Anomaly(
                    anomaly_id=row[0],
                    user=row[1],
                    anomaly_type=AnomalyType(row[2]),
                    detected_at=datetime.fromisoformat(row[3]),
                    risk_score=row[4],
                    details=json.loads(row[5]) if row[5] else {},
                    resolved=bool(row[6]),
                )
                anomalies.append(anomaly)
            except Exception as e:
                self.logger.error(f"Failed to parse anomaly: {e}")
                continue

        return anomalies

    def generate_activity_report(
        self,
        user: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate comprehensive activity report."""
        activities = self.get_user_activity(user, start_date, end_date)

        # Count by activity type
        ssh_logins = [a for a in activities if a.activity_type == ActivityType.SSH_LOGIN]
        commands = [a for a in activities if a.activity_type == ActivityType.COMMAND]
        sudo_commands = [a for a in activities if a.activity_type == ActivityType.SUDO_COMMAND]
        file_accesses = [a for a in activities if a.activity_type == ActivityType.FILE_ACCESS]
        auth_failures = [a for a in activities if a.activity_type == ActivityType.AUTH_FAILURE]

        # Calculate session statistics
        timedelta()
        source_ips = set()

        for activity in ssh_logins:
            if activity.source_ip:
                source_ips.add(activity.source_ip)

        report = {
            "user": user,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_activities": len(activities),
                "ssh_sessions": len(ssh_logins),
                "commands": len(commands),
                "sudo_commands": len(sudo_commands),
                "file_accesses": len(file_accesses),
                "auth_failures": len(auth_failures),
                "unique_ips": len(source_ips),
            },
            "recent_activities": [a.to_dict() for a in activities[:50]],  # Last 50
        }

        return report

    def start_ssh_session(
        self,
        user: str,
        source_ip: str,
    ) -> str:
        """Start tracking an SSH session."""
        session_id = f"SSH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO ssh_sessions (session_id, user, source_ip, login_time)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, user, source_ip, datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

        # Log activity
        self.log_activity(
            user=user,
            activity_type=ActivityType.SSH_LOGIN,
            source_ip=source_ip,
            session_id=session_id,
        )

        return session_id

    def end_ssh_session(self, session_id: str):
        """End tracking an SSH session."""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE ssh_sessions
            SET logout_time = ?
            WHERE session_id = ?
        """,
            (datetime.now().isoformat(), session_id),
        )

        conn.commit()
        conn.close()
