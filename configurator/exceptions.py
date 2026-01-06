"""
Custom exception hierarchy for beginner-friendly error messages.

Every exception includes:
- what: What happened (plain English)
- why: Why it happened (explanation)
- how: How to fix (actionable steps)
- docs_link: Link to relevant documentation (optional)
"""

from typing import Optional


class ConfiguratorError(Exception):
    """
    Base exception for all configurator errors.

    Provides beginner-friendly error messages with:
    - What happened
    - Why it happened
    - How to fix it
    - Optional documentation link
    """

    def __init__(
        self,
        what: str,
        why: str = "",
        how: str = "",
        docs_link: Optional[str] = None,
    ):
        self.what = what
        self.why = why
        self.how = how
        self.docs_link = docs_link

        message = self._format_message()
        super().__init__(message)

    def _format_message(self) -> str:
        """Format the error message in a user-friendly way."""
        lines = [
            "",
            "╔════════════════════════════════════════════════════════╗",
            "║                  ❌ ERROR OCCURRED                      ║",
            "╚════════════════════════════════════════════════════════╝",
            "",
            "WHAT HAPPENED:",
            f"  {self.what}",
        ]

        if self.why:
            lines.extend(
                [
                    "",
                    "WHY IT HAPPENED:",
                    f"  {self.why}",
                ]
            )

        if self.how:
            lines.extend(
                [
                    "",
                    "HOW TO FIX:",
                ]
            )
            for line in self.how.strip().split("\n"):
                lines.append(f"  {line}")

        if self.docs_link:
            lines.extend(
                [
                    "",
                    f"📖 More help: {self.docs_link}",
                ]
            )

        lines.extend(
            [
                "",
                "════════════════════════════════════════════════════════",
                "",
                "Need more help?",
                "  • View logs: tail -f /var/log/debian-vps-configurator/install.log",
                "  • Community: https://github.com/youruser/debian-vps-configurator/discussions",
                "  • Report bug: https://github.com/youruser/debian-vps-configurator/issues",
                "",
            ]
        )

        return "\n".join(lines)


class PrerequisiteError(ConfiguratorError):
    """
    Raised when system prerequisites are not met.

    Examples:
    - Wrong Debian version
    - Insufficient RAM or disk space
    - Missing root/sudo access
    - No internet connectivity
    """


class ConfigurationError(ConfiguratorError):
    """
    Raised when there's a configuration problem.

    Examples:
    - Invalid YAML syntax
    - Missing required configuration values
    - Invalid configuration values
    """


class ModuleExecutionError(ConfiguratorError):
    """
    Raised when a module fails during execution.

    Examples:
    - Package installation failed
    - Service failed to start
    - File creation failed
    """


class ValidationError(ConfiguratorError):
    """
    Raised when validation fails after installation.

    Examples:
    - Service not running after installation
    - Command not found after installation
    - Expected file not created
    """


class RollbackError(ConfiguratorError):
    """
    Raised when rollback fails.

    Examples:
    - Cannot undo changes
    - Backup not found
    - Restore operation failed
    """


class NetworkError(ConfiguratorError):
    """
    Raised for network-related errors.

    Examples:
    - Cannot reach package repository
    - Download failed
    - Connection timeout
    """


class UserCancelledError(ConfiguratorError):
    """
    Raised when user cancels an operation.

    This is a clean exit, not an error.
    """

    def __init__(self, message: str = "Operation cancelled by user"):
        super().__init__(
            what=message,
            why="You chose to cancel the operation",
            how="Run the command again when you're ready to proceed",
        )
