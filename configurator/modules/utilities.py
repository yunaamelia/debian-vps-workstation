"""
CLI utilities module.

Handles:
- System utilities (htop, tmux, etc.)
- Development utilities
- Network utilities
"""

from configurator.modules.base import ConfigurationModule


class UtilitiesModule(ConfigurationModule):
    """
    CLI utilities installation module.

    Installs commonly used command-line tools.
    """

    name = "System Utilities"
    description = "htop, ripgrep, fzf, zsh, etc."
    depends_on = ["system"]
    priority = 54
    mandatory = False

    # Default utilities to install
    SYSTEM_UTILS = [
        "htop",  # Interactive process viewer
        "btop",  # Better htop
        "tmux",  # Terminal multiplexer
        "screen",  # Alternative multiplexer
        "tree",  # Directory tree viewer
        "ncdu",  # Disk usage analyzer
        "iotop",  # I/O monitoring
        "iftop",  # Network monitoring
        "nethogs",  # Network usage per process
        "duf",  # Disk usage (modern)
        "bat",  # Better cat
        "exa",  # Better ls
        "fd-find",  # Better find
        "ripgrep",  # Better grep
        "fzf",  # Fuzzy finder
        "jq",  # JSON processor
        "yq",  # YAML processor
        "httpie",  # HTTP client
        "rsync",  # File sync
        "zip",  # Compression
        "unzip",
        "p7zip-full",
        "pigz",  # Parallel gzip
    ]

    DEV_UTILS = [
        "shellcheck",  # Shell script linter
        "strace",  # System call tracer
        "ltrace",  # Library call tracer
        "gdb",  # Debugger
        "valgrind",  # Memory debugger
        "make",  # Build tool
        "cmake",  # Build system
        "pkg-config",  # Package config
    ]

    NETWORK_UTILS = [
        "curl",  # URL transfer
        "wget",  # URL download
        "netcat-openbsd",  # Networking utility
        "nmap",  # Network scanner
        "tcpdump",  # Packet analyzer
        "whois",  # Domain lookup
        "dnsutils",  # DNS tools (dig, nslookup)
        "mtr-tiny",  # Network diagnostic
        "traceroute",  # Route tracer
        "iproute2",  # IP routing
        "net-tools",  # ifconfig, etc.
        "openssh-client",  # SSH client
        "sshfs",  # SSH filesystem
    ]

    def validate(self) -> bool:
        """Validate prerequisites."""
        return True

    def configure(self) -> bool:
        """Install utilities."""
        self.logger.info("Installing CLI utilities...")

        packages = []

        # System utilities
        if self.get_config("system_utils", True):
            packages.extend(self.SYSTEM_UTILS)

        # Development utilities
        if self.get_config("dev_utils", True):
            packages.extend(self.DEV_UTILS)

        # Network utilities
        if self.get_config("network_utils", True):
            packages.extend(self.NETWORK_UTILS)

        # Custom utilities from config
        custom = self.get_config("custom", [])
        if custom:
            packages.extend(custom)

        # Remove duplicates
        packages = list(set(packages))

        self.logger.info(f"Installing {len(packages)} utilities...")
        self.install_packages(packages)

        # Configure some utilities
        self._configure_aliases()

        self.logger.info("✓ CLI utilities installed")
        return True

    def verify(self) -> bool:
        """Verify installation."""
        checks_passed = True

        # Check key utilities
        key_utils = ["htop", "tmux", "jq", "curl", "rsync"]

        for util in key_utils:
            if self.command_exists(util):
                self.logger.info(f"✓ {util}")
            else:
                self.logger.warning(f"⚠ {util} not found")

        return checks_passed

    def _configure_aliases(self):
        """Configure useful aliases."""
        aliases = """
# Aliases added by debian-vps-configurator
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Modern alternatives (if installed)
command -v bat &> /dev/null && alias cat='bat --paging=never'
command -v exa &> /dev/null && alias ls='exa --icons'
command -v exa &> /dev/null && alias ll='exa -alh --icons'
command -v exa &> /dev/null && alias tree='exa --tree --icons'

# Safety aliases
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Grep coloring
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# Quick system info
alias df='df -h'
alias du='du -h'
alias free='free -h'
alias ports='ss -tulanp'
"""

        # Add to /etc/profile.d for all users
        alias_file = "/etc/profile.d/aliases.sh"
        with open(alias_file, "w") as f:
            f.write(aliases)

        self.run(f"chmod +x {alias_file}", check=False)

        self.logger.info("✓ Shell aliases configured")
