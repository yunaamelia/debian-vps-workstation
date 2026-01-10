#!/bin/bash
# Comprehensive test runner for XRDP optimization feature

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  XRDP Optimization Test Suite                            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
UNIT_TESTS_PASSED=0
INTEGRATION_TESTS_PASSED=0
PERFORMANCE_TESTS_PASSED=0
SECURITY_TESTS_PASSED=0

# Change to script directory
cd "$(dirname "$0")/.."

echo "📋 Phase 1: Unit Tests"
echo "─────────────────────────────────────────────────────────"
if python3 -m pytest tests/unit/modules/test_desktop_xrdp_optimization.py -v \
    --cov=configurator.modules.desktop \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/unit; then
    echo -e "${GREEN}✅ Unit tests PASSED${NC}"
    UNIT_TESTS_PASSED=1
else
    echo -e "${RED}❌ Unit tests FAILED${NC}"
fi
echo ""

echo "📋 Phase 2: Integration Tests"
echo "─────────────────────────────────────────────────────────"
if python3 -m pytest tests/integration/test_desktop_module_integration.py -v; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
    INTEGRATION_TESTS_PASSED=1
else
    echo -e "${RED}❌ Integration tests FAILED${NC}"
fi
echo ""

echo "📋 Phase 3: Performance Tests"
echo "─────────────────────────────────────────────────────────"
if python3 -m pytest tests/performance/test_xrdp_performance.py -v; then
    echo -e "${GREEN}✅ Performance tests PASSED${NC}"
    PERFORMANCE_TESTS_PASSED=1
else
    echo -e "${RED}❌ Performance tests FAILED${NC}"
fi
echo ""

echo "📋 Phase 4: Security Tests"
echo "─────────────────────────────────────────────────────────"
if python3 -m pytest tests/security/test_xrdp_security.py -v; then
    echo -e "${GREEN}✅ Security tests PASSED${NC}"
    SECURITY_TESTS_PASSED=1
else
    echo -e "${RED}❌ Security tests FAILED${NC}"
fi
echo ""

echo "📋 Phase 5: System Tests (Optional)"
echo "─────────────────────────────────────────────────────────"
echo -e "${BLUE}ℹ️  System tests require XRDP installation${NC}"
echo "   Run with: pytest tests/system/ -v -m system"
echo ""
echo -e "${YELLOW}⚠️  Manual tests checklist:${NC}"
echo "   1. Deploy to test VM: ./scripts/deploy_test.sh"
echo "   2. Run configurator: sudo python3 -m configurator --module desktop"
echo "   3. Connect via RDP client (Windows/Remmina)"
echo "   4. Verify:"
echo "      - Login successful within 5 seconds"
echo "      - XFCE desktop loads properly"
echo "      - No cursor rendering issues"
echo "      - Smooth mouse/keyboard interaction"
echo "      - No screen blanking"
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Test Summary                                             ║"
echo "╚══════════════════════════════════════════════════════════╝"

TOTAL_PASSED=$((UNIT_TESTS_PASSED + INTEGRATION_TESTS_PASSED + PERFORMANCE_TESTS_PASSED + SECURITY_TESTS_PASSED))
TOTAL_TESTS=4

echo ""
echo "Automated Tests: $TOTAL_PASSED/$TOTAL_TESTS passed"
echo ""

if [ $UNIT_TESTS_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Unit Tests"
else
    echo -e "  ${RED}✗${NC} Unit Tests"
fi

if [ $INTEGRATION_TESTS_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Integration Tests"
else
    echo -e "  ${RED}✗${NC} Integration Tests"
fi

if [ $PERFORMANCE_TESTS_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Performance Tests"
else
    echo -e "  ${RED}✗${NC} Performance Tests"
fi

if [ $SECURITY_TESTS_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Security Tests"
else
    echo -e "  ${RED}✗${NC} Security Tests"
fi

echo ""
echo "Coverage Report: htmlcov/unit/index.html"
echo ""

if [ $TOTAL_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 All automated tests PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review coverage report"
    echo "  2. Run system tests (if XRDP installed)"
    echo "  3. Perform manual testing"
    echo "  4. Ready for code review and merge"
    exit 0
else
    echo -e "${RED}❌ Some tests FAILED${NC}"
    echo ""
    echo "Action required:"
    echo "  1. Review test failures above"
    echo "  2. Fix failing tests"
    echo "  3. Re-run test suite"
    exit 1
fi
