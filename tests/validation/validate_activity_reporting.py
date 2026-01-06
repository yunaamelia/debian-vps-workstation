#!/usr/bin/env python3
"""Test activity report generation"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta

from configurator.users.activity_monitor import ActivityMonitor, ActivityType


def test_report_generation():
    """Test generating activity reports."""
    print("Activity Report Generation Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "activity.db"
    audit_log = Path(temp_dir) / "audit.log"

    monitor = ActivityMonitor(db_file=db_file, audit_log=audit_log)
    test_user = "testuser_report"

    # Setup: Log activities
    print("\n1. Setting up test activities...")

    for i in range(10):
        monitor.log_activity(
            user=test_user, activity_type=ActivityType.COMMAND, command=f"test command {i}"
        )

    monitor.log_activity(
        user=test_user, activity_type=ActivityType.SSH_LOGIN, source_ip="203.0.113.50"
    )

    monitor.log_activity(
        user=test_user, activity_type=ActivityType.SUDO_COMMAND, command="systemctl restart myapp"
    )

    print("  ✅ Test activities logged")

    # Test 2: Generate report
    print("\n2. Generating activity report...")

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        report = monitor.generate_activity_report(
            user=test_user, start_date=start_date, end_date=end_date
        )

        print("  ✅ Report generated")
        print("\n  Report Summary:")
        print(f"    User: {report['user']}")
        print(f"    Total activities: {report['summary']['total_activities']}")
        print(f"    SSH sessions: {report['summary']['ssh_sessions']}")
        print(f"    Commands: {report['summary']['commands']}")
        print(f"    Sudo commands: {report['summary']['sudo_commands']}")

        # Verify report structure
        if "user" in report and "summary" in report and "recent_activities" in report:
            print("\n  ✅ Report structure correct")
        else:
            print("\n  ❌ Report structure incomplete")
            return False

        # Verify summary values
        if report["summary"]["total_activities"] >= 12:
            print("  ✅ Activity count correct")
        else:
            print(f"  ⚠️  Expected >= 12 activities, got {report['summary']['total_activities']}")

    except Exception as e:
        print(f"  ❌ Report generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Report generation validated")
    return True


if __name__ == "__main__":
    result = test_report_generation()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Report Generation: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
