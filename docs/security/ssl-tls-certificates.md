# SSL/TLS Certificate Management with Let's Encrypt

This document covers the automated SSL/TLS certificate management features using Let's Encrypt and Certbot.

## Overview

The VPS Configurator provides automated SSL/TLS certificate management with the following features:

- **Automatic Certificate Installation** - One-command certificate setup
- **Auto-Renewal** - Certificates renew automatically 30 days before expiry
- **Web Server Integration** - Nginx and Apache configuration
- **Wildcard Certificates** - DNS-01 challenge support
- **Certificate Monitoring** - Expiry alerts and notifications
- **Strong TLS Configuration** - A+ SSL Labs grade settings

## Prerequisites

The following are required for certificate management:

### External Dependencies

- **Certbot**: Installed automatically if missing
- **Web Server**: Nginx or Apache (for automatic configuration)
- **DNS**: Domain must point to this server for HTTP-01 challenge

### Python Dependencies

```
python-dateutil>=2.8.0  # For date parsing
```

## Quick Start

### Install a Certificate

```bash
# Basic installation with Nginx
vps-configurator cert install --domain mysite.com --email admin@mysite.com

# With additional domains (SAN certificate)
vps-configurator cert install --domain mysite.com --email admin@mysite.com \
    --additional www.mysite.com \
    --additional api.mysite.com

# Using Apache instead of Nginx
vps-configurator cert install --domain mysite.com --email admin@mysite.com \
    --webserver apache

# Wildcard certificate (requires DNS-01 challenge)
vps-configurator cert install --domain mysite.com --email admin@mysite.com \
    --wildcard

# Test with staging environment first
vps-configurator cert install --domain mysite.com --email admin@mysite.com \
    --staging
```

### Check Certificate Status

```bash
# All certificates
vps-configurator cert status

# Specific domain
vps-configurator cert status --domain mysite.com

# JSON output
vps-configurator cert status --json
```

### List Certificates

```bash
vps-configurator cert list
```

### Renew Certificates

```bash
# Renew all certificates due
vps-configurator cert renew

# Renew specific domain
vps-configurator cert renew --domain mysite.com

# Force renewal (even if not due)
vps-configurator cert renew --domain mysite.com --force
```

### Delete a Certificate

```bash
vps-configurator cert delete --domain mysite.com
```

## Configuration

Add the following to your `config/default.yaml`:

```yaml
ssl_certificates:
  enabled: true
  provider: letsencrypt

  letsencrypt:
    email: "admin@example.com"  # Required for notifications
    staging: false              # Use production by default

  auto_renewal:
    enabled: true
    threshold_days: 30          # Renew 30 days before expiry
    schedule: "0 2 * * *"       # Daily at 2 AM
    reload_webserver: true

  challenge:
    preferred: http-01          # http-01, dns-01, tls-alpn-01
    dns_plugin: ""              # cloudflare, route53, etc.

  monitoring:
    enabled: true
    warning_threshold_days: 30
    critical_threshold_days: 14
    email_notifications: false
    slack_webhook: ""

  webserver:
    type: nginx                 # nginx, apache, caddy
    auto_configure: true

  tls_settings:
    protocols: ["TLSv1.2", "TLSv1.3"]
    hsts_enabled: true
    hsts_max_age: 31536000
    ocsp_stapling: true
```

## Data Models

### Certificate

```python
from configurator.security.certificate_manager import Certificate

@dataclass
class Certificate:
    domain: str                              # Primary domain
    subject_alternative_names: List[str]     # SANs
    issuer: str                              # CA name
    valid_from: datetime                     # Not before
    valid_until: datetime                    # Not after
    certificate_path: Path                   # Full chain certificate
    private_key_path: Path                   # Private key
    serial_number: Optional[str]             # Certificate serial
    fingerprint_sha256: Optional[str]        # SHA-256 fingerprint
    auto_renewal_enabled: bool               # Auto-renewal status
    last_renewal: Optional[datetime]         # Last renewal time
    challenge_type: ChallengeType            # ACME challenge used

# Methods
cert.days_until_expiry() -> int              # Days until expiry
cert.status() -> CertificateStatus           # Current status
cert.needs_renewal(threshold_days=30) -> bool # Renewal needed?
cert.is_wildcard() -> bool                   # Is wildcard cert?
cert.to_dict() -> Dict                       # Serialize to dict
```

### Enums

```python
from configurator.security.certificate_manager import (
    ChallengeType,
    CertificateStatus,
    WebServerType,
)

# ACME challenge types
class ChallengeType(Enum):
    HTTP_01 = "http-01"      # HTTP challenge (port 80)
    DNS_01 = "dns-01"        # DNS TXT record (wildcards)
    TLS_ALPN_01 = "tls-alpn-01"  # TLS challenge (port 443)

# Certificate validity status
class CertificateStatus(Enum):
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"  # < 30 days
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    FAILED = "failed"

# Web server types
class WebServerType(Enum):
    NGINX = "nginx"
    APACHE = "apache"
    CADDY = "caddy"
    STANDALONE = "standalone"
```

## CertificateManager API

