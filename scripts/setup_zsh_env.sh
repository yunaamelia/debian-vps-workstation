#!/bin/bash
# Debian VPS Zsh Environment Setup with Best Practices
# Installs and configures: zsh, oh-my-zsh, eza, bat, zoxide
# With optimized plugin loading order and modern zsh features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Phase 1: Update system and install tools
# ============================================================================
log_info "Phase 1: Installing system tools..."
sudo apt-get update
sudo apt-get install --reinstall -y zsh bat eza zoxide curl git

# ============================================================================
# Phase 2: Handle Debian bat alias (bat -> batcat)
# ============================================================================
log_info "Phase 2: Configuring bat symlink for Debian..."
if command -v batcat &> /dev/null; then
    if [ ! -f /usr/local/bin/bat ]; then
        log_info "Creating symlink: batcat → bat"
        sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
    else
        log_info "bat symlink already exists"
    fi
fi

# ============================================================================
# Phase 3: Install Oh My Zsh
# ============================================================================
log_info "Phase 3: Installing Oh My Zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    log_info "Cloning Oh My Zsh repository..."
    RUNZSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
else
    log_warn "Oh My Zsh already installed at $HOME/.oh-my-zsh"
fi

# ============================================================================
# Phase 4: Install custom plugins
# ============================================================================
log_info "Phase 4: Installing zsh plugins..."
ZSH_CUSTOM=${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}
mkdir -p "$ZSH_CUSTOM/plugins"

# Install zsh-autosuggestions
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    log_info "Installing zsh-autosuggestions..."
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
else
    log_warn "zsh-autosuggestions already installed"
fi

# Install zsh-syntax-highlighting
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
    log_info "Installing zsh-syntax-highlighting..."
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
else
    log_warn "zsh-syntax-highlighting already installed"
fi

# ============================================================================
# Phase 5: Generate optimized .zshrc with best practices
# ============================================================================
log_info "Phase 5: Generating optimized .zshrc..."
cat > "$HOME/.zshrc" << 'ZSHRC_EOF'
# ============================================================================
# Debian VPS Workstation - Zsh Configuration
# Optimized with best practices from Oh My Zsh, zoxide, eza, bat, and GitHub
# ============================================================================

# PATH TO OH MY ZSH INSTALLATION
export ZSH="$HOME/.oh-my-zsh"

# ============================================================================
# THEME CONFIGURATION
# ============================================================================
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# ============================================================================
# ZSH OPTIONS - Core Settings
# ============================================================================
# Enable command correction
setopt CORRECT
setopt CORRECT_ALL

# History settings
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_SAVE_NO_DUPS
setopt HIST_FIND_NO_DUPS
setopt INC_APPEND_HISTORY

# Expansion and completion
setopt EXTENDED_GLOB
setopt NO_CASE_GLOB

# ============================================================================
# COMPLETION SYSTEM - Initialize Before Plugins
# ============================================================================
# Must be before plugin sourcing for proper completion integration
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qNmh+24) ]]; then
    compinit
else
    compinit -C
fi

# ============================================================================
# OH MY ZSH PLUGINS - Carefully Selected & Ordered
# ============================================================================
# Standard plugins from OMZ
plugins=(
    git                      # Git aliases and functions
    docker                   # Docker completion and aliases
    docker-compose           # Docker Compose support
    sudo                     # sudo plugin (ESC ESC)
    command-not-found        # Suggests package when command not found
    debian                   # Debian/Ubuntu specific aliases
    zsh-autosuggestions      # Fish-like autosuggestions (load BEFORE syntax-highlighting)
)

# Source Oh My Zsh framework
source $ZSH/oh-my-zsh.sh

# ============================================================================
# ZOXIDE INITIALIZATION - Smart Directory Navigation
# ============================================================================
# Initialize AFTER compinit but BEFORE syntax-highlighting
# Provides 'z' and 'zi' commands for frecent directory navigation
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    # Override cd with zoxide
    alias cd="z"
    alias cdi="zi"

    # Uncomment for debugging
    # export _ZO_ECHO=1
fi

