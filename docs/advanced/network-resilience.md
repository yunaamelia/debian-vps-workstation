# Network Resilience

This document describes the network resilience layer implemented in the VPS Configurator. This layer provides circuit breaker protection, intelligent retry strategies, and timeout handling for all network-dependent operations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Usage](#usage)
- [Configuration](#configuration)
- [Circuit Breakers](#circuit-breakers)
- [Retry Strategies](#retry-strategies)
- [Monitoring](#monitoring)
- [Best Practices](#best-practices)

## Overview

Network operations are inherently unreliable. External services can be slow, temporarily unavailable, or experience transient failures. Without proper resilience mechanisms, these failures can cascade throughout the system, causing:

- **Installation freezes** when network operations hang indefinitely
- **Cascading failures** when one service's failure impacts others
- **Poor user experience** with no automatic recovery
- **Resource exhaustion** from retrying too aggressively

The network resilience layer solves these problems by providing:

✅ **Circuit Breaker Protection** - Fast-fail when services are down
✅ **Intelligent Retry Logic** - Exponential backoff with jitter
✅ **Timeout Handling** - Prevents hanging operations
✅ **Health Monitoring** - Track external service health
✅ **Graceful Degradation** - System continues even when services fail

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Network Resilience Layer                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐    ┌─────────────────┐       │
│  │ CircuitBreaker   │◄───│HealthCheck      │       │
│  │ Manager          │    │ System          │       │
│  └────────┬─────────┘    └─────────────────┘       │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────────────────────────┐           │
│  │   NetworkOperationWrapper            │           │
│  ├──────────────────────────────────────┤           │
│  │  • execute_with_retry()              │           │
│  │  • apt_update_with_retry()           │           │
│  │  • download_with_retry()             │           │
│  │  • git_clone_resilient()             │           │
│  └──────────────────────────────────────┘           │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────────────────────────┐           │
│  │   RetryStrategy                      │           │
│  ├──────────────────────────────────────┤           │
│  │  • ExponentialBackoff                │           │
│  │  • JitterStrategy                    │           │
│  │  • MaxRetries configuration          │           │
│  └──────────────────────────────────────┘           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Features

### 1. Circuit Breaker Pattern

Circuit breakers prevent cascading failures by **failing fast** when a service is known to be down.

**States:**

- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: Service is down, fail immediately without trying
- **HALF_OPEN**: Testing if service recovered

**Example:**

```python
# After 3 failures, circuit opens
# Requests fail immediately for 60 seconds
# Then one test request (half-open)
# If successful, circuit closes
```

**Protected Services:**

- `apt_repository` - Debian package repositories
- `github` - GitHub for git clones
- `docker_hub` - Docker Hub downloads
- `microsoft_packages` - Microsoft APT repositories
- `external_downloads` - General downloads

### 2. Retry Logic

Intelligent retry with **exponential backoff** and **jitter**.

**Retry Sequence:**

```
Attempt 1: Immediate
Attempt 2: Wait 1.0s + jitter
Attempt 3: Wait 2.0s + jitter
Attempt 4: Wait 4.0s + jitter (if max_retries > 3)
```

**Jitter** adds randomness (0-10% of delay) to prevent the **thundering herd problem** where many clients retry simultaneously.

### 3. Timeout Handling

All network operations have configurable timeouts:

| Operation    | Default Timeout |
| ------------ | --------------- |
| APT Update   | 300s (5 min)    |
| APT Install  | 600s (10 min)   |
| Download     | 600s (10 min)   |
| Git Clone    | 300s (5 min)    |
| HTTP Request | 30s             |

### 4. Health Check System

Monitor external service health in real-time.

**Health Statuses:**

- **HEALTHY**: Response time < 1s
- **DEGRADED**: Response time 1-3s
- **UNHEALTHY**: Response time > 3s or connection failed

## Usage

### For Module Developers

All configuration modules inherit network resilience capabilities:

```python
class MyModule(ConfigurationModule):
    def configure(self):
        # Use resilient package installation
        self.install_packages_resilient([
            "package1",
            "package2"
        ])

        # Use network wrapper directly
        self.network.download_with_retry(
            url="https://example.com/file.tar.gz",
            dest="/tmp/file.tar.gz"
        )

        # Check connectivity first
        if not self.network.check_internet_connectivity():
            self.logger.warning("No internet connectivity")
            return False

        # Clone with resilience
        self.network.git_clone_resilient(
            url="https://github.com/user/repo.git",
            dest="/opt/myrepo"
        )
```

### Network Operation Wrapper Methods

#### `apt_update_with_retry()`

```python
# Update APT package lists with retry
success = self.network.apt_update_with_retry()
```

#### `apt_install_with_retry(packages, update_cache=True)`

```python
# Install packages with automatic retry
success = self.network.apt_install_with_retry(
    packages=["docker-ce", "docker-compose"],
    update_cache=True
)
```

#### `download_with_retry(url, dest, verify_ssl=True)`

```python
# Download file with retry
file_path = self.network.download_with_retry(
    url="https://example.com/installer.sh",
    dest="/tmp/installer.sh",
    verify_ssl=True
)

if file_path:
    print(f"Downloaded to: {file_path}")
```

#### `git_clone_resilient(url, dest, depth=1, branch=None)`

```python
# Git clone with retry and timeout
success = self.network.git_clone_resilient(
    url="https://github.com/ohmyzsh/ohmyzsh.git",
    dest="/opt/ohmyzsh",
    depth=1,
    branch="master"
)
```

#### `check_internet_connectivity(test_urls=None)`

```python
# Check if internet is available
if self.network.check_internet_connectivity():
    # Proceed with network operations
    pass
else:
    # Handle offline scenario
    pass
```

### Get Circuit Breaker Status

```python
# Get current status of all circuit breakers
status = self.network.get_circuit_breaker_status()

for service, info in status.items():
    print(f"{service}:")
    print(f"  State: {info['state']}")
    print(f"  Failures: {info['failure_count']}")
    print(f"  Total Calls: {info['total_calls']}")
```

## Configuration

Network resilience is configured in `config/default.yaml`:

```yaml
performance:
  # Circuit Breaker Configuration
  circuit_breaker:
    enabled: true
    failure_threshold: 3 # Open after 3 failures
    timeout: 60 # Retry after 60 seconds
    success_threshold: 1 # Close after 1 success in half-open

  # Network Retry Configuration
  network_retry:
    enabled: true
    max_retries: 3
    initial_delay: 1.0 # seconds
    max_delay: 30.0 # seconds
    exponential_base: 2.0
    jitter: true # Add random jitter

  # Timeout Configuration
  timeouts:
    apt_update: 300 # 5 minutes
    apt_install: 600 # 10 minutes
    download: 600 # 10 minutes
    git_clone: 300 # 5 minutes
    http_request: 30 # 30 seconds

  # Health Checks
  health_checks:
    enabled: true
    check_on_startup: true
    services:
      - apt_repository
      - github
      - docker_hub
```

### Configuration Options

#### Circuit Breaker

| Option              | Default | Description                                      |
| ------------------- | ------- | ------------------------------------------------ |
| `enabled`           | `true`  | Enable circuit breaker protection                |
| `failure_threshold` | `3`     | Number of failures before opening circuit        |
| `timeout`           | `60`    | Seconds to wait before trying again (half-open)  |
| `success_threshold` | `1`     | Successes needed to close circuit from half-open |

#### Network Retry

| Option             | Default | Description                  |
| ------------------ | ------- | ---------------------------- |
| `enabled`          | `true`  | Enable retry logic           |
| `max_retries`      | `3`     | Maximum retry attempts       |
| `initial_delay`    | `1.0`   | Initial delay in seconds     |
| `max_delay`        | `30.0`  | Maximum delay in seconds     |
| `exponential_base` | `2.0`   | Base for exponential backoff |
| `jitter`           | `true`  | Add randomness to delays     |

## Circuit Breakers

### How Circuit Breakers Work

1. **Normal Operation (CLOSED)**

   - All requests pass through
   - Failures are counted
   - After `failure_threshold` consecutive failures → OPEN

2. **Fast-Fail Mode (OPEN)**

   - All requests fail immediately (no network call)
   - After `timeout` seconds → HALF_OPEN
   - Prevents cascading failures

3. **Testing Recovery (HALF_OPEN)**
   - One test request is allowed
   - If successful → CLOSED (normal operation)
   - If fails → OPEN (back to fast-fail)

### Manual Circuit Breaker Control

Circuit breakers can be manually reset if needed (future CLI command):

```bash
# Check circuit breaker status
vps-configurator circuit-breaker status

# Reset a specific circuit breaker
vps-configurator circuit-breaker reset apt_repository

# Reset all circuit breakers
vps-configurator circuit-breaker reset --all
```

## Retry Strategies

### Exponential Backoff

Delays increase exponentially to avoid overwhelming failing services:

```
delay = min(initial_delay * (exponential_base ^ attempt), max_delay)
```

**Example with defaults (initial_delay=1.0, base=2.0, max=30.0):**

- Attempt 1: Immediate
- Attempt 2: 1.0s delay
- Attempt 3: 2.0s delay
- Attempt 4: 4.0s delay
- Attempt 5: 8.0s delay (if max_retries > 4)

### Jitter

Adds randomness (0-10% of calculated delay) to prevent synchronized retries:

```python
if jitter:
    delay += random.uniform(0, delay * 0.1)
```

**Why jitter?** Without jitter, when 100 clients fail simultaneously, they all retry at the same intervals, creating traffic spikes that can overwhelm recovering services.

## Monitoring

### Health Check Dashboard

Check health of external services:

```python
from configurator.core.health import HealthCheckService

health = HealthCheckService(logger)

# Check all configured services
results = health.check_all()

# Get summary
summary = health.get_summary()
print(f"Healthy: {summary['healthy']}")
print(f"Degraded: {summary['degraded']}")
print(f"Unhealthy: {summary['unhealthy']}")
```

### Logging

All network operations are logged with detailed information:

```
INFO: Updating APT package lists (with retry protection)...
INFO: ✅ APT update successful

WARNING: ⚠️  Attempt 1 failed: Connection timeout
INFO: 🔄 Retrying in 1.2s... (2 retries left)
INFO: ✅ Operation succeeded after 2 attempts

ERROR: 🚨 Circuit breaker open: apt_repository
ERROR: ❌ All 3 attempts failed
```

## Best Practices

### 1. Always Use Resilient Methods

❌ **Bad:**

```python
subprocess.run(['apt-get', 'install', 'package'])
```

✅ **Good:**

```python
self.install_packages_resilient(['package'])
```

### 2. Check Connectivity First (Optional)

```python
if not self.network.check_internet_connectivity():
    self.logger.warning("No internet, skipping online features")
    # Implement offline fallback
    return True  # Don't fail, just skip
```

### 3. Handle Circuit Breaker Errors

```python
from configurator.utils.circuit_breaker import CircuitBreakerError

try:
    self.network.apt_update_with_retry()
except CircuitBreakerError:
    self.logger.error("APT repository circuit is open")
    # Inform user to check connectivity or wait
except Exception as e:
    self.logger.error(f"APT update failed: {e}")
```

### 4. Use Appropriate Timeouts

```python
# For large downloads, increase timeout
from configurator.core.network import RetryConfig

retry_config = RetryConfig(
    max_retries=5,
    download_timeout=1800  # 30 minutes for large files
)

wrapper = NetworkOperationWrapper(config, logger, retry_config)
```

### 5. Monitor Circuit Breaker State

```python
# Before critical operations, check circuit state
status = self.network.get_circuit_breaker_status()

if status['apt_repository']['state'] == 'open':
    self.logger.warning("APT circuit is open, waiting...")
    time.sleep(60)  # Wait for circuit to attempt recovery
```

### 6. Test Network Resilience

Always test network failure scenarios:

```bash
# Run resilience tests
pytest tests/resilience/test_network_failure_simulation.py -v

# Run integration tests (requires internet)
pytest tests/integration/test_network_integration.py -v --slow
```

## Troubleshooting

See [Network Issues Troubleshooting Guide](../troubleshooting/network-issues.md) for common problems and solutions.

## Performance Impact

Network resilience adds minimal overhead:

- **Successful operations**: < 2ms overhead
- **Failed operations**: Delayed by retry logic (by design)
- **Circuit open**: ~0.1ms (fast-fail, no network call)
- **Memory usage**: ~1MB for circuit breaker state

## Future Enhancements

Planned improvements:

- [ ] Prometheus metrics export
- [ ] Distributed circuit breaker state (Redis)
- [ ] Adaptive timeout calculation
- [ ] Request rate limiting
- [ ] Bulkhead pattern for resource isolation
- [ ] Dead letter queue for failed operations

---

**Next Steps:**

- Review [Troubleshooting Guide](../troubleshooting/network-issues.md)
- Explore [Module Development Guide](module-development.md)
- Check [Security Best Practices](../SECURITY.md)
