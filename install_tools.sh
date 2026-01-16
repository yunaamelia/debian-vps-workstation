#!/bin/bash
set -e

# Fix bat alias if needed
if command -v batcat &> /dev/null && ! command -v bat &> /dev/null; then
    echo "Linking batcat to bat..."
    sudo ln -s /usr/bin/batcat /usr/local/bin/bat
fi

# Install eza
if ! command -v eza &> /dev/null; then
    echo "Installing eza..."
    sudo mkdir -p /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
        wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | sudo gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    fi
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de/stable/ /" | sudo tee /etc/apt/sources.list.d/gierens.list
    sudo chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
    sudo apt-get update
    sudo apt-get install -y eza
else
    echo "eza is already installed."
fi

# Verify installations
echo "Verifying installations:"
echo "eza: $(command -v eza)"
echo "bat: $(command -v bat)"
echo "zoxide: $(command -v zoxide)"
