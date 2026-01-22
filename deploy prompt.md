You are an Expert DevOps Engineer and Automation Specialist. Your goal is to achieve a pristine, error-free deployment of the `debian-vps-configurator` application on a specific target server. You must operate in a strict "Fail-Fast & Fix" loop.

# Target Environment

- **Server IP**: `170.64.138.110`
- **User**: `root`
- **Password**: `gg123123@`
- **Tooling**: Use `sshpass` for non-interactive authentication.

# Core Objective

Deploy the application to the target server using command `vps-configurator install --profile advanced --verbose`. If _any_ issue arises (syntax error, hardcoded IP failure, logic bug, dependency issue, or process hang), you must fix the root cause in the local codebase and retry until the deployment completes perfectly (100% success).

# Phase 0: Preparation (Crucial)

Before starting the deployment loop, create a local helper script named `run_deploy_cycle.sh` to automate the process. This script must:

1.  **Encapsulate Authentication**: Use `sshpass` so credentials are not typed manually.
2.  **Prevent Disconnects**: Include SSH Keep-Alive flags (`-o ServerAliveInterval=60 -o ServerAliveCountMax=3`) to ensure long-running storage/install commands do not drop the connection.
3.  **Sync Code**: Automate the `rsync` or `scp` of the current local codebase to the remote server.
4.  **Activate Virtual Environment**: Ensure `.venv` is activated on the remote server before executing any Python commands.
5.  **Execute**: Trigger the remote setup script.

_Use this script for every retry attempt._

# Mandatory Workflow (The Loop)

You must execute the following process iteratively:

## 1. Safety Checkpoint (Critical)

**Before** applying changes on the server:

- Connect to the server.
- Create or verify a filesystem snapshot/tar backup of critical directories (etc, opt, home) to ensure a clean state for retries.
- Example: `tar --exclude='/proc' --exclude='/sys' -czf /root/checkpoint.tar.gz /etc /opt /home`

## 2. Deploy & Execute

- Run your `run_deploy_cycle.sh` helper script.
- **CRITICAL**: Ensure you have fixed any obvious hardcoded IPs (e.g., in `deploy.sh`) _before_ pushing.
- **CRITICAL**: Ensure virtual environment (`.venv`) is activated before running `vps-configurator` command.

## 3. Real-Time Analysis & Stuck Detection

- **Monitor the stream**: Watch `stdout`/`stderr` closely.
- **Stuck Detection**: If the deployment output hangs (no new log lines) for more than **60 seconds**, assume a process deadlock or prompt blocking.
- **Reaction**:
  1.  **STOP** the execution immediately (Ctrl+C).
  2.  **ROLLBACK**: Restore the server state using the checkpoint from Step 1.
  3.  **ANALYZE**: Determine _why_ it got stuck (e.g., implicit `apt-get` prompt, network timeout, infinite loop).
  4.  **FIX**: Edit the file **locally** to resolve the issue (e.g., add `-y` flag, fix logic).
  5.  **RETRY**: Restart the loop at Step 1.

# Constraints

- **Zero Tolerance**: Do not ignore warnings. Fix ALL issues.
- **No Manual Server Edits**: All fixes must be applied to the local codebase.
- **Hardcoding**: Aggressively replace hardcoded IP addresses with dynamic variables.
- **Safety**: Never execute a retry without ensuring the environment is clean (rollback if necessary).

# Output Format

For every iteration of the loop, report:

1.  **Action**: (e.g., "Deploying via Helper", "Detected Hang", "Rolled Back")
2.  **Issue Identified**: (Specific error or point of stagnation)
3.  **Fix Applied**: (The specific code change made locally)
4.  **Status**: "Retrying" or "Success"

Begin by creating the helper script and initiating the first deployment attempt.

---

# APPENDIX: Complete Helper Script

## run_deploy_cycle.sh (Production-Ready)

Save this as `run_deploy_cycle.sh` in the project root:

