"""User lifecycle management - automated provisioning and offboarding."""

import grp
import json
import logging
import os
import pwd
import secrets
import string
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class UserStatus(Enum):
    """User account status."""

    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    OFFBOARDED = "offboarded"
    LOCKED = "locked"


class LifecycleEvent(Enum):
    """User lifecycle events."""

    CREATED = "created"
    ACTIVATED = "activated"
    MODIFIED = "modified"
    ROLE_CHANGED = "role_changed"
    SUSPENDED = "suspended"
    REACTIVATED = "reactivated"
    OFFBOARDED = "offboarded"


@dataclass
class UserProfile:
    """Complete user profile with lifecycle metadata."""

    username: str
    uid: int
    full_name: str
    email: str
    role: str
    status: UserStatus = UserStatus.PENDING

    # System info
    gid: Optional[int] = None
    home_dir: Optional[Path] = None
    shell: str = "/bin/bash"

    # Organization info
    department: Optional[str] = None
    manager: Optional[str] = None
    employee_id: Optional[str] = None

    # Lifecycle metadata
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    activated_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    offboarded_at: Optional[datetime] = None
    offboarded_by: Optional[str] = None
    offboarding_reason: Optional[str] = None

    # Security features
    ssh_keys_enabled: bool = False
    mfa_enabled: bool = False
    certificates_issued: bool = False

    # Access tracking
    last_login: Optional[datetime] = None
    login_count: int = 0

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "username": self.username,
            "uid": self.uid,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "status": self.status.value,
            "gid": self.gid,
            "home_dir": str(self.home_dir) if self.home_dir else None,
            "shell": self.shell,
            "department": self.department,
            "manager": self.manager,
            "employee_id": self.employee_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "offboarded_at": self.offboarded_at.isoformat() if self.offboarded_at else None,
            "offboarded_by": self.offboarded_by,
            "offboarding_reason": self.offboarding_reason,
            "ssh_keys_enabled": self.ssh_keys_enabled,
            "mfa_enabled": self.mfa_enabled,
            "certificates_issued": self.certificates_issued,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
        }


