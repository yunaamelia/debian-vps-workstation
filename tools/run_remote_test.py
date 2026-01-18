import os
import sys

import paramiko


def create_ssh_client(hostname, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname} ({username})...")
        client.connect(hostname, username=username, password=password)
        print("Connected!")
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)


def run_command(client, command, sudo=False, password=None):
    if sudo and password:
        command = f"echo '{password}' | sudo -S -p '' {command}"

    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)

    # Process output line by line as it comes in
    while True:
        try:
            line = stdout.readline()
            if not line:
                break
            print(line, end="")
        except Exception:
            break

    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0


def main():
    host = "206.189.42.66"
    user = "root"
    pwd = os.environ.get("REMOTE_PASSWORD", "")
    if not pwd:
        print("ERROR: REMOTE_PASSWORD environment variable not set")
        sys.exit(1)

    client = create_ssh_client(host, user, pwd)

    # Correct home directory for root, or use standard home for others
    if user == "root":
        repo_dir = "/root/debian-vps-workstation"
    else:
        repo_dir = f"/home/{user}/debian-vps-workstation"

    # 0. Install Prerequisites
    print("\n--- Installing Prerequisites ---")
    run_command(
        client,
        "apt-get update && apt-get install -y git python3-venv python3-pip",
        sudo=True,
        password=pwd,
    )

    # 1. Update/Clone Repo
    print("\n--- Checking Repository ---")
    check_dir_cmd = f"[ -d {repo_dir} ] && echo 'exists'"
    stdin, stdout, stderr = client.exec_command(check_dir_cmd)
    if stdout.read().decode().strip() == "exists":
        print("Repository exists, pulling latest changes...")
        run_command(client, f"cd {repo_dir} && git pull")
    else:
        print("Cloning repository...")
        if not run_command(
            client, f"git clone https://github.com/yunaamelia/debian-vps-workstation.git {repo_dir}"
        ):
            print("Failed to clone repository")
            return

    # 2. Setup/Update Virtualenv
    print("\n--- Setting up Virtualenv ---")
    # Check if venv exists
    venv_check = f"[ -d {repo_dir}/.venv ] && echo 'exists'"
    stdin, stdout, stderr = client.exec_command(venv_check)
    if stdout.read().decode().strip() != "exists":
        run_command(client, f"cd {repo_dir} && python3 -m venv .venv")

    # 3. Install Dependencies
    print("\n--- Installing Dependencies ---")
    # Upgrade pip first to avoid issues
    run_command(client, f"cd {repo_dir} && .venv/bin/pip install --upgrade pip")
    run_command(client, f"cd {repo_dir} && .venv/bin/pip install -e .")

    # 4. Run Configurator
    print("\n--- Running Configurator ---")
    # Using 'advanced' profile with verbose as requested
    # We construct the sudo command manually to ensure we change directory and run python as root
    # Note: We wrap the command in bash -c to handle path change and execution in one go under sudo
    # --verbose must be BEFORE install
    real_cmd = (
        f"cd {repo_dir} && .venv/bin/python3 -m configurator --verbose install --profile advanced"
    )
    escaped_cmd = real_cmd.replace('"', '\\"')
    sudo_cmd = f"echo '{pwd}' | sudo -S -p '' bash -c \"{escaped_cmd}\""

    print("Running sudo command...")
    # We use run_command with manual command string, passing sudo=False because we baked it in
    if run_command(client, sudo_cmd, sudo=False):
        print("\n✅ Execution completed successfully!")
    else:
        print("\n❌ Execution failed!")

    client.close()


if __name__ == "__main__":
    main()
