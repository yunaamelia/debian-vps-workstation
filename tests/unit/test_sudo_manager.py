"""Unit tests for sudo policy manager."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from configurator.rbac.sudo_manager import (
    PasswordRequirement,
    SudoCommandRule,
    SudoPolicy,
    SudoPolicyManager,
)


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


@pytest.fixture
def sudo_manager(temp_dirs):
    """Create sudo policy manager with temp directories."""
    return SudoPolicyManager(
        sudoers_dir=temp_dirs["sudoers_dir"],
        policy_dir=temp_dirs["policy_dir"],
        audit_log=temp_dirs["audit_log"],
        dry_run=True,
    )


def test_command_rule_matching():
    """Test command pattern matching."""
    rule = SudoCommandRule(
        command_pattern="systemctl restart myapp",
        password_required=PasswordRequirement.NONE,
    )

    # Exact match
    assert rule.matches_command("systemctl restart myapp")

    # No match
    assert not rule.matches_command("systemctl restart other")
    assert not rule.matches_command("systemctl stop myapp")


def test_command_rule_wildcard_matching():
    """Test wildcard pattern matching."""
    rule = SudoCommandRule(
        command_pattern="docker logs *",
        password_required=PasswordRequirement.NONE,
    )

    # Wildcard matches
    assert rule.matches_command("docker logs myapp")
    assert rule.matches_command("docker logs container-123")
    assert rule.matches_command("docker logs anything")

    # No match
    assert not rule.matches_command("docker ps")
    assert not rule.matches_command("docker inspect myapp")


def test_command_rule_time_restrictions():
    """Test time-based restrictions."""
    from datetime import datetime

    # Allow only during business hours
    rule = SudoCommandRule(
        command_pattern="apt-get upgrade",
        allowed_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17],  # 9 AM - 5 PM
    )

    # Mock current time
    with patch("configurator.rbac.sudo_manager.datetime") as mock_dt:
        # During allowed hours
        mock_dt.now.return_value = datetime(2026, 1, 6, 10, 0)  # 10 AM
        assert rule.is_allowed_now()

        # Outside allowed hours
        mock_dt.now.return_value = datetime(2026, 1, 6, 20, 0)  # 8 PM
        assert not rule.is_allowed_now()


def test_sudo_policy_find_matching_rule():
    """Test finding matching rule in policy."""
    policy = SudoPolicy(
        name="test",
        rules=[
            SudoCommandRule("systemctl restart myapp", PasswordRequirement.NONE),
            SudoCommandRule("systemctl stop *", PasswordRequirement.REQUIRED),
            SudoCommandRule("docker *", PasswordRequirement.NONE),
        ],
    )

    # Find exact match
    rule = policy.find_matching_rule("systemctl restart myapp")
    assert rule is not None
    assert rule.command_pattern == "systemctl restart myapp"

    # Find wildcard match
    rule = policy.find_matching_rule("systemctl stop nginx")
    assert rule is not None
    assert rule.command_pattern == "systemctl stop *"

    # Find broad wildcard
    rule = policy.find_matching_rule("docker ps")
    assert rule is not None
    assert rule.command_pattern == "docker *"

    # No match
    rule = policy.find_matching_rule("apt-get update")
    assert rule is None


def test_sudo_policy_command_allowed():
    """Test policy command allowance."""
    policy = SudoPolicy(
        name="test",
        rules=[
            SudoCommandRule("systemctl restart myapp", PasswordRequirement.NONE),
        ],
        default_deny=True,
    )

    # Allowed by rule
    assert policy.is_command_allowed("systemctl restart myapp")

    # Denied by default
    assert not policy.is_command_allowed("systemctl stop nginx")


def test_sudo_manager_initialization(sudo_manager):
    """Test sudo manager initialization."""
    assert sudo_manager is not None
    assert "developer" in sudo_manager.policies
    assert "devops" in sudo_manager.policies
    assert "admin" in sudo_manager.policies
    assert "viewer" in sudo_manager.policies


def test_default_policies_loaded(sudo_manager):
    """Test that default policies are loaded."""
    # Developer policy
    dev_policy = sudo_manager.policies["developer"]
    assert dev_policy is not None
    assert len(dev_policy.rules) > 0
    assert dev_policy.default_deny is True

    # Admin policy
    admin_policy = sudo_manager.policies["admin"]
    assert admin_policy is not None
    assert len(admin_policy.rules) > 0

    # Viewer policy (no sudo)
    viewer_policy = sudo_manager.policies["viewer"]
    assert viewer_policy is not None
    assert len(viewer_policy.rules) == 0


def test_generate_sudoers_content(sudo_manager):
    """Test sudoers file content generation."""
    policy = SudoPolicy(
        name="test",
        rules=[
            SudoCommandRule(
                "systemctl restart myapp",
                password_required=PasswordRequirement.NONE,
                description="Restart app",
            ),
            SudoCommandRule(
                "systemctl stop *",
                password_required=PasswordRequirement.REQUIRED,
                description="Stop services",
            ),
        ],
    )

    content = sudo_manager._generate_sudoers_content("testuser", policy)

    assert "testuser" in content
    assert "NOPASSWD: systemctl restart myapp" in content
    assert "testuser ALL=(ALL) systemctl stop *" in content
    assert "Restart app" in content
    assert "Stop services" in content


def test_apply_policy_for_user(sudo_manager):
    """Test applying policy for user."""
    # Apply developer policy
    success = sudo_manager.apply_policy_for_user("testuser", "developer")

    assert success is True

    # In dry run, file won't be created
    if not sudo_manager.dry_run:
        sudoers_file = sudo_manager.SUDOERS_DIR / "rbac-testuser"
        assert sudoers_file.exists()


def test_apply_policy_unknown_role(sudo_manager):
    """Test applying policy for unknown role."""
    success = sudo_manager.apply_policy_for_user("testuser", "unknown_role")

    # Should still succeed but with empty policy
    assert success is True


def test_test_command_with_rbac(sudo_manager):
    """Test command testing with RBAC integration."""
    # Mock RBAC manager
    mock_rbac = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    mock_rbac.assignments = {"testuser": mock_assignment}

    sudo_manager.rbac_manager = mock_rbac

    # Test allowed command
    result = sudo_manager.test_command("testuser", "systemctl restart myapp")

    assert result["allowed"] is True
    assert result["password_required"] is False

    # Test denied command
    result = sudo_manager.test_command("testuser", "apt-get install nginx")

    assert result["allowed"] is False
    assert "not in whitelist" in result["reason"]


def test_test_command_no_rbac(sudo_manager):
    """Test command testing without RBAC."""
    sudo_manager.rbac_manager = None

    result = sudo_manager.test_command("testuser", "systemctl restart myapp")

    assert result["allowed"] is False
    assert "RBAC manager not available" in result["reason"]


def test_get_user_policy(sudo_manager):
    """Test getting user policy."""
    # Mock RBAC manager
    mock_rbac = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    mock_rbac.assignments = {"testuser": mock_assignment}

    sudo_manager.rbac_manager = mock_rbac

    policy = sudo_manager.get_user_policy("testuser")

    assert policy is not None
    assert policy.name == "developer"


def test_revoke_sudo_access(sudo_manager):
    """Test revoking sudo access."""
    # First apply policy
    sudo_manager.apply_policy_for_user("testuser", "developer")

    # Then revoke
    success = sudo_manager.revoke_sudo_access("testuser")

    assert success is True


def test_audit_logging(sudo_manager):
    """Test audit logging."""
    sudo_manager._audit_log(
        action="test_action",
        username="testuser",
        role="developer",
    )

    assert sudo_manager.AUDIT_LOG.exists()

    with open(sudo_manager.AUDIT_LOG, "r") as f:
        content = f.read()

    assert "test_action" in content
    assert "testuser" in content


def test_developer_policy_commands():
    """Test specific commands in developer policy."""
    manager = SudoPolicyManager(dry_run=True)

    dev_policy = manager.policies["developer"]

    # Should allow
    assert dev_policy.find_matching_rule("systemctl restart myapp") is not None
    assert dev_policy.find_matching_rule("systemctl status nginx") is not None
    assert dev_policy.find_matching_rule("docker ps") is not None
    assert dev_policy.find_matching_rule("docker logs myapp") is not None

    # Should not allow
    assert dev_policy.find_matching_rule("apt-get install nginx") is None
    assert dev_policy.find_matching_rule("iptables -A INPUT") is None


def test_devops_policy_commands():
    """Test specific commands in devops policy."""
    manager = SudoPolicyManager(dry_run=True)

    devops_policy = manager.policies["devops"]

    # Should allow (passwordless)
    assert devops_policy.find_matching_rule("docker ps") is not None

    # Should allow (password required)
    rule = devops_policy.find_matching_rule("systemctl restart nginx")
    assert rule is not None
    assert rule.password_required == PasswordRequirement.REQUIRED

    rule = devops_policy.find_matching_rule("apt-get upgrade")
    assert rule is not None
    assert rule.password_required == PasswordRequirement.REQUIRED


def test_admin_policy_full_access():
    """Test admin policy allows everything."""
    manager = SudoPolicyManager(dry_run=True)

    admin_policy = manager.policies["admin"]

    # Should allow any command
    assert admin_policy.find_matching_rule("apt-get install anything") is not None
    assert admin_policy.find_matching_rule("rm -rf /") is not None
    assert admin_policy.find_matching_rule("iptables -F") is not None
