"""Role-Based Access Control (RBAC) manager.

Provides a lightweight RBAC engine with predefined roles, custom role creation,
role assignment, permission validation (with wildcards), and optional
system-level integrations (sudo, groups).

The implementation is safe to use in non-root environments; system mutations are
skipped when `dry_run=True` or when the current user lacks privileges.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

from configurator.rbac.permissions import (
    flatten_permissions,
    normalize_permission_string,
    wildcard_match,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PermissionScope(Enum):
    SYSTEM = "system"
    APPLICATION = "app"
    DATABASE = "db"
    NETWORK = "network"
    USER = "user"
    FILE = "file"
    SERVICE = "service"


class PermissionAction(Enum):
    ALL = "*"
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    EXECUTE = "execute"


class SudoAccess(Enum):
    NONE = "none"
    LIMITED = "limited"
    FULL = "full"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Permission:
    """Represents a single permission of the form scope:resource:action."""

    permission_string: str
    description: str = ""

    def __post_init__(self) -> None:
        normalized = normalize_permission_string(self.permission_string)
        parts = normalized.split(":")
        if len(parts) == 2:
            parts.append("*")
        if len(parts) != 3:
            raise ValueError(f"Invalid permission format: {self.permission_string}")

        self.scope, self.resource, self.action = parts

    def matches(self, required: "Permission") -> bool:
        """Check whether this permission satisfies a required permission."""

        if not wildcard_match(self.scope, required.scope):
            return False
        if not wildcard_match(self.resource, required.resource):
            return False
        if not wildcard_match(self.action, required.action):
            return False
        return True

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.scope}:{self.resource}:{self.action}"


@dataclass
class Role:
    """Represents a role with associated permissions and system bindings."""

    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    sudo_access: SudoAccess = SudoAccess.NONE
    sudo_commands: List[str] = field(default_factory=list)
    system_groups: List[str] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    custom: bool = False
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    def has_permission(
        self, required_permission: Permission, role_registry: Dict[str, "Role"]
    ) -> bool:
        for perm in self.get_all_permissions(role_registry):
            if perm.matches(required_permission):
                return True
        return False

    def get_all_permissions(
        self, role_registry: Dict[str, "Role"], seen: Optional[set] = None
    ) -> List[Permission]:
        """Return permissions including inherited roles (deduplicated order preserved)."""
        seen = seen or set()
        if self.name in seen:
            return []
        seen.add(self.name)

        combined: List[Permission] = []
        combined.extend(self.permissions)

        for parent in self.inherits_from:
            if parent not in role_registry:
                continue
            combined.extend(role_registry[parent].get_all_permissions(role_registry, seen=seen))

        # Deduplicate by string representation
        unique: Dict[str, Permission] = {}
        for perm in combined:
            unique[str(perm)] = perm
        return list(unique.values())

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [str(p) for p in self.permissions],
            "sudo_access": self.sudo_access.value,
            "sudo_commands": self.sudo_commands,
            "system_groups": self.system_groups,
            "inherits_from": self.inherits_from,
            "custom": self.custom,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


@dataclass
class RoleAssignment:
    """Assignment of a role to a user."""

    user: str
    role_name: str
    assigned_at: datetime
    assigned_by: str
    expires_at: Optional[datetime] = None
    reason: str = ""

    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.now() > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "user": self.user,
            "role_name": self.role_name,
            "assigned_at": self.assigned_at.isoformat(),
            "assigned_by": self.assigned_by,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# RBAC Manager
# ---------------------------------------------------------------------------


class RBACManager:
    """Manages roles, assignments, permission checks, and system bindings."""

    DEFAULT_DIR = Path("/etc/debian-vps-configurator/rbac")
    DEFAULT_ROLES_FILE = DEFAULT_DIR / "roles.yaml"
    DEFAULT_ASSIGNMENTS_FILE = DEFAULT_DIR / "assignments.json"
    DEFAULT_AUDIT_LOG = Path("/var/log/rbac-audit.log")

    def __init__(
        self,
        roles_file: Optional[Path] = None,
        assignments_file: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        sudoers_dir: Optional[Path] = None,
        validate_sudo: bool = True,
        dry_run: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.roles_file = Path(roles_file) if roles_file else self.DEFAULT_ROLES_FILE
        self.assignments_file = (
            Path(assignments_file) if assignments_file else self.DEFAULT_ASSIGNMENTS_FILE
        )
        self.audit_log = Path(audit_log) if audit_log else self.DEFAULT_AUDIT_LOG
        self.sudoers_dir = Path(sudoers_dir) if sudoers_dir else Path("/etc/sudoers.d")
        self.validate_sudo = validate_sudo
        self.dry_run = dry_run

        self.roles: Dict[str, Role] = {}
        self.assignments: Dict[str, RoleAssignment] = {}

        self._ensure_paths()
        self._load_roles()
        self._load_role_assignments()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _ensure_paths(self) -> None:
        """Ensure parent directories exist for RBAC artifacts."""
        self.roles_file.parent.mkdir(parents=True, exist_ok=True)
        self.assignments_file.parent.mkdir(parents=True, exist_ok=True)
        # Audit log directory may be shared; create if possible
        try:
            self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.logger.debug("No permission to create audit log directory; logging may fail")

    def _load_roles(self) -> None:
        """Load roles from YAML, falling back to packaged defaults."""
        if not self.roles_file.exists():
            self._write_default_roles()

        try:
            with open(self.roles_file, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as exc:  # pragma: no cover - logged error path
            self.logger.error("Failed to load roles: %s", exc)
            data = {}

        for role_name, cfg in data.items():
            permissions = [Permission(p) for p in cfg.get("permissions", [])]
            role = Role(
                name=role_name,
                description=cfg.get("description", ""),
                permissions=permissions,
                sudo_access=SudoAccess(cfg.get("sudo_access", "none")),
                sudo_commands=cfg.get("sudo_commands", []),
                system_groups=cfg.get("system_groups", []),
                inherits_from=cfg.get("inherits_from", []),
                custom=cfg.get("custom", False),
            )
            self.roles[role_name] = role

        self.logger.debug("Loaded %s roles from %s", len(self.roles), self.roles_file)

    def _write_default_roles(self) -> None:
        """Seed roles file with packaged defaults."""
        packaged = Path(__file__).with_name("roles.yaml")
        if packaged.exists():
            self.roles_file.write_text(packaged.read_text())
            return
        # Fallback minimal admin role
        self.roles_file.write_text(
            yaml.safe_dump(
                {
                    "admin": {
                        "description": "Full system administrator",
                        "permissions": ["system:*"],
                        "sudo_access": "full",
                        "sudo_commands": [],
                        "system_groups": ["sudo"],
                    }
                },
                sort_keys=False,
            )
        )

    def _load_role_assignments(self) -> None:
        if not self.assignments_file.exists():
            return

        try:
            raw = json.loads(self.assignments_file.read_text())
        except Exception as exc:  # pragma: no cover - logged error path
            self.logger.error("Failed to load role assignments: %s", exc)
            return

        for user, payload in raw.items():
            expires_at = payload.get("expires_at")
            self.assignments[user] = RoleAssignment(
                user=payload["user"],
                role_name=payload["role_name"],
                assigned_at=datetime.fromisoformat(payload["assigned_at"]),
                assigned_by=payload.get("assigned_by", "system"),
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                reason=payload.get("reason", ""),
            )

    def _save_role_assignments(self) -> None:
        data = {user: assignment.to_dict() for user, assignment in self.assignments.items()}
        try:
            self.assignments_file.write_text(json.dumps(data, indent=2))
        except Exception as exc:  # pragma: no cover - logged error path
            self.logger.error("Failed to save role assignments: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_custom_role(
        self,
        name: str,
        description: str,
        permissions: Iterable[str],
        sudo_access: SudoAccess = SudoAccess.NONE,
        sudo_commands: Optional[List[str]] = None,
        system_groups: Optional[List[str]] = None,
        inherits_from: Optional[List[str]] = None,
        created_by: str = "system",
    ) -> Role:
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")

        permission_objs = [Permission(p) for p in flatten_permissions([permissions])]
        role = Role(
            name=name,
            description=description,
            permissions=permission_objs,
            sudo_access=sudo_access,
            sudo_commands=sudo_commands or [],
            system_groups=system_groups or [],
            inherits_from=inherits_from or [],
            custom=True,
            created_at=datetime.now(),
            created_by=created_by,
        )
        self.roles[name] = role
        self._persist_roles()
        self._audit_log("create_role", role=name, created_by=created_by)
        return role

    def assign_role(
        self,
        user: str,
        role_name: str,
        assigned_by: str = "system",
        expires_at: Optional[datetime] = None,
        reason: str = "",
    ) -> RoleAssignment:
        if role_name not in self.roles:
            raise ValueError(f"Role not found: {role_name}")

        assignment = RoleAssignment(
            user=user,
            role_name=role_name,
            assigned_at=datetime.now(),
            assigned_by=assigned_by,
            expires_at=expires_at,
            reason=reason,
        )
        self.assignments[user] = assignment
        self._save_role_assignments()

        role = self.roles[role_name]
        self._apply_role_to_system(user, role)
        self._audit_log(
            "assign_role",
            user=user,
            role=role_name,
            assigned_by=assigned_by,
            reason=reason,
        )
        return assignment

    def check_permission(self, user: str, permission_string: str) -> bool:
        assignment = self.assignments.get(user)
        if not assignment:
            return False
        if assignment.is_expired():
            return False

        role = self.roles.get(assignment.role_name)
        if not role:
            return False

        required = Permission(permission_string)
        return role.has_permission(required, self.roles)

    def get_user_permissions(self, user: str) -> List[Permission]:
        assignment = self.assignments.get(user)
        if not assignment or assignment.is_expired():
            return []
        role = self.roles.get(assignment.role_name)
        if not role:
            return []
        return role.get_all_permissions(self.roles)

    def list_roles(self) -> List[Role]:
        return list(self.roles.values())

    def get_role(self, role_name: str) -> Optional[Role]:
        return self.roles.get(role_name)

    # ------------------------------------------------------------------
    # System integration
    # ------------------------------------------------------------------

    def _apply_role_to_system(self, user: str, role: Role) -> None:
        if self.dry_run:
            self.logger.info("DRY RUN: skipping system changes for %s", user)
            return

        if os.geteuid() != 0:
            self.logger.warning("Skipping system changes (not running as root)")
            return

        self._add_user_to_groups(user, role.system_groups)
        if role.sudo_access != SudoAccess.NONE:
            self._configure_sudo(user, role)

    def _add_user_to_groups(self, user: str, groups: List[str]) -> None:
        for group in groups:
            try:
                subprocess.run(["usermod", "-aG", group, user], check=True, capture_output=True)
                self.logger.info("Added %s to group %s", user, group)
            except subprocess.CalledProcessError as exc:
                if b"does not exist" in exc.stderr:
                    self.logger.warning("Group %s does not exist; creating it", group)
                    try:
                        subprocess.run(["groupadd", group], check=True, capture_output=True)
                        subprocess.run(
                            ["usermod", "-aG", group, user], check=True, capture_output=True
                        )
                        self.logger.info("Created group %s and added %s", group, user)
                    except subprocess.CalledProcessError as e2:
                        self.logger.error("Failed to create group %s: %s", group, e2.stderr)
                else:
                    self.logger.error("Failed to add %s to group %s: %s", user, group, exc.stderr)

    def _configure_sudo(self, user: str, role: Role) -> None:
        sudoers_file = self.sudoers_dir / f"rbac-{user}"
        lines = [
            f"# RBAC-managed sudo rules for {user} (role: {role.name})",
            f"# Generated: {datetime.now().isoformat()}",
            "",
        ]

        if role.sudo_access == SudoAccess.FULL:
            lines.append(f"{user} ALL=(ALL) ALL")
        elif role.sudo_access == SudoAccess.LIMITED:
            for cmd in role.sudo_commands:
                lines.append(f"{user} ALL=(ALL) NOPASSWD: {cmd}")

        sudoers_file.write_text("\n".join(lines) + "\n")
        sudoers_file.chmod(0o440)

        if self.validate_sudo:
            try:
                subprocess.run(
                    ["visudo", "-cf", str(sudoers_file)], check=True, capture_output=True
                )
            except subprocess.CalledProcessError as exc:  # pragma: no cover - requires root
                self.logger.error("Sudo validation failed for %s: %s", sudoers_file, exc.stderr)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist_roles(self) -> None:
        data = {role.name: role.to_dict() for role in self.roles.values()}
        try:
            self.roles_file.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception as exc:  # pragma: no cover - logged error path
            self.logger.error("Failed to persist roles: %s", exc)

    def _audit_log(self, action: str, **details: str) -> None:
        entry = {"timestamp": datetime.now().isoformat(), "action": action, **details}
        try:
            with self.audit_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        except Exception:  # pragma: no cover - best effort logging
            self.logger.debug("Audit log unavailable at %s", self.audit_log)
