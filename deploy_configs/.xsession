#!/bin/bash

# Apply One-Time XFCE Settings (idempotent via xfconf-query)
if [ -f "$HOME/deploy_configs/apply_xfce_settings.sh" ]; then
    bash "$HOME/deploy_configs/apply_xfce_settings.sh"
fi
# === Environment Setup ===
export NO_AT_BRIDGE=1           # Disable accessibility
export GNOME_KEYRING_CONTROL="" # Disable keyring
export GTK_MODULES=""           # Disable GTK modules

# === Session Variables ===
export XDG_SESSION_DESKTOP=xfce
export XDG_CURRENT_DESKTOP=XFCE
export DESKTOP_SESSION=xfce

# === Cursor Fix (Critical for RDP) ===
export XCURSOR_THEME=Adwaita
export XCURSOR_SIZE=24

# === Performance: Disable Screen Blanking ===
xset s off
xset -dpms
xset s noblank

# === Cursor Rendering Fix ===
xsetroot -cursor_name left_ptr

# === Start XFCE ===
exec startxfce4
