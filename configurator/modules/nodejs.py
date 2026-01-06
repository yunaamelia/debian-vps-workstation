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
        nvm_dir = os.path.expanduser("~/.nvm")
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
        checks_passed = True

        # Source nvm in verification commands
        nvm_source = "source ~/.nvm/nvm.sh && "

        # Check nvm
        nvm_dir = os.path.expanduser("~/.nvm")
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
        nvm_dir = os.path.expanduser("~/.nvm")

        if os.path.exists(nvm_dir):
            self.logger.info("nvm already installed, updating...")

        self.logger.info(f"Installing nvm v{self.NVM_VERSION}...")

        # Download and run nvm install script
        nvm_url = f"https://raw.githubusercontent.com/nvm-sh/nvm/v{self.NVM_VERSION}/install.sh"

        # Explicitly set NVM_DIR
        env = os.environ.copy()
        env["NVM_DIR"] = nvm_dir

        result = self.run(
            f"curl -o- {nvm_url} | bash",
            check=False,
            env=env,
        )

        if not result.success:
            self.logger.warning("nvm installation may have had issues")

        # Add nvm to bashrc if not already there
        bashrc = os.path.expanduser("~/.bashrc")
        nvm_init = """
# NVM (Node Version Manager)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"
"""

        with open(bashrc, "r") as f:
            bashrc_content = f.read()

        if "NVM_DIR" not in bashrc_content:
            with open(bashrc, "a") as f:
                f.write(nvm_init)

        self.logger.info("✓ nvm installed")

    def _install_nodejs(self):
        """Install Node.js using nvm."""
        node_version = self.get_config("version", "20")  # Default to LTS
        nvm_dir = os.path.expanduser("~/.nvm")

        self.logger.info(f"Installing Node.js v{node_version} (LTS)...")

        # Install and use specified version
        # NVM_DIR is explicitly set within the bash script for robustness
        nvm_commands = f"""
export NVM_DIR="{nvm_dir}"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
nvm install {node_version}
nvm use {node_version}
nvm alias default {node_version}
"""

        result = self.run(f"bash -c '{nvm_commands}'", check=False)

        if result.success:
            self.logger.info(f"✓ Node.js v{node_version} installed")
        else:
            self.logger.warning(f"Node.js installation may have had issues: {result.stderr}")

    def _install_package_managers(self):
        """Install yarn and pnpm package managers."""
        package_managers = self.get_config("package_managers", ["npm", "yarn", "pnpm"])

        nvm_source = "source ~/.nvm/nvm.sh && "

        for pm in package_managers:
            if pm == "npm":
                continue  # npm comes with Node.js

            self.logger.info(f"Installing {pm}...")

            if pm == "yarn":
                result = self.run(
                    f"bash -c '{nvm_source}npm install -g yarn'",
                    check=False,
                )
            elif pm == "pnpm":
                result = self.run(
                    f"bash -c '{nvm_source}npm install -g pnpm'",
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

        nvm_source = "source ~/.nvm/nvm.sh && "
        packages_str = " ".join(global_packages)

        result = self.run(
            f"bash -c '{nvm_source}npm install -g {packages_str}'",
            check=False,
        )

        if result.success:
            self.logger.info(f"  ✓ Installed: {', '.join(global_packages)}")
        else:
            self.logger.warning("  ⚠ Some packages may not have installed correctly")
