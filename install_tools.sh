#!/bin/bash
set -e

echo "Starting configuration of hardcoded local development environment..."

# 1. Install/Reinstall Core Tools
echo "Installing core packages..."
sudo apt-get update
sudo apt-get install --reinstall -y zsh bat eza zoxide curl git fzf unzip fonts-powerline

# 2. Fix 'bat' alias (Debian installs it as batcat)
if command -v batcat &> /dev/null; then
    if [ ! -f /usr/local/bin/bat ]; then
        echo "Linking batcat to bat..."
        sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
    fi
fi

# 3. Hardcode Oh My Zsh Installation
OMZ_DIR="/home/apexdev/.oh-my-zsh"
if [ ! -d "$OMZ_DIR" ]; then
    echo "Installing Oh My Zsh..."
    # Install unattended
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
    echo "Oh My Zsh already installed."
fi

# 4. Install Best Practice Plugins
ZSH_CUSTOM="$OMZ_DIR/custom"
mkdir -p "$ZSH_CUSTOM/plugins"

echo "Installing Zsh plugins..."
# zsh-autosuggestions
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
else
    git -C "$ZSH_CUSTOM/plugins/zsh-autosuggestions" pull
fi

# zsh-syntax-highlighting
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
else
    git -C "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" pull
fi

# 5. Hardcode .zshrc Configuration
echo "Applying hardcoded .zshrc best practices..."
cat > "/home/apexdev/.zshrc" << 'EOF'
# HARDCODED CONFIGURATION - DO NOT EDIT MANUALLY IF MANAGED BY INSTALL_TOOLS.SH
export ZSH="/home/apexdev/.oh-my-zsh"

# Theme: RobbyRussell is classic and minimal, perfect for performance
ZSH_THEME="robbyrussell"

# Plugins configuration
plugins=(
    git
    docker
    docker-compose
    sudo
    command-not-found
    debian
    zoxide
    zsh-autosuggestions
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# --- Tool Integrations & Best Practices ---

# Zoxide (Smart directory jumper)
# Replaces cd with z. 'z' jumps around, 'zi' allows interactive selection.
# Check if zoxide is installed
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    alias cd="z"
fi

# Eza (Modern ls replacement)
# Best practice aliases for different view modes
if command -v eza &> /dev/null; then
    # --icons removed to ensure compatibility if Nerd Fonts aren't installed on client
    # Add --icons back if you are sure your terminal font supports it
    alias ls="eza --group-directories-first"
    alias ll="eza -l --git --group-directories-first --time-style=long-iso"
    alias la="eza -la --git --group-directories-first --time-style=long-iso"
    alias lT="eza --tree --level=2 --group-directories-first"
else
    # Fallback standard aliases
    alias ll='ls -alF'
    alias la='ls -A'
    alias l='ls -CF'
fi

# Bat (Modern cat replacement)
if command -v bat &> /dev/null; then
    alias cat="bat"
    # Use bat as MANPAGER for colored man pages
    export MANPAGER="sh -c 'col -bx | bat -l man -p'"
fi

# FZF (Fuzzy Finder) integration
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Recommended User Environment
export EDITOR='nano'
export VISUAL='nano'
export LANG=en_US.UTF-8

EOF

# 6. Set Zsh as Default Shell
CURRENT_SHELL=$(basename "$SHELL")
if [ "$CURRENT_SHELL" != "zsh" ]; then
    echo "Setting Zsh as default shell for user $(whoami)..."
    ZSH_PATH=$(which zsh)
    sudo chsh -s "$ZSH_PATH" "$(whoami)"
    echo "Default shell changed to $ZSH_PATH. Please log out and log back in for changes to take full effect."
else
    echo "Zsh is already the default shell."
fi

echo "Hardcoded configuration completed successfully."
echo "Summary:"
echo "- Reinstalled: zsh, bat, eza, zoxide"
echo "- Configured: Oh My Zsh + Plugins (autosuggestions, syntax-highlighting)"
echo "- Applied: .zshrc best practices"
echo "- Default Shell: zsh"
