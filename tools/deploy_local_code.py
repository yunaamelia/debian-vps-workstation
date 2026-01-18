import os
import sys
import zipfile

import paramiko


def create_ssh_client(hostname, username, password, timeout=30):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname} ({username})...")
        print(f"Timeout: {timeout}s")
        client.connect(
            hostname,
            username=username,
            password=password,
            timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        print("✅ Connected!")
        return client
    except paramiko.AuthenticationException:
        print(f"❌ Authentication failed for {username}@{hostname}")
        print("Please verify credentials.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"❌ SSH connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Host: {hostname}")
        print(f"   User: {username}")
        print(f"   Error type: {type(e).__name__}")
        print("\nTroubleshooting:")
        print("  - Verify server is accessible: ping or telnet to port 22")
        print("  - Check firewall rules")
        print("  - Verify SSH service is running on the server")
        sys.exit(1)


def run_command(client, command, sudo=False, password=None, stream_output=True):
    if sudo and password:
        command = f"echo '{password}' | sudo -S -p '' bash -c \"{command}\""

    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)

    output_lines = []
    while True:
        try:
            line = stdout.readline()
            if not line:
                break
            if stream_output:
                print(line, end="", flush=True)
            output_lines.append(line)
        except Exception as e:
            if stream_output:
                print(f"Read error: {e}")
            break

    exit_status = stdout.channel.recv_exit_status()

    # Also read stderr if any
    try:
        stderr_lines = stderr.readlines()
        if stderr_lines and stream_output:
            print("STDERR:", file=sys.stderr)
            for line in stderr_lines:
                print(line, end="", file=sys.stderr, flush=True)
    except Exception:
        pass

    return exit_status == 0


def create_local_zip(filename):
    print("Creating local zip archive...")
    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Exclude directories
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            if ".git" in dirs:
                dirs.remove(".git")
            if ".venv" in dirs:
                dirs.remove(".venv")
            if "cis-reports" in dirs:
                dirs.remove("cis-reports")

            for file in files:
                if file.endswith(".pyc"):
                    continue
                if file == filename:
                    continue

                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file_path)
    print(f"Created {filename}")


def main():
    host = "209.97.162.195"
    user = "root"
    pwd = os.environ.get("REMOTE_PASSWORD", "")
    if not pwd:
        print("ERROR: REMOTE_PASSWORD environment variable not set")
        sys.exit(1)
    zip_name = "deploy_package.zip"
    remote_path = f"/root/{zip_name}"
    repo_dir = "/root/debian-vps-workstation"

    # 1. Zip local files
    create_local_zip(zip_name)

    # Test connectivity first
    print(f"\n--- Testing connectivity to {host} ---")
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, 22))
        sock.close()
        if result == 0:
            print(f"✅ Port 22 is open on {host}")
        else:
            print(f"⚠️  Port 22 may be closed or filtered on {host}")
    except Exception as e:
        print(f"⚠️  Could not test connectivity: {e}")

    client = create_ssh_client(host, user, pwd, timeout=30)

    # 1.5 Install system dependencies
    print("Installing system dependencies (unzip, python3-venv)...")
    run_command(
        client,
        "apt-get update && apt-get install -y unzip python3-venv git python3-pip",
        sudo=True,
        password=pwd,
    )
    sftp = client.open_sftp()

    # 2. Upload zip
    print(f"Uploading {zip_name} to {remote_path}...")
    sftp.put(zip_name, remote_path)
    sftp.close()

    # 3. Unzip on server
    print("Extracting files on server...")
    # Ensure dir exists (it should, from previous run)
    run_command(client, f"mkdir -p {repo_dir}")

    # Unzip -o to overwrite
    run_command(client, f"unzip -o {remote_path} -d {repo_dir}")

    # Clear any existing apt locks or stuck processes
    run_command(client, "killall apt apt-get dpkg || true")
    run_command(
        client, "rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock*"
    )
    run_command(client, "dpkg --configure -a")

    # 3.5 Create venv if missing
    print("\n--- Creating venv if missing ---")
    run_command(
        client, f"cd {repo_dir} && [ ! -d .venv ] && python3 -m venv .venv || echo 'venv exists'"
    )

    # 4. Re-install package in venv (to update code)
    print("\n--- Updating Package in Venv ---")
    run_command(client, f"cd {repo_dir} && .venv/bin/pip install -e .")

    # 4.5 Upload circuit breaker script
    print("\n--- Uploading Circuit Breaker Script ---")
    monitor_script_local = "tools/monitor_install_with_checkpoint.py"
    monitor_script_remote = f"{repo_dir}/tools/monitor_install_with_checkpoint.py"

    if os.path.exists(monitor_script_local):
        sftp = client.open_sftp()
        # Ensure remote tools directory exists
        run_command(client, f"mkdir -p {repo_dir}/tools")
        sftp.put(monitor_script_local, monitor_script_remote)
        sftp.close()
        print(f"✅ Circuit breaker script uploaded to {monitor_script_remote}")
    else:
        print(f"⚠️  Warning: Circuit breaker script not found at {monitor_script_local}")

    # 5. Run Configurator through Circuit Breaker
    print("\n--- Running Configurator through Circuit Breaker ---")
    print("=" * 80)
    print("MONITORING MODE: Circuit breaker will halt on any ERROR, WARNING, SKIP, or TIMEOUT")
    print("=" * 80)

    # Using 'advanced' profile with verbose as requested, and disabling parallel to avoid apt locks
    install_cmd = f"cd {repo_dir} && .venv/bin/python3 -m configurator --verbose install --profile advanced --no-parallel"

    # Run through circuit breaker
    monitor_cmd = (
        f'cd {repo_dir} && python3 tools/monitor_install_with_checkpoint.py "{install_cmd}"'
    )

    if run_command(client, monitor_cmd):
        print("\n✅ Execution completed successfully!")
    else:
        print("\n❌ Execution failed or was halted by circuit breaker!")

    client.close()

    # Clean up local zip
    if os.path.exists(zip_name):
        os.remove(zip_name)


if __name__ == "__main__":
    main()
