#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "PHASE 2 VALIDATION - AUTOMATED TEST SEQUENCE"
echo "═══════════════════════════════════════════════════════════"

# 1. Check assertion completeness
echo -e "\n[1/8] Checking assertion completeness..."
python3 -c "
import ast
import glob
import sys
import os

print(f'CWD: {os.getcwd()}')
files = glob.glob('tests/modules/test_desktop*.py')
print(f'Found files: {files}')

incomplete = 0
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f'⚠️  Empty file: {file}')
                continue
            tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                has_assert = any(isinstance(n, ast.Assert) for n in ast.walk(node))
                # basic check for assertion helper calls like 'self.assert' or 'mock.assert'
                has_assert_call = False
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                         # check attribute calls like assert_called_with
                        if isinstance(subnode.func, ast.Attribute):
                             if 'assert' in subnode.func.attr:
                                 has_assert_call = True

                if not has_assert and not has_assert_call:
                    print(f'⚠️  No assertion in {file} :: {node.name}')
                    incomplete += 1
    except Exception as e:
        print(f'Error parsing {file}: {e}')

print(f'\nResult: {incomplete} tests without assertions')
"

# 2. Run unit tests
echo -e "\n[2/8] Running unit tests..."
pytest tests/modules/test_desktop*.py -v --tb=short

# 3. Check security test files exist
echo -e "\n[3/8] Checking security test files..."
for file in test_phase1_security test_phase2_security_penetration test_input_validation test_command_injection test_privilege_escalation; do
    if [ -f "tests/security/${file}.py" ]; then
        echo "✅ tests/security/${file}.py"
    else
        echo "❌ MISSING: tests/security/${file}.py"
    fi
done

# 4. Run security tests
echo -e "\n[4/8] Running security tests..."
if [ -d "tests/security" ]; then
    pytest tests/security/ -v --tb=short
else
    echo "tests/security directory not found or empty"
fi

# 5. Run integration tests
echo -e "\n[5/8] Running integration tests..."
if [ -d "tests/integration" ]; then
    pytest tests/integration/ -v --tb=short -m integration
else
     echo "tests/integration directory not found or empty"
fi

# 6. Generate coverage report
echo -e "\n[6/8] Generating coverage report..."
pytest tests/ --cov=configurator --cov-report=term --ignore=tests/performance/

# 7. Code quality checks
echo -e "\n[7/8] Running code quality checks..."
echo "Linting..."
flake8 tests/ --count --statistics --select=E9,F63,F7,F82
echo "Formatting check..."
black tests/ --check
echo "Import order check..."
isort tests/ --check-only

# 8. Full suite execution time
echo -e "\n[8/8] Measuring full suite execution time..."
time pytest tests/ -v --ignore=tests/performance/ --tb=line

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PHASE 2 VALIDATION COMPLETE"
echo "═══════════════════════════════════════════════════════════"
