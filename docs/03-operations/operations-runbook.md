# OPERATIONS RUNBOOK

**Debian VPS Configurator - Day-to-Day Operations Guide**
**Standard Operating Procedures for Small Teams**
**Date:** January 6, 2026

---

## 🎯 OVERVIEW

This runbook provides **standard operating procedures (SOPs)** for managing Debian VPS Configurator in production. It covers daily operations, common maintenance tasks, and emergency procedures.

**Target Audience:** System administrators, on-call engineers
**Purpose:** Quick reference for operational tasks
**Scope:** Day-to-day operations, not installation/deployment

---

## 📋 TABLE OF CONTENTS

1. [Daily Operations](#daily-operations)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Tasks](#monthly-tasks)
4. [User Management](#user-management)
5. [Security Operations](#security-operations)
6. [Backup & Restore](#backup-restore)
7. [Monitoring & Alerts](#monitoring-alerts)
8. [Troubleshooting](#troubleshooting)
9. [Emergency Procedures](#emergency-procedures)
10. [Contact Information](#contact-information)

---

## ⏰ DAILY OPERATIONS (15 minutes)

### Morning Health Check (5 minutes)

**Time:** Start of business day
**Frequency:** Daily (Monday-Friday)

```bash
# 1. SSH into server
ssh admin-yourname@vps.company.com

# 2. Run health check
vps-configurator health-check

# 3. Review output for any ⚠️ or ❌
# Expected: All ✅ green checks
```

**What to look for:**

- ✅ All services running
- ✅ Disk space < 80%
- ✅ Memory usage < 80%
- ✅ No critical errors in logs
- ✅ Backups completed within 24h
- ✅ SSL certificates valid

**If any issues:**

1. Note the specific error
2. Check [Troubleshooting](#troubleshooting) section
3. If unresolved, escalate to team lead

---

### Check Overnight Logs (5 minutes)

```bash
# View last 50 lines of main log
tail -50 /var/log/vps-configurator/main.log

# Check for ERROR or CRITICAL
grep -i "error\|critical" /var/log/vps-configurator/main.log | tail -20

# Check failed login attempts
sudo grep "Failed" /var/log/auth.log | tail -20
```

**Red flags to watch for:**

- 🚨 Multiple failed login attempts (>10)
- 🚨 ERROR messages about database
- 🚨 CRITICAL security alerts
- 🚨 Service restart failures
- 🚨 Disk space warnings

**Actions:**

- Document any issues found
- If critical, follow [Emergency Procedures](#emergency-procedures)
- If minor, add to weekly review list

---

### Review Scheduled Tasks (5 minutes)

```bash
# Check cron job results
ls -lth /var/log/cron.log | head -20

# Verify last backup
ls -lth /opt/vps-configurator/backups/ | head -5

# Check security scan results (if scheduled)
vps-configurator security last-scan-results
```

**Expected:**

- ✅ Daily backup completed (1 AM)
- ✅ Vulnerability scan completed (3 AM)
- ✅ No cron job failures

**If backup failed:**

1. Check disk space: `df -h`
2. Check logs: `tail -100 /var/log/vps-configurator/backup.log`
3. Run manual backup: `/opt/vps-configurator/scripts/backup.sh`

---

### Quick Checklist (Daily)

```
[ ] Health check passed
[ ] No critical errors in logs
[ ] No suspicious login attempts
[ ] Backups completed successfully
[ ] Disk space < 80%
[ ] All services running
[ ] Any alerts addressed
```

**Time commitment:** 15 minutes/day
**Best time:** Morning (9:00 AM)

---

## 🗓️ WEEKLY MAINTENANCE (30 minutes)

### Security Review (15 minutes)

**Time:** Every Monday, 10:00 AM
**Frequency:** Weekly

```bash
# 1. Run vulnerability scan
vps-configurator security vuln-scan

# 2. Review results
vps-configurator security vuln-report --severity high,critical

# 3. Check for package updates
apt list --upgradable

# 4. Review user activity
vps-configurator activity report --last 7d --anomalies-only
```

**Action items:**

- Prioritize CRITICAL vulnerabilities (fix within 24h)
- Schedule HIGH vulnerabilities (fix within 7 days)
- Note MEDIUM for next maintenance window
- Investigate any anomalies in user activity

---

### User Access Review (10 minutes)

```bash
# 1. List all users
vps-configurator user list

# 2. Check temporary access expiring soon
vps-configurator temp-access list --expiring-soon

# 3. Check inactive users (no login 30+ days)
vps-configurator user list --inactive 30

# 4. Review 2FA status
vps-configurator mfa status --all
```

**Actions:**

- Remind users with expiring access
- Contact inactive users (verify still need access)
- Follow up with users without 2FA
- Remove/offboard users who left company

---

### Log Review (5 minutes)

```bash
# 1. Check log file sizes
du -sh /var/log/vps-configurator/*

# 2. Review error summary
grep -c "ERROR" /var/log/vps-configurator/main.log

# 3. Top error messages
grep "ERROR" /var/log/vps-configurator/main.log | sort | uniq -c | sort -rn | head -10
```

**Actions:**

- If logs > 1GB, verify log rotation working
- Investigate recurring errors
- Document any patterns observed

---

### Weekly Checklist

```
[ ] Vulnerability scan completed
[ ] High/Critical vulns addressed
[ ] User access reviewed
[ ] Expiring access handled
[ ] Inactive users contacted
[ ] Logs reviewed for patterns
[ ] Backup verification (restore test)
```

**Time commitment:** 30 minutes/week
**Best time:** Monday morning

---

## 📅 MONTHLY TASKS (1-2 hours)

### Comprehensive Security Audit (30 minutes)

**Time:** First Monday of each month
**Frequency:** Monthly

```bash
# 1. Full CIS benchmark scan
vps-configurator security cis-scan

# 2. Review compliance score
vps-configurator security cis-report --summary

# 3. Check SSH key rotation status
vps-configurator ssh list-keys --expiring 30

# 4. Review sudo policy usage
vps-configurator sudo audit --last 30d
```

**Actions:**

- If compliance < 90%, create remediation plan
- Rotate SSH keys expiring in next 30 days
- Review sudo usage for anomalies
- Update security documentation

---

### System Updates (30 minutes)

**Time:** Second Saturday of each month (maintenance window)
**Frequency:** Monthly

```bash
# 1. Create pre-update backup
/opt/vps-configurator/scripts/backup.sh

# 2. Update package list
sudo apt update

# 3. Review available updates
apt list --upgradable

# 4. Apply security updates
sudo apt upgrade -y

# 5. Reboot if kernel updated
# Check if reboot required
[ -f /var/run/reboot-required ] && echo "Reboot required"

# 6. Schedule reboot during maintenance window
sudo shutdown -r +5 "System reboot for updates in 5 minutes"
```

**⚠️ Important:**

- Notify team 24h before maintenance
- Perform during low-usage time (e.g., Saturday 2 AM)
- Have rollback plan ready
- Test after reboot

---

### User Account Cleanup (20 minutes)

```bash
# 1. List inactive users (90+ days)
vps-configurator user list --inactive 90

# 2. List expired temporary access
vps-configurator temp-access list --expired

# 3. Review team memberships
vps-configurator team list --include-members

# 4. Audit user permissions
vps-configurator rbac audit-permissions
```

**Actions:**

- Offboard inactive users (with manager approval)
- Archive expired temporary access data
- Remove users from teams they no longer need
- Document all changes

---

### Backup Verification (30 minutes)

```bash
# 1. List recent backups
ls -lh /opt/vps-configurator/backups/ | head -10

# 2. Verify backup integrity
tar -tzf /opt/vps-configurator/backups/[latest-backup].tar.gz > /dev/null
echo "Backup integrity: $?"  # Should be 0

# 3. Test restore (on test system if available)
mkdir -p /tmp/restore-test
tar -xzf /opt/vps-configurator/backups/[latest-backup].tar.gz -C /tmp/restore-test

# 4. Verify restored files
ls -la /tmp/restore-test/etc/debian-vps-configurator/

# 5. Cleanup
rm -rf /tmp/restore-test
```

**Success criteria:**

- ✅ Backup files exist and accessible
- ✅ No corruption errors
- ✅ All expected files present
- ✅ Can restore successfully

---

### Performance Review (20 minutes)

```bash
# 1. Check system resources
vps-configurator system-stats

# 2. Database size
du -sh /var/lib/debian-vps-configurator/activity/activity.db

# 3. Cache usage
du -sh /var/cache/vps-configurator/

# 4. Review slow operations
grep "took.*[5-9][0-9][0-9][0-9]ms" /var/log/vps-configurator/main.log
```

**Actions:**

- If DB > 5GB, consider archiving old data
- If cache > 10GB, clear old cache
- Investigate slow operations
- Plan performance optimization if needed

---

### Monthly Checklist

```
[ ] Full security audit completed
[ ] System updates applied
[ ] System rebooted (if needed)
[ ] Inactive users offboarded
[ ] Backup restore tested
[ ] Performance reviewed
[ ] Monthly report generated
[ ] Documentation updated
```

**Time commitment:** 1-2 hours/month
**Best time:** First Saturday (maintenance window)

---

## 👥 USER MANAGEMENT OPERATIONS

### Creating a New User (5 minutes)

**Scenario:** New employee joins team

```bash
# 1. Create user account
vps-configurator user create [username] \
  --full-name "First Last" \
  --email user@company.com \
  --role [developer|devops|admin|viewer] \
  --enable-2fa \
  --generate-ssh-key

# 2. Save credentials securely
# - Temporary password (shown in output)
# - SSH private key location
# - 2FA QR code location
# - Backup codes location

# 3. Send welcome email (manual or automated)
cat /home/[username]/.welcome-info.txt | mail -s "VPS Access" user@company.com

# 4. Add to relevant teams
vps-configurator team add-member [team-name] [username]

# 5. Verify user can login
# Ask user to test: ssh [username]@vps.company.com
```

**Documentation:**

- Add user to team roster
- Document role assignment rationale
- Note any special permissions

---

### Offboarding a User (10 minutes)

**Scenario:** Employee leaves company

```bash
# 1. Confirm offboarding approval
# Check with HR/manager first!

# 2. Review user's access
vps-configurator user info [username]

# 3. Check team memberships
vps-configurator team list --member [username]

# 4. Check file ownership in shared dirs
find /var/projects -user [username] -ls

# 5. Offboard user (automated process)
vps-configurator user offboard [username] \
  --reason "Employment ended" \
  --transfer-files-to [new-owner] \
  --generate-report

# 6. Verify offboarding complete
vps-configurator user info [username]
# Should show: Status: OFFBOARDED

# 7. Save offboarding report
cp /var/reports/offboarding-[username]-*.pdf /secure/archive/
```

**Offboarding checklist:**

- [ ] Manager approval documented
- [ ] User account disabled
- [ ] SSH keys revoked
- [ ] 2FA disabled
- [ ] RBAC permissions removed
- [ ] Team memberships removed
- [ ] Files transferred/archived
- [ ] Offboarding report generated
- [ ] HR notified of completion

---

### Granting Temporary Access (5 minutes)

**Scenario:** Contractor needs 30-day access

```bash
# 1. Get approval
# Document who approved and why

# 2. Grant temporary access
vps-configurator temp-access grant contractor-[name] \
  --full-name "Contractor Name" \
  --email contractor@company.com \
  --role developer \
  --duration 30d \
  --reason "Q1 2026 project work" \
  --notify-before 7d

# 3. Document in tracking sheet
# Add to: /docs/temporary-access-log.txt

# 4. Setup calendar reminder
# Reminder 7 days before expiration to evaluate extension

# 5. Send credentials to contractor
# Use secure method (encrypted email, password manager)
```

**Notes:**

- Max duration: 90 days
- Extensions require re-approval
- Auto-revocation on expiration
- All activity logged

---

### Extending Temporary Access (3 minutes)

**Scenario:** Contractor needs 2 more weeks

```bash
# 1. Verify extension approval
# Check with project manager

# 2. Request extension
vps-configurator temp-access extend contractor-[name] \
  --days 14 \
  --reason "Project extended 2 weeks" \
  --requested-by [your-username]

# 3. If auto-approved:
# Extension applied immediately

# 4. If manual approval required:
# Wait for security team approval

# 5. Notify contractor of extension
mail -s "Access Extended" contractor@company.com <<EOF
Your access has been extended by 14 days.
New expiration: [date]
EOF
```

---

### Resetting User Password (3 minutes)

**Scenario:** User forgot password

```bash
# 1. Verify user identity
# Use alternative communication channel (phone, Slack)

# 2. Reset password
vps-configurator user reset-password [username] \
  --generate-temp

# 3. Temporary password shown in output
# Send via secure channel (encrypted chat, voice call)

# 4. User must change on next login
# Password expires after first use

# 5. Log the reset
echo "$(date): Password reset for [username] by [admin]" >> /var/log/vps-configurator/admin-actions.log
```

---

### Resetting 2FA (5 minutes)

**Scenario:** User lost phone/authenticator app

```bash
# 1. Verify user identity strongly
# Use video call or in-person verification

# 2. Check if user has backup codes
# Ask user to try backup codes first

# 3. If no backup codes, reset 2FA
vps-configurator mfa reset --user [username]

# 4. Generate new 2FA enrollment
vps-configurator mfa setup --user [username]

# 5. Send new QR code securely
# Use encrypted email or password manager

# 6. Log the reset
echo "$(date): 2FA reset for [username] by [admin] - Reason: Lost device" >> /var/log/vps-configurator/security-actions.log

# 7. Monitor user's next logins
# Watch for suspicious activity
```

**⚠️ Security note:**

- 2FA resets are sensitive operations
- Require strong identity verification
- Log all resets
- Monitor user activity after reset

---

## 🔒 SECURITY OPERATIONS

### Responding to Failed Login Attempts (5 minutes)

**Scenario:** Multiple failed logins detected

```bash
# 1. Check failed login attempts
sudo grep "Failed password" /var/log/auth.log | tail -50

# 2. Identify source IPs
sudo grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn

# 3. Check if legitimate user
# Contact user if it's their IP

# 4. If attack, block IP
sudo ufw deny from [attacker-ip]

# 5. Check fail2ban status
sudo fail2ban-client status sshd

# 6. Document incident
cat >> /var/log/vps-configurator/security-incidents.log <<EOF
$(date): Multiple failed logins detected
Source: [IP address]
Target user: [username]
Action: IP blocked
EOF
```

**Escalate if:**

- > 50 failed attempts from single IP
- Multiple IPs attacking simultaneously
- Successful breach suspected
- Legitimate user account compromised

---

### Handling Security Alerts (10-30 minutes)

**Scenario:** Anomaly detection alert received

```bash
# 1. Review the alert
vps-configurator activity anomalies --last 24h

# 2. Get detailed information
vps-configurator activity report --user [flagged-user] --last 7d

# 3. Check what triggered alert
# Examples:
# - Unusual login time (3 AM)
# - New IP address
# - Suspicious commands
# - Bulk file downloads

# 4. Investigate legitimacy
# Contact user: "Were you working at 3 AM yesterday?"

# 5. If legitimate:
vps-configurator activity anomaly-dismiss [anomaly-id] \
  --reason "User confirmed working late"

# 6. If suspicious:
# Follow incident response procedure below
```

---

### Incident Response Procedure (30-60 minutes)

**Scenario:** Security incident confirmed

**IMMEDIATE ACTIONS (5 minutes):**

```bash
# 1. Suspend affected user(s)
vps-configurator user suspend [username] \
  --reason "Security incident INC-[date]-001"

# 2. Document incident start
cat > /var/log/incidents/INC-$(date +%Y%m%d)-001.txt <<EOF
INCIDENT: INC-$(date +%Y%m%d)-001
Started: $(date)
Affected user: [username]
Description: [brief description]
Severity: [LOW/MEDIUM/HIGH/CRITICAL]
Status: INVESTIGATING
EOF

# 3. Notify security team
# Email/Slack security team immediately

# 4. Preserve evidence
cp /var/log/vps-configurator/activity-audit.log /var/log/incidents/
vps-configurator activity report --user [username] --last 30d > /var/log/incidents/user-activity.txt
```

**INVESTIGATION (15-30 minutes):**

```bash
# 5. Analyze user activity
vps-configurator activity report --user [username] --detailed

# 6. Check commands executed
grep "COMMAND" /var/log/sudo.log | grep [username]

# 7. Check files accessed
grep [username] /var/log/vps-configurator/file-access.log

# 8. Identify scope
# What data accessed?
# What systems affected?
# When did it start?

# 9. Document findings
vim /var/log/incidents/INC-$(date +%Y%m%d)-001-findings.txt
```

**CONTAINMENT (10-15 minutes):**

```bash
# 10. Revoke all access
vps-configurator user offboard [username] --immediate

# 11. Rotate compromised credentials
# If SSH keys compromised:
vps-configurator ssh rotate-all-keys --emergency

# If sudo used:
vps-configurator sudo revoke-all [username]

# 12. Check for backdoors
vps-configurator security scan-backdoors

# 13. Update firewall rules if needed
sudo ufw [add rules]
```

**POST-INCIDENT (ongoing):**

```bash
# 14. Generate incident report
vps-configurator incident report INC-$(date +%Y%m%d)-001

# 15. Lessons learned meeting
# Schedule with team

# 16. Update security procedures
# Document what worked, what didn't

# 17. Close incident
vim /var/log/incidents/INC-$(date +%Y%m%d)-001.txt
# Add resolution and close
```

---

### Certificate Renewal (10 minutes)

**Scenario:** SSL certificate expiring soon

```bash
# 1. Check certificate status
vps-configurator ssl check vps.company.com

# 2. If < 30 days, renew
vps-configurator ssl renew vps.company.com

# 3. Verify new certificate
vps-configurator ssl check vps.company.com
# Should show new expiration date

# 4. Test HTTPS
curl -I https://vps.company.com

# 5. Document renewal
echo "$(date): SSL certificate renewed for vps.company.com" >> /var/log/vps-configurator/ssl-renewals.log
```

**Note:** Auto-renewal should handle this, but manual renewal needed if:

- Auto-renewal failed
- DNS changed
- New domains added

---

## 💾 BACKUP & RESTORE OPERATIONS

### Manual Backup (5 minutes)

**Scenario:** Before major changes

```bash
# 1. Run backup script
/opt/vps-configurator/scripts/backup.sh

# 2. Verify backup created
ls -lh /opt/vps-configurator/backups/ | head -1

# 3. Test backup integrity
tar -tzf /opt/vps-configurator/backups/[latest].tar.gz > /dev/null
echo "Backup status: $?"  # 0 = success

# 4. Document backup
echo "$(date): Manual backup before [reason]" >> /opt/vps-configurator/backups/backup.log
```

---

### Restore from Backup (15-30 minutes)

**Scenario:** Data corruption or accidental deletion

**⚠️ CAUTION: This will overwrite current data!**

```bash
# 1. Stop services
sudo systemctl stop vps-configurator

# 2. List available backups
ls -lth /opt/vps-configurator/backups/

# 3. Choose backup to restore
BACKUP_FILE="vps-config-backup-[timestamp].tar.gz"

# 4. Create safety backup of current state
tar -czf /tmp/pre-restore-backup-$(date +%Y%m%d).tar.gz \
  /etc/debian-vps-configurator \
  /var/lib/debian-vps-configurator

# 5. Restore from backup
tar -xzf /opt/vps-configurator/backups/$BACKUP_FILE -C /

# 6. Verify restored files
ls -la /etc/debian-vps-configurator/
ls -la /var/lib/debian-vps-configurator/

# 7. Fix permissions
chown -R vpsconfig:vpsconfig /var/lib/debian-vps-configurator
chmod 600 /opt/vps-configurator/.env

# 8. Restart services
sudo systemctl start vps-configurator

# 9. Verify system working
vps-configurator health-check

# 10. Document restore
cat >> /var/log/vps-configurator/restore.log <<EOF
$(date): Restored from backup: $BACKUP_FILE
Reason: [reason]
Performed by: [admin]
Status: [SUCCESS/FAILED]
EOF
```

**Post-restore verification:**

- [ ] All services running
- [ ] Users can login
- [ ] Data intact
- [ ] No errors in logs

---

### Remote Backup Verification (10 minutes)

**Scenario:** Verify offsite backups

```bash
# 1. List remote backups (if using rclone)
rclone ls remote:backups/vps-configurator/

# 2. Check last backup date
rclone ls remote:backups/vps-configurator/ | tail -1

# 3. Download latest for verification
rclone copy remote:backups/vps-configurator/[latest] /tmp/

# 4. Verify integrity
tar -tzf /tmp/[latest].tar.gz > /dev/null

# 5. Cleanup
rm /tmp/[latest].tar.gz

# 6. Document verification
echo "$(date): Remote backup verified" >> /opt/vps-configurator/backups/verification.log
```

---

## 📊 MONITORING & ALERTS

### Checking System Health (5 minutes)

```bash
# Comprehensive health check
vps-configurator health-check --detailed

# Specific checks:

# CPU usage
top -bn1 | head -5

# Memory usage
free -h

# Disk usage
df -h

# Service status
systemctl status vps-configurator

# Network connectivity
ping -c 4 8.8.8.8

# DNS resolution
nslookup vps.company.com
```

---

### Reviewing Metrics (10 minutes)

```bash
# Activity metrics
vps-configurator metrics activity --last 7d

# Security metrics
vps-configurator metrics security --last 7d

# Performance metrics
vps-configurator metrics performance --last 7d

# User metrics
vps-configurator metrics users --last 7d
```

---

### Setting Up Alerts (15 minutes)

**Configure email alerts:**

```bash
# Edit config
sudo vim /etc/debian-vps-configurator/config.yaml
```

```yaml
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_user: alerts@company.com
    from_address: vps-configurator@company.com

  alerts:
    disk_usage_threshold: 80
    memory_usage_threshold: 85
    failed_logins_threshold: 10
    certificate_expiry_days: 30

  recipients:
    critical: admin@company.com, oncall@company.com
    warning: team@company.com
    info: logs@company.com
```

**Test alerts:**

```bash
# Send test email
vps-configurator alert test --email admin@company.com

# Trigger test alert
vps-configurator alert trigger --type test
```

---

## 🔧 TROUBLESHOOTING QUICK REFERENCE

### Service Won't Start

```bash
# Check status
systemctl status vps-configurator

# Check logs
journalctl -u vps-configurator -n 50

# Common fixes:
# 1. Check config syntax
vps-configurator config validate

# 2. Check file permissions
ls -la /opt/vps-configurator/.env
# Should be 600

# 3. Check disk space
df -h

# 4. Restart service
sudo systemctl restart vps-configurator
```

---

### User Can't Login

```bash
# 1. Check user status
vps-configurator user info [username]

# 2. Check SSH logs
sudo grep [username] /var/log/auth.log | tail -20

# 3. Common issues:
# - Account suspended: vps-configurator user activate [username]
# - SSH key issue: vps-configurator ssh verify [username]
# - 2FA issue: Help user with backup codes
# - Expired temp access: Extend or renew

# 4. Test from server
su - [username]
```

---

### Backup Failed

```bash
# 1. Check disk space
df -h /opt/vps-configurator/backups/

# 2. Check permissions
ls -la /opt/vps-configurator/backups/

# 3. Check logs
tail -50 /opt/vps-configurator/backups/backup.log

# 4. Run manual backup with verbose
/opt/vps-configurator/scripts/backup.sh -v

# 5. If still failing, check cron
crontab -l | grep backup
```

---

### High CPU/Memory Usage

```bash
# 1. Identify process
top -bn1

# 2. Check vps-configurator processes
ps aux | grep vps-configurator

# 3. Check for runaway jobs
vps-configurator jobs list --running

# 4. If needed, restart service
sudo systemctl restart vps-configurator

# 5. Monitor for 10 minutes
watch -n 10 'free -h && echo "---" && df -h'
```

---

## 🚨 EMERGENCY PROCEDURES

### System Completely Down

**Priority: CRITICAL**
**Response Time: Immediate**

```bash
# 1. Check if server is reachable
ping vps.company.com

# 2. If no response, use console access (provider dashboard)

# 3. Check basic services
systemctl status sshd
systemctl status vps-configurator

# 4. Check disk space (common cause)
df -h

# 5. Check memory
free -h

# 6. Review crash logs
dmesg | tail -50

# 7. Attempt service restart
systemctl restart vps-configurator

# 8. If still down, restore from backup
# Follow restore procedure

# 9. Document incident
# Create incident report
```

---

### Security Breach Suspected

**Priority: CRITICAL**
**Response Time: Immediate**

```bash
# 1. ISOLATE IMMEDIATELY
# Disconnect from network if needed
sudo ufw default deny incoming
sudo ufw default deny outgoing
# Keep only SSH for admin
sudo ufw allow from [admin-ip] to any port 22

# 2. Preserve evidence
cp -r /var/log /secure-location/incident-$(date +%Y%m%d)/

# 3. Suspend all users except admins
vps-configurator user suspend-all --except admin-*

# 4. Review recent activity
vps-configurator activity report --last 48h --all-users

# 5. Contact security team/vendor

# 6. Follow incident response procedure (see above)

# 7. Do NOT proceed without guidance
```

---

### Data Loss / Corruption

**Priority: HIGH**
**Response Time: Within 1 hour**

```bash
# 1. STOP all writes immediately
sudo systemctl stop vps-configurator

# 2. Identify scope
# What data is affected?
# When did it happen?

# 3. Check if recoverable from logs
# Activity database might have history

# 4. Restore from most recent clean backup
# Follow restore procedure

# 5. Verify restored data
vps-configurator data verify

# 6. Document data loss
# What was lost?
# Impact assessment
# Root cause

# 7. Resume operations
sudo systemctl start vps-configurator
```

---

### Certificate Expired

**Priority: HIGH**
**Response Time: Within 2 hours**

```bash
# 1. Check certificate status
vps-configurator ssl check vps.company.com

# 2. Attempt immediate renewal
vps-configurator ssl renew vps.company.com --force

# 3. If Let's Encrypt having issues, use alternative
# Manual certificate from another CA
# Or use self-signed temporarily

# 4. Update certificate
vps-configurator ssl install --cert [path] --key [path]

# 5. Verify HTTPS working
curl -I https://vps.company.com

# 6. Notify team
# Service may have been disrupted

# 7. Investigate why auto-renewal failed
grep "ssl" /var/log/vps-configurator/main.log | tail -50
```

---

### Locked Out of System

**Priority: HIGH**
**Response Time: Within 1 hour**

```bash
# 1. Use console access (VPS provider dashboard)

# 2. Login as root via console

# 3. Check what's wrong
systemctl status sshd
cat /etc/ssh/sshd_config

# 4. Temporarily re-enable root SSH if needed
sed -i 's/PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd

# 5. Fix the actual issue
# User account? SSH keys? Firewall?

# 6. Test new admin access
# Create new admin user or fix existing

# 7. Disable root SSH again
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# 8. Document what caused lockout
```

---

## 📞 CONTACT INFORMATION

### Internal Contacts

**Primary Admin:**

- Name: [Your Name]
- Email: <admin@company.com>
- Phone: [Phone]
- Availability: 24/7 for critical issues

**Secondary Admin:**

- Name: [Backup Admin]
- Email: <backup-admin@company.com>
- Phone: [Phone]
- Availability: Business hours + on-call rotation

**Team Lead:**

- Name: [Team Lead]
- Email: <lead@company.com>
- Phone: [Phone]
- Escalation: Major incidents, policy decisions

---

### External Contacts

**VPS Provider Support:**

- Provider: [e.g., DigitalOcean, AWS, Linode]
- Support Portal: [URL]
- Support Email: <support@provider.com>
- Phone: [Support Phone]
- Account ID: [Account]

**Domain/DNS Provider:**

- Provider: [e.g., Cloudflare, Route53]
- Support: [Contact info]

**Email Provider (for alerts):**

- Provider: [e.g., Gmail, SendGrid]
- Support: [Contact info]

---

### Escalation Matrix

**Level 1: Self-service (0-30 minutes)**

- Check documentation
- Review logs
- Common troubleshooting

**Level 2: Team discussion (30-60 minutes)**

- Consult with team
- Review runbook
- Search community forums

**Level 3: Admin escalation (1-2 hours)**

- Contact primary/secondary admin
- Senior team members
- Subject matter experts

**Level 4: External support (2+ hours)**

- VPS provider support
- Vendor support
- Security consultants

**Level 5: Management (Critical only)**

- CTO/Technical Director
- For business-critical outages
- Security breaches
- Data loss events

---

## 📋 CHECKLISTS

### Daily Operations Checklist

```
[ ] Morning health check completed
[ ] Logs reviewed for errors
[ ] Failed login attempts checked
[ ] Backups verified
[ ] Disk space checked
[ ] Any alerts addressed
[ ] Documentation updated (if changes made)

Time: 15 minutes
Frequency: Daily (M-F)
```

### Weekly Maintenance Checklist

```
[ ] Vulnerability scan completed
[ ] Critical/High vulns addressed
[ ] User access reviewed
[ ] Temporary access managed
[ ] Inactive users contacted
[ ] 2FA status verified
[ ] Log patterns analyzed
[ ] Backup restore tested

Time: 30 minutes
Frequency: Weekly (Monday)
```

### Monthly Maintenance Checklist

```
[ ] Full CIS security audit
[ ] System updates applied
[ ] System rebooted (if needed)
[ ] User account cleanup
[ ] Backup verification (full restore test)
[ ] Performance review completed
[ ] Monthly report generated
[ ] Documentation updated
[ ] Compliance review (if applicable)

Time: 1-2 hours
Frequency: Monthly (First Saturday)
```

---

## 📝 LOGGING STANDARDS

### When to Log

**Always log:**

- User creation/deletion
- Role changes
- Permission changes
- Security incidents
- System configuration changes
- Backup/restore operations
- Service restarts
- Emergency procedures

### How to Log

```bash
# Standard log format:
# [ISO 8601 timestamp] [LEVEL] [Component] Message

# Example:
echo "$(date -Iseconds) INFO [UserMgmt] Created user: johndoe" >> /var/log/vps-configurator/admin-actions.log

# Severity levels:
# DEBUG - Detailed information for debugging
# INFO - General informational messages
# WARNING - Warning messages, not errors
# ERROR - Error messages, service continues
# CRITICAL - Critical errors, service may stop
```

### Log Locations

```
Main log:           /var/log/vps-configurator/main.log
Security log:       /var/log/vps-configurator/security.log
Audit log:          /var/log/vps-configurator/admin-actions.log
Backup log:         /opt/vps-configurator/backups/backup.log
Incident log:       /var/log/incidents/
```

---

## 🎓 TRAINING RESOURCES

### New Team Member Onboarding

**Week 1: Read-only access**

- Review this runbook
- Shadow current admin
- Practice commands on test system

**Week 2: Supervised access**

- Perform daily checks with supervision
- Practice user management
- Learn backup/restore

**Week 3: Independent operations**

- Perform daily/weekly tasks independently
- Handle routine user requests
- On-call shadowing

**Week 4: On-call ready**

- Handle emergency procedures with backup
- Full access granted
- Added to on-call rotation

---

### Command Reference Card

```bash
# Quick reference for daily use

# Health
vps-configurator health-check

# Users
vps-configurator user create [username] --role [role]
vps-configurator user list
vps-configurator user info [username]
vps-configurator user offboard [username]

# Security
vps-configurator security cis-scan
vps-configurator security vuln-scan

# Backup
/opt/vps-configurator/scripts/backup.sh

# Logs
tail -f /var/log/vps-configurator/main.log
grep ERROR /var/log/vps-configurator/main.log

# Service
systemctl status vps-configurator
systemctl restart vps-configurator
```

---

## 📊 METRICS & REPORTING

### Weekly Report Template

```
VPS Configurator - Weekly Report
Week of: [Date] to [Date]

SYSTEM HEALTH:
- Uptime: [percentage]
- Average load: [load]
- Disk usage: [percentage]
- Memory usage: [percentage]

SECURITY:
- Security scans: [count]
- Vulnerabilities found: [count]
- Critical: [count] (all resolved)
- High: [count] ([resolved count] resolved)
- Failed login attempts: [count]

USERS:
- Active users: [count]
- New users: [count]
- Offboarded: [count]
- 2FA adoption: [percentage]

OPERATIONS:
- Backups: [success count]/[total count]
- Incidents: [count]
- User requests: [count]

NOTES:
[Any notable events or issues]
```

---

## ✅ RUNBOOK COMPLETION

### Runbook Maintenance

This runbook should be reviewed and updated:

- **Monthly:** Update contact info, add new procedures
- **Quarterly:** Full review, remove outdated info
- **Annually:** Complete rewrite if needed

Last updated: [Date]
Next review: [Date]

---

**END OF OPERATIONS RUNBOOK**

📖 **This runbook is your day-to-day operations bible. Bookmark it!**
