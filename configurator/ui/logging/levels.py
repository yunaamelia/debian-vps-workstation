"""
Custom logging levels for the configurator.
Adds TRACE level for detailed execution tracing.
"""

import logging
from typing import Dict

# ============================================================================
# Custom TRACE Level
# ============================================================================

# TRACE level sits between NOTSET (0) and DEBUG (10)
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


def trace(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a message with TRACE level.

    TRACE is for extremely detailed execution flow information,
    typically used for debugging complex issues.
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


# Add trace method to Logger class
logging.Logger.trace = trace  # type: ignore[attr-defined]


# ============================================================================
# Level Specifications
# ============================================================================

LEVEL_SPECS: Dict[str, Dict] = {
    "TRACE": {
        "value": TRACE,
        "symbol": "└─",
        "color": "TRACE",
        "description": "Detailed execution tracing",
    },
    "DEBUG": {
        "value": logging.DEBUG,
        "symbol": "→",
        "color": "DEBUG",
        "description": "Debugging information",
    },
    "INFO": {
        "value": logging.INFO,
        "symbol": "✓",
        "color": "INFO",
        "description": "General information",
    },
    "WARNING": {
        "value": logging.WARNING,
        "symbol": "⚠",
        "color": "WARN",
        "description": "Warning messages",
    },
    "ERROR": {
        "value": logging.ERROR,
        "symbol": "✗",
        "color": "ERROR",
        "description": "Error messages",
    },
    "CRITICAL": {
        "value": logging.CRITICAL,
        "symbol": "✗",
        "color": "ERROR",
        "description": "Critical failures",
    },
}


def get_level_symbol(level_name: str) -> str:
    """Get the symbol for a log level."""
    spec = LEVEL_SPECS.get(level_name, LEVEL_SPECS.get("INFO"))
    return spec["symbol"] if spec else "?"


def get_level_color(level_name: str) -> str:
    """Get the color key for a log level."""
    spec = LEVEL_SPECS.get(level_name, LEVEL_SPECS.get("INFO"))
    return spec["color"] if spec else "INFO"


def get_level_value(level_name: str) -> int:
    """Get the numeric value for a log level."""
    spec = LEVEL_SPECS.get(level_name)
    if spec:
        return spec["value"]
    return getattr(logging, level_name, logging.INFO)
