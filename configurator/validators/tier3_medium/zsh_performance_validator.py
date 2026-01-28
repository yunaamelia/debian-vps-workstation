"""
Zsh performance validator - Tier 3 Medium.

Measures shell startup time and warns if too slow.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

from configurator.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


class ZshPerformanceValidator(BaseValidator):
    """Validate zsh shell startup performance."""

    name = "Zsh Performance"
    severity = ValidationSeverity.MEDIUM
    auto_fix_available = False

    # Thresholds in milliseconds
    WARNING_THRESHOLD_MS = 500
    CRITICAL_THRESHOLD_MS = 2000

    def validate(self) -> ValidationResult:
        """
        Check zsh startup time.

        Returns:
            ValidationResult indicating if startup time is acceptable
        """
        zsh_path = shutil.which("zsh")
        if not zsh_path:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="Zsh not installed, skipping performance check",
            )

        # Determine user's zshrc
        user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))
        if user == "root":
            home = Path("/root")
        else:
            home = Path(f"/home/{user}")

        zshrc = home / ".zshrc"
        if not zshrc.exists():
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="No .zshrc to benchmark",
            )

        # Measure startup time (average of 3 runs)
        times = []
        for _ in range(3):
            try:
                start = time.perf_counter()
                result = subprocess.run(
                    [zsh_path, "-i", "-c", "exit"],
                    capture_output=True,
                    timeout=10,
                    env={**os.environ, "HOME": str(home)},
                )
                end = time.perf_counter()
                if result.returncode == 0:
                    times.append((end - start) * 1000)  # Convert to ms
            except subprocess.TimeoutExpired:
                return ValidationResult(
                    validator_name=self.name,
                    severity=ValidationSeverity.HIGH,
                    passed=False,
                    message="Zsh startup timed out (>10s)",
                    fix_suggestion="Check .zshrc for problematic plugins or slow operations",
                )
            except Exception:
                pass

        if not times:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="Could not measure zsh startup time",
            )

        avg_time = sum(times) / len(times)

        if avg_time > self.CRITICAL_THRESHOLD_MS:
            return ValidationResult(
                validator_name=self.name,
                severity=ValidationSeverity.HIGH,
                passed=False,
                message=f"Zsh startup is very slow: {avg_time:.0f}ms",
                details=f"Threshold: {self.CRITICAL_THRESHOLD_MS}ms",
                current_value=f"{avg_time:.0f}ms",
                fix_suggestion=(
                    "Consider lazy-loading plugins, removing unused plugins, "
                    "or profiling with 'zprof'"
                ),
            )

        if avg_time > self.WARNING_THRESHOLD_MS:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,  # Pass with warning
                message=f"Zsh startup is slow: {avg_time:.0f}ms",
                details=f"Recommended: <{self.WARNING_THRESHOLD_MS}ms",
                current_value=f"{avg_time:.0f}ms",
                fix_suggestion="Consider optimizing plugin loading",
            )

        return ValidationResult(
            validator_name=self.name,
            severity=self.severity,
            passed=True,
            message=f"Zsh startup time is good: {avg_time:.0f}ms",
            current_value=f"{avg_time:.0f}ms",
        )
