# PROMPT 2.1: CIS BENCHMARK SCANNER IMPLEMENTATION

## 📋 Context

The Center for Internet Security (CIS) Benchmarks are the global standard for secure configuration. We need an automated scanner to verify Debian/Ubuntu servers against these benchmarks (e.g., File permissions, Kernel parameters, SSH config).

## 🎯 Objective

Implement the `CISScanner` engine in `configurator/security/cis_scanner.py` that can load definitions, execute checks, and report compliance.

## 🛠️ Requirements

### Functional

1. **Definitions**: Store checks in YAML/JSON (id, description, audit_command, remediation_command).
2. **Execution**: Run shell commands to verify state.
3. **Remediation**: (Optional/Interactive) Run commands to fix failed checks.
4. **Reporting**: Generate an HTML/PDF report of pass/fail status.

### Non-Functional

1. **Safety**: Audit commands must be read-only. Remediation must be careful.
2. **Extensibility**: Easy to add new checks.

## 📝 Specifications

### check_definitions.yaml

```yaml
checks:
  - id: "1.1.1.1"
    name: "Ensure mounting of cramfs filesystems is disabled"
    audit: "modprobe -n -v cramfs | grep -E 'install /bin/true'"
    remediate: "echo 'install cramfs /bin/true' > /etc/modprobe.d/cramfs.conf"
    type: "filesystem"
```

### Class Signature (`configurator/security/cis_scanner.py`)

```python
@dataclass
class ScanResult:
    check_id: str
    status: str # PASS, FAIL, ERROR
    output: str

class CISScanner:
    def __init__(self, definitions_path: str):
        pass

    def run_scan(self, profile: str = "level1") -> List[ScanResult]:
        pass

    def generate_report(self, results: List[ScanResult], format: str = "html"):
        pass
```

## 🪜 Implementation Steps

1. **Data Structure**: Create `configurator/security/checks.yaml` with 5 sample CIS checks.
2. **Scanner Logic**:
    - Load YAML.
    - Loop through checks.
    - Execute `subprocess.run(check['audit'])`.
    - Check return code/output.
3. **Reporter**:
    - Use Jinja2 to create a simple HTML template.
    - Render `results` into HTML.
4. **CLI Integration**:
    - Add command `vps-configurator security cis-scan`.

## 🔍 Validation Checklist

- [ ] Scanner parses YAML correctly.
- [ ] Correctly identifies PASS vs FAIL based on exit code.
- [ ] HTML report is generated.
- [ ] Does not modify system state during 'scan' mode.

---

**Output**: Python code for scanner and sample YAML definitions.
