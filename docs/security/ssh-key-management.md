# SSH Key Management & Security Hardening

Automated SSH key lifecycle management for secure, password-free authentication.

## Quick Start

```bash
# Interactive setup (recommended)
vps-configurator ssh setup

# Generate new key
vps-configurator ssh generate-key --user johndoe --deploy

# Check status
vps-configurator ssh status
```

## Commands

### `ssh setup`

Interactive wizard for SSH security setup:

- Generates Ed25519 key pair
- Deploys key to authorized_keys
- Optionally disables password authentication
- Optionally disables root login

```bash
vps-configurator ssh setup --user johndoe
vps-configurator ssh setup --disable-password-auth --disable-root-login
```

### `ssh generate-key`

Generate a new SSH key pair:

```bash
vps-configurator ssh generate-key --user johndoe --key-id laptop --deploy
vps-configurator ssh generate-key --user johndoe --type rsa --rotation-days 180
```

Options:

- `--user, -u`: System username (required)
- `--key-id, -i`: Custom key identifier
- `--type`: Key type (ed25519, rsa)
- `--rotation-days`: Days until expiration (default: 90)
- `--deploy`: Deploy to authorized_keys

### `ssh rotate`

Rotate an existing key with grace period:

```bash
vps-configurator ssh rotate --user johndoe --key-id johndoe-laptop-2026-01-06
vps-configurator ssh rotate --user johndoe --key-id old-key --grace-days 14
```

During grace period, both old and new keys are valid.

### `ssh list-keys`

Show key inventory with status:

```bash
vps-configurator ssh list-keys
vps-configurator ssh list-keys --user johndoe
vps-configurator ssh list-keys --json
```

### `ssh revoke-key`

Revoke and remove a key:

```bash
vps-configurator ssh revoke-key --user johndoe --key-id old-key
```

### `ssh status`

Show SSH security status:

```bash
vps-configurator ssh status
vps-configurator ssh status --json
```

### `ssh harden`

Apply SSH security hardening:

```bash
vps-configurator ssh harden
```

## Key Rotation Policy

Default policy:

- **Rotation interval**: 90 days
- **Grace period**: 7 days (both keys valid)
- **Expiry warning**: 14 days before expiration

## Security Best Practices

1. **Use Ed25519 keys** - Modern, secure, fast
2. **Disable password auth** - Eliminates brute-force attacks
3. **Disable root login** - Use sudo instead
4. **Rotate keys regularly** - 90-day policy recommended
5. **Remove stale keys** - Check with `ssh list-keys`

## Troubleshooting

### Cannot connect after disabling password auth

1. Ensure your public key is in `~/.ssh/authorized_keys`
2. Check file permissions: `chmod 600 ~/.ssh/authorized_keys`
3. Verify SSH config: `ssh -v user@server`

### Key generation fails

- Ensure user exists: `id username`
- Check SSH directory: `ls -la ~/.ssh`
- Verify permissions: SSH dir must be 700

### Restoring password auth (emergency)

```bash
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl reload sshd
```
