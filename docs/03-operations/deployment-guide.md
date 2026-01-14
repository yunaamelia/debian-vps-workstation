# PRODUCTION DEPLOYMENT GUIDE

**Debian VPS Configurator - Production Setup & Configuration**
**Safe and Secure Production Deployment for Small Teams**
**Date:** January 6, 2026

---

## 🎯 OVERVIEW

This guide provides **step-by-step instructions** for deploying Debian VPS Configurator to a production environment for small teams (2-10 users).

**Target Audience:** System administrators, DevOps engineers
**Time Required:** 2-4 hours (first deployment)
**Prerequisites:**

- Debian 11+ server with root access
- Domain name with DNS access
- SSL certificate capability (Let's Encrypt)
- Basic Linux administration skills

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Server Requirements

**Minimum Specs:**

- [ ] CPU: 2 cores
- [ ] RAM: 4 GB
- [ ] Disk: 50 GB SSD
- [ ] OS: Debian 11 or 12 (clean install)
- [ ] Network: Public IP address

**Recommended Specs:**

- [ ] CPU: 4 cores
- [ ] RAM: 8 GB
- [ ] Disk: 100 GB SSD
- [ ] Backup: Automated daily backups

### Access Requirements

- [ ] Root SSH access
- [ ] Domain name configured (e.g., vps.company.com)
- [ ] DNS A record pointing to server IP
- [ ] Firewall access (ports 22, 80, 443)
- [ ] Email for SSL certificates

### Pre-Deployment Tasks

- [ ] Server OS updated to latest
- [ ] Firewall rules planned
- [ ] Backup solution in place
- [ ] Monitoring system ready (optional)
- [ ] Team notified of deployment window

---

## 🔧 STEP 1: SERVER PREPARATION (30 minutes)

### 1.1 Initial Server Hardening

```bash
# SSH into server as root
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential tools
apt install -y curl wget git sudo ufw fail2ban

# Set timezone
timedatectl set-timezone Asia/Jakarta  # Adjust to your timezone

# Set hostname
hostnamectl set-hostname vps.company.com

# Add to /etc/hosts
echo "127.0.0.1 vps.company.com" >> /etc/hosts
```

### 1.2 Configure Firewall (UFW)

```bash
# Enable UFW
ufw --force enable

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (IMPORTANT!)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Check status
ufw status verbose
```

**Output should show:**

```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

### 1.3 Configure Fail2Ban

```bash
# Create local config
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
EOF

# Restart fail2ban
systemctl restart fail2ban
systemctl enable fail2ban

# Check status
fail2ban-client status sshd
```

---

## 📦 STEP 2: INSTALL VPS CONFIGURATOR (45 minutes)

### 2.1 Install Dependencies

```bash
# Install Python 3.9+
apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies
apt install -y \
  build-essential \
  libssl-dev \
  libffi-dev \
  libpam0g-dev \
  libqrencode-dev \
  sqlite3

# Verify Python version
python3 --version  # Should be 3.9 or higher
```

### 2.2 Create Application User

```bash
# Create dedicated user (don't run as root!)
useradd -r -m -d /opt/vps-configurator -s /bin/bash vpsconfig

# Add to sudo group (for system operations)
usermod -aG sudo vpsconfig

# Create directory structure
mkdir -p /opt/vps-configurator/{app,logs,data,backups,scripts}
chown -R vpsconfig:vpsconfig /opt/vps-configurator
```

### 2.3 Install Application

```bash
# Switch to application user
su - vpsconfig

# Clone repository
cd /opt/vps-configurator/app
git clone https://github.com/yunaamelia/debian-vps-workstation.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install application
pip install -e .

# Verify installation
vps-configurator --version
```

**Expected output:**

```
debian-vps-configurator v1.0.0
```

---

## ⚙️ STEP 3: PRODUCTION CONFIGURATION (30 minutes)

### 3.1 Initialize Configuration

```bash
# Still as vpsconfig user
vps-configurator init --production
```

This creates:

- `/etc/debian-vps-configurator/` - Configuration directory
- `/var/lib/debian-vps-configurator/` - Data directory
- `/var/log/vps-configurator/` - Log directory

### 3.2 Configure for Production

```bash
# Edit main configuration
nano /etc/debian-vps-configurator/config.yaml
```

**Production Configuration Template:**

```yaml
# /etc/debian-vps-configurator/config.yaml

# ═══════════════════════════════════════════════════════════════════
# PRODUCTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# General Settings
general:
  environment: production
  hostname: vps.company.com
  admin_email: admin@company.com
  timezone: Asia/Jakarta

# Logging Configuration
logging:
  level: INFO # Use INFO for production (not DEBUG)
  file: /var/log/vps-configurator/main.log
  max_size_mb: 100
  backup_count: 10
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance Settings
performance:
  parallel_execution:
    enabled: true
    max_workers: 4
  cache:
    enabled: true
    directory: /var/cache/vps-configurator
    max_size_gb: 10
  lazy_loading:
    enabled: true

# Security Settings
security:
  cis_benchmark:
    enabled: true
    auto_remediate: false # Manual review in production
    scan_schedule: "0 2 * * 0" # Weekly, Sunday 2 AM

  vulnerability_scanner:
    enabled: true
    scan_schedule: "0 3 * * *" # Daily, 3 AM
    auto_update_db: true

  ssl_certificates:
    enabled: true
    provider: letsencrypt
    email: admin@company.com
    auto_renew: true
    renew_days_before: 30

  ssh_keys:
    rotation_enabled: true
    rotation_days: 90
    key_type: ed25519

  mfa:
    enabled: true
    enforcement: required # All users must have 2FA
    backup_codes: 10

# RBAC Settings
rbac:
  enabled: true
  default_deny: true

  sudo:
    enabled: true
    validate_before_apply: true
    audit_enabled: true

# User Management
users:
  lifecycle:
    enabled: true
    welcome_email: true
    offboarding_archive: true
    archive_retention_days: 2555 # 7 years

  activity_monitoring:
    enabled: true
    database: /var/lib/debian-vps-configurator/activity/activity.db
    retention_days: 2555 # 7 years
    anomaly_detection: true
    alert_threshold: 70

  teams:
    enabled: true
    shared_directories: /var/projects
    default_quota_gb: 50

  temp_access:
    enabled: true
    default_duration_days: 30
    max_duration_days: 90
    extension_approval: true

# Backup Settings
backup:
  enabled: true
  directory: /opt/vps-configurator/backups
  schedule: "0 1 * * *" # Daily, 1 AM
  retention_days: 30
  compress: true
  include:
    - /etc/debian-vps-configurator
    - /var/lib/debian-vps-configurator
    - /var/log/vps-configurator

# Notifications
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_user: alerts@company.com
    smtp_password_env: SMTP_PASSWORD # Use environment variable
    from_address: vps-configurator@company.com

  alerts:
    security_scan_failed: true
    certificate_expiring: true
    user_suspicious_activity: true
    system_error: true

# Maintenance Windows
maintenance:
  allowed_hours: [1, 2, 3, 4, 5] # 1 AM - 5 AM
  auto_approve_during_window: true
  notify_before_minutes: 30
```

### 3.3 Set Environment Variables

```bash
# Create environment file
nano /opt/vps-configurator/.env
```

```bash
# /opt/vps-configurator/.env

# Database
DATABASE_URL=sqlite:////var/lib/debian-vps-configurator/activity/activity.db

# SMTP (for email notifications)
SMTP_PASSWORD=your-smtp-password-here

# Let's Encrypt
LETSENCRYPT_EMAIL=admin@company.com

# Security
SECRET_KEY=generate-random-key-here  # Generate with: openssl rand -base64 32

# Backup
BACKUP_ENCRYPTION_KEY=generate-backup-key  # Generate with: openssl rand -base64 32
```

**Secure the environment file:**

```bash
chmod 600 /opt/vps-configurator/.env
chown vpsconfig:vpsconfig /opt/vps-configurator/.env
```

---

## 🔒 STEP 4: SECURITY HARDENING (45 minutes)

### 4.1 Run Initial Security Scan

```bash
# As vpsconfig user
vps-configurator security cis-scan --production
```

**Review the report:**

- Note all FAILED checks
- Prioritize CRITICAL and HIGH issues
- Create remediation plan

### 4.2 Apply Security Hardening

```bash
# Run with manual review (safer for production)
vps-configurator security cis-scan --remediate --interactive

# Or if confident, auto-approve non-critical
vps-configurator security cis-scan --remediate --auto-approve-low
```

**Expected result:**

- Compliance score: 90%+
- All CRITICAL issues resolved
- Most HIGH issues resolved

### 4.3 Setup SSL Certificate

```bash
# Issue SSL certificate
vps-configurator ssl issue vps.company.com

# Verify certificate
vps-configurator ssl check vps.company.com
```

### 4.4 Harden SSH

```bash
# Edit SSH config
nano /etc/ssh/sshd_config
```

**Recommended SSH settings:**

```
# /etc/ssh/sshd_config

Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
X11Forwarding no
MaxAuthTries 3
MaxSessions 2
Protocol 2
AllowUsers vpsconfig admin-*  # Whitelist users
```

**Restart SSH:**

```bash
systemctl restart sshd
```

⚠️ **WARNING:** Test new SSH connection BEFORE closing current session!

---

## 👥 STEP 5: USER SETUP (30 minutes)

### 5.1 Create Admin Users

```bash
# Create primary admin
vps-configurator user create admin-yourname \
  --full-name "Your Name" \
  --email your.email@company.com \
  --role admin \
  --enable-2fa \
  --generate-ssh-key

# Save credentials securely!
# - Temporary password
# - SSH private key
# - 2FA QR code
# - Backup codes
```

### 5.2 Create Team Accounts

```bash
# Create developer users
for user in dev-alice dev-bob dev-charlie; do
  vps-configurator user create $user \
    --role developer \
    --enable-2fa \
    --generate-ssh-key
done

# Create team
vps-configurator team create backend-team \
  --lead admin-yourname \
  --shared-dir /var/projects/backend

# Add members
vps-configurator team add-member backend-team dev-alice
vps-configurator team add-member backend-team dev-bob
```

### 5.3 Disable Root SSH (After Admin Setup)

```bash
# Verify admin user can login first!
# Then disable root

# Edit SSH config
nano /etc/ssh/sshd_config

# Change:
PermitRootLogin no

# Restart SSH
systemctl restart sshd
```

---

## 📊 STEP 6: MONITORING & LOGGING (30 minutes)

### 6.1 Setup Log Rotation

```bash
# Create logrotate config
cat > /etc/logrotate.d/vps-configurator <<EOF
/var/log/vps-configurator/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 vpsconfig vpsconfig
    sharedscripts
    postrotate
        systemctl reload vps-configurator > /dev/null 2>&1 || true
    endscript
}
EOF
```

### 6.2 Setup Systemd Service

```bash
# Create systemd service
cat > /etc/systemd/system/vps-configurator.service <<EOF
[Unit]
Description=Debian VPS Configurator
After=network.target

