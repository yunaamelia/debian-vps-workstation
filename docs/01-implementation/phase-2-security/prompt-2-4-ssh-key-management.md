# PROMPT 2.4: SSH KEY MANAGEMENT IMPLEMENTATION

## 📋 Context

Password authentication for SSH is insecure. We mandate Key-based auth.
We need a manager to generate, deploy, and rotate SSH keys for users.

## 🎯 Objective

Implement `SSHKeyManager` in `configurator/security/ssh_keys.py`.

## 🛠️ Requirements

### Functional

1. **Generation**: Create Ed25519 (preferred) or RSA-4096 keys.
2. **Deployment**: Add public key to `~/.ssh/authorized_keys`.
3. **Hardening**: Ensure `.ssh` permissions (700 dir, 600 files).
4. **Rotation**: Generate new key, add to authorized_keys, (optional: remove old key after confirmation).
5. **SSHD Config**: Disable `PasswordAuthentication` and `PermitRootLogin`.

## 📝 Specifications

### Class Signature (`configurator/security/ssh_keys.py`)

```python
class SSHKeyManager:
    def generate_key_pair(self, type: str = "ed25519") -> Tuple[str, str]:
        # Returns (private_key, public_key)
        pass

    def install_public_key(self, user: str, public_key: str):
        pass

    def harden_sshd_config(self):
        # Edits /etc/ssh/sshd_config
        pass
```

## 🪜 Implementation Steps

1. **Key Gen**: Use `subprocess` to call `ssh-keygen` or Python `cryptography` library.
2. **File Ops**:
    - `os.makedirs` with mode 0o700.
    - Write authorized_keys.
    - `shutil.chown` to user.
3. **Config Editor**:
    - Regex replacement for `sshd_config` parameters.
    - `systemctl reload sshd`.

## 🔍 Validation Checklist

- [ ] Keys generated are valid (loadable).
- [ ] Permissions on `.ssh` are strict.
- [ ] `sshd_config` modified correctly (no duplicate lines).

---

**Output**: Python code for `configurator/security/ssh_keys.py`.
