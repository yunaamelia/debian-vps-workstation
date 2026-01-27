# Migration Guide: Configuration Validation v2

## Breaking Changes

Starting with version 2.0, `vps-configurator` uses **Pydantic** for strict configuration validation. This improves type safety and prevents invalid configurations from being applied.

However, this means:

- **Strict Typing**: Fields that expect integers (like ports) must be integers.
- **Unknown Fields**: Keys that are not defined in the schema will cause validation errors (previously they might have been ignored).
- **Required Fields**: Any fields marked as required must be present.

## How to Migrate

If your existing `config.yaml` fails to validate, follow these steps:

### 1. Validate your current configuration

Run the installation in dry-run mode to trigger validation without changes:

```bash
vps-configurator install --config config.yaml --dry-run
```

If you see errors like:

```text
Configuration Error: security -> ufw -> ssh_port
Why: Validation failed... value is not a valid integer
```

### 2. Common Fixes

#### Invalid Port Numbers

**Error**: `value is not a valid integer`
**Fix**: Ensure ports are numbers, not strings.

```yaml
# ❌ Bad
ssh_port: "22"

# ✅ Good
ssh_port: 22
```

#### Extra Keys

**Error**: `extra fields not permitted`
**Fix**: Remove configuration keys that are no longer supported or misspelled.

#### Legacy `enable` vs `enabled`

**Fix**: Ensure you use `enabled: true` (standardized) instead of mixed `enable` or `active`.

## Schema Reference

Refer to `docs/CONFIGURATION.md` (or the source `configurator/config_schema.py`) for the complete definition of allowed fields.
