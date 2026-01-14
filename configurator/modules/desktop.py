"""
Desktop module for xrdp + XFCE4 remote desktop.

Handles:
- xrdp server installation with xorgxrdp backend (Pure RDP - NO VNC)
- XFCE4 desktop environment with performance optimizations
- Dynamic resolution support for mobile/portrait displays
- SSL certificate configuration
- Session management
- Xwrapper configuration for non-console users
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

    Phase 1 - XRDP Best Practices:
        - Pure XRDP with xorgxrdp backend (NO VNC for better performance)
        - Optimized xrdp.ini (tcp_nodelay, bitmap caching, dynamic resolution)
        - Optimized sesman.ini (Xorg backend configuration)
        - Xwrapper.config (allow non-console users to start X server)
        - Dynamic resolution support (8192x8192 max, mobile portrait/landscape)

    Phase 2 - XFCE Optimization:
        - Compositor disabled for remote desktop performance
        - Polkit rule configuration (prevent auth popups)
        - User .xsession optimization (dbus, no compositing)

    Configuration:
        desktop:
          enabled: true
          xrdp:
            max_bpp: 32
            bitmap_cache: true
            security_layer: "rdp"
          compositor:
            mode: "disabled"  # disabled | optimized | enabled
          polkit:
            allow_colord: true
            allow_packagekit: true

    Dependencies:
        - system (for base packages)
        - security (for firewall rules)

    Performance Characteristics:
        - Pure Xorg backend: Native performance without VNC overhead
        - Dynamic resolution: Auto-adjusts to client screen size
        - Compositor disabled: Best performance, no visual lag
        - Bitmap caching: Reduces bandwidth usage significantly

    Security:
        - Username validation prevents command injection
        - File permissions properly set (644 for configs)
        - TLS/RDP security enabled by default
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
                f"Low disk space: {free_gb:.1f} GB free. Desktop installation may fail."
            )

        self.logger.info(f"✓ Disk space: {free_gb:.1f} GB free")
        return True

    def configure(self) -> bool:
        """Install and configure remote desktop."""
        import traceback

        self.logger.info("Installing Remote Desktop (xrdp + XFCE4)...")

        try:
            # 1. Install xrdp
            self._install_xrdp()

            # 2. Install XFCE4
            self._install_xfce4()

            # 3. Configure xrdp
            self._configure_xrdp()

            # === Phase 1: Performance optimizations ===
            # 4. Optimize XRDP performance
            self._optimize_xrdp_performance()

            # 4.5. Configure Xwrapper (allow non-console users to start X)
            self._configure_xwrapper()

            # 5. Configure user session
            self._configure_user_session()

            # === Phase 2: XFCE & Polkit optimizations ===
            # 6. Optimize XFCE compositor
            self._optimize_xfce_compositor()

            # 7. Configure Polkit rules
            self._configure_polkit_rules()

            # === Phase 3: Visual Customization ===
            # 8. Install themes
            self._install_themes()

            # 9. Install icon packs
            self._install_icon_packs()

            # 10. Configure fonts
            self._configure_fonts()

            # 11. Configure panel layout
            self._configure_panel_layout()

            # 12. Apply theme and icons
            self._apply_theme_and_icons()

            # === Phase 4: Zsh Configuration ===
            self._install_and_configure_zsh()

            # === NEW: Phase 5 - Advanced Terminal Tools ===
            self._configure_advanced_terminal_tools()
            self._install_optional_productivity_tools()

            # === Finalization ===
            # 13. Configure session (polkit rules)
            self._configure_session()

            # 14. Start services
            self._start_services()

            self.logger.info("✓ Remote Desktop with complete productivity environment configured")
            return True

        except Exception:
            self.logger.error(f"Desktop configuration failed at step: {traceback.format_exc()}")
            raise

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

        # === Phase 3: Verify themes and icons ===
        if not self._verify_themes_and_icons():
            checks_passed = False

        # === Phase 4: Verify Zsh ===
        if not self._verify_zsh_installation():
            checks_passed = False

        # Phase 5 verification
        if not self._verify_advanced_tools():
            checks_passed = False

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

        # Configure xrdp.ini - Extended default config with best practices
        xrdp_ini_content = f"""# xrdp.ini - Default Configuration + Best Practices
# Generated by debian-vps-workstation configurator
# Based on default xrdp.ini with performance optimizations

[Globals]
; xrdp.ini file version number
ini_version=1

; fork a new process for each incoming connection
fork=true

; ports to listen on, number alone means listen on all interfaces
; 0.0.0.0 or :: if ipv6 is configured
port=3389

; 'port' above should be connected to with vsock instead of tcp
use_vsock=false

; regulate if the listening socket use socket option tcp_nodelay
; no buffering will be performed in the TCP stack
tcp_nodelay={str(tcp_nodelay).lower()}

; regulate if the listening socket use socket option keepalive
; if the network connection disappear without close messages the connection will be closed
tcp_keepalive=true

; set tcp send/recv buffer (BEST PRACTICE: Enabled for better performance)
tcp_send_buffer_bytes=32768
tcp_recv_buffer_bytes=65536

; security layer can be 'tls', 'rdp' or 'negotiate'
security_layer={security_layer}

; minimum security level allowed for client for classic RDP encryption
crypt_level=high

; X.509 certificate and private key
certificate=
key_file=

; set SSL protocols
ssl_protocols=TLSv1.2, TLSv1.3

; Section name to use for automatic login
autorun=

; Performance settings (BEST PRACTICE)
allow_channels=true
allow_multimon=true
bitmap_cache={str(enable_bitmap_cache).lower()}
bitmap_compression=true
bulk_compression=true
max_bpp={max_bpp}
new_cursors=true
use_fastpath=both

; Login screen colors
grey=e1e1e1
dark_grey=b4b4b4
blue=0078d7
dark_blue=0078d7

; Login screen configuration
ls_top_window_bg_color=003057
ls_width=350
ls_height=360
ls_bg_color=f0f0f0
ls_logo_filename=
ls_logo_transform=scale
ls_logo_width=250
ls_logo_height=110
ls_logo_x_pos=55
ls_logo_y_pos=35
ls_label_x_pos=30
ls_label_width=68
ls_input_x_pos=110
ls_input_width=210
ls_input_y_pos=158
ls_btn_ok_x_pos=142
ls_btn_ok_y_pos=308
ls_btn_ok_width=85
ls_btn_ok_height=30
ls_btn_cancel_x_pos=237
ls_btn_cancel_y_pos=308
ls_btn_cancel_width=85
ls_btn_cancel_height=30

[Logging]
LogFile=xrdp.log
LogLevel=INFO
EnableSyslog=true

[Channels]
; Channel settings
rdpdr=true
rdpsnd=true
drdynvc=true
cliprdr=true
rail=true
xrdpvr=true

; Session types - Pure Xorg backend (NO VNC)
[Xorg]
name=Xorg
lib=libxup.so
username=ask
password=ask
port=-1
code=20

; VNC session (optional)
[Xvnc]
name=Xvnc
lib=libvnc.so
username=ask
password=ask
ip=127.0.0.1
port=-1

; Generic VNC Proxy
[vnc-any]
name=vnc-any
lib=libvnc.so
ip=ask
port=ask5900
username=na
password=ask

; Generic RDP proxy
[neutrinordp-any]
name=neutrinordp-any
lib=libxrdpneutrinordp.so
ip=ask
port=ask3389
username=ask
password=ask
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

        # Configure sesman.ini - Default + Best Practices
        sesman_ini_content = """# sesman.ini - Default Configuration + Best Practices
# Generated by debian-vps-workstation configurator

[Globals]
; listening port
EnableUserWindowManager=true
UserWindowManager=startwm.sh
DefaultWindowManager=startwm.sh
ReconnectScript=reconnectwm.sh

[Security]
AllowRootLogin=false
MaxLoginRetry=4
TerminalServerUsers=tsusers
TerminalServerAdmins=tsadmins
AlwaysGroupCheck=false
RestrictOutboundClipboard=none
RestrictInboundClipboard=none

[Sessions]
X11DisplayOffset=10
MaxSessions=10
KillDisconnected=false
DisconnectedTimeLimit=0
IdleTimeLimit=0
Policy=Default

[Logging]
LogFile=xrdp-sesman.log
LogLevel=INFO
EnableSyslog=true

; Xorg backend - Pure XRDP (Primary)
[Xorg]
param=/usr/lib/xorg/Xorg
param=-config
param=xrdp/xorg.conf
param=-noreset
param=-nolisten
param=tcp
param=-logfile
param=.xorgxrdp.%s.log

; Xvnc backend (Optional fallback)
[Xvnc]
param=Xvnc
param=-bs
param=-ac
param=-nolisten
param=tcp
param=-localhost
param=-dpi
param=96

[Chansrv]
FuseMountName=thinclient_drives
FileUmask=077

[ChansrvLogging]
LogLevel=INFO
EnableSyslog=true

[SessionVariables]
PULSE_SCRIPT=/etc/xrdp/pulse/default.pa
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

    def _configure_xwrapper(self):
        """Configure Xwrapper to allow non-console users to start X server (required for xrdp)."""
        self.logger.info("Configuring Xwrapper for xrdp...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_file_write("/etc/X11/Xwrapper.config")
            self.logger.info("[DRY RUN] Would configure Xwrapper to allow anybody to start X")
            return

        xwrapper_content = """# Xwrapper.config - Allow xrdp users to start X server
# Generated by debian-vps-workstation configurator
# Required for xrdp/xorgxrdp to work properly

