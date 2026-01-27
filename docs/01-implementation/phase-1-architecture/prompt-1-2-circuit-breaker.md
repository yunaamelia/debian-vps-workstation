# PROMPT 1.2: CIRCUIT BREAKER PATTERN IMPLEMENTATION

## 📋 Context

External services (like package repositories, DNS, 3rd party APIs) can be unreliable. Retrying indefinitely or failing hard can cause cascading failures or lock up the application.
We need a **Circuit Breaker** to detect failures and temporarily stop calling a failing service.

## 🎯 Objective

Implement a `CircuitBreaker` class and decorator in `configurator/core/circuit_breaker.py`.

## 🛠️ Requirements

### Functional

1. **States**:
    - **CLOSED**: Normal operation. Calls go through.
    - **OPEN**: Failure threshold reached. Calls fail immediately (fast failure).
    - **HALF-OPEN**: Timeout passed. Allow one trial call. If success -> CLOSED, else -> OPEN.
2. **Configurable**: Failure threshold (N failures) and Reset timeout (T seconds).
3. **Persistence**: (Optional) In-memory is fine for this CLI tool.

### Non-Functional

1. **Thread Safety**: Must handle concurrent checks (atomic state changes).
2. **Logging**: Log state transitions (e.g., "Circuit OPEN for PyPI").

## 📝 Specifications

### Configuration (`config.yaml`)

```yaml
performance:
  circuit_breaker:
    enabled: true
    failure_threshold: 3
    recovery_timeout: 30 # seconds
```

### Class Signature (`configurator/core/circuit_breaker.py`)

```python
import time
from enum import Enum
from functools import wraps
import threading

class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: int = 30):
        pass

    def call(self, func, *args, **kwargs):
        """Executes func with circuit breaker logic."""
        pass
```

## 🪜 Implementation Steps

1. **Create the Module**:

    - `configurator/core/circuit_breaker.py`.

2. **Implement Logic**:

    - Track `failure_count`.
    - Track `last_failure_time`.
    - In `call()`:
      - If `State.OPEN`: Check if `recovery_timeout` passed.
        - No: Raise `CircuitBreakerOpenException`.
        - Yes: Transition to `State.HALF_OPEN`.
      - Execute `func()`.
      - If Success:
        - If `HALF_OPEN` -> Reset to `CLOSED`.
        - Return result.
      - If Exception:
        - Increment `failure_count`.
        - If `failure_count` >= `threshold` -> Transition to `OPEN`.
        - Raise Exception.

3. **Implement Decorator**:

    - Create `@circuit_breaker(name="api_calls")` decorator for easy usage.

4. **Integration Test**:
    - Create `tests/unit/test_circuit_breaker.py`.
    - Simulate a function that fails 3 times then succeeds.
    - Verify state transitions.

## 🔍 Validation Checklist

- [ ] Circuit opens after N failures.
- [ ] Circuit raises fast exception when OPEN.
- [ ] Circuit allows one call after timeout (HALF-OPEN).
- [ ] Circuit closes after success in HALF-OPEN.
- [ ] Thread safe access.

---

**Output**: Generate the python code for `configurator/core/circuit_breaker.py` and the test file.
