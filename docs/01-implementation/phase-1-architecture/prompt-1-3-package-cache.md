# PROMPT 1.3: PACKAGE CACHE MANAGER IMPLEMENTATION

## 📋 Context

Repeatedly downloading the same packages (apt debs, pip wheels, git repos) during testing or re-provisioning wastes bandwidth and time.
We need a **Package Cache** to store downloaded assets locally and serve them if they haven't changed.

## 🎯 Objective

Implement `PackageCache` in `configurator/core/package_cache.py` to manage local storage of artifacts.

## 🛠️ Requirements

### Functional

1. **Storage**: Central directory (e.g., `~/.vps-configurator/cache/`).
2. **Hashing**: Identify files by SHA256 checksum or version string.
3. **Operations**: `get(key)`, `put(key, file_path)`, `exists(key)`.
4. **Backend Support**:
    - APT: Proxy or local repo (simulated via `var/cache/apt/archives` checks).
    - PIP: Use pip's internal cache or copy wheels.
    - Files: Generic file download cache.

### Non-Functional

1. **Integrity**: Ensure cached files are not corrupted (check hash on retrieval).
2. **Size Limit**: (Optional) LRU policies to clear old cache files.

## 📝 Specifications

### Configuration (`config.yaml`)

```yaml
performance:
  cache:
    enabled: true
    directory: "/var/cache/vps-configurator"
    max_size_gb: 5
```

### Class Signature (`configurator/core/package_cache.py`)

```python
import hashlib
import shutil
from pathlib import Path

class PackageCache:
    def __init__(self, cache_dir: str, enabled: bool = True):
        pass

    def get_cached_file(self, url: str) -> str:
        """Returns path to cached file or None"""
        pass

    def cache_file(self, url: str, source_path: str):
        """Copies file to cache"""
        pass

    def calculate_hash(self, file_path: str) -> str:
        pass
```

## 🪜 Implementation Steps

1. **Create Module**: `configurator/core/package_cache.py`.
2. **Hash Generation**: Implement URL -> Filename logic (e.g., MD5 of URL) to store unique files.
3. **File Operations**:
    - Ensure cache dir exists.
    - `shutil.copy2` for storing.
4. **Integration**:
    - Identify where `wget` or `curl` is used in the codebase.
    - Wrap downloads with this cache logic.

## 🔍 Validation Checklist

- [ ] File is downloaded once.
- [ ] Second request returns local path.
- [ ] Corrupted cache file (modifying content) is detected/ignored (if hash check implemented).
- [ ] Cache can be disabled via config.

---

**Output**: Generate `configurator/core/package_cache.py` and unit tests.