[Service]
Type=simple
User=vpsconfig
Group=vpsconfig
WorkingDirectory=/opt/vps-configurator/app
Environment="PATH=/opt/vps-configurator/app/venv/bin"
EnvironmentFile=/opt/vps-configurator/.env
ExecStart=/opt/vps-configurator/app/venv/bin/vps-configurator daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable vps-configurator
systemctl start vps-configurator

# Check status
systemctl status vps-configurator
```

### 6.3 Setup Cron Jobs

```bash
# Edit crontab as vpsconfig
crontab -e
```

```cron
# Debian VPS Configurator Scheduled Tasks

# Daily vulnerability scan (3 AM)
0 3 * * * /opt/vps-configurator/app/venv/bin/vps-configurator security vuln-scan --quiet

# Weekly CIS scan (Sunday 2 AM)
0 2 * * 0 /opt/vps-configurator/app/venv/bin/vps-configurator security cis-scan --quiet

# Daily backup (1 AM)
0 1 * * * /opt/vps-configurator/app/venv/bin/vps-configurator backup create --quiet

# Check expiring certificates (daily 4 AM)
0 4 * * * /opt/vps-configurator/app/venv/bin/vps-configurator ssl check-expiring --quiet

# Check expiring temporary access (daily 5 AM)
0 5 * * * /opt/vps-configurator/app/venv/bin/vps-configurator temp-access check-expired --quiet

