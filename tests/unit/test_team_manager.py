"""Unit tests for team management."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from configurator.users.team_manager import (
    MemberRole,
    ResourceQuota,
    Team,
    TeamManager,
    TeamMember,
)


@pytest.fixture
def temp_paths():
    """Create temporary paths for testing."""
    temp_dir = tempfile.mkdtemp()
    registry = Path(temp_dir) / "teams.json"
    shared_dirs = Path(temp_dir) / "projects"
    audit_log = Path(temp_dir) / "audit.log"

    yield {
        "registry": registry,
        "shared_dirs": shared_dirs,
        "audit_log": audit_log,
    }

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def team_manager(temp_paths):
    """Create team manager with temp paths."""
    return TeamManager(
        registry_file=temp_paths["registry"],
        shared_dirs_base=temp_paths["shared_dirs"],
        audit_log=temp_paths["audit_log"],
    )


def test_team_manager_initialization(team_manager):
    """Test team manager initialization."""
    assert team_manager is not None
    assert len(team_manager.teams) == 0


def test_create_team(team_manager):
    """Test creating a team."""
    team = team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    assert team is not None
    assert team.name == "test-team"
    assert team.description == "Test team"
    assert len(team.members) == 1
    assert team.members[0].username == "testuser"
    assert team.members[0].role == MemberRole.LEAD


def test_create_team_with_quotas(team_manager):
    """Test creating team with resource quotas."""
    team = team_manager.create_team(
        name="quota-team",
        description="Team with quotas",
        lead="testuser",
        disk_quota_gb=50,
        docker_containers=10,
        skip_system_group=True,
    )

    assert team.quotas is not None
    assert team.quotas.disk_quota_gb == 50
    assert team.quotas.docker_containers == 10


def test_create_team_with_permissions(team_manager):
    """Test creating team with permissions."""
    permissions = ["app:backend:*", "db:backend-dev:*"]

    team = team_manager.create_team(
        name="perm-team",
        description="Team with permissions",
        lead="testuser",
        permissions=permissions,
        skip_system_group=True,
    )

    assert team.permissions == permissions


def test_create_duplicate_team(team_manager):
    """Test creating duplicate team fails."""
    team_manager.create_team(
        name="test-team",
        description="First team",
        lead="testuser",
        skip_system_group=True,
    )

    with pytest.raises(ValueError, match="Team already exists"):
        team_manager.create_team(
            name="test-team",
            description="Second team",
            lead="testuser2",
            skip_system_group=True,
        )


def test_shared_directory_created(team_manager, temp_paths):
    """Test shared directory is created."""
    team = team_manager.create_team(
        name="dir-team",
        description="Test directory",
        lead="testuser",
        skip_system_group=True,
    )

    assert team.shared_directory.exists()
    assert team.shared_directory.is_dir()

    # Check README exists
    readme = team.shared_directory / "README.md"
    assert readme.exists()


def test_add_member(team_manager):
    """Test adding member to team."""
    team = team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    success = team_manager.add_member("test-team", "newuser", skip_system=True)

    assert success
    assert len(team.members) == 2

    member = team.get_member("newuser")
    assert member is not None
    assert member.role == MemberRole.MEMBER


def test_add_duplicate_member(team_manager):
    """Test adding duplicate member fails gracefully."""
    team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    # Try to add lead again
    success = team_manager.add_member("test-team", "testuser", skip_system=True)

    assert not success  # Should return False, not raise error


def test_add_member_to_nonexistent_team(team_manager):
    """Test adding member to non-existent team fails."""
    with pytest.raises(ValueError, match="Team not found"):
        team_manager.add_member("nonexistent", "testuser")


def test_remove_member(team_manager):
    """Test removing member from team."""
    team = team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    team_manager.add_member("test-team", "removeme", skip_system=True)

    success = team_manager.remove_member("test-team", "removeme", skip_system=True)

    assert success
    assert len(team.members) == 1
    assert team.get_member("removeme") is None


def test_remove_nonexistent_member(team_manager):
    """Test removing non-existent member fails gracefully."""
    team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    success = team_manager.remove_member("test-team", "nonexistent", skip_system=True)

    assert not success


def test_remove_lead_without_transfer(team_manager):
    """Test removing lead without transfer fails."""
    team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    with pytest.raises(ValueError, match="Must specify new lead"):
        team_manager.remove_member("test-team", "testuser", skip_system=True)


def test_remove_lead_with_transfer(team_manager):
    """Test removing lead with transfer."""
    team = team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="oldlead",
        skip_system_group=True,
    )

    team_manager.add_member("test-team", "newlead", skip_system=True)

    success = team_manager.remove_member(
        "test-team",
        "oldlead",
        transfer_lead="newlead",
        skip_system=True,
    )

    assert success

    new_lead = team.get_lead()
    assert new_lead is not None
    assert new_lead.username == "newlead"


def test_get_team(team_manager):
    """Test getting team by name."""
    team_manager.create_team(
        name="test-team",
        description="Test team",
        lead="testuser",
        skip_system_group=True,
    )

    team = team_manager.get_team("test-team")

    assert team is not None
    assert team.name == "test-team"


def test_get_nonexistent_team(team_manager):
    """Test getting non-existent team returns None."""
    team = team_manager.get_team("nonexistent")

    assert team is None


def test_list_teams(team_manager):
    """Test listing all teams."""
    team_manager.create_team(
        name="team1",
        description="First team",
        lead="user1",
        skip_system_group=True,
    )

    team_manager.create_team(
        name="team2",
        description="Second team",
        lead="user2",
        skip_system_group=True,
    )

    teams = team_manager.list_teams()

    assert len(teams) == 2
    assert any(t.name == "team1" for t in teams)
    assert any(t.name == "team2" for t in teams)


def test_get_user_teams(team_manager):
    """Test getting all teams for a user."""
    team_manager.create_team(
        name="team1",
        description="First team",
        lead="testuser",
        skip_system_group=True,
    )

    team_manager.create_team(
        name="team2",
        description="Second team",
        lead="other",
        skip_system_group=True,
    )

    team_manager.add_member("team2", "testuser", skip_system=True)

    user_teams = team_manager.get_user_teams("testuser")

    assert len(user_teams) == 2
    assert any(t.name == "team1" for t in user_teams)
    assert any(t.name == "team2" for t in user_teams)


def test_team_persistence(team_manager, temp_paths):
    """Test teams persist to registry."""
    team_manager.create_team(
        name="persist-team",
        description="Test persistence",
        lead="testuser",
        skip_system_group=True,
    )

    # Create new manager instance
    new_manager = TeamManager(
        registry_file=temp_paths["registry"],
        shared_dirs_base=temp_paths["shared_dirs"],
        audit_log=temp_paths["audit_log"],
    )

    # Should load from registry
    team = new_manager.get_team("persist-team")

    assert team is not None
    assert team.name == "persist-team"


def test_delete_team(team_manager):
    """Test deleting a team."""
    team_manager.create_team(
        name="delete-team",
        description="To be deleted",
        lead="testuser",
        skip_system_group=True,
    )

    success = team_manager.delete_team("delete-team", skip_system=True)

    assert success
    assert team_manager.get_team("delete-team") is None


def test_team_member_dataclass():
    """Test TeamMember dataclass."""
    member = TeamMember(
        username="testuser",
        role=MemberRole.LEAD,
        joined_at=datetime(2025, 10, 15),
    )

    data = member.to_dict()

    assert data["username"] == "testuser"
    assert data["role"] == "lead"
    assert data["joined_at"] == "2025-10-15T00:00:00"


def test_resource_quota_dataclass():
    """Test ResourceQuota dataclass."""
    quota = ResourceQuota(
        disk_quota_gb=50,
        docker_containers=10,
    )

    data = quota.to_dict()

    assert data["disk_quota_gb"] == 50
    assert data["docker_containers"] == 10


def test_team_dataclass():
    """Test Team dataclass."""
    team = Team(
        team_id="team-001",
        name="test-team",
        description="Test team",
        gid=1001,
        shared_directory=Path("/var/projects/test-team"),
        members=[
            TeamMember("user1", MemberRole.LEAD),
            TeamMember("user2", MemberRole.MEMBER),
        ],
        quotas=ResourceQuota(disk_quota_gb=50),
    )

    # Test get_lead
    lead = team.get_lead()
    assert lead is not None
    assert lead.username == "user1"

    # Test get_member
    member = team.get_member("user2")
    assert member is not None
    assert member.role == MemberRole.MEMBER

    # Test to_dict
    data = team.to_dict()
    assert data["name"] == "test-team"
    assert len(data["members"]) == 2


def test_audit_log_created(team_manager, temp_paths):
    """Test audit log is created."""
    team_manager.create_team(
        name="audit-team",
        description="Test audit",
        lead="testuser",
        skip_system_group=True,
    )

    assert temp_paths["audit_log"].exists()

    # Check content
    with open(temp_paths["audit_log"], "r") as f:
        content = f.read()

    assert "create_team" in content
    assert "audit-team" in content
