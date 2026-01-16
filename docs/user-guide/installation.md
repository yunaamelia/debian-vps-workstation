# Installation Guide

## Quick Start

The fastest way to install the Debian VPS Workstation Configurator is using the quick-install script:

```bash
curl -sSL https://raw.githubusercontent.com/ahmadrizal7/debian-vps-workstation/main/quick-install.sh | bash
```

## Manual Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ahmadrizal7/debian-vps-workstation.git
    cd debian-vps-workstation
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .
    ```

4.  **Run the configurator:**
    ```bash
    vps-configurator wizard
    ```

## Requirements

*   **OS:** Debian 13 (Trixie) or Debian 12 (Bookworm)
*   **RAM:** Minimum 1GB, Recommended 2GB
*   **Disk:** Minimum 10GB free space
*   **User:** Root access or sudo privileges
