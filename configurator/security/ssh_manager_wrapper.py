"""
SSH Manager Wrapper

Simplified wrapper for SSH key management and hardening.
Provides easy interface for the security module.
"""

import logging
import os
import pwd
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class SimpleSSHKey:
    """Simplified SSH key representation."""

    user: str
    key_type: str  # rsa, ed25519, ecdsa
    public_key_path: str
    private_key_path: str
    fingerprint: str
    created: datetime
    expires: Optional[datetime]


class SSHManagerWrapper:
    """
    Simplified SSH Key and Configuration Manager.

    Manages SSH keys and hardens SSH daemon configuration.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize SSH manager.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # SSH configuration
        self.enabled = config.get("security_advanced.ssh_key_manager.enabled", True)
        self.generate_keys = config.get("security_advanced.ssh_key_manager.generate_keys", True)
        self.key_type = config.get("security_advanced.ssh_key_manager.key_type", "ed25519")
        self.key_size = config.get("security_advanced.ssh_key_manager.key_size", 4096)
        self.key_rotation_days = config.get(
            "security_advanced.ssh_key_manager.key_rotation_days", 365
        )
        self.disable_password_auth = config.get(
            "security_advanced.ssh_key_manager.disable_password_auth", False
        )

        self.keys: List[SimpleSSHKey] = []

    def setup(self) -> bool:
        """
        Setup SSH key management and hardening.

        Returns:
            bool: True if setup successful
        """
        if not self.enabled:
            self.logger.info("SSH key manager disabled")
            return True

        self.logger.info("Setting up SSH key management...")

        try:
            # Harden SSH daemon configuration
            if not self._harden_sshd_config():
                self.logger.warning("SSH hardening had issues")

            # Generate keys for users if configured
            if self.generate_keys:
                if not self._generate_user_keys():
                    self.logger.warning("Key generation had issues")

            self.logger.info("✓ SSH key management configured")
            return True

        except Exception as e:
            self.logger.error(f"SSH setup failed: {e}", exc_info=True)
            return False

    def _harden_sshd_config(self) -> bool:
        """Apply SSH daemon hardening configurations."""
        self.logger.info("Hardening SSH daemon configuration...")

        try:
            sshd_config_path = "/etc/ssh/sshd_config"

            # Backup original config
            if not os.path.exists(f"{sshd_config_path}.backup-advanced"):
                subprocess.run(["cp", sshd_config_path, f"{sshd_config_path}.backup-advanced"])

            # Hardening configurations
            hardening_configs = {
                "PubkeyAuthentication": "yes",
                "PermitEmptyPasswords": "no",
                "MaxAuthTries": "3",
                "ClientAliveInterval": "300",
                "ClientAliveCountMax": "2",
                "Protocol": "2",
                "UsePAM": "yes",
                # Strong ciphers only
                "Ciphers": "chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr",
                # Strong MACs only
                "MACs": "hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-sha2-512,hmac-sha2-256",
                # Strong key exchange algorithms
                "KexAlgorithms": "curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256",
            }

            # Read current config
            with open(sshd_config_path, "r") as f:
                lines = f.readlines()

            # Track which configs were applied
            applied_configs = set()

            # Update existing settings
            new_lines = []
            for line in lines:
                stripped = line.strip()

                # Skip empty lines and comments initially
                if not stripped or stripped.startswith("#"):
                    new_lines.append(line)
                    continue

                # Check if this line sets one of our hardening configs
                updated = False
                for key, value in hardening_configs.items():
                    if stripped.startswith(key):
                        new_lines.append(f"{key} {value}\n")
                        applied_configs.add(key)
                        updated = True
                        break

                if not updated:
                    new_lines.append(line)

            # Add any missing hardening configs
            new_lines.append("\n# === Advanced SSH Hardening ===\n")
            for key, value in hardening_configs.items():
                if key not in applied_configs:
                    new_lines.append(f"{key} {value}\n")
            new_lines.append("# === End Advanced Hardening ===\n")

            # Write updated config
            with open(sshd_config_path, "w") as f:
                f.writelines(new_lines)

            # Test configuration
            result = subprocess.run(["sshd", "-t"], capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"SSH config test failed: {result.stderr}")
                # Restore backup
                subprocess.run(["cp", f"{sshd_config_path}.backup-advanced", sshd_config_path])
                return False

            # Reload SSH daemon
            subprocess.run(["systemctl", "reload", "sshd"])

            self.logger.info("✓ SSH daemon hardened with strong crypto")
            return True

        except Exception as e:
            self.logger.error(f"SSH hardening error: {e}", exc_info=True)
            return False

    def _generate_user_keys(self) -> bool:
        """Generate SSH keys for regular users."""
        self.logger.info("Generating SSH keys for users...")

        try:
            # Get regular users
            users = [u for u in pwd.getpwall() if 1000 <= u.pw_uid < 60000]

            generated_count = 0

            for user in users:
                username = user.pw_name
                home_dir = user.pw_dir

                if not os.path.isdir(home_dir):
                    continue

                # Generate key for user
                if self._generate_key_for_user(username, home_dir):
                    generated_count += 1

            self.logger.info(f"✓ Generated keys for {generated_count} user(s)")
            return True

        except Exception as e:
            self.logger.error(f"Key generation error: {e}", exc_info=True)
            return False

    def _generate_key_for_user(self, username: str, home_dir: str) -> bool:
        """
        Generate SSH key for a specific user.

        Args:
            username: Username
            home_dir: User's home directory

        Returns:
            bool: True if successful
        """
        try:
            ssh_dir = os.path.join(home_dir, ".ssh")

            # Create .ssh directory if it doesn't exist
            os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

            # Set ownership
            import shutil

            shutil.chown(ssh_dir, user=username, group=username)

            # Determine key path based on type
            if self.key_type == "ed25519":
                key_path = os.path.join(ssh_dir, "id_ed25519")
            elif self.key_type == "ecdsa":
                key_path = os.path.join(ssh_dir, "id_ecdsa")
            else:  # rsa
                key_path = os.path.join(ssh_dir, "id_rsa")

            # Skip if key already exists
            if os.path.exists(key_path):
                self.logger.debug(f"Key already exists for {username}")
                return True

            # Build ssh-keygen command
            cmd = [
                "ssh-keygen",
                "-t",
                self.key_type,
                "-f",
                key_path,
                "-N",
                "",  # No passphrase
                "-C",
                f"{username}@debian-vps-workstation-{datetime.now().strftime('%Y%m%d')}",
            ]

            # Add key size for RSA
            if self.key_type == "rsa":
                cmd.extend(["-b", str(self.key_size)])

            # Generate key
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Key generation failed for {username}: {result.stderr}")
                return False

            # Set correct permissions
            os.chmod(key_path, 0o600)
            os.chmod(f"{key_path}.pub", 0o644)

            # Set ownership
            shutil.chown(key_path, user=username, group=username)
            shutil.chown(f"{key_path}.pub", user=username, group=username)

            # Get fingerprint
            fingerprint_result = subprocess.run(
                ["ssh-keygen", "-lf", key_path], capture_output=True, text=True
            )

            fingerprint = (
                fingerprint_result.stdout.split()[1]
                if fingerprint_result.returncode == 0
                else "unknown"
            )

            # Store key info
            ssh_key = SimpleSSHKey(
                user=username,
                key_type=self.key_type,
                public_key_path=f"{key_path}.pub",
                private_key_path=key_path,
                fingerprint=fingerprint,
                created=datetime.now(),
                expires=(
                    datetime.now() + timedelta(days=self.key_rotation_days)
                    if self.key_rotation_days > 0
                    else None
                ),
            )

            self.keys.append(ssh_key)

            self.logger.info(f"✓ Generated {self.key_type} key for {username}")
            self.logger.debug(f"  Fingerprint: {fingerprint}")

            return True

        except Exception as e:
            self.logger.error(f"Error generating key for {username}: {e}", exc_info=True)
            return False

    def get_ssh_security_status(self) -> Dict[str, bool]:
        """
        Get SSH security status.

        Returns:
            dict: Security check results
        """
        status = {
            "pubkey_auth_enabled": False,
            "empty_passwords_disabled": False,
            "strong_ciphers": False,
            "protocol_2_only": False,
        }

        try:
            # Check sshd configuration
            result = subprocess.run(["sshd", "-T"], capture_output=True, text=True)

            if result.returncode == 0:
                config = result.stdout.lower()

                status["pubkey_auth_enabled"] = "pubkeyauthentication yes" in config
                status["empty_passwords_disabled"] = "permitemptypasswords no" in config
                status["strong_ciphers"] = "chacha20-poly1305" in config or "aes256-gcm" in config
                status["protocol_2_only"] = "protocol 2" in config

        except Exception as e:
            self.logger.error(f"Error checking SSH status: {e}", exc_info=True)

        return status
