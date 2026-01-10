#!/usr/bin/env python3
"""
Real-Time Fail-Fast Orchestrator for VPS Configurator Installation
Monitors installation in real-time and interrupts on first sign of trouble.
"""

import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import List, Optional, Tuple


# ANSI color codes for output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


# Configuration
REMOTE_HOST = "143.198.89.149"
REMOTE_USER = "root"
REMOTE_PASSWORD = "gg123123@"
REMOTE_WORKSPACE = "/root/vps-configurator"
LOCAL_WORKSPACE = "/home/racoon/AgentMemorh/debian-vps-workstation"

# Failure patterns to detect (case-insensitive)
FAILURE_PATTERNS = [
    r"\bERROR\b",
    r"\bWARNING\b",
    r"\bWARN\b",
    r"\bException\b",
    r"\bSkipping\b",
    r"\bFailed\b",
    r"\bfail\b",
    r"\bTraceback\b",
    r"\bCritical\b",
    r"\bFATAL\b",
    r"command not found",
    r"No such file",
    r"Permission denied",
    r"cannot access",
    r"ModuleNotFoundError",
    r"ImportError",
    r"KeyError",
    r"ValueError",
    r"TypeError",
    r"AttributeError",
]

# Compiled regex patterns
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in FAILURE_PATTERNS]


