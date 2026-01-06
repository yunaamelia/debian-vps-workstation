"""
SSH Key Management and Rotation.

This module provides comprehensive SSH key lifecycle management including
key generation, deployment, rotation, and revocation.

Features:
- SSH key generation (Ed25519, RSA)
- Key deployment to authorized_keys
- Automatic key rotation with grace period
- Key inventory and monitoring
- Stale key detection
- Audit logging integration
"""

import json
import logging
import os
import pwd
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class KeyType(Enum):
    """SSH key algorithm types."""

    ED25519 = "ed25519"  # Recommended: modern, secure, fast
    RSA = "rsa"  # Legacy compatible, use 4096 bits
    ECDSA = "ecdsa"  # NIST curves
    DSA = "dsa"  # Deprecated, avoid


class KeyStatus(Enum):
    """SSH key status."""

    ACTIVE = "active"
    ROTATING = "rotating"  # In grace period during rotation
    EXPIRED = "expired"
    REVOKED = "revoked"
    STALE = "stale"  # Not used for long time
    UNMANAGED = "unmanaged"  # No metadata (legacy key)


@dataclass
class SSHKey:
    """
    Represents an SSH public key.

    Attributes:
        key_id: Unique identifier for the key
        user: System username the key belongs to
        public_key: Full public key string
        key_type: Algorithm type (Ed25519, RSA, etc.)
        fingerprint: SHA256 fingerprint
        created_at: When the key was created
        expires_at: Expiration date (None = never)
        last_used: Last successful authentication
        status: Current key status
        comment: Key comment (usually user@host)
        metadata: Additional key metadata

    Example:
        SSHKey(
            key_id="johndoe-laptop-2026-01-06",
            user="johndoe",
            public_key="ssh-ed25519 AAAAC3...",
            key_type=KeyType.ED25519,
            fingerprint="SHA256:abc123...",
            created_at=datetime(2026, 1, 6),
            expires_at=datetime(2026, 4, 6),
            status=KeyStatus.ACTIVE,
        )
    """

    key_id: str
    user: str
    public_key: str
    key_type: KeyType
    fingerprint: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    status: KeyStatus = KeyStatus.ACTIVE
    comment: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now()
        return delta.days

    def needs_rotation(self, threshold_days: int = 14) -> bool:
        """Check if key needs rotation soon."""
        days = self.days_until_expiry()
        if days is None:
            return False
        return days <= threshold_days

    def days_since_last_use(self) -> Optional[int]:
        """Calculate days since last use."""
        if self.last_used is None:
            return None
        delta = datetime.now() - self.last_used
        return delta.days

    def is_stale(self, inactive_days: int = 180) -> bool:
        """Check if key is stale (not used for long time)."""
        if self.last_used is None:
            # Never used, check age
            return (datetime.now() - self.created_at).days > inactive_days
        return self.days_since_last_use() > inactive_days

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "key_id": self.key_id,
            "user": self.user,
            "public_key": self.public_key,
            "key_type": self.key_type.value,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "status": self.status.value,
            "comment": self.comment,
            "metadata": self.metadata,
            "days_until_expiry": self.days_until_expiry(),
            "is_expired": self.is_expired(),
            "needs_rotation": self.needs_rotation(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SSHKey":
        """Deserialize from dictionary."""
        return cls(
            key_id=data["key_id"],
            user=data["user"],
            public_key=data.get("public_key", ""),
            key_type=KeyType(data["key_type"]),
            fingerprint=data["fingerprint"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            status=KeyStatus(data["status"]),
            comment=data.get("comment", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class KeyRotationResult:
    """Result of a key rotation operation."""

    success: bool
    old_key_id: str
    new_key: Optional[SSHKey] = None
    new_private_key_path: Optional[Path] = None
    grace_period_until: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class SSHSecurityStatus:
    """Current SSH security configuration status."""

    password_auth_enabled: bool
    root_login_enabled: bool
    empty_passwords_allowed: bool
    pubkey_auth_enabled: bool
    total_keys: int
    active_keys: int
    expiring_keys: int
    stale_keys: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "password_auth_enabled": self.password_auth_enabled,
            "root_login_enabled": self.root_login_enabled,
            "empty_passwords_allowed": self.empty_passwords_allowed,
            "pubkey_auth_enabled": self.pubkey_auth_enabled,
            "total_keys": self.total_keys,
            "active_keys": self.active_keys,
            "expiring_keys": self.expiring_keys,
            "stale_keys": self.stale_keys,
            "is_hardened": not self.password_auth_enabled and not self.root_login_enabled,
        }


class SSHKeyManager:
    """
    Manages SSH keys for users on the system.

    Features:
    - Generate SSH key pairs (Ed25519 recommended)
    - Deploy keys to authorized_keys
    - Key rotation with grace period
    - Key inventory and monitoring
    - Automatic key expiration
    - Stale key detection
    - Audit logging

    Usage:
        manager = SSHKeyManager()

        # Generate and deploy key
        key, private_path = manager.generate_key_pair(
            user="johndoe",
            key_id="johndoe-laptop"
        )
        manager.deploy_key(key)

        # Rotate key
        result = manager.rotate_key(
            user="johndoe",
            old_key_id="johndoe-laptop-old"
        )

        # List all keys
        keys = manager.list_keys(user="johndoe")
    """

    KEY_REGISTRY_DIR = Path("/var/lib/debian-vps-configurator")
    KEY_REGISTRY_FILE = KEY_REGISTRY_DIR / "ssh-keys.json"
    DEFAULT_KEY_TYPE = KeyType.ED25519
    DEFAULT_RSA_BITS = 4096
    DEFAULT_ROTATION_DAYS = 90
    GRACE_PERIOD_DAYS = 7
    STALE_THRESHOLD_DAYS = 180

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize SSHKeyManager.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._ensure_registry_dir()
        self._load_key_registry()

    def _ensure_registry_dir(self) -> None:
        """Ensure key registry directory exists."""
        try:
            self.KEY_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
            if self.KEY_REGISTRY_DIR.exists():
                self.KEY_REGISTRY_DIR.chmod(0o755)
        except (PermissionError, OSError) as e:
            self.logger.warning(
                f"Cannot create registry directory {self.KEY_REGISTRY_DIR}: {e}. "
                "Using in-memory registry only."
            )

    def _load_key_registry(self) -> None:
        """Load key registry from disk."""
        if self.KEY_REGISTRY_FILE.exists():
            try:
                with open(self.KEY_REGISTRY_FILE, "r") as f:
                    self._registry = json.load(f)
                self.logger.debug(f"Loaded key registry: {len(self._registry)} users")
            except (json.JSONDecodeError, PermissionError) as e:
                self.logger.error(f"Failed to load key registry: {e}")
                self._registry = {}
        else:
            self._registry = {}

    def _save_key_registry(self) -> bool:
        """
        Save key registry to disk.

        Returns:
            True if save was successful
        """
        try:
            with open(self.KEY_REGISTRY_FILE, "w") as f:
                json.dump(self._registry, f, indent=2)
            self.KEY_REGISTRY_FILE.chmod(0o600)  # Restrict permissions
            return True
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to save key registry: {e}")
            return False

    def _get_user_info(self, user: str) -> pwd.struct_passwd:
        """
        Get user information from system.

        Args:
            user: System username

        Returns:
            pwd.struct_passwd object

        Raises:
            ValueError: If user not found
        """
        try:
            return pwd.getpwnam(user)
        except KeyError:
            raise ValueError(f"User not found: {user}")

    def _get_ssh_dir(self, user: str) -> Path:
        """
        Get user's SSH directory, creating if needed.

        Args:
            user: System username

        Returns:
            Path to ~/.ssh directory
        """
        user_info = self._get_user_info(user)
        ssh_dir = Path(user_info.pw_dir) / ".ssh"

        if not ssh_dir.exists():
            ssh_dir.mkdir(mode=0o700)
            os.chown(ssh_dir, user_info.pw_uid, user_info.pw_gid)

        return ssh_dir

    def generate_key_pair(
        self,
        user: str,
        key_id: Optional[str] = None,
        key_type: KeyType = DEFAULT_KEY_TYPE,
        passphrase: Optional[str] = None,
        rotation_days: int = DEFAULT_ROTATION_DAYS,
        comment: Optional[str] = None,
    ) -> Tuple[SSHKey, Path]:
        """
        Generate SSH key pair.

        Args:
            user: System username
            key_id: Unique key identifier (auto-generated if None)
            key_type: Key algorithm type
            passphrase: Private key passphrase (None for no passphrase)
            rotation_days: Days until key expiration
            comment: Key comment (defaults to user@key_id)

        Returns:
            Tuple of (SSHKey object, private_key_path)

        Raises:
            ValueError: If user not found
            RuntimeError: If key generation fails
        """
        # Generate key ID if not provided
        if key_id is None:
            key_id = f"{user}-{datetime.now().strftime('%Y-%m-%d')}"

        self.logger.info(f"Generating SSH key pair for {user} (ID: {key_id})")

        # Get user info and SSH directory
        user_info = self._get_user_info(user)
        ssh_dir = self._get_ssh_dir(user)

        # Generate key paths
        private_key_path = ssh_dir / f"id_{key_type.value}_{key_id}"
        public_key_path = Path(str(private_key_path) + ".pub")

        # Check if key already exists
        if private_key_path.exists():
            raise ValueError(f"Key already exists: {private_key_path}")

        # Build comment
        if comment is None:
            comment = f"{user}@{key_id}"

        # Build ssh-keygen command
        cmd = [
            "ssh-keygen",
            "-t",
            key_type.value,
            "-f",
            str(private_key_path),
            "-C",
            comment,
        ]

        # Add key-specific options
        if key_type == KeyType.RSA:
            cmd.extend(["-b", str(self.DEFAULT_RSA_BITS)])
        elif key_type == KeyType.ECDSA:
            cmd.extend(["-b", "521"])  # Use strongest curve

        # Add passphrase
        if passphrase:
            cmd.extend(["-N", passphrase])
        else:
            cmd.extend(["-N", ""])  # No passphrase

        # Generate key
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            self.logger.info(f"Generated key pair: {private_key_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Key generation failed: {e.stderr}")
            raise RuntimeError(f"Failed to generate SSH key: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Key generation timed out")

        # Set proper permissions
        private_key_path.chmod(0o600)
        public_key_path.chmod(0o644)
        os.chown(private_key_path, user_info.pw_uid, user_info.pw_gid)
        os.chown(public_key_path, user_info.pw_uid, user_info.pw_gid)

        # Read public key
        public_key = public_key_path.read_text().strip()

        # Get fingerprint
        fingerprint = self._get_key_fingerprint(public_key_path)

        # Create SSHKey object
        ssh_key = SSHKey(
            key_id=key_id,
            user=user,
            public_key=public_key,
            key_type=key_type,
            fingerprint=fingerprint,
            created_at=datetime.now(),
            expires_at=(
                datetime.now() + timedelta(days=rotation_days) if rotation_days > 0 else None
            ),
            comment=comment,
            metadata={
                "private_key_path": str(private_key_path),
                "public_key_path": str(public_key_path),
                "rotation_days": rotation_days,
                "generated_by": "vps-configurator",
            },
        )

        # Register key
        self._register_key(ssh_key)

        return ssh_key, private_key_path

    def _get_key_fingerprint(self, public_key_path: Path) -> str:
        """
        Get SHA256 fingerprint of public key.

        Args:
            public_key_path: Path to public key file

        Returns:
            Fingerprint string (e.g., "SHA256:abc123...")
        """
        try:
            result = subprocess.run(
                ["ssh-keygen", "-l", str(public_key_path), "-E", "sha256"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            # Parse fingerprint from output
            # Format: "256 SHA256:abc123... user@host (ED25519)"
            match = re.search(r"(SHA256:[^\s]+)", result.stdout)
            if match:
                return match.group(1)
            else:
                return "SHA256:unknown"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return "SHA256:unknown"

    def _get_fingerprint_from_pubkey(self, public_key: str) -> str:
        """
        Get fingerprint from public key string.

        Args:
            public_key: Public key string

        Returns:
            Fingerprint string
        """
        try:
            result = subprocess.run(
                ["ssh-keygen", "-l", "-", "-E", "sha256"],
                input=public_key,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            match = re.search(r"(SHA256:[^\s]+)", result.stdout)
            if match:
                return match.group(1)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        return "SHA256:unknown"

    def _register_key(self, key: SSHKey) -> None:
        """
        Register key in registry.

        Args:
            key: SSHKey object to register
        """
        key_data = key.to_dict()

        if key.user not in self._registry:
            self._registry[key.user] = {}

        self._registry[key.user][key.key_id] = key_data
        self._save_key_registry()

        self.logger.debug(f"Registered key {key.key_id} for user {key.user}")

    def deploy_key(self, key: SSHKey) -> bool:
        """
        Deploy public key to user's authorized_keys.

        Args:
            key: SSHKey object

        Returns:
            True if successful

        Raises:
            ValueError: If user not found
        """
        self.logger.info(f"Deploying key {key.key_id} for user {key.user}")

        # Get user info
        user_info = self._get_user_info(key.user)
        ssh_dir = self._get_ssh_dir(key.user)
        authorized_keys = ssh_dir / "authorized_keys"

        # Read existing keys
        existing_lines: List[str] = []
        if authorized_keys.exists():
            existing_lines = [
                line.strip() for line in authorized_keys.read_text().split("\n") if line.strip()
            ]

        # Extract just the key part (without comment) for comparison
        key_parts = key.public_key.split()
        key_data = f"{key_parts[0]} {key_parts[1]}" if len(key_parts) >= 2 else key.public_key

        # Check if key already exists
        for line in existing_lines:
            if key_data in line:
                self.logger.info(f"Key already exists in {authorized_keys}")
                return True

        # Add new key with metadata comment
        expires_str = key.expires_at.isoformat() if key.expires_at else "never"
        key_line = f"{key.public_key} " f"# MANAGED KEY_ID={key.key_id} EXPIRES={expires_str}"

        existing_lines.append(key_line)

        # Write back
        authorized_keys.write_text("\n".join(existing_lines) + "\n")
        authorized_keys.chmod(0o600)
        os.chown(authorized_keys, user_info.pw_uid, user_info.pw_gid)

        self.logger.info(f"✅ Key deployed to {authorized_keys}")
        return True

    def rotate_key(
        self,
        user: str,
        old_key_id: str,
        grace_period_days: int = GRACE_PERIOD_DAYS,
    ) -> KeyRotationResult:
        """
        Rotate SSH key for user.

        Process:
        1. Generate new key pair
        2. Deploy new key to authorized_keys
        3. Mark old key as "rotating" (grace period)
        4. Schedule old key removal after grace period

        Args:
            user: System username
            old_key_id: Key ID to rotate
            grace_period_days: Days both keys are valid

        Returns:
            KeyRotationResult object
        """
        self.logger.info(f"Rotating key {old_key_id} for user {user}")

        # Get old key
        old_key = self.get_key(user, old_key_id)
        if not old_key:
            return KeyRotationResult(
                success=False, old_key_id=old_key_id, error=f"Key not found: {old_key_id}"
            )

        try:
            # Generate new key
            new_key_id = f"{user}-{datetime.now().strftime('%Y-%m-%d')}"

            # Avoid duplicate key IDs
            counter = 1
            base_key_id = new_key_id
            while self.get_key(user, new_key_id):
                new_key_id = f"{base_key_id}-{counter}"
                counter += 1

            new_key, private_key_path = self.generate_key_pair(
                user=user,
                key_id=new_key_id,
                key_type=old_key.key_type,
            )

            # Deploy new key
            self.deploy_key(new_key)

            # Mark old key as rotating
            grace_until = datetime.now() + timedelta(days=grace_period_days)
            old_key.status = KeyStatus.ROTATING
            old_key.metadata["grace_period_until"] = grace_until.isoformat()
            old_key.metadata["replaced_by"] = new_key_id
            self._register_key(old_key)

            self.logger.info(f"✅ Key rotation complete. Grace period: {grace_period_days} days")

            return KeyRotationResult(
                success=True,
                old_key_id=old_key_id,
                new_key=new_key,
                new_private_key_path=private_key_path,
                grace_period_until=grace_until,
            )

        except Exception as e:
            self.logger.error(f"Key rotation failed: {e}")
            return KeyRotationResult(success=False, old_key_id=old_key_id, error=str(e))

    def revoke_key(self, user: str, key_id: str) -> bool:
        """
        Revoke SSH key (remove from authorized_keys).

        Args:
            user: System username
            key_id: Key ID to revoke

        Returns:
            True if successful

        Raises:
            ValueError: If key not found
        """
        self.logger.info(f"Revoking key {key_id} for user {user}")

        key = self.get_key(user, key_id)
        if not key:
            raise ValueError(f"Key not found: {key_id}")

        # Get authorized_keys
        user_info = self._get_user_info(user)
        authorized_keys = Path(user_info.pw_dir) / ".ssh" / "authorized_keys"

        if not authorized_keys.exists():
            self.logger.warning(f"authorized_keys not found for {user}")
            # Still update registry
            key.status = KeyStatus.REVOKED
            self._register_key(key)
            return True

        # Read and filter keys
        lines = authorized_keys.read_text().strip().split("\n")

        # Extract key data for comparison
        key_parts = key.public_key.split()
        key_data = f"{key_parts[0]} {key_parts[1]}" if len(key_parts) >= 2 else key.public_key

        filtered_lines = [line for line in lines if line.strip() and key_data not in line]

        # Write back
        authorized_keys.write_text("\n".join(filtered_lines) + "\n")

        # Update registry
        key.status = KeyStatus.REVOKED
        key.metadata["revoked_at"] = datetime.now().isoformat()
        self._register_key(key)

        self.logger.info("✅ Key revoked and removed from authorized_keys")
        return True

    def get_key(self, user: str, key_id: str) -> Optional[SSHKey]:
        """
        Get SSH key by ID.

        Args:
            user: System username
            key_id: Key ID to retrieve

        Returns:
            SSHKey object or None if not found
        """
        user_keys = self._registry.get(user, {})
        key_data = user_keys.get(key_id)

        if not key_data:
            return None

        return SSHKey.from_dict(key_data)

    def list_keys(self, user: Optional[str] = None) -> List[SSHKey]:
        """
        List SSH keys.

        Args:
            user: Filter by user (None for all users)

        Returns:
            List of SSHKey objects
        """
        keys: List[SSHKey] = []

        if user:
            user_keys = self._registry.get(user, {})
            for key_id in user_keys:
                key = self.get_key(user, key_id)
                if key:
                    keys.append(key)
        else:
            # All users
            for username in self._registry:
                keys.extend(self.list_keys(user=username))

        return keys

    def detect_stale_keys(self, inactive_days: int = STALE_THRESHOLD_DAYS) -> List[SSHKey]:
        """
        Detect stale keys (not used for long time).

        Args:
            inactive_days: Days of inactivity to consider stale

        Returns:
            List of stale SSH keys
        """
        stale: List[SSHKey] = []

        for key in self.list_keys():
            if key.status in (KeyStatus.REVOKED, KeyStatus.EXPIRED):
                continue

            if key.is_stale(inactive_days):
                stale.append(key)

        return stale

    def detect_expiring_keys(self, threshold_days: int = 14) -> List[SSHKey]:
        """
        Detect keys expiring soon.

        Args:
            threshold_days: Days threshold for expiring soon

        Returns:
            List of expiring SSH keys
        """
        expiring: List[SSHKey] = []

        for key in self.list_keys():
            if key.status in (KeyStatus.REVOKED, KeyStatus.EXPIRED):
                continue

            if key.needs_rotation(threshold_days):
                expiring.append(key)

        return expiring

    def cleanup_grace_period_keys(self) -> int:
        """
        Remove keys whose grace period has expired.

        Returns:
            Number of keys removed
        """
        removed = 0
        now = datetime.now()

        for key in self.list_keys():
            if key.status != KeyStatus.ROTATING:
                continue

            grace_until = key.metadata.get("grace_period_until")
            if grace_until:
                grace_date = datetime.fromisoformat(grace_until)
                if now > grace_date:
                    self.logger.info(f"Grace period expired for {key.key_id}, revoking")
                    try:
                        self.revoke_key(key.user, key.key_id)
                        removed += 1
                    except Exception as e:
                        self.logger.error(f"Failed to revoke {key.key_id}: {e}")

        return removed

    def scan_authorized_keys(self, user: str) -> List[SSHKey]:
        """
        Scan authorized_keys for unmanaged keys.

        Args:
            user: System username

        Returns:
            List of unmanaged SSHKey objects
        """
        unmanaged: List[SSHKey] = []

        try:
            user_info = self._get_user_info(user)
            authorized_keys = Path(user_info.pw_dir) / ".ssh" / "authorized_keys"

            if not authorized_keys.exists():
                return unmanaged

            lines = authorized_keys.read_text().strip().split("\n")

            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Check if this is a managed key
                if "KEY_ID=" in line:
                    continue  # Managed key

                # Parse key
                parts = line.split()
                if len(parts) < 2:
                    continue

                key_type_str = parts[0]
                parts[1]
                comment = parts[2] if len(parts) > 2 else f"unmanaged-{i}"

                # Determine key type
                key_type = KeyType.ED25519  # Default
                if "rsa" in key_type_str.lower():
                    key_type = KeyType.RSA
                elif "ecdsa" in key_type_str.lower():
                    key_type = KeyType.ECDSA
                elif "dsa" in key_type_str.lower():
                    key_type = KeyType.DSA

                # Get fingerprint
                fingerprint = self._get_fingerprint_from_pubkey(line)

                unmanaged_key = SSHKey(
                    key_id=f"unmanaged-{i}",
                    user=user,
                    public_key=line,
                    key_type=key_type,
                    fingerprint=fingerprint,
                    created_at=datetime.now(),  # Unknown
                    status=KeyStatus.UNMANAGED,
                    comment=comment,
                    metadata={"line_number": i + 1},
                )
                unmanaged.append(unmanaged_key)

        except Exception as e:
            self.logger.error(f"Failed to scan authorized_keys: {e}")

        return unmanaged

    def import_key(
        self,
        user: str,
        public_key: str,
        key_id: Optional[str] = None,
        rotation_days: int = DEFAULT_ROTATION_DAYS,
    ) -> SSHKey:
        """
        Import an existing public key into management.

        Args:
            user: System username
            public_key: Public key string
            key_id: Key identifier
            rotation_days: Days until expiration

        Returns:
            SSHKey object
        """
        if key_id is None:
            key_id = f"{user}-imported-{datetime.now().strftime('%Y-%m-%d')}"

        # Parse key type
        parts = public_key.strip().split()
        key_type_str = parts[0] if parts else "ssh-ed25519"

        key_type = KeyType.ED25519
        if "rsa" in key_type_str.lower():
            key_type = KeyType.RSA
        elif "ecdsa" in key_type_str.lower():
            key_type = KeyType.ECDSA

        # Get fingerprint
        fingerprint = self._get_fingerprint_from_pubkey(public_key)

        ssh_key = SSHKey(
            key_id=key_id,
            user=user,
            public_key=public_key.strip(),
            key_type=key_type,
            fingerprint=fingerprint,
            created_at=datetime.now(),
            expires_at=(
                datetime.now() + timedelta(days=rotation_days) if rotation_days > 0 else None
            ),
            comment=parts[2] if len(parts) > 2 else "",
            metadata={"imported": True},
        )

        self._register_key(ssh_key)
        self.logger.info(f"Imported key {key_id} for user {user}")

        return ssh_key

    def get_key_summary(self) -> Dict[str, Any]:
        """
        Get summary of all managed keys.

        Returns:
            Summary dictionary with counts and status
        """
        all_keys = self.list_keys()

        active = sum(1 for k in all_keys if k.status == KeyStatus.ACTIVE)
        rotating = sum(1 for k in all_keys if k.status == KeyStatus.ROTATING)
        expired = sum(1 for k in all_keys if k.is_expired())
        expiring = sum(1 for k in all_keys if k.needs_rotation())
        stale = len(self.detect_stale_keys())

        return {
            "total": len(all_keys),
            "active": active,
            "rotating": rotating,
            "expired": expired,
            "expiring_soon": expiring,
            "stale": stale,
            "users": list(self._registry.keys()),
        }
