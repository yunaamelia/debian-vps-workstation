#!/usr/bin/env python3
"""Test activity monitor database initialization"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3

from configurator.users.activity_monitor import ActivityMonitor


def test_database_initialization():
    """Test activity monitor database initialization."""
    print("Activity Monitor Database Initialization Test")
    print("=" * 60)

    # Use temp database for testing
    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "activity.db"
    audit_log = Path(temp_dir) / "audit.log"

    # Test 1: Initialize monitor
    print("\n1. Initializing Activity Monitor...")
    try:
        monitor = ActivityMonitor(
            db_file=db_file,
            audit_log=audit_log,
        )
        print("  ✅ ActivityMonitor initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Check database file
    print("\n2. Checking database file...")

    if db_file.exists():
        print(f"  ✅ Database file exists: {db_file}")

        # Check file size
        size = db_file.stat().st_size
        print(f"     Size: {size} bytes")
    else:
        print("  ❌ Database file not created")
        return False

    # Test 3: Verify database schema
    print("\n3. Verifying database schema...")

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ["activity_events", "ssh_sessions", "anomalies"]

        for table in expected_tables:
            if table in tables:
                print(f"  ✅ Table exists: {table}")
            else:
                print(f"  ❌ Table missing: {table}")
                return False

        # Check activity_events schema
        cursor.execute("PRAGMA table_info(activity_events)")
        columns = [row[1] for row in cursor.fetchall()]

        expected_columns = ["id", "user", "activity_type", "timestamp", "source_ip", "command"]

        for col in expected_columns:
            if col in columns:
                print(f"     ✅ Column exists: {col}")
            else:
                print(f"     ⚠️  Column missing: {col}")

        conn.close()

    except Exception as e:
        print(f"  ❌ Schema verification failed: {e}")
        return False

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Database initialization validated")
    return True


if __name__ == "__main__":
    result = test_database_initialization()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Database Initialization: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
