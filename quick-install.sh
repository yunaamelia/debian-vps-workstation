#!/bin/bash
# ==============================================================================
# quick-install.sh - Robust DevOps Deployment Pipeline for VPS Configurator
# ==============================================================================
#
# DESCRIPTION
#   Automates the deployment of the vps-configurator with a focus on reliability,
#   observability, and self-healing. Implements a sequential workflow with
#   automatic rollback and structured logging for AI analysis.
#
# WORKFLOW
#   1. Transfer (rsync)
#   2. Dependencies (apt/pip)
#   3. User Provisioning (security)
#   4. Environment (venv)
#   5. Execution (install)
#
# USAGE
#   ./quick-install.sh [options]
#
# OPTIONS
#   --user <name>       Target system user to create/use (default: vps-admin)
#   --password <pass>   Password for the target user (default: random)
#   --sync-source <dir> Path to source code for rsync transfer
#   --verbose           Enable debug logging
#   --max-retries <n>   Number of retry attempts on failure (default: 3)
#   --profile <name>    Configurator profile to run (default: advanced)
#   --timezone <tz>     System timezone (default: Asia/Jakarta)
#
# ==============================================================================

set -euo pipefail
IFS=$'\n\t'

# ==============================================================================
# GLOBAL CONSTANTS & CONFIGURATION
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly LOG_FILE="${LOG_DIR}/install_${TIMESTAMP}.log"

# Force unbuffered Python output for real-time logging
export PYTHONUNBUFFERED=1
# Prevent apt-get from hanging on prompts
export DEBIAN_FRONTEND=noninteractive

# Default Configuration
TARGET_USER="vps-admin"
TARGET_PASS=""
SYNC_SOURCE=""
VERBOSE=false
MAX_RETRIES=3
PROFILE="advanced"
TARGET_TIMEZONE="Asia/Jakarta"
DRY_RUN=false
RETRY_DELAY=5

# State Tracking
PHASE_STATE_FILE="${LOG_DIR}/.install_phase"
USER_CREATED_MARKER="${LOG_DIR}/.user_created"
PHASE_TRANSFER="TRANSFER"
PHASE_DEPS="DEPS"
PHASE_USER="USER"
PHASE_ENV="ENV"
PHASE_EXEC="EXEC"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# ==============================================================================
# LOGGING SYSTEM
# ==============================================================================

init_logging() {
    mkdir -p "$LOG_DIR"
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE" # Allow multiple users to write to log
    log "INFO" "INIT" "Logging initialized at $LOG_FILE"
}

# Format: [TIMESTAMP] [LEVEL] [PHASE:NAME] Message
log() {
    local level="$1"
    local phase="${2:-SYSTEM}"
    local message="$3"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    # Strip user/pass info for security mask
    if [[ -n "$TARGET_PASS" ]]; then
        message="${message//$TARGET_PASS/******}"
    fi

    # Console Output with Color
    local color=""
    case "$level" in
        INFO)    color="$BLUE" ;;
        SUCCESS) color="$GREEN" ;;
        WARNING) color="$YELLOW" ;;
        ERROR|FAIL)   color="$RED" ;;
        DEBUG)   color="$CYAN" ;;
        ACTION)  color="$NC" ;;
    esac

    # Don't print DEBUG to console unless verbose
    if [[ "$level" != "DEBUG" ]] || [[ "$VERBOSE" == "true" ]]; then
        echo -e "${color}[${timestamp}] [${level}] [PHASE:${phase}] ${message}${NC}" >&2
    fi

    # File Output (Plain text/Structured for AI)
    echo "[${timestamp}] [${level}] [PHASE:${phase}] ${message}" >> "$LOG_FILE"
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

root_check() {
    if [[ $EUID -ne 0 ]]; then
        log "WARNING" "INIT" "Not running as root. Sudo will be requested."
    fi
}

run_priv() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "ACTION" "DRY-RUN" "Would run: $*"
        return 0
    fi

    if [[ $EUID -eq 0 ]]; then
        "$@"
    else
        sudo -E "$@"
    fi
}

