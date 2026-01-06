#!/usr/bin/env python3
"""Test team creation (basic tests without system operations)"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.team_manager import MemberRole, TeamManager


def test_team_creation():
    """Test creating a team (without system group operations)."""
    print("Team Creation Test")
    print("=" * 60)
    print("ℹ️  Testing without system group operations")
    print()

    # Use temp directories
    temp_dir = tempfile.mkdtemp()
    registry_file = Path(temp_dir) / "teams.json"
    shared_dirs = Path(temp_dir) / "projects"
    audit_log = Path(temp_dir) / "audit.log"

    team_mgr = TeamManager(
        registry_file=registry_file,
        shared_dirs_base=shared_dirs,
        audit_log=audit_log,
    )

    test_team_name = "testteam"
    test_user = "testuser"

    print(f"Test team: {test_team_name}")
    print(f"Test lead: {test_user}\n")

    # Test 1: Create team
    print("1. Creating team...")
    try:
        team = team_mgr.create_team(
            name=test_team_name,
            description="Test team for validation",
            lead=test_user,
            created_by="test-script",
            disk_quota_gb=10,
            docker_containers=5,
            skip_system_group=True,  # Skip system operations for testing
        )

        print("  ✅ Team created successfully")
        print(f"     Team ID: {team.team_id}")
        print(f"     Name: {team.name}")
        print(f"     Description: {team.description}")
        print(f"     GID: {team.gid}")
        print(f"     Shared dir: {team.shared_directory}")

    except Exception as e:
        print(f"  ❌ Team creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Verify shared directory
    print("\n2. Verifying shared directory...")

    if team.shared_directory.exists():
        print(f"  ✅ Shared directory exists: {team.shared_directory}")

        # Check README
        readme = team.shared_directory / "README.md"
        if readme.exists():
            print("  ✅ README.md created")

            # Check content
            content = readme.read_text()
            if test_team_name in content:
                print("  ✅ README contains team name")
        else:
            print("  ⚠️  README.md not found")
    else:
        print("  ❌ Shared directory not created")
        return False

    # Test 3: Verify team lead
    print("\n3. Verifying team lead...")

    lead = team.get_lead()

    if lead:
        print(f"  ✅ Team lead assigned: {lead.username}")

        if lead.username == test_user:
            print("  ✅ Correct lead")
        else:
            print(f"  ❌ Wrong lead (expected {test_user}, got {lead.username})")
            return False

        if lead.role == MemberRole.LEAD:
            print("  ✅ Lead role correct")
    else:
        print("  ❌ No team lead found")
        return False

    # Test 4: Verify team in registry
    print("\n4. Verifying team registry...")

    retrieved_team = team_mgr.get_team(test_team_name)

    if retrieved_team:
        print("  ✅ Team found in registry")
        print(f"     Members: {len(retrieved_team.members)}")
    else:
        print("  ❌ Team not in registry")
        return False

    # Test 5: Verify resource quotas
    print("\n5. Verifying resource quotas...")

    if team.quotas:
        print("  ✅ Quotas configured")
        print(f"     Disk quota: {team.quotas.disk_quota_gb} GB")
        print(f"     Container limit: {team.quotas.docker_containers}")

        if team.quotas.disk_quota_gb == 10:
            print("  ✅ Disk quota correct")

        if team.quotas.docker_containers == 5:
            print("  ✅ Container limit correct")
    else:
        print("  ⚠️  No quotas configured")

    # Test 6: Verify audit log
    print("\n6. Verifying audit log...")

    if audit_log.exists():
        print(f"  ✅ Audit log created: {audit_log}")

        with open(audit_log, "r") as f:
            content = f.read()

        if "create_team" in content and test_team_name in content:
            print("  ✅ Team creation logged")
    else:
        print("  ⚠️  Audit log not found")

    # Cleanup
    print("\n7. Cleaning up...")
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Team creation validated")
    return True


if __name__ == "__main__":
    result = test_team_creation()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Team Creation: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
