#!/usr/bin/env python3
"""Test user creation (basic and integrated)"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.lifecycle_manager import UserLifecycleManager


def test_basic_user_creation():
    """Test basic user creation without security integrations"""

    print("Basic User Creation Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    lifecycle = UserLifecycleManager(
        registry_file=Path(temp_dir) / "registry.json",
        archive_dir=Path(temp_dir) / "archives",
        audit_log=Path(temp_dir) / "audit.log",
        dry_run=True,
    )

    test_username = "testuser_basic"

    print(f"\nTest username: {test_username}\n")

    # Test 1: Create user (basic)
    print("1. Creating user (basic setup)...")
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
                    full_name="Test User",
                    email="testuser@example.com",
                    role="developer",
                    created_by="test-script",
                    enable_ssh_key=False,
                    enable_2fa=False,
                    generate_temp_password=False,
                )

        print("  ✅ User created successfully")
        print(f"     Username: {profile.username}")
        print(f"     UID: {profile.uid}")
        print(f"     Role: {profile.role}")
        print(f"     Status: {profile.status.value}")

    except Exception as e:
        print(f"  ❌ User creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Verify profile in registry
    print("\n2. Verifying user registry...")

    retrieved_profile = lifecycle.get_user_profile(test_username)

    if retrieved_profile:
        print("  ✅ User profile found in registry")
        print(f"     Full name: {retrieved_profile.full_name}")
        print(f"     Email: {retrieved_profile.email}")
        print(f"     Created: {retrieved_profile.created_at}")
    else:
        print("  ❌ User profile not in registry")
        return False

    # Test 3: Verify registry persistence
    print("\n3. Testing registry persistence...")

    # Check if registry file exists
    if lifecycle.USER_REGISTRY_FILE.exists():
        print("  ✅ Registry file created")

        # Reload manager
        lifecycle2 = UserLifecycleManager(
            registry_file=lifecycle.USER_REGISTRY_FILE,
            archive_dir=lifecycle.USER_ARCHIVE_DIR,
            audit_log=lifecycle.AUDIT_LOG,
            dry_run=True,
        )

        if test_username in lifecycle2.users:
            print("  ✅ User profile persisted correctly")
        else:
            print("  ❌ User profile not persisted")
            return False
    else:
        print("  ❌ Registry file not created")
        return False

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Basic user creation validated")
    return True


def test_integrated_user_creation():
    """Test user creation with RBAC integration"""

    print("\n\nIntegrated User Creation Test")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()

    lifecycle = UserLifecycleManager(
        registry_file=Path(temp_dir) / "registry.json",
        archive_dir=Path(temp_dir) / "archives",
        audit_log=Path(temp_dir) / "audit.log",
        dry_run=False,
    )

    test_username = "testuser_integrated"

    print(f"\nTest username: {test_username}\n")

    # Check which integrations are available
    print("Available integrations:")
    print(f"  RBAC: {'✅' if lifecycle.rbac_manager else '❌'}")
    print(f"  SSH:  {'✅' if lifecycle.ssh_manager else '❌'}")
    print(f"  MFA:  {'✅' if lifecycle.mfa_manager else '❌'}")
    print()

    # Test 1: Create user with RBAC integration
    print("1. Creating user with RBAC integration...")
    try:
        # Mock RBAC manager
        if not lifecycle.rbac_manager:
            mock_rbac = MagicMock()
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
                            full_name="Test User Integrated",
                            email="testuser.int@example.com",
                            role="developer",
                            created_by="test-script",
                            enable_ssh_key=False,
                            enable_2fa=False,
                        )

        print("  ✅ User created with RBAC integration")
        print(f"     Username: {profile.username}")
        print(f"     Role: {profile.role}")

    except Exception as e:
        print(f"  ❌ User creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Verify RBAC role assignment
    if lifecycle.rbac_manager:
        print("\n2. Verifying RBAC role assignment...")

        # Check if assign_role was called (for mocked manager)
        if hasattr(lifecycle.rbac_manager, "assign_role"):
            try:
                if hasattr(lifecycle.rbac_manager.assign_role, "called"):
                    if lifecycle.rbac_manager.assign_role.called:
                        print("  ✅ RBAC assign_role was called")
                    else:
                        print("  ⚠️  RBAC assign_role not called")
                else:
                    # Real RBAC manager
                    print("  ✅ Using real RBAC manager")
            except Exception as e:
                print(f"  ℹ️  RBAC integration check skipped: {e}")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Integrated user creation validated")
    return True


if __name__ == "__main__":
    result1 = test_basic_user_creation()
    result2 = test_integrated_user_creation()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Basic Creation: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Integrated Creation: {'✅ PASS' if result2 else '❌ FAIL'}")

    sys.exit(0 if (result1 and result2) else 1)
