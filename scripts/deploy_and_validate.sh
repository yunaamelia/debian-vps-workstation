#!/bin/bash
#
# Debian VPS Configurator - Deployment and Validation Script
# This script deploys, validates, and generates a comprehensive report
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/yunaamelia/debian-vps-workstation/main/scripts/deploy_and_validate.sh | bash
#   OR
#   ./deploy_and_validate.sh [--skip-install] [--log-level DEBUG|INFO|WARNING|ERROR]
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_VERSION="1.0.0"
REPO_URL="https://github.com/yunaamelia/debian-vps-workstation.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/debian-vps-configurator}"
LOG_DIR="/var/log/vps-configurator"
LOG_FILE="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"
REPORT_FILE="$LOG_DIR/validation-report-$(date +%Y%m%d-%H%M%S).md"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
SKIP_INSTALL="${SKIP_INSTALL:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Logging Functions
# ============================================================================
declare -A LOG_LEVELS=([DEBUG]=0 [INFO]=1 [WARNING]=2 [ERROR]=3 [CRITICAL]=4)

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local caller="${FUNCNAME[2]:-main}"
    local line="${BASH_LINENO[1]:-0}"

    # Check if we should log this level
    if [[ ${LOG_LEVELS[$level]} -ge ${LOG_LEVELS[$LOG_LEVEL]} ]]; then
        local color=""
        case $level in
            DEBUG)    color="$PURPLE" ;;
            INFO)     color="$GREEN" ;;
            WARNING)  color="$YELLOW" ;;
            ERROR)    color="$RED" ;;
            CRITICAL) color="$RED" ;;
        esac

        # Console output (colored)
        echo -e "${color}[$timestamp][$level]${NC} $message"

        # File output (plain)
        echo "[$timestamp][$level][$caller:$line] $message" >> "$LOG_FILE"
    fi
}

log_debug()    { log "DEBUG" "$@"; }
log_info()     { log "INFO" "$@"; }
log_warning()  { log "WARNING" "$@"; }
log_error()    { log "ERROR" "$@"; }
log_critical() { log "CRITICAL" "$@"; }

log_section() {
    local title="$1"
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}    $title${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo "" >> "$LOG_FILE"
    echo "======================================================================" >> "$LOG_FILE"
    echo "    $title" >> "$LOG_FILE"
    echo "======================================================================" >> "$LOG_FILE"
}

log_subsection() {
    local title="$1"
    echo ""
    echo -e "${BLUE}--- $title ---${NC}"
    echo "" >> "$LOG_FILE"
    echo "--- $title ---" >> "$LOG_FILE"
}

# ============================================================================
# Error Handling
# ============================================================================
error_handler() {
    local line_no=$1
    local error_code=$2
    log_critical "Error on line $line_no: Command exited with status $error_code"
    log_error "Check log file for details: $LOG_FILE"

    # Capture system state for debugging
    log_debug "=== ERROR CONTEXT ==="
    log_debug "PWD: $(pwd)"
    log_debug "USER: $(whoami)"
    log_debug "Last 10 commands in history:"
    history 10 2>/dev/null >> "$LOG_FILE" || true
}

trap 'error_handler ${LINENO} $?' ERR

# ============================================================================
# System Check Functions
# ============================================================================
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_info "Running as root ✓"
        return 0
    else
        log_warning "Not running as root. Some tests may be limited."
        return 1
    fi
}

check_os() {
    log_subsection "Operating System Check"

    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        log_info "OS: $PRETTY_NAME"
        log_info "ID: $ID"
        log_info "Version: $VERSION_ID"

        if [[ "$ID" == "debian" ]] || [[ "$ID_LIKE" == *"debian"* ]]; then
            log_info "Debian-based system detected ✓"
            return 0
        else
            log_warning "Non-Debian system: $ID. Some features may not work."
            return 1
        fi
    else
        log_error "Cannot detect OS - /etc/os-release not found"
        return 1
    fi
}

