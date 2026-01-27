# Frequently Asked Questions (FAQ)

Common questions and answers about the Debian VPS Workstation Configurator.

## General Questions

### What is this tool?

The Debian VPS Workstation Configurator is an automated tool that transforms a fresh Debian 13 VPS into a fully-featured remote desktop coding workstation. It installs and configures:

- Remote desktop (xRDP + XFCE4)
- Development languages (Python, Node.js, etc.)
- Developer tools (Docker, Git, VS Code)
- Security hardening (Firewall, fail2ban)

### Why Debian 13 specifically?

Debian 13 (Trixie) is the latest stable release with:

- Up-to-date software packages
- Excellent stability
- Long-term support
- Wide VPS provider availability

### Is this free to use?

Yes! This tool is 100% free and open source under the MIT license. All installed software is free and open source.

### Can I use this on other Linux distributions?

Currently, **only Debian 13 is supported**. The tool validates the OS before installation and will refuse to run on other distributions.

Future versions may support:

- Debian 12 (Bookworm)
- Ubuntu 24.04

---

## Installation Questions

### How long does installation take?

| Profile | Estimated Time |
|---------|---------------|
| Beginner | ~30 minutes |
| Intermediate | ~45 minutes |
| Advanced | ~60 minutes |

Actual time depends on your VPS speed and internet connection.

### Can I stop and resume installation?

Yes, if installation is interrupted:

1. The tool tracks progress
2. Run the same command again
3. Already-completed steps will be skipped

### What if installation fails?

1. Check the error message for guidance
2. Look at logs: `/var/log/debian-vps-configurator/install.log`
3. Fix the issue and retry
4. Use `--rollback` to undo changes if needed

### Can I customize what gets installed?

Yes! Three ways:

1. **Choose a profile**: beginner, intermediate, or advanced
2. **Use a custom config file**: `--config myconfig.yaml`
3. **Answer wizard questions**: Different options per profile

See [Configuration Reference](../configuration/overview.md) for all options.

---

## Remote Desktop Questions

### What RDP clients can I use?

Any standard RDP client:

| OS | Client |
|-----|--------|
| Windows | Built-in Remote Desktop Connection |
| macOS | Microsoft Remote Desktop (App Store) |
| Linux | Remmina, rdesktop, FreeRDP |
| Android | Microsoft Remote Desktop |
| iOS | Microsoft Remote Desktop |

### What's the default RDP port?

**Port 3389** (standard RDP port). You can change this in configuration if needed.

### Why XFCE4 and not GNOME or KDE?

XFCE4 was chosen because it's:

- **Lightweight**: Low resource usage
- **Fast**: Responsive over network connections
- **Stable**: Mature and reliable
- **Traditional**: Familiar desktop paradigm

GNOME and KDE require more resources and are harder to use over RDP.

### Is the connection secure?

Yes, the RDP connection is encrypted. For additional security:

1. Use VPN like WireGuard
2. Use SSH tunneling
3. Enable additional UFW rules

---

## Security Questions

### Why is security mandatory?

Every server connected to the internet faces constant attacks. Mandatory security ensures:

- Your server isn't compromised
- No botnets or crypto miners installed
- Your data stays safe
- You don't accidentally harm others

### What security measures are installed?

1. **UFW Firewall**: Only allows SSH and RDP
2. **Fail2ban**: Blocks brute force attacks
3. **SSH Hardening**: Secure SSH configuration
4. **Auto Updates**: Security patches applied automatically

### Will I get locked out?

Unlikely with default settings:

- 5 failed SSH attempts triggers 1-hour ban
- Your RDP access is separate from SSH
- VPS console access always available

If locked out, use your VPS provider's console to unban yourself.

### Can I disable security?

**No.** Security cannot be disabled. This is by design to protect you.

However, you can customize:

- Fail2ban thresholds
- SSH settings
- Firewall rules (additional ports)

---

## Development Questions

### Can I install additional languages?

Yes! Use the intermediate or advanced profile, or specify in your config:

```yaml
languages:
  golang:
    enabled: true
  rust:
    enabled: true
```

### How do I add SSH keys for Git?

1. Generate key on your VPS:

   ```bash
   ssh-keygen -t ed25519 -C "your@email.com"
   ```

2. Add to GitHub:

   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. Copy output to GitHub Settings → SSH Keys

### Can I use this for production hosting?

This tool is designed for **development workstations**, not production servers.

For production:

- Use a dedicated server
- Implement proper CI/CD
- Add monitoring and logging
- Configure backup solutions

### Does it support container development?

Yes! Docker and Docker Compose are installed. You can:

- Build and run containers
- Use docker-compose for multi-container apps
- Access Docker without sudo

---

## Performance Questions

### What VPS size do I need?

| Use Case | Minimum | Recommended |
|----------|---------|-------------|
| Light coding | 2 vCPU, 4 GB RAM | 2 vCPU, 4 GB RAM |
| Web development | 2 vCPU, 4 GB RAM | 4 vCPU, 8 GB RAM |
| Docker + databases | 4 vCPU, 8 GB RAM | 4 vCPU, 16 GB RAM |
| AI/ML development | 4 vCPU, 16 GB RAM | 8+ vCPU, 32+ GB RAM |

### Why is my desktop slow?

Common causes:

1. **Network latency**: Try a VPS closer to your location
2. **Low resources**: Upgrade your VPS
3. **Color depth**: Reduce to 16-bit in RDP client
4. **Desktop effects**: Disable compositor in XFCE

### How can I monitor resources?

Use the built-in tools:

```bash
htop          # CPU and memory
iotop         # Disk I/O
nethogs       # Network usage
```

Or enable Netdata in configuration for web-based monitoring.

---

## Troubleshooting Questions

### Where are the logs?

| Log | Location |
|-----|----------|
| Installation | `/var/log/debian-vps-configurator/install.log` |
| xRDP | `/var/log/xrdp.log` |
| System | `journalctl -xe` |
| SSH | `journalctl -u sshd` |

### How do I reset everything?

```bash
# Rollback all changes
sudo python -m configurator rollback

# Or for complete reset, restore VPS from snapshot
```

### Can I get help?

Yes!

1. 📖 Read the [Troubleshooting Guide](../installation/troubleshooting.md)
2. 🔍 Search [GitHub Issues](https://github.com/yunaamelia/debian-vps-workstation/issues)
3. 💬 Ask in [Discussions](https://github.com/yunaamelia/debian-vps-workstation/discussions)
4. 🐛 [Open an issue](https://github.com/yunaamelia/debian-vps-workstation/issues/new) with logs

---

## Contributing Questions

### How can I contribute?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [CONTRIBUTING.md](https://github.com/yunaamelia/debian-vps-workstation/blob/main/CONTRIBUTING.md)

### Can I add support for other distros?

We'd love that! The modular architecture makes this possible:

1. Create new system detection in `utils/system.py`
2. Adjust package names in modules
3. Test thoroughly
4. Submit PR with test results

### How do I report bugs?

Open an issue with:

- Description of the problem
- Steps to reproduce
- Installation logs
- System information (`uname -a`, `/etc/os-release`)

---

## Didn't find your answer?

Ask in [GitHub Discussions](https://github.com/yunaamelia/debian-vps-workstation/discussions)!
