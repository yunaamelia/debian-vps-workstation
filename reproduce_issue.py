import sys

from configurator.exceptions import ConfigurationError

print("Attempting to raise ConfigurationError with what/why/how...")
try:
    raise ConfigurationError(what="Test Error", why="Testing failure", how="Fix it")
    print("SUCCESS: ConfigurationError raised successfully with what/why/how")
except TypeError as e:
    print(f"FAILURE: Caught TypeError: {e}")
    sys.exit(1)
except Exception as e:
    # This is actually expected if we just raised it and didn't catch it inside the try block,
    # but for this script we want to catch it to verify it IS a ConfigurationError
    if "ConfigurationError" in type(e).__name__:
        print("SUCCESS: ConfigurationError raised successfully")
        sys.exit(0)
    print(f"FAILURE: Caught unexpected exception: {type(e).__name__}: {e}")
    sys.exit(1)

print("FAILURE: No exception raised (or incorrect one)")
sys.exit(1)
