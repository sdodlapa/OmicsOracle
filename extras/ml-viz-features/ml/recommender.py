"""
Biomarker Recommendation Engine

This module provides intelligent biomarker recommendations using:
- Embedding-based similarity
- Trend forecasting
- Citation prediction
- Hybrid scoring

Features:
- Similar biomarker recommendations
- Emerging biomarker detection
- High-impact biomarker suggestions
- Personalized recommendations
- Recommendation explanations
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from omics_oracle_v2.lib.ml.citation_predictor import CitationPredictor
from omics_oracle_v2.lib.ml.embeddings import BiomarkerEmbedder, SimilaritySearch
from omics_oracle_v2.lib.ml.trend_forecaster import TrendForecaster
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Single biomarker recommendation."""

    biomarker: str
    score: float  # Overall score (0-1)
    similarity_score: float  # Embedding similarity (0-1)
    trend_score: float  # Growth momentum (0-1)
    impact_score: float  # Citation prediction (0-1)
    novelty_score: float  # Research novelty (0-1)
    explanation: str
    related_publications: int
    confidence: float


@dataclass
class RecommendationResult:
    """Result of recommendation query."""

    query: str
    strategy: str
    recommendations: List[Recommendation]
    search_time_ms: float
    metadata: Dict[str, Any]


