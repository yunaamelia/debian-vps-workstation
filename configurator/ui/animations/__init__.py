"""
Animation components for terminal UI.
High-performance, low-overhead implementations.
"""

from configurator.ui.animations.loader import (
    CompletionIndicator,
    PhaseBanner,
    TransitionEffect,
)
from configurator.ui.animations.spinner import (
    CompactProgressBar,
    EfficientSpinner,
    PercentageIndicator,
    SpinnerStyle,
)

__all__ = [
    # Spinners
    "EfficientSpinner",
    "SpinnerStyle",
    # Progress
    "CompactProgressBar",
    "PercentageIndicator",
    # Phase/Loader
    "PhaseBanner",
    "CompletionIndicator",
    "TransitionEffect",
]
