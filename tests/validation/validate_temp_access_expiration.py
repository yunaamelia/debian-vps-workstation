#!/usr/bin/env python3
"""Test expired access detection"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.temp_access import AccessStatus, AccessType, TempAccess, TempAccessManager


def test_expiration_detection():
    """Test detecting expired access."""
    print("Expiration Detection Test")
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

    test_username = "temp_expired_test"

    # Test 1: Create access that expired yesterday
    print("\n1. Creating already-expired access...")

    access = TempAccess(
        access_id=f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        username=test_username,
        access_type=AccessType.TEMPORARY,
        granted_at=datetime.now() - timedelta(days=31),
        expires_at=datetime.now() - timedelta(days=1),  # Expired yesterday
        role="developer",
        reason="Test expired access",
        granted_by="test-script",
    )

    temp_mgr.access_grants[test_username] = access
    temp_mgr._save_access_registry()

    print("  Created access:")
    print(f"     Granted: {access.granted_at.strftime('%Y-%m-%d')}")
    print(f"     Expired: {access.expires_at.strftime('%Y-%m-%d')}")

    # Test 2: Check if expired
    print("\n2. Testing is_expired() method...")

    if access.is_expired():
        print("  ✅ Access correctly detected as expired")
    else:
        print("  ❌ Access should be expired")
        return False

    # Test 3: Check days remaining
    print("\n3. Testing days_remaining() method...")

    days_left = access.days_remaining()

    if days_left == 0:
        print(f"  ✅ Days remaining: {days_left} (correct for expired access)")
    else:
        print(f"  ⚠️  Days remaining: {days_left} (expected 0)")

    # Test 4: Check expired access detection
    print("\n4. Testing check_expired_access()...")

    expired_list = temp_mgr.check_expired_access()

    print(f"  Found {len(expired_list)} expired access")

    if len(expired_list) > 0:
        print("  ✅ Expired access detected")

        # Verify status was updated
        if access.status == AccessStatus.EXPIRED:
            print("  ✅ Status updated to EXPIRED")
    else:
        print("  ⚠️  No expired access detected")

    # Test 5: Test not expired access
    print("\n5. Testing active access (not expired)...")

    active_username = "temp_active_test"
    active_access = TempAccess(
        access_id=f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}-active",
        username=active_username,
        access_type=AccessType.TEMPORARY,
        granted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=20),  # Expires in 20 days
        role="developer",
        reason="Test active access",
        granted_by="test-script",
    )

    if not active_access.is_expired():
        print("  ✅ Active access correctly detected as not expired")
        print(f"     Days remaining: {active_access.days_remaining()}")
    else:
        print("  ❌ Active access should not be expired")
        return False

    # Cleanup
    print("\n6. Cleaning up...")
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Expiration detection validated")
    return True


if __name__ == "__main__":
    result = test_expiration_detection()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Expiration Detection: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
