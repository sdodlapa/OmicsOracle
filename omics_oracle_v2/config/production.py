"""
Production configuration with environment variables.
Week 3 Day 4: Environment-based configuration.
"""

import os
from typing import Optional


class ProductionConfig:
    """Production environment configuration."""

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # GEO settings
    GEO_MAX_CONCURRENT: int = int(os.getenv("GEO_MAX_CONCURRENT", "20"))
    GEO_TIMEOUT_SECONDS: int = int(os.getenv("GEO_TIMEOUT_SECONDS", "30"))

    # Cache settings
    CACHE_TTL_SEARCH: int = int(os.getenv("CACHE_TTL_SEARCH", "86400"))  # 24h
    CACHE_TTL_METADATA: int = int(os.getenv("CACHE_TTL_METADATA", "2592000"))  # 30d

    # Monitoring
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"


config = ProductionConfig()
