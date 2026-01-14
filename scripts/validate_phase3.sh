#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "PHASE 3 VALIDATION - AUTOMATED TEST SEQUENCE"
echo "Desktop Module Phase 1-2 (XRDP + Compositor)"
echo "═══════════════════════════════════════════════════════════"

# 1. Code quality
echo -e "\n[1/9] Code quality checks..."
python3 -m py_compile configurator/modules/desktop.py && echo "✅ Syntax OK" || echo "❌ Syntax errors"
black configurator/modules/desktop.py --check && echo "✅ Formatted" || echo "❌ Needs formatting"
flake8 configurator/modules/desktop.py --max-line-length=100 --ignore=E203,E501,W503 && echo "✅ No lint errors" || echo "⚠️ Lint issues"

# 2. Unit tests
echo -e "\n[2/9] Running unit tests..."
pytest tests/modules/test_desktop_xrdp_optimization.py -v --tb=short
pytest tests/modules/test_desktop_phase2_unit.py -v --tb=short

# 3. Security tests
echo -e "\n[3/9] Running security tests..."
pytest tests/security/test_phase1_security.py -v --tb=short

# 4. Configuration generation
echo -e "\n[4/9] Testing configuration generation..."
python3 << 'EOF'
from unittest.mock import Mock
from configurator.modules.desktop import DesktopModule
module = DesktopModule(config={"desktop": {"xrdp": {}}}, logger=Mock(), rollback_manager=Mock(), dry_run_manager=Mock())
xrdp_ini = module._generate_xrdp_ini()
assert "port=" in xrdp_ini, "xrdp.ini generation failed"
print("✅ Config generation OK")
EOF

# 5. Dry-run
echo -e "\n[5/9] Running dry-run installation..."
# We use sudo here because the configurator might check for root permissions even in dry-run
sudo python3 -m configurator install --profile beginner --dry-run 2>&1 | tee /tmp/phase3_dryrun.log
if grep -q "Desktop environment configured successfully" /tmp/phase3_dryrun.log; then
    echo "✅ Dry-run PASS"
else
    echo "❌ Dry-run FAIL"
fi

echo -e "\n[6/9] Validation script complete. Review output above."
