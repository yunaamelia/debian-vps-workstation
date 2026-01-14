#!/bin/bash
set -e

# Install basics
apt-get update
# Suppress interactive prompts
export DEBIAN_FRONTEND=noninteractive
apt-get install -y python3-venv unzip sshpass

# Prepare directory
mkdir -p /opt/vps-workstation
cd /opt/vps-workstation

# Unzip
unzip -o /tmp/deploy.zip

# Setup Python Env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create a test script to verify the fix specifically
cat << 'EOF' > verify_fix.py
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add current dir to path
sys.path.append(os.getcwd())

from configurator.modules.desktop import DesktopModule

# Setup logging
logging.basicConfig(level=logging.INFO)

def verify_fix():
    print("Verifying XRDP configuration fix...")

    # Mock resources
    module = DesktopModule(manager=MagicMock())
    module.run = MagicMock()
    module.run.return_value.success = True
    module.get_config = MagicMock(side_effect=lambda k, d=None: {
        "desktop.xrdp.max_bpp": 24,
        "desktop.xrdp.security_layer": "tls",
        "desktop.xrdp.tcp_nodelay": True,
        "desktop.xrdp.bitmap_cache": True
    }.get(k, d))

    # Mock file writing to capture content
    written_files = {}

    def mock_write_file(path, content, **kwargs):
        written_files[path] = content
        print(f"Captured write to {path}")

    # Patch modules
    with patch('configurator.modules.desktop.write_file', side_effect=mock_write_file), \
         patch('configurator.modules.desktop.backup_file'):

        # Run the optimization method
        # We need to bypass the dry_run check or ensure it's False
        module.dry_run = False
        module._optimize_xrdp_performance()

        # Verify xrdp.ini content
        xrdp_content = written_files.get('/etc/xrdp/xrdp.ini', '')

        issues = []
        if "max_bpp=24" not in xrdp_content:
            issues.append(f"FAIL: max_bpp=24 not found. Found: {xrdp_content.find('max_bpp')}")
        if "security_layer=tls" not in xrdp_content:
            issues.append("FAIL: security_layer=tls not found")
        if "{max_bpp}" in xrdp_content:
            issues.append("FAIL: Template variable {max_bpp} check failed (was not replaced)")

        # Verify sesman.ini content
        sesman_content = written_files.get('/etc/xrdp/sesman.ini', '')
        if "MaxSessions=10" not in sesman_content:
            issues.append("FAIL: MaxSessions=10 not found in sesman.ini")

        if issues:
            print("\n❌ Verification Failed:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("\n✅ Verification Successful!")
            print("  - max_bpp is correctly set to 24")
            print("  - security_layer is correctly set to tls")
            print("  - MaxSessions is 10")
            print("  - Template variables are correctly substituted")

verify_fix()
EOF

# Run the verification script
python3 verify_fix.py
