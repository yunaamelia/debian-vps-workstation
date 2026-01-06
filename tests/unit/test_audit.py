import json
from unittest.mock import patch

import pytest

from configurator.core.audit import AuditEventType, AuditLogger


@pytest.fixture
def audit_logger(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    with patch("os.chmod"):
        logger = AuditLogger(log_path=log_file)
        yield logger


def test_log_event(audit_logger):
    audit_logger.log_event(
        AuditEventType.USER_CREATE, "Created user test", details={"username": "test"}
    )

    assert audit_logger.log_path.exists()

    with open(audit_logger.log_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "user_create"
        assert event["description"] == "Created user test"
        assert event["details"]["username"] == "test"
        assert event["success"] is True
        assert "timestamp" in event


def test_query_events(audit_logger):
    audit_logger.log_event(AuditEventType.INSTALL_START, "Start")
    audit_logger.log_event(AuditEventType.USER_CREATE, "User 1")
    audit_logger.log_event(AuditEventType.USER_CREATE, "User 2")

    # Query all
    events = audit_logger.query_events()
    assert len(events) == 3
    # Check order (most recent first)
    assert events[0]["description"] == "User 2"

    # Query filtered
    user_events = audit_logger.query_events(event_type=AuditEventType.USER_CREATE)
    assert len(user_events) == 2
    assert user_events[0]["event_type"] == "user_create"


def test_query_limit(audit_logger):
    for i in range(10):
        audit_logger.log_event(AuditEventType.PACKAGE_INSTALL, f"Pkg {i}")

    events = audit_logger.query_events(limit=5)
    assert len(events) == 5
    assert events[0]["description"] == "Pkg 9"


def test_permissions(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    with patch("os.chmod") as mock_chmod:
        AuditLogger(log_path=log_file)
        mock_chmod.assert_called()  # Should set permissions on init if file missing/folder created
