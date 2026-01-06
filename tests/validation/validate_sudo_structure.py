#!/usr/bin/env python3
"""Validate sudo policy data models and file structure"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from configurator.rbac.sudo_manager import (
    CommandRisk,
    MFARequirement,
    PasswordRequirement,
    SudoCommandRule,
    SudoPolicy,
    SudoPolicyManager,
)


def validate_file_structure():
    """Validate file structure"""
    print("File Structure Validation")
    print("=" * 60)

    files_to_check = [
        ("configurator/rbac/sudo_manager.py", True),
        ("tests/unit/test_sudo_manager.py", True),
        ("tests/integration/test_sudo_policies.py", True),
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
    """Validate sudo policy data models"""
    print("\n\nSudo Policy Data Model Validation")
    print("=" * 60)

    # Check enums
    print("\n1. Checking enums...")
    try:
        assert hasattr(PasswordRequirement, "NONE"), "Missing NONE password requirement"
        assert hasattr(PasswordRequirement, "REQUIRED"), "Missing REQUIRED password requirement"
        print("  ✅ PasswordRequirement enum complete")
    except AssertionError as e:
        print(f"  ❌ PasswordRequirement enum incomplete: {e}")
        return False

    try:
        assert hasattr(MFARequirement, "NONE"), "Missing NONE MFA requirement"
        assert hasattr(MFARequirement, "REQUIRED"), "Missing REQUIRED MFA requirement"
        assert hasattr(MFARequirement, "OPTIONAL"), "Missing OPTIONAL MFA requirement"
        print("  ✅ MFARequirement enum complete")
    except AssertionError as e:
        print(f"  ❌ MFARequirement enum incomplete: {e}")
        return False

    try:
        assert hasattr(CommandRisk, "LOW"), "Missing LOW risk level"
        assert hasattr(CommandRisk, "MEDIUM"), "Missing MEDIUM risk level"
        assert hasattr(CommandRisk, "HIGH"), "Missing HIGH risk level"
        assert hasattr(CommandRisk, "CRITICAL"), "Missing CRITICAL risk level"
        print("  ✅ CommandRisk enum complete")
    except AssertionError as e:
        print(f"  ❌ CommandRisk enum incomplete: {e}")
        return False

    # Check SudoCommandRule class
    print("\n2. Checking SudoCommandRule class...")
    try:
        # Create test rule
        rule = SudoCommandRule(
            command_pattern="systemctl restart myapp",
            password_required=PasswordRequirement.NONE,
        )

        assert hasattr(rule, "command_pattern")
        assert hasattr(rule, "password_required")
        print("  ✅ SudoCommandRule dataclass complete")

        # Check methods
        assert hasattr(SudoCommandRule, "matches_command"), "Missing matches_command() method"
        assert hasattr(SudoCommandRule, "is_allowed_now"), "Missing is_allowed_now() method"
        print("  ✅ SudoCommandRule methods present")

    except Exception as e:
        print(f"  ❌ SudoCommandRule validation failed: {e}")
        return False

    # Check SudoPolicy class
    print("\n3. Checking SudoPolicy class...")
    try:
        assert hasattr(SudoPolicy, "find_matching_rule"), "Missing find_matching_rule()"
        assert hasattr(SudoPolicy, "is_command_allowed"), "Missing is_command_allowed()"
        print("  ✅ SudoPolicy methods present")
    except AssertionError as e:
        print(f"  ❌ SudoPolicy incomplete: {e}")
        return False

    # Check SudoPolicyManager methods
    print("\n4. Checking SudoPolicyManager methods...")
    required_methods = [
        "apply_policy_for_user",
        "test_command",
        "get_user_policy",
        "revoke_sudo_access",
    ]

    try:
        for method in required_methods:
            assert hasattr(SudoPolicyManager, method), f"Missing method: {method}"
        print(f"  ✅ SudoPolicyManager has all {len(required_methods)} required methods")
    except AssertionError as e:
        print(f"  ❌ SudoPolicyManager incomplete: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Data models validated")
    return True


def validate_manager_initialization():
    """Test Sudo Policy Manager initialization"""
    print("\n\nSudo Policy Manager Initialization Test")
    print("=" * 60)

    # Test 1: Initialize manager with temp directories
    print("\n1. Initializing Sudo Policy Manager...")
    try:
        import tempfile

        temp_dir = tempfile.mkdtemp()

        sudo_mgr = SudoPolicyManager(
            sudoers_dir=Path(temp_dir) / "sudoers.d",
            policy_dir=Path(temp_dir) / "policies",
            audit_log=Path(temp_dir) / "audit.log",
            dry_run=True,
        )
        print("  ✅ SudoPolicyManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Check default policies loaded
    print("\n2. Checking default policies...")

    expected_roles = ["developer", "devops", "admin", "viewer"]

    try:
        for role in expected_roles:
            if role in sudo_mgr.policies:
                policy = sudo_mgr.policies[role]
                print(f"  ✅ {role:12s} - {len(policy.rules)} rule(s)")
            else:
                print(f"  ❌ {role} policy not found")
                return False
    except Exception as e:
        print(f"  ❌ Policy check failed: {e}")
        return False

    # Test 3: Check RBAC integration
    print("\n3. Checking RBAC integration...")

    if sudo_mgr.rbac_manager:
        print("  ✅ RBAC manager integrated")
    else:
        print("  ⚠️  RBAC manager not available (may need initialization)")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Sudo Policy Manager initialization validated")
    return True


if __name__ == "__main__":
    result1 = validate_file_structure()
    result2 = validate_data_models()
    result3 = validate_manager_initialization()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"File Structure: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"Manager Init: {'✅ PASS' if result3 else '❌ FAIL'}")

    sys.exit(0 if (result1 and result2 and result3) else 1)
