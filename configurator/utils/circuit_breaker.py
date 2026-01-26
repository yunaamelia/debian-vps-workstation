import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, Type


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 3  # Failures before opening circuit
    success_threshold: int = 1  # Successes to close circuit
    timeout: float = 60.0  # Seconds before attempting reset
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Too many failures, reject all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    def __init__(
        self,
        name: str,
        state: CircuitState,
        failure_count: int,
        last_failure_time: Optional[datetime],
        retry_after: float,
    ):
        self.name = name
        self.state = state
        self.failure_count = failure_count
        self.last_failure_time = last_failure_time
        self.retry_after = retry_after

        message = """
╔════════════════════════════════════════════════════════╗
║           ⚠️  CIRCUIT BREAKER OPEN                     ║
╚════════════════════════════════════════════════════════╝

Service: {name}
State: {state.value.upper()}
Failures: {failure_count}
Retry after: {retry_after:.1f} seconds

The circuit breaker has detected repeated failures and is
preventing further attempts to avoid wasting time.

This usually means:
  • The service is temporarily unavailable
  • Network connectivity issues
  • Repository/API is down

WHAT TO DO:
  1. Wait for automatic retry (in {retry_after:.0f} seconds)
  2. Check network:  ping deb.debian.org
  3. Manual reset: vps-configurator reset circuit-breaker {name}

The system will automatically retry after the timeout period.

For more information: docs/troubleshooting/circuit-breaker.md
"""
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker(
            name="apt-repository",
            failure_threshold=3,
            timeout=60.0
        )

        result = breaker.call(install_package, 'docker-ce')
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        success_threshold: int = 1,
        timeout: float = 60.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions
        self.logger = logger or logging.getLogger(__name__)

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()

        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0

        # Thread safety
        import threading

        self._state_lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Original exception: If function fails
        """
        self.total_calls += 1

        # Check if circuit is open
        with self._state_lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerError(
                        name=self.name,
                        state=self.state,
                        failure_count=self.failure_count,
                        last_failure_time=self.last_failure_time,
                        retry_after=self._time_until_retry(),
                    )

        # Execute function
        try:
            result = func(*args, **kwargs)
            with self._state_lock:
                self._on_success()
            return result

        except self.expected_exceptions as e:
            with self._state_lock:
                self._on_failure(e)
            raise

    def _on_success(self):
        """Handle successful execution"""
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        self.logger.debug(
            f"Circuit breaker '{self.name}' recorded failure "
            f"({self.failure_count}/{self.failure_threshold}): {exception}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state reopens circuit
            self._transition_to_open()

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0

        self.logger.debug(
            f"⚠️  Circuit breaker '{self.name}' OPENED after "
            f"{self.failure_count} failures.  "
            f"Will retry after {self.timeout}s"
        )

    def _transition_to_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0

        self.logger.info(
            f"🔄 Circuit breaker '{self.name}' entering HALF-OPEN state "
            "(testing if service recovered)"
        )

    def _transition_to_closed(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0

        self.logger.info(
            f"✅ Circuit breaker '{self.name}' CLOSED "
            f"(service recovered after {self.success_count} successes)"
        )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _time_until_retry(self) -> float:
        """Calculate seconds until next retry attempt"""
        if self.last_failure_time is None:
            return 0.0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        remaining = max(0.0, self.timeout - elapsed)
        return remaining

    def reset(self):
        """Manually reset circuit breaker"""
        with self._state_lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        with self._state_lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_calls": self.total_calls,
                "total_failures": self.total_failures,
                "total_successes": self.total_successes,
                "failure_rate": self.total_failures / self.total_calls
                if self.total_calls > 0
                else 0.0,
                "last_state_change": self.last_state_change.isoformat(),
            }


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers.

    Usage:
        manager = CircuitBreakerManager()

        # Get or create circuit breaker
        breaker = manager.get_breaker('apt-repository')

        # Execute through breaker
        result = breaker.call(install_package, 'docker-ce')
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(__name__)

    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, logger=self.logger, **kwargs)
        return self._breakers[name]

    def get_all_metrics(self) -> Dict[str, dict]:
        """Get metrics for all circuit breakers"""
        return {name: breaker.get_metrics() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.reset()

    def get_open_breakers(self) -> list:
        """Get list of open circuit breakers"""
        return [
            name for name, breaker in self._breakers.items() if breaker.state == CircuitState.OPEN
        ]
