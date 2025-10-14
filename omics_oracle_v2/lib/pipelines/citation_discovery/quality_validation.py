"""
Publication Quality Validation for Citation Discovery (Phase 8).

Filters and validates discovered citations based on multiple quality criteria:
1. Metadata completeness (title, abstract, authors, etc.)
2. Journal reputation (predatory journals, low-quality venues)
3. Content quality (abstract length, citation count)
4. Publication type (peer-reviewed vs preprints)
5. Temporal relevance (not too old)

This system enhances relevance scoring with explicit quality gates.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality level classification for publications."""
    
    EXCELLENT = "excellent"  # High-quality, well-cited, complete metadata
    GOOD = "good"            # Good quality, some minor issues
    ACCEPTABLE = "acceptable"  # Acceptable but has quality concerns
    POOR = "poor"            # Low quality, consider excluding
    REJECTED = "rejected"    # Fails quality gates, should exclude


@dataclass
class QualityConfig:
    """Configuration for quality validation thresholds."""
    
    # Metadata completeness thresholds
    require_title: bool = True
    require_abstract: bool = True
    min_abstract_length: int = 100  # Minimum abstract length in characters
    require_authors: bool = True
    require_date: bool = True
    require_journal: bool = False  # Optional for preprints
    
    # Content quality thresholds
    min_citations_recent: int = 5  # Min citations for papers < 2 years old
    min_citations_older: int = 10  # Min citations for papers 2-5 years old
    max_age_years: int = 15  # Maximum age in years
    recent_paper_years: int = 5  # Papers within this range are "recent"
    
    # Journal quality
    check_predatory: bool = True
    allow_preprints: bool = True
    require_peer_review: bool = False  # Strict mode
    
    # Overall thresholds
    min_quality_score: float = 0.3  # Minimum overall quality score (0-1)
    excellent_threshold: float = 0.8
    good_threshold: float = 0.6
    acceptable_threshold: float = 0.4


@dataclass
class QualityIssue:
    """Represents a quality issue found in a publication."""
    
    severity: str  # "critical", "warning", "info"
    category: str  # "metadata", "journal", "content", "age"
    message: str
    impact: float  # Score impact (0-1)


@dataclass
class QualityAssessment:
    """Complete quality assessment for a publication."""
    
    publication: Publication
    quality_level: QualityLevel
    quality_score: float  # 0-1 scale
    issues: List[QualityIssue]
    strengths: List[str]
    metadata_completeness: float  # 0-1 scale
    content_quality: float  # 0-1 scale
    journal_quality: float  # 0-1 scale
    temporal_relevance: float  # 0-1 scale
    recommended_action: str  # "include", "include_with_warning", "exclude"
    
    @property
    def breakdown(self) -> Dict[str, float]:
        """Get score breakdown as dictionary."""
        return {
            "overall": round(self.quality_score, 3),
            "metadata": round(self.metadata_completeness, 3),
            "content": round(self.content_quality, 3),
            "journal": round(self.journal_quality, 3),
            "temporal": round(self.temporal_relevance, 3),
        }
    
    @property
    def critical_issues(self) -> List[QualityIssue]:
        """Get only critical issues."""
        return [i for i in self.issues if i.severity == "critical"]
    
    @property
    def warnings(self) -> List[QualityIssue]:
        """Get only warnings."""
        return [i for i in self.issues if i.severity == "warning"]


# Predatory journal indicators (common patterns)
PREDATORY_PATTERNS = [
    r"international journal of recent",
    r"international journal of innovative",
    r"world journal of",
    r"global journal of",
    r"universal journal of",
    r"american journal of.*research",  # Common pattern
    r"journal of.*international.*research",
    r"international.*journal of advanced",
]

# Low-quality venue patterns
LOW_QUALITY_PATTERNS = [
    r"proceedings of.*conference",  # Conference proceedings (lower tier)
    r"^arxiv$",  # Preprints (not peer-reviewed)
    r"^biorxiv$",
    r"^medrxiv$",
    r"^ssrn$",
]

