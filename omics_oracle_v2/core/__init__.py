"""
Core infrastructure for OmicsOracle v2.

Provides configuration management, exception hierarchy, type definitions,
and other foundational components used across all modules.

Key Components:
    - config: Pydantic-based settings with environment variable support
    - exceptions: Custom exception hierarchy for domain errors
    - types: Common type definitions and protocols

Example:
    >>> from omics_oracle_v2.core.config import Settings
    >>> settings = Settings(debug=True)
    >>> print(settings.nlp.model_name)
    en_core_web_sm

Status: Phase 1 Task 2 (Complete)
"""

from .config import AISettings, GEOSettings, NLPSettings, Settings, get_settings
from .exceptions import AIError, ConfigurationError, GEOError, NLPError, OmicsOracleError

__all__ = [
    # Config
    "Settings",
    "NLPSettings",
    "GEOSettings",
    "AISettings",
    "get_settings",
    # Exceptions
    "OmicsOracleError",
    "ConfigurationError",
    "NLPError",
    "GEOError",
    "AIError",
]
