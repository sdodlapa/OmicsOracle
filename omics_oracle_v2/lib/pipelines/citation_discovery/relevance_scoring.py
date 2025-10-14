"""
Relevance scoring for citation discovery.

Scores papers based on multiple factors to rank them by relevance to the GEO dataset:
1. Recency - Newer papers weighted higher
2. Citation count - Highly cited papers rank higher
3. Keyword matching - Papers with matching keywords rank higher
4. Title/abstract similarity - Content similarity to dataset
5. Source reliability - Different sources have different quality
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Configurable weights for relevance scoring components.
    
    All weights must sum to 1.0 for proper normalization.
    
    SIMPLIFIED APPROACH:
    - Content relevance (what): 70%
    - Temporal & quality (when/who): 30%
    
    Attributes:
        content_similarity: Weight for content similarity (0-1) - PRIMARY SIGNAL
        keyword_match: Weight for keyword matching (0-1) - SECONDARY RELEVANCE
        recency: Weight for publication recency (0-1) - TEMPORAL RELEVANCE
        citation_count: Weight for citation count (0-1) - IMPACT INDICATOR
    """
    content_similarity: float = 0.40  # PRIMARY: What the paper is about
    keyword_match: float = 0.30       # SECONDARY: Direct keyword matches
    recency: float = 0.20             # TEMPORAL: Recent papers preferred (5yr cutoff)
    citation_count: float = 0.10      # IMPACT: Higher for recent influential papers


@dataclass
class RelevanceScore:
    """Detailed relevance score breakdown.
    
    Attributes:
        publication: The publication being scored
        total: Final weighted score (0-1)
        content_similarity: Content similarity score (0-1)
        keyword_match: Keyword matching score (0-1)
        recency: Recency score (0-1)
        citation_count: Citation count score (0-1)
        breakdown: Dictionary of component scores for transparency
    """
    publication: "Publication"  # Forward reference
    total: float
    content_similarity: float
    keyword_match: float
    recency: float
    citation_count: float
    
    @property
    def breakdown(self) -> Dict[str, float]:
        """Get score breakdown as dictionary."""
        return {
            "total": round(self.total, 3),
            "content_similarity": round(self.content_similarity, 3),
            "keyword_match": round(self.keyword_match, 3),
            "recency": round(self.recency, 3),
            "citation_count": round(self.citation_count, 3)
        }