class RecommendationScorer:
    """
    Scores biomarkers for recommendation using multiple signals.
    """

    def __init__(
        self,
        citation_predictor: Optional[CitationPredictor] = None,
        trend_forecaster: Optional[TrendForecaster] = None,
    ):
        """
        Initialize scorer.

        Args:
            citation_predictor: Citation prediction model
            trend_forecaster: Trend forecasting model
        """
        self.citation_predictor = citation_predictor
        self.trend_forecaster = trend_forecaster

    def score_similarity(self, similarity: float) -> float:
        """
        Score based on embedding similarity.

        Args:
            similarity: Cosine similarity (0-1)

        Returns:
            Similarity score (0-1)
        """
        # Similarity is already 0-1, just return it
        return max(0.0, min(1.0, similarity))

    def score_trend(self, publications: List[Publication], min_pubs: int = 5) -> float:
        """
        Score based on publication growth trend.

        Args:
            publications: Publications mentioning biomarker
            min_pubs: Minimum publications required for scoring

        Returns:
            Trend score (0-1)
        """
        if len(publications) < min_pubs:
            return 0.0

        # Sort by date
        sorted_pubs = sorted(
            [p for p in publications if p.publication_date],
            key=lambda p: p.publication_date,
        )

        if len(sorted_pubs) < 2:
            return 0.0

        # Calculate year-over-year growth
        current_year = datetime.now().year
        year_counts = {}

        for pub in sorted_pubs:
            year = pub.publication_date.year
            year_counts[year] = year_counts.get(year, 0) + 1

        # Look at last 3 years
        recent_years = [current_year - i for i in range(3)]
        recent_counts = [year_counts.get(year, 0) for year in recent_years]

        if sum(recent_counts) == 0:
            return 0.0

        # Calculate growth rate
        if recent_counts[2] > 0:  # Avoid division by zero
            growth_rate = (recent_counts[0] - recent_counts[2]) / recent_counts[2]
        else:
            growth_rate = 0.0

        # Normalize to 0-1 (growth rate > 1.0 = score of 1.0)
        score = min(1.0, max(0.0, (growth_rate + 1.0) / 2.0))
        return score

    def score_impact(self, publications: List[Publication], min_pubs: int = 3) -> float:
        """
        Score based on citation impact.

        Args:
            publications: Publications mentioning biomarker
            min_pubs: Minimum publications for scoring

        Returns:
            Impact score (0-1)
        """
        if len(publications) < min_pubs:
            return 0.0

        # Calculate average citations
        total_citations = sum(p.citations or 0 for p in publications)
        avg_citations = total_citations / len(publications)

        # Normalize (100+ citations = score of 1.0)
        score = min(1.0, avg_citations / 100.0)
        return score

    def score_novelty(self, publications: List[Publication]) -> float:
        """
        Score based on research novelty.

        Args:
            publications: Publications mentioning biomarker

        Returns:
            Novelty score (0-1)
        """
        if not publications:
            return 0.0

        # Recent publications indicate active/novel research
        current_year = datetime.now().year
        recent_pubs = [
            p for p in publications if p.publication_date and p.publication_date.year >= current_year - 2
        ]

        novelty = len(recent_pubs) / max(1, len(publications))
        return min(1.0, novelty)

    def combine_scores(
        self,
        similarity: float,
        trend: float,
        impact: float,
        novelty: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Combine multiple scores into final recommendation score.

        Args:
            similarity: Similarity score
            trend: Trend score
            impact: Impact score
            novelty: Novelty score
            weights: Optional custom weights

        Returns:
            Combined score (0-1)
        """
        if weights is None:
            # Default weights
            weights = {
                "similarity": 0.4,
                "trend": 0.25,
                "impact": 0.25,
                "novelty": 0.1,
            }

        score = (
            weights.get("similarity", 0.4) * similarity
            + weights.get("trend", 0.25) * trend
            + weights.get("impact", 0.25) * impact
            + weights.get("novelty", 0.1) * novelty
        )

        return max(0.0, min(1.0, score))


class RecommendationExplainer:
    """
    Generates human-readable explanations for recommendations.
    """

    @staticmethod
    def explain(recommendation: Recommendation) -> str:
        """
        Generate explanation for a recommendation.

        Args:
            recommendation: Recommendation to explain

        Returns:
            Human-readable explanation
        """
        factors = []

        # Similarity
        if recommendation.similarity_score > 0.8:
            factors.append("highly similar research context")
        elif recommendation.similarity_score > 0.6:
            factors.append("similar research focus")

        # Trend
        if recommendation.trend_score > 0.7:
            factors.append("rapidly growing research area")
        elif recommendation.trend_score > 0.5:
            factors.append("increasing research interest")

        # Impact
        if recommendation.impact_score > 0.7:
            factors.append("high citation impact")
        elif recommendation.impact_score > 0.5:
            factors.append("notable citation impact")

        # Novelty
        if recommendation.novelty_score > 0.7:
            factors.append("active recent research")

        if not factors:
            return "Related biomarker with moderate relevance"

        return f"Recommended due to {', '.join(factors)}"

    @staticmethod
    def get_key_factors(recommendation: Recommendation) -> List[str]:
        """
        Get key recommendation factors.

        Args:
            recommendation: Recommendation to analyze

        Returns:
            List of key factors
        """
        factors = []

        scores = [
            ("similarity", recommendation.similarity_score),
            ("trend", recommendation.trend_score),
            ("impact", recommendation.impact_score),
            ("novelty", recommendation.novelty_score),
        ]

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Take top factors
        for factor, score in scores:
            if score > 0.3:  # Threshold for significance
                factors.append(factor)

        return factors


class BiomarkerRecommender:
    """
    Main recommendation engine for biomarkers.
    """

    def __init__(
        self,
        embedder: BiomarkerEmbedder,
        similarity_search: SimilaritySearch,
        scorer: Optional[RecommendationScorer] = None,
    ):
        """
        Initialize recommender.

        Args:
            embedder: Biomarker embedder
            similarity_search: Similarity search engine
            scorer: Recommendation scorer
        """
        self.embedder = embedder
        self.similarity_search = similarity_search
        self.scorer = scorer or RecommendationScorer()
        self.explainer = RecommendationExplainer()

    def recommend_similar(
        self,
        biomarker: str,
        biomarker_data: Dict[str, List[Publication]],
        k: int = 10,
    ) -> List[Recommendation]:
        """
        Recommend similar biomarkers based on embedding similarity.

        Args:
            biomarker: Query biomarker
            biomarker_data: Dictionary mapping biomarker names to publications
            k: Number of recommendations

        Returns:
            List of recommendations
        """
        # Get query embedding
        query_embedding = self.similarity_search.get_embedding_by_name(biomarker)
        if query_embedding is None:
            logger.warning(f"No embedding found for biomarker: {biomarker}")
            return []

        # Find similar biomarkers
        similar = self.similarity_search.find_similar(query_embedding, k=k)

        # Create recommendations
        recommendations = []
        for similar_biomarker, similarity in similar:
            pubs = biomarker_data.get(similar_biomarker, [])

            # Calculate scores
            similarity_score = self.scorer.score_similarity(similarity)
            trend_score = self.scorer.score_trend(pubs)
            impact_score = self.scorer.score_impact(pubs)
            novelty_score = self.scorer.score_novelty(pubs)

            # Combined score (emphasize similarity for this strategy)
            weights = {"similarity": 0.7, "trend": 0.1, "impact": 0.1, "novelty": 0.1}
            score = self.scorer.combine_scores(
                similarity_score, trend_score, impact_score, novelty_score, weights
            )

            rec = Recommendation(
                biomarker=similar_biomarker,
                score=score,
                similarity_score=similarity_score,
                trend_score=trend_score,
                impact_score=impact_score,
                novelty_score=novelty_score,
                explanation="",
                related_publications=len(pubs),
                confidence=similarity,
            )

            rec.explanation = self.explainer.explain(rec)
            recommendations.append(rec)

        # Sort by score
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations

    def recommend_emerging(
        self, biomarker_data: Dict[str, List[Publication]], k: int = 10
    ) -> List[Recommendation]:
        """
        Recommend emerging biomarkers with high growth.

        Args:
            biomarker_data: Dictionary mapping biomarker names to publications
            k: Number of recommendations

        Returns:
            List of emerging biomarker recommendations
        """
        recommendations = []

        for biomarker, pubs in biomarker_data.items():
            if len(pubs) < 5:  # Need minimum data
                continue

            # Calculate scores
            similarity_score = 0.0  # Not applicable for emerging
            trend_score = self.scorer.score_trend(pubs)
            impact_score = self.scorer.score_impact(pubs)
            novelty_score = self.scorer.score_novelty(pubs)

            # Skip if not trending
            if trend_score < 0.5:
                continue

            # Combined score (emphasize trend for this strategy)
            weights = {"similarity": 0.0, "trend": 0.6, "impact": 0.2, "novelty": 0.2}
            score = self.scorer.combine_scores(
                similarity_score, trend_score, impact_score, novelty_score, weights
            )

            rec = Recommendation(
                biomarker=biomarker,
                score=score,
                similarity_score=similarity_score,
                trend_score=trend_score,
                impact_score=impact_score,
                novelty_score=novelty_score,
                explanation="",
                related_publications=len(pubs),
                confidence=trend_score,
            )

            rec.explanation = self.explainer.explain(rec)
            recommendations.append(rec)

        # Sort by score
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations[:k]

    def recommend_high_impact(
        self, biomarker_data: Dict[str, List[Publication]], k: int = 10
    ) -> List[Recommendation]:
        """
        Recommend high-impact biomarkers based on citations.

        Args:
            biomarker_data: Dictionary mapping biomarker names to publications
            k: Number of recommendations

        Returns:
            List of high-impact recommendations
        """
        recommendations = []

        for biomarker, pubs in biomarker_data.items():
            if len(pubs) < 3:  # Need minimum data
                continue

            # Calculate scores
            similarity_score = 0.0  # Not applicable
            trend_score = self.scorer.score_trend(pubs)
            impact_score = self.scorer.score_impact(pubs)
            novelty_score = self.scorer.score_novelty(pubs)

            # Skip if low impact
            if impact_score < 0.3:
                continue

            # Combined score (emphasize impact)
            weights = {"similarity": 0.0, "trend": 0.2, "impact": 0.6, "novelty": 0.2}
            score = self.scorer.combine_scores(
                similarity_score, trend_score, impact_score, novelty_score, weights
            )

            rec = Recommendation(
                biomarker=biomarker,
                score=score,
                similarity_score=similarity_score,
                trend_score=trend_score,
                impact_score=impact_score,
                novelty_score=novelty_score,
                explanation="",
                related_publications=len(pubs),
                confidence=impact_score,
            )

            rec.explanation = self.explainer.explain(rec)
            recommendations.append(rec)

        # Sort by score
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations[:k]

    def get_hybrid_recommendations(
        self,
        biomarker: Optional[str],
        biomarker_data: Dict[str, List[Publication]],
        k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Recommendation]:
        """
        Get hybrid recommendations combining all strategies.

        Args:
            biomarker: Optional query biomarker for similarity
            biomarker_data: Dictionary mapping biomarker names to publications
            k: Number of recommendations
            weights: Optional custom scoring weights

        Returns:
            List of hybrid recommendations
        """
        if biomarker:
            # Use similarity-based approach
            return self.recommend_similar(biomarker, biomarker_data, k)

        # General recommendations
        recommendations = []

        for bm, pubs in biomarker_data.items():
            if len(pubs) < 3:
                continue

            # Calculate all scores
            similarity_score = 0.0  # Not applicable without query
            trend_score = self.scorer.score_trend(pubs)
            impact_score = self.scorer.score_impact(pubs)
            novelty_score = self.scorer.score_novelty(pubs)

            # Combined score
            score = self.scorer.combine_scores(
                similarity_score, trend_score, impact_score, novelty_score, weights
            )

            rec = Recommendation(
                biomarker=bm,
                score=score,
                similarity_score=similarity_score,
                trend_score=trend_score,
                impact_score=impact_score,
                novelty_score=novelty_score,
                explanation="",
                related_publications=len(pubs),
                confidence=score,
            )

            rec.explanation = self.explainer.explain(rec)
            recommendations.append(rec)

        # Sort by score
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations[:k]
