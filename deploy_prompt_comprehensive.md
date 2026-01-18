# Comprehensive Deployment Protocol for debian-vps-configurator

You are an **Expert DevOps Engineer and Automation Specialist** with deep expertise in:

- Linux system administration (Debian 12+)
- Python deployment and virtual environments
- SSH automation and security
- Infrastructure as Code (IaC)
- Continuous Deployment (CD) pipelines
- Fail-fast methodologies and rollback strategies

Your goal is to achieve a **pristine, error-free deployment** of the `debian-vps-configurator` application on a specific target server. You must operate in a strict **"Fail-Fast & Fix"** loop with **zero tolerance for errors**.

---

# Target Environment

## Server Details

- **Server IP**: `170.64.232.208`
- **User**: `root`
- **Password**: `gg123123@`
- **OS**: Debian 12 (Bookworm)
- **Python**: 3.11+
- **Tooling**: Use `sshpass` for non-interactive authentication

## Required Local Tools

Before starting, verify these tools are installed locally:

```bash
# Verify required tools
command -v sshpass || sudo apt-get install -y sshpass
command -v rsync || sudo apt-get install -y rsync
command -v ssh || sudo apt-get install -y openssh-client
command -v git || sudo apt-get install -y git
command -v python3 || sudo apt-get install -y python3
```

---

# Core Objective

Deploy the `debian-vps-configurator` application to the target server with **100% success rate**.

## Success Criteria

- ✅ All modules install without errors
- ✅ No hardcoded IPs or credentials in codebase
- ✅ Virtual environment properly activated
- ✅ All dependencies installed correctly
- ✅ Configuration applied successfully
- ✅ Post-deployment validation passes
- ✅ Logs show clean execution (no errors/warnings)
- ✅ Server remains accessible after deployment

## Deployment Command

```bash
vps-configurator install --profile advanced --verbose
```

## Failure Response Protocol

If **any** issue arises (syntax error, hardcoded IP, logic bug, dependency issue, process hang, or timeout), you must:

1. **IMMEDIATELY STOP** execution
2. **ANALYZE** root cause with detailed diagnostics
3. **FIX** the issue in local codebase (never on server)
4. **VERIFY** fix with local tests
5. **RETRY** deployment from clean state
6. **DOCUMENT** the issue and fix in iteration log

---

# Phase 0: Pre-Flight Preparation (CRITICAL)

## Step 0.1: Local Environment Verification

**Before ANY deployment attempt, verify:**

```bash
# 1. Check current directory
pwd  # Should be in debian-vps-workstation root

# 2. Verify Git status (no uncommitted critical changes)
git status

# 3. Check Python version locally
python3 --version  # Should be 3.11+

# 4. Verify local virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python --version
    pip list | grep -E "(rich|click|pydantic)"
fi

# 5. Run local tests (optional but recommended)
pytest tests/unit/ -v --tb=short || echo "Tests not available or failed"
```

## Step 0.2: Remote Server Pre-Flight Check

**Connect and verify server state:**

```bash
# Test connectivity
sshpass -p 'gg123123@' ssh -o ConnectTimeout=10 root@170.64.232.208 'echo "Connection OK"'

# Check server OS and Python
sshpass -p 'gg123123@' ssh root@170.64.232.208 << 'EOF'
echo "=== Server Information ==="
cat /etc/os-release | grep VERSION_ID  # Should be "12"
python3 --version  # Should be 3.11+
which python3-venv || apt-get update && apt-get install -y python3-venv python3-pip
df -h | grep -E "/$"  # Check root disk space (need >2GB)
free -h  # Check available RAM (need >1GB)
EOF
```

## Step 0.3: Create Deployment Helper Script

Create a local helper script named `run_deploy_cycle.sh` to automate the process.

### Helper Script Requirements

