# QUICK START GUIDE - GET STARTED IN 15 MINUTES

**Debian VPS Configurator**
**Fast Track to Your First Automated VPS Configuration**
**Date:** January 6, 2026

---

## 🎯 OVERVIEW

This guide will get you from **zero to running** in just **15 minutes**, with a working VPS configuration system performing basic security hardening and user setup.

**What You'll Accomplish:**

- ✅ Install the configurator
- ✅ Run your first security scan
- ✅ Create your first admin user
- ✅ Setup SSL certificates
- ✅ Enable 2FA authentication

**Time Required:** 15 minutes
**Difficulty:** Beginner-friendly
**Prerequisites:** Debian 11+ VPS with root access

---

## ⚡ LIGHTNING SETUP (5 minutes)

### Step 1: Install (2 minutes)

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Python 3.9+ (if not already installed)
apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone https://github.com/yunaamelia/debian-vps-workstation.git
cd debian-vps-configurator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the configurator
pip install -e .
```

**✅ Checkpoint:** Verify installation

```bash
python -m configurator --version
# Should output: debian-vps-configurator v1.0.0
```

---

### Step 2: Initialize (1 minute)

```bash
# Initialize the configurator
python -m configurator init

# This creates:
# - /etc/debian-vps-configurator/ (config directory)
# - /var/lib/debian-vps-configurator/ (data directory)
# - /var/log/ (log files)
# - Default configuration file
```

**Expected Output:**

```
Initializing Debian VPS Configurator...
══════════════════════════════════════════════════════

✅ Created configuration directory
✅ Created data directory
✅ Created log directory
✅ Generated default configuration
✅ Initialization complete!

Configuration file: /etc/debian-vps-configurator/config.yaml
Edit this file to customize your setup.
```

---

### Step 3: View Current Status (2 minutes)

```bash
# Check system status
python -m configurator status
```

**Output:**

```
System Status
══════════════════════════════════════════════════════

Security:
  CIS Compliance: Not scanned yet
  Firewall: Unknown
  SSH: Default configuration
  SSL/TLS: No certificates

Users:
  Total users: 0
  Admin users: 0
  2FA enabled: 0

System:
  OS: Debian 11
  Kernel: 5.10.0
  Uptime: 15 days
  Load: 0.25

Next Steps:
  1. Run security scan: python -m configurator security cis-scan
  2. Create admin user: python -m configurator user create <username>
```

---

## 🔒 SECURITY HARDENING (5 minutes)

### Step 4: Run Security Scan (2 minutes)

```bash
# Run CIS benchmark scan (read-only)
python -m configurator security cis-scan
```

**Example Output:**

```
CIS Benchmark Security Scan
══════════════════════════════════════════════════════

Scanning... ████████████████████████████████ 100%

Scan Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Checks:     147
Passed:          89 (60.5%)
Failed:          45 (30.6%)
Manual Review:   13 (8.8%)

Compliance Score: 60.5% (NEEDS IMPROVEMENT)

Critical Issues:  8
High Priority:    15
Medium Priority:  18
Low Priority:     4

Top Issues:
  ❌ SSH root login enabled (CRITICAL)
  ❌ No firewall configured (CRITICAL)
  ❌ Weak password policy (HIGH)
  ❌ No audit logging (HIGH)
  ❌ Unnecessary services running (MEDIUM)

Recommendation: Review issues and run with --remediate flag
```

---

### Step 5: Basic Security Hardening (3 minutes)

```bash
# Apply basic security fixes
# NOTE: This makes system changes - review in production first!
python -m configurator security harden-basic

# This will:
# - Disable SSH root login
# - Update SSH configuration
# - Configure basic firewall
# - Set password policies
# - Enable unattended security updates
```

**Output:**

```
Basic Security Hardening
══════════════════════════════════════════════════════

✅ Disabled SSH root login
✅ Configured SSH (key-only auth)
✅ Enabled UFW firewall
   - Allow SSH (port 22)
   - Allow HTTP (port 80)
   - Allow HTTPS (port 443)
✅ Configured password policies
✅ Enabled automatic security updates
✅ Configured basic audit logging

Security Level: BASIC → GOOD

Recommendations:
  - Run full CIS scan for comprehensive hardening
  - Setup 2FA for all users
  - Configure SSL certificates
```

**✅ Checkpoint:** Basic security is in place!

---

## 👤 USER SETUP (3 minutes)

### Step 6: Create Admin User (2 minutes)

```bash
# Create your first admin user
python -m configurator user create admin-john \
  --full-name "John Administrator" \
  --email john@example.com \
  --role admin \
  --enable-2fa
