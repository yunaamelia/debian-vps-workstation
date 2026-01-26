"""Monitor remote deployment and classify streaming logs."""

import argparse
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from typing import List, Optional, Set, Tuple

# Configuration (loaded via CLI or environment)
SSH_OPTS = [
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "UserKnownHostsFile=/dev/null",
    "-o",
    "LogLevel=ERROR",
    "-o",
    "ConnectTimeout=30",
    "-o",
    "ServerAliveInterval=15",
    "-o",
    "ServerAliveCountMax=4",
    "-o",
    "TCPKeepAlive=yes",
]

# Patterns
PATTERNS = {
    "FAIL": re.compile(r"\b(EXIT_CODE != 0|Failed|Abort)\b", re.IGNORECASE),
    "ERROR": re.compile(r"\b(Error:|Exception|Traceback)\b", re.IGNORECASE),
    "WARN": re.compile(r"\b(Warning:|Deprecation)\b", re.IGNORECASE),
}

ALERT_TYPE_MAP = {
    "FAIL": "Error",
    "ERROR": "Error",
    "WARN": "Warning",
    "HANG": "Hang",
}


class LogMonitor:
    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.last_output_time = time.time()
        self.issues = []
        self.stop_event = threading.Event()
        self.process = None
        self.recent_lines = deque(maxlen=10)
        self.issue_signatures: Set[Tuple[str, str]] = set()

    def _stream_reader(self, pipe, stream_name: str) -> None:
        """Read output from a pipe and update status."""
        for line in iter(pipe.readline, ""):
            if self.stop_event.is_set():
                break
            line = line.strip()
            if not line:
                continue

            self.last_output_time = time.time()
            print(f"[{stream_name}] {line}")
            self.recent_lines.append(f"[{stream_name}] {line}")
            self._analyze_line(line)

    def _analyze_line(self, line: str) -> None:
        """Analyze a single line for issues."""
        if self._should_ignore_line(line):
            return
        for issue_type, pattern in PATTERNS.items():
            if pattern.search(line):
                alert_type = ALERT_TYPE_MAP.get(issue_type, "Error")
                signature = (alert_type, line)
                if signature in self.issue_signatures:
                    return
                self.issue_signatures.add(signature)
                self.issues.append(
                    {
                        "type": alert_type,
                        "message": line,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                self._emit_alert(alert_type, line)

    def _watchdog(self) -> None:
        """Monitor for hangs."""
        while not self.stop_event.is_set():
            time.sleep(1)
            elapsed = time.time() - self.last_output_time
            if elapsed > self.timeout:
                msg = f"Hang detected! No output for {elapsed:.1f} seconds."
                signature = ("Hang", msg)
                if signature not in self.issue_signatures:
                    self.issue_signatures.add(signature)
                    self.issues.append(
                        {
                            "type": "Hang",
                            "message": msg,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                self._emit_alert("Hang", msg)
                if self.process:
                    print("Terminating process due to hang...")
                    self.process.terminate()
                self.stop_event.set()

    def _emit_alert(self, alert_type: str, message: str) -> None:
        context_lines = list(self.recent_lines)[-10:]
        diagnosis, suggestion = self._get_alert_metadata(alert_type, message)
        print("\nALERT")
        print(f"Type: {alert_type}")
        print("Context:")
        if context_lines:
            for ctx in context_lines:
                print(f"- {ctx}")
        else:
            print("- (no prior context)")
        print(f"Diagnosis: {diagnosis}")
        print(f"Suggested Fix: {suggestion}")
        print("")

    def run_command(self, cmd_list: List[str], input_str: Optional[str] = None) -> int:
        """Run a command with monitoring."""
        print(f"Starting: {' '.join(cmd_list)}")
        try:
            # Prepare process
            self.process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if input_str else None,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Start threads
            t_out = threading.Thread(
                target=self._stream_reader, args=(self.process.stdout, "STDOUT")
            )
            t_err = threading.Thread(
                target=self._stream_reader, args=(self.process.stderr, "STDERR")
            )
            t_wd = threading.Thread(target=self._watchdog)

            t_out.start()
            t_err.start()
            t_wd.start()

            # Pass input if any
            if input_str and self.process.stdin:
                self.process.stdin.write(input_str)
                self.process.stdin.close()

            # Wait for finish with timeout
            try:
                self.process.wait(timeout=self.timeout * 10)  # Max 10x watchdog timeout
            except subprocess.TimeoutExpired:
                print("Process timeout expired, terminating...")
                self.process.kill()

            self.stop_event.set()

            # Join threads with timeout to prevent hang
            t_out.join(timeout=5)
            t_err.join(timeout=5)
            t_wd.join(timeout=5)

            # Force cleanup if threads still alive
            if t_out.is_alive() or t_err.is_alive() or t_wd.is_alive():
                print("Warning: Some threads did not terminate gracefully")

            return self.process.returncode
        except Exception as e:
            print(f"Execution Error: {e}")
            return -1

    def _should_ignore_line(self, line: str) -> bool:
        """Return True for lines that should not trigger alerts."""
        if line.startswith("INFO") and "Cached:" in line:
            return True
        return False

    def _get_alert_metadata(self, alert_type: str, message: str) -> Tuple[str, str]:
        """Return diagnosis and fix suggestions for an alert."""
        message_lower = message.lower()
        if "running pip as the 'root' user" in message_lower:
            return (
                "Pip executed as root; this can cause permission conflicts.",
                "Use a virtual environment for pip installs or set "
                "PIP_ROOT_USER_ACTION=ignore if intentional.",
            )
        if alert_type == "Hang":
            return (
                "No output within the hang timeout window.",
                "Check remote process state and apt/dpkg locks. The script now has "
                "automatic timeout for lock waiting (5 min) and installer execution. "
                "If this persists, manually kill blocking processes on the remote server.",
            )
        if "lock timeout" in message_lower or "installer timeout" in message_lower:
            return (
                "Operation exceeded maximum allowed time.",
                "Check for stuck processes, network issues, or increase timeout values. "
                "Use 'ps aux' and 'lsof' on remote server to identify blocking processes.",
            )
        if alert_type == "Warning":
            return (
                "Warning detected in stream output.",
                "Review the warning context and adjust installer steps if needed.",
            )
        return (
            "Error indicator detected in stream output.",
            "Inspect the failing command and rerun after correcting the root cause.",
        )


def bundle_project(output_filename: str = "deploy_bundle.tar.gz") -> bool:
    """Create a tarball for remote upload."""
    print("Bundling project files...")
    excludes = [
        "venv",
        ".venv",
        ".git",
        ".vscode",
        "__pycache__",
        "logs",
        "deploy_bundle.tar.gz",
        ".DS_Store",
        "monitor_deploy.py",
    ]
    cmd = ["tar", "--exclude-vcs"]
    for ex in excludes:
        cmd.extend(["--exclude", ex])
    cmd.extend(["-czf", output_filename, "."])

    try:
        subprocess.run(cmd, check=True)
        print(f"Created {output_filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Bundling failed: {e}")
        return False


def upload_file(
    local_path: str,
    remote_path: str,
    user: str,
    server_ip: str,
    password: str,
) -> bool:
    """Upload a file to the remote host."""
    print(f"Uploading {local_path} to {remote_path}...")
    cmd = (
        ["sshpass", "-p", password, "scp"]
        + SSH_OPTS
        + [local_path, f"{user}@{server_ip}:{remote_path}"]
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}")
        return False
    print("Upload successful.")
    return True


def main() -> None:
    """Run remote deployment with streaming log analysis."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run the installer in dry-run mode")
    parser.add_argument(
        "--server-ip", default=os.getenv("DEPLOY_SERVER_IP"), help="Target server IP"
    )
    parser.add_argument("--user", default=os.getenv("DEPLOY_USER", "root"), help="SSH user")
    parser.add_argument(
        "--password",
        default=os.getenv("DEPLOY_PASSWORD"),
        help="SSH password (or set DEPLOY_PASSWORD)",
    )
    parser.add_argument(
        "--local-script", default="quick-install.sh", help="Local installer script name"
    )
    parser.add_argument(
        "--remote-dir", default="/root/vps-configurator", help="Remote project directory"
    )
    parser.add_argument("--timeout", type=int, default=60, help="Hang timeout in seconds")
    args = parser.parse_args()

    if not args.server_ip or not args.password:
        print(
            "Missing required connection details. Provide --server-ip and "
            "--password (or set DEPLOY_SERVER_IP/DEPLOY_PASSWORD)."
        )
        sys.exit(1)

    # 1. Bundle & Upload
    bundle_name = "deploy_bundle.tar.gz"
    local_bundle = f"/tmp/{bundle_name}"
    remote_dir = args.remote_dir

    if not bundle_project(local_bundle):
        sys.exit(1)

    # Create remote dir
    setup_cmd = (
        ["sshpass", "-p", args.password, "ssh"]
        + SSH_OPTS
        + [f"{args.user}@{args.server_ip}", f"rm -rf {remote_dir} && mkdir -p {remote_dir}"]
    )
    subprocess.run(setup_cmd, check=True)

    if not upload_file(
        local_bundle,
        f"/root/{bundle_name}",
        args.user,
        args.server_ip,
        args.password,
    ):
        sys.exit(1)

    # 2. Extract & Execute
    # 2. Extract
    print("Extracting bundle...")
    extract_cmd = (
        ["sshpass", "-p", args.password, "ssh"]
        + SSH_OPTS
        + [f"{args.user}@{args.server_ip}", f"tar -xzf /root/{bundle_name} -C {remote_dir}"]
    )
    if subprocess.run(extract_cmd).returncode != 0:
        print("Extraction failed!")
        sys.exit(2)

    # 3. Execute with Monitoring
    # Chain: chmod -> execute
    install_args = ""
    if args.dry_run:
        install_args = "--dry-run"

    # Add timeout for lock waiting (5 minutes max)
    lock_timeout = 300
    remote_cmd = (
        f"cd {remote_dir} && "
        f"chmod +x {args.local_script} && "
        f"export DEBIAN_FRONTEND=noninteractive && "
        f"export PIP_ROOT_USER_ACTION=ignore && "
        # Wait for locks with timeout
        f"echo 'Waiting for apt locks (max {lock_timeout}s)...' && "
        f"COUNTER=0 && "
        f"while [ $COUNTER -lt {lock_timeout} ] && ("
        f"  fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || "
        f"  fuser /var/lib/dpkg/lock >/dev/null 2>&1 || "
        f"  fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 "
        f"); do "
        f'  echo "Waiting for lock release... ($COUNTER/{lock_timeout}s)"; '
        f"  sleep 5; "
        f"  COUNTER=$((COUNTER + 5)); "
        f"done && "
        f"if [ $COUNTER -ge {lock_timeout} ]; then "
        f"  echo 'ERROR: Lock timeout reached!'; "
        f"  exit 124; "
        f"fi && "
        # Use timeout wrapper for the installer
        f"timeout {args.timeout * 15} bash -c 'yes 2>/dev/null | ./{args.local_script} {install_args}' || "
        f"EXIT_CODE=$? && "
        f'if [ "$EXIT_CODE" = "124" ]; then '
        f"  echo 'ERROR: Installer timeout!'; "
        f"  exit 124; "
        f'elif [ "$EXIT_CODE" != "0" ] && [ "$EXIT_CODE" != "141" ]; then '
        f"  echo 'ERROR: Installer failed with exit code '$EXIT_CODE; "
        f"  exit $EXIT_CODE; "
        f"fi"
    )

    ssh_cmd = (
        ["sshpass", "-p", args.password, "ssh"]
        + SSH_OPTS
        + [f"{args.user}@{args.server_ip}", remote_cmd]
    )

    # 3. Execute & Monitor
    monitor = LogMonitor(timeout=args.timeout)
    ret_code = monitor.run_command(ssh_cmd)

    # Cleanup local bundle
    subprocess.run(["rm", local_bundle])

    # 4. Final Report
    print("\n" + "=" * 40)
    print("FINAL INCIDENT REPORT")
    print("=" * 40)
    if ret_code == 0:
        print("Status: SUCCESS")
    elif ret_code == 124:
        print("Status: TIMEOUT (Exit Code: 124)")
        print("The installer exceeded the maximum execution time.")
    else:
        print(f"Status: FAILURE (Exit Code: {ret_code})")

    if monitor.issues:
        print(f"Detected {len(monitor.issues)} anomalies:")
        for i, issue in enumerate(monitor.issues, 1):
            print(f"{i}. [{issue['type']}] {issue['message']}")
    else:
        print("No anomalies detected.")


if __name__ == "__main__":
    main()
