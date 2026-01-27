# Desktop & XRDP Module

This module installs a lightweight desktop environment (XFCE4) and configures XRDP for remote access.

## Features

* **XFCE4**: Lightweight, fast, and stable.
* **XRDP**: Optimized configuration for low-latency remote access.
* **Audio Redirection**: Pulseaudio configuration for remote sound.
* **Browser**: Firefox ESR pre-installed.

## Configuration

```yaml
modules:
  desktop:
    enabled: true
    environment: "xfce4"
    rdp_port: 3389
```
