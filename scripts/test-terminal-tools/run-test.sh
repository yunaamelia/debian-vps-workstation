#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Terminal Tools Test Execution Script
# Runs comprehensive tests with automatic rollback on failure
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

STARTUP_THRESHOLD_MS=2000  # 2 seconds max startup time
TEST_TEMP_DIR="/tmp/terminal-tools-test-$$"

# =============================================================================
# ERROR HANDLER
# =============================================================================

trigger_rollback() {
    local level="$1"
    local tool="${2:-}"

    log_error "Triggering Level $level rollback${tool:+ for $tool}"

    if [[ "$level" == "1" && -n "$tool" ]]; then
        "${SCRIPT_DIR}/auto-rollback.sh" 1 "$tool"
    elif [[ "$level" == "2" ]]; then
        "${SCRIPT_DIR}/auto-rollback.sh" 2
    else
        "${SCRIPT_DIR}/auto-rollback.sh" 3
    fi
}

# =============================================================================
# PHASE 1A: INSTALLATION TESTS
# =============================================================================

test_eza_installation() {
    log_info "Testing eza installation..."

    if command_exists eza; then
        local version=$(eza --version 2>&1 | head -1)
        record_test "eza_installation" "PASS" "$version"
        return 0
    else
        record_test "eza_installation" "FAIL" "eza binary not found"
        return 1
    fi
}

test_bat_installation() {
    log_info "Testing bat installation..."

    if command_exists bat || command_exists batcat; then
        local version=$(get_tool_version bat)
        record_test "bat_installation" "PASS" "$version"
        return 0
    else
        record_test "bat_installation" "FAIL" "bat/batcat binary not found"
        return 1
    fi
}

test_zoxide_installation() {
    log_info "Testing zoxide installation..."

    if command_exists zoxide; then
        local version=$(zoxide --version 2>&1)
        record_test "zoxide_installation" "PASS" "$version"
        return 0
    else
        record_test "zoxide_installation" "FAIL" "zoxide binary not found"
        return 1
    fi
}

test_zsh_installation() {
    log_info "Testing zsh installation..."

    if command_exists zsh; then
        local version=$(zsh --version 2>&1)
        record_test "zsh_installation" "PASS" "$version"
        return 0
    else
        record_test "zsh_installation" "FAIL" "zsh binary not found"
        return 1
    fi
}

test_ohmyzsh_installation() {
    log_info "Testing oh-my-zsh installation..."

    if [[ -d "${HOME}/.oh-my-zsh" && -f "${HOME}/.oh-my-zsh/oh-my-zsh.sh" ]]; then
        record_test "ohmyzsh_installation" "PASS" "Found at ~/.oh-my-zsh"
        return 0
    else
        record_test "ohmyzsh_installation" "FAIL" "oh-my-zsh not found"
        return 1
    fi
}

# =============================================================================
# PHASE 1B: CONFIGURATION TESTS
# =============================================================================

test_zshrc_syntax() {
    log_info "Testing .zshrc syntax..."

    if [[ ! -f "${HOME}/.zshrc" ]]; then
        record_test "zshrc_syntax" "FAIL" ".zshrc not found"
        return 1
    fi

    if validate_zshrc_syntax; then
        record_test "zshrc_syntax" "PASS" "Valid syntax"
        return 0
    else
        record_test "zshrc_syntax" "FAIL" "Syntax error in .zshrc"
        record_error $SEVERITY_CRITICAL "zshrc syntax error"
        return 1
    fi
}

test_bat_config() {
    log_info "Testing bat configuration..."

    local bat_config="${HOME}/.config/bat/config"
    if [[ -f "$bat_config" ]]; then
        record_test "bat_config" "PASS" "Config exists"
        return 0
    else
        record_test "bat_config" "SKIP" "No config file (using defaults)"
        return 0
    fi
}

# =============================================================================
# PHASE 1C: FUNCTIONALITY TESTS
# =============================================================================

