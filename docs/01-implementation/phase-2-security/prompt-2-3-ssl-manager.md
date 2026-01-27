# PROMPT 2.3: SSL/TLS CERTIFICATE MANAGER IMPLEMENTATION

## 📋 Context

Secure communication (HTTPS) is mandatory. Manually running Certbot is error-prone.
We need an `SSLManager` to automate certificate issuance and renewal via Let's Encrypt.

## 🎯 Objective

Implement a wrapper around `certbot` or `acme` client in `configurator/security/ssl_manager.py`.

## 🛠️ Requirements

### Functional

1. **Issue**: Request new cert for domain(s).
2. **Renew**: Check expiry and renew if needed.
3. **Hooks**: Reload Nginx/Apache after renewal.
4. **Monitoring**: Alert if cert is expiring and renewal failed.

## 📝 Specifications

### Class Signature (`configurator/security/ssl_manager.py`)

```python
class SSLManager:
    def issue_cert(self, domains: List[str], email: str):
        # cmd: certbot certonly --standalone -d example.com ...
        pass

    def check_expiry(self, domain: str) -> int:
        # Returns days remaining
        pass

    def auto_renew(self):
        # cmd: certbot renew
        pass
```

## 🪜 Implementation Steps

1. **Check Certbot**: Ensure `certbot` is installed.
2. **Command Construction**: Securely build shell commands.
3. **Parser**: Parse `openssl x509 -enddate -noout -in ...` to get expiry.
4. **Cron Integration**: Method to add a daily cron job for renewal.

## 🔍 Validation Checklist

- [ ] Correctly constructs certbot command.
- [ ] Parses expiry date from a sample `.pem` file.
- [ ] Handles missing certbot gracefully.

---

**Output**: Python code for `configurator/security/ssl_manager.py`.
