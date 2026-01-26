#!/bin/bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PASS="${REMOTE_PASS:-}"
TARGET_USER="${TARGET_USER:-devtest}"
TARGET_PASS="${TARGET_PASS:-}"
SCRIPT_TO_RUN="${SCRIPT_TO_RUN:-quick-install.sh}"

if [[ -z "$REMOTE_HOST" || -z "$REMOTE_PASS" ]]; then
    echo "Error: Set REMOTE_HOST and REMOTE_PASS"
    exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

echo "Phase 1: Provisioning"
sshpass -p "$REMOTE_PASS" ssh $SSH_OPTS ${REMOTE_USER}@${REMOTE_HOST} "useradd -m $TARGET_USER || true; echo $TARGET_USER:$TARGET_PASS | chpasswd"

echo "Phase 2: Transfer"
sshpass -p "$TARGET_PASS" scp $SSH_OPTS -r . ${TARGET_USER}@${REMOTE_HOST}:~/deployment/

echo "Phase 3: Execute"
sshpass -p "$TARGET_PASS" ssh $SSH_OPTS ${TARGET_USER}@${REMOTE_HOST} "cd ~/deployment && chmod +x $SCRIPT_TO_RUN && ./$SCRIPT_TO_RUN"