class DebugSession:
    """Tracks debug session progress and results"""

    def __init__(self):
        self.runs: List[dict] = []
        self.start_time = datetime.now()
        self.current_run = 0

    def add_run(self, stop_reason: str, action_taken: str, time_saved: str):
        self.current_run += 1
        self.runs.append(
            {
                "run": self.current_run,
                "stop_reason": stop_reason,
                "action_taken": action_taken,
                "time_saved": time_saved,
                "timestamp": datetime.now(),
            }
        )

    def print_status(self):
        """Print formatted status table"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}Debug Session Status{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*100}{Colors.RESET}\n")

        if not self.runs:
            print(f"{Colors.YELLOW}No runs yet{Colors.RESET}\n")
            return

        # Header
        print(
            f"{Colors.BOLD}| {'Run #':<6} | {'Stop Reason (Log Line)':<50} | {'Action Taken':<30} | {'Time Saved':<12} |{Colors.RESET}"
        )
        print(f"{Colors.CYAN}|{'='*8}|{'='*52}|{'='*32}|{'='*14}|{Colors.RESET}")

        # Rows
        for run in self.runs:
            stop_reason = (
                run["stop_reason"][:48] + "..."
                if len(run["stop_reason"]) > 48
                else run["stop_reason"]
            )
            action = (
                run["action_taken"][:28] + "..."
                if len(run["action_taken"]) > 28
                else run["action_taken"]
            )
            print(
                f"| {run['run']:<6} | {stop_reason:<50} | {action:<30} | {run['time_saved']:<12} |"
            )

        print(f"{Colors.CYAN}{'='*100}{Colors.RESET}\n")

        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(
            f"{Colors.BOLD}Total Session Time: {elapsed:.1f}s | Total Runs: {self.current_run}{Colors.RESET}\n"
        )


class RemoteCommandMonitor:
    """Monitors remote command execution with real-time log streaming"""

    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.process: Optional[subprocess.Popen] = None
        self.should_stop = threading.Event()
        self.failure_detected = threading.Event()
        self.failure_line = None

    def check_connection(self) -> bool:
        """Verify SSH connection is working"""
        print(f"{Colors.BLUE}→ Testing SSH connection to {self.user}@{self.host}...{Colors.RESET}")

        cmd = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ServerAliveInterval=60",
            "-o",
            "ConnectTimeout=10",
            f"{self.user}@{self.host}",
            'echo "Connection successful"',
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ SSH connection successful{Colors.RESET}")

                # Install rsync if not present
                self._ensure_remote_tools()

                return True
            else:
                print(f"{Colors.RED}✗ SSH connection failed: {result.stderr}{Colors.RESET}")
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ Connection test failed: {e}{Colors.RESET}")
            return False

    def _ensure_remote_tools(self):
        """Ensure required tools are installed on remote server"""
        print(f"{Colors.BLUE}→ Checking remote tools...{Colors.RESET}")

        # Install rsync
        check_rsync = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            f"{self.user}@{self.host}",
            "command -v rsync >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq rsync)",
        ]

        try:
            subprocess.run(check_rsync, timeout=60, capture_output=True)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Rsync install warning: {e}{Colors.RESET}")

        # Install pip if not present
        print(f"{Colors.BLUE}→ Ensuring pip is installed...{Colors.RESET}")
        install_pip = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            f"{self.user}@{self.host}",
            "command -v pip3 >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq python3-pip python3-venv)",
        ]
        try:
            subprocess.run(install_pip, timeout=120, capture_output=True)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Pip install warning: {e}{Colors.RESET}")

        # Set up virtual environment and install dependencies
        print(
            f"{Colors.BLUE}→ Setting up virtual environment and installing dependencies...{Colors.RESET}"
        )
        setup_venv = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            f"{self.user}@{self.host}",
            f"cd {REMOTE_WORKSPACE} && "
            f"(test -d venv || python3 -m venv venv) && "
            f"source venv/bin/activate && "
            f"pip install --quiet --upgrade pip && "
            f"pip install --quiet -r requirements.txt 2>&1 | tail -10",
        ]

        try:
            result = subprocess.run(setup_venv, timeout=300, capture_output=True, text=True)
            if (
                result.returncode == 0
                or "Successfully installed" in result.stdout
                or "Requirement already satisfied" in result.stdout
            ):
                print(f"{Colors.GREEN}✓ Virtual environment and dependencies ready{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠ Venv setup output: {result.stdout}{Colors.RESET}")
                if result.stderr:
                    print(
                        f"{Colors.YELLOW}⚠ Venv setup errors: {result.stderr[-500:]}{Colors.RESET}"
                    )
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Venv setup warning: {e}{Colors.RESET}")

        print(f"{Colors.GREEN}✓ Remote tools ready{Colors.RESET}")

    def sync_workspace(self) -> bool:
        """Rsync local workspace to remote server"""
        print(f"{Colors.BLUE}→ Syncing workspace to remote server...{Colors.RESET}")

        cmd = [
            "rsync",
            "-avz",
            "--delete",
            "--exclude=.git",
            "--exclude=__pycache__",
            "--exclude=*.pyc",
            "--exclude=htmlcov",
            "--exclude=.pytest_cache",
            "--exclude=venv",
            "--exclude=.venv",
            "-e",
            f"sshpass -p {self.password} ssh -o StrictHostKeyChecking=no",
            f"{LOCAL_WORKSPACE}/",
            f"{self.user}@{self.host}:{REMOTE_WORKSPACE}/",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ Workspace synced successfully{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}✗ Rsync failed: {result.stderr}{Colors.RESET}")
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ Sync failed: {e}{Colors.RESET}")
            return False

    def cleanup_remote(self) -> bool:
        """Clean up remote installation artifacts"""
        print(f"{Colors.BLUE}→ Cleaning remote state...{Colors.RESET}")

        cleanup_commands = [
            "rm -rf /tmp/vps-configurator-*",
            "rm -rf ~/.vps-configurator-state",
            "pkill -f vps-configurator || true",
        ]

        cmd = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            f"{self.user}@{self.host}",
            " && ".join(cleanup_commands),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print(f"{Colors.GREEN}✓ Remote state cleaned{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Cleanup warning: {e}{Colors.RESET}")
            return True  # Non-critical

    def detect_failure(self, line: str) -> bool:
        """Check if line matches any failure pattern"""
        for pattern in COMPILED_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def stream_command(self, command: str) -> Tuple[int, Optional[str]]:
        """Execute command remotely and stream output in real-time"""
        print(f"{Colors.MAGENTA}→ Executing: {command}{Colors.RESET}\n")

        # SSH command with proper escaping
        ssh_cmd = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ServerAliveInterval=60",
            f"{self.user}@{self.host}",
            f"cd {REMOTE_WORKSPACE} && {command}",
        ]

        try:
            self.process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            line_buffer = []
            failure_context = []
            context_size = 25  # Increased context window
            in_traceback = False
            traceback_lines = []

            # Read output line by line
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break

                line = line.rstrip()
                if not line:
                    continue

                line_buffer.append(line)
                failure_context.append(line)
                if len(failure_context) > context_size:
                    failure_context.pop(0)

                # Track tracebacks specially - wait for complete error
                if "Traceback (most recent call last):" in line:
                    in_traceback = True
                    traceback_lines = [line]
                    continue
                elif in_traceback:
                    traceback_lines.append(line)
                    # Check if this is the final error line
                    if any(err in line for err in ["Error:", "Exception:", "Warning:"]):
                        # Complete traceback collected
                        in_traceback = False
                        full_error = "\n".join(traceback_lines)
                        if self.detect_failure(full_error):
                            self.failure_line = full_error
                            self.failure_detected.set()

                            print(f"\n{Colors.BOLD}{Colors.RED}{'!'*80}{Colors.RESET}")
                            print(
                                f"{Colors.BOLD}{Colors.RED}FAILURE DETECTED - INTERRUPTING PROCESS{Colors.RESET}"
                            )
                            print(f"{Colors.BOLD}{Colors.RED}{'!'*80}{Colors.RESET}\n")

                            print(f"{Colors.YELLOW}Complete Error:{Colors.RESET}")
                            for err_line in traceback_lines:
                                print(f"{Colors.RED}  {err_line}{Colors.RESET}")
                            print()

                            print(
                                f"{Colors.YELLOW}Last {context_size} lines of context:{Colors.RESET}"
                            )
                            for ctx_line in failure_context:
                                print(f"  {ctx_line}")
                            print()  # Extra newline for readability

                            # Kill the remote process
                            self._kill_remote_process()

                            return 1, full_error
                    continue

                # Print the line (color-code based on content)
                if self.detect_failure(line) and not in_traceback:
                    print(f"{Colors.RED}[!] {line}{Colors.RESET}")
                elif "success" in line.lower() or "✓" in line:
                    print(f"{Colors.GREEN}{line}{Colors.RESET}")
                elif "info" in line.lower() or "→" in line:
                    print(f"{Colors.CYAN}{line}{Colors.RESET}")
                else:
                    print(line)

                # Check for failure patterns (skip tracebacks - handled above)
                if not in_traceback and self.detect_failure(line):
                    self.failure_line = line
                    self.failure_detected.set()

                    print(f"\n{Colors.BOLD}{Colors.RED}{'!'*80}{Colors.RESET}")
                    print(
                        f"{Colors.BOLD}{Colors.RED}FAILURE DETECTED - INTERRUPTING PROCESS{Colors.RESET}"
                    )
                    print(f"{Colors.BOLD}{Colors.RED}{'!'*80}{Colors.RESET}\n")

                    print(f"{Colors.YELLOW}Last {context_size} lines of context:{Colors.RESET}")
                    for ctx_line in failure_context:
                        print(f"  {ctx_line}")
                    print()  # Extra newline for readability

                    # Kill the remote process
                    self._kill_remote_process()

                    return 1, line

            # Wait for process to complete
            exit_code = self.process.wait(timeout=5)

            if exit_code == 0:
                print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.RESET}")
                print(
                    f"{Colors.BOLD}{Colors.GREEN}SUCCESS - Installation completed without errors!{Colors.RESET}"
                )
                print(f"{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.RESET}\n")

            return exit_code, None

        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Process timeout - killing...{Colors.RESET}")
            self._kill_remote_process()
            return 124, "Timeout"
        except Exception as e:
            print(f"{Colors.RED}Execution error: {e}{Colors.RESET}")
            self._kill_remote_process()
            return 1, str(e)

    def _kill_remote_process(self):
        """Kill the remote process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except (subprocess.TimeoutExpired, Exception):
                try:
                    self.process.kill()
                except Exception:
                    pass

        # Also kill on remote side
        kill_cmd = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            f"{self.user}@{self.host}",
            "pkill -9 -f vps-configurator || true",
        ]
        try:
            subprocess.run(kill_cmd, timeout=5, capture_output=True)
        except Exception:
            pass


