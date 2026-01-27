# CLI Command Reference

Complete reference for all `vps-configurator` commands.

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--verbose, -v` | Enable verbose output |
| `--quiet, -q` | Suppress output |
| `--config PATH` | Use custom config file |
| `--version` | Show version and exit |
| `--help` | Show help message |

## Commands

### `vps-configurator activity`

User activity monitoring and auditing.

**Syntax:**

```bash
vps-configurator activity
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator audit`

Query security audit logs.

**Syntax:**

```bash
vps-configurator audit
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator cache`

Manage package cache.

**Syntax:**

```bash
vps-configurator cache
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator cert`

SSL/TLS certificate management with Let's Encrypt.

**Syntax:**

```bash
vps-configurator cert
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator cis`

Security compliance and hardening based on CIS Benchmarks.

**Syntax:**

```bash
vps-configurator cis
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator dashboard`

Launch TUI dashboard for installation monitoring.

Provides a full-screen terminal UI with:

- Real-time module status
- System resource monitoring
- Activity log
- Keyboard controls (p=pause, r=resume, q=quit)

Requires: textual (pip install textual)

**Syntax:**

```bash
vps-configurator dashboard [DEMO]
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--demo` | boolean | Run dashboard in demo mode with mock data | `False` |

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator fim`

File Integrity Monitoring.

**Syntax:**

```bash
vps-configurator fim
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator install`

Install and configure the workstation.

Examples:

# Interactive wizard (recommended for beginners)

  vps-configurator wizard

# Quick install with beginner profile

  vps-configurator install --profile beginner -y

# Install with custom config

  vps-configurator install --config myconfig.yaml -y

**Syntax:**

```bash
vps-configurator install [PROFILE] [CONFIG] [NON_INTERACTIVE] [SKIP_VALIDATION] [DRY_RUN] [NO_PARALLEL] [PARALLEL_WORKERS] [VERBOSE]
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--profile`, `-p` | choice | Installation profile to use | - |
| `--config`, `-c` | path | Path to custom configuration file | - |
| `--non-interactive`, `-y` | boolean | Run without prompts (use with --profile or --config) | `False` |
| `--skip-validation` | boolean | Skip system validation checks | `False` |
| `--dry-run` | boolean | Show what would be done without making changes | `False` |
| `--no-parallel` | boolean | Disable parallel module execution | `False` |
| `--parallel-workers` | integer | Number of workers for parallel execution | `3` |
| `--verbose`, `-v` | boolean | Enable verbose output | `False` |

**Examples:**

```bash
# Interactive wizard
vps-configurator install --wizard

# Use beginner profile
vps-configurator install --profile beginner

# Dry run (preview without installing)
vps-configurator install --profile advanced --dry-run
```

**See also:**

- [`wizard`](#vps-configurator-wizard)
- [`verify`](#vps-configurator-verify)
- [`profiles`](#vps-configurator-profiles)
- [`visualize`](#vps-configurator-visualize)

---

### `vps-configurator mfa`

Two-factor authentication (2FA/MFA) management.

**Syntax:**

```bash
vps-configurator mfa
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator monitoring`

Monitoring and observability commands.

**Syntax:**

```bash
vps-configurator monitoring
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator plugin`

Manage external plugins.

**Syntax:**

```bash
vps-configurator plugin
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator profiles`

List available installation profiles.

**Syntax:**

```bash
vps-configurator profiles
```

**Examples:**

```bash
# List available profiles
vps-configurator profiles

# Inspect a profile
vps-configurator profiles inspect beginner
```

**See also:**

- [`install`](#vps-configurator-install)
- [`visualize`](#vps-configurator-visualize)

---

### `vps-configurator rbac`

Manage RBAC roles, assignments, and permission checks.

**Syntax:**

```bash
vps-configurator rbac
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator reset`

Reset a resource (e.g., circuit breaker).

**Syntax:**

```bash
vps-configurator reset
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator rollback`

Rollback installation changes.

Undoes changes made during the installation process.
Use with caution!

**Syntax:**

```bash
vps-configurator rollback [DRY_RUN] [FORCE]
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--dry-run` | boolean | Show what would be rolled back without making changes | `False` |
| `--force`, `-f` | boolean | Skip confirmation prompt | `False` |

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator secrets`

Manage encrypted secrets.

**Syntax:**

```bash
vps-configurator secrets
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator ssh`

SSH key management and security hardening.

**Syntax:**

```bash
vps-configurator ssh
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator status`

Check system status.

**Syntax:**

```bash
vps-configurator status
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator sudo`

Manage sudo policies (fine-grained access control).

**Syntax:**

```bash
vps-configurator sudo
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator team`

Team and group management.

**Syntax:**

```bash
vps-configurator team
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator temp-access`

Temporary access and time-based permissions.

**Syntax:**

```bash
vps-configurator temp-access
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator user`

Manage user lifecycle (create, offboard, suspend).

**Syntax:**

```bash
vps-configurator user
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator verify`

Verify the installation.

Checks that all installed components are working correctly.

**Syntax:**

```bash
vps-configurator verify [PROFILE] [CONFIG]
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--profile`, `-p` | choice | Profile that was used for installation | - |
| `--config`, `-c` | path | Path to configuration file used for installation | - |

**Examples:**

```bash
# Verify all installed modules
vps-configurator verify

# Verify specific module
vps-configurator verify --module docker
```

**See also:**

- [`install`](#vps-configurator-install)
- [`visualize`](#vps-configurator-visualize)

---

### `vps-configurator visualize`

Visualize dependencies for a profile.

Displays the dependency tree or exports it to Mermaid format.
If no profile is specified, uses the 'beginner' profile by default.

**Syntax:**

```bash
vps-configurator visualize [PROFILE] [FORMAT] [OUTPUT]
```

**Options:**

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `-p`, `--profile` | text | Profile to visualize (e.g., beginner, fullstack) | `Sentinel.UNSET` |
| `-f`, `--format` | choice | Output format | `ascii` |
| `-o`, `--output` | path | Output file for mermaid export | `Sentinel.UNSET` |

**Examples:**

```bash
# Visualize default profile
vps-configurator visualize

# Export to Mermaid file
vps-configurator visualize --profile fullstack --format mermaid-file -o graph.mmd
```

**See also:**

- [`install`](#vps-configurator-install)
- [`profiles`](#vps-configurator-profiles)

---

### `vps-configurator vuln`

Vulnerability scanning and management.

**Syntax:**

```bash
vps-configurator vuln
```

**Examples:**

```bash
```

**See also:**

---

### `vps-configurator wizard`

Run the interactive setup wizard.

Guides you through the configuration process
with beginner-friendly prompts.

**Syntax:**

```bash
vps-configurator wizard
```

**Examples:**

```bash
# Launch interactive wizard
vps-configurator wizard
```

**See also:**

- [`install`](#vps-configurator-install)
- [`profiles`](#vps-configurator-profiles)

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid usage |
| 3 | Validation failed |
| 4 | Installation failed |
| 130 | Interrupted by user (Ctrl+C) |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VPS_CONFIG_FILE` | Default config file path | `config/default.yaml` |
| `VPS_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `VPS_NO_COLOR` | Disable colored output | `false` |
