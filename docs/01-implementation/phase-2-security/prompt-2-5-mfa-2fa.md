# PROMPT 2.5: MFA/2FA SYSTEM IMPLEMENTATION

## 📋 Context

For privileged access (Sudo, SSH), single factor authentication is insufficient.
We need to integrate TOTP (Time-Based One-Time Password) using `libpam-google-authenticator`.

## 🎯 Objective

Implement `MFAManager` in `configurator/security/mfa_manager.py`.

## 🛠️ Requirements

### Functional

1. **Setup**: Install `libpam-google-authenticator`.
2. **User Enrollment**: Generate secret, QR code, and scratch codes for a user.
3. **PAM Configuration**:
    - Edit `/etc/pam.d/sshd` and `/etc/pam.d/sudo`.
    - Enforce MFA requirement.
4. **SSH Integration**: Update `sshd_config` (`ChallengeResponseAuthentication yes`).

## 📝 Specifications

### Class Signature (`configurator/security/mfa_manager.py`)

```python
class MFAManager:
    def install_dependencies(self):
        pass

    def enroll_user(self, user: str) -> Dict[str, Any]:
        """
        Runs google-authenticator for user.
        Returns: {
            "secret": "...",
            "qr_code_url": "...",
            "scratch_codes": [...]
        }
        """
        pass

    def enable_for_service(self, service: str = "ssh"):
        pass
```

## 🪜 Implementation Steps

1. **Dependency**: `apt-get install libpam-google-authenticator`.
2. **Enrollment**:
    - Run `google-authenticator` non-interactively via flags (time-based, disallow-reuse, force, rate-limit).
    - Capture output to parse secret/codes.
    - Save to `~/.google_authenticator`.
3. **PAM Editing**:
    - Insert `auth required pam_google_authenticator.so` line in PAM files.

## 🔍 Validation Checklist

- [ ] User directory has `.google_authenticator` file.
- [ ] PAM files contain the module line.
- [ ] SSH config has `ChallengeResponseAuthentication yes`.

---

**Output**: Python code for `configurator/security/mfa_manager.py`.
