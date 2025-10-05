"""
Ranking and quality scoring module for OmicsOracle.

Provides modular, configurable classes for:
- Keyword-based relevance ranking
- Dataset quality assessment
- Synonym expansion (Phase 1)
- Semantic similarity search (Phase 2)

This module separates scoring logic from agent implementations,
making it easier to test, tune, and extend with new algorithms.

Example:
    >>> from omics_oracle_v2.lib.ranking import KeywordRanker, QualityScorer
    >>> from omics_oracle_v2.core.config import Settings
    >>>
    >>> settings = Settings()
    >>> ranker = KeywordRanker(settings.ranking)
    >>> scorer = QualityScorer(settings.quality)
    >>>
    >>> # Use in agents
    >>> score, reasons = ranker.calculate_relevance(dataset, search_terms)
    >>> quality, issues, strengths = scorer.calculate_quality(metadata)
"""

from .keyword_ranker import KeywordRanker
from .quality_scorer import QualityScorer

__all__ = [
    "KeywordRanker",
    "QualityScorer",
]
