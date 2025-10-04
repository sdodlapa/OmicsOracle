"""
API Routes Package

Contains all API route modules.
"""

from omics_oracle_v2.api.routes.health import router as health_router

__all__ = ["health_router"]
