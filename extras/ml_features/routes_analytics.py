"""
Analytics API

Endpoints for comprehensive biomarker analytics.
"""

import logging
import time

from fastapi import APIRouter, HTTPException, Query

from omics_oracle_v2.api.models.ml_schemas import BiomarkerAnalyticsResponse, MLHealthResponse
from omics_oracle_v2.lib.services import MLService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/biomarker/{biomarker}", response_model=BiomarkerAnalyticsResponse)
async def get_biomarker_analytics(
    biomarker: str,
    use_cache: bool = Query(True, description="Use cache"),
) -> BiomarkerAnalyticsResponse:
    """
    Get comprehensive analytics for a biomarker.

    Provides a complete analytical overview including:
    - Publication statistics
    - Emerging research topics
    - Similar biomarkers
    - Research trajectory analysis

    Args:
        biomarker: Biomarker name
        use_cache: Whether to use cache

    Returns:
        Comprehensive biomarker analytics

    Example:
        GET /api/analytics/biomarker/BRCA1?use_cache=true
    """
    start_time = time.time()

    try:
        # Get ML service
        ml_service = MLService()

        # Fetch publications for biomarker
        # TODO: Replace with actual database query
        publications = []  # Placeholder

        if not publications:
            raise HTTPException(status_code=404, detail=f"No publications found for biomarker: {biomarker}")

        # Get analytics
        analytics = await ml_service.get_biomarker_analytics(
            biomarker=biomarker,
            publications=publications,
            use_cache=use_cache,
        )

        # Convert to response format
        result = BiomarkerAnalyticsResponse(**analytics)

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Analytics for {biomarker}: {execution_time:.2f}ms")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting biomarker analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=MLHealthResponse)
async def get_ml_health() -> MLHealthResponse:
    """
    Get ML service health status.

    Checks the status of all ML models and cache availability.
    Useful for monitoring and debugging.

    Returns:
        ML service health status

    Example:
        GET /api/analytics/health
    """
    start_time = time.time()

    try:
        # Get ML service
        ml_service = MLService()

        # Check model status
        models_loaded = {
            "citation_predictor": ml_service.citation_predictor is not None,
            "trend_forecaster": ml_service.trend_forecaster is not None,
            "embedder": ml_service.embedder is not None,
            "recommender": ml_service.recommender is not None,
        }

        # Check cache
        cache_available = ml_service.cache is not None
        cache_stats = None
        if cache_available:
            try:
                cache_stats = await ml_service.get_cache_stats()
            except Exception as e:
                logger.warning(f"Failed to get cache stats: {e}")
                cache_available = False

        # Determine overall status
        all_models_loaded = all(models_loaded.values())
        if all_models_loaded and cache_available:
            status = "healthy"
        elif all_models_loaded:
            status = "degraded"
        else:
            status = "unavailable"

        result = MLHealthResponse(
            status=status,
            models_loaded=models_loaded,
            cache_available=cache_available,
            cache_stats=cache_stats,
        )

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"ML health check: {status} in {execution_time:.2f}ms")

        return result

    except Exception as e:
        logger.error(f"Error checking ML health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query(None, description="Optional key pattern to clear"),
) -> dict:
    """
    Clear ML service cache.

    Clears cache entries for ML predictions and recommendations.
    Use with caution in production.

    Args:
        pattern: Optional pattern to match keys (e.g., "citation_pred:*")

    Returns:
        Success message

    Example:
        POST /api/analytics/cache/clear?pattern=citation_pred:*
    """
    try:
        # Get ML service
        ml_service = MLService()

        # Clear cache
        await ml_service.clear_cache(pattern=pattern)

        message = "Cache cleared"
        if pattern:
            message += " (pattern: {})".format(pattern)

        logger.info(message)

        return {
            "success": True,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats() -> dict:
    """
    Get ML cache statistics.

    Returns cache hit rates, memory usage, and other metrics.

    Returns:
        Cache statistics

    Example:
        GET /api/analytics/cache/stats
    """
    try:
        # Get ML service
        ml_service = MLService()

        # Get cache stats
        stats = await ml_service.get_cache_stats()

        return {
            "success": True,
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
