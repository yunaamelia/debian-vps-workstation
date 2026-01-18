#!/bin/bash
# Bootstrap script for Debian VPS Workstation Configurator
# This script installs prerequisites and runs the configurator

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🚀 Debian VPS Workstation Configurator               ║"
echo "║   Bootstrap Script                                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root${NC}"
    echo "Usage: sudo bash bootstrap.sh"
    exit 1
fi

# Check Debian version
echo -e "${CYAN}Checking system requirements...${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "debian" ]; then
        echo -e "${RED}Error: This script is designed for Debian only${NC}"
        echo "Detected: $PRETTY_NAME"
        exit 1
    fi

    if [ "$VERSION_ID" != "13" ]; then
        echo -e "${YELLOW}Warning: This script is designed for Debian 13 (Trixie)${NC}"
        echo "Detected: $PRETTY_NAME"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${RED}Error: Cannot determine OS version${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Debian detected: $PRETTY_NAME${NC}"

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "aarch64" ]; then
    echo -e "${RED}Error: Unsupported architecture: $ARCH${NC}"
    echo "Supported: x86_64, aarch64"
    exit 1
fi
echo -e "${GREEN}✓ Architecture: $ARCH${NC}"

# Check internet connectivity
echo -e "${CYAN}Checking internet connectivity...${NC}"
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${RED}Error: No internet connection${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Internet connected${NC}"

# Install Python if needed
echo -e "${CYAN}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# Check if we're in the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR/.."

if [ -f "$PROJECT_DIR/requirements.txt" ] && [ -d "$PROJECT_DIR/configurator" ]; then
    echo -e "${GREEN}✓ Found configurator in parent directory${NC}"
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}Configurator not found locally, downloading...${NC}"

    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Try to clone from git
    if command -v git &> /dev/null; then
        echo "Cloning repository..."
        git clone https://github.com/yunaamelia/debian-vps-workstation.git
        cd debian-vps-configurator
    else
        echo "Installing git..."
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y git
        git clone https://github.com/yunaamelia/debian-vps-workstation.git
        cd debian-vps-configurator
    fi
fi

# Install Python dependencies
echo -e "${CYAN}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Install the package
echo -e "${CYAN}Installing configurator...${NC}"
pip3 install -e .

echo
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Bootstrap complete!                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo

# Run the configurator
echo -e "${CYAN}Starting configurator...${NC}"
echo

# If arguments are provided, pass them through. Otherwise, run the wizard.
# Using 'install' with -y allows for non-interactive execution if passed.
if [ $# -eq 0 ]; then
    python3 -m configurator wizard
else
    python3 -m configurator "$@"
fi
