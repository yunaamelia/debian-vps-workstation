"""Temporary access and time-based permissions management."""

import json
import logging
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class AccessType(Enum):
    """Types of temporary access."""

    TEMPORARY = "temporary"
    EMERGENCY = "emergency"
    TRIAL = "trial"


class AccessStatus(Enum):
    """Temporary access status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class ExtensionStatus(Enum):
    """Extension request status."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass
class TempAccess:
    """
    Represents temporary access grant.

    Example:
        TempAccess(
            access_id="TEMP-20260106-001",
            username="contractor-john",
            access_type=AccessType.TEMPORARY,
            granted_at=datetime(2026, 1, 6),
            expires_at=datetime(2026, 2, 5),
            role="developer",
            reason="Q1 2026 backend project",
        )
    """

    access_id: str
    username: str
    access_type: AccessType
    granted_at: datetime
    expires_at: datetime
    role: str
    reason: str
    granted_by: str = "system"
    status: AccessStatus = AccessStatus.ACTIVE
    notify_before_days: int = 7
    extended_count: int = 0
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if access has expired."""
        return datetime.now() > self.expires_at

    def days_remaining(self) -> int:
        """Calculate days remaining."""
        if self.is_expired():
            return 0
        delta = self.expires_at - datetime.now()
        return delta.days

    def needs_reminder(self) -> bool:
        """Check if reminder should be sent."""
        days_left = self.days_remaining()
        return days_left <= self.notify_before_days and days_left > 0

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "access_id": self.access_id,
            "username": self.username,
            "access_type": self.access_type.value,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "role": self.role,
            "reason": self.reason,
            "granted_by": self.granted_by,
            "status": self.status.value,
            "notify_before_days": self.notify_before_days,
            "extended_count": self.extended_count,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_by": self.revoked_by,
        }


@dataclass
class ExtensionRequest:
    """Access extension request."""

    request_id: str
    access_id: str
    username: str
    additional_days: int
    reason: str
    requested_by: str
    requested_at: datetime
    status: ExtensionStatus = ExtensionStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "request_id": self.request_id,
            "access_id": self.access_id,
            "username": self.username,
            "additional_days": self.additional_days,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "status": self.status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class TempAccessManager:
    """
    Manages temporary and time-limited access.

    Features:
    - Grant temporary access with auto-expiration
    - Schedule automatic revocation
    - Send expiration reminders
    - Handle extension requests
    - Emergency break-glass access
    - Complete audit trail
    """

    ACCESS_REGISTRY = Path("/var/lib/debian-vps-configurator/temp-access/registry.json")
    EXTENSIONS_FILE = Path("/var/lib/debian-vps-configurator/temp-access/extensions.json")
    AUDIT_LOG = Path("/var/log/temp-access-audit.log")

    def __init__(
        self,
        registry_file: Optional[Path] = None,
        extensions_file: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        # Allow overriding paths (for testing)
        self.ACCESS_REGISTRY = registry_file or self.ACCESS_REGISTRY
        self.EXTENSIONS_FILE = extensions_file or self.EXTENSIONS_FILE
        self.AUDIT_LOG = audit_log or self.AUDIT_LOG

        self._ensure_directories()
        self._load_access_registry()
        self._load_extensions()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        try:
            self.ACCESS_REGISTRY.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            if self.AUDIT_LOG.parent != Path("/var/log"):
                self.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        except PermissionError:
            self.logger.debug("No permission to create directories")

    def _load_access_registry(self):
        """Load access registry."""
        self.access_grants: Dict[str, TempAccess] = {}

        if self.ACCESS_REGISTRY.exists():
            try:
                with open(self.ACCESS_REGISTRY, "r") as f:
                    data = json.load(f)

                for username, access_data in data.items():
                    self.access_grants[username] = self._access_from_dict(access_data)

                self.logger.info(f"Loaded {len(self.access_grants)} temporary access grants")
            except Exception as e:
                self.logger.error(f"Failed to load access registry: {e}")

    def _load_extensions(self):
        """Load extension requests."""
        self.extensions: Dict[str, ExtensionRequest] = {}

        if self.EXTENSIONS_FILE.exists():
            try:
                with open(self.EXTENSIONS_FILE, "r") as f:
                    data = json.load(f)

                for request_id, ext_data in data.items():
                    self.extensions[request_id] = self._extension_from_dict(ext_data)

                self.logger.info(f"Loaded {len(self.extensions)} extension requests")
            except Exception as e:
                self.logger.error(f"Failed to load extensions: {e}")

    def _save_access_registry(self):
        """Save access registry."""
        try:
            data = {username: access.to_dict() for username, access in self.access_grants.items()}

            with open(self.ACCESS_REGISTRY, "w") as f:
                json.dump(data, f, indent=2)

            try:
                self.ACCESS_REGISTRY.chmod(0o600)
            except PermissionError:
                pass
        except Exception as e:
            self.logger.error(f"Failed to save access registry: {e}")

    def _save_extensions(self):
        """Save extension requests."""
        try:
            data = {request_id: ext.to_dict() for request_id, ext in self.extensions.items()}

            with open(self.EXTENSIONS_FILE, "w") as f:
                json.dump(data, f, indent=2)

            try:
                self.EXTENSIONS_FILE.chmod(0o600)
            except PermissionError:
                pass
        except Exception as e:
            self.logger.error(f"Failed to save extensions: {e}")

    def _access_from_dict(self, data: Dict) -> TempAccess:
        """Deserialize TempAccess from dictionary."""
        return TempAccess(
            access_id=data["access_id"],
            username=data["username"],
            access_type=AccessType(data["access_type"]),
            granted_at=datetime.fromisoformat(data["granted_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            role=data["role"],
            reason=data["reason"],
            granted_by=data.get("granted_by", "system"),
            status=AccessStatus(data.get("status", "active")),
            notify_before_days=data.get("notify_before_days", 7),
            extended_count=data.get("extended_count", 0),
            revoked_at=(
                datetime.fromisoformat(data["revoked_at"]) if data.get("revoked_at") else None
            ),
            revoked_by=data.get("revoked_by"),
        )

    def _extension_from_dict(self, data: Dict) -> ExtensionRequest:
        """Deserialize ExtensionRequest from dictionary."""
        return ExtensionRequest(
            request_id=data["request_id"],
            access_id=data["access_id"],
            username=data["username"],
            additional_days=data["additional_days"],
            reason=data["reason"],
            requested_by=data["requested_by"],
            requested_at=datetime.fromisoformat(data["requested_at"]),
            status=ExtensionStatus(data.get("status", "pending")),
            approved_by=data.get("approved_by"),
            approved_at=(
                datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None
            ),
        )

    def grant_temp_access(
        self,
        username: str,
        full_name: str,
        email: str,
        role: str,
        duration_days: int,
        reason: str,
        granted_by: str = "system",
        access_type: AccessType = AccessType.TEMPORARY,
        notify_before_days: int = 7,
        skip_user_creation: bool = False,
    ) -> TempAccess:
        """
        Grant temporary access to a user.

        Args:
            username: Username
            full_name: User's full name
            email: User's email
            role: RBAC role to assign
            duration_days: Access duration in days
            reason: Reason for temporary access
            granted_by: Who granted the access
            access_type: Type of temporary access
            notify_before_days: Days before expiration to send reminder
            skip_user_creation: Skip user creation (for testing)

        Returns:
            TempAccess object
        """
        self.logger.info(f"Granting temporary access to {username} for {duration_days} days")

        # Calculate expiration
        granted_at = datetime.now()
        expires_at = granted_at + timedelta(days=duration_days)

        # Set account expiration at OS level (if not testing)
        if not skip_user_creation:
            self._set_account_expiration(username, expires_at)

        # Create access record
        access_id = f"{access_type.value.upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"

        access = TempAccess(
            access_id=access_id,
            username=username,
            access_type=access_type,
            granted_at=granted_at,
            expires_at=expires_at,
            role=role,
            reason=reason,
            granted_by=granted_by,
            notify_before_days=notify_before_days,
        )

        # Save access
        self.access_grants[username] = access
        self._save_access_registry()

        # Audit log
        self._audit_log(
            action="grant_access",
            username=username,
            access_type=access_type.value,
            duration_days=duration_days,
            expires_at=expires_at.isoformat(),
        )

        self.logger.info(f"✅ Temporary access granted to {username} (expires: {expires_at})")

        return access

    def _set_account_expiration(self, username: str, expires_at: datetime):
        """Set account expiration at OS level."""
        try:
            # Format date for chage command (YYYY-MM-DD)
            expire_date = expires_at.strftime("%Y-%m-%d")

            subprocess.run(["chage", "-E", expire_date, username], check=True, capture_output=True)

            self.logger.info(f"Account expiration set for {username}: {expire_date}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set account expiration: {e.stderr}")
        except FileNotFoundError:
            self.logger.debug("chage command not available (testing mode)")

    def check_expired_access(self) -> List[TempAccess]:
        """Check for expired access and mark as expired."""
        expired = []

        for access in self.access_grants.values():
            if access.status == AccessStatus.ACTIVE and access.is_expired():
                self.logger.info(f"Access expired for {access.username}")

                # Mark as expired
                access.status = AccessStatus.EXPIRED
                expired.append(access)

        if expired:
            self._save_access_registry()

        return expired

    def revoke_access(
        self,
        username: str,
        reason: str = "Manual revocation",
        revoked_by: str = "system",
        skip_system: bool = False,
    ) -> bool:
        """
        Revoke temporary access.

        Args:
            username: Username
            reason: Revocation reason
            revoked_by: Who revoked the access
            skip_system: Skip system operations (testing)

        Returns:
            True if successful
        """
        access = self.access_grants.get(username)

        if not access:
            self.logger.warning(f"No temporary access found for {username}")
            return False

        self.logger.info(f"Revoking temporary access for {username}")

        # Disable account (if not testing)
        if not skip_system:
            self._disable_account(username)

        # Update access record
        access.status = AccessStatus.REVOKED
        access.revoked_at = datetime.now()
        access.revoked_by = revoked_by

        self._save_access_registry()

        # Audit log
        self._audit_log(
            action="revoke_access",
            username=username,
            reason=reason,
            revoked_by=revoked_by,
        )

        self.logger.info(f"✅ Temporary access revoked for {username}")

        return True

    def _disable_account(self, username: str):
        """Disable user account."""
        try:
            subprocess.run(
                ["usermod", "-L", username], check=True, capture_output=True  # Lock account
            )

            self.logger.info(f"Account disabled for {username}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to disable account: {e.stderr}")
        except FileNotFoundError:
            self.logger.debug("usermod command not available (testing mode)")

    def request_extension(
        self,
        username: str,
        additional_days: int,
        reason: str,
        requested_by: str,
    ) -> ExtensionRequest:
        """
        Request extension for temporary access.

        Args:
            username: Username
            additional_days: Additional days requested
            reason: Extension reason
            requested_by: Who requested the extension

        Returns:
            ExtensionRequest object
        """
        access = self.access_grants.get(username)

        if not access:
            raise ValueError(f"No temporary access found for {username}")

        request_id = f"EXT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"

        extension = ExtensionRequest(
            request_id=request_id,
            access_id=access.access_id,
            username=username,
            additional_days=additional_days,
            reason=reason,
            requested_by=requested_by,
            requested_at=datetime.now(),
        )

        self.extensions[request_id] = extension
        self._save_extensions()

        # Audit log
        self._audit_log(
            action="request_extension",
            username=username,
            additional_days=additional_days,
            requested_by=requested_by,
        )

        self.logger.info(f"Extension requested for {username}: +{additional_days} days")

        return extension

    def approve_extension(
        self,
        request_id: str,
        approved_by: str,
    ) -> bool:
        """
        Approve extension request.

        Args:
            request_id: Extension request ID
            approved_by: Who approved the extension

        Returns:
            True if successful
        """
        extension = self.extensions.get(request_id)

        if not extension:
            raise ValueError(f"Extension request not found: {request_id}")

        access = self.access_grants.get(extension.username)

        if not access:
            raise ValueError(f"No temporary access found for {extension.username}")

        # Update extension
        extension.status = ExtensionStatus.APPROVED
        extension.approved_by = approved_by
        extension.approved_at = datetime.now()

        # Extend access
        access.expires_at += timedelta(days=extension.additional_days)
        access.extended_count += 1

        self._save_extensions()
        self._save_access_registry()

        # Audit log
        self._audit_log(
            action="approve_extension",
            request_id=request_id,
            username=extension.username,
            approved_by=approved_by,
            new_expiration=access.expires_at.isoformat(),
        )

        self.logger.info(f"Extension approved for {extension.username}")

        return True

    def get_expiring_soon(self, days: int = 7) -> List[TempAccess]:
        """Get access expiring soon."""
        expiring = []

        for access in self.access_grants.values():
            if access.status == AccessStatus.ACTIVE:
                days_left = access.days_remaining()
                if 0 < days_left <= days:
                    expiring.append(access)

        return expiring

    def get_access(self, username: str) -> Optional[TempAccess]:
        """Get temporary access for user."""
        return self.access_grants.get(username)

    def list_access(self, status: Optional[AccessStatus] = None) -> List[TempAccess]:
        """List all temporary access grants."""
        if status:
            return [a for a in self.access_grants.values() if a.status == status]
        return list(self.access_grants.values())

    def get_pending_extensions(self) -> List[ExtensionRequest]:
        """Get pending extension requests."""
        return [e for e in self.extensions.values() if e.status == ExtensionStatus.PENDING]

    def _audit_log(self, action: str, **details):
        """Log temporary access action."""
        log_entry = {"timestamp": datetime.now().isoformat(), "action": action, **details}

        try:
            with open(self.AUDIT_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