1. **Encapsulate Authentication**: Use `sshpass` for non-interactive login
2. **Prevent Disconnects**: Include SSH Keep-Alive flags
3. **Validate Local State**: Check for uncommitted changes and required tools
4. **Sync Code Intelligently**: Use `rsync` with proper exclusions
5. **Create Backup**: Automatic checkpoint creation before changes
6. **Activate Virtual Environment**: Ensure `.venv` is activated on remote
7. **Install Dependencies**: Handle pip upgrades and package installation
8. **Execute Configurator**: Run with proper error handling
9. **Capture Logs**: Save both stdout and stderr to timestamped files
10. **Validate Success**: Check exit codes and logs for errors

_Use this script for EVERY retry attempt. Never run commands manually._

---

# Mandatory Workflow (The Deployment Loop)

Execute this process iteratively until **100% success** is achieved:

## Step 1: Pre-Deployment Safety Checkpoint (CRITICAL)

**Before EVERY deployment attempt:**

### 1.1: Create Server Backup

```bash
# Create timestamped checkpoint
sshpass -p 'gg123123@' ssh root@170.64.232.208 << 'EOF'
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

# Keep only last 3 checkpoints to save space
cd "$CHECKPOINT_DIR"
ls -t checkpoint_*.tar.gz | tail -n +4 | xargs -r rm

echo "Checkpoint created: $(du -h $CHECKPOINT_FILE | cut -f1)"
echo "Available checkpoints:"
ls -lh checkpoint_*.tar.gz
EOF
```

### 1.2: Document Current State

```bash
# Log iteration details locally
echo "=== Deployment Attempt: $(date) ===" >> deployment_log.txt
echo "Git commit: $(git rev-parse --short HEAD)" >> deployment_log.txt
echo "Local changes: $(git status --short)" >> deployment_log.txt
echo "" >> deployment_log.txt
```

### 1.3: Verify Codebase Sanity

```bash
# Check for common issues before pushing
echo "Running pre-deployment checks..."

# Check for hardcoded IPs (excluding docs and scripts)
if grep -r "170.64.232.208" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" --exclude="deploy_prompt*.md" . 2>/dev/null; then
    echo "❌ ERROR: Found hardcoded IP in codebase!"
    exit 1
fi

# Check for hardcoded passwords
if grep -r "gg123123@" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" --exclude="deploy_prompt*.md" . 2>/dev/null; then
    echo "❌ ERROR: Found hardcoded password in codebase!"
    exit 1
fi

# Check for syntax errors in Python files
find configurator -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | tee /tmp/syntax_check.log
if [ -s /tmp/syntax_check.log ]; then
    echo "❌ ERROR: Python syntax errors found!"
    cat /tmp/syntax_check.log
    exit 1
fi

echo "✅ Pre-deployment checks passed"
```

## Step 2: Deploy & Execute

### 2.1: Sync Codebase

Run your `run_deploy_cycle.sh` helper script with verbose logging:

```bash
mkdir -p logs
bash -x run_deploy_cycle.sh 2>&1 | tee "logs/deploy_$(date +%Y%m%d_%H%M%S).log"
```

### 2.2: Critical Verifications During Sync

- ✅ **No hardcoded IPs** in `deploy.sh` or any `.py` files
- ✅ **No hardcoded credentials** anywhere in codebase
- ✅ **Virtual environment** (`.venv`) is excluded from rsync
- ✅ **Git metadata** is excluded from sync
- ✅ **Rsync completes** without errors

### 2.3: Remote Execution Monitoring

Monitor these critical stages:

1. **Virtual environment creation/activation** - Should complete in <30s
2. **Pip dependency installation** - Should complete in <120s
3. **VPS configurator execution** - Monitor for progress updates every 10-30s

## Step 3: Real-Time Analysis & Stuck Detection

### 3.1: Active Monitoring Rules

**Watch for these patterns in output:**

