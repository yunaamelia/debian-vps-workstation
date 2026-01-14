"""
Input Validation and Sanitization Module.

Centralized input validation to prevent injection attacks and
ensure data integrity across the application.

Validates:
- Usernames
- File paths
- Command arguments
- Configuration values
- Shell commands
"""

import logging
import re
import shlex
from pathlib import Path
from typing import Union


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class InputValidator:
    """
    Centralized input validation and sanitization.

    Prevents injection attacks and validates input formats.
    """

    # Common dangerous characters/patterns
    DANGEROUS_CHARS = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    DANGEROUS_PATTERNS = [
        r"\$\(",  # Command substitution
        r"`",  # Backticks
        r"&&",  # Command chaining
        r"\|\|",  # Command chaining
        r">\s*&",  # Redirection
    ]

    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initialize input validator.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.strict_mode = config.get("security_advanced.input_validation.strict_mode", True)
        self.log_failures = config.get(
            "security_advanced.input_validation.log_validation_failures", True
        )

        # Username pattern
        self.username_pattern = re.compile(
            config.get(
                "security_advanced.input_validation.username_pattern", r"^[a-z][a-z0-9_-]{2,31}$"
            )
        )

        # Path whitelist
        self.path_whitelist = [
            Path(p) for p in config.get("security_advanced.input_validation.path_whitelist", [])
        ]

        # Command whitelist
        self.command_whitelist_enabled = config.get(
            "security_advanced.input_validation.command_whitelist_enabled", False
        )

    def validate_username(self, username: str) -> bool:
        """
        Validate username format.

        Args:
            username: Username to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not username:
            return self._handle_failure("Username cannot be empty")

        if not self.username_pattern.match(username):
            return self._handle_failure(
                f"Invalid username format: {username}\n"
                f"Must match pattern: {self.username_pattern.pattern}"
            )

        # Additional checks
        if len(username) > 32:
            return self._handle_failure(f"Username too long: {username}")

        if username in ["root", "admin", "administrator"]:
            self.logger.warning(f"Using privileged username: {username}")

        return True

    def validate_path(self, path: Union[str, Path], must_exist: bool = False) -> bool:
        """
        Validate file path.

        Args:
            path: Path to validate
            must_exist: Whether path must exist

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        path = Path(path)

        # Check for path traversal
        if ".." in str(path):
            return self._handle_failure(f"Path traversal detected: {path}")

        # Check for dangerous characters
        path_str = str(path)
        for char in self.DANGEROUS_CHARS:
            if char in path_str:
                return self._handle_failure(f"Dangerous character in path: {char}")

        # Check against whitelist if enabled
        if self.path_whitelist:
            allowed = False
            for allowed_prefix in self.path_whitelist:
                try:
                    # Check if path is under allowed prefix
                    path.resolve().relative_to(allowed_prefix.resolve())
                    allowed = True
                    break
                except ValueError:
                    continue

            if not allowed:
                return self._handle_failure(f"Path not in whitelist: {path}")

        # Check existence if required
        if must_exist and not path.exists():
            return self._handle_failure(f"Path does not exist: {path}")

        # Check for symlink attacks
        if path.is_symlink():
            target = path.resolve()
            self.logger.warning(f"Symlink detected: {path} -> {target}")
            # Recursively validate target
            return self.validate_path(target, must_exist)

        return True

    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename.

        Args:
            filename: Filename to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not filename:
            return self._handle_failure("Filename cannot be empty")

        # Check for path separators
        if "/" in filename or "\\" in filename:
            return self._handle_failure(f"Path separators not allowed in filename: {filename}")

        # Check for dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in filename:
                return self._handle_failure(f"Dangerous character in filename: {char}")

        # Check for null bytes
        if "\x00" in filename:
            return self._handle_failure("Null byte in filename")

        # Check for hidden files (warning only)
        if filename.startswith("."):
            self.logger.warning(f"Hidden file: {filename}")

        return True

    def validate_command(self, command: str) -> bool:
        """
        Validate shell command for dangerous patterns.

        Args:
            command: Command string to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not command:
            return self._handle_failure("Command cannot be empty")

        # Check for specific dangerous sequences
        dangerous_sequences = [";", "&&", "||", "|", ">", "<", "`", "$(", "${"]
        for seq in dangerous_sequences:
            if seq in command:
                return self._handle_failure(f"Dangerous sequence in command: {seq}")

        # Check for null bytes
        if "\x00" in command:
            return self._handle_failure("Null byte in command")

        # Parse command
        try:
            parts = shlex.split(command)
            if not parts:
                return self._handle_failure("Empty command after parsing")

            # Get base command
            base_cmd = parts[0]

            # Check if command exists
            if not self._command_exists(base_cmd):
                self.logger.warning(f"Command not found: {base_cmd}")

        except ValueError as e:
            return self._handle_failure(f"Failed to parse command: {e}")

        return True

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not email:
            return self._handle_failure("Email cannot be empty")

        # Simple regex for email validation
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        if not email_pattern.match(email):
            return self._handle_failure(f"Invalid email format: {email}")

        return True

    def validate_port(self, port: Union[int, str]) -> bool:
        """
        Validate port number.

        Args:
            port: Port number to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        try:
            port_int = int(port)
        except (ValueError, TypeError):
            return self._handle_failure(f"Invalid port number: {port}")

        if port_int < 1 or port_int > 65535:
            return self._handle_failure(f"Port out of range: {port_int}")

        # Warn about privileged ports
        if port_int < 1024:
            self.logger.warning(f"Using privileged port: {port_int}")

        return True

    def validate_ip_address(self, ip: str) -> bool:
        """
        Validate IP address format.

        Args:
            ip: IP address to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not ip:
            return self._handle_failure("IP address cannot be empty")

        # IPv4 pattern
        ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")

        if ipv4_pattern.match(ip):
            # Validate octets
            octets = ip.split(".")
            for octet in octets:
                if int(octet) > 255:
                    return self._handle_failure(f"Invalid IP address: {ip}")
            return True

        # IPv6 pattern (simplified)
        ipv6_pattern = re.compile(r"^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$")
        if ipv6_pattern.match(ip):
            return True

        return self._handle_failure(f"Invalid IP address format: {ip}")

    def validate_domain(self, domain: str) -> bool:
        """
        Validate domain name format.

        Args:
            domain: Domain name to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails in strict mode
        """
        if not domain:
            return self._handle_failure("Domain cannot be empty")

        # Domain pattern
        domain_pattern = re.compile(
            r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )

        if not domain_pattern.match(domain):
            return self._handle_failure(f"Invalid domain format: {domain}")

        return True

    def sanitize_string(self, value: str, allow_spaces: bool = True) -> str:
        """
        Sanitize string by removing dangerous characters.

        Args:
            value: String to sanitize
            allow_spaces: Whether to allow spaces

        Returns:
            str: Sanitized string
        """
        # Remove null bytes
        value = value.replace("\x00", "")

        # Remove dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char == " " and allow_spaces:
                continue
            value = value.replace(char, "")

        return value

    def sanitize_path(self, path: Union[str, Path]) -> Path:
        """
        Sanitize file path.

        Args:
            path: Path to sanitize

        Returns:
            Path: Sanitized path
        """
        path = Path(path)

        # Remove path traversal
        parts = []
        for part in path.parts:
            if part != "..":
                parts.append(part)

        return Path(*parts) if parts else Path(".")

    def escape_shell_arg(self, arg: str) -> str:
        """
        Escape argument for safe shell execution.

        Args:
            arg: Argument to escape

        Returns:
            str: Escaped argument
        """
        return shlex.quote(arg)

    def _command_exists(self, command: str) -> bool:
        """Check if command exists on system."""
        try:
            from shutil import which

            return which(command) is not None
        except Exception:
            return True  # Assume exists if check fails

    def _handle_failure(self, message: str) -> bool:
        """
        Handle validation failure.

        Args:
            message: Failure message

        Returns:
            bool: False

        Raises:
            ValidationError: If in strict mode
        """
        if self.log_failures:
            self.logger.error(f"Validation failed: {message}")

        if self.strict_mode:
            raise ValidationError(message)

        return False


# Convenience functions for common validations


def validate_username(username: str, strict: bool = True) -> bool:
    """Quick username validation."""
    pattern = re.compile(r"^[a-z][a-z0-9_-]{2,31}$")
    valid = bool(pattern.match(username))
    if not valid and strict:
        raise ValidationError(f"Invalid username: {username}")
    return valid


def validate_path_safe(path: Union[str, Path]) -> bool:
    """Quick path safety check."""
    path_str = str(path)
    if ".." in path_str:
        return False
    for char in [";", "&", "|", "`", "$"]:
        if char in path_str:
            return False
    return True


def sanitize_filename(filename: str) -> str:
    """Quick filename sanitization."""
    # Remove path separators and dangerous characters
    safe = re.sub(r"[/\\;|&`$<>\n\r]", "", filename)
    # Remove leading dots
    safe = safe.lstrip(".")
    return safe


def escape_for_shell(value: str) -> str:
    """Escape value for safe shell usage."""
    return shlex.quote(value)

    def validate_xml_value(self, value: str) -> bool:
        """
        Validate value for XML safety (prevents XML injection).

        Args:
            value: Value to validate

        Returns:
            bool: True if safe for XML
        """
        if not value:
            return True

        try:
            # Check for XML special characters that could be used for injection
            dangerous_patterns = ["<script", "<?php", "<!entity", "<![cdata[", "-->", "]]>"]

            value_lower = value.lower()
            if any(pattern in value_lower for pattern in dangerous_patterns):
                return self._handle_failure(f"XML injection attempt detected: {value[:50]}")

            # Check for excessive special characters
            special_count = sum(1 for char in value if char in '<>&"\'"')
            if special_count > 5:
                return self._handle_failure(f"Too many XML special characters: {value[:50]}")

            return True

        except Exception as e:
            self.logger.error(f"XML validation error: {e}", exc_info=True)
            return False

    def escape_xml(self, value: str) -> str:
        """
        Escape XML special characters.

        Args:
            value: String to escape

        Returns:
            str: XML-safe string
        """
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;",
        }

        for char, replacement in replacements.items():
            value = value.replace(char, replacement)

        return value
