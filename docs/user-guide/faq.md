# Frequently Asked Questions (FAQ)

Quick answers to common questions.

## General

### What is Debian VPS Workstation Configurator?

A tool that transforms a fresh Debian 13 VPS into a fully-featured remote development workstation with one command. It installs and configures:

- Remote desktop (XRDP + XFCE)
- Development tools (Python, Node.js, Docker, etc.)
- Security hardening (firewall, fail2ban, SSH keys)
- IDEs and editors (VS Code, Cursor, Neovim)

See [Getting Started](getting-started.md) for more.

### Who is this for?

- 👨💻 Developers who want a cloud-based coding environment
- 🎓 Students learning programming on limited hardware
- 🚀 Teams needing consistent development environments
- 🌍 Remote workers needing access from anywhere

### How much does it cost?

The tool is **free and open source**. You only pay for:

- VPS hosting ($5-20/month depending on specs)
- Optional: domain name for easy access

### What cloud providers are supported?

Works on any provider offering Debian 13 VPS:

- ✅ DigitalOcean
- ✅ Linode
- ✅ Vultr
- ✅ Hetzner
- ✅ AWS EC2
- ✅ Google Cloud
- ✅ Azure

See [Cloud Provider Guides](../deployment/index.md).

### How long does installation take?

Depends on profile:

- **Beginner**: ~30 minutes
- **Intermediate**: ~45 minutes
- **Advanced**: ~60 minutes

Actual time varies based on VPS speed and network.

## Installation

### Can I install on existing system?

⚠️ **Not recommended.** This tool is designed for fresh Debian 13 installations.

Installing on an existing system may:

- Conflict with existing packages
- Override configurations
- Cause unexpected behavior

**Best practice:** Use a fresh VPS or VM.

### What if installation fails?

The tool has automatic rollback:

1. **Resume**: If interrupted, you can resume:

   ```bash
   vps-configurator install --resume
   ```

2. **Rollback**: Undo changes:

   ```bash
   vps-configurator rollback
   ```

3. **Fresh start**: If needed:

   ```bash
   vps-configurator uninstall --purge
   ```

See [Troubleshooting](troubleshooting.md) for common issues.

### Can I customize what's installed?

Yes! Three ways:

1. **Wizard**: Interactive selection:

   ```bash
   vps-configurator wizard
   ```

2. **Profiles**: Use or create profiles:

   ```bash
   vps-configurator install --profile custom-profile
   ```

3. **Config file**: Edit `config.yaml`:

   ```bash
   vps-configurator install --config my-config.yaml
   ```

See [Configuration Guide](configuration.md).

### How much disk space is needed?

Minimum 20 GB, recommended 40 GB.

Breakdown:

- Base OS: ~3 GB
- Desktop environment: ~2 GB
- Development tools: ~5-10 GB
- Docker images: ~5-15 GB (varies)
- Workspace: ~10-20 GB

### Can I run this without root?

No, root or sudo access is required because:

- Installing system packages (apt)
- Configuring firewall (ufw)
- Setting up system services
- Creating users and groups

## Configuration

### How do I change modules after installation?

Add more modules:

```bash
vps-configurator module add docker
```

Remove modules:

```bash
vps-configurator module remove nodejs
```

Update module config:

```bash
vps-configurator module configure python --version 3.12
```

### Can I create custom profiles?

Yes! Two ways:

1. **Profile builder**:

   ```bash
   vps-configurator profile create my-profile --interactive
   ```

2. **YAML file**:

   ```yaml
   # ~/.config/debian-vps-configurator/profiles/my-profile.yaml
   name: my-profile
   enabled_modules:
     - system
     - security
     - python
     - docker
   ```

See [Profiles Guide](profiles.md).

### Where are configuration files stored?

- **System config**: `/etc/debian-vps-configurator/`
- **User config**: `~/.config/debian-vps-configurator/`
- **Profiles**: `~/.config/debian-vps-configurator/profiles/`
- **State**: `/var/lib/debian-vps-configurator/`
- **Logs**: `/var/log/debian-vps-configurator/`

### How do I backup my configuration?

```bash
vps-configurator backup create --output ~/backup.tar.gz
```

Restore later:

```bash
vps-configurator backup restore ~/backup.tar.gz
```

## Troubleshooting

### "Permission denied" errors

**Cause:** Not running as root/sudo.

**Solution:**

```bash
sudo vps-configurator install
```

### "Module validation failed"

**Cause:** System doesn't meet prerequisites.

**Solution:** Check requirements:

```bash
vps-configurator check-system
```

Fix issues shown, then retry.

### Can't connect via RDP

**Cause:** Firewall blocking port 3389.

**Solution:**

```bash
sudo ufw allow 3389/tcp
sudo systemctl status xrdp
```

