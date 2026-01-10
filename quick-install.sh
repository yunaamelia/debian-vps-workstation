#!/bin/bash

#####################################################################
# Debian VPS Configurator - Quick Install Script
#
# Purpose: Install all prerequisites and dependencies required to run
#          vps-configurator install --profile advanced
#
# Features:
# - Checkpoint system for error recovery
# - Automatic rollback on failure
# - Resume from last successful checkpoint
#
# Usage: ./quick-install.sh
#####################################################################

set -e  # Exit on error

# Checkpoint tracking
CHECKPOINT_DIR=".install_checkpoints"
BACKUP_DIR=".install_backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_msg "$BLUE" "  $1"
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
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

# Checkpoint management functions
create_checkpoint() {
    local checkpoint_name=$1
    mkdir -p "$CHECKPOINT_DIR"
    touch "$CHECKPOINT_DIR/$checkpoint_name"
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
        rm -rf "$CHECKPOINT_DIR"
        print_info "All checkpoints cleared"
    fi
}

# Backup and restore functions
backup_state() {
    local backup_name=$1
    mkdir -p "$BACKUP_DIR"

    if [ -d "venv" ]; then
        print_info "Backing up virtual environment..."
        tar -czf "$BACKUP_DIR/venv_$backup_name.tar.gz" venv 2>/dev/null || true
    fi

    print_success "State backed up: $backup_name"
}

restore_state() {
    local backup_name=$1

    print_warning "Restoring from backup: $backup_name"

    if [ -f "$BACKUP_DIR/venv_$backup_name.tar.gz" ]; then
        print_info "Restoring virtual environment..."
        rm -rf venv 2>/dev/null || true
        tar -xzf "$BACKUP_DIR/venv_$backup_name.tar.gz" 2>/dev/null || true
        print_success "Virtual environment restored"
    fi
}

# Error handler
error_handler() {
    local exit_code=$?
    local line_number=$1

    print_error "Installation failed at line $line_number with exit code $exit_code"

    print_header "Error Recovery Options"

    list_checkpoints

    echo ""
    print_warning "What would you like to do?"
    echo "1) Retry from last checkpoint"
    echo "2) Start fresh (clean install)"
    echo "3) Exit and investigate manually"

    read -p "Choose an option (1-3): " -n 1 -r
    echo

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
            exit $exit_code
            ;;
        *)
            print_error "Invalid option. Exiting."
            exit $exit_code
            ;;
    esac
}

restore_from_checkpoint() {
    if [ -d "$CHECKPOINT_DIR" ] && [ "$(ls -A $CHECKPOINT_DIR 2>/dev/null)" ]; then
        local last_checkpoint=$(ls -t "$CHECKPOINT_DIR" | head -n1)
        print_info "Last successful checkpoint: $last_checkpoint"

        # Determine where to resume
        if check_checkpoint "python_deps_installed"; then
            print_info "Resuming from verification..."
            verify_installation
            show_next_steps
        elif check_checkpoint "venv_created"; then
            print_info "Resuming from Python dependencies installation..."
            install_python_deps
            verify_installation
            show_next_steps
        elif check_checkpoint "system_deps_installed"; then
            print_info "Resuming from virtual environment setup..."
            setup_venv
            install_python_deps
            verify_installation
            show_next_steps
        else
            print_info "No valid checkpoint found. Starting from system dependencies..."
            install_system_deps
            setup_venv
            install_python_deps
            verify_installation
            show_next_steps
        fi
    else
        print_error "No checkpoints found. Please start fresh."
        exit 1
    fi
}

cleanup_all() {
    print_info "Cleaning up installation artifacts..."
    rm -rf "$CHECKPOINT_DIR" "$BACKUP_DIR" venv 2>/dev/null || true
    print_success "Cleanup complete"
}

# Trap errors
trap 'error_handler $LINENO' ERR

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root!"
        print_info "Run as normal user: ./quick-install.sh"
        exit 1
    fi
}

# Check OS compatibility
check_os() {
    print_header "Checking OS Compatibility"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_info "Detected OS: $NAME $VERSION"

        case "$ID" in
            debian|ubuntu)
                print_success "OS is compatible"
                ;;
            *)
                print_warning "OS not officially supported but may work"
                print_info "Officially supported: Debian 11+, Ubuntu 20.04+"
                read -p "Continue anyway? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
                ;;
        esac
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

