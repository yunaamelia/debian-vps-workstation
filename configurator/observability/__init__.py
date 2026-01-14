"""
Observability components for VPS Configurator.

Provides metrics, logging, dashboards, and alerting.
"""

# Import metrics (already created)
try:
    from configurator.observability.metrics import MetricsCollector, get_metrics
except ImportError:
    MetricsCollector = None
    get_metrics = None

# Import structured logging (to be created)
try:
    from configurator.observability.structured_logging import CorrelationContext, StructuredLogger
except ImportError:
    StructuredLogger = None
    CorrelationContext = None

# Import dashboard (to be created)
try:
    from configurator.observability.dashboard import InstallationDashboard, SimpleProgressReporter
except ImportError:
    InstallationDashboard = None
    SimpleProgressReporter = None

# Import alerting (to be created)
try:
    from configurator.observability.alerting import Alert, AlertManager, AlertSeverity
except ImportError:
    AlertManager = None
    AlertSeverity = None
    Alert = None

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