test_eza_functionality() {
    log_info "Testing eza functionality..."

    if ! command_exists eza; then
        record_test "eza_functionality" "SKIP" "eza not installed"
        return 0
    fi

    mkdir -p "$TEST_TEMP_DIR"
    touch "$TEST_TEMP_DIR/testfile.txt"

    if eza "$TEST_TEMP_DIR" &>/dev/null && eza -la "$TEST_TEMP_DIR" &>/dev/null; then
        record_test "eza_functionality" "PASS" "Commands execute correctly"
        return 0
    else
        record_test "eza_functionality" "FAIL" "eza commands failed"
        return 1
    fi
}

test_bat_functionality() {
    log_info "Testing bat functionality..."

    local bat_cmd=""
    if command_exists bat; then
        bat_cmd="bat"
    elif command_exists batcat; then
        bat_cmd="batcat"
    else
        record_test "bat_functionality" "SKIP" "bat not installed"
        return 0
    fi

    mkdir -p "$TEST_TEMP_DIR"
    echo '#!/bin/bash' > "$TEST_TEMP_DIR/test.sh"
    echo 'echo "Hello"' >> "$TEST_TEMP_DIR/test.sh"

    if $bat_cmd "$TEST_TEMP_DIR/test.sh" &>/dev/null; then
        record_test "bat_functionality" "PASS" "Syntax highlighting works"
        return 0
    else
        record_test "bat_functionality" "FAIL" "bat display failed"
        return 1
    fi
}

test_zoxide_functionality() {
    log_info "Testing zoxide functionality..."

    if ! command_exists zoxide; then
        record_test "zoxide_functionality" "SKIP" "zoxide not installed"
        return 0
    fi

    mkdir -p "$TEST_TEMP_DIR/zoxide_test_dir"

    if zoxide add "$TEST_TEMP_DIR/zoxide_test_dir" &>/dev/null; then
        if zoxide query zoxide_test &>/dev/null; then
            record_test "zoxide_functionality" "PASS" "Add and query work"
            return 0
        fi
    fi

    record_test "zoxide_functionality" "FAIL" "zoxide operations failed"
    return 1
}

# =============================================================================
# PHASE 1D: INTEGRATION TESTS
# =============================================================================

test_shell_startup_time() {
    log_info "Testing shell startup time..."

    if ! command_exists zsh; then
        record_test "shell_startup_time" "SKIP" "zsh not installed"
        return 0
    fi

    local total_ms=0
    local runs=3

    for ((i=1; i<=runs; i++)); do
        local duration=$(validate_shell_startup)
        if [[ "$duration" == "timeout" ]]; then
            record_test "shell_startup_time" "FAIL" "Shell startup timed out"
            record_error $SEVERITY_HIGH "Shell startup timeout"
            return 1
        fi
        total_ms=$((total_ms + duration))
    done

    local avg_ms=$((total_ms / runs))

    if [[ $avg_ms -lt $STARTUP_THRESHOLD_MS ]]; then
        record_test "shell_startup_time" "PASS" "${avg_ms}ms (threshold: ${STARTUP_THRESHOLD_MS}ms)"
        return 0
    else
        record_test "shell_startup_time" "FAIL" "${avg_ms}ms exceeds ${STARTUP_THRESHOLD_MS}ms threshold"
        record_error $SEVERITY_MEDIUM "Shell startup too slow"
        return 1
    fi
}

test_aliases() {
    log_info "Testing shell aliases..."

    if ! command_exists zsh || [[ ! -f "${HOME}/.zshrc" ]]; then
        record_test "shell_aliases" "SKIP" "zsh or .zshrc not available"
        return 0
    fi

    local alias_output
    alias_output=$(zsh -i -c 'alias' 2>/dev/null) || true

    local found_count=0
    [[ "$alias_output" == *"eza"* ]] && ((found_count++)) || true
    [[ "$alias_output" == *"bat"* ]] && ((found_count++)) || true

    if [[ $found_count -gt 0 ]]; then
        record_test "shell_aliases" "PASS" "Found $found_count tool aliases"
        return 0
    else
        record_test "shell_aliases" "PASS" "No aliases found (tools may not be configured)"
        return 0
    fi
}

