"""
Dataset quality scoring for GEO datasets.

Provides configurable, testable quality assessment logic extracted from DataAgent.
Evaluates datasets across multiple quality dimensions with weighted scoring.
"""

import logging
from typing import List, Tuple

from ...core.config import QualityConfig
from ...lib.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Quality scorer for GEO datasets.

    Calculates quality scores (0.0-1.0) based on:
    - Sample count (20 points)
    - Title quality (15 points)
    - Summary quality (15 points)
    - Publications (20 points)
    - SRA data availability (10 points)
    - Dataset recency (10 points)
    - Metadata completeness (10 points)

    Total: 100 points, normalized to 0.0-1.0 scale.
    All thresholds are configurable via QualityConfig.

    Example:
        >>> from omics_oracle_v2.core.config import Settings
        >>> settings = Settings()
        >>> scorer = QualityScorer(settings.quality)
        >>>
        >>> quality, issues, strengths = scorer.calculate_quality(metadata)
        >>> print(f"Quality: {quality:.2f}")
        >>> print("Strengths:", strengths)
        >>> print("Issues:", issues)
    """

    def __init__(self, config: QualityConfig):
        """
        Initialize quality scorer with configuration.

        Args:
            config: QualityConfig with points and thresholds
        """
        self.config = config
        logger.debug(f"Initialized QualityScorer with config: {config}")

    def calculate_quality(self, metadata: GEOSeriesMetadata) -> Tuple[float, List[str], List[str]]:
        """
        Calculate quality score for a dataset.

        Args:
            metadata: GEO dataset metadata

        Returns:
            Tuple of (quality_score, issues, strengths)
            - quality_score: Float between 0.0 and 1.0
            - issues: List of quality issues found
            - strengths: List of quality strengths found

        Example:
            >>> quality, issues, strengths = scorer.calculate_quality(metadata)
            >>> print(f"Quality: {quality:.2f}")  # 0.85
            >>> print("Issues:", issues)
            >>> # ['No SRA sequencing data']
            >>> print("Strengths:", strengths)
            >>> # ['Large sample size: 150 samples', 'Published (3 publication(s))']
        """
        score = 0.0
        issues = []
        strengths = []

        # 1. Sample count (0-20 points)
        sample_score, sample_issues, sample_strengths = self._score_sample_count(metadata.sample_count)
        score += sample_score
        issues.extend(sample_issues)
        strengths.extend(sample_strengths)

        # 2. Title quality (0-15 points)
        title_score, title_issues, title_strengths = self._score_title_quality(metadata.title)
        score += title_score
        issues.extend(title_issues)
        strengths.extend(title_strengths)

        # 3. Summary quality (0-15 points)
        summary_score, summary_issues, summary_strengths = self._score_summary_quality(metadata.summary)
        score += summary_score
        issues.extend(summary_issues)
        strengths.extend(summary_strengths)

        # 4. Publications (0-20 points)
        pub_score, pub_issues, pub_strengths = self._score_publications(metadata.pubmed_ids)
        score += pub_score
        issues.extend(pub_issues)
        strengths.extend(pub_strengths)

        # 5. SRA data availability (0-10 points)
        sra_score, sra_issues, sra_strengths = self._score_sra_data(metadata)
        score += sra_score
        issues.extend(sra_issues)
        strengths.extend(sra_strengths)

        # 6. Dataset recency (0-10 points)
        recency_score, recency_issues, recency_strengths = self._score_recency(metadata)
        score += recency_score
        issues.extend(recency_issues)
        strengths.extend(recency_strengths)

        # 7. Metadata completeness (0-10 points)
        metadata_score, metadata_issues, metadata_strengths = self._score_metadata_completeness(metadata)
        score += metadata_score
        issues.extend(metadata_issues)
        strengths.extend(metadata_strengths)

        # Normalize to 0.0-1.0
        quality_score = min(1.0, score / 100.0)

        return quality_score, issues, strengths

    def _score_sample_count(self, sample_count: int | None) -> Tuple[float, List[str], List[str]]:
        """
        Score sample count quality.

        Args:
            sample_count: Number of samples

        Returns:
            Tuple of (score, issues, strengths)
        """
        if not sample_count:
            return 0.0, ["Missing sample count information"], []

        max_points = self.config.points_sample_count

        if sample_count >= self.config.sample_count_excellent:
            score = max_points
            strengths = [f"Large sample size: {sample_count} samples"]
            issues = []
        elif sample_count >= self.config.sample_count_good:
            score = max_points * 0.75
            strengths = [f"Good sample size: {sample_count} samples"]
            issues = []
        elif sample_count >= self.config.sample_count_adequate:
            score = max_points * 0.5
            strengths = [f"Adequate sample size: {sample_count} samples"]
            issues = []
        else:
            score = max_points * 0.25
            issues = [f"Small sample size: {sample_count} samples"]
            strengths = []

        return score, issues, strengths

    def _score_title_quality(self, title: str | None) -> Tuple[float, List[str], List[str]]:
        """
        Score title quality based on length and descriptiveness.

        Args:
            title: Dataset title

        Returns:
            Tuple of (score, issues, strengths)
        """
        if not title:
            return 0.0, ["Missing title"], []

        max_points = self.config.points_title
        title_len = len(title)

        if title_len >= self.config.title_length_descriptive:
            score = max_points
            strengths = ["Descriptive title"]
            issues = []
        elif title_len >= self.config.title_length_adequate:
            score = max_points * 0.67
            strengths = []
            issues = []
        elif title_len >= self.config.title_length_minimal:
            score = max_points * 0.33
            strengths = []
            issues = []
        else:
            score = max_points * 0.33
            issues = ["Very short title"]
            strengths = []

        return score, issues, strengths

    def _score_summary_quality(self, summary: str | None) -> Tuple[float, List[str], List[str]]:
        """
        Score summary quality based on length and informativeness.

        Args:
            summary: Dataset summary

        Returns:
            Tuple of (score, issues, strengths)
        """
        if not summary:
            return 0.0, ["Missing summary"], []

        max_points = self.config.points_summary
        summary_len = len(summary)

        if summary_len >= self.config.summary_length_comprehensive:
            score = max_points
            strengths = ["Comprehensive summary"]
            issues = []
        elif summary_len >= self.config.summary_length_good:
            score = max_points * 0.67
            strengths = []
            issues = []
        elif summary_len >= self.config.summary_length_minimal:
            score = max_points * 0.33
            strengths = []
            issues = []
        else:
            score = 0.0
            issues = ["Very short summary"]
            strengths = []

        return score, issues, strengths

    def _score_publications(self, pubmed_ids: List[str] | None) -> Tuple[float, List[str], List[str]]:
        """
        Score publication quality.

        Args:
            pubmed_ids: List of PubMed IDs

        Returns:
            Tuple of (score, issues, strengths)
        """
        if not pubmed_ids or len(pubmed_ids) == 0:
            return 0.0, ["No associated publications"], []

        max_points = self.config.points_publications
        pub_count = len(pubmed_ids)

        if pub_count >= self.config.publications_many:
            score = max_points
        elif pub_count >= self.config.publications_some:
            score = max_points * 0.75
        elif pub_count >= self.config.publications_one:
            score = max_points * 0.5
        else:
            score = 0.0

        strengths = [f"Published ({pub_count} publication(s))"]
        issues = []

        return score, issues, strengths

    def _score_sra_data(self, metadata: GEOSeriesMetadata) -> Tuple[float, List[str], List[str]]:
        """
        Score SRA data availability.

        Args:
            metadata: Dataset metadata

        Returns:
            Tuple of (score, issues, strengths)
        """
        max_points = self.config.points_sra_data

        if metadata.has_sra_data():
            score = max_points
            strengths = ["Raw sequencing data available (SRA)"]
            issues = []
        else:
            score = 0.0
            issues = ["No SRA sequencing data"]
            strengths = []

        return score, issues, strengths

    def _score_recency(self, metadata: GEOSeriesMetadata) -> Tuple[float, List[str], List[str]]:
        """
        Score dataset recency.

        Args:
            metadata: Dataset metadata

        Returns:
            Tuple of (score, issues, strengths)
        """
        age_days = metadata.get_age_days()

        if age_days is None:
            return 0.0, [], []

        max_points = self.config.points_recency

        if age_days <= self.config.recency_recent:
            score = max_points
            strengths = ["Recent dataset (< 1 year old)"]
            issues = []
        elif age_days <= self.config.recency_moderate:
            score = max_points * 0.5
            strengths = []
            issues = []
        elif age_days <= self.config.recency_old:
            score = max_points * 0.25
            strengths = []
            issues = []
        else:
            score = 0.0
            issues = [f"Old dataset ({age_days // 365} years)"]
            strengths = []

        return score, issues, strengths

    def _score_metadata_completeness(self, metadata: GEOSeriesMetadata) -> Tuple[float, List[str], List[str]]:
        """
        Score metadata completeness.

        Args:
            metadata: Dataset metadata

        Returns:
            Tuple of (score, issues, strengths)
        """
        # Count non-null metadata fields
        fields = [
            metadata.geo_id,
            metadata.title,
            metadata.summary,
            metadata.organism,
            metadata.sample_count,
            metadata.pubmed_ids,
            metadata.platforms,
            metadata.submission_date,
            metadata.last_update_date,
            metadata.contact_name,
        ]

        filled_fields = sum(1 for field in fields if field)
        total_fields = len(fields)
        _ = filled_fields / total_fields  # Calculated for potential future use

        max_points = self.config.points_metadata

        if filled_fields >= self.config.metadata_fields_complete:
            score = max_points
            strengths = ["Complete metadata"]
            issues = []
        elif filled_fields >= self.config.metadata_fields_good:
            score = max_points * 0.75
            strengths = []
            issues = []
        elif filled_fields >= self.config.metadata_fields_basic:
            score = max_points * 0.5
            strengths = []
            issues = []
        else:
            score = max_points * 0.25
            issues = ["Incomplete metadata"]
            strengths = []

        return score, issues, strengths

    def get_quality_level(self, score: float) -> str:
        """
        Determine quality level from score.

        Args:
            score: Quality score (0.0-1.0)

        Returns:
            Quality level string: EXCELLENT, GOOD, FAIR, or POOR

        Example:
            >>> level = scorer.get_quality_level(0.85)
            >>> print(level)  # 'EXCELLENT'
        """
        if score >= self.config.excellent_threshold:
            return "EXCELLENT"
        elif score >= self.config.good_threshold:
            return "GOOD"
        elif score >= self.config.fair_threshold:
            return "FAIR"
        else:
            return "POOR"

    def explain_config(self) -> str:
        """
        Get human-readable explanation of quality scoring configuration.

        Returns:
            Formatted string explaining points and thresholds

        Example:
            >>> print(scorer.explain_config())
            Quality Scoring Configuration:
              Sample count: 20 points (100+ excellent, 50+ good, 10+ adequate)
              Title: 15 points (50+ descriptive, 20+ adequate)
              Summary: 15 points (200+ comprehensive, 100+ good)
              ...
        """
        return f"""Quality Scoring Configuration:
  Sample count: {self.config.points_sample_count} points ({self.config.sample_count_excellent}+ excellent, {self.config.sample_count_good}+ good, {self.config.sample_count_adequate}+ adequate)
  Title: {self.config.points_title} points ({self.config.title_length_descriptive}+ descriptive, {self.config.title_length_adequate}+ adequate)
  Summary: {self.config.points_summary} points ({self.config.summary_length_comprehensive}+ comprehensive, {self.config.summary_length_good}+ good)
  Publications: {self.config.points_publications} points ({self.config.publications_many}+ many, {self.config.publications_some}+ some)
  SRA data: {self.config.points_sra_data} points
  Recency: {self.config.points_recency} points (<{self.config.recency_recent} days recent, <{self.config.recency_moderate} moderate)
  Metadata: {self.config.points_metadata} points ({self.config.metadata_fields_complete}+ complete, {self.config.metadata_fields_good}+ good)
  Total: {self.config.points_sample_count + self.config.points_title + self.config.points_summary + self.config.points_publications + self.config.points_sra_data + self.config.points_recency + self.config.points_metadata}/100 points
  Quality thresholds: {self.config.excellent_threshold} (excellent), {self.config.good_threshold} (good), {self.config.fair_threshold} (fair)"""
