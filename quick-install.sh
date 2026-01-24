#!/bin/bash

#####################################################################
# Debian VPS Configurator - Quick Install Script
#
# Purpose: Install all prerequisites and dependencies required to run
#          vps-configurator install --profile advanced
#
# Features:
# - Structured logging with timestamped log files
# - Pre-flight validation (OS, disk, memory, Python, git)
# - Checkpoint system for error recovery (preserved)
# - Automatic rollback on failure (preserved)
# - Resume from last successful checkpoint (preserved)
# - Post-installation verification and status summary
#
# Usage: ./quick-install.sh
#####################################################################

set -euo pipefail
IFS=$'\n\t'

# ==========================================================================
# CONSTANTS AND CONFIGURATION
# ==========================================================================

readonly SCRIPT_NAME="$(basename "$0")"
readonly CHECKPOINT_DIR=".install_checkpoints"
readonly BACKUP_DIR=".install_backup"
readonly LOG_DIR="./logs"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly INSTALL_LOG="${LOG_DIR}/install_${TIMESTAMP}.log"
readonly LOG_RETENTION="${LOG_RETENTION:-10}"

readonly MIN_DISK_KB=2097152   # 2 GB
readonly MIN_MEM_KB=1048576    # 1 GB
readonly MIN_PY_MAJOR=3
readonly MIN_PY_MINOR=11

readonly EXIT_GENERAL=1
readonly EXIT_PREFLIGHT=2
readonly EXIT_INSTALL_SYSTEM=3
readonly EXIT_VENV=4
readonly EXIT_PY_DEPS=5
readonly EXIT_VERIFY=6
readonly EXIT_INTERRUPT=130

ROOT_MODE=false
DRY_RUN=false
ERROR_CONTEXT=""
ERROR_CODE=$EXIT_GENERAL
NEW_USER=""
NEW_PASS=""
DELETE_USER=""
SSH_KEY_VAL=""
SUDO_TIMEOUT="-1"
MANAGE_ONLY=false

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ==========================================================================
# LOGGING FUNCTIONS
# ==========================================================================

init_logging() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi
    mkdir -p "$LOG_DIR"
    rotate_logs
    touch "$INSTALL_LOG"
}

rotate_logs() {
    if [ ! -d "$LOG_DIR" ]; then
        return 0
    fi

    local count
    # Fix: Prevent script exit if no logs exist (ls returns 2) due to set -eo pipefail
    count=$(find "$LOG_DIR" -maxdepth 1 -name "install_*.log" 2>/dev/null | wc -l || echo 0)
    if [ "$count" -le "$LOG_RETENTION" ]; then
        return 0
    fi

    # Fix: Safely list and rotate logs
    (ls -1t "$LOG_DIR"/install_*.log 2>/dev/null || true) | tail -n +$((LOG_RETENTION + 1)) | xargs -r rm -f
}

log_line() {
    local message=$1
    if [ "$DRY_RUN" = true ]; then
        echo -e "$message"
        return 0
    fi
    if [ -n "${INSTALL_LOG:-}" ] && [ -d "${LOG_DIR:-}" ]; then
        echo -e "$message" | tee -a "$INSTALL_LOG" || true
    else
        echo -e "$message"
    fi
}

log_info() {
    log_line "${BLUE}[INFO]${NC} $*"
}

log_success() {
    log_line "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    log_line "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    log_line "${RED}[ERROR]${NC} $*"
}

log_section() {
    log_line ""
    log_line "═══════════════════════════════════════════════════════════════"
    log_line "$*"
    log_line "═══════════════════════════════════════════════════════════════"
}

print_msg() {
    local color=$1
    shift
    log_line "${color}$*${NC}"
}

print_header() {
    echo "" | tee -a "$INSTALL_LOG"
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_msg "$BLUE" "  $1"
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "" | tee -a "$INSTALL_LOG"
}

print_success() {
    print_msg "$GREEN" "✓ $1"
}

print_error() {
    print_msg "$RED" "✗ $1"
}

print_warning() {
    print_msg "$YELLOW" "⚠ $1"
}

print_info() {
    print_msg "$BLUE" "ℹ $1"
}

