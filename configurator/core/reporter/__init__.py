from configurator.core.reporter.animations import SpinnerAnimation as SpinnerAnimation
from configurator.core.reporter.base import ReporterInterface as ReporterInterface
from configurator.core.reporter.compact_reporter import CompactReporter
from configurator.core.reporter.console import ConsoleReporter as ConsoleReporter
from configurator.core.reporter.facts import FactsDatabase as FactsDatabase
from configurator.core.reporter.rich_reporter import RichProgressReporter

# Default reporter alias
ProgressReporter = RichProgressReporter


def get_reporter(mode: str = "rich") -> ReporterInterface:
    """
    Factory function for reporter selection.

    Args:
        mode: Reporter mode. Options:
            - "rich": Full Rich TUI with progress bars (default)
            - "compact": High-performance streaming output
            - "minimal": No colors, plain text (CI/CD friendly)
            - "console": Simple console output

    Returns:
        Reporter instance implementing ReporterInterface
    """
    if mode == "compact":
        return CompactReporter(use_colors=True)
    elif mode == "minimal":
        return CompactReporter(use_colors=False)
    elif mode == "console":
        return ConsoleReporter()
    else:  # "rich" or default
        return RichProgressReporter()


__all__ = [
    "SpinnerAnimation",
    "ReporterInterface",
    "CompactReporter",
    "ConsoleReporter",
    "FactsDatabase",
    "RichProgressReporter",
    "ProgressReporter",
    "get_reporter",
]
