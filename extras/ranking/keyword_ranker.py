"""
Keyword-based relevance ranking for GEO datasets.

Provides configurable, testable ranking logic extracted from SearchAgent.
Supports exact keyword matching with weighted scoring across multiple fields.
"""

import logging
from typing import List, Set, Tuple

from ...core.config import RankingConfig
from ...lib.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


class KeywordRanker:
    """
    Keyword-based relevance ranker for GEO datasets.

    Calculates relevance scores (0.0-1.0) based on keyword matches in:
    - Dataset title (highest weight)
    - Dataset summary (medium weight)
    - Organism match (bonus)
    - Sample count adequacy (bonus)

    All weights and thresholds are configurable via RankingConfig.

    Example:
        >>> from omics_oracle_v2.core.config import Settings
        >>> settings = Settings()
        >>> ranker = KeywordRanker(settings.ranking)
        >>>
        >>> search_terms = ["ATAC-seq", "chromatin", "accessibility"]
        >>> score, reasons = ranker.calculate_relevance(dataset, search_terms)
        >>> print(f"Score: {score:.2f}")
        >>> for reason in reasons:
        ...     print(f"  - {reason}")
    """

    def __init__(self, config: RankingConfig):
        """
        Initialize keyword ranker with configuration.

        Args:
            config: RankingConfig with weights and thresholds
        """
        self.config = config
        logger.debug(f"Initialized KeywordRanker with config: {config}")

    def calculate_relevance(
        self,
        dataset: GEOSeriesMetadata,
        search_terms: List[str],
        organism: str | None = None,
    ) -> Tuple[float, List[str]]:
        """
        Calculate relevance score for a dataset based on keyword matches.

        Args:
            dataset: GEO dataset metadata
            search_terms: List of search terms to match
            organism: Optional organism filter

        Returns:
            Tuple of (score, match_reasons)
            - score: Float between 0.0 and 1.0
            - match_reasons: List of human-readable match explanations

        Example:
            >>> score, reasons = ranker.calculate_relevance(
            ...     dataset,
            ...     ["ATAC-seq", "chromatin"],
            ...     organism="Homo sapiens"
            ... )
            >>> print(score)  # 0.75
            >>> print(reasons)
            >>> # ['Title matches 2 search term(s)', 'Organism matches: Homo sapiens']
        """
        score = 0.0
        reasons = []

        # Normalize search terms for case-insensitive matching
        search_terms_lower = self._normalize_terms(search_terms)

        # 1. Title matches (highest weight)
        title_score, title_reasons = self._score_title_matches(dataset.title or "", search_terms_lower)
        score += title_score
        reasons.extend(title_reasons)

        # 2. Summary matches (medium weight)
        summary_score, summary_reasons = self._score_summary_matches(
            dataset.summary or "", search_terms_lower
        )
        score += summary_score
        reasons.extend(summary_reasons)

        # 3. Organism match (bonus)
        if organism:
            organism_score, organism_reasons = self._score_organism_match(dataset.organism or "", organism)
            score += organism_score
            reasons.extend(organism_reasons)

        # 4. Sample count adequacy (bonus)
        sample_score, sample_reasons = self._score_sample_count(dataset.sample_count)
        score += sample_score
        reasons.extend(sample_reasons)

        # Normalize to 0.0-1.0 range
        score = min(1.0, score)

        # Ensure minimum score if any match exists
        if not reasons:
            reasons.append("General database match")
            score = 0.1  # Minimum score for being in results

        return score, reasons

    def _normalize_terms(self, terms: List[str]) -> Set[str]:
        """
        Normalize search terms to lowercase set.

        Args:
            terms: List of search terms

        Returns:
            Set of lowercase terms
        """
        return {term.lower() for term in terms}

    def _score_title_matches(self, title: str, search_terms_lower: Set[str]) -> Tuple[float, List[str]]:
        """
        Score keyword matches in dataset title.

        Args:
            title: Dataset title
            search_terms_lower: Set of lowercase search terms

        Returns:
            Tuple of (score, reasons)
        """
        title_lower = title.lower()
        matches = sum(1 for term in search_terms_lower if term in title_lower)

        if matches == 0:
            return 0.0, []

        # Score: min(max_weight, matches * multiplier)
        score = min(self.config.keyword_title_weight, matches * self.config.keyword_match_multiplier)

        reasons = [f"Title matches {matches} search term(s)"]
        return score, reasons

    def _score_summary_matches(self, summary: str, search_terms_lower: Set[str]) -> Tuple[float, List[str]]:
        """
        Score keyword matches in dataset summary.

        Args:
            summary: Dataset summary
            search_terms_lower: Set of lowercase search terms

        Returns:
            Tuple of (score, reasons)
        """
        summary_lower = summary.lower()
        matches = sum(1 for term in search_terms_lower if term in summary_lower)

        if matches == 0:
            return 0.0, []

        # Score: min(max_weight, matches * multiplier)
        score = min(self.config.keyword_summary_weight, matches * self.config.keyword_summary_multiplier)

        reasons = [f"Summary matches {matches} search term(s)"]
        return score, reasons

    def _score_organism_match(self, dataset_organism: str, query_organism: str) -> Tuple[float, List[str]]:
        """
        Score organism match.

        Args:
            dataset_organism: Organism from dataset metadata
            query_organism: Organism from search query

        Returns:
            Tuple of (score, reasons)
        """
        dataset_organism_lower = dataset_organism.lower()
        query_organism_lower = query_organism.lower()

        if query_organism_lower not in dataset_organism_lower:
            return 0.0, []

        score = self.config.keyword_organism_bonus
        reasons = [f"Organism matches: {dataset_organism}"]

        return score, reasons

    def _score_sample_count(self, sample_count: int | None) -> Tuple[float, List[str]]:
        """
        Score sample count adequacy.

        Args:
            sample_count: Number of samples in dataset

        Returns:
            Tuple of (score, reasons)
        """
        if not sample_count:
            return 0.0, []

        # Progressive bonus based on sample count thresholds
        if sample_count >= self.config.sample_count_large:
            score = self.config.keyword_sample_count_bonus
            reasons = [f"Large sample size: {sample_count} samples"]
        elif sample_count >= self.config.sample_count_medium:
            score = self.config.keyword_sample_count_bonus * 0.67
            reasons = [f"Good sample size: {sample_count} samples"]
        elif sample_count >= self.config.sample_count_small:
            score = self.config.keyword_sample_count_bonus * 0.33
            reasons = [f"Adequate sample size: {sample_count} samples"]
        else:
            return 0.0, []

        return score, reasons

    def explain_config(self) -> str:
        """
        Get human-readable explanation of ranking configuration.

        Returns:
            Formatted string explaining weights and thresholds

        Example:
            >>> print(ranker.explain_config())
            Keyword Ranking Configuration:
              Title weight: 0.40 (max)
              Summary weight: 0.30 (max)
              Organism bonus: 0.15
              Sample count bonus: 0.15
              Sample thresholds: 100+ (large), 50+ (medium), 10+ (small)
        """
        return f"""Keyword Ranking Configuration:
  Title weight: {self.config.keyword_title_weight:.2f} (max)
  Summary weight: {self.config.keyword_summary_weight:.2f} (max)
  Organism bonus: {self.config.keyword_organism_bonus:.2f}
  Sample count bonus: {self.config.keyword_sample_count_bonus:.2f}
  Sample thresholds: {self.config.sample_count_large}+ (large), {self.config.sample_count_medium}+ (medium), {self.config.sample_count_small}+ (small)
  Match multipliers: title={self.config.keyword_match_multiplier}, summary={self.config.keyword_summary_multiplier}"""
