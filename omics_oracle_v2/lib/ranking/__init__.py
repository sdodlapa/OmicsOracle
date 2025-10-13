"""
Ranking and quality scoring module for OmicsOracle.

Provides modular, configurable classes for:
- Dataset quality assessment
- Synonym expansion (Phase 1)
- Semantic similarity search (Phase 2)

This module separates scoring logic from agent implementations,
making it easier to test, tune, and extend with new algorithms.

Example:
    >>> from omics_oracle_v2.lib.ranking import QualityScorer
    >>> from omics_oracle_v2.core.config import Settings
    >>>
    >>> settings = Settings()
    >>> scorer = QualityScorer(settings.quality)
    >>>
    >>> quality, issues, strengths = scorer.calculate_quality(metadata)
"""

# Archived: KeywordRanker (unused in production, moved to extras/ranking/)
from .quality_scorer import QualityScorer

__all__ = [
    "QualityScorer",
]
