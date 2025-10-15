"""
Machine Learning client for predictions and recommendations.

All ML features that exist in backend but not exposed in dashboard!
"""

import logging
from typing import Any, Dict, List, Optional

from .base_client import APIClient
from .models import Publication, RecommendationRequest, RecommendationResponse

logger = logging.getLogger(__name__)


class MLClient(APIClient):
    """
    Client for ML-powered features.

    Features:
    - Paper recommendations
    - Citation prediction
    - Quality scoring
    - Relevance ranking

    Usage:
        async with MLClient() as client:
            # Get recommendations
            recs = await client.get_recommendations(
                seed_papers=["PMID:12345", "PMID:67890"],
                count=10
            )

            # Predict citations
            prediction = await client.predict_citations("PMID:12345")

            # Score quality
            quality = await client.score_quality(publication)
    """

    async def get_recommendations(
        self,
        seed_papers: List[str],
        count: int = 10,
    ) -> RecommendationResponse:
        """
        Get ML-based paper recommendations.

        MISSING from dashboard! Backend ready at /api/v1/recommendations/similar

        Args:
            seed_papers: Publication IDs to base recommendations on
            count: Number of recommendations

        Returns:
            RecommendationResponse with recommendations and scores

        Example:
            recs = await client.get_recommendations(
                seed_papers=["PMID:12345", "PMID:67890"],
                count=20
            )

            for rec in recs.recommendations:
                print(f"{rec.publication.title}")
                print(f"  Score: {rec.score:.2f}")
                print(f"  Reason: {rec.reason}")
        """
        # Build request
        request = RecommendationRequest(
            seed_papers=seed_papers,
            count=count,
        )

        logger.info(
            f"Getting {count} recommendations based on {len(seed_papers)} papers..."
        )

        # Call API
        response_data = await self.post(
            "/recommendations/similar",
            json=request.dict(),
        )

        # Parse response
        response = RecommendationResponse(**response_data)

        logger.info(
            f"Got {len(response.recommendations)} recommendations "
            f"(model: {response.model_used})"
        )

        return response

    async def predict_citations(
        self,
        pub_id: str,
        years_ahead: int = 5,
    ) -> Dict[str, Any]:
        """
        Predict future citations for a publication.

        MISSING from dashboard! Backend ready at /api/v1/predictions/citations

        Args:
            pub_id: Publication ID
            years_ahead: Number of years to predict

        Returns:
            Dictionary with predictions, confidence intervals

        Example:
            prediction = await client.predict_citations("PMID:12345", years_ahead=5)

            print(f"Current citations: {prediction['current_count']}")
            print(f"Predicted in 5 years: {prediction['predicted_count']}")
            print(f"Confidence: {prediction['confidence']:.2f}")
        """
        logger.info(f"Predicting citations for {pub_id} ({years_ahead} years)...")

        response = await self.post(
            "/predictions/citations",
            json={
                "publication_id": pub_id,
                "years_ahead": years_ahead,
            },
        )

        return response

    async def score_quality(
        self,
        publication: Publication,
    ) -> Dict[str, Any]:
        """
        Score publication quality using ML.

        Backend generates this but dashboard doesn't display it!

        Args:
            publication: Publication to score

        Returns:
            Quality scores with explanation
        """
        logger.info(f"Scoring quality for: {publication.title[:50]}...")

        response = await self.post(
            "/predictions/quality",
            json={"publication": publication.dict()},
        )

        return response

    async def rank_by_relevance(
        self,
        query: str,
        publications: List[Publication],
    ) -> List[Publication]:
        """
        Re-rank publications by relevance using ML.

        Args:
            query: Search query
            publications: Publications to rank

        Returns:
            Re-ranked publications
        """
        logger.info(f"Re-ranking {len(publications)} publications...")

        response = await self.post(
            "/predictions/rank",
            json={
                "query": query,
                "publications": [pub.dict() for pub in publications],
            },
        )

        return [Publication(**pub) for pub in response["ranked"]]

    async def get_trending_topics(
        self,
        field: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get trending research topics.

        Args:
            field: Optional field filter (e.g., "genomics")
            days: Number of days to analyze

        Returns:
            List of trending topics with scores
        """
        logger.info(f"Getting trending topics (last {days} days)...")

        params = {"days": days}
        if field:
            params["field"] = field

        response = await self.get(
            "/predictions/trending",
            params=params,
            use_cache=True,
        )

        return response.get("topics", [])

    async def get_emerging_authors(
        self,
        field: Optional[str] = None,
        min_papers: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Identify emerging researchers.

        Args:
            field: Optional field filter
            min_papers: Minimum papers required

        Returns:
            List of emerging authors with metrics
        """
        logger.info("Getting emerging authors...")

        params = {"min_papers": min_papers}
        if field:
            params["field"] = field

        response = await self.get(
            "/predictions/emerging-authors",
            params=params,
            use_cache=True,
        )

        return response.get("authors", [])
