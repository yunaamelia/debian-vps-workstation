import hashlib
import hmac
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.core.audit import AuditEventType, AuditLogger
from configurator.exceptions import ConfiguratorError

logger = logging.getLogger(__name__)


class FIMError(ConfiguratorError):
    """Exception for FIM errors."""


@dataclass
class FileState:
    path: str
    sha256: str
    size: int
    mode: int
    uid: int
    gid: int
    mtime: float
    last_check: str


class FileIntegrityMonitor:
    """
    Monitors critical system files for unauthorized changes.

    Features:
    - Calculates SHA256 hashes of monitored files
    - Tracks metadata (permissions, ownership, size)
    - Signs the baseline database with HMAC-SHA256 to prevent tampering
    - Integrates with AuditLogger to report security violations
    """

    DEFAULT_DB_PATH = Path("/var/lib/debian-vps-configurator/file-integrity.json")
    DEFAULT_MONITORED_FILES = [
        "/etc/ssh/sshd_config",
        "/etc/sudoers",
        "/etc/passwd",
        "/etc/shadow",
        "/etc/group",
        "/etc/ufw/user.rules",
        "/etc/fail2ban/jail.local",
        "/etc/xrdp/xrdp.ini",
    ]

    DEFAULT_KEY_PATH = Path("/etc/debian-vps-configurator/.fim_key")

    def __init__(self, db_path: Optional[Path] = None, monitored_files: Optional[List[str]] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.monitored_files = monitored_files or self.DEFAULT_MONITORED_FILES
        self.baseline: Dict[str, FileState] = {}
        self._hmac_key: Optional[bytes] = None

        # Ensure db dir exists
        if not self.db_path.parent.exists():
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                os.chmod(self.db_path.parent, 0o700)
            except PermissionError:
                self.db_path = Path.cwd() / "file-integrity.json"
                logger.warning(f"Using local FIM DB: {self.db_path}")

        self._load_key()
        self._load_baseline()

    def _load_key(self) -> None:
        """Load or generate the HMAC signing key."""
        try:
            if not self.DEFAULT_KEY_PATH.exists():
                # Generate new key
                # Ensure directory exists
                self.DEFAULT_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
                os.chmod(self.DEFAULT_KEY_PATH.parent, 0o700)

                key = os.urandom(32)
                with open(self.DEFAULT_KEY_PATH, "wb") as f:
                    f.write(key)
                os.chmod(self.DEFAULT_KEY_PATH, 0o600)
                self._hmac_key = key
                logger.info(f"Generated new FIM HMAC key at {self.DEFAULT_KEY_PATH}")
            else:
                with open(self.DEFAULT_KEY_PATH, "rb") as f:
                    self._hmac_key = f.read()
        except OSError as e:
            logger.warning(
                f"Failed to load FIM key: {e}. FIM database will not be signed (INSECURE)."
            )
            self._hmac_key = None

    def _calculate_signature(self, data_bytes: bytes) -> str:
        """Calculate HMAC-SHA256 signature."""
        if not self._hmac_key:
            return ""
        return hmac.new(self._hmac_key, data_bytes, hashlib.sha256).hexdigest()

    def _load_baseline(self) -> None:
        if not self.db_path.exists():
            return

        try:
            with open(self.db_path, "r") as f:
                content = f.read()
                data = json.loads(content)

            # Verify signature if present and key is available
            if self._hmac_key:
                signature = data.get("_signature", "")
                # Reconstruct data payload to verify
                # We need to be careful about JSON serialization stability.
                # A better approach is to sign the 'baseline' dict structure dump.

                baseline_data = data.get("baseline", {})
                canonical_json = json.dumps(baseline_data, sort_keys=True)

                expected_sig = self._calculate_signature(canonical_json.encode())

                if not hmac.compare_digest(expected_sig, signature):
                    msg = "FIM Database Integrity Check Failed! Signature mismatch."
                    logger.critical(msg)
                    try:
                        audit = AuditLogger()
                        audit.log_event(
                            AuditEventType.SECURITY_VIOLATION,
                            "FIM Database Tampering Detected",
                            success=False,
                        )
                    except Exception:
                        pass
                    raise FIMError(msg)

            self.baseline = {k: FileState(**v) for k, v in data.get("baseline", {}).items()}
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load FIM baseline: {e}")

    def _save_baseline(self) -> None:
        try:
            # Convert dataclasses to dicts
            baseline_data = {k: asdict(v) for k, v in self.baseline.items()}

            output_data = {"baseline": baseline_data}

            if self._hmac_key:

                # Sign the canonical content of baseline
                canonical_json = json.dumps(baseline_data, sort_keys=True)
                signature = self._calculate_signature(canonical_json.encode())
                output_data["_signature"] = signature

            with open(self.db_path, "w") as f:
                json.dump(output_data, f, indent=2)
            os.chmod(self.db_path, 0o600)
        except OSError as e:
            logger.error(f"Failed to save FIM baseline: {e}")

    def _calculate_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except OSError:
            return ""

    def _get_file_state(self, path_str: str) -> Optional[FileState]:
        path = Path(path_str)
        if not path.exists():
            return None

        try:
            stat = path.stat()
            file_hash = self._calculate_hash(path)

            return FileState(
                path=path_str,
                sha256=file_hash,
                size=stat.st_size,
                mode=stat.st_mode,
                uid=stat.st_uid,
                gid=stat.st_gid,
                mtime=stat.st_mtime,
                last_check=datetime.now(timezone.utc).isoformat(),
            )
        except OSError as e:
            logger.warning(f"Failed to check file {path_str}: {e}")
            return None

    def initialize(self) -> None:
        """Initialize or reset the baseline."""
        logger.info("Initializing FIM baseline...")
        self.baseline = {}

        for file_path in self.monitored_files:
            state = self._get_file_state(file_path)
            if state:
                self.baseline[file_path] = state
                logger.info(f"Added to baseline: {file_path}")
            else:
                logger.warning(f"File not found, skipping: {file_path}")

        self._save_baseline()

        # Log initialization
        try:
            audit = AuditLogger()
            audit.log_event(
                AuditEventType.SECURITY_VIOLATION, "FIM Baseline Initialized", success=True
            )
        except Exception:
            pass

    def check(self) -> List[Dict[str, Any]]:
        """
        Check for changes against baseline.

        Returns:
            List of violations (dictionaries describing changes)
        """
        violations = []

        if not self.baseline:
            logger.warning("No baseline found. Please run 'initialize' first.")
            return []

        for path, baseline_state in self.baseline.items():
            current_state = self._get_file_state(path)

            if not current_state:
                # File deleted
                violation = {
                    "path": path,
                    "type": "file_deleted",
                    "severity": "high",
                    "details": "File exists in baseline but is missing from disk",
                }
                violations.append(violation)
                continue

            # Check for changes
            changes = []
            if current_state.sha256 != baseline_state.sha256:
                changes.append("content_modified")
            if current_state.mode != baseline_state.mode:
                changes.append("permissions_modified")
            if current_state.uid != baseline_state.uid or current_state.gid != baseline_state.gid:
                changes.append("ownership_modified")

            if changes:
                violation = {
                    "path": path,
                    "type": "file_modified",
                    "changes": changes,
                    "severity": "high" if "content_modified" in changes else "medium",
                    "details": f"Changes detected: {', '.join(changes)}",
                }
                violations.append(violation)

        # Log violations
        if violations:
            try:
                audit = AuditLogger()
                for v in violations:
                    audit.log_event(
                        AuditEventType.SECURITY_VIOLATION,
                        f"FIM Violation: {v['path']}",
                        details=v,
                        success=False,
                    )
            except Exception:
                pass

        return violations

    def update_baseline(self, file_path: str) -> bool:
        """Update baseline for a specific file (authorize change)."""
        state = self._get_file_state(file_path)
        if state:
            self.baseline[file_path] = state
            self._save_baseline()
            logger.info(f"Updated baseline for: {file_path}")
            return True
        return False
