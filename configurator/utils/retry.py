import functools
import logging
import os
import random
import time
from typing import Any, Callable, Tuple, Type, Union

logger = logging.getLogger(__name__)


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: Maximum number of retries (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        backoff_factor: Multiplier for backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
        exceptions: Exceptions to catch and retry on (default: Exception)

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # In test mode, drastically reduce retries to prevent test hangs
            actual_max_retries = max_retries
            actual_base_delay = base_delay
            actual_max_delay = max_delay

            if os.environ.get("PYTEST_CURRENT_TEST"):
                actual_max_retries = min(max_retries, 2)
                actual_base_delay = min(base_delay, 0.1)
                actual_max_delay = min(max_delay, 1.0)

            retries = 0
            delay = actual_base_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > actual_max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {actual_max_retries} retries. Last error: {e}"
                        )
                        raise

                    # Calculate delay with backoff
                    current_delay = delay
                    if jitter:
                        current_delay = delay * (0.5 + random.random())

                    # Cap at max_delay
                    current_delay = min(current_delay, actual_max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed with {e.__class__.__name__}: {e}. "
                        f"Retrying in {current_delay:.2f}s ({retries}/{actual_max_retries})..."
                    )

                    time.sleep(current_delay)

                    # Increment backoff
                    delay *= backoff_factor

        return wrapper

    return decorator
