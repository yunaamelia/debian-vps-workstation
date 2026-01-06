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
    def validate_hostname(cls, v):
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
    def security_must_be_enabled(cls, v):
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


class MonitoringConfig(BaseModel):
    netdata: EnabledConfig = Field(default_factory=EnabledConfig)


class Config(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    languages: LanguagesConfig = Field(default_factory=LanguagesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    networking: NetworkingConfig = Field(default_factory=NetworkingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    interactive: bool = True
    verbose: bool = False
    dry_run: bool = False