# ==============================================================================
# SYSTEM RESTORE (ROLLBACK)
# ==============================================================================

system_restore() {
    local phase="$1"
    log "ACTION" "RESTORE" "Initiating System Restore for failure in phase: $phase..."

    # Reverse order cleanup based on phase progression
    case "$phase" in
        "$PHASE_EXEC")
            log "INFO" "RESTORE" "Phase EXEC failure: Cleaning up..."
            # Fallthrough to lower layers
            ;&
        "$PHASE_ENV")
            log "INFO" "RESTORE" "Removing virtual environment..."
            if [[ "$DRY_RUN" != "true" ]]; then
                rm -rf "${SCRIPT_DIR}/venv"
            fi
            ;&
        "$PHASE_USER")
            log "INFO" "RESTORE" "Checking user provisioning cleanup..."
            if [[ -f "$USER_CREATED_MARKER" ]]; then
                log "WARNING" "RESTORE" "Deleting user '$TARGET_USER' (created by this script)..."
                if [[ "$DRY_RUN" != "true" ]]; then
                    # Force kill processes owned by user before removal
                    pkill -u "$TARGET_USER" || true
                    run_priv userdel -r "$TARGET_USER" || log "WARNING" "RESTORE" "Failed to remove user '$TARGET_USER'"
                    rm -f "$USER_CREATED_MARKER"
                fi
            else
                log "INFO" "RESTORE" "User '$TARGET_USER' was pre-existing or not created. Skipping deletion."
            fi
            ;&
        "$PHASE_DEPS")
             log "INFO" "RESTORE" "Phase DEPS: Rolling back DEPS is risky. Leaving packages."
             ;&
        "$PHASE_TRANSFER")
             log "INFO" "RESTORE" "Phase TRANSFER: Cleaning up transfer artifacts not implemented (requires file list)."
             ;;
        *)
            log "WARNING" "RESTORE" "Unknown phase or initial failure: $phase"
            ;;
    esac

    log "SUCCESS" "RESTORE" "System Restore actions completed."
}

# ==============================================================================
# WORKFLOW PHASES
# ==============================================================================

# 1. Codebase Transfer
phase_transfer() {
    echo "$PHASE_TRANSFER" > "$PHASE_STATE_FILE"
    if [[ -z "$SYNC_SOURCE" ]]; then
        log "INFO" "$PHASE_TRANSFER" "No sync source provided. Using current directory."
        return 0
    fi

    log "INFO" "$PHASE_TRANSFER" "Syncing from $SYNC_SOURCE..."

    if [[ ! -d "$SYNC_SOURCE" ]]; then
        log "FAIL" "$PHASE_TRANSFER" "Source directory not found: $SYNC_SOURCE"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "ACTION" "DRY-RUN" "Would rsync from $SYNC_SOURCE to $SCRIPT_DIR"
    else
        rsync -av \
            --exclude='.git' \
            --exclude='__pycache__' \
            --exclude='venv' \
            --exclude='logs' \
            "${SYNC_SOURCE}/" "${SCRIPT_DIR}/" >> "${LOG_FILE}" 2>&1
    fi

    log "SUCCESS" "$PHASE_TRANSFER" "Codebase transfer complete."
}

# 2. Dependency Initialization
phase_deps() {
    echo "$PHASE_DEPS" > "$PHASE_STATE_FILE"
    log "INFO" "$PHASE_DEPS" "Updating system package lists..."

    run_priv apt-get update -qq >> "${LOG_FILE}" 2>&1

    local sys_deps=(
        python3-pip
        python3-venv
        python3-dev
        build-essential
        libssl-dev
        libffi-dev
        git
        curl
        rsync
    )

    log "INFO" "$PHASE_DEPS" "Installing system dependencies: ${sys_deps[*]}"
    run_priv apt-get install -y "${sys_deps[@]}" >> "${LOG_FILE}" 2>&1

    log "SUCCESS" "$PHASE_DEPS" "System dependencies installed."
}