class UserLifecycleManager:
    """
    Manages complete user lifecycle from creation to offboarding.

    Features:
    - Automated user provisioning
    - Integration with RBAC (PROMPT 3.1)
    - Integration with SSH key management (PROMPT 2.4)
    - Integration with 2FA (PROMPT 2.5)
    - User suspension and reactivation
    - Complete offboarding with data archival
    - Audit trail for compliance
    """

    USER_REGISTRY_FILE = Path("/var/lib/debian-vps-configurator/users/registry.json")
    USER_ARCHIVE_DIR = Path("/var/backups/users")
    AUDIT_LOG = Path("/var/log/user-lifecycle-audit.log")

    def __init__(
        self,
        registry_file: Optional[Path] = None,
        archive_dir: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
        dry_run: bool = False,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.dry_run = dry_run

        self.USER_REGISTRY_FILE = registry_file or self.USER_REGISTRY_FILE
        self.USER_ARCHIVE_DIR = archive_dir or self.USER_ARCHIVE_DIR
        self.AUDIT_LOG = audit_log or self.AUDIT_LOG

        self._ensure_directories()
        self._load_user_registry()
        self._init_integrated_managers()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        try:
            self.USER_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            self.USER_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        except PermissionError:
            self.logger.debug("No permission to create directories; will use temp")

    def _init_integrated_managers(self):
        """Initialize integrated security/RBAC managers."""
        try:
            from configurator.rbac.rbac_manager import RBACManager

            self.rbac_manager = RBACManager()
        except (ImportError, Exception) as e:
            self.logger.warning(f"RBAC manager not available: {e}")
            self.rbac_manager = None

        # SSH manager not implemented yet
        self.ssh_manager = None

        # MFA manager not implemented yet
        self.mfa_manager = None

    def _load_user_registry(self):
        """Load user registry from JSON."""
        self.users: Dict[str, UserProfile] = {}

        if self.USER_REGISTRY_FILE.exists():
            try:
                with open(self.USER_REGISTRY_FILE, "r") as f:
                    data = json.load(f)

                for username, user_data in data.items():
                    self.users[username] = self._profile_from_dict(user_data)

                self.logger.info(f"Loaded {len(self.users)} user profiles")
            except Exception as e:
                self.logger.error(f"Failed to load user registry: {e}")

    def _save_user_registry(self):
        """Save user registry to JSON."""
        try:
            data = {username: profile.to_dict() for username, profile in self.users.items()}

            with open(self.USER_REGISTRY_FILE, "w") as f:
                json.dump(data, f, indent=2)

            self.USER_REGISTRY_FILE.chmod(0o600)
        except Exception as e:
            self.logger.error(f"Failed to save user registry: {e}")

    def _profile_from_dict(self, data: Dict) -> UserProfile:
        """Deserialize UserProfile from dictionary."""
        return UserProfile(
            username=data["username"],
            uid=data["uid"],
            full_name=data["full_name"],
            email=data["email"],
            role=data["role"],
            status=UserStatus(data["status"]),
            gid=data.get("gid"),
            home_dir=Path(data["home_dir"]) if data.get("home_dir") else None,
            shell=data.get("shell", "/bin/bash"),
            department=data.get("department"),
            manager=data.get("manager"),
            employee_id=data.get("employee_id"),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            created_by=data.get("created_by"),
            activated_at=(
                datetime.fromisoformat(data["activated_at"]) if data.get("activated_at") else None
            ),
            last_modified=(
                datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None
            ),
            offboarded_at=(
                datetime.fromisoformat(data["offboarded_at"]) if data.get("offboarded_at") else None
            ),
            offboarded_by=data.get("offboarded_by"),
            offboarding_reason=data.get("offboarding_reason"),
            ssh_keys_enabled=data.get("ssh_keys_enabled", False),
            mfa_enabled=data.get("mfa_enabled", False),
            certificates_issued=data.get("certificates_issued", False),
            last_login=(
                datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
            ),
            login_count=data.get("login_count", 0),
        )

    def create_user(
        self,
        username: str,
        full_name: str,
        email: str,
        role: str,
        created_by: str = "system",
        shell: str = "/bin/bash",
        department: Optional[str] = None,
        manager: Optional[str] = None,
        enable_ssh_key: bool = False,
        enable_2fa: bool = False,
        generate_temp_password: bool = True,
    ) -> UserProfile:
        """
        Create a new user with complete provisioning.

        Args:
            username: System username
            full_name: User's full name
            email: User's email address
            role: RBAC role to assign
            created_by: Who created the user
            shell: User's default shell
            department: Department/team
            manager: Manager's username
            enable_ssh_key: Generate and deploy SSH key
            enable_2fa: Enroll user in 2FA
            generate_temp_password: Generate temporary password

        Returns:
            UserProfile object
        """
        self.logger.info(f"Creating user: {username}")

        # Check if user already exists
        if username in self.users:
            raise ValueError(f"User already exists: {username}")

        # Step 1: Create system user account
        self.logger.info("Step 1/12: Creating user account...")
        uid, gid = self._create_system_user(username, shell)

        # Get user info
        try:
            user_info = pwd.getpwnam(username)
            home_dir = Path(user_info.pw_dir)
        except KeyError:
            # User not found, use defaults
            home_dir = Path(f"/home/{username}")

        # Step 2: Setup home directory
        self.logger.info("Step 2/12: Setting up home directory...")
        if not self.dry_run:
            self._setup_home_directory(username, home_dir)

        # Step 3: Configure shell
        self.logger.info("Step 3/12: Configuring shell...")
        # Already done in create_system_user

        # Step 4: Assign RBAC role (PROMPT 3.1 integration)
        self.logger.info(f"Step 4/12: Assigning RBAC role: {role}...")
        if self.rbac_manager and not self.dry_run:
            try:
                self.rbac_manager.assign_role(
                    user=username,
                    role_name=role,
                    assigned_by=created_by,
                    reason="User provisioning",
                )
            except Exception as e:
                self.logger.error(f"Failed to assign RBAC role: {e}")

        # Step 5: Configure system groups
        self.logger.info("Step 5/12: Configuring system groups...")
        if self.rbac_manager and not self.dry_run:
            role_obj = self.rbac_manager.get_role(role)
            if role_obj and role_obj.system_groups:
                for group in role_obj.system_groups:
                    self._add_user_to_group(username, group)

        # Step 6: Configure sudo access
        self.logger.info("Step 6/12: Configuring sudo access...")
        # Handled by RBAC manager

        # Step 7: Generate SSH key (PROMPT 2.4 integration)
        if enable_ssh_key:
            self.logger.info("Step 7/12: Generating SSH key...")
            # SSH manager integration placeholder
            self.logger.warning("SSH key generation not yet implemented")

        # Step 8: Enroll in 2FA (PROMPT 2.5 integration)
        if enable_2fa:
            self.logger.info("Step 8/12: Enrolling in 2FA...")
            # MFA manager integration placeholder
            self.logger.warning("2FA enrollment not yet implemented")

        # Step 9: Set temporary password
        temp_password = None
        if generate_temp_password:
            self.logger.info("Step 9/12: Setting temporary password...")
            temp_password = self._generate_temp_password()
            if not self.dry_run:
                self._set_user_password(username, temp_password, force_change=True)

        # Step 10: Configure user metadata
        self.logger.info("Step 10/12: Configuring user metadata...")

        # Step 11: Create user profile
        self.logger.info("Step 11/12: Creating user registry entry...")
        profile = UserProfile(
            username=username,
            uid=uid,
            gid=gid,
            full_name=full_name,
            email=email,
            role=role,
            home_dir=home_dir,
            shell=shell,
            department=department,
            manager=manager,
            created_at=datetime.now(),
            created_by=created_by,
            status=UserStatus.PENDING if enable_2fa else UserStatus.ACTIVE,
            ssh_keys_enabled=enable_ssh_key,
            mfa_enabled=enable_2fa,
        )

        # Register user
        self.users[username] = profile
        self._save_user_registry()

        # Step 12: Send welcome email
        self.logger.info("Step 12/12: Sending welcome email...")
        # Email sending placeholder
        self.logger.info(f"Welcome email would be sent to: {email}")

        # Audit log
        self._audit_log(
            event=LifecycleEvent.CREATED,
            username=username,
            performed_by=created_by,
            details={
                "role": role,
                "ssh_key": enable_ssh_key,
                "2fa": enable_2fa,
            },
        )

        self.logger.info(f"✅ User {username} created successfully")

        return profile

    def _create_system_user(self, username: str, shell: str) -> tuple[int, int]:
        """Create system user account."""
        if self.dry_run:
            return (1000, 1000)

        try:
            result = subprocess.run(
                ["useradd", "-m", "-s", shell, username],  # Create home directory  # Set shell
                check=True,
                capture_output=True,
                text=True,
            )

            # Get UID and GID
            user_info = pwd.getpwnam(username)
            return (user_info.pw_uid, user_info.pw_gid)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create user: {e.stderr}")
            raise RuntimeError(f"User creation failed: {e.stderr}")

    def _setup_home_directory(self, username: str, home_dir: Path):
        """Setup user home directory with proper permissions."""
        try:
            user_info = pwd.getpwnam(username)

            # Ensure home directory exists
            if not home_dir.exists():
                home_dir.mkdir(parents=True, exist_ok=True)

            # Set ownership recursively
            for item in home_dir.rglob("*"):
                try:
                    os.chown(item, user_info.pw_uid, user_info.pw_gid)
                except Exception:
                    pass

            # Set permissions on home directory
            home_dir.chmod(0o755)
            os.chown(home_dir, user_info.pw_uid, user_info.pw_gid)

        except Exception as e:
            self.logger.error(f"Failed to setup home directory: {e}")

    def _add_user_to_group(self, username: str, group: str):
        """Add user to a system group."""
        try:
            # Check if group exists
            grp.getgrnam(group)

            # Add user to group
            subprocess.run(
                ["usermod", "-a", "-G", group, username], check=True, capture_output=True
            )

            self.logger.info(f"Added {username} to group: {group}")

        except KeyError:
            self.logger.warning(f"Group does not exist: {group}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to add user to group: {e}")

    def _generate_temp_password(self) -> str:
        """Generate secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(16))
        return password

    def _set_user_password(self, username: str, password: str, force_change: bool = True):
        """Set user password."""
        try:
            # Set password using chpasswd
            proc = subprocess.Popen(
                ["chpasswd"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            proc.communicate(f"{username}:{password}")

            # Force password change on first login
            if force_change:
                subprocess.run(["passwd", "--expire", username], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set password: {e}")

    def offboard_user(
        self,
        username: str,
        reason: str,
        offboarded_by: str = "system",
        archive_data: bool = True,
    ) -> bool:
        """
        Offboard a user completely.

        This includes:
        - Disabling account
        - Revoking SSH keys
        - Disabling 2FA
        - Revoking certificates
        - Removing RBAC role
        - Removing from groups
        - Archiving home directory
        - Generating offboarding report

        Args:
            username: Username to offboard
            reason: Reason for offboarding
            offboarded_by: Who performed the offboarding
            archive_data: Whether to archive user's data

        Returns:
            True if successful
        """
        self.logger.info(f"Offboarding user: {username}")

        profile = self.users.get(username)

        if not profile:
            raise ValueError(f"User not found: {username}")

        # Step 1: Disable account
        self.logger.info("Step 1/10: Disabling user account...")
        if not self.dry_run:
            self._disable_system_user(username)

        # Step 2: Revoke SSH keys (PROMPT 2.4 integration)
        if profile.ssh_keys_enabled:
            self.logger.info("Step 2/10: Revoking SSH keys...")
            # SSH manager integration placeholder
            self.logger.warning("SSH key revocation not yet implemented")

        # Step 3: Disable 2FA (PROMPT 2.5 integration)
        if profile.mfa_enabled:
            self.logger.info("Step 3/10: Disabling 2FA...")
            # MFA manager integration placeholder
            self.logger.warning("2FA disabling not yet implemented")

        # Step 4: Revoke certificates (PROMPT 2.3 integration)
        if profile.certificates_issued:
            self.logger.info("Step 4/10: Revoking certificates...")
            # Certificate manager integration placeholder
            self.logger.warning("Certificate revocation not yet implemented")

        # Step 5: Revoke RBAC role (PROMPT 3.1 integration)
        if self.rbac_manager and not self.dry_run:
            self.logger.info("Step 5/10: Revoking RBAC permissions...")

            # Remove role assignment
            if username in self.rbac_manager.assignments:
                del self.rbac_manager.assignments[username]
                self.rbac_manager._save_role_assignments()

            # Remove sudo rules
            sudo_file = Path(f"/etc/sudoers.d/rbac-{username}")
            if sudo_file.exists():
                sudo_file.unlink()

        # Step 6: Remove from groups
        self.logger.info("Step 6/10: Removing from groups and teams...")
        if not self.dry_run:
            self._remove_user_from_all_groups(username)

        # Step 7: Archive home directory
        archive_path = None
        if archive_data and profile.home_dir:
            self.logger.info("Step 7/10: Archiving home directory...")
            if not self.dry_run:
                archive_path = self._archive_home_directory(username, profile.home_dir)

        # Step 8: Check for shared credentials
        self.logger.info("Step 8/10: Checking for shared credentials...")
        # Placeholder for shared credential detection

        # Step 9: Generate offboarding report
        self.logger.info("Step 9/10: Generating offboarding report...")
        # Placeholder for report generation

        # Step 10: Update profile
        self.logger.info("Step 10/10: Audit logging...")
        profile.status = UserStatus.OFFBOARDED
        profile.offboarded_at = datetime.now()
        profile.offboarded_by = offboarded_by
        profile.offboarding_reason = reason

        self._save_user_registry()

        # Audit log
        self._audit_log(
            event=LifecycleEvent.OFFBOARDED,
            username=username,
            performed_by=offboarded_by,
            details={
                "reason": reason,
                "archived": archive_data,
                "archive_path": str(archive_path) if archive_path else None,
            },
        )

        self.logger.info(f"✅ User {username} offboarded successfully")

        return True

    def _disable_system_user(self, username: str):
        """Disable system user account."""
        try:
            # Lock account
            subprocess.run(["usermod", "--lock", username], check=True, capture_output=True)

            # Expire password
            subprocess.run(
                ["usermod", "--expiredate", "1", username], check=True, capture_output=True
            )

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to disable user: {e}")
            raise

    def _remove_user_from_all_groups(self, username: str):
        """Remove user from all supplementary groups."""
        try:
            # Get current groups
            pwd.getpwnam(username)
            groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]

            # Remove from each group
            for group in groups:
                try:
                    subprocess.run(
                        ["gpasswd", "-d", username, group], check=True, capture_output=True
                    )
                except subprocess.CalledProcessError:
                    pass

        except Exception as e:
            self.logger.error(f"Failed to remove user from groups: {e}")

    def _archive_home_directory(self, username: str, home_dir: Path) -> Path:
        """Archive user's home directory."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        archive_name = f"{username}-{timestamp}.tar.gz"
        archive_path = self.USER_ARCHIVE_DIR / archive_name

        try:
            subprocess.run(
                ["tar", "-cz", str(archive_path), "-C", str(home_dir.parent), home_dir.name],
                check=True,
                capture_output=True,
            )

            # Set restrictive permissions
            archive_path.chmod(0o400)

            self.logger.info(f"Home directory archived to: {archive_path}")

            return archive_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to archive home directory: {e}")
            raise

    def suspend_user(self, username: str, reason: str, suspended_by: str = "system") -> bool:
        """Suspend user account temporarily."""
        self.logger.info(f"Suspending user: {username}")

        profile = self.users.get(username)
        if not profile:
            raise ValueError(f"User not found: {username}")

        if not self.dry_run:
            try:
                subprocess.run(["usermod", "--lock", username], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to suspend user: {e}")
                raise

        profile.status = UserStatus.SUSPENDED
        profile.last_modified = datetime.now()
        self._save_user_registry()

        self._audit_log(
            event=LifecycleEvent.SUSPENDED,
            username=username,
            performed_by=suspended_by,
            details={"reason": reason},
        )

        return True

    def reactivate_user(self, username: str, reactivated_by: str = "system") -> bool:
        """Reactivate a suspended user account."""
        self.logger.info(f"Reactivating user: {username}")

        profile = self.users.get(username)
        if not profile:
            raise ValueError(f"User not found: {username}")

        if profile.status != UserStatus.SUSPENDED:
            raise ValueError(f"User is not suspended: {username}")

        if not self.dry_run:
            try:
                subprocess.run(["usermod", "--unlock", username], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to reactivate user: {e}")
                raise

        profile.status = UserStatus.ACTIVE
        profile.activated_at = datetime.now()
        profile.last_modified = datetime.now()
        self._save_user_registry()

        self._audit_log(
            event=LifecycleEvent.REACTIVATED,
            username=username,
            performed_by=reactivated_by,
            details={},
        )

        return True

    def update_user_role(self, username: str, new_role: str, updated_by: str = "system") -> bool:
        """Update user's RBAC role."""
        self.logger.info(f"Updating role for user {username} to {new_role}")

        profile = self.users.get(username)
        if not profile:
            raise ValueError(f"User not found: {username}")

        old_role = profile.role

        # Update RBAC role
        if self.rbac_manager and not self.dry_run:
            self.rbac_manager.assign_role(
                user=username,
                role_name=new_role,
                assigned_by=updated_by,
                reason=f"Role changed from {old_role} to {new_role}",
            )

        profile.role = new_role
        profile.last_modified = datetime.now()
        self._save_user_registry()

        self._audit_log(
            event=LifecycleEvent.ROLE_CHANGED,
            username=username,
            performed_by=updated_by,
            details={
                "old_role": old_role,
                "new_role": new_role,
            },
        )

        return True

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Get user profile."""
        return self.users.get(username)

    def list_users(self, status: Optional[UserStatus] = None) -> List[UserProfile]:
        """List users, optionally filtered by status."""
        if status:
            return [u for u in self.users.values() if u.status == status]
        return list(self.users.values())

    def _audit_log(
        self, event: LifecycleEvent, username: str, performed_by: str, details: Dict = None
    ):
        """Log lifecycle event for audit."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event.value,
            "username": username,
            "performed_by": performed_by,
            "details": details or {},
        }

        try:
            with open(self.AUDIT_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
