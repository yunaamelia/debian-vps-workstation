"""
MFA Manager Wrapper

Simplified wrapper for multi-factor authentication setup.
Provides easy interface for the security module.
"""

import logging
import os
import secrets
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SimpleMFAConfig:
    """Simplified MFA configuration."""

    username: str
    method: str  # totp, u2f
    enabled: bool
    backup_codes: List[str]


class MFAManagerWrapper:
    """
    Simplified Multi-Factor Authentication Manager.

    Manages MFA setup and enforcement via PAM.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize MFA manager.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # MFA configuration
        self.enabled = config.get("security_advanced.mfa.enabled", False)
        self.method = config.get("security_advanced.mfa.method", "totp")
        self.provider = config.get("security_advanced.mfa.provider", "google-authenticator")
        self.enforce_for_sudo = config.get("security_advanced.mfa.enforce_for_sudo", True)
        self.enforce_for_ssh = config.get("security_advanced.mfa.enforce_for_ssh", True)
        self.backup_codes_count = config.get("security_advanced.mfa.backup_codes_count", 10)

        self.user_configs: List[SimpleMFAConfig] = []

    def setup(self) -> bool:
        """
        Setup multi-factor authentication.

        Returns:
            bool: True if setup successful
        """
        if not self.enabled:
            self.logger.info("MFA is disabled")
            return True

        self.logger.warning(
            "⚠️  Setting up MFA - ensure you have alternative access before proceeding!"
        )

        try:
            # Install MFA packages
            if not self._install_mfa_packages():
                return False

            # Configure PAM for MFA
            if not self._configure_pam():
                return False

            self.logger.info("✓ MFA configured")
            self.logger.warning("⚠️  Users must run 'google-authenticator' to complete setup!")
            self.logger.warning("⚠️  Test MFA in a new session before closing this one!")

            return True

        except Exception as e:
            self.logger.error(f"MFA setup failed: {e}", exc_info=True)
            return False

    def _install_mfa_packages(self) -> bool:
        """Install MFA-related packages."""
        self.logger.info("Installing MFA packages...")

        try:
            packages = []

            if "totp" in self.method:
                packages.append("libpam-google-authenticator")

            if "u2f" in self.method:
                packages.extend(["libpam-u2f", "pamu2fcfg"])

            if not packages:
                self.logger.error("No MFA method specified")
                return False

            result = subprocess.run(
                ["apt-get", "install", "-y"] + packages, capture_output=True, text=True
            )

            if result.returncode != 0:
                self.logger.error(f"Package installation failed: {result.stderr}")
                return False

            self.logger.info(f"✓ MFA packages installed: {', '.join(packages)}")
            return True

        except Exception as e:
            self.logger.error(f"Package installation error: {e}", exc_info=True)
            return False

    def _configure_pam(self) -> bool:
        """Configure PAM for MFA."""
        self.logger.info("Configuring PAM for MFA...")

        try:
            # Configure SSH PAM if enforced
            if self.enforce_for_ssh:
                if not self._configure_ssh_pam():
                    self.logger.error("Failed to configure SSH PAM")
                    return False

            # Configure sudo PAM if enforced
            if self.enforce_for_sudo:
                if not self._configure_sudo_pam():
                    self.logger.error("Failed to configure sudo PAM")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"PAM configuration error: {e}", exc_info=True)
            return False

    def _configure_ssh_pam(self) -> bool:
        """Configure PAM for SSH with MFA."""

        try:
            pam_sshd = "/etc/pam.d/sshd"

            # Backup original
            if not os.path.exists(f"{pam_sshd}.backup-mfa"):
                subprocess.run(["cp", pam_sshd, f"{pam_sshd}.backup-mfa"])

            # Read current PAM config
            with open(pam_sshd, "r") as f:
                lines = f.readlines()

            # Add Google Authenticator PAM module
            mfa_line = "auth required pam_google_authenticator.so nullok\n"

            # Check if already configured
            if any("pam_google_authenticator" in line for line in lines):
                self.logger.info("SSH PAM already configured for MFA")
                return True

            # Insert after @include common-auth
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if "@include common-auth" in line:
                    new_lines.append(mfa_line)

            # Write updated config
            with open(pam_sshd, "w") as f:
                f.writelines(new_lines)

            # Update SSH config to enable challenge-response
            sshd_config = "/etc/ssh/sshd_config"
            with open(sshd_config, "r") as f:
                sshd_lines = f.readlines()

            # Update or add ChallengeResponseAuthentication
            updated = False
            new_sshd_lines = []
            for line in sshd_lines:
                if line.strip().startswith("ChallengeResponseAuthentication"):
                    new_sshd_lines.append("ChallengeResponseAuthentication yes\n")
                    updated = True
                else:
                    new_sshd_lines.append(line)

            if not updated:
                new_sshd_lines.append("\n# MFA Configuration\n")
                new_sshd_lines.append("ChallengeResponseAuthentication yes\n")

            with open(sshd_config, "w") as f:
                f.writelines(new_sshd_lines)

            # Reload SSH
            subprocess.run(["systemctl", "reload", "sshd"])

            self.logger.info("✓ SSH PAM configured for MFA")
            return True

        except Exception as e:
            self.logger.error(f"SSH PAM configuration error: {e}", exc_info=True)
            return False

    def _configure_sudo_pam(self) -> bool:
        """Configure PAM for sudo with MFA."""

        try:
            pam_sudo = "/etc/pam.d/sudo"

            # Backup original
            if not os.path.exists(f"{pam_sudo}.backup-mfa"):
                subprocess.run(["cp", pam_sudo, f"{pam_sudo}.backup-mfa"])

            # Read current PAM config
            with open(pam_sudo, "r") as f:
                lines = f.readlines()

            # Add Google Authenticator PAM module
            mfa_line = "auth required pam_google_authenticator.so nullok\n"

            # Check if already configured
            if any("pam_google_authenticator" in line for line in lines):
                self.logger.info("sudo PAM already configured for MFA")
                return True

            # Insert after @include common-auth
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if "@include common-auth" in line:
                    new_lines.append(mfa_line)

            # Write updated config
            with open(pam_sudo, "w") as f:
                f.writelines(new_lines)

            self.logger.info("✓ sudo PAM configured for MFA")
            return True

        except Exception as e:
            self.logger.error(f"sudo PAM configuration error: {e}", exc_info=True)
            return False

    def _generate_backup_codes(self, count: int) -> List[str]:
        """
        Generate backup codes for MFA.

        Args:
            count: Number of codes to generate

        Returns:
            list: Backup codes
        """
        codes = []

        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)

        return codes

    def verify_mfa_status(self) -> Dict[str, bool]:
        """
        Verify MFA configuration status.

        Returns:
            dict: MFA status checks
        """
        status = {
            "packages_installed": False,
            "pam_configured": False,
            "ssh_mfa_enabled": False,
            "sudo_mfa_enabled": False,
        }

        try:
            # Check packages
            result = subprocess.run(
                ["dpkg", "-s", "libpam-google-authenticator"], capture_output=True
            )
            status["packages_installed"] = result.returncode == 0

            # Check PAM configs
            if os.path.exists("/etc/pam.d/sshd"):
                with open("/etc/pam.d/sshd", "r") as f:
                    content = f.read()
                    status["ssh_mfa_enabled"] = "pam_google_authenticator" in content

            if os.path.exists("/etc/pam.d/sudo"):
                with open("/etc/pam.d/sudo", "r") as f:
                    content = f.read()
                    status["sudo_mfa_enabled"] = "pam_google_authenticator" in content

            status["pam_configured"] = status["ssh_mfa_enabled"] or status["sudo_mfa_enabled"]

        except Exception as e:
            self.logger.error(f"Error verifying MFA status: {e}", exc_info=True)

        return status

    def disable_mfa(self) -> bool:
        """
        Disable MFA (emergency recovery).

        Returns:
            bool: True if successful
        """
        self.logger.warning("⚠️  Disabling MFA - use only for emergency recovery!")

        try:
            # Restore original PAM configs
            pam_files = ["/etc/pam.d/sshd", "/etc/pam.d/sudo"]

            for pam_file in pam_files:
                backup_file = f"{pam_file}.backup-mfa"
                if os.path.exists(backup_file):
                    subprocess.run(["cp", backup_file, pam_file])
                    self.logger.info(f"Restored {pam_file}")

            # Reload SSH
            subprocess.run(["systemctl", "reload", "sshd"])

            self.logger.info("✓ MFA disabled")
            return True

        except Exception as e:
            self.logger.error(f"Error disabling MFA: {e}", exc_info=True)
            return False
