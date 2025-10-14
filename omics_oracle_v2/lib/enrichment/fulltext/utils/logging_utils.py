"""
Logging utilities for fulltext enrichment sources.

Provides standardized logging functions with visual indicators and source prefixes
for easy filtering and debugging.

Format: [SOURCE] ✓/✗/⚠ Message

Created: October 14, 2025 (Phase 2.3 - Pipeline 2 Cleanup)
"""

import logging
from typing import Optional

# Visual indicators
SUCCESS = "✓"
FAILURE = "✗"
WARNING = "⚠"
INFO = "ℹ"


def log_source_success(logger: logging.Logger, source: str, message: str, **kwargs):
    """
    Log a successful operation from a source.

    Format: [SOURCE] ✓ Message

    Args:
        logger: Logger instance
        source: Source name (e.g., 'PMC', 'CORE', 'Unpaywall')
        message: Log message
        **kwargs: Additional context to include

    Example:
        >>> log_source_success(logger, "PMC", "Found fulltext", pmcid="PMC12345")
        # Output: [PMC] ✓ Found fulltext (pmcid=PMC12345)
    """
    context = _format_context(kwargs)
    logger.info(f"[{source}] {SUCCESS} {message}{context}")


def log_source_failure(logger: logging.Logger, source: str, message: str, **kwargs):
    """
    Log a failed operation from a source.

    Format: [SOURCE] ✗ Message

    Args:
        logger: Logger instance
        source: Source name
        message: Log message
        **kwargs: Additional context to include

    Example:
        >>> log_source_failure(logger, "CORE", "API error", status=500)
        # Output: [CORE] ✗ API error (status=500)
    """
    context = _format_context(kwargs)
    logger.warning(f"[{source}] {FAILURE} {message}{context}")


def log_source_warning(logger: logging.Logger, source: str, message: str, **kwargs):
    """
    Log a warning from a source.

    Format: [SOURCE] ⚠ Message

    Args:
        logger: Logger instance
        source: Source name
        message: Log message
        **kwargs: Additional context to include

    Example:
        >>> log_source_warning(logger, "Unpaywall", "Rate limited", wait_time=5)
        # Output: [Unpaywall] ⚠ Rate limited (wait_time=5)
    """
    context = _format_context(kwargs)
    logger.warning(f"[{source}] {WARNING} {message}{context}")


def log_source_info(logger: logging.Logger, source: str, message: str, **kwargs):
    """
    Log informational message from a source.

    Format: [SOURCE] ℹ Message

    Args:
        logger: Logger instance
        source: Source name
        message: Log message
        **kwargs: Additional context to include

    Example:
        >>> log_source_info(logger, "arXiv", "Initializing client", rate_limit=3.0)
        # Output: [arXiv] ℹ Initializing client (rate_limit=3.0)
    """
    context = _format_context(kwargs)
    logger.info(f"[{source}] {INFO} {message}{context}")


def log_source_debug(logger: logging.Logger, source: str, message: str, **kwargs):
    """
    Log debug message from a source.

    Format: [SOURCE] Message

    Args:
        logger: Logger instance
        source: Source name
        message: Log message
        **kwargs: Additional context to include

    Example:
        >>> log_source_debug(logger, "PMC", "Trying URL pattern", pattern="oa_api")
        # Output: [PMC] Trying URL pattern (pattern=oa_api)
    """
    context = _format_context(kwargs)
    logger.debug(f"[{source}] {message}{context}")


def log_source_error(
    logger: logging.Logger, source: str, message: str, error: Optional[Exception] = None, **kwargs
):
    """
    Log an error from a source.

    Format: [SOURCE] ✗ Message

    Args:
        logger: Logger instance
        source: Source name
        message: Log message
        error: Optional exception to include
        **kwargs: Additional context to include

    Example:
        >>> log_source_error(logger, "CORE", "Request failed", error=e, attempt=3)
        # Output: [CORE] ✗ Request failed: ValueError(...) (attempt=3)
    """
    if error:
        message = f"{message}: {error}"
    context = _format_context(kwargs)
    logger.error(f"[{source}] {FAILURE} {message}{context}")


def _format_context(context: dict) -> str:
    """
    Format context dictionary as a string.

    Args:
        context: Dictionary of key-value pairs

    Returns:
        Formatted context string like " (key1=value1, key2=value2)"

    Example:
        >>> _format_context({"doi": "10.1234", "attempt": 2})
        " (doi=10.1234, attempt=2)"
    """
    if not context:
        return ""

    items = [f"{k}={v}" for k, v in context.items()]
    return f" ({', '.join(items)})"


# Convenience function for grep filtering
def grep_pattern(source: str) -> str:
    """
    Get grep pattern to filter logs for a specific source.

    Args:
        source: Source name

    Returns:
        Grep pattern string

    Example:
        >>> pattern = grep_pattern("PMC")
        >>> # Use in terminal: grep "[PMC]" logfile.log
    """
    return f"[{source}]"
