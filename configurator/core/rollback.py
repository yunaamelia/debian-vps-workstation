"""
Rollback manager for failed installations.

Tracks changes made during installation and can undo them if needed.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.utils.command import run_command
from configurator.utils.file import restore_file

# Rollback state file
ROLLBACK_STATE_FILE = Path("/var/lib/debian-vps-configurator/rollback-state.json")


@dataclass
class RollbackAction:
    """A single action that can be rolled back."""

    action_type: str  # "command", "file_restore", "package_remove", "service_stop"
    description: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "action_type": self.action_type,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackAction":
        """Create from dictionary."""
        return cls(
            action_type=data["action_type"],
            description=data["description"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class RollbackManager:
    """
    Manages rollback of installation changes.

    Tracks all changes made during installation and provides
    the ability to undo them in reverse order.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize rollback manager.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.actions: List[RollbackAction] = []
        self.state_file = ROLLBACK_STATE_FILE

    def add_command(self, rollback_command: str, description: str = "") -> None:
        """
        Add a command to be executed during rollback.

        Args:
            rollback_command: Shell command to undo the change
            description: Human-readable description
        """
        action = RollbackAction(
            action_type="command",
            description=description or f"Run: {rollback_command}",
            data={"command": rollback_command},
        )
        self.actions.append(action)
        self._save_state()

    def add_file_restore(self, backup_path: str, original_path: str, description: str = "") -> None:
        """
        Add a file restoration to rollback.

        Args:
            backup_path: Path to backup file
            original_path: Original file path to restore to
            description: Human-readable description
        """
        action = RollbackAction(
            action_type="file_restore",
            description=description or f"Restore: {original_path}",
            data={
                "backup_path": backup_path,
                "original_path": original_path,
            },
        )
        self.actions.append(action)
        self._save_state()

    def add_package_remove(self, packages: List[str], description: str = "") -> None:
        """
        Add packages to be removed during rollback.

        Args:
            packages: List of package names
            description: Human-readable description
        """
        action = RollbackAction(
            action_type="package_remove",
            description=description or f"Remove packages: {', '.join(packages)}",
            data={"packages": packages},
        )
        self.actions.append(action)
        self._save_state()

    def add_service_stop(self, service: str, description: str = "") -> None:
        """
        Add a service to be stopped during rollback.

        Args:
            service: Service name
            description: Human-readable description
        """
        action = RollbackAction(
            action_type="service_stop",
            description=description or f"Stop service: {service}",
            data={"service": service},
        )
        self.actions.append(action)
        self._save_state()

    def rollback(self, dry_run: bool = False) -> bool:
        """
        Execute rollback actions in reverse order.

        Args:
            dry_run: If True, only show what would be done

        Returns:
            True if rollback was successful
        """
        if not self.actions:
            self.logger.info("No rollback actions to execute")
            return True

        self.logger.info(f"Rolling back {len(self.actions)} actions...")

        errors = []

        # Execute in reverse order
        for action in reversed(self.actions):
            self.logger.info(f"  • {action.description}")

            if dry_run:
                continue

            try:
                self._execute_action(action)
            except Exception as e:
                self.logger.error(f"    Failed: {e}")
                errors.append((action, e))

        if errors:
            self.logger.warning(f"Rollback completed with {len(errors)} errors")
            return False

        # Clear state on successful rollback
        self.actions = []
        self._clear_state()

        self.logger.info("Rollback completed successfully")
        return True

    def _execute_action(self, action: RollbackAction) -> None:
        """Execute a single rollback action."""
        if action.action_type == "command":
            run_command(action.data["command"], check=False)

        elif action.action_type == "file_restore":
            restore_file(
                action.data["backup_path"],
                action.data["original_path"],
            )

        elif action.action_type == "package_remove":
            packages = " ".join(action.data["packages"])
            run_command(f"apt-get remove -y {packages}", check=False)

        elif action.action_type == "service_stop":
            run_command(f"systemctl stop {action.data['service']}", check=False)
            run_command(f"systemctl disable {action.data['service']}", check=False)

    def _save_state(self) -> None:
        """Save rollback state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {
                "actions": [a.to_dict() for a in self.actions],
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            self.logger.debug(f"Could not save rollback state: {e}")

    def _clear_state(self) -> None:
        """Clear saved rollback state."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except Exception as e:
            self.logger.debug(f"Could not clear rollback state: {e}")

    def load_state(self) -> bool:
        """
        Load rollback state from file.

        Returns:
            True if state was loaded
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)

            self.actions = [RollbackAction.from_dict(a) for a in state.get("actions", [])]

            self.logger.info(f"Loaded {len(self.actions)} rollback actions from previous run")
            return True

        except Exception as e:
            self.logger.warning(f"Could not load rollback state: {e}")
            return False

    def get_summary(self) -> str:
        """Get a summary of pending rollback actions."""
        if not self.actions:
            return "No rollback actions pending"

        types: Dict[str, int] = {}
        for action in self.actions:
            types[action.action_type] = types.get(action.action_type, 0) + 1

        summary_parts = []
        for action_type, count in types.items():
            summary_parts.append(f"{count} {action_type}")

        return f"Rollback actions: {', '.join(summary_parts)}"
