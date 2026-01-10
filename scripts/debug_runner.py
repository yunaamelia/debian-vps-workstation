#!/usr/bin/env python3
import os
import re
import subprocess
import sys

REMOTE_HOST = "root@143.198.89.149"
REMOTE_DIR = "/root/vps-configurator"
LOCAL_DIR = os.getcwd()

# SSH Control Master Configuration
SSH_CONTROL_DIR = os.path.expanduser("~/.ssh/ctl")
if not os.path.exists(SSH_CONTROL_DIR):
    os.makedirs(SSH_CONTROL_DIR, exist_ok=True)

SSH_OPTS = [
    "-o",
    "ControlMaster=auto",
    "-o",
    f"ControlPath={SSH_CONTROL_DIR}/%r@%h:%p",
    "-o",
    "ControlPersist=600",
]

# Keywords to trigger immediate failure
FAILURE_PATTERNS = [
    r"ERROR",
    r"WARNING",
    r"WARN",
    r"Exception",
    r"Skipping",
    r"Failed",
    r"Traceback",
]
FAILURE_REGEX = re.compile(f"({'|'.join(FAILURE_PATTERNS)})", re.IGNORECASE)


def run_sync():
    print(f"[*] Syncing {LOCAL_DIR} -> {REMOTE_HOST}:{REMOTE_DIR}")
    rsync_rsh = f"ssh {' '.join(SSH_OPTS)}"
    cmd = [
        "rsync",
        "-az",
        "--delete",
        "-e",
        rsync_rsh,
        "--exclude",
        ".git",
        "--exclude",
        ".venv",
        "--exclude",
        "__pycache__",
        "--exclude",
        "*.pyc",
        "--exclude",
        ".pytest_cache",
        ".",
        f"{REMOTE_HOST}:{REMOTE_DIR}/",
    ]
    subprocess.check_call(cmd)


def setup_remote():
    print("[*] Installing package on remote...")
    cmd = (
        ["ssh"]
        + SSH_OPTS
        + [
            REMOTE_HOST,
            "pip uninstall -y debian-vps-configurator --break-system-packages || true",
        ]
    )
    subprocess.check_call(cmd)

    cmd = (
        ["ssh"]
        + SSH_OPTS
        + [
            REMOTE_HOST,
            f"cd {REMOTE_DIR} && pip install --break-system-packages -e .",
        ]
    )
    subprocess.check_call(cmd)


def run_command_with_logging(command):
    """Execute command on remote with fail-fast logging."""
    print(f"[*] Running: {command}")
    cmd = ["ssh"] + SSH_OPTS + [REMOTE_HOST, command]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in iter(proc.stdout.readline, ""):
        if line:
            print(line, end="")
            if FAILURE_REGEX.search(line):
                print("\n[!] Failure pattern detected, stopping...")
                proc.kill()
                return False

    proc.wait()
    return proc.returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: debug_runner.py <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])

    try:
        run_sync()
        setup_remote()
        success = run_command_with_logging(command)
        if not success:
            print("[!] Command failed or was interrupted")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
