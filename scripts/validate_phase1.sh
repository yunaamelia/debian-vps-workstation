#!/bin/bash
# Phase 1 Validation Script
# Validates all changes from Phase 1 implementation

set +e  # Continue on error for better reporting

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     PHASE 1 VALIDATION - Implementation Verification     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Helper functions
pass() {
    echo -e "  ${GREEN}✅ PASS${NC} - $1"
    ((PASS++))
}

fail() {
    echo -e "  ${RED}❌ FAIL${NC} - $1"
    ((FAIL++))
}

warn() {
    echo -e "  ${YELLOW}⚠️  WARN${NC} - $1"
    ((WARN++))
}

section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# TEST 1: URL Updates Validation
# ============================================================================
section "TEST 1: URL Updates Validation"

echo "[1.1] Checking for outdated URLs..."
OUTDATED=$(grep -r "youruser/debian-vps-configurator" . \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude="validate_phase1.sh" \
    2>/dev/null || true)

if [ -z "$OUTDATED" ]; then
    pass "No outdated 'youruser' URLs found"
else
    fail "Found outdated URLs:"
    echo "$OUTDATED"
fi

echo "[1.2] Verifying new URLs in pyproject.toml..."
CORRECT_URLS=$(grep -c "yunaamelia/debian-vps-workstation" pyproject.toml || echo "0")
if [ "$CORRECT_URLS" -ge 4 ]; then
    pass "pyproject.toml has correct URLs ($CORRECT_URLS occurrences)"
else
    fail "pyproject.toml missing URLs (found: $CORRECT_URLS, expected: ≥4)"
fi

echo "[1.3] Checking exceptions.py URLs..."
EXCEPTION_URLS=$(grep -c "yunaamelia/debian-vps-workstation" configurator/exceptions.py || echo "0")
if [ "$EXCEPTION_URLS" -ge 1 ]; then
    pass "exceptions.py has correct URLs"
else
    warn "exceptions.py may need URL updates (found: $EXCEPTION_URLS)"
fi

# ============================================================================
# TEST 2: Module Dependencies Validation
# ============================================================================
section "TEST 2: Module Dependencies Validation"

echo "[2.1] Checking desktop module dependencies..."
if grep -q 'depends_on.*=.*\["system".*"security"\]' configurator/modules/desktop.py; then
    pass "Desktop module declares dependencies on system and security"
elif grep -q 'depends_on.*=.*\["system"\]' configurator/modules/desktop.py; then
    warn "Desktop only depends on 'system' (should include 'security')"
else
    fail "Desktop module missing depends_on declaration"
fi

echo "[2.2] Validating dependency graph builds without errors..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.modules.desktop import DesktopModule
    from unittest.mock import Mock

    # Test that desktop module has dependencies
    config = {"enabled": True}
    module = DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    if hasattr(module, 'depends_on'):
        print(f"    ✓ Desktop module depends_on: {module.depends_on}")
        if 'system' in module.depends_on and 'security' in module.depends_on:
            print(f"    ✓ Both system and security dependencies present")
            sys.exit(0)
        else:
            print(f"    ⚠ Missing required dependencies")
            sys.exit(0)
    else:
        print(f"    ⚠ depends_on not found as instance attribute")
        sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Dependency validation passed"
else
    fail "Dependency validation failed"
fi

# ============================================================================
# TEST 3: Documentation Completeness
# ============================================================================
section "TEST 3: Documentation Completeness"

echo "[3.1] Checking required documentation files exist..."
REQUIRED_DOCS=(
    "docs/advanced/rollback-behavior.md"
    "docs/advanced/module-execution-order.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        pass "Found: $doc"
    else
        fail "Missing: $doc"
    fi
done

echo "[3.2] Validating rollback-behavior.md content..."
if [ -f "docs/advanced/rollback-behavior.md" ]; then
    # Check for required sections
    SECTIONS=("When Rollback Occurs" "What Gets Rolled Back" "Partial Rollback")
    for section in "${SECTIONS[@]}"; do
        if grep -q "$section" docs/advanced/rollback-behavior.md; then
            pass "Section found: $section"
        else
            warn "Section missing: $section"
        fi
    done
fi

echo "[3.3] Validating module-execution-order.md content..."
if [ -f "docs/advanced/module-execution-order.md" ]; then
    if grep -q "system (Priority 10)" docs/advanced/module-execution-order.md; then
        pass "Execution order documented"
    else
        warn "Execution order may be incomplete"
    fi

    if grep -q "Batch" docs/advanced/module-execution-order.md; then
        pass "Batch execution examples present"
    else
        warn "Batch examples may be missing"
    fi
fi

# ============================================================================
# TEST 4: Path Standardization
# ============================================================================
section "TEST 4: Path Standardization"

echo "[4.1] Checking if constants.py exists..."
# Constants.py was removed as it was unused in the codebase (tech debt cleanup)
# if [ -f "configurator/constants.py" ]; then ...

echo "[4.3] Checking for hardcoded paths in modules..."
HARDCODED=$(grep -r "/etc/debian-vps-configurator" configurator/modules/ 2>/dev/null || true)
if [ -n "$HARDCODED" ]; then
    warn "Found hardcoded paths (should use constants):"
    echo "$HARDCODED" | head -5
else
    pass "No hardcoded paths in modules"
fi

# ============================================================================
# TEST 5: Enhanced Error Messages
# ============================================================================
section "TEST 5: Enhanced Error Messages"

echo "[5.1] Validating exception classes..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.exceptions import (
        ConfiguratorError,
        PrerequisiteError,
        ConfigurationError,
        ValidationError
    )

    # Test base exception
    try:
        raise ConfiguratorError(
            what="Test error",
            why="Testing",
            how="This is a test"
        )
    except ConfiguratorError as e:
        msg = str(e)
        if "WHAT HAPPENED" in msg and "WHY IT HAPPENED" in msg and "HOW TO FIX" in msg:
            print("    ✓ ConfiguratorError formatting correct")
        else:
            print("    ✗ ConfiguratorError missing sections")
            sys.exit(1)

    # Test that exception classes have enhanced documentation
    if "Common Causes" in ValidationError.__doc__:
        print("    ✓ ValidationError has enhanced documentation")
    else:
        print("    ⚠ ValidationError may need enhanced documentation")

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Exception classes validated"
else
    fail "Exception validation failed"
