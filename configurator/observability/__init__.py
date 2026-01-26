"""
Observability components for VPS Configurator.

Provides metrics, logging, dashboards, and alerting.
"""

# Import metrics (already created)
try:
    from configurator.observability.metrics import MetricsCollector, get_metrics
except ImportError:
    MetricsCollector = None  # type: ignore
    get_metrics = None  # type: ignore

# Import structured logging (to be created)
try:
    from configurator.observability.structured_logging import CorrelationContext, StructuredLogger
except ImportError:
    StructuredLogger = None  # type: ignore
    CorrelationContext = None  # type: ignore

# Import dashboard (to be created)
try:
    from configurator.observability.dashboard import InstallationDashboard, SimpleProgressReporter
except ImportError:
    InstallationDashboard = None  # type: ignore
    SimpleProgressReporter = None  # type: ignore

# Import alerting (to be created)
try:
    from configurator.observability.alerting import Alert, AlertManager, AlertSeverity
except ImportError:
    AlertManager = None  # type: ignore
    AlertSeverity = None  # type: ignore
    Alert = None  # type: ignore

__all__ = [
    "MetricsCollector",
    "get_metrics",
    "StructuredLogger",
    "CorrelationContext",
    "InstallationDashboard",
    "SimpleProgressReporter",
    "AlertManager",
    "AlertSeverity",
    "Alert",
]
