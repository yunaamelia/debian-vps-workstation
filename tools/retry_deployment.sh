#!/bin/bash
#####################################################################
# Retry Deployment with Multiple Strategies
#
# Attempts deployment using various methods until one succeeds.
#
# Usage: ./retry_deployment.sh
#####################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOST="${REMOTE_HOST:-}"
USER="${REMOTE_USER:-root}"
PASS="${REMOTE_PASSWORD:-}"
if [ -z "$HOST" ]; then
    echo "ERROR: REMOTE_HOST environment variable not set"
    exit 1
fi
if [ -z "$PASS" ]; then
    echo "ERROR: REMOTE_PASSWORD environment variable not set"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Retry Deployment - Multiple Strategies"
echo "=========================================="
echo ""

# Strategy 1: Direct SSH connection
echo "Strategy 1: Direct SSH deployment..."
if source venv/bin/activate 2>/dev/null && python3 tools/deploy_local_code.py 2>&1 | tee /tmp/deploy_attempt.log; then
    echo "✅ Deployment successful via Strategy 1!"
    exit 0
fi

echo "Strategy 1 failed. Checking connectivity..."
if ! timeout 5 bash -c "echo > /dev/tcp/$HOST/22" 2>/dev/null; then
    echo "⚠️  Port 22 is not accessible"
    echo ""
    echo "Switching to manual deployment method..."
    echo ""

    # Strategy 2: Prepare manual package
    echo "Strategy 2: Preparing manual deployment package..."
    if bash tools/prepare_manual_deployment.sh; then
        LATEST_PKG=$(ls -t deploy_package_*.tar.gz 2>/dev/null | head -1)
        if [ -n "$LATEST_PKG" ]; then
            echo ""
            echo "✅ Manual deployment package created: $LATEST_PKG"
            echo ""
            echo "To deploy manually:"
            echo "  1. Transfer: scp $LATEST_PKG $USER@$HOST:/root/"
            echo "  2. SSH: ssh $USER@$HOST"
            echo "  3. Extract: tar -xzf $(basename $LATEST_PKG)"
            echo "  4. Run: cd deploy_package && bash deploy_on_server.sh"
            echo ""
            exit 0
        fi
    fi
fi

echo "❌ All deployment strategies failed"
echo "Check /tmp/deploy_attempt.log for details"
exit 1
