"""
API Routes Package

Contains all API route modules.
"""

from omics_oracle_v2.api.routes.agents import router as agents_router
from omics_oracle_v2.api.routes.auth import router as auth_router
from omics_oracle_v2.api.routes.health import router as health_router
from omics_oracle_v2.api.routes.metrics import router as metrics_router
from omics_oracle_v2.api.routes.users import router as users_router
from omics_oracle_v2.api.routes.websockets import router as websocket_router

__all__ = [
    "health_router",
    "agents_router",
    "auth_router",
    "users_router",
    "websocket_router",
    "metrics_router",
]
