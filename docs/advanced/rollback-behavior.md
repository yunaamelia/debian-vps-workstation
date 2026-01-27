# Rollback Mechanism

The VPS Configurator includes a comprehensive rollback system that tracks all configuration changes and can restore the system to its previous state if something goes wrong.

## When Rollback Occurs

Rollback is triggered automatically in the following scenarios:

### 1. Module Failure

When a module's `configure()` method fails and returns `False`:

```bash
# Example: Docker installation fails
✗ Module 'docker' configuration failed
⚙️  Rolling back docker changes...
✓ Rollback complete
```

### 2. Verification Failure

When a module's `verify()` method fails after successful configuration:

```bash
# Example: Service didn't start
✓ XRDP installed successfully
✗ XRDP service verification failed
⚙️  Rolling back xrdp changes...
✓ Rollback complete
```

### 3. Manual Trigger

You can manually trigger rollback for specific modules:

```bash
# Rollback a specific module
vps-configurator rollback --module docker

# Rollback all changes
vps-configurator rollback --full

# Rollback to a specific checkpoint
vps-configurator rollback --checkpoint 20250114_120000
```

### 4. Installation Abort

When user cancels installation (Ctrl+C):

```bash
Installing modules...
^C
✗ Installation cancelled by user
⚙️  Rolling back partially installed modules...
✓ System restored to previous state
```

---

## What Gets Rolled Back

The rollback system tracks and can restore:

### ✅ Tracked Changes

#### **Package Installations**

```python
# All packages installed via install_packages() are tracked
self.install_packages(["docker-ce", "docker-compose"])
# Rollback: apt-get remove docker-ce docker-compose
```

#### **File Modifications**

```python
# Files written with backup enabled are tracked
self.write_file("/etc/docker/daemon.json", content, backup=True)
# Rollback: Restore from backup at /var/backups/vps-configurator/...
```

#### **Service Changes**

```python
# Services started/enabled are tracked
self.start_service("docker")
self.enable_service("docker")
# Rollback: systemctl stop docker && systemctl disable docker
```

#### **User Account Changes**

```python
# User creations and modifications are tracked
self.create_user("devuser", shell="/bin/zsh")
# Rollback: userdel devuser
```

#### **Firewall Rules**

```python
# UFW rules added by security module
self.run("ufw allow 3389/tcp")
# Rollback: ufw delete allow 3389/tcp
```

#### **Symbolic Links**

```python
# Symlinks created by modules
self.create_symlink("/usr/local/bin/node", "/usr/bin/node")
# Rollback: rm /usr/local/bin/node
```

### ❌ NOT Rolled Back

#### **Direct System Commands**

```python
# Commands run via run() without rollback registration
self.run("wget https://example.com/file.tar.gz")
# NOT rolled back automatically
```

#### **External Downloads**

```python
# Downloaded files in cache are retained
cache_file = CACHE_DIR / "package.deb"
# Rollback: Files remain in cache (intentional for performance)
```

#### **Database State**

```python
# Database contents are NOT rolled back
# You must implement application-level rollback
```

#### **User Data**

```python
# Home directory contents created by users
# Only tracked if explicitly registered
```

---

## Rollback Behavior

### Partial Rollback (Default)

When Module B fails, only Module B is rolled back. Previously installed modules (A) remain active.

**Example Scenario:**

```
✓ Module: system (installed)
✓ Module: security (installed)
✗ Module: docker (FAILED)
  ⚙️  Rolling back docker only...
  ✓ Rollback complete

Final State:
✓ system: Installed
✓ security: Installed
✗ docker: Not installed
```

**Why Partial Rollback?**

- Faster recovery
- Preserves working modules
- Allows fixing specific module and retrying

**Use Case:**

```bash
# Fix docker issue and retry
vps-configurator install --module docker
```

### Full Rollback (Manual)

Removes ALL changes made by ALL modules:

```bash
vps-configurator rollback --full
```

**Example:**

```
⚙️  Rolling back all modules...
  ⏳ Removing docker...
  ⏳ Removing security configurations...
  ⏳ Removing system packages...
✓ System restored to pre-installation state
```

