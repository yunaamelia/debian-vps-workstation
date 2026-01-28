"""
Tool integration validator - Tier 2 High.

Validates that terminal tools (eza, bat, zoxide) integrations work together.
"""

import shutil
import subprocess

from configurator.validators.base import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
)


class ToolIntegrationValidator(BaseValidator):
    """Validate terminal tools integration."""

    name = "Terminal Tools Integration"
    severity = ValidationSeverity.HIGH
    auto_fix_available = False

    def validate(self) -> ValidationResult:
        """
        Check that terminal tools work together.

        Returns:
            ValidationResult indicating integration status
        """
        tools_status = []
        failed_tools = []

        # Check eza
        eza_path = shutil.which("eza")
        if eza_path:
            try:
                result = subprocess.run(
                    [eza_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    tools_status.append("eza: OK")
                else:
                    failed_tools.append("eza")
            except Exception:
                failed_tools.append("eza")
        else:
            tools_status.append("eza: Not installed")

        # Check bat/batcat
        bat_path = shutil.which("bat") or shutil.which("batcat")
        if bat_path:
            try:
                result = subprocess.run(
                    [bat_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    tools_status.append("bat: OK")
                else:
                    failed_tools.append("bat")
            except Exception:
                failed_tools.append("bat")
        else:
            tools_status.append("bat: Not installed")

        # Check zoxide
        zoxide_path = shutil.which("zoxide")
        if zoxide_path:
            try:
                result = subprocess.run(
                    [zoxide_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    tools_status.append("zoxide: OK")
                else:
                    failed_tools.append("zoxide")
            except Exception:
                failed_tools.append("zoxide")
        else:
            tools_status.append("zoxide: Not installed")

        if failed_tools:
            return ValidationResult(
                validator_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Tool(s) failed verification: {', '.join(failed_tools)}",
                details="\n".join(tools_status),
                fix_suggestion="Reinstall failing tools or check system PATH",
            )

        return ValidationResult(
            validator_name=self.name,
            severity=self.severity,
            passed=True,
            message="Terminal tools integration verified",
            details="\n".join(tools_status),
        )