# 3. User Provisioning & Security
phase_user() {
    echo "$PHASE_USER" > "$PHASE_STATE_FILE"
    log "INFO" "$PHASE_USER" "Verifying user: $TARGET_USER"

    # Set system Timezone
    if [[ "$DRY_RUN" != "true" ]]; then
        run_priv timedatectl set-timezone "$TARGET_TIMEZONE" || log "WARNING" "$PHASE_USER" "Failed to set timezone to $TARGET_TIMEZONE"
    fi

    if ! id "$TARGET_USER" &>/dev/null; then
        log "INFO" "$PHASE_USER" "Creating user '$TARGET_USER'..."
        run_priv useradd -m -s /bin/bash "$TARGET_USER"

        # Mark user as created by us for rollback safety
        touch "$USER_CREATED_MARKER"

        if [[ -n "$TARGET_PASS" ]]; then
            echo "${TARGET_USER}:${TARGET_PASS}" | run_priv chpasswd
            log "INFO" "$PHASE_USER" "Password set for '$TARGET_USER'."
        fi
    else
        log "INFO" "$PHASE_USER" "User '$TARGET_USER' already exists."
    fi

    # Sudo setup
    log "INFO" "$PHASE_USER" "Configuring sudo privileges..."
    run_priv usermod -aG sudo "$TARGET_USER"

    # Allow passwordless sudo for automation comfort
    # WARNING: In highly secure envs, strictly limit this.
    echo "$TARGET_USER ALL=(ALL) NOPASSWD:ALL" | run_priv tee "/etc/sudoers.d/90-vps-configurator-$TARGET_USER" >/dev/null
    run_priv chmod 0440 "/etc/sudoers.d/90-vps-configurator-$TARGET_USER"

    # Add Go/Cargo to PATH for the target user globally
    local user_home
    if ! user_home=$(getent passwd "$TARGET_USER" | cut -d: -f6); then
        log "WARNING" "$PHASE_USER" "Could not determine home dir for $TARGET_USER. Assuming /home/$TARGET_USER"
        user_home="/home/$TARGET_USER"
    fi

    local profile_path="${user_home}/.profile"
    local bashrc_path="${user_home}/.bashrc"
    local path_line='export PATH=$PATH:/usr/local/go/bin:$HOME/.cargo/bin'

    if [[ "$DRY_RUN" != "true" ]]; then
        # Append to .profile if not present
        run_priv grep -qxF "$path_line" "$profile_path" || echo "$path_line" | run_priv tee -a "$profile_path" > /dev/null
        # Append to .bashrc if not present
        run_priv grep -qxF "$path_line" "$bashrc_path" || echo "$path_line" | run_priv tee -a "$bashrc_path" > /dev/null

        run_priv chown "$TARGET_USER:$TARGET_USER" "$profile_path" "$bashrc_path"
    fi

    log "SUCCESS" "$PHASE_USER" "User provisioning complete."
}

# 4. Environment Isolation
phase_env() {
    echo "$PHASE_ENV" > "$PHASE_STATE_FILE"
    log "INFO" "$PHASE_ENV" "Setting up Python Virtual Environment..."

    # Ensure correct ownership of the project dir so the user can write venv
    run_priv chown -R "$TARGET_USER:$TARGET_USER" "$SCRIPT_DIR"

    # Run venv creation as target user
    if [[ "$DRY_RUN" == "true" ]]; then
         log "ACTION" "DRY-RUN" "Would create venv at ${SCRIPT_DIR}/venv as $TARGET_USER"
         log "ACTION" "DRY-RUN" "Would install pip deps in venv"
         log "ACTION" "DRY-RUN" "Would install project in editable mode"
    else
        # Don't fail if venv exists, but we might want to clean it?
        # For now, we trust system_restore to clean it on failure.
        sudo -u "$TARGET_USER" python3 -m venv "${SCRIPT_DIR}/venv"

        log "DEBUG" "$PHASE_ENV" "Upgrading pip in venv..."
        sudo -u "$TARGET_USER" "${SCRIPT_DIR}/venv/bin/pip" install -U pip setuptools wheel >> "${LOG_FILE}" 2>&1

        log "INFO" "$PHASE_ENV" "Installing Python requirements..."
        if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
            sudo -u "$TARGET_USER" "${SCRIPT_DIR}/venv/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" >> "${LOG_FILE}" 2>&1
        fi

        # Install the package itself in editable mode
        sudo -u "$TARGET_USER" "${SCRIPT_DIR}/venv/bin/pip" install -e "${SCRIPT_DIR}" >> "${LOG_FILE}" 2>&1
    fi

    log "SUCCESS" "$PHASE_ENV" "Virtual Environment prepared."
}

