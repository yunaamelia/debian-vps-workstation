# Configuration

The configurator uses a YAML-based configuration system.

## Configuration File

The default configuration is located at `config/default.yaml`. You can override these settings by creating a custom config file or using profiles.

## Key Sections

### System
Basic system settings like hostname and timezone.

```yaml
system:
  hostname: "my-vps"
  timezone: "UTC"
```

### Security
Security hardening settings.

```yaml
security:
  ssh_port: 2222
  firewall_enabled: true
```

### Modules
Enable or disable specific modules.

```yaml
modules:
  docker:
    enabled: true
  vscode:
    enabled: true
```
