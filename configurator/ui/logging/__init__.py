"""
Logging components for the configurator UI.
High-performance formatters and rendering utilities.
"""

from configurator.ui.logging.formatter import (
    CompactLogFormatter,
    JSONLogFormatter,
    MinimalLogFormatter,
    StructuredLogFormatter,
)
from configurator.ui.logging.levels import (
    LEVEL_SPECS,
    TRACE,
    get_level_color,
    get_level_symbol,
    get_level_value,
)
from configurator.ui.logging.renderer import (
    ANSIRenderer,
    ColorMode,
    OutputBuffer,
    TerminalInfo,
)

__all__ = [
    # Formatters
    "CompactLogFormatter",
    "JSONLogFormatter",
    "MinimalLogFormatter",
    "StructuredLogFormatter",
    # Levels
    "TRACE",
    "LEVEL_SPECS",
    "get_level_symbol",
    "get_level_color",
    "get_level_value",
    # Rendering
    "ANSIRenderer",
    "ColorMode",
    "OutputBuffer",
    "TerminalInfo",
]
