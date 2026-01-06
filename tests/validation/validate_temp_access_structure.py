#!/usr/bin/env python3
"""Validate temporary access data models and file structure"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from configurator.users.temp_access import (
    AccessStatus,
    AccessType,
    ExtensionRequest,
    ExtensionStatus,
    TempAccess,
    TempAccessManager,
)


def validate_file_structure():
    """Validate file structure."""
    print("File Structure Validation")
    print("=" * 60)

    files_to_check = [
        ("configurator/users/temp_access.py", True),
        ("tests/unit/test_temp_access.py", True),
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
    """Validate temporary access data models."""
    print("\n\nTemporary Access Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(AccessType, "TEMPORARY"), "Missing TEMPORARY access type"
        assert hasattr(AccessType, "EMERGENCY"), "Missing EMERGENCY access type"
        assert hasattr(AccessType, "TRIAL"), "Missing TRIAL access type"
        print("  ✅ AccessType enum complete")
    except AssertionError as e:
        print(f"  ❌ AccessType enum incomplete: {e}")
        return False

    try:
        assert hasattr(AccessStatus, "ACTIVE"), "Missing ACTIVE status"
        assert hasattr(AccessStatus, "EXPIRED"), "Missing EXPIRED status"
        assert hasattr(AccessStatus, "REVOKED"), "Missing REVOKED status"
        assert hasattr(AccessStatus, "PENDING"), "Missing PENDING status"
        print("  ✅ AccessStatus enum complete")
    except AssertionError as e:
        print(f"  ❌ AccessStatus enum incomplete: {e}")
        return False

    try:
        assert hasattr(ExtensionStatus, "PENDING"), "Missing PENDING status"
        assert hasattr(ExtensionStatus, "APPROVED"), "Missing APPROVED status"
        assert hasattr(ExtensionStatus, "DENIED"), "Missing DENIED status"
        print("  ✅ ExtensionStatus enum complete")
    except AssertionError as e:
        print(f"  ❌ ExtensionStatus enum incomplete: {e}")
        return False

    # Check TempAccess class
    print("\n2. Checking TempAccess class...")
    try:
        # Check methods
        assert hasattr(TempAccess, "is_expired"), "Missing is_expired() method"
        assert hasattr(TempAccess, "days_remaining"), "Missing days_remaining() method"
        assert hasattr(TempAccess, "needs_reminder"), "Missing needs_reminder() method"
        assert hasattr(TempAccess, "to_dict"), "Missing to_dict() method"
        print("  ✅ TempAccess dataclass complete")
        print("  ✅ TempAccess methods present")
    except AssertionError as e:
        print(f"  ❌ TempAccess validation failed: {e}")
        return False

    # Check ExtensionRequest class
    print("\n3. Checking ExtensionRequest class...")
    try:
        assert hasattr(ExtensionRequest, "to_dict"), "Missing to_dict() method"
        print("  ✅ ExtensionRequest complete")
    except AssertionError as e:
        print(f"  ❌ ExtensionRequest validation failed: {e}")
        return False

    # Check TempAccessManager methods
    print("\n4. Checking TempAccessManager methods...")
    required_methods = [
        "grant_temp_access",
        "revoke_access",
        "check_expired_access",
        "get_expiring_soon",
        "request_extension",
        "approve_extension",
        "get_access",
        "list_access",
    ]

    try:
        for method in required_methods:
            assert hasattr(TempAccessManager, method), f"Missing method: {method}"
        print(f"  ✅ TempAccessManager has all {len(required_methods)} required methods")
    except AssertionError as e:
        print(f"  ❌ TempAccessManager incomplete: {e}")
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
