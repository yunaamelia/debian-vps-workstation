"""
Rust module for Rust development environment.

Handles:
- rustup installation
- Stable toolchain
- Common Rust tools
"""

import os

from configurator.modules.base import ConfigurationModule


class RustModule(ConfigurationModule):
    """
    Rust development environment module.

    Uses rustup for Rust toolchain management.
    """

    name = "Rust Development"
    description = "Rust programming language (via rustup)"
    depends_on = ["system"]
    priority = 43
    mandatory = False

    # Rust tools to install
    RUST_TOOLS = [
        "cargo-watch",
        "cargo-edit",
        "cargo-audit",
    ]

    def validate(self) -> bool:
        """Validate Rust prerequisites."""
        # Check if Rust is already installed
        if self.command_exists("rustc"):
            result = self.run("rustc --version", check=False)
            self.logger.info(f"  Found existing Rust: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure Rust."""
        self.logger.info("Installing Rust via rustup...")

        # 1. Install rustup
        self._install_rustup()

        # 2. Install stable toolchain
        self._install_toolchain()

        # 3. Install components
        self._install_components()

        # 4. Install cargo tools
        self._install_cargo_tools()

        self.logger.info("✓ Rust development environment ready")
        return True

    def verify(self) -> bool:
        """Verify Rust installation."""
        checks_passed = True

        cargo_env = os.path.expanduser("~/.cargo/env")
        source_cmd = f"source {cargo_env} && " if os.path.exists(cargo_env) else ""

        # Check rustc
        result = self.run(f"bash -c '{source_cmd}rustc --version'", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("rustc not found!")
            checks_passed = False

        # Check cargo
        result = self.run(f"bash -c '{source_cmd}cargo --version'", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("cargo not found!")
            checks_passed = False

        return checks_passed

    def _install_rustup(self):
        """Install rustup."""
        self.logger.info("Installing rustup...")

        # Download and run rustup installer
        # Use sudo -u if needed to install for target user
        cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable"
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd = f"sudo -u {self.target_user} bash -c 'curl --proto \"=https\" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable'"

        self.run(cmd, check=True)

        # Explicitly configure shell files as redundancy
        cargo_env_source = '\n. "$HOME/.cargo/env"\n'

        for rc_file in [".bashrc", ".zshrc"]:
            target_rc = f"{self.target_home}/{rc_file}"
            try:
                current_content = ""
                if os.path.exists(target_rc):
                    with open(target_rc, "r") as f:
                        current_content = f.read()

                if "cargo/env" not in current_content:
                    with open(target_rc, "a") as f:
                        f.write(cargo_env_source)
                    # Fix permissions
                    if self.target_user != "root":
                        self.run(
                            f"chown {self.target_user}:{self.target_user} {target_rc}", check=False
                        )
            except Exception as e:
                self.logger.warning(f"Failed to update {rc_file} for Rust: {e}")

        self.logger.info("✓ rustup installed")

    def _install_toolchain(self):
        """Install Rust toolchain."""
        cargo_env = f"{self.target_home}/.cargo/env"
        source_cmd = f"source {cargo_env} && "

        toolchain = self.get_config("toolchain", "stable")

        self.logger.info(f"Installing {toolchain} toolchain...")

        cmd_prefix = ""
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd_prefix = f"sudo -u {self.target_user} "

        self.run(
            f"{cmd_prefix}bash -c '{source_cmd}rustup default {toolchain}'",
            check=True,
        )

    def _install_components(self):
        """Install Rust components."""
        cargo_env = f"{self.target_home}/.cargo/env"
        source_cmd = f"source {cargo_env} && "

        components = ["rustfmt", "clippy", "rust-analyzer"]

        self.logger.info("Installing Rust components...")

        cmd_prefix = ""
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd_prefix = f"sudo -u {self.target_user} "

        for component in components:
            result = self.run(
                f"{cmd_prefix}bash -c '{source_cmd}rustup component add {component}'",
                check=False,
            )

            if result.success:
                self.logger.info(f"  ✓ {component}")
            else:
                self.logger.warning(f"  ⚠ Failed to install {component}")

    def _install_cargo_tools(self):
        """Install cargo tools."""
        tools = self.get_config("tools", self.RUST_TOOLS)

        if not tools:
            return

        cargo_env = f"{self.target_home}/.cargo/env"
        source_cmd = f"source {cargo_env} && "

        self.logger.info("Installing cargo tools...")

        cmd_prefix = ""
        if self.target_user != "root" and os.environ.get("USER") == "root":
            cmd_prefix = f"sudo -u {self.target_user} "

        for tool in tools:
            result = self.run(
                f"{cmd_prefix}bash -c '{source_cmd}cargo install {tool}'",
                check=False,
            )

            if result.success:
                self.logger.info(f"  ✓ {tool}")
            else:
                self.logger.warning(f"  ⚠ Failed to install {tool}")