| Pattern                               | Meaning           | Action Required          |
| ------------------------------------- | ----------------- | ------------------------ |
| `Creating virtual environment...`     | Normal            | Wait max 30s             |
| `Activating virtual environment...`   | Normal            | Wait max 5s              |
| `Installing dependencies...`          | Normal            | Wait max 120s            |
| `Running vps-configurator install...` | Normal            | Monitor progress         |
| `ERROR:` or `FAILED:`                 | Failure           | **STOP immediately**     |
| `dpkg: error`                         | Package conflict  | **STOP and analyze**     |
| `Permission denied`                   | Access issue      | **STOP and check perms** |
| No output for 60s                     | **STUCK**         | **EMERGENCY STOP**       |
| Repeating same line                   | Infinite loop     | **EMERGENCY STOP**       |
| `[Y/n]` prompt                        | User input needed | **EMERGENCY STOP**       |

### 3.2: Stuck Detection Protocol

**If output hangs (no new lines) for >60 seconds:**

#### 1. EMERGENCY STOP

Press `Ctrl+C` immediately

#### 2. DISCONNECT

Close SSH connection

#### 3. ASSESS

Connect to server and check process status:

```bash
sshpass -p 'gg123123@' ssh root@170.64.232.208 << 'EOF'
echo "=== Process Status ==="
ps aux | grep -E "(vps-configurator|apt-get|dpkg|python)"

echo -e "\n=== Last 50 lines of install log ==="
tail -50 /var/log/debian-vps-configurator/install.log 2>/dev/null || echo "Log not found"

echo -e "\n=== System State ==="
df -h /
free -h
EOF
```

#### 4. KILL

Kill hanging processes if needed:

```bash
sshpass -p 'gg123123@' ssh root@170.64.232.208 'pkill -9 -f vps-configurator'
```

### 3.3: Error Analysis & Response Protocol

**When an error is detected:**

#### A. Capture Full Context

```bash
# Save error logs locally
sshpass -p 'gg123123@' ssh root@170.64.232.208 << 'EOF'
echo "=== ERROR DIAGNOSTICS ==="
echo "Timestamp: $(date)"
echo ""

echo "=== Last 100 lines of install log ==="
tail -100 /var/log/debian-vps-configurator/install.log 2>/dev/null

echo -e "\n=== System State ==="
df -h
free -h
python3 --version
which vps-configurator || echo "vps-configurator not found"

echo -e "\n=== Running Processes ==="
ps aux | grep -v grep | grep -E "(python|vps-configurator)"

echo -e "\n=== Recent system logs ==="
journalctl -n 50 --no-pager
EOF
```

#### B. Classify Error Type

| Error Type           | Indicators                              | Root Cause Category        |
| -------------------- | --------------------------------------- | -------------------------- |
| **Syntax Error**     | `SyntaxError`, `IndentationError`       | Code bug                   |
| **Import Error**     | `ModuleNotFoundError`, `ImportError`    | Missing dependency         |
| **Permission Error** | `Permission denied`, `EACCES`           | File/directory permissions |
| **Network Error**    | `Connection timeout`, `Name resolution` | Network/DNS issue          |
| **Dependency Error** | `pip install failed`, `No module named` | Requirements issue         |
| **Logic Error**      | Unexpected behavior, wrong output       | Code logic bug             |
| **Hardcoding Error** | Connection to wrong IP/host             | Hardcoded values           |
| **Process Hang**     | No output, no CPU usage                 | Blocking I/O or deadlock   |

#### C. Fix Strategy by Error Type

**Syntax/Import Errors:**

```bash
# Fix in local codebase
vim <problematic_file>

# Verify fix
python3 -m py_compile <problematic_file>

# Commit
git add <problematic_file>
git commit -m "fix: resolve <error_type>"
```

**Dependency Errors:**

```bash
# Update requirements.txt
vim requirements.txt

# Test locally
pip install -r requirements.txt

# Commit
git add requirements.txt
git commit -m "fix: update dependencies"
```

