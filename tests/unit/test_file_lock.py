import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from configurator.utils.file_lock import file_lock


class TestFileLock:
    def test_lock_creation(self, tmp_path):
        lock_target = tmp_path / "test.file"
        lock_file_path = tmp_path / "test.file.lock"

        with file_lock(str(lock_target)):
            assert lock_file_path.exists()

        # Lock file is cleaned up
        assert not lock_file_path.exists()

    def test_lock_exclusion(self, tmp_path):
        lock_target = tmp_path / "shared.file"

        events = []

        def worker(id, sleep_time):
            with file_lock(str(lock_target)):
                events.append(f"start-{id}")
                time.sleep(sleep_time)
                events.append(f"end-{id}")

        t1 = threading.Thread(target=worker, args=(1, 0.2))
        t2 = threading.Thread(target=worker, args=(2, 0.1))

        t1.start()
        time.sleep(0.05)  # Ensure t1 grabs lock
        t2.start()

        t1.join()
        t2.join()

        # t1 should finish before t2 starts because t1 holds lock
        # t2 tries to acquire lock at 0.05, but t1 holds it for 0.2
        # So t1 ends at 0.2, t2 starts at 0.2, t2 ends at 0.3

        assert events[0] == "start-1"
        assert events[1] == "end-1"
        assert events[2] == "start-2"
        assert events[3] == "end-2"

    def test_lock_cleanup_error(self, tmp_path):
        """Test safety when unlink fails"""
        lock_target = tmp_path / "cleanup.file"

        with patch("os.unlink", side_effect=FileNotFoundError):
            with file_lock(str(lock_target)):
                pass
        # Should not raise exception
