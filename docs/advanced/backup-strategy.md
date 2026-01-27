# Backup Strategy

## What is Backed Up?

* Configuration files modified by the tool.
* State database (`state.db`).
* User data (if configured).

## Backup Location

Backups are stored in `/var/backups/vps-configurator/` by default.

## Restoration

To restore a file:

```bash
cp /var/backups/vps-configurator/timestamp/etc/ssh/sshd_config /etc/ssh/sshd_config
```