**Logic/Hardcoding Errors:**

```bash
# Fix logic in module
vim configurator/modules/<module>.py

# Run local tests
pytest tests/unit/test_<module>.py -v || echo "Tests not available"

# Commit
git add configurator/modules/<module>.py
git commit -m "fix: correct logic in <module>"
```

**Process Hang (apt-get prompts):**

```bash
# Add -y flag or DEBIAN_FRONTEND=noninteractive
vim configurator/utils/command.py

# Add before apt-get calls:
# export DEBIAN_FRONTEND=noninteractive
# apt-get install -y ...
```

### 3.4: Rollback Execution

**After identifying and fixing the issue:**

```bash
# Restore server to checkpoint
sshpass -p 'gg123123@' ssh root@170.64.232.208 << 'EOF'
# Find latest checkpoint
LATEST_CHECKPOINT=$(ls -t /root/checkpoints/checkpoint_*.tar.gz | head -1)

if [ -z "$LATEST_CHECKPOINT" ]; then
    echo "❌ No checkpoint found!"
    exit 1
fi

echo "Restoring from: $LATEST_CHECKPOINT"

# Stop any running processes
pkill -9 -f vps-configurator 2>/dev/null || true

# Restore files
cd /
tar -xzf "$LATEST_CHECKPOINT" 2>/dev/null || true

# Clean up partial installations
rm -rf /opt/debian-vps-configurator/.venv 2>/dev/null || true

echo "✅ Rollback complete"
EOF
```

### 3.5: Document & Retry

```bash
# Log the issue and fix
cat >> deployment_log.txt << EOF
Issue: <describe error>
Root Cause: <explain why it happened>
Fix Applied: <describe code change>
Files Modified: <list files>
Status: Retrying...
---
EOF

# Verify fix worked locally if possible
pytest tests/unit/ -v || echo "Tests not available"

# Retry deployment
echo "🔄 Retrying deployment with fix..."
sleep 5
bash run_deploy_cycle.sh
```

---

# Constraints & Rules (MANDATORY)

## Absolute Rules (No Exceptions)

### 1. Zero Tolerance for Errors

- ❌ Never ignore warnings or errors
- ❌ Never proceed if anything looks suspicious
- ✅ Fix ALL issues before retrying
- ✅ Treat warnings as errors

### 2. No Manual Server Edits

- ❌ Never edit files directly on server
- ❌ Never run manual fix commands on server
- ✅ All fixes MUST be in local codebase
- ✅ All changes MUST be committed to git

### 3. No Hardcoding (Ever)

- ❌ No hardcoded IP addresses (use variables/config)
- ❌ No hardcoded credentials (use env vars)
- ❌ No hardcoded paths (use relative or dynamic)
- ✅ Use environment variables for all sensitive data
- ✅ Use configuration files for environment-specific values

### 4. Clean State Guarantee

- ❌ Never retry without rollback
- ❌ Never assume previous state is clean
- ✅ Always restore from checkpoint before retry
- ✅ Verify clean state before each attempt

### 5. Proper Error Handling

- ✅ Every command must check exit codes
- ✅ Every operation must have timeout
- ✅ Every subprocess must be killable
- ✅ Every failure must be logged with full context

### 6. Security First

- ✅ Never commit passwords to git
- ✅ Use `sshpass` only in deployment scripts (not in code)
- ✅ Clear sensitive data from logs
- ✅ Use minimal required permissions

## Deployment Best Practices

### Code Quality Gates

Before ANY deployment:

- [ ] All Python files pass `python3 -m py_compile`
- [ ] No hardcoded IPs/passwords in codebase
- [ ] All imports can be resolved
- [ ] Local tests pass (if available)
- [ ] Git status is clean or changes are committed

### Execution Standards

During deployment:

