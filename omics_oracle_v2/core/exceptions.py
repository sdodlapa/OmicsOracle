"""
Custom exceptions for OmicsOracle v2.

Provides a clear exception hierarchy for different types of errors that can
occur in the system. All exceptions inherit from OmicsOracleError for easy
catching of any package-specific error.

Exception Hierarchy:
    OmicsOracleError (base)
    +-- ConfigurationError - Configuration and settings issues
    +-- NLPError - NLP processing errors
    +-- GEOError - GEO data access errors
    +-- AIError - AI service errors

Example:
    >>> from omics_oracle_v2.core.exceptions import GEOError
    >>> try:
    ...     client.get_series("INVALID")
    ... except GEOError as e:
    ...     print(f"GEO error: {e}")
"""


class OmicsOracleError(Exception):
    """Base exception for all OmicsOracle v2 errors."""

    pass


class ConfigurationError(OmicsOracleError):
    """Raised when there are configuration or settings issues."""

    pass


class NLPError(OmicsOracleError):
    """Raised when NLP processing fails."""

    pass


class GEOError(OmicsOracleError):
    """Raised when GEO data access fails."""

    pass


class AIError(OmicsOracleError):
    """Raised when AI services fail."""

    pass
