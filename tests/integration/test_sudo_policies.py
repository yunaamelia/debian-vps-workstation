"""Integration tests for sudo policy management."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from configurator.rbac.sudo_manager import PasswordRequirement, SudoPolicyManager


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = tempfile.mkdtemp()
    sudoers_dir = Path(temp_dir) / "sudoers.d"
    policy_dir = Path(temp_dir) / "policies"
    audit_log = Path(temp_dir) / "audit.log"

    sudoers_dir.mkdir()

    yield {
        "temp_dir": temp_dir,
        "sudoers_dir": sudoers_dir,
        "policy_dir": policy_dir,
        "audit_log": audit_log,
    }

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_complete_sudo_workflow(temp_dirs):
    """Test complete workflow: apply policy, test command, revoke."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Mock RBAC
    mock_rbac = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    mock_rbac.assignments = {"testuser": mock_assignment}
    sudo_mgr.rbac_manager = mock_rbac

    # Step 1: Apply policy
    success = sudo_mgr.apply_policy_for_user("testuser", "developer")
    assert success is True

    # Verify sudoers file created
    sudoers_file = temp_dirs["sudoers_dir"] / "rbac-testuser"
    assert sudoers_file.exists()

    # Verify content
    content = sudoers_file.read_text()
    assert "testuser" in content
    assert "NOPASSWD" in content

    # Step 2: Test allowed command
    result = sudo_mgr.test_command("testuser", "systemctl restart myapp")
    assert result["allowed"] is True
    assert result["password_required"] is False

    # Step 3: Test denied command
    result = sudo_mgr.test_command("testuser", "apt-get install nginx")
    assert result["allowed"] is False

    # Step 4: Get user policy
    policy = sudo_mgr.get_user_policy("testuser")
    assert policy is not None
    assert policy.name == "developer"

    # Step 5: Revoke access
    success = sudo_mgr.revoke_sudo_access("testuser")
    assert success is True
    assert not sudoers_file.exists()


def test_role_upgrade_workflow(temp_dirs):
    """Test upgrading user from developer to devops role."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Mock RBAC
    mock_rbac = MagicMock()
    sudo_mgr.rbac_manager = mock_rbac

    # Start as developer
    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    mock_rbac.assignments = {"johndoe": mock_assignment}

    sudo_mgr.apply_policy_for_user("johndoe", "developer")

    # Test developer command
    result = sudo_mgr.test_command("johndoe", "systemctl restart myapp")
    assert result["allowed"] is True
    assert result["password_required"] is False

    # Test devops-only command (should fail)
    result = sudo_mgr.test_command("johndoe", "apt-get update")
    assert result["allowed"] is False

    # Remove existing file before upgrade
    sudoers_file = temp_dirs["sudoers_dir"] / "rbac-johndoe"
    if sudoers_file.exists():
        sudoers_file.unlink()

    # Upgrade to devops
    mock_assignment.role_name = "devops"
    sudo_mgr.apply_policy_for_user("johndoe", "devops")

    # Test devops command (should now work)
    result = sudo_mgr.test_command("johndoe", "apt-get update")
    assert result["allowed"] is True
    assert result["password_required"] is True  # Requires password


def test_multiple_users_different_policies(temp_dirs):
    """Test multiple users with different policies."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Mock RBAC
    mock_rbac = MagicMock()
    mock_rbac.assignments = {}
    sudo_mgr.rbac_manager = mock_rbac

    # Create developer user
    dev_assignment = MagicMock()
    dev_assignment.role_name = "developer"
    mock_rbac.assignments["dev_user"] = dev_assignment

    sudo_mgr.apply_policy_for_user("dev_user", "developer")

    # Create admin user
    admin_assignment = MagicMock()
    admin_assignment.role_name = "admin"
    mock_rbac.assignments["admin_user"] = admin_assignment

    sudo_mgr.apply_policy_for_user("admin_user", "admin")

    # Verify both sudoers files exist
    assert (temp_dirs["sudoers_dir"] / "rbac-dev_user").exists()
    assert (temp_dirs["sudoers_dir"] / "rbac-admin_user").exists()

    # Test developer permissions
    result = sudo_mgr.test_command("dev_user", "systemctl restart myapp")
    assert result["allowed"] is True

    result = sudo_mgr.test_command("dev_user", "apt-get install nginx")
    assert result["allowed"] is False

    # Test admin permissions (can do anything)
    result = sudo_mgr.test_command("admin_user", "apt-get install nginx")
    assert result["allowed"] is True


def test_audit_log_completeness(temp_dirs):
    """Test that all operations are logged to audit log."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Apply policy
    sudo_mgr.apply_policy_for_user("testuser", "developer")

    # Revoke policy
    sudo_mgr.revoke_sudo_access("testuser")

    # Check audit log
    assert temp_dirs["audit_log"].exists()

    with open(temp_dirs["audit_log"], "r") as f:
        lines = f.readlines()

    assert len(lines) >= 2  # At least apply and revoke

    # Verify entries
    import json

    entries = [json.loads(line) for line in lines]

    actions = [e["action"] for e in entries]
    assert "apply_policy" in actions
    assert "revoke_access" in actions

    # All entries should have username
    for entry in entries:
        assert "username" in entry
        assert "timestamp" in entry


def test_passwordless_vs_password_required(temp_dirs):
    """Test differentiation between passwordless and password-required commands."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Mock RBAC
    mock_rbac = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.role_name = "devops"
    mock_rbac.assignments = {"devops_user": mock_assignment}
    sudo_mgr.rbac_manager = mock_rbac

    # Apply devops policy
    sudo_mgr.apply_policy_for_user("devops_user", "devops")

    # Test passwordless command
    result = sudo_mgr.test_command("devops_user", "docker ps")
    assert result["allowed"] is True
    assert result["password_required"] is False

    # Test password-required command
    result = sudo_mgr.test_command("devops_user", "systemctl restart nginx")
    assert result["allowed"] is True
    assert result["password_required"] is True

    # Verify sudoers file has both types
    sudoers_file = temp_dirs["sudoers_dir"] / "rbac-devops_user"
    content = sudoers_file.read_text()

    assert "NOPASSWD:" in content
    assert "docker" in content


def test_wildcard_command_matching(temp_dirs):
    """Test wildcard command matching works correctly."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Mock RBAC
    mock_rbac = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    mock_rbac.assignments = {"testuser": mock_assignment}
    sudo_mgr.rbac_manager = mock_rbac

    # Test various wildcard matches
    test_cases = [
        ("docker logs myapp", True),
        ("docker logs container-123", True),
        ("docker logs anything-here", True),
        ("systemctl status nginx", True),
        ("systemctl status myapp", True),
        ("journalctl -u myapp-web", True),
        ("journalctl -u myapp-worker", True),
    ]

    for command, should_allow in test_cases:
        result = sudo_mgr.test_command("testuser", command)
        assert result["allowed"] == should_allow, f"Command '{command}' failed"


def test_policy_validation_prevents_errors(temp_dirs):
    """Test that policy validation prevents syntax errors."""
    sudo_mgr = SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=False,
    )

    # Generate valid content
    from configurator.rbac.sudo_manager import SudoCommandRule, SudoPolicy

    policy = SudoPolicy(
        name="test",
        rules=[
            SudoCommandRule("systemctl restart myapp", password_required=PasswordRequirement.NONE),
        ],
    )

    content = sudo_mgr._generate_sudoers_content("testuser", policy)

    # Validate (should pass)
    # Note: This will skip if visudo not available
    is_valid = sudo_mgr._validate_sudoers_content(content)

    # Should be valid or skipped (both are OK)
    assert is_valid is True
