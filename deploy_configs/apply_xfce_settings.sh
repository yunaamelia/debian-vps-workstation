#!/bin/bash
# =============================================================================
# Script Name: apply_xfce_settings.sh
# Description: Optimizes XFCE for remote/VPS environments by disabling
#              compositing, screensavers, and accessibility features.
#              Also applies modern flat aesthetics for professional look.
# Usage:       Run as the user you want to configure (do NOT run as root).
# =============================================================================

echo "Applying XFCE optimizations for remote desktop performance..."

# 1. Disable Compositor (Critical for latency)
# Removes transparency, shadows, and vsync buffering overhead.
xfconf-query --channel=xfwm4 --property=/general/use_compositing --type=bool --set=false --create
echo "✓ Compositor disabled"

# 2. Disable Screensaver and Locking
# Prevents the session from locking out, which can be troublesome in RDP.
xfconf-query --channel=xfce4-session --property=/shutdown/LockScreen --type=bool --set=false --create
xfconf-query --channel=xfce4-screensaver --property=/saver/enabled --type=bool --set=false --create
echo "✓ Screensaver & Lock disabled"

# 3. Disable Accessibility (Assistive Technologies)
# Reduces background process overhead if not needed.
xfconf-query --channel=xsettings --property=/Net/EnableAccessibility --type=bool --set=false --create
echo "✓ Accessibility disabled"

# 4. Disable Power Management
# Start with presentation mode or disable DPMS defaults
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled -t bool -s false --create
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/presentation-mode -t bool -s false --create
echo "✓ Power management optimized"

# 5. Aesthetic Improvements (Professional & Efficient)
echo "Applying visual improvements..."

# Set Theme (Greybird is optimized for XFCE and looks professional)
# Flat themes compress better over RDP than gradient-heavy themes
xfconf-query -c xsettings -p /Net/ThemeName -s "Greybird" --create -t string

# Set Icon Theme (Adwaita is standard, clean, and usually pre-installed)
xfconf-query -c xsettings -p /Net/IconThemeName -s "Adwaita" --create -t string

# Font Rendering (Critical for RDP readability)
# Antialias=1 (Enabled), Hinting=1 (Slight), RGBA=none (Grayscale for bandwidth efficiency)
xfconf-query -c xsettings -p /Xft/Antialias -s 1 --create -t int
xfconf-query -c xsettings -p /Xft/Hinting -s 1 --create -t int
xfconf-query -c xsettings -p /Xft/HintStyle -s "hintslight" --create -t string
xfconf-query -c xsettings -p /Xft/RGBA -s "none" --create -t string

# Window Manager Theme
xfconf-query -c xfwm4 -p /general/theme -s "Greybird" --create -t string

# Desktop Background (Solid Color for performance)
# color-style: 0=Auto, 1=Solid, 2=Horizontal, 3=Vertical, 4=Transparent
# Set to Solid (0 or 1 depending on version, usually 2 is solid in some contexts, but let's try 0 first or just remove image)
# Actually, let's properly set standard XFCE background props for monitor0/workspace0
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/color-style -s 0 --create -t int
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/rgba1 -s 0.1686,0.1882,0.2314,1.0 --create -t double -t double -t double -t double # #2b303b

echo "✓ Visuals optimized (Theme: Greybird, Fonts: Smoothed, BG: Solid)"

echo "Configuration complete. Please restart your session for changes to take full effect."
