"""
Multi-Factor Authentication (MFA) Manager.

This module provides comprehensive 2FA/MFA support including TOTP
(Google Authenticator), backup codes, and PAM integration.
"""

import io
import json
import logging
import os
import secrets
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pyotp
    import qrcode

    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False


class MFAMethod(Enum):
    """Multi-factor authentication methods."""

    TOTP = "totp"  # Time-based OTP (Google Authenticator)
    SMS = "sms"  # SMS verification (requires external service)
    BACKUP_CODE = "backup"  # One-time backup codes
    HARDWARE = "hardware"  # Hardware token (YubiKey, etc.)


class MFAStatus(Enum):
    """MFA enrollment status."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING = "pending"  # Enrolled but not verified
    LOCKED = "locked"  # Too many failed attempts


@dataclass
class MFAConfig:
    """
    MFA configuration for a user.

    Attributes:
        user: System username
        method: MFA method (TOTP, SMS, etc.)
        secret: TOTP secret key (base32)
        backup_codes: List of one-time backup codes
        enabled: Whether MFA is active
        enrolled_at: Enrollment timestamp
        last_used: Last successful verification
        failed_attempts: Consecutive failed attempts
        status: Current MFA status
    """

    user: str
    method: MFAMethod
    secret: str
    backup_codes: List[str] = field(default_factory=list)
    enabled: bool = False
    enrolled_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    failed_attempts: int = 0
    status: MFAStatus = MFAStatus.PENDING

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "user": self.user,
            "method": self.method.value,
            "secret": self.secret,
            "backup_codes": self.backup_codes,
            "enabled": self.enabled,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "failed_attempts": self.failed_attempts,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MFAConfig":
        """Deserialize from dictionary."""
        return cls(
            user=data["user"],
            method=MFAMethod(data["method"]),
            secret=data["secret"],
            backup_codes=data.get("backup_codes", []),
            enabled=data.get("enabled", False),
            enrolled_at=(
                datetime.fromisoformat(data["enrolled_at"]) if data.get("enrolled_at") else None
            ),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            failed_attempts=data.get("failed_attempts", 0),
            status=MFAStatus(data.get("status", "pending")),
        )

    def backup_codes_remaining(self) -> int:
        """Return number of backup codes remaining."""
        return len(self.backup_codes)

    def is_locked(self) -> bool:
        """Check if account is locked."""
        return self.status == MFAStatus.LOCKED


class MFAManager:
    """
    Manages multi-factor authentication for system users.

    Features:
    - TOTP (Google Authenticator) setup
    - QR code generation for easy enrollment
    - Backup codes for emergency access
    - Integration with PAM for SSH/sudo
    - Failed attempt tracking and lockout
    - Audit logging

    Usage:
        manager = MFAManager()

        # Enroll user
        config, qr = manager.enroll_user("johndoe")

        # Verify code
        is_valid = manager.verify_code("johndoe", "123456")

        # Check status
        config = manager.get_user_config("johndoe")
    """

    MFA_CONFIG_DIR = Path("/var/lib/debian-vps-configurator/mfa")
    BACKUP_CODE_COUNT = 10
    MAX_FAILED_ATTEMPTS = 5
    DEFAULT_ISSUER = "Debian VPS Configurator"

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize MFAManager.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._configs: Dict[str, MFAConfig] = {}
        self._ensure_config_dir()
        self._load_configs()

    def _ensure_config_dir(self) -> None:
        """Ensure MFA config directory exists."""
        try:
            self.MFA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if self.MFA_CONFIG_DIR.exists():
                self.MFA_CONFIG_DIR.chmod(0o700)
        except (PermissionError, OSError) as e:
            self.logger.warning(
                f"Cannot create MFA config directory {self.MFA_CONFIG_DIR}: {e}. "
                "Using in-memory storage only."
            )

    def _load_configs(self) -> None:
        """Load all MFA configurations from disk."""
        config_file = self.MFA_CONFIG_DIR / "mfa-config.json"

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)

                for user, config_data in data.items():
                    self._configs[user] = MFAConfig.from_dict(config_data)

                self.logger.info(f"Loaded MFA configs for {len(self._configs)} users")
            except Exception as e:
                self.logger.error(f"Failed to load MFA configs: {e}")

    def _save_configs(self) -> None:
        """Save all MFA configurations to disk."""
        config_file = self.MFA_CONFIG_DIR / "mfa-config.json"

        try:
            data = {user: config.to_dict() for user, config in self._configs.items()}

            with open(config_file, "w") as f:
                json.dump(data, f, indent=2)

            config_file.chmod(0o600)
        except Exception as e:
            self.logger.error(f"Failed to save MFA configs: {e}")

    def enroll_user(
        self,
        user: str,
        method: MFAMethod = MFAMethod.TOTP,
        issuer: str = DEFAULT_ISSUER,
    ) -> Tuple[MFAConfig, str]:
        """
        Enroll user in MFA.

        Args:
            user: System username
            method: MFA method (default: TOTP)
            issuer: Issuer name for authenticator app

        Returns:
            Tuple of (MFAConfig, QR code ASCII string)
        """
        if not PYOTP_AVAILABLE:
            raise RuntimeError("pyotp not installed. Run: pip install pyotp qrcode")

        self.logger.info(f"Enrolling {user} in MFA (method: {method.value})")

        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Generate backup codes
        backup_codes = self._generate_backup_codes()

        # Create config
        config = MFAConfig(
            user=user,
            method=method,
            secret=secret,
            backup_codes=backup_codes,
            enabled=False,  # Not enabled until verified
            enrolled_at=datetime.now(),
            status=MFAStatus.PENDING,
        )

        # Save config
        self._configs[user] = config
        self._save_configs()

        # Save backup codes to user's home directory
        self._save_backup_codes_file(user, backup_codes)

        # Generate QR code
        qr_code = self.generate_qr_code(config, issuer)

        self.logger.info(f"✅ User {user} enrolled in MFA")

        return config, qr_code

    def _generate_backup_codes(self, count: Optional[int] = None) -> List[str]:
        """Generate one-time backup codes."""
        if count is None:
            count = self.BACKUP_CODE_COUNT

        codes = []
        for _ in range(count):
            # Generate 12-character code (format: XXXX-XXXX-XXXX)
            code_bytes = secrets.token_bytes(6)
            code = code_bytes.hex().upper()
            formatted = f"{code[0:4]}-{code[4:8]}-{code[8:12]}"
            codes.append(formatted)

        return codes

    def _save_backup_codes_file(self, user: str, backup_codes: List[str]) -> None:
        """Save backup codes to user's home directory."""
        import pwd

        try:
            user_info = pwd.getpwnam(user)
            home_dir = Path(user_info.pw_dir)

            backup_file = home_dir / ".mfa-backup-codes.txt"

            with open(backup_file, "w") as f:
                f.write("Multi-Factor Authentication Backup Codes\n")
                f.write(f"User: {user}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("\n")
                f.write("⚠️  IMPORTANT: Keep these codes secure!\n")
                f.write("Each code can only be used once.\n")
                f.write("\n")

                for i, code in enumerate(backup_codes, 1):
                    f.write(f"{i:2d}. {code}\n")

            # Secure permissions
            backup_file.chmod(0o600)
            os.chown(backup_file, user_info.pw_uid, user_info.pw_gid)

            self.logger.info(f"Backup codes saved to {backup_file}")

        except KeyError:
            self.logger.warning(f"User {user} not found, skipping backup file")
        except Exception as e:
            self.logger.error(f"Failed to save backup codes: {e}")

    def generate_qr_code(self, config: MFAConfig, issuer: str = DEFAULT_ISSUER) -> str:
        """
        Generate ASCII QR code for TOTP enrollment.

        Args:
            config: MFAConfig object
            issuer: Issuer name shown in authenticator app

        Returns:
            ASCII art QR code string
        """
        if not PYOTP_AVAILABLE:
            return "[QR code unavailable - pyotp not installed]"

        # Generate TOTP URI
        totp = pyotp.TOTP(config.secret)
        uri = totp.provisioning_uri(name=config.user, issuer_name=issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Get ASCII representation
        buffer = io.StringIO()
        qr.print_ascii(out=buffer)

        return buffer.getvalue()

    def get_totp_uri(self, config: MFAConfig, issuer: str = DEFAULT_ISSUER) -> str:
        """Get TOTP provisioning URI."""
        if not PYOTP_AVAILABLE:
            return ""

        totp = pyotp.TOTP(config.secret)
        return totp.provisioning_uri(name=config.user, issuer_name=issuer)

    def verify_code(
        self,
        user: str,
        code: str,
        allow_backup: bool = True,
    ) -> bool:
        """
        Verify MFA code.

        Args:
            user: Username
            code: 6-digit TOTP code or backup code
            allow_backup: Allow backup codes

        Returns:
            True if valid
        """
        if not PYOTP_AVAILABLE:
            self.logger.error("pyotp not installed")
            return False

        config = self._configs.get(user)

        if not config:
            self.logger.warning(f"MFA not configured for user: {user}")
            return False

        if config.status == MFAStatus.LOCKED:
            self.logger.warning(f"MFA locked for user {user} (too many failed attempts)")
            return False

        # Normalize code (remove dashes for backup codes)
        normalized_code = code.replace("-", "").strip()

        # Try TOTP verification
        totp = pyotp.TOTP(config.secret)

        if totp.verify(normalized_code, valid_window=1):  # Allow 30s time drift
            # Valid TOTP code
            config.last_used = datetime.now()
            config.failed_attempts = 0

            # Enable MFA if this is first successful verification
            if config.status == MFAStatus.PENDING:
                config.enabled = True
                config.status = MFAStatus.ENABLED
                self.logger.info(f"✅ MFA enabled for {user}")

            self._save_configs()
            self.logger.info(f"✅ TOTP verification successful for {user}")
            return True

        # Try backup code (with dashes)
        if allow_backup and code in config.backup_codes:
            # Valid backup code - remove it
            config.backup_codes.remove(code)
            config.last_used = datetime.now()
            config.failed_attempts = 0

            self._save_configs()

            remaining = len(config.backup_codes)
            self.logger.info(f"✅ Backup code accepted for {user} ({remaining} remaining)")

            return True

        # Invalid code
        config.failed_attempts += 1

        if config.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            config.status = MFAStatus.LOCKED
            self.logger.warning(
                f"🚨 MFA locked for {user} after {config.failed_attempts} failed attempts"
            )

        self._save_configs()

        self.logger.warning(
            f"❌ MFA verification failed for {user} (attempt {config.failed_attempts})"
        )
        return False

    def disable_mfa(self, user: str, backup_code: Optional[str] = None) -> bool:
        """
        Disable MFA for user.

        Args:
            user: Username
            backup_code: Backup code for verification (required if MFA enabled)

        Returns:
            True if disabled
        """
        config = self._configs.get(user)

        if not config:
            self.logger.warning(f"MFA not configured for {user}")
            return False

        # If MFA is enabled, require backup code
        if config.enabled and config.status != MFAStatus.LOCKED:
            if not backup_code:
                self.logger.error("Backup code required to disable MFA")
                return False

            if backup_code not in config.backup_codes:
                self.logger.error("Invalid backup code")
                return False

        # Disable MFA
        config.enabled = False
        config.status = MFAStatus.DISABLED
        self._save_configs()

        self.logger.info(f"✅ MFA disabled for {user}")
        return True

    def unlock_user(self, user: str) -> bool:
        """
        Unlock a locked MFA account.

        Args:
            user: Username

        Returns:
            True if unlocked
        """
        config = self._configs.get(user)

        if not config:
            return False

        if config.status == MFAStatus.LOCKED:
            config.status = MFAStatus.ENABLED
            config.failed_attempts = 0
            self._save_configs()
            self.logger.info(f"✅ MFA unlocked for {user}")
            return True

        return False

    def regenerate_backup_codes(self, user: str) -> List[str]:
        """
        Regenerate backup codes for user.

        Args:
            user: Username

        Returns:
            New backup codes
        """
        config = self._configs.get(user)

        if not config:
            raise ValueError(f"MFA not configured for {user}")

        # Generate new codes
        new_codes = self._generate_backup_codes()
        config.backup_codes = new_codes

        self._save_configs()
        self._save_backup_codes_file(user, new_codes)

        self.logger.info(f"✅ Backup codes regenerated for {user}")

        return new_codes

    def get_user_config(self, user: str) -> Optional[MFAConfig]:
        """Get MFA configuration for user."""
        return self._configs.get(user)

    def list_users(self) -> List[str]:
        """List users with MFA configured."""
        return list(self._configs.keys())

    def get_summary(self) -> Dict:
        """Get MFA summary statistics."""
        total = len(self._configs)
        enabled = sum(1 for c in self._configs.values() if c.enabled)
        pending = sum(1 for c in self._configs.values() if c.status == MFAStatus.PENDING)
        locked = sum(1 for c in self._configs.values() if c.status == MFAStatus.LOCKED)

        return {
            "total": total,
            "enabled": enabled,
            "pending": pending,
            "locked": locked,
            "disabled": total - enabled - pending,
        }

    def configure_pam(self, enable_for_ssh: bool = True, enable_for_sudo: bool = False) -> bool:
        """
        Configure PAM (Pluggable Authentication Modules) for MFA.

        Args:
            enable_for_ssh: Enable MFA for SSH
            enable_for_sudo: Enable MFA for sudo

        Returns:
            True if configuration successful
        """
        self.logger.info("Configuring PAM for MFA...")

        # Check if libpam-google-authenticator is installed
        try:
            result = subprocess.run(
                ["dpkg", "-s", "libpam-google-authenticator"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.info("Installing libpam-google-authenticator...")
                subprocess.run(
                    ["apt-get", "install", "-y", "libpam-google-authenticator"],
                    check=True,
                    capture_output=True,
                )
                self.logger.info("✅ Installed libpam-google-authenticator")
        except Exception as e:
            self.logger.error(f"Failed to install PAM module: {e}")
            return False

        # Configure SSH PAM
        if enable_for_ssh:
            if not self._configure_ssh_pam():
                return False

        # Configure sudo PAM
        if enable_for_sudo:
            if not self._configure_sudo_pam():
                return False

        return True

    def _configure_ssh_pam(self) -> bool:
        """Configure PAM for SSH."""
        pam_sshd = Path("/etc/pam.d/sshd")

        if not pam_sshd.exists():
            self.logger.error("PAM sshd config not found")
            return False

        # Backup
        backup = Path("/etc/pam.d/sshd.backup-mfa")
        if not backup.exists():
            shutil.copy2(pam_sshd, backup)
            self.logger.info(f"Created backup: {backup}")

        # Read current config
        content = pam_sshd.read_text()

        # Check if already configured
        if "pam_google_authenticator.so" in content:
            self.logger.info("SSH PAM already configured for MFA")
            return True

        # Add after @include common-auth
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            new_lines.append(line)
            if "@include common-auth" in line:
                new_lines.append("auth required pam_google_authenticator.so nullok")

        pam_sshd.write_text("\n".join(new_lines))

        # Configure sshd_config
        sshd_config = Path("/etc/ssh/sshd_config")
        config_content = sshd_config.read_text()

        updates = []

        # Enable ChallengeResponseAuthentication
        if "ChallengeResponseAuthentication yes" not in config_content:
            updates.append("ChallengeResponseAuthentication yes")

        # Add AuthenticationMethods if not present
        if "AuthenticationMethods" not in config_content:
            updates.append("AuthenticationMethods publickey,keyboard-interactive")

        if updates:
            with open(sshd_config, "a") as f:
                f.write("\n# MFA Configuration\n")
                for update in updates:
                    f.write(f"{update}\n")

        # Reload SSH
        try:
            subprocess.run(["systemctl", "reload", "sshd"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            subprocess.run(["systemctl", "reload", "ssh"], check=True, capture_output=True)

        self.logger.info("✅ SSH PAM configured for MFA")
        return True

    def _configure_sudo_pam(self) -> bool:
        """Configure PAM for sudo."""
        pam_sudo = Path("/etc/pam.d/sudo")

        if not pam_sudo.exists():
            self.logger.error("PAM sudo config not found")
            return False

        # Backup
        backup = Path("/etc/pam.d/sudo.backup-mfa")
        if not backup.exists():
            shutil.copy2(pam_sudo, backup)

        content = pam_sudo.read_text()

        if "pam_google_authenticator.so" in content:
            self.logger.info("sudo PAM already configured for MFA")
            return True

        lines = content.split("\n")
        new_lines = []

        for line in lines:
            new_lines.append(line)
            if "@include common-auth" in line:
                new_lines.append("auth required pam_google_authenticator.so nullok")

        pam_sudo.write_text("\n".join(new_lines))

        self.logger.info("✅ sudo PAM configured for MFA")
        return True

    def generate_google_authenticator_file(self, user: str) -> bool:
        """
        Generate ~/.google_authenticator file for user.

        This file is required by pam_google_authenticator.

        Args:
            user: Username

        Returns:
            True if successful
        """
        import pwd

        config = self._configs.get(user)
        if not config:
            self.logger.error(f"MFA not configured for {user}")
            return False

        try:
            user_info = pwd.getpwnam(user)
            home_dir = Path(user_info.pw_dir)

            ga_file = home_dir / ".google_authenticator"

            # Format for pam_google_authenticator
            lines = [
                config.secret,
                '" RATE_LIMIT 3 30',
                '" WINDOW_SIZE 17',
                '" DISALLOW_REUSE',
                '" TOTP_AUTH',
            ]

            # Add backup codes (scratch codes)
            for code in config.backup_codes:
                # Convert format: XXXX-XXXX-XXXX -> 8-digit number
                clean = code.replace("-", "")
                lines.append(clean[:8])

            ga_file.write_text("\n".join(lines) + "\n")
            ga_file.chmod(0o600)
            os.chown(ga_file, user_info.pw_uid, user_info.pw_gid)

            self.logger.info(f"✅ Generated .google_authenticator for {user}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate .google_authenticator: {e}")
            return False
