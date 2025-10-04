"""
API Routes Package

Contains all API route modules.
"""

from omics_oracle_v2.api.routes.agents import router as agents_router
from omics_oracle_v2.api.routes.batch import router as batch_router
from omics_oracle_v2.api.routes.health import router as health_router
from omics_oracle_v2.api.routes.metrics import router as metrics_router
from omics_oracle_v2.api.routes.websockets import router as websocket_router
from omics_oracle_v2.api.routes.workflows import router as workflows_router

__all__ = [
    "health_router",
    "agents_router",
    "workflows_router",
    "websocket_router",
    "batch_router",
    "metrics_router",
]
