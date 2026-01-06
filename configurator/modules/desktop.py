"""
Desktop module for xrdp + XFCE4 remote desktop.

Handles:
- xrdp server installation
- XFCE4 desktop environment
- SSL certificate configuration
- Session management
"""

from configurator.exceptions import ModuleExecutionError
from configurator.modules.base import ConfigurationModule
from configurator.utils.file import backup_file, write_file
from configurator.utils.system import get_disk_free_gb


class DesktopModule(ConfigurationModule):
    """
    Remote desktop module (xrdp + XFCE4).

    Installs and configures a lightweight remote desktop
    environment accessible via standard RDP clients.
    """

    name = "Desktop Environment"
    description = "XFCE4 Desktop and XRDP"
    priority = 30
    depends_on = ["system", "security"]
    force_sequential = True
    mandatory = False

    # Packages for XFCE4 desktop
    XFCE_PACKAGES = [
        "xfce4",
        "xfce4-goodies",
        "xfce4-terminal",
        "thunar",
        "firefox-esr",
        "dbus-x11",
    ]

    # Packages for xrdp
    XRDP_PACKAGES = [
        "xrdp",
        "xorgxrdp",
    ]

    def validate(self) -> bool:
        """Validate prerequisites for desktop installation."""
        # Check disk space (desktop needs ~2-3GB)
        free_gb = get_disk_free_gb("/")
        if free_gb < 5:
            self.logger.warning(
                f"Low disk space: {free_gb:.1f} GB free. " "Desktop installation may fail."
            )

        self.logger.info(f"✓ Disk space: {free_gb:.1f} GB free")
        return True

    def configure(self) -> bool:
        """Install and configure remote desktop."""
        self.logger.info("Installing Remote Desktop (xrdp + XFCE4)...")

        # 1. Install xrdp
        self._install_xrdp()

        # 2. Install XFCE4
        self._install_xfce4()

        # 3. Configure xrdp
        self._configure_xrdp()

        # 4. Configure session
        self._configure_session()

        # 5. Start services
        self._start_services()

        self.logger.info("✓ Remote Desktop installed")
        return True

    def verify(self) -> bool:
        """Verify remote desktop installation."""
        checks_passed = True

        # Check xrdp service
        if not self.is_service_active("xrdp"):
            self.logger.error("xrdp service is not running!")
            checks_passed = False
        else:
            self.logger.info("✓ xrdp service is running")

        # Check xrdp-sesman service
        if not self.is_service_active("xrdp-sesman"):
            self.logger.warning("xrdp-sesman service is not running")

        # Check port 3389
        result = self.run("ss -tlnp | grep :3389", check=False)
        if not result.success:
            self.logger.error("Port 3389 is not listening!")
            checks_passed = False
        else:
            self.logger.info("✓ Port 3389 is listening")

        # Check XFCE4 is installed
        if not self.command_exists("xfce4-session"):
            self.logger.error("XFCE4 is not installed!")
            checks_passed = False
        else:
            self.logger.info("✓ XFCE4 is installed")

        return checks_passed

    def _install_xrdp(self):
        """Install xrdp packages."""
        self.logger.info("Installing xrdp...")
        self.install_packages(self.XRDP_PACKAGES)

    def _install_xfce4(self):
        """Install XFCE4 desktop environment."""
        self.logger.info("Installing XFCE4 desktop (this may take a few minutes)...")
        self.install_packages(self.XFCE_PACKAGES, update_cache=False)

    def _configure_xrdp(self):
        """Configure xrdp for optimal performance."""
        self.logger.info("Configuring xrdp...")

        # Backup original config
        backup_file("/etc/xrdp/xrdp.ini")

        # Read current config and modify
        with open("/etc/xrdp/xrdp.ini", "r") as f:
            config = f.read()

        # Ensure key settings are correct
        modifications = {
            "max_bpp": "max_bpp=24",
            "xserverbpp": "xserverbpp=24",
            "crypt_level": "crypt_level=high",
            "bitmap_cache": "bitmap_cache=true",
            "bitmap_compression": "bitmap_compression=true",
            "bulk_compression": "bulk_compression=true",
        }

        # Apply modifications (simple approach - could be improved)
        for key, value in modifications.items():
            if key + "=" in config:
                # Replace existing setting
                import re

                config = re.sub(
                    rf"^{key}=.*$",
                    value,
                    config,
                    flags=re.MULTILINE,
                )

        write_file("/etc/xrdp/xrdp.ini", config, backup=False)

        # Add user to ssl-cert group for SSL access
        self.run("usermod -a -G ssl-cert xrdp", check=False)

        self.logger.info("✓ xrdp configured")

    def _configure_session(self):
        """Configure desktop session for xrdp."""
        self.logger.info("Configuring session...")

        # Create startwm.sh for xrdp (run as each user)
        startwm_content = """#!/bin/sh
# xrdp session startup script

# Source profile
if [ -r /etc/profile ]; then
    . /etc/profile
fi

# Source user's bashrc
if [ -r ~/.bashrc ]; then
    . ~/.bashrc
fi

# Start XFCE4 session
exec /usr/bin/startxfce4
"""

        backup_file("/etc/xrdp/startwm.sh")
        write_file("/etc/xrdp/startwm.sh", startwm_content, mode=0o755)

        # Fix polkit permissions for RDP users
        polkit_rule = """polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.color-manager.create-device" ||
         action.id == "org.freedesktop.color-manager.create-profile" ||
         action.id == "org.freedesktop.color-manager.delete-device" ||
         action.id == "org.freedesktop.color-manager.delete-profile" ||
         action.id == "org.freedesktop.color-manager.modify-device" ||
         action.id == "org.freedesktop.color-manager.modify-profile") &&
        subject.isInGroup("users")) {
        return polkit.Result.YES;
    }
});
"""

        polkit_dir = "/etc/polkit-1/rules.d"
        self.run(f"mkdir -p {polkit_dir}", check=False)
        write_file(
            f"{polkit_dir}/02-allow-colord.rules",
            polkit_rule,
        )

        self.logger.info("✓ Session configured")

    def _start_services(self):
        """Start xrdp services."""
        self.logger.info("Starting xrdp services...")

        # Enable and start xrdp
        self.enable_service("xrdp")

        # Verify started
        if not self.is_service_active("xrdp"):
            raise ModuleExecutionError(
                what="xrdp service failed to start",
                why="Check systemctl status xrdp for details",
                how="Try: sudo systemctl restart xrdp",
            )

        self.logger.info("✓ xrdp services started")
        self.logger.info("  You can now connect via RDP on port 3389")