```

**Output:**

```
User Provisioning: admin-john
══════════════════════════════════════════════════════

✅ Step 1/10: User account created (UID: 1001)
✅ Step 2/10: Home directory created
✅ Step 3/10: Shell configured (/bin/bash)
✅ Step 4/10: RBAC role assigned (admin)
✅ Step 5/10: System groups configured
✅ Step 6/10: Sudo access configured
✅ Step 7/10: SSH directory prepared
✅ Step 8/10: 2FA enrolled
✅ Step 9/10: Temporary password set
✅ Step 10/10: User profile created

🎉 User Created Successfully!

Credentials (save securely):
  Username: admin-john
  Temporary Password: Xy9#mK2$pL4@qR8n

2FA Setup:
  1. Install Google Authenticator or Authy
  2. Scan QR code: /home/admin-john/.mfa-qr-code.txt
  3. Save backup codes: /home/admin-john/.mfa-backup-codes.txt

  QR Code (ASCII):
  ████ ▄▄▄▄▄ █▀█ █▄▀▄▀▄█ ▄▄▄▄▄ ████
  ████ █   █ █▀▀▀█  ▀▄  █   █ ████
  ████ █▄▄▄█ █▀ █▀▄ ▀█▄ █▄▄▄█ ████

Backup Codes (use once each):
  1. 1234-5678
  2. 2345-6789
  3. 3456-7890
  (7 more codes)

Next Steps:
  1. Setup 2FA on your phone
  2. SSH key: python -m configurator user generate-ssh-key admin-john
  3. Change password on first login
```

---

### Step 7: Generate SSH Key (1 minute)

```bash
# Generate SSH key for user
python -m configurator user generate-ssh-key admin-john --type ed25519
```

**Output:**

```
SSH Key Generation
══════════════════════════════════════════════════════

✅ Generated Ed25519 key pair
✅ Private key: /home/admin-john/.ssh/id_ed25519
✅ Public key: /home/admin-john/.ssh/id_ed25519.pub
✅ Added to authorized_keys

Download private key:
  scp root@your-vps-ip:/home/admin-john/.ssh/id_ed25519 ~/admin-john-key
  chmod 600 ~/admin-john-key

Login command:
  ssh -i ~/admin-john-key admin-john@your-vps-ip
```

**✅ Checkpoint:** Admin user is ready!

---

## 🔐 SSL CERTIFICATE (Optional - 2 minutes)

### Step 8: Issue SSL Certificate

```bash
# Issue Let's Encrypt certificate
python -m configurator ssl issue myserver.example.com

# For multiple domains:
python -m configurator ssl issue myserver.example.com www.myserver.example.com
```

**Output:**

```
SSL Certificate Issuance
══════════════════════════════════════════════════════

Domain: myserver.example.com

Step 1/6: Validating domain
✅ DNS records verified

Step 2/6: Generating certificate request
✅ CSR generated

Step 3/6: ACME challenge
✅ HTTP challenge passed

Step 4/6: Issuing certificate
✅ Certificate issued by Let's Encrypt

Step 5/6: Installing certificate
✅ Certificate installed

Step 6/6: Scheduling auto-renewal
✅ Renewal scheduled (30 days before expiry)

🎉 SSL Certificate Issued!

Certificate Details:
  Domain: myserver.example.com
  Issuer: Let's Encrypt
  Valid from: 2026-01-07
  Valid until: 2026-04-07 (90 days)

Auto-renewal: Scheduled for 2026-03-08

Certificate files:
  Cert: /etc/letsencrypt/live/myserver.example.com/fullchain.pem
  Key: /etc/letsencrypt/live/myserver.example.com/privkey.pem
```

**✅ Checkpoint:** HTTPS is enabled!

---

## ✅ VERIFICATION & TESTING

### Quick Health Check

```bash
# Run system health check
python -m configurator health-check
```

**Output:**

```
System Health Check
══════════════════════════════════════════════════════

Security:
  ✅ SSH: Hardened (root login disabled)
  ✅ Firewall: Active (UFW)
  ✅ Password Policy: Configured
  ✅ Auto Updates: Enabled
  ⚠️  CIS Compliance: 60.5% (basic hardening only)

Users:
  ✅ Admin users: 1
  ✅ Regular users: 0
  ✅ 2FA enrollment: 100%

System:
  ✅ Uptime: 15 days, 3 hours
  ✅ Load: 0.25 (low)
  ✅ Memory: 45% used
  ✅ Disk: 15% used