class RelevanceScorer:
    """
    Score publications by relevance to a GEO dataset.

    Uses multiple factors:
    - Recency: Newer papers score higher (exponential decay)
    - Citations: More cited papers score higher (log scale)
    - Keywords: Papers with matching terms score higher
    - Content: Title/abstract similarity to dataset
    - Source: Quality of the data source

    Example:
        >>> scorer = RelevanceScorer()
        >>> scores = scorer.score_publications(papers, geo_metadata)
        >>> sorted_papers = sorted(scores, key=lambda x: x.total, reverse=True)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        """Initialize relevance scorer with optional custom weights.
        
        Args:
            weights: Custom scoring weights (uses defaults if not provided)
        """
        self.weights = weights or ScoringWeights()

        logger.info(
            f"Initialized relevance scorer with simplified weights: "
            f"content={self.weights.content_similarity:.0%}, "
            f"keywords={self.weights.keyword_match:.0%}, "
            f"recency={self.weights.recency:.0%}, "
            f"citations={self.weights.citation_count:.0%}"
        )

    def score_publications(
        self, publications: List[Publication], geo_metadata: GEOSeriesMetadata
    ) -> List[RelevanceScore]:
        """
        Score all publications for relevance.

        Args:
            publications: List of publications to score
            geo_metadata: GEO dataset metadata for comparison

        Returns:
            List of RelevanceScore objects
        """
        if not publications:
            return []

        logger.info(f"Scoring {len(publications)} papers for relevance...")

        # Extract keywords from GEO metadata
        geo_keywords = self._extract_keywords(geo_metadata)
        logger.debug(f"GEO keywords: {geo_keywords}")

        scores = []
        for pub in publications:
            score = self._score_publication(pub, geo_metadata, geo_keywords)
            scores.append(score)

        # Log scoring distribution
        avg_score = sum(s.total for s in scores) / len(scores)
        max_score = max(s.total for s in scores)
        min_score = min(s.total for s in scores)

        logger.info(
            f"Scoring complete: avg={avg_score:.3f}, "
            f"max={max_score:.3f}, min={min_score:.3f}"
        )

        return scores

    def _score_publication(
        self,
        pub: Publication,
        geo_metadata: GEOSeriesMetadata,
        geo_keywords: List[str],
    ) -> RelevanceScore:
        """Score a single publication using simplified 4-factor model.
        
        Scoring factors:
        1. Content similarity (40%) - What the paper discusses
        2. Keyword matching (30%) - Direct keyword matches
        3. Recency (20%) - Publication date with 5-year cutoff
        4. Citation count (10%) - Impact indicator
        """

        # Calculate component scores
        content_score = self._score_content_similarity(pub, geo_metadata)
        keyword_score = self._score_keywords(pub, geo_keywords)
        recency_score = self._score_recency(pub)
        citation_score = self._score_citations(pub)

        # Calculate weighted total
        total_score = (
            content_score * self.weights.content_similarity +
            keyword_score * self.weights.keyword_match +
            recency_score * self.weights.recency +
            citation_score * self.weights.citation_count
        )

        return RelevanceScore(
            publication=pub,
            total=total_score,
            content_similarity=content_score,
            keyword_match=keyword_score,
            recency=recency_score,
            citation_count=citation_score
        )

    def _score_recency(self, pub: Publication) -> float:
        """Score based on publication recency with sharp 5-year cutoff.
        
        Scoring philosophy:
        - 0-5 years: High scores (1.0 to 0.4) - Recent and relevant
        - 5+ years: Sharp decline - Older methods/findings less relevant
        
        Scoring:
        - This year: 1.0
        - 1 year: 0.9
        - 2 years: 0.8
        - 3 years: 0.7
        - 4 years: 0.6
        - 5 years: 0.4 (cutoff starts)
        - 6 years: 0.2 (sharp drop)
        - 7+ years: Exponential decay toward 0
        """
        if not pub.publication_date:
            return 0.3  # Unknown date gets low score

        current_year = datetime.now().year
        pub_year = pub.publication_date.year
        years_old = current_year - pub_year

        if years_old < 0:
            return 1.0  # Future publication (data error, but score high)
        elif years_old == 0:
            return 1.0
        elif years_old == 1:
            return 0.9
        elif years_old == 2:
            return 0.8
        elif years_old == 3:
            return 0.7
        elif years_old == 4:
            return 0.6
        elif years_old == 5:
            return 0.4  # 5-year cutoff
        elif years_old == 6:
            return 0.2  # Sharp drop after cutoff
        else:
            # 7+ years: exponential decay
            return max(0.0, 0.2 * (0.7 ** (years_old - 6)))

    def _score_citations(self, pub: Publication) -> float:
        """Score based on citation count with log scale.
        
        Uses logarithmic scale to prevent highly-cited papers from dominating.
        With higher weight (10% vs 5%), this better rewards impactful papers,
        especially recent ones that are quickly gaining citations.
        
        Scoring:
        - 0 citations: 0.0
        - 10 citations: ~0.5
        - 50 citations: ~0.7
        - 100 citations: ~0.75
        - 500 citations: ~0.85
        - 1000+ citations: ~0.9
        """
        if not pub.citations or pub.citations <= 0:
            return 0.0

        import math

        # Log scale: log10(citations + 1) / 4
        score = math.log10(pub.citations + 1) / 4.0
        return min(1.0, max(0.0, score))

    def _score_keywords(self, pub: Publication, geo_keywords: List[str]) -> float:
        """
        Score based on keyword matching.

        Checks title, abstract, keywords, and MeSH terms for matches.
        """
        if not geo_keywords:
            return 0.5  # No keywords to match

        # Combine all searchable text from publication
        pub_text = " ".join(
            [
                pub.title or "",
                pub.abstract or "",
                " ".join(pub.keywords),
                " ".join(pub.mesh_terms),
            ]
        ).lower()

        # Count matching keywords
        matches = 0
        for keyword in geo_keywords:
            if keyword.lower() in pub_text:
                matches += 1

        # Score = proportion of keywords matched
        score = matches / len(geo_keywords) if geo_keywords else 0.0
        return min(1.0, max(0.0, score))

    def _score_content_similarity(
        self, pub: Publication, geo_metadata: GEOSeriesMetadata
    ) -> float:
        """
        Score based on content similarity.

        Uses fuzzy string matching between publication and GEO dataset.
        """
        # Combine GEO content
        geo_text = " ".join(
            [
                geo_metadata.title or "",
                geo_metadata.summary or "",
            ]
        ).lower()

        # Combine publication content
        pub_text = " ".join(
            [
                pub.title or "",
                pub.abstract or "",
            ]
        ).lower()

        if not geo_text or not pub_text:
            return 0.0

        # Use SequenceMatcher for fuzzy similarity
        similarity = SequenceMatcher(None, geo_text, pub_text).ratio()
        return min(1.0, max(0.0, similarity))

    def _extract_keywords(self, geo_metadata: GEOSeriesMetadata) -> List[str]:
        """
        Extract keywords from GEO metadata.

        Extracts meaningful terms from title and summary.
        """
        text = " ".join(
            [
                geo_metadata.title or "",
                geo_metadata.summary or "",
            ]
        )

        # Common stopwords to ignore
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "this",
            "that",
            "these",
            "those",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
        }

        # Extract words (alphanumeric only, 3+ characters)
        words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())

        # Filter stopwords and deduplicate
        keywords = list(set(w for w in words if w not in stopwords))

        return keywords[:20]  # Top 20 keywords


def rank_by_relevance(
    publications: List[Publication],
    geo_metadata: GEOSeriesMetadata,
    weights: Optional[ScoringWeights] = None,
) -> List[Tuple[Publication, RelevanceScore]]:
    """
    Convenience function to rank publications by relevance.

    Args:
        publications: List of publications
        geo_metadata: GEO dataset metadata
        weights: Optional custom weights

    Returns:
        List of (publication, score) tuples, sorted by score (highest first)

    Example:
        >>> ranked = rank_by_relevance(papers, geo_metadata)
        >>> for pub, score in ranked[:5]:
        ...     print(f"{score.total:.3f}: {pub.title}")
    """
    scorer = RelevanceScorer(weights)
    scores = scorer.score_publications(publications, geo_metadata)

    # Sort by total score (highest first)
    ranked = [(score.publication, score) for score in scores]
    ranked.sort(key=lambda x: x[1].total, reverse=True)

    return ranked
