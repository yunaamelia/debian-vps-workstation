import logging
import threading
import time

import pytest

from configurator.logger import ParallelLogManager, shutdown_log_manager


@pytest.fixture
def log_manager(tmp_path):
    """Fixture for parallel log manager using tmp_path."""
    shutdown_log_manager()
    manager = ParallelLogManager(
        base_log_dir=tmp_path,
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        enable_per_module_logs=True,
    )
    manager.start()
    yield manager
    manager.stop()
    shutdown_log_manager()


def test_no_interleaved_logs(log_manager, tmp_path):
    """Test that logs from multiple threads are written sequentially."""

    def worker(name, count):
        logger = log_manager.get_logger(name)
        for i in range(count):
            logger.info(f"Message {i} from {name}")
            time.sleep(0.001)

    threads = []
    # Start 3 threads writing 100 messages each
    for i in range(3):
        t = threading.Thread(target=worker, args=(f"worker_{i}", 100))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Give listener time to flush
    time.sleep(0.2)
    log_manager.stop()

    # Check main log file
    log_file = tmp_path / "install.log"
    assert log_file.exists()

    content = log_file.read_text()
    lines = content.strip().split("\n")

    # Basic check: we expect 300 lines (plus maybe header/footer if any)
    # The LogManager formatter uses standard format.
    # We verify that lines are not garbled (e.g. two messages on one line)
    assert len(lines) == 300

    for line in lines:
        assert " | INFO     | configurator.modules.worker_" in line
        assert " | Message " in line


def test_per_module_logs(log_manager, tmp_path):
    """Test that per-module logs are created and contain only module logs."""

    logger1 = log_manager.get_logger("module_a")
    logger2 = log_manager.get_logger("module_b")

    logger1.info("Hello from A")
    logger2.info("Hello from B")

    time.sleep(0.1)
    log_manager.stop()

    log_a = tmp_path / "module_a.log"
    log_b = tmp_path / "module_b.log"

    assert log_a.exists()
    assert log_b.exists()

    assert "Hello from A" in log_a.read_text()
    assert "Hello from B" not in log_a.read_text()

    assert "Hello from B" in log_b.read_text()
    assert "Hello from A" not in log_b.read_text()
