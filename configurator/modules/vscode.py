"""
VS Code module for editor installation.

Handles:
- VS Code installation from Microsoft repository
- Extension installation
"""

import os

from configurator.modules.base import ConfigurationModule
from configurator.utils.file import write_file


class VSCodeModule(ConfigurationModule):
    """
    Visual Studio Code installation module.

    Installs VS Code from the official Microsoft repository
    and configures recommended extensions.
    """

    name = "VS Code"
    description = "Visual Studio Code editor"
    depends_on = ["system"]
    priority = 60
    mandatory = False

    # Recommended extensions
    EXTENSIONS = [
        "ms-python.python",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-azuretools.vscode-docker",
        "eamodio.gitlens",
        "formulahendry.auto-rename-tag",
        "christian-kohler.path-intellisense",
    ]

    def validate(self) -> bool:
        """Validate VS Code prerequisites."""
        if self.command_exists("code"):
            result = self.run("code --version", check=False)
            version = result.stdout.split("\n")[0] if result.success else "unknown"
            self.logger.info(f"  Found existing VS Code: {version}")

        return True

    def configure(self) -> bool:
        """Install and configure VS Code."""
        self.logger.info("Installing Visual Studio Code...")

        # 1. Add Microsoft repository
        self._add_microsoft_repository()

        # 2. Install VS Code
        self._install_vscode()

        # 3. Install extensions
        self._install_extensions()

        self.logger.info("✓ VS Code installed")
        return True

    def verify(self) -> bool:
        """Verify VS Code installation."""
        if self.dry_run:
            return True

        checks_passed = True

        # Check code command
        if not self.command_exists("code"):
            self.logger.error("VS Code not found!")
            checks_passed = False
        else:
            result = self.run("code --version", check=False)
            version = result.stdout.split("\n")[0] if result.success else "unknown"
            self.logger.info(f"✓ VS Code {version}")

        return checks_passed

    def _add_microsoft_repository(self):
        """Add Microsoft package repository."""
        self.logger.info("Adding Microsoft repository...")

        import os

        # Cleanup potential conflicting files from previous configs
        for conflicting_file in [
            "/etc/apt/sources.list.d/vscode.sources",
            "/etc/apt/sources.list.d/vscode.list",
        ]:
            if os.path.exists(conflicting_file):
                self.logger.info(f"Removing conflicting file {conflicting_file}...")
                os.remove(conflicting_file)

        # Download and install GPG key
        self.run(
            "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | "
            "gpg --dearmor --yes -o /usr/share/keyrings/packages.microsoft.gpg",
            check=True,
        )

        # Add repository
        repo_line = (
            "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/packages.microsoft.gpg] "
            "https://packages.microsoft.com/repos/code stable main"
        )

        write_file("/etc/apt/sources.list.d/vscode.list", repo_line + "\n")

        self.logger.info("✓ Microsoft repository added")

    def _install_vscode(self):
        """Install VS Code package."""
        self.logger.info("Installing VS Code package...")
        self.install_packages(["code"], update_cache=True)

    def _install_extensions(self):
        """Install recommended extensions."""
        extensions = self.get_config("extensions", self.EXTENSIONS)

        if not extensions:
            self.logger.info("No extensions to install")
            return

        self.logger.info(f"Installing {len(extensions)} extensions...")

        # Determine user to install extensions for
        # If running as root, we want to install for target_user
        # VS Code installs extensions to ~/.vscode/extensions by default

        cmd_prefix = ""
        user_data_dir_flag = ""

        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd_prefix = f"sudo -u {self.target_user} "
            # We don't strictly need user-data-dir if we run as the user,
            # but code might complain about running as root if we didn't use sudo.
            # --no-sandbox is needed if running as root, but as user it's fine.
        elif self.target_user == "root":
            # Running as root for root (not recommended for VS Code but supported with args)
            user_data_dir_flag = "--user-data-dir /root/.config/Code --no-sandbox"

        for ext in extensions:
            retries = 3
            for attempt in range(1, retries + 1):
                try:
                    # Construct command
                    install_cmd = (
                        f"{cmd_prefix}code --install-extension {ext} --force {user_data_dir_flag}"
                    )

                    self.run(
                        install_cmd,
                        check=True,
                        timeout=600,
                    )
                    self.logger.info(f"  ✓ {ext}")
                    break
                except Exception as e:
                    if attempt == retries:
                        self.logger.warning(
                            f"  ⚠ Failed to install {ext} after {retries} attempts: {e}"
                        )
                    else:
                        self.logger.info(
                            f"  ⚠ Failed to install {ext} (attempt {attempt}/{retries}), retrying..."
                        )
                        import time

                        time.sleep(5)
