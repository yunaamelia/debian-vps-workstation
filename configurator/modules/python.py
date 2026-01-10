"""
Python module for Python development environment.

Handles:
- System Python (Debian default)
- pip and venv
- Development tools (black, pylint, mypy, etc.)
"""

from configurator.modules.base import ConfigurationModule


class PythonModule(ConfigurationModule):
    """
    Python development environment module.

    Uses Debian's system Python 3.11 and installs
    common development tools.
    """

    name = "Python Development"
    description = "Python 3.11+, Pip, Poetry, Pyenv"
    depends_on = ["system"]
    priority = 40
    mandatory = False

    # System packages for Python development
    SYSTEM_PACKAGES = [
        "python3",
        "python3-pip",
        "python3-venv",
        "python3-dev",
        "python3-setuptools",
        "python3-wheel",
        "libssl-dev",
        "libffi-dev",
        "pipx",  # Install pipx via apt
    ]

    # Python dev tools to install
    DEV_TOOLS = [
        "black",
        "pylint",
        "mypy",
        "pytest",
        "ipython",
        "httpie",
        "poetry",
    ]

    # Map tools to Debian packages
    TOOL_PACKAGE_MAP = {
        "mypy": "python3-mypy",
        "pytest": "python3-pytest",
        "ipython": "python3-ipython",
        "virtualenv": "python3-virtualenv",
        "wheel": "python3-wheel",
        "poetry": "python3-poetry",
        "httpie": "httpie",
    }

    def validate(self) -> bool:
        """Validate Python prerequisites."""
        # Python3 should already be on Debian 13
        if self.command_exists("python3"):
            result = self.run("python3 --version", check=False)
            self.logger.info(f"✓ Found {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Configure Python development environment."""
        self.logger.info("Setting up Python development environment...")

        # 1. Install system packages
        self._install_system_packages()

        # 2. Upgrade pip (only if not restricted by PEP 668)
        self._upgrade_pip()

        # 3. Install dev tools
        self._install_dev_tools()

        # 4. Create example virtual environment
        self._create_example_venv()

        self.logger.info("✓ Python development environment ready")
        return True

    def verify(self) -> bool:
        """Verify Python installation."""
        checks_passed = True

        # Check python3
        if not self.command_exists("python3"):
            self.logger.error("python3 not found!")
            checks_passed = False
        else:
            result = self.run("python3 --version", check=False)
            self.logger.info(f"✓ {result.stdout.strip()}")

        # Check pip
        if not self.command_exists("pip3"):
            self.logger.error("pip3 not found!")
            checks_passed = False
        else:
            result = self.run("pip3 --version", check=False)
            self.logger.info("✓ pip installed")

        # Check pipx
        if not self.command_exists("pipx"):
            self.logger.warning("pipx not found!")
        else:
            result = self.run("pipx --version", check=False)
            self.logger.info(f"✓ pipx {result.stdout.strip()}")

        # Check venv
        result = self.run("python3 -c 'import venv'", check=False)
        if not result.success:
            self.logger.warning("venv module not available")
        else:
            self.logger.info("✓ venv module available")

        return checks_passed

    def _install_system_packages(self):
        """Install system Python packages."""
        self.logger.info("Installing Python system packages...")
        self.install_packages(self.SYSTEM_PACKAGES)

    def _upgrade_pip(self):
        """Upgrade pip to latest version."""
        # On Debian 12+, we need --break-system-packages or just skip it
        # Since we use system packages, we probably shouldn't mess with system pip
        self.logger.debug("Global pip upgrade managed by apt (system)")

    def _install_dev_tools(self):
        """Install Python development tools."""
        # Get dev tools from config or use defaults
        dev_tools = self.get_config("dev_tools", self.DEV_TOOLS)

        if not dev_tools:
            self.logger.info("No dev tools specified.")
            return

        self.logger.info(f"Installing dev tools: {', '.join(dev_tools)}")

        packages_to_install = []
        pipx_tools = []

        for tool in dev_tools:
            if tool in self.TOOL_PACKAGE_MAP:
                packages_to_install.append(self.TOOL_PACKAGE_MAP[tool])
            else:
                pipx_tools.append(tool)

        # Install APT packages
        if packages_to_install:
            self.logger.info(f"Installing system packages: {', '.join(packages_to_install)}")
            self.install_packages(packages_to_install)

        # Install pipx tools
        if pipx_tools:
            # Ensure pipx path is set up for root if we are running as root
            # But usually we want these for the user.
            # If running as root, 'pipx install' goes to /root/.local/bin
            # We explicitly allow this for now, or just warn.

            for tool in pipx_tools:
                self.logger.info(f"Installing {tool} via pipx...")
                result = self.run(f"pipx install {tool} --global", check=False)

                if not result.success:
                    # Try without --global
                    result = self.run(f"pipx install {tool}", check=False)

                if result.success:
                    self.logger.info(f"  ✓ Installed {tool} (pipx)")
                else:
                    self.logger.warning(f"  ⚠ Failed to install {tool} via pipx")

    def _create_example_venv(self):
        """Create an example virtual environment."""
        example_dir = "/root/python-example"

        self.logger.info(f"Creating example venv at {example_dir}...")

        self.run(f"mkdir -p {example_dir}", check=False)
        result = self.run(f"python3 -m venv {example_dir}/venv", check=False)

        if result.success:
            self.logger.info(f"  ✓ Example venv created at {example_dir}/venv")
            self.logger.info(f"    Activate with: source {example_dir}/venv/bin/activate")

        # Create a helpful README
        readme_content = """# Python Development Environment

## Quick Start

### Create a virtual environment:
```bash
python3 -m venv myproject
source myproject/bin/activate
```

### Install packages:
```bash
pip install requests flask django
```

### Code formatting (black):
```bash
black mycode.py
```

### Linting (pylint):
```bash
pylint mycode.py
```

### Type checking (mypy):
```bash
mypy mycode.py
```

### Testing (pytest):
```bash
pytest
```

### Interactive Python (ipython):
```bash
ipython
```

## Installed Tools
- black: Code formatter
- pylint: Linter
- mypy: Type checker
- pytest: Testing framework
- ipython: Enhanced Python shell
- virtualenv: Virtual environment manager

Enjoy coding! 🐍
"""

        with open(f"{example_dir}/README.md", "w") as f:
            f.write(readme_content)