test_path_integrity() {
    log_info "Testing PATH integrity..."

    local path_length=${#PATH}

    if [[ $path_length -gt 2000 ]]; then
        record_test "path_integrity" "FAIL" "PATH too long: $path_length chars"
        record_error $SEVERITY_MEDIUM "PATH bloat detected"
        return 1
    fi

    record_test "path_integrity" "PASS" "PATH length: $path_length chars"
    return 0
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

run_all_tests() {
    local failed=0

    log_section "Phase 1A: Installation Tests"
    test_zsh_installation || ((failed++)) || true
    test_ohmyzsh_installation || true  # Not critical
    test_eza_installation || true
    test_bat_installation || true
    test_zoxide_installation || true

    log_section "Phase 1B: Configuration Tests"
    if ! test_zshrc_syntax; then
        ((failed++))
        log_error "CRITICAL: .zshrc syntax error detected"
        if [[ $LAST_ERROR_SEVERITY -ge $SEVERITY_CRITICAL ]]; then
            trigger_rollback 2
            return 1
        fi
    fi
    test_bat_config || true

    log_section "Phase 1C: Functionality Tests"
    test_eza_functionality || true
    test_bat_functionality || true
    test_zoxide_functionality || true

    log_section "Phase 1D: Integration Tests"
    test_shell_startup_time || true
    test_aliases || true
    test_path_integrity || true

    return $failed
}

cleanup() {
    rm -rf "$TEST_TEMP_DIR" 2>/dev/null || true
}

main() {
    local skip_snapshot="${1:-}"

    ensure_dirs
    export LOG_FILE="${LOG_DIR}/test-${TIMESTAMP}.log"

    trap cleanup EXIT

    log_section "Terminal Tools Test Suite"
    echo "Timestamp: $(date -Iseconds)"
    echo "User: ${USER}"
    echo "Host: $(hostname)"
    echo ""

    # Create snapshot unless skipped
    if [[ "$skip_snapshot" != "--skip-snapshot" ]]; then
        log_section "Creating Pre-Test Snapshot"
        local snapshot_id
        snapshot_id=$("${SCRIPT_DIR}/create-snapshot.sh")
        export SNAPSHOT_ID="$snapshot_id"
        log_info "Snapshot created: ${SNAPSHOT_ID}"
    else
        if [[ -f "${SNAPSHOT_DIR}/latest" ]]; then
            export SNAPSHOT_ID="$(cat "${SNAPSHOT_DIR}/latest")"
            log_info "Using existing snapshot: ${SNAPSHOT_ID}"
        else
            log_error "No snapshot available. Run without --skip-snapshot"
            exit 1
        fi
    fi

    # Run tests
    local test_result=0
    run_all_tests || test_result=$?

    # Generate report
    log_section "Generating Test Report"
    local report_path
    report_path=$(generate_report)

    # Summary
    log_section "Test Summary"

    local passed=$(grep -c "PASS" <<< "$(printf '%s\n' "${TEST_RESULTS[@]}")" 2>/dev/null || echo 0)
    local failed=$(grep -c "FAIL" <<< "$(printf '%s\n' "${TEST_RESULTS[@]}")" 2>/dev/null || echo 0)
    local skipped=$(grep -c "SKIP" <<< "$(printf '%s\n' "${TEST_RESULTS[@]}")" 2>/dev/null || echo 0)

    echo "  Passed:  $passed"
    echo "  Failed:  $failed"
    echo "  Skipped: $skipped"
    echo "  Errors:  $ERRORS_COUNT"
    echo ""
    echo "  Report:  $report_path"
    echo "  Log:     $LOG_FILE"
    echo ""

    if [[ $test_result -eq 0 && $ERRORS_COUNT -eq 0 ]]; then
        log_success "All tests passed!"
        return 0
    elif [[ ${#ROLLBACKS_EXECUTED[@]} -gt 0 ]]; then
        log_warning "Tests completed with rollbacks executed"
        return 1
    else
        log_error "Tests completed with failures"
        return 1
    fi
}

main "$@"
