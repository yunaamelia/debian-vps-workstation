# Autonomous Deployment Toolkit

## Created Scripts

1. **autonomous_deploy.sh** - Main deployment script
2. **deploy_monitor.py** - Error detection wrapper

## Quick Start

```bash
# Set environment variables
export REMOTE_HOST="<your-server-ip>"
export REMOTE_PASS="your_password"
export TARGET_USER="devtest"
export TARGET_PASS="target_password"

# Execute deployment
cd /home/racoon/Desktop/debian-vps-workstation/scripts
./autonomous_deploy.sh

# OR with monitoring
python3 deploy_monitor.py
```

## Security Warning

**IMPORTANT**: These scripts use plaintext passwords. For production:
- Use SSH keys instead of passwords
- Store credentials in environment variables or secrets manager
- Never commit credentials to version control
- Review all scripts before execution

## What It Does

1. **User Provisioning**: Creates user on remote server
2. **File Transfer**: Copies project files via SCP
3. **Execution**: Runs installation script
4. **Monitoring**: Detects errors and provides feedback

## Error Detection

Monitors for:
- Missing dependencies
- Permission issues
- Network failures
- Python exceptions

Aborts after 3 consecutive identical errors.