Certificates:
  ✅ Valid certificates: 1
  ⏰ Expiring soon: 0

Overall Status: 🟢 HEALTHY

Recommendations:
  - Run full CIS scan for comprehensive hardening
  - Add more users as needed
  - Configure teams for collaboration
```

---

## 🎯 WHAT YOU'VE ACCOMPLISHED

In just **15 minutes**, you've:

✅ **Installed** the VPS configurator
✅ **Applied** basic security hardening
✅ **Created** a secure admin user with 2FA
✅ **Generated** SSH keys for secure access
✅ **Issued** SSL/TLS certificates (optional)
✅ **Configured** automatic security updates

**Your server is now:**

- 🔒 **More Secure** (basic hardening applied)
- 🚀 **Automated** (auto-updates enabled)
- 👤 **User-ready** (admin account configured)
- 📊 **Monitored** (basic logging enabled)

---

## 🚀 NEXT STEPS (Optional)

### 1. Full CIS Hardening (5 minutes)

```bash
# Run comprehensive CIS scan with auto-remediation
# WARNING: Review changes before running in production
python -m configurator security cis-scan --remediate --auto-approve

# This will bring compliance to 90%+
```

---

### 2. Create Additional Users (2 minutes)

```bash
# Create a developer user
python -m configurator user create dev-jane \
  --full-name "Jane Developer" \
  --email jane@example.com \
  --role developer \
  --enable-2fa
```

---

### 3. Create a Team (3 minutes)

```bash
# Create backend development team
python -m configurator team create backend-team \
  --description "Backend development team" \
  --lead admin-john \
  --shared-dir /var/projects/backend \
  --disk-quota 50

# Add team member
python -m configurator team add-member backend-team dev-jane
```

---

### 4. Setup Temporary Access (2 minutes)

```bash
# Grant 30-day access to contractor
python -m configurator temp-access grant contractor-mike \
  --full-name "Mike Contractor" \
  --email mike@contractor.com \
  --role developer \
  --duration 30 \
  --reason "Q1 2026 project work"
```

---

### 5. Run Vulnerability Scan (3 minutes)

```bash
# Scan for vulnerabilities
python -m configurator security vuln-scan

# View report
python -m configurator security vuln-report
```

---

## 📚 COMMON TASKS CHEAT SHEET

### User Management

```bash
# Create user
python -m configurator user create <username> --role <role>

# List users
python -m configurator user list

# User info
python -m configurator user info <username>

# Offboard user
python -m configurator user offboard <username>
```

### Security

```bash
# CIS scan
python -m configurator security cis-scan

# Vulnerability scan
python -m configurator security vuln-scan

# SSL certificate
python -m configurator ssl issue <domain>

# Check SSL
python -m configurator ssl check <domain>
```

### RBAC

```bash
# Assign role
python -m configurator rbac assign --user <username> --role <role>

# Check permission
python -m configurator rbac check --user <username> --permission <perm>

# List roles
python -m configurator rbac list-roles
```

### Teams

```bash
# Create team
python -m configurator team create <team-name> --lead <username>

# Add member
python -m configurator team add-member <team-name> <username>

# Team info
python -m configurator team info <team-name>
```

### Temporary Access

```bash
# Grant temp access
python -m configurator temp-access grant <username> --duration 30

# List expiring
python -m configurator temp-access list --expiring-soon

# Extend access
python -m configurator temp-access extend <username> --days 14
```

---

## 🔧 TROUBLESHOOTING

### Issue: "Module not found"

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate

# Verify installation
python -m configurator --version
```

---

### Issue: "Permission denied" errors

**Solution:**

```bash
# Run with sudo for system operations
sudo python -m configurator security cis-scan --remediate

# Or ensure user has proper permissions
```

---

### Issue: SSH key login not working

**Solution:**

```bash
# Check SSH key permissions (on local machine)
chmod 600 ~/admin-john-key

# Test SSH connection with verbose output
ssh -vvv -i ~/admin-john-key admin-john@your-vps-ip

# Verify authorized_keys on server
cat /home/admin-john/.ssh/authorized_keys
```

---

### Issue: 2FA code not working

**Solution:**

```bash
# Check system time (must be synced)
timedatectl status

# If time is wrong, sync it
timedatectl set-ntp true

# Use backup code if needed
cat /home/admin-john/.mfa-backup-codes.txt
```

---

## 📊 MONITORING & MAINTENANCE

### Daily Tasks (Automated)

These run automatically:

- ✅ Security updates check
- ✅ Certificate renewal check
- ✅ Temporary access expiration check
- ✅ Log rotation

---

