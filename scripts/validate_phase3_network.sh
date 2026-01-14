#!/bin/bash
# Phase 3 Network Resilience Validation Script
# Tests circuit breakers, retries, and failure handling

set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
WARN=0
CHAOS_PASS=0
CHAOS_FAIL=0

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🌐 PHASE 3 NETWORK RESILIENCE VALIDATION             ║
║        Circuit Breakers & Retry Logic Tests              ║
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
# TEST 1: File Structure Validation
# ============================================================================
section "TEST 1: File Structure Validation"

echo "[1.1] Checking required network resilience files..."
REQUIRED_FILES=(
    "configurator/core/network.py"
    "configurator/core/health.py"
    "tests/resilience/test_network_failure_simulation.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "Found: $file"
    else
        fail "Missing: $file"
    fi
done

echo "[1.2] Checking circuit breaker still exists..."
if [ -f "configurator/utils/circuit_breaker.py" ]; then
    pass "Circuit breaker module exists"
else
    fail "Circuit breaker module missing"
fi

# ============================================================================
# TEST 2: Network Wrapper Import & Initialization
# ============================================================================
section "TEST 2: Network Wrapper Validation"

echo "[2.1] Testing NetworkOperationWrapper import..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import (
        NetworkOperationWrapper,
        NetworkOperationType,
        RetryConfig
    )

    print("    ✓ NetworkOperationWrapper imported")

    # Test initialization
    from unittest.mock import Mock
    wrapper = NetworkOperationWrapper({}, Mock())
    print("    ✓ NetworkOperationWrapper initialized")

    # Check methods exist
    methods = [
        'execute_with_retry',
        'apt_update_with_retry',
        'apt_install_with_retry',
        'download_with_retry',
        'git_clone_resilient',
        'check_internet_connectivity'
    ]

    for method in methods:
        if hasattr(wrapper, method):
            print(f"    ✓ Method exists: {method}")
        else:
            print(f"    ✗ Method missing: {method}")
            sys.exit(1)

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "NetworkOperationWrapper validated"
else
    fail "NetworkOperationWrapper validation failed"
fi

echo "[2.2] Testing RetryConfig..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import RetryConfig

    # Test default config
    config = RetryConfig()

    assert config.max_retries > 0, "max_retries must be positive"
    assert config.initial_delay > 0, "initial_delay must be positive"
    assert config.max_delay >= config.initial_delay, "max_delay must be >= initial_delay"

    print(f"    ✓ Default config: max_retries={config.max_retries}")
    print(f"    ✓ Exponential base: {config.exponential_base}")
    print(f"    ✓ Jitter enabled: {config.jitter}")

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "RetryConfig validated"
else
    fail "RetryConfig validation failed"
fi

echo "[2.3] Testing circuit breaker integration..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper
    from unittest.mock import Mock

    config = {
        "performance": {
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 3,
                "timeout": 60
            }
        }
    }

    wrapper = NetworkOperationWrapper(config, Mock())

    # Check circuit breakers were created
    if wrapper.circuit_breakers:
        print(f"    ✓ Circuit breakers created: {list(wrapper.circuit_breakers.keys())}")

        # Verify services
        expected_services = ['apt_repository', 'github', 'external_downloads']
        for service in expected_services:
            if service in wrapper.circuit_breakers:
                print(f"    ✓ Circuit breaker exists: {service}")
            else:
                print(f"    ⚠ Circuit breaker missing: {service}")
    else:
        print("    ✗ No circuit breakers created")
        sys.exit(1)

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Circuit breaker integration works"
else
    fail "Circuit breaker integration failed"
fi

# ============================================================================
# TEST 3: Retry Logic Tests
# ============================================================================
section "TEST 3: Retry Logic Tests"

echo "[3.1] Testing exponential backoff calculation..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper, RetryConfig
    from unittest.mock import Mock

    # Test without jitter for predictable results
    retry_config = RetryConfig(
        initial_delay=1.0,
        exponential_base=2.0,
        max_delay=30.0,
        jitter=False
    )

    wrapper = NetworkOperationWrapper({}, Mock(), retry_config)

    # Test exponential backoff
    delays = [wrapper._calculate_backoff_delay(i) for i in range(6)]

    expected = [1.0, 2.0, 4.0, 8.0, 16.0, 30.0]  # Last one capped at max_delay

    for i, (actual, expect) in enumerate(zip(delays, expected)):
        if abs(actual - expect) < 0.01:
            print(f"    ✓ Attempt {i}: {actual:.1f}s (expected {expect}s)")
        else:
            print(f"    ✗ Attempt {i}: {actual:.1f}s (expected {expect}s)")
            sys.exit(1)

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Exponential backoff works correctly"
else
    fail "Exponential backoff calculation wrong"
fi

