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
        self.run(
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | "
            "sh -s -- -y --default-toolchain stable",
            check=True,
        )

        self.logger.info("✓ rustup installed")

    def _install_toolchain(self):
        """Install Rust toolchain."""
        cargo_env = os.path.expanduser("~/.cargo/env")
        source_cmd = f"source {cargo_env} && "

        toolchain = self.get_config("toolchain", "stable")

        self.logger.info(f"Installing {toolchain} toolchain...")

        self.run(
            f"bash -c '{source_cmd}rustup default {toolchain}'",
            check=True,
        )

    def _install_components(self):
        """Install Rust components."""
        cargo_env = os.path.expanduser("~/.cargo/env")
        source_cmd = f"source {cargo_env} && "

        components = ["rustfmt", "clippy", "rust-analyzer"]

        self.logger.info("Installing Rust components...")

        for component in components:
            result = self.run(
                f"bash -c '{source_cmd}rustup component add {component}'",
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

        cargo_env = os.path.expanduser("~/.cargo/env")
        source_cmd = f"source {cargo_env} && "

        self.logger.info("Installing cargo tools...")

        for tool in tools:
            result = self.run(
                f"bash -c '{source_cmd}cargo install {tool}'",
                check=False,
            )

            if result.success:
                self.logger.info(f"  ✓ {tool}")
            else:
                self.logger.warning(f"  ⚠ Failed to install {tool}")
