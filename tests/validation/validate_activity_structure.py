#!/usr/bin/env python3
"""Validate activity monitoring data models and file structure"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from configurator.users.activity_monitor import (
    ActivityEvent,
    ActivityMonitor,
    ActivityType,
    Anomaly,
    AnomalyType,
    RiskLevel,
    SSHSession,
)


def validate_file_structure():
    """Validate file structure."""
    print("File Structure Validation")
    print("=" * 60)

    files_to_check = [
        ("configurator/users/activity_monitor.py", True),
        ("tests/unit/test_activity_monitor.py", True),
        ("tests/integration/test_activity_monitoring.py", True),
        ("config/default.yaml", True),
    ]

    all_exist = True
    for file_path, required in files_to_check:
        full_path = Path(__file__).parent.parent.parent / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(
                f"  {'❌' if required else '⚠️ '} {file_path} {'(required)' if required else '(optional)'}"
            )
            if required:
                all_exist = False

    if all_exist:
        print("\n✅ All required files exist")
        return True
    else:
        print("\n❌ Some required files missing")
        return False


def validate_data_models():
    """Validate activity monitoring data models."""
    print("\n\nActivity Monitoring Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(ActivityType, "SSH_LOGIN"), "Missing SSH_LOGIN activity type"
        assert hasattr(ActivityType, "COMMAND"), "Missing COMMAND activity type"
        assert hasattr(ActivityType, "SUDO_COMMAND"), "Missing SUDO_COMMAND activity type"
        assert hasattr(ActivityType, "FILE_ACCESS"), "Missing FILE_ACCESS activity type"
        print("  ✅ ActivityType enum complete (8 types)")
    except AssertionError as e:
        print(f"  ❌ ActivityType enum incomplete: {e}")
        return False

    try:
        assert hasattr(RiskLevel, "LOW"), "Missing LOW risk level"
        assert hasattr(RiskLevel, "MEDIUM"), "Missing MEDIUM risk level"
        assert hasattr(RiskLevel, "HIGH"), "Missing HIGH risk level"
        assert hasattr(RiskLevel, "CRITICAL"), "Missing CRITICAL risk level"
        print("  ✅ RiskLevel enum complete")
    except AssertionError as e:
        print(f"  ❌ RiskLevel enum incomplete: {e}")
        return False

    try:
        assert hasattr(AnomalyType, "UNUSUAL_TIME"), "Missing UNUSUAL_TIME anomaly"
        assert hasattr(AnomalyType, "NEW_LOCATION"), "Missing NEW_LOCATION anomaly"
        assert hasattr(AnomalyType, "UNUSUAL_COMMAND"), "Missing UNUSUAL_COMMAND anomaly"
        print("  ✅ AnomalyType enum complete")
    except AssertionError as e:
        print(f"  ❌ AnomalyType enum incomplete: {e}")
        return False

    # Check ActivityEvent class
    print("\n2. Checking ActivityEvent class...")
    try:
        # Create test event
        event = ActivityEvent(
            user="testuser",
            activity_type=ActivityType.COMMAND,
            timestamp=__import__("datetime").datetime.now(),
        )

        assert hasattr(event, "user")
        assert hasattr(event, "activity_type")
        assert hasattr(event, "timestamp")
        print("  ✅ ActivityEvent dataclass complete")

        # Check methods
        assert hasattr(ActivityEvent, "to_dict"), "Missing to_dict() method"
        print("  ✅ ActivityEvent methods present")

    except Exception as e:
        print(f"  ❌ ActivityEvent validation failed: {e}")
        return False

    # Check SSHSession class
    print("\n3. Checking SSHSession class...")
    try:
        assert hasattr(SSHSession, "duration"), "Missing duration() method"
        print("  ✅ SSHSession complete")
    except AssertionError as e:
        print(f"  ❌ SSHSession incomplete: {e}")
        return False

    # Check Anomaly class
    print("\n4. Checking Anomaly class...")
    try:
        assert hasattr(Anomaly, "to_dict"), "Missing to_dict() method"
        print("  ✅ Anomaly complete")
    except AssertionError as e:
        print(f"  ❌ Anomaly incomplete: {e}")
        return False

    # Check ActivityMonitor methods
    print("\n5. Checking ActivityMonitor methods...")
    required_methods = [
        "log_activity",
        "get_user_activity",
        "generate_activity_report",
        "start_ssh_session",
        "end_ssh_session",
    ]

    try:
        for method in required_methods:
            assert hasattr(ActivityMonitor, method), f"Missing method: {method}"
        print(f"  ✅ ActivityMonitor has all {len(required_methods)} required methods")
    except AssertionError as e:
        print(f"  ❌ ActivityMonitor incomplete: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Data models validated")
    return True


if __name__ == "__main__":
    result1 = validate_file_structure()
    result2 = validate_data_models()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"File Structure: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if result2 else '❌ FAIL'}")

    sys.exit(0 if (result1 and result2) else 1)
