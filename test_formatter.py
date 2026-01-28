import logging
import time

from configurator.ui.logging.formatter import CompactLogFormatter

# Mock Record
record = logging.LogRecord(
    name="configurator.modules.docker",
    level=logging.INFO,
    pathname="test.py",
    lineno=10,
    msg="Docker installed successfully",
    args=(),
    exc_info=None,
)
record.created = time.time()
record.duration_ms = 1500

formatter = CompactLogFormatter(use_colors=True)
print(f"Formatter Output:\n{formatter.format(record)}")

# Test Warn
record.levelname = "WARNING"
record.msg = "Slow download detected"
print(f"\nWarning Output:\n{formatter.format(record)}")

# Test Error
record.levelname = "ERROR"
record.msg = "Installation failed"
print(f"\nError Output:\n{formatter.format(record)}")
