#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Automatic Rollback Script
# Restores system to pre-test state based on severity level
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# =============================================================================
# ROLLBACK FUNCTIONS
# =============================================================================

rollback_eza() {
    log_section "Rollback: eza"

    # Remove binary
    sudo rm -f /usr/local/bin/eza 2>/dev/null || true
    sudo rm -f /usr/bin/eza 2>/dev/null || true

    # Remove config
    rm -rf "${HOME}/.config/eza" 2>/dev/null || true

    # Restore from backup
    local backup_dir="$(get_backup_dir)/dirs/.config/eza"
    if [[ -d "$backup_dir" ]]; then
        mkdir -p "${HOME}/.config"
        cp -a "$backup_dir" "${HOME}/.config/eza"
        log_info "Restored eza config from backup"
    fi

    # Remove aliases from .zshrc
    if [[ -f "${HOME}/.zshrc" ]]; then
        sed -i '/alias.*eza/d' "${HOME}/.zshrc" 2>/dev/null || true
        sed -i '/EZA_ICONS_AUTO/d' "${HOME}/.zshrc" 2>/dev/null || true
    fi

    ROLLBACKS_EXECUTED+=("eza")
    log_success "eza rollback complete"
}

rollback_bat() {
    log_section "Rollback: bat"

    # Remove binary
    sudo rm -f /usr/local/bin/bat 2>/dev/null || true
    # Don't remove batcat as it's from apt

    # Remove config
    rm -rf "${HOME}/.config/bat" 2>/dev/null || true

    # Restore from backup
    local backup_dir="$(get_backup_dir)/dirs/.config/bat"
    if [[ -d "$backup_dir" ]]; then
        mkdir -p "${HOME}/.config"
        cp -a "$backup_dir" "${HOME}/.config/bat"
        log_info "Restored bat config from backup"
    fi

    # Remove aliases from .zshrc
    if [[ -f "${HOME}/.zshrc" ]]; then
        sed -i '/alias.*bat/d' "${HOME}/.zshrc" 2>/dev/null || true
    fi

    ROLLBACKS_EXECUTED+=("bat")
    log_success "bat rollback complete"
}

rollback_zoxide() {
    log_section "Rollback: zoxide"

    # Remove binary
    sudo rm -f /usr/local/bin/zoxide 2>/dev/null || true

    # Remove config and database
    rm -rf "${HOME}/.config/zoxide" 2>/dev/null || true
    rm -rf "${HOME}/.local/share/zoxide" 2>/dev/null || true

    # Restore from backup
    local backup_dir="$(get_backup_dir)/dirs/.config/zoxide"
    if [[ -d "$backup_dir" ]]; then
        mkdir -p "${HOME}/.config"
        cp -a "$backup_dir" "${HOME}/.config/zoxide"
        log_info "Restored zoxide config from backup"
    fi

    # Remove from .zshrc
    if [[ -f "${HOME}/.zshrc" ]]; then
        sed -i '/zoxide init/d' "${HOME}/.zshrc" 2>/dev/null || true
        sed -i '/alias j=/d' "${HOME}/.zshrc" 2>/dev/null || true
        sed -i '/alias ji=/d' "${HOME}/.zshrc" 2>/dev/null || true
    fi

    ROLLBACKS_EXECUTED+=("zoxide")
    log_success "zoxide rollback complete"
}

rollback_ohmyzsh() {
    log_section "Rollback: oh-my-zsh"

    # Remove oh-my-zsh directory
    rm -rf "${HOME}/.oh-my-zsh" 2>/dev/null || true

    # Restore from backup
    local backup_dir="$(get_backup_dir)/dirs/.oh-my-zsh"
    if [[ -d "$backup_dir" ]]; then
        cp -a "$backup_dir" "${HOME}/.oh-my-zsh"
        log_info "Restored oh-my-zsh from backup"
    fi

    ROLLBACKS_EXECUTED+=("oh-my-zsh")
    log_success "oh-my-zsh rollback complete"
}

rollback_zshrc() {
    log_section "Rollback: .zshrc"

    local backup_file="$(get_backup_dir)/files/.zshrc"
    if [[ -f "$backup_file" ]]; then
        cp -a "$backup_file" "${HOME}/.zshrc"
        log_info "Restored .zshrc from backup"

        # Verify syntax
        if validate_zshrc_syntax; then
            log_success ".zshrc syntax valid after restore"
        else
            log_error ".zshrc syntax still invalid - restoring bashrc"
            rollback_bashrc
        fi
    else
        log_warning "No .zshrc backup found"
    fi

    ROLLBACKS_EXECUTED+=(".zshrc")
    log_success ".zshrc rollback complete"
}

