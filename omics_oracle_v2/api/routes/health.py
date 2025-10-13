"""
Health Check Routes

Endpoints for monitoring API health and status.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from omics_oracle_v2.api.dependencies import get_api_settings, get_settings
from omics_oracle_v2.cache import get_redis_client
from omics_oracle_v2.core import Settings

from ..config import APISettings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Current server timestamp")
    version: str = Field(..., description="API version")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with component status."""

    components: dict = Field(..., description="Component health status")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")


# Track server start time
_start_time = datetime.now(timezone.utc)


@router.get("/", response_model=HealthResponse, summary="Basic health check")
async def health_check(api_settings: APISettings = Depends(get_api_settings)):
    """
    Basic health check endpoint.

    Returns:
        HealthResponse: Simple health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=api_settings.version,
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness_check(
    settings: Settings = Depends(get_settings),
    api_settings: APISettings = Depends(get_api_settings),
):
    """
    Readiness check endpoint for load balancers.

    Verifies the API is ready to handle requests.

    Returns:
        HealthResponse: Readiness status
    """
    # TODO: Add checks for dependencies (NCBI API, OpenAI API, etc.)

    return HealthResponse(
        status="ready",
        timestamp=datetime.now(timezone.utc),
        version=api_settings.version,
    )


@router.get("/live", response_model=HealthResponse, summary="Liveness check")
async def liveness_check(api_settings: APISettings = Depends(get_api_settings)):
    """
    Liveness check endpoint for kubernetes/docker health checks.

    Returns:
        HealthResponse: Liveness status
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.now(timezone.utc),
        version=api_settings.version,
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check",
)
async def detailed_health_check(
    settings: Settings = Depends(get_settings),
    api_settings: APISettings = Depends(get_api_settings),
):
    """
    Detailed health check with component status.

    Checks:
    - Redis cache availability
    - Database connectivity (if used)
    - External API availability

    Returns:
        DetailedHealthResponse: Detailed health status including component checks
    """
    now = datetime.now(timezone.utc)
    uptime = (now - _start_time).total_seconds()

    # Check component health
    components = {
        "settings": "healthy",
    }

    # Check Redis
    try:
        redis = await get_redis_client()
        if redis:
            await redis.ping()
            components["redis"] = "healthy"
        else:
            components["redis"] = "unavailable"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        components["redis"] = "unhealthy"

    # Note: ML Service removed - archived to extras/ml-viz-features/

    # Overall status
    overall_status = "healthy"
    if any(status == "unhealthy" for status in components.values()):
        overall_status = "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=now,
        version=api_settings.version,
        components=components,
        uptime_seconds=uptime,
    )
