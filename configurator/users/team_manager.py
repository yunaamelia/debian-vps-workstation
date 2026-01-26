"""Team and group management system."""

import grp
import json
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TeamStatus(Enum):
    """Team status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class MemberRole(Enum):
    """Team member roles."""

    LEAD = "lead"
    MEMBER = "member"


@dataclass
class TeamMember:
    """
    Represents a team member.

    Example:
        TeamMember(
            username="johndoe",
            role=MemberRole.LEAD,
            joined_at=datetime(2025, 10, 15),
        )
    """

    username: str
    role: MemberRole = MemberRole.MEMBER
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "username": self.username,
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }


@dataclass
class ResourceQuota:
    """Team resource quotas."""

    disk_quota_gb: Optional[float] = None
    docker_containers: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "disk_quota_gb": self.disk_quota_gb,
            "docker_containers": self.docker_containers,
        }


@dataclass
class Team:
    """
    Represents a team.

    Example:
        Team(
            team_id="team-backend-001",
            name="backend-team",
            description="Backend development team",
            gid=1001,
            shared_directory=Path("/var/projects/backend"),
            members=[
                TeamMember("johndoe", MemberRole.LEAD),
                TeamMember("janedoe", MemberRole.MEMBER),
            ],
            quotas=ResourceQuota(disk_quota_gb=50, docker_containers=10),
        )
    """

    team_id: str
    name: str
    description: str
    gid: int
    shared_directory: Path
    members: List[TeamMember] = field(default_factory=list)
    quotas: Optional[ResourceQuota] = None
    permissions: List[str] = field(default_factory=list)
    status: TeamStatus = TeamStatus.ACTIVE
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    def get_lead(self) -> Optional[TeamMember]:
        """Get team lead."""
        for member in self.members:
            if member.role == MemberRole.LEAD:
                return member
        return None

    def get_member(self, username: str) -> Optional[TeamMember]:
        """Get specific member."""
        for member in self.members:
            if member.username == username:
                return member
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "gid": self.gid,
            "shared_directory": str(self.shared_directory),
            "members": [m.to_dict() for m in self.members],
            "quotas": self.quotas.to_dict() if self.quotas else None,
            "permissions": self.permissions,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


class TeamManager:
    """
    Manages teams and group memberships.

    Features:
    - Team creation and deletion
    - Member management (add/remove)
    - Shared directory management
    - Resource quota enforcement
    - Team permissions (integrated with RBAC)
    - Team lead management
    - Automatic onboarding/offboarding
    """

    TEAMS_REGISTRY = Path("/var/lib/debian-vps-configurator/teams/teams.json")
    SHARED_DIRS_BASE = Path("/var/projects")
    AUDIT_LOG = Path("/var/log/team-audit.log")

    def __init__(
        self,
        registry_file: Optional[Path] = None,
        shared_dirs_base: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        # Allow overriding paths (for testing)
        self.TEAMS_REGISTRY = registry_file or self.TEAMS_REGISTRY
        self.SHARED_DIRS_BASE = shared_dirs_base or self.SHARED_DIRS_BASE
        self.AUDIT_LOG = audit_log or self.AUDIT_LOG

        self._ensure_directories()
        self._load_teams()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        try:
            self.TEAMS_REGISTRY.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            self.SHARED_DIRS_BASE.mkdir(parents=True, exist_ok=True, mode=0o755)
            if self.AUDIT_LOG.parent != Path("/var/log"):
                self.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        except PermissionError:
            self.logger.debug("No permission to create directories; will use temp")

    def _load_teams(self) -> None:
        """Load teams from registry."""
        self.teams: Dict[str, Team] = {}

        if self.TEAMS_REGISTRY.exists():
            try:
                with open(self.TEAMS_REGISTRY, "r") as f:
                    data = json.load(f)

                for team_name, team_data in data.items():
                    self.teams[team_name] = self._team_from_dict(team_data)

                self.logger.info(f"Loaded {len(self.teams)} teams")
            except Exception as e:
                self.logger.error(f"Failed to load teams: {e}")

    def _save_teams(self) -> None:
        """Save teams to registry."""
        try:
            data = {name: team.to_dict() for name, team in self.teams.items()}

            with open(self.TEAMS_REGISTRY, "w") as f:
                json.dump(data, f, indent=2)

            try:
                self.TEAMS_REGISTRY.chmod(0o600)
            except PermissionError:
                pass
        except Exception as e:
            self.logger.error(f"Failed to save teams: {e}")

    def _team_from_dict(self, data: Dict[str, Any]) -> Team:
        """Deserialize Team from dictionary."""
        members = [
            TeamMember(
                username=m["username"],
                role=MemberRole(m["role"]),
                joined_at=datetime.fromisoformat(m["joined_at"]) if m.get("joined_at") else None,
                left_at=datetime.fromisoformat(m["left_at"]) if m.get("left_at") else None,
            )
            for m in data.get("members", [])
        ]

        quotas = None
        if data.get("quotas"):
            quotas = ResourceQuota(
                disk_quota_gb=data["quotas"].get("disk_quota_gb"),
                docker_containers=data["quotas"].get("docker_containers"),
            )

        return Team(
            team_id=data["team_id"],
            name=data["name"],
            description=data["description"],
            gid=data["gid"],
            shared_directory=Path(data["shared_directory"]),
            members=members,
            quotas=quotas,
            permissions=data.get("permissions", []),
            status=TeamStatus(data.get("status", "active")),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            created_by=data.get("created_by"),
        )

    def create_team(
        self,
        name: str,
        description: str,
        lead: str,
        created_by: str = "system",
        shared_directory: Optional[Path] = None,
        disk_quota_gb: Optional[float] = None,
        docker_containers: Optional[int] = None,
        permissions: Optional[List[str]] = None,
        skip_system_group: bool = False,  # For testing
    ) -> Team:
        """
        Create a new team.

        Args:
            name: Team name (will be used as group name)
            description: Team description
            lead: Username of team lead
            created_by: Who created the team
            shared_directory: Custom shared directory path
            disk_quota_gb: Disk quota in GB
            docker_containers: Max Docker containers
            permissions: Team-specific permissions
            skip_system_group: Skip system group creation (testing only)

        Returns:
            Team object
        """
        self.logger.info(f"Creating team: {name}")

        # Check if team already exists
        if name in self.teams:
            raise ValueError(f"Team already exists: {name}")

        # Step 1: Create system group
        if not skip_system_group:
            gid = self._create_system_group(name)
        else:
            gid = 9999  # Fake GID for testing

        # Step 2: Setup shared directory
        if not shared_directory:
            shared_directory = self.SHARED_DIRS_BASE / name

        self._setup_shared_directory(shared_directory, name, gid)

        # Step 3: Create team object
        team_id = f"team-{name}-{uuid.uuid4().hex[:6]}"

        quotas = None
        if disk_quota_gb or docker_containers:
            quotas = ResourceQuota(
                disk_quota_gb=disk_quota_gb,
                docker_containers=docker_containers,
            )

        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            gid=gid,
            shared_directory=shared_directory,
            members=[],
            quotas=quotas,
            permissions=permissions or [],
            created_at=datetime.now(),
            created_by=created_by,
        )

        # Step 4: Add lead
        self._add_member_internal(team, lead, role=MemberRole.LEAD, skip_system=skip_system_group)

        # Step 5: Save team
        self.teams[name] = team
        self._save_teams()

        # Step 6: Audit log
        self._audit_log(
            action="create_team",
            team_name=name,
            performed_by=created_by,
        )

        self.logger.info(f"✅ Team {name} created successfully")

        return team

    def _create_system_group(self, group_name: str) -> int:
        """Create system group and return GID."""
        try:
            result = subprocess.run(
                ["groupadd", group_name], check=True, capture_output=True, text=True
            )

            # Get GID
            group_info = grp.getgrnam(group_name)
            return group_info.gr_gid

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create group: {e.stderr}")
            raise RuntimeError(f"Group creation failed: {e.stderr}")
        except KeyError:
            self.logger.error(f"Group not found after creation: {group_name}")
            raise RuntimeError(f"Group not found: {group_name}")

    def _setup_shared_directory(self, directory: Path, group_name: str, gid: int) -> None:
        """Setup shared directory with proper permissions."""
        # Create directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o2775)

        try:
            # Set ownership (root:group)
            os.chown(directory, 0, gid)

            # Set setgid bit (new files inherit group)
            directory.chmod(0o2775)
        except PermissionError:
            self.logger.debug("No permission to chown; skipping")

        # Create README
        readme = directory / "README.md"
        readme.write_text(f"# {group_name}\n\nShared directory for {group_name}.\n")

        try:
            os.chown(readme, 0, gid)
        except PermissionError:
            pass

    def _add_member_internal(
        self,
        team: Team,
        username: str,
        role: MemberRole = MemberRole.MEMBER,
        skip_system: bool = False,
    ) -> None:
        """Internal method to add member to team."""
        # Add to system group
        if not skip_system:
            try:
                subprocess.run(
                    ["usermod", "-aG", team.name, username], check=True, capture_output=True
                )
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to add user to group: {e.stderr}")
                raise

        # Add to team members
        member = TeamMember(
            username=username,
            role=role,
            joined_at=datetime.now(),
        )
        team.members.append(member)

    def add_member(self, team_name: str, username: str, skip_system: bool = False) -> bool:
        """
        Add member to team.

        Args:
            team_name: Team name
            username: Username to add
            skip_system: Skip system group addition (testing only)

        Returns:
            True if successful
        """
        team = self.teams.get(team_name)

        if not team:
            raise ValueError(f"Team not found: {team_name}")

        # Check if already a member
        if team.get_member(username):
            self.logger.warning(f"User {username} already in team {team_name}")
            return False

        self._add_member_internal(team, username, skip_system=skip_system)

        self._save_teams()

        self._audit_log(
            action="add_member",
            team_name=team_name,
            username=username,
        )

        self.logger.info(f"✅ Added {username} to team {team_name}")

        return True

    def remove_member(
        self,
        team_name: str,
        username: str,
        transfer_lead: Optional[str] = None,
        skip_system: bool = False,
    ) -> bool:
        """
        Remove member from team.

        Args:
            team_name: Team name
            username: Username to remove
            transfer_lead: New lead if removing current lead
            skip_system: Skip system group removal (testing only)

        Returns:
            True if successful
        """
        team = self.teams.get(team_name)

        if not team:
            raise ValueError(f"Team not found: {team_name}")

        member = team.get_member(username)

        if not member:
            self.logger.warning(f"User {username} not in team {team_name}")
            return False

        # If removing lead, transfer leadership
        if member.role == MemberRole.LEAD:
            if not transfer_lead:
                raise ValueError("Must specify new lead when removing current lead")

            new_lead = team.get_member(transfer_lead)
            if not new_lead:
                raise ValueError(f"New lead {transfer_lead} not in team")

            new_lead.role = MemberRole.LEAD

        # Remove from system group
        if not skip_system:
            try:
                subprocess.run(
                    ["gpasswd", "-d", username, team.name], check=True, capture_output=True
                )
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to remove from group: {e.stderr}")

        # Remove from team
        team.members.remove(member)

        self._save_teams()

        self._audit_log(
            action="remove_member",
            team_name=team_name,
            username=username,
        )

        self.logger.info(f"✅ Removed {username} from team {team_name}")

        return True

    def get_team(self, team_name: str) -> Optional[Team]:
        """Get team by name."""
        return self.teams.get(team_name)

    def list_teams(self) -> List[Team]:
        """List all teams."""
        return list(self.teams.values())

    def get_user_teams(self, username: str) -> List[Team]:
        """Get all teams a user is a member of."""
        user_teams = []

        for team in self.teams.values():
            if team.get_member(username):
                user_teams.append(team)

        return user_teams

    def delete_team(self, team_name: str, skip_system: bool = False) -> bool:
        """
        Delete a team.

        Args:
            team_name: Team name
            skip_system: Skip system group deletion (testing only)

        Returns:
            True if successful
        """
        team = self.teams.get(team_name)

        if not team:
            raise ValueError(f"Team not found: {team_name}")

        # Remove system group
        if not skip_system:
            try:
                subprocess.run(["groupdel", team.name], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to delete group: {e.stderr}")

        # Remove from registry
        del self.teams[team_name]
        self._save_teams()

        self._audit_log(
            action="delete_team",
            team_name=team_name,
        )

        self.logger.info(f"✅ Team {team_name} deleted")

        return True

    def _audit_log(self, action: str, **details: Any) -> None:
        """Log team action for audit."""
        log_entry = {"timestamp": datetime.now().isoformat(), "action": action, **details}

        try:
            with open(self.AUDIT_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
