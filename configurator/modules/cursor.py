"""
Cursor IDE module for AI-powered code editor.

Handles:
- Cursor .deb package download (v2.3+)
- Installation via apt-get
- Configuration and Verification
"""

import os
from pathlib import Path

from configurator.exceptions import ModuleExecutionError
from configurator.modules.base import ConfigurationModule
from configurator.utils.command import command_exists


class CursorModule(ConfigurationModule):
    """
    Cursor IDE installation module.

    Cursor is an AI-powered code editor based on VS Code.
    """

    name = "Cursor"
    description = "Cursor AI editor"
    depends_on = ["system"]
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
        config_dir = Path(os.path.join(self.target_home, ".config/Cursor"))
        config_dir.mkdir(parents=True, exist_ok=True)

        # Set permissions if running as sudo/root
        if self.target_user != os.environ.get("USER"):
            self.run(f"chown -R {self.target_user}:{self.target_user} {config_dir}", check=False)

    def _install_cursor(self) -> None:
        """Install Cursor IDE via .deb package."""
        self.logger.info("Installing Cursor IDE...")

        # New URL for .deb package (v2.3)
        # Using the specific version endpoint as requested by user
        cursor_url = "https://api2.cursor.sh/updates/download/golden/linux-x64-deb/cursor/2.3"
        temp_deb = str(Path(self.target_home) / "cursor.deb")

        self.logger.info("Downloading Cursor .deb package...")
        try:
            # Download with retry logic
            self.run(
                f"curl -L --retry 3 --retry-delay 5 -o {temp_deb} '{cursor_url}'",
                check=True,
                description="Download Cursor .deb",
            )

            self.logger.info("Installing Cursor package...")
            # Use dpkg directly for .deb files to allow downgrades
            result = self.run(
                f"dpkg --force-confnew --force-confdef --force-overwrite -i {temp_deb}",
                check=False,
                description="Install Cursor .deb",
            )

            if result.return_code != 0:
                self.logger.warning("dpkg install had errors, fixing dependencies...")

            # Fix any broken dependencies after dpkg install
            # Retry with exponential backoff for lock contention
            max_retries = 5
            for attempt in range(max_retries):
                fix_result = self.run(
                    "apt-get install -f -y --allow-downgrades",
                    check=False,
                    description="Fix Cursor dependencies",
                )

                if fix_result.return_code == 0:
                    self.logger.info("✓ Dependencies fixed successfully")
                    break
                elif "Could not get lock" in fix_result.stderr or "is held by" in fix_result.stderr:
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff: 1, 2, 4, 8, 16s
                        self.logger.info(f"APT lock detected, waiting {wait_time}s before retry...")
                        import time

                        time.sleep(wait_time)
                    else:
                        raise ModuleExecutionError(
                            what="Failed to fix Cursor dependencies",
                            why="APT lock timeout - another process is using package manager",
                            how="Wait for other installations to complete, then retry manually: sudo apt-get install -f",
                        )
                else:
                    raise ModuleExecutionError(
                        what="Failed to fix Cursor dependencies",
                        why=fix_result.stderr,
                        how="Check the error above and fix manually",
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
