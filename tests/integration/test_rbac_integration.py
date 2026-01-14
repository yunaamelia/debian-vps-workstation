import pytest

from configurator.rbac.rbac_manager import RBACManager


@pytest.mark.integration
@pytest.mark.parametrize("role_name", ["admin", "devops", "developer", "viewer"])
def test_default_roles_exist(role_name, tmp_path):
    # Mock paths to avoid writing to /etc
    rbac_dir = tmp_path / "rbac"
    rbac_dir.mkdir()

    manager = RBACManager(
        roles_file=rbac_dir / "roles.yaml",
        assignments_file=rbac_dir / "assignments.json",
        audit_log=rbac_dir / "audit.log",
        dry_run=True
    )
    assert manager.get_role(role_name) is not None
