#!/usr/bin/env python3
"""Test adding and removing members"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.users.team_manager import MemberRole, TeamManager


def test_member_management():
    """Test adding and removing members."""
    print("Member Management Test")
    print("=" * 60)

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
    test_lead = "testlead"

    # Create team first
    print("\n1. Creating test team...")
    try:
        team = team_mgr.create_team(
            name=test_team_name,
            description="Test team",
            lead=test_lead,
            created_by="test-script",
            skip_system_group=True,
        )
        print("  ✅ Test team created")
        print(f"     Members: {len(team.members)}")
    except Exception as e:
        print(f"  ❌ Team creation failed: {e}")
        return False

    # Test 2: Add member
    print("\n2. Testing member addition...")

    test_member = "testmember"

    try:
        success = team_mgr.add_member(test_team_name, test_member, skip_system=True)

        if success:
            print("  ✅ Member added successfully")

            # Verify in team
            member = team.get_member(test_member)
            if member:
                print("  ✅ Member found in team registry")
                print(f"     Username: {member.username}")
                print(f"     Role: {member.role.value}")

                if member.role == MemberRole.MEMBER:
                    print("  ✅ Member role correct")
            else:
                print("  ❌ Member not in team registry")
                return False

            # Check member count
            if len(team.members) == 2:
                print("  ✅ Member count correct (2)")
            else:
                print(f"  ⚠️  Expected 2 members, got {len(team.members)}")
        else:
            print("  ❌ Member addition failed")
            return False

    except Exception as e:
        print(f"  ❌ Member addition error: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Add duplicate member
    print("\n3. Testing duplicate member prevention...")

    success = team_mgr.add_member(test_team_name, test_member, skip_system=True)

    if not success:
        print("  ✅ Duplicate member rejected")
    else:
        print("  ⚠️  Duplicate member not rejected")

    # Test 4: Remove member
    print("\n4. Testing member removal...")

    try:
        success = team_mgr.remove_member(test_team_name, test_member, skip_system=True)

        if success:
            print("  ✅ Member removed successfully")

            # Verify removal
            member = team.get_member(test_member)
            if not member:
                print("  ✅ Member not in team registry")
            else:
                print("  ❌ Member still in team registry")
                return False

            # Check member count
            if len(team.members) == 1:
                print("  ✅ Member count correct (1)")
            else:
                print(f"  ⚠️  Expected 1 member, got {len(team.members)}")
        else:
            print("  ❌ Member removal failed")
            return False

    except Exception as e:
        print(f"  ❌ Member removal error: {e}")
        return False

    # Test 5: Lead transfer
    print("\n5. Testing lead transfer...")

    # Add new member
    new_lead = "newlead"
    team_mgr.add_member(test_team_name, new_lead, skip_system=True)

    try:
        # Remove current lead with transfer
        success = team_mgr.remove_member(
            test_team_name,
            test_lead,
            transfer_lead=new_lead,
            skip_system=True,
        )

        if success:
            print("  ✅ Lead transferred successfully")

            # Verify new lead
            lead = team.get_lead()
            if lead and lead.username == new_lead:
                print(f"  ✅ New lead assigned: {lead.username}")
            else:
                print("  ❌ Lead transfer failed")
                return False
        else:
            print("  ❌ Lead transfer failed")
            return False

    except Exception as e:
        print(f"  ❌ Lead transfer error: {e}")
        return False

    # Cleanup
    print("\n6. Cleaning up...")
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("  ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ Member management validated")
    return True


if __name__ == "__main__":
    result = test_member_management()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Member Management: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
