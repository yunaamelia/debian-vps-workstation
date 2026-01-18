#!/bin/bash
set -e

HOST="209.97.162.195"
USER="root"
PASS="gg123123@"
REMOTE_DIR="/root/debian-vps-workstation"

echo "Cleaning remote directory..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$HOST "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR"

echo "Syncing files..."
sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no ./* $USER@$HOST:$REMOTE_DIR/

echo "Setting up virtual environment and dependencies..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$HOST "cd $REMOTE_DIR && apt-get update && apt-get install -y python3-venv python3-pip && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

echo "Starting deployment with circuit breaker..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$HOST "cd $REMOTE_DIR && source .venv/bin/activate && python tools/monitor_install_with_checkpoint.py 'python -m configurator install --profile advanced --verbose'"
