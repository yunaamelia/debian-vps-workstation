# Package Cache & Local Mirror

The Debian VPS Configurator includes an intelligent package caching system designed to optimize bandwidth usage and speed up repeated installations.

## Overview

When enabled, the package cache transparently captures `.deb` files downloaded by APT during the installation process. Subsequent installations (on the same machine or others sharing the cache) will use these cached files instead of downloading them again.

### Key Features
- **Transparent Caching**: Automatically captures packages from `/var/cache/apt/archives`.
- **Bandwidth Optimization**: Reduces internet data usage by up to 60%.
- **Speed**: Installing from local cache is significantly faster than downloading.
- **Offline Capability**: Enables installation of cached packages without internet access.
- **LRU Eviction**: Automatically removes least recently used packages when cache size limit is reached.
- **Integrity Verification**: Verifies SHA256 hashes to ensuring package integrity.

## Configuration

The package cache is configured in `config.yaml` under the `performance` section:

```yaml
performance:
  package_cache:
    enabled: true             # Enable/Disable the cache
    max_size_gb: 10.0         # Maximum cache size in GB
```

### Cache Directory
- **Root (Default)**: `/var/cache/debian-vps-configurator/packages`
- **User (Fallback)**: `~/.cache/debian-vps-configurator/packages`

## CLI Commands

Manage the cache using the `vps-configurator cache` command group:

### View Statistics
```bash
vps-configurator cache stats
```
Shows total size, hit rate, bandwidth saved, and other metrics.

### List Packages
```bash
vps-c## Configuration
The package cache is configured in `config.yaml` under the `performance.package_cache` section:

```yaml
performance:
  package_cache:
    enabled: true
    max_size_gb: 10.0
```

## Structure
The cache stores packages with filenames including metadata:
`{package}_{version}_{original_filename}`

## Cache Location
Default paths:
- System: `/var/cache/debian-vps-configurator/packages`
- User (fallback): `~/.cache/debian-vps-configurator/packages`

## Usage
Manage the cache via CLI:

```bash
# List packages
vps-configurator cache list

# Show statistics
vps-configurator cache stats

# Clear cache
vps-configurator cache clear --older-than 30
```

## Architecture

The system consists of three main components:

1.  **PackageCacheManager** (`configurator.core.package_cache`):
    - Manages the storage and indexing of packages.
    - Handles LRU eviction and persistence.

2.  **AptCacheIntegration** (`configurator.utils.apt_cache`):
    - Bridges the gap between the custom cache and APT's internal cache (`/var/cache/apt/archives`).
    - **Pre-Install**: Copies cached files to APT archives.
    - **Post-Install**: Scans APT archives for new files and adds them to the custom cache.

3.  **ConfigurationModule Integration**:
    - The `ConfigurationModule` base class orchestrates the pre/post-install hooks during `install_packages()`.

## Best Practices

- **Shared Cache**: For multiple VPS instances, share the `/var/cache/debian-vps-configurator` directory via NFS or a shared volume to create a local mirror.
- **Regular Cleanup**: Use `cache clear --days 90` in a cron job to keep the cache size manageable if you frequently install different packages.
