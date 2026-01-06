# Circuit Breaker Pattern - Troubleshooting Guide

The Circuit Breaker pattern prevents cascading failures and wasted time by automatically detecting broken services (like APT repositories) and stopping retry attempts after a threshold.

## 📊 State Diagram

```ascii
           [Success]
     ┌────────────────────┐
     │                    │
     ▼                    │
┌─────────┐           ┌─────────┐
│         │ [Failure] │         │
│ CLOSED  │──────────►│  OPEN   │
│         │           │         │
└─────────┘           └─────────┘
     ▲                     │
     │                     │ [Timeout]
     │                     │
     │    ┌─────────┐      │
     │    │         │◄─────┘
     └────│HALF-OPEN│
 [Success]│         │
          └─────────┘
            [Failure]
```

## 🔄 States Explained

1.  **CLOSED (Normal)**:
    - Requests are allowed through.
    - Failures are counted.
    - If failures >= `failure_threshold` (default: 3), state changes to **OPEN**.

2.  **OPEN (Failure)**:
    - All requests fail immediately with `CircuitBreakerError`.
    - Prevents wasting time on retries when a service is known to be down.
    - After `timeout` (default: 60s), state changes to **HALF-OPEN**.

3.  **HALF-OPEN (Recovery)**:
    - A single test request is allowed through.
    - If successful: State changes to **CLOSED** (Service recovered).
    - If failed: State returns to **OPEN** (Service still down).

## 🛠️ CLI Commands

### status circuit-breakers
View real-time status of all circuit breakers.

```bash
vps-configurator status circuit-breakers
```

**Output:**
```
Circuit Breaker Status
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┓
┃ Service         ┃ State  ┃ Failures ┃ Successes ┃ Rate ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━┩
│ apt-repository  │ CLOSED │ 0        │ 12        │ 0.0% │
│ pypi-repository │ OPEN   │ 3        │ 45        │ 6.2% │
└─────────────────┴────────┴──────────┴───────────┴──────┘
```

### reset circuit-breaker
Manually reset a circuit breaker to CLOSED state.

```bash
vps-configurator reset circuit-breaker apt-repository
```

## ⚠️ Common Errors & Troubleshooting

### Error: "Circuit breaker open for apt"

**Message:**
```
╔════════════════════════════════════════════════════════╗
║           ⚠️  CIRCUIT BREAKER OPEN                     ║
╚════════════════════════════════════════════════════════╝
Service: apt-repository
State: OPEN
...
```

**Why it happened:**
The system detected repeated failures (usually 3) when trying to connect to the APT repository.

**Resolution Steps:**

1.  **Check Connectivity**:
    ```bash
    ping -c 3 deb.debian.org
    ```

2.  **Wait for Recovery**:
    The system will automatically try again after 60 seconds.

3.  **Manual Reset**:
    If you fixed the issue (e.g., restored internet connectivity), you can force a reset:
    ```bash
    vps-configurator reset circuit-breaker apt-repository
    ```

## ⚙️ Configuration

Tune the sensitivity in `config.yaml`:

```yaml
performance:
  circuit_breaker:
    enabled: true        # Enable/Disable globally
    failure_threshold: 3 # Failures before opening
    timeout: 60          # Seconds to wait before retry
```
