"""
Configuration management for OmicsOracle v2.

Provides type-safe configuration using Pydantic with environment variable
support, validation, and sensible defaults. No global state - all settings
are injectable for testing and flexibility.

Example:
    >>> from omics_oracle_v2.core.config import Settings
    >>> settings = Settings()  # Loads from environment
    >>> print(settings.nlp.model_name)
    en_core_web_sm

    >>> # Or override programmatically
    >>> settings = Settings(debug=True, nlp=NLPSettings(model_name="custom"))

Environment Variables:
    OMICS_DEBUG=true
    OMICS_LOG_LEVEL=INFO

    OMICS_NLP_MODEL_NAME=en_core_web_sm
    OMICS_NLP_BATCH_SIZE=32
    OMICS_NLP_MAX_ENTITIES=100

    OMICS_GEO_API_KEY=your_key
    OMICS_GEO_CACHE_TTL=3600
    OMICS_GEO_MAX_RETRIES=3

    OMICS_AI_OPENAI_API_KEY=your_key
    OMICS_AI_MODEL=gpt-4
    OMICS_AI_MAX_TOKENS=1000
    OMICS_AI_TEMPERATURE=0.7
"""

from pathlib import Path
from typing import Optional

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field  # type: ignore


class NLPSettings(BaseSettings):
    """Configuration for NLP services."""

    model_name: str = Field(default="en_core_web_sm", description="spaCy model name for NER")
    batch_size: int = Field(default=32, ge=1, le=1000, description="Batch size for processing")
    max_entities: int = Field(default=100, ge=1, le=10000, description="Max entities to extract per document")

    class Config:
        env_prefix = "OMICS_NLP_"
        case_sensitive = False


class GEOSettings(BaseSettings):
    """Configuration for GEO data access."""

    api_key: Optional[str] = Field(default=None, description="Optional NCBI API key")
    cache_dir: Path = Field(default=Path(".cache/geo"), description="Directory for cached responses")
    cache_ttl: int = Field(default=3600, ge=0, description="Cache time-to-live in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts for API calls")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")

    class Config:
        env_prefix = "OMICS_GEO_"
        case_sensitive = False


class AISettings(BaseSettings):
    """Configuration for AI services."""

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for summarization")
    model: str = Field(default="gpt-4", description="OpenAI model to use")
    max_tokens: int = Field(default=1000, ge=1, le=32000, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    timeout: int = Field(default=60, ge=1, le=300, description="Request timeout in seconds")

    class Config:
        env_prefix = "OMICS_AI_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings."""

    # General settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Service-specific settings
    nlp: NLPSettings = Field(default_factory=NLPSettings, description="NLP service configuration")
    geo: GEOSettings = Field(default_factory=GEOSettings, description="GEO service configuration")
    ai: AISettings = Field(default_factory=AISettings, description="AI service configuration")

    class Config:
        env_prefix = "OMICS_"  # Add prefix for main settings too
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars from v1


# Convenience function to get settings instance
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance loaded from environment

    Example:
        >>> settings = get_settings()
        >>> print(settings.debug)
        False
    """
    return Settings()
