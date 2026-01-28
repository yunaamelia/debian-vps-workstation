"""
Zsh installed validator - Tier 1 Critical.

Validates that zsh shell is installed and executable.
"""

import shutil

from configurator.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


class ZshInstalledValidator(BaseValidator):
    """Validate zsh shell installation."""

    name = "Zsh Installation"
    severity = ValidationSeverity.CRITICAL
    auto_fix_available = True

    def validate(self) -> ValidationResult:
        """
        Check if zsh is installed and executable.

        Returns:
            ValidationResult indicating if zsh is available
        """
        zsh_path = shutil.which("zsh")

        if not zsh_path:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message="Zsh shell is not installed",
                details="The zsh binary was not found in PATH",
                fix_suggestion="Install zsh with: apt-get install zsh",
                auto_fixable=True,
            )

        # Verify it's executable
        import os

        if not os.access(zsh_path, os.X_OK):
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message="Zsh is installed but not executable",
                details=f"Found at {zsh_path} but lacks execute permission",
                current_value=zsh_path,
                fix_suggestion=f"Fix permissions: chmod +x {zsh_path}",
                auto_fixable=True,
            )

        # Get version info
        import subprocess

        try:
            result = subprocess.run(
                [zsh_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            version = "unknown"

        return ValidationResult(
            validator_name=self.name,
            severity=self.severity,
            passed=True,
            message="Zsh shell is installed",
            details=version,
            current_value=zsh_path,
        )

    def auto_fix(self) -> bool:
        """Install zsh automatically."""
        import subprocess

        try:
            subprocess.run(
                ["apt-get", "install", "-y", "zsh"],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
