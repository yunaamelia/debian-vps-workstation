"""
SSH Daemon Hardening.

This module provides SSH daemon configuration management for security hardening,
including disabling password authentication, root login, and other security settings.
"""

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SSHDConfig:
    """Current sshd_config settings."""

    password_authentication: bool
    challenge_response_authentication: bool
    permit_root_login: str  # "yes", "no", "prohibit-password", "forced-commands-only"
    permit_empty_passwords: bool
    pubkey_authentication: bool
    max_auth_tries: int
    client_alive_interval: int
    client_alive_count_max: int
    x11_forwarding: bool
    allow_tcp_forwarding: bool

    def is_hardened(self) -> bool:
        """Check if SSH is properly hardened."""
        return (
            not self.password_authentication
            and not self.challenge_response_authentication
            and self.permit_root_login == "no"
            and not self.permit_empty_passwords
            and self.pubkey_authentication
        )

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "password_authentication": self.password_authentication,
            "challenge_response_authentication": self.challenge_response_authentication,
            "permit_root_login": self.permit_root_login,
            "permit_empty_passwords": self.permit_empty_passwords,
            "pubkey_authentication": self.pubkey_authentication,
            "max_auth_tries": self.max_auth_tries,
            "client_alive_interval": self.client_alive_interval,
            "client_alive_count_max": self.client_alive_count_max,
            "x11_forwarding": self.x11_forwarding,
            "allow_tcp_forwarding": self.allow_tcp_forwarding,
            "is_hardened": self.is_hardened(),
        }


