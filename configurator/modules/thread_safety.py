# configurator/modules/thread_safety.py

"""
Thread Safety Guidelines for Parallel Module Execution

When modules run in parallel, they must avoid race conditions
and resource conflicts.

DO:
✅ Use file locking for shared files
✅ Use atomic file operations
✅ Check-and-create atomically
✅ Use thread-safe utilities from configurator.utils

DON'T:
❌ Assume you're the only module running
❌ Use time.sleep() as synchronization
❌ Modify shared files without locking
❌ Use non-atomic check-then-act patterns
"""

import os
import tempfile

from configurator.utils.file_lock import file_lock


# GOOD: Atomic file write with locking
def safe_append_to_file(file_path: str, content: str):
    """Thread-safe file append"""
    with file_lock(file_path):
        with open(file_path, "a") as f:
            f.write(content)


# GOOD: Atomic file creation
def safe_create_file(file_path: str, content: str):
    """Thread-safe file creation (atomic)"""
    # Write to temp file first
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
    try:
        os.write(fd, content.encode())
        os.close(fd)

        # Atomic rename
        os.rename(temp_path, file_path)
    except Exception:
        os.close(fd)
        os.unlink(temp_path)
        raise


# BAD: Race condition (Time-Of-Check-Time-Of-Use)
def unsafe_create_if_not_exists(file_path: str):
    """❌ UNSAFE:  Race condition possible"""
    if not os.path.exists(file_path):  # Check
        # Another module could create it here!
        with open(file_path, "w") as f:  # Act
            f.write("content")


# GOOD: Atomic check-and-create
def safe_create_if_not_exists(file_path: str):
    """✅ SAFE: Atomic operation"""
    try:
        fd = os.open(file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, b"content")
        os.close(fd)
    except FileExistsError:
        pass  # File already exists, that's OK