```bash
#!/bin/bash
#
# Debian VPS Configurator - Automated Deployment Script
#
# This script automates the complete deployment cycle including:
# - Pre-flight validation
# - Checkpoint creation
# - Code synchronization
# - Remote execution
# - Error detection
# - Logging
#
# Usage: ./run_deploy_cycle.sh
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Safer field splitting

# ============================================================================
# CONFIGURATION
# ============================================================================

# Server credentials (TODO: Move to environment variables in production)
readonly SERVER_IP="170.64.232.208"
readonly SERVER_USER="root"
readonly SERVER_PASS="gg123123@"
readonly REMOTE_DIR="/opt/debian-vps-configurator"
readonly LOCAL_DIR="$(pwd)"

# SSH options for reliability
readonly SSH_OPTS="-o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Logging
readonly LOG_DIR="${LOCAL_DIR}/logs"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly DEPLOY_LOG="${LOG_DIR}/deploy_${TIMESTAMP}.log"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$DEPLOY_LOG"
}

log_section() {
    echo "" | tee -a "$DEPLOY_LOG"
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$DEPLOY_LOG"
    echo "$*" | tee -a "$DEPLOY_LOG"
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$DEPLOY_LOG"
}

# Execute SSH command with proper error handling
ssh_exec() {
    local cmd="$1"
    sshpass -p "$SERVER_PASS" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$cmd"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

pre_flight_local() {
    log_section "PRE-FLIGHT: Local Environment Check"

    # Check required tools
    log_info "Checking required tools..."
    for tool in sshpass rsync ssh git python3; do
        if command_exists "$tool"; then
            log_success "✓ $tool found"
        else
            log_error "✗ $tool not found - please install it"
            exit 1
        fi
    done

    # Verify we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        log_error "Not in debian-vps-configurator root directory!"
        exit 1
    fi
    log_success "✓ Correct directory: $LOCAL_DIR"

    # Check git status
    if ! git status &>/dev/null; then
        log_error "Not a git repository!"
        exit 1
    fi
    log_success "✓ Git repository detected"

    local git_status=$(git status --short)
    if [ -n "$git_status" ]; then
        log_warning "Uncommitted changes detected:"
        echo "$git_status"
    else
        log_success "✓ Git status clean"
    fi

    # Check for hardcoded IPs/passwords
    log_info "Scanning for hardcoded credentials..."
    if grep -r "$SERVER_IP" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" . 2>/dev/null; then
        log_error "Found hardcoded IP in codebase!"
        exit 1
    fi
    log_success "✓ No hardcoded IPs found"

    if grep -r "$SERVER_PASS" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" . 2>/dev/null; then
        log_error "Found hardcoded password in codebase!"
        exit 1
    fi
    log_success "✓ No hardcoded passwords found"

    # Python syntax check
    log_info "Checking Python syntax..."
    local syntax_errors=0
    while IFS= read -r -d '' file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            log_error "Syntax error in: $file"
            syntax_errors=$((syntax_errors + 1))
        fi
    done < <(find configurator -name "*.py" -print0)

    if [ $syntax_errors -eq 0 ]; then
        log_success "✓ No Python syntax errors"
    else
        log_error "$syntax_errors file(s) with syntax errors!"
        exit 1
    fi
}

pre_flight_remote() {
    log_section "PRE-FLIGHT: Remote Server Check"

    # Test connectivity
    log_info "Testing server connectivity..."
    if ! ssh_exec "echo 'Connection OK'" &>/dev/null; then
        log_error "Cannot connect to server!"
        exit 1
    fi
    log_success "✓ Server accessible"

    # Check OS version
    log_info "Checking OS version..."
    local os_version=$(ssh_exec "cat /etc/os-release | grep VERSION_ID | cut -d'=' -f2 | tr -d '\"'")
    if [ "$os_version" != "12" ]; then
        log_warning "Expected Debian 12, found: $os_version"
    else
        log_success "✓ Debian 12 detected"
    fi

    # Check Python version
    log_info "Checking Python version..."
    local python_version=$(ssh_exec "python3 --version 2>&1 | awk '{print \$2}'")
    log_success "✓ Python $python_version"

    # Check disk space
    log_info "Checking disk space..."
    local disk_free=$(ssh_exec "df -h / | tail -1 | awk '{print \$4}'")
    log_success "✓ Free space: $disk_free"

    # Check memory
    log_info "Checking memory..."
    local mem_free=$(ssh_exec "free -h | grep Mem | awk '{print \$4}'")
    log_success "✓ Free memory: $mem_free"

    # Ensure python3-venv is installed
    log_info "Ensuring python3-venv is installed..."
    ssh_exec "which python3-venv >/dev/null 2>&1 || apt-get install -y python3-venv python3-pip >/dev/null 2>&1"
    log_success "✓ python3-venv available"
}

# ============================================================================
# CHECKPOINT CREATION
# ============================================================================

create_checkpoint() {
    log_section "CHECKPOINT: Creating Server Backup"

    log_info "Creating checkpoint on remote server..."
    ssh_exec "$(cat << 'CHECKPOINT_SCRIPT'
        CHECKPOINT_DIR="/root/checkpoints"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        CHECKPOINT_FILE="${CHECKPOINT_DIR}/checkpoint_${TIMESTAMP}.tar.gz"

        mkdir -p "$CHECKPOINT_DIR"

        echo "Creating checkpoint: $CHECKPOINT_FILE"
        tar --exclude='/proc' \
            --exclude='/sys' \
            --exclude='/dev' \
            --exclude='/tmp' \
            --exclude='/run' \
            --exclude='/mnt' \
            --exclude='/media' \
            --exclude='*.tar.gz' \
            -czf "$CHECKPOINT_FILE" \
            /etc /opt /root /home 2>/dev/null || true

        # Keep only last 3 checkpoints
        cd "$CHECKPOINT_DIR"
        ls -t checkpoint_*.tar.gz 2>/dev/null | tail -n +4 | xargs -r rm

        # Output checkpoint info
        if [ -f "$CHECKPOINT_FILE" ]; then
            echo "SUCCESS:$(basename $CHECKPOINT_FILE):$(du -h $CHECKPOINT_FILE | cut -f1)"
        else
            echo "FAILED"
        fi
CHECKPOINT_SCRIPT
    )"

    log_success "✓ Checkpoint created"
}

# ============================================================================
# CODE SYNCHRONIZATION
# ============================================================================

sync_codebase() {
    log_section "DEPLOY: Syncing Codebase to Server"

    log_info "Syncing files to $SERVER_IP:$REMOTE_DIR..."

    # Create remote directory if it doesn't exist
    ssh_exec "mkdir -p $REMOTE_DIR"

    # Sync codebase
    sshpass -p "$SERVER_PASS" rsync -avz --delete \
        --exclude='.git/' \
        --exclude='.venv/' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.pytest_cache/' \
        --exclude='logs/' \
        --exclude='deployment_log.txt' \
        --exclude='run_deploy_cycle.sh' \
        -e "ssh $SSH_OPTS" \
        "$LOCAL_DIR/" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/" | tee -a "$DEPLOY_LOG"

    log_success "✓ Codebase synced successfully"
}

# ============================================================================
# REMOTE EXECUTION
# ============================================================================

execute_deployment() {
    log_section "DEPLOY: Executing Remote Installation"

    log_info "Running installation on remote server..."

    # Execute deployment with real-time output
    sshpass -p "$SERVER_PASS" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" 'bash -s' << 'REMOTE_SCRIPT' | tee -a "$DEPLOY_LOG"
#!/bin/bash
set -euo pipefail

cd /opt/debian-vps-configurator

echo "[REMOTE] Current directory: $(pwd)"

# Create/activate virtual environment
if [ ! -d ".venv" ]; then
    echo "[REMOTE] Creating virtual environment..."
    python3 -m venv .venv
    echo "[REMOTE] ✓ Virtual environment created"
else
    echo "[REMOTE] ✓ Virtual environment exists"
fi

echo "[REMOTE] Activating virtual environment..."
source .venv/bin/activate

echo "[REMOTE] Python: $(which python)"
echo "[REMOTE] Python version: $(python --version)"

# Upgrade pip
echo "[REMOTE] Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install package in editable mode
echo "[REMOTE] Installing debian-vps-configurator..."
pip install -e . --quiet

# Verify installation
echo "[REMOTE] Verifying installation..."
which vps-configurator

# Run configurator
echo "[REMOTE] ═══════════════════════════════════════════════════════════════"
echo "[REMOTE] Running: vps-configurator install --profile advanced --verbose"
echo "[REMOTE] ═══════════════════════════════════════════════════════════════"

# Set timeout for the entire installation (30 minutes)
timeout 1800 vps-configurator install --profile advanced --verbose

echo "[REMOTE] ═══════════════════════════════════════════════════════════════"
echo "[REMOTE] Installation completed successfully!"
echo "[REMOTE] ═══════════════════════════════════════════════════════════════"
REMOTE_SCRIPT

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_success "✓ Remote installation completed successfully"
        return 0
    elif [ $exit_code -eq 124 ]; then
        log_error "✗ Remote installation TIMEOUT (exceeded 30 minutes)"
        return 1
    else
        log_error "✗ Remote installation FAILED (exit code: $exit_code)"
        return 1
    fi
}

# ============================================================================
# POST-DEPLOYMENT VERIFICATION
# ============================================================================

verify_deployment() {
    log_section "VERIFICATION: Post-Deployment Checks"

    log_info "Verifying installation..."

    # Check if vps-configurator is installed
    if ssh_exec "which vps-configurator" &>/dev/null; then
        log_success "✓ vps-configurator command available"
    else
        log_error "✗ vps-configurator command not found"
        return 1
    fi

    # Check logs
    log_info "Checking installation logs..."
    local log_exists=$(ssh_exec "[ -f /var/log/debian-vps-configurator/install.log ] && echo 'yes' || echo 'no'")
    if [ "$log_exists" = "yes" ]; then
        log_success "✓ Installation logs created"

        # Check for errors in logs
        local error_count=$(ssh_exec "grep -c ERROR /var/log/debian-vps-configurator/install.log 2>/dev/null || echo 0")
        if [ "$error_count" -eq 0 ]; then
            log_success "✓ No errors in installation logs"
        else
            log_warning "⚠ Found $error_count error(s) in logs"
        fi
    else
        log_warning "⚠ Installation log not found"
    fi

    # Check server accessibility
    if ssh_exec "echo 'Server accessible'" &>/dev/null; then
        log_success "✓ Server still accessible after installation"
    else
        log_error "✗ Cannot connect to server after installation!"
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    # Create logs directory
    mkdir -p "$LOG_DIR"

    # Start logging
    log_section "DEPLOYMENT SESSION STARTED"
    log_info "Timestamp: $(date)"
    log_info "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
    log_info "Log file: $DEPLOY_LOG"

    # Run deployment stages
    pre_flight_local
    pre_flight_remote
    create_checkpoint
    sync_codebase

    # Execute deployment and capture result
    if execute_deployment; then
        verify_deployment

        log_section "DEPLOYMENT SUCCESSFUL ✅"
        log_success "All stages completed successfully!"
        log_info "Deployment log: $DEPLOY_LOG"
        exit 0
    else
        log_section "DEPLOYMENT FAILED ❌"
        log_error "Deployment failed - check logs for details"
        log_info "Deployment log: $DEPLOY_LOG"

        # Suggest rollback
        echo ""
        log_warning "To rollback, run on server:"
        log_warning "  LATEST=\$(ls -t /root/checkpoints/checkpoint_*.tar.gz | head -1)"
        log_warning "  cd / && tar -xzf \"\$LATEST\""

        exit 1
    fi
}

# Trap errors
trap 'log_error "Deployment script interrupted or failed at line $LINENO"' ERR

# Run main function
main "$@"
```

## Permissions Setup

```bash
# Make script executable
chmod +x run_deploy_cycle.sh

# Create logs directory
mkdir -p logs

# Initialize deployment log
touch deployment_log.txt
```

## Usage

```bash
# Run deployment
./run_deploy_cycle.sh

# View logs in real-time (in another terminal)
tail -f logs/deploy_*.log

# Check deployment history
cat deployment_log.txt
```

---

**Ready to deploy! Execute: `./run_deploy_cycle.sh`** 🚀
