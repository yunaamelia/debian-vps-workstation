"""
RBAC (Role-Based Access Control) module.

Handles creation and management of users with predefined roles:
- admin: Full system access (sudo, docker, all tools)
- developer: Development access (docker, git, editors)
- viewer: Read-only access (view logs, status)
"""

import secrets
import string
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.modules.base import ConfigurationModule


@dataclass
class UserRole:
    """Definition of a user role."""

    name: str
    description: str
    groups: List[str]
    sudo_access: bool = False
    sudo_nopasswd: bool = False
    shell: str = "/bin/bash"
    home_skeleton: Optional[str] = None


# Predefined roles
ROLES: Dict[str, UserRole] = {
    "admin": UserRole(
        name="admin",
        description="Full system administrator access",
        groups=["sudo", "docker", "adm", "systemd-journal"],
        sudo_access=True,
        sudo_nopasswd=False,
    ),
    "developer": UserRole(
        name="developer",
        description="Development environment access",
        groups=["docker", "www-data"],
        sudo_access=False,
        sudo_nopasswd=False,
    ),
    "viewer": UserRole(
        name="viewer",
        description="Read-only monitoring access",
        groups=["systemd-journal", "adm"],
        sudo_access=False,
        sudo_nopasswd=False,
        shell="/bin/rbash",  # Restricted bash
    ),
}


@dataclass
class ManagedUser:
    """A user managed by RBAC."""

    username: str
    role: str
    ssh_keys: List[str] = field(default_factory=list)
    full_name: str = ""
    email: str = ""
    enabled: bool = True


