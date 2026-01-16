# CI/CD Integration

Automate your VPS configuration using CI/CD pipelines.

## GitHub Actions Example

```yaml
name: VPS Config
on: [push]
jobs:
  configure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Configurator
        run: |
          pip install .
          vps-configurator install --profile production --dry-run
```

## Security Note

Always use secrets for sensitive data like SSH keys and passwords.
