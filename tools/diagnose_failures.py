import os
import sys

import paramiko


def create_ssh_client(hostname, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, username=username, password=password)
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)


def run_command(client, command, title=None):
    if title:
        print(f"\n--- {title} ---")
        print(f"Command: {command}")

    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if out:
        print("Output:")
        print(out)
    if err:
        print("Error:")
        print(err)

    return exit_status == 0


def main():
    host = "206.189.42.66"
    user = "root"
    pwd = os.environ.get("REMOTE_PASSWORD", "")
    if not pwd:
        print("ERROR: REMOTE_PASSWORD environment variable not set")
        sys.exit(1)

    client = create_ssh_client(host, user, pwd)

    # 1. Diagnose Wireguard
    run_command(
        client, "systemctl status wg-quick@wg0.service --no-pager", "WireGuard Service Status"
    )
    run_command(
        client,
        "journalctl -xeu wg-quick@wg0.service --no-pager | tail -n 50",
        "WireGuard Journal Logs",
    )
    run_command(client, "cat /etc/wireguard/wg0.conf", "WireGuard Config (Check)")

    # 2. Diagnose Docker
    run_command(client, "systemctl status docker --no-pager", "Docker Service Status")
    run_command(client, "docker info", "Docker Info")
    run_command(
        client,
        "cat /var/log/debian-vps-configurator/install.log | grep -A 20 -B 5 'Installing Docker'",
        "Docker Install Log Snippet",
    )

    # 3. Diagnose PHP
    run_command(client, "php -v", "PHP Version")
    run_command(
        client, "apt-get install -y php --dry-run", "PHP Install Dry Run (Check Dependencies)"
    )
    run_command(
        client,
        "cat /var/log/debian-vps-configurator/install.log | grep -A 20 -B 5 'Installing PHP'",
        "PHP Install Log Snippet",
    )

    client.close()


if __name__ == "__main__":
    main()
