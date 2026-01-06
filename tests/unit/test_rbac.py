import json
from pathlib import Path

import yaml

from configurator.rbac.rbac_manager import Permission, RBACManager, Role


def test_permission_matching_wildcards():
    granted = Permission("app:*:deploy")
    required_exact = Permission("app:myapp:deploy")
    required_other = Permission("db:prod:read")

    assert granted.matches(required_exact)
    assert not granted.matches(required_other)


def test_role_inheritance_combines_permissions():
    base = Role(name="base", description="base", permissions=[Permission("app:foo:read")])
    child = Role(
        name="child",
        description="child",
        permissions=[Permission("app:bar:write")],
        inherits_from=["base"],
    )

    registry = {"base": base, "child": child}
    perms = child.get_all_permissions(registry)
    rendered = {str(p) for p in perms}
    assert "app:foo:read" in rendered
    assert "app:bar:write" in rendered


def test_rbac_assignment_and_check(tmp_path: Path):
    roles_file = tmp_path / "roles.yaml"
    assignments_file = tmp_path / "assignments.json"
    role_def = {
        "developer": {
            "description": "dev",
            "permissions": ["app:*:deploy", "db:dev:read"],
            "sudo_access": "none",
            "sudo_commands": [],
            "system_groups": [],
        }
    }
    roles_file.write_text(yaml.safe_dump(role_def, sort_keys=False))

    manager = RBACManager(
        roles_file=roles_file,
        assignments_file=assignments_file,
        dry_run=True,
    )

    manager.assign_role("alice", "developer", assigned_by="test")

    assert manager.check_permission("alice", "app:demo:deploy")
    assert not manager.check_permission("alice", "db:prod:write")

    # Ensure assignments persisted
    data = json.loads(assignments_file.read_text())
    assert "alice" in data
