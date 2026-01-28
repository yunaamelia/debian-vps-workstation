"""
Zsh config integrity validator - Tier 2 High.

Validates .zshrc syntax before and after changes.
"""

import subprocess
from pathlib import Path

from configurator.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


class ZshConfigIntegrityValidator(BaseValidator):
    """Validate zsh configuration file syntax."""

    name = "Zsh Configuration Integrity"
    severity = ValidationSeverity.HIGH
    auto_fix_available = False

    def validate(self) -> ValidationResult:
        """
        Check if .zshrc has valid zsh syntax.

        Returns:
            ValidationResult indicating if .zshrc is valid
        """
        import os
        import shutil

        # Determine home directory
        user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))
        if user == "root":
            home = Path("/root")
        else:
            home = Path(f"/home/{user}")

        zshrc = home / ".zshrc"

        # Check if .zshrc exists
        if not zshrc.exists():
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="No .zshrc file to validate (will be created)",
                current_value="Not found",
            )

        # Check if zsh is available for syntax checking
        zsh_path = shutil.which("zsh")
        if not zsh_path:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="Cannot validate .zshrc syntax (zsh not installed)",
                details="Syntax validation skipped",
            )

        # Run syntax check
        try:
            result = subprocess.run(
                [zsh_path, "-n", str(zshrc)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown syntax error"
                return ValidationResult(
                    validator_name=self.name,
                    severity=self.severity,
                    passed=False,
                    message="Zsh configuration has syntax errors",
                    details=error_msg,
                    current_value=str(zshrc),
                    fix_suggestion="Review and fix .zshrc syntax errors",
                )

            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="Zsh configuration syntax is valid",
                details=str(zshrc),
                current_value="Valid syntax",
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message="Zsh syntax check timed out",
                details="The syntax check took too long",
                fix_suggestion="Check .zshrc for infinite loops or complex logic",
            )
        except Exception as e:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=True,
                message="Could not validate .zshrc syntax",
                details=str(e),
            )
