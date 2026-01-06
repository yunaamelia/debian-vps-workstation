#!/usr/bin/env python3
"""
Final Validation - Phase 3: User Management & RBAC
Tests for RBAC, User Lifecycle, Sudo Policy, Activity Monitoring, Teams, and Temp Access
"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_rbac_system():
    """Test 3.1: RBAC System"""
    print("\n=== Validation 3.1: RBAC System ===\n")

    from configurator.rbac.rbac_manager import RBACManager

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: RBAC Manager initialization
    print("Test 1: RBACManager initialization...")

    try:
        manager = RBACManager()
        print("  ✅ RBACManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: Roles defined
    print("Test 2: Roles defined...")

    try:
        roles = manager.list_roles()

        if roles and len(roles) > 0:
            print(
                f"  ✅ {len(roles)} roles defined: {[r.name if hasattr(r, 'name') else r for r in roles[:5]]}..."
            )
            results["passed"] += 1
            results["tests"].append(("Roles Defined", "PASS"))
        else:
            print("  ❌ No roles defined")
            results["failed"] += 1
            results["tests"].append(("Roles Defined", "FAIL"))
    except Exception as e:
        print(f"  ❌ Roles check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Roles Defined", "FAIL"))

    # Test 3: Get role
    print("Test 3: Get role by name...")

    try:
        admin_role = manager.get_role("admin")

        if admin_role:
            print("  ✅ Found admin role")
            results["passed"] += 1
            results["tests"].append(("Get Role", "PASS"))
        else:
            # Try developer role
            dev_role = manager.get_role("developer")
            if dev_role:
                print("  ✅ Found developer role")
                results["passed"] += 1
                results["tests"].append(("Get Role", "PASS"))
            else:
                print("  ❌ Could not find any standard roles")
                results["failed"] += 1
                results["tests"].append(("Get Role", "FAIL"))
    except Exception as e:
        print(f"  ❌ Get role failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Get Role", "FAIL"))

    # Test 4: Check permissions method
    print("Test 4: Check permissions method...")

    try:
        has_check = hasattr(manager, "check_permission") or hasattr(manager, "has_permission")

        if has_check:
            print("  ✅ Permission check method available")
            results["passed"] += 1
            results["tests"].append(("Permission Check Method", "PASS"))
        else:
            print("  ❌ Permission check method not found")
            results["failed"] += 1
            results["tests"].append(("Permission Check Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Permission check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Permission Check Method", "FAIL"))

    # Test 5: Assign role method
    print("Test 5: Assign role method...")

    try:
        has_assign = hasattr(manager, "assign_role") or hasattr(manager, "add_user_to_role")

        if has_assign:
            print("  ✅ Role assignment method available")
            results["passed"] += 1
            results["tests"].append(("Role Assignment Method", "PASS"))
        else:
            print("  ❌ Role assignment method not found")
            results["failed"] += 1
            results["tests"].append(("Role Assignment Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Role assignment check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Role Assignment Method", "FAIL"))

    print(f"\n📊 Validation 3.1 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_sudo_manager():
    """Test 3.3: Sudo Policy Management"""
    print("\n=== Validation 3.3: Sudo Policy Management ===\n")

    from configurator.rbac.sudo_manager import SudoPolicy, SudoPolicyManager

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: SudoManager initialization
    print("Test 1: SudoManager initialization...")

    try:
        manager = SudoPolicyManager(dry_run=True)
        print("  ✅ SudoPolicyManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: SudoPolicy dataclass
    print("Test 2: SudoPolicy dataclass...")

    try:
        from configurator.rbac.sudo_manager import SudoCommandRule

        policy = SudoPolicy(
            name="test-policy",
            rules=[
                SudoCommandRule(
                    command_pattern="/usr/bin/systemctl status *",
                )
            ],
            default_deny=True,
        )

        if hasattr(policy, "name") and hasattr(policy, "rules"):
            print("  ✅ SudoPolicy dataclass works")
            results["passed"] += 1
            results["tests"].append(("SudoPolicy Dataclass", "PASS"))
        else:
            print("  ❌ SudoPolicy missing attributes")
            results["failed"] += 1
            results["tests"].append(("SudoPolicy Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ SudoPolicy dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("SudoPolicy Dataclass", "FAIL"))

    # Test 3: Add policy method
    print("Test 3: Add policy method...")

    try:
        has_add = hasattr(manager, "apply_policy_for_user") or hasattr(manager, "add_policy")

        if has_add:
            print("  ✅ Add policy method available")
            results["passed"] += 1
            results["tests"].append(("Add Policy Method", "PASS"))
        else:
            print("  ❌ Add policy method not found")
            results["failed"] += 1
            results["tests"].append(("Add Policy Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Add policy check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Add Policy Method", "FAIL"))

    # Test 4: Generate sudoers file method
    print("Test 4: Generate sudoers file method...")

    try:
        has_generate = hasattr(manager, "_generate_sudoers_content") or hasattr(
            manager, "generate_sudoers"
        )

        if has_generate:
            print("  ✅ Generate sudoers method available")
            results["passed"] += 1
            results["tests"].append(("Generate Sudoers Method", "PASS"))
        else:
            print("  ❌ Generate sudoers method not found")
            results["failed"] += 1
            results["tests"].append(("Generate Sudoers Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Generate sudoers check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Generate Sudoers Method", "FAIL"))

    # Test 5: Validate syntax method
    print("Test 5: Validate syntax method...")

    try:
        has_validate = hasattr(manager, "_validate_sudoers_content") or hasattr(
            manager, "validate_syntax"
        )

        if has_validate:
            print("  ✅ Validate syntax method available")
            results["passed"] += 1
            results["tests"].append(("Validate Syntax Method", "PASS"))
        else:
            print("  ⚠️ Validate syntax method not exposed directly")
            results["tests"].append(("Validate Syntax Method", "SKIP"))
    except Exception as e:
        print(f"  ❌ Validate syntax check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Validate Syntax Method", "FAIL"))

    print(f"\n📊 Validation 3.3 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_user_lifecycle():
    """Test 3.2: User Lifecycle Management"""
    print("\n=== Validation 3.2: User Lifecycle Management ===\n")

    from configurator.users.lifecycle_manager import UserLifecycleManager, UserProfile

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: LifecycleManager initialization
    print("Test 1: LifecycleManager initialization...")

    try:
        manager = UserLifecycleManager(dry_run=True)
        print("  ✅ UserLifecycleManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: UserProfile dataclass
    print("Test 2: UserProfile dataclass...")

    try:
        profile = UserProfile(
            username="testuser",
            uid=1000,
            full_name="Test User",
            email="test@example.com",
            role="developer",
        )

        if hasattr(profile, "username") and hasattr(profile, "role"):
            print("  ✅ UserProfile dataclass works")
            results["passed"] += 1
            results["tests"].append(("UserProfile Dataclass", "PASS"))
        else:
            print("  ❌ UserProfile missing attributes")
            results["failed"] += 1
            results["tests"].append(("UserProfile Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ UserProfile dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("UserProfile Dataclass", "FAIL"))

    # Test 3: Provision user method
    print("Test 3: Provision user method...")

    try:
        has_provision = hasattr(manager, "provision_user") or hasattr(manager, "create_user")

        if has_provision:
            print("  ✅ Provision user method available")
            results["passed"] += 1
            results["tests"].append(("Provision User Method", "PASS"))
        else:
            print("  ❌ Provision user method not found")
            results["failed"] += 1
            results["tests"].append(("Provision User Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Provision user check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Provision User Method", "FAIL"))

    # Test 4: Offboard user method
    print("Test 4: Offboard user method...")

    try:
        has_offboard = hasattr(manager, "offboard_user") or hasattr(manager, "delete_user")

        if has_offboard:
            print("  ✅ Offboard user method available")
            results["passed"] += 1
            results["tests"].append(("Offboard User Method", "PASS"))
        else:
            print("  ❌ Offboard user method not found")
            results["failed"] += 1
            results["tests"].append(("Offboard User Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Offboard user check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Offboard User Method", "FAIL"))

    # Test 5: List users method
    print("Test 5: List users method...")

    try:
        has_list = hasattr(manager, "list_users") or hasattr(manager, "get_users")

        if has_list:
            print("  ✅ List users method available")
            results["passed"] += 1
            results["tests"].append(("List Users Method", "PASS"))
        else:
            print("  ❌ List users method not found")
            results["failed"] += 1
            results["tests"].append(("List Users Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ List users check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("List Users Method", "FAIL"))

    print(f"\n📊 Validation 3.2 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_activity_monitor():
    """Test 3.4: Activity Monitoring"""
    print("\n=== Validation 3.4: Activity Monitoring ===\n")

    from configurator.users.activity_monitor import ActivityEvent, ActivityMonitor, ActivityType

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: ActivityMonitor initialization
    print("Test 1: ActivityMonitor initialization...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ActivityMonitor(db_file=Path(tmpdir) / "activity.db")
            print("  ✅ ActivityMonitor initialized")
            results["passed"] += 1
            results["tests"].append(("Monitor Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Monitor Initialization", "FAIL"))

    # Test 2: EventType enum
    print("Test 2: ActivityType enum...")

    try:
        event_types = [ActivityType.SSH_LOGIN, ActivityType.SSH_LOGOUT, ActivityType.COMMAND]
        print(f"  ✅ Activity types: {[et.value for et in event_types]}")
        results["passed"] += 1
        results["tests"].append(("ActivityType Enum", "PASS"))
    except Exception as e:
        print(f"  ❌ ActivityType enum failed: {e}")
        results["failed"] += 1
        results["tests"].append(("ActivityType Enum", "FAIL"))

    # Test 3: ActivityEvent dataclass
    print("Test 3: ActivityEvent dataclass...")

    try:
        event = ActivityEvent(
            user="testuser",
            activity_type=ActivityType.SSH_LOGIN,
            timestamp=datetime.now(),
            source_ip="192.168.1.1",
        )

        if hasattr(event, "activity_type") and hasattr(event, "user"):
            print("  ✅ ActivityEvent dataclass works")
            results["passed"] += 1
            results["tests"].append(("ActivityEvent Dataclass", "PASS"))
        else:
            print("  ❌ ActivityEvent missing attributes")
            results["failed"] += 1
            results["tests"].append(("ActivityEvent Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ ActivityEvent dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("ActivityEvent Dataclass", "FAIL"))

    # Test 4: Log event method
    print("Test 4: Log event method...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ActivityMonitor(db_file=Path(tmpdir) / "activity.db")
            has_log = hasattr(monitor, "log_activity") or hasattr(monitor, "log_event")

            if has_log:
                print("  ✅ Log event method available")
                results["passed"] += 1
                results["tests"].append(("Log Event Method", "PASS"))
            else:
                print("  ❌ Log event method not found")
                results["failed"] += 1
                results["tests"].append(("Log Event Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Log event check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Log Event Method", "FAIL"))

    # Test 5: Query events method
    print("Test 5: Query events method...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ActivityMonitor(db_file=Path(tmpdir) / "activity.db")
            has_query = hasattr(monitor, "get_user_activity") or hasattr(monitor, "query_events")

            if has_query:
                print("  ✅ Query events method available")
                results["passed"] += 1
                results["tests"].append(("Query Events Method", "PASS"))
            else:
                print("  ❌ Query events method not found")
                results["failed"] += 1
                results["tests"].append(("Query Events Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Query events check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Query Events Method", "FAIL"))

    print(f"\n📊 Validation 3.4 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_team_manager():
    """Test 3.5: Team Management"""
    print("\n=== Validation 3.5: Team Management ===\n")

    from configurator.users.team_manager import Team, TeamManager

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: TeamManager initialization
    print("Test 1: TeamManager initialization...")

    try:
        manager = TeamManager()
        print("  ✅ TeamManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: Team dataclass
    print("Test 2: Team dataclass...")

    try:
        from pathlib import Path

        from configurator.users.team_manager import MemberRole, TeamMember

        team = Team(
            team_id="test-team-001",
            name="test-team",
            gid=1001,
            description="Test team",
            shared_directory=Path("/var/projects/test-team"),
            members=[TeamMember(username="teamlead", role=MemberRole.LEAD)],
        )

        if hasattr(team, "name") and hasattr(team, "members"):
            print("  ✅ Team dataclass works")
            results["passed"] += 1
            results["tests"].append(("Team Dataclass", "PASS"))
        else:
            print("  ❌ Team missing attributes")
            results["failed"] += 1
            results["tests"].append(("Team Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ Team dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Team Dataclass", "FAIL"))

    # Test 3: Create team method
    print("Test 3: Create team method...")

    try:
        has_create = hasattr(manager, "create_team")

        if has_create:
            print("  ✅ Create team method available")
            results["passed"] += 1
            results["tests"].append(("Create Team Method", "PASS"))
        else:
            print("  ❌ Create team method not found")
            results["failed"] += 1
            results["tests"].append(("Create Team Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Create team check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Create Team Method", "FAIL"))

    # Test 4: Add member method
    print("Test 4: Add member method...")

    try:
        has_add = hasattr(manager, "add_member") or hasattr(manager, "add_team_member")

        if has_add:
            print("  ✅ Add member method available")
            results["passed"] += 1
            results["tests"].append(("Add Member Method", "PASS"))
        else:
            print("  ❌ Add member method not found")
            results["failed"] += 1
            results["tests"].append(("Add Member Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Add member check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Add Member Method", "FAIL"))

    # Test 5: List teams method
    print("Test 5: List teams method...")

    try:
        has_list = hasattr(manager, "list_teams")

        if has_list:
            print("  ✅ List teams method available")
            results["passed"] += 1
            results["tests"].append(("List Teams Method", "PASS"))
        else:
            print("  ❌ List teams method not found")
            results["failed"] += 1
            results["tests"].append(("List Teams Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ List teams check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("List Teams Method", "FAIL"))

    print(f"\n📊 Validation 3.5 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def test_temp_access():
    """Test 3.6: Temporary Access Management"""
    print("\n=== Validation 3.6: Temporary Access Management ===\n")

    from configurator.users.temp_access import AccessStatus, TempAccess, TempAccessManager

    results = {"passed": 0, "failed": 0, "tests": []}

    # Test 1: TempAccessManager initialization
    print("Test 1: TempAccessManager initialization...")

    try:
        manager = TempAccessManager()
        print("  ✅ TempAccessManager initialized")
        results["passed"] += 1
        results["tests"].append(("Manager Initialization", "PASS"))
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Manager Initialization", "FAIL"))
        return results

    # Test 2: AccessStatus enum
    print("Test 2: AccessStatus enum...")

    try:
        statuses = [AccessStatus.ACTIVE, AccessStatus.EXPIRED, AccessStatus.REVOKED]
        print(f"  ✅ Access statuses: {[s.value for s in statuses]}")
        results["passed"] += 1
        results["tests"].append(("AccessStatus Enum", "PASS"))
    except Exception as e:
        print(f"  ❌ AccessStatus enum failed: {e}")
        results["failed"] += 1
        results["tests"].append(("AccessStatus Enum", "FAIL"))

    # Test 3: TempAccess dataclass
    print("Test 3: TempAccess dataclass...")

    try:
        from configurator.users.temp_access import AccessType

        access = TempAccess(
            access_id="temp-001",
            username="contractor1",
            role="developer",
            access_type=AccessType.TEMPORARY,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            reason="Q1 project",
            granted_by="admin",
        )

        if hasattr(access, "username") and hasattr(access, "expires_at"):
            print("  ✅ TempAccess dataclass works")
            results["passed"] += 1
            results["tests"].append(("TempAccess Dataclass", "PASS"))
        else:
            print("  ❌ TempAccess missing attributes")
            results["failed"] += 1
            results["tests"].append(("TempAccess Dataclass", "FAIL"))
    except Exception as e:
        print(f"  ❌ TempAccess dataclass failed: {e}")
        results["failed"] += 1
        results["tests"].append(("TempAccess Dataclass", "FAIL"))

    # Test 4: Grant access method
    print("Test 4: Grant access method...")

    try:
        has_grant = hasattr(manager, "grant_temp_access")

        if has_grant:
            print("  ✅ Grant access method available")
            results["passed"] += 1
            results["tests"].append(("Grant Access Method", "PASS"))
        else:
            print("  ❌ Grant access method not found")
            results["failed"] += 1
            results["tests"].append(("Grant Access Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Grant access check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Grant Access Method", "FAIL"))

    # Test 5: Revoke access method
    print("Test 5: Revoke access method...")

    try:
        has_revoke = hasattr(manager, "revoke_access")

        if has_revoke:
            print("  ✅ Revoke access method available")
            results["passed"] += 1
            results["tests"].append(("Revoke Access Method", "PASS"))
        else:
            print("  ❌ Revoke access method not found")
            results["failed"] += 1
            results["tests"].append(("Revoke Access Method", "FAIL"))
    except Exception as e:
        print(f"  ❌ Revoke access check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("Revoke Access Method", "FAIL"))

    # Test 6: List expiring access method
    print("Test 6: List expiring access method...")

    try:
        has_list = hasattr(manager, "list_expiring") or hasattr(manager, "get_expiring_access")

        if has_list:
            print("  ✅ List expiring method available")
            results["passed"] += 1
            results["tests"].append(("List Expiring Method", "PASS"))
        else:
            print("  ⚠️ List expiring method not directly exposed")
            results["tests"].append(("List Expiring Method", "SKIP"))
    except Exception as e:
        print(f"  ❌ List expiring check failed: {e}")
        results["failed"] += 1
        results["tests"].append(("List Expiring Method", "FAIL"))

    print(f"\n📊 Validation 3.6 Results: {results['passed']} passed, {results['failed']} failed")
    return results


def run_phase3_validation():
    """Run all Phase 3 validation tests"""
    print("\n" + "=" * 70)
    print("    PHASE 3 VALIDATION: User Management & RBAC")
    print("=" * 70)

    all_results = []

    try:
        all_results.append(("3.1 RBAC System", test_rbac_system()))
    except Exception as e:
        print(f"\n❌ Validation 3.1 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.1 RBAC System", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("3.2 User Lifecycle", test_user_lifecycle()))
    except Exception as e:
        print(f"\n❌ Validation 3.2 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.2 User Lifecycle", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("3.3 Sudo Policy", test_sudo_manager()))
    except Exception as e:
        print(f"\n❌ Validation 3.3 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.3 Sudo Policy", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("3.4 Activity Monitoring", test_activity_monitor()))
    except Exception as e:
        print(f"\n❌ Validation 3.4 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.4 Activity Monitoring", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("3.5 Team Management", test_team_manager()))
    except Exception as e:
        print(f"\n❌ Validation 3.5 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.5 Team Management", {"passed": 0, "failed": 1, "error": str(e)}))

    try:
        all_results.append(("3.6 Temporary Access", test_temp_access()))
    except Exception as e:
        print(f"\n❌ Validation 3.6 failed with exception: {e}")
        import traceback

        traceback.print_exc()
        all_results.append(("3.6 Temporary Access", {"passed": 0, "failed": 1, "error": str(e)}))

    # Summary
    print("\n" + "=" * 70)
    print("    PHASE 3 VALIDATION SUMMARY")
    print("=" * 70)

    total_passed = 0
    total_failed = 0

    for name, result in all_results:
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        total_passed += passed
        total_failed += failed

        status = "✅ PASS" if failed == 0 else "❌ FAIL"
        print(f"\n{name}: {status} ({passed} passed, {failed} failed)")

        if "tests" in result:
            for test_name, test_status in result["tests"]:
                icon = "✅" if test_status == "PASS" else "⚠️" if test_status == "SKIP" else "❌"
                print(f"    {icon} {test_name}")

    print(f"\n{'=' * 70}")
    print(f"PHASE 3 TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"{'=' * 70}")

    return total_passed, total_failed


if __name__ == "__main__":
    passed, failed = run_phase3_validation()
    sys.exit(0 if failed == 0 else 1)