### Weekly Tasks (5 minutes)

```bash
# Check system health
python -m configurator health-check

# Review activity logs
python -m configurator activity report --last 7

# Check for vulnerabilities
python -m configurator security vuln-scan
```

---

### Monthly Tasks (15 minutes)

```bash
# Full CIS compliance scan
python -m configurator security cis-scan

# Review user access
python -m configurator user list --inactive

# Generate compliance report
python -m configurator compliance report --standard soc2
```

---

## 💡 PRO TIPS

### 1. Enable Command Completion

```bash
# Add to ~/.bashrc
alias vps='python -m configurator'

# Reload
source ~/.bashrc

# Now use shorter commands
vps user list
vps security cis-scan
```

---

### 2. Use Configuration Profiles

```bash
# Create profiles for different environments
vps config profile create production
vps config profile create staging

# Switch between profiles
vps config profile use production
```

---

### 3. Setup Regular Scans

```bash
# Add to crontab
crontab -e

# Daily vulnerability scan at 2 AM
0 2 * * * /path/to/venv/bin/python -m configurator security vuln-scan --quiet

# Weekly CIS scan on Sundays at 3 AM
0 3 * * 0 /path/to/venv/bin/python -m configurator security cis-scan --report-only
```

---

### 4. Export Reports

```bash
# JSON format
python -m configurator security cis-scan --format json > cis-report.json

# HTML format
python -m configurator security cis-scan --format html > cis-report.html

# PDF format (requires wkhtmltopdf)
python -m configurator security cis-scan --format pdf --output cis-report.pdf
```

---

## ⚠️ IMPORTANT NOTES

### Security Considerations

1. **Change Default Passwords Immediately**

   - All temporary passwords expire on first use
   - Use strong, unique passwords (20+ characters)

2. **Backup Your 2FA Codes**

   - Save backup codes in a secure password manager
   - Don't lose access to your authenticator app

3. **Keep SSH Keys Safe**

   - Never share private keys
   - Use passphrase-protected keys
   - Set permissions: `chmod 600 ~/.ssh/id_ed25519`

4. **Review Logs Regularly**
   - Check `/var/log/vps-configurator/` daily
   - Investigate suspicious activity immediately
   - Setup alerts for critical events

---

### Production Deployment Checklist

Before using in production:

- [ ] Test in staging environment first
- [ ] Review all configuration changes
- [ ] Backup existing system
- [ ] Have rollback plan ready
- [ ] Schedule maintenance window
- [ ] Notify users of changes
- [ ] Document changes made
- [ ] Test user access after changes

---

## 🎉 CONGRATULATIONS

You've successfully set up a **secure VPS** in just 15 minutes!

**What's next?**

- ✅ Explore advanced features
- ✅ Customize for your needs
- ✅ Add more users and teams
- ✅ Setup monitoring dashboards
- ✅ Integrate with your workflow

**Need help?**

- 📚 Full Documentation: `/docs` directory
- 💬 GitHub Discussions: Ask questions
- 🐛 GitHub Issues: Report bugs
- 📧 Email: <support@example.com>

---

## 📞 QUICK REFERENCE

### Essential Commands

```bash
# Help
python -m configurator --help

# Version
python -m configurator --version

# Health check
python -m configurator health-check

# Security scan
python -m configurator security cis-scan

# Create user
python -m configurator user create <username>

# View logs
tail -f /var/log/vps-configurator/main.log
```

### Configuration Files

```bash
# Main config
/etc/debian-vps-configurator/config.yaml

# User registry
/var/lib/debian-vps-configurator/users/registry.json

# RBAC roles
/etc/debian-vps-configurator/rbac/roles.yaml

# Logs
/var/log/vps-configurator/
```

### Default Ports

- SSH: 22 (customizable)
- HTTP: 80
- HTTPS: 443

---

## 📖 RELATED DOCUMENTATION

- **Complete Project Summary:** [PROJECT-COMPLETE-SUMMARY.md](../PROJECT-COMPLETE-SUMMARY.md)
- **Implementation Roadmap:** [IMPLEMENTATION-ROADMAP.md](../IMPLEMENTATION-ROADMAP.md)
- **Architecture Guide:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Security Best Practices:** [docs/security/SECURITY.md](security/SECURITY.md)
- **RBAC Guide:** [docs/rbac/README.md](rbac/README.md)

---

**END OF QUICK START GUIDE**

🚀 **You're now ready to manage your VPS like a pro!**

_Happy configuring!_ 🎉

---

_Last Updated: January 6, 2026_
_Version: 1.0.0_
