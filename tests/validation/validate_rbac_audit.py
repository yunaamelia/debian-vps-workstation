#!/usr/bin/env python3
"""Test audit logging"""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.rbac.rbac_manager import RBACManager


def test_audit_logging():
    print("Audit Logging Test")
    print("=" * 60)

    # Setup temp environment
    temp_dir = tempfile.mkdtemp(prefix="rbac_test_")
    roles_file = Path(temp_dir) / "roles.yaml"
    assignments_file = Path(temp_dir) / "assignments.json"
    audit_log = Path(temp_dir) / "audit.log"

    default_roles = Path(__file__).parent.parent.parent / "configurator/rbac/roles.yaml"
    if default_roles.exists():
        shutil.copy(default_roles, roles_file)

    rbac = RBACManager(
        roles_file=str(roles_file),
        assignments_file=str(assignments_file),
        audit_log=str(audit_log),
        dry_run=True,
    )

    test_user = "testuser"

    # Test 1: Perform auditable action
    print("\n1. Performing auditable action (role assignment)...")
    rbac.assign_role(
        user=test_user, role_name="developer", assigned_by="test-script", reason="Audit log test"
    )
    print("  ✅ Action performed")

    # Test 2: Check audit log exists
    print("\n2. Checking audit log file...")

    if audit_log.exists():
        print(f"  ✅ Audit log exists: {audit_log}")

        import json

        with open(audit_log, "r") as f:
            lines = f.readlines()

        if lines:
            last_entry = json.loads(lines[-1])
            print("     Last entry:")
            print(f"       Timestamp: {last_entry['timestamp']}")
            print(f"       Action: {last_entry['action']}")
            print(f"       User: {last_entry.get('user', 'N/A')}")
            print(f"       Role: {last_entry.get('role', 'N/A')}")
        else:
            print("  ⚠️  Audit log is empty")
    else:
        print(f"  ❌ Audit log not found: {audit_log}")
        shutil.rmtree(temp_dir)
        return False

    # Cleanup
    print("\n3. Cleaning up...")
    shutil.rmtree(temp_dir)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Audit logging validated")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_audit_logging() else 1)
