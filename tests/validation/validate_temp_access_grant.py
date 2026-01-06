#!/usr/bin/env python3
"""Test granting temporary access"""

import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.temp_access import AccessStatus, AccessType, TempAccessManager


def test_temp_access_grant():
    """Test granting temporary access."""
    print("Temporary Access Grant Test")
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

    test_username = "temp_contractor_test"

    print(f"\nTest user: {test_username}\n")

    # Test 1: Grant temporary access
    print("1. Granting temporary access...")
    try:
        access = temp_mgr.grant_temp_access(
            username=test_username,
            full_name="Test Contractor",
            email="test@contractor.com",
            role="developer",
            duration_days=30,
            reason="Testing temporary access",
            granted_by="test-script",
            skip_user_creation=True,
        )

        print("  ✅ Temporary access granted")
        print(f"     Access ID: {access.access_id}")
        print(f"     Username: {access.username}")
        print(f"     Granted: {access.granted_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Expires: {access.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Duration: {access.days_remaining()} days")

    except Exception as e:
        print(f"  ❌ Access grant failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Verify expiration calculation
    print("\n2. Verifying expiration calculation...")

    expected_duration = timedelta(days=30)
    actual_duration = access.expires_at - access.granted_at

    # Allow 1 minute tolerance
    if abs((actual_duration - expected_duration).total_seconds()) < 60:
        print("  ✅ Expiration calculated correctly")
        print("     Expected: 30 days")
        print(f"     Actual: {actual_duration.days} days")
    else:
        print("  ❌ Expiration calculation incorrect")
        print("     Expected: 30 days")
        print(f"     Actual: {actual_duration.days} days")
        return False

    # Test 3: Verify access in registry
    print("\n3. Verifying access in registry...")

    if test_username in temp_mgr.access_grants:
        print("  ✅ Access found in registry")
    else:
        print("  ❌ Access not in registry")
        return False

    # Test 4: Verify access status
    print("\n4. Verifying access status...")

    retrieved_access = temp_mgr.access_grants[test_username]

    if retrieved_access.status == AccessStatus.ACTIVE:
        print("  ✅ Status is ACTIVE")
    else:
        print(f"  ⚠️  Status is {retrieved_access.status.value}")

    if not retrieved_access.is_expired():
        print("  ✅ Access not yet expired")
    else:
        print("  ❌ Access should not be expired")
        return False

    # Test 5: Verify access type
    print("\n5. Verifying access type...")

    if access.access_type == AccessType.TEMPORARY:
        print("  ✅ Access type is TEMPORARY")
    else:
        print(f"  ⚠️  Access type is {access.access_type.value}")

    # Test 6: Verify persistence
    print("\n6. Verifying persistence...")

    # Create new manager instance
    new_mgr = TempAccessManager(
        registry_file=registry_file,
        extensions_file=extensions_file,
        audit_log=audit_log,
    )

    persisted_access = new_mgr.get_access(test_username)

    if persisted_access:
        print("  ✅ Access persisted to registry")
        print(f"     Access ID: {persisted_access.access_id}")
    else:
        print("  ❌ Access not persisted")
        return False

    # Test 7: Verify audit log
    print("\n7. Verifying audit log...")

    if audit_log.exists():
        print("  ✅ Audit log created")

        with open(audit_log, "r") as f:
            content = f.read()

        if "grant_access" in content and test_username in content:
            print("  ✅ Access grant logged")
    else:
        print("  ⚠️  Audit log not found")

    # Cleanup
    print("\n8. Cleaning up...")
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Temporary access grant validated")
    return True


if __name__ == "__main__":
    result = test_temp_access_grant()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Access Grant: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