# ============================================================================
# EZA CONFIGURATION - Modern ls Replacement
# ============================================================================
if command -v eza &> /dev/null; then
    # Standard ls command (with icons for Nerd Font)
    # Remove --icons if not using Nerd Font to avoid broken characters
    alias ls="eza --icons --group-directories-first"

    # Long format with git integration
    alias ll="eza -l --icons --git --group-directories-first --time-style=long-iso"

    # All files including hidden
    alias la="eza -la --icons --git --group-directories-first --time-style=long-iso"

    # Tree view
    alias tree="eza --tree --icons --level=3"

    # Grid format (useful for quick scanning)
    alias lx="eza -G --icons --group-directories-first"
else
    # Fallback for systems without eza
    alias ll='ls -alF'
    alias la='ls -A'
    alias l='ls -CF'
fi

# ============================================================================
# BAT CONFIGURATION - Better cat with Syntax Highlighting
# ============================================================================
if command -v bat &> /dev/null; then
    # Replace cat with bat for syntax highlighting
    alias cat="bat --paging=never"

    # Configure man pager to use bat
    export MANPAGER="sh -c 'col -bx | bat -l man -p'"

    # Set bat theme (Dracula is a good default, customize as needed)
    export BAT_THEME="Dracula"

    # Optional: Use bat for git diff
    export GIT_PAGER="bat -p"
fi

# ============================================================================
# ZSH SYNTAX HIGHLIGHTING - MUST BE LAST
# ============================================================================
# CRITICAL: This must be sourced LAST, after all other configurations
# In zsh 5.8+, this uses zle-line-pre-redraw hooks instead of widget wrapping
if [[ -f ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
    source ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

    # Configure highlighting (main=commands, brackets=matching braces, etc)
    ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern cursor)

    # Customize colors if desired
    ZSH_HIGHLIGHT_STYLES[comment]='fg=240'
fi

# ============================================================================
# USER EXPORTS & CUSTOM ENVIRONMENT
# ============================================================================
# Add custom bin directories to PATH if they exist
[[ -d "$HOME/bin" ]] && export PATH="$HOME/bin:$PATH"
[[ -d "$HOME/.local/bin" ]] && export PATH="$HOME/.local/bin:$PATH"

# Set default editor
export EDITOR="nano"

# ============================================================================
# CUSTOM ALIASES
# ============================================================================
# Utility aliases
alias reload='exec zsh'              # Reload zsh configuration
alias zshconfig='nano ~/.zshrc'      # Quick edit zshrc

# Common command shortcuts
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

ZSHRC_EOF

log_info ".zshrc configuration generated successfully"

# ============================================================================
# Phase 6: Verify installation
# ============================================================================
log_info "Phase 6: Verifying installation..."
echo ""
echo "Installation Status:"
command -v zsh &> /dev/null && echo "  ✓ zsh: $(zsh --version | head -1)" || echo "  ✗ zsh: NOT FOUND"
command -v eza &> /dev/null && echo "  ✓ eza: $(eza --version)" || echo "  ✗ eza: NOT FOUND"
command -v bat &> /dev/null && echo "  ✓ bat: $(bat --version)" || echo "  ✗ bat: NOT FOUND"
command -v zoxide &> /dev/null && echo "  ✓ zoxide: $(zoxide --version)" || echo "  ✗ zoxide: NOT FOUND"
[ -d "$HOME/.oh-my-zsh" ] && echo "  ✓ Oh My Zsh: installed" || echo "  ✗ Oh My Zsh: NOT FOUND"
[ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ] && echo "  ✓ zsh-autosuggestions: installed" || echo "  ✗ zsh-autosuggestions: NOT FOUND"
[ -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ] && echo "  ✓ zsh-syntax-highlighting: installed" || echo "  ✗ zsh-syntax-highlighting: NOT FOUND"
echo ""

log_info "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start a new terminal session or run: zsh"
echo "  2. Verify: echo \$ZSH_THEME"
echo "  3. Test eza: ls -la"
echo "  4. Test bat: cat ~/.zshrc"
echo "  5. Test zoxide: z --list"
echo ""
echo "Configuration file: $HOME/.zshrc"
echo "Edit with: nano $HOME/.zshrc"
