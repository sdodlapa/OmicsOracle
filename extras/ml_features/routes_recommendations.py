"""
Recommendations API

Endpoints for biomarker recommendations using ML.
"""

import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, Query

from omics_oracle_v2.api.models.ml_schemas import RecommendationRequest, RecommendationResponse
from omics_oracle_v2.lib.services import MLService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/similar", response_model=List[RecommendationResponse])
async def recommend_similar_biomarkers(
    request: RecommendationRequest,
) -> List[RecommendationResponse]:
    """
    Recommend biomarkers similar to the given biomarker.

    Uses semantic embeddings to find biomarkers with similar research profiles.
    Ideal for finding related research areas or alternative biomarkers.

    Args:
        request: Recommendation request with biomarker and parameters

    Returns:
        List of similar biomarker recommendations with scores

    Example:
        POST /api/recommendations/similar
        {
            "biomarker": "BRCA1",
            "num_recommendations": 5,
            "use_cache": true
        }
    """
    start_time = time.time()

    try:
        # Get ML service
        ml_service = MLService()

        # For similar recommendations, we need some publication context
        # In production, this would fetch from database
        # For now, return empty list or raise error
        publications = []  # TODO: Fetch publications for biomarker

        # Get recommendations
        recommendations = await ml_service.get_recommendations(
            biomarker=request.biomarker,
            publications=publications,
            num_recommendations=request.num_recommendations,
            strategy="similar",
            use_cache=request.use_cache,
        )

        # Convert to response format
        results = [
            RecommendationResponse(
                biomarker=r.biomarker,
                score=r.score,
                rank=r.rank,
                strategy=r.strategy,
                explanation=r.explanation,
                supporting_evidence=r.supporting_evidence,
            )
            for r in recommendations
        ]

        execution_time = (time.time() - start_time) * 1000
        logger.info(
            f"Similar recommendations for {request.biomarker}: "
            f"{len(results)} results in {execution_time:.2f}ms"
        )

        return results

    except Exception as e:
        logger.error(f"Error getting similar recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emerging", response_model=List[RecommendationResponse])
async def recommend_emerging_biomarkers(
    num_recommendations: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    use_cache: bool = Query(True, description="Use cache"),
) -> List[RecommendationResponse]:
    """
    Recommend emerging biomarkers with high growth potential.

    Analyzes publication trends to identify biomarkers showing rapid growth
    in research activity. Ideal for discovering cutting-edge research areas.

    Args:
        num_recommendations: Number of recommendations to return
        use_cache: Whether to use cache

    Returns:
        List of emerging biomarker recommendations

    Example:
        GET /api/recommendations/emerging?num_recommendations=10
    """
    start_time = time.time()

    try:
        # Get ML service
        ml_service = MLService()

        # For emerging recommendations, we need recent publication data
        publications = []  # TODO: Fetch recent publications from database

        # Get recommendations
        recommendations = await ml_service.get_recommendations(
            biomarker="",  # Not needed for emerging
            publications=publications,
            num_recommendations=num_recommendations,
            strategy="emerging",
            use_cache=use_cache,
        )

        # Convert to response format
        results = [
            RecommendationResponse(
                biomarker=r.biomarker,
                score=r.score,
                rank=r.rank,
                strategy=r.strategy,
                explanation=r.explanation,
                supporting_evidence=r.supporting_evidence,
            )
            for r in recommendations
        ]

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Emerging recommendations: {len(results)} results in {execution_time:.2f}ms")

        return results

    except Exception as e:
        logger.error(f"Error getting emerging recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-impact", response_model=List[RecommendationResponse])
async def recommend_high_impact_biomarkers(
    num_recommendations: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    use_cache: bool = Query(True, description="Use cache"),
) -> List[RecommendationResponse]:
    """
    Recommend high-impact biomarkers based on citation metrics.

    Identifies biomarkers with high citation counts and strong research impact.
    Ideal for finding well-established, influential research areas.

    Args:
        num_recommendations: Number of recommendations to return
        use_cache: Whether to use cache

    Returns:
        List of high-impact biomarker recommendations

    Example:
        GET /api/recommendations/high-impact?num_recommendations=10
    """
    start_time = time.time()

    try:
        # Get ML service
        ml_service = MLService()

        # For high-impact recommendations, we need citation data
        publications = []  # TODO: Fetch publications with citation data

        # Get recommendations
        recommendations = await ml_service.get_recommendations(
            biomarker="",  # Not needed for high-impact
            publications=publications,
            num_recommendations=num_recommendations,
            strategy="high_impact",
            use_cache=use_cache,
        )

        # Convert to response format
        results = [
            RecommendationResponse(
                biomarker=r.biomarker,
                score=r.score,
                rank=r.rank,
                strategy=r.strategy,
                explanation=r.explanation,
                supporting_evidence=r.supporting_evidence,
            )
            for r in recommendations
        ]

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"High-impact recommendations: {len(results)} results in {execution_time:.2f}ms")

        return results

    except Exception as e:
        logger.error(f"Error getting high-impact recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
