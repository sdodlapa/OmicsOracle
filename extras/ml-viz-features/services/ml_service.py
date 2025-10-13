"""
ML Service Layer

Singleton service that orchestrates all ML components:
- Citation prediction
- Trend forecasting
- Biomarker embeddings
- Recommendation engine

Integrates with Redis caching for performance.
"""

import logging
from typing import Dict, List, Optional

from omics_oracle_v2.lib.cache.redis_client import AsyncRedisCache
from omics_oracle_v2.lib.ml.citation_predictor import CitationPredictor
from omics_oracle_v2.lib.ml.embeddings import BiomarkerEmbedder, SimilaritySearch
from omics_oracle_v2.lib.ml.recommender import BiomarkerRecommender, Recommendation
from omics_oracle_v2.lib.ml.trend_forecaster import TrendForecaster
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class MLService:
    """
    ML Service singleton for coordinating ML operations.

    Provides high-level interface to all ML capabilities:
    - Citation prediction with ML models
    - Research trend forecasting
    - Semantic search with embeddings
    - Multi-strategy biomarker recommendations
    """

    _instance: Optional["MLService"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize ML service (only once)."""
        if not self._initialized:
            self._initialize()
            MLService._initialized = True

    def _initialize(self):
        """Initialize all ML components."""
        logger.info("Initializing ML Service...")

        # Initialize cache
        self.cache = AsyncRedisCache()

        # Initialize ML models
        self.citation_predictor = CitationPredictor()
        self.trend_forecaster = TrendForecaster()
        self.embedder = BiomarkerEmbedder()
        self.similarity_search = SimilaritySearch(self.embedder)
        self.recommender = BiomarkerRecommender(
            embedder=self.embedder, similarity_search=self.similarity_search
        )

        # Cache configuration
        self.cache_ttl = {
            "embeddings": 7 * 24 * 3600,  # 7 days - embeddings are expensive
            "recommendations": 24 * 3600,  # 1 day - recommendations change
            "predictions": 12 * 3600,  # 12 hours - predictions evolve
            "trends": 6 * 3600,  # 6 hours - trends update frequently
        }

        logger.info("ML Service initialized successfully")

    async def predict_citations(
        self,
        publications: List[Publication],
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Predict future citations for publications.

        Args:
            publications: List of publications to predict for
            use_cache: Whether to use Redis cache

        Returns:
            List of prediction results with confidence intervals
        """
        results = []

        for pub in publications:
            # Generate cache key
            cache_key = f"citation_pred:{pub.pmid or pub.title[:50]}"

            # Try cache first
            if use_cache:
                cached = await self.cache.get(cache_key)
                if cached:
                    results.append(cached)
                    continue

            # Make prediction
            prediction = self.citation_predictor.predict_citations(pub)

            result = {
                "publication_id": pub.pmid,
                "title": pub.title,
                "current_citations": pub.citations or 0,
                "predicted_1_year": int(prediction.predicted_citations),
                "predicted_3_years": int(prediction.predicted_citations * 1.5),  # Scaled estimate
                "predicted_5_years": int(prediction.predicted_citations * 2),  # Scaled estimate
                "confidence_lower": int(prediction.confidence_interval[0]),
                "confidence_upper": int(prediction.confidence_interval[1]),
                "model_confidence": prediction.confidence_score,
            }

            # Cache result
            if use_cache:
                await self.cache.set(cache_key, result, ttl=self.cache_ttl["predictions"])

            results.append(result)

        return results

    async def get_recommendations(
        self,
        biomarker: str,
        publications: List[Publication],
        num_recommendations: int = 5,
        strategy: str = "similar",
        use_cache: bool = True,
    ) -> List[Recommendation]:
        """
        Get biomarker recommendations using specified strategy.

        Args:
            biomarker: Source biomarker name
            publications: Historical publications for context
            num_recommendations: Number of recommendations to return
            strategy: Recommendation strategy (similar/emerging/high_impact)
            use_cache: Whether to use Redis cache

        Returns:
            List of recommendations with scores and explanations
        """
        # Generate cache key
        cache_key = f"recommend:{strategy}:{biomarker}:{num_recommendations}"

        # Try cache first
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return [Recommendation(**r) for r in cached]

        # Get recommendations
        if strategy == "similar":
            # For similar recommendations, we need biomarker data dict
            biomarker_data = {pub.title.split()[0]: [pub] for pub in publications}
            recommendations = self.recommender.recommend_similar(
                biomarker, biomarker_data, k=num_recommendations
            )
        elif strategy == "emerging":
            # For emerging, use publication data dict
            biomarker_data = {pub.title.split()[0]: [pub] for pub in publications}
            recommendations = self.recommender.recommend_emerging(biomarker_data, k=num_recommendations)
        elif strategy == "high_impact":
            # For high-impact, use publication data dict
            biomarker_data = {pub.title.split()[0]: [pub] for pub in publications}
            recommendations = self.recommender.recommend_high_impact(biomarker_data, k=num_recommendations)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Cache result (serialize to dict)
        if use_cache:
            cached_data = [
                {
                    "biomarker": r.biomarker,
                    "score": r.score,
                    "rank": r.rank,
                    "strategy": r.strategy,
                    "explanation": r.explanation,
                    "supporting_evidence": r.supporting_evidence,
                }
                for r in recommendations
            ]
            await self.cache.set(cache_key, cached_data, ttl=self.cache_ttl["recommendations"])

        return recommendations

    async def forecast_trends(
        self,
        biomarker: str,
        publications: List[Publication],
        periods: int = 12,
        use_cache: bool = True,
    ) -> Dict:
        """
        Forecast publication trends for a biomarker.

        Args:
            biomarker: Biomarker name
            publications: Historical publications
            periods: Number of future periods to forecast
            use_cache: Whether to use Redis cache

        Returns:
            Trend forecast with predictions and confidence intervals
        """
        # Generate cache key
        cache_key = f"trend:{biomarker}:{periods}"

        # Try cache first
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Forecast trends
        forecast = self.trend_forecaster.forecast_publication_volume(publications, months_ahead=periods)

        result = {
            "biomarker": biomarker,
            "periods": periods,
            "forecast": forecast.predictions,
            "lower_bound": [ci[0] for ci in forecast.confidence_intervals],
            "upper_bound": [ci[1] for ci in forecast.confidence_intervals],
            "model": forecast.model_type,
        }

        # Cache result
        if use_cache:
            await self.cache.set(cache_key, result, ttl=self.cache_ttl["trends"])

        return result

    async def enrich_search_results(
        self,
        publications: List[Publication],
        include_predictions: bool = True,
        include_similar: bool = True,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Enrich search results with ML predictions and similarities.

        Args:
            publications: Publications to enrich
            include_predictions: Include citation predictions
            include_similar: Include similar biomarkers
            use_cache: Whether to use Redis cache

        Returns:
            Enriched publication data
        """
        enriched = []

        for pub in publications:
            # Generate cache key
            cache_key = f"enrich:{pub.pmid or pub.title[:50]}"

            # Try cache first
            if use_cache:
                cached = await self.cache.get(cache_key)
                if cached:
                    enriched.append(cached)
                    continue

            # Base publication data
            result = {
                "id": pub.pmid,
                "title": pub.title,
                "authors": pub.authors if isinstance(pub.authors, list) else [pub.authors],
                "publication_date": (pub.publication_date.isoformat() if pub.publication_date else None),
                "citations": pub.citations or 0,
                "journal": pub.journal,
            }

            # Add citation predictions
            if include_predictions:
                prediction = self.citation_predictor.predict_citations(pub)
                result["predicted_citations"] = {
                    "1_year": int(prediction.predicted_citations),
                    "3_years": int(prediction.predicted_citations * 1.5),
                    "5_years": int(prediction.predicted_citations * 2),
                }

            # Add similar biomarkers
            if include_similar and pub.title:
                # Extract biomarker from title (simple heuristic)
                biomarker = pub.title.split()[0]  # First word as proxy
                similar = self.similarity_search.find_similar(biomarker, k=3)
                result["similar_biomarkers"] = [
                    {"biomarker": s[0], "similarity": float(s[1])} for s in similar
                ]

            # Cache result
            if use_cache:
                await self.cache.set(cache_key, result, ttl=self.cache_ttl["embeddings"])

            enriched.append(result)

        return enriched

    async def get_biomarker_analytics(
        self,
        biomarker: str,
        publications: List[Publication],
        use_cache: bool = True,
    ) -> Dict:
        """
        Get comprehensive analytics for a biomarker.

        Args:
            biomarker: Biomarker name
            publications: Related publications
            use_cache: Whether to use Redis cache

        Returns:
            Comprehensive analytics including trends, predictions, similar biomarkers
        """
        # Generate cache key
        cache_key = f"analytics:{biomarker}"

        # Try cache first
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Get emerging topics
        emerging = self.trend_forecaster.detect_emerging_topics(publications)

        # Get similar biomarkers
        similar = self.similarity_search.find_similar(biomarker, k=5)

        # Analyze trajectory
        trajectory = self.trend_forecaster.analyze_biomarker_trajectory(biomarker, publications)

        result = {
            "biomarker": biomarker,
            "total_publications": len(publications),
            "emerging_topics": [
                {
                    "topic": topic["topic"],
                    "growth_rate": float(topic["growth_rate"]),
                    "recent_count": int(topic["recent_count"]),
                    "total_count": int(topic["total_count"]),
                }
                for topic in emerging[:5]
            ],
            "similar_biomarkers": [{"biomarker": s[0], "similarity": float(s[1])} for s in similar],
            "trajectory": {
                "status": trajectory["status"],
                "growth_rate": float(trajectory["growth_rate"]),
                "trend": trajectory["trend"],
                "forecasted_peak_month": (
                    trajectory["forecasted_peak_month"].isoformat()
                    if trajectory["forecasted_peak_month"]
                    else None
                ),
            },
        }

        # Cache result
        if use_cache:
            await self.cache.set(cache_key, result, ttl=self.cache_ttl["trends"])

        return result

    async def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return await self.cache.get_stats()

    async def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (e.g., "citation_pred:*")
        """
        if pattern:
            # Delete matching keys
            # Note: This would require SCAN command in production
            logger.warning(f"Pattern-based cache clearing not implemented: {pattern}")
        else:
            # Clear all cache
            logger.info("Clearing all ML service cache")
