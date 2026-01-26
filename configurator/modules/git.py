"""
Git module for version control.

Handles:
- Git installation and configuration
- GitHub CLI installation
"""

from configurator.modules.base import ConfigurationModule
from configurator.utils.file import write_file


class GitModule(ConfigurationModule):
    """
    Git and GitHub CLI installation module.
    """

    name = "Git"
    description = "Git configuration and GPG signing"
    depends_on = ["system"]
    priority = 51
    mandatory = False

    def validate(self) -> bool:
        """Validate Git prerequisites."""
        if self.command_exists("git"):
            result = self.run("git --version", check=False)
            self.logger.info(f"  Found existing Git: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure Git."""
        self.logger.info("Setting up Git...")

        # 1. Install Git
        self._install_git()

        # 2. Install GitHub CLI
        if self.get_config("github_cli", True):
            self._install_github_cli()

        # 3. Configure Git
        self._configure_git()

        self.logger.info("✓ Git setup complete")
        return True

    def verify(self) -> bool:
        """Verify Git installation."""
        if self.dry_run:
            return True

        checks_passed = True

        # Check git
        result = self.run("git --version", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("Git not found!")
            checks_passed = False

        # Check gh (GitHub CLI)
        result = self.run("gh --version", check=False)
        if result.success:
            version_line = result.stdout.split("\n")[0]
            self.logger.info(f"✓ GitHub CLI: {version_line}")
        else:
            self.logger.info("  GitHub CLI not installed (optional)")

        return checks_passed

    def _install_git(self):
        """Install Git."""
        self.logger.info("Installing Git...")
        self.install_packages(["git", "git-lfs"])

        # Initialize git-lfs
        self.run("git lfs install", check=False)

    def _install_github_cli(self):
        """Install GitHub CLI."""
        self.logger.info("Installing GitHub CLI...")

        # Add GitHub CLI repository
        # Download GPG key
        self.run(
            "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg "
            "| dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
            check=False,
        )

        self.run(
            "chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
            check=False,
        )

        # Add repository
        repo_line = (
            "deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] "
            "https://cli.github.com/packages stable main"
        )

        write_file("/etc/apt/sources.list.d/github-cli.list", repo_line + "\n")

        # Install
        self.run("apt-get update", check=False)
        self.install_packages(["gh"], update_cache=False)

        self.logger.info("✓ GitHub CLI installed")

    def _configure_git(self):
        """Configure Git with sensible defaults."""
        self.logger.info("Configuring Git defaults...")

        # Set useful defaults (system-wide)
        defaults = [
            ("init.defaultBranch", "main"),
            ("core.autocrl", "input"),
            ("pull.rebase", "false"),
            ("push.autoSetupRemote", "true"),
            ("color.ui", "auto"),
        ]

        for key, value in defaults:
            self.run(f"git config --system {key} {value}", check=False)

        # Create global gitignore
        gitignore_global = """# Global gitignore
# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
*.local

# Logs
*.log
logs/

# Dependencies (language-specific should be in project)
node_modules/
__pycache__/
*.pyc
.venv/
venv/
"""

        write_file("/etc/gitignore", gitignore_global)
        self.run("git config --system core.excludesFile /etc/gitignore", check=False)

        self.logger.info("✓ Git configured with sensible defaults")
