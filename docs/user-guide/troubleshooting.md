# Troubleshooting Guide

This guide helps you resolve common issues with Debian VPS Workstation Configurator.

## Quick Diagnostics

Before diving deep, run the system check command:

```bash
vps-configurator check-system
```

This will identify:

- Missing dependencies
- Permission issues
- Network connectivity problems
- Disk space shortages

## Installation Issues

### "Permission denied"

**Symptom:** Command fails immediately with permission errors.
**Cause:** The tool requires root privileges to install packages and configure system services.
**Solution:**
Run with `sudo`:

```bash
sudo vps-configurator install
```

Or switch to root user:

```bash
sudo su -
vps-configurator install
```

### "Module validation failed"

**Symptom:** Installation stops during the validation phase.
**Cause:** Prerequisites for a specific module are not met.
**Solution:**
Read the error message carefully. It usually tells you what is missing.
Example:

```
[ERROR] Validation failed for module 'docker':
        - Port 80 is already in use
```

Fix the specific issue (e.g., stop the service using port 80) and retry.

### Installation Stuck or Frozen

**Symptom:** Progress bar stops moving for >5 minutes.
**Cause:** Usually a network timeout or a package manager lock.
**Solution:**

1. Press `Ctrl+C` to interrupt.
2. Resume the installation:

   ```bash
   vps-configurator install --resume
   ```

### "Unable to exact lock" (apt error)

**Symptom:** Error about `/var/lib/dpkg/lock`.
**Cause:** Another process (like unattended-upgrades) is using `apt`.
**Solution:**
Wait 5-10 minutes for the background process to finish.
If it persists:

```bash
sudo killall apt apt-get
sudo dpkg --configure -a
```

## Connection Issues

### Cannot Connect via Remote Desktop (RDP)

**Symptom:** RDP client fails to connect or times out.
**Cause:** Firewall checking or XRDP service down.
**Solution:**

1. **Check Firewall:**
   Ensure port 3389 is open.

   ```bash
   sudo ufw status
   ```

   If not allowed:

   ```bash
   sudo ufw allow 3389/tcp
   ```

2. **Check Service Status:**

   ```bash
   sudo systemctl status xrdp
   ```

   If not running:

   ```bash
   sudo systemctl restart xrdp
   ```

3. **Check Cloud Provider Firewall:**
   Ensure your VPS provider's security group allows TCP traffic on port 3389.

### SSH Connection Refused

**Symptom:** Cannot SSH into the VPS after installation.
**Cause:** SSH configuration changed (e.g., port changed or password auth disabled).
**Solution:**

- Use the correct port if you changed it (default 22, or custom like 2222).

  ```bash
  ssh -p 2222 user@host
  ```

- Use the SSH key generated during setup.

  ```bash
  ssh -i path/to/key user@host
  ```

- Access via your cloud provider's web console to debug.

## Module-Specific Issues

### Docker

**Symptom:** `docker command not found` or permission denied.
**Cause:** User not in docker group or shell not reloaded.
**Solution:**
Log out and log back in to apply group changes.

```bash
exit
ssh user@host
docker info
```

### Python/Pip

**Symptom:** `pip install` fails with "externally-managed-environment".
**Cause:** Debian 13 enforces PEP 668.
**Solution:**
Do not run `pip install` globally. Use a virtual environment:

```bash
python3 -m venv myproject
source myproject/bin/activate
pip install <package>
```

Or use `pipx` for tools:

```bash
pipx install <tool>
```

### VS Code (Remote)

**Symptom:** VS Code cannot connect to remote host.
**Cause:** SSH issues or missing server component.
**Solution:**

- Verify you can SSH from terminal first.
- Kill VS Code server on VPS:

  ```bash
  rm -rf ~/.vscode-server
  ```

- Reconnect to force re-download.

## Error Messages Reference

### `E1001: System Requirement Not Met`

**Meaning:** Your VPS does not have enough RAM or disk space.
**Action:** Upgrade your VPS plan.

### `E2005: Dependency Cycle Detected`

**Meaning:** Modules depend on each other in a loop.
**Action:** Report this as a bug. Install modules individually as a workaround.

### `E5003: Playbook Execution Failed`

**Meaning:** An Ansible playbook or internal configuration script failed.
**Action:** Run with `-v` to see detailed logs.

```bash
vps-configurator install -v
```

## Getting Support

If you cannot resolve the issue:

1. **Collect Logs:**

   ```bash
   tar -czf logs.tar.gz /var/log/debian-vps-configurator/
   ```

2. **Open an Issue:**
   Go to [GitHub Issues](https://github.com/ahmadrizal7/debian-vps-workstation/issues) and attach the logs (scrub secrets first!).

3. **Join Discussion:**
   Ask in [GitHub Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions).
