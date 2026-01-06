#!/usr/bin/env python3
"""Test user offboarding"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.lifecycle_manager import UserLifecycleManager, UserStatus


def test_user_offboarding():
    """Test complete user offboarding process"""

    print("User Offboarding Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    lifecycle = UserLifecycleManager(
        registry_file=Path(temp_dir) / "registry.json",
        archive_dir=Path(temp_dir) / "archives",
        audit_log=Path(temp_dir) / "audit.log",
        dry_run=False,
    )

    test_username = "testuser_offboard"

    print(f"\nTest username: {test_username}\n")

    # Create user first
    print("1. Creating test user for offboarding...")
    try:
        # Mock RBAC if not available
        if not lifecycle.rbac_manager:
            mock_rbac = MagicMock()
            mock_rbac.assignments = {}
            lifecycle.rbac_manager = mock_rbac

        with patch("subprocess.run"):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.communicate.return_value = ("", "")
                mock_popen.return_value = mock_proc

                with patch("pwd.getpwnam") as mock_getpwnam:
                    mock_pwd = MagicMock()
                    mock_pwd.pw_uid = 1001
                    mock_pwd.pw_gid = 1001
                    mock_pwd.pw_dir = f"/home/{test_username}"
                    mock_getpwnam.return_value = mock_pwd

                    with patch("os.chown"):
                        profile = lifecycle.create_user(
                            username=test_username,
                            full_name="Test User Offboard",
                            email="testuser.off@example.com",
                            role="developer",
                            created_by="test-script",
                            enable_ssh_key=False,
                            enable_2fa=False,
                        )
        print("  ✅ Test user created")
    except Exception as e:
        print(f"  ❌ User creation failed: {e}")
        return False

    # Test 2: Offboard user
    print("\n2. Offboarding user...")
    try:
        with patch("subprocess.run"):
            with patch("pathlib.Path.exists", return_value=False):  # Mock sudoers check
                success = lifecycle.offboard_user(
                    username=test_username,
                    reason="Testing offboarding process",
                    offboarded_by="test-script",
                    archive_data=False,  # Skip archival for test
                )

        if success:
            print("  ✅ User offboarded successfully")
        else:
            print("  ❌ Offboarding failed")
            return False

    except Exception as e:
        print(f"  ❌ Offboarding error: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Verify profile updated
    print("\n3. Verifying profile status...")

    updated_profile = lifecycle.get_user_profile(test_username)

    if updated_profile:
        if updated_profile.status == UserStatus.OFFBOARDED:
            print(f"  ✅ Profile status: {updated_profile.status.value}")
            print(f"     Offboarded at: {updated_profile.offboarded_at}")
            print(f"     Offboarded by: {updated_profile.offboarded_by}")
            print(f"     Reason: {updated_profile.offboarding_reason}")
        else:
            print(f"  ❌ Status incorrect: {updated_profile.status.value}")
            return False
    else:
        print("  ❌ Profile not found")
        return False

    # Test 4: Verify RBAC role removed
    if lifecycle.rbac_manager:
        print("\n4. Verifying RBAC role removed...")

        if test_username not in lifecycle.rbac_manager.assignments:
            print("  ✅ RBAC role revoked")
        else:
            print("  ❌ RBAC role still assigned")
            return False

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ User offboarding validated")
    return True


if __name__ == "__main__":
    result = test_user_offboarding()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Offboarding: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
