"""
FastAPI Application Factory

Creates and configures the FastAPI application for the agent API.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from omics_oracle_v2.api.config import APISettings
from omics_oracle_v2.api.metrics import PrometheusMetricsMiddleware
from omics_oracle_v2.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from omics_oracle_v2.api.routes import (
    agents_router,
    auth_router,
    batch_router,
    health_router,
    metrics_router,
    users_router,
    websocket_router,
    workflows_router,
)
from omics_oracle_v2.core import Settings
from omics_oracle_v2.database import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting OmicsOracle Agent API...")
    logger.info(f"API version: {app.version}")

    # Initialize components
    try:
        # Load settings to verify configuration
        settings = Settings()
        api_settings = APISettings()

        logger.info("Settings loaded successfully")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"NCBI email: {settings.geo.ncbi_email}")
        logger.info(f"CORS origins: {api_settings.cors_origins}")

        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
        raise

    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down OmicsOracle Agent API...")

    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)

    logger.info("API shutdown complete")


def create_app(settings: Settings = None, api_settings: APISettings = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        settings: Application settings (optional, will create if not provided)
        api_settings: API settings (optional, will create if not provided)

    Returns:
        FastAPI: Configured application instance
    """
    # Load settings if not provided
    if settings is None:
        settings = Settings()
    if api_settings is None:
        api_settings = APISettings()

    # Create FastAPI app
    app = FastAPI(
        title=api_settings.title,
        description=api_settings.description,
        version=api_settings.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=api_settings.cors_allow_credentials,
        allow_methods=api_settings.cors_allow_methods,
        allow_headers=api_settings.cors_allow_headers,
    )

    # Add custom middleware
    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["Health"])

    # V2 API with authentication
    app.include_router(auth_router, prefix="/api/v2")
    app.include_router(users_router, prefix="/api/v2")

    # V1 API (legacy, will be deprecated)
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["Workflows"])
    app.include_router(batch_router, prefix="/api/v1", tags=["Batch"])
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    app.include_router(metrics_router, tags=["Metrics"])

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Mounted static files from {static_dir}")

    # Dashboard endpoint
    @app.get("/dashboard", tags=["Dashboard"])
    async def dashboard():
        """Serve the web dashboard."""
        dashboard_path = static_dir / "dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        return JSONResponse(
            status_code=404,
            content={"error": "Dashboard not found"},
        )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": api_settings.title,
            "version": api_settings.version,
            "description": api_settings.description,
            "docs": "/docs",
            "dashboard": "/dashboard",
            "health": "/health",
        }

    # Custom exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            },
        )

    logger.info(f"FastAPI application created: {api_settings.title} v{api_settings.version}")

    return app


# Create default app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Load settings
    api_settings = APISettings()

    # Run server
    uvicorn.run(
        "omics_oracle_v2.api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=True,
        log_level="info",
    )
