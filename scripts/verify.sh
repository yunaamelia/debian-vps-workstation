#!/bin/bash
# Verification script for Debian VPS Workstation
# Checks that all installed components are working

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🔍 Debian VPS Workstation Verification               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

PASSED=0
FAILED=0
WARNINGS=0

check_service() {
    local service=$1
    local name=$2

    if systemctl is-active --quiet "$service"; then
        echo -e "  ${GREEN}✓${NC} $name is running"
        ((PASSED++))
    else
        echo -e "  ${RED}✗${NC} $name is NOT running"
        ((FAILED++))
    fi
}

check_command() {
    local cmd=$1
    local name=$2

    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n 1)
        echo -e "  ${GREEN}✓${NC} $name: $version"
        ((PASSED++))
    else
        echo -e "  ${RED}✗${NC} $name: NOT FOUND"
        ((FAILED++))
    fi
}

check_port() {
    local port=$1
    local name=$2

    if ss -tlnp | grep -q ":$port "; then
        echo -e "  ${GREEN}✓${NC} $name (port $port) is listening"
        ((PASSED++))
    else
        echo -e "  ${YELLOW}⚠${NC} $name (port $port) is NOT listening"
        ((WARNINGS++))
    fi
}

# Services
echo -e "\n${CYAN}Services:${NC}"
check_service "xrdp" "xRDP Server"
check_service "docker" "Docker"
check_service "fail2ban" "Fail2ban"
check_service "ssh" "SSH"

# Security
echo -e "\n${CYAN}Security:${NC}"
if ufw status | grep -q "Status: active"; then
    echo -e "  ${GREEN}✓${NC} UFW Firewall is active"
    ((PASSED++))
else
    echo -e "  ${RED}✗${NC} UFW Firewall is NOT active"
    ((FAILED++))
fi

# Commands
echo -e "\n${CYAN}Commands:${NC}"
check_command "python3" "Python"
check_command "pip3" "pip"
check_command "docker" "Docker"
check_command "docker-compose" "Docker Compose" || check_command "docker" "Docker Compose (plugin)"
check_command "git" "Git"
check_command "code" "VS Code"

# Node.js (through nvm)
if [ -f "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    if command -v node &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Node.js: $(node --version)"
        ((PASSED++))
    else
        echo -e "  ${YELLOW}⚠${NC} Node.js: Not installed via nvm"
        ((WARNINGS++))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} nvm: Not installed"
    ((WARNINGS++))
fi

# Ports
echo -e "\n${CYAN}Ports:${NC}"
check_port 22 "SSH"
check_port 3389 "RDP"

# Summary
echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "Summary: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}, ${YELLOW}$WARNINGS warnings${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some checks failed. Run 'vps-configurator verify' for details.${NC}"
    exit 1
fi
