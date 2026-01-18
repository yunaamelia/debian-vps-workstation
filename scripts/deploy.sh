#!/bin/bash
# SECURITY: Use env var or argument, do not hardcode secrets
export SSHPASS="${SSHPASS:-gg123123@}"
SERVER_IP="${1:-170.64.232.208}"

echo "📦 Zipping codebase..."
rm -f /tmp/deploy.zip
# Exclude heavy/unnecessary dirs
zip -r /tmp/deploy.zip . -x "*.git*" "*.venv*" "*.mypy_cache*" "*.pytest_cache*" "htmlcov/*" "tests/*" "*.egg-info*"

echo "🚀 Transferring to $SERVER_IP..."
sshpass -e scp -o StrictHostKeyChecking=no /tmp/deploy.zip root@$SERVER_IP:/tmp/deploy.zip

echo "⚙️  Running usage verification on server..."
sshpass -e ssh -o StrictHostKeyChecking=no root@$SERVER_IP "bash -c 'rm -f /etc/apt/sources.list.d/{github-cli,vscode,docker}* && apt-get update -qq && apt-get install -y unzip -qq && mkdir -p /opt/vps-workstation && cd /opt/vps-workstation && unzip -o -q /tmp/deploy.zip && bash scripts/remote_setup.sh'"
