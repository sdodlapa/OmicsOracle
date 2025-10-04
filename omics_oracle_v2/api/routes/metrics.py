"""
Metrics endpoints for Prometheus monitoring.

Provides endpoints for exposing Prometheus metrics.
"""

import logging

from fastapi import APIRouter, Response

from omics_oracle_v2.api.metrics import get_metrics, get_metrics_content_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", include_in_schema=False)
async def metrics():
    """
    Expose Prometheus metrics.

    Returns metrics in Prometheus text format for scraping.
    This endpoint is excluded from OpenAPI docs.
    """
    return Response(content=get_metrics(), media_type=get_metrics_content_type())
