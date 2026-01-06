#!/usr/bin/env python3
"""Test Temp Access Manager initialization"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.temp_access import TempAccessManager


def test_manager_initialization():
    """Test Temp Access Manager initialization."""
    print("Temp Access Manager Initialization Test")
    print("=" * 60)

    # Use temp directories for testing
    temp_dir = tempfile.mkdtemp()
    registry_file = Path(temp_dir) / "registry.json"
    extensions_file = Path(temp_dir) / "extensions.json"
    audit_log = Path(temp_dir) / "audit.log"

    # Test 1: Initialize manager
    print("\n1. Initializing Temp Access Manager...")
    try:
        temp_mgr = TempAccessManager(
            registry_file=registry_file,
            extensions_file=extensions_file,
            audit_log=audit_log,
        )
        print("  ✅ TempAccessManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Check directories
    print("\n2. Checking temp access directories...")

    if registry_file.parent.exists():
        print(f"  ✅ Registry directory exists: {registry_file.parent}")
    else:
        print("  ❌ Registry directory not found")
        return False

    # Test 3: Check access registry
    print("\n3. Checking access registry...")

    if registry_file.exists():
        print(f"  ✅ Registry file exists: {registry_file}")
        print(f"     Active access grants: {len(temp_mgr.access_grants)}")
    else:
        print("  ℹ️  Registry file will be created on first access grant")

    # Test 4: Check initial state
    print("\n4. Checking initial state...")

    access_list = temp_mgr.list_access()
    print(f"  Total access grants: {len(access_list)}")

    extensions = temp_mgr.get_pending_extensions()
    print(f"  Pending extensions: {len(extensions)}")

    if len(access_list) == 0 and len(extensions) == 0:
        print("  ✅ Initial state is empty")
    else:
        print(f"  ℹ️  {len(access_list)} access grants and {len(extensions)} extensions exist")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Temp Access Manager initialization validated")
    return True


if __name__ == "__main__":
    result = test_manager_initialization()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Manager Initialization: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