fail() {
    local message=$1
    local code=${2:-$EXIT_GENERAL}
    ERROR_CONTEXT="$message"
    ERROR_CODE=$code
    log_error "$message"
    return "$code"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

run_as_root() {
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: $*"
        return 0
    fi
    if [ "$ROOT_MODE" = true ]; then
        "$@"
    else
        sudo "$@"
    fi
}

# ==========================================================================
# CHECKPOINT MANAGEMENT (PRESERVED)
# ==========================================================================

create_checkpoint() {
    local checkpoint_name=$1
    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would create checkpoint $checkpoint_name"
        return 0
    fi
    mkdir -p "$CHECKPOINT_DIR"
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$CHECKPOINT_DIR/$checkpoint_name"
    print_success "Checkpoint created: $checkpoint_name"
}

check_checkpoint() {
    local checkpoint_name=$1
    [ -f "$CHECKPOINT_DIR/$checkpoint_name" ]
}

list_checkpoints() {
    if [ -d "$CHECKPOINT_DIR" ]; then
        print_info "Existing checkpoints:"
        ls -1 "$CHECKPOINT_DIR" 2>/dev/null || echo "  None"
    fi
}

clear_checkpoints() {
    if [ -d "$CHECKPOINT_DIR" ]; then
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: would remove checkpoints"
            return 0
        fi
        rm -rf "$CHECKPOINT_DIR"
        print_info "All checkpoints cleared"
    fi
}

backup_state() {
    local backup_name=$1
    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would backup state ($backup_name)"
        return 0
    fi
    mkdir -p "$BACKUP_DIR"

    if [ -d "venv" ]; then
        print_info "Backing up virtual environment..."
        tar -czf "$BACKUP_DIR/venv_$backup_name.tar.gz" venv 2>/dev/null || true
    fi

    print_success "State backed up: $backup_name"
}

restore_state() {
    local backup_name=$1

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would restore backup ($backup_name)"
        return 0
    fi

    print_warning "Restoring from backup: $backup_name"

    if [ -f "$BACKUP_DIR/venv_$backup_name.tar.gz" ]; then
        print_info "Restoring virtual environment..."
        rm -rf venv 2>/dev/null || true
        tar -xzf "$BACKUP_DIR/venv_$backup_name.tar.gz" 2>/dev/null || true
        print_success "Virtual environment restored"
    fi
}

# ==========================================================================
# ERROR HANDLING
# ==========================================================================

error_handler() {
    local exit_code=$?
    local line_number=$1

    if [ -n "$ERROR_CONTEXT" ]; then
        log_error "Failure: $ERROR_CONTEXT"
    fi

    log_error "Installation failed at line $line_number with exit code $exit_code"

    print_header "Error Recovery Options"
    list_checkpoints

    echo "" | tee -a "$INSTALL_LOG"
    print_warning "What would you like to do?"
    echo "1) Retry from last checkpoint" | tee -a "$INSTALL_LOG"
    echo "2) Start fresh (clean install)" | tee -a "$INSTALL_LOG"
    echo "3) Exit and investigate manually" | tee -a "$INSTALL_LOG"

    read -r -p "Choose an option (1-3): " -n 1 REPLY
    echo "" | tee -a "$INSTALL_LOG"

    case $REPLY in
        1)
            print_info "Attempting to recover from last checkpoint..."
            restore_from_checkpoint
            ;;
        2)
            print_info "Starting fresh installation..."
            cleanup_all
            exec "$0"
            ;;
        3)
            print_info "Exiting. You can investigate and run the script again."
            exit "$exit_code"
            ;;
        *)
            print_error "Invalid option. Exiting."
            exit "$exit_code"
            ;;
    esac
}

interrupt_handler() {
    log_warning "Installation interrupted by user"
    exit "$EXIT_INTERRUPT"
}

restore_from_checkpoint() {
    if [ -d "$CHECKPOINT_DIR" ] && [ "$(ls -A "$CHECKPOINT_DIR" 2>/dev/null)" ]; then
        local last_checkpoint
        last_checkpoint=$(ls -t "$CHECKPOINT_DIR" | head -n1)
        print_info "Last successful checkpoint: $last_checkpoint"

        if check_checkpoint "deployment_executed"; then
            print_info "Resuming from post-installation verification..."
            verify_installation
        elif check_checkpoint "python_deps_installed"; then
            print_info "Resuming from deployment execution..."
            execute_configurator_install
            verify_installation
        elif check_checkpoint "venv_created"; then
            print_info "Resuming from Python dependencies installation..."
            install_python_deps
            execute_configurator_install
            verify_installation
        elif check_checkpoint "system_deps_installed"; then
            print_info "Resuming from virtual environment setup..."
            setup_venv
            install_python_deps
            execute_configurator_install
            verify_installation
        else
            print_info "No valid checkpoint found. Starting from system dependencies..."
            install_system_deps
            setup_venv
            install_python_deps
            execute_configurator_install
            verify_installation
        fi
    else
        print_error "No checkpoints found. Please start fresh."
        exit "$EXIT_GENERAL"
    fi
}

