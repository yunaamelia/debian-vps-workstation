# UI Performance & Design Specification

## Overview
This document details the performance optimization strategy for the VPS Configurator UI, transitioning from a resource-intensive rich TUI to a high-performance compact interface.

## Performance Targets

| Metric | Legacy (Rich TUI) | Optimized (Compact) | Improvement |
|--------|-------------------|---------------------|-------------|
| **Frame Render Time** | ~40-80ms | < 2ms | 20x-40x |
| **CPU Usage (Idle)** | 5-15% | < 0.1% | ~99% |
| **Memory Footprint** | ~35MB | < 5MB | ~85% |
| **Log Throughput** | ~200 lines/sec | > 2000 lines/sec | 10x |
| **Startup Overhead** | ~150ms | < 10ms | 15x |

## Architecture Decisions

### 1. Minimal Animation System
Instead of calculating complex progress bars per frame:
- **Pre-rendered Spinners**: Frames are constant strings, accessed by index.
- **Math-based Selection**: `frame_idx = (time * fps) % count`. No state mutation.
- **4 FPS Cap**: Human-perceivable movement without wasting cycles.
- **Multiple Styles**: ASCII, Braille, Dots, Line, Arrows, Bounce.

### 2. Compact Logging
- **Streaming Output**: No TUI redraws. Standard stdout appending.
- **Structured Format**: `HH:MM:SS ✓ [module] [duration] Message`
- **Zero-Copy Formatting**: Minimal string manipulation using f-strings.
- **Four Formatters**: Compact, Structured, JSON, Minimal.

### 3. Progressive Disclosure
- **Default**: INFO level, single line per major action.
- **Verbose**: DEBUG level, detailed step info.
- **Errors**: Always full detail with context.

## Implementation Components

### Animation System (`configurator/ui/animations/`)

| Component | File | Purpose |
|-----------|------|---------|
| `EfficientSpinner` | `spinner.py` | 4fps, configurable styles |
| `SpinnerStyle` | `spinner.py` | Enum: ASCII, BRAILLE, DOTS, LINE, etc. |
| `CompactProgressBar` | `spinner.py` | `[████░░░░░] 50%` format |
| `PercentageIndicator` | `spinner.py` | Minimal `75%` display |
| `PhaseBanner` | `loader.py` | Phase headers and transitions |
| `CompletionIndicator` | `loader.py` | Success/failure markers |
| `TransitionEffect` | `loader.py` | Visual separators |

### Logging System (`configurator/ui/logging/`)

| Component | File | Purpose |
|-----------|------|---------|
| `CompactLogFormatter` | `formatter.py` | Single-line, aligned output |
| `StructuredLogFormatter` | `formatter.py` | Multi-line with details |
| `JSONLogFormatter` | `formatter.py` | Machine-readable JSON |
| `MinimalLogFormatter` | `formatter.py` | CI/CD-friendly `[LEVEL] msg` |
| `TRACE` | `levels.py` | Custom level (5) for detailed tracing |
| `ANSIRenderer` | `renderer.py` | Direct ANSI escape output |
| `OutputBuffer` | `renderer.py` | Batched writes for throughput |

### Reporter System (`configurator/core/reporter/`)

| Component | File | Purpose |
|-----------|------|---------|
| `CompactReporter` | `compact_reporter.py` | Streaming, append-only output |
| `RichProgressReporter` | `rich_reporter.py` | Full Rich TUI (optimized 4fps) |
| `get_reporter()` | `__init__.py` | Factory function for mode selection |

## User Guide

### Modes
- `compact` (Default): Fast, clean, professional. Single line per module.
- `verbose`: Traditional detail for debugging with Rich progress bars.
- `minimal`: Pure text for CI/CD pipelines (no colors, no unicode).
- `json`: Structured JSON for machine parsing.

### Usage
```bash
# Default Compact Mode (High Performance)
vps-configurator install --profile beginner

# Verbose Mode (Rich TUI)
vps-configurator install --profile beginner --ui-mode verbose

# CI/CD Mode (Text only, no colors)
vps-configurator install --ui-mode minimal --non-interactive

# Machine Parsing (JSON logs)
vps-configurator install --ui-mode json --non-interactive

# Dry-run with compact output
vps-configurator install --profile beginner --dry-run
```

### Environment Variables
- `VPS_UI_MODE`: Set default UI mode (`compact`, `verbose`, `minimal`, `json`)
- `NO_COLOR`: Disable color output when set
- `FORCE_COLOR`: Force color output even in non-TTY

## Theme Configuration

The theme system (`configurator/ui/theme.py`) provides:
- **Colors**: ANSI escape codes for direct terminal output
- **Symbols**: Unicode with ASCII fallbacks
- **Animation Timings**: FPS constants for spinners and progress
- **Spinner Frames**: Pre-defined frame sets for different styles
- **Progress Characters**: Fill/empty characters for progress bars

### Extending the Theme
```python
from configurator.ui import Theme

# Get spinner frames for a style
frames = Theme.get_spinner_frames("BRAILLE")

# Colorize text
colored = Theme.colorize("Success!", "SUCCESS")

# Check capabilities
if Theme.supports_unicode():
    print(Theme.get_symbol("CHECK"))
else:
    print(Theme.get_symbol("CHECK", ascii_only=True))
```

## API Reference

### EfficientSpinner
```python
from configurator.ui import EfficientSpinner, SpinnerStyle

spinner = EfficientSpinner(
    style=SpinnerStyle.BRAILLE,  # Animation style
    fps=4.0,                      # Frames per second
    auto_detect=True,             # Auto-select based on terminal
)

frame = spinner.render()          # Get current frame
line = spinner.render_with_message("Loading...")
```

### CompactReporter
```python
from configurator.core.reporter import CompactReporter, get_reporter

# Direct instantiation
reporter = CompactReporter(use_colors=True, show_timestamp=True)

# Or use factory
reporter = get_reporter("compact")  # or "minimal", "rich", "console"

# Usage
reporter.start("Installation")
reporter.start_phase("docker", total_steps=100)
reporter.update("pulling images...", module="docker")
reporter.complete_phase(success=True, module="docker")
reporter.show_summary({"docker": True})
```

### Custom Log Formatting
```python
import logging
from configurator.ui.logging import CompactLogFormatter, TRACE

handler = logging.StreamHandler()
handler.setFormatter(CompactLogFormatter(use_colors=True))

logger = logging.getLogger("my_module")
logger.addHandler(handler)
logger.setLevel(TRACE)

# Use custom TRACE level
logger.trace("Detailed trace message")
logger.info("Operation complete", extra={"duration_ms": 150})
```
