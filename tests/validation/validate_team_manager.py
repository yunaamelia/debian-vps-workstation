#!/usr/bin/env python3
"""Test Team Manager initialization"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.team_manager import TeamManager


def test_manager_initialization():
    """Test Team Manager initialization."""
    print("Team Manager Initialization Test")
    print("=" * 60)

    # Use temp directories for testing
    temp_dir = tempfile.mkdtemp()
    registry_file = Path(temp_dir) / "teams.json"
    shared_dirs = Path(temp_dir) / "projects"
    audit_log = Path(temp_dir) / "audit.log"

    # Test 1: Initialize manager
    print("\n1. Initializing Team Manager...")
    try:
        team_mgr = TeamManager(
            registry_file=registry_file,
            shared_dirs_base=shared_dirs,
            audit_log=audit_log,
        )
        print("  ✅ TeamManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Check directories
    print("\n2. Checking team directories...")

    if registry_file.parent.exists():
        print(f"  ✅ Registry directory exists: {registry_file.parent}")
    else:
        print("  ❌ Registry directory not found")
        return False

    if shared_dirs.exists():
        print(f"  ✅ Shared dirs base exists: {shared_dirs}")
    else:
        print("  ❌ Shared dirs base not found")
        return False

    # Test 3: Check team registry
    print("\n3. Checking team registry...")

    if registry_file.exists():
        print(f"  ✅ Registry file exists: {registry_file}")
        print(f"     Registered teams: {len(team_mgr.teams)}")
    else:
        print("  ℹ️  Registry file will be created on first team")

    # Test 4: Check empty state
    print("\n4. Checking initial state...")

    teams = team_mgr.list_teams()
    print(f"  Total teams: {len(teams)}")

    if len(teams) == 0:
        print("  ✅ Initial state is empty")
    else:
        print(f"  ℹ️  {len(teams)} teams already exist")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Team Manager initialization validated")
    return True


if __name__ == "__main__":
    result = test_manager_initialization()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Manager Initialization: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
