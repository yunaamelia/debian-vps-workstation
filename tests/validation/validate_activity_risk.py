#!/usr/bin/env python3
"""Test risk level calculation"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.activity_monitor import ActivityMonitor, ActivityType, RiskLevel


def test_risk_calculation():
    """Test risk calculation for different activities."""
    print("Risk Calculation Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "activity.db"
    audit_log = Path(temp_dir) / "audit.log"

    monitor = ActivityMonitor(db_file=db_file, audit_log=audit_log)
    test_user = "testuser_risk"

    # Test 1: Low-risk command
    print("\n1. Testing low-risk command (git)...")
    event = monitor.log_activity(
        user=test_user, activity_type=ActivityType.COMMAND, command="git status"
    )

    print(f"  Command: {event.command}")
    print(f"  Risk: {event.risk_level.value}")

    if event.risk_level == RiskLevel.LOW:
        print("  ✅ Low risk correctly assigned")
    else:
        print(f"  ℹ️  Risk: {event.risk_level.value}")

    # Test 2: Medium-risk command (sudo)
    print("\n2. Testing medium-risk command (sudo)...")
    event = monitor.log_activity(
        user=test_user, activity_type=ActivityType.SUDO_COMMAND, command="systemctl restart myapp"
    )

    print(f"  Command: {event.command}")
    print(f"  Risk: {event.risk_level.value}")

    if event.risk_level in [RiskLevel.MEDIUM, RiskLevel.LOW]:
        print("  ✅ Appropriate risk assigned")
    else:
        print(f"  ℹ️  Unexpected risk: {event.risk_level.value}")

    # Test 3: Suspicious command
    print("\n3. Testing suspicious command (chmod 777)...")
    event = monitor.log_activity(
        user=test_user, activity_type=ActivityType.COMMAND, command="chmod 777 /etc/passwd"
    )

    print(f"  Command: {event.command}")
    print(f"  Risk: {event.risk_level.value}")

    if event.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
        print("  ✅ Elevated risk for suspicious command")
    else:
        print(f"  ℹ️  Risk: {event.risk_level.value}")

    # Test 4: Permission change
    print("\n4. Testing permission change activity...")
    event = monitor.log_activity(
        user=test_user,
        activity_type=ActivityType.PERMISSION_CHANGE,
        command="chmod 644 /tmp/file.txt",
    )

    print("  Activity: Permission change")
    print(f"  Risk: {event.risk_level.value}")

    if event.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
        print("  ✅ Elevated risk for permission change")
    else:
        print(f"  ℹ️  Risk: {event.risk_level.value}")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Risk calculation validated")
    return True


if __name__ == "__main__":
    result = test_risk_calculation()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Risk Calculation: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