rollback_bashrc() {
    log_section "Emergency Rollback: .bashrc"

    local backup_file="$(get_backup_dir)/files/.bashrc"
    if [[ -f "$backup_file" ]]; then
        cp -a "$backup_file" "${HOME}/.bashrc"
        log_info "Restored .bashrc from backup"
    fi

    ROLLBACKS_EXECUTED+=(".bashrc (emergency)")
    log_success ".bashrc restored as emergency fallback"
}

# =============================================================================
# ROLLBACK LEVELS
# =============================================================================

level1_rollback() {
    local tool="$1"
    log_section "Level 1 Rollback: $tool"

    case "$tool" in
        eza)     rollback_eza ;;
        bat)     rollback_bat ;;
        zoxide)  rollback_zoxide ;;
        ohmyzsh) rollback_ohmyzsh ;;
        zshrc)   rollback_zshrc ;;
        *)       log_error "Unknown tool: $tool" ;;
    esac
}

level2_rollback() {
    log_section "Level 2 Rollback: Shell Configuration"

    rollback_zshrc
    rollback_ohmyzsh

    # Reload shell if possible
    if command_exists zsh && validate_zshrc_syntax; then
        log_info "Shell config restored and validated"
    else
        rollback_bashrc
    fi
}

level3_rollback() {
    log_section "Level 3 Rollback: FULL SYSTEM RESTORATION"

    log_warning "Executing catastrophic rollback..."

    # Restore ALL tools
    rollback_eza
    rollback_bat
    rollback_zoxide
    rollback_ohmyzsh
    rollback_zshrc

    # Restore all backup files
    local backup_dir="$(get_backup_dir)"
    if [[ -d "$backup_dir/files" ]]; then
        find "$backup_dir/files" -type f | while read -r backup_file; do
            local rel_path="${backup_file#$backup_dir/files/}"
            local target="${HOME}/${rel_path}"
            mkdir -p "$(dirname "$target")"
            cp -a "$backup_file" "$target"
            log_info "Restored: $target"
        done
    fi

    # Restore all backup directories
    if [[ -d "$backup_dir/dirs" ]]; then
        find "$backup_dir/dirs" -mindepth 1 -maxdepth 1 -type d | while read -r backup_subdir; do
            local rel_path="${backup_subdir#$backup_dir/dirs/}"
            local target="${HOME}/${rel_path}"
            rm -rf "$target"
            cp -a "$backup_subdir" "$target"
            log_info "Restored directory: $target"
        done
    fi

    # Restore PATH from backup
    local path_backup="$backup_dir/system/path.txt"
    if [[ -f "$path_backup" ]]; then
        export PATH="$(cat "$path_backup")"
        log_info "PATH restored from backup"
    fi

    ROLLBACKS_EXECUTED+=("FULL SYSTEM")
    log_success "Full system rollback complete"
    log_warning "Manual review recommended"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local level="${1:-}"
    local tool="${2:-}"

    # Load latest snapshot
    if [[ -f "${SNAPSHOT_DIR}/latest" ]]; then
        export SNAPSHOT_ID="$(cat "${SNAPSHOT_DIR}/latest")"
        log_info "Using snapshot: ${SNAPSHOT_ID}"
    else
        log_error "No snapshot found. Run create-snapshot.sh first."
        exit 1
    fi

    export LOG_FILE="${LOG_DIR}/rollback-${TIMESTAMP}.log"

    case "$level" in
        1)
            if [[ -z "$tool" ]]; then
                log_error "Level 1 requires tool name: eza, bat, zoxide, ohmyzsh, zshrc"
                exit 1
            fi
            level1_rollback "$tool"
            ;;
        2)
            level2_rollback
            ;;
        3)
            level3_rollback
            ;;
        *)
            echo "Usage: $0 <level> [tool]"
            echo ""
            echo "Levels:"
            echo "  1 <tool>  - Tool-specific rollback (eza, bat, zoxide, ohmyzsh, zshrc)"
            echo "  2         - Shell configuration rollback"
            echo "  3         - Full system restoration"
            exit 1
            ;;
    esac

    # Generate rollback report
    echo ""
    log_section "Rollback Summary"
    echo "Rollbacks executed:"
    printf '  - %s\n' "${ROLLBACKS_EXECUTED[@]}"
    echo ""
    log_success "Rollback procedure complete"
}

main "$@"