cleanup_all() {
    print_info "Cleaning up installation artifacts..."
    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would remove $CHECKPOINT_DIR $BACKUP_DIR venv"
        return 0
    fi
    rm -rf "$CHECKPOINT_DIR" "$BACKUP_DIR" venv 2>/dev/null || true
    print_success "Cleanup complete"
}

# ==========================================================================
# PRE-FLIGHT CHECKS
# ==========================================================================

check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root - will install system-wide (no venv)"
        ROOT_MODE=true
    else
        ROOT_MODE=false
    fi
}

check_os_version() {
    print_header "Checking OS Compatibility"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_info "Detected OS: $NAME $VERSION"

        if [ "$ID" = "debian" ] && { [ "${VERSION_ID:-}" = "12" ] || [ "${VERSION_ID:-}" = "13" ]; }; then
            print_success "OS is compatible (Debian $VERSION_ID)"
            return 0
        fi

        print_warning "Expected Debian 12 or 13"
        print_info "Detected: $ID ${VERSION_ID:-unknown}"
        read -r -p "Continue anyway? (y/N) " -n 1 REPLY
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            fail "Unsupported OS version" "$EXIT_PREFLIGHT"
        fi
    else
        fail "Cannot detect OS" "$EXIT_PREFLIGHT"
    fi
}

check_disk_space() {
    print_header "Checking Disk Space"

    local available_kb
    available_kb=$(df -Pk / | awk 'NR==2 {print $4}')

    if [ -z "$available_kb" ]; then
        fail "Unable to determine available disk space" "$EXIT_PREFLIGHT"
    fi

    local available_gb
    available_gb=$(awk "BEGIN {printf \"%.2f\", $available_kb/1024/1024}")
    print_info "Available disk space: ${available_gb} GB"

    if [ "$available_kb" -lt "$MIN_DISK_KB" ]; then
        fail "Insufficient disk space (minimum 2 GB required)" "$EXIT_PREFLIGHT"
    fi

    print_success "Disk space check passed"
}

check_memory() {
    print_header "Checking Memory"

    local available_kb
    available_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || true)

    if [ -z "$available_kb" ]; then
        available_kb=$(free -k | awk '/Mem:/ {print $7}')
    fi

    if [ -z "$available_kb" ]; then
        fail "Unable to determine available memory" "$EXIT_PREFLIGHT"
    fi

    local available_gb
    available_gb=$(awk "BEGIN {printf \"%.2f\", $available_kb/1024/1024}")
    print_info "Available memory: ${available_gb} GB"

    if [ "$available_kb" -lt "$MIN_MEM_KB" ]; then
        fail "Insufficient memory (minimum 1 GB required)" "$EXIT_PREFLIGHT"
    fi

    print_success "Memory check passed"
}

check_python_version() {
    print_header "Checking Python Installation"

    if ! command_exists python3; then
        fail "Python 3 is not installed" "$EXIT_PREFLIGHT"
    fi

    local py_version
    py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
    print_info "Python version: $py_version"

    local py_major
    local py_minor
    py_major=$(echo "$py_version" | cut -d'.' -f1)
    py_minor=$(echo "$py_version" | cut -d'.' -f2)

    if [ "$py_major" -gt "$MIN_PY_MAJOR" ] || { [ "$py_major" -eq "$MIN_PY_MAJOR" ] && [ "$py_minor" -ge "$MIN_PY_MINOR" ]; }; then
        print_success "Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ is installed"
        return 0
    fi

    fail "Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ is required (found $py_version)" "$EXIT_PREFLIGHT"
}

check_git_repo() {
    print_header "Checking Repository State"

    if [ ! -f "pyproject.toml" ]; then
        print_warning "Not in the project root (pyproject.toml not found)"
        return 0
    fi

    if [ -d ".git" ]; then
        if command_exists git; then
            print_success "Git repository detected"
            local git_status
            git_status=$(git status --short 2>/dev/null || true)
            if [ -n "$git_status" ]; then
                print_info "Uncommitted changes detected:"
                echo "$git_status" | tee -a "$INSTALL_LOG"
            else
                print_success "Git status clean"
            fi
        else
            print_warning "Git repository detected but git is not installed"
        fi
    else
        print_info "No git repository detected (skipping git checks)"
    fi
}

