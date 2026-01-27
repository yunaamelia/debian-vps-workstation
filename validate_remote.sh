#!/bin/bash
HOST="209.38.91.97"
USER="devtest"
PASS="gg123123@"

echo "[INFO] Waiting for $HOST to come online..."
count=0
while ! ping -c 1 -W 1 $HOST &>/dev/null; do
    echo -n "."
    sleep 2
    ((count++))
    if [ $count -gt 30 ]; then echo "[FAIL] Host unreachable"; exit 1; fi
done
echo ""
echo "[INFO] Host is pingable. Waiting for SSH..."
sleep 5

echo "[INFO] Connecting for Validation..."
sshpass -p $PASS ssh -o StrictHostKeyChecking=no $USER@$HOST "
    echo '=== Uptime ==='
    uptime

    echo '=== Service Status ==='
    sudo systemctl is-active docker caddy xrdp wg-quick@wg0

    echo '=== HTTP Check ==='
    curl -I localhost:80 || echo 'Curl failed'

    echo '=== VPS Configurator Verify ==='
    # Using full path if needed or assumed in path (it was installed to venv/bin? linked?)
    # The output said 'Next Steps: Verify installation with: vps-configurator verify'
    # We should try finding it.
    if command -v vps-configurator &>/dev/null; then
        vps-configurator verify
    elif [ -f ~/debian-vps-workstation/venv/bin/vps-configurator ]; then
         sudo ~/debian-vps-workstation/venv/bin/vps-configurator verify
    else
         echo 'Skipping verify: binary not found in path'
    fi
"
