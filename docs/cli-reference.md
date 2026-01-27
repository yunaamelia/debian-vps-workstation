# CLI Reference

The `vps-configurator` CLI tool provides a comprehensive interface for managing your Debian VPS.

## Core Commands

### `install`

Run the automated installation process.

**Usage:**

```bash
vps-configurator install [OPTIONS]
```

**Options:**

- `--dry-run`: Simulate the installation without making changes. Shows a report of actions.
- `--skip-validation`: Skip system prerequisite checks.
- `--profile [beginner|intermediate|advanced]`: Select configuration profile.
- `--config <path>`: Path to custom configuration file.

### `wizard`

Launch the interactive Textual-based TUI wizard for guided setup.

**Usage:**

```bash
vps-configurator wizard
```

### `verify`

Verify the current system configuration against established requirements.

**Usage:**

```bash
vps-configurator verify
```

## Security Commands

### `secrets`

Manage secure secrets (passwords, keys).

**Subcommands:**

- `set <key>`:  Set a secret value (prompts securely).
- `get <key>`:  Retrieve and display a secret.
- `list`:       List all stored secret keys.
- `delete <key>`: Remove a secret.

**Example:**

```bash
vps-configurator secrets set api_key
```

### `audit`

Query the security audit log.

**Usage:**

```bash
vps-configurator audit query [OPTIONS]
```

**Options:**

- `--type <type>`: Filter by event type (e.g., `user_create`, `ssh_attempt`).
- `--limit <n>`:   Limit results (default: 50).

### `fim`

File Integrity Monitoring commands.

**Subcommands:**

- `init`:   Initialize or reset the file integrity baseline.
- `check`:  Check monitored files for unauthorized changes.
- `update <file>`: Update the baseline for a specific file (authorize change).

**Example:**

```bash
# Check for changes
vps-configurator fim check
# Update baseline after editing ssh config
vps-configurator fim update /etc/ssh/sshd_config
```

## Utility Commands

### `rollback`

Rollback the last installation attempt.

**Usage:**

```bash
vps-configurator rollback
```

### `plugin`

Manage plugins.

**Subcommands:**

- `list`: List available plugins.
- `install <path/url>`: Install a plugin.
