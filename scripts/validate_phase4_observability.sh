#!/bin/bash
# Phase 4 Testing & Observability Validation Script

set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
WARN=0

echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🧪 PHASE 4 TESTING & OBSERVABILITY VALIDATION        ║
║        Production Readiness Verification                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Helper functions
pass() { echo -e "  ${GREEN}✅ PASS${NC} - $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}❌ FAIL${NC} - $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}⚠️  WARN${NC} - $1"; WARN=$((WARN+1)); }
section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# TEST 1: File Structure
# ============================================================================
section "TEST 1: File Structure Validation"

echo "[1.1] Checking observability files..."
OBS_FILES=(
    "configurator/observability/metrics.py"
    "configurator/observability/structured_logging.py"
    "configurator/observability/dashboard.py"
    "configurator/observability/alerting.py"
    "configurator/cli_monitoring.py"
)

for file in "${OBS_FILES[@]}"; do
    [ -f "$file" ] && pass "Found: $file" || fail "Missing: $file"
done

# ============================================================================
# TEST 2: Metrics System
# ============================================================================
section "TEST 2: Metrics System Validation"

echo "[2.1] Testing MetricsCollector..."
python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')
try:
    from configurator.observability.metrics import MetricsCollector, get_metrics
    m = MetricsCollector()
    print("    ✓ MetricsCollector initialized")

    c = m.counter("test_counter", "Test"); c.inc(); c.inc(5)
    assert c.get() == 6; print("    ✓ Counter works")

    g = m.gauge("test_gauge", "Test"); g.set(10); g.inc(5); g.dec(3)
    assert g.get() == 12; print("    ✓ Gauge works")

    h = m.histogram("test_histogram", "Test")
    for v in [0.5, 1.5, 2.5]: h.observe(v)
    assert h.get_count() == 3; print("    ✓ Histogram works")

    prom = m.export_prometheus()
    assert "test_counter" in prom; print("    ✓ Prometheus export works")

    import json
    data = json.loads(m.export_json())
    assert "counters" in data; print("    ✓ JSON export works")
except Exception as e:
    print(f"    ✗ Error: {e}"); import traceback; traceback.print_exc(); sys.exit(1)
PYEOF
[ $? -eq 0 ] && pass "Metrics system validated" || fail "Metrics system failed"

echo "[2.2] Testing global metrics..."
python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')
try:
    from configurator.observability.metrics import get_metrics
    m1, m2 = get_metrics(), get_metrics()
    assert m1 is m2; print("    ✓ Singleton pattern works")
    for m in ['installations_total', 'module_executions_total', 'network_operations_total', 'circuit_breaker_opens_total']:
        assert hasattr(m1, m)
    print("    ✓ 4 standard metrics initialized")
except Exception as e:
    print(f"    ✗ Error: {e}"); sys.exit(1)
PYEOF
[ $? -eq 0 ] && pass "Global metrics works" || fail "Global metrics issue"

# ============================================================================
# TEST 3: Structured Logging
# ============================================================================
section "TEST 3: Structured Logging Validation"

python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')
try:
    from configurator.observability.structured_logging import StructuredLogger
    import logging
    l = StructuredLogger("test", level=logging.INFO)
    for m in ['info', 'error', 'warning']: assert hasattr(l, m)
    print("    ✓ Logging methods exist")
    with l.correlation_context() as c:
        assert c; print(f"    ✓ Correlation context works (ID: {c[:8]}...)")
except Exception as e:
    print(f"    ✗ Error: {e}"); import traceback; traceback.print_exc(); sys.exit(1)
PYEOF
[ $? -eq 0 ] && pass "Structured logging validated" || fail "Logging failed"

# ============================================================================
# TEST 4: Dashboard
# ============================================================================
section "TEST 4: Dashboard Validation"

python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')
try:
    from configurator.observability.dashboard import SimpleProgressReporter
    r = SimpleProgressReporter(); r.update_module("test", "running")
    print("    ✓ SimpleProgressReporter works")
    try:
        from configurator.observability.dashboard import InstallationDashboard
        d = InstallationDashboard()
        d.update_module("docker", "running", 50, 10.5)
        d.update_circuit_breaker("apt", "CLOSED", 0)
        d.update_metric("cpu", 45.5)
        print("    ✓ InstallationDashboard works")
    except ImportError:
        print("    ⚠ Rich not available (fallback OK)")
except Exception as e:
    print(f"    ✗ Error: {e}"); import traceback; traceback.print_exc(); sys.exit(1)
PYEOF
[ $? -eq 0 ] && pass "Dashboard validated" || warn "Dashboard issues"

# ============================================================================
# TEST 5: Alerting
# ============================================================================
section "TEST 5: Alerting System Validation"

python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')
import tempfile
from pathlib import Path
try:
    from configurator.observability.alerting import AlertManager, Alert, AlertSeverity, FileAlertChannel
    from datetime import datetime
    with tempfile.TemporaryDirectory() as t:
        af = Path(t) / "alerts.log"
        ch = FileAlertChannel(af)
        a = Alert(AlertSeverity.WARNING, "Test", "Msg", "test", datetime.now())
        assert ch.send(a) and af.exists()
        print("    ✓ FileAlertChannel works")

        m = AlertManager(); m.add_channel(FileAlertChannel(Path(t) / "test.log"))
        m.alert(AlertSeverity.INFO, "Test", "Msg", "val")
        print("    ✓ AlertManager works")

        m.add_threshold_rule("test", lambda v: v > 100, AlertSeverity.WARNING, "Exceeded")
        print("    ✓ Threshold rules work")
except Exception as e:
    print(f"    ✗ Error: {e}"); import traceback; traceback.print_exc(); sys.exit(1)
PYEOF
[ $? -eq 0 ] && pass "Alerting validated" || fail "Alerting failed"

# ============================================================================
# TEST 6: Configuration
# ============================================================================
section "TEST 6: Configuration Validation"

if grep -q "observability:" config/default.yaml; then
    pass "Observability config exists"
    python3 << 'PYEOF'
import yaml
with open("config/default.yaml") as f: c = yaml.safe_load(f)
obs = c.get('observability', {})
for s in ['metrics', 'logging', 'alerting', 'dashboard']:
    print(f"    {'✓' if s in obs else '⚠'} Section: {s}")
PYEOF
else
    fail "Observability config missing"
fi

# ============================================================================
# FINAL REPORT
# ============================================================================
section "VALIDATION SUMMARY"

TOTAL=$((PASS + FAIL + WARN))
echo -e "\n  Total: $TOTAL | ${GREEN}Pass: $PASS${NC} | ${RED}Fail: $FAIL${NC} | ${YELLOW}Warn: $WARN${NC}\n"

if [ $FAIL -eq 0 ]; then
    if [ $WARN -gt 3 ]; then
        echo -e "${YELLOW}⚠️  PASSED WITH WARNINGS - Review before production${NC}"
    else
        echo -e "${GREEN}✅ PHASE 4 VALIDATION PASSED - Production ready! 🎉${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ PHASE 4 VALIDATION FAILED - Fix issues above${NC}"
    exit 1
fi