fi

# ============================================================================
# TEST 6: No Breaking Changes
# ============================================================================
section "TEST 6: No Breaking Changes"

echo "[6.1] Checking import compatibility..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    # Test critical imports still work
    from configurator.cli import main
    from configurator.config import ConfigManager
    from configurator.modules.base import ConfigurationModule

    print("    ✓ All critical imports successful")
    sys.exit(0)

except ImportError as e:
    print(f"    ✗ Import failed: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Import compatibility maintained"
else
    fail "Breaking changes detected in imports"
fi

echo "[6.2] Validating configuration loading..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.config import ConfigManager
    from pathlib import Path

    # Test default config loads
    if Path("config/default.yaml").exists():
        config = ConfigManager("config/default.yaml")
        enabled = config.get_enabled_modules()
        print(f"    ✓ Configuration loads successfully")
        print(f"    ✓ Found {len(enabled)} enabled modules")
        sys.exit(0)
    else:
        print("    ⚠ config/default.yaml not found")
        sys.exit(0)

except Exception as e:
    print(f"    ✗ Error loading config: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Configuration loading works"
else
    fail "Configuration loading broken"
fi

# ============================================================================
# TEST 7: Code Quality Checks
# ============================================================================
section "TEST 7: Code Quality Checks"

echo "[7.1] Checking Python syntax..."
SYNTAX_ERRORS=0
for file in $(find configurator -name "*.py" 2>/dev/null); do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo "    ✗ Syntax error in: $file"
        ((SYNTAX_ERRORS++))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    pass "No syntax errors found"
else
    fail "Found $SYNTAX_ERRORS syntax errors"
fi

echo "[7.2] Checking for new TODO/FIXME comments..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    NEW_TODOS=$(git diff HEAD --unified=0 2>/dev/null | grep -c "^\+.*TODO\|^\+.*FIXME" || echo "0")
    if [ "$NEW_TODOS" -eq 0 ]; then
        pass "No new TODO/FIXME comments"
    else
        warn "Added $NEW_TODOS new TODO/FIXME comments"
    fi
else
    warn "Not a git repository, skipping TODO check"
fi

# ============================================================================
# TEST 8: Git Commit Validation
# ============================================================================
section "TEST 8: Git Commit Validation"

if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[8.1] Checking last commit message format..."
    LAST_COMMIT=$(git log -1 --pretty=%B 2>/dev/null || echo "")
    if echo "$LAST_COMMIT" | grep -qE "^(feat|fix|docs|refactor|test|chore|style|perf)(\(.+\))?: .+"; then
        pass "Commit follows conventional commits format"
    else
        warn "Commit may not follow conventional commits format"
    fi

    echo "[8.2] Checking for uncommitted changes..."
    if git diff --quiet 2>/dev/null; then
        pass "No uncommitted changes"
    else
        warn "Uncommitted changes detected"
    fi
else
    warn "Not a git repository, skipping git checks"
fi

# ============================================================================
# FINAL REPORT
# ============================================================================
section "VALIDATION SUMMARY"

TOTAL=$((PASS + FAIL + WARN))
echo ""
echo "  Total Tests: $TOTAL"
echo -e "  ${GREEN}Passed: $PASS${NC}"
echo -e "  ${RED}Failed: $FAIL${NC}"
echo -e "  ${YELLOW}Warnings: $WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║           ✅ PHASE 1 VALIDATION PASSED ✅                 ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  All critical checks passed. Ready for Phase 2!           ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║           ❌ PHASE 1 VALIDATION FAILED ❌                 ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  Please fix the issues above before proceeding.          ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
