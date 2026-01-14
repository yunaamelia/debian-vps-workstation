# Network Issues Troubleshooting

Common network-related problems and their solutions when using the VPS Configurator.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Circuit Breaker Problems](#circuit-breaker-problems)
- [Retry Failures](#retry-failures)
- [Timeout Issues](#timeout-issues)
- [APT Repository Problems](#apt-repository-problems)
- [Download Failures](#download-failures)
- [Advanced Debugging](#advanced-debugging)

## Quick Diagnostics

### Check Internet Connectivity

```bash
# Test basic connectivity
ping -c 3 8.8.8.8

# Test DNS resolution
nslookup deb.debian.org

# Test HTTP connectivity
curl -I http://deb.debian.org
```

### Check Circuit Breaker Status

```python
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from configurator.core.network import NetworkOperationWrapper
from unittest.mock import Mock
import logging

logging.basicConfig(level=logging.INFO)

wrapper = NetworkOperationWrapper({}, logging.getLogger())
status = wrapper.get_circuit_breaker_status()

for service, info in status.items():
    state = info['state']
    symbol = "✅" if state == "closed" else "🚨"
    print(f"{symbol} {service}: {state} ({info['failure_count']} failures)")
EOF
```

### Check Health Status

```python
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from configurator.core.health import HealthCheckService
import logging

logging.basicConfig(level=logging.INFO)

health = HealthCheckService(logging.getLogger())
results = health.check_all()

for service, check in results.items():
    status = check.status.value
    time_ms = check.response_time_ms
    symbol = "✅" if status == "healthy" else "⚠️"
    print(f"{symbol} {service}: {status} ({time_ms:.0f}ms)")
EOF
```

## Common Issues

### Issue 1: "Circuit breaker open" Error

**Symptom:**

```
ERROR: 🚨 Circuit breaker open: apt_repository
ERROR: APT update failed: CircuitBreakerError
```

**Cause:** The circuit breaker has detected repeated failures and entered "open" state to prevent cascading failures.

**Solutions:**

1. **Wait for automatic recovery** (60 seconds by default):

   ```bash
   # Circuit will enter half-open state after timeout
   # and attempt one test request
   sleep 65

   # Try operation again
   python -m configurator install --module system
   ```

2. **Check underlying connectivity:**

   ```bash
   # Can you reach the APT repository?
   curl -I http://deb.debian.org

   # Check DNS
   nslookup deb.debian.org

   # Check routing
   traceroute deb.debian.org
   ```

3. **Manually reset circuit breaker** (if connectivity is restored):

   ```python
   # Future CLI command (not yet implemented):
   # vps-configurator circuit-breaker reset apt_repository

   # Workaround: Restart the installation
   # Circuit breakers reset on new process
   ```

4. **Increase failure threshold** (if network is legitimately unstable):
   ```yaml
   # config/default.yaml
   performance:
     circuit_breaker:
       failure_threshold: 5 # Allow more failures before opening
       timeout: 120 # Wait longer before retrying
   ```

### Issue 2: "All X attempts failed"

**Symptom:**

```
WARNING: ⚠️  Attempt 1 failed: Connection timeout
INFO: 🔄 Retrying in 1.2s... (2 retries left)
WARNING: ⚠️  Attempt 2 failed: Connection timeout
INFO: 🔄 Retrying in 2.3s... (1 retries left)
WARNING: ⚠️  Attempt 3 failed: Connection timeout
ERROR: ❌ All 3 attempts failed
```

**Cause:** Operation failed even after all retry attempts.

**Solutions:**

1. **Check network stability:**

   ```bash
   # Test packet loss
   ping -c 100 8.8.8.8 | grep loss

   # Test connection quality
   mtr deb.debian.org --report-cycles 10
   ```

2. **Increase retry attempts:**

   ```yaml
   # config/default.yaml
   performance:
     network_retry:
       max_retries: 5 # Try more times
       max_delay: 60.0 # Allow longer delays
   ```

3. **Check firewall rules:**

   ```bash
   # Check UFW status
   sudo ufw status

   # Temporarily disable firewall to test
   sudo ufw disable
   # Test operation
   # Re-enable: sudo ufw enable
   ```

4. **Use a different mirror:**

   ```bash
   # Edit APT sources to use different mirror
   sudo nano /etc/apt/sources.list

   # Example: Change to a geographically closer mirror
   # deb http://ftp.us.debian.org/debian bookworm main
   ```

### Issue 3: Operation Hangs/Timeout

**Symptom:**

```
INFO: Updating APT package lists...
[Hangs for several minutes]
ERROR: Command timeout after 300 seconds
```

**Cause:** Network operation exceeded configured timeout.

**Solutions:**

1. **Check if operation is actually slow:**

   ```bash
   # Test APT update speed manually
   time sudo apt-get update
   ```

2. **Increase timeout for slow connections:**

   ```yaml
   # config/default.yaml
   performance:
     timeouts:
       apt_update: 600 # Increase to 10 minutes
       download: 1200 # 20 minutes for large files
   ```

3. **Check for proxy issues:**

   ```bash
   # Check if proxy is configured
   echo $http_proxy
   echo $https_proxy

   # Test without proxy
   unset http_proxy https_proxy
   curl -I http://deb.debian.org
   ```

4. **Switch to faster network:**
   ```bash
   # If on WiFi, try ethernet
   # If on VPN, try without VPN
   # If using corporate network, check firewall
   ```

## Circuit Breaker Problems

### Circuit Stuck Open

**Problem:** Circuit breaker remains open even after connectivity is restored.

**Solution:**

```bash
# 1. Verify connectivity is actually restored
curl -I http://deb.debian.org

# 2. Wait for timeout period (default 60s)
sleep 65

# 3. Try a simple operation to test half-open state
python3 << 'EOF'
from configurator.core.network import NetworkOperationWrapper
import logging

logging.basicConfig(level=logging.INFO)
wrapper = NetworkOperationWrapper({}, logging.getLogger())

# This should trigger half-open -> closed transition
result = wrapper.check_internet_connectivity()
print(f"Connectivity: {result}")

# Check circuit state
status = wrapper.get_circuit_breaker_status()
print(f"APT repository state: {status['apt_repository']['state']}")
EOF
```

### Circuit Opens Too Quickly

**Problem:** Circuit breaker opens after just a few transient failures.

**Solution:**

```yaml
# config/default.yaml
performance:
  circuit_breaker:
    failure_threshold: 5 # Tolerate more failures
    timeout: 30 # Recover faster
```

### Circuit Never Opens (Cascading Failures)

**Problem:** Circuit breaker doesn't protect against cascading failures.

**Check configuration:**

```yaml
# Ensure circuit breaker is enabled
performance:
  circuit_breaker:
    enabled: true # Must be true
    failure_threshold: 3
```

## Retry Failures

### Retries Happen Too Quickly

**Problem:** Service gets overwhelmed by rapid retries.

**Solution:**

```yaml
# config/default.yaml
performance:
  network_retry:
    initial_delay: 2.0 # Start with longer delay
    exponential_base: 3.0 # Increase delay more aggressively
    jitter: true # Ensure jitter is enabled
```

### Too Few Retries

**Problem:** Operation fails before service recovers.

**Solution:**

```yaml
# config/default.yaml
performance:
  network_retry:
    max_retries: 5 # More attempts
    max_delay: 60.0 # Allow longer delays
```

### Retries Disabled

**Check configuration:**

```yaml
# config/default.yaml
performance:
  network_retry:
    enabled: true # Must be true
```

## Timeout Issues

### Timeouts Too Short

**Problem:** Operations timeout on slow connections.

**Solution:**

```yaml
# config/default.yaml
performance:
  timeouts:
    apt_update: 600 # 10 minutes
    apt_install: 1200 # 20 minutes
    download: 1800 # 30 minutes for large files
    git_clone: 600 # 10 minutes
```

### Timeouts Too Long

**Problem:** System hangs for too long on failed operations.

**Solution:**

```yaml
# config/default.yaml
performance:
  timeouts:
    apt_update: 180 # 3 minutes
    download: 300 # 5 minutes
```

## APT Repository Problems

### APT Update Fails Repeatedly

**Diagnosis:**

```bash
# Test APT update manually
sudo apt-get update

# Check sources list
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/

# Check APT lock
sudo lsof /var/lib/dpkg/lock-frontend
```

**Solutions:**

1. **Clear APT cache:**

   ```bash
   sudo apt-get clean
   sudo rm -rf /var/lib/apt/lists/*
   sudo apt-get update
   ```

2. **Fix broken packages:**

   ```bash
   sudo dpkg --configure -a
   sudo apt-get install -f
   ```

3. **Change mirror:**
   ```bash
   # Use main Debian mirror
   sudo sed -i 's|http://.*debian.org|http://deb.debian.org|g' /etc/apt/sources.list
   sudo apt-get update
   ```

### APT Lock Errors

**Symptom:**

```
Could not get lock /var/lib/dpkg/lock-frontend
```

**Solution:**

```bash
# Wait for other APT processes to complete
sudo lsof /var/lib/dpkg/lock-frontend

# If no process is holding the lock, remove it
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock
sudo dpkg --configure -a
```

## Download Failures

### Downloads Fail with SSL Errors

**Symptom:**

```
ERROR: SSL certificate problem: certificate verify failed
```

**Solutions:**

1. **Update CA certificates:**

   ```bash
   sudo apt-get update
   sudo apt-get install --reinstall ca-certificates
   ```

2. **Check system time:**

   ```bash
   # Incorrect time causes SSL verification failures
   date

   # Sync time
   sudo ntpdate pool.ntp.org
   # Or
   sudo timedatectl set-ntp true
   ```

3. **Temporary workaround (NOT recommended for production):**
   ```python
   # Disable SSL verification for testing only
   result = wrapper.download_with_retry(
       url="https://example.com/file.tar.gz",
       dest="/tmp/file.tar.gz",
       verify_ssl=False  # Only for debugging!
   )
   ```

### Large File Downloads Timeout

**Solution:**

```python
from configurator.core.network import RetryConfig, NetworkOperationWrapper

# Create wrapper with extended timeout
retry_config = RetryConfig(
    max_retries=5,
    download_timeout=3600  # 1 hour
)

wrapper = NetworkOperationWrapper(config, logger, retry_config)

result = wrapper.download_with_retry(
    url="https://example.com/large-file.iso",
    dest="/tmp/large-file.iso"
)
```

## Advanced Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all network operations will log detailed information
```

### Inspect Circuit Breaker State

```python
from configurator.core.network import NetworkOperationWrapper
import logging

wrapper = NetworkOperationWrapper({}, logging.getLogger())

# Get detailed status
status = wrapper.get_circuit_breaker_status()

for service, info in status.items():
    print(f"\n{service}:")
    print(f"  State: {info['state']}")
    print(f"  Failure Count: {info['failure_count']}")
    print(f"  Success Count: {info['success_count']}")
    print(f"  Total Calls: {info['total_calls']}")
    print(f"  Total Failures: {info['total_failures']}")
```

### Monitor Network Operations

```bash
# Watch network traffic
sudo tcpdump -i any host deb.debian.org

# Monitor bandwidth
sudo iftop

# Check connection states
netstat -an | grep ESTABLISHED
```

### Test Specific Operations

```python
# Test APT update
from configurator.core.network import NetworkOperationWrapper
import logging

logging.basicConfig(level=logging.DEBUG)
wrapper = NetworkOperationWrapper({}, logging.getLogger())

print("Testing APT update...")
result = wrapper.apt_update_with_retry()
print(f"Result: {result}")

# Check circuit breaker after
status = wrapper.get_circuit_breaker_status()
print(f"APT circuit: {status['apt_repository']['state']}")
```

### Simulate Network Conditions

```bash
# Add network delay (requires root)
sudo tc qdisc add dev eth0 root netem delay 100ms

# Test with delay
python -m configurator install --dry-run

# Remove delay
sudo tc qdisc del dev eth0 root

# Add packet loss
sudo tc qdisc add dev eth0 root netem loss 10%

# Test with packet loss
python -m configurator install --dry-run

# Remove packet loss
sudo tc qdisc del dev eth0 root
```

## Getting Help

If problems persist:

1. **Check logs:**

   ```bash
   tail -100 logs/install.log
   grep ERROR logs/install.log
   ```

2. **Run diagnostics:**

   ```bash
   ./scripts/validate_phase3_network.sh
   ```

3. **Report issue with details:**

   - Operating system and version
   - Network configuration (proxy, firewall)
   - Circuit breaker status
   - Full error log
   - Steps to reproduce

4. **Community support:**
   - GitHub Issues: [project-url]/issues
   - Documentation: `docs/`

---

**Related Documentation:**

- [Network Resilience Overview](../advanced/network-resilience.md)
- [Configuration Guide](../configuration/README.md)
- [Module Development](../advanced/module-development.md)
