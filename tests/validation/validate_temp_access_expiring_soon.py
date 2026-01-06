#!/usr/bin/env python3
"""Test expiring soon detection"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.temp_access import AccessType, TempAccess, TempAccessManager


def test_expiring_soon():
    """Test detecting access expiring soon."""
    print("Expiring Soon Detection Test")
    print("=" * 60)

    # Use temp directories
    temp_dir = tempfile.mkdtemp()
    registry_file = Path(temp_dir) / "registry.json"
    extensions_file = Path(temp_dir) / "extensions.json"
    audit_log = Path(temp_dir) / "audit.log"

    temp_mgr = TempAccessManager(
        registry_file=registry_file,
        extensions_file=extensions_file,
        audit_log=audit_log,
    )

    # Test 1: Create access expiring in 5 days
    print("\n1. Creating access expiring in 5 days...")

    test_username = "temp_expiring_test"

    access = TempAccess(
        access_id=f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        username=test_username,
        access_type=AccessType.TEMPORARY,
        granted_at=datetime.now() - timedelta(days=25),
        expires_at=datetime.now() + timedelta(days=5),  # Expires in 5 days
        role="developer",
        reason="Test expiring soon",
        granted_by="test-script",
        notify_before_days=7,
    )

    temp_mgr.access_grants[test_username] = access

    print("  Created access:")
    print(f"     Expires in: {access.days_remaining()} days")

    # Test 2: Test get_expiring_soon()
    print("\n2. Testing get_expiring_soon(days=7)...")

    expiring = temp_mgr.get_expiring_soon(days=7)

    print(f"  Found {len(expiring)} access expiring in 7 days")

    if len(expiring) > 0:
        print("  ✅ Expiring access detected")
        for exp_access in expiring:
            print(f"     - {exp_access.username}: {exp_access.days_remaining()} days left")
    else:
        print("  ⚠️  No expiring access detected")
        return False

    # Test 3: Test needs_reminder()
    print("\n3. Testing needs_reminder() method...")

    if access.needs_reminder():
        print(f"  ✅ Reminder needed (expires in {access.days_remaining()} days)")
    else:
        print(f"  ⚠️  No reminder needed (but should, expires in {access.days_remaining()} days)")
        return False

    # Test 4: Test access not expiring soon
    print("\n4. Testing access not expiring soon...")

    far_username = "temp_far_future_test"
    far_access = TempAccess(
        access_id=f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}-far",
        username=far_username,
        access_type=AccessType.TEMPORARY,
        granted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=25),  # Expires in 25 days
        role="developer",
        reason="Test far future",
        granted_by="test-script",
        notify_before_days=7,
    )

    temp_mgr.access_grants[far_username] = far_access

    # Should not appear in expiring soon (7 days)
    expiring_7 = temp_mgr.get_expiring_soon(days=7)

    if far_username not in [a.username for a in expiring_7]:
        print("  ✅ Access expiring in 25 days not in 7-day list")
    else:
        print("  ❌ Access expiring in 25 days should not be in 7-day list")
        return False

    if not far_access.needs_reminder():
        print("  ✅ No reminder needed for access expiring in 25 days")
    else:
        print("  ⚠️  Should not need reminder yet")

    # Cleanup
    print("\n5. Cleaning up...")
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Expiring soon detection validated")
    return True


if __name__ == "__main__":
    result = test_expiring_soon()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Expiring Soon Detection: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
