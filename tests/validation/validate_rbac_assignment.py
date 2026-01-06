#!/usr/bin/env python3
"""Test role assignment and validation"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.rbac.rbac_manager import RBACManager


def test_manager_initialization():
    print("RBAC Manager Initialization Test")
    print("=" * 60)

    # Use temp directory for testing
    temp_dir = tempfile.mkdtemp(prefix="rbac_test_")
    roles_file = Path(temp_dir) / "roles.yaml"
    assignments_file = Path(temp_dir) / "assignments.json"
    audit_log = Path(temp_dir) / "audit.log"

    # Copy default roles file to temp
    import shutil

    default_roles = Path(__file__).parent.parent.parent / "configurator/rbac/roles.yaml"
    if default_roles.exists():
        shutil.copy(default_roles, roles_file)

    # Test 1: Initialize manager
    print("\n1. Initializing RBAC Manager...")
    try:
        rbac = RBACManager(
            roles_file=str(roles_file),
            assignments_file=str(assignments_file),
            audit_log=str(audit_log),
            dry_run=True,
        )
        print("  ✅ RBACManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False, None, temp_dir

    # Test 2: Check RBAC directory
    print("\n2. Checking RBAC directory...")
    if Path(temp_dir).exists():
        print(f"  ✅ RBAC directory exists: {temp_dir}")
    else:
        print("  ❌ RBAC directory not found")
        return False, None, temp_dir

    # Test 3: Check roles file
    print("\n3. Checking roles configuration...")
    if roles_file.exists():
        print(f"  ✅ Roles file exists: {roles_file}")

        roles = rbac.list_roles()
        print(f"     Loaded roles: {len(roles)}")

        if len(roles) >= 4:
            print("  ✅ Default roles loaded")
        else:
            print(f"  ⚠️  Few roles loaded: {len(roles)}")
    else:
        print("  ℹ️  Roles file will be created with defaults")

    # Test 4: List predefined roles
    print("\n4. Listing predefined roles...")
    roles = rbac.list_roles()

    expected_roles = ["admin", "devops", "developer", "viewer"]

    for role_name in expected_roles:
        role = rbac.get_role(role_name)
        if role:
            print(f"  ✅ {role_name:12s} - {role.description}")
            print(f"     Permissions: {len(role.permissions)}")
            print(f"     Sudo: {role.sudo_access.value}")
        else:
            print(f"  ❌ {role_name} role not found")
            return False, None, temp_dir

    print("\n" + "=" * 60)
    print("✅ RBAC Manager initialization validated")
    return True, rbac, temp_dir


def test_role_assignment(rbac):
    print("\n\nRole Assignment Test")
    print("=" * 60)

    test_user = "testuser"

    print(f"Test user: {test_user}\n")

    # Test 1: Assign developer role
    print("1. Assigning 'developer' role...")
    try:
        assignment = rbac.assign_role(
            user=test_user,
            role_name="developer",
            assigned_by="test-script",
            reason="Testing role assignment",
        )

        print("  ✅ Role assigned successfully")
        print(f"     User: {assignment.user}")
        print(f"     Role: {assignment.role_name}")
        print(f"     Assigned by: {assignment.assigned_by}")
        print(f"     Assigned at: {assignment.assigned_at}")

    except Exception as e:
        print(f"  ❌ Role assignment failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Verify assignment persistence
    print("\n2. Verifying assignment persistence...")

    # Need to save first
    rbac._save_role_assignments()

    # Reload manager to test persistence - use same files
    roles_file = rbac.roles_file
    assignments_file = rbac.assignments_file
    audit_log = rbac.audit_log

    rbac2 = RBACManager(
        roles_file=str(roles_file),
        assignments_file=str(assignments_file),
        audit_log=str(audit_log),
        dry_run=True,
    )

    if test_user in rbac2.assignments:
        print("  ✅ Assignment persisted correctly")
        saved_assignment = rbac2.assignments[test_user]
        print(f"     Role: {saved_assignment.role_name}")
    else:
        print("  ❌ Assignment not persisted")
        return False

    # Test 3: Check assignment file
    print("\n3. Checking assignments file...")

    if rbac.assignments_file.exists():
        print(f"  ✅ Assignments file exists: {rbac.assignments_file}")

        import json

        with open(rbac.assignments_file, "r") as f:
            data = json.load(f)

        if test_user in data:
            print("  ✅ User assignment found in file")
        else:
            print("  ❌ User assignment not in file")
            return False
    else:
        print("  ❌ Assignments file not created")
        return False

    # Test 4: Assign non-existent role
    print("\n4. Testing invalid role assignment...")
    try:
        rbac.assign_role(user=test_user, role_name="nonexistent-role", assigned_by="test-script")
        print("  ❌ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✅ Invalid role rejected: {e}")

    print("\n" + "=" * 60)
    print("✅ Role assignment validated")
    return True


def test_permission_validation(rbac):
    print("\n\nPermission Validation Test")
    print("=" * 60)

    test_user = "testuser"

    # Test 1: Check granted permission
    print("\n1. Checking granted permission (app:myapp:deploy)...")
    has_perm = rbac.check_permission(test_user, "app:myapp:deploy")

    if has_perm:
        print("  ✅ Granted permission validated correctly")
    else:
        print("  ⚠️  Developer should have this permission")

    # Test 2: Check denied permission
    print("\n2. Checking denied permission (system:infrastructure:restart)...")
    has_perm = rbac.check_permission(test_user, "system:infrastructure:restart")

    if not has_perm:
        print("  ✅ Denied permission validated correctly")
    else:
        print("  ⚠️  Developer should NOT have this permission")

    # Test 3: Check wildcard permission
    print("\n3. Checking wildcard permission (db:development:read)...")
    has_perm = rbac.check_permission(test_user, "db:development:read")

    if has_perm:
        print("  ✅ Wildcard permission works")
    else:
        print("  ⚠️  Wildcard permission failed")

    # Test 4: Get all user permissions
    print("\n4. Getting all user permissions...")
    permissions = rbac.get_user_permissions(test_user)

    print(f"  Total permissions: {len(permissions)}")

    if len(permissions) > 0:
        print("  ✅ User has permissions")
        print("     Sample permissions (first 5):")
        for perm in permissions[:5]:
            print(f"       - {perm}")
    else:
        print("  ❌ User has no permissions")
        return False

    print("\n" + "=" * 60)
    print("✅ Permission validation validated")
    return True


def cleanup(rbac, temp_dir):
    print("\n\nCleanup")
    print("=" * 60)
    test_user = "testuser"

    if test_user in rbac.assignments:
        del rbac.assignments[test_user]
        rbac._save_role_assignments()
        print("  ✅ Test assignment cleaned up")
    else:
        print("  ℹ️  Nothing to clean up")

    # Clean up temp directory
    import shutil

    try:
        shutil.rmtree(temp_dir)
        print("  ✅ Temp directory cleaned up")
    except Exception as e:
        print(f"  ⚠️  Error cleaning temp directory: {e}")


if __name__ == "__main__":
    result1, rbac, temp_dir = test_manager_initialization()
    if not result1:
        sys.exit(1)

    result2 = test_role_assignment(rbac)
    if not result2:
        cleanup(rbac, temp_dir)
        sys.exit(1)

    result3 = test_permission_validation(rbac)

    cleanup(rbac, temp_dir)

    sys.exit(0 if (result1 and result2 and result3) else 1)