allowed_users=anybody
needs_root_rights=yes
"""

        try:
            write_file("/etc/X11/Xwrapper.config", xwrapper_content, backup=True)
            self.logger.info("✓ Xwrapper configured to allow non-console users")
        except Exception as e:
            raise ModuleExecutionError(
                what="Failed to write Xwrapper.config",
                why=str(e),
                how="Check /etc/X11/ permissions and disk space",
            )

            self.logger.warning("XRDP configuration updated but manual restart required")

    def _configure_user_session(self):
        """Configure user session startup script for XRDP."""
        self.logger.info("Configuring user session startup...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command("configure .xsession for all users")
            self.logger.info(
                f"[DRY RUN] Would create .xsession files for users with UID >= {self.MIN_USER_UID}"
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
            self.logger.warning("No regular users found; .xsession configuration bypassed.")
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

                # Fix: Check for path traversal in home directory
                if ".." in user_home.split(os.sep):
                    self.logger.warning(
                        f"Skipping user {user}: home directory contains path traversal"
                    )
                    continue

                if not os.path.isdir(user_home):
                    self.logger.warning(f"Skipping user {user}: home directory doesn't exist")
                    continue

                xsession_path = os.path.join(user_home, ".xsession")

                xsession_content = """#!/bin/bash
# .xsession - XFCE Optimized for Remote Desktop
# Generated by debian-vps-workstation configurator
# Combines best practices from multiple sources

# === Environment Cleanup (Disable problematic services) ===
export NO_AT_BRIDGE=1           # Disable accessibility bridge
export GNOME_KEYRING_CONTROL="" # Disable keyring daemon
export GTK_MODULES=""           # Disable GTK modules that may cause issues

# === Session Variables (Explicit XFCE session) ===
export XDG_SESSION_DESKTOP=xfce
export XDG_CURRENT_DESKTOP=XFCE
export DESKTOP_SESSION=xfce
export DISPLAY=:10

# === XFCE Performance Settings ===
export XFCE_PANEL_DISABLE_BACKGROUND=1
export XFCE_PANEL_NO_COMPOSITING=1

# === Cursor Configuration (Fix cursor rendering) ===
export XCURSOR_THEME=Adwaita
export XCURSOR_SIZE=24

# === D-Bus Session Setup ===
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi

# === Disable Compositor (Critical for remote desktop performance) ===
xfconf-query -c xfwm4 -p /general/use_compositing -s false 2>/dev/null

