"""
Security module for system hardening.

MANDATORY - Cannot be disabled.

Handles:
- UFW firewall setup
- Fail2ban installation
- SSH hardening
- Automatic security updates
"""

import os

from configurator.exceptions import ModuleExecutionError
from configurator.modules.base import ConfigurationModule
from configurator.utils.file import backup_file, write_file


class SecurityModule(ConfigurationModule):
    """
    Security hardening module.

    This module is MANDATORY and cannot be disabled.
    It sets up essential security measures.
    """

    name = "Security"
    description = "Security hardening (UFW, Fail2Ban, SSH)"
    depends_on = ["system"]
    priority = 20
    mandatory = True

    def validate(self) -> bool:
        """Validate security prerequisites."""
        self.logger.info("Checking security prerequisites...")

        # Warn about existing firewall rules
        result = self.run("iptables-save", check=False)
        if result.stdout.strip() and "-A" in result.stdout:
            self.logger.info(
                "Existing iptables rules detected. " "They will be replaced by UFW configuration."
            )

        return True

    def configure(self) -> bool:
        """Configure security settings."""
        self.logger.info(
            """
╔════════════════════════════════════════════════════════╗
║         🔒 SECURITY HARDENING (MANDATORY)              ║
╚════════════════════════════════════════════════════════╝

Your server will be protected with:
  ✓ UFW Firewall (blocks unauthorized access)
  ✓ Fail2ban (prevents brute force attacks)
  ✓ SSH Hardening (secure remote access)
  ✓ Automatic Updates (security patches)
        """
        )

        # 1. Setup UFW firewall
        self._setup_ufw()

        # 2. Setup fail2ban
        self._setup_fail2ban()

        # 3. Harden SSH
        self._harden_ssh()

        # 4. Enable automatic updates
        self._enable_auto_updates()

        self.logger.info("✓ Security hardening complete")
        return True

    def verify(self) -> bool:
        """Verify security configuration."""
        checks_passed = True

        # Check UFW is active
        result = self.run("ufw status", check=False)
        if "Status: active" not in result.stdout:
            self.logger.error("UFW firewall is not active!")
            checks_passed = False
        else:
            self.logger.info("✓ UFW firewall is active")

        # Check fail2ban is running
        if not self.is_service_active("fail2ban"):
            self.logger.error("Fail2ban is not running!")
            checks_passed = False
        else:
            self.logger.info("✓ Fail2ban is running")

        # Check SSH is running
        if not self.is_service_active("sshd") and not self.is_service_active("ssh"):
            self.logger.error("SSH service is not running!")
            checks_passed = False
        else:
            self.logger.info("✓ SSH is running")

        return checks_passed

    def _setup_ufw(self):
        """Setup UFW firewall."""
        self.logger.info("Setting up UFW firewall...")

        # Install UFW
        self.install_packages(["ufw"])

        # Reset to clean state
        self.run("ufw --force reset", check=True)

        # Default policies
        self.run("ufw default deny incoming", check=True)
        self.run("ufw default allow outgoing", check=True)

        # Allow SSH with rate limiting
        ssh_port = self.get_config("ufw.ssh_port", 22)
        if self.get_config("ufw.ssh_rate_limit", True):
            self.run(f"ufw limit {ssh_port}/tcp comment 'SSH'", check=True)
        else:
            self.run(f"ufw allow {ssh_port}/tcp comment 'SSH'", check=True)

        # Allow RDP for xrdp
        self.run("ufw allow 3389/tcp comment 'RDP'", check=True)

        # Enable UFW
        self.run("ufw --force enable", check=True)

        # Verify
        result = self.run("ufw status", check=True)
        if "Status: active" not in result.stdout:
            raise ModuleExecutionError(
                what="UFW failed to activate",
                why="The firewall did not enable properly",
                how="Check /var/log/ufw.log for details",
            )

        self.rollback_manager.add_command(
            "ufw --force disable",
            description="Disable UFW firewall",
        )

        self.logger.info("✓ UFW firewall configured")
        self.logger.info(f"  Allowed ports: SSH ({ssh_port}), RDP (3389)")

        # Audit Log
        try:
            from configurator.core.audit import AuditEventType, AuditLogger

            audit = AuditLogger()
            audit.log_event(
                AuditEventType.FIREWALL_RULE_ADD,
                "Configured UFW firewall",
                details={
                    "ssh_port": ssh_port,
                    "rdp_port": 3389,
                    "ssh_rate_limit": self.get_config("ufw.ssh_rate_limit", True),
                },
            )
        except Exception:
            pass

    def _setup_fail2ban(self):
        """Setup fail2ban for brute force protection."""
        self.logger.info("Setting up fail2ban...")

        # Install fail2ban
        self.install_packages(["fail2ban"])

        # Configure fail2ban
        max_retry = self.get_config("fail2ban.ssh_max_retry", 5)
        ban_time = self.get_config("fail2ban.ssh_ban_time", 3600)

        jail_config = """# Debian VPS Workstation - Fail2ban Configuration
# Generated by debian-vps-configurator

[DEFAULT]
bantime = {ban_time}
findtime = 600
maxretry = {max_retry}
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
maxretry = {max_retry}
bantime = {ban_time}
"""

        backup_file("/etc/fail2ban/jail.local")
        write_file("/etc/fail2ban/jail.local", jail_config)

        # Enable and start fail2ban
        self.enable_service("fail2ban")

        self.logger.info("✓ Fail2ban configured")
        self.logger.info(f"  Max retries: {max_retry}, Ban time: {ban_time}s")

    def _harden_ssh(self):
        """Harden SSH configuration."""
        self.logger.info("Hardening SSH configuration...")

        sshd_config_path = "/etc/ssh/sshd_config"
        backup_file(sshd_config_path)

        # Create hardened SSH config
        disable_root_password = self.get_config("ssh.disable_root_password", True)
        disable_password_auth = self.get_config("ssh.disable_password_auth", False)

        # Read current config
        with open(sshd_config_path, "r") as f:
            current_config = f.read()

        # Add our hardening settings
        hardening_block = """
# === Debian VPS Workstation SSH Hardening ===
# Added by debian-vps-configurator

# Protocol settings
Protocol 2

# Disable empty passwords
PermitEmptyPasswords no

# Disable X11 forwarding (not needed for RDP setup)
X11Forwarding no

# Client alive interval (disconnect idle sessions)
ClientAliveInterval 300
ClientAliveCountMax 2

# Max authentication attempts
MaxAuthTries 3

# Disable TCP forwarding (optional, can be enabled if needed)
AllowTcpForwarding no

# Logging
LogLevel VERBOSE
"""

        if disable_root_password:
            hardening_block += """
# Disable root login with password (key only)
PermitRootLogin prohibit-password
"""

        if disable_password_auth:
            hardening_block += """
# Disable password authentication entirely (SSH keys only)
PasswordAuthentication no
"""

        hardening_block += "\n# === End SSH Hardening ===\n"

        # Check if we've already added our config
        if "Debian VPS Workstation SSH Hardening" not in current_config:
            # Append our config
            with open(sshd_config_path, "a") as f:
                f.write(hardening_block)

        # Test SSH config
        result = self.run("sshd -t", check=False)
        if not result.success:
            self.logger.error("SSH configuration test failed!")
            self.logger.error(result.stderr)
            raise ModuleExecutionError(
                what="SSH configuration is invalid",
                why=result.stderr,
                how="Check /etc/ssh/sshd_config for syntax errors",
            )

        # Restart SSH
        self.restart_service("sshd")

        self.logger.info("✓ SSH hardened")

        # Audit Log
        try:
            from configurator.core.audit import AuditEventType, AuditLogger

            audit = AuditLogger()
            audit.log_event(
                AuditEventType.SSH_CONFIG_CHANGE,
                "Applied SSH hardening configuration",
                details={
                    "disable_root_password": disable_root_password,
                    "disable_password_auth": disable_password_auth,
                    "permit_empty_passwords": False,
                },
            )
        except Exception:
            pass

    def _enable_auto_updates(self):
        """Enable automatic security updates."""
        if not self.get_config("auto_updates", True):
            self.logger.info("Automatic updates disabled in config")
            return

        self.logger.info("Enabling automatic security updates...")

        # Install debconf-utils for preseeding
        self.install_packages(["debconf-utils"])

        # Preseed unattended-upgrades to enable auto updates without prompt
        self.run(
            "echo 'unattended-upgrades unattended-upgrades/enable_auto_updates boolean true' | debconf-set-selections",
            check=False,
        )

        # Install unattended-upgrades
        self.install_packages(["unattended-upgrades", "apt-listchanges"])

        # Configure unattended-upgrades
        auto_upgrades_config = """APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
"""

        write_file(
            "/etc/apt/apt.conf.d/20auto-upgrades",
            auto_upgrades_config,
        )

        # Enable the service
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        self.run(
            "dpkg-reconfigure -f noninteractive -plow unattended-upgrades",
            check=False,
            env=env,
        )

        self.logger.info("✓ Automatic security updates enabled")
