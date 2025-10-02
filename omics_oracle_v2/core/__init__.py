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

Status: Phase 1 Task 2 (In Progress)
"""

# Exports will be added as modules are implemented
# from .config import Settings, NLPSettings, GEOSettings, AISettings
# from .exceptions import (
#     OmicsOracleError,
#     ConfigurationError,
#     NLPError,
#     GEOError,
#     AIError,
# )

__all__ = []