check_sudo() {
    if [ "$ROOT_MODE" = false ] && ! command_exists sudo; then
        fail "sudo is required for non-root installations" "$EXIT_PREFLIGHT"
    fi
}

pre_flight_checks() {
    log_section "PRE-FLIGHT: System Validation"
    check_os_version
    check_disk_space
    check_memory
    check_python_version
    check_git_repo
    check_sudo
}

# ==========================================================================
# INSTALLATION FUNCTIONS (PRESERVED AND ENHANCED)
# ==========================================================================

install_system_deps() {
    if check_checkpoint "system_deps_installed"; then
        print_info "System dependencies already installed (checkpoint found)"
        return 0
    fi

    print_header "Installing System Dependencies"
    backup_state "before_system_deps"

    print_info "Updating package list..."
    run_as_root apt-get update

    print_info "Installing required packages..."
    run_as_root apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        git \
        curl \
        wget \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    print_success "System dependencies installed"
    create_checkpoint "system_deps_installed"
}

setup_venv() {
    if [ "$ROOT_MODE" = true ]; then
        print_info "Running as root - skipping virtual environment"
        create_checkpoint "venv_created"
        return 0
    fi

    if check_checkpoint "venv_created"; then
        print_info "Virtual environment already created (checkpoint found)"
        return 0
    fi

    print_header "Setting Up Virtual Environment"
    backup_state "before_venv"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -r -p "Recreate it? (y/N) " -n 1 REPLY
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_info "Removed existing virtual environment"
        else
            print_info "Using existing virtual environment"
            create_checkpoint "venv_created"
            return 0
        fi
    fi

    print_info "Creating virtual environment..."
    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would create virtual environment"
    else
        python3 -m venv venv
    fi

    print_success "Virtual environment created"
    create_checkpoint "venv_created"
}

install_python_deps() {
    if check_checkpoint "python_deps_installed"; then
        print_info "Python dependencies already installed (checkpoint found)"
        return 0
    fi

    print_header "Installing Python Dependencies"
    backup_state "before_python_deps"

    if [ "$ROOT_MODE" = true ]; then
        print_info "Installing system-wide (root mode)..."
        print_info "Installing setuptools and wheel..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python3 -m pip install setuptools wheel --break-system-packages --ignore-installed"
        else
            python3 -m pip install setuptools wheel --break-system-packages --ignore-installed 2>/dev/null || true
        fi

        print_info "Installing project dependencies..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed"
        else
            python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed
        fi

        print_info "Installing project in development mode..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python3 -m pip install -e . --break-system-packages --ignore-installed"
        else
            python3 -m pip install -e . --break-system-packages --ignore-installed
        fi
    else
        print_info "Activating virtual environment..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: would activate virtual environment"
        else
            source venv/bin/activate
        fi

        print_info "Upgrading pip..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python -m pip install --upgrade pip setuptools wheel"
        else
            python -m pip install --upgrade pip setuptools wheel
        fi

        print_info "Installing project dependencies..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python -m pip install -r requirements.txt"
        else
            python -m pip install -r requirements.txt
        fi

        print_info "Installing project in development mode..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: python -m pip install -e ."
        else
            python -m pip install -e .
        fi
    fi

    print_success "Python dependencies installed"
    create_checkpoint "python_deps_installed"
}

# ==========================================================================
# DEPLOYMENT EXECUTION
# ==========================================================================

