"""
Test for deprecated Textual UI components.
These components have been replaced by the new compact UI system.
"""

import pytest

# Skip this test module - components module deprecated
pytest.skip(
    "ui.components module deprecated - replaced by compact UI system", allow_module_level=True
)

try:
    from configurator.ui.components import ActivityLog, ModuleCard, OverallProgress, ResourceGauge
except ImportError:
    ActivityLog = ModuleCard = OverallProgress = ResourceGauge = None


def test_module_card_instantiation():
    card = ModuleCard()
    assert card is not None
    # Reactive properties check
    assert card.status == "pending"


def test_resource_gauge_instantiation():
    gauge = ResourceGauge()
    assert gauge is not None


def test_activity_log_instantiation():
    log = ActivityLog()
    assert log is not None


def test_overall_progress_instantiation():
    prog = OverallProgress()
    assert prog is not None
