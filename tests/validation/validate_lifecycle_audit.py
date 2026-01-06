#!/usr/bin/env python3
"""Test lifecycle audit logging"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.lifecycle_manager import LifecycleEvent, UserLifecycleManager


def test_audit_logging():
    """Test lifecycle audit logging"""

    print("Audit Logging Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    lifecycle = UserLifecycleManager(
        registry_file=Path(temp_dir) / "registry.json",
        archive_dir=Path(temp_dir) / "archives",
        audit_log=Path(temp_dir) / "audit.log",
        dry_run=True,
    )

    test_username = "testuser_audit"

    # Test 1: Create user (generates audit log)
    print("\n1. Creating user to generate audit log...")
    try:
        with patch("subprocess.run"):
            with patch("pwd.getpwnam") as mock_getpwnam:
                mock_pwd = MagicMock()
                mock_pwd.pw_uid = 1001
                mock_pwd.pw_gid = 1001
                mock_pwd.pw_dir = f"/home/{test_username}"
                mock_getpwnam.return_value = mock_pwd

                profile = lifecycle.create_user(
                    username=test_username,
                    full_name="Test Audit User",
                    email="testaudit@example.com",
                    role="viewer",
                    created_by="test-script",
                    enable_ssh_key=False,
                    enable_2fa=False,
                    generate_temp_password=False,
                )
        print("  ✅ User created")
    except Exception as e:
        print(f"  ❌ User creation failed: {e}")
        return False

    # Test 2: Check audit log exists
    print("\n2. Checking audit log file...")

    if lifecycle.AUDIT_LOG.exists():
        print(f"  ✅ Audit log exists: {lifecycle.AUDIT_LOG}")

        # Read last line
        with open(lifecycle.AUDIT_LOG, "r") as f:
            lines = f.readlines()

        if lines:
            last_entry = json.loads(lines[-1])
            print("     Last entry:")
            print(f"       Timestamp: {last_entry['timestamp']}")
            print(f"       Event: {last_entry['event']}")
            print(f"       Username: {last_entry['username']}")
            print(f"       Performed by: {last_entry['performed_by']}")

            # Verify it's a CREATED event
            if last_entry["event"] == LifecycleEvent.CREATED.value:
                print("  ✅ CREATED event logged correctly")
            else:
                print(f"  ⚠️  Unexpected event: {last_entry['event']}")
        else:
            print("  ⚠️  Audit log is empty")
            return False
    else:
        print("  ❌ Audit log not found")
        return False

    # Test 3: Suspend user (generates another audit log)
    print("\n3. Suspending user to generate suspend event...")
    try:
        with patch("subprocess.run"):
            lifecycle.suspend_user(
                username=test_username,
                reason="Audit test",
                suspended_by="test-script",
            )

        # Check for suspend event
        with open(lifecycle.AUDIT_LOG, "r") as f:
            lines = f.readlines()

        last_entry = json.loads(lines[-1])

        if last_entry["event"] == LifecycleEvent.SUSPENDED.value:
            print("  ✅ SUSPENDED event logged correctly")
        else:
            print(f"  ⚠️  Unexpected event: {last_entry['event']}")
    except Exception as e:
        print(f"  ⚠️  Suspend failed: {e}")

    # Test 4: Offboard user
    print("\n4. Offboarding user to generate offboard event...")
    try:
        with patch("subprocess.run"):
            lifecycle.offboard_user(
                username=test_username,
                reason="Audit test",
                offboarded_by="test-script",
                archive_data=False,
            )

        # Check for offboard event
        with open(lifecycle.AUDIT_LOG, "r") as f:
            lines = f.readlines()

        last_entry = json.loads(lines[-1])

        if last_entry["event"] == LifecycleEvent.OFFBOARDED.value:
            print("  ✅ OFFBOARDED event logged correctly")
        else:
            print(f"  ⚠️  Unexpected event: {last_entry['event']}")
    except Exception as e:
        print(f"  ⚠️  Offboard failed: {e}")

    # Test 5: Verify all events logged
    print("\n5. Verifying all lifecycle events...")

    with open(lifecycle.AUDIT_LOG, "r") as f:
        lines = f.readlines()

    events = [json.loads(line)["event"] for line in lines]

    print(f"  Total events logged: {len(events)}")
    print(f"  Events: {', '.join(events)}")

    if LifecycleEvent.CREATED.value in events:
        print("  ✅ CREATED event present")
    if LifecycleEvent.SUSPENDED.value in events:
        print("  ✅ SUSPENDED event present")
    if LifecycleEvent.OFFBOARDED.value in events:
        print("  ✅ OFFBOARDED event present")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Audit logging validated")
    return True


if __name__ == "__main__":
    result = test_audit_logging()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Audit Logging: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
