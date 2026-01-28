# tests/manual/test_tui_interactive.py
"""
Manual TUI interactive test.
Requires the deprecated tui_dashboard module which has been replaced by
the new compact UI system. This test is skipped by default.
"""

import asyncio
import sys

import pytest

# Skip this test module - tui_dashboard has been replaced by compact UI
pytest.skip(
    "tui_dashboard module deprecated - replaced by compact UI system", allow_module_level=True
)

# The following imports would fail without the skip above
try:
    from configurator.ui.tui_dashboard import InstallationDashboard
except ImportError:
    InstallationDashboard = None

# Check textual availability
try:
    import textual  # noqa: F401
except ImportError:
    print("❌ Textual not installed. Skipping TUI test.")
    sys.exit(0)


async def main():
    print("🚀 Starting TUI Interactive Test...")
    app = InstallationDashboard()

    # Add modules
    app.add_module("docker")
    app.add_module("python")
    app.add_module("nodejs")

    # Simulate progress
    async def simulate():
        await asyncio.sleep(1)
        app.update_module("docker", status="running", progress=25, step="Checking prerequisites")

        await asyncio.sleep(1)
        app.update_module("docker", status="running", progress=50, step="Downloading images")
        app.update_module("python", status="running", progress=10, step="Installing pip")

        # Update resources
        app.update_resources(cpu=45.5, ram=60.2, disk=30.1)
        app.log("Docker installation progressing...", "info")

        await asyncio.sleep(1)
        app.update_module("docker", status="completed", progress=100, step="Done")
        app.update_overall_progress(33)
        app.log("Docker installation finished", "success")

        await asyncio.sleep(2)
        app.exit()

    # Schedule simulation
    asyncio.create_task(simulate())

    # Run app
    await app.run_async()
    print("✅ TUI Test Completed")


if __name__ == "__main__":
    asyncio.run(main())
