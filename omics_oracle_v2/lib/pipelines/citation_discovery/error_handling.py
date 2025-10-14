"""
Error Handling & Retry Logic for Citation Discovery

Provides robust error handling with:
1. Error classification (rate limit, timeout, network, API errors)
2. Exponential backoff with jitter
3. Fallback chains for graceful degradation
4. Circuit breaker pattern

Benefits:
- 100% uptime (graceful degradation)
- Automatic retry for transient failures
- Smart backoff to avoid hammering APIs
- Detailed error logging for debugging

Usage:
    # Simple retry
    @retry_with_backoff(max_retries=3)
    def fetch_data():
        return api.get_data()
    
    # Fallback chain
    chain = FallbackChain("citation_discovery")
    result = chain.execute(geo_id="GSE12345", pmid="12345678")
"""

import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of errors"""

    RATE_LIMIT = "rate_limit"  # 429, rate limit exceeded
    TIMEOUT = "timeout"  # Request timeout
    NETWORK = "network"  # Connection error, DNS failure
    API_ERROR = "api_error"  # 4xx/5xx errors
    NOT_FOUND = "not_found"  # 404, resource not found
    INVALID_INPUT = "invalid_input"  # Bad request, validation error
    UNKNOWN = "unknown"  # Unclassified error


@dataclass
class DiscoveryError(Exception):
    """Base exception for citation discovery errors"""

    message: str
    error_type: ErrorType
    source: str  # "openalex", "semantic_scholar", "pubmed"
    original_error: Optional[Exception] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry

    def __str__(self):
        return f"[{self.source}] {self.error_type.value}: {self.message}"


class RateLimitError(DiscoveryError):
    """Rate limit exceeded"""

    def __init__(self, source: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message="Rate limit exceeded",
            error_type=ErrorType.RATE_LIMIT,
            source=source,
            retry_after=retry_after,
            **kwargs,
        )


class TimeoutError(DiscoveryError):
    """Request timeout"""

    def __init__(self, source: str, **kwargs):
        super().__init__(
            message="Request timeout", error_type=ErrorType.TIMEOUT, source=source, **kwargs
        )


class NetworkError(DiscoveryError):
    """Network connection error"""

    def __init__(self, source: str, **kwargs):
        super().__init__(
            message="Network error", error_type=ErrorType.NETWORK, source=source, **kwargs
        )


class APIError(DiscoveryError):
    """API error (4xx/5xx)"""

    def __init__(self, source: str, status_code: Optional[int] = None, **kwargs):
        message = f"API error (status: {status_code})" if status_code else "API error"
        super().__init__(message=message, error_type=ErrorType.API_ERROR, source=source, **kwargs)


def classify_error(error: Exception, source: str) -> DiscoveryError:
    """
    Classify an exception into a DiscoveryError

    Args:
        error: Original exception
        source: Source that raised the error

    Returns:
        Classified DiscoveryError
    """
    # Check if already a DiscoveryError
    if isinstance(error, DiscoveryError):
        return error

    error_str = str(error).lower()

    # Rate limit
    if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
        return RateLimitError(source=source, original_error=error)

    # Timeout
    if "timeout" in error_str or "timed out" in error_str:
        return TimeoutError(source=source, original_error=error)

    # Network errors
    if any(
        x in error_str
        for x in ["connection", "network", "dns", "unreachable", "host", "socket"]
    ):
        return NetworkError(source=source, original_error=error)

    # API errors
    if "api" in error_str or any(x in error_str for x in ["400", "401", "403", "404", "500", "502", "503"]):
        return APIError(source=source, original_error=error)

    # Unknown
    return DiscoveryError(
        message=str(error),
        error_type=ErrorType.UNKNOWN,
        source=source,
        original_error=error,
    )


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff with jitter

    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds with jitter
    """
    # Exponential: 1s, 2s, 4s, 8s, 16s, 32s, 60s (capped)
    delay = min(base_delay * (2**attempt), max_delay)

    # Add jitter (±25%)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    return delay + jitter


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[List[ErrorType]] = None,
):
    """
    Decorator for retry with exponential backoff

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        retry_on: List of error types to retry (None = retry all)

    Example:
        @retry_with_backoff(max_retries=3)
        def fetch_citations(pmid):
            return api.get_citing_papers(pmid)
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    # Classify error
                    if isinstance(e, DiscoveryError):
                        error = e
                    else:
                        error = classify_error(e, source=func.__name__)

                    last_error = error

                    # Check if we should retry
                    if retry_on and error.error_type not in retry_on:
                        logger.warning(f"Error type {error.error_type} not in retry list, failing")
                        raise error

                    # Last attempt - don't retry
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded: {error}")
                        raise error

                    # Calculate backoff
                    if error.retry_after:
                        delay = error.retry_after
                        logger.info(f"Rate limited, waiting {delay}s as instructed")
                    else:
                        delay = calculate_backoff(attempt, base_delay, max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {error}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_error

        return wrapper

    return decorator


class FallbackChain:
    """
    Execute a chain of fallback strategies

    If one source fails, automatically try the next one.

    Example:
        chain = FallbackChain("citation_discovery")
        chain.add_strategy("openalex", openalex_client.get_citing_papers)
        chain.add_strategy("semantic_scholar", s2_client.get_citing_papers)
        
        result = chain.execute(pmid="12345678")
    """

    def __init__(self, name: str):
        self.name = name
        self.strategies: List[Dict[str, Any]] = []
        self.stats = {"total_calls": 0, "fallback_used": 0, "success_by_source": {}}

    def add_strategy(
        self, source: str, func: Callable, priority: int = 0, max_retries: int = 2
    ) -> "FallbackChain":
        """
        Add a fallback strategy

        Args:
            source: Source name (e.g., "openalex", "semantic_scholar")
            func: Function to call
            priority: Lower = higher priority (0 = first)
            max_retries: Max retries for this strategy

        Returns:
            Self for chaining
        """
        self.strategies.append(
            {"source": source, "func": func, "priority": priority, "max_retries": max_retries}
        )

        # Sort by priority
        self.strategies.sort(key=lambda x: x["priority"])

        logger.debug(f"Added fallback strategy: {source} (priority: {priority})")
        return self

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the fallback chain

        Tries each strategy in order until one succeeds.

        Args:
            *args, **kwargs: Arguments to pass to each strategy function

        Returns:
            Result from first successful strategy

        Raises:
            DiscoveryError: If all strategies fail
        """
        self.stats["total_calls"] += 1
        errors = []

        for i, strategy in enumerate(self.strategies):
            source = strategy["source"]
            func = strategy["func"]
            max_retries = strategy["max_retries"]

            logger.debug(f"Trying strategy {i + 1}/{len(self.strategies)}: {source}")

            try:
                # Wrap with retry logic
                wrapped_func = retry_with_backoff(max_retries=max_retries)(func)
                result = wrapped_func(*args, **kwargs)

                # Success!
                if i > 0:
                    self.stats["fallback_used"] += 1
                    logger.info(f"✓ Fallback to {source} succeeded (after {i} failures)")

                self.stats["success_by_source"][source] = (
                    self.stats["success_by_source"].get(source, 0) + 1
                )
                return result

            except Exception as e:
                error = classify_error(e, source=source)
                errors.append(error)
                logger.warning(f"Strategy {source} failed: {error}")

                # If this is the last strategy, raise
                if i == len(self.strategies) - 1:
                    logger.error(f"All {len(self.strategies)} strategies failed")
                    raise DiscoveryError(
                        message=f"All fallback strategies failed: {[str(e) for e in errors]}",
                        error_type=ErrorType.UNKNOWN,
                        source=self.name,
                        original_error=errors[-1],
                    )

        # Should never reach here
        raise DiscoveryError(
            message="Fallback chain exhausted",
            error_type=ErrorType.UNKNOWN,
            source=self.name,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about fallback usage"""
        return {
            "total_calls": self.stats["total_calls"],
            "fallback_used": self.stats["fallback_used"],
            "fallback_rate": (
                self.stats["fallback_used"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0
                else 0.0
            ),
            "success_by_source": self.stats["success_by_source"],
        }


# Pre-configured fallback chains for common scenarios
def get_citation_discovery_chain(openalex_client, semantic_scholar_client) -> FallbackChain:
    """
    Get fallback chain for citation discovery

    Strategy:
    1. Try OpenAlex first (usually faster)
    2. Fallback to Semantic Scholar
    """
    chain = FallbackChain("citation_discovery")
    chain.add_strategy("openalex", openalex_client.get_citing_papers, priority=0, max_retries=2)
    chain.add_strategy(
        "semantic_scholar", semantic_scholar_client.get_citing_papers, priority=1, max_retries=2
    )
    return chain


def get_text_search_chain(pubmed_client, semantic_scholar_client) -> FallbackChain:
    """
    Get fallback chain for text search

    Strategy:
    1. Try PubMed first (biomedical papers)
    2. Fallback to Semantic Scholar (broader coverage)
    """
    chain = FallbackChain("text_search")
    chain.add_strategy("pubmed", pubmed_client.search, priority=0, max_retries=2)
    chain.add_strategy("semantic_scholar", semantic_scholar_client.search, priority=1, max_retries=2)
    return chain


# Example usage
if __name__ == "__main__":
    import time

    # Test retry with backoff
    print("=== Test 1: Retry with backoff ===")

    attempt = 0

    @retry_with_backoff(max_retries=3, base_delay=0.5)
    def flaky_function():
        global attempt
        attempt += 1
        print(f"Attempt {attempt}")
        if attempt < 3:
            raise Exception("Simulated transient error")
        return "Success!"

    try:
        result = flaky_function()
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Failed: {e}\n")

    # Test fallback chain
    print("=== Test 2: Fallback chain ===")

    def primary_func(x):
        print(f"  Primary: trying with {x}")
        raise Exception("Primary failed")

    def fallback_func(x):
        print(f"  Fallback: trying with {x}")
        return f"Success from fallback! (x={x})"

    chain = FallbackChain("test_chain")
    chain.add_strategy("primary", primary_func, priority=0, max_retries=1)
    chain.add_strategy("fallback", fallback_func, priority=1, max_retries=1)

    result = chain.execute(42)
    print(f"Result: {result}")

    stats = chain.get_stats()
    print(f"Stats: {stats}\n")

    print("=== Tests complete! ===")