# Rotate SSH keys (weekly, Monday 6 AM)
0 6 * * 1 /opt/vps-configurator/app/venv/bin/vps-configurator ssh rotate-keys --quiet

# Generate weekly report (Sunday 7 AM)
0 7 * * 0 /opt/vps-configurator/app/venv/bin/vps-configurator report generate --weekly --email admin@company.com
```

---

## 💾 STEP 7: BACKUP CONFIGURATION (20 minutes)

### 7.1 Setup Automated Backups

```bash
# Create backup script
cat > /opt/vps-configurator/scripts/backup.sh <<'EOF'
#!/bin/bash

# Backup script for VPS Configurator
BACKUP_DIR="/opt/vps-configurator/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="vps-config-backup-$DATE.tar.gz"

# Create backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
  /etc/debian-vps-configurator \
  /var/lib/debian-vps-configurator \
  /var/log/vps-configurator \
  /opt/vps-configurator/.env

# Keep only last 30 days
find "$BACKUP_DIR" -name "vps-config-backup-*.tar.gz" -mtime +30 -delete

# Log
echo "$(date): Backup created: $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"
EOF

chmod +x /opt/vps-configurator/scripts/backup.sh

# Test backup
/opt/vps-configurator/scripts/backup.sh
```

### 7.2 Setup Remote Backup (Optional but Recommended)

```bash
# Install rclone for remote backup
curl https://rclone.org/install.sh | bash

