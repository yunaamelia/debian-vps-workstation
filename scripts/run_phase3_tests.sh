#!/bin/bash
# Comprehensive test runner for Phase 3

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Phase 3: Theme & Visual Customization Tests             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TOTAL_TESTS=0

echo "🔐 Phase 1: Supply Chain Security Tests"
echo "─────────────────────────────────────────────────────────"
if python -m pytest tests/security/test_phase3_supply_chain.py -v --tb=short; then
    echo -e "${GREEN}✅ Supply chain security tests PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ CRITICAL: Supply chain tests FAILED${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "📋 Phase 2: Unit Tests"
echo "─────────────────────────────────────────────────────────"
if python -m pytest tests/unit/modules/test_desktop_phase3_unit.py -v \
    --cov=configurator.modules.desktop \
    --cov-append \
    --cov-report=term-missing; then
    echo -e "${GREEN}✅ Unit tests PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ Unit tests FAILED${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "📋 Phase 3: Integration Tests"
echo "─────────────────────────────────────────────────────────"
if python -m pytest tests/integration/test_desktop_phase3_integration.py -v; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ Integration tests FAILED${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "📋 Phase 4: Performance Tests"
echo "─────────────────────────────────────────────────────────"
if python -m pytest tests/performance/test_phase3_performance.py -v; then
    echo -e "${GREEN}✅ Performance tests PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ Performance tests FAILED${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "🎨 Phase 5: Visual Quality Tests (Manual)"
echo "─────────────────────────────────────────────────────────"
echo -e "${YELLOW}⚠️  Visual tests require manual validation:${NC}"
echo ""
echo "   1. Deploy to test VM: ./scripts/deploy_test.sh"
echo "   2. Run: vps-configurator install --profile beginner"
echo "   3. Connect via RDP client"
echo "   4. Complete visual checklist:"
echo ""
echo "   ${BLUE}Theme Appearance:${NC}"
echo "      [ ] Window borders crisp"
echo "      [ ] No transparency artifacts"
echo "      [ ] Colors consistent"
echo "      [ ] Dark theme applied"
echo ""
echo "   ${BLUE}Font Rendering:${NC}"
echo "      [ ] Text sharp, not blurry"
echo "      [ ] No color fringing"
echo "      [ ] Small text readable"
echo ""
echo "   ${BLUE}Icons:${NC}"
echo "      [ ] All icons present (no fallbacks)"
echo "      [ ] Icons consistent size"
echo "      [ ] Icons not pixelated"
echo ""
echo "   ${BLUE}Panel/Dock:${NC}"
echo "      [ ] Panel at top (macOS layout)"
echo "      [ ] Plank dock at bottom"
echo "      [ ] No visual overlap"
echo ""
echo "   5. Document results in: tests/visual/RESULTS.md"
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Test Summary                                             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo "Automated Tests: $TESTS_PASSED/$TOTAL_TESTS passed"
echo ""

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 All automated tests PASSED!${NC}"
    echo "Next step: Complete manual visual validation"
    exit 0
else
    echo -e "${RED}❌ Some tests FAILED${NC}"
    exit 1
fi