class SSHDConfigManager:
    """
    Manages SSH daemon configuration for security hardening.

    Features:
    - Parse current sshd_config
    - Apply security hardening settings
    - Backup before modifications
    - Validate configuration syntax
    - Safely reload SSH daemon

    Usage:
        manager = SSHDConfigManager()

        # Get current settings
        config = manager.get_current_config()

        # Apply hardening
        manager.harden()
    """

    SSHD_CONFIG_PATH = Path("/etc/ssh/sshd_config")
    SSHD_CONFIG_DIR = Path("/etc/ssh/sshd_config.d")
    BACKUP_SUFFIX = ".backup-vps-configurator"

    # Security hardening settings
    HARDENING_SETTINGS = {
        "PasswordAuthentication": "no",
        "ChallengeResponseAuthentication": "no",
        "PermitRootLogin": "no",
        "PermitEmptyPasswords": "no",
        "PubkeyAuthentication": "yes",
        "MaxAuthTries": "3",
        "ClientAliveInterval": "300",
        "ClientAliveCountMax": "2",
        "X11Forwarding": "no",
        "AllowTcpForwarding": "no",
        "Protocol": "2",
    }

    def __init__(self, config_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize SSHDConfigManager.

        Args:
            config_path: Custom path to sshd_config
            logger: Optional logger instance
        """
        self.config_path = config_path or self.SSHD_CONFIG_PATH
        self.logger = logger or logging.getLogger(__name__)

    def _parse_bool_value(self, value: str) -> bool:
        """Parse boolean value from sshd_config."""
        return value.lower() in ("yes", "true", "1")

    def _parse_int_value(self, value: str, default: int = 0) -> int:
        """Parse integer value from sshd_config."""
        try:
            return int(value)
        except ValueError:
            return default

    def get_current_config(self) -> SSHDConfig:
        """
        Parse and return current sshd_config settings.

        Returns:
            SSHDConfig object with current settings
        """
        settings = {
            "PasswordAuthentication": "yes",
            "ChallengeResponseAuthentication": "yes",
            "PermitRootLogin": "yes",
            "PermitEmptyPasswords": "no",
            "PubkeyAuthentication": "yes",
            "MaxAuthTries": "6",
            "ClientAliveInterval": "0",
            "ClientAliveCountMax": "3",
            "X11Forwarding": "yes",
            "AllowTcpForwarding": "yes",
        }

        if self.config_path.exists():
            try:
                content = self.config_path.read_text()

                for line in content.split("\n"):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse key-value pairs
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        if key in settings:
                            settings[key] = value

            except PermissionError:
                self.logger.warning("Cannot read sshd_config (permission denied)")

        return SSHDConfig(
            password_authentication=self._parse_bool_value(settings["PasswordAuthentication"]),
            challenge_response_authentication=self._parse_bool_value(
                settings["ChallengeResponseAuthentication"]
            ),
            permit_root_login=settings["PermitRootLogin"].lower(),
            permit_empty_passwords=self._parse_bool_value(settings["PermitEmptyPasswords"]),
            pubkey_authentication=self._parse_bool_value(settings["PubkeyAuthentication"]),
            max_auth_tries=self._parse_int_value(settings["MaxAuthTries"], 6),
            client_alive_interval=self._parse_int_value(settings["ClientAliveInterval"], 0),
            client_alive_count_max=self._parse_int_value(settings["ClientAliveCountMax"], 3),
            x11_forwarding=self._parse_bool_value(settings["X11Forwarding"]),
            allow_tcp_forwarding=self._parse_bool_value(settings["AllowTcpForwarding"]),
        )

    def backup_config(self) -> Path:
        """
        Create backup of current sshd_config.

        Returns:
            Path to backup file
        """
        backup_path = Path(str(self.config_path) + self.BACKUP_SUFFIX)

        if not backup_path.exists() and self.config_path.exists():
            shutil.copy2(self.config_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")

        return backup_path

    def validate_config(self) -> bool:
        """
        Validate sshd_config syntax.

        Returns:
            True if configuration is valid
        """
        try:
            result = subprocess.run(
                ["sshd", "-t"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.logger.debug("sshd_config syntax is valid")
                return True
            else:
                self.logger.error(f"sshd_config validation failed: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Cannot validate sshd_config: {e}")
            return False

    def reload_sshd(self) -> bool:
        """
        Reload SSH daemon to apply configuration changes.

        Returns:
            True if reload was successful
        """
        try:
            result = subprocess.run(
                ["systemctl", "reload", "sshd"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info("SSH daemon reloaded successfully")
                return True
            else:
                # Try ssh.service if sshd.service fails
                result = subprocess.run(
                    ["systemctl", "reload", "ssh"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    self.logger.info("SSH daemon reloaded successfully")
                    return True

                self.logger.error(f"Failed to reload SSH daemon: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Failed to reload SSH daemon: {e}")
            return False

    def _update_setting(self, lines: List[str], setting: str, value: str) -> List[str]:
        """
        Update a setting in sshd_config lines.

        Args:
            lines: List of config file lines
            setting: Setting name to update
            value: New value

        Returns:
            Updated lines list
        """
        pattern = re.compile(rf"^#?\s*{setting}\s+", re.IGNORECASE)
        found = False
        new_lines = []

        for line in lines:
            if pattern.match(line):
                new_lines.append(f"{setting} {value}")
                found = True
            else:
                new_lines.append(line)

        if not found:
            # Add at end
            new_lines.append(f"{setting} {value}")

        return new_lines

    def harden(
        self,
        settings: Optional[Dict[str, str]] = None,
        reload_service: bool = True,
    ) -> bool:
        """
        Apply security hardening to sshd_config.

        Args:
            settings: Custom settings to apply (defaults to HARDENING_SETTINGS)
            reload_service: Whether to reload SSH daemon after changes

        Returns:
            True if hardening was successful
        """
        if settings is None:
            settings = self.HARDENING_SETTINGS

        self.logger.info("Applying SSH security hardening")

        if not self.config_path.exists():
            self.logger.error(f"sshd_config not found: {self.config_path}")
            return False

        # Create backup
        self.backup_config()

        try:
            # Read current config
            content = self.config_path.read_text()
            lines = content.split("\n")

            # Apply settings
            for setting, value in settings.items():
                lines = self._update_setting(lines, setting, value)

            # Write back
            self.config_path.write_text("\n".join(lines))
            self.logger.info("Updated sshd_config with hardening settings")

            # Validate
            if not self.validate_config():
                self.logger.error("Configuration validation failed, restoring backup")
                self.restore_backup()
                return False

            # Reload
            if reload_service:
                if not self.reload_sshd():
                    self.logger.warning("Failed to reload SSH daemon")

            self.logger.info("✅ SSH security hardening applied successfully")
            return True

        except PermissionError:
            self.logger.error("Permission denied: cannot modify sshd_config")
            return False
        except Exception as e:
            self.logger.error(f"Failed to apply hardening: {e}")
            self.restore_backup()
            return False

    def restore_backup(self) -> bool:
        """
        Restore sshd_config from backup.

        Returns:
            True if restore was successful
        """
        backup_path = Path(str(self.config_path) + self.BACKUP_SUFFIX)

        if backup_path.exists():
            shutil.copy2(backup_path, self.config_path)
            self.logger.info("Restored sshd_config from backup")
            return True

        self.logger.warning("No backup found to restore")
        return False

    def set_password_auth(self, enabled: bool, reload_service: bool = True) -> bool:
        """
        Enable or disable password authentication.

        Args:
            enabled: Whether to enable password auth
            reload_service: Whether to reload SSH daemon

        Returns:
            True if successful
        """
        value = "yes" if enabled else "no"
        return self.harden(
            settings={"PasswordAuthentication": value},
            reload_service=reload_service,
        )

    def set_root_login(self, mode: str = "no", reload_service: bool = True) -> bool:
        """
        Configure root login setting.

        Args:
            mode: "yes", "no", "prohibit-password", "forced-commands-only"
            reload_service: Whether to reload SSH daemon

        Returns:
            True if successful
        """
        valid_modes = ["yes", "no", "prohibit-password", "forced-commands-only"]
        if mode not in valid_modes:
            self.logger.error(f"Invalid root login mode: {mode}")
            return False

        return self.harden(
            settings={"PermitRootLogin": mode},
            reload_service=reload_service,
        )
