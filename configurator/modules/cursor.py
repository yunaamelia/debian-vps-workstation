"""
Cursor IDE module for AI-powered code editor.

Handles:
- Cursor AppImage download
- Desktop integration
"""

import os
from pathlib import Path

from configurator.modules.base import ConfigurationModule
from configurator.utils.network import get_latest_github_release


class CursorModule(ConfigurationModule):
    """
    Cursor IDE installation module.

    Cursor is an AI-powered code editor based on VS Code.
    """

    name = "Cursor IDE"
    description = "Install Cursor AI-powered code editor"
    priority = 61
    mandatory = False

    # Cursor download URL (AppImage)
    CURSOR_URL = "https://downloader.cursor.sh/linux/appImage/x64"

    def validate(self) -> bool:
        """Validate Cursor prerequisites."""
        # Check if Cursor is already installed
        if self.command_exists("cursor"):
            self.logger.info("  Cursor is already installed")

        return True

    def configure(self) -> bool:
        """Install Cursor IDE."""
        self.logger.info("Installing Cursor IDE...")

        # 1. Download Cursor AppImage
        self._download_cursor()

        # 2. Create desktop entry
        self._create_desktop_entry()

        self.logger.info("✓ Cursor IDE installed")
        return True

    def verify(self) -> bool:
        """Verify Cursor installation."""
        cursor_path = Path("/opt/cursor/cursor.AppImage")

        if cursor_path.exists():
            self.logger.info("✓ Cursor is installed")
            return True
        else:
            self.logger.error("Cursor not found!")
            return False

    def _download_cursor(self):
        """Download Cursor AppImage."""
        self.logger.info("Downloading Cursor...")

        # Create installation directory
        cursor_dir = Path("/opt/cursor")
        cursor_dir.mkdir(parents=True, exist_ok=True)

        cursor_path = cursor_dir / "cursor.AppImage"

        # Download
        # Download with retry
        self.run(
            f"curl -fsSL --retry 3 --retry-delay 5 '{self.CURSOR_URL}' -o {cursor_path}",
            check=True,
        )

        # Make executable
        self.run(f"chmod +x {cursor_path}", check=True)

        # Create symlink
        self.run(f"ln -sf {cursor_path} /usr/local/bin/cursor", check=True)

        self.logger.info("✓ Cursor downloaded")

    def _create_desktop_entry(self):
        """Create desktop entry for Cursor."""
        desktop_entry = """[Desktop Entry]
Name=Cursor
Comment=AI-powered Code Editor
Exec=/opt/cursor/cursor.AppImage --no-sandbox %F
Icon=cursor
Terminal=false
Type=Application
Categories=Development;IDE;TextEditor;
MimeType=text/plain;inode/directory;
StartupWMClass=Cursor
"""

        # Create desktop entry
        desktop_file = Path("/usr/share/applications/cursor.desktop")
        desktop_file.write_text(desktop_entry)

        # Download icon (using VS Code icon as fallback)
        icon_dir = Path("/usr/share/icons/hicolor/256x256/apps")
        icon_dir.mkdir(parents=True, exist_ok=True)

        # Use a simple placeholder or VS Code icon
        self.run(
            "curl -fsSL 'https://raw.githubusercontent.com/getcursor/cursor/main/resources/icon.png' "
            f"-o {icon_dir}/cursor.png 2>/dev/null || true",
            check=False,
        )

        self.logger.info("✓ Desktop entry created")
