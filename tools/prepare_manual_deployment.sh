#!/bin/bash
#####################################################################
# Prepare Manual Deployment Package
#
# Creates a deployment package that can be manually transferred
# to the server and run there.
#
# Usage: ./prepare_manual_deployment.sh
#####################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deploy_package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="deploy_package_${TIMESTAMP}.tar.gz"

echo "=========================================="
echo "Preparing Manual Deployment Package"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT"

# Clean up old deploy directory
if [ -d "$DEPLOY_DIR" ]; then
    echo "Cleaning up old deployment package..."
    rm -rf "$DEPLOY_DIR"
fi

# Create deployment directory
echo "Creating deployment package structure..."
mkdir -p "$DEPLOY_DIR"

# Copy essential files (excluding venv, git, etc.)
echo "Copying project files..."

# Use rsync if available, otherwise cp
if command -v rsync &> /dev/null; then
    rsync -av \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='deploy_venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='.ruff_cache' \
        --exclude='cis-reports' \
        --exclude='deploy_package*' \
        --exclude='*.zip' \
        --exclude='*.tar.gz' \
        --exclude='.install_checkpoints' \
        --exclude='.install_backup' \
        --exclude='*.log' \
        "$PROJECT_ROOT/" "$DEPLOY_DIR/"
else
    # Fallback to find + cp
    find . -type f \
        ! -path './.git/*' \
        ! -path './.venv/*' \
        ! -path './venv/*' \
        ! -path '*/__pycache__/*' \
        ! -name '*.pyc' \
        ! -path './.pytest_cache/*' \
        ! -path './cis-reports/*' \
        ! -path './deploy_package*' \
        ! -name '*.zip' \
        ! -path './.install_checkpoints/*' \
        ! -path './.install_backup/*' \
        -exec cp --parents {} "$DEPLOY_DIR/" \;
fi

# Copy deployment scripts
echo "Including deployment scripts..."
cp "$SCRIPT_DIR/deploy_on_server.sh" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/monitor_install_with_checkpoint.py" "$DEPLOY_DIR/tools/"

# Make scripts executable
chmod +x "$DEPLOY_DIR/deploy_on_server.sh"
chmod +x "$DEPLOY_DIR/tools/monitor_install_with_checkpoint.py"

# Create README with instructions
cat > "$DEPLOY_DIR/DEPLOYMENT_README.md" << 'EOF'
# Manual Deployment Instructions

## Quick Start

1. **Transfer this package to the server:**
   ```bash
   # From your local machine:
   scp -r deploy_package root@<your-server-ip>:/root/
   # Or use any other transfer method (rsync, sftp, etc.)
   ```

2. **SSH into the server:**
   ```bash
   ssh root@<your-server-ip>
   ```

3. **Extract and run:**
   ```bash
   cd /root
   tar -xzf deploy_package_*.tar.gz  # if using archive
   # OR if you transferred the directory directly:
   cd deploy_package

   # Run the deployment script
   bash deploy_on_server.sh
   ```

## What This Does

1. Creates a Python virtual environment
2. Installs all dependencies
3. Runs the installation through a circuit breaker that:
   - Creates a system checkpoint before installation
   - Monitors for ERRORS, WARNINGS, SKIPS, and TIMEOUTS
   - Automatically halts and rolls back on issues
   - Reports detailed information about any problems

## Monitoring

The circuit breaker will:
- Stream all output in real-time
- Halt immediately on any issue
- Create checkpoints at `/tmp/vps-checkpoint-*`
- Log events to `/tmp/monitor_install.log`

## Troubleshooting

If deployment fails:
1. Check `/tmp/monitor_install.log` for details
2. Review checkpoint directory: `/tmp/vps-checkpoint-*`
3. The system should be automatically rolled back
4. Fix issues in the codebase and re-run

## Alternative: Direct Installation

If you prefer to run without the circuit breaker:
```bash
cd /root/debian-vps-workstation
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m configurator --verbose install --profile advanced --no-parallel
```
EOF

# Create archive
echo ""
echo "Creating archive..."
cd "$PROJECT_ROOT"
tar -czf "$ARCHIVE_NAME" -C "$PROJECT_ROOT" deploy_package

echo ""
echo "✅ Deployment package created!"
echo ""
echo "Package location: $PROJECT_ROOT/$ARCHIVE_NAME"
echo "Package size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "To deploy:"
echo "  1. Transfer: scp $ARCHIVE_NAME root@<your-server-ip>:/root/"
echo "  2. SSH: ssh root@<your-server-ip>"
echo "  3. Extract: tar -xzf $ARCHIVE_NAME"
echo "  4. Run: cd deploy_package && bash deploy_on_server.sh"
echo ""