# Configure rclone (interactive)
rclone config

# Add to backup script
# rclone copy "$BACKUP_DIR/$BACKUP_FILE" remote:backups/vps-configurator/
```

---

## ✅ STEP 8: POST-DEPLOYMENT VALIDATION (30 minutes)

### 8.1 Run Health Check

```bash
vps-configurator health-check --production
```

**Expected output:**

```
Production Health Check
══════════════════════════════════════════════════════

✅ System Status: HEALTHY
✅ CIS Compliance: 92%
✅ SSL Certificate: Valid (89 days remaining)
✅ Users: 5 active
✅ 2FA Enrollment: 100%
✅ Backups: Latest 2 hours ago
✅ Disk Space: 25% used
✅ Memory: 45% used
✅ Services: All running

⚠️  Warnings: None
❌ Errors: None

Overall Status: 🟢 PRODUCTION READY
```

### 8.2 Test User Login

```bash
# From your local machine
ssh admin-yourname@vps.company.com

# Enter 2FA code when prompted
# Verify you can run commands
vps-configurator user list
```

### 8.3 Test Core Functionality

```bash
# Test security scan
vps-configurator security cis-scan --dry-run

# Test user creation
vps-configurator user create test-user --role viewer

# Test team operations
vps-configurator team list

# Clean up test user
vps-configurator user offboard test-user --reason "Test user"
```

---

## 🚀 STEP 9: GO LIVE (10 minutes)

### 9.1 Final Checklist

- [ ] All admin users created and tested
- [ ] All users have 2FA enabled
- [ ] SSH root login disabled
- [ ] Firewall configured correctly
- [ ] SSL certificate valid
- [ ] Backups configured and tested
- [ ] Monitoring/logging active
- [ ] Cron jobs scheduled
- [ ] Documentation updated with server details

### 9.2 Notify Team

```bash
# Send announcement email
cat > /tmp/deployment-announcement.txt <<EOF
Subject: VPS Configurator Production Deployment Complete

Team,

The VPS Configurator has been successfully deployed to production.

Server: vps.company.com
Access: SSH with your provided credentials

Getting Started:
1. Login: ssh your-username@vps.company.com
2. Use 2FA when prompted
3. Run: vps-configurator --help

Documentation: [link to docs]
Support: [support channel]

Please confirm you can login successfully.

Best regards,
System Administrator
EOF

# Send email (adjust mail command as needed)
mail -s "VPS Configurator Production Deployment" team@company.com < /tmp/deployment-announcement.txt
```

### 9.3 Monitor First 24 Hours

**Check these every 4 hours on Day 1:**

```bash
# System status
systemctl status vps-configurator

# Recent logs
tail -100 /var/log/vps-configurator/main.log

# Failed login attempts
grep "Failed" /var/log/auth.log | tail -20

# Disk space
df -h

# Memory usage
free -h

# Active users
who
```

---

## 🔄 ROLLBACK PROCEDURES

### If Deployment Fails

**Option 1: Rollback to Previous State**

```bash
# Restore from backup
cd /opt/vps-configurator/backups
tar -xzf vps-config-backup-[latest].tar.gz -C /

