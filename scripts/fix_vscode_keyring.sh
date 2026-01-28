#!/bin/bash
set -e

# ANSI Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Install Dependencies
log "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y gnome-keyring libsecret-1-0 libsecret-tools dbus-x11 jq

# 2. Configure argv.json
log "Configuring VS Code argv.json..."
VSCODE_DIR="${HOME}/.vscode"
ARGV_FILE="${VSCODE_DIR}/argv.json"

mkdir -p "$VSCODE_DIR"

if [ -f "$ARGV_FILE" ]; then
    # Create temp file to handle comments in json
    TMP_JSON=$(mktemp)
    grep -v "^//" "$ARGV_FILE" > "$TMP_JSON"

    if jq -e . "$TMP_JSON" >/dev/null 2>&1; then
        jq '."password-store"="gnome-libsecret"' "$TMP_JSON" > "${TMP_JSON}.new"
        mv "${TMP_JSON}.new" "$ARGV_FILE"
        log "Updated password-store in argv.json"
    else
        warn "argv.json exists but contains invalid JSON (or comments jq can't handle). Appending manually if needed."
        # Fallback simplistic check
        if ! grep -q "password-store" "$ARGV_FILE"; then
             # This is risky with JSON structure, but safer to assume broken JSON needs manual fix
             warn "Could not robustly edit argv.json. Please check it manually."
        fi
    fi
    rm -f "$TMP_JSON"
else
    echo '{
    "password-store": "gnome-libsecret"
}' > "$ARGV_FILE"
    log "Created argv.json"
fi

# 3. Enable Systemd Service
log "Enabling gnome-keyring-daemon systemd user service..."
systemctl --user unmask gnome-keyring-daemon.service || true
systemctl --user enable --now gnome-keyring-daemon.service

# 4. Verify DBus
log "Verifying DBus session..."
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    warn "DBUS_SESSION_BUS_ADDRESS is not set."
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
    echo "Exported DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
fi

# 5. Check Keyring
log "Checking keyring accessibility..."
if echo "test" | secret-tool store --label="Test Check" test check 2>/dev/null; then
    log "✓ Keyring is writable."
    secret-tool clear attribute.label "Test Check"
else
    error "✗ Keyring is NOT writable. It might be locked or the daemon is not responding."
    warn "Try running: 'gnome-keyring-daemon --replace --daemonize --components=pkcs11,secrets,ssh'"
fi

log "✓ Fix script completed. Please fully RESTART VS Code (Code > Quit or Kill User Server)."
