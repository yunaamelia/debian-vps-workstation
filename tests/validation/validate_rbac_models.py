#!/usr/bin/env python3
"""Validate RBAC data models"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.rbac.rbac_manager import (
    Permission,
    PermissionAction,
    PermissionScope,
    RBACManager,
    Role,
    RoleAssignment,
    SudoAccess,
)


def validate_data_models():
    print("RBAC Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(PermissionScope, "SYSTEM"), "Missing SYSTEM scope"
        assert hasattr(PermissionScope, "APPLICATION"), "Missing APPLICATION scope"
        assert hasattr(PermissionScope, "DATABASE"), "Missing DATABASE scope"
        print("  ✅ PermissionScope enum complete")

        assert hasattr(PermissionAction, "READ"), "Missing READ action"
        assert hasattr(PermissionAction, "WRITE"), "Missing WRITE action"
        assert hasattr(PermissionAction, "ALL"), "Missing ALL action"
        print("  ✅ PermissionAction enum complete")

        assert hasattr(SudoAccess, "NONE"), "Missing NONE sudo"
        assert hasattr(SudoAccess, "LIMITED"), "Missing LIMITED sudo"
        assert hasattr(SudoAccess, "FULL"), "Missing FULL sudo"
        print("  ✅ SudoAccess enum complete")
    except Exception as e:
        print(f"  ❌ Enum validation failed: {e}")
        return False

    # Check Permission class
    print("\n2. Checking Permission class...")
    try:
        assert hasattr(Permission, "matches"), "Missing matches() method"
        print("  ✅ Permission methods present")
    except Exception as e:
        print(f"  ❌ Permission validation failed: {e}")
        return False

    # Check Role class
    print("\n3. Checking Role class...")
    try:
        assert hasattr(Role, "has_permission"), "Missing has_permission()"
        assert hasattr(Role, "get_all_permissions"), "Missing get_all_permissions()"
        print("  ✅ Role methods present")
    except Exception as e:
        print(f"  ❌ Role validation failed: {e}")
        return False

    # Check RoleAssignment class
    print("\n4. Checking RoleAssignment class...")
    try:
        assert hasattr(RoleAssignment, "is_expired"), "Missing is_expired()"
        assert hasattr(RoleAssignment, "to_dict"), "Missing to_dict()"
        print("  ✅ RoleAssignment complete")
    except Exception as e:
        print(f"  ❌ RoleAssignment validation failed: {e}")
        return False

    # Check RBACManager methods
    print("\n5. Checking RBACManager methods...")
    required_methods = [
        "assign_role",
        "check_permission",
        "get_user_permissions",
        "list_roles",
        "get_role",
    ]

    try:
        for method in required_methods:
            assert hasattr(RBACManager, method), f"Missing method: {method}"
        print(f"  ✅ RBACManager has all {len(required_methods)} required methods")
    except Exception as e:
        print(f"  ❌ RBACManager validation failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Data models validated")
    return True


if __name__ == "__main__":
    sys.exit(0 if validate_data_models() else 1)
