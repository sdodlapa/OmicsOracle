"""
FastAPI Routes Setup - Consolidated Architecture

This module configures all API routes for the application with clear
separation between:
- API v1 (legacy/backward compatibility)
- API v2 (enhanced features, real-time updates)
- Health/monitoring endpoints
- UI/dashboard serving

Version Strategy:
- v1: Stable, maintenance mode (planned deprecation in 6 months)
- v2: Active development, recommended for new integrations
"""

import logging

from fastapi import FastAPI

from .api_v1 import router as api_v1_router
from .api_v2 import router as api_v2_router
from .health import router as health_router
from .ui import router as ui_router

logger = logging.getLogger(__name__)


def setup_routes(app: FastAPI) -> None:
    """
    Setup all application routes with consolidated architecture.

    Route Organization:
    - /health/* - Health check and monitoring endpoints
    - /api/v1/* - Legacy API (backward compatibility)
    - /api/v2/* - Enhanced API with real-time features
    - /* - UI and dashboard routes
    """

    # Health check routes (unversioned for load balancer compatibility)
    app.include_router(health_router, prefix="/health")

    # API v1 routes (legacy, backward compatibility)
    app.include_router(api_v1_router, prefix="/api")

    # API v2 routes (enhanced, recommended)
    app.include_router(api_v2_router, prefix="/api")

    # UI and dashboard routes (includes root "/")
    app.include_router(ui_router)

    # API version discovery endpoint
    @app.get("/api", tags=["api-info"])
    async def api_version_discovery():
        """
        Discover available API versions and their capabilities.

        Returns information about all available API versions,
        their status, features, and documentation links.
        """
        return {
            "api_name": "OmicsOracle API",
            "version": "2.0.0",
            "available_versions": {
                "v1": {
                    "version": "1.0.0",
                    "status": "stable",
                    "mode": "maintenance",
                    "endpoints": "/api/v1/",
                    "documentation": "/docs#/v1-api",
                    "features": ["basic_search", "analysis", "health_check"],
                },
                "v2": {
                    "version": "2.0.0",
                    "status": "active",
                    "mode": "recommended",
                    "endpoints": "/api/v2/",
                    "documentation": "/docs#/v2-api",
                    "features": [
                        "enhanced_search",
                        "real_time_updates",
                        "websocket_support",
                        "ai_ranking",
                        "intelligent_suggestions",
                        "query_analysis",
                    ],
                },
            },
            "recommended_version": "v2",
            "deprecation_notice": {
                "v1": "API v1 will be deprecated in 6 months (April 2026)",
                "migration_guide": "/docs/migration-v1-to-v2",
            },
        }

    logger.info("All routes configured successfully with consolidated architecture")
    logger.info("  - Health: /health/*")
    logger.info("  - API v1: /api/v1/* (legacy)")
    logger.info("  - API v2: /api/v2/* (recommended)")
    logger.info("  - UI: /* (dashboards)")
