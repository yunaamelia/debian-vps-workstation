# Security Guide

This document outlines the security features and best practices for the Debian VPS Configurator.

## Secrets Management

We provide a built-in Secrets Manager to securely store sensitive information such as passwords, API keys, and certificates.

### Encryption

Secrets are encrypted using **Fernet** (symmetric encryption) from the `cryptography` library. The encryption key is derived from a **Master Password** using **PBKDF2HMAC** with SHA256 and a 32-byte salt.

- **Storage**: Encrypted secrets are stored in `/var/lib/debian-vps-configurator/secrets.json`.
- **Permissions**: The storage file is restricted to read/write only by the owner (0600).
- **Master Password**:
  - Can be provided via the `DVPS_MASTER_PASSWORD` environment variable.
  - If not provided, a random master password is auto-generated and stored in `/root/.dvps_master_pass` (only readable by root).

### Usage

You can manage secrets using the CLI:

```bash
# Store a secret
vps-configurator secrets set database_password
# You will be prompted to enter the password securely

# Retrieve a secret
vps-configurator secrets get database_password

# List all secrets
vps-configurator secrets list

# Delete a secret
vps-configurator secrets delete database_password
```

### Integration

The **RBAC (Role-Based Access Control)** module automatically uses the Secrets Manager to store generated user passwords. When a new user is created with a temporary password, that password is secure saved in the secrets store under the key `user_password_<username>`.

## Network Security

- **UFW (Uncomplicated Firewall)**: Enabled by default. Incoming traffic is denied by default, except for SSH (rate-limited) and specific allowed ports.
- **Fail2Ban**: Monitors SSH logs to ban IPs that show malicious signs like too many password failures.
- **SSH Hardening**: Root password login is disabled by default. SSH key authentication is encouraged.

## System Security

- **Auto-Updates**: Unattended upgrades are enabled to ensure security patches are applied automatically.
- **File Permissions**: Critical configuration files are created with restricted permissions.

## Security Audit Logging

All security-relevant events are logged to an immutable, append-only JSON Lines file for compliance and forensics.

- **Location**: `/var/log/debian-vps-configurator/audit.jsonl`
- **Format**: JSON Lines (structured logging)
- **Permissions**: 0600 (owner read-write only)

### Logged Events

- Installation start/complete
- User creation/deletion
- Firewall rule addition/deletion
- SSH configuration changes
- Package installation
- Service start/stop
- Security violations

### Querying Logs

Use the CLI to query audit logs:

```bash
# View last 20 events
vps-configurator audit query

# Filter by event type
vps-configurator audit query --type user_create

# Limit results
vps-configurator audit query --limit 50
```

## File Integrity Monitoring (FIM)

The system monitors critical configuration files for unauthorized changes, similar to tools like Tripwire or AIDE.

### Monitored Files

By default, the following files are monitored for changes in hash, size, modification time, permissions, and ownership:

- `/etc/ssh/sshd_config`
- `/etc/sudoers`
- `/etc/passwd`, `/etc/shadow`, `/etc/group`
- `/etc/ufw/user.rules`
- `/etc/fail2ban/jail.local`
- `/etc/xrdp/xrdp.ini`

### Usage

```bash
# Check for integrity violations (changes since baseline)
vps-configurator fim check

# Initialize/Reset baseline (done automatically on install)
vps-configurator fim init

# Update baseline for specific file (after authorized changes)
vps-configurator fim update /etc/ssh/sshd_config
```

### Automation

A systemd service (`file-integrity-check.service`) and timer run a daily check automatically. Violations are logged to the audit log.
