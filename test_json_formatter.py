import json
import logging

from configurator.ui.logging.formatter import JSONLogFormatter

# Mock Record
record = logging.LogRecord(
    name="configurator.modules.docker",
    level=logging.ERROR,
    pathname="test.py",
    lineno=10,
    msg="Installation failed",
    args=(),
    exc_info=None,
)
record.created = 1738040000.0
record.duration_ms = 1500
record.code = "ERR_INSTALL"

formatter = JSONLogFormatter()
output = formatter.format(record)
print("JSON Output:")
print(output)

# Validate JSON
parsed = json.loads(output)
assert parsed["level"] == "ERROR"
assert parsed["code"] == "ERR_INSTALL"
print("Standard JSON Validation Passed")


# Test Non-Serializable Object
class WeirdObj:
    pass


record.msg = "Weird object incoming"
record.weird = WeirdObj()
output = formatter.format(record)
print("\nNon-Serializable Object Output:")
print(output)
parsed = json.loads(output)
assert "WeirdObj" in output
print("Safe Serialization Validation Passed")