# === Disable Screensaver & Power Management ===
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
            self.logger.info("No regular users found; compositor configuration bypassed.")
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

                write_file(colord_rule_path, colord_rule_content, backup=False)
                self.run(f"chmod 644 {colord_rule_path}", check=False)

                rules_installed.append("colord")
                self.logger.info("✓ Installed Polkit rule: colord")

                # Register rollback
                if self.rollback_manager:
                    self.rollback_manager.add_command(
                        f"rm -f {colord_rule_path}",
                        description="Remove colord Polkit rule",
                    )

            except Exception:
                self.logger.info("Unable to install colord rule (non-critical).")

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

                write_file(packagekit_rule_path, packagekit_rule_content, backup=False)
                self.run(f"chmod 644 {packagekit_rule_path}", check=False)

                rules_installed.append("packagekit")
                self.logger.info("✓ Installed Polkit rule: packagekit")

                # Register rollback
                if self.rollback_manager:
                    self.rollback_manager.add_command(
                        f"rm -f {packagekit_rule_path}",
                        description="Remove packagekit Polkit rule",
                    )

            except Exception:
                self.logger.info("Unable to install packagekit rule (non-critical).")

        # Restart polkit service to apply rules
        if rules_installed:
            try:
                self.run("systemctl restart polkit", check=False)
                self.logger.info(f"✓ Polkit rules configured: {', '.join(rules_installed)}")
            except Exception as e:
                self.logger.warning(f"Failed to restart polkit service: {e}")

        return len(rules_installed) > 0

    # === PHASE 3: Theme & Visual Customization ===

    def _install_themes(self):
        """
        Install GTK themes for XFCE desktop.

        Installs themes from both APT repositories and Git sources.
        Supports multiple theme options configurable via config.

        Themes installed:
        - Nordic (Git) - Dark theme optimized for remote desktop
        - WhiteSur (Git) - macOS Big Sur inspired theme
        - Arc (APT) - Lightweight modern theme
        - Dracula (Git) - High contrast vibrant theme
        """
        self.logger.info("Installing desktop themes...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                themes = self.get_config("desktop.themes.install", ["nordic"])
                self.dry_run_manager.record_command(f"Install themes: {', '.join(themes)}")
            self.logger.info("[DRY-RUN] Would install desktop themes")
            return

        # Get theme configuration
        themes_config = self.get_config("desktop.themes", {})

        # Install base theme dependencies
        self.logger.info("Installing theme dependencies...")
        theme_deps = [
            "gtk2-engines-murrine",  # Required for many themes
            "gtk2-engines-pixbuf",  # Icon rendering
            "sassc",  # SASS compiler for theme building
            "git",  # For cloning theme repos
        ]
        self.install_packages(theme_deps)

        # Install themes based on configuration
        themes_to_install = themes_config.get("install", ["nordic", "arc"])

        for theme_name in themes_to_install:
            theme_name_lower = theme_name.lower()

            try:
                if theme_name_lower == "nordic":
                    self._install_nordic_theme()
                elif theme_name_lower == "whitesur":
                    self._install_whitesur_theme()
                elif theme_name_lower == "arc":
                    self._install_arc_theme()
                elif theme_name_lower == "dracula":
                    self._install_dracula_theme()
                else:
                    self.logger.warning(f"Unknown theme: {theme_name}")
            except Exception as e:
                self.logger.error(f"Failed to install theme '{theme_name}': {e}")
                # Continue with other themes
                continue

        self.logger.info("✓ Themes installed")

    def _install_nordic_theme(self):
        """Install Nordic theme from GitHub."""
        self.logger.info("Installing Nordic theme...")

        theme_repo = "https://github.com/EliverLara/Nordic.git"
        temp_dir = "/tmp/nordic-theme"
        install_dir = "/usr/share/themes/Nordic"

        # Check if already installed
        if os.path.exists(install_dir):
            self.logger.info("Nordic theme already installed, updating...")
            self.run(f"rm -rf {install_dir}", check=False)

        # Clone repository
        self.run(f"rm -rf {temp_dir}", check=False)
        self.run(f"git clone --depth=1 {theme_repo} {temp_dir}", check=True)

        # Install theme
        self.run(f"mv {temp_dir} {install_dir}", check=True)

        # Cleanup
        self.run(f"rm -rf {temp_dir}", check=False)

        # Register rollback
        if self.rollback_manager:
            self.rollback_manager.add_command(
                f"rm -rf {install_dir}", description="Remove Nordic theme"
            )

        self.logger.info("✓ Nordic theme installed")

    def _install_whitesur_theme(self):
        """Install WhiteSur GTK theme from GitHub."""
        self.logger.info("Installing WhiteSur theme...")

        theme_repo = "https://github.com/vinceliuice/WhiteSur-gtk-theme.git"
        temp_dir = "/tmp/whitesur-theme"

        # Clone repository
        self.run(f"rm -rf {temp_dir}", check=False)
        self.run(f"git clone --depth=1 {theme_repo} {temp_dir}", check=True)

        # Run installer script
        # Install to system directory (-d /usr/share/themes)
        # Install all variants (-t all)
        install_cmd = f"cd {temp_dir} && ./install.sh -d /usr/share/themes -t all"

        result = self.run(install_cmd, check=False, shell=True)

        if not result.success:
            self.logger.warning("WhiteSur installation script failed, attempting manual install")
            # Fallback: just copy theme files
            self.run("mkdir -p /usr/share/themes/WhiteSur-Dark", check=True)
            self.run(
                f"cp -r {temp_dir}/src/* /usr/share/themes/WhiteSur-Dark/",
                check=False,
            )

        # Cleanup
        self.run(f"rm -rf {temp_dir}", check=False)

        # Register rollback
        if self.rollback_manager:
            self.rollback_manager.add_command(
                "rm -rf /usr/share/themes/WhiteSur*",
                description="Remove WhiteSur theme",
            )

        self.logger.info("✓ WhiteSur theme installed")

    def _install_arc_theme(self):
        """Install Arc theme from APT repository."""
        self.logger.info("Installing Arc theme...")

        # Arc is available in Debian repos
        self.install_packages(["arc-theme"])

        self.logger.info("✓ Arc theme installed")

    def _install_dracula_theme(self):
        """Install Dracula theme from GitHub."""
        self.logger.info("Installing Dracula theme...")

        theme_repo = "https://github.com/dracula/gtk.git"
        temp_dir = "/tmp/dracula-theme"
        install_dir = "/usr/share/themes/Dracula"

        # Clone repository
        self.run(f"rm -rf {temp_dir}", check=False)
        self.run(f"git clone --depth=1 {theme_repo} {temp_dir}", check=True)

        # Install theme
        self.run("mkdir -p /usr/share/themes", check=True)
        self.run(f"mv {temp_dir} {install_dir}", check=True)

        # Cleanup
        self.run(f"rm -rf {temp_dir}", check=False)

        # Register rollback
        if self.rollback_manager:
            self.rollback_manager.add_command(
                f"rm -rf {install_dir}", description="Remove Dracula theme"
            )

        self.logger.info("✓ Dracula theme installed")

    def _install_icon_packs(self):
        """
        Install icon packs for XFCE desktop.

        Icon packs installed:
        - Papirus (APT) - Modern, colorful, comprehensive
        - Tela (Git) - Rounded, modern design
        - Numix Circle (APT) - Flat, minimalist
        """
        self.logger.info("Installing icon packs...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                icons = self.get_config("desktop.icons.install", ["papirus"])
                self.dry_run_manager.record_command(f"Install icon packs: {', '.join(icons)}")
            self.logger.info("[DRY-RUN] Would install icon packs")
            return

        # Get icon pack configuration
        icons_config = self.get_config("desktop.icons", {})
        icons_to_install = icons_config.get("install", ["papirus"])

        for icon_name in icons_to_install:
            icon_name_lower = icon_name.lower()

            try:
                if icon_name_lower == "papirus":
                    self._install_papirus_icons()
                elif icon_name_lower == "tela":
                    self._install_tela_icons()
                elif icon_name_lower == "numix":
                    self._install_numix_icons()
                else:
                    self.logger.warning(f"Unknown icon pack: {icon_name}")
            except Exception as e:
                self.logger.error(f"Failed to install icon pack '{icon_name}': {e}")
                continue

        self.logger.info("✓ Icon packs installed")

    def _install_papirus_icons(self):
        """Install Papirus icon theme from APT."""
        self.logger.info("Installing Papirus icons...")

        # Papirus is available in Debian repos
        self.install_packages(["papirus-icon-theme"])

        self.logger.info("✓ Papirus icons installed")

    def _install_tela_icons(self):
        """Install Tela icon theme from GitHub."""
        self.logger.info("Installing Tela icons...")

        icon_repo = "https://github.com/vinceliuice/Tela-icon-theme.git"
        temp_dir = "/tmp/tela-icons"

        # Clone repository
        self.run(f"rm -rf {temp_dir}", check=False)
        self.run(f"git clone --depth=1 {icon_repo} {temp_dir}", check=True)

        # Run installer script (installs all variants)
        install_cmd = f"cd {temp_dir} && ./install.sh -a"
        self.run(install_cmd, check=True, shell=True)

        # Cleanup
        self.run(f"rm -rf {temp_dir}", check=False)

        # Register rollback
        if self.rollback_manager:
            self.rollback_manager.add_command(
                "rm -rf /usr/share/icons/Tela*", description="Remove Tela icons"
            )

        self.logger.info("✓ Tela icons installed")

    def _install_numix_icons(self):
        """Install Numix Circle icon theme from APT."""
        self.logger.info("Installing Numix icons...")

        # Numix Circle available in repos
        self.install_packages(["numix-icon-theme-circle"])

        self.logger.info("✓ Numix icons installed")

    def _configure_fonts(self):
        """
        Configure font rendering optimized for remote desktop.

        Key optimizations:
        - Disable subpixel rendering (RGBA=none) - critical for RDP
        - Enable hinting with hintslight
        - Install modern font families
        - Configure fontconfig for all users
        """
        self.logger.info("Configuring fonts for remote desktop...")
        print("!!! DEBUG: I AM THE CORRECT FILE v2 !!!")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command("Configure fonts for remote desktop")
            self.logger.info("[DRY-RUN] Would configure fonts")
            return

        # Install font packages
        self.logger.info("Installing font packages...")
        font_packages = [
            "fonts-firacode",  # Monospace with ligatures
            "fonts-noto",  # Google Noto (comprehensive)
            "fonts-noto-color-emoji",  # Emoji support
            "fonts-roboto",  # Modern sans-serif
            # Note: ttf-mscorefonts-installer not available in Debian 13
            # Using fonts-liberation as drop-in replacement for core fonts
            "fonts-liberation",  # Drop-in replacements for Arial, Times, etc.
            "fonts-dejavu",  # Additional comprehensive fonts
        ]

        try:
            self.install_packages(font_packages)
        except Exception as e:
            self.logger.warning(f"Font package installation encountered issue: {e}")
            self.logger.info("Continuing with desktop installation (fonts are non-critical)")

        # Configure fontconfig for all users
        self._configure_fontconfig_system()

        # Rebuild font cache
        self.logger.info("Rebuilding font cache...")
        self.run("fc-cache -fv", check=False)

        self.logger.info("✓ Fonts configured")

    def _configure_fontconfig_system(self):
        """Create system-wide fontconfig configuration."""
        fontconfig_content = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Font rendering optimized for remote desktop -->
  <match target="font">
    <!-- Enable antialiasing -->
    <edit mode="assign" name="antialias">
      <bool>true</bool>
    </edit>

    <!-- Enable hinting -->
    <edit mode="assign" name="hinting">
      <bool>true</bool>
    </edit>

    <!-- Use slight hinting (better for remote) -->
    <edit mode="assign" name="hintstyle">
      <const>hintslight</const>
    </edit>

    <!-- CRITICAL: Disable subpixel rendering for RDP -->
    <!-- Subpixel rendering causes blurry text over remote connections -->
    <edit mode="assign" name="rgba">
      <const>none</const>
    </edit>

    <!-- LCD filter (only applies if RGBA enabled, but set for completeness) -->
    <edit mode="assign" name="lcdfilter">
      <const>lcddefault</const>
    </edit>
  </match>

  <!-- Font preferences -->
  <alias>
    <family>sans-serif</family>
    <prefer>
      <family>Roboto</family>
      <family>Noto Sans</family>
      <family>DejaVu Sans</family>
    </prefer>
  </alias>

  <alias>
    <family>serif</family>
    <prefer>
      <family>Noto Serif</family>
      <family>DejaVu Serif</family>
    </prefer>
  </alias>

  <alias>
    <family>monospace</family>
    <prefer>
      <family>Fira Code</family>
      <family>Noto Sans Mono</family>
      <family>DejaVu Sans Mono</family>
    </prefer>
  </alias>
</fontconfig>
"""

        fontconfig_path = "/etc/fonts/local.conf"

        # Backup if exists
        if os.path.exists(fontconfig_path):
            backup_file(fontconfig_path)

        write_file(fontconfig_path, fontconfig_content)

        # Register rollback
        if self.rollback_manager:
            self.rollback_manager.add_command(
                f"rm -f {fontconfig_path}", description="Remove fontconfig customization"
            )

    def _configure_panel_layout(self):
        """
        Configure XFCE panel layout and install Plank dock.

        Creates macOS-like layout:
        - Top panel: menu, window buttons, system tray
        - Bottom dock: Plank application launcher
        """
        self.logger.info("Configuring panel layout...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                layout = self.get_config("desktop.panel.layout", "macos")
                self.dry_run_manager.record_command(f"Configure panel layout: {layout}")
            self.logger.info("[DRY-RUN] Would configure panel layout")
            return

        # Install Plank dock
        self.logger.info("Installing Plank dock...")
        self.install_packages(["plank"])

        # Setup Plank autostart
        self._setup_plank_autostart()

        self.logger.info("✓ Panel layout configured")

    def _setup_plank_autostart(self):
        """Configure Plank to auto-start for all users."""
        users = [
            u.pw_name
            for u in pwd.getpwall()
            if u.pw_uid >= self.MIN_USER_UID and u.pw_uid < self.MAX_USER_UID
        ]

        plank_desktop_content = """[Desktop Entry]
Type=Application
Exec=plank
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Plank
Comment=Dock
"""

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_home = pwd.getpwnam(user).pw_dir
                autostart_dir = os.path.join(user_home, ".config", "autostart")
                plank_desktop_path = os.path.join(autostart_dir, "plank.desktop")

                # Create autostart directory
                safe_user = shlex.quote(user)
                safe_dir = shlex.quote(autostart_dir)
                self.run(f"sudo -u {safe_user} mkdir -p {safe_dir}", check=False)

                # Write autostart file
                safe_path = shlex.quote(plank_desktop_path)
                self.run(
                    f"sudo -u {safe_user} tee {safe_path} > /dev/null",
                    input=plank_desktop_content.encode(),
                    check=True,
                )

                self.logger.info(f"✓ Plank autostart configured for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to configure Plank for user {user}: {e}")
                continue

    def _apply_theme_and_icons(self):
        """
        Apply selected theme and icon pack to XFCE.

        Applies configuration for all users.
        """
        self.logger.info("Applying theme and icon settings...")

        # Handle dry-run mode
        if self.dry_run:
            if self.dry_run_manager:
                theme = self.get_config("desktop.themes.active", "Nordic-darker")
                icons = self.get_config("desktop.icons.active", "Papirus-Dark")
                self.dry_run_manager.record_command(f"Apply theme: {theme}, icons: {icons}")
            self.logger.info("[DRY-RUN] Would apply theme and icons")
            return

        # Get theme configuration
        theme_name = self.get_config("desktop.themes.active", "Nordic-darker")
        icon_name = self.get_config("desktop.icons.active", "Papirus-Dark")

        users = [
            u.pw_name
            for u in pwd.getpwall()
            if u.pw_uid >= self.MIN_USER_UID and u.pw_uid < self.MAX_USER_UID
        ]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                safe_user = shlex.quote(user)

                # Apply GTK theme
                self.run(
                    f"sudo -u {safe_user} xfconf-query -c xsettings "
                    f"-p /Net/ThemeName -s '{theme_name}'",
                    check=False,
                )

                # Apply icon theme
                self.run(
                    f"sudo -u {safe_user} xfconf-query -c xsettings "
                    f"-p /Net/IconThemeName -s '{icon_name}'",
                    check=False,
                )

                # Apply window manager theme
                self.run(
                    f"sudo -u {safe_user} xfconf-query -c xfwm4 "
                    f"-p /general/theme -s '{theme_name}'",
                    check=False,
                )

                self.logger.info(f"✓ Theme applied for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to apply theme for user {user}: {e}")
                continue

        self.logger.info(f"✓ Theme: {theme_name}, Icons: {icon_name}")

    def _verify_themes_and_icons(self) -> bool:
        """Verify themes and icons are installed and applied."""
        checks_passed = True

        # Verify theme installation
        theme_name = self.get_config("desktop.themes.active", "Nordic-darker")
        theme_path = f"/usr/share/themes/{theme_name}"

        if os.path.exists(theme_path):
            self.logger.info(f"✓ Theme installed: {theme_name}")
        else:
            self.logger.warning(f"Theme not found: {theme_name} at {theme_path}")
            checks_passed = False

        # Verify icon pack installation
        icon_name = self.get_config("desktop.icons.active", "Papirus-Dark")
        icon_path = f"/usr/share/icons/{icon_name}"

        if os.path.exists(icon_path):
            self.logger.info(f"✓ Icon pack installed: {icon_name}")
        else:
            self.logger.warning(f"Icon pack not found: {icon_name}")
            checks_passed = False

        # Verify Plank installation
        if self.command_exists("plank"):
            self.logger.info("✓ Plank dock installed")
        else:
            self.logger.warning("Plank dock not found")

        # Verify fonts
        font_families = ["Roboto", "Fira Code", "Noto Sans"]
        result = self.run("fc-list : family", check=False, force_execute=True)

        if result.success:
            installed_fonts = result.stdout
            for font in font_families:
                if font in installed_fonts:
                    self.logger.info(f"✓ Font installed: {font}")
                else:
                    self.logger.warning(f"Font not found: {font}")

        return checks_passed

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

    # === Phase 4: Zsh Configuration Methods ===

    def _install_and_configure_zsh(self):
        """
        Install and configure Zsh shell with Oh My Zsh and Powerlevel10k.

        Complete terminal transformation:
        - Zsh shell installation
        - Oh My Zsh framework
        - Powerlevel10k theme
        - Essential plugins
        - Custom aliases and functions
        - Terminal emulator configuration

        Applied per-user for all regular users.
        """
        self.logger.info("Installing and configuring Zsh shell environment...")

        # Check if Zsh should be installed
        if not self.get_config("desktop.zsh.enabled", True):
            self.logger.info("Zsh installation disabled in config")
            return

        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_command("Install Zsh + Oh My Zsh + Powerlevel10k")
            self.logger.info("[DRY-RUN] Would install and configure Zsh")
            return

        # Install Zsh package
        self._install_zsh_package()

        # Install Oh My Zsh for all users
        self._install_oh_my_zsh()

        # Install Powerlevel10k theme
        self._install_powerlevel10k()

        # Install Meslo Nerd Font
        self._install_meslo_nerd_font()

        # Install essential plugins
        self._install_zsh_plugins()

        # Install productivity tools
        self._install_terminal_tools()

        # Configure .zshrc for all users
        self._configure_zshrc()

        # Configure Powerlevel10k
        self._configure_powerlevel10k()

        # Set Zsh as default shell
        self._set_zsh_as_default_shell()

        # Configure Terminal Emulator
        self._configure_terminal_emulator()

        self.logger.info("✓ Zsh environment configured")

    def _install_zsh_package(self):
        """Install Zsh package from APT."""
        self.logger.info("Installing Zsh package...")

        self.install_packages(["zsh"])

        # Verify installation
        if not self.command_exists("zsh"):
            raise ModuleExecutionError(
                what="Zsh installation failed",
                why="zsh command not found after apt install",
                how="Check APT logs: /var/log/apt/term.log",
            )

        # Get Zsh version
        result = self.run("zsh --version", check=False, force_execute=True)
        if result.success:
            self.logger.info(f"✓ Zsh installed: {result.stdout.strip()}")

        self.logger.info("✓ Zsh package installed")

    def _install_oh_my_zsh(self):
        """
        Install Oh My Zsh framework for all regular users.

        Oh My Zsh provides:
        - Plugin management system
        - Theme support
        - Aliases and functions
        - Auto-update mechanism
        """
        self.logger.info("Installing Oh My Zsh framework...")

        import pwd

        # Get regular users
        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        if not users:
            self.logger.warning("No regular users found for Oh My Zsh installation")
            return

        # Oh My Zsh installation script URL and Checksum (Pinned for security)
        ohmyzsh_install_url = (
            "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
        )
        expected_sha256 = "ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352"

        # Download and verify script once
        script_path = "/tmp/ohmyzsh_install.sh"
        try:
            self.logger.info("Downloading and verifying Oh My Zsh installer...")
            self.run(f"curl -fsSL {ohmyzsh_install_url} -o {script_path}", check=True)

            # Verify checksum
            result = self.run(f"sha256sum {script_path}", check=True)
            if expected_sha256 not in result.stdout:
                raise ModuleExecutionError(
                    what="Oh My Zsh installer checksum mismatch!",
                    why=f"Downloaded file checksum does not match expected value {expected_sha256}",
                    how="Check your network connection or report a potential security issue.",
                )

            self.logger.info("✓ Installer checksum verified")
            self.run(f"chmod 644 {script_path}")  # Ensure not executable by default, read-only

        except Exception as e:
            self.logger.error(f"Failed to prepare Oh My Zsh installer: {e}")
            self.run(f"rm -f {script_path}", check=False)
            return

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Check if already installed
                ohmyzsh_dir = os.path.join(user_home, ".oh-my-zsh")
                if os.path.exists(ohmyzsh_dir):
                    self.logger.info(f"Oh My Zsh already installed for user: {user}")
                    continue

                # Execute verified script
                # Use unattended mode to skip prompts
                # Copy script to user temp or read from /tmp
                install_cmd = f"sudo -u {shlex.quote(user)} sh {script_path} --unattended"

                result = self.run(install_cmd, check=False)

                if result.success:
                    self.logger.info(f"✓ Oh My Zsh installed for user: {user}")

                    # Register rollback
                    self.rollback_manager.add_command(
                        f"rm -rf {shlex.quote(ohmyzsh_dir)}",
                        description=f"Remove Oh My Zsh for {user}",
                    )
                else:
                    self.logger.error(
                        f"Failed to install Oh My Zsh for user {user}: {result.stderr}"
                    )

            except Exception as e:
                self.logger.error(f"Failed to install Oh My Zsh for user {user}: {e}")
                continue

        # Cleanup
        self.run(f"rm -f {script_path}", check=False)
        self.logger.info("✓ Oh My Zsh framework installed")

    def _install_powerlevel10k(self):
        """
        Install Powerlevel10k theme for Oh My Zsh.

        Powerlevel10k features:
        - Ultra-fast prompt rendering
        - Instant prompt (terminal ready in <1ms)
        - Rich information display
        - Configuration wizard
        """
        self.logger.info("Installing Powerlevel10k theme...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        p10k_repo = "https://github.com/romkatv/powerlevel10k.git"

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Powerlevel10k installation directory
                ohmyzsh_custom = os.path.join(
                    user_home, ".oh-my-zsh", "custom", "themes", "powerlevel10k"
                )

                # Check if already installed
                if os.path.exists(ohmyzsh_custom):
                    self.logger.info(f"Powerlevel10k already installed for user: {user}")
                    continue

                # Clone Powerlevel10k repository
                clone_cmd = (
                    f"sudo -u {shlex.quote(user)} "
                    f"git clone --depth=1 {p10k_repo} {shlex.quote(ohmyzsh_custom)}"
                )

                result = self.run(clone_cmd, check=False)

                if result.success:
                    self.logger.info(f"✓ Powerlevel10k installed for user: {user}")

                    # Register rollback
                    self.rollback_manager.add_command(
                        f"rm -rf {shlex.quote(ohmyzsh_custom)}",
                        description=f"Remove Powerlevel10k for {user}",
                    )
                else:
                    self.logger.error(f"Failed to install Powerlevel10k for user {user}")

            except Exception as e:
                self.logger.error(f"Failed to install Powerlevel10k for user {user}: {e}")
                continue

        self.logger.info("✓ Powerlevel10k theme installed")

    def _install_meslo_nerd_font(self):
        """
        Install Meslo Nerd Font required for Powerlevel10k icons.

        MesloLGS NF is the recommended font for Powerlevel10k.
        Includes all necessary glyphs and icons.
        """
        self.logger.info("Installing Meslo Nerd Font...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        # Font URLs (from Powerlevel10k repo)
        font_base_url = "https://github.com/romkatv/powerlevel10k-media/raw/master"
        fonts = [
            "MesloLGS%20NF%20Regular.ttf",
            "MesloLGS%20NF%20Bold.ttf",
            "MesloLGS%20NF%20Italic.ttf",
            "MesloLGS%20NF%20Bold%20Italic.ttf",
        ]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Font directory
                font_dir = os.path.join(user_home, ".local", "share", "fonts")

                # Create font directory
                self.run(f"sudo -u {shlex.quote(user)} mkdir -p {shlex.quote(font_dir)}")

                # Download fonts
                for font in fonts:
                    font_url = f"{font_base_url}/{font}"
                    font_file = font.replace("%20", " ")
                    font_path = os.path.join(font_dir, font_file)

                    # Download if not exists
                    if not os.path.exists(font_path):
                        download_cmd = (
                            f"sudo -u {shlex.quote(user)} "
                            f"wget -q -O {shlex.quote(font_path)} {font_url}"
                        )

                        self.run(download_cmd, check=False)

                # Rebuild font cache
                self.run(f"sudo -u {shlex.quote(user)} fc-cache -fv", check=False)

                self.logger.info(f"✓ Meslo Nerd Font installed for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to install font for user {user}: {e}")
                continue

        self.logger.info("✓ Meslo Nerd Font installed")

    def _install_zsh_plugins(self):
        """
        Install essential Zsh plugins for productivity.

        Plugins installed:
        - zsh-autosuggestions: Fish-like autosuggestions
        - zsh-syntax-highlighting: Real-time syntax validation
        """
        self.logger.info("Installing Zsh plugins...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        plugins = {
            "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions.git",
            "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting.git",
        }

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                plugins_dir = os.path.join(user_home, ".oh-my-zsh", "custom", "plugins")

                for plugin_name, plugin_repo in plugins.items():
                    plugin_path = os.path.join(plugins_dir, plugin_name)

                    # Check if already installed
                    if os.path.exists(plugin_path):
                        self.logger.info(f"{plugin_name} already installed for user: {user}")
                        continue

                    # Clone plugin repository
                    clone_cmd = (
                        f"sudo -u {shlex.quote(user)} "
                        f"git clone --depth=1 {plugin_repo} {shlex.quote(plugin_path)}"
                    )

                    result = self.run(clone_cmd, check=False)

                    if result.success:
                        self.logger.info(f"✓ {plugin_name} installed for user: {user}")
                    else:
                        self.logger.error(f"Failed to install {plugin_name} for user {user}")

            except Exception as e:
                self.logger.error(f"Failed to install plugins for user {user}: {e}")
                continue

        self.logger.info("✓ Zsh plugins installed")

    def _install_terminal_tools(self):
        """
        Install modern terminal productivity tools.

        Tools installed:
        - fzf: Fuzzy finder for history, files, directories
        - bat: Better 'cat' with syntax highlighting
        - eza: Better 'ls' with colors and icons
        - zoxide: Smarter 'cd' that learns your habits
        """
        self.logger.info("Installing terminal productivity tools...")

        # Get tool configuration
        tools_config = self.get_config("desktop.zsh.tools", {})

        # Install from APT
        apt_tools = []

        if tools_config.get("fzf", True):
            apt_tools.append("fzf")

        if tools_config.get("bat", True):
            apt_tools.append("bat")

        if tools_config.get("eza", True):
            apt_tools.append("eza")

        if tools_config.get("zoxide", True):
            apt_tools.append("zoxide")

        if apt_tools:
            self.install_packages(apt_tools)
            self.logger.info(f"✓ Terminal tools installed: {', '.join(apt_tools)}")

        self.logger.info("✓ Terminal productivity tools configured")

    def _configure_zshrc(self):
        """
        Configure .zshrc file for all users with optimized settings.

        Configuration includes:
        - Oh My Zsh initialization
        - Powerlevel10k theme
        - Plugin loading
        - Custom aliases
        - History settings
        - Environment variables
        """
        self.logger.info("Configuring .zshrc files...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                zshrc_path = os.path.join(user_home, ".zshrc")

                # Generate .zshrc content
                zshrc_content = self._generate_zshrc_content()

                # Backup existing .zshrc
                if os.path.exists(zshrc_path):
                    backup_file(zshrc_path)

                # Write .zshrc
                self.run(
                    f"sudo -u {shlex.quote(user)} tee {shlex.quote(zshrc_path)} > /dev/null",
                    input=zshrc_content.encode(),
                    check=True,
                )

                self.logger.info(f"✓ .zshrc configured for user: {user}")

                # Register rollback
                self.rollback_manager.add_command(
                    f"rm -f {shlex.quote(zshrc_path)}", description=f"Remove .zshrc for {user}"
                )

            except Exception as e:
                self.logger.error(f"Failed to configure .zshrc for user {user}: {e}")
                continue

        self.logger.info("✓ .zshrc files configured")

    def _generate_zshrc_content(self) -> str:
        """
        Generate .zshrc configuration content.

        Returns:
            Complete .zshrc file content as string
        """
        # Get plugin configuration
        plugins_list = self.get_config(
            "desktop.zsh.plugins",
            [
                "git",
                "docker",
                "docker-compose",
                "kubectl",
                "sudo",
                "command-not-found",
                "colored-man-pages",
                "zsh-autosuggestions",
                "zsh-syntax-highlighting",
            ],
        )

        # Ensure zsh-syntax-highlighting is LAST
        if "zsh-syntax-highlighting" in plugins_list:
            plugins_list.remove("zsh-syntax-highlighting")
            plugins_list.append("zsh-syntax-highlighting")

        plugins_str = "\\n    ".join(plugins_list)

        zshrc_content = f"""# Zsh Configuration
# Generated by debian-vps-workstation configurator

# Path to Oh My Zsh installation
export ZSH="$HOME/.oh-my-zsh"

# === Powerlevel10k Instant Prompt ===
# Enable instant prompt (ultra-fast terminal startup)
if [[ -r "${{XDG_CACHE_HOME:-$HOME/.cache}}/p10k-instant-prompt-${{(%):-%n}}.zsh" ]]; then
  source "${{XDG_CACHE_HOME:-$HOME/.cache}}/p10k-instant-prompt-${{(%):-%n}}.zsh"
fi

# === Theme Configuration ===
ZSH_THEME="powerlevel10k/powerlevel10k"

# === Plugin Configuration ===
plugins=(
    {plugins_str}
)

# Source Oh My Zsh
source $ZSH/oh-my-zsh.sh

# === User Configuration ===

# Editor
export EDITOR='vim'
export VISUAL='vim'

# Terminal
export TERM=xterm-256color

# === History Configuration ===
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_ALL_DUPS  # Don't record duplicates
setopt HIST_FIND_NO_DUPS     # Don't show duplicates in search
setopt SHARE_HISTORY         # Share history across all sessions
setopt HIST_REDUCE_BLANKS    # Remove extra blanks
setopt INC_APPEND_HISTORY    # Add commands immediately

# === Aliases ===

# Modern tool replacements
alias cat='batcat --paging=never 2>/dev/null || cat'
alias ls='eza --icons 2>/dev/null || ls --color=auto'
alias ll='eza -lah --icons 2>/dev/null || ls -lah'
alias tree='eza --tree --icons 2>/dev/null || tree'

# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'

# System info
alias df='df -h'
alias du='du -h'
alias free='free -h'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gd='git diff'
alias gp='git push'
alias gl='git log --oneline --graph --decorate --all'
alias gco='git checkout'
alias gb='git branch'

# Docker shortcuts
alias dps='docker ps'
alias dpa='docker ps -a'
alias di='docker images'
alias dex='docker exec -it'
alias dlog='docker logs -f'
alias dstop='docker stop $(docker ps -q)'
alias drm='docker rm $(docker ps -aq)'

# System management
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install'
alias search='apt search'

# Network
alias myip='curl -s ifconfig.me'
alias ports='netstat -tulanp'
alias listening='ss -tulnp'

# Process management
alias psg='ps aux | grep -v grep | grep -i -e VSZ -e'
alias topcpu='ps aux --sort=-%cpu | head -11'
alias topmem='ps aux --sort=-%mem | head -11'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias ln='ln -i'

# Quick edits
alias zshconfig='vim ~/.zshrc'
alias ohmyzsh='vim ~/.oh-my-zsh'
alias reload='source ~/.zshrc'

# === FZF Configuration ===
if command -v fzf &> /dev/null; then
    export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --preview "bat --color=always --style=numbers --line-range=:500 {{}}"'

    # FZF key bindings (if available)
    if [ -f /usr/share/doc/fzf/examples/key-bindings.zsh ]; then
        source /usr/share/doc/fzf/examples/key-bindings.zsh
    fi

    # FZF completion (if available)
    if [ -f /usr/share/doc/fzf/examples/completion.zsh ]; then
        source /usr/share/doc/fzf/examples/completion.zsh
    fi
fi

# === Zoxide Configuration ===
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    alias cd='z'  # Replace cd with zoxide
fi

# === Autosuggestions Configuration ===
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=240,italic'
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=20

# === Colored Man Pages ===
export LESS_TERMCAP_mb=$'\\e[1;32m'
export LESS_TERMCAP_md=$'\\e[1;32m'
export LESS_TERMCAP_me=$'\\e[0m'
export LESS_TERMCAP_se=$'\\e[0m'
export LESS_TERMCAP_so=$'\\e[01;33m'
export LESS_TERMCAP_ue=$'\\e[0m'
export LESS_TERMCAP_us=$'\\e[1;4;31m'

# === Powerlevel10k Configuration ===
# To customize prompt, run: p10k configure
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
"""

        return zshrc_content

    def _configure_powerlevel10k(self):
        """
        Configure Powerlevel10k with optimized defaults.

        Creates .p10k.zsh configuration file with professional settings.
        Users can run 'p10k configure' to customize.
        """
        self.logger.info("Configuring Powerlevel10k defaults...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                p10k_config_path = os.path.join(user_home, ".p10k.zsh")

                # Skip if user already has custom configuration
                if os.path.exists(p10k_config_path):
                    self.logger.info(f"Powerlevel10k config exists for user: {user}, skipping")
                    continue

                # Generate default P10k config
                # Note: Full p10k config is ~3000 lines, we'll create a minimal starter
                p10k_content = self._generate_p10k_starter_config()

                # Write configuration
                self.run(
                    f"sudo -u {shlex.quote(user)} tee {shlex.quote(p10k_config_path)} > /dev/null",
                    input=p10k_content.encode(),
                    check=True,
                )

                self.logger.info(f"✓ Powerlevel10k configured for user: {user}")
                self.logger.info("  User can customize with: p10k configure")

            except Exception as e:
                self.logger.error(f"Failed to configure Powerlevel10k for user {user}: {e}")
                continue

        self.logger.info("✓ Powerlevel10k configured")

    def _generate_p10k_starter_config(self) -> str:
        """
        Generate minimal Powerlevel10k configuration.

        Users can run 'p10k configure' to generate full config.
        This is a reasonable default that works immediately.
        """
        return """# Powerlevel10k Starter Configuration
# Run 'p10k configure' to customize

# Temporarily change options
'builtin' 'local' '-a' 'p10k_config_opts'
[[ ! -o 'aliases'         ]] || p10k_config_opts+=('aliases')
[[ ! -o 'sh_glob'         ]] || p10k_config_opts+=('sh_glob')
[[ ! -o 'no_brace_expand' ]] || p10k_config_opts+=('no_brace_expand')
'builtin' 'setopt' 'no_aliases' 'no_sh_glob' 'brace_expand'

() {
  emulate -L zsh -o extended_glob

  # Prompt style: lean (minimal, fast)
  typeset -g POWERLEVEL9K_MODE=nerdfont-complete
  typeset -g POWERLEVEL9K_PROMPT_ON_NEWLINE=true
  typeset -g POWERLEVEL9K_RPROMPT_ON_NEWLINE=false
  typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always

  # Prompt segments
  typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(
    dir                     # current directory
    vcs                     # git status
    newline                 # \\n
    prompt_char             # prompt symbol
  )

  typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
    status                  # exit code of last command
    command_execution_time  # duration of last command
    background_jobs         # presence of background jobs
    time                    # current time
  )

  # Directory
  typeset -g POWERLEVEL9K_DIR_FOREGROUND=blue

  # Git
  typeset -g POWERLEVEL9K_VCS_FOREGROUND=green

  # Time
  typeset -g POWERLEVEL9K_TIME_FOREGROUND=gray
  typeset -g POWERLEVEL9K_TIME_FORMAT='%D{%H:%M}'

  # Instant prompt
  typeset -g POWERLEVEL9K_INSTANT_PROMPT=verbose

  (( ! $+functions[p10k] )) || p10k reload
}

# Restore options
(( ${#p10k_config_opts} )) && setopt ${p10k_config_opts[@]}
'builtin' 'unset' 'p10k_config_opts'
"""

    def _set_zsh_as_default_shell(self):
        """
        Set Zsh as the default shell for all regular users.

        Uses chsh to change default shell to /usr/bin/zsh.
        """
        self.logger.info("Setting Zsh as default shell...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        # Get Zsh path
        zsh_path = "/usr/bin/zsh"

        if not os.path.exists(zsh_path):
            self.logger.error("Zsh binary not found, cannot set as default shell")
            return

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                # Get current shell
                user_info = pwd.getpwnam(user)
                current_shell = user_info.pw_shell

                if current_shell == zsh_path:
                    self.logger.info(f"Zsh already default shell for user: {user}")
                    continue

                # Change shell
                chsh_cmd = f"chsh -s {zsh_path} {shlex.quote(user)}"
                result = self.run(chsh_cmd, check=False)

                if result.success:
                    self.logger.info(f"✓ Zsh set as default shell for user: {user}")

                    # Register rollback
                    self.rollback_manager.add_command(
                        f"chsh -s {current_shell} {shlex.quote(user)}",
                        description=f"Restore original shell for {user}",
                    )
                else:
                    self.logger.error(f"Failed to set Zsh as default for user {user}")

            except Exception as e:
                self.logger.error(f"Failed to change shell for user {user}: {e}")
                continue

        self.logger.info("✓ Zsh configured as default shell")
        self.logger.info("  Users need to logout/login for shell change to take effect")

    def _configure_terminal_emulator(self):
        """
        Configure XFCE Terminal for optimal Zsh experience.

        Configuration:
        - Font: MesloLGS NF (Nerd Font for icons)
        - Color scheme: Optimized for Powerlevel10k
        - Scrollback: Increased buffer
        """
        self.logger.info("Configuring XFCE Terminal for Zsh...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                # Configure terminal via xfconf-query
                terminal_settings = [
                    # Font configuration
                    ("/font-name", "MesloLGS NF 11"),
                    # Scrollback
                    ("/scrolling-unlimited", "false"),
                    ("/scrolling-lines", "10000"),
                    # Cursor
                    ("/cursor-shape", "TERMINAL_CURSOR_SHAPE_IBEAM"),
                    ("/cursor-blinks", "true"),
                    # Colors (use terminal theme)
                    ("/color-use-theme", "false"),
                ]

                for property_path, value in terminal_settings:
                    cmd = f"sudo -u {shlex.quote(user)} xfconf-query -c xfce4-terminal -p {property_path}"

                    # Determine type
                    if value in ["true", "false"]:
                        cmd += f" -t bool -s {value}"
                    elif value.isdigit():
                        cmd += f" -t int -s {value}"
                    else:
                        cmd += f" -s '{value}'"

                    self.run(cmd, check=False)

                self.logger.info(f"✓ Terminal configured for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to configure terminal for user {user}: {e}")
                continue

        self.logger.info("✓ XFCE Terminal configured")

    def _verify_zsh_installation(self) -> bool:
        """Verify Zsh installation and configuration."""
        checks_passed = True

        # Check Zsh installed
        if not self.command_exists("zsh"):
            self.logger.error("Zsh not installed!")
            checks_passed = False
        else:
            self.logger.info("✓ Zsh installed")

        # Check Oh My Zsh for users
        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            try:
                user_home = pwd.getpwnam(user).pw_dir
                ohmyzsh_dir = os.path.join(user_home, ".oh-my-zsh")

                if os.path.exists(ohmyzsh_dir):
                    self.logger.info(f"✓ Oh My Zsh installed for: {user}")
                else:
                    self.logger.warning(f"Oh My Zsh not found for: {user}")

            except Exception as e:
                self.logger.error(f"Failed to verify for user {user}: {e}")

        # Check terminal tools
        tools = ["fzf", "bat", "eza", "zoxide"]
        for tool in tools:
            if self.command_exists(tool):
                self.logger.info(f"✓ {tool} installed")
            else:
                self.logger.warning(f"{tool} not found")

        return checks_passed

    def _configure_advanced_terminal_tools(self):
        """
        Configure advanced settings for terminal productivity tools.

        Tools configured:
        - bat: Custom themes, paging, git integration
        - eza: Git status, icons, colors
        - zoxide: Interactive mode, frecency tuning
        - fzf:  Preview window, key bindings, colors
        """
        self.logger.info("Configuring advanced terminal tool settings...")

        # Configure bat
        self._configure_bat_advanced()

        # Configure eza
        self._configure_eza_advanced()

        # Configure zoxide
        self._configure_zoxide_advanced()

        # Configure fzf
        self._configure_fzf_advanced()

        # Create custom integration scripts
        self._create_tool_integration_scripts()

        # Update .zshrc with advanced configurations
        self._update_zshrc_for_advanced_tools()

        self.logger.info("✓ Advanced terminal tool configurations applied")

    def _configure_bat_advanced(self):
        """
        Configure bat (better cat) with advanced settings.

        Configuration:
        - Custom theme matching terminal
        - Git integration enabled
        - Smart paging
        - Line numbers
        - Custom syntax mappings
        """
        self.logger.info("Configuring bat (syntax highlighting cat)...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        # Get bat configuration from config
        bat_config = self.get_config("desktop.terminal_tools.bat", {})
        theme = bat_config.get("theme", "TwoDark")
        show_line_numbers = bat_config.get("line_numbers", True)
        git_integration = bat_config.get("git_integration", True)

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Create bat config directory
                bat_config_dir = os.path.join(user_home, ".config", "bat")
                self.run(f"sudo -u {shlex.quote(user)} mkdir -p {shlex.quote(bat_config_dir)}")

                # Generate bat config
                bat_config_content = self._generate_bat_config(
                    theme, show_line_numbers, git_integration
                )

                bat_config_path = os.path.join(bat_config_dir, "config")

                # Write config
                self.run(
                    f"sudo -u {shlex.quote(user)} tee {shlex.quote(bat_config_path)} > /dev/null",
                    input=bat_config_content.encode(),
                    check=True,
                )

                self.logger.info(f"✓ Bat configured for user: {user}")

                # Register rollback
                self.rollback_manager.add_command(
                    f"rm -rf {shlex.quote(bat_config_dir)}",
                    description=f"Remove bat config for {user}",
                )

            except Exception as e:
                self.logger.error(f"Failed to configure bat for user {user}: {e}")
                continue

        self.logger.info("✓ Bat configuration complete")

    def _generate_bat_config(self, theme: str, line_numbers: bool, git_integration: bool) -> str:
        """
        Generate bat configuration file content.

        Args:
            theme: Color theme name
            line_numbers: Enable line numbers
            git_integration:  Enable git diff indicators

        Returns:
            Bat config file content
        """
        config_lines = [
            "# Bat Configuration",
            "# Generated by debian-vps-workstation configurator",
            "",
            "# Theme (run 'bat --list-themes' to see all)",
            f'--theme="{theme}"',
            "",
        ]

        if line_numbers:
            config_lines.extend(
                [
                    "# Show line numbers",
                    '--style="numbers,changes,header"',
                    "",
                ]
            )
        else:
            config_lines.extend(
                [
                    "# Minimal style",
                    '--style="changes,header"',
                    "",
                ]
            )

        if git_integration:
            config_lines.extend(
                [
                    "# Git integration (show modifications)",
                    '--decorations="always"',
                    "",
                ]
            )

        config_lines.extend(
            [
                "# Use italic text (requires font support)",
                "--italic-text=always",
                "",
                "# Paging",
                "--paging=auto",
                "",
                "# Add custom syntax mappings",
                '--map-syntax="*.conf:INI"',
                '--map-syntax="*Dockerfile*:Dockerfile"',
                '--map-syntax=".env:Bash"',
                "",
                "# Tab width",
                "--tabs=4",
                "",
                "# Wrap long lines",
                "--wrap=auto",
            ]
        )

        return "\\n".join(config_lines)

    def _configure_eza_advanced(self):
        """
        Configure eza (better ls) with advanced settings.

        Configuration via environment variables and enhanced aliases:
        - Git integration (show status per file)
        - Icons (requires Nerd Font)
        - Extended attributes
        - Custom colors
        - Time style
        """
        self.logger.info("Configuring eza (modern ls replacement)...")

        # Eza is configured via environment variables in .zshrc
        # and enhanced aliases
        # This method sets up the configuration data structure
        # that will be used when updating .zshrc

        exa_config = self.get_config("desktop.terminal_tools.eza", {})

        self.exa_settings = {
            "git_integration": exa_config.get("git_integration", True),
            "icons": exa_config.get("icons", True),
            "extended_attributes": exa_config.get("extended_attributes", False),
            "time_style": exa_config.get("time_style", "long-iso"),
            "group_directories_first": exa_config.get("group_directories_first", True),
        }

        self.logger.info("✓ Eza configuration prepared")

    def _generate_exa_aliases(self) -> str:
        """
        Generate enhanced eza aliases based on configuration.

        Returns:
            Alias definitions for .zshrc
        """
        exa_settings = getattr(self, "exa_settings", {})

        # Base options
        base_opts = []

        if exa_settings.get("icons", True):
            base_opts.append("--icons")

        if exa_settings.get("git_integration", True):
            base_opts.append("--git")

        if exa_settings.get("group_directories_first", True):
            base_opts.append("--group-directories-first")

        time_style = exa_settings.get("time_style", "long-iso")
        base_opts.append(f"--time-style={time_style}")

        base_opts_str = " ".join(base_opts)

        aliases = f"""
# Eza (better ls) - Enhanced Aliases
if command -v eza &> /dev/null; then
    # Basic listing
    alias ls='eza {base_opts_str}'

    # Detailed listing
    alias ll='eza -lah {base_opts_str}'
    alias la='eza -a {base_opts_str}'
    alias l='eza -lh {base_opts_str}'

    # Tree view
    alias tree='eza --tree {base_opts_str}'
    alias tree2='eza --tree --level=2 {base_opts_str}'
    alias tree3='eza --tree --level=3 {base_opts_str}'

    # Sort options
    alias lS='eza -lah --sort=size {base_opts_str}'          # Sort by size
    alias lt='eza -lah --sort=modified {base_opts_str}'      # Sort by date
    alias lm='eza -lah --sort=modified {base_opts_str}'      # Sort by modified
    alias lc='eza -lah --sort=created {base_opts_str}'       # Sort by created

    # Git-specific
    alias lg='eza -lah --git --git-ignore {base_opts_str}'   # Show git status

    # Extended attributes (Linux-specific)
"""

        if exa_settings.get("extended_attributes", False):
            aliases += f"""    alias lx='eza -lah --extended {base_opts_str}'          # Show extended attrs
"""

        aliases += """else
    # Fallback to standard ls
    alias ll='ls -lah --color=auto'
    alias la='ls -A --color=auto'
    alias l='ls -lh --color=auto'
fi
"""

        return aliases

    def _configure_zoxide_advanced(self):
        """
        Configure zoxide (smart cd) with advanced settings.

        Configuration:
        - Interactive mode (zi command)
        - Frecency algorithm tuning
        - Exclude patterns
        - Custom scoring
        """
        self.logger.info("Configuring zoxide (smart directory jumper)...")

        zoxide_config = self.get_config("desktop.terminal_tools.zoxide", {})

        self.zoxide_settings = {
            "interactive_mode": zoxide_config.get("interactive_mode", True),
            "exclude_dirs": zoxide_config.get("exclude_dirs", ["/tmp", "/var/tmp"]),
            "max_results": zoxide_config.get("max_results", 10),
        }

        self.logger.info("✓ Zoxide configuration prepared")

    def _generate_zoxide_config(self) -> str:
        """
        Generate zoxide configuration for .zshrc.

        Returns:
            Zoxide configuration block
        """
        zoxide_settings = getattr(self, "zoxide_settings", {})

        config = """
# Zoxide (smart cd) - Advanced Configuration
if command -v zoxide &> /dev/null; then
    # Initialize zoxide
    eval "$(zoxide init zsh)"

    # Aliases
    alias cd='z'          # Replace cd with zoxide
"""

        if zoxide_settings.get("interactive_mode", True):
            config += """    alias zi='zi'         # Interactive mode (selection menu)
    alias cdi='zi'        # Alternative interactive alias
"""

        config += """
    # Utility functions

    # Show zoxide database
    alias zoxide-stats='zoxide query -l'
    alias zs='zoxide query -l'

    # Remove path from zoxide
    zoxide-remove() {
        if [ -z "$1" ]; then
            echo "Usage: zoxide-remove <path>"
            return 1
        fi
        zoxide remove "$1"
    }

    # Clean zoxide database (remove non-existent dirs)
    zoxide-clean() {
        echo "Cleaning zoxide database..."
        local removed=0
        while IFS= read -r dir; do
            if [ ! -d "$dir" ]; then
                zoxide remove "$dir" 2>/dev/null && ((removed++))
            fi
        done < <(zoxide query -l)
        echo "Removed $removed non-existent directories"
    }
"""

        # Exclude directories
        exclude_dirs = zoxide_settings.get("exclude_dirs", [])
        if exclude_dirs:
            config += f"""
    # Exclude directories from zoxide
    export _ZO_EXCLUDE_DIRS="{":".join(exclude_dirs)}"
"""

        config += """fi
"""

        return config

    def _configure_fzf_advanced(self):
        """
        Configure fzf (fuzzy finder) with advanced settings.

        Configuration:
        - Custom key bindings
        - Preview window with bat
        - Color scheme matching theme
        - Multi-select options
        - Integration with fd/ripgrep
        """
        self.logger.info("Configuring fzf (fuzzy finder)...")

        fzf_config = self.get_config("desktop.terminal_tools.fzf", {})

        self.fzf_settings = {
            "preview_enabled": fzf_config.get("preview", True),
            "height": fzf_config.get("height", "40%"),
            "layout": fzf_config.get("layout", "reverse"),
            "border": fzf_config.get("border", True),
            "color_scheme": fzf_config.get("color_scheme", "dark"),
        }

        self.logger.info("✓ FZF configuration prepared")

    def _generate_fzf_config(self) -> str:
        """
        Generate FZF configuration for .zshrc.

        Returns:
            FZF configuration block
        """
        fzf_settings = getattr(self, "fzf_settings", {})

        # Build FZF_DEFAULT_OPTS
        opts = []

        # Height and layout
        height = fzf_settings.get("height", "40%")
        layout = fzf_settings.get("layout", "reverse")
        opts.append(f"--height {height}")
        opts.append(f"--layout={layout}")

        # Border
        if fzf_settings.get("border", True):
            opts.append("--border")

        # Preview
        if fzf_settings.get("preview_enabled", True):
            preview_cmd = "bat --color=always --style=numbers --line-range=:500 {}"
            opts.append(f"--preview '{preview_cmd}'")

        # Color scheme
        color_scheme = fzf_settings.get("color_scheme", "dark")
        if color_scheme == "dark":
            colors = (
                "--color=bg+:#3B4252,bg:#2E3440,spinner:#81A1C1,hl:#616E88,"
                "fg:#D8DEE9,header:#616E88,info:#81A1C1,pointer:#81A1C1,"
                "marker:#81A1C1,fg+:#D8DEE9,prompt:#81A1C1,hl+:#81A1C1"
            )
            opts.append(colors)

        opts_str = " ".join(opts)

        config = f"""
# FZF (fuzzy finder) - Advanced Configuration
if command -v fzf &> /dev/null; then
    # Default options
    export FZF_DEFAULT_OPTS='{opts_str}'

    # Use fd instead of find if available
    if command -v fd &> /dev/null; then
        export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
        export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
        export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
    fi

    # Key bindings (if not already loaded)
    if [ -f /usr/share/doc/fzf/examples/key-bindings.zsh ]; then
        source /usr/share/doc/fzf/examples/key-bindings.zsh
    fi

    # Completion (if not already loaded)
    if [ -f /usr/share/doc/fzf/examples/completion.zsh ]; then
        source /usr/share/doc/fzf/examples/completion.zsh
    fi

    # Custom functions

    # fzf-based cd
    fcd() {{
        local dir
        dir=$(fd --type d --hidden --follow --exclude .git | fzf --preview 'eza -lah --color=always {{}}') && cd "$dir"
    }}

    # fzf-based file edit
    fe() {{
        local file
        file=$(fzf --preview 'bat --color=always --style=numbers {{}}') && ${{EDITOR:-vim}} "$file"
    }}

    # fzf-based git commit browser
    fgc() {{
        git log --oneline --color=always | fzf --ansi --preview 'git show --color=always {{1}}'
    }}

    # fzf-based process kill
    fkill() {{
        local pid
        pid=$(ps aux | sed 1d | fzf -m | awk '{{print $2}}')
        if [ -n "$pid" ]; then
            echo "$pid" | xargs kill -${{1:-9}}
        fi
    }}
fi
"""

        return config

    def _create_tool_integration_scripts(self):
        """
        Create custom scripts that integrate multiple tools together.

        Scripts:
        - preview:  Universal file previewer using bat/eza
        - search:  Intelligent search using fzf+ripgrep
        - goto: Smart directory navigation using zoxide+fzf
        """
        self.logger.info("Creating tool integration scripts...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir

                # Create scripts directory
                scripts_dir = os.path.join(user_home, ".local", "bin")
                self.run(f"sudo -u {shlex.quote(user)} mkdir -p {shlex.quote(scripts_dir)}")

                # Create preview script
                self._create_preview_script(user, scripts_dir)

                # Create search script
                self._create_search_script(user, scripts_dir)

                # Create goto script
                self._create_goto_script(user, scripts_dir)

                self.logger.info(f"✓ Integration scripts created for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to create scripts for user {user}: {e}")
                continue

        self.logger.info("✓ Tool integration scripts created")

    def _create_preview_script(self, user: str, scripts_dir: str):
        """Create universal preview script."""
        preview_script = """#!/bin/bash
# Universal file previewer
# Uses bat for text files, eza for directories

FILE="$1"

# Validate input
if [ -z "$FILE" ]; then
    echo "Usage: preview <file>"
    exit 1
fi

# Check file exists
if [ ! -e "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

if [ -d "$FILE" ]; then
    # Directory:  use eza
    eza -lah --color=always --icons --git -- "$FILE"
elif [ -f "$FILE" ]; then
    # File: detect type and use appropriate tool
    MIME=$(file --mime-type -b -- "$FILE")

    case "$MIME" in
        text/*|application/json|application/xml)
            # Text file: use bat
            bat --color=always --style=numbers -- "$FILE"
            ;;
        image/*)
            # Image:  show info
            file -- "$FILE"
            ;;
        application/pdf)
            # PDF: show info
            pdfinfo -- "$FILE" 2>/dev/null || file -- "$FILE"
            ;;
        *)
            # Unknown:  show file info
            file -- "$FILE"
            ls -lh -- "$FILE"
            ;;
    esac
else
    echo "Not a file or directory: $FILE"
fi
"""

        preview_path = os.path.join(scripts_dir, "preview")
        self.run(
            f"sudo -u {shlex.quote(user)} tee {shlex.quote(preview_path)} > /dev/null",
            input=preview_script.encode(),
            check=True,
        )
        self.run(f"chmod +x {shlex.quote(preview_path)}")

    def _create_search_script(self, user: str, scripts_dir: str):
        """Create intelligent search script using fzf + ripgrep."""
        search_script = """#!/bin/bash
# Intelligent search using ripgrep + fzf

if ! command -v rg &> /dev/null; then
    echo "ripgrep (rg) not installed"
    exit 1
fi

if ! command -v fzf &> /dev/null; then
    echo "fzf not installed"
    exit 1
fi

# Search pattern
PATTERN="$1"

if [ -z "$PATTERN" ]; then
    echo "Usage: search <pattern>"
    exit 1
fi

# Search and preview
# Using -- to separate flags from pattern for safety
rg --line-number --color=always --smart-case -- "$PATTERN" | \\
    fzf --ansi \\
        --delimiter : \\
        --preview 'bat --color=always --highlight-line {2} -- {1}' \\
        --preview-window '+{2}/2' \\
        --bind 'enter:execute(${EDITOR:-vim} +{2} -- {1})'
"""

        search_path = os.path.join(scripts_dir, "search")
        self.run(
            f"sudo -u {shlex.quote(user)} tee {shlex.quote(search_path)} > /dev/null",
            input=search_script.encode(),
            check=True,
        )
        self.run(f"chmod +x {shlex.quote(search_path)}")

    def _create_goto_script(self, user: str, scripts_dir: str):
        """Create smart directory navigation using zoxide + fzf."""
        goto_script = """#!/bin/bash
# Smart directory navigation with zoxide + fzf

if ! command -v zoxide &> /dev/null; then
    echo "zoxide not installed"
    exit 1
fi

if ! command -v fzf &> /dev/null; then
    echo "fzf not installed"
    exit 1
fi

# Get zoxide database and use fzf for selection
SELECTED=$(zoxide query -l | fzf --preview 'eza -lah --color=always --icons {}')

if [ -n "$SELECTED" ]; then
    cd "$SELECTED" || exit 1
    # Update zoxide score
    zoxide add "$SELECTED"
    # Show contents
    eza -lah --icons --git
fi
"""

        goto_path = os.path.join(scripts_dir, "goto")
        self.run(
            f"sudo -u {shlex.quote(user)} tee {shlex.quote(goto_path)} > /dev/null",
            input=goto_script.encode(),
            check=True,
        )
        self.run(f"chmod +x {shlex.quote(goto_path)}")

    def _update_zshrc_for_advanced_tools(self):
        """
        Update .zshrc to include advanced tool configurations.

        This appends to existing .zshrc created in Phase 4.
        """
        self.logger.info("Updating .zshrc with advanced tool configurations...")

        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            if not self._validate_user_safety(user):
                continue

            try:
                user_info = pwd.getpwnam(user)
                user_home = user_info.pw_dir
                zshrc_path = os.path.join(user_home, ".zshrc")

                # Generate advanced configuration block
                advanced_config = self._generate_advanced_tools_zshrc_block()

                # Append to existing .zshrc
                append_cmd = (
                    f"sudo -u {shlex.quote(user)} sh -c "
                    f"'echo {shlex.quote(advanced_config)} >> {shlex.quote(zshrc_path)}'"
                )

                self.run(append_cmd, check=False, shell=True)

                self.logger.info(f"✓ .zshrc updated for user: {user}")

            except Exception as e:
                self.logger.error(f"Failed to update .zshrc for user {user}: {e}")
                continue

        self.logger.info("✓ .zshrc files updated with advanced configurations")

    def _generate_advanced_tools_zshrc_block(self) -> str:
        """
        Generate the advanced tools configuration block for .zshrc.

        Returns:
            Complete configuration block
        """
        config_block = """

# ============================================================
# Advanced Terminal Tools Configuration (Phase 5)
# ============================================================

"""

        # Add eza aliases
        config_block += self._generate_exa_aliases()

        # Add zoxide config
        config_block += self._generate_zoxide_config()

        # Add FZF config
        config_block += self._generate_fzf_config()

        # Add PATH for custom scripts
        config_block += """
# Add custom scripts to PATH
export PATH="$HOME/.local/bin:$PATH"

# ============================================================
# Workflow-Specific Functions
# ============================================================

# Development workflow
dev() {
    local project_dir="${1:-.}"

    # Validate directory
    if [ ! -d "$project_dir" ]; then
        echo "Directory not found: $project_dir"
        return 1
    fi

    cd "$project_dir" || return 1

    echo "📂 Project: $(pwd)"
    echo ""

    # Show git status if in git repo
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "📊 Git Status:"
        git status -sb
        echo ""
    fi

    # Show recent files
    echo "📄 Recent Files:"
    eza -lah --sort=modified --icons | head -10
}

# System administration workflow
sysinfo() {
    echo "🖥️  System Information"
    echo "===================="
    echo ""
    echo "Hostname: $(hostname)"
    echo "OS: $(lsb_release -ds)"
    echo "Kernel: $(uname -r)"
    echo ""
    echo "💾 Disk Usage:"
    df -h / /home | tail -n +2
    echo ""
    echo "🧠 Memory Usage:"
    free -h
    echo ""
    echo "📊 Load Average:"
    uptime
}

# Docker workflow
denv() {
    echo "🐳 Docker Environment"
    echo "===================="
    echo ""
    echo "Containers:"
    docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
    echo ""
    echo "Images:"
    docker images --format "table {{.Repository}}: {{.Tag}}\\t{{.Size}}"
}

"""

        return config_block

    def _install_optional_productivity_tools(self):
        """
        Install optional but highly recommended productivity tools.

        Tools:
        - ripgrep (rg): Fast grep alternative
        - fd: Fast find alternative
        - delta: Better git diff
        - tokei: Code statistics
        - bottom (btm): Better top/htop
        """
        self.logger.info("Installing optional productivity tools...")

        optional_tools_config = self.get_config("desktop.terminal_tools.optional", {})

        tools_to_install = []

        if optional_tools_config.get("ripgrep", True):
            tools_to_install.append("ripgrep")

        if optional_tools_config.get("fd", True):
            tools_to_install.append("fd-find")

        if optional_tools_config.get("delta", True):
            # Git delta might need manual installation
            self._install_git_delta()

        if optional_tools_config.get("tokei", False):
            self._install_tokei()

        if optional_tools_config.get("bottom", False):
            self._install_bottom()

        if tools_to_install:
            self.install_packages(tools_to_install)
            self.logger.info(f"✓ Optional tools installed: {', '.join(tools_to_install)}")

        self.logger.info("✓ Optional productivity tools configured")

    def _install_git_delta(self):
        """Install git-delta for better git diffs."""
        self.logger.info("Installing git-delta...")

        # Git delta often needs to be installed from releases
        # Check if available in APT first
        result = self.run("apt-cache search git-delta", check=False, force_execute=True)

        if result.success and "git-delta" in result.stdout:
            self.install_packages(["git-delta"])
        else:
            self.logger.info("git-delta not available in APT; installation bypassed.")
            # Could download from GitHub releases here if needed

    def _install_tokei(self):
        """Install tokei for code statistics."""
        self.logger.info("Installing tokei...")

        # Tokei often needs manual installation
        self.logger.warning("tokei installation not automated, install manually if needed")

    def _install_bottom(self):
        """Install bottom (btm) for system monitoring."""
        self.logger.info("Installing bottom...")

        # Bottom might be available in newer Debian versions
        result = self.run("apt-cache search '^bottom$'", check=False, force_execute=True)

        if result.success and "bottom" in result.stdout:
            self.install_packages(["bottom"])
        else:
            self.logger.info("bottom not available in APT; installation bypassed.")

    def _verify_advanced_tools(self) -> bool:
        """Verify advanced terminal tools configuration."""
        checks_passed = True

        # Check bat configuration
        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        for user in users:
            try:
                user_home = pwd.getpwnam(user).pw_dir
                bat_config = os.path.join(user_home, ".config", "bat", "config")

                if os.path.exists(bat_config):
                    self.logger.info(f"✓ Bat configured for:  {user}")
                else:
                    self.logger.warning(f"Bat config missing for: {user}")

            except Exception as e:
                self.logger.error(f"Failed to verify for user {user}: {e}")

        # Check integration scripts
        for user in users:
            try:
                user_home = pwd.getpwnam(user).pw_dir
                scripts_dir = os.path.join(user_home, ".local", "bin")

                scripts = ["preview", "search", "goto"]
                for script in scripts:
                    script_path = os.path.join(scripts_dir, script)
                    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                        self.logger.info(f"✓ {script} script installed for: {user}")
                    else:
                        self.logger.warning(f"{script} script missing for: {user}")

            except Exception as e:
                self.logger.error(f"Failed to verify scripts for user {user}: {e}")

        # Check optional tools
        optional_tools = {"rg": "ripgrep", "fd": "fd-find", "delta": "git-delta"}

        for cmd, name in optional_tools.items():
            if self.command_exists(cmd):
                self.logger.info(f"✓ {name} installed")
            else:
                self.logger.info(f"○ {name} not installed (optional)")

        return checks_passed
