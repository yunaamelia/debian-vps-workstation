"""
Cursor IDE module for AI-powered code editor.

Handles:
- Cursor .deb package download (v2.3+)
- Installation via apt-get
- Configuration and Verification
"""

import os
from pathlib import Path

from configurator.modules.base import ConfigurationModule
from configurator.exceptions import ModuleExecutionError
from configurator.utils.command import command_exists


class CursorModule(ConfigurationModule):
    """
    Cursor IDE installation module.

    Cursor is an AI-powered code editor based on VS Code.
    """

    name = "Cursor IDE"
    description = "Install Cursor AI-powered code editor"
    priority = 61
    mandatory = False

    def validate(self) -> bool:
        """Validate Cursor prerequisites."""
        # Check if Cursor is already installed
        if command_exists("cursor"):
            self.logger.info("  Cursor is already installed")

        return True

    def configure(self) -> bool:
        """Install and Configure Cursor IDE."""
        self._install_cursor()
        self._configure()
        self._verify_installation()
        return True

    def verify(self) -> bool:
        """Verify Cursor installation."""
        try:
            self._verify_installation()
            return True
        except ModuleExecutionError:
            return False

    def _verify_installation(self) -> None:
        """Verify Cursor installation."""
        if not command_exists("cursor"):
            raise ModuleExecutionError(
                what="Cursor verification failed",
                why="cursor command not found",
                how="Check installation logs",
            )
        
        # Check if it was installed via package manager
        result = self.run("dpkg -s cursor", check=False)
        if not result.success:
             self.logger.warning("Cursor installed but not found in dpkg (manual install?)")

        self.logger.info("✓ Cursor IDE installed")

    def _configure(self) -> None:
        """Configure Cursor settings directory."""
        # Create config directory
        config_dir = Path.home() / ".config" / "Cursor"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Set permissions if running as sudo
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            self.run(f"chown -R {sudo_user}:{sudo_user} {config_dir}", check=False)

    def _install_cursor(self) -> None:
        """Install Cursor IDE via .deb package."""
        self.logger.info("Installing Cursor IDE...")

        # New URL for .deb package (v2.3)
        # Using the specific version endpoint as requested by user
        cursor_url = "https://api2.cursor.sh/updates/download/golden/linux-x64-deb/cursor/2.3"
        temp_deb = "/tmp/cursor.deb"

        self.logger.info("Downloading Cursor .deb package...")
        try:
            # Download with retry logic
            self.run(
                f"curl -L --retry 3 --retry-delay 5 -o {temp_deb} '{cursor_url}'", 
                check=True,
                description="Download Cursor .deb"
            )

            self.logger.info("Installing Cursor package...")
            # Use apt-get install to handle dependencies automatically
            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"
            
            self.run(
                f"apt-get install -y {temp_deb}",
                check=True,
                env=env,
                description="Install Cursor .deb"
            )

        except Exception as e:
            raise ModuleExecutionError(
                what="Failed to install Cursor",
                why=str(e),
                how="Check network connection and URL",
            )
        finally:
            # Cleanup
            if os.path.exists(temp_deb):
                os.remove(temp_deb)
