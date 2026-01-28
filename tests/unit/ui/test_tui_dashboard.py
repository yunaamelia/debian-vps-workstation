"""
Test for deprecated TUI Dashboard.
This component has been replaced by the new compact UI system.
"""

import pytest

# Skip this test module - tui_dashboard deprecated
pytest.skip(
    "ui.tui_dashboard module deprecated - replaced by compact UI system", allow_module_level=True
)

try:
    from configurator.ui.tui_dashboard import InstallationDashboard
except ImportError:
    InstallationDashboard = None


@pytest.mark.asyncio
async def test_dashboard_creation():
    app = InstallationDashboard()
    assert app is not None
    # Running textual app tests requires headless environment and more setup.
    # We just verify it instantiates and has methods.
    assert hasattr(app, "add_module")
    assert hasattr(app, "update_module")
