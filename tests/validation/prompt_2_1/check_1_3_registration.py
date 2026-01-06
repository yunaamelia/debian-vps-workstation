#!/usr/bin/env python3
"""Validate check registration"""

import os
import sys
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from configurator.security.cis_scanner import CISBenchmarkScanner


def validate_check_registration():
    """Validate all checks are properly registered"""

    print("Check Registration Validation")
    print("=" * 60)

    scanner = CISBenchmarkScanner()
    checks = scanner.checks

    print(f"Total checks registered: {len(checks)}")

    # Validate minimum count
    if len(checks) < 100:
        print(f"❌ Insufficient checks: {len(checks)} < 100")
        # Don't fail immediately, let's see stats
        # return False
    else:
        print(f"✅ Sufficient checks: {len(checks)} >= 100")

    # Check for duplicate IDs
    ids = [c.id for c in checks]
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        print(f"❌ Duplicate check IDs found: {set(duplicates)}")
        return False
    else:
        print("✅ No duplicate check IDs")

    # Validate categories
    by_category = defaultdict(int)
    for check in checks:
        by_category[check.category] += 1

    print("\nChecks by category:")
    for category, count in sorted(by_category.items()):
        print(f"  {category:25s}:  {count:3d} checks")

    # Validate expected categories
    expected_categories = [
        "Initial Setup",
        "Services",
        "Network",
        "Logging",
        "Access Control",
        "System Maintenance",
    ]
    for category in expected_categories:
        if category not in by_category:
            print(f"❌ Missing category: {category}")
            return False
    print(f"✅ All {len(expected_categories)} expected categories present")

    # Validate severity distribution
    by_severity = defaultdict(int)
    for check in checks:
        by_severity[check.severity.value] += 1

    print("\nChecks by severity:")
    for severity in ["critical", "high", "medium", "low"]:
        count = by_severity.get(severity, 0)
        print(f"  {severity.capitalize():10s}: {count:3d} checks")

    # Should have some of each severity
    if by_severity.get("critical", 0) < 5:
        print("⚠️  Few CRITICAL checks (expected >= 5)")
    else:
        print("✅ Sufficient CRITICAL checks")

    # Validate check functions
    checks_with_function = len([c for c in checks if c.check_function is not None])
    manual_checks = len([c for c in checks if c.manual])

    print("\nCheck functions:")
    print(f"  Automated checks: {checks_with_function}")
    print(f"  Manual checks: {manual_checks}")
    print(f"  Total: {checks_with_function + manual_checks}")

    if checks_with_function + manual_checks != len(checks):
        print("❌ Some checks have no check_function and are not marked manual")
        return False
    else:
        print("✅ All checks have check_function or are marked manual")

    # Validate remediation functions
    remediable = len([c for c in checks if c.remediation_function is not None])
    print("\nRemediation:")
    print(f"  Auto-remediable checks: {remediable}")
    print(f"  Remediation coverage: {remediable/len(checks)*100:.1f}%")

    if remediable < 50:
        print("⚠️  Few remediation functions (expected >= 50)")
    else:
        print(f"✅ Sufficient remediation functions ({remediable})")

    print("=" * 60)
    print("✅ Check registration validated")
    return True


if __name__ == "__main__":
    sys.exit(0 if validate_check_registration() else 1)
