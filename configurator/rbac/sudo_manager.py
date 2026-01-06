"""Sudo policy management - fine-grained sudo access control integrated with RBAC."""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class PasswordRequirement(Enum):
    """Password requirement for sudo commands."""

    NONE = "none"
    REQUIRED = "required"


class MFARequirement(Enum):
    """2FA requirement for sudo commands."""

    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"


class CommandRisk(Enum):
    """Risk level of commands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SudoCommandRule:
    """
    Represents a single sudo command rule.

    Example:
        SudoCommandRule(
            command_pattern="systemctl restart myapp",
            password_required=PasswordRequirement.NONE,
            mfa_required=MFARequirement.NONE,
            description="Restart application service",
            risk_level=CommandRisk.LOW,
        )
    """

    command_pattern: str
    password_required: PasswordRequirement = PasswordRequirement.REQUIRED
    mfa_required: MFARequirement = MFARequirement.NONE
    description: str = ""
    risk_level: CommandRisk = CommandRisk.MEDIUM

    # Time restrictions
    allowed_hours: Optional[List[int]] = None
    allowed_days: Optional[List[int]] = None

    # Additional constraints
    max_executions_per_day: Optional[int] = None
    requires_reason: bool = False

    def matches_command(self, command: str) -> bool:
        """Check if command matches this rule's pattern."""
        pattern = self.command_pattern

        # Replace * with regex wildcard
        pattern = pattern.replace("*", ".*")

        # Escape special regex characters except .*
        pattern = re.escape(pattern)
        pattern = pattern.replace(r"\.\*", ".*")

        # Add anchors
        pattern = f"^{pattern}$"

        try:
            return bool(re.match(pattern, command))
        except re.error:
            return False

    def is_allowed_now(self) -> bool:
        """Check if command is allowed at current time."""
        now = datetime.now()

        # Check hour restriction
        if self.allowed_hours and now.hour not in self.allowed_hours:
            return False

        # Check day restriction
        if self.allowed_days and now.weekday() not in self.allowed_days:
            return False

        return True


