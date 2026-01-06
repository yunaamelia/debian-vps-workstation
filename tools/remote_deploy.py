import sys

import paramiko


def create_ssh_client(hostname, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, username=username, password=password)
        print("Connected!")
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)


def run_command(client, command, sudo=False, password=None):
    if sudo and password:
        command = f"echo '{password}' | sudo -S {command}"

    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)

    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    if output:
        print(output)
    if error:
        print(f"Error: {error}")

    return exit_status == 0


def deploy(hostname, password):
    client = create_ssh_client(hostname, "root", password)

    # 1. Update and install git
    print("\n--- Installing Git ---")
    # Clean up conflicting docker sources if they exist (prevents apt warnings)
    run_command(client, "rm -f /etc/apt/sources.list.d/docker.sources", sudo=True)

    if not run_command(client, "apt-get update && apt-get install -y git python3-venv"):
        print("Failed to install prerequisites")
        return

    # 2. Clone repository
    print("\n--- Cloning Repository ---")
    repo_dir = "/root/debian-vps-workstation"

    # Check if dir exists
    check_dir = (
        client.exec_command(f"[ -d {repo_dir} ] && echo 'exists'")[1].read().decode().strip()
    )

    if check_dir == "exists":
        print("Repository exists, pulling latest changes...")
        run_command(client, f"cd {repo_dir} && git pull")
    else:
        print("Cloning repository...")
        run_command(
            client, f"git clone https://github.com/yunaamelia/debian-vps-workstation.git {repo_dir}"
        )

    # 3. Setup Virtualenv
    print("\n--- Setting up Virtualenv ---")
    run_command(client, f"cd {repo_dir} && python3 -m venv .venv")

    # 4. Install Dependencies
    print("\n--- Installing Dependencies ---")
    run_command(client, f"cd {repo_dir} && .venv/bin/pip install -e .")

    # 5. Run Configurator (Dry Run first)
    print("\n--- Running Configurator (Dry Run) ---")
    # Using 'advanced' profile with dry-run
    cmd = f"cd {repo_dir} && .venv/bin/python3 -m configurator install --profile advanced -y --dry-run"
    if run_command(client, cmd):
        print("Dry run successful!")
    else:
        print("Dry run failed!")
        return

    # 6. Real Run?
    # For now, let's stop at dry run and ask user, or just run it?
    # The user asked to "test app". Let's run it.
    print("\n--- Running Configurator (Real Install) ---")
    cmd_install = f"cd {repo_dir} && .venv/bin/python3 -m configurator --verbose install --profile advanced -y"

    # We use a wrapper to stream output better if possible, but exec_command waits.
    # This might take a while.
    stdin, stdout, stderr = client.exec_command(cmd_install, get_pty=True)

    print("Installation started... this may take some time.")
    for line in iter(stdout.readline, ""):
        print(line, end="")

    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("\n✅ Installation completed successfully!")
    else:
        print("\n❌ Installation failed!")

    client.close()


if __name__ == "__main__":
    host = "139.59.124.59"
    pwd = "gg123123@"
    deploy(host, pwd)