# Restart services
systemctl restart vps-configurator
```

**Option 2: Fresh Install**

```bash
# Remove installation
rm -rf /opt/vps-configurator
userdel -r vpsconfig

# Start from Step 2
```

**Option 3: Emergency Access**

```bash
# If locked out, use console/VNC
# Re-enable root SSH temporarily
sed -i 's/PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Debug and fix issue
# Then disable root again
```

---

## 📊 POST-DEPLOYMENT MONITORING

### Week 1: Daily Monitoring

**Daily checks (15 minutes):**

- [ ] Check system logs for errors
- [ ] Verify all services running
- [ ] Review failed login attempts
- [ ] Check disk space
- [ ] Confirm backups completed

### Month 1: Weekly Review

**Weekly tasks (30 minutes):**

- [ ] Review security scan results
- [ ] Check certificate expiration
- [ ] Review user activity logs
- [ ] Test backup restoration
- [ ] Update documentation

### Ongoing: Monthly Maintenance

**Monthly tasks (1 hour):**

- [ ] Apply system updates
- [ ] Review and rotate logs
- [ ] Audit user access
- [ ] Test disaster recovery
- [ ] Performance tuning

---

## 🆘 EMERGENCY CONTACTS

### Critical Issues

**System Down:**

1. Check systemd service: `systemctl status vps-configurator`
2. Check logs: `/var/log/vps-configurator/main.log`
3. Restart service: `systemctl restart vps-configurator`

**Locked Out:**

1. Use console/VNC access
2. Review `/var/log/auth.log`
3. Temporarily enable root SSH if needed

**Data Loss:**

1. Stop all services immediately
2. Restore from latest backup
3. Verify data integrity

### Support Escalation

1. **Level 1:** Check documentation
2. **Level 2:** Review logs and troubleshooting guide
3. **Level 3:** Contact team lead
4. **Level 4:** External support (if applicable)

---

## 📝 POST-DEPLOYMENT DOCUMENTATION

### Update These Documents

- [ ] Server inventory (add new server details)
- [ ] Network diagram (add VPS configurator)
- [ ] Backup procedures (include new backup locations)
- [ ] Disaster recovery plan (add rollback procedures)
- [ ] Team access list (update with new users)

### Create These Documents

- [ ] Server credentials (store securely!)
- [ ] Backup restoration procedure
- [ ] Incident response plan
- [ ] Maintenance schedule

---

## ✅ DEPLOYMENT COMPLETION CHECKLIST

### Technical Validation

- [ ] Application installed and running
- [ ] Configuration file reviewed and customized
- [ ] Security hardening completed (CIS 90%+)
- [ ] SSL certificate issued and valid
- [ ] SSH hardened (root disabled)
- [ ] Firewall configured
- [ ] Users created and tested
- [ ] 2FA enforced
- [ ] Backups configured and tested
- [ ] Monitoring active
- [ ] Cron jobs scheduled
- [ ] Logs rotating properly

### Operational Validation

- [ ] Admin users can login
- [ ] All core features tested
- [ ] Health check passes
- [ ] Team notified
- [ ] Documentation updated
- [ ] Support procedures defined
- [ ] Emergency contacts documented

### Sign-off

```
Deployment completed by: ___________________
Date: ___________________
Production ready: [ ] Yes  [ ] No
Sign-off: ___________________
```

---

**END OF PRODUCTION DEPLOYMENT GUIDE**

🎉 **Congratulations! Your VPS Configurator is now in production!**

---

## 📞 QUICK REFERENCE

### Essential Commands

```bash
# Service management
systemctl status vps-configurator
systemctl restart vps-configurator

# Health check
vps-configurator health-check

# View logs
tail -f /var/log/vps-configurator/main.log

# Manual backup
/opt/vps-configurator/scripts/backup.sh

# Security scan
vps-configurator security cis-scan
```

### Important Paths

```
Config:    /etc/debian-vps-configurator/config.yaml
Env:      /opt/vps-configurator/.env
Logs:     /var/log/vps-configurator/
Data:     /var/lib/debian-vps-configurator/
Backups:  /opt/vps-configurator/backups/
```

### Emergency

```bash
# If system is broken
systemctl stop vps-configurator
systemctl start vps-configurator --debug

# If locked out
# Use console access, re-enable root SSH temporarily
```
