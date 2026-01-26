"""
State manager with SQLite persistence.

Manages installation state with database persistence for resume capability.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from configurator.core.state.models import (
    InstallationState,
    ModuleState,
    ModuleStatus,
)


class StateManager:
    """
    Manages installation state with SQLite persistence.

    Provides:
    - State persistence across restarts
    - Checkpoint creation and restore
    - Resume capability after crashes
    - Installation history

    db_path: Union[Path, str]
    """

    def __init__(
        self,
        db_path: Optional[Union[Path, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize state manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
                    Supports :memory: for in-memory database (testing).
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Determine database path
        self.db_path: Union[Path, str]
        if db_path is None:
            # Try /var/lib first (requires root)
            default_path = Path("/var/lib/debian-vps-configurator/state.db")
            if default_path.parent.exists() or self._can_create_dir(default_path.parent):
                self.db_path = default_path
            else:
                # Fallback to user config directory
                fallback_path = Path.home() / ".config" / "debian-vps-configurator" / "state.db"
                self.logger.info(f"Cannot write to {default_path}, using fallback: {fallback_path}")
                self.db_path = fallback_path
        else:
            is_path_obj = isinstance(db_path, Path)
            is_memory = db_path == ":memory:"
            self.db_path = Path(db_path) if not is_path_obj and not is_memory else db_path

        # For in-memory databases, keep persistent connection
        self._in_memory_conn: Optional[sqlite3.Connection] = None

        # Create database directory if needed
        if self.db_path != ":memory:" and isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        # Current installation state (in-memory)
        self.current_state: Optional[InstallationState] = None

    def _can_create_dir(self, path: Path) -> bool:
        """
        Check if directory can be created.

        Args:
            path: Directory path to check

        Returns:
            True if directory can be created
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except (PermissionError, OSError):
            return False

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            SQLite connection
        """
        # For in-memory databases, reuse the same connection
        if self.db_path == ":memory:":
            if self._in_memory_conn is None:
                self._in_memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._in_memory_conn.row_factory = sqlite3.Row
            return self._in_memory_conn

        # For file-based databases, create new connection each time
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        # Handle migration file path
        migration_file = Path(__file__).parent / "migrations" / "v1_initial.sql"

        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            sql = migration_file.read_text()
            cursor.executescript(sql)
            conn.commit()
        finally:
            # Only close if it's not the persistent in-memory connection
            if self.db_path != ":memory:":
                conn.close()

        self.logger.debug("Database initialized")

    def start_installation(
        self, profile: str, metadata: Optional[Dict[str, Any]] = None
    ) -> InstallationState:
        """
        Start a new installation.

        Args:
            profile: Installation profile name
            metadata: Optional metadata dictionary

        Returns:
            New InstallationState
        """
        installation_id = f"inst-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now()

        state = InstallationState(
            installation_id=installation_id,
            started_at=started_at,
            profile=profile,
            metadata=metadata or {},
        )

        # Persist to database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO installations (
                    installation_id, started_at, profile, overall_status, metadata
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    installation_id,
                    started_at.isoformat(),
                    profile,
                    state.overall_status,
                    json.dumps(state.metadata),
                ),
            )
            conn.commit()

        self.current_state = state
        self.logger.info(f"Started installation {installation_id} with profile {profile}")

        return state

    def update_module(
        self,
        module_name: str,
        status: Optional[ModuleStatus] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update module state.

        Args:
            module_name: Name of module to update
            status: New status (optional)
            progress: Progress percentage 0-100 (optional)
            current_step: Current execution step (optional)
            error: Error message if failed (optional)
        """
        if not self.current_state:
            raise RuntimeError("No active installation")

        # Get or create module state
        if module_name not in self.current_state.modules:
            self.current_state.modules[module_name] = ModuleState(name=module_name)

        module_state = self.current_state.modules[module_name]

        # Update fields
        if status is not None:
            module_state.status = status
            if status == ModuleStatus.RUNNING and module_state.started_at is None:
                module_state.started_at = datetime.now()
            elif status in (ModuleStatus.COMPLETED, ModuleStatus.FAILED):
                module_state.completed_at = datetime.now()
                if module_state.started_at:
                    delta = module_state.completed_at - module_state.started_at
                    module_state.duration_seconds = delta.total_seconds()

        if progress is not None:
            module_state.progress_percent = min(100, max(0, progress))

        if current_step is not None:
            module_state.current_step = current_step

        if error is not None:
            module_state.error_message = error

        # Persist to database
        self._persist_module_state(module_name, module_state)

        self.logger.debug(f"Updated module {module_name}: {status}")

    def _persist_module_state(self, module_name: str, state: ModuleState) -> None:
        """
        Persist module state to database.

        Args:
            module_name: Module name
            state: Module state to persist
        """
        if not self.current_state:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO modules
                (installation_id, module_name, status, started_at, completed_at,
                 duration_seconds, progress_percent, current_step, error_message,
                 checkpoint, rollback_actions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.current_state.installation_id,
                    module_name,
                    state.status.value,
                    state.started_at.isoformat() if state.started_at else None,
                    state.completed_at.isoformat() if state.completed_at else None,
                    state.duration_seconds,
                    state.progress_percent,
                    state.current_step,
                    state.error_message,
                    state.checkpoint,
                    json.dumps(state.rollback_actions),
                ),
            )
            conn.commit()

    def create_checkpoint(self, module_name: str, checkpoint_name: str) -> None:
        """
        Create a checkpoint for a module.

        Args:
            module_name: Module name
            checkpoint_name: Name of checkpoint
        """
        if not self.current_state:
            raise RuntimeError("No active installation")

        if module_name not in self.current_state.modules:
            self.logger.warning(f"Cannot create checkpoint for unknown module: {module_name}")
            return

        module_state = self.current_state.modules[module_name]
        module_state.checkpoint = checkpoint_name

        # Update module state in database to persist checkpoint
        self._persist_module_state(module_name, module_state)

        # Save checkpoint snapshot to database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO checkpoints (
                    installation_id, module_name, checkpoint_name, state_snapshot
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.current_state.installation_id,
                    module_name,
                    checkpoint_name,
                    json.dumps(module_state.to_dict()),
                ),
            )
            conn.commit()

        self.logger.info(f"Created checkpoint '{checkpoint_name}' for {module_name}")

    def can_resume(self) -> bool:
        """
        Check if there is an incomplete installation that can be resumed.

        Returns:
            True if resumable installation exists
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM installations
                WHERE overall_status = 'in_progress' AND completed_at IS NULL
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            return int(row["count"]) > 0

    def resume_installation(self) -> Optional[InstallationState]:
        """
        Resume the most recent incomplete installation.

        Returns:
            InstallationState if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get most recent incomplete installation
            cursor.execute(
                """
                SELECT * FROM installations
                WHERE overall_status = 'in_progress' AND completed_at IS NULL
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
            inst_row = cursor.fetchone()

            if not inst_row:
                return None

            # Load installation state
            state = InstallationState(
                installation_id=inst_row["installation_id"],
                started_at=datetime.fromisoformat(inst_row["started_at"]),
                profile=inst_row["profile"],
                overall_status=inst_row["overall_status"],
                metadata=json.loads(inst_row["metadata"] or "{}"),
            )

            # Load module states
            cursor.execute(
                """
                SELECT * FROM modules WHERE installation_id = ?
                """,
                (state.installation_id,),
            )

            for module_row in cursor.fetchall():
                module_state = ModuleState(
                    name=module_row["module_name"],
                    status=ModuleStatus(module_row["status"]),
                    started_at=(
                        datetime.fromisoformat(module_row["started_at"])
                        if module_row["started_at"]
                        else None
                    ),
                    completed_at=(
                        datetime.fromisoformat(module_row["completed_at"])
                        if module_row["completed_at"]
                        else None
                    ),
                    duration_seconds=module_row["duration_seconds"],
                    progress_percent=module_row["progress_percent"],
                    current_step=module_row["current_step"] or "",
                    error_message=module_row["error_message"],
                    checkpoint=module_row["checkpoint"],
                    rollback_actions=json.loads(module_row["rollback_actions"] or "[]"),
                )
                state.modules[module_state.name] = module_state

        self.current_state = state
        self.logger.info(f"Resumed installation {state.installation_id}")

        return state

    def complete_installation(self, success: bool) -> None:
        """
        Mark installation as complete.

        Args:
            success: Whether installation succeeded
        """
        if not self.current_state:
            raise RuntimeError("No active installation")

        self.current_state.completed_at = datetime.now()
        self.current_state.overall_status = "success" if success else "failed"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE installations
                SET completed_at = ?, overall_status = ?
                WHERE installation_id = ?
                """,
                (
                    self.current_state.completed_at.isoformat(),
                    self.current_state.overall_status,
                    self.current_state.installation_id,
                ),
            )
            conn.commit()

        self.logger.info(
            f"Installation {self.current_state.installation_id} "
            f"completed with status: {self.current_state.overall_status}"
        )

    def get_installation_history(self, limit: int = 10) -> List[InstallationState]:
        """
        Get installation history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of InstallationState objects, most recent first
        """
        history: List[InstallationState] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM installations
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            )

            for inst_row in cursor.fetchall():
                state = InstallationState(
                    installation_id=inst_row["installation_id"],
                    started_at=datetime.fromisoformat(inst_row["started_at"]),
                    profile=inst_row["profile"],
                    completed_at=(
                        datetime.fromisoformat(inst_row["completed_at"])
                        if inst_row["completed_at"]
                        else None
                    ),
                    overall_status=inst_row["overall_status"],
                    metadata=json.loads(inst_row["metadata"] or "{}"),
                )
                history.append(state)

        return history