# High-quality journal patterns (top-tier)
HIGH_QUALITY_JOURNALS = {
    "nature", "science", "cell", "lancet", "jama", "nejm",
    "nature genetics", "nature biotechnology", "nature medicine",
    "cell reports", "cell metabolism", "genome research",
    "genome biology", "nucleic acids research", "pnas",
    "proceedings of the national academy of sciences",
    "elife", "plos biology", "molecular cell", "genes & development",
}


class QualityValidator:
    """
    Validates publication quality for citation discovery.
    
    Performs multi-criteria quality assessment:
    - Metadata completeness (40%) - Does it have essential info?
    - Content quality (30%) - Is the content substantial?
    - Journal quality (20%) - Is it from a reputable venue?
    - Temporal relevance (10%) - Is it recent enough?
    
    Example:
        >>> validator = QualityValidator()
        >>> assessments = validator.validate_publications(papers)
        >>> high_quality = [a for a in assessments if a.quality_level in ["excellent", "good"]]
    """
    
    def __init__(self, config: Optional[QualityConfig] = None):
        """Initialize validator with configuration.
        
        Args:
            config: Quality configuration (uses defaults if not provided)
        """
        self.config = config or QualityConfig()
        logger.info(
            f"Initialized quality validator with config: "
            f"min_score={self.config.min_quality_score:.2f}, "
            f"require_abstract={self.config.require_abstract}, "
            f"check_predatory={self.config.check_predatory}"
        )
    
    def validate_publications(
        self, publications: List[Publication]
    ) -> List[QualityAssessment]:
        """Validate all publications.
        
        Args:
            publications: List of publications to validate
            
        Returns:
            List of QualityAssessment objects
        """
        if not publications:
            return []
        
        logger.info(f"Validating quality of {len(publications)} publications...")
        
        assessments = []
        for pub in publications:
            assessment = self._assess_publication(pub)
            assessments.append(assessment)
        
        # Log summary statistics
        self._log_validation_summary(assessments)
        
        return assessments
    
    def _assess_publication(self, pub: Publication) -> QualityAssessment:
        """Assess quality of a single publication.
        
        Scoring breakdown:
        - Metadata completeness: 40%
        - Content quality: 30%
        - Journal quality: 20%
        - Temporal relevance: 10%
        """
        issues = []
        strengths = []
        
        # 1. Metadata completeness (40%)
        metadata_score, metadata_issues, metadata_strengths = self._check_metadata_completeness(pub)
        issues.extend(metadata_issues)
        strengths.extend(metadata_strengths)
        
        # 2. Content quality (30%)
        content_score, content_issues, content_strengths = self._check_content_quality(pub)
        issues.extend(content_issues)
        strengths.extend(content_strengths)
        
        # 3. Journal quality (20%)
        journal_score, journal_issues, journal_strengths = self._check_journal_quality(pub)
        issues.extend(journal_issues)
        strengths.extend(journal_strengths)
        
        # 4. Temporal relevance (10%)
        temporal_score, temporal_issues, temporal_strengths = self._check_temporal_relevance(pub)
        issues.extend(temporal_issues)
        strengths.extend(temporal_strengths)
        
        # Calculate weighted overall score
        overall_score = (
            metadata_score * 0.40 +
            content_score * 0.30 +
            journal_score * 0.20 +
            temporal_score * 0.10
        )
        
        # Determine quality level and action
        quality_level = self._determine_quality_level(overall_score, issues)
        action = self._determine_action(quality_level, issues)
        
        return QualityAssessment(
            publication=pub,
            quality_level=quality_level,
            quality_score=overall_score,
            issues=issues,
            strengths=strengths,
            metadata_completeness=metadata_score,
            content_quality=content_score,
            journal_quality=journal_score,
            temporal_relevance=temporal_score,
            recommended_action=action,
        )
    
    def _check_metadata_completeness(
        self, pub: Publication
    ) -> Tuple[float, List[QualityIssue], List[str]]:
        """Check metadata completeness (40% weight).
        
        Essential fields:
        - Title (critical)
        - Abstract (critical)
        - Authors (important)
        - Publication date (important)
        - Journal (optional for preprints)
        """
        score = 0.0
        issues = []
        strengths = []
        
        # Title (20 points)
        if pub.title:
            score += 0.20
            if len(pub.title) > 50:
                strengths.append("Descriptive title")
        else:
            issues.append(QualityIssue(
                severity="critical",
                category="metadata",
                message="Missing title",
                impact=0.20
            ))
        
        # Abstract (35 points)
        if pub.abstract:
            if len(pub.abstract) >= self.config.min_abstract_length:
                score += 0.35
                if len(pub.abstract) > 500:
                    strengths.append(f"Comprehensive abstract ({len(pub.abstract)} chars)")
            else:
                score += 0.15
                issues.append(QualityIssue(
                    severity="warning",
                    category="metadata",
                    message=f"Short abstract ({len(pub.abstract)} chars)",
                    impact=0.20
                ))
        elif self.config.require_abstract:
            issues.append(QualityIssue(
                severity="critical",
                category="metadata",
                message="Missing abstract",
                impact=0.35
            ))
        
        # Authors (20 points)
        if pub.authors and len(pub.authors) > 0:
            score += 0.20
            if len(pub.authors) >= 3:
                strengths.append(f"Multiple authors ({len(pub.authors)})")
        elif self.config.require_authors:
            issues.append(QualityIssue(
                severity="warning",
                category="metadata",
                message="Missing authors",
                impact=0.20
            ))
        
        # Publication date (15 points)
        if pub.publication_date:
            score += 0.15
        elif self.config.require_date:
            issues.append(QualityIssue(
                severity="warning",
                category="metadata",
                message="Missing publication date",
                impact=0.15
            ))
        
        # Journal (10 points)
        if pub.journal:
            score += 0.10
        
        return score, issues, strengths
    
    def _check_content_quality(
        self, pub: Publication
    ) -> Tuple[float, List[QualityIssue], List[str]]:
        """Check content quality (30% weight).
        
        Factors:
        - Abstract length and substance
        - Citation count (age-adjusted)
        - Keywords/MeSH terms availability
        """
        score = 0.0
        issues = []
        strengths = []
        
        # Abstract substance (40 points)
        if pub.abstract:
            abstract_len = len(pub.abstract)
            if abstract_len >= 500:
                score += 0.40
                strengths.append("Detailed abstract")
            elif abstract_len >= 200:
                score += 0.30
            elif abstract_len >= self.config.min_abstract_length:
                score += 0.20
            else:
                score += 0.10
                issues.append(QualityIssue(
                    severity="warning",
                    category="content",
                    message=f"Thin abstract ({abstract_len} chars)",
                    impact=0.30
                ))
        
        # Citation count (age-adjusted, 40 points)
        citation_score, citation_issue = self._assess_citations(pub)
        score += citation_score * 0.40
        if citation_issue:
            issues.append(citation_issue)
        elif pub.citations and pub.citations > 50:
            strengths.append(f"Well-cited ({pub.citations} citations)")
        
        # Keywords/MeSH terms (20 points)
        has_terms = len(pub.keywords) > 0 or len(pub.mesh_terms) > 0
        if has_terms:
            score += 0.20
            term_count = len(pub.keywords) + len(pub.mesh_terms)
            strengths.append(f"Indexed ({term_count} terms)")
        
        return score, issues, strengths
    
    def _assess_citations(self, pub: Publication) -> Tuple[float, Optional[QualityIssue]]:
        """Assess citation count adjusted for publication age."""
        if not pub.publication_date or not pub.citations:
            return 0.5, None  # Neutral if unknown
        
        age_years = (datetime.now() - pub.publication_date).days / 365.25
        
        # Age-adjusted expectations
        if age_years < 2:
            # Recent papers: 5+ citations is good
            if pub.citations >= 10:
                return 1.0, None
            elif pub.citations >= self.config.min_citations_recent:
                return 0.7, None
            else:
                return 0.3, QualityIssue(
                    severity="info",
                    category="content",
                    message=f"Low citations for recent paper ({pub.citations})",
                    impact=0.20
                )
        elif age_years < 5:
            # 2-5 years: 10+ citations expected
            if pub.citations >= 50:
                return 1.0, None
            elif pub.citations >= self.config.min_citations_older:
                return 0.7, None
            else:
                return 0.4, QualityIssue(
                    severity="warning",
                    category="content",
                    message=f"Low citations ({pub.citations} in {age_years:.1f} years)",
                    impact=0.20
                )
        else:
            # Older papers: should be well-cited
            if pub.citations >= 100:
                return 1.0, None
            elif pub.citations >= 20:
                return 0.6, None
            else:
                return 0.3, QualityIssue(
                    severity="warning",
                    category="content",
                    message=f"Low citations for older paper ({pub.citations})",
                    impact=0.20
                )
    
    def _check_journal_quality(
        self, pub: Publication
    ) -> Tuple[float, List[QualityIssue], List[str]]:
        """Check journal/venue quality (20% weight).
        
        Checks:
        - Predatory journal patterns
        - High-quality journal recognition
        - Preprint status
        """
        score = 0.5  # Default neutral
        issues = []
        strengths = []
        
        if not pub.journal:
            # No journal info
            if pub.doi and "10.1101" in pub.doi:  # bioRxiv/medRxiv DOI pattern
                if self.config.allow_preprints:
                    score = 0.6
                    issues.append(QualityIssue(
                        severity="info",
                        category="journal",
                        message="Preprint (not peer-reviewed)",
                        impact=0.10
                    ))
                else:
                    score = 0.3
                    issues.append(QualityIssue(
                        severity="warning",
                        category="journal",
                        message="Preprint not allowed",
                        impact=0.40
                    ))
            else:
                # No journal, no preprint indicator
                issues.append(QualityIssue(
                    severity="info",
                    category="journal",
                    message="No journal information",
                    impact=0.10
                ))
            return score, issues, strengths
        
        journal_lower = pub.journal.lower()
        
        # Check for high-quality journals
        if any(hq in journal_lower for hq in HIGH_QUALITY_JOURNALS):
            score = 1.0
            strengths.append(f"Top-tier journal: {pub.journal}")
            return score, issues, strengths
        
        # Check for predatory patterns
        if self.config.check_predatory:
            for pattern in PREDATORY_PATTERNS:
                if re.search(pattern, journal_lower):
                    score = 0.2
                    issues.append(QualityIssue(
                        severity="critical",
                        category="journal",
                        message=f"Potential predatory journal: {pub.journal}",
                        impact=0.60
                    ))
                    return score, issues, strengths
        
        # Check for low-quality patterns
        for pattern in LOW_QUALITY_PATTERNS:
            if re.search(pattern, journal_lower):
                score = 0.4
                issues.append(QualityIssue(
                    severity="warning",
                    category="journal",
                    message=f"Lower-tier venue: {pub.journal}",
                    impact=0.30
                ))
                return score, issues, strengths
        
        # Default: reputable journal (PubMed indexed, has journal name)
        if pub.pmid:
            score = 0.7
            strengths.append("PubMed indexed")
        
        return score, issues, strengths
    
    def _check_temporal_relevance(
        self, pub: Publication
    ) -> Tuple[float, List[QualityIssue], List[str]]:
        """Check temporal relevance (10% weight).
        
        Recent papers are more relevant for current research.
        """
        score = 0.5
        issues = []
        strengths = []
        
        if not pub.publication_date:
            return score, issues, strengths
        
        age_years = (datetime.now() - pub.publication_date).days / 365.25
        
        if age_years < 0:
            # Future date (data error)
            issues.append(QualityIssue(
                severity="warning",
                category="age",
                message="Future publication date",
                impact=0.10
            ))
            return 0.5, issues, strengths
        
        # Score based on age
        if age_years <= 2:
            score = 1.0
            strengths.append(f"Recent publication ({int(age_years)} years)")
        elif age_years <= self.config.recent_paper_years:
            score = 0.8
        elif age_years <= 10:
            score = 0.5
        elif age_years <= self.config.max_age_years:
            score = 0.3
            issues.append(QualityIssue(
                severity="info",
                category="age",
                message=f"Older publication ({int(age_years)} years)",
                impact=0.10
            ))
        else:
            score = 0.1
            issues.append(QualityIssue(
                severity="warning",
                category="age",
                message=f"Very old publication ({int(age_years)} years)",
                impact=0.30
            ))
        
        return score, issues, strengths
    
    def _determine_quality_level(
        self, score: float, issues: List[QualityIssue]
    ) -> QualityLevel:
        """Determine quality level from score and issues."""
        # Check for critical issues (automatic downgrade)
        critical_count = sum(1 for i in issues if i.severity == "critical")
        
        if critical_count >= 2:
            return QualityLevel.REJECTED
        elif score >= self.config.excellent_threshold and critical_count == 0:
            return QualityLevel.EXCELLENT
        elif score >= self.config.good_threshold and critical_count == 0:
            return QualityLevel.GOOD
        elif score >= self.config.acceptable_threshold and critical_count <= 1:
            return QualityLevel.ACCEPTABLE
        elif score >= self.config.min_quality_score:
            return QualityLevel.POOR
        else:
            return QualityLevel.REJECTED
    
    def _determine_action(
        self, quality_level: QualityLevel, issues: List[QualityIssue]
    ) -> str:
        """Determine recommended action based on quality level."""
        if quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]:
            return "include"
        elif quality_level == QualityLevel.ACCEPTABLE:
            critical_count = sum(1 for i in issues if i.severity == "critical")
            if critical_count > 0:
                return "include_with_warning"
            return "include"
        else:
            return "exclude"
    
    def _log_validation_summary(self, assessments: List[QualityAssessment]):
        """Log summary statistics for validation results."""
        if not assessments:
            return
        
        # Count by quality level
        level_counts = {}
        for level in QualityLevel:
            level_counts[level] = sum(1 for a in assessments if a.quality_level == level)
        
        # Count by action
        include_count = sum(1 for a in assessments if a.recommended_action == "include")
        warning_count = sum(1 for a in assessments if a.recommended_action == "include_with_warning")
        exclude_count = sum(1 for a in assessments if a.recommended_action == "exclude")
        
        # Average scores
        avg_score = sum(a.quality_score for a in assessments) / len(assessments)
        
        logger.info("=" * 60)
        logger.info("📊 Quality Validation Summary")
        logger.info("=" * 60)
        logger.info(f"Total publications assessed: {len(assessments)}")
        logger.info(f"Average quality score: {avg_score:.3f}")
        logger.info("")
        logger.info("Quality levels:")
        for level in QualityLevel:
            count = level_counts[level]
            pct = (count / len(assessments)) * 100
            logger.info(f"  {level.value:12s}: {count:3d} ({pct:5.1f}%)")
        logger.info("")
        logger.info("Recommended actions:")
        logger.info(f"  Include:          {include_count:3d} ({(include_count/len(assessments))*100:5.1f}%)")
        logger.info(f"  Include w/warning: {warning_count:3d} ({(warning_count/len(assessments))*100:5.1f}%)")
        logger.info(f"  Exclude:          {exclude_count:3d} ({(exclude_count/len(assessments))*100:5.1f}%)")
        logger.info("=" * 60)