**Warning:** This removes everything including:

- All installed packages
- All configuration files
- All user accounts created
- All firewall rules

**Use When:**

- Starting fresh installation
- Major configuration error
- Testing rollback functionality

---

## Rollback Checkpoints

The system creates checkpoints after each successful module installation:

### Checkpoint Structure

```json
{
  "checkpoint_id": "20250114_120000",
  "timestamp": "2025-01-14T12:00:00Z",
  "modules_installed": ["system", "security", "docker"],
  "rollback_actions": [
    {
      "module": "docker",
      "type": "package",
      "packages": ["docker-ce", "docker-compose"],
      "restore_command": "apt-get remove -y docker-ce docker-compose"
    },
    {
      "module": "docker",
      "type": "file",
      "path": "/etc/docker/daemon.json",
      "backup_path": "/var/backups/vps-configurator/daemon.json.20250114_120000",
      "restore_command": "cp {backup_path} {path}"
    }
  ]
}
```

### List Checkpoints

```bash
vps-configurator rollback --list

Available Checkpoints:
  20250114_120000  System + Security + Docker
  20250114_110000  System + Security
  20250114_100000  System only
```

### Rollback to Checkpoint

```bash
vps-configurator rollback --checkpoint 20250114_110000
```

---

## Rollback Logs

All rollback operations are logged:

### Log Location

```bash
/var/log/vps-configurator/rollback.log
```

### Example Log Entry

```
[2025-01-14 12:05:30] INFO: Rollback started for module: docker
[2025-01-14 12:05:31] INFO: Removing package: docker-ce
[2025-01-14 12:05:35] INFO: Restoring file: /etc/docker/daemon.json
[2025-01-14 12:05:35] INFO: Stopping service: docker
[2025-01-14 12:05:36] INFO: Rollback completed successfully
```

### View Recent Rollbacks

```bash
tail -f /var/log/vps-configurator/rollback.log
```

---

## Rollback Limitations

### Cannot Rollback

1. **Manual System Changes**

   - Commands run outside configurator
   - Files edited manually

2. **Destructive Operations**

   - Data deleted by applications
   - Database records removed

3. **External State**
   - Cloud resources (DNS, CDN)
   - External services

### Best Practices

✅ **Use Module Methods**

```python
# Good: Tracked
self.write_file(path, content, backup=True)

# Bad: Not tracked
with open(path, 'w') as f:
    f.write(content)
```

✅ **Register Custom Rollback**

```python
self.rollback_manager.add_command(
    "rm -rf /opt/myapp",
    "Remove custom installation"
)
```

✅ **Idempotent Configuration**

```python
# Safe to run multiple times
def configure(self):
    if self.is_configured():
        return True
    # ... setup
```

❌ **Avoid Direct State Changes**

```python
# Risky: Cannot rollback
subprocess.run(["systemctl", "enable", "myservice"])
```

---

## Troubleshooting Rollback

### Rollback Failed

**Problem:** Rollback operation failed

```bash
✗ Rollback failed: Package removal error
```

**Solution:**

1. Check rollback log:

   ```bash
   tail -50 /var/log/vps-configurator/rollback.log
   ```

2. Manually fix issue:

   ```bash
   # Example: Fix APT
   sudo apt-get --fix-broken install
   ```

3. Retry rollback:

   ```bash
   vps-configurator rollback --module docker --force
   ```

### Incomplete Rollback

**Problem:** Some changes not rolled back

**Solution:**

```bash
# Check what's still installed
vps-configurator status --verbose

# Manual cleanup
sudo rm -rf /etc/docker
sudo apt-get remove docker-ce
```

### Rollback History Corrupted

**Problem:** Cannot read rollback history

**Solution:**

```bash
# Reset rollback history (CAUTION!)
sudo rm /var/lib/vps-configurator/rollback_history.json

# Rebuild from system state
vps-configurator rebuild-history
```

---

## See Also

- [Error Recovery Guide](../troubleshooting/error-recovery.md)
- [Module Development Guide](../development/creating-modules.md)
- [Backup Strategy](./backup-strategy.md)
