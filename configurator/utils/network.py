"""
Network utilities for connectivity checks and downloads.
"""

import socket
from pathlib import Path
from typing import Any, Optional, Tuple, cast

import requests

from configurator.exceptions import NetworkError


def check_internet(
    hosts: Optional[list[tuple[str, int]]] = None,
    timeout: int = 5,
) -> bool:
    """
    Check internet connectivity.

    Args:
        hosts: List of hosts to check (default: common DNS servers)
        timeout: Connection timeout in seconds

    Returns:
        True if internet is available
    """
    if hosts is None:
        hosts = [
            ("8.8.8.8", 53),  # Google DNS
            ("1.1.1.1", 53),  # Cloudflare DNS
            ("9.9.9.9", 53),  # Quad9 DNS
        ]

    for host, port in hosts:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.error, socket.timeout):
            continue

    return False


def check_url_reachable(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    Check if a URL is reachable.

    Args:
        url: URL to check
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (reachable, status_code)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return True, response.status_code
    except requests.RequestException:
        return False, 0


from configurator.utils.retry import retry


@retry(max_retries=3, base_delay=2.0)
def download_file(
    url: str,
    destination: Path,
    timeout: int = 60,
    show_progress: bool = True,
) -> Path:
    """
    Download a file from URL.

    Args:
        url: URL to download from
        destination: Local path to save file
        timeout: Download timeout in seconds
        show_progress: Show download progress (for large files)

    Returns:
        Path to downloaded file

    Raises:
        NetworkError if download fails
    """
    try:
        # Create destination directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(destination, "wb") as f:
            if show_progress and total_size > 1024 * 1024:  # > 1MB
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return destination

    except requests.Timeout:
        raise NetworkError(
            what=f"Download timed out: {url}",
            why=f"Download did not complete within {timeout} seconds",
            how="Check your internet connection and try again.\n"
            "If the file is large, the download might need more time.",
        )
    except requests.HTTPError as e:
        raise NetworkError(
            what=f"Download failed: {url}",
            why=f"HTTP error: {e.response.status_code}",
            how="The URL might be invalid or temporarily unavailable.\n"
            "Check if you can access the URL in a browser.",
        )
    except requests.RequestException as e:
        raise NetworkError(
            what=f"Download failed: {url}",
            why=str(e),
            how="Check your internet connection and try again.",
        )


def get_public_ip() -> Optional[str]:
    """
    Get the public IP address of this server.

    Returns:
        Public IP address or None if unable to determine
    """
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException:
            continue

    return None


@retry(max_retries=2, base_delay=1.0)
def get_latest_github_release(repo: str) -> Optional[dict[str, Any]]:
    """
    Get the latest release info from a GitHub repository.

    Args:
        repo: Repository in format "owner/repo"

    Returns:
        Release info dict or None if not found
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return cast(dict[str, Any], response.json())
        return None
    except requests.RequestException:
        return None


def wait_for_port(
    host: str,
    port: int,
    timeout: int = 30,
    interval: float = 0.5,
) -> bool:
    """
    Wait for a port to become available.

    Args:
        host: Host to check
        port: Port to check
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds

    Returns:
        True if port is available within timeout
    """
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return True
        except socket.error:
            pass

        time.sleep(interval)

    return False