echo "[3.2] Testing jitter adds randomness..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper, RetryConfig
    from unittest.mock import Mock

    retry_config = RetryConfig(jitter=True)
    wrapper = NetworkOperationWrapper({}, Mock(), retry_config)

    # Calculate same delay multiple times
    delays = [wrapper._calculate_backoff_delay(2) for _ in range(10)]

    # Check they're all different (jitter applied)
    unique_delays = len(set(delays))

    if unique_delays > 5:  # Most should be different
        print(f"    ✓ Jitter working: {unique_delays}/10 delays are unique")
    else:
        print(f"    ✗ Jitter not working: only {unique_delays}/10 unique")
        sys.exit(1)

    # Check they're within reasonable range
    base_delay = 4.0  # 2^2
    for delay in delays:
        if base_delay <= delay <= base_delay * 1.1:  # Within 10% jitter
            pass
        else:
            print(f"    ✗ Delay {delay} outside expected range")
            sys.exit(1)

    print(f"    ✓ All delays within expected range")
    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Jitter prevents thundering herd"
else
    warn "Jitter may not be working correctly"
fi

echo "[3.3] Testing retry exhaustion..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper, NetworkOperationType, RetryConfig
    from unittest.mock import Mock

    retry_config = RetryConfig(max_retries=3, initial_delay=0.1, jitter=False)
    wrapper = NetworkOperationWrapper({}, Mock(), retry_config)

    call_count = [0]

    def always_fail():
        call_count[0] += 1
        raise Exception("Persistent failure")

    try:
        wrapper.execute_with_retry(
            always_fail,
            NetworkOperationType.HTTP_REQUEST
        )
        print("    ✗ Should have raised exception after retries")
        sys.exit(1)
    except Exception as e:
        if "Persistent failure" in str(e):
            print(f"    ✓ Exception raised after {call_count[0]} attempts")
            if call_count[0] == 3:
                print(f"    ✓ Correct number of retries")
            else:
                print(f"    ✗ Wrong retry count: {call_count[0]} (expected 3)")
                sys.exit(1)
        else:
            print(f"    ✗ Wrong exception: {e}")
            sys.exit(1)

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Retry exhaustion handled correctly"
else
    fail "Retry exhaustion behavior incorrect"
fi

# ============================================================================
# TEST 4: Circuit Breaker Integration Tests
# ============================================================================
section "TEST 4: Circuit Breaker Integration Tests"

echo "[4.1] Testing circuit breaker opens after failures..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper, NetworkOperationType
    from configurator.utils.circuit_breaker import CircuitBreakerError
    from unittest.mock import Mock

    config = {
        "performance": {
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 2,  # Open after 2 failures
                "timeout": 60
            }
        }
    }

    wrapper = NetworkOperationWrapper(config, Mock())

    def always_fail():
        raise Exception("Service unavailable")

    # Fail twice to open circuit
    for i in range(2):
        try:
            wrapper.execute_with_retry(
                always_fail,
                NetworkOperationType.APT_UPDATE
            )
        except Exception:
            pass

    # Third attempt should fail immediately (circuit open)
    try:
        wrapper.execute_with_retry(
            always_fail,
            NetworkOperationType.APT_UPDATE
        )
        print("    ✗ Circuit breaker did not open")
        sys.exit(1)
    except CircuitBreakerError:
        print("    ✓ Circuit breaker opened after threshold")
        sys.exit(0)
    except Exception as e:
        print(f"    ✗ Wrong exception type: {type(e).__name__}")
        sys.exit(1)

except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Circuit breaker opens correctly"
else
    fail "Circuit breaker not opening"
fi

echo "[4.2] Testing circuit breaker status reporting..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.core.network import NetworkOperationWrapper
    from unittest.mock import Mock

    config = {
        "performance": {
            "circuit_breaker": {
                "enabled": True
            }
        }
    }

    wrapper = NetworkOperationWrapper(config, Mock())

    # Get status
    status = wrapper.get_circuit_breaker_status()

    if status:
        print(f"    ✓ Status reporting works: {len(status)} services")

        # Check structure
        for service, info in status.items():
            required_keys = ['state', 'failure_count', 'total_calls']
            if all(k in info for k in required_keys):
                print(f"    ✓ Service '{service}': {info['state']}")
            else:
                print(f"    ✗ Service '{service}' missing keys")
                sys.exit(1)
    else:
        print("    ✗ No status returned")
        sys.exit(1)

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Circuit breaker status reporting works"
else
    fail "Status reporting failed"
fi

# ============================================================================
# TEST 5: Module Integration Tests
# ============================================================================
section "TEST 5: Module Integration Tests"

