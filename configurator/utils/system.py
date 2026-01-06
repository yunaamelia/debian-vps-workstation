"""
System information utilities.
"""

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class OSInfo:
    """Operating system information."""

    name: str
    version: str
    version_id: str
    codename: str
    pretty_name: str

    @property
    def is_debian(self) -> bool:
        """Check if this is a Debian-based system."""
        return self.name.lower() == "debian"

    @property
    def is_debian_13(self) -> bool:
        """Check if this is Debian 13 (Trixie)."""
        return self.is_debian and self.version_id == "13"


def get_os_info() -> OSInfo:
    """
    Get operating system information from /etc/os-release.

    Returns:
        OSInfo dataclass with OS details
    """
    os_release_path = Path("/etc/os-release")

    if not os_release_path.exists():
        return OSInfo(
            name="unknown",
            version="unknown",
            version_id="unknown",
            codename="unknown",
            pretty_name="Unknown OS",
        )

    info = {}
    content = os_release_path.read_text()

    for line in content.strip().split("\n"):
        if "=" in line:
            key, value = line.split("=", 1)
            # Remove quotes
            value = value.strip('"').strip("'")
            info[key.lower()] = value

    return OSInfo(
        name=info.get("id", "unknown"),
        version=info.get("version", "unknown"),
        version_id=info.get("version_id", "unknown"),
        codename=info.get("version_codename", "unknown"),
        pretty_name=info.get("pretty_name", "Unknown OS"),
    )


def get_architecture() -> str:
    """
    Get the system architecture.

    Returns:
        Architecture string (e.g., "x86_64", "aarch64")
    """
    return platform.machine()


def is_x86_64() -> bool:
    """Check if running on x86_64 architecture."""
    return get_architecture() in ("x86_64", "amd64")


def is_arm64() -> bool:
    """Check if running on ARM64 architecture."""
    return get_architecture() in ("aarch64", "arm64")


def get_ram_gb() -> float:
    """
    Get total RAM in gigabytes.

    Returns:
        Total RAM in GB
    """
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    # Value is in KB
                    kb = int(line.split()[1])
                    return kb / 1024 / 1024
    except Exception:
        pass

    return 0.0


def get_available_ram_gb() -> float:
    """
    Get available RAM in gigabytes.

    Returns:
        Available RAM in GB
    """
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    return kb / 1024 / 1024
    except Exception:
        pass

    return 0.0


def get_disk_free_gb(path: str = "/") -> float:
    """
    Get free disk space in gigabytes.

    Args:
        path: Path to check (default: root filesystem)

    Returns:
        Free disk space in GB
    """
    try:
        stat = os.statvfs(path)
        free_bytes = stat.f_bavail * stat.f_frsize
        return free_bytes / 1024 / 1024 / 1024
    except Exception:
        return 0.0


def get_disk_total_gb(path: str = "/") -> float:
    """
    Get total disk space in gigabytes.

    Args:
        path: Path to check (default: root filesystem)

    Returns:
        Total disk space in GB
    """
    try:
        stat = os.statvfs(path)
        total_bytes = stat.f_blocks * stat.f_frsize
        return total_bytes / 1024 / 1024 / 1024
    except Exception:
        return 0.0


def get_cpu_count() -> int:
    """
    Get the number of CPU cores.

    Returns:
        Number of CPU cores
    """
    return os.cpu_count() or 1


def is_root() -> bool:
    """
    Check if running as root.

    Returns:
        True if running as root (UID 0)
    """
    return os.getuid() == 0


def is_sudo_available() -> bool:
    """
    Check if sudo is available and the user can use it.

    Returns:
        True if sudo is available
    """
    import subprocess

    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def is_systemd() -> bool:
    """
    Check if the system is using systemd.

    Returns:
        True if systemd is the init system
    """
    # Check if systemd is PID 1
    try:
        init_path = Path("/proc/1/comm")
        if init_path.exists():
            init = init_path.read_text().strip()
            return init == "systemd"
    except Exception:
        pass

    # Fallback: check if systemctl exists
    return Path("/bin/systemctl").exists() or Path("/usr/bin/systemctl").exists()


def get_current_hostname() -> str:
    """
    Get the current system hostname.

    Returns:
        Current hostname
    """
    import socket

    return socket.gethostname()


def get_current_timezone() -> str:
    """
    Get the current system timezone.

    Returns:
        Current timezone (e.g., "Asia/Jakarta")
    """
    # Try to read from timedatectl
    import subprocess

    try:
        result = subprocess.run(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Try to read from /etc/timezone
    tz_file = Path("/etc/timezone")
    if tz_file.exists():
        return tz_file.read_text().strip()

    # Try to resolve /etc/localtime symlink
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        target = str(localtime.resolve())
        if "/zoneinfo/" in target:
            return target.split("/zoneinfo/", 1)[1]

    return "UTC"


def get_swap_info() -> Tuple[float, float]:
    """
    Get swap memory information.

    Returns:
        Tuple of (total_gb, used_gb)
    """
    try:
        with open("/proc/meminfo", "r") as f:
            total: float = 0.0
            used: float = 0.0
            for line in f:
                if line.startswith("SwapTotal:"):
                    total = int(line.split()[1]) / 1024 / 1024
                elif line.startswith("SwapFree:"):
                    free = int(line.split()[1]) / 1024 / 1024
                    used = total - free
            return total, used
    except Exception:
        return 0.0, 0.0


def get_uptime_seconds() -> float:
    """
    Get system uptime in seconds.

    Returns:
        Uptime in seconds
    """
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0
