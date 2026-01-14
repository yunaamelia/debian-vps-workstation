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
                "  • Community: https://github.com/yunaamelia/debian-vps-workstation/discussions",
                "  • Report bug: https://github.com/yunaamelia/debian-vps-workstation/issues",
                "",
            ]
        )

        return "\n".join(lines)


class PrerequisiteError(ConfiguratorError):
    """
    Raised when system prerequisites are not met.

    Common Causes:
    - Wrong Debian version (requires Debian 12/13)
    - Insufficient RAM (<1GB) or disk space (<10GB)
    - Missing root/sudo access
    - No internet connectivity

    Resolution:
    Check system requirements at:
    https://github.com/yunaamelia/debian-vps-workstation#requirements
    """

    def __init__(self, requirement: str, current_value: str, **kwargs):
        what = f"System does not meet requirement: {requirement}"
        why = f"Current value: {current_value}"
        how = (
            "1. Check system specs: vps-configurator check-system\n"
            "2. Review requirements: cat README.md | grep -A 10 'Requirements'\n"
            "3. Upgrade system or adjust configuration"
        )
        super().__init__(what=what, why=why, how=how, **kwargs)


class ConfigurationError(ConfiguratorError):
    """
    Raised when there's a configuration problem.

    Common Causes:
    - Invalid YAML syntax
    - Missing required configuration values
    - Invalid configuration values (wrong type, out of range)
    - Conflicting configuration options

    Resolution:
    Validate your configuration file with:
    vps-configurator validate --config your-config.yaml
    """

    def __init__(
        self,
        config_key: Optional[str] = None,
        issue: Optional[str] = None,
        what: Optional[str] = None,
        why: Optional[str] = None,
        how: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize ConfigurationError.

        Can be initialized in two ways:
        1. With config_key and issue (structured)
        2. With what, why, how (direct)
        """
        if what:
            # Direct initialization
            super().__init__(what=what, why=why or "", how=how or "", **kwargs)
        elif config_key and issue:
            # Structured initialization
            generated_what = f"Configuration error in '{config_key}'"
            generated_why = issue
            generated_how = (
                "1. Validate config: vps-configurator validate --config <file>\n"
                "2. Check syntax: yamllint config/your-config.yaml\n"
                "3. Compare with: config/default.yaml (working example)"
            )
            super().__init__(what=generated_what, why=generated_why, how=generated_how, **kwargs)
        else:
            raise ValueError(
                "ConfigurationError requires either ('what') or ('config_key' and 'issue')"
            )


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

    Common Causes:
    - Cannot undo changes (files already deleted)
    - Backup not found or corrupted
    - Restore operation failed (permission denied)
    - Package removal conflicts

    Manual Recovery:
    1. Check rollback log: /var/log/vps-configurator/rollback.log
    2. Identify failed operation
    3. Manually revert changes
    4. Use: vps-configurator rollback --force (if safe)
    """

    def __init__(self, module_name: str, failed_operation: str, **kwargs):
        what = f"Rollback failed for module '{module_name}'"
        why = f"Failed operation: {failed_operation}"
        how = (
            "1. Check rollback log: tail -50 /var/log/vps-configurator/rollback.log\n"
            "2. Manual cleanup may be required\n"
            "3. See: docs/advanced/rollback-behavior.md"
        )
        super().__init__(what=what, why=why, how=how, **kwargs)


class NetworkError(ConfiguratorError):
    """
    Raised for network-related errors.

    Common Causes:
    - Cannot reach package repository (DNS failure)
    - Download failed (timeout, connection reset)
    - Connection timeout (slow network)
    - Firewall blocking outbound connections

    Troubleshooting:
    1. Check internet: ping -c 3 8.8.8.8
    2. Check DNS: ping -c 3 deb.debian.org
    3. Check firewall: iptables -L -n -v
    4. Try again: Network issues may be temporary
    """

    def __init__(self, url: str, error_details: str, **kwargs):
        what = "Network operation failed"
        why = f"Cannot access: {url}\nError: {error_details}"
        how = (
            "1. Check internet: ping -c 3 8.8.8.8\n"
            "2. Check DNS: host deb.debian.org\n"
            "3. Check proxy/firewall settings\n"
            "4. Retry: vps-configurator install --retry"
        )
        super().__init__(what=what, why=why, how=how, **kwargs)


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
