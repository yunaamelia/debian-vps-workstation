#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Snapshot Creation Script
# Creates comprehensive backups before terminal tools testing
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# =============================================================================
# MAIN SNAPSHOT CREATION
# =============================================================================

main() {
    log_section "Creating System Snapshot"

    ensure_dirs
    local backup_dir="$(get_backup_dir)"
    mkdir -p "$backup_dir"/{files,dirs,system}

    export LOG_FILE="${LOG_DIR}/snapshot-${TIMESTAMP}.log"

    log_info "Snapshot ID: ${SNAPSHOT_ID}"
    log_info "Backup directory: ${backup_dir}"

    # =========================================================================
    # 1. Shell Configuration Snapshot
    # =========================================================================
    log_section "Phase 1: Shell Configuration"

    backup_file "${HOME}/.zshrc" || log_warning ".zshrc not found"
    backup_file "${HOME}/.bashrc" || log_warning ".bashrc not found"
    backup_file "${HOME}/.profile" || log_warning ".profile not found"
    backup_file "${HOME}/.zprofile" || log_warning ".zprofile not found"
    backup_file "${HOME}/.zshenv" || log_warning ".zshenv not found"

    # =========================================================================
    # 2. Tool Configuration Snapshot
    # =========================================================================
    log_section "Phase 2: Tool Configurations"

    backup_dir "${HOME}/.config/bat" || log_warning "bat config not found"
    backup_dir "${HOME}/.config/eza" || log_warning "eza config not found"
    backup_dir "${HOME}/.config/zoxide" || log_warning "zoxide config not found"
    backup_dir "${HOME}/.config/fzf" || log_warning "fzf config not found"
    backup_dir "${HOME}/.oh-my-zsh" || log_warning "oh-my-zsh not found"

    # =========================================================================
    # 3. System State Snapshot
    # =========================================================================
    log_section "Phase 3: System State"

    local sys_dir="${backup_dir}/system"

    # Package list
    log_info "Capturing installed packages..."
    dpkg -l > "${sys_dir}/packages.txt" 2>/dev/null || apt list --installed > "${sys_dir}/packages.txt" 2>/dev/null || true

    # Environment
    log_info "Capturing environment..."
    env | sort > "${sys_dir}/env.txt"

    # Aliases
    log_info "Capturing aliases..."
    alias > "${sys_dir}/aliases.txt" 2>/dev/null || true

    # Binary locations
    log_info "Capturing binary locations..."
    {
        echo "eza: $(which eza 2>/dev/null || echo 'not installed')"
        echo "bat: $(which bat 2>/dev/null || which batcat 2>/dev/null || echo 'not installed')"
        echo "zoxide: $(which zoxide 2>/dev/null || echo 'not installed')"
        echo "zsh: $(which zsh 2>/dev/null || echo 'not installed')"
        echo "fzf: $(which fzf 2>/dev/null || echo 'not installed')"
    } > "${sys_dir}/binaries.txt"

    # Versions
    log_info "Capturing tool versions..."
    {
        echo "eza: $(get_tool_version eza)"
        echo "bat: $(get_tool_version bat)"
        echo "zoxide: $(get_tool_version zoxide)"
        echo "zsh: $(get_tool_version zsh)"
        echo "fzf: $(get_tool_version fzf)"
    } > "${sys_dir}/versions.txt"

    # PATH
    log_info "Capturing PATH..."
    echo "$PATH" > "${sys_dir}/path.txt"

    # =========================================================================
    # 4. Create Manifest
    # =========================================================================
    log_section "Phase 4: Creating Manifest"

    local manifest_path="$(create_manifest)"
    log_info "Manifest created: ${manifest_path}"

    # =========================================================================
    # Summary
    # =========================================================================
    log_section "Snapshot Complete"

    local file_count=$(find "${backup_dir}" -type f | wc -l)
    local dir_count=$(find "${backup_dir}" -type d | wc -l)
    local total_size=$(du -sh "${backup_dir}" | cut -f1)

    echo ""
    echo "  Snapshot ID:    ${SNAPSHOT_ID}"
    echo "  Location:       ${backup_dir}"
    echo "  Files backed:   ${file_count}"
    echo "  Directories:    ${dir_count}"
    echo "  Total size:     ${total_size}"
    echo "  Manifest:       ${manifest_path}"
    echo ""

    # Output snapshot ID for use by other scripts
    echo "${SNAPSHOT_ID}" > "${SNAPSHOT_DIR}/latest"

    log_success "Snapshot created successfully"
    echo "${SNAPSHOT_ID}"
}

main "$@"