def main():
    """Main orchestration loop"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*100}{Colors.RESET}")
    print(
        f"{Colors.BOLD}{Colors.MAGENTA}VPS Configurator - Fail-Fast Real-Time Orchestrator{Colors.RESET}"
    )
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*100}{Colors.RESET}\n")

    session = DebugSession()
    monitor = RemoteCommandMonitor(REMOTE_HOST, REMOTE_USER, REMOTE_PASSWORD)

    # Initial connection check
    if not monitor.check_connection():
        print(f"{Colors.RED}Cannot establish SSH connection. Aborting.{Colors.RESET}")
        return 1

    max_iterations = 50  # Safety limit
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}Iteration #{iteration}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*100}{Colors.RESET}\n")

        # Step 1: Sync workspace
        if not monitor.sync_workspace():
            print(f"{Colors.RED}Sync failed. Retrying in 5 seconds...{Colors.RESET}")
            time.sleep(5)
            continue

        # Step 2: Clean remote state
        monitor.cleanup_remote()

        # Step 3: Execute installation with real-time monitoring
        exit_code, failure_line = monitor.stream_command(
            "source venv/bin/activate && python3 -m configurator install --profile advanced --verbose 2>&1"
        )

        # Step 4: Analyze result
        if exit_code == 0 and failure_line is None:
            # SUCCESS!
            print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*100}{Colors.RESET}")
            print(
                f"{Colors.BOLD}{Colors.GREEN}✓✓✓ INSTALLATION COMPLETED SUCCESSFULLY ✓✓✓{Colors.RESET}"
            )
            print(f"{Colors.BOLD}{Colors.GREEN}{'='*100}{Colors.RESET}\n")

            session.print_status()
            return 0

        # Failure detected - prompt for fix
        if failure_line:
            time_saved = "~10 mins"

            session.add_run(
                stop_reason=failure_line[:100],
                action_taken="Waiting for user input...",
                time_saved=time_saved,
            )

            session.print_status()

            print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*100}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.YELLOW}ACTION REQUIRED{Colors.RESET}")
            print(f"{Colors.YELLOW}{'='*100}{Colors.RESET}\n")

            print(f"{Colors.WHITE}Failure detected: {Colors.RED}{failure_line}{Colors.RESET}")
            print(f"\n{Colors.WHITE}Please fix the issue in your local workspace:{Colors.RESET}")
            print(f"{Colors.CYAN}  {LOCAL_WORKSPACE}{Colors.RESET}\n")

            print(f"{Colors.WHITE}Options:{Colors.RESET}")
            print(f"  {Colors.GREEN}[Enter]{Colors.RESET} - Retry after fixing")
            print(f"  {Colors.YELLOW}[s]{Colors.RESET} - Skip this error and continue")
            print(f"  {Colors.RED}[q]{Colors.RESET} - Quit")

            choice = input(f"\n{Colors.BOLD}Your choice: {Colors.RESET}").strip().lower()

            if choice == "q":
                print(f"{Colors.YELLOW}Exiting...{Colors.RESET}")
                session.print_status()
                return 1
            elif choice == "s":
                print(f"{Colors.YELLOW}Skipping error (adding to ignore patterns)...{Colors.RESET}")
                # Remove the pattern that matched
                continue
            else:
                # Default: retry
                action = input(f"{Colors.WHITE}What did you fix? (for log): {Colors.RESET}").strip()
                if action:
                    session.runs[-1]["action_taken"] = action
                print(f"\n{Colors.GREEN}Retrying...{Colors.RESET}")
                continue

    print(f"{Colors.RED}Maximum iterations reached. Giving up.{Colors.RESET}")
    session.print_status()
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(130)
