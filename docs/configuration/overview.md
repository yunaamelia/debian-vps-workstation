# Configuration Reference

Complete reference for all configuration options in the Debian VPS Workstation Configurator.

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [System Configuration](#system-configuration)
3. [Security Configuration](#security-configuration)
4. [Desktop Configuration](#desktop-configuration)
5. [Programming Languages](#programming-languages)
6. [Development Tools](#development-tools)
7. [Networking](#networking)
8. [Monitoring](#monitoring)
9. [Example Configurations](#example-configurations)

---

## Configuration Files

### File Locations

| File | Purpose |
|------|---------|
| `config/default.yaml` | Default values for all options |
| `config/profiles/beginner.yaml` | Beginner profile overrides |
| `config/profiles/intermediate.yaml` | Intermediate profile overrides |
| `config/profiles/advanced.yaml` | Advanced profile overrides |
| Custom file | Your custom configuration |

### Load Order

Configuration is loaded in this order (later overrides earlier):

1. Built-in defaults (in code)
2. `config/default.yaml`
3. Profile file (if specified)
4. Custom config file (if specified)
5. Command-line arguments

### File Format

All configuration files use YAML format:

```yaml
# Comments start with #
key: value

nested:
  key: value

list:
  - item1
  - item2
```

---

## System Configuration

### `system.hostname`

**Type:** string
**Default:** `dev-workstation`
**Validation:** lowercase alphanumeric with hyphens, max 63 chars

Sets the server's hostname.

```yaml
system:
  hostname: my-coding-server
```

---

### `system.timezone`

**Type:** string
**Default:** `UTC`

Sets the system timezone. Use IANA timezone names.

```yaml
system:
  timezone: Asia/Jakarta
```

Common values:

- `UTC`
- `America/New_York`
- `America/Los_Angeles`
- `Europe/London`
- `Europe/Berlin`
- `Asia/Tokyo`
- `Asia/Singapore`
- `Asia/Jakarta`

---

### `system.locale`

**Type:** string
**Default:** `en_US.UTF-8`

Sets the system locale.

```yaml
system:
  locale: en_US.UTF-8
```

---

### `system.swap_size_gb`

**Type:** integer
**Default:** `2`
**Range:** 0-16

Size of swap file to create in GB. Set to 0 to disable.

```yaml
system:
  swap_size_gb: 4
```

---

### `system.kernel_tuning`

**Type:** boolean
**Default:** `true`

Enable kernel parameter tuning for better performance.

```yaml
system:
  kernel_tuning: true
```

Tuned parameters include:

- `vm.swappiness`
- `fs.file-max`
- `fs.inotify.max_user_watches`
- TCP optimization settings
- BBR congestion control

---

## Security Configuration

> ⚠️ **Security is MANDATORY** and cannot be disabled.

### `security.enabled`

**Type:** boolean
**Default:** `true`
**Override:** Cannot be set to `false`

```yaml
security:
  enabled: true  # Cannot change
```

---

### `security.ufw`

UFW Firewall settings.

```yaml
security:
  ufw:
    enabled: true
    default_incoming: deny
    default_outgoing: allow
    ssh_port: 22
    ssh_rate_limit: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable UFW firewall |
| `default_incoming` | string | `deny` | Default policy for incoming |
| `default_outgoing` | string | `allow` | Default policy for outgoing |
| `ssh_port` | integer | `22` | SSH port number |
| `ssh_rate_limit` | boolean | `true` | Enable rate limiting on SSH |

---

### `security.fail2ban`

Fail2ban intrusion prevention settings.

```yaml
security:
  fail2ban:
    enabled: true
    ssh_max_retry: 5
    ssh_ban_time: 3600
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable fail2ban |
| `ssh_max_retry` | integer | `5` | Max failed logins before ban |
| `ssh_ban_time` | integer | `3600` | Ban duration in seconds |

---

### `security.ssh`

SSH hardening settings.

```yaml
security:
  ssh:
    disable_root_password: true
    disable_password_auth: false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `disable_root_password` | boolean | `true` | Disable root password login (keys only) |
| `disable_password_auth` | boolean | `false` | Disable all password auth (SSH keys only) |

> ⚠️ Only set `disable_password_auth: true` if you have SSH keys configured!

---

### `security.auto_updates`

**Type:** boolean
**Default:** `true`

Enable automatic security updates.

```yaml
security:
  auto_updates: true
```

---

## Desktop Configuration

### `desktop.enabled`

**Type:** boolean
**Default:** `true`

Enable remote desktop installation.

```yaml
desktop:
  enabled: true
```

---

### `desktop.xrdp_port`

**Type:** integer
**Default:** `3389`

RDP port number.

```yaml
desktop:
  xrdp_port: 3389
```

---

### `desktop.environment`

**Type:** string
**Default:** `xfce4`

Desktop environment to install.

```yaml
desktop:
  environment: xfce4
```

Currently supported: `xfce4` only.

---

## Programming Languages

### Python

```yaml
languages:
  python:
    enabled: true
    version: system  # Uses Debian's Python
    dev_tools:
      - black
      - pylint
      - mypy
      - pytest
      - ipython
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Python setup |
| `version` | string | `system` | Python version (only `system` supported) |
| `dev_tools` | list | See default | Python development tools to install |

---

### Node.js

```yaml
languages:
  nodejs:
    enabled: true
    version: "20"
    use_nvm: true
    package_managers:
      - npm
      - yarn
      - pnpm
    global_packages:
      - typescript
      - ts-node
      - nodemon
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Node.js setup |
| `version` | string | `"20"` | Node.js version (LTS recommended) |
| `use_nvm` | boolean | `true` | Use nvm for version management |
| `package_managers` | list | `[npm, yarn, pnpm]` | Package managers to install |
| `global_packages` | list | See default | Global npm packages |

---

### Go (Golang)

```yaml
languages:
  golang:
    enabled: false
    version: "1.22"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable Go setup |
| `version` | string | `"1.22"` | Go version |

---

### Rust

```yaml
languages:
  rust:
    enabled: false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable Rust setup (via rustup) |

---

### Java

```yaml
languages:
  java:
    enabled: false
    jdk: openjdk-17
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable Java setup |
| `jdk` | string | `openjdk-17` | JDK package to install |

---

### PHP

```yaml
languages:
  php:
    enabled: false
    version: "8.2"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable PHP setup |
| `version` | string | `"8.2"` | PHP version |

---

## Development Tools

### Docker

```yaml
tools:
  docker:
    enabled: true
    compose: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Docker installation |
| `compose` | boolean | `true` | Include Docker Compose plugin |

---

### Git

```yaml
tools:
  git:
    enabled: true
    github_cli: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Git installation |
| `github_cli` | boolean | `true` | Install GitHub CLI (gh) |

---

### Editors

#### VS Code

```yaml
tools:
  editors:
    vscode:
      enabled: true
      extensions:
        - ms-python.python
        - dbaeumer.vscode-eslint
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable VS Code installation |
| `extensions` | list | See default | Extensions to install |

#### Cursor

```yaml
tools:
  editors:
    cursor:
      enabled: false
```

#### Neovim

```yaml
tools:
  editors:
    neovim:
      enabled: false
```

---

## Networking

### WireGuard VPN

```yaml
networking:
  wireguard:
    enabled: false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable WireGuard installation |

---

### Caddy

```yaml
networking:
  caddy:
    enabled: false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable Caddy reverse proxy |

---

## Monitoring

### Netdata

```yaml
monitoring:
  netdata:
    enabled: false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable Netdata monitoring |

---

## Example Configurations

### Minimal Web Development

```yaml
system:
  hostname: web-dev
  timezone: UTC

languages:
  python:
    enabled: false
  nodejs:
    enabled: true
    version: "20"

tools:
  docker:
    enabled: true
  git:
    enabled: true
  editors:
    vscode:
      enabled: true
```

### Python Data Science

```yaml
system:
  hostname: data-server
  swap_size_gb: 4

languages:
  python:
    enabled: true
    dev_tools:
      - black
      - pylint
      - jupyter
      - ipython
      - pandas
      - numpy
  nodejs:
    enabled: false

tools:
  docker:
    enabled: true
```

### Full Stack Development

```yaml
system:
  hostname: fullstack-dev
  timezone: Asia/Jakarta
  swap_size_gb: 4

languages:
  python:
    enabled: true
  nodejs:
    enabled: true
  golang:
    enabled: true

tools:
  docker:
    enabled: true
  git:
    enabled: true
    github_cli: true
  editors:
    vscode:
      enabled: true
    neovim:
      enabled: true

networking:
  caddy:
    enabled: true

monitoring:
  netdata:
    enabled: true
```

---

## Using Custom Configuration

Save your configuration to a file and use it:

```bash
# Create config
cat > myconfig.yaml << 'EOF'
system:
  hostname: my-server
  timezone: America/New_York

languages:
  python:
    enabled: true
  nodejs:
    enabled: true
EOF

# Run with custom config
sudo python -m configurator install --config myconfig.yaml -y
```