def filter_by_quality(
    publications: List[Publication],
    config: Optional[QualityConfig] = None,
    min_level: QualityLevel = QualityLevel.ACCEPTABLE,
) -> Tuple[List[Publication], List[QualityAssessment]]:
    """Convenience function to filter publications by quality.
    
    Args:
        publications: List of publications to filter
        config: Quality configuration
        min_level: Minimum quality level to include
        
    Returns:
        Tuple of (filtered_publications, all_assessments)
        
    Example:
        >>> filtered, assessments = filter_by_quality(papers, min_level=QualityLevel.GOOD)
        >>> print(f"Filtered {len(papers)} -> {len(filtered)} papers")
    """
    validator = QualityValidator(config)
    assessments = validator.validate_publications(publications)
    
    # Define quality level order
    level_order = {
        QualityLevel.EXCELLENT: 5,
        QualityLevel.GOOD: 4,
        QualityLevel.ACCEPTABLE: 3,
        QualityLevel.POOR: 2,
        QualityLevel.REJECTED: 1,
    }
    
    min_order = level_order[min_level]
    
    # Filter publications
    filtered = [
        a.publication
        for a in assessments
        if level_order[a.quality_level] >= min_order and a.recommended_action != "exclude"
    ]
    
    logger.info(f"Quality filtering: {len(publications)} -> {len(filtered)} papers (min_level={min_level.value})")
    
    return filtered, assessments
