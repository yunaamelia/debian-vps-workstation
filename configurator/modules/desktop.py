"""
Desktop module for xrdp + XFCE4 remote desktop.

Handles:
- xrdp server installation
- XFCE4 desktop environment
- SSL certificate configuration
- Session management
"""

import os
import pwd
import re
import shlex

from configurator.exceptions import ModuleExecutionError
from configurator.modules.base import ConfigurationModule
from configurator.utils.file import backup_file, write_file
from configurator.utils.system import get_disk_free_gb


class DesktopModule(ConfigurationModule):
    """
    Remote Desktop Environment Module (XRDP + XFCE4).

    Installs and configures a production-ready remote desktop environment with:

    Phase 1 - XRDP Performance:
        - Optimized xrdp.ini (tcp_nodelay, bitmap caching)
        - Optimized sesman.ini (session timeouts, Xvnc parameters)
        - User session startup scripts (.xsession)

    Phase 2 - XFCE Optimization:
        - Compositor tuning (disabled/optimized/enabled modes)
        - Polkit rule configuration (prevent auth popups)

    Configuration:
        desktop:
          enabled: true
          xrdp:
            max_bpp: 24
            bitmap_cache: true
            security_layer: "tls"
          compositor:
            mode: "disabled"  # disabled | optimized | enabled
          polkit:
            allow_colord: true
            allow_packagekit: true

    Dependencies:
        - system (for base packages)
        - security (for firewall rules)

    Performance Characteristics:
        - Compositor disabled: Best performance, no visual lag
        - Compositor optimized: Balanced (some effects, VSync off)
        - Compositor enabled: Full effects (LAN-only)

    Security:
        - Username validation prevents command injection
        - File permissions properly set (644 for configs)
        - TLS security enabled by default
        - Polkit rules limited to safe operations
    """

    name = "Desktop Environment"
    description = "XFCE4 Desktop and XRDP"
    priority = 30
    depends_on = ["system", "security"]
    force_sequential = True
    mandatory = False

    # User UID ranges (POSIX standard)
    MIN_USER_UID = 1000
    MAX_USER_UID = 65534

    # Valid XRDP configuration values
    VALID_BPP_VALUES = [8, 15, 16, 24, 32]
    VALID_SECURITY_LAYERS = ["tls", "rdp", "negotiate"]

    # Valid compositor modes
    VALID_COMPOSITOR_MODES = ["disabled", "optimized", "enabled"]

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

        # === Phase 1: Performance optimizations ===
        # 4. Optimize XRDP performance
        self._optimize_xrdp_performance()

        # 5. Configure user session
        self._configure_user_session()

        # === Phase 2: XFCE & Polkit optimizations ===
        # 6. Optimize XFCE compositor
        self._optimize_xfce_compositor()

        # 7. Configure Polkit rules
        self._configure_polkit_rules()

        # 8. Configure session (polkit rules)
        self._configure_session()

        # 9. Start services
        self._start_services()

        self.logger.info("✓ Remote Desktop installed with full optimizations")
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

        # === Phase 2: Verify compositor and Polkit configuration ===
        # Check compositor configuration
        compositor_mode = self.get_config("desktop.compositor.mode", "disabled")
        self._verify_compositor_config(compositor_mode)

        # Check Polkit rules
        self._verify_polkit_rules()

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

    def _optimize_xrdp_performance(self):
        """Apply production-ready XRDP performance optimizations."""
        self.logger.info("Optimizing XRDP performance settings...")

        # Get performance settings from config (with sensible defaults)
        max_bpp = self.get_config("desktop.xrdp.max_bpp", 24)
        enable_bitmap_cache = self.get_config("desktop.xrdp.bitmap_cache", True)
        security_layer = self.get_config("desktop.xrdp.security_layer", "tls")
        tcp_nodelay = self.get_config("desktop.xrdp.tcp_nodelay", True)

        # Validate configuration values
        if max_bpp not in self.VALID_BPP_VALUES:
            self.logger.warning(
                f"Invalid max_bpp={max_bpp}, using 24. Valid values: {self.VALID_BPP_VALUES}"
            )
            max_bpp = 24

        if security_layer not in self.VALID_SECURITY_LAYERS:
            self.logger.warning(
                f"Invalid security_layer={security_layer}, using tls. "
                f"Valid values: {self.VALID_SECURITY_LAYERS}"
            )
            security_layer = "tls"

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_file_write("/etc/xrdp/xrdp.ini")
                self.dry_run_manager.record_file_write("/etc/xrdp/sesman.ini")
            self.logger.info(
                f"[DRY RUN] Would optimize XRDP configs with max_bpp={max_bpp}, "
                f"security={security_layer}"
            )
            return

        # Backup original configs
        try:
            backup_file("/etc/xrdp/xrdp.ini")
            backup_file("/etc/xrdp/sesman.ini")
        except Exception as e:
            self.logger.warning(f"Could not backup XRDP configs: {e}")
            # Continue - files might not exist yet

        # Configure xrdp.ini with optimized settings
        xrdp_ini_content = f"""# xrdp.ini - Performance Optimized Configuration
# Generated by debian-vps-workstation configurator

[Globals]
# Performance Optimizations
bitmap_compression=true
bulk_compression=true
max_bpp={max_bpp}
xserverbpp=24

# Security
security_layer={security_layer}
crypt_level=high

# Network optimizations (critical for responsiveness)
tcp_nodelay={str(tcp_nodelay).lower()}
tcp_keepalive=true

# Logging
log_level=WARNING

# Fork settings
fork=true

# Bitmap caching (huge performance win)
bitmap_cache={str(enable_bitmap_cache).lower()}

# Connection Settings
[xrdp1]
name=sesman-Xvnc
lib=libvnc.so
username=ask
password=ask
ip=127.0.0.1
port=-1
xserverbpp=24
code=20
"""

        try:
            write_file("/etc/xrdp/xrdp.ini", xrdp_ini_content, backup=False)
            self.logger.info("✓ xrdp.ini configured")
        except Exception as e:
            raise ModuleExecutionError(
                what="Failed to write xrdp.ini",
                why=str(e),
                how="Check /etc/xrdp/ permissions and disk space",
            )

        # Configure sesman.ini with optimized settings
        sesman_ini_content = """# sesman.ini - Performance Optimized Configuration
# Generated by debian-vps-workstation configurator

[Globals]
ListenAddress=127.0.0.1
ListenPort=3350
EnableUserWindowManager=true
UserWindowManager=startwm.sh
DefaultWindowManager=startwm.sh

[Security]
AllowRootLogin=false
MaxLoginRetry=4
TerminalServerUsers=tsusers
TerminalServerAdmins=tsadmins

[Sessions]
# Disable delays for better performance
X11DisplayOffset=10
MaxSessions=10
KillDisconnected=false
IdleTimeLimit=0
DisconnectedTimeLimit=0

[Logging]
LogLevel=WARNING
EnableSyslog=false
SyslogLevel=WARNING

[Xvnc]
param1=-bs
param2=-ac
param3=-nolisten tcp
param4=-localhost
param5=-dpi 96
# Performance parameters
param6=-DefineDefaultFontPath=catalogue:/etc/X11/fontpath.d
param7=+extension GLX
param8=+extension RANDR
param9=+extension RENDER
"""

        try:
            write_file("/etc/xrdp/sesman.ini", sesman_ini_content, backup=False)
            self.logger.info("✓ sesman.ini configured")
        except Exception as e:
            raise ModuleExecutionError(
                what="Failed to write sesman.ini",
                why=str(e),
                how="Check /etc/xrdp/ permissions and disk space",
            )

        self.logger.info("✓ XRDP performance optimizations applied")

        # Restart services to apply changes
        try:
            self.logger.info("Restarting XRDP services...")
            self.run("systemctl restart xrdp", check=True)
            self.run("systemctl restart xrdp-sesman", check=False)
            self.logger.info("✓ XRDP services restarted")
        except Exception as e:
            self.logger.warning(f"Could not restart XRDP services: {e}")
            self.logger.warning("XRDP configuration updated but manual restart required")

    def _configure_user_session(self):
        """Configure user session startup script for XRDP."""
        self.logger.info("Configuring user session startup...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command("configure .xsession for all users")
            self.logger.info(
                f"[DRY RUN] Would create .xsession files for users with "
                f"UID >= {self.MIN_USER_UID}"
            )
            return

        # Get all non-system users (UID range from constants)
        try:
            users = [
                u.pw_name
                for u in pwd.getpwall()
                if u.pw_uid >= self.MIN_USER_UID and u.pw_uid < self.MAX_USER_UID
            ]
        except Exception as e:
            self.logger.warning(f"Could not enumerate users: {e}")
            users = []

        if not users:
            self.logger.warning("No regular users found, skipping .xsession configuration")
            return

        for user in users:
            # Validate username format (POSIX-compliant: lowercase, digits, underscore, hyphen)
            if not re.match(r"^[a-z_][a-z0-9_-]{0,31}$", user):
                self.logger.warning(f"Skipping user with invalid username format: {user}")
                continue

            try:
                user_home = pwd.getpwnam(user).pw_dir

                # Validate home directory
                if not os.path.isabs(user_home):
                    self.logger.warning(f"Skipping user {user}: invalid home path")
                    continue

                if not os.path.isdir(user_home):
                    self.logger.warning(f"Skipping user {user}: home directory doesn't exist")
                    continue

                xsession_path = os.path.join(user_home, ".xsession")

                xsession_content = """#!/bin/bash
# .xsession - XRDP Session Startup Configuration
# Generated by debian-vps-workstation configurator

# === Environment Setup ===
export NO_AT_BRIDGE=1
export GNOME_KEYRING_CONTROL=""
export GTK_MODULES=""

# === Session Variables ===
export XDG_SESSION_DESKTOP=xfce
export XDG_CURRENT_DESKTOP=XFCE
export DESKTOP_SESSION=xfce
export DISPLAY=:10

# === Cursor Fix ===
export XCURSOR_THEME=Adwaita
export XCURSOR_SIZE=24

# === Performance: Disable Screen Blanking ===
xset s off 2>/dev/null
xset -dpms 2>/dev/null
xset s noblank 2>/dev/null

# === Cursor Rendering Fix ===
xsetroot -cursor_name left_ptr 2>/dev/null

# === Start XFCE ===
exec startxfce4
"""

                # Use shlex.quote for shell safety
                safe_user = shlex.quote(user)
                safe_path = shlex.quote(xsession_path)

                # Write file as user (not root) and make executable
                self.run(
                    f"sudo -u {safe_user} bash -c 'cat > {safe_path}'",
                    input=xsession_content.encode(),
                    check=False,
                )
                self.run(f"chmod +x {safe_path}", check=False)
                self.run(f"chown {safe_user}:{safe_user} {safe_path}", check=False)

                self.logger.info(f"✓ Configured .xsession for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to configure .xsession for user {user}: {e}")
                continue

    def _optimize_xfce_compositor(self):
        """
        Optimize XFCE compositor for remote desktop performance.

        Disables or tunes compositor settings that cause lag over RDP:
        - Disables compositing entirely (recommended) OR
        - Disables VSync, shadows, and opacity effects

        Configuration is applied per-user to ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
        """
        self.logger.info("Optimizing XFCE compositor for remote desktop...")

        # Validate compositor mode
        raw_mode = self.get_config("desktop.compositor.mode", "disabled")
        compositor_mode = self._validate_compositor_mode(raw_mode)

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command(
                    f"configure XFCE compositor mode: {compositor_mode}"
                )
            self.logger.info(f"[DRY RUN] Would configure compositor mode: {compositor_mode}")
            return

        # Get all regular users
        try:
            users = [
                u.pw_name
                for u in pwd.getpwall()
                if u.pw_uid >= self.MIN_USER_UID and u.pw_uid < self.MAX_USER_UID
            ]
        except Exception as e:
            self.logger.warning(f"Could not enumerate users: {e}")
            return

        if not users:
            self.logger.warning("No regular users found, skipping compositor configuration")
            return

        for user in users:
            # CRITICAL: Validate username before using in shell commands
            if not self._validate_user_safety(user):
                self.logger.error(f"Skipping unsafe username: {user}")
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Validate home directory exists
                if not os.path.isabs(user_home):
                    self.logger.warning(f"Skipping user {user}: invalid home path")
                    continue

                if not os.path.isdir(user_home):
                    self.logger.warning(f"Skipping user {user}: home directory doesn't exist")
                    continue

                # Create XFCE config directory structure
                xfconf_dir = os.path.join(
                    user_home, ".config", "xfce4", "xfconf", "xfce-perchannel-xml"
                )

                safe_user = shlex.quote(user)
                safe_dir = shlex.quote(xfconf_dir)

                self.run(f"sudo -u {safe_user} mkdir -p {safe_dir}", check=False)

                # Generate xfwm4.xml based on mode
                xfwm4_config = self._generate_xfwm4_config(compositor_mode)

                xfwm4_path = os.path.join(xfconf_dir, "xfwm4.xml")
                safe_path = shlex.quote(xfwm4_path)

                # Write config as user
                self.run(
                    f"sudo -u {safe_user} bash -c 'cat > {safe_path}'",
                    input=xfwm4_config.encode(),
                    check=False,
                )

                # Set correct permissions
                self.run(f"chmod 644 {safe_path}", check=False)
                self.run(f"chown {safe_user}:{safe_user} {safe_path}", check=False)

                self.logger.info(
                    f"✓ Configured XFCE compositor ({compositor_mode}) for user: {user}"
                )

                # Register rollback action
                if self.rollback_manager:
                    self.rollback_manager.add_command(
                        f"rm -f {safe_path}",
                        description=f"Remove compositor config for {user}",
                    )

            except Exception as e:
                self.logger.error(f"Failed to configure compositor for user {user}: {e}")
                continue

    def _generate_xfwm4_config(self, mode: str) -> str:
        """
        Generate xfwm4.xml configuration based on compositor mode.

        Args:
            mode: "disabled" | "optimized" | "enabled"

        Returns:
            XML configuration string
        """
        if mode == "disabled":
            # Completely disable compositing (recommended for RDP)
            return """<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <!-- Disable compositing entirely for remote sessions -->
    <property name="use_compositing" type="bool" value="false"/>

    <!-- Opacity settings (only apply if compositing enabled) -->
    <property name="frame_opacity" type="int" value="100"/>
    <property name="inactive_opacity" type="int" value="100"/>
    <property name="move_opacity" type="int" value="100"/>
    <property name="popup_opacity" type="int" value="100"/>
    <property name="resize_opacity" type="int" value="100"/>

    <!-- Disable shadows (performance) -->
    <property name="show_frame_shadow" type="bool" value="false"/>
    <property name="show_popup_shadow" type="bool" value="false"/>
  </property>
</channel>
"""

        elif mode == "optimized":
            # Enable compositing but disable expensive features
            return """<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <!-- Keep compositing but optimize for remote -->
    <property name="use_compositing" type="bool" value="true"/>

    <!-- Disable VSync (causes stuttering over RDP) -->
    <property name="vblank_mode" type="string" value="off"/>

    <!-- Disable zoom effects -->
    <property name="zoom_desktop" type="bool" value="false"/>

    <!-- Full opacity (no transparency) -->
    <property name="frame_opacity" type="int" value="100"/>
    <property name="inactive_opacity" type="int" value="100"/>
    <property name="move_opacity" type="int" value="100"/>
    <property name="popup_opacity" type="int" value="100"/>
    <property name="resize_opacity" type="int" value="100"/>

    <!-- Disable shadows -->
    <property name="show_frame_shadow" type="bool" value="false"/>
    <property name="show_popup_shadow" type="bool" value="false"/>
  </property>
</channel>
"""

        else:  # mode == "enabled"
            # Full compositing (for LAN-only high-bandwidth connections)
            return """<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <!-- Full compositing enabled -->
    <property name="use_compositing" type="bool" value="true"/>

    <!-- VSync enabled for smooth animations -->
    <property name="vblank_mode" type="string" value="auto"/>

    <!-- Enable effects -->
    <property name="zoom_desktop" type="bool" value="true"/>

    <!-- Default opacity settings -->
    <property name="frame_opacity" type="int" value="100"/>
    <property name="inactive_opacity" type="int" value="100"/>

    <!-- Shadows enabled -->
    <property name="show_frame_shadow" type="bool" value="true"/>
    <property name="show_popup_shadow" type="bool" value="true"/>
  </property>
</channel>
"""

    def _configure_polkit_rules(self):
        """
        Configure Polkit rules to prevent authentication popups in remote sessions.

        Creates rules for:
        - colord (color management)
        - packagekit (package management)

        Rules allow operations for all users without password prompt.
        """
        self.logger.info("Configuring Polkit rules for remote desktop...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command("configure Polkit rules")
            self.logger.info("[DRY RUN] Would configure Polkit rules")
            return True

        # Check if Polkit directory exists
        polkit_dir = "/etc/polkit-1/localauthority/50-local.d"
        if not os.path.isdir(polkit_dir):
            self.logger.warning(f"Polkit directory not found: {polkit_dir}")
            # Try to create it
            try:
                self.run(f"mkdir -p {polkit_dir}", check=True)
            except Exception as e:
                self.logger.error(f"Failed to create Polkit directory: {e}")
                return False

        # Get list of rules to install from config
        install_colord = self.get_config("desktop.polkit.allow_colord", True)
        install_packagekit = self.get_config("desktop.polkit.allow_packagekit", True)

        rules_installed = []

        # Install colord rule
        if install_colord:
            colord_rule_path = os.path.join(polkit_dir, "45-allow-colord.pkla")
            colord_rule_content = """[Allow Colord for XFCE]
Identity=unix-user:*
Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
ResultAny=no
ResultInactive=no
ResultActive=yes
"""
            try:
                # Backup if exists
                if os.path.exists(colord_rule_path):
                    backup_file(colord_rule_path)

                write_file(colord_rule_path, colord_rule_content, mode="w", backup=False)
                self.run(f"chmod 644 {colord_rule_path}", check=False)

                rules_installed.append("colord")
                self.logger.info("✓ Installed Polkit rule: colord")

                # Register rollback
                if self.rollback_manager:
                    self.rollback_manager.add_command(
                        f"rm -f {colord_rule_path}",
                        description="Remove colord Polkit rule",
                    )

            except Exception as e:
                self.logger.error(f"Failed to install colord rule: {e}")

        # Install packagekit rule
        if install_packagekit:
            packagekit_rule_path = os.path.join(polkit_dir, "46-allow-packagekit.pkla")
            packagekit_rule_content = """[Allow Package Management]
Identity=unix-user:*
Action=org.freedesktop.packagekit.*
ResultAny=no
ResultInactive=no
ResultActive=yes
"""
            try:
                # Backup if exists
                if os.path.exists(packagekit_rule_path):
                    backup_file(packagekit_rule_path)

                write_file(packagekit_rule_path, packagekit_rule_content, mode="w", backup=False)
                self.run(f"chmod 644 {packagekit_rule_path}", check=False)

                rules_installed.append("packagekit")
                self.logger.info("✓ Installed Polkit rule: packagekit")

                # Register rollback
                if self.rollback_manager:
                    self.rollback_manager.add_command(
                        f"rm -f {packagekit_rule_path}",
                        description="Remove packagekit Polkit rule",
                    )

            except Exception as e:
                self.logger.error(f"Failed to install packagekit rule: {e}")

        # Restart polkit service to apply rules
        if rules_installed:
            try:
                self.run("systemctl restart polkit", check=False)
                self.logger.info(f"✓ Polkit rules configured: {', '.join(rules_installed)}")
            except Exception as e:
                self.logger.warning(f"Failed to restart polkit service: {e}")

        return len(rules_installed) > 0

    def _verify_compositor_config(self, expected_mode: str) -> bool:
        """Verify compositor configuration for all users."""
        try:
            users = [
                u.pw_name
                for u in pwd.getpwall()
                if u.pw_uid >= self.MIN_USER_UID and u.pw_uid < self.MAX_USER_UID
            ]
        except Exception as e:
            self.logger.warning(f"Could not enumerate users: {e}")
            return True

        for user in users:
            try:
                user_home = pwd.getpwnam(user).pw_dir
                xfwm4_path = os.path.join(
                    user_home,
                    ".config",
                    "xfce4",
                    "xfconf",
                    "xfce-perchannel-xml",
                    "xfwm4.xml",
                )

                if not os.path.exists(xfwm4_path):
                    self.logger.warning(f"Compositor config not found for user {user}")
                    continue

                # Read and verify config
                with open(xfwm4_path, "r") as f:
                    content = f.read()

                if expected_mode == "disabled":
                    if 'value="false"' in content and "use_compositing" in content:
                        self.logger.info(f"✓ Compositor disabled for user: {user}")
                    else:
                        self.logger.warning(f"Compositor config mismatch for user: {user}")

                elif expected_mode == "optimized":
                    if "vblank_mode" in content and 'value="off"' in content:
                        self.logger.info(f"✓ Compositor optimized for user: {user}")
                    else:
                        self.logger.warning(f"Compositor config mismatch for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to verify compositor for user {user}: {e}")

        return True

    def _verify_polkit_rules(self) -> bool:
        """Verify Polkit rules are installed and valid."""
        polkit_dir = "/etc/polkit-1/localauthority/50-local.d"

        # Check colord rule
        colord_rule = os.path.join(polkit_dir, "45-allow-colord.pkla")
        if os.path.exists(colord_rule):
            self.logger.info("✓ Polkit rule installed: colord")
        else:
            self.logger.warning("Polkit rule missing: colord")

        # Check packagekit rule
        packagekit_rule = os.path.join(polkit_dir, "46-allow-packagekit.pkla")
        if os.path.exists(packagekit_rule):
            self.logger.info("✓ Polkit rule installed: packagekit")
        else:
            self.logger.warning("Polkit rule missing: packagekit")

        # Check polkit service
        result = self.run("systemctl is-active polkit", check=False, force_execute=True)
        if result.success:
            self.logger.info("✓ Polkit service is active")
        else:
            self.logger.warning("Polkit service is not active")

        return True

    def _validate_compositor_mode(self, mode: str) -> str:
        """Validate and sanitize compositor mode input."""
        if mode not in self.VALID_COMPOSITOR_MODES:
            self.logger.warning(
                f"Invalid compositor mode '{mode}', defaulting to 'disabled'. "
                f"Valid modes: {', '.join(self.VALID_COMPOSITOR_MODES)}"
            )
            return "disabled"

        return mode

    def _validate_user_safety(self, username: str) -> bool:
        """
        Validate username for security.

        Prevents command injection via malicious usernames.

        Returns:
            True if username is safe, False otherwise
        """
        # Username must match POSIX portable username format
        if not re.match(r"^[a-z_][a-z0-9_-]*[$]?$", username):
            self.logger.warning(f"Invalid or potentially malicious username: {username}")
            return False

        # Additional checks
        if len(username) > 32:
            self.logger.warning(f"Username too long: {username}")
            return False

        # Check for shell metacharacters
        dangerous_chars = [";", "&", "|", "$", "`", "\n", "\r", ">", "<", "(", ")"]
        if any(char in username for char in dangerous_chars):
            self.logger.warning(f"Username contains dangerous characters: {username}")
            return False

        return True

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
