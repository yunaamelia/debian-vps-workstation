"""
Central configuration for paths and constants used across the configurator.

This module provides a single source of truth for all system paths,
avoiding inconsistencies and magic strings across modules.
"""

from pathlib import Path

# Main configuration directory
CONFIG_DIR = Path("/etc/vps-configurator")

# Data storage directory (user registry, state files)
DATA_DIR = Path("/var/lib/vps-configurator")

# Log directory
LOG_DIR = Path("/var/log/vps-configurator")

# Cache directory (downloaded packages, temporary files)
CACHE_DIR = Path("/var/cache/vps-configurator")

# Backup directory (configuration backups)
BACKUP_DIR = Path("/var/backups/vps-configurator")

# Lock files directory
LOCK_DIR = Path("/var/lock/vps-configurator")

# User registry file
USER_REGISTRY_FILE = DATA_DIR / "users.json"

# Global configuration file
GLOBAL_CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Module state file
MODULE_STATE_FILE = DATA_DIR / "module_state.json"

# Rollback history file
ROLLBACK_HISTORY_FILE = DATA_DIR / "rollback_history.json"

# Circuit breaker state file
CIRCUIT_BREAKER_STATE_FILE = DATA_DIR / "circuit_breaker_state.json"

# Package cache directory
PACKAGE_CACHE_DIR = CACHE_DIR / "packages"

# Main log file
MAIN_LOG_FILE = LOG_DIR / "install.log"

# Error log file
ERROR_LOG_FILE = LOG_DIR / "error.log"

# Audit log file
AUDIT_LOG_FILE = LOG_DIR / "audit.log"

# Global APT lock
APT_LOCK_FILE = LOCK_DIR / "apt.lock"


def ensure_directories():
    """
    Create all required directories if they don't exist.

    Should be called during initial setup or before any file operations.
    """
    for directory in [
        CONFIG_DIR,
        DATA_DIR,
        LOG_DIR,
        CACHE_DIR,
        BACKUP_DIR,
        LOCK_DIR,
        PACKAGE_CACHE_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True, mode=0o755)


# Repository information
GITHUB_OWNER = "yunaamelia"
GITHUB_REPO = "debian-vps-workstation"
GITHUB_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_ISSUES_URL = f"{GITHUB_URL}/issues"
GITHUB_DOCS_URL = f"{GITHUB_URL}#readme"