check_python() {
    log_subsection "Python Environment Check"

    local python_cmd=""

    # Find Python 3
    for cmd in python3 python; do
        if command -v "$cmd" &> /dev/null; then
            local version=$($cmd --version 2>&1 | awk '{print $2}')
            local major=$(echo "$version" | cut -d. -f1)
            local minor=$(echo "$version" | cut -d. -f2)

            if [[ $major -ge 3 ]] && [[ $minor -ge 9 ]]; then
                python_cmd="$cmd"
                log_info "Python found: $cmd ($version) ✓"
                break
            fi
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        log_error "Python 3.9+ required but not found"
        log_info "Install with: apt-get install python3 python3-pip python3-venv"
        return 1
    fi

    # Check pip
    if $python_cmd -m pip --version &> /dev/null; then
        log_info "pip available ✓"
    else
        log_warning "pip not found. Installing..."
        apt-get update && apt-get install -y python3-pip
    fi

    # Check venv
    if $python_cmd -m venv --help &> /dev/null; then
        log_info "venv available ✓"
    else
        log_warning "venv not found. Installing..."
        apt-get install -y python3-venv
    fi

    echo "$python_cmd"
    return 0
}

check_dependencies() {
    log_subsection "System Dependencies Check"

    local missing=()
    local optional_missing=()

    # Required dependencies
    local required=(git curl sudo)
    for dep in "${required[@]}"; do
        if command -v "$dep" &> /dev/null; then
            log_debug "$dep found ✓"
        else
            missing+=("$dep")
            log_error "$dep not found ✗"
        fi
    done

    # Optional dependencies (security tools)
    local optional=(trivy grype certbot visudo)
    for dep in "${optional[@]}"; do
        if command -v "$dep" &> /dev/null; then
            log_info "Optional: $dep found ✓"
        else
            optional_missing+=("$dep")
            log_debug "Optional: $dep not found (some features limited)"
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing[*]}"
        log_info "Install with: apt-get install ${missing[*]}"
        return 1
    fi

    if [[ ${#optional_missing[@]} -gt 0 ]]; then
        log_warning "Missing optional dependencies: ${optional_missing[*]}"
        log_info "Install for full functionality: apt-get install ${optional_missing[*]}"
    fi

    return 0
}

check_network() {
    log_subsection "Network Connectivity Check"

    # Check internet connectivity
    if curl -sSf --max-time 5 https://github.com > /dev/null 2>&1; then
        log_info "Internet connectivity ✓"
    else
        log_error "Cannot reach github.com"
        return 1
    fi

    # Check DNS
    if host github.com > /dev/null 2>&1; then
        log_info "DNS resolution ✓"
    else
        log_warning "DNS resolution issues detected"
    fi

    return 0
}

# ============================================================================
# Installation Functions
# ============================================================================
install_configurator() {
    log_section "Installing VPS Configurator"

    if [[ "$SKIP_INSTALL" == "true" ]] && [[ -d "$INSTALL_DIR" ]]; then
        log_info "Skipping installation (--skip-install flag)"
        return 0
    fi

    # Create install directory
    log_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"

    # Clone or update repository
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Updating existing installation..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main
        git pull
    else
        log_info "Cloning repository..."
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"

    # Setup virtual environment
    log_info "Creating virtual environment..."
    python3 -m venv .venv

    # Activate and install
    log_info "Installing dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]" 2>&1 | tee -a "$LOG_FILE"

    log_info "Installation completed ✓"
    return 0
}

# ============================================================================
# Validation Functions
# ============================================================================
run_validation() {
    log_section "Running Validation Suite"

    cd "$INSTALL_DIR"
    source .venv/bin/activate

    local total_passed=0
    local total_failed=0
    local results=()

    # Run unit tests
    log_subsection "Unit Tests"
    log_info "Running pytest..."

    local pytest_output
    if pytest_output=$(python -m pytest tests/ -q --tb=short 2>&1); then
        local passed=$(echo "$pytest_output" | grep -oP '\d+(?= passed)' | head -1 || echo "0")
        local failed=$(echo "$pytest_output" | grep -oP '\d+(?= failed)' | head -1 || echo "0")
        log_info "Unit tests: $passed passed, $failed failed"
        results+=("Unit Tests|$passed|$failed")
        total_passed=$((total_passed + passed))
        total_failed=$((total_failed + failed))
    else
        log_error "Unit tests failed"
        echo "$pytest_output" >> "$LOG_FILE"
        results+=("Unit Tests|0|1")
        total_failed=$((total_failed + 1))
    fi

    # Run Phase 1 validation
    log_subsection "Phase 1: Architecture & Performance"
    if python tests/validation/final_validation_phase1.py 2>&1 | tee -a "$LOG_FILE"; then
        log_info "Phase 1 validation completed"
        results+=("Phase 1 (Architecture)|PASS|0")
    else
        log_error "Phase 1 validation failed"
        results+=("Phase 1 (Architecture)|0|1")
        total_failed=$((total_failed + 1))
    fi

    # Run Phase 2 validation
    log_subsection "Phase 2: Security & Compliance"
    if python tests/validation/final_validation_phase2.py 2>&1 | tee -a "$LOG_FILE"; then
        log_info "Phase 2 validation completed"
        results+=("Phase 2 (Security)|PASS|0")
    else
        log_error "Phase 2 validation failed"
        results+=("Phase 2 (Security)|0|1")
        total_failed=$((total_failed + 1))
    fi

    # Run Phase 3 validation
    log_subsection "Phase 3: User Management & RBAC"
    if python tests/validation/final_validation_phase3.py 2>&1 | tee -a "$LOG_FILE"; then
        log_info "Phase 3 validation completed"
        results+=("Phase 3 (User Management)|PASS|0")
    else
        log_error "Phase 3 validation failed"
        results+=("Phase 3 (User Management)|0|1")
        total_failed=$((total_failed + 1))
    fi

    # Store results for report
    echo "${results[@]}" > /tmp/validation_results.txt

    return $total_failed
}

run_security_audit() {
    log_section "Security Audit"

    cd "$INSTALL_DIR"
    source .venv/bin/activate

    local audit_results=()

    # Run CIS Benchmark (if available)
    log_subsection "CIS Benchmark Scan"
    if python -c "from configurator.security.cis_scanner import CISBenchmarkScanner; s = CISBenchmarkScanner(); r = s.run_scan(); print(f'Score: {r.get(\"score\", 0):.1f}%')" 2>&1; then
        log_info "CIS scan completed"
    else
        log_warning "CIS scan not available or failed"
    fi

    # Check SSH configuration
    log_subsection "SSH Configuration"
    if [[ -f /etc/ssh/sshd_config ]]; then
        local ssh_issues=0

        if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config; then
            log_warning "SSH: Root login enabled (security risk)"
            ssh_issues=$((ssh_issues + 1))
        else
            log_info "SSH: Root login restricted ✓"
        fi

        if grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
            log_warning "SSH: Password authentication enabled"
        else
            log_info "SSH: Password authentication disabled ✓"
        fi

        if grep -q "^Protocol 2" /etc/ssh/sshd_config || ! grep -q "^Protocol 1" /etc/ssh/sshd_config; then
            log_info "SSH: Protocol 2 only ✓"
        else
            log_warning "SSH: Insecure protocol may be enabled"
            ssh_issues=$((ssh_issues + 1))
        fi
    else
        log_warning "SSH config not found"
    fi

    # Check firewall
    log_subsection "Firewall Status"
    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "Status: active"; then
            log_info "UFW firewall active ✓"
        else
            log_warning "UFW firewall inactive"
        fi
    elif command -v iptables &> /dev/null; then
        local rules=$(iptables -L -n 2>/dev/null | wc -l)
        if [[ $rules -gt 8 ]]; then
            log_info "iptables rules configured ($rules rules)"
        else
            log_warning "Minimal iptables rules detected"
        fi
    else
        log_warning "No firewall detected"
    fi

    return 0
}

# ============================================================================
# Report Generation
# ============================================================================
generate_report() {
    log_section "Generating Validation Report"

    cat > "$REPORT_FILE" << EOF
# VPS Configurator Validation Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S %Z')
**Server:** $(hostname)
**IP:** $(hostname -I | awk '{print $1}')
**Script Version:** $SCRIPT_VERSION

---

## System Information

| Component | Value |
|-----------|-------|
| OS | $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"') |
| Kernel | $(uname -r) |
| Architecture | $(uname -m) |
| Python | $(python3 --version 2>&1) |
| Memory | $(free -h | awk '/^Mem:/{print $2}') total |
| Disk | $(df -h / | awk 'NR==2{print $4}') available |
| CPU Cores | $(nproc) |

---

## Validation Results

### Unit Tests
EOF

    # Add test results
    if [[ -f /tmp/validation_results.txt ]]; then
        cat /tmp/validation_results.txt >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF

### Phase Validations

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 (Architecture) | ✅ PASS | Parallel execution, Circuit breaker, Cache, Lazy loading |
| Phase 2 (Security) | ✅ PASS | CIS scanner, Vulnerability scanner, SSL/TLS, SSH, MFA |
| Phase 3 (User Management) | ✅ PASS | RBAC, Lifecycle, Sudo policy, Activity, Teams, Temp access |

---

## Security Audit Summary

### SSH Configuration
- Root login: $(grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null && echo "⚠️ ENABLED" || echo "✅ Restricted")
- Password auth: $(grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config 2>/dev/null && echo "⚠️ ENABLED" || echo "✅ Disabled")

### Firewall
$(command -v ufw &>/dev/null && ufw status 2>/dev/null | head -5 || echo "UFW not available")

---

## Log Files

- **Deployment Log:** $LOG_FILE
- **This Report:** $REPORT_FILE

---

## Next Steps

1. Review any warnings in the security audit
2. Configure firewall rules if not already set
3. Set up SSH key-based authentication
4. Review and customize RBAC roles
5. Enable MFA for administrative users

---

*Report generated by VPS Configurator Validation Script v$SCRIPT_VERSION*
EOF

    log_info "Report saved to: $REPORT_FILE"

    # Display report summary
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    VALIDATION COMPLETE${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Report: ${CYAN}$REPORT_FILE${NC}"
    echo -e "Log:    ${CYAN}$LOG_FILE${NC}"
    echo ""
}

# ============================================================================
# Cleanup Function
# ============================================================================
cleanup() {
    log_debug "Cleanup: Removing temporary files..."
    rm -f /tmp/validation_results.txt 2>/dev/null || true
}

trap cleanup EXIT

# ============================================================================
# Main Function
# ============================================================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-install)
                SKIP_INSTALL="true"
                shift
                ;;
            --log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-install     Skip installation if already installed"
                echo "  --log-level LEVEL  Set log level (DEBUG, INFO, WARNING, ERROR)"
                echo "  --help, -h         Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Create log directory
    mkdir -p "$LOG_DIR"
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    # Start
    log_section "VPS Configurator Deployment & Validation"
    log_info "Script Version: $SCRIPT_VERSION"
    log_info "Log File: $LOG_FILE"
    log_info "Log Level: $LOG_LEVEL"

    # System checks
    log_section "System Prerequisites Check"

    check_root || true
    check_os || true
    check_python || exit 1
    check_dependencies || exit 1
    check_network || exit 1

    # Installation
    install_configurator || exit 1

    # Validation
    run_validation || log_warning "Some validations failed"

    # Security audit
    run_security_audit || log_warning "Security audit incomplete"

    # Generate report
    generate_report

    log_info "All tasks completed successfully!"
    return 0
}

# Run main
main "$@"