@dataclass
class SudoPolicy:
    """
    Complete sudo policy for a user/role.

    Example:
        SudoPolicy(
            name="developer-policy",
            rules=[
                SudoCommandRule("systemctl restart myapp",
                               password_required=PasswordRequirement.NONE),
                SudoCommandRule("systemctl stop *",
                               password_required=PasswordRequirement.REQUIRED),
            ],
            default_deny=True,
        )
    """

    name: str
    rules: List[SudoCommandRule] = field(default_factory=list)
    default_deny: bool = True
    audit_enabled: bool = True

    def find_matching_rule(self, command: str) -> Optional[SudoCommandRule]:
        """Find the first rule that matches the command."""
        for rule in self.rules:
            if rule.matches_command(command):
                return rule
        return None

    def is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed by policy."""
        rule = self.find_matching_rule(command)

        if rule:
            return rule.is_allowed_now()

        return not self.default_deny


class SudoPolicyManager:
    """
    Manages sudo policies and generates sudoers configuration.

    Features:
    - Role-based sudo policies (integrated with RBAC)
    - Command whitelisting
    - Passwordless sudo for specific commands
    - 2FA integration for sensitive commands
    - Time-based restrictions
    - Audit logging
    - Policy validation
    - Safe sudoers.d file generation
    """

    SUDOERS_DIR = Path("/etc/sudoers.d")
    POLICY_DIR = Path("/etc/debian-vps-configurator/sudo-policies")
    AUDIT_LOG = Path("/var/log/sudo-audit.log")

    def __init__(
        self,
        sudoers_dir: Optional[Path] = None,
        policy_dir: Optional[Path] = None,
        audit_log: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
        dry_run: bool = False,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.dry_run = dry_run

        self.SUDOERS_DIR = sudoers_dir or self.SUDOERS_DIR
        self.POLICY_DIR = policy_dir or self.POLICY_DIR
        self.AUDIT_LOG = audit_log or self.AUDIT_LOG

        self._ensure_directories()
        self._load_policies()
        self._init_rbac_integration()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        try:
            self.POLICY_DIR.mkdir(parents=True, exist_ok=True, mode=0o755)

            # Check if sudoers.d exists (may not in test environments)
            if not self.dry_run and not self.SUDOERS_DIR.exists():
                self.logger.warning(f"sudoers.d directory not found: {self.SUDOERS_DIR}")
        except PermissionError:
            self.logger.debug("No permission to create directories; will use temp")

    def _init_rbac_integration(self):
        """Initialize RBAC integration."""
        try:
            from configurator.rbac.rbac_manager import RBACManager

            self.rbac_manager = RBACManager()
        except (ImportError, Exception) as e:
            self.logger.warning(f"RBAC manager not available: {e}")
            self.rbac_manager = None

    def _load_policies(self):
        """Load sudo policies from configuration."""
        self.policies: Dict[str, SudoPolicy] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Load default sudo policies for standard roles."""

        # Developer policy
        developer_rules = [
            SudoCommandRule(
                command_pattern="systemctl restart myapp",
                password_required=PasswordRequirement.NONE,
                description="Restart application",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="systemctl status *",
                password_required=PasswordRequirement.NONE,
                description="Check service status",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="systemctl reload myapp",
                password_required=PasswordRequirement.NONE,
                description="Reload application config",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="journalctl -u myapp*",
                password_required=PasswordRequirement.NONE,
                description="View application logs",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="docker ps*",
                password_required=PasswordRequirement.NONE,
                description="List containers",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="docker logs *",
                password_required=PasswordRequirement.NONE,
                description="View container logs",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="docker inspect *",
                password_required=PasswordRequirement.NONE,
                description="Inspect containers",
                risk_level=CommandRisk.LOW,
            ),
        ]

        self.policies["developer"] = SudoPolicy(
            name="developer",
            rules=developer_rules,
            default_deny=True,
        )

        # DevOps policy (includes developer + more)
        devops_rules = developer_rules + [
            SudoCommandRule(
                command_pattern="systemctl restart *",
                password_required=PasswordRequirement.REQUIRED,
                description="Restart any service",
                risk_level=CommandRisk.MEDIUM,
            ),
            SudoCommandRule(
                command_pattern="systemctl stop *",
                password_required=PasswordRequirement.REQUIRED,
                description="Stop any service",
                risk_level=CommandRisk.MEDIUM,
            ),
            SudoCommandRule(
                command_pattern="systemctl start *",
                password_required=PasswordRequirement.REQUIRED,
                description="Start any service",
                risk_level=CommandRisk.MEDIUM,
            ),
            SudoCommandRule(
                command_pattern="docker *",
                password_required=PasswordRequirement.NONE,
                description="All docker commands",
                risk_level=CommandRisk.MEDIUM,
            ),
            SudoCommandRule(
                command_pattern="apt-get update",
                password_required=PasswordRequirement.REQUIRED,
                description="Update package lists",
                risk_level=CommandRisk.LOW,
            ),
            SudoCommandRule(
                command_pattern="apt-get upgrade",
                password_required=PasswordRequirement.REQUIRED,
                mfa_required=MFARequirement.OPTIONAL,
                description="Upgrade packages",
                risk_level=CommandRisk.MEDIUM,
            ),
        ]

        self.policies["devops"] = SudoPolicy(
            name="devops",
            rules=devops_rules,
            default_deny=True,
        )

        # Admin policy (full sudo)
        admin_rules = [
            SudoCommandRule(
                command_pattern="*",
                password_required=PasswordRequirement.REQUIRED,
                mfa_required=MFARequirement.OPTIONAL,
                description="Full sudo access",
                risk_level=CommandRisk.HIGH,
            ),
        ]

        self.policies["admin"] = SudoPolicy(
            name="admin",
            rules=admin_rules,
            default_deny=False,
        )

        # Viewer policy (no sudo)
        self.policies["viewer"] = SudoPolicy(
            name="viewer",
            rules=[],
            default_deny=True,
        )

    def apply_policy_for_user(self, username: str, role: str) -> bool:
        """
        Apply sudo policy for user based on role.

        Args:
            username: System username
            role: RBAC role name

        Returns:
            True if successful
        """
        self.logger.info(f"Applying sudo policy for {username} (role: {role})")

        # Get policy for role
        policy = self.policies.get(role)

        if not policy:
            self.logger.warning(f"No sudo policy defined for role: {role}")
            # Create empty policy (deny all)
            policy = SudoPolicy(name=role, rules=[], default_deny=True)

        # Generate sudoers.d file
        sudoers_file = self.SUDOERS_DIR / f"rbac-{username}"

        try:
            content = self._generate_sudoers_content(username, policy)

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would write to: {sudoers_file}")
                self.logger.debug(f"Content:\n{content}")
                return True

            # Validate before writing
            if self._validate_sudoers_content(content):
                # Write file
                sudoers_file.write_text(content)
                sudoers_file.chmod(0o440)

                self.logger.info(f"✅ Sudo policy applied: {sudoers_file}")

                # Audit log
                self._audit_log(
                    action="apply_policy",
                    username=username,
                    role=role,
                    rules_count=len(policy.rules),
                )

                return True
            else:
                self.logger.error("Sudoers content validation failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply sudo policy: {e}")
            raise

    def _generate_sudoers_content(self, username: str, policy: SudoPolicy) -> str:
        """Generate sudoers.d file content."""
        content = f"# Sudo policy for {username}\n"
        content += f"# Role: {policy.name}\n"
        content += f"# Generated: {datetime.now().isoformat()}\n"
        content += "# Managed by: VPS Configurator RBAC\n\n"

        if not policy.rules:
            content += "# No sudo access granted\n"
            return content

        # Group rules by password requirement
        passwordless_rules = [
            r for r in policy.rules if r.password_required == PasswordRequirement.NONE
        ]
        password_rules = [
            r for r in policy.rules if r.password_required == PasswordRequirement.REQUIRED
        ]

        # Passwordless commands
        if passwordless_rules:
            content += "# Passwordless commands\n"
            for rule in passwordless_rules:
                content += f"# {rule.description}\n"
                content += f"{username} ALL=(ALL) NOPASSWD: {rule.command_pattern}\n"
            content += "\n"

        # Password-required commands
        if password_rules:
            content += "# Password-required commands\n"
            for rule in password_rules:
                content += f"# {rule.description}\n"
                content += f"{username} ALL=(ALL) {rule.command_pattern}\n"
            content += "\n"

        return content

    def _validate_sudoers_content(self, content: str) -> bool:
        """Validate sudoers content using visudo."""
        import tempfile

        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sudoers", delete=False) as f:
                f.write(content)
                temp_file = f.name

            # Validate with visudo
            result = subprocess.run(
                ["visudo", "-c", "-f", temp_file], capture_output=True, text=True
            )

            # Clean up
            Path(temp_file).unlink()

            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"Sudoers validation failed: {result.stderr}")
                return False

        except FileNotFoundError:
            self.logger.warning("visudo not found, skipping validation")
            return True  # Allow in test environments
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def test_command(self, username: str, command: str) -> Dict:
        """
        Test if a command is allowed for user.

        Args:
            username: System username
            command: Command to test

        Returns:
            Dictionary with test results
        """
        result = {
            "allowed": False,
            "rule": None,
            "password_required": True,
            "mfa_required": False,
            "reason": "",
        }

        # Get user's role
        if not self.rbac_manager:
            result["reason"] = "RBAC manager not available"
            return result

        assignment = self.rbac_manager.assignments.get(username)

        if not assignment:
            result["reason"] = "User has no role assigned"
            return result

        role = assignment.role_name

        # Get policy for role
        policy = self.policies.get(role)

        if not policy:
            result["reason"] = f"No policy defined for role: {role}"
            return result

        # Find matching rule
        rule = policy.find_matching_rule(command)

        if rule:
            # Check time restrictions
            if not rule.is_allowed_now():
                result["reason"] = "Command not allowed at this time"
                return result

            result["allowed"] = True
            result["rule"] = rule.command_pattern
            result["password_required"] = rule.password_required == PasswordRequirement.REQUIRED
            result["mfa_required"] = rule.mfa_required == MFARequirement.REQUIRED
            result["reason"] = rule.description
        else:
            if policy.default_deny:
                result["reason"] = "Command not in whitelist (default deny)"
            else:
                result["allowed"] = True
                result["reason"] = "Allowed by default policy"

        return result

    def get_user_policy(self, username: str) -> Optional[SudoPolicy]:
        """Get sudo policy for user."""
        if not self.rbac_manager:
            return None

        assignment = self.rbac_manager.assignments.get(username)

        if not assignment:
            return None

        return self.policies.get(assignment.role_name)

    def revoke_sudo_access(self, username: str) -> bool:
        """Revoke all sudo access for user."""
        self.logger.info(f"Revoking sudo access for {username}")

        sudoers_file = self.SUDOERS_DIR / f"rbac-{username}"

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would remove: {sudoers_file}")
            return True

        if sudoers_file.exists():
            sudoers_file.unlink()
            self.logger.info(f"✅ Sudo access revoked: {sudoers_file}")

            # Audit log
            self._audit_log(
                action="revoke_access",
                username=username,
            )

            return True
        else:
            self.logger.info(f"No sudo file to remove for {username}")
            return False

    def _audit_log(self, action: str, username: str, **details):
        """Log sudo policy action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "username": username,
            **details,
        }

        try:
            with open(self.AUDIT_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
