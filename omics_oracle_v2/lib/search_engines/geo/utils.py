"""
Rate limiting and retry utilities for GEO API calls.

Provides rate limiting to comply with NCBI guidelines and retry logic
with exponential backoff for handling transient failures.
"""

import asyncio
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """
    Simple rate limiter for API calls.

    Enforces a maximum number of calls within a time window using
    a sliding window approach.
    """

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []
        logger.debug(f"Rate limiter: {max_calls} calls per {time_window}s")

    async def acquire(self) -> None:
        """
        Acquire permission for an API call.

        Waits if rate limit would be exceeded.
        """
        now = time.time()

        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

        # If we've hit the limit, wait
        if len(self.calls) >= self.max_calls:
            wait_time = self.time_window - (now - self.calls[0])
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire()  # Retry after waiting

        # Record this call
        self.calls.append(now)

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.calls = []
        logger.debug("Rate limiter reset")


async def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        max_delay: Maximum delay between retries in seconds

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"All {max_retries} retry attempts failed: {str(e)}")
                break

            # Calculate next delay with exponential backoff
            actual_delay = min(delay, max_delay)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. " f"Retrying in {actual_delay:.2f}s")

            await asyncio.sleep(actual_delay)
            delay *= backoff_factor

    if last_exception:
        raise last_exception
    raise RuntimeError("All retry attempts failed")
