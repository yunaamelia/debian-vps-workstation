#!/bin/bash
###############################################################################
# Debian VPS Configurator - Fail-Fast Deployment Cycle
# Purpose: Deploy with safety checkpoints and automatic rollback
###############################################################################

set -euo pipefail

# Configuration
SERVER_IP="${1:-170.64.232.208}"
SSH_PASS="gg123123@"
SSH_OPTS="-o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $*${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Trap errors
trap 'log_error "Deployment failed at line $LINENO"' ERR

###############################################################################
# STEP 0: Pre-flight Checks
###############################################################################
log_step "STEP 0: Pre-flight Checks"

if ! command -v sshpass &> /dev/null; then
    log_error "sshpass not installed. Run: sudo apt install sshpass"
    exit 1
fi

if ! command -v rsync &> /dev/null; then
    log_error "rsync not installed. Run: sudo apt install rsync"
    exit 1
fi

log_info "Testing SSH connectivity to $SERVER_IP..."
if ! sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$SERVER_IP "echo 'OK'" &> /dev/null; then
    log_error "Cannot connect to $SERVER_IP"
    exit 1
fi
log_success "SSH connectivity verified"

###############################################################################
# STEP 1: Create Safety Checkpoint
###############################################################################
log_step "STEP 1: Creating Safety Checkpoint"

log_info "Creating filesystem checkpoint on remote server..."
sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$SERVER_IP bash <<'CHECKPOINT'
    mkdir -p /root/checkpoints
    CHECKPOINT="/root/checkpoints/checkpoint_$(date +%Y%m%d_%H%M%S).tar.gz"

    echo "Creating checkpoint: $CHECKPOINT"
    tar --warning=no-file-changed \
        --exclude='/proc' --exclude='/sys' --exclude='/dev' \
        --exclude='/run' --exclude='/tmp' --exclude='/var/cache' \
        -czf "$CHECKPOINT" /etc /opt /root/.bashrc /root/.profile 2>/dev/null || true

    # Keep only last 5 checkpoints
    cd /root/checkpoints && ls -t checkpoint_*.tar.gz | tail -n +6 | xargs -r rm -f

    echo "Checkpoint created successfully"
    ls -lh "$CHECKPOINT"
CHECKPOINT

log_success "Safety checkpoint created"

###############################################################################
# STEP 2: Bootstrap Remote Server
###############################################################################
log_step "STEP 2: Bootstrapping Remote Server"

log_info "Installing system prerequisites..."
log_info "Installing system prerequisites..."
sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$SERVER_IP \
    "export DEBIAN_FRONTEND=noninteractive && rm -f /etc/apt/sources.list.d/vscode.list /etc/apt/sources.list.d/code.list && apt-get update -qq && apt-get install -y -qq rsync unzip python3-venv python3-pip"

log_success "Bootstrap complete"

###############################################################################
# STEP 3: Sync Codebase
###############################################################################
log_step "STEP 3: Syncing Codebase"

log_info "Syncing local codebase to /opt/vps-workstation..."
sshpass -p "$SSH_PASS" rsync -avz --delete \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    --exclude='.mypy_cache/' \
    --exclude='*.pyc' \
    --exclude='.coverage' \
    --exclude='htmlcov/' \
    --exclude='*.egg-info/' \
    --exclude='dist/' \
    --exclude='build/' \
    -e "ssh $SSH_OPTS" \
    ./ root@$SERVER_IP:/opt/vps-workstation/

log_success "Codebase synced"

###############################################################################
# STEP 4: Execute Remote Setup
###############################################################################
log_step "STEP 4: Executing Remote Setup"

log_info "Running remote_setup.sh..."
sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$SERVER_IP bash <<'SETUP'
    set -e
    export DEBIAN_FRONTEND=noninteractive
    cd /opt/vps-workstation

    # Clean old sources
    rm -f /etc/apt/sources.list.d/{github-cli,vscode,docker}*

    # Run setup
    bash scripts/remote_setup.sh
SETUP

log_success "Remote setup complete"

###############################################################################
# STEP 5: Execute Deployment
###############################################################################
log_step "STEP 5: Executing Deployment"

log_info "Running: vps-configurator install --profile advanced --verbose"
log_warn "Monitoring for issues (will auto-detect hangs)..."

if sshpass -p "$SSH_PASS" ssh $SSH_OPTS root@$SERVER_IP bash <<'DEPLOY'
    set -e
    cd /opt/vps-workstation
    source .venv/bin/activate

    # Execute deployment command
    vps-configurator install --profile advanced --verbose
DEPLOY
then
    log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_success "  DEPLOYMENT SUCCESSFUL - 100% COMPLETE"
    log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    log_error "Deployment failed!"
    log_warn "To rollback: ssh root@$SERVER_IP 'cd /root/checkpoints && tar -xzf \$(ls -t checkpoint_*.tar.gz | head -n1) -C /'"
    exit 1
fi
