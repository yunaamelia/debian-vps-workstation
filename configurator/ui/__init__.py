"""
User Interface components for VPS Configurator.
High-performance terminal UI with compact logging and efficient animations.
"""

from configurator.ui.animations import (
    CompactProgressBar,
    CompletionIndicator,
    EfficientSpinner,
    PercentageIndicator,
    PhaseBanner,
    SpinnerStyle,
    TransitionEffect,
)
from configurator.ui.layout.console import ConsoleManager, UIMode
from configurator.ui.logging import (
    TRACE,
    CompactLogFormatter,
    JSONLogFormatter,
    MinimalLogFormatter,
    StructuredLogFormatter,
)
from configurator.ui.theme import Theme

__all__ = [
    # Theme
    "Theme",
    # Layout
    "UIMode",
    "ConsoleManager",
    # Animations
    "EfficientSpinner",
    "SpinnerStyle",
    "CompactProgressBar",
    "PercentageIndicator",
    "PhaseBanner",
    "CompletionIndicator",
    "TransitionEffect",
    # Logging
    "CompactLogFormatter",
    "JSONLogFormatter",
    "MinimalLogFormatter",
    "StructuredLogFormatter",
    "TRACE",
]