# Check Python version
check_python() {
    print_header "Checking Python Installation"

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python version: $PYTHON_VERSION"

        # Check if version >= 3.9
        MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
            print_success "Python 3.9+ is installed"
        else
            print_error "Python 3.9+ is required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    if check_checkpoint "system_deps_installed"; then
        print_info "System dependencies already installed (checkpoint found)"
        return 0
    fi

    print_header "Installing System Dependencies"

    backup_state "before_system_deps"

    print_info "Updating package list..."
    sudo apt-get update -qq

    print_info "Installing required packages..."
    sudo apt-get install -y -qq \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        git \
        curl \
        wget \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    print_success "System dependencies installed"
    create_checkpoint "system_deps_installed"
}

# Setup virtual environment
setup_venv() {
    if check_checkpoint "venv_created"; then
        print_info "Virtual environment already created (checkpoint found)"
        return 0
    fi

    print_header "Setting Up Virtual Environment"

    backup_state "before_venv"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Recreate it? (y/N) " -n 1 -r
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
    python3 -m venv venv

    print_success "Virtual environment created"
    create_checkpoint "venv_created"
}

# Install Python dependencies
install_python_deps() {
    if check_checkpoint "python_deps_installed"; then
        print_info "Python dependencies already installed (checkpoint found)"
        return 0
    fi

    print_header "Installing Python Dependencies"

    backup_state "before_python_deps"

    print_info "Activating virtual environment..."
    source venv/bin/activate

    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel -q

    print_info "Installing project dependencies..."
    pip install -r requirements.txt -q

    print_info "Installing project in development mode..."
    pip install -e . -q

    print_success "Python dependencies installed"
    create_checkpoint "python_deps_installed"
}

# Verify installation
verify_installation() {
    if check_checkpoint "installation_verified"; then
        print_info "Installation already verified (checkpoint found)"
        return 0
    fi

    print_header "Verifying Installation"

    source venv/bin/activate

    if command -v vps-configurator &> /dev/null; then
        VERSION=$(vps-configurator --version 2>&1 | head -n1)
        print_success "vps-configurator is installed: $VERSION"
    else
        print_error "vps-configurator command not found"
        return 1
    fi

    # Test basic functionality
    print_info "Testing basic functionality..."
    if vps-configurator --help &> /dev/null; then
        print_success "Basic functionality test passed"
    else
        print_error "Basic functionality test failed"
        return 1
    fi

    create_checkpoint "installation_verified"
}

# Display next steps
show_next_steps() {
    print_header "Installation Complete! 🎉"

    cat << EOF
$(print_success "All prerequisites have been installed successfully!")

$(print_info "Checkpoint Summary:")
$(list_checkpoints)

$(print_info "Next Steps:")

1. Activate the virtual environment:
   $(print_msg "$YELLOW" "source venv/bin/activate")

2. Run the advanced installation:
   $(print_msg "$YELLOW" "vps-configurator install --profile advanced -v")

3. Or explore available commands:
   $(print_msg "$YELLOW" "vps-configurator --help")

$(print_info "What the advanced profile includes:")
   ✓ System security hardening (UFW, Fail2ban, SSH)
   ✓ Development tools (Python, Node, Go, Rust, Java, PHP)
   ✓ IDEs and editors (VS Code, Cursor, Neovim)
   ✓ Desktop environment (XRDP + XFCE)
   ✓ Container platform (Docker + Docker Compose)

$(print_info "Estimated installation time: 15-30 minutes")

$(print_info "Documentation:")
   📘 Quick Start: docs/00-project-overview/quick-start-guide.md
   📘 Full Docs: docs/00-project-overview/master-index.md

$(print_info "Cleanup:")
   To remove checkpoints and backups:
   $(print_msg "$YELLOW" "rm -rf $CHECKPOINT_DIR $BACKUP_DIR")

EOF
}

# Main execution
main() {
    clear

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

    # Check if resuming from previous run
    if [ -d "$CHECKPOINT_DIR" ] && [ "$(ls -A $CHECKPOINT_DIR 2>/dev/null)" ]; then
        print_warning "Previous installation checkpoints detected!"
        list_checkpoints
        echo ""
        read -p "Resume from last checkpoint? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            restore_from_checkpoint
            return 0
        else
            print_info "Starting fresh installation..."
            cleanup_all
        fi
    fi

    check_root
    check_os
    check_python
    install_system_deps
    setup_venv
    install_python_deps
    verify_installation
    show_next_steps

    print_info "Installation completed successfully!"
    print_warning "You can now safely remove checkpoints with: rm -rf $CHECKPOINT_DIR $BACKUP_DIR"
}

# Run main function
main
