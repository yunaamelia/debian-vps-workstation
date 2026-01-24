import re
import select
import subprocess
import sys
import time

HOST = "134.199.146.186"
USER = "apex"
PASS = "gg123123@"
REMOTE_DIR = "/root/deploy_temp"

PATTERNS = {
    "Error": [r"Error:", r"Exception", r"Traceback", r"Failed", r"fatal:", r"ERROR"],
    "Warning": [r"Warning:", r"Deprecation", r"WARNING", r"warn"],
    "Failure": [r"EXIT_CODE", r"Installation failed", r"Command failed"],
    "Success": [r"Installation completed successfully"],
}

STAGES = [
    (r"Installing System Deps", "Installing System Dependencies"),
    (r"Setting Up Virtual Environment", "Setting up Venv"),
    (r"Installing Python Dependencies", "Installing Python Deps"),
    (r"DEPLOY: Running", "Executing Deployment"),
    (r"Verifying Installation", "Verifying"),
]


def transfer_files():
    print(f">>> [Status] Connecting to {HOST}...")
    subprocess.run(
        [
            "sshpass",
            "-p",
            PASS,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"{USER}@{HOST}",
            f"mkdir -p {REMOTE_DIR}",
        ],
        stderr=subprocess.DEVNULL,
    )

    print(">>> [Status] Transferring files (using tar pipe)...")

    # Construct tar command locally to stream to remote
    tar_cmd = [
        "tar",
        "-c",
        "--exclude=.venv",
        "--exclude=.git",
        "--exclude=__pycache__",
        "--exclude=.mypy_cache",
        "--exclude=.pytest_cache",
        "--exclude=.ruff_cache",
        ".",
    ]

    ssh_cmd = [
        "sshpass",
        "-p",
        PASS,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        f"{USER}@{HOST}",
        f"tar -x -C {REMOTE_DIR}",
    ]

    # We need to pipe tar stdout to ssh stdin
    # Popen usage: tar_proc stdout -> ssh_proc stdin
    try:
        tar_proc = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ssh_proc = subprocess.Popen(
            ssh_cmd, stdin=tar_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Allow tar_proc to receive SIGPIPE if ssh_proc exits
        tar_proc.stdout.close()

        out, err = ssh_proc.communicate()

        if ssh_proc.returncode != 0:
            print(f">>> [Fatal] Transfer failed: {err.decode()}")
            sys.exit(1)
    except Exception as e:
        print(f">>> [Fatal] Transfer exception: {e}")
        sys.exit(1)

    print(">>> [Status] Transfer complete.")


def analyze_line(line, context_buffer):
    # Check for stage updates
    for pattern, name in STAGES:
        if re.search(pattern, line, re.IGNORECASE):
            print(f"\n>>> [Stream Status] {name}\n")

    timestamp = time.strftime("%H:%M:%S")

    # Check for Issues
    # We prioritize Failure > Error > Warning
    found_type = None
    found_regex = None

    for p_type in ["Failure", "Error", "Warning"]:
        if found_type:
            break
        for r in PATTERNS[p_type]:
            if re.search(r, line, re.IGNORECASE):
                found_type = p_type
                found_regex = r
                break

    if found_type:
        print("\n────────────────────────────────────────────────────────────")
        print(f">>> [Incident Report] {timestamp}")
        print(f"  Type: {found_type}")
        print(f"  Diagnosis: Detected keyword '{found_regex}' in output.")
        print("  Context:")
        for c in context_buffer[-5:]:
            print(f"    {c.strip()}")
        print(f"    > {line.strip()}")
        print(
            "  Suggested Fix: Review the specific error above. Check permissions or dependencies."
        )
        print("────────────────────────────────────────────────────────────\n")


def run_script():
    print(">>> [Status] Preparing remote environment...")

    # 1. Clear previous checkpoints to force a fresh run (so new features trigger)
    subprocess.run(
        [
            "sshpass",
            "-p",
            PASS,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"{USER}@{HOST}",
            f"rm -rf {REMOTE_DIR}/.install_checkpoints {REMOTE_DIR}/.install_backup",
        ],
        stderr=subprocess.DEVNULL,
    )

    print(">>> [Status] Starting remote execution (with User Creation)...")

    # 2. Add User/Pass arguments
    # We use 'yes' to auto-accept any prompts (like apt installs if they ask, though -y is used)
    remote_cmd = (
        f"cd {REMOTE_DIR} && "
        f"chmod +x quick-install.sh && "
        f"yes | ./quick-install.sh "
        f"--user developer "
        f"--password 'DevPass123!' "
        f"--sudo-config -1"
    )

    cmd = [
        "sshpass",
        "-p",
        PASS,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        f"{USER}@{HOST}",
        remote_cmd,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    last_output_time = time.time()
    context_buffer = []

    while True:
        # Check for output or timeout
        reads = [process.stdout.fileno()]
        # Use select to poll with timeout
        ret = select.select(reads, [], [], 1.0)

        if reads[0] in ret[0]:
            line = process.stdout.readline()
            if not line:
                break

            # Reset timeout timer
            last_output_time = time.time()

            # Update buffer
            context_buffer.append(line)
            if len(context_buffer) > 10:
                context_buffer.pop(0)

            # Print and analyze
            print(line, end="")
            analyze_line(line, context_buffer)
        else:
            # No data for 1.0 second
            if time.time() - last_output_time > 60:
                print("\n────────────────────────────────────────────────────────────")
                print(">>> [Incident Report] Type: Hang")
                print("  Context: No output received for 60 seconds.")
                print("  Diagnosis: The process appears to be stuck.")
                print("  Suggested Fix: Intervention required. Terminating process.")
                print("────────────────────────────────────────────────────────────\n")
                process.terminate()
                return 1  # Treat as error

        # Check if process finished
        if process.poll() is not None:
            # Drain pipe
            for line in process.stdout:
                print(line, end="")
                analyze_line(line, context_buffer)
            break

    return process.returncode


if __name__ == "__main__":
    try:
        transfer_files()
        code = run_script()
        if code == 0:
            print("\n>>> [Status] SUCCESS: Deployment Completed.")
        else:
            print(f"\n>>> [Status] FAILURE: Deployment exited with code {code}.")
    except KeyboardInterrupt:
        print("\n>>> [Status] Aborted by user.")
