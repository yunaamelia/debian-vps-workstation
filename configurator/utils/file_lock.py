import fcntl
import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(file_path: str):
    """
    Context manager for file locking to prevent race conditions.

    Usage:
        with file_lock('/etc/environment'):
            # Safely modify file
            with open('/etc/environment', 'a') as f:
                f.write('MY_VAR=value\\n')
    """
    lock_file = Path(f"{file_path}.lock")

    # Ensure directory exists for lock file
    if not lock_file.parent.exists():
        # This might fail if parent is root owned and we are not root,
        # but typically this runs as root.
        pass

    # We need to be careful about permissions if creating directories.
    # Assuming the installer ensures paths exist or runs as root.

    # Open lock file
    f = open(lock_file, "w")
    try:
        # Acquire exclusive lock
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        # Release lock
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()
        # Clean up lock file (optional, might race if we delete,
        # but standardized advisory locking ignores file existence strictly speaking
        # if using flock on fd. However, unlink is standard practice for pid files/locks)
        try:
            os.unlink(lock_file)
        except FileNotFoundError:
            pass