See [Troubleshooting Guide](troubleshooting.md#rdp-connection).

### Installation stuck/frozen

**Cause:** Network issue or package download timeout.

**Solution:**

1. Press Ctrl+C to cancel
2. Resume installation:

   ```bash
   vps-configurator install --resume
   ```

The tool saves progress and resumes from where it stopped.

### Out of disk space

**Cause:** VPS has less than 20 GB free.

**Solution:**

1. Check disk usage:

   ```bash
   df -h
   ```

2. Clean package cache:

   ```bash
   sudo apt clean
   ```

3. Upgrade VPS plan if needed.

## Security

### Is this tool secure?

Yes. Security features include:

- 🔒 UFW firewall (only essential ports open)
- 🔒 Fail2ban (blocks brute force attacks)
- 🔒 SSH key authentication (password auth disabled)
- 🔒 Automatic security updates
- 🔒 File integrity monitoring
- 🔒 RBAC (role-based access control)

See [Security Guide](../deployment/security-hardening.md).

### Should I change default ports?

Recommended for extra security:

```bash
# Change SSH port
vps-configurator config set ssh.port 2222

# Change RDP port
vps-configurator config set desktop.xrdp_port 13389
```

### How to setup SSH keys?

During installation, or manually:

```bash
vps-configurator security setup-ssh-keys
```

This:

1. Generates SSH key pair
2. Adds public key to authorized_keys
3. Disables password authentication
4. Provides private key for download

### Is my data encrypted?

- **In transit**: Yes (SSH, HTTPS, RDP with TLS)
- **At rest**: Depends on your VPS provider

For full disk encryption, enable at VPS provider level.

## Performance

### System feels slow

**Check resource usage:**

```bash
vps-configurator monitor
```

**Common causes:**

- RAM: Upgrade if using >80% consistently
- CPU: Check for runaway processes
- Disk: Check if SSD vs HDD

**Optimize:**

```bash
# Reduce desktop effects
vps-configurator config set desktop.compositor picom-basic

# Disable unnecessary services
sudo systemctl disable <service>
```

### How to improve installation speed?

1. **Use SSD VPS** (not HDD)
2. **Choose datacenter near you** (lower latency)
3. **Use package cache** (enabled by default):

   ```bash
   vps-configurator config set performance.package_cache.enabled true
   ```

4. **Increase parallel workers**:

   ```bash
   vps-configurator config set performance.max_workers 8
   ```

### Docker containers slow

**Cause:** Limited RAM or CPU.

**Solutions:**

1. Increase VPS resources
2. Limit container resources:

   ```bash
   docker run --memory="512m" --cpus="1.0" ...
   ```

3. Use Docker BuildKit caching

## Modules

### What modules are available?

See full list:

```bash
vps-configurator list-modules
```

Categories:

- **System**: Base, security, RBAC
- **Desktop**: XRDP, XFCE, themes
- **Languages**: Python, Node.js, Go, Rust, Java, PHP
- **Tools**: Docker, Git, databases
- **IDEs**: VS Code, Cursor, Neovim
- **Networking**: WireGuard, Caddy
- **Monitoring**: Netdata, logging

### Can I add custom modules?

Yes! See [Module Development Guide](../developer-guide/module-development.md).

Basic steps:

1. Create module class extending `ConfigurationModule`
2. Implement `validate()`, `configure()`, `verify()`
3. Register in config or plugins directory

### How to update modules?

```bash
# Update all
vps-configurator update

# Update specific module
vps-configurator update docker
```

### Can I uninstall modules?

```bash
vps-configurator module uninstall nodejs
```

⚠️ **Warning:** Check dependencies first:

```bash
vps-configurator module deps nodejs
```

## Advanced

### Can I run in Docker?

Not recommended. This tool configures a VPS, not a container.

For containerized development, use the installed Docker instead.

### How to integrate with CI/CD?

See [CI/CD Integration Tutorial](../tutorials/cicd-integration.md).

Example for automated deployment:

```yaml
# .github/workflows/deploy.yml
- name: Configure VPS
  run: |
    vps-configurator install --profile production --non-interactive
```

### Can I contribute?

Yes! We welcome contributions:

- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation
- 🔧 Code contributions

See [Contributing Guide](../developer-guide/contributing.md).

### Where to get help?

- 📚 [Documentation](../index.md)
- 💬 [GitHub Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions)
- 🐛 [Issue Tracker](https://github.com/ahmadrizal7/debian-vps-workstation/issues)
- 📧 Email: <support@example.com>
- 💬 Discord: [Join our server](#)

---

**Didn't find your answer?** [Ask in Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions) or [open an issue](https://github.com/ahmadrizal7/debian-vps-workstation/issues/new).
