"""
Node.js module for JavaScript/TypeScript development.

Handles:
- nvm (Node Version Manager)
- Node.js LTS installation
- npm, yarn, pnpm package managers
- Global development tools
"""

import os

from configurator.modules.base import ConfigurationModule


class NodeJSModule(ConfigurationModule):
    """
    Node.js development environment module.

    Uses nvm for Node.js version management, making it easy
    to switch between Node.js versions.
    """

    name = "Node.js Development"
    description = "Node.js (via NVM), NPM, Yarn"
    depends_on = ["system"]
    priority = 41
    mandatory = False

    # nvm version to install
    NVM_VERSION = "0.40.1"

    # Global packages to install
    GLOBAL_PACKAGES = [
        "typescript",
        "ts-node",
        "nodemon",
        "eslint",
        "prettier",
    ]

    def validate(self) -> bool:
        """Validate Node.js prerequisites."""
        # Check if nvm is already installed
        nvm_dir = f"{self.target_home}/.nvm"
        if os.path.exists(nvm_dir):
            self.logger.info("✓ nvm is already installed")

        # Check if node is already installed (system-wide)
        if self.command_exists("node"):
            result = self.run("node --version", check=False)
            self.logger.info(f"  Found existing Node.js: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Configure Node.js development environment."""
        self.logger.info("Setting up Node.js with nvm...")

        # 1. Install nvm
        self._install_nvm()

        # 2. Install Node.js LTS
        self._install_nodejs()

        # 3. Install package managers
        self._install_package_managers()

        # 4. Install global tools
        self._install_global_tools()

        self.logger.info("✓ Node.js development environment ready")
        return True

    def verify(self) -> bool:
        """Verify Node.js installation."""
        if self.dry_run:
            return True

        checks_passed = True

        # Source nvm in verification commands
        nvm_source = f'export NVM_DIR="{self.target_home}/.nvm" && . "$NVM_DIR/nvm.sh" && '

        # Check nvm
        nvm_dir = f"{self.target_home}/.nvm"
        if not os.path.exists(nvm_dir):
            self.logger.error("nvm is not installed!")
            checks_passed = False
        else:
            self.logger.info("✓ nvm is installed")

        # Check node
        result = self.run(f"bash -c '{nvm_source}node --version'", check=False)
        if result.success:
            self.logger.info(f"✓ Node.js {result.stdout.strip()}")
        else:
            self.logger.error("Node.js not found!")
            checks_passed = False

        # Check npm
        result = self.run(f"bash -c '{nvm_source}npm --version'", check=False)
        if result.success:
            self.logger.info(f"✓ npm {result.stdout.strip()}")

        return checks_passed

    def _install_nvm(self):
        """Install Node Version Manager."""
        nvm_dir = f"{self.target_home}/.nvm"

        if os.path.exists(nvm_dir):
            self.logger.info("nvm already installed, updating...")

        self.logger.info(f"Installing nvm v{self.NVM_VERSION}...")

        # Download and run nvm install script
        nvm_url = f"https://raw.githubusercontent.com/nvm-sh/nvm/v{self.NVM_VERSION}/install.sh"

        # Explicitly set NVM_DIR and install as target user if applicable
        # If running as root but targeting user, we must switch user OR fix permissions later.
        # nvm install script uses $HOME.

        # Strategy: Run as target user if possible
        cmd = f"curl -o- {nvm_url} | bash"
        env = os.environ.copy()

        if self.target_user != "root" and os.environ.get("USER") == "root":
            # We are root, targeting a user.
            # Use su/sudo to run as user
            # Since 'run' uses subprocess/shell, we can wrap the command
            # But we also need to set HOME
            cmd = f"sudo -u {self.target_user} bash -c 'export HOME={self.target_home} && curl -o- {nvm_url} | NVM_DIR={nvm_dir} bash'"
        else:
            env["NVM_DIR"] = nvm_dir

        result = self.run(
            cmd,
            check=False,
            # env=env # Env not needed if using sudo wrapper with export
        )

        if not result.success:
            self.logger.warning("nvm installation may have had issues")

        # Add nvm to user's bashrc and zshrc
        nvm_init = """
# NVM (Node Version Manager)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"
"""

        for rc_file in [".bashrc", ".zshrc"]:
            target_rc = f"{self.target_home}/{rc_file}"
            # Only append to zshrc if it exists (or just create it, but desktop.py should have made it)
            # If desktop module is disabled, we might create a loose .zshrc, which is fine.

            if os.path.exists(target_rc) or rc_file == ".bashrc":
                # Always do bashrc, do zshrc if exists or if we want to force it.
                # Let's check consistency.

                try:
                    current_content = ""
                    if os.path.exists(target_rc):
                        with open(target_rc, "r") as f:
                            current_content = f.read()

                    if "NVM_DIR" not in current_content:
                        with open(target_rc, "a") as f:
                            f.write(nvm_init)
                        # Fix permissions
                        if self.target_user != "root":
                            self.run(
                                f"chown {self.target_user}:{self.target_user} {target_rc}",
                                check=False,
                            )
                except Exception as e:
                    self.logger.warning(f"Failed to update {rc_file}: {e}")

        self.logger.info("✓ nvm installed")

    def _install_nodejs(self):
        """Install Node.js using nvm."""
        node_version = self.get_config("version", "20")  # Default to LTS
        nvm_dir = f"{self.target_home}/.nvm"

        self.logger.info(f"Installing Node.js v{node_version} (LTS)...")

        # Install and use specified version
        nvm_source = (
            f'export NVM_DIR="{nvm_dir}" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"'
        )
        nvm_commands = f"""
{nvm_source}
nvm install {node_version}
nvm use {node_version}
nvm alias default {node_version}
"""
        cmd = f"bash -c '{nvm_commands}'"
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd = f"sudo -u {self.target_user} bash -c '{nvm_commands}'"

        result = self.run(cmd, check=False)

        if result.success:
            self.logger.info(f"✓ Node.js v{node_version} installed")
        else:
            self.logger.warning(f"Node.js installation may have had issues: {result.stderr}")

    def _install_package_managers(self):
        """Install yarn and pnpm package managers."""
        package_managers = self.get_config("package_managers", ["npm", "yarn", "pnpm"])

        nvm_dir = f"{self.target_home}/.nvm"
        nvm_source = (
            f'export NVM_DIR="{nvm_dir}" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
        )

        for pm in package_managers:
            if pm == "npm":
                continue  # npm comes with Node.js

            self.logger.info(f"Installing {pm}...")

            cmd_prefix = ""
            if self.target_user != "root" and os.environ.get("USER") == "root":
                cmd_prefix = f"sudo -u {self.target_user} "

            if pm == "yarn":
                result = self.run(
                    f"{cmd_prefix}bash -c '{nvm_source}npm install -g yarn'",
                    check=False,
                )
            elif pm == "pnpm":
                result = self.run(
                    f"{cmd_prefix}bash -c '{nvm_source}npm install -g pnpm'",
                    check=False,
                )

            if result.success:
                self.logger.info(f"  ✓ {pm} installed")
            else:
                self.logger.warning(f"  ⚠ Failed to install {pm}")

    def _install_global_tools(self):
        """Install global development tools."""
        global_packages = self.get_config("global_packages", self.GLOBAL_PACKAGES)

        if not global_packages:
            return

        self.logger.info("Installing global packages...")

        nvm_dir = f"{self.target_home}/.nvm"
        nvm_source = (
            f'export NVM_DIR="{nvm_dir}" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
        )
        packages_str = " ".join(global_packages)

        cmd_prefix = ""
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd_prefix = f"sudo -u {self.target_user} "

        result = self.run(
            f"{cmd_prefix}bash -c '{nvm_source}npm install -g {packages_str}'",
            check=False,
        )

        if result.success:
            self.logger.info(f"  ✓ Installed: {', '.join(global_packages)}")
        else:
            self.logger.warning("  ⚠ Some packages may not have installed correctly")
