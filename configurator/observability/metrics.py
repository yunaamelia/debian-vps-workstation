"""
Metrics collection and export system.

Provides Prometheus-compatible metrics for monitoring.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Base metric."""

    name: str
    metric_type: MetricType
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Counter metric - monotonically increasing value."""

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text
        self._value = 0.0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0):
        """Increment counter."""
        with self._lock:
            self._value += amount

    def get(self) -> float:
        """Get current value."""
        with self._lock:
            return self._value

    def reset(self):
        """Reset counter to zero."""
        with self._lock:
            self._value = 0.0


class Gauge:
    """Gauge metric - value that can go up and down."""

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text
        self._value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float):
        """Set gauge value."""
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0):
        """Increment gauge."""
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0):
        """Decrement gauge."""
        with self._lock:
            self._value -= amount

    def get(self) -> float:
        """Get current value."""
        with self._lock:
            return self._value


class Histogram:
    """Histogram metric - distribution of values."""

    def __init__(self, name: str, help_text: str, buckets: Optional[List[float]] = None):
        self.name = name
        self.help_text = help_text
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

        self._counts = {b: 0 for b in self.buckets}
        self._counts[float("inf")] = 0
        self._sum = 0.0
        self._count = 0
        self._lock = threading.Lock()

    def observe(self, value: float):
        """Record an observation."""
        with self._lock:
            self._sum += value
            self._count += 1

            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[bucket] += 1
            self._counts[float("inf")] += 1

    def get_buckets(self) -> Dict[float, int]:
        """Get bucket counts."""
        with self._lock:
            return self._counts.copy()

    def get_sum(self) -> float:
        """Get sum of all observations."""
        with self._lock:
            return self._sum

    def get_count(self) -> int:
        """Get total number of observations."""
        with self._lock:
            return self._count


class MetricsCollector:
    """
    Central metrics collector.

    Usage:
        metrics = MetricsCollector()

        # Create metrics
        install_counter = metrics.counter(
            "vps_installations_total",
            "Total number of installations"
        )

        # Record data
        install_counter.inc()

        # Export
        prometheus_format = metrics.export_prometheus()
    """

    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()

        # Initialize standard metrics
        self._init_standard_metrics()

    def _init_standard_metrics(self):
        """Initialize standard metrics."""
        # Installation metrics
        self.installations_total = self.counter(
            "vps_installations_total", "Total number of installations attempted"
        )

        self.installations_success = self.counter(
            "vps_installations_success_total", "Total number of successful installations"
        )

        self.installations_failed = self.counter(
            "vps_installations_failed_total", "Total number of failed installations"
        )

        self.installation_duration = self.histogram(
            "vps_installation_duration_seconds", "Installation duration in seconds"
        )

        # Module metrics
        self.module_executions_total = self.counter(
            "vps_module_executions_total", "Total module executions"
        )

        self.module_failures_total = self.counter(
            "vps_module_failures_total", "Total module failures"
        )

        self.module_duration = self.histogram(
            "vps_module_duration_seconds", "Module execution duration"
        )

        # Network metrics
        self.network_operations_total = self.counter(
            "vps_network_operations_total", "Total network operations"
        )

        self.network_failures_total = self.counter(
            "vps_network_failures_total", "Total network failures"
        )

        self.network_retries_total = self.counter(
            "vps_network_retries_total", "Total network retry attempts"
        )

        # Circuit breaker metrics
        self.circuit_breaker_opens_total = self.counter(
            "vps_circuit_breaker_opens_total", "Total circuit breaker opens"
        )

        self.circuit_breaker_state = self.gauge(
            "vps_circuit_breaker_state", "Circuit breaker state (0=closed, 1=half-open, 2=open)"
        )

        # Resource metrics
        self.memory_usage_bytes = self.gauge(
            "vps_memory_usage_bytes", "Current memory usage in bytes"
        )

        self.cpu_usage_percent = self.gauge("vps_cpu_usage_percent", "Current CPU usage percentage")

    def counter(self, name: str, help_text: str) -> Counter:
        """Create or get a counter metric."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, help_text)
            return self._counters[name]

    def gauge(self, name: str, help_text: str) -> Gauge:
        """Create or get a gauge metric."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, help_text)
            return self._gauges[name]

    def histogram(
        self, name: str, help_text: str, buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Create or get a histogram metric."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, help_text, buckets)
            return self._histograms[name]

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Export counters
        for counter in self._counters.values():
            lines.append(f"# HELP {counter.name} {counter.help_text}")
            lines.append(f"# TYPE {counter.name} counter")
            lines.append(f"{counter.name} {counter.get()}")

        # Export gauges
        for gauge in self._gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.help_text}")
            lines.append(f"# TYPE {gauge.name} gauge")
            lines.append(f"{gauge.name} {gauge.get()}")

        # Export histograms
        for histogram in self._histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.help_text}")
            lines.append(f"# TYPE {histogram.name} histogram")

            buckets = histogram.get_buckets()
            for le, count in sorted(buckets.items()):
                le_str = "+Inf" if le == float("inf") else str(le)
                lines.append(f'{histogram.name}_bucket{{le="{le_str}"}} {count}')

            lines.append(f"{histogram.name}_sum {histogram.get_sum()}")
            lines.append(f"{histogram.name}_count {histogram.get_count()}")

        return "\n".join(lines) + "\n"

    def export_json(self) -> str:
        """Export metrics in JSON format."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "counters": {name: counter.get() for name, counter in self._counters.items()},
            "gauges": {name: gauge.get() for name, gauge in self._gauges.items()},
            "histograms": {
                name: {
                    "sum": hist.get_sum(),
                    "count": hist.get_count(),
                    "buckets": {str(k): v for k, v in hist.get_buckets().items()},
                }
                for name, hist in self._histograms.items()
            },
        }

        return json.dumps(data, indent=2)

    def save_to_file(self, filepath: Path, format: str = "prometheus"):
        """Save metrics to file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "prometheus":
            content = self.export_prometheus()
        elif format == "json":
            content = self.export_json()
        else:
            raise ValueError(f"Unknown format: {format}")

        with open(filepath, "w") as f:
            f.write(content)

    def update_resource_metrics(self):
        """Update system resource metrics."""
        try:
            import psutil

            process = psutil.Process()

            # Memory
            mem_info = process.memory_info()
            self.memory_usage_bytes.set(mem_info.rss)

            # CPU
            cpu_percent = process.cpu_percent(interval=0.1)
            self.cpu_usage_percent.set(cpu_percent)

        except ImportError:
            pass  # psutil not available


# Global metrics instance
_metrics = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
