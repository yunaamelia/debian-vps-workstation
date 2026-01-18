#!/usr/bin/env python3
"""
Deployment Orchestrator with Circuit Breaker Monitoring

This script orchestrates the deployment of debian-vps-workstation to a remote server
following the strict execution protocol defined in tools/prompt.md.

Features:
- Automatic codebase transfer to remote server
- Real-time monitoring through circuit breaker
- Automatic issue detection and rollback
- Iterative fix-and-retry workflow
"""

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import paramiko

# Configuration from environment variables
REMOTE_HOST = os.environ.get("REMOTE_HOST", "")
REMOTE_USER = os.environ.get("REMOTE_USER", "root")
REMOTE_PASSWORD = os.environ.get("REMOTE_PASSWORD", "")
REMOTE_REPO_DIR = "/root/debian-vps-workstation"

if not REMOTE_HOST:
    print("ERROR: REMOTE_HOST environment variable not set")
    sys.exit(1)
if not REMOTE_PASSWORD:
    print("ERROR: REMOTE_PASSWORD environment variable not set")
    sys.exit(1)
INSTALL_CMD = "cd {repo_dir} && .venv/bin/python3 -m configurator --verbose install --profile advanced --no-parallel"


# Colors for output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(msg):
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")


def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")


def create_ssh_client(hostname, username, password):
    """Create and connect SSH client"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print_info(f"Connecting to {username}@{hostname}...")
        client.connect(hostname, username=username, password=password, timeout=30)
        print_success("SSH connection established")
        return client
    except Exception as e:
        print_error(f"SSH connection failed: {e}")
        sys.exit(1)


def run_remote_command(client, command, sudo=False, password=None, stream_output=False):
    """Execute command on remote server"""
    if sudo and password:
        command = f"echo '{password}' | sudo -S bash -c {repr(command)}"

    if stream_output:
        # For streaming output, use exec_command with get_pty
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        for line in iter(stdout.readline, ""):
            print(line, end="")
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0
    else:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(output)
        if error:
            print_warning(f"stderr: {error}")

        return exit_status == 0


def transfer_file_sftp(client, local_path, remote_path):
    """Transfer file using SFTP"""
    sftp = client.open_sftp()
    try:
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.mkdir(remote_dir)
        except Exception:
            pass  # Directory might already exist

        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print_error(f"SFTP transfer failed: {e}")
        if "sftp" in locals():
            sftp.close()
        return False


def transfer_directory_rsync(local_dir, remote_host, remote_user, remote_password, remote_dir):
    """Transfer directory using rsync (more efficient for large directories)"""
    print_info(f"Transferring {local_dir} to {remote_user}@{remote_host}:{remote_dir}...")

    # Check if rsync is available on remote server first
    check_cmd = f"sshpass -p {remote_password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {remote_user}@{remote_host} 'which rsync'"
    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not result.stdout.strip():
            print_warning("rsync not available on remote server, using package method")
            return False
    except Exception:
        print_warning("Could not verify rsync on remote, using package method")
        return False

    # Use rsync with sshpass for password authentication
    rsync_cmd = [
        "rsync",
        "-avz",
        "--progress",
        "--exclude",
        ".git",
        "--exclude",
        "venv",
        "--exclude",
        ".venv",
        "--exclude",
        "deploy_venv",
        "--exclude",
        "__pycache__",
        "--exclude",
        "*.pyc",
        "--exclude",
        ".pytest_cache",
        "--exclude",
        "deploy_package*",
        "--exclude",
        "*.tar.gz",
        "--exclude",
        "*.zip",
        "-e",
        f"sshpass -p {remote_password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
        f"{local_dir}/",
        f"{remote_user}@{remote_host}:{remote_dir}/",
    ]

    try:
        result = subprocess.run(rsync_cmd, check=True, capture_output=True, text=True)
        print_success("Directory transfer completed")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"rsync failed: {e.stderr if e.stderr else 'unknown error'}")
        return False
    except FileNotFoundError:
        print_warning("rsync not found locally, falling back to package method...")
        return False


def prepare_deployment_package():
    """Create a deployment package (tar.gz) of the codebase"""
    print_info("Creating deployment package...")

    project_root = Path(__file__).parent.parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"deploy_package_{timestamp}.tar.gz"
    temp_dir = tempfile.mkdtemp()
    package_path = os.path.join(temp_dir, package_name)

    try:
        # Create tar.gz excluding unnecessary files
        exclude_patterns = [
            "--exclude",
            ".git",
            "--exclude",
            "venv",
            "--exclude",
            ".venv",
            "--exclude",
            "deploy_venv",
            "--exclude",
            "__pycache__",
            "--exclude",
            "*.pyc",
            "--exclude",
            ".pytest_cache",
            "--exclude",
            "deploy_package*",
            "--exclude",
            "*.tar.gz",
            "--exclude",
            "*.zip",
            "--exclude",
            ".install_checkpoints",
            "--exclude",
            ".install_backup",
        ]

        tar_cmd = ["tar", "-czf", package_path] + exclude_patterns + ["."]

        subprocess.run(tar_cmd, cwd=project_root, check=True)
        print_success(f"Deployment package created: {package_path}")
        return package_path
    except Exception as e:
        print_error(f"Failed to create deployment package: {e}")
        return None


def deploy_codebase(client):
    """Deploy codebase to remote server"""
    print_header("Phase 2: Deploy Circuit Breaker & Codebase")

    project_root = Path(__file__).parent.parent

    # Method 1: Try rsync (most efficient)
    if shutil.which("rsync") and shutil.which("sshpass"):
        print_info("Using rsync for efficient transfer...")
        if transfer_directory_rsync(
            str(project_root), REMOTE_HOST, REMOTE_USER, REMOTE_PASSWORD, REMOTE_REPO_DIR
        ):
            return True

    # Method 2: Create package and transfer
    print_info("Creating deployment package...")
    package_path = prepare_deployment_package()
    if not package_path:
        return False

    remote_package = f"/tmp/{os.path.basename(package_path)}"

    print_info("Transferring package to remote server...")
    if not transfer_file_sftp(client, package_path, remote_package):
        return False

    print_info("Extracting package on remote server...")
    # Remove existing directory to avoid symlink conflicts
    extract_cmd = f"""
        rm -rf {REMOTE_REPO_DIR} && \
        mkdir -p {REMOTE_REPO_DIR} && \
        cd {REMOTE_REPO_DIR} && \
        tar -xzf {remote_package} 2>&1 | grep -v 'Cannot create symlink' || true && \
        rm -f {remote_package}
    """
    if not run_remote_command(client, extract_cmd):
        print_error("Failed to extract package")
        return False

    # Cleanup local package
    os.remove(package_path)
    os.rmdir(os.path.dirname(package_path))

    print_success("Codebase deployed successfully")
    return True


def setup_remote_environment(client):
    """Setup Python environment on remote server"""
    print_header("Phase 3: Setup Remote Environment")

    # Check Python
    print_info("Checking Python installation...")
    if not run_remote_command(client, "python3 --version"):
        print_error("Python 3 not found on remote server")
        return False

    # Create venv
    print_info("Creating virtual environment...")
    venv_cmd = f"cd {REMOTE_REPO_DIR} && python3 -m venv .venv"
    if not run_remote_command(client, venv_cmd):
        print_error("Failed to create virtual environment")
        return False

    # Install dependencies
    print_info("Installing dependencies...")
    install_cmd = f"""
        cd {REMOTE_REPO_DIR} && \
        .venv/bin/pip install --upgrade pip setuptools wheel && \
        .venv/bin/pip install -e .
    """
    if not run_remote_command(client, install_cmd, stream_output=True):
        print_error("Failed to install dependencies")
        return False

    print_success("Remote environment setup complete")
    return True


def execute_with_monitoring(client):
    """Execute installation through circuit breaker monitor"""
    print_header("Phase 4: Execute & Monitor Installation")

    monitor_script = f"{REMOTE_REPO_DIR}/tools/monitor_install_with_checkpoint.py"
    install_command = INSTALL_CMD.format(repo_dir=REMOTE_REPO_DIR)

    # Verify monitor script exists
    print_info("Verifying circuit breaker script...")
    check_cmd = f"test -f {monitor_script} && echo 'exists'"
    stdin, stdout, stderr = client.exec_command(check_cmd)
    if stdout.read().decode().strip() != "exists":
        print_error(f"Monitor script not found: {monitor_script}")
        return False

    # Run through monitor
    print_info("Starting installation with circuit breaker monitoring...")
    print_warning("MONITORING MODE: Will halt on ERROR, WARNING, SKIP, or TIMEOUT")
    print()

    monitor_cmd = f'python3 {monitor_script} "{install_command}"'

    stdin, stdout, stderr = client.exec_command(monitor_cmd, get_pty=True)

    # Stream output in real-time
    exit_code = None
    for line in iter(stdout.readline, ""):
        print(line, end="")
        # Check if process has finished
        if stdout.channel.exit_status_ready():
            exit_code = stdout.channel.recv_exit_status()
            break

    # Get final exit code if not already retrieved
    if exit_code is None:
        exit_code = stdout.channel.recv_exit_status()

    if exit_code == 0:
        print_success("Installation completed successfully!")
        return True
    else:
        print_error(f"Installation failed or was halted (exit code: {exit_code})")
        return False


def get_remote_logs(client):
    """Retrieve monitoring logs from remote server"""
    print_info("Retrieving monitoring logs...")

    log_file = "/tmp/monitor_install.log"
    cmd = f"cat {log_file} 2>/dev/null || echo 'Log file not found'"
    stdin, stdout, stderr = client.exec_command(cmd)
    log_content = stdout.read().decode()

    if log_content and log_content.strip() != "Log file not found":
        print("\n" + "=" * 80)
        print("MONITORING LOG:")
        print("=" * 80)
        print(log_content)
        print("=" * 80 + "\n")
        return log_content
    return None


def main():
    """Main deployment workflow"""
    print_header("DevOps Deployment Orchestrator")
    print_info(f"Target: {REMOTE_USER}@{REMOTE_HOST}")
    print_info(f"Repository: {REMOTE_REPO_DIR}")
    print()

    # Phase 1: Initiate Connection
    print_header("Phase 1: Initiate Connection")
    client = create_ssh_client(REMOTE_HOST, REMOTE_USER, REMOTE_PASSWORD)

    try:
        # Phase 2: Deploy Circuit Breaker & Codebase
        if not deploy_codebase(client):
            print_error("Failed to deploy codebase")
            return 1

        # Phase 3: Setup Remote Environment
        if not setup_remote_environment(client):
            print_error("Failed to setup remote environment")
            return 1

        # Phase 4: Execute & Monitor
        success = execute_with_monitoring(client)

        # Phase 5: Retrieve logs if failed
        if not success:
            get_remote_logs(client)
            print_warning("Review the logs above to identify issues")
            print_info("Checkpoint location: /tmp/vps-checkpoint-*")
            return 1

        print_success("Deployment completed successfully!")
        return 0

    except KeyboardInterrupt:
        print_warning("\nDeployment interrupted by user")
        return 1
    except Exception as e:
        print_error(f"Deployment failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
