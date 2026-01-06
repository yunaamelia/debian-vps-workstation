#!/usr/bin/env python3
"""Validate team management data models and file structure"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from configurator.users.team_manager import (
    MemberRole,
    ResourceQuota,
    Team,
    TeamManager,
    TeamMember,
    TeamStatus,
)


def validate_file_structure():
    """Validate file structure."""
    print("File Structure Validation")
    print("=" * 60)

    files_to_check = [
        ("configurator/users/team_manager.py", True),
        ("tests/unit/test_team_manager.py", True),
        ("config/default.yaml", True),
    ]

    all_exist = True
    for file_path, required in files_to_check:
        full_path = Path(__file__).parent.parent.parent / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(
                f"  {'❌' if required else '⚠️ '} {file_path} {'(required)' if required else '(optional)'}"
            )
            if required:
                all_exist = False

    if all_exist:
        print("\n✅ All required files exist")
        return True
    else:
        print("\n❌ Some required files missing")
        return False


def validate_data_models():
    """Validate team management data models."""
    print("\n\nTeam Management Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(TeamStatus, "ACTIVE"), "Missing ACTIVE status"
        assert hasattr(TeamStatus, "INACTIVE"), "Missing INACTIVE status"
        assert hasattr(TeamStatus, "ARCHIVED"), "Missing ARCHIVED status"
        print("  ✅ TeamStatus enum complete")
    except AssertionError as e:
        print(f"  ❌ TeamStatus enum incomplete: {e}")
        return False

    try:
        assert hasattr(MemberRole, "LEAD"), "Missing LEAD role"
        assert hasattr(MemberRole, "MEMBER"), "Missing MEMBER role"
        print("  ✅ MemberRole enum complete")
    except AssertionError as e:
        print(f"  ❌ MemberRole enum incomplete: {e}")
        return False

    # Check TeamMember class
    print("\n2. Checking TeamMember class...")
    try:
        # Create test member
        member = TeamMember(
            username="testuser",
            role=MemberRole.LEAD,
        )

        assert hasattr(member, "username")
        assert hasattr(member, "role")
        print("  ✅ TeamMember dataclass complete")

        # Check methods
        assert hasattr(TeamMember, "to_dict"), "Missing to_dict() method"
        print("  ✅ TeamMember methods present")

    except Exception as e:
        print(f"  ❌ TeamMember validation failed: {e}")
        return False

    # Check ResourceQuota class
    print("\n3. Checking ResourceQuota class...")
    try:
        quota = ResourceQuota(disk_quota_gb=50, docker_containers=10)
        assert hasattr(ResourceQuota, "to_dict"), "Missing to_dict() method"
        print("  ✅ ResourceQuota complete")
    except Exception as e:
        print(f"  ❌ ResourceQuota validation failed: {e}")
        return False

    # Check Team class
    print("\n4. Checking Team class...")
    try:
        assert hasattr(Team, "get_lead"), "Missing get_lead() method"
        assert hasattr(Team, "get_member"), "Missing get_member() method"
        assert hasattr(Team, "to_dict"), "Missing to_dict() method"
        print("  ✅ Team methods present")
    except AssertionError as e:
        print(f"  ❌ Team incomplete: {e}")
        return False

    # Check TeamManager methods
    print("\n5. Checking TeamManager methods...")
    required_methods = [
        "create_team",
        "add_member",
        "remove_member",
        "get_team",
        "list_teams",
        "get_user_teams",
    ]

    try:
        for method in required_methods:
            assert hasattr(TeamManager, method), f"Missing method: {method}"
        print(f"  ✅ TeamManager has all {len(required_methods)} required methods")
    except AssertionError as e:
        print(f"  ❌ TeamManager incomplete: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Data models validated")
    return True


if __name__ == "__main__":
    result1 = validate_file_structure()
    result2 = validate_data_models()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"File Structure: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if result2 else '❌ FAIL'}")

    sys.exit(0 if (result1 and result2) else 1)