```python
from configurator.security.certificate_manager import (
    CertificateManager,
    WebServerType,
    ChallengeType,
)

manager = CertificateManager()

# Check if Certbot is available
manager.is_certbot_available() -> bool

# Get Certbot version
manager.get_certbot_version() -> Optional[str]

# Install Certbot
manager.install_certbot() -> bool

# Validate DNS
manager.validate_dns(domain, skip_ip_check=False) -> bool

# Install certificate
cert = manager.install_certificate(
    domain="example.com",
    email="admin@example.com",
    webserver=WebServerType.NGINX,
    additional_domains=["www.example.com"],
    challenge=ChallengeType.HTTP_01,
    staging=False,
    force=False,
)

# Get certificate information
cert = manager.get_certificate("example.com")

# List all certificates
certs = manager.list_certificates()

# Renew certificate
success = manager.renew_certificate("example.com", force=False)

# Renew all certificates
status = manager.renew_all_certificates()

# Setup auto-renewal cron job
manager.setup_auto_renewal(
    schedule="0 2 * * *",
    reload_webserver=True,
    webserver=WebServerType.NGINX,
)

# Backup certificate
backup_path = manager.backup_certificate("example.com")

# Revoke certificate
manager.revoke_certificate("example.com", reason="unspecified")

# Delete certificate
manager.delete_certificate("example.com")

# Get status summary
summary = manager.get_certificate_status_summary()
```

## Certificate Monitoring

```python
from configurator.security.certificate_manager import CertificateManager
from configurator.security.cert_monitor import (
    CertificateMonitor,
    AlertConfig,
    ScheduledMonitor,
)

manager = CertificateManager()

# Configure alerts
alert_config = AlertConfig(
    email_enabled=True,
    email_recipients=["admin@example.com"],
    smtp_host="smtp.example.com",
    smtp_port=587,
    slack_enabled=True,
    slack_webhook="https://hooks.slack.com/...",
)

# Create monitor
monitor = CertificateMonitor(
    certificate_manager=manager,
    alert_config=alert_config,
    warning_threshold_days=30,
    critical_threshold_days=14,
)

# Check certificates
alerts = monitor.check_all_certificates()

# Send alerts
monitor.send_alerts(alerts)

# Get dashboard data
dashboard = monitor.get_status_dashboard()

# Scheduled monitoring
scheduled = ScheduledMonitor(monitor, interval_hours=24)
scheduled.start()
# ... later
scheduled.stop()
```

## Web Server Configuration

### TLS Settings

```python
from configurator.security.webserver_config import TLSConfig

config = TLSConfig(
    protocols=[TLSProtocol.TLS_1_2, TLSProtocol.TLS_1_3],
    hsts_enabled=True,
    hsts_max_age=31536000,
    hsts_include_subdomains=True,
    hsts_preload=False,
    ocsp_stapling=True,
)
```

### Nginx Configuration

```python
from configurator.security.webserver_config import NginxConfigurator

nginx = NginxConfigurator()

# Generate SSL snippet
snippet = nginx.generate_ssl_snippet(config)

# Configure site with SSL
nginx.configure_site(
    domain="example.com",
    cert_path=Path("/etc/letsencrypt/live/example.com/fullchain.pem"),
    key_path=Path("/etc/letsencrypt/live/example.com/privkey.pem"),
    tls_config=config,
)
```

## Security Best Practices

The certificate manager applies these security settings by default:

### TLS Configuration (A+ Grade)

- **Protocols**: TLS 1.2 and TLS 1.3 only
- **Ciphers**: Strong AEAD ciphers only
- **Forward Secrecy**: ECDHE key exchange
- **Session Tickets**: Disabled

### Security Headers

- **HSTS**: Strict-Transport-Security with 1 year max-age
- **X-Frame-Options**: SAMEORIGIN
- **X-Content-Type-Options**: nosniff
- **X-XSS-Protection**: 1; mode=block

### OCSP Stapling

Enabled by default for faster certificate validation.

## Troubleshooting

### DNS Validation Fails

```
DNS validation failed for example.com
```

**Solution**: Ensure DNS A record points to this server's IP.

```bash
# Check DNS
dig +short example.com

# Check server IP
curl -s https://api.ipify.org
```

### Certbot Not Found

Certbot is installed automatically when you run certificate commands. If installation fails:

```bash
# Manual installation
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

### Certificate Renewal Fails

```bash
# Check renewal configuration
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run

# Force renewal
vps-configurator cert renew --domain example.com --force
```

### Rate Limits

Let's Encrypt has rate limits:

- 50 certificates per domain per week
- 5 duplicate certificates per week
- 300 new orders per account per 3 hours

Use `--staging` flag for testing to avoid rate limits.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CertificateManager                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │   Install   │  │    Renew     │  │     Monitor       │   │
│  │ Certificate │  │ Certificate  │  │  Certificates     │   │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘   │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                     Certbot                          │   │
│  │  • HTTP-01 Challenge                                 │   │
│  │  • DNS-01 Challenge                                  │   │
│  │  • TLS-ALPN-01 Challenge                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Web Server Configurator                │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│  │  │  Nginx  │  │ Apache  │  │  Caddy  │               │   │
│  │  └─────────┘  └─────────┘  └─────────┘               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Alert System                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│  │  │  Email  │  │ Webhook │  │  Slack  │               │   │
│  │  └─────────┘  └─────────┘  └─────────┘               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `configurator/security/certificate_manager.py` | Core certificate management |
| `configurator/security/webserver_config.py` | Nginx/Apache configuration |
| `configurator/security/cert_monitor.py` | Monitoring and alerts |
| `config/default.yaml` | Configuration settings |
| `tests/unit/test_certificate_manager.py` | Unit tests |
