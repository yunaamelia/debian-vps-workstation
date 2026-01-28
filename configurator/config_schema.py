from typing import List

from pydantic import BaseModel, Field, field_validator


class SystemConfig(BaseModel):
    hostname: str = Field(default="dev-workstation")
    timezone: str = Field(default="UTC")
    locale: str = Field(default="en_US.UTF-8")
    swap_size_gb: float = Field(default=2, ge=0)
    kernel_tuning: bool = Field(default=True)

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        import re

        if not re.match(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", v):
            raise ValueError("Hostname must be lowercase alphanumeric with optional hyphens")
        return v


class UFWConfig(BaseModel):
    enabled: bool = True
    default_incoming: str = Field(default="deny")
    default_outgoing: str = Field(default="allow")
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_rate_limit: bool = True


class Fail2BanConfig(BaseModel):
    enabled: bool = True
    ssh_max_retry: int = Field(default=5, ge=1)
    ssh_ban_time: int = Field(default=3600, ge=1)


class SSHConfig(BaseModel):
    disable_root_password: bool = True
    disable_password_auth: bool = False


class SecurityConfig(BaseModel):
    enabled: bool = True
    ufw: UFWConfig = Field(default_factory=UFWConfig)
    fail2ban: Fail2BanConfig = Field(default_factory=Fail2BanConfig)
    ssh: SSHConfig = Field(default_factory=SSHConfig)
    auto_updates: bool = True

    @field_validator("enabled")
    @classmethod
    def security_must_be_enabled(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Security module cannot be disabled")
        return v


class DesktopConfig(BaseModel):
    enabled: bool = True
    xrdp_port: int = Field(default=3389, ge=1, le=65535)
    environment: str = Field(default="xfce4")


class PythonConfig(BaseModel):
    enabled: bool = True
    version: str = Field(default="system")
    dev_tools: List[str] = Field(default=["black", "pylint", "mypy", "pytest", "ipython"])


class NodeJSConfig(BaseModel):
    enabled: bool = True
    version: str = Field(default="20")
    use_nvm: bool = True
    package_managers: List[str] = Field(default=["npm", "yarn", "pnpm"])


class EnabledConfig(BaseModel):
    enabled: bool = False


class LanguagesConfig(BaseModel):
    python: PythonConfig = Field(default_factory=PythonConfig)
    nodejs: NodeJSConfig = Field(default_factory=NodeJSConfig)
    golang: EnabledConfig = Field(default_factory=EnabledConfig)
    rust: EnabledConfig = Field(default_factory=EnabledConfig)
    java: EnabledConfig = Field(default_factory=EnabledConfig)
    php: EnabledConfig = Field(default_factory=EnabledConfig)


class DockerConfig(BaseModel):
    enabled: bool = True
    compose: bool = True


class GitConfig(BaseModel):
    enabled: bool = True
    github_cli: bool = True


class EditorsConfig(BaseModel):
    vscode: EnabledConfig = Field(default_factory=lambda: EnabledConfig(enabled=True))
    cursor: EnabledConfig = Field(default_factory=EnabledConfig)
    neovim: EnabledConfig = Field(default_factory=EnabledConfig)


class ToolsConfig(BaseModel):
    docker: DockerConfig = Field(default_factory=DockerConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    editors: EditorsConfig = Field(default_factory=EditorsConfig)


class NetworkingConfig(BaseModel):
    wireguard: EnabledConfig = Field(default_factory=EnabledConfig)
    caddy: EnabledConfig = Field(default_factory=EnabledConfig)


# =============================================================================
# Terminal Tools Configuration (Context7 Best Practices)
# =============================================================================


class EzaConfig(BaseModel):
    """Eza (modern ls) configuration - Context7 best practices."""

    enabled: bool = True
    icons: bool = True
    git_integration: bool = True
    git_repos: bool = False
    group_directories_first: bool = True
    color_scale: bool = False
    time_style: str = Field(default="long-iso")


class BatConfig(BaseModel):
    """Bat (modern cat) configuration - Context7 best practices."""

    enabled: bool = True
    theme: str = Field(default="TwoDark")
    line_numbers: bool = True
    style: str = Field(default="numbers,changes,header")
    italic_text: bool = True


class ZshPluginsConfig(BaseModel):
    """Zsh plugin configuration with categorization."""

    core: List[str] = Field(default=["git", "sudo", "command-not-found", "colored-man-pages"])
    productivity: List[str] = Field(default=["zsh-autosuggestions"])
    syntax: List[str] = Field(default=["zsh-syntax-highlighting"])
    lazy_load: List[str] = Field(default=["nvm"])


class ZshConfig(BaseModel):
    """Zsh shell configuration - Context7 best practices."""

    enabled: bool = True
    framework: str = Field(default="oh-my-zsh")
    theme: str = Field(default="robbyrussell")
    plugins: List[str] = Field(
        default=[
            "git",
            "docker",
            "sudo",
            "command-not-found",
            "colored-man-pages",
            "zsh-autosuggestions",
            "zsh-syntax-highlighting",
        ]
    )
    lazy_loading: bool = True
    set_default_shell: bool = True


class ZoxideConfig(BaseModel):
    """Zoxide (smart cd) configuration - Context7 best practices."""

    enabled: bool = True
    interactive_mode: bool = True
    hook: str = Field(default="pwd")  # pwd or prompt
    exclude_dirs: List[str] = Field(default=["/tmp", "/var/tmp"])


class TerminalToolsConfig(BaseModel):
    """Terminal tools configuration with Context7 best practices."""

    eza: EzaConfig = Field(default_factory=EzaConfig)
    bat: BatConfig = Field(default_factory=BatConfig)
    zsh: ZshConfig = Field(default_factory=ZshConfig)
    zoxide: ZoxideConfig = Field(default_factory=ZoxideConfig)


class MonitoringConfig(BaseModel):
    netdata: EnabledConfig = Field(default_factory=EnabledConfig)


class Config(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    languages: LanguagesConfig = Field(default_factory=LanguagesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    networking: NetworkingConfig = Field(default_factory=NetworkingConfig)
    terminal_tools: TerminalToolsConfig = Field(default_factory=TerminalToolsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    interactive: bool = True
    verbose: bool = False
    dry_run: bool = False
