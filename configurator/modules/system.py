"""
System module for base system configuration.

Handles:
- Package repository optimization
- Hostname configuration
- Timezone configuration
- Locale configuration
- Swap configuration
- Kernel parameter tuning
"""

import os
import re

from configurator.exceptions import ModuleExecutionError, PrerequisiteError
from configurator.modules.base import ConfigurationModule
from configurator.utils.file import backup_file, write_file
from configurator.utils.system import (
    get_current_hostname,
    get_current_timezone,
    get_disk_free_gb,
    get_os_info,
    get_swap_info,
)


class SystemModule(ConfigurationModule):
    """
    System optimization and configuration module.

    This is the first module to run and sets up the base system.
    """

    name = "System Base"
    description = "Base system configuration (curl, wget, build-essential)"
    depends_on = []
    priority = 10
    mandatory = True

    # Essential packages to install
    ESSENTIAL_PACKAGES = [
        "curl",
        "wget",
        "git",
        "vim",
        "htop",
        "build-essential",
        "apt-transport-https",
        "ca-certificates",
        "gnupg",
        "lsb-release",
        "unzip",
        "zip",
        "jq",
    ]

    def validate(self) -> bool:
        """Validate system prerequisites."""
        os_info = get_os_info()

        # Check Debian version
        if not os_info.is_debian:
            raise PrerequisiteError(
                what=f"Unsupported operating system: {os_info.pretty_name}",
                why="This tool is designed for Debian 13 (Trixie) only",
                how="Please use a fresh Debian 13 VPS",
                docs_link="https://github.com/yunaamelia/debian-vps-workstation#requirements",
            )

        if not os_info.is_debian_13:
            raise PrerequisiteError(
                what=f"Unsupported Debian version: {os_info.version_id}",
                why="This tool requires Debian 13 (Trixie)",
                how=f"Your system: Debian {os_info.version_id}\n"
                "Required: Debian 13 (Trixie)\n"
                "Please use a fresh Debian 13 VPS.",
            )

        self.logger.info(f"✓ Detected: {os_info.pretty_name}")
        return True

    def configure(self) -> bool:
        """Configure the system."""
        self.logger.info("Configuring base system...")

        # 1. Update package lists
        self._update_packages()

        # 2. Install essential packages
        self._install_essentials()

        # 3. Configure hostname
        self._configure_hostname()

        # 4. Configure timezone
        self._configure_timezone()

        # 5. Configure locale
        self._configure_locale()

        # 6. Configure swap
        self._configure_swap()

        # 7. Tune kernel parameters
        if self.get_config("kernel_tuning", True):
            self._tune_kernel()

        # 8. Initialize FIM
        self._initialize_fim()

        self.logger.info("✓ System configuration complete")
        return True

    def _initialize_fim(self):
        """Initialize File Integrity Monitoring."""
        self.logger.info("Initializing File Integrity Monitoring baseline...")
        try:
            from configurator.core.file_integrity import FileIntegrityMonitor

            fim = FileIntegrityMonitor()
            fim.initialize()

            # Enable systemd check if on a systemd system
            if os.path.isdir("/etc/systemd/system"):
                # Copy service files from where relevant?
                # Since this is running as python package, I might not have source files easily.
                # I'll manually create them or assume they are deployed by installer.
                # For now, I'll just init the baseline.
                pass

        except Exception as e:
            self.logger.warning(f"Failed to initialize FIM: {e}")

    def verify(self) -> bool:
        """Verify system configuration."""
        checks_passed = True

        # Check hostname
        expected_hostname = self.get_config("hostname", "dev-workstation")
        current_hostname = get_current_hostname()
        if current_hostname != expected_hostname:
            self.logger.warning(
                f"Hostname mismatch: expected {expected_hostname}, got {current_hostname}"
            )
            checks_passed = False

        # Check timezone
        expected_tz = self.get_config("timezone", "UTC")
        current_tz = get_current_timezone()
        if current_tz != expected_tz:
            self.logger.warning(f"Timezone mismatch: expected {expected_tz}, got {current_tz}")
            checks_passed = False

        # Check essential commands exist
        for cmd in ["curl", "wget", "git", "htop"]:
            if not self.command_exists(cmd):
                self.logger.warning(f"Command not found: {cmd}")
                checks_passed = False

        return checks_passed

    def _update_packages(self):
        """Update package lists."""
        self.logger.info("Updating package lists...")
        self.run("apt-get update", check=True)

        # Upgrade existing packages
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        self.run(
            "apt-get upgrade -y",
            check=False,  # Don't fail on upgrade issues
            env=env,
        )

    def _install_essentials(self):
        """Install essential packages."""
        self.logger.info("Installing essential packages...")
        self.install_packages(self.ESSENTIAL_PACKAGES, update_cache=False)

    def _configure_hostname(self):
        """Configure system hostname."""
        hostname = self.get_config("hostname", "dev-workstation")

        # Validate hostname format
        if not re.match(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", hostname):
            raise ModuleExecutionError(
                what=f"Invalid hostname: {hostname}",
                why="Hostname must be lowercase alphanumeric with optional hyphens",
                how="Use a valid hostname like 'dev-workstation' or 'myserver'",
            )

        current_hostname = get_current_hostname()

        if current_hostname == hostname:
            self.logger.info(f"✓ Hostname already set: {hostname}")
            return

        self.logger.info(f"Setting hostname: {hostname}")

        # Set hostname
        self.run(
            f"hostnamectl set-hostname {hostname}",
            rollback_command=f"hostnamectl set-hostname {current_hostname}",
            description="Restore original hostname",
        )

        # Update /etc/hosts
        backup_file("/etc/hosts")

        hosts_content = """127.0.0.1   localhost
127.0.1.1   {hostname}

# IPv6
::1         localhost ip6-localhost ip6-loopback
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
"""
        write_file("/etc/hosts", hosts_content, backup=False)

        self.logger.info(f"✓ Hostname: {hostname}")

    def _configure_timezone(self):
        """Configure system timezone."""
        timezone = self.get_config("timezone", "UTC")
        current_tz = get_current_timezone()

        if current_tz == timezone:
            self.logger.info(f"✓ Timezone already set: {timezone}")
            return

        self.logger.info(f"Setting timezone: {timezone}")

        self.run(
            f"timedatectl set-timezone {timezone}",
            rollback_command=f"timedatectl set-timezone {current_tz}",
            description="Restore original timezone",
        )

        self.logger.info(f"✓ Timezone: {timezone}")

    def _configure_locale(self):
        """Configure system locale."""
        locale = self.get_config("locale", "en_US.UTF-8")

        self.logger.info(f"Configuring locale: {locale}")

        # Generate locale
        self.run(f"locale-gen {locale}", check=False)

        # Set default locale
        self.run(f"update-locale LANG={locale}", check=False)

        self.logger.info(f"✓ Locale: {locale}")

    def _configure_swap(self):
        """Configure swap space."""
        swap_size_gb = self.get_config("swap_size_gb", 2)

        if swap_size_gb <= 0:
            self.logger.info("Swap configuration skipped (disabled)")
            return

        # Check existing swap
        current_swap, _ = get_swap_info()

        if current_swap >= swap_size_gb * 0.9:  # Within 10% of target
            self.logger.info(f"✓ Swap already configured: {current_swap:.1f} GB")
            return

        # Check available disk space
        free_gb = get_disk_free_gb("/")
        if free_gb < swap_size_gb + 5:  # Keep at least 5GB free
            self.logger.warning(f"Skipping swap creation: only {free_gb:.1f} GB free")
            return

        swap_file = "/swapfile"
        swap_size_mb = int(swap_size_gb * 1024)

        self.logger.info(f"Creating {swap_size_gb} GB swap file...")

        # Create swap file
        self.run(f"fallocate -l {swap_size_mb}M {swap_file}")
        self.run(f"chmod 600 {swap_file}")
        self.run(f"mkswap {swap_file}")
        self.run(f"swapon {swap_file}")

        # Add to fstab
        fstab_entry = f"\n{swap_file} none swap sw 0 0\n"
        with open("/etc/fstab", "a") as f:
            f.write(fstab_entry)

        self.rollback_manager.add_command(
            f"swapoff {swap_file} && rm {swap_file}",
            description="Remove swap file",
        )

        self.logger.info(f"✓ Swap: {swap_size_gb} GB")

    def _tune_kernel(self):
        """Apply kernel parameter tuning."""
        self.logger.info("Tuning kernel parameters...")

        sysctl_config = """# Debian VPS Workstation - Kernel Tuning
# Generated by debian-vps-configurator

# Memory Management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File System
fs.file-max = 100000
fs.inotify.max_user_watches = 524288

# Network Performance
net.core.netdev_max_backlog = 5000
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# TCP Optimization
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200

# BBR Congestion Control (if available)
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
"""

        sysctl_file = "/etc/sysctl.d/99-vps-workstation.conf"
        write_file(sysctl_file, sysctl_config)

        # Apply settings
        self.run(f"sysctl -p {sysctl_file}", check=False)

        self.rollback_manager.add_command(
            f"rm {sysctl_file} && sysctl --system",
            description="Remove custom kernel parameters",
        )

        self.logger.info("✓ Kernel parameters tuned")
