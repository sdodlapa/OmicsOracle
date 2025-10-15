"""
Content Quality Scorer

Assigns quality scores to enriched content based on multiple criteria.
Helps identify well-extracted papers vs. problematic ones.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Individual quality metrics."""

    text_length_score: float = 0.0  # 0-1 based on text length
    section_score: float = 0.0  # 0-1 based on section detection
    abstract_score: float = 0.0  # 0-1 if abstract found
    table_score: float = 0.0  # 0-1 based on table extraction
    reference_score: float = 0.0  # 0-1 based on reference parsing
    structure_score: float = 0.0  # 0-1 based on overall structure

    total_score: float = 0.0  # Weighted average
    grade: str = "F"  # A, B, C, D, F


class QualityScorer:
    """Score enriched content quality."""

    # Weights for different quality dimensions
    WEIGHTS = {
        "text_length": 0.20,
        "sections": 0.25,
        "abstract": 0.15,
        "tables": 0.10,
        "references": 0.10,
        "structure": 0.20,
    }

    # Grading thresholds
    GRADES = [
        (0.90, "A"),  # Excellent
        (0.75, "B"),  # Good
        (0.60, "C"),  # Fair
        (0.40, "D"),  # Poor
        (0.00, "F"),  # Failed
    ]

    @staticmethod
    def score_content(enriched: Dict) -> QualityMetrics:
        """
        Score enriched content quality.

        Args:
            enriched: Enriched content dict from PDFExtractor

        Returns:
            QualityMetrics with scores and grade
        """
        metrics = QualityMetrics()

        # 1. Text Length Score (0-0.2)
        text_len = enriched.get("text_length", 0)
        if text_len > 20000:
            metrics.text_length_score = 1.0
        elif text_len > 10000:
            metrics.text_length_score = 0.8
        elif text_len > 5000:
            metrics.text_length_score = 0.5
        elif text_len > 1000:
            metrics.text_length_score = 0.2
        else:
            metrics.text_length_score = 0.0

        # 2. Section Score (0-0.25)
        sections = enriched.get("sections", {})
        section_names = set(sections.keys())

        # Check for key sections
        has_intro = any(s in section_names for s in ["introduction", "background"])
        has_methods = any(s in section_names for s in ["methods", "methodology"])
        has_results = "results" in section_names
        has_discussion = "discussion" in section_names

        section_score = 0.0
        if has_intro:
            section_score += 0.25
        if has_methods:
            section_score += 0.25
        if has_results:
            section_score += 0.25
        if has_discussion:
            section_score += 0.25

        metrics.section_score = section_score

        # 3. Abstract Score (0-0.15)
        abstract = enriched.get("abstract")
        if abstract and len(abstract) > 100:
            metrics.abstract_score = 1.0
        elif abstract:
            metrics.abstract_score = 0.5
        else:
            metrics.abstract_score = 0.0

        # 4. Table Score (0-0.1)
        table_count = enriched.get("table_count", 0)
        if table_count >= 3:
            metrics.table_score = 1.0
        elif table_count >= 1:
            metrics.table_score = 0.5
        else:
            metrics.table_score = 0.0

        # 5. Reference Score (0-0.1)
        ref_count = enriched.get("reference_count", 0)
        if ref_count >= 20:
            metrics.reference_score = 1.0
        elif ref_count >= 10:
            metrics.reference_score = 0.7
        elif ref_count >= 1:
            metrics.reference_score = 0.4
        else:
            metrics.reference_score = 0.0

        # 6. Structure Score (0-0.2)
        # Overall structure quality
        structure_score = 0.0

        # Has sections
        if len(sections) >= 4:
            structure_score += 0.4
        elif len(sections) >= 2:
            structure_score += 0.2

        # Sections have content
        if sections:
            avg_section_len = sum(len(str(s)) for s in sections.values()) / len(sections)
            if avg_section_len > 1000:
                structure_score += 0.3
            elif avg_section_len > 500:
                structure_score += 0.15

        # Has both abstract and references
        if abstract and ref_count > 0:
            structure_score += 0.3

        metrics.structure_score = min(structure_score, 1.0)

        # Calculate total score (weighted average)
        total = 0.0
        total += metrics.text_length_score * QualityScorer.WEIGHTS["text_length"]
        total += metrics.section_score * QualityScorer.WEIGHTS["sections"]
        total += metrics.abstract_score * QualityScorer.WEIGHTS["abstract"]
        total += metrics.table_score * QualityScorer.WEIGHTS["tables"]
        total += metrics.reference_score * QualityScorer.WEIGHTS["references"]
        total += metrics.structure_score * QualityScorer.WEIGHTS["structure"]

        metrics.total_score = round(total, 2)

        # Assign grade
        for threshold, grade in QualityScorer.GRADES:
            if metrics.total_score >= threshold:
                metrics.grade = grade
                break

        return metrics

    @staticmethod
    def filter_by_quality(
        enriched_list: List[Dict],
        min_score: float = 0.6,
        min_grade: str = "C",
    ) -> List[Dict]:
        """
        Filter enriched content by minimum quality.

        Args:
            enriched_list: List of enriched content dicts
            min_score: Minimum quality score (0-1)
            min_grade: Minimum grade (A, B, C, D, F)

        Returns:
            Filtered list meeting quality criteria
        """
        grade_values = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        min_grade_value = grade_values.get(min_grade, 1)

        filtered = []
        for enriched in enriched_list:
            metrics = QualityScorer.score_content(enriched)

            # Check criteria
            meets_score = metrics.total_score >= min_score
            meets_grade = grade_values.get(metrics.grade, 0) >= min_grade_value

            if meets_score and meets_grade:
                # Add quality metrics to enriched content
                enriched["quality_metrics"] = {
                    "score": metrics.total_score,
                    "grade": metrics.grade,
                    "text_length_score": metrics.text_length_score,
                    "section_score": metrics.section_score,
                    "abstract_score": metrics.abstract_score,
                    "table_score": metrics.table_score,
                    "reference_score": metrics.reference_score,
                    "structure_score": metrics.structure_score,
                }
                filtered.append(enriched)

        logger.info(
            f"Quality filter: {len(filtered)}/{len(enriched_list)} papers passed "
            f"(min_score={min_score}, min_grade={min_grade})"
        )

        return filtered
