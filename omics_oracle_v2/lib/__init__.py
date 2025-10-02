"""
Algorithm library for OmicsOracle v2.

This package contains standalone, reusable implementations of core biomedical
algorithms extracted from the v1 codebase. Each submodule is designed to work
independently with zero dependencies on the old architecture.

Modules:
    - nlp: Biomedical named entity recognition and text processing
    - geo: GEO database access and data retrieval
    - ai: AI-powered summarization and analysis

All modules follow these principles:
    - Standalone operation (no v1 imports)
    - Full type hints (PEP 561 compliant)
    - Comprehensive testing (80%+ coverage)
    - Dependency injection (configurable via Settings)
    - Immutable data models (Pydantic-based)
"""

__all__ = []  # Exports added as modules are implemented
