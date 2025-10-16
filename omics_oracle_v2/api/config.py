"""
API Configuration

Configuration settings specific to the FastAPI application.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API-specific configuration settings."""

    # API Metadata
    title: str = "OmicsOracle Agent API"
    description: str = "Multi-agent biomedical research platform"
    version: str = "2.0.0"

    # Server Settings
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    workers: int = Field(default=1, description="Number of worker processes")

    # CORS Settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # API Limits
    max_query_length: int = Field(default=500, description="Maximum query length")
    max_results_per_request: int = Field(
        default=1000, description="Maximum results per request"
    )
    max_batch_size: int = Field(default=50, description="Maximum batch size")

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # Middleware Features
    enable_prometheus_metrics: bool = Field(
        default=True, description="Enable Prometheus metrics collection"
    )
    enable_request_logging: bool = Field(
        default=True, description="Enable request/response logging"
    )

    # Timeouts
    request_timeout_seconds: int = 300  # 5 minutes
    workflow_timeout_seconds: int = 600  # 10 minutes

    class Config:
        env_prefix = "API_"
        case_sensitive = False