class RBACModule(ConfigurationModule):
    """
    Role-Based Access Control module.

    Creates and manages users with predefined roles.
    """

    name = "User Management"
    description = "RBAC and user configuration"
    depends_on = ["system", "security"]
    priority = 25  # After security, before desktop
    mandatory = False

    def __init__(self, config: Dict[str, Any], *args: Any, **kwargs: Any):
        super().__init__(config, *args, **kwargs)
        self.users: List[ManagedUser] = []
        self._parse_users()

    def _parse_users(self) -> None:
        """Parse users from configuration."""
        users_config = self.get_config("users", [])

        for user_cfg in users_config:
            user = ManagedUser(
                username=user_cfg.get("username"),
                role=user_cfg.get("role", "developer"),
                ssh_keys=user_cfg.get("ssh_keys", []),
                full_name=user_cfg.get("full_name", ""),
                email=user_cfg.get("email", ""),
                enabled=user_cfg.get("enabled", True),
            )
            if user.username:
                self.users.append(user)

    def validate(self) -> bool:
        """Validate RBAC configuration."""
        # Check that all roles are valid
        for user in self.users:
            if user.role not in ROLES:
                self.logger.error(f"Unknown role '{user.role}' for user '{user.username}'")
                return False

        # Check for duplicate usernames
        usernames = [u.username for u in self.users]
        if len(usernames) != len(set(usernames)):
            self.logger.error("Duplicate usernames in configuration")
            return False

        return True

    def configure(self) -> bool:
        """Create and configure users."""
        if not self.users:
            self.logger.info("No users to configure")
            return True

        self.logger.info(f"Configuring {len(self.users)} users...")

        for user in self.users:
            if not user.enabled:
                continue

            self._create_user(user)
            self._configure_groups(user)
            self._configure_ssh(user)
            self._configure_sudo(user)

        self.logger.info("✓ RBAC configuration complete")
        return True

    def verify(self) -> bool:
        """Verify users are configured correctly."""
        for user in self.users:
            if not user.enabled:
                continue

            # Check user exists
            result = self.run(f"id {user.username}", check=False)
            if not result.success:
                self.logger.warning(f"User {user.username} not found")
                continue

            self.logger.info(f"✓ User {user.username} ({user.role})")

        return True

    def _create_user(self, user: ManagedUser) -> None:
        """Create a user account."""
        role = ROLES[user.role]

        # Check if user exists
        result = self.run(f"id {user.username}", check=False)
        if result.success:
            self.logger.info(f"User {user.username} already exists, updating...")
            return

        self.logger.info(f"Creating user {user.username} ({user.role})...")

        # Build useradd command
        cmd = [
            "useradd",
            "-m",  # Create home directory
            "-s",
            role.shell,
        ]

        if user.full_name:
            cmd.extend(["-c", f'"{user.full_name}"'])

        cmd.append(user.username)

        self.run(" ".join(cmd), check=True)

        # Generate random password (user should use SSH keys)
        password = self._generate_password()
        self._set_password(user.username, password)

        # Store password in secrets manager
        try:
            from configurator.core.secrets import SecretsManager

            secrets = SecretsManager()
            secrets.store(f"user_password_{user.username}", password)
            self.logger.info(
                f"  Password stored in secrets manager (key: user_password_{user.username})"
            )
        except Exception as e:
            self.logger.warning(f"  Failed to store password in secrets manager: {e}")

        self.logger.info(f"  Created with temporary password (use SSH keys for login)")

        # Audit Log
        try:
            from configurator.core.audit import AuditEventType, AuditLogger

            audit = AuditLogger()
            audit.log_event(
                AuditEventType.USER_CREATE,
                f"Created user {user.username} with role {user.role}",
                details={"username": user.username, "role": user.role, "groups": role.groups},
            )
        except Exception:
            pass  # Don't fail installation if audit logging fails

    def _configure_groups(self, user: ManagedUser) -> None:
        """Configure user groups based on role."""
        role = ROLES[user.role]

        # Get groups that exist
        existing_groups = []
        for group in role.groups:
            result = self.run(f"getent group {group}", check=False)
            if result.success:
                existing_groups.append(group)
            else:
                self.logger.debug(f"Group {group} doesn't exist, skipping")

        if existing_groups:
            groups_str = ",".join(existing_groups)
            self.run(f"usermod -aG {groups_str} {user.username}", check=True)
            self.logger.info(f"  Added to groups: {groups_str}")

    def _configure_ssh(self, user: ManagedUser) -> None:
        """Configure SSH keys for user."""
        if not user.ssh_keys:
            return

        home_dir = Path(f"/home/{user.username}")
        ssh_dir = home_dir / ".ssh"
        authorized_keys = ssh_dir / "authorized_keys"

        # Create .ssh directory
        self.run(f"mkdir -p {ssh_dir}", check=True)
        self.run(f"chmod 700 {ssh_dir}", check=True)

        # Write authorized_keys
        keys_content = "\n".join(user.ssh_keys)
        with open(authorized_keys, "w") as f:
            f.write(keys_content + "\n")

        self.run(f"chmod 600 {authorized_keys}", check=True)
        self.run(f"chown -R {user.username}:{user.username} {ssh_dir}", check=True)

        self.logger.info(f"  Added {len(user.ssh_keys)} SSH key(s)")

    def _configure_sudo(self, user: ManagedUser) -> None:
        """Configure sudo access for user."""
        role = ROLES[user.role]

        if not role.sudo_access:
            return

        sudoers_dir = Path("/etc/sudoers.d")
        sudoers_file = sudoers_dir / f"99-{user.username}"

        if role.sudo_nopasswd:
            content = f"{user.username} ALL=(ALL) NOPASSWD: ALL\n"
        else:
            content = f"{user.username} ALL=(ALL) ALL\n"

        with open(sudoers_file, "w") as f:
            f.write(content)

        self.run(f"chmod 440 {sudoers_file}", check=True)
        self.logger.info(f"  Configured sudo access")

    def _generate_password(self, length: int = 16) -> str:
        """Generate a random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _set_password(self, username: str, password: str) -> None:
        """Set password for user."""
        try:
            # Use openssl to generate password hash
            result = subprocess.run(
                ["openssl", "passwd", "-6", password],
                capture_output=True,
                text=True,
                check=True,
            )
            hashed = result.stdout.strip()
            self.run(f"usermod -p '{hashed}' {username}", check=True)
        except subprocess.CalledProcessError:
            # Fallback if openssl not found (shouldn't happen on Debian)
            # Just set password via chpasswd
            p = subprocess.Popen(
                ["chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            p.communicate(input=f"{username}:{password}".encode())

    @classmethod
    def get_available_roles(cls) -> Dict[str, UserRole]:
        """Get all available roles."""
        return ROLES.copy()
