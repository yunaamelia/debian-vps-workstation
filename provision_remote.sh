#!/bin/bash
set -e

# Configuration
# Source .env if exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

HOST="${DEPLOY_SERVER_IP:-170.64.138.110}"
ROOT_USER="${DEPLOY_USER:-root}"
ROOT_PASS="${DEPLOY_PASSWORD:-gg123123@}"
TARGET_USER="devtest"
TARGET_PASS="gg123123@"
REMOTE_DIR="/home/${TARGET_USER}/debian-vps-workstation"

# SSH Command Wrappers
SSH_ROOT="sshpass -p ${ROOT_PASS} ssh -o StrictHostKeyChecking=no ${ROOT_USER}@${HOST}"
SSH_TARGET="sshpass -p ${TARGET_PASS} ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${HOST}"

echo "[INFO] Starting Phase 1: Connection & Provisioning"

# 1. Create User & Sudo (Idempotent)
echo "[INFO] Verifying/Creating user '${TARGET_USER}'..."
$SSH_ROOT "
  if ! id ${TARGET_USER} >/dev/null 2>&1; then
      useradd -m -s /bin/bash ${TARGET_USER}
      echo '${TARGET_USER}:${TARGET_PASS}' | chpasswd
      usermod -aG sudo ${TARGET_USER}
      echo '${TARGET_USER} ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/${TARGET_USER}
      chmod 0440 /etc/sudoers.d/${TARGET_USER}
      echo '[INFO] User created.'
  else
      echo '[INFO] User exists.'
  fi
"

# 2. Sync Files
echo "[INFO] Transferring codebase..."
# Ensure remote directory exists
$SSH_ROOT "mkdir -p ${REMOTE_DIR} && chown ${TARGET_USER}:${TARGET_USER} ${REMOTE_DIR}"

# Rsync using sshpass with ssh as rsh
export SSHPASS="${ROOT_PASS}"
rsync -av -e "sshpass -e ssh -o StrictHostKeyChecking=no -l ${ROOT_USER}" \
    --exclude='.venv' \
    --exclude='logs' \
    --exclude='.git' \
    ./ "${HOST}:${REMOTE_DIR}/"

# 3. Permissions
echo "[INFO] Fixing permissions..."
$SSH_ROOT "
  chown -R ${TARGET_USER}:${TARGET_USER} ${REMOTE_DIR}
  chmod +x ${REMOTE_DIR}/quick-install.sh
"

echo "[SUCCESS] Phase 1 Complete. Ready for Phase 2."
