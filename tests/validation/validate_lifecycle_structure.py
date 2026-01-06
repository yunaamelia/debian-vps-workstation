#!/usr/bin/env python3
"""Validate user lifecycle data models and file structure"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from configurator.users.lifecycle_manager import (
    LifecycleEvent,
    UserLifecycleManager,
    UserProfile,
    UserStatus,
)


def validate_file_structure():
    """Validate file structure"""
    print("File Structure Validation")
    print("=" * 60)

    files_to_check = [
        ("configurator/users/__init__.py", True),
        ("configurator/users/lifecycle_manager.py", True),
        ("tests/unit/test_lifecycle_manager.py", True),
        ("tests/integration/test_user_lifecycle.py", True),
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
    """Validate user lifecycle data models"""
    print("\n\nUser Lifecycle Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(UserStatus, "ACTIVE"), "Missing ACTIVE status"
        assert hasattr(UserStatus, "PENDING"), "Missing PENDING status"
        assert hasattr(UserStatus, "SUSPENDED"), "Missing SUSPENDED status"
        assert hasattr(UserStatus, "OFFBOARDED"), "Missing OFFBOARDED status"
        assert hasattr(UserStatus, "LOCKED"), "Missing LOCKED status"
        print("  ✅ UserStatus enum complete (5 states)")
    except AssertionError as e:
        print(f"  ❌ UserStatus enum incomplete: {e}")
        return False

    try:
        assert hasattr(LifecycleEvent, "CREATED"), "Missing CREATED event"
        assert hasattr(LifecycleEvent, "OFFBOARDED"), "Missing OFFBOARDED event"
        assert hasattr(LifecycleEvent, "SUSPENDED"), "Missing SUSPENDED event"
        assert hasattr(LifecycleEvent, "REACTIVATED"), "Missing REACTIVATED event"
        print("  ✅ LifecycleEvent enum complete")
    except AssertionError as e:
        print(f"  ❌ LifecycleEvent enum incomplete: {e}")
        return False

    # Check UserProfile class
    print("\n2. Checking UserProfile class...")
    try:
        # Create test profile
        profile = UserProfile(
            username="testuser",
            uid=1001,
            full_name="Test User",
            email="test@example.com",
            role="developer",
        )

        # Check required fields
        assert profile.username == "testuser"
        assert profile.uid == 1001
        assert profile.full_name == "Test User"
        assert profile.email == "test@example.com"
        assert profile.role == "developer"

        print("  ✅ UserProfile dataclass complete")

        # Check methods
        assert hasattr(UserProfile, "to_dict"), "Missing to_dict() method"

        # Test to_dict
        data = profile.to_dict()
        assert isinstance(data, dict)
        assert "username" in data
        assert "uid" in data

        print("  ✅ UserProfile methods present")

    except Exception as e:
        print(f"  ❌ UserProfile validation failed: {e}")
        return False

    # Check UserLifecycleManager methods
    print("\n3. Checking UserLifecycleManager methods...")
    required_methods = [
        "create_user",
        "offboard_user",
        "suspend_user",
        "reactivate_user",
        "get_user_profile",
        "list_users",
        "update_user_role",
    ]

    try:
        for method in required_methods:
            assert hasattr(UserLifecycleManager, method), f"Missing method: {method}"
        print(f"  ✅ UserLifecycleManager has all {len(required_methods)} required methods")
    except AssertionError as e:
        print(f"  ❌ UserLifecycleManager incomplete: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Data models validated")
    return True


def validate_manager_initialization():
    """Test Lifecycle Manager initialization"""
    print("\n\nLifecycle Manager Initialization Test")
    print("=" * 60)

    # Test 1: Initialize manager with temp directories
    print("\n1. Initializing Lifecycle Manager...")
    try:
        import tempfile

        temp_dir = tempfile.mkdtemp()

        lifecycle = UserLifecycleManager(
            registry_file=Path(temp_dir) / "registry.json",
            archive_dir=Path(temp_dir) / "archives",
            audit_log=Path(temp_dir) / "audit.log",
            dry_run=True,
        )
        print("  ✅ UserLifecycleManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Check attributes
    print("\n2. Checking manager attributes...")
    try:
        assert hasattr(lifecycle, "users"), "Missing users attribute"
        assert hasattr(lifecycle, "USER_REGISTRY_FILE"), "Missing USER_REGISTRY_FILE"
        assert hasattr(lifecycle, "USER_ARCHIVE_DIR"), "Missing USER_ARCHIVE_DIR"
        assert hasattr(lifecycle, "AUDIT_LOG"), "Missing AUDIT_LOG"
        print("  ✅ Manager attributes present")
    except AssertionError as e:
        print(f"  ❌ Manager attributes incomplete: {e}")
        return False

    # Test 3: Check integrated managers
    print("\n3. Checking integrated managers...")

    if lifecycle.rbac_manager:
        print("  ✅ RBAC manager integrated")
    else:
        print("  ⚠️  RBAC manager not available (may need initialization)")

    if lifecycle.ssh_manager:
        print("  ✅ SSH manager integrated")
    else:
        print("  ℹ️  SSH manager not available (PROMPT 2.4 not implemented)")

    if lifecycle.mfa_manager:
        print("  ✅ MFA manager integrated")
    else:
        print("  ℹ️  MFA manager not available (PROMPT 2.5 not implemented)")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lifecycle Manager initialization validated")
    return True


if __name__ == "__main__":
    result1 = validate_file_structure()
    result2 = validate_data_models()
    result3 = validate_manager_initialization()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"File Structure: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"Manager Init: {'✅ PASS' if result3 else '❌ FAIL'}")

    sys.exit(0 if (result1 and result2 and result3) else 1)
