"""
Shell permission validator - Tier 1 Critical.

Validates that the user can modify shell configuration files.
"""

import os
from pathlib import Path

from configurator.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


class ShellPermissionValidator(BaseValidator):
    """Validate shell configuration permissions."""

    name = "Shell Configuration Permissions"
    severity = ValidationSeverity.CRITICAL
    auto_fix_available = False

    def validate(self) -> ValidationResult:
        """
        Check if user can modify shell configuration files.

        Returns:
            ValidationResult indicating if permissions are adequate
        """
        # Determine home directory
        user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))
        if user == "root":
            home = Path("/root")
        else:
            home = Path(f"/home/{user}")

        # Check home directory exists
        if not home.exists():
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Home directory does not exist: {home}",
                details=f"User: {user}",
                fix_suggestion=f"Create home directory: mkdir -p {home}",
            )

        # Check write access to home directory
        if not os.access(home, os.W_OK):
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Cannot write to home directory: {home}",
                details="Write permission denied",
                current_value=str(home),
                fix_suggestion=f"Fix permissions: chown {user}:{user} {home}",
            )

        # Check .zshrc if it exists
        zshrc = home / ".zshrc"
        if zshrc.exists() and not os.access(zshrc, os.W_OK):
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Cannot modify existing .zshrc: {zshrc}",
                details="File exists but is not writable",
                current_value=str(zshrc),
                fix_suggestion=f"Fix permissions: chmod u+w {zshrc}",
            )

        # Check .config directory for tool configs
        config_dir = home / ".config"
        if config_dir.exists() and not os.access(config_dir, os.W_OK):
            return ValidationResult(
                validator_name=self.name,
                severity=ValidationSeverity.HIGH,  # Downgrade - not critical
                passed=False,
                message=f"Cannot write to .config directory: {config_dir}",
                details="Tool configurations may fail",
                current_value=str(config_dir),
                fix_suggestion=f"Fix permissions: chown -R {user}:{user} {config_dir}",
            )

        return ValidationResult(
            validator_name=self.name,
            severity=self.severity,
            passed=True,
            message="Shell configuration permissions are adequate",
            details=f"Home directory: {home}",
            current_value=str(home),
        )
