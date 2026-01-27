"""
Go (Golang) module for Go development environment.

Handles:
- Go installation from official source
- GOPATH configuration
- Common Go tools
"""

import os

from configurator.modules.base import ConfigurationModule


class GolangModule(ConfigurationModule):
    """
    Go development environment module.

    Installs Go from the official download and configures
    the environment for Go development.
    """

    name = "Go Development"
    description = "Go programming language environment"
    depends_on = ["system"]
    priority = 42
    mandatory = False

    # Default Go version
    DEFAULT_VERSION = "1.22.0"

    # Go tools to install
    GO_TOOLS = [
        "golang.org/x/tools/gopls@latest",
        "github.com/go-delve/delve/cmd/dlv@latest",
        "github.com/golangci/golangci-lint/cmd/golangci-lint@latest",
        "golang.org/x/tools/cmd/goimports@latest",
    ]

    def validate(self) -> bool:
        """Validate Go prerequisites."""
        # Check if Go is already installed
        if self.command_exists("go"):
            result = self.run("go version", check=False)
            self.logger.info(f"  Found existing Go: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure Go."""
        self.logger.info("Installing Go...")

        # 1. Download and install Go
        self._install_go()

        # 2. Configure environment
        self._configure_environment()

        # 3. Install Go tools
        self._install_go_tools()

        self.logger.info("✓ Go development environment ready")
        return True

    def verify(self) -> bool:
        """Verify Go installation."""
        checks_passed = True

        # Source environment
        go_env = self._get_go_env()

        # Check go command
        result = self.run(
            f"bash -c 'export PATH={go_env['PATH']} && go version'",
            check=False,
        )

        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("Go not found!")
            checks_passed = False

        return checks_passed

    def _install_go(self):
        """Download and install Go."""
        version = self.get_config("version", self.DEFAULT_VERSION)

        # Determine architecture
        result = self.run("uname -m", check=True)
        arch = result.stdout.strip()

        if arch == "x86_64":
            go_arch = "amd64"
        elif arch in ("aarch64", "arm64"):
            go_arch = "arm64"
        else:
            go_arch = "amd64"

        # Download Go
        go_url = f"https://go.dev/dl/go{version}.linux-{go_arch}.tar.gz"
        go_tarball = f"/tmp/go{version}.linux-{go_arch}.tar.gz"

        self.logger.info(f"Downloading Go {version}...")

        self.run(f"curl -fsSL {go_url} -o {go_tarball}", check=True)

        # Remove old installation
        self.run("rm -rf /usr/local/go", check=False)

        # Extract
        self.run(f"tar -C /usr/local -xzf {go_tarball}", check=True)

        # Cleanup
        self.run(f"rm {go_tarball}", check=False)

        self.logger.info(f"✓ Go {version} installed to /usr/local/go")

    def _configure_environment(self):
        """Configure Go environment variables."""
        self.logger.info("Configuring Go environment...")

        go_env_content = """
# Go environment
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin
"""

        # Add to /etc/profile.d for all users (requires root)
        try:
            profile_path = "/etc/profile.d/golang.sh"
            with open(profile_path, "w") as f:
                f.write(go_env_content)
            self.run(f"chmod +x {profile_path}", check=False)
        except Exception as e:
            self.logger.warning(f"Could not write to /etc/profile.d: {e}")

        # Also add to target user's bashrc and zshrc
        for rc_file in [".bashrc", ".zshrc"]:
            target_rc = f"{self.target_home}/{rc_file}"

            try:
                current_content = ""
                if os.path.exists(target_rc):
                    with open(target_rc, "r") as f:
                        current_content = f.read()

                if "GOROOT" not in current_content:
                    with open(target_rc, "a") as f:
                        f.write(go_env_content)
                    # Fix permissions
                    if self.target_user != "root":
                        self.run(
                            f"chown {self.target_user}:{self.target_user} {target_rc}", check=False
                        )
            except Exception as e:
                self.logger.warning(f"Failed to update {rc_file}: {e}")

        self.logger.info("✓ Go environment configured")

    def _install_go_tools(self):
        """Install common Go development tools."""
        tools = self.get_config("tools", self.GO_TOOLS)

        if not tools:
            return

        self.logger.info("Installing Go tools...")

        go_env = self._get_go_env()
        env_exports = f"export PATH={go_env['PATH']} && export GOPATH={go_env['GOPATH']} && export GOROOT={go_env['GOROOT']}"

        for tool in tools:
            tool_name = tool.split("/")[-1].split("@")[0]

            cmd = f"bash -c '{env_exports} && go install {tool}'"
            if self.target_user != "root" and os.environ.get("USER") == "root":
                cmd = f"sudo -u {self.target_user} {cmd}"

            result = self.run(
                cmd,
                check=False,
            )

            if result.success:
                self.logger.info(f"  ✓ {tool_name}")
            else:
                self.logger.warning(f"  ⚠ Failed to install {tool_name}")

    def _get_go_env(self):
        """Get Go environment variables."""
        home = self.target_home
        return {
            "GOROOT": "/usr/local/go",
            "GOPATH": f"{home}/go",
            "PATH": f"/usr/local/go/bin:{home}/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
