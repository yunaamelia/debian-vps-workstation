# CIS Benchmark Compliance

## Overview
The **Centers for Internet Security (CIS) Benchmarks** are globally recognized best practices for securing IT systems. The Debian VPS Configurator includes a built-in scanner to assess and harden your Debian 13 system against the **CIS Debian Linux 12 Benchmark v3.0** (adapted for Debian 13).

## Features
- **Automated Scanning**: Checks 150+ security controls.
- **Scoring**: Calculates a compliance score (0-100%).
- **Reporting**: Generates HTML and JSON reports.
- **Auto-Remediation**: Can automatically fix common misconfigurations (SSH, sysctl, permissions).

## Usage

### Running a Scan
To run a basic compliance scan (Level 1 - Essential):
```bash
vps-configurator cis scan
```

To run a thorough scan (Level 2 - Defense-in-Depth):
```bash
vps-configurator cis scan --level 2
```

### Reporting
Reports are generated in `/var/log/vps-configurator/cis-reports/` (or `./cis-reports/` if not root).
You can specify formats:
```bash
vps-configurator cis scan --format html --format json
```

### Auto-Remediation
> [!WARNING]
> Auto-remediation changes system configuration files. While safe defaults are used, it is recommended to review the report first.

To automatically fix failed checks:
```bash
vps-configurator cis scan --auto-remediate
```
Or interactively after a scan.

## Covered Checks

### 1. Initial Setup
- Filesystem partitions (`/tmp`)
- Mount options (`nodev`, `nosuid`, `noexec`)

### 2. Services
- Remove xinetd
- Remove X Window System
- Remove Avahi Server

### 3. Network Configuration
- Disable packet redirect sending
- Disable source routed packets

### 4. Logging and Auditing
- Ensure `auditd` is installed and enabled

### 5. Access Control
- SSH Protocol 2
- Disable SSH Root Login
- Disable Empty Passwords

### 6. System Maintenance
- Permissions on critical files (`/etc/passwd`, `/etc/shadow`, `/etc/group`)

## Data Models
The system uses the following data structures defined in `configurator.security.cis_scanner`:
- `CISCheck`: Definition of a security control.
- `CheckResult`: Outcome of a check (PASS/FAIL).
- `ScanReport`: Implementation of the full scan results.

## Extending
New checks can be added by creating modules in `configurator/security/cis_checks/`.