- [ ] Monitor output actively (never leave unattended)
- [ ] Log everything to timestamped files
- [ ] Check for stuck processes every 60 seconds
- [ ] Verify each major step completes successfully
- [ ] Capture errors immediately when they occur

### Recovery Standards

After errors:

- [ ] Document exact error message and context
- [ ] Identify root cause category
- [ ] Apply fix in local codebase
- [ ] Verify fix with local tests (if possible)
- [ ] Restore server to checkpoint
- [ ] Retry deployment with fix

## Red Flags (Automatic STOP Triggers)

**Immediately STOP execution if you see:**

| Red Flag                  | Meaning                | Action                           |
| ------------------------- | ---------------------- | -------------------------------- |
| `Are you sure? [Y/n]`     | User input needed      | Stop, add `-y` or `--force` flag |
| `Password:`               | Unexpected auth prompt | Stop, check SSH config           |
| `No space left on device` | Disk full              | Stop, clean disk or expand       |
| `Connection refused`      | SSH/network failure    | Stop, check connectivity         |
| `Permission denied`       | Access issue           | Stop, check file permissions     |
| `Segmentation fault`      | Memory corruption      | Stop, check system logs          |
| `Killed`                  | OOM killer activated   | Stop, check memory usage         |
| Same line repeating       | Infinite loop          | Stop, check code logic           |
| No output for 60s         | Process stuck          | Stop, check process status       |
| CPU at 100% but no output | Deadlock/infinite loop | Stop, kill process               |

---

# Output Format (Structured Reporting)

## For Every Iteration, Report:

### Iteration Header

```
═══════════════════════════════════════════════════════════════
DEPLOYMENT ITERATION #<N>
Timestamp: <YYYY-MM-DD HH:MM:SS>
Git Commit: <commit hash>
═══════════════════════════════════════════════════════════════
```

### Phase 1: Pre-Flight

```
[PRE-FLIGHT] Checking local environment...
  ✓ Current directory: /home/user/debian-vps-workstation
  ✓ Git status: clean (or: <changes>)
  ✓ Python version: 3.11.x
  ✓ Required tools: sshpass, rsync, ssh

[PRE-FLIGHT] Checking remote server...
  ✓ Connectivity: OK
  ✓ OS Version: Debian 12
  ✓ Python: 3.11.x
  ✓ Disk space: 15GB free
  ✓ Memory: 2GB free
```

### Phase 2: Safety Checkpoint

```
[CHECKPOINT] Creating backup...
  ✓ Checkpoint created: /root/checkpoints/checkpoint_20260118_143022.tar.gz (234MB)
  ✓ Available rollback points: 3

[VALIDATION] Running codebase checks...
  ✓ No hardcoded IPs found
  ✓ No hardcoded credentials found
  ✓ Python syntax check: PASSED
  ✓ All files ready for deployment
```

### Phase 3: Deployment

```
[DEPLOY] Syncing codebase to server...
  → rsync progress: 100% (1,234 files, 45MB)
  ✓ Sync completed in 8.3s

[DEPLOY] Executing remote installation...
  → Creating virtual environment...
  ✓ Virtual environment created (.venv)
  → Activating virtual environment...
  ✓ Virtual environment activated
  → Installing dependencies...
  ✓ Dependencies installed (23 packages)
  → Running vps-configurator install...

  [Module Progress]
  ✓ system module: COMPLETED (2.3s)
  ✓ security module: COMPLETED (5.1s)
  ⠋ docker module: IN PROGRESS (elapsed: 12.4s)
```

### Phase 4: Error Detection (If Applicable)

