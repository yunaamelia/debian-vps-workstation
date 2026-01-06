#!/usr/bin/env python3
"""Test command permission checking"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurator.rbac.sudo_manager import SudoPolicyManager


def test_command_testing():
    """Test checking if commands are allowed"""

    print("Command Testing Test")
    print("=" * 60)

    sudo_mgr = SudoPolicyManager(dry_run=True)

    # Check if RBAC manager available
    if not sudo_mgr.rbac_manager:
        print("\n⚠️  RBAC manager not available, using mock")
        sudo_mgr.rbac_manager = MagicMock()
        sudo_mgr.rbac_manager.assignments = {}

    test_user = "testuser_cmd"

    # Setup test user with developer role
    print(f"\nTest user: {test_user}")
    print("Assigning developer role...\n")

    mock_assignment = MagicMock()
    mock_assignment.role_name = "developer"
    sudo_mgr.rbac_manager.assignments[test_user] = mock_assignment

    # Test 1: Allowed command (passwordless)
    print("1. Testing allowed passwordless command...")

    result = sudo_mgr.test_command(test_user, "systemctl restart myapp")

    print("  Command: systemctl restart myapp")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Password required: {result['password_required']}")
    print(f"  Rule matched: {result.get('rule', 'None')}")

    if result["allowed"] and not result["password_required"]:
        print("  ✅ Command correctly allowed (passwordless)")
    else:
        print("  ❌ Command should be allowed without password")
        return False

    # Test 2: Denied command
    print("\n2. Testing denied command...")

    result = sudo_mgr.test_command(test_user, "iptables -A INPUT -j DROP")

    print("  Command: iptables -A INPUT -j DROP")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Reason: {result['reason']}")

    if not result["allowed"]:
        print("  ✅ Command correctly denied")
    else:
        print("  ❌ Command should be denied")
        return False

    # Test 3: Wildcard match
    print("\n3. Testing wildcard match...")

    result = sudo_mgr.test_command(test_user, "docker logs container123")

    print("  Command: docker logs container123")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Rule matched: {result.get('rule', 'None')}")

    if result["allowed"]:
        print("  ✅ Wildcard matching works")
    else:
        print("  ❌ Should match 'docker logs *' rule")
        return False

    # Test 4: Multiple status checks (should all be allowed)
    print("\n4. Testing multiple allowed commands...")

    allowed_commands = [
        "systemctl status nginx",
        "systemctl status myapp",
        "docker ps",
        "docker inspect container1",
    ]

    all_passed = True
    for cmd in allowed_commands:
        result = sudo_mgr.test_command(test_user, cmd)
        if result["allowed"]:
            print(f"  ✅ {cmd}")
        else:
            print(f"  ❌ {cmd} - should be allowed")
            all_passed = False

    if not all_passed:
        return False

    # Test 5: Test devops role permissions
    print("\n5. Testing devops role permissions...")

    mock_assignment.role_name = "devops"

    result = sudo_mgr.test_command(test_user, "apt-get update")

    print("  Command: apt-get update (devops role)")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Password required: {result['password_required']}")

    if result["allowed"] and result["password_required"]:
        print("  ✅ DevOps command allowed with password requirement")
    else:
        print("  ❌ apt-get update should be allowed for devops (with password)")
        return False

    print("\n" + "=" * 60)
    print("✅ Command testing validated")
    return True


if __name__ == "__main__":
    result = test_command_testing()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Command Testing: {'✅ PASS' if result else '❌ FAIL'}")

    sys.exit(0 if result else 1)
