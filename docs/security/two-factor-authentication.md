# Two-Factor Authentication (2FA/MFA)

Multi-factor authentication for enhanced SSH and system access security.

## Quick Start

```bash
# Enroll a user
vps-configurator mfa setup --user johndoe

# Verify code
vps-configurator mfa verify --user johndoe --code 123456

# Check status
vps-configurator mfa status
```

## Commands

### `mfa setup`

Interactive 2FA enrollment with QR code:

```bash
vps-configurator mfa setup --user johndoe
```

Steps:

1. Generates TOTP secret
2. Displays QR code (scan with authenticator app)
3. Verifies initial code
4. Provides 10 backup codes

### `mfa status`

View MFA status:

```bash
vps-configurator mfa status              # Summary
vps-configurator mfa status --user john  # User details
vps-configurator mfa status --json       # JSON output
```

### `mfa verify`

Test code verification:

```bash
vps-configurator mfa verify --user johndoe --code 123456
```

### `mfa disable`

Disable 2FA for a user:

```bash
vps-configurator mfa disable --user johndoe --backup-code AAAA-BBBB-CCCC
vps-configurator mfa disable --user johndoe --force  # Admin only
```

### `mfa regenerate-backup-codes`

Generate new backup codes:

```bash
vps-configurator mfa regenerate-backup-codes --user johndoe
```

### `mfa unlock`

Unlock locked account (after 5 failed attempts):

```bash
vps-configurator mfa unlock --user johndoe
```

### `mfa enable-pam`

Enable PAM integration for SSH/sudo:

```bash
vps-configurator mfa enable-pam          # SSH only
vps-configurator mfa enable-pam --sudo   # SSH + sudo
```

## Supported Authenticator Apps

- Google Authenticator (iOS/Android)
- Microsoft Authenticator (iOS/Android)
- Authy (iOS/Android)
- FreeOTP (iOS/Android)
- Any TOTP-compatible app

## Security Features

- **TOTP** - Time-based codes (30 second window)
- **Backup Codes** - 10 one-time emergency codes
- **Lockout** - Account locks after 5 failed attempts
- **PAM Integration** - Works with SSH and sudo

## Emergency Access

If you lose your authenticator device:

1. Use a backup code:

   ```bash
   # During SSH login, enter backup code instead of TOTP
   Verification code: AAAA-BBBB-CCCC
   ```

2. Disable MFA with backup code:

   ```bash
   vps-configurator mfa disable --user johndoe --backup-code AAAA-BBBB-CCCC
   ```

3. Re-enroll:

   ```bash
   vps-configurator mfa setup --user johndoe
   ```

## Troubleshooting

### "Invalid code" errors

- Check time sync on both devices
- Ensure 30-second window alignment
- Try next code if on boundary

### Account locked

```bash
# Unlock (requires root)
vps-configurator mfa unlock --user johndoe
```
