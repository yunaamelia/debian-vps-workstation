import paramiko


def fetch_log(hostname, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, username="root", password=password)

        print("\n--- Checking Binaries ---")
        stdin, stdout, stderr = client.exec_command("which black")
        print(f"black: {stdout.read().decode().strip()}")
        stdin, stdout, stderr = client.exec_command("which pylint")
        print(f"pylint: {stdout.read().decode().strip()}")

        print("\n--- pipx global list ---")
        stdin, stdout, stderr = client.exec_command("pipx list --global")
        print(stdout.read().decode())

        client.close()
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    host = "139.59.124.59"
    pwd = "gg123123@"
    fetch_log(host, pwd)