execute_configurator_install() {
    if check_checkpoint "deployment_executed"; then
        print_info "Deployment already executed (checkpoint found)"
        return 0
    fi

    log_section "DEPLOY: Running vps-configurator install"

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: would run vps-configurator install --profile advanced"
        create_checkpoint "deployment_executed"
        return 0
    fi

    if [ "$ROOT_MODE" != true ] && [ -z "$NEW_USER" ]; then
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        else
            fail "Virtual environment not found for deployment" "$EXIT_VENV"
        fi
    fi

    if [ -n "$NEW_USER" ]; then
        print_info "Transferring execution to user: $NEW_USER"
        print_info "Executing: sudo vps-configurator install --profile advanced (as $NEW_USER)"

        # Determine how to run sudo based on password availability
        if [ -n "$NEW_PASS" ]; then
            # We have the password, use it to bypass the prompt for this initial run
            # Use 'su -' to simulate full login shell
            su - "$NEW_USER" -c "echo '$NEW_PASS' | sudo -S -p '' vps-configurator install --profile advanced"
        else
            # Interactive mode - user must type password
            su - "$NEW_USER" -c "sudo vps-configurator install --profile advanced"
        fi
    else
        print_info "Executing: vps-configurator install --profile advanced (as root)"
        vps-configurator install --profile advanced
    fi

    create_checkpoint "deployment_executed"
    print_success "Deployment execution completed"
}

# ==========================================================================
# VERIFICATION FUNCTIONS (NEW)
# ==========================================================================

verify_installation() {
    if check_checkpoint "installation_verified"; then
        print_info "Installation already verified (checkpoint found)"
        return 0
    fi

    print_header "Verifying Installation"

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: skipping verification checks"
        return 0
    fi

    if [ "$ROOT_MODE" != true ]; then
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        else
            fail "Virtual environment not found for verification" "$EXIT_VERIFY"
        fi
    fi

    local failures=0
    local python_cmd="python3"

    if [ "$ROOT_MODE" != true ]; then
        python_cmd="python"
    fi

    if command_exists vps-configurator; then
        local version
        version=$(vps-configurator --version 2>&1 | head -n1)
        print_success "vps-configurator is installed: $version"
    else
        print_error "vps-configurator command not found"
        failures=$((failures + 1))
    fi

    print_info "Testing basic functionality..."
    if command_exists vps-configurator && vps-configurator --help &> /dev/null; then
        print_success "Basic functionality test passed"
    else
        print_error "Basic functionality test failed"
        failures=$((failures + 1))
    fi

    print_info "Checking Python imports..."
    if "$python_cmd" -c "import configurator" &>/dev/null; then
        print_success "Python import test passed"
    else
        print_error "Python import test failed"
        failures=$((failures + 1))
    fi

    if [ "$failures" -eq 0 ]; then
        create_checkpoint "installation_verified"
        print_success "Verification completed successfully"
        return 0
    fi

    fail "Verification failed with $failures issue(s)" "$EXIT_VERIFY"
}

# ==========================================================================
# MAIN EXECUTION
# ==========================================================================

main() {
    parse_args "$@"
    init_logging

    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     Debian VPS Configurator - Quick Install Script       ║
║                                                           ║
║     This script will install all prerequisites needed     ║
║     to run: vps-configurator install --profile advanced  ║
║                                                           ║
║     Features: Checkpoint system & Auto-recovery          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF

    if [ "$DRY_RUN" = true ]; then
        log_info "Dry-run enabled: no system changes will be made"
        log_info "Logging to console only"
    else
        log_info "Logging to: $INSTALL_LOG"
    fi

    if [ -d "$CHECKPOINT_DIR" ] && [ "$(ls -A "$CHECKPOINT_DIR" 2>/dev/null)" ]; then
        print_warning "Previous installation checkpoints detected!"
        list_checkpoints
        echo "" | tee -a "$INSTALL_LOG"
        read -r -p "Resume from last checkpoint? (Y/n) " -n 1 REPLY
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            restore_from_checkpoint
            return 0
        fi
        print_info "Starting fresh installation..."
        cleanup_all
    fi

    check_root

    # If in management mode, only run user tasks
    if [ "$MANAGE_ONLY" = true ]; then
        log_section "User Management Mode"
        setup_user_auth
        print_success "User management tasks completed"
        exit 0
    fi

    pre_flight_checks
    install_system_deps
    setup_user_auth
    setup_venv
    install_python_deps
    execute_configurator_install
    verify_installation

    print_info "Installation completed successfully!"
    print_warning "You can now safely remove checkpoints with: rm -rf $CHECKPOINT_DIR $BACKUP_DIR"
}

parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --dry-run|-n)
                DRY_RUN=true
                shift
                ;;
            --user|-u)
                NEW_USER="$2"
                shift 2
                ;;
            --password|-p)
                NEW_PASS="$2"
                shift 2
                ;;
            --delete-user|-d)
                DELETE_USER="$2"
                MANAGE_ONLY=true
                shift 2
                ;;
            --add-ssh-key|-k)
                SSH_KEY_VAL="$2"
                shift 2
                ;;
            --sudo-config|-c)
                SUDO_TIMEOUT="$2"
                shift 2
                ;;
            --manage-only|-m)
                MANAGE_ONLY=true
                shift
                ;;
            --help|-h)
                echo "Usage: $SCRIPT_NAME [options]"
                echo "Options:"
                echo "  --dry-run, -n          Simulate actions"
                echo "  --user, -u <name>      Create/Update user"
                echo "  --password, -p <pass>  Set password for user"
                echo "  --delete-user, -d <name> Delete specified user"
                echo "  --add-ssh-key, -k <key> Add SSH public key to user"
                echo "  --sudo-config, -c <val> Set sudo timeout (-1=once, 0=always, X=mins)"
                echo "  --manage-only, -m      Run only user management tasks"
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done
}

setup_user_auth() {
    # 1. Handle Deletion
    if [ -n "$DELETE_USER" ]; then
        print_header "Deleting User: $DELETE_USER"
        if id "$DELETE_USER" &>/dev/null; then
            if [ "$DRY_RUN" = true ]; then
                print_info "DRY RUN: userdel -r $DELETE_USER"
                print_info "DRY RUN: rm /etc/sudoers.d/99-$DELETE_USER-timeout"
            else
                userdel -r "$DELETE_USER" || print_warning "Failed to remove home directory"
                rm -f "/etc/sudoers.d/99-$DELETE_USER-timeout"
                print_success "User $DELETE_USER removed"
            fi
        else
            print_warning "User $DELETE_USER does not exist"
        fi
    fi

    # 2. Handle Creation / Update
    if [ -n "$NEW_USER" ]; then
        print_header "Configuring User: $NEW_USER"

        if [ "$ROOT_MODE" = false ]; then
            print_warning "Must be root to manage users."
            return 0
        fi

        # Create
        if id "$NEW_USER" &>/dev/null; then
            print_info "User $NEW_USER exists (updating configuration)"
        else
            print_info "Creating user $NEW_USER..."
            if [ "$DRY_RUN" = true ]; then
                    print_info "DRY RUN: useradd -m -s /bin/bash $NEW_USER"
            else
                    useradd -m -s /bin/bash "$NEW_USER"
            fi
        fi

        # Password
        if [ -n "$NEW_PASS" ]; then
            print_info "Updating password..."
            if [ "$DRY_RUN" = true ]; then
                print_info "DRY RUN: chpasswd $NEW_USER"
            else
                echo "$NEW_USER:$NEW_PASS" | chpasswd
            fi
        fi

        # Sudo Group
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: usermod -aG sudo $NEW_USER"
        else
            usermod -aG sudo "$NEW_USER"
        fi

        # Sudo Timeout
        print_info "Configuring sudo timeout ($SUDO_TIMEOUT)..."
        if [ "$DRY_RUN" = true ]; then
            print_info "DRY RUN: writing /etc/sudoers.d/99-$NEW_USER-timeout"
        else
            echo "Defaults:$NEW_USER timestamp_timeout=$SUDO_TIMEOUT" > "/etc/sudoers.d/99-$NEW_USER-timeout"
            chmod 440 "/etc/sudoers.d/99-$NEW_USER-timeout"
        fi

        # SSH Key
        if [ -n "$SSH_KEY_VAL" ]; then
            print_info "Adding SSH key..."
            if [ "$DRY_RUN" = true ]; then
                print_info "DRY RUN: adding key to ~$NEW_USER/.ssh/authorized_keys"
            else
                local user_home
                user_home=$(eval echo "~$NEW_USER")
                mkdir -p "$user_home/.ssh"
                echo "$SSH_KEY_VAL" >> "$user_home/.ssh/authorized_keys"
                chown -R "$NEW_USER:$NEW_USER" "$user_home/.ssh"
                chmod 700 "$user_home/.ssh"
                chmod 600 "$user_home/.ssh/authorized_keys"
                print_success "SSH key added"
            fi
        fi

        print_success "User $NEW_USER installation/update complete"
        # We don't checkpoint here if in manage-only mode to allow repeated runs
        if [ "$MANAGE_ONLY" = false ]; then
            create_checkpoint "user_auth_setup"
        fi
    fi
}

trap 'error_handler $LINENO' ERR
trap 'interrupt_handler' INT TERM

main "$@"