# 5. Execution
phase_exec() {
    echo "$PHASE_EXEC" > "$PHASE_STATE_FILE"
    log "INFO" "$PHASE_EXEC" "Starting VPS Configurator (Profile: $PROFILE)..."

    local cmd_flags=""
    if [[ "$VERBOSE" == "true" ]]; then
         cmd_flags="--verbose"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "ACTION" "DRY-RUN" "Would execute: sudo -u $TARGET_USER vps-configurator install --profile $PROFILE $cmd_flags"
        return 0
    fi

    # Attempt execution (as root/current user)
    if ! sudo -E "${SCRIPT_DIR}/venv/bin/vps-configurator" install --profile "$PROFILE" $cmd_flags >> "${LOG_FILE}" 2>&1; then
        log "FAIL" "$PHASE_EXEC" "Configuration failed."
        return 1
    fi

    log "SUCCESS" "$PHASE_EXEC" "VPS Configurator Execution Successful."
}

# ==============================================================================
# MAIN CONTROL LOOP
# ==============================================================================

run_workflow() {
    phase_transfer
    phase_deps
    phase_user
    phase_env
    phase_exec
}

main() {
    # Parse Arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --user) TARGET_USER="$2"; shift 2 ;;
            --password) TARGET_PASS="$2"; shift 2 ;;
            --sync-source) SYNC_SOURCE="$2"; shift 2 ;;
            --verbose) VERBOSE=true; shift ;;
            --max-retries) MAX_RETRIES="$2"; shift 2 ;;
            --profile) PROFILE="$2"; shift 2 ;;
            --timezone) TARGET_TIMEZONE="$2"; shift 2 ;;
            --dry-run) DRY_RUN=true; shift ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done

    init_logging
    root_check

    log "INFO" "INIT" "Starting Deployment Workflow..."
    log "DEBUG" "INIT" "Configuration: User=$TARGET_USER, Source=${SYNC_SOURCE:-None}, Retries=$MAX_RETRIES"

    local attempt=1
    local success=false
    local max_attempts=$((MAX_RETRIES + 1))
    local current_delay=$RETRY_DELAY

    while [[ $attempt -le $max_attempts ]]; do
        if [[ $attempt -gt 1 ]]; then
            log "ACTION" "RETRY" "Starting Retry Attempt $attempt/$max_attempts in ${current_delay}s..."
            sleep "$current_delay"
            # Exponential backoff
            current_delay=$((current_delay * 2))
        fi

        log "INFO" "MAIN" "Deployment Attempt #$attempt"

        # Subshell execution to isolate failure
        set +e
        (
            set -e
            run_workflow
        )
        local status=$?
        set -e

        if [[ $status -eq 0 ]]; then
            success=true
            break
        else
            local failed_phase
            failed_phase=$(cat "$PHASE_STATE_FILE" 2>/dev/null || echo "UNKNOWN")
            log "ERROR" "MAIN" "Workflow failed in phase: $failed_phase (Exit Code: $status)"

            # Perform system restore to clean up for next attempt
            system_restore "$failed_phase"

            ((attempt++))
        fi
    done

    if [[ "$success" == "true" ]]; then
        log "SUCCESS" "MAIN" "Deployment Completed Successfully."
        exit 0
    else
        log "FAIL" "MAIN" "Deployment Failed after $((attempt - 1)) attempts."
        exit 1
    fi
}

main "$@"
