#!/bin/bash
# Safe deployment wrapper - review before use

echo "=== Autonomous Deployment Toolkit ==="
echo ""
echo "Available scripts:"
echo "  1. autonomous_deploy.sh - Direct deployment"
echo "  2. deploy_monitor.py - Deployment with error monitoring"
echo ""
echo "SECURITY NOTICE: Set credentials as environment variables"
echo ""
echo "Required variables:"
echo "  - REMOTE_HOST (target server IP)"
echo "  - REMOTE_PASS (root password)"
echo "  - TARGET_USER (user to create, default: devtest)"
echo "  - TARGET_PASS (target user password)"
echo ""
if [[ -z "$REMOTE_HOST" ]]; then
    echo "ERROR: REMOTE_HOST not set"
    echo "Example: export REMOTE_HOST=209.38.91.97"
    exit 1
fi

if [[ -z "$REMOTE_PASS" ]]; then
    echo "ERROR: REMOTE_PASS not set"
    echo "Example: export REMOTE_PASS=your_password"
    exit 1
fi

echo "Configuration:"
echo "  Host: $REMOTE_HOST"
echo "  User: ${REMOTE_USER:-root}"
echo "  Target: ${TARGET_USER:-devtest}"
echo ""
read -p "Continue with deployment? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Starting deployment..."
python3 deploy_monitor.py
