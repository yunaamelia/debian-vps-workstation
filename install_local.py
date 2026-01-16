import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

LOCAL_BIN = Path.home() / ".local/bin"
LOCAL_BIN.mkdir(parents=True, exist_ok=True)


def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


def install_zoxide():
    print("Installing zoxide...")
    # Zoxide has a nice install script but we want to control placement
    # It's a single binary usually.
    # Let's use the official install script but direct it
    try:
        subprocess.run(
            "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash",
            shell=True,
            check=True,
        )
        print("Zoxide installed via script (check ~/.local/bin)")
    except subprocess.CalledProcessError:
        print("Failed to install zoxide via script")


def install_eza():
    print("Installing eza...")
    url = "https://github.com/eza-community/eza/releases/download/v0.18.11/eza_x86_64-unknown-linux-gnu.tar.gz"
    dest = Path("eza.tar.gz")
    if download_file(url, dest):
        try:
            with tarfile.open(dest, "r:gz") as tar:
                tar.extractall(path=".")
            # It extracts a binary usually named 'eza'
            if Path("eza").exists():
                shutil.move("eza", LOCAL_BIN / "eza")
                (LOCAL_BIN / "eza").chmod(0o755)
                print("eza installed.")
            else:
                print("eza binary not found after extraction")
        except Exception as e:
            print(f"Failed to extract eza: {e}")
        finally:
            if dest.exists():
                dest.unlink()


def install_bat():
    print("Installing bat...")
    ver = "v0.24.0"
    url = f"https://github.com/sharkdp/bat/releases/download/{ver}/bat-{ver}-x86_64-unknown-linux-gnu.tar.gz"
    dest = Path("bat.tar.gz")
    if download_file(url, dest):
        try:
            with tarfile.open(dest, "r:gz") as tar:
                tar.extractall(path=".")
            # Extracts to directory bat-v0.24.0-x86_64-unknown-linux-gnu/bat
            extract_dir = Path(f"bat-{ver}-x86_64-unknown-linux-gnu")
            bin_path = extract_dir / "bat"
            if bin_path.exists():
                shutil.move(str(bin_path), LOCAL_BIN / "bat")
                (LOCAL_BIN / "bat").chmod(0o755)
                print("bat installed.")
            else:
                print("bat binary not found")

            # Cleanup
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
        except Exception as e:
            print(f"Failed to extract bat: {e}")
        finally:
            if dest.exists():
                dest.unlink()


if __name__ == "__main__":
    install_zoxide()
    install_eza()
    install_bat()
    print("Done. Ensure ~/.local/bin is in your PATH.")
