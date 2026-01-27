# Getting Started with Debian VPS Workstation Configurator

Welcome! This guide will help you transform a fresh Debian 13 VPS into a fully-featured remote development workstation in about 15-30 minutes.

## What You'll Get

After completing this guide, you'll have:

- 🖥️ **Remote Desktop** - Full XFCE desktop accessible via RDP
- 🛡️ **Security Hardening** - UFW firewall, Fail2ban, SSH keys
- 🐍 **Development Tools** - Python, Node.js, Docker, Git, VS Code
- 📊 **Monitoring** - System monitoring and logging
- 🎯 **Your Choice** - Customizable via profiles or wizard

## Prerequisites

Before you begin, ensure you have:

### VPS Requirements

| Requirement | Minimum            | Recommended        |
| ----------- | ------------------ | ------------------ |
| OS          | Debian 13 (Trixie) | Debian 13 (Trixie) |
| RAM         | 4 GB               | 8 GB               |
| Disk        | 20 GB              | 40 GB SSD          |
| CPU         | 2 vCPU             | 4+ vCPU            |
| Network     | Public IP          | Static IP          |

### Local Machine Requirements

You'll need an RDP client:

- **Windows**: Built-in Remote Desktop Connection
- **macOS**: [Microsoft Remote Desktop](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466)
- **Linux**: Remmina, rdesktop, or FreeRDP

### Access Requirements

- ✅ Root or sudo access to your VPS
- ✅ SSH access to your VPS
- ✅ Basic command-line knowledge

## Installation

### Method 1: Quick Install (Recommended)

For most users, the quick install script is the easiest:

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Download and run quick install
curl -sSL https://raw.githubusercontent.com/ahmadrizal7/debian-vps-workstation/main/quick-install.sh | bash

# Activate virtual environment (if not root)
source venv/bin/activate

# Run the interactive wizard
vps-configurator wizard
```

The wizard will guide you through:

1. ✅ Selecting your experience level
2. ✅ Choosing modules to install
3. ✅ Reviewing installation plan
4. ✅ Confirming and starting installation

**Estimated time:** 5 minutes setup + 20-30 minutes installation

### Method 2: Manual Installation

For advanced users or custom setups:

```bash
# Clone repository
git clone https://github.com/ahmadrizal7/debian-vps-workstation.git
cd debian-vps-workstation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run with profile
vps-configurator install --profile beginner
```

See [Installation Guide](installation.md) for detailed instructions.

## First Run: Using the Wizard

The interactive wizard is the easiest way to get started.

### Step 1: Launch Wizard

```bash
vps-configurator wizard
```

### Step 2: Select Experience Level

You'll see three options:

**🟢 Beginner** (Recommended)

- Safe defaults with essential tools
- Includes: Desktop, Python, VS Code, Git, Security
- Installation time: ~30 minutes

**🟡 Intermediate**

- More languages and tools
- Includes: Multiple languages, Docker, Databases
- Installation time: ~45 minutes

**🔴 Advanced**

- Full control over module selection
- Custom configuration options
- Installation time: ~60 minutes

💡 **Tip:** Start with Beginner if unsure. You can always add more modules later.

### Step 3: Review Installation Plan

The wizard shows:

- ✅ Modules to be installed
- ✅ Dependencies (automatically included)
- ✅ Estimated installation time
- ✅ Disk space required

### Step 4: Confirm and Install

Once you confirm:

- ⚙️ System prerequisites are validated
- ⚙️ Modules are installed in optimal order
- ⚙️ Progress is displayed in real-time
- ⚙️ Installation state is saved (can resume if interrupted)

## Verifying Installation

After installation completes:

### 1. Check Installation Status

```bash
vps-configurator verify
```

This verifies all installed modules are working.

### 2. Connect via Remote Desktop

**On Windows:**

1. Open Remote Desktop Connection
2. Enter your VPS IP address
3. Click "Connect"
4. Login with your Linux username/password

**On macOS:**

1. Open Microsoft Remote Desktop
2. Add a new PC with your VPS IP
3. Connect and login

**On Linux:**

```bash
remmina -c rdp://your-vps-ip:3389
```

### 3. Test Installed Tools

Once connected to the desktop:

```bash
# Check Python
python3 --version

# Check Docker
docker --version

# Check VS Code
code --version

# Check Git
git --version
```

## Common Issues

### "Permission Denied"

**Solution:** Run as root or with sudo:

```bash
sudo vps-configurator wizard
```

### "Module Validation Failed"

**Solution:** Check system requirements:

```bash
vps-configurator check-system
```

### "Cannot Connect via RDP"

**Solution:** Check firewall allows port 3389:

```bash
sudo ufw status
sudo ufw allow 3389/tcp
```

See [Troubleshooting Guide](troubleshooting.md) for more solutions.

## Next Steps

Now that you're set up, explore:

📖 **Learn More**

- [Configuration Guide](configuration.md) - Customize your setup
- [Profiles Guide](profiles.md) - Create custom profiles
- [CLI Reference](cli-reference.md) - All available commands

🎓 **Tutorials**

- [Creating a Custom Profile](../tutorials/custom-profile.md)
- [Adding More Modules](../tutorials/adding-modules.md)
- [CI/CD Integration](../tutorials/cicd-integration.md)

🔧 **Advanced**

- [Module Development](../developer-guide/module-development.md)
- [Hooks & Plugins](../developer-guide/hooks-plugins.md)
- [API Reference](../api-reference/index.md)

## Getting Help

- 📚 [Documentation](../index.md)
- 💬 [GitHub Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions)
- 🐛 [Report Issues](https://github.com/ahmadrizal7/debian-vps-workstation/issues)
- 📧 Email: <support@example.com>

---

**Need help?** Don't hesitate to ask in GitHub Discussions or open an issue!
