# Troubleshooting Guide

Common issues and their solutions when using the Debian VPS Workstation Configurator.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Remote Desktop Issues](#remote-desktop-issues)
3. [Security Issues](#security-issues)
4. [Performance Issues](#performance-issues)
5. [Module-Specific Issues](#module-specific-issues)
6. [Recovery Options](#recovery-options)

---

## Installation Issues

### "System validation failed"

**Error:**

```
PrerequisiteError: System validation failed
```

**Cause:** The system doesn't meet minimum requirements.

**Solution:**

1. Check you're running Debian 13:

   ```bash
   cat /etc/os-release
   ```

2. Check you have enough RAM:

   ```bash
   free -h
   ```

3. Check disk space:

   ```bash
   df -h /
   ```

4. Run as root:

   ```bash
   sudo python -m configurator install
   ```

---

### "Package installation failed"

**Error:**

```
ModuleExecutionError: Failed to install packages
```

**Cause:** APT repository issues or network problems.

**Solution:**

1. Update package lists:

   ```bash
   sudo apt update
   ```

2. Fix broken packages:

   ```bash
   sudo apt --fix-broken install
   ```

3. Check internet connectivity:

   ```bash
   ping -c 3 google.com
   ```

4. Retry installation:

   ```bash
   sudo python -m configurator install --profile beginner
   ```

---

### "Configuration file not found"

**Error:**

```
ConfigurationError: Configuration file not found
```

**Cause:** Custom config file doesn't exist.

**Solution:**

1. Check the file path:

   ```bash
   ls -la /path/to/your/config.yaml
   ```

2. Use absolute path:

   ```bash
   sudo python -m configurator install --config /full/path/to/config.yaml
   ```

---

## Remote Desktop Issues

### Cannot connect via RDP

**Symptoms:** RDP client times out or connection refused.

**Solution:**

1. Check xrdp is running:

   ```bash
   sudo systemctl status xrdp
   ```

2. Restart xrdp if needed:

   ```bash
   sudo systemctl restart xrdp
   sudo systemctl restart xrdp-sesman
   ```

3. Check port 3389:

   ```bash
   ss -tlnp | grep 3389
   ```

4. Check firewall allows RDP:

   ```bash
   sudo ufw status
   sudo ufw allow 3389/tcp
   ```

5. Check cloud provider firewall (AWS/GCP/Azure security groups)

---

### Black screen after login

**Cause:** Session startup script not configured correctly.

**Solution:**

1. Check startwm.sh:

   ```bash
   cat /etc/xrdp/startwm.sh
   ```

2. Reset to default:

   ```bash
   echo '#!/bin/sh
   exec /usr/bin/startxfce4' | sudo tee /etc/xrdp/startwm.sh
   sudo chmod +x /etc/xrdp/startwm.sh
   sudo systemctl restart xrdp
   ```

---

### "Authentication failed" in RDP

**Cause:** Wrong credentials or user doesn't exist.

**Solution:**

1. Verify user exists:

   ```bash
   id YOUR_USERNAME
   ```

2. Reset password:

   ```bash
   sudo passwd YOUR_USERNAME
   ```

3. Try with root user (if enabled)

---

### Desktop is slow/laggy

**Cause:** High latency, insufficient resources, or color depth.

**Solution:**

1. In RDP client, reduce color depth to 16-bit

2. Disable desktop effects:
   - Right-click desktop → Applications → Settings → Window Manager Tweaks
   - Disable compositor

3. Check server resources:

   ```bash
   htop
   ```

4. Consider upgrading VPS plan

---

## Security Issues

### Locked out after fail2ban

**Symptoms:** Cannot SSH, even with correct credentials.

**Solution:**

1. Access via VPS provider's console (web-based)

2. Check if you're banned:

   ```bash
   sudo fail2ban-client status sshd
   ```

3. Unban your IP:

   ```bash
   sudo fail2ban-client set sshd unbanip YOUR_IP_ADDRESS
   ```

4. Whitelist your IP:

   ```bash
   echo "YOUR_IP_ADDRESS" | sudo tee -a /etc/fail2ban/jail.local
   sudo systemctl restart fail2ban
   ```

---

### SSH "Connection refused"

**Cause:** SSH not running or firewall blocked.

**Solution:**

1. Use VPS provider console

2. Start SSH:

   ```bash
   sudo systemctl start sshd
   sudo systemctl enable sshd
   ```

3. Check firewall:

   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp
   ```

---

### Firewall blocking services

**Solution:**

1. Check current rules:

   ```bash
   sudo ufw status verbose
   ```

2. Allow specific port:

   ```bash
   sudo ufw allow 8080/tcp
   ```

3. Reset firewall (careful!):

   ```bash
   sudo ufw reset
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow 22/tcp
   sudo ufw allow 3389/tcp
   sudo ufw enable
   ```

---

## Performance Issues

### High memory usage

**Solution:**

1. Check memory consumers:

   ```bash
   ps aux --sort=-%mem | head -10
   ```

2. Kill heavy processes:

   ```bash
   kill -9 PID
   ```

3. Add swap:

   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

### High CPU usage

**Solution:**

1. Check CPU consumers:

   ```bash
   top -o %CPU
   ```

2. Limit specific processes with cgroups or nice

3. Consider upgrading VPS

---

### Disk space full

**Solution:**

1. Find large files:

   ```bash
   du -h / | sort -rh | head -20
   ```

2. Clean package cache:

   ```bash
   sudo apt clean
   sudo apt autoremove
   ```

3. Clean Docker:

   ```bash
   docker system prune -a
   ```

4. Clean logs:

   ```bash
   sudo journalctl --vacuum-time=7d
   ```

---

## Module-Specific Issues

### Docker not working without sudo

**Cause:** User not in docker group.

**Solution:**

```bash
sudo usermod -aG docker $USER
# Log out and back in, or:
newgrp docker
```

---

### Node.js not found

**Cause:** nvm not sourced in current shell.

**Solution:**

```bash
source ~/.nvm/nvm.sh
node --version
```

Add to your shell profile if not present:

```bash
echo 'export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc
source ~/.bashrc
```

---

### VS Code extensions not installing

**Cause:** Network issues or permission problems.

**Solution:**

```bash
# Install manually
code --install-extension ms-python.python --force

# Check logs
cat ~/.config/Code/logs/main.log
```

---

## Recovery Options

### Rollback installation

```bash
sudo python -m configurator rollback
```

### Manual rollback steps

1. Restore backup files:

   ```bash
   ls /var/backups/debian-vps-configurator/
   ```

2. Disable services:

   ```bash
   sudo systemctl disable xrdp
   sudo systemctl stop xrdp
   ```

3. Remove packages:

   ```bash
   sudo apt remove xrdp xfce4
   ```

### Full system reset

If all else fails:

1. Create new VPS from provider
2. Restore from snapshot (if available)
3. Run fresh installation

---

## Getting Help

If you can't solve your issue:

1. **Collect logs**:

   ```bash
   cat /var/log/debian-vps-configurator/install.log
   journalctl -u xrdp
   ```

2. **Check GitHub Issues**: [Known Issues](https://github.com/yunaamelia/debian-vps-workstation/issues)

3. **Ask in Discussions**: [Community Help](https://github.com/yunaamelia/debian-vps-workstation/discussions)

4. **Open new issue** with:
   - Full error message
   - Installation logs
   - System info (`uname -a`, `cat /etc/os-release`)