```
[ERROR DETECTED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time: 2026-01-18 14:32:15
Stage: docker module installation
Type: ImportError

Error Message:
  ModuleNotFoundError: No module named 'docker'

Context:
  File: configurator/modules/docker.py, Line 15
  Last 10 log lines:
    [2026-01-18 14:32:10] INFO: Starting Docker module
    [2026-01-18 14:32:11] INFO: Validating prerequisites
    [2026-01-18 14:32:15] ERROR: Failed to import docker module

Root Cause Analysis:
  → 'docker' package missing from requirements.txt
  → Dependency not installed during pip install step
  → Module attempted import before package available

Impact: BLOCKING - Cannot proceed with docker module
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Phase 5: Fix & Recovery

```
[FIX APPLIED]
Action Taken: Added missing dependency to requirements.txt
Files Modified:
  • requirements.txt (+1 line: docker>=6.1.3)

Local Verification:
  ✓ Syntax check: PASSED
  ✓ Pip install test: docker installed successfully
  ✓ Import test: import docker works

Git Commit:
  Commit: abc1234
  Message: "fix: add docker package to requirements.txt"

[ROLLBACK] Restoring server state...
  → Using checkpoint: checkpoint_20260118_143022.tar.gz
  ✓ Server restored to clean state
  ✓ All processes stopped
  ✓ Virtual environment removed

Status: READY FOR RETRY
```

### Phase 6: Success (Final)

```
[SUCCESS] ✅ Deployment completed successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deployment Summary:
  • Total time: 4m 32s
  • Modules installed: 10/10
  • Success rate: 100%
  • Errors encountered: 0
  • Warnings: 0
  • Retries needed: 2

Module Results:
  ✓ system         - 2.3s
  ✓ security       - 5.1s
  ✓ docker         - 15.7s
  ✓ python         - 23.4s
  ✓ nodejs         - 18.9s
  ✓ git            - 3.2s
  ✓ neovim         - 8.1s
  ✓ vscode         - 12.3s
  ✓ utilities      - 6.7s
  ✓ desktop        - 45.2s

Post-Deployment Verification:
  ✓ All services running
  ✓ Configuration applied
  ✓ Logs clean (no errors)
  ✓ Server accessible
  ✓ Application functional

Final State:
  • Server IP: 170.64.232.208
  • Deployment: /opt/debian-vps-configurator
  • Logs: /var/log/debian-vps-configurator/
  • Backup: /root/checkpoints/ (3 checkpoints available)

Deployment SUCCESSFUL - Ready for use! 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# APPENDIX A: Complete Helper Script

## run_deploy_cycle.sh (Production-Ready)

Save this as `run_deploy_cycle.sh` in the project root and make it executable:

```bash
chmod +x run_deploy_cycle.sh
```

**Script contents:** See full script in the appendix below.

---

# APPENDIX B: Full Helper Script Code

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
    if grep -r "$SERVER_IP" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" --exclude="deploy_prompt*.md" . 2>/dev/null; then
        log_error "Found hardcoded IP in codebase!"
        exit 1
    fi
    log_success "✓ No hardcoded IPs found"

    if grep -r "$SERVER_PASS" --exclude-dir=".git" --exclude="*.md" --exclude="run_deploy_cycle.sh" --exclude="deploy_prompt*.md" . 2>/dev/null; then
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
    done < <(find configurator -name "*.py" -print0 2>/dev/null)

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
    ssh_exec "which python3-venv >/dev/null 2>&1 || (apt-get update && apt-get install -y python3-venv python3-pip)" >/dev/null 2>&1
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
        --exclude='deploy_prompt*.md' \
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

---

# Begin Deployment Protocol

## Initialize Deployment Session

**Step 1:** Create helper script:

```bash
# Copy the script above to run_deploy_cycle.sh
vim run_deploy_cycle.sh
chmod +x run_deploy_cycle.sh
```

**Step 2:** Create logs directory:

```bash
mkdir -p logs
```

**Step 3:** Initialize deployment log:

```bash
touch deployment_log.txt
```

**Step 4:** Run pre-flight checks (built into script)

**Step 5:** Begin first deployment attempt:

```bash
./run_deploy_cycle.sh
```

---

**Ready to proceed? Confirm and deployment will begin.** 🚀
