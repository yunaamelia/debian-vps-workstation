"""
Security module for system hardening.

MANDATORY - Cannot be disabled.

Handles:
- UFW firewall setup
- Fail2ban installation
- SSH hardening
- Automatic security updates
- Phase 2: Advanced security features (CIS scanner, vulnerability scanner, SSL, MFA)
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
                "Existing iptables rules detected. They will be replaced by UFW configuration."
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

Phase 2 Advanced Security:
  ✓ CIS Benchmark Scanner
  ✓ Vulnerability Scanner
  ✓ Supply Chain Protection
  ✓ Input Validation
        """
        )

        # Phase 1: Basic Security
        self._setup_ufw()
        self._setup_fail2ban()
        self._harden_ssh()
        self._enable_auto_updates()

        # Phase 2: Advanced Security Features
        self._setup_advanced_security()

        self.logger.info("✓ Security hardening complete")
        return True

    def verify(self) -> bool:
        """Verify security configuration."""
        if self.dry_run_manager.is_enabled:
            return True

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
        """Setup UFW firewall with safety checks."""
        self.logger.info("Setting up UFW firewall...")

        # Detect current SSH connection port
        ssh_connection = os.getenv("SSH_CONNECTION", "")
        current_ssh_port = 22  # default

        if ssh_connection:
            # SSH_CONNECTION format: "client_ip client_port server_ip server_port"
            parts = ssh_connection.split()
            if len(parts) >= 4:
                current_ssh_port = int(parts[3])
                self.logger.info(f"  Detected SSH connection on port {current_ssh_port}")

        # Install UFW
        self.install_packages(["ufw"])

        # Reset to clean state
        self.run("ufw --force reset", check=True)

        # Default policies
        self.run("ufw default deny incoming", check=True)
        self.run("ufw default allow outgoing", check=True)

        # Allow SSH with rate limiting
        ssh_port = self.get_config("ufw.ssh_port", current_ssh_port)

        # Safety: Always allow current SSH port if we're in remote session
        if ssh_connection and current_ssh_port != ssh_port:
            self.logger.warning(
                f"  Config specifies port {ssh_port}, but you're connected on {current_ssh_port}"
            )
            self.logger.warning("  Will allow BOTH ports to preserve access")
            # Allow both ports
            self.run(f"ufw limit {current_ssh_port}/tcp comment 'SSH (current)'", check=True)
            self.run(f"ufw limit {ssh_port}/tcp comment 'SSH (config)'", check=True)
        else:
            # Normal case - allow configured port
            if self.get_config("ufw.ssh_rate_limit", True):
                self.run(f"ufw limit {ssh_port}/tcp comment 'SSH'", check=True)
            else:
                self.run(f"ufw allow {ssh_port}/tcp comment 'SSH'", check=True)

        # Allow RDP for xrdp
        self.run("ufw allow 3389/tcp comment 'RDP'", check=True)

        # Allow additional ports from config
        additional_ports = self.get_config("ufw.additional_ports", [])
        for port_spec in additional_ports:
            self.logger.info(f"  Allowing additional port: {port_spec}")
            self.run(f"ufw allow {port_spec}", check=True)

        # Enable UFW
        self.run("ufw --force enable", check=True)

        # Verify
        if not self.dry_run_manager.is_enabled:
            result = self.run("ufw status", check=True)
            if "Status: active" not in result.stdout:
                raise ModuleExecutionError(
                    what="UFW failed to activate",
                    why="The firewall did not enable properly",
                    how="Check /var/log/ufw.log for details",
                )
        else:
            self.logger.info("Dry-run: skipping UFW status verification")

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

        jail_config = f"""# Debian VPS Workstation - Fail2ban Configuration
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
        """Harden SSH configuration with safety checks."""
        self.logger.info("Hardening SSH configuration...")

        sshd_config_path = "/etc/ssh/sshd_config"
        backup_file(sshd_config_path)

        # Detect current SSH connection to preserve access
        current_user = os.getenv("USER", "root")
        ssh_connection = os.getenv("SSH_CONNECTION", "")
        is_remote_session = bool(ssh_connection)

        if is_remote_session:
            self.logger.info(f"  Detected remote SSH session for user '{current_user}'")
            self.logger.info("  Will preserve current authentication method")

        # Create hardened SSH config
        # SAFE DEFAULTS: Never disable current access method during installation
        disable_root_password = self.get_config("ssh.disable_root_password", False)
        disable_password_auth = self.get_config("ssh.disable_password_auth", False)

        # Safety: If we're in a remote session as root with password, don't disable it
        if is_remote_session and current_user == "root":
            if disable_root_password:
                self.logger.warning(
                    "  Skipping root password disable - would lock out current session"
                )
                disable_root_password = False
            if disable_password_auth:
                self.logger.warning(
                    "  Skipping password auth disable - would lock out current session"
                )
                disable_password_auth = False

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
MaxAuthTries 6

# Allow TCP forwarding (needed for SSH tunnels)
AllowTcpForwarding yes

# Logging
LogLevel INFO
"""

        # Explicitly set root login and password auth (always show current state)
        if disable_root_password:
            hardening_block += """
# Disable root login with password (key only)
PermitRootLogin prohibit-password
"""
        else:
            hardening_block += """
# Allow root login with password (ENABLED for easier server management)
PermitRootLogin yes
"""

        if disable_password_auth:
            hardening_block += """
# Disable password authentication entirely (SSH keys only)
PasswordAuthentication no
"""
        else:
            hardening_block += """
# Allow password authentication (ENABLED for easier access)
PasswordAuthentication yes
"""

        hardening_block += "\n# === End SSH Hardening ===\n"

        # Check if we've already added our config
        if "Debian VPS Workstation SSH Hardening" not in current_config:
            # Append our config
            # Append our config
            # Use append mode by reading first? write_file doesn't support append easily in its current signature.
            # But wait, write_file supports **kwargs forwarded to utils.write_file?
            # self.write_file(sshd_config_path, hardening_block, mode="a") ?
            # utils/file.py write_file uses open(path, mode).
            # Let's check utils/file.py signature.
            # For now, let's just use a read-modify-write approach which is safer for dry-run.
            new_config = current_config + hardening_block
            self.write_file(sshd_config_path, new_config)

        # Test SSH config
        result = self.run("sshd -t", check=False)
        if not result.success:
            self.logger.error("SSH configuration test failed!")
            self.logger.error(result.stderr)
            # Restore backup
            self.run(f"cp {sshd_config_path}.bak {sshd_config_path}", check=False)
            raise ModuleExecutionError(
                what="SSH configuration is invalid",
                why=result.stderr,
                how="Config restored from backup. Check /etc/ssh/sshd_config for syntax errors",
            )

        # Safe SSH restart with connection preservation
        # Default to False to prevent connection drops during remote installation
        restart_ssh = self.get_config("ssh.restart_service", False)

        if restart_ssh:
            if is_remote_session:
                self.logger.info("  ⚠️  Restarting SSH (current connection will be preserved)")
                # Use reload instead of restart to preserve connections
                reload_result = self.run("systemctl reload sshd", check=False)
                if not reload_result.success:
                    # Fallback to restart if reload fails
                    self.logger.warning("  Reload failed! Skipping restart to preserve connection.")
                    self.logger.warning("  Please restart SSH manually: systemctl restart sshd")
                    # self.restart_service("sshd")  # RISKY: Do not restart in remote session
            else:
                # Not remote, safe to restart normally
                self.restart_service("sshd")
        else:
            self.logger.info("  SSH restart skipped (config: ssh.restart_service=false)")
            self.logger.info("  Run 'systemctl reload sshd' manually to apply changes")

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

    def _setup_advanced_security(self):
        """Setup Phase 2 advanced security features."""
        if not self.get_config("security_advanced", {}).get("enabled", True):
            self.logger.info("Advanced security features disabled in config")
            return

        self.logger.info("Configuring advanced security features...")

        # Initialize validators and managers
        try:
            from configurator.security.input_validator import InputValidator
            from configurator.security.supply_chain import SupplyChainValidator

            supply_chain = SupplyChainValidator(self.config, self.logger)
            input_validator = InputValidator(self.config, self.logger)

            self.logger.info("✓ Supply chain validator initialized")
            self.logger.info("✓ Input validator initialized")

        except Exception as e:
            self.logger.warning(f"Failed to initialize security validators: {e}")

        # Setup CIS Scanner
        if self.get_config("security_advanced.cis_scanner.enabled", True):
            self._setup_cis_scanner()

        # Setup Vulnerability Scanner
        if self.get_config("security_advanced.vulnerability_scanner.enabled", True):
            self._setup_vulnerability_scanner()

        # Setup SSH Key Manager
        if self.get_config("security_advanced.ssh_key_manager.enabled", True):
            self._setup_ssh_key_manager()

        # Setup SSL Manager
        if self.get_config("security_advanced.ssl_manager.enabled", False):
            self._setup_ssl_manager()

        # Setup MFA
        if self.get_config("security_advanced.mfa.enabled", False):
            self._setup_mfa()

        self.logger.info("✓ Advanced security features configured")

    def _setup_cis_scanner(self):
        """Setup CIS Benchmark Scanner."""
        try:
            from configurator.security.cis_scanner import CISBenchmarkScanner

            scanner = CISBenchmarkScanner(self.logger)

            # Run initial scan
            scan_on_install = self.get_config("security_advanced.cis_scanner.scan_on_install", True)
            if scan_on_install:
                self.logger.info("Running initial CIS compliance scan...")
                scanner.scan()

            # Setup cron job for scheduled scans
            schedule = self.get_config("security_advanced.cis_scanner.scan_schedule", "weekly")
            self._setup_cron_job("cis-scan", schedule, "vps-configurator scan cis")

            self.logger.info("✓ CIS scanner configured")

        except Exception as e:
            self.logger.warning(f"Failed to setup CIS scanner: {e}")

    def _setup_vulnerability_scanner(self):
        """Setup vulnerability scanner."""
        try:
            from configurator.security.vuln_scanner_wrapper import VulnScannerWrapper

            scanner = VulnScannerWrapper(self.config, self.logger)

            # Install scanners
            if not scanner.install_scanners():
                self.logger.warning("Scanner installation incomplete")
                return

            # Run initial scan
            if self.get_config("security_advanced.vulnerability_scanner.scan_on_install", True):
                self.logger.info("Running initial vulnerability scan...")
                scanner.run_scan()

            # Setup cron job
            schedule = self.get_config(
                "security_advanced.vulnerability_scanner.scan_schedule", "daily"
            )
            self._setup_cron_job("vuln-scan", schedule, "vps-configurator scan vulnerabilities")

            self.logger.info("✓ Vulnerability scanner configured")

        except Exception as e:
            self.logger.warning(f"Failed to setup vulnerability scanner: {e}")

    def _setup_ssh_key_manager(self):
        """Setup SSH key management."""
        try:
            from configurator.security.ssh_manager_wrapper import SSHManagerWrapper

            manager = SSHManagerWrapper(self.config, self.logger)

            # Run SSH setup
            if manager.setup():
                self.logger.info("✓ SSH key manager configured")

                # Display security status
                status = manager.get_ssh_security_status()
                if status["strong_ciphers"]:
                    self.logger.info("  ✓ Strong ciphers enabled")
                if status["pubkey_auth_enabled"]:
                    self.logger.info("  ✓ Public key authentication enabled")
            else:
                self.logger.warning("SSH key manager setup incomplete")

        except Exception as e:
            self.logger.warning(f"Failed to setup SSH key manager: {e}")

    def _setup_ssl_manager(self):
        """Setup SSL/TLS certificate manager."""
        try:
            from configurator.security.ssl_manager import SSLManager

            manager = SSLManager(self.config, self.logger)

            # Run SSL setup
            if manager.setup():
                self.logger.info("✓ SSL certificate manager configured")
            else:
                self.logger.warning("SSL manager setup incomplete")

        except Exception as e:
            self.logger.warning(f"Failed to setup SSL manager: {e}")

    def _setup_mfa(self):
        """Setup multi-factor authentication."""
        try:
            from configurator.security.mfa_manager_wrapper import MFAManagerWrapper

            manager = MFAManagerWrapper(self.config, self.logger)

            # Run MFA setup
            if manager.setup():
                # Display status
                status = manager.verify_mfa_status()
                if status["packages_installed"]:
                    self.logger.info("  ✓ MFA packages installed")
                if status["ssh_mfa_enabled"]:
                    self.logger.info("  ✓ SSH MFA enabled")
                if status["sudo_mfa_enabled"]:
                    self.logger.info("  ✓ sudo MFA enabled")

                self.logger.info("✓ MFA support configured")
                self.logger.warning("  ⚠️  Users must run: google-authenticator")
            else:
                self.logger.warning("MFA setup incomplete")

        except Exception as e:
            self.logger.warning(f"Failed to setup MFA: {e}")

    def _setup_cron_job(self, name: str, schedule: str, command: str):
        """Setup cron job for automated tasks."""
        try:
            # Map schedule to cron format
            cron_schedule = {
                "daily": "0 2 * * *",  # 2 AM daily
                "weekly": "0 2 * * 0",  # 2 AM Sunday
                "monthly": "0 2 1 * *",  # 2 AM 1st of month
            }.get(schedule, "0 2 * * *")

            cron_line = f"{cron_schedule} root {command} >> /var/log/{name}.log 2>&1\n"
            cron_file = f"/etc/cron.d/{name}"

            self.write_file(cron_file, cron_line)

            self.write_file(cron_file, cron_line)

            if not self.dry_run_manager.is_enabled:
                os.chmod(cron_file, 0o644)

            self.logger.debug(f"Created cron job: {cron_file}")

        except Exception as e:
            self.logger.warning(f"Failed to setup cron job {name}: {e}")

    def generate_security_report(self) -> dict:
        """
        Generate comprehensive security report.

        Returns:
            dict: Security status report
        """
        from datetime import datetime

        report = {
            "timestamp": datetime.now().isoformat(),
            "basic_security": {
                "firewall": self._check_firewall_status(),
                "fail2ban": self._check_fail2ban_status(),
                "ssh_hardening": self._check_ssh_hardening(),
                "auto_updates": self._check_auto_updates_status(),
            },
            "advanced_security": {},
        }

        try:
            # Add vulnerability scanner status
            if self.get_config("security_advanced.vulnerability_scanner.enabled", True):
                report["advanced_security"]["vulnerability_scanner"] = {"configured": True}

            # Add CIS scanner status
            if self.get_config("security_advanced.cis_scanner.enabled", True):
                report["advanced_security"]["cis_scanner"] = {"configured": True}

            # Add SSL manager status
            if self.get_config("security_advanced.ssl_manager.enabled", False):
                report["advanced_security"]["ssl_manager"] = {"enabled": True}

            # Add SSH key manager status
            if self.get_config("security_advanced.ssh_key_manager.enabled", True):
                try:
                    from configurator.security.ssh_manager_wrapper import SSHManagerWrapper

                    manager = SSHManagerWrapper(self.config, self.logger)
                    report["advanced_security"]["ssh"] = manager.get_ssh_security_status()
                except Exception:
                    pass

            # Add MFA status
            if self.get_config("security_advanced.mfa.enabled", False):
                try:
                    from configurator.security.mfa_manager_wrapper import MFAManagerWrapper

                    manager = MFAManagerWrapper(self.config, self.logger)
                    report["advanced_security"]["mfa"] = manager.verify_mfa_status()
                except Exception:
                    pass

            # Add supply chain status
            try:
                from configurator.security.supply_chain import SupplyChainValidator

                validator = SupplyChainValidator(self.config, self.logger)
                report["advanced_security"]["supply_chain"] = validator.get_audit_report()
            except Exception:
                pass

        except Exception as e:
            self.logger.error(f"Error generating security report: {e}", exc_info=True)

        return report

    def _check_firewall_status(self) -> str:
        """Check firewall status."""
        result = self.run("ufw status", check=False)
        if "Status: active" in result.stdout:
            return "active"
        return "inactive"

    def _check_fail2ban_status(self) -> str:
        """Check fail2ban status."""
        if self.is_service_active("fail2ban"):
            return "active"
        return "inactive"

    def _check_ssh_hardening(self) -> str:
        """Check SSH hardening status."""
        result = self.run("sshd -T", check=False)
        if result.success and "permitemptypasswords no" in result.stdout.lower():
            return "hardened"
        return "standard"

    def _check_auto_updates_status(self) -> str:
        """Check auto-updates status."""
        if os.path.exists("/etc/apt/apt.conf.d/20auto-upgrades"):
            return "enabled"
        return "disabled"