echo "[5.1] Checking modules use NetworkOperationWrapper..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from configurator.modules.base import ConfigurationModule
    from unittest.mock import Mock

    # Create a mock module
    class TestModule(ConfigurationModule):
        name = "test"
        def validate(self): return True
        def configure(self): return True
        def verify(self): return True

    module = TestModule({}, Mock())

    # Check network wrapper exists
    if hasattr(module, 'network'):
        print("    ✓ Base module has 'network' attribute")

        # Check it's the right type
        from configurator.core.network import NetworkOperationWrapper
        if isinstance(module.network, NetworkOperationWrapper):
            print("    ✓ network is NetworkOperationWrapper instance")
        else:
            print(f"    ✗ network is wrong type: {type(module.network)}")
            sys.exit(1)
    else:
        print("    ✗ Base module missing 'network' attribute")
        sys.exit(1)

    # Check helper method exists
    if hasattr(module, 'install_packages_resilient'):
        print("    ✓ install_packages_resilient method exists")
    else:
        print("    ⚠ install_packages_resilient not found")

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Base module integration works"
else
    fail "Module integration failed"
fi

# ============================================================================
# TEST 6: Configuration Tests
# ============================================================================
section "TEST 6: Configuration Tests"

echo "[6.1] Checking resilience configuration..."
if grep -q "circuit_breaker:" config/default.yaml; then
    pass "circuit_breaker config exists"
else
    fail "circuit_breaker config missing"
fi

if grep -q "network_retry:" config/default.yaml; then
    pass "network_retry config exists"
else
    fail "network_retry config missing"
fi

echo "[6.2] Validating configuration structure..."
python3 << 'PYEOF'
import sys
import yaml

try:
    with open('config/default.yaml', 'r') as f:
        config = yaml.safe_load(f)

    perf = config.get('performance', {})

    # Check circuit breaker config
    cb = perf.get('circuit_breaker', {})
    if 'enabled' in cb and 'failure_threshold' in cb and 'timeout' in cb:
        print(f"    ✓ Circuit breaker config complete")
    else:
        print(f"    ⚠ Circuit breaker config incomplete")

    # Check retry config
    retry = perf.get('network_retry', {})
    if 'enabled' in retry and 'max_retries' in retry:
        print(f"    ✓ Retry config complete")
    else:
        print(f"    ⚠ Retry config incomplete")

    sys.exit(0)

except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    pass "Configuration validated"
else
    warn "Configuration may need review"
fi

# ============================================================================
# TEST 7: Running Test Suite
# ============================================================================
section "TEST 7: Running Resilience Test Suite"

echo "[7.1] Running network failure simulation tests..."
if command -v pytest &> /dev/null; then
    if [ -f "tests/resilience/test_network_failure_simulation.py" ]; then
        if pytest tests/resilience/test_network_failure_simulation.py -v --tb=short -m "not slow and not chaos" > /tmp/resilience_tests.txt 2>&1; then
            pass "Network failure simulation tests passed"
            TESTS_PASSED=$(grep -c "PASSED" /tmp/resilience_tests.txt || echo "0")
            echo "      Tests passed: $TESTS_PASSED"
        else
            fail "Some resilience tests failed (check /tmp/resilience_tests.txt)"
            TESTS_FAILED=$(grep -c "FAILED" /tmp/resilience_tests.txt || echo "0")
            echo "      Tests failed: $TESTS_FAILED"
        fi
    else
        warn "Resilience test file not found"
    fi
else
    warn "pytest not available, skipping test suite"
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

# Verdict
if [ $FAIL -eq 0 ]; then
    if [ $WARN -gt 5 ]; then
        echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║                                                           ║${NC}"
        echo -e "${YELLOW}║      ⚠️  PHASE 3 VALIDATION PASSED WITH WARNINGS         ║${NC}"
        echo -e "${YELLOW}║                                                           ║${NC}"
        echo -e "${YELLOW}║  Network resilience is functional but needs review.      ║${NC}"
        echo -e "${YELLOW}║  Address warnings before production deployment.          ║${NC}"
        echo -e "${YELLOW}║                                                           ║${NC}"
        echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                           ║${NC}"
        echo -e "${GREEN}║        ✅ PHASE 3 VALIDATION PASSED ✅                    ║${NC}"
        echo -e "${GREEN}║                                                           ║${NC}"
        echo -e "${GREEN}║  Network resilience layer is working correctly!          ║${NC}"
        echo -e "${GREEN}║  System can handle network failures gracefully.          ║${NC}"
        echo -e "${GREEN}║  Ready to proceed to Phase 4.                            ║${NC}"
        echo -e "${GREEN}║                                                           ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
        exit 0
    fi
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║          ❌ PHASE 3 VALIDATION FAILED ❌                  ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  Network resilience layer has issues.                    ║${NC}"
    echo -e "${RED}║  Fix the failures above before proceeding.               ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
