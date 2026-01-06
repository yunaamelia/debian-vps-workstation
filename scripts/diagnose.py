#!/usr/bin/env python3
"""
VPS Configurator - Comprehensive Diagnostic and Validation Tool

This script provides detailed system diagnostics, validation,
and error analysis with comprehensive logging.

Usage:
    python3 diagnose.py [--verbose] [--output-dir DIR] [--fix]
"""

import argparse
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# Configuration
# ============================================================================
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    status: str  # PASS, FAIL, WARN, SKIP
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "error": self.error,
            "fix_suggestion": self.fix_suggestion,
        }


# ============================================================================
# Custom Logger with Color Support
# ============================================================================
class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support."""

    COLORS = {
        "DEBUG": "\033[0;35m",  # Purple
        "INFO": "\033[0;32m",  # Green
        "WARNING": "\033[1;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build message
        formatted = f"{color}[{timestamp}][{record.levelname}]{reset} {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{color}{self.formatException(record.exc_info)}{reset}"

        return formatted


class PlainFormatter(logging.Formatter):
    """Plain text formatter for file logging."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}][{record.levelname}][{record.funcName}:{record.lineno}] {record.getMessage()}"

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(log_file: Path, verbose: bool = False) -> logging.Logger:
    """Set up logging with both console and file handlers."""
    logger = logging.getLogger("vps_diagnose")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File handler
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(PlainFormatter())
    logger.addHandler(file_handler)

    return logger


