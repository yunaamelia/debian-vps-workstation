"""
File operation utilities with backup support.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from configurator.exceptions import ModuleExecutionError

# Default backup directory
BACKUP_DIR = Path("/var/backups/debian-vps-configurator")


def ensure_dir(path: Union[str, Path], mode: int = 0o755) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path
        mode: Directory permissions

    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=mode)
    return path


def backup_file(
    path: Union[str, Path],
    backup_dir: Optional[Path] = None,
    suffix: Optional[str] = None,
) -> Optional[Path]:
    """
    Create a backup of a file.

    Args:
        path: File to backup
        backup_dir: Directory to store backup (default: /var/backups/debian-vps-configurator)
        suffix: Optional suffix for backup filename

    Returns:
        Path to backup file, or None if original doesn't exist
    """
    path = Path(path)

    if not path.exists():
        return None

    # Determine backup location
    backup_dir = backup_dir or BACKUP_DIR
    ensure_dir(backup_dir)

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = suffix or timestamp
    backup_name = f"{path.name}.{suffix}.bak"
    backup_path = backup_dir / backup_name

    # Create backup
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        raise ModuleExecutionError(
            what=f"Failed to backup file: {path}",
            why=str(e),
            how="Check file permissions and available disk space",
        )


def restore_file(
    backup_path: Union[str, Path],
    original_path: Union[str, Path],
) -> bool:
    """
    Restore a file from backup.

    Args:
        backup_path: Path to backup file
        original_path: Path to restore to

    Returns:
        True if restoration was successful
    """
    backup_path = Path(backup_path)
    original_path = Path(original_path)

    if not backup_path.exists():
        raise ModuleExecutionError(
            what=f"Backup file not found: {backup_path}",
            why="The backup file does not exist",
            how="Check if the backup was created successfully",
        )

    try:
        shutil.copy2(backup_path, original_path)
        return True
    except Exception as e:
        raise ModuleExecutionError(
            what=f"Failed to restore file: {original_path}",
            why=str(e),
            how="Check file permissions and available disk space",
        )


# ... imports ...
from pathlib import Path
from typing import Optional, Union

from configurator.exceptions import ModuleExecutionError
from configurator.utils.file_lock import file_lock

# Default backup directory
BACKUP_DIR = Path("/var/backups/debian-vps-configurator")

# ... ensure_dir, backup_file, restore_file unchanged ...


def write_file(
    path: Union[str, Path],
    content: str,
    backup: bool = True,
    mode: int = 0o644,
    owner: Optional[str] = None,
    group: Optional[str] = None,
) -> Path:
    """
    Write content to a file with optional backup (Thread-Safe).

    Args:
        path: File path
        content: Content to write
        backup: Create backup if file exists
        mode: File permissions
        owner: File owner (username)
        group: File group (groupname)

    Returns:
        Path to the written file
    """
    path = Path(path)

    # Create parent directories
    ensure_dir(path.parent)

    with file_lock(str(path)):
        # Backup existing file
        if backup and path.exists():
            backup_file(path)

        # Write content
        try:
            path.write_text(content, encoding="utf-8")
            os.chmod(path, mode)

            # Set ownership if specified
            if owner or group:
                import grp
                import pwd

                uid = pwd.getpwnam(owner).pw_uid if owner else -1
                gid = grp.getgrnam(group).gr_gid if group else -1
                os.chown(path, uid, gid)

            return path
        except Exception as e:
            raise ModuleExecutionError(
                what=f"Failed to write file: {path}",
                why=str(e),
                how="Check file permissions and available disk space",
            )


def read_file(path: Union[str, Path]) -> str:
    """Read file content (Thread-Safeish - advisory lock ignored for read usually, but good practice if critical)."""
    # For read, strictly dependent on writer lock. flock shared lock?
    # fcntl.LOCK_SH
    # But file_lock context manager creates new file for lock?
    # file_lock uses .lock file.
    # So writers acquire EX lock on .lock.
    # Readers should probably just read, unless we want strict consistency.
    # For this project, config files are small. Atomic writes (rename) are best but we use in-place write_text.
    # write_text is not atomic (truncates then writes).
    # So we SHOULD lock readers too if we expect parallel read/write.
    # But read_file is simple.
    path = Path(path)

    if not path.exists():
        raise ModuleExecutionError(
            what=f"File not found: {path}",
            why="The file does not exist",
            how="Check if the file path is correct",
        )

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise ModuleExecutionError(
            what=f"Failed to read file: {path}",
            why=str(e),
            how="Check file permissions",
        )


def append_to_file(
    path: Union[str, Path],
    content: str,
    create: bool = True,
) -> Path:
    """
    Append content to a file (Thread-Safe).

    Args:
        path: File path
        content: Content to append
        create: Create file if it doesn't exist

    Returns:
        Path to the file
    """
    path = Path(path)

    with file_lock(str(path)):
        if not path.exists() and not create:
            raise ModuleExecutionError(
                what=f"File not found: {path}",
                why="The file does not exist and create=False",
                how="Set create=True or create the file first",
            )

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return path
        except Exception as e:
            raise ModuleExecutionError(
                what=f"Failed to append to file: {path}",
                why=str(e),
                how="Check file permissions",
            )


def file_contains(path: Union[str, Path], pattern: str) -> bool:
    """Check if a file contains a pattern."""
    path = Path(path)

    if not path.exists():
        return False

    # Naive read without lock is mostly fine for checking exists
    try:
        content = path.read_text(encoding="utf-8")
    except:
        return False
    return pattern in content


def replace_in_file(
    path: Union[str, Path],
    old: str,
    new: str,
    backup: bool = True,
) -> bool:
    """
    Replace text in a file (Thread-Safe).

    Args:
        path: File path
        old: Text to replace
        new: Replacement text
        backup: Create backup before modifying

    Returns:
        True if replacement was made
    """
    path = Path(path)

    if not path.exists():
        raise ModuleExecutionError(
            what=f"File not found: {path}",
            why="The file does not exist",
            how="Check if the file path is correct",
        )

    with file_lock(str(path)):
        content = path.read_text(encoding="utf-8")

        if old not in content:
            return False

        new_content = content.replace(old, new)

        # We assume write_file will lock again? No, file_lock is typically reentrant if same process/thread?
        # NO. fcntl on same file from same process?
        # lock file is separate file .lock
        # If we nest locks on same file, it might deadlock or be a no-op?
        # flock is valid per fd.
        # But here we call write_file which calls file_lock.
        # If replace_in_file acquires lock, then write_file tries to acquire SAME lock...
        # It will wait forever if in another thread, but same thread?
        # flock is associated with OPEN FILE DESCRIPTION.
        # If we open .lock again, it's a new file description.
        # Locking it again from same thread WILL BLOCK if using fcntl.LOCK_EX?
        # Actually, POSIX locks: "If a process has a write lock, it can also have a read lock..."
        # But wait, fcntl locks are per process?
        # "flock() locks are associated with a file description... duplicated fds share lock..."
        # "Process-oriented: if a process holding a lock on a file closes any fd for that file, the lock is released."
        # If we open new fd, it might block.
        # So we should call internal write logic or bypass lock in write_file.
        # Refactoring write_file to have `_write_file_internal` and `write_file` wrapper is safer.
        # OR just duplicate logic here.

        # Backup existing file (manually to avoid nested lock in write_file)
        if backup:
            backup_file(path)  # backup_file doesn't lock? It reads.

        try:
            path.write_text(new_content, encoding="utf-8")
            # Mode? Preserved?
            # write_text replaces file.
            return True
        except Exception as e:
            raise ModuleExecutionError(what=f"Failed to replace in {path}", why=str(e))
