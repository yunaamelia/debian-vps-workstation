# Step-by-Step Installation Guide

This guide walks you through setting up your Debian 13 VPS as a remote desktop coding workstation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting a VPS](#getting-a-vps)
3. [Initial Server Setup](#initial-server-setup)
4. [Running the Configurator](#running-the-configurator)
5. [Connecting via Remote Desktop](#connecting-via-remote-desktop)
6. [Post-Installation Steps](#post-installation-steps)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, make sure you have:

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Operating System** | Debian 13 (Trixie) | Debian 13 (Trixie) |
| **Architecture** | x86_64 (AMD64) | x86_64 (AMD64) |
| **CPU** | 2 vCPU | 4+ vCPU |
| **RAM** | 4 GB | 8+ GB |
| **Disk Space** | 20 GB | 40+ GB SSD |
| **Network** | Internet access | Stable connection |

### Client Requirements

You'll need an RDP (Remote Desktop Protocol) client on your local machine:

- **Windows**: Built-in Remote Desktop Connection
- **macOS**: [Microsoft Remote Desktop](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466) from App Store
- **Linux**: Remmina, rdesktop, or FreeRDP

---

## Getting a VPS

If you don't already have a VPS, here are some providers that offer Debian 13:

### Recommended Providers

| Provider | Minimum Plan | Notes |
|----------|--------------|-------|
| [Hetzner](https://www.hetzner.com/) | CX22 (~€4/mo) | Excellent price/performance |
| [DigitalOcean](https://www.digitalocean.com/) | Basic ($6/mo) | Easy to use |
| [Linode](https://www.linode.com/) | Nanode ($5/mo) | Good documentation |
| [Vultr](https://www.vultr.com/) | Cloud Compute ($5/mo) | Many locations |
| [OVH](https://www.ovhcloud.com/) | VPS Starter (~€3/mo) | European option |

### Choosing a Plan

For a comfortable development experience, we recommend:

- **Light development** (web, scripting): 2 vCPU, 4 GB RAM
- **Standard development** (Docker, multiple services): 4 vCPU, 8 GB RAM
- **Heavy development** (AI/ML, large projects): 8+ vCPU, 16+ GB RAM

---

## Initial Server Setup

### Step 1: Create Your VPS

1. Sign up with your chosen provider
2. Create a new VPS with:
   - **Image**: Debian 13 (Trixie)
   - **Region**: Closest to your location
   - **SSH Key**: Add your public SSH key (recommended)

### Step 2: Connect to Your Server

```bash
# Replace with your server's IP address
ssh root@YOUR_SERVER_IP
```

If you set up SSH keys:

```bash
ssh -i ~/.ssh/your_key root@YOUR_SERVER_IP
```

### Step 3: Update the System

```bash
apt update && apt upgrade -y
```

### Step 4: Create a Non-Root User (Recommended)

```bash
# Create user (replace 'developer' with your username)
adduser developer

# Add to sudo group
usermod -aG sudo developer

# Switch to new user
su - developer
```

---

## Running the Configurator

### Option 1: Quick Install (One-Line)

```bash
curl -fsSL https://raw.githubusercontent.com/yunaamelia/debian-vps-workstation/main/scripts/bootstrap.sh | sudo bash
```

### Option 2: Manual Installation

```bash
# Install Git if needed
sudo apt update && sudo apt install -y git python3-venv

# Clone the repository
git clone https://github.com/yunaamelia/debian-vps-workstation.git
cd debian-vps-configurator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the configurator
pip install -e .

# Run the wizard
sudo python -m configurator wizard
```

### Using the Wizard

The interactive wizard will guide you through:

1. **Experience Level Selection**
   - 🟢 **Beginner**: Safe defaults, ~30 minutes
   - 🟡 **Intermediate**: More features, ~45 minutes
   - 🔴 **Advanced**: Full control, ~60 minutes

2. **Basic Configuration**
   - Hostname
   - Timezone

3. **Feature Selection** (Intermediate/Advanced only)
   - Additional languages
   - Extra tools
   - Networking options

4. **Confirmation**
   - Review installation plan
   - Confirm to start

### Using Command-Line Options

```bash
# Quick install with profile
sudo python -m configurator install --profile beginner -y

# With custom config file
sudo python -m configurator install --config myconfig.yaml -y

# Dry run (preview without changes)
sudo python -m configurator install --profile beginner --dry-run
```

---

## Connecting via Remote Desktop

After installation completes, you can connect to your desktop.

### Windows

1. Press `Win + R`, type `mstsc`, press Enter
2. Enter your server's IP address
3. Click **Connect**
4. Enter your Linux username and password
5. Click **OK**

### macOS

1. Open **Microsoft Remote Desktop**
2. Click **Add PC**
3. Enter your server's IP in **PC name**
4. Double-click to connect
5. Enter your Linux credentials

### Linux

Using Remmina:

```bash
remmina -c rdp://YOUR_SERVER_IP
```

Using rdesktop:

```bash
rdesktop -u YOUR_USERNAME YOUR_SERVER_IP
```

Using FreeRDP:

```bash
xfreerdp /u:YOUR_USERNAME /v:YOUR_SERVER_IP
```

### First Login

On first login:

1. You'll see the XFCE4 desktop
2. A panel setup dialog may appear - choose "Use default config"
3. Open File Manager or Terminal from the dock

---

## Post-Installation Steps

### Verify Installation

```bash
# Run verification
sudo python -m configurator verify

# Or use the shell script
sudo bash scripts/verify.sh
```

### Check Service Status

```bash
# Remote desktop
sudo systemctl status xrdp

# Firewall
sudo ufw status

# Protection
sudo systemctl status fail2ban
```

### Install Additional Software

The desktop includes Firefox and a terminal. You can install more:

```bash
# Example: Install Chromium
sudo apt install chromium

# Install via flatpak (if configured)
flatpak install flathub com.spotify.Client
```

### Configure VS Code

1. Open VS Code from the applications menu
2. Sign in to sync settings
3. Install additional extensions as needed

### Configure Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Troubleshooting

### Cannot Connect via RDP

1. **Check if xrdp is running**:

   ```bash
   sudo systemctl status xrdp
   sudo systemctl restart xrdp
   ```

2. **Check firewall**:

   ```bash
   sudo ufw status
   sudo ufw allow 3389/tcp
   ```

3. **Check port is listening**:

   ```bash
   ss -tlnp | grep 3389
   ```

### Slow Desktop Performance

1. **Check system resources**:

   ```bash
   htop
   ```

2. **Reduce color depth** in RDP client settings

3. **Consider upgrading** your VPS plan

### SSH Connection Issues

1. **Check SSH service**:

   ```bash
   sudo systemctl status sshd
   ```

2. **Check fail2ban** (you might be banned):

   ```bash
   sudo fail2ban-client status sshd
   sudo fail2ban-client set sshd unbanip YOUR_IP
   ```

### Reset to Clean State

If something goes wrong:

```bash
# Rollback all changes
sudo python -m configurator rollback

# Or start fresh with a new VPS snapshot
```

---

## Next Steps

- Read the [Configuration Reference](../configuration/overview.md)
- Check the [FAQ](../community/faq.md)
- Join the [Community](https://github.com/yunaamelia/debian-vps-workstation/discussions)

---

**Need Help?**

- 📖 [Documentation](https://github.com/yunaamelia/debian-vps-workstation/wiki)
- 💬 [Discussions](https://github.com/yunaamelia/debian-vps-workstation/discussions)
- 🐛 [Report Issues](https://github.com/yunaamelia/debian-vps-workstation/issues)