# ============================================================================
# System Diagnostics
# ============================================================================
class SystemDiagnostics:
    """System-level diagnostic checks."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.results: List[DiagnosticResult] = []

    def run_all(self) -> List[DiagnosticResult]:
        """Run all system diagnostics."""
        self.logger.info("=" * 60)
        self.logger.info("Running System Diagnostics")
        self.logger.info("=" * 60)

        checks = [
            self.check_os,
            self.check_python,
            self.check_memory,
            self.check_disk,
            self.check_network,
            self.check_user_permissions,
            self.check_required_packages,
            self.check_optional_packages,
        ]

        for check in checks:
            try:
                result = check()
                self.results.append(result)
                self._log_result(result)
            except Exception as e:
                self.logger.error(f"Check {check.__name__} failed with exception: {e}")
                self.logger.debug(traceback.format_exc())
                self.results.append(
                    DiagnosticResult(
                        name=check.__name__,
                        status="FAIL",
                        message=f"Exception: {str(e)}",
                        error=traceback.format_exc(),
                    )
                )

        return self.results

    def _log_result(self, result: DiagnosticResult) -> None:
        """Log a diagnostic result."""
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(result.status, "❓")

        if result.status == "PASS":
            self.logger.info(f"{icon} {result.name}: {result.message}")
        elif result.status == "WARN":
            self.logger.warning(f"{icon} {result.name}: {result.message}")
        elif result.status == "FAIL":
            self.logger.error(f"{icon} {result.name}: {result.message}")
            if result.fix_suggestion:
                self.logger.info(f"   Fix: {result.fix_suggestion}")
        else:
            self.logger.info(f"{icon} {result.name}: {result.message}")

    def check_os(self) -> DiagnosticResult:
        """Check operating system compatibility."""
        self.logger.debug("Checking operating system...")

        details = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        }

        # Check for Debian-based
        os_id = ""
        if Path("/etc/os-release").exists():
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        os_id = line.strip().split("=")[1].strip('"')
                        details["os_id"] = os_id
                    if line.startswith("PRETTY_NAME="):
                        details["pretty_name"] = line.strip().split("=")[1].strip('"')

        if os_id in ("debian", "ubuntu") or platform.system() == "Linux":
            return DiagnosticResult(
                name="Operating System",
                status="PASS",
                message=f"Compatible OS: {details.get('pretty_name', platform.system())}",
                details=details,
            )
        else:
            return DiagnosticResult(
                name="Operating System",
                status="WARN",
                message=f"Non-Debian OS detected: {os_id}",
                details=details,
                fix_suggestion="This tool is optimized for Debian/Ubuntu systems",
            )

    def check_python(self) -> DiagnosticResult:
        """Check Python version and modules."""
        self.logger.debug("Checking Python environment...")

        version_info = sys.version_info
        details = {
            "version": f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            "executable": sys.executable,
            "platform": sys.platform,
        }

        if version_info.major >= 3 and version_info.minor >= 9:
            return DiagnosticResult(
                name="Python Version",
                status="PASS",
                message=f"Python {details['version']} ✓",
                details=details,
            )
        else:
            return DiagnosticResult(
                name="Python Version",
                status="FAIL",
                message=f"Python 3.9+ required, found {details['version']}",
                details=details,
                fix_suggestion="apt-get install python3.9 python3.9-venv",
            )

    def check_memory(self) -> DiagnosticResult:
        """Check available memory."""
        self.logger.debug("Checking memory...")

        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]
                        meminfo[key] = int(value)

            total_mb = meminfo.get("MemTotal", 0) / 1024
            available_mb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0)) / 1024

            details = {
                "total_mb": round(total_mb, 2),
                "available_mb": round(available_mb, 2),
                "usage_percent": (
                    round((1 - available_mb / total_mb) * 100, 2) if total_mb > 0 else 0
                ),
            }

            if available_mb >= 512:
                return DiagnosticResult(
                    name="Memory",
                    status="PASS",
                    message=f"{available_mb:.0f}MB available of {total_mb:.0f}MB total",
                    details=details,
                )
            elif available_mb >= 256:
                return DiagnosticResult(
                    name="Memory",
                    status="WARN",
                    message=f"Low memory: {available_mb:.0f}MB available",
                    details=details,
                    fix_suggestion="Consider adding swap or upgrading memory",
                )
            else:
                return DiagnosticResult(
                    name="Memory",
                    status="FAIL",
                    message=f"Insufficient memory: {available_mb:.0f}MB",
                    details=details,
                    fix_suggestion="Minimum 256MB required, 512MB recommended",
                )
        except Exception as e:
            return DiagnosticResult(
                name="Memory", status="SKIP", message=f"Cannot check memory: {e}", error=str(e)
            )

    def check_disk(self) -> DiagnosticResult:
        """Check disk space."""
        self.logger.debug("Checking disk space...")

        try:
            stat = os.statvfs("/")
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            used_percent = (1 - available_gb / total_gb) * 100

            details = {
                "total_gb": round(total_gb, 2),
                "available_gb": round(available_gb, 2),
                "used_percent": round(used_percent, 2),
            }

            if available_gb >= 2:
                return DiagnosticResult(
                    name="Disk Space",
                    status="PASS",
                    message=f"{available_gb:.1f}GB available ({used_percent:.0f}% used)",
                    details=details,
                )
            elif available_gb >= 1:
                return DiagnosticResult(
                    name="Disk Space",
                    status="WARN",
                    message=f"Low disk: {available_gb:.1f}GB available",
                    details=details,
                    fix_suggestion="Clean up unnecessary files or expand disk",
                )
            else:
                return DiagnosticResult(
                    name="Disk Space",
                    status="FAIL",
                    message=f"Critical: {available_gb:.1f}GB available",
                    details=details,
                    fix_suggestion="Immediate cleanup required",
                )
        except Exception as e:
            return DiagnosticResult(
                name="Disk Space", status="SKIP", message=f"Cannot check disk: {e}", error=str(e)
            )

    def check_network(self) -> DiagnosticResult:
        """Check network connectivity."""
        self.logger.debug("Checking network...")

        details = {"hostname": socket.gethostname()}

        try:
            # Get IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            details["ip_address"] = s.getsockname()[0]
            s.close()

            # Test DNS resolution
            socket.gethostbyname("github.com")
            details["dns_works"] = True

            # Test HTTPS connectivity
            result = subprocess.run(
                ["curl", "-sSf", "--max-time", "5", "https://github.com"],
                capture_output=True,
                timeout=10,
            )
            details["https_works"] = result.returncode == 0

            if details.get("https_works"):
                return DiagnosticResult(
                    name="Network",
                    status="PASS",
                    message=f"Connected ({details['ip_address']})",
                    details=details,
                )
            else:
                return DiagnosticResult(
                    name="Network",
                    status="WARN",
                    message="Limited connectivity",
                    details=details,
                    fix_suggestion="Check firewall rules",
                )

        except Exception as e:
            return DiagnosticResult(
                name="Network",
                status="FAIL",
                message=f"Network error: {e}",
                details=details,
                error=str(e),
                fix_suggestion="Check network configuration",
            )

    def check_user_permissions(self) -> DiagnosticResult:
        """Check user permissions."""
        self.logger.debug("Checking permissions...")

        details = {
            "uid": os.getuid(),
            "gid": os.getgid(),
            "username": os.environ.get("USER", "unknown"),
            "is_root": os.getuid() == 0,
        }

        # Check sudo access
        try:
            result = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)
            details["has_sudo"] = result.returncode == 0
        except Exception:
            details["has_sudo"] = False

        if details["is_root"]:
            return DiagnosticResult(
                name="Permissions",
                status="PASS",
                message="Running as root",
                details=details,
            )
        elif details.get("has_sudo"):
            return DiagnosticResult(
                name="Permissions",
                status="PASS",
                message=f"User {details['username']} has sudo access",
                details=details,
            )
        else:
            return DiagnosticResult(
                name="Permissions",
                status="WARN",
                message=f"Limited permissions (user: {details['username']})",
                details=details,
                fix_suggestion="Some features require root or sudo access",
            )

    def check_required_packages(self) -> DiagnosticResult:
        """Check required system packages."""
        self.logger.debug("Checking required packages...")

        required = ["git", "curl", "sudo"]
        found = []
        missing = []

        for pkg in required:
            if shutil.which(pkg):
                found.append(pkg)
            else:
                missing.append(pkg)

        details = {"found": found, "missing": missing}

        if not missing:
            return DiagnosticResult(
                name="Required Packages",
                status="PASS",
                message=f"All required packages installed: {', '.join(found)}",
                details=details,
            )
        else:
            return DiagnosticResult(
                name="Required Packages",
                status="FAIL",
                message=f"Missing: {', '.join(missing)}",
                details=details,
                fix_suggestion=f"apt-get install {' '.join(missing)}",
            )

    def check_optional_packages(self) -> DiagnosticResult:
        """Check optional packages for full functionality."""
        self.logger.debug("Checking optional packages...")

        optional = ["trivy", "grype", "certbot", "visudo", "ufw"]
        found = []
        missing = []

        for pkg in optional:
            if shutil.which(pkg):
                found.append(pkg)
            else:
                missing.append(pkg)

        details = {"found": found, "missing": missing}

        if not missing:
            return DiagnosticResult(
                name="Optional Packages",
                status="PASS",
                message=f"All optional packages: {', '.join(found)}",
                details=details,
            )
        else:
            return DiagnosticResult(
                name="Optional Packages",
                status="WARN" if found else "INFO",
                message=f"Optional missing: {', '.join(missing)}",
                details=details,
                fix_suggestion="Install for full security scanning capabilities",
            )


# ============================================================================
# VPS Configurator Diagnostics
# ============================================================================
class ConfiguratorDiagnostics:
    """VPS Configurator specific diagnostics."""

    def __init__(self, logger: logging.Logger, project_dir: Path):
        self.logger = logger
        self.project_dir = project_dir
        self.results: List[DiagnosticResult] = []

    def run_all(self) -> List[DiagnosticResult]:
        """Run all configurator diagnostics."""
        self.logger.info("=" * 60)
        self.logger.info("Running VPS Configurator Diagnostics")
        self.logger.info("=" * 60)

        checks = [
            self.check_installation,
            self.check_venv,
            self.check_imports,
            self.check_cli_tool,
            self.run_unit_tests,
            self.run_phase1_validation,
            self.run_phase2_validation,
            self.run_phase3_validation,
        ]

        for check in checks:
            try:
                result = check()
                self.results.append(result)
                self._log_result(result)
            except Exception as e:
                self.logger.error(f"Check {check.__name__} failed: {e}")
                self.logger.debug(traceback.format_exc())
                self.results.append(
                    DiagnosticResult(
                        name=check.__name__,
                        status="FAIL",
                        message=str(e),
                        error=traceback.format_exc(),
                    )
                )

        return self.results

    def _log_result(self, result: DiagnosticResult) -> None:
        """Log a diagnostic result."""
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(result.status, "❓")

        if result.status == "PASS":
            self.logger.info(f"{icon} {result.name}: {result.message}")
        elif result.status == "WARN":
            self.logger.warning(f"{icon} {result.name}: {result.message}")
        elif result.status == "FAIL":
            self.logger.error(f"{icon} {result.name}: {result.message}")
            if result.error:
                self.logger.debug(f"Error details:\n{result.error}")
            if result.fix_suggestion:
                self.logger.info(f"   ➜ Fix: {result.fix_suggestion}")
        else:
            self.logger.info(f"{icon} {result.name}: {result.message}")

    def check_installation(self) -> DiagnosticResult:
        """Check if VPS Configurator is installed."""
        self.logger.debug("Checking installation...")

        if not self.project_dir.exists():
            return DiagnosticResult(
                name="Installation",
                status="FAIL",
                message=f"Project directory not found: {self.project_dir}",
                fix_suggestion=f"git clone <repo> {self.project_dir}",
            )

        # Check for setup.py OR pyproject.toml
        has_setup = (self.project_dir / "setup.py").exists() or (
            self.project_dir / "pyproject.toml"
        ).exists()

        required_files = [
            "configurator/__init__.py",
            "tests/validation/final_validation_phase1.py",
        ]

        missing = [f for f in required_files if not (self.project_dir / f).exists()]
        if not has_setup:
            missing.append("setup.py or pyproject.toml")

        if missing:
            return DiagnosticResult(
                name="Installation",
                status="FAIL",
                message=f"Missing files: {', '.join(missing)}",
                fix_suggestion="Reinstall or update from repository",
            )

        return DiagnosticResult(
            name="Installation",
            status="PASS",
            message=f"Installed at {self.project_dir}",
        )

    def check_venv(self) -> DiagnosticResult:
        """Check virtual environment."""
        self.logger.debug("Checking virtual environment...")

        venv_path = self.project_dir / ".venv"
        python_path = venv_path / "bin" / "python"

        if not venv_path.exists():
            return DiagnosticResult(
                name="Virtual Environment",
                status="FAIL",
                message="Virtual environment not found",
                fix_suggestion="python3 -m venv .venv && source .venv/bin/activate && pip install -e .",
            )

        if not python_path.exists():
            return DiagnosticResult(
                name="Virtual Environment",
                status="FAIL",
                message="Python not found in venv",
                fix_suggestion="Recreate virtual environment",
            )

        return DiagnosticResult(
            name="Virtual Environment",
            status="PASS",
            message=f"Found at {venv_path}",
        )

    def check_imports(self) -> DiagnosticResult:
        """Check if all modules can be imported."""
        self.logger.debug("Checking imports...")

        # Add project to path
        if str(self.project_dir) not in sys.path:
            sys.path.insert(0, str(self.project_dir))

        modules = [
            "configurator.core.parallel",
            "configurator.core.package_cache",
            "configurator.core.lazy_loader",
            "configurator.security.cis_scanner",
            "configurator.security.mfa_manager",
            "configurator.rbac.rbac_manager",
            "configurator.users.lifecycle_manager",
        ]

        failed = []
        errors = {}

        for module in modules:
            try:
                __import__(module)
            except Exception as e:
                failed.append(module)
                errors[module] = str(e)

        if not failed:
            return DiagnosticResult(
                name="Module Imports",
                status="PASS",
                message=f"All {len(modules)} modules import successfully",
            )
        else:
            return DiagnosticResult(
                name="Module Imports",
                status="FAIL",
                message=f"Failed to import: {', '.join(failed)}",
                details=errors,
                fix_suggestion="pip install -e . to install dependencies",
            )

    def check_cli_tool(self) -> DiagnosticResult:
        """Check if CLI tool is accessible."""
        self.logger.debug("Checking CLI tool...")

        try:
            result = subprocess.run(
                ["vps-configurator", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return DiagnosticResult(
                    name="CLI Tool",
                    status="PASS",
                    message=f"vps-configurator {version}",
                )
            else:
                return DiagnosticResult(
                    name="CLI Tool",
                    status="WARN",
                    message="CLI tool found but returned non-zero",
                    details={"stderr": result.stderr},
                )

        except FileNotFoundError:
            return DiagnosticResult(
                name="CLI Tool",
                status="FAIL",
                message="vps-configurator not found in PATH",
                fix_suggestion="pip install -e . or add to PATH",
            )
        except Exception as e:
            return DiagnosticResult(
                name="CLI Tool",
                status="FAIL",
                message=str(e),
                error=traceback.format_exc(),
            )

    def run_unit_tests(self) -> DiagnosticResult:
        """Run unit tests."""
        self.logger.debug("Running unit tests...")

        try:
            python_path = self.project_dir / ".venv" / "bin" / "python"
            if not python_path.exists():
                python_path = Path(sys.executable)

            result = subprocess.run(
                [str(python_path), "-m", "pytest", "tests/", "-q", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=str(self.project_dir),
                timeout=300,
            )

            # Parse results
            output = result.stdout + result.stderr
            passed = 0
            failed = 0

            for line in output.split("\n"):
                if "passed" in line:
                    match = re.search(r"(\d+) passed", line)
                    if match:
                        passed = int(match.group(1))
                if "failed" in line:
                    match = re.search(r"(\d+) failed", line)
                    if match:
                        failed = int(match.group(1))

            details = {"passed": passed, "failed": failed, "output": output[-2000:]}

            if result.returncode == 0:
                return DiagnosticResult(
                    name="Unit Tests",
                    status="PASS",
                    message=f"{passed} tests passed",
                    details=details,
                )
            else:
                return DiagnosticResult(
                    name="Unit Tests",
                    status="FAIL" if failed > 0 else "WARN",
                    message=f"{passed} passed, {failed} failed",
                    details=details,
                    error=output[-1000:] if failed > 0 else None,
                )

        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                name="Unit Tests",
                status="FAIL",
                message="Tests timed out (>300s)",
            )
        except Exception as e:
            return DiagnosticResult(
                name="Unit Tests",
                status="FAIL",
                message=str(e),
                error=traceback.format_exc(),
            )

    def _run_validation_script(self, script_name: str, phase_name: str) -> DiagnosticResult:
        """Run a validation script."""
        self.logger.debug(f"Running {phase_name} validation...")

        script_path = self.project_dir / "tests" / "validation" / script_name

        if not script_path.exists():
            return DiagnosticResult(
                name=phase_name,
                status="SKIP",
                message=f"Script not found: {script_path}",
            )

        try:
            python_path = self.project_dir / ".venv" / "bin" / "python"
            if not python_path.exists():
                python_path = Path(sys.executable)

            result = subprocess.run(
                [str(python_path), str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_dir),
                timeout=120,
            )

            output = result.stdout + result.stderr

            # Check for pass/fail in output
            if result.returncode == 0:
                return DiagnosticResult(
                    name=phase_name,
                    status="PASS",
                    message="All validations passed",
                    details={"output": output[-2000:]},
                )
            else:
                return DiagnosticResult(
                    name=phase_name,
                    status="FAIL",
                    message="Some validations failed",
                    details={"output": output[-2000:]},
                    error=output[-1000:],
                )

        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                name=phase_name,
                status="FAIL",
                message="Validation timed out (>120s)",
            )
        except Exception as e:
            return DiagnosticResult(
                name=phase_name, status="FAIL", message=str(e), error=traceback.format_exc()
            )

    def run_phase1_validation(self) -> DiagnosticResult:
        return self._run_validation_script(
            "final_validation_phase1.py", "Phase 1: Architecture & Performance"
        )

    def run_phase2_validation(self) -> DiagnosticResult:
        return self._run_validation_script(
            "final_validation_phase2.py", "Phase 2: Security & Compliance"
        )

    def run_phase3_validation(self) -> DiagnosticResult:
        return self._run_validation_script(
            "final_validation_phase3.py", "Phase 3: User Management & RBAC"
        )


# ============================================================================
# Report Generator
# ============================================================================
class ReportGenerator:
    """Generate diagnostic reports."""

    def __init__(
        self,
        system_results: List[DiagnosticResult],
        configurator_results: List[DiagnosticResult],
        output_dir: Path,
    ):
        self.system_results = system_results
        self.configurator_results = configurator_results
        self.output_dir = output_dir

    def generate_markdown(self) -> Path:
        """Generate markdown report."""
        report_path = (
            self.output_dir / f"diagnostic-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        )

        with open(report_path, "w") as f:
            f.write("# VPS Configurator Diagnostic Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Hostname:** {socket.gethostname()}\n\n")

            # Summary
            f.write("## Summary\n\n")

            total_pass = sum(
                1 for r in self.system_results + self.configurator_results if r.status == "PASS"
            )
            total_fail = sum(
                1 for r in self.system_results + self.configurator_results if r.status == "FAIL"
            )
            total_warn = sum(
                1 for r in self.system_results + self.configurator_results if r.status == "WARN"
            )

            f.write("| Status | Count |\n")
            f.write("|--------|-------|\n")
            f.write(f"| ✅ PASS | {total_pass} |\n")
            f.write(f"| ⚠️ WARN | {total_warn} |\n")
            f.write(f"| ❌ FAIL | {total_fail} |\n\n")

            # System Results
            f.write("## System Diagnostics\n\n")
            f.write("| Check | Status | Message |\n")
            f.write("|-------|--------|----------|\n")
            for r in self.system_results:
                icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(r.status, "❓")
                f.write(f"| {r.name} | {icon} {r.status} | {r.message} |\n")

            # Configurator Results
            f.write("\n## Configurator Diagnostics\n\n")
            f.write("| Check | Status | Message |\n")
            f.write("|-------|--------|----------|\n")
            for r in self.configurator_results:
                icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(r.status, "❓")
                f.write(f"| {r.name} | {icon} {r.status} | {r.message} |\n")

            # Errors Section
            errors = [r for r in self.system_results + self.configurator_results if r.error]
            if errors:
                f.write("\n## Error Details\n\n")
                for r in errors:
                    f.write(f"### {r.name}\n\n")
                    f.write(f"```\n{r.error[:2000]}\n```\n\n")
                    if r.fix_suggestion:
                        f.write(f"**Fix:** {r.fix_suggestion}\n\n")

            # Recommendations
            fails = [r for r in self.system_results + self.configurator_results if r.fix_suggestion]
            if fails:
                f.write("\n## Recommended Actions\n\n")
                for i, r in enumerate(fails, 1):
                    f.write(f"{i}. **{r.name}**: {r.fix_suggestion}\n")

        return report_path

    def generate_json(self) -> Path:
        """Generate JSON report."""
        report_path = (
            self.output_dir / f"diagnostic-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )

        report = {
            "generated_at": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "system_diagnostics": [r.to_dict() for r in self.system_results],
            "configurator_diagnostics": [r.to_dict() for r in self.configurator_results],
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report_path


# ============================================================================
# Main
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="VPS Configurator Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("/var/log/vps-configurator"),
        help="Output directory for reports",
    )
    parser.add_argument(
        "-p",
        "--project-dir",
        type=Path,
        default=(
            Path(__file__).parent.parent if Path(__file__).parent.name == "scripts" else Path.cwd()
        ),
        help="Project directory",
    )
    parser.add_argument("--json", action="store_true", help="Also generate JSON report")

    args = parser.parse_args()

    # Setup output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = args.output_dir / f"diagnose-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    logger = setup_logging(log_file, args.verbose)

    logger.info("=" * 60)
    logger.info("VPS Configurator Diagnostic Tool")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Project dir: {args.project_dir}")

    # Run diagnostics
    system_diag = SystemDiagnostics(logger)
    system_results = system_diag.run_all()

    config_diag = ConfiguratorDiagnostics(logger, args.project_dir)
    config_results = config_diag.run_all()

    # Generate reports
    logger.info("=" * 60)
    logger.info("Generating Reports")
    logger.info("=" * 60)

    reporter = ReportGenerator(system_results, config_results, args.output_dir)

    md_report = reporter.generate_markdown()
    logger.info(f"Markdown report: {md_report}")

    if args.json:
        json_report = reporter.generate_json()
        logger.info(f"JSON report: {json_report}")

    # Summary
    total_fail = sum(1 for r in system_results + config_results if r.status == "FAIL")

    logger.info("=" * 60)
    if total_fail == 0:
        logger.info("✅ All diagnostics passed!")
    else:
        logger.warning(f"⚠️ {total_fail} issue(s) found. See report for details.")
    logger.info("=" * 60)

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
