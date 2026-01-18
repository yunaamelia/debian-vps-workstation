#!/bin/bash
set -e

# Clean potential broken sources from previous failed runs
rm -f /etc/apt/sources.list.d/github-cli.list
rm -f /etc/apt/sources.list.d/vscode.list
rm -f /etc/apt/sources.list.d/docker.sources
rm -f /etc/apt/sources.list.d/docker.list

# Install basics
apt-get update
# Suppress interactive prompts
export DEBIAN_FRONTEND=noninteractive
apt-get install -y python3-venv unzip sshpass

# Prepare directory
mkdir -p /opt/vps-workstation
cd /opt/vps-workstation



# Setup Python Env
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install the vps-configurator package in editable mode
pip install -e .

echo "✅ Remote setup complete."
