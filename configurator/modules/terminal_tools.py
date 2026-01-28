"""
Terminal tools configuration module.

Handles:
- Zsh shell installation and configuration
- Oh-My-Zsh framework setup
- Eza (modern ls replacement) installation
- Bat (modern cat replacement) installation
- Zoxide (smarter cd) installation
- Terminal integrations and aliases
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from configurator.modules.base import ConfigurationModule
from configurator.utils.file import write_file


class TerminalToolsModule(ConfigurationModule):
    """
    Terminal tools installation and configuration module.

    Installs and configures eza, bat, zsh, zoxide, and oh-my-zsh
    with best practices and integrations between tools.
    """

    name = "Terminal Tools"
    description = "Eza, Bat, Zsh, Zoxide with Oh-My-Zsh"
    depends_on = ["system"]
    priority = 45
    mandatory = False

    # State file for idempotency tracking
    STATE_FILE = Path.home() / ".configurator" / "terminal-tools.state.json"

    # Oh-My-Zsh install URL
    OHMYZSH_INSTALL_URL = (
        "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
    )

    def __init__(self, *args, **kwargs):
        """Initialize the terminal tools module."""
        super().__init__(*args, **kwargs)
        self._state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load installation state for idempotency."""
        if self.STATE_FILE.exists():
            try:
                self._state = json.loads(self.STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                self._state = {}
        else:
            self._state = {}

    def _save_state(self) -> None:
        """Save installation state for idempotency."""
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.STATE_FILE.write_text(json.dumps(self._state, indent=2))

    def _get_target_user(self) -> str:
        """Get the target user for configuration."""
        return os.environ.get("SUDO_USER", os.environ.get("USER", "root"))

    def _get_home_dir(self) -> Path:
        """Get home directory for target user."""
        user = self._get_target_user()
        if user == "root":
            return Path("/root")
        return Path(f"/home/{user}")

    def validate(self) -> bool:
        """Validate prerequisites for terminal tools installation."""
        self.logger.info("Validating terminal tools prerequisites...")

        # Check if apt is available
        if not self.command_exists("apt-get"):
            self.logger.error("apt-get not found - this module requires Debian/Ubuntu")
            return False

        # Check if curl is available (needed for oh-my-zsh)
        if not self.command_exists("curl"):
            self.logger.info("curl not found, will be installed")

        # Check write permissions on home directory
        home = self._get_home_dir()
        if not os.access(home, os.W_OK):
            self.logger.error(f"Cannot write to home directory: {home}")
            return False

        # Check if zsh is already installed
        if self.command_exists("zsh"):
            result = self.run("zsh --version", check=False)
            self.logger.info(f"  Found existing zsh: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure terminal tools."""
        self.logger.info("Configuring terminal tools...")

        # Get configuration from config manager
        config = self._get_tools_config()

        # 1. Install base dependencies
        self._install_dependencies()

        # 2. Install zsh if enabled
        if config.get("zsh", {}).get("enabled", True):
            self._install_zsh()

            # 3. Install oh-my-zsh if not skipped
            if not config.get("skip_ohmyzsh", False):
                self._install_ohmyzsh()

        # 4. Install eza
        if config.get("eza", {}).get("enabled", True):
            self._install_eza()

        # 5. Install bat
        if config.get("bat", {}).get("enabled", True):
            self._install_bat()

        # 6. Install zoxide
        if config.get("zoxide", {}).get("enabled", True):
            self._install_zoxide()

        # 7. Apply zsh configuration with aliases and integrations
        self._apply_zsh_config(config)

        # 8. Save state
        self._state["configured"] = True
        self._state["configured_at"] = datetime.now().isoformat()
        self._save_state()

        self.logger.info("✓ Terminal tools configured successfully")
        return True

    def verify(self) -> bool:
        """Verify terminal tools installation."""
        if self.dry_run:
            return True

        self.logger.info("Verifying terminal tools installation...")
        checks_passed = True

        # Check zsh
        if self.command_exists("zsh"):
            result = self.run("zsh --version", check=False)
            if result.success:
                self.logger.info(f"✓ zsh: {result.stdout.strip()}")
            else:
                self.logger.warning("zsh installed but version check failed")
        else:
            self.logger.warning("zsh not installed")

        # Check eza
        if self.command_exists("eza"):
            result = self.run("eza --version", check=False)
            if result.success:
                version = result.stdout.strip().split("\n")[0]
                self.logger.info(f"✓ eza: {version}")
            else:
                self.logger.warning("eza installed but version check failed")
        else:
            self.logger.warning("eza not installed")
            checks_passed = False

        # Check bat
        if self.command_exists("bat") or self.command_exists("batcat"):
            cmd = "bat" if self.command_exists("bat") else "batcat"
            result = self.run(f"{cmd} --version", check=False)
            if result.success:
                self.logger.info(f"✓ bat: {result.stdout.strip()}")
            else:
                self.logger.warning("bat installed but version check failed")
        else:
            self.logger.warning("bat not installed")
            checks_passed = False

        # Check zoxide
        if self.command_exists("zoxide"):
            result = self.run("zoxide --version", check=False)
            if result.success:
                self.logger.info(f"✓ zoxide: {result.stdout.strip()}")
            else:
                self.logger.warning("zoxide installed but version check failed")
        else:
            self.logger.warning("zoxide not installed")
            checks_passed = False

        # Check oh-my-zsh
        ohmyzsh_dir = self._get_home_dir() / ".oh-my-zsh"
        if ohmyzsh_dir.exists():
            self.logger.info("✓ oh-my-zsh installed")
        else:
            self.logger.info("  oh-my-zsh not installed (optional)")

        # Check .zshrc exists
        zshrc = self._get_home_dir() / ".zshrc"
        if zshrc.exists():
            self.logger.info("✓ .zshrc configured")
        else:
            self.logger.warning(".zshrc not found")
            checks_passed = False

        return checks_passed

    def _get_tools_config(self) -> Dict[str, Any]:
        """Get terminal tools configuration from config manager."""
        config: Dict[str, Any] = {}

        # Try to get from desktop.terminal_tools first
        if hasattr(self.config, "get"):
            terminal_tools = self.config.get("desktop.terminal_tools", {})
            zsh_config = self.config.get("desktop.zsh", {})

            config["eza"] = terminal_tools.get("exa", {})  # Note: config uses 'exa' key
            config["bat"] = terminal_tools.get("bat", {})
            config["zoxide"] = terminal_tools.get("zoxide", {})
            config["fzf"] = terminal_tools.get("fzf", {})
            config["zsh"] = zsh_config
        else:
            # Default configuration
            config = {
                "eza": {"enabled": True, "icons": True, "git_integration": True},
                "bat": {"enabled": True, "theme": "TwoDark", "line_numbers": True},
                "zoxide": {"enabled": True, "interactive_mode": True},
                "zsh": {"enabled": True, "plugins": ["git", "docker", "zsh-autosuggestions"]},
            }

        return config

    def _install_dependencies(self) -> None:
        """Install base dependencies required for terminal tools."""
        self.logger.info("Installing base dependencies...")

        packages = ["curl", "git", "unzip"]
        self.install_packages_resilient(packages, update_cache=True)

    def _install_zsh(self) -> None:
        """Install zsh shell."""
        if self.command_exists("zsh"):
            self.logger.info("  zsh already installed, skipping")
            return

        self.logger.info("Installing zsh...")

        self.install_packages_resilient(["zsh"], update_cache=False)

        self.logger.info("✓ zsh installed")

    def _install_ohmyzsh(self) -> None:
        """Install Oh-My-Zsh framework."""
        ohmyzsh_dir = self._get_home_dir() / ".oh-my-zsh"

        if ohmyzsh_dir.exists():
            self.logger.info("  oh-my-zsh already installed, skipping")
            return

        self.logger.info("Installing oh-my-zsh...")

        user = self._get_target_user()
        home = self._get_home_dir()

        # Backup existing .zshrc if present
        zshrc = home / ".zshrc"
        if zshrc.exists():
            backup_path = home / f".zshrc.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(zshrc, backup_path)
            self.logger.info(f"  Backed up .zshrc to {backup_path.name}")

        # Download and run oh-my-zsh installer
        install_cmd = (
            f'curl -fsSL {self.OHMYZSH_INSTALL_URL} | RUNZSH=no CHSH=no ZSH="{ohmyzsh_dir}" sh'
        )

        if user != "root":
            install_cmd = f"su - {user} -c '{install_cmd}'"

        self.run(install_cmd, check=True, timeout=300)

        # Install additional plugins
        self._install_zsh_plugins(user, ohmyzsh_dir)

        self.logger.info("✓ oh-my-zsh installed")

    def _install_zsh_plugins(self, user: str, ohmyzsh_dir: Path) -> None:
        """Install additional zsh plugins."""
        plugins_dir = ohmyzsh_dir / "custom" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        # zsh-autosuggestions
        autosuggestions_dir = plugins_dir / "zsh-autosuggestions"
        if not autosuggestions_dir.exists():
            self.logger.info("  Installing zsh-autosuggestions...")
            clone_cmd = (
                f"git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions.git "
                f"{autosuggestions_dir}"
            )
            if user != "root":
                clone_cmd = f'su - {user} -c "{clone_cmd}"'
            self.run(clone_cmd, check=False, timeout=120)

        # zsh-syntax-highlighting
        highlighting_dir = plugins_dir / "zsh-syntax-highlighting"
        if not highlighting_dir.exists():
            self.logger.info("  Installing zsh-syntax-highlighting...")
            clone_cmd = (
                f"git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting.git "
                f"{highlighting_dir}"
            )
            if user != "root":
                clone_cmd = f'su - {user} -c "{clone_cmd}"'
            self.run(clone_cmd, check=False, timeout=120)

    def _install_eza(self) -> None:
        """Install eza (modern ls replacement)."""
        if self.command_exists("eza"):
            self.logger.info("  eza already installed, skipping")
            return

        self.logger.info("Installing eza...")

        # Add eza GPG key and repository
        self.run(
            "mkdir -p /etc/apt/keyrings",
            check=False,
        )

        self.run(
            "curl -fsSL https://raw.githubusercontent.com/eza-community/eza/main/deb.asc "
            "| gpg --dearmor -o /etc/apt/keyrings/eza.gpg",
            check=True,
            timeout=60,
        )

        self.run(
            'echo "deb [signed-by=/etc/apt/keyrings/eza.gpg] '
            'http://deb.gierens.de stable main" > /etc/apt/sources.list.d/eza.list',
            check=True,
        )

        self.run("chmod 644 /etc/apt/keyrings/eza.gpg", check=False)

        # Install eza
        self.install_packages_resilient(["eza"], update_cache=True)

        self.logger.info("✓ eza installed")

    def _install_bat(self) -> None:
        """Install bat (modern cat replacement)."""
        if self.command_exists("bat") or self.command_exists("batcat"):
            self.logger.info("  bat already installed, skipping")
            return

        self.logger.info("Installing bat...")

        # On Debian, the package is 'bat' but binary is 'batcat'
        self.install_packages_resilient(["bat"], update_cache=False)

        # Create symlink from bat to batcat if needed
        if self.command_exists("batcat") and not self.command_exists("bat"):
            self.run(
                "ln -sf /usr/bin/batcat /usr/local/bin/bat",
                check=False,
            )

        # Apply bat configuration
        self._apply_bat_config()

        self.logger.info("✓ bat installed")

    def _apply_bat_config(self) -> None:
        """Apply bat configuration."""
        config = self._get_tools_config().get("bat", {})

        config_dir = self._get_home_dir() / ".config" / "bat"
        config_dir.mkdir(parents=True, exist_ok=True)

        theme = config.get("theme", "TwoDark")
        show_line_numbers = config.get("line_numbers", True)

        config_content = f'''# Bat configuration
# Generated by debian-vps-configurator

--theme="{theme}"
{"--style=numbers,changes" if show_line_numbers else "--style=plain"}
--italic-text=always
--map-syntax "*.md:Markdown"
--map-syntax ".zshrc:Bourne Again Shell (bash)"
'''

        config_file = config_dir / "config"
        write_file(str(config_file), config_content)

        # Set ownership if not root
        user = self._get_target_user()
        if user != "root":
            self.run(f"chown -R {user}:{user} {config_dir}", check=False)

    def _install_zoxide(self) -> None:
        """Install zoxide (smarter cd)."""
        if self.command_exists("zoxide"):
            self.logger.info("  zoxide already installed, skipping")
            return

        self.logger.info("Installing zoxide...")

        user = self._get_target_user()

        # Install via official script
        install_cmd = (
            "curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh"
        )

        if user != "root":
            # Install to /usr/local/bin for system-wide access
            install_cmd = "curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh -s -- --bin-dir /usr/local/bin"

        self.run(install_cmd, check=True, timeout=120)

        self.logger.info("✓ zoxide installed")

    def _apply_zsh_config(self, config: Dict[str, Any]) -> None:
        """Apply zsh configuration with aliases and integrations."""
        self.logger.info("Applying zsh configuration...")

        user = self._get_target_user()
        home = self._get_home_dir()
        zshrc = home / ".zshrc"

        # Get plugin configuration
        zsh_config = config.get("zsh", {})
        plugins = zsh_config.get(
            "plugins",
            [
                "git",
                "docker",
                "sudo",
                "command-not-found",
                "colored-man-pages",
                "zsh-autosuggestions",
                "zsh-syntax-highlighting",
            ],
        )

        # Build .zshrc content
        zshrc_content = self._generate_zshrc(plugins, config)

        # Backup existing .zshrc
        if zshrc.exists():
            backup_path = (
                home / f".zshrc.pre-configurator.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            shutil.copy2(zshrc, backup_path)

        # Write new .zshrc
        write_file(str(zshrc), zshrc_content)

        # Set ownership
        if user != "root":
            self.run(f"chown {user}:{user} {zshrc}", check=False)

        # Set zsh as default shell if configured
        if zsh_config.get("set_default_shell", True):
            self._set_default_shell(user)

        self.logger.info("✓ zsh configuration applied")

    def _generate_zshrc(self, plugins: List[str], config: Dict[str, Any]) -> str:
        """Generate .zshrc content with all configurations.

        Implements Context7 best practices:
        - Lazy loading for heavy plugins (nvm)
        - compinit before zoxide init
        - EZA_ICONS_AUTO environment variable
        - Enhanced aliases with --group-directories-first
        """
        home = self._get_home_dir()
        ohmyzsh_dir = home / ".oh-my-zsh"

        # Build plugins string (syntax-highlighting must be last per Context7)
        if "zsh-syntax-highlighting" in plugins:
            plugins.remove("zsh-syntax-highlighting")
            plugins.append("zsh-syntax-highlighting")

        plugins_str = " ".join(plugins)

        # Get tool-specific configs
        eza_config = config.get("eza", {})
        bat_config = config.get("bat", {})
        zoxide_config = config.get("zoxide", {})
        zsh_config = config.get("zsh", {})

        # Build eza options (Context7: use env var + flags)
        eza_icons = "--icons" if eza_config.get("icons", True) else ""
        eza_git = "--git" if eza_config.get("git_integration", True) else ""
        eza_group_dirs = (
            "--group-directories-first" if eza_config.get("group_directories_first", True) else ""
        )
        eza_git_repos = "--git-repos" if eza_config.get("git_repos", False) else ""

        # Check if lazy loading is enabled (Context7 best practice)
        lazy_loading = zsh_config.get("lazy_loading", True)

        # Zoxide hook configuration (Context7: pwd hook is more efficient)
        zoxide_hook = zoxide_config.get("hook", "pwd")

        content = f'''# ~/.zshrc - Generated by debian-vps-configurator
# Generated at: {datetime.now().isoformat()}
# Best practices from Context7 documentation

# =============================================================================
# Oh-My-Zsh Configuration
# =============================================================================

export ZSH="{ohmyzsh_dir}"

# Theme (robbyrussell is fast and reliable)
ZSH_THEME="robbyrussell"

# Plugins
plugins=({plugins_str})

# Performance: Disable auto-update prompts
DISABLE_AUTO_UPDATE="true"
DISABLE_UPDATE_PROMPT="true"

# Context7 Best Practice: Lazy loading for heavy plugins
# This defers initialization until first use, improving startup by ~200ms
'''

        # Add lazy loading configuration if enabled (Context7)
        if lazy_loading and "nvm" in plugins:
            content += """zstyle ':omz:plugins:nvm' lazy yes
"""

        content += f"""
# Load Oh-My-Zsh
[ -f "$ZSH/oh-my-zsh.sh" ] && source "$ZSH/oh-my-zsh.sh"

# =============================================================================
# Environment Variables (Context7 Best Practices)
# =============================================================================

# Eza: Use environment variable for consistent icon display
export EZA_ICONS_AUTO=1

# Editor
export EDITOR="nano"
export VISUAL="nano"

# Path additions
export PATH="$HOME/.local/bin:$PATH"

# =============================================================================
# Completions (Context7: Must be before zoxide init)
# =============================================================================

# Initialize completion system
autoload -Uz compinit && compinit -C

# =============================================================================
# Terminal Tools Configuration
# =============================================================================

# Eza (modern ls) - Enhanced aliases with Context7 best practices
if command -v eza &> /dev/null; then
    alias ls='eza {eza_icons} {eza_git} {eza_group_dirs}'
    alias ll='eza -la {eza_icons} {eza_git} {eza_group_dirs}'
    alias la='eza -a {eza_icons} {eza_group_dirs}'
    alias lt='eza --tree --level=3 {eza_icons}'
    alias ltr='eza --tree {eza_git_repos}'  # Tree with git repo status
    alias l='eza -l {eza_icons} {eza_group_dirs}'
fi

# Bat (modern cat) - Context7 recommended style
if command -v bat &> /dev/null; then
    alias cat='bat --paging=never'
    alias catp='bat'  # With paging
    alias bathelp='bat --plain --language=help'  # For --help output
elif command -v batcat &> /dev/null; then
    alias cat='batcat --paging=never'
    alias bat='batcat'
    alias catp='batcat'
fi

# Zoxide (smarter cd) - Context7: Initialize after compinit
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh --hook {zoxide_hook})"
    alias j='z'      # Jump to directory
    alias ji='zi'    # Interactive jump
fi

# =============================================================================
# Shell Options
# =============================================================================

# History configuration (expanded for productivity)
HISTSIZE=50000
SAVEHIST=50000
HISTFILE=~/.zsh_history
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_SAVE_NO_DUPS
setopt HIST_REDUCE_BLANKS
setopt SHARE_HISTORY
setopt EXTENDED_HISTORY

# Better directory navigation
setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS
setopt PUSHD_SILENT

# Better completion
setopt COMPLETE_IN_WORD
setopt ALWAYS_TO_END
setopt MENU_COMPLETE

# Key bindings
bindkey -e  # Emacs-style bindings
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

# =============================================================================
# Welcome message
# =============================================================================

echo "Terminal tools loaded: eza, bat, zoxide (Context7 optimized)"
"""

        return content

    def _set_default_shell(self, user: str) -> None:
        """Set zsh as the default shell for user."""
        self.logger.info(f"  Setting zsh as default shell for {user}...")

        zsh_path = shutil.which("zsh")
        if not zsh_path:
            self.logger.warning("zsh not found in PATH, skipping shell change")
            return

        # Check if already using zsh
        result = self.run(f"getent passwd {user}", check=False)
        if result.success and zsh_path in result.stdout:
            self.logger.info("  zsh is already the default shell")
            return

        # Change shell
        self.run(f"chsh -s {zsh_path} {user}", check=False)
        self.logger.info(f"  Default shell changed to zsh for {user}")
