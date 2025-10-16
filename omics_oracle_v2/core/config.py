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

    OPENAI_API_KEY=your_key
    OMICS_AI_MODEL=gpt-4
    OMICS_AI_MAX_TOKENS=1000
    OMICS_AI_TEMPERATURE=0.7
"""

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

try:
    from pydantic import BaseModel, Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseModel, BaseSettings, Field  # type: ignore

    SettingsConfigDict = None  # type: ignore

if TYPE_CHECKING:
    from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import PubMedConfig


class NLPSettings(BaseSettings):
    """Configuration for NLP services."""

    model_name: str = Field(
        default="en_core_web_sm", description="spaCy model name for NER"
    )
    batch_size: int = Field(
        default=32, ge=1, le=1000, description="Batch size for processing"
    )
    max_entities: int = Field(
        default=100, ge=1, le=10000, description="Max entities to extract per document"
    )

    class Config:
        env_prefix = "OMICS_NLP_"
        case_sensitive = False


class GEOSettings(BaseSettings):
    """Configuration for GEO data access."""

    model_config = SettingsConfigDict(
        env_prefix="OMICS_GEO_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ncbi_email: Optional[str] = Field(
        default=None, description="Email for NCBI API (required)"
    )
    ncbi_api_key: Optional[str] = Field(
        default=None, description="Optional NCBI API key for higher rate limits"
    )
    cache_dir: Path = Field(
        default=Path(".cache/geo"), description="Directory for cached responses"
    )
    cache_ttl: int = Field(
        default=3600, ge=0, description="Cache time-to-live in seconds"
    )
    use_cache: bool = Field(default=True, description="Enable caching of API responses")
    rate_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Requests per second (NCBI guideline: 3 without API key)",
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry attempts for API calls"
    )
    timeout: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    verify_ssl: bool = Field(
        default=True, description="Verify SSL certificates for API calls"
    )
    max_concurrent_fetches: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum concurrent GEO metadata fetches (Week 3 Day 2: 10-50 recommended)",
    )


class AISettings(BaseSettings):
    """Configuration for AI services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for summarization",
        env="OPENAI_API_KEY",
    )
    model: str = Field(
        default="gpt-4-turbo-preview",  # Changed from gpt-4 for 128K context window
        description="OpenAI model to use",
        env="OMICS_AI_MODEL"
    )
    max_tokens: int = Field(
        default=4000,  # Comprehensive analysis with GPT-4 Turbo's large context
        ge=1,
        le=32000,
        description="Maximum tokens in response",
        env="OMICS_AI_MAX_TOKENS",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
        env="OMICS_AI_TEMPERATURE",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Request timeout in seconds",
        env="OMICS_AI_TIMEOUT",
    )


class RedisSettings(BaseSettings):
    """Configuration for Redis caching and rate limiting."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    password: str | None = Field(default=None, description="Redis password")
    max_connections: int = Field(
        default=10, ge=1, le=100, description="Maximum number of Redis connections"
    )
    socket_timeout: int = Field(
        default=5, ge=1, le=60, description="Socket timeout in seconds"
    )
    socket_connect_timeout: int = Field(
        default=5, ge=1, le=60, description="Socket connect timeout in seconds"
    )
    decode_responses: bool = Field(
        default=True, description="Automatically decode responses to strings"
    )
    health_check_interval: int = Field(
        default=30, ge=5, le=300, description="Health check interval in seconds"
    )

    class Config:
        env_prefix = "OMICS_REDIS_"
        case_sensitive = False


class RateLimitSettings(BaseSettings):
    """Configuration for rate limiting and quotas."""

    enabled: bool = Field(default=True, description="Enable rate limiting")
    fallback_to_memory: bool = Field(
        default=True, description="Use in-memory rate limiting if Redis unavailable"
    )

    # Tier limits (requests per hour)
    free_tier_limit_hour: int = Field(
        default=100, ge=1, description="Free tier hourly limit"
    )
    pro_tier_limit_hour: int = Field(
        default=1000, ge=1, description="Pro tier hourly limit"
    )
    enterprise_tier_limit_hour: int = Field(
        default=10000, ge=1, description="Enterprise tier hourly limit"
    )

    # Daily limits
    free_tier_limit_day: int = Field(
        default=1000, ge=1, description="Free tier daily limit"
    )
    pro_tier_limit_day: int = Field(
        default=20000, ge=1, description="Pro tier daily limit"
    )
    enterprise_tier_limit_day: int = Field(
        default=200000, ge=1, description="Enterprise tier daily limit"
    )

    # Anonymous/IP-based limits
    anonymous_limit_hour: int = Field(
        default=10, ge=1, description="Anonymous hourly limit"
    )

    # Concurrent request limits
    free_tier_concurrent: int = Field(
        default=5, ge=1, description="Free tier concurrent limit"
    )
    pro_tier_concurrent: int = Field(
        default=20, ge=1, description="Pro tier concurrent limit"
    )
    enterprise_tier_concurrent: int = Field(
        default=100, ge=1, description="Enterprise tier concurrent limit"
    )

    class Config:
        env_prefix = "OMICS_RATE_LIMIT_"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Configuration for database connection."""

    url: str = Field(
        default="postgresql+asyncpg://omics:omics@localhost:5432/omics_oracle",
        description="Database connection URL (async)",
    )
    echo: bool = Field(default=False, description="Echo SQL queries (debug)")
    pool_size: int = Field(default=5, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(
        default=10, ge=0, le=100, description="Max connections beyond pool_size"
    )

    class Config:
        env_prefix = "OMICS_DB_"
        case_sensitive = False


class AuthSettings(BaseSettings):
    """Configuration for authentication and security."""

    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32",
        description="Secret key for JWT tokens (use openssl rand -hex 32)",
    )
    access_token_expire_minutes: int = Field(
        default=60 * 24,  # 24 hours
        ge=1,
        description="JWT access token expiration (minutes)",
    )
    password_reset_token_expire_hours: int = Field(
        default=24, ge=1, description="Password reset token expiration (hours)"
    )
    email_verification_token_expire_hours: int = Field(
        default=48, ge=1, description="Email verification token expiration (hours)"
    )
    bcrypt_rounds: int = Field(
        default=12, ge=4, le=31, description="Bcrypt hashing rounds"
    )

    class Config:
        env_prefix = "OMICS_AUTH_"
        case_sensitive = False


class RankingConfig(BaseSettings):
    """Configuration for relevance ranking algorithms.

    Controls how datasets are scored for relevance to search queries.
    Supports both keyword-based matching (current) and semantic search (Phase 2).

    Environment Variables:
        OMICS_RANKING_KEYWORD_TITLE_WEIGHT=0.4
        OMICS_RANKING_KEYWORD_SUMMARY_WEIGHT=0.3
        OMICS_RANKING_KEYWORD_ORGANISM_BONUS=0.15
        OMICS_RANKING_KEYWORD_SAMPLE_COUNT_BONUS=0.15
        OMICS_RANKING_USE_SEMANTIC_RANKING=false
        OMICS_RANKING_SEMANTIC_WEIGHT=0.6

    Example:
        >>> config = RankingConfig()
        >>> config.keyword_title_weight
        0.4
        >>> # Higher weight means title matches contribute more to score
    """

    # Keyword matching weights (Phase 0 - Current)
    keyword_title_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for title keyword matches (0.0-1.0)",
    )
    keyword_summary_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for summary keyword matches (0.0-1.0)",
    )
    keyword_organism_bonus: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Bonus score for organism match (0.0-1.0)",
    )
    keyword_sample_count_bonus: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Bonus score for adequate sample count (0.0-1.0)",
    )

    # Sample count thresholds for bonus scoring
    sample_count_large: int = Field(
        default=100,
        ge=1,
        description="Sample count threshold for 'large' dataset",
    )
    sample_count_medium: int = Field(
        default=50,
        ge=1,
        description="Sample count threshold for 'medium' dataset",
    )
    sample_count_small: int = Field(
        default=10,
        ge=1,
        description="Sample count threshold for 'small' dataset",
    )

    # Keyword matching parameters
    keyword_match_multiplier: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Multiplier per keyword match for title scoring",
    )
    keyword_summary_multiplier: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Multiplier per keyword match for summary scoring",
    )

    # Semantic search configuration (Phase 2)
    use_semantic_ranking: bool = Field(
        default=False,
        description="Enable semantic similarity ranking (requires OpenAI)",
    )
    semantic_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for semantic similarity score when enabled",
    )
    keyword_weight_semantic_mode: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for keyword score when semantic ranking enabled",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model for semantic search",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity for semantic matches",
    )

    # Synonym expansion (Phase 1)
    use_synonyms: bool = Field(
        default=False,
        description="Enable biomedical synonym expansion",
    )
    synonym_weight: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Weight multiplier for synonym matches (vs exact matches)",
    )

    class Config:
        env_prefix = "OMICS_RANKING_"
        case_sensitive = False


class QualityConfig(BaseSettings):
    """Configuration for dataset quality scoring.

    Controls how datasets are assessed for quality based on metadata completeness,
    sample counts, text quality, publications, and other factors.

    Total points add up to 100. Thresholds determine what constitutes 'high quality'.

    Environment Variables:
        OMICS_QUALITY_POINTS_SAMPLE_COUNT=20
        OMICS_QUALITY_POINTS_TITLE=15
        OMICS_QUALITY_SAMPLE_COUNT_EXCELLENT=100

    Example:
        >>> config = QualityConfig()
        >>> config.points_sample_count
        20
        >>> config.sample_count_excellent
        100
    """

    # Point allocations (should sum to 100 for clarity)
    points_sample_count: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum points for sample count (out of 100)",
    )
    points_title: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Maximum points for title quality (out of 100)",
    )
    points_summary: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Maximum points for summary quality (out of 100)",
    )
    points_publications: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum points for associated publications (out of 100)",
    )
    points_sra_data: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for SRA data availability (out of 100)",
    )
    points_recency: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for dataset recency (out of 100)",
    )
    points_metadata: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for metadata completeness (out of 100)",
    )

    # Sample count thresholds
    sample_count_excellent: int = Field(
        default=100,
        ge=1,
        description="Sample count for excellent quality (full points)",
    )
    sample_count_good: int = Field(
        default=50,
        ge=1,
        description="Sample count for good quality (75% points)",
    )
    sample_count_adequate: int = Field(
        default=10,
        ge=1,
        description="Sample count for adequate quality (50% points)",
    )

    # Title length thresholds (characters)
    title_length_descriptive: int = Field(
        default=50,
        ge=1,
        description="Title length for descriptive quality (full points)",
    )
    title_length_adequate: int = Field(
        default=20,
        ge=1,
        description="Title length for adequate quality (67% points)",
    )
    title_length_minimal: int = Field(
        default=10,
        ge=1,
        description="Title length for minimal quality (33% points)",
    )

    # Summary length thresholds (characters)
    summary_length_comprehensive: int = Field(
        default=200,
        ge=1,
        description="Summary length for comprehensive quality (full points)",
    )
    summary_length_good: int = Field(
        default=100,
        ge=1,
        description="Summary length for good quality (67% points)",
    )
    summary_length_minimal: int = Field(
        default=50,
        ge=1,
        description="Summary length for minimal quality (33% points)",
    )

    # Publication thresholds
    publications_many: int = Field(
        default=5,
        ge=1,
        description="Publication count for 'many' (full points)",
    )
    publications_some: int = Field(
        default=2,
        ge=1,
        description="Publication count for 'some' (75% points)",
    )
    publications_one: int = Field(
        default=1,
        ge=1,
        description="Publication count for 'one' (50% points)",
    )

    # Recency thresholds (days)
    recency_recent: int = Field(
        default=365,
        ge=1,
        description="Days for 'recent' dataset (< 1 year, full points)",
    )
    recency_moderate: int = Field(
        default=1825,
        ge=1,
        description="Days for 'moderate' age (< 5 years, 50% points)",
    )
    recency_old: int = Field(
        default=3650,
        ge=1,
        description="Days for 'old' dataset (< 10 years, 25% points)",
    )

    # Metadata completeness thresholds
    metadata_fields_complete: int = Field(
        default=10,
        ge=1,
        description="Required metadata fields for 'complete' (full points)",
    )
    metadata_fields_good: int = Field(
        default=7,
        ge=1,
        description="Required metadata fields for 'good' (75% points)",
    )
    metadata_fields_basic: int = Field(
        default=5,
        ge=1,
        description="Required metadata fields for 'basic' (50% points)",
    )

    # Quality level thresholds (normalized 0-1)
    excellent_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Score threshold for EXCELLENT quality level",
    )
    good_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Score threshold for GOOD quality level",
    )
    fair_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Score threshold for FAIR quality level",
    )
    # Below fair_threshold is considered POOR

    class Config:
        env_prefix = "OMICS_QUALITY_"
        case_sensitive = False


class SearchSettings(BaseSettings):
    """Configuration for SearchOrchestrator."""

    # Search sources
    enable_geo: bool = Field(default=True, description="Enable GEO dataset search")
    enable_pubmed: bool = Field(default=True, description="Enable PubMed search")
    enable_openalex: bool = Field(default=True, description="Enable OpenAlex search")

    # Query optimization
    enable_query_optimization: bool = Field(
        default=True, description="Enable query optimization"
    )
    enable_ner: bool = Field(
        default=True, description="Enable Named Entity Recognition"
    )
    enable_sapbert: bool = Field(
        default=True, description="Enable SapBERT entity extraction"
    )

    # Caching
    enable_cache: bool = Field(default=True, description="Enable result caching")
    cache_host: str = Field(default="localhost", description="Redis cache host")
    cache_port: int = Field(default=6379, description="Redis cache port")
    cache_db: int = Field(default=0, description="Redis database number")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Result limits
    max_geo_results: int = Field(
        default=100, ge=1, le=1000, description="Maximum GEO results"
    )
    max_publication_results: int = Field(
        default=100, ge=1, le=1000, description="Maximum publication results"
    )

    # PubMed configuration
    pubmed_email: str = Field(
        default_factory=lambda: os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"),
        description="Email for PubMed API"
    )
    
    @property
    def pubmed_config(self):
        """Lazy-load PubMedConfig to avoid circular imports."""
        from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import PubMedConfig
        return PubMedConfig(email=self.pubmed_email)

    # OpenAlex config
    openalex_email: str | None = Field(
        default=None, description="Email for OpenAlex polite pool"
    )

    # Database persistence
    enable_database: bool = Field(
        default=True, description="Enable database persistence"
    )
    db_path: str = Field(
        default="data/database/omics_oracle.db",
        description="Path to UnifiedDatabase file"
    )
    storage_path: str = Field(
        default="data",
        description="Base path for file storage"
    )

    # Feature flags
    enable_citations: bool = Field(
        default=False, description="Enable citation discovery"
    )
    enable_fulltext: bool = Field(
        default=False, description="Enable fulltext extraction"
    )

    class Config:
        env_prefix = "OMICS_SEARCH_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings."""

    # General settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production, test)",
    )

    # Service-specific settings
    nlp: NLPSettings = Field(
        default_factory=NLPSettings, description="NLP service configuration"
    )
    geo: GEOSettings = Field(
        default_factory=GEOSettings, description="GEO service configuration"
    )
    ai: AISettings = Field(
        default_factory=AISettings, description="AI service configuration"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings, description="Redis configuration"
    )
    rate_limit: RateLimitSettings = Field(
        default_factory=RateLimitSettings, description="Rate limiting configuration"
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings, description="Database configuration"
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings, description="Authentication configuration"
    )
    ranking: RankingConfig = Field(
        default_factory=RankingConfig, description="Ranking algorithm configuration"
    )
    quality: QualityConfig = Field(
        default_factory=QualityConfig, description="Quality scoring configuration"
    )
    search: SearchSettings = Field(
        default_factory=SearchSettings, description="Search orchestration configuration"
    )

    # Computed properties for convenience
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return self.database.url

    @property
    def database_echo(self) -> bool:
        """Get database echo setting."""
        return self.database.echo

    @property
    def database_pool_size(self) -> int:
        """Get database pool size."""
        return self.database.pool_size

    @property
    def database_max_overflow(self) -> int:
        """Get database max overflow."""
        return self.database.max_overflow

    @property
    def secret_key(self) -> str:
        """Get secret key for JWT tokens."""
        return self.auth.secret_key

    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration."""
        return self.auth.access_token_expire_minutes

    @property
    def password_reset_token_expire_hours(self) -> int:
        """Get password reset token expiration."""
        return self.auth.password_reset_token_expire_hours

    @property
    def email_verification_token_expire_hours(self) -> int:
        """Get email verification token expiration."""
        return self.auth.email_verification_token_expire_hours

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


# ============================================================================
# Embedding Configuration (Phase 1: Semantic Search)
# ============================================================================


class EmbeddingConfig(BaseModel):
    """
    Configuration for text embedding generation.

    Used by the EmbeddingService to generate vector representations
    of text for semantic similarity search.
    """

    # OpenAI settings
    api_key: Optional[str] = Field(
        None,
        description="OpenAI API key (falls back to OPENAI_API_KEY env var)",
    )
    model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model: text-embedding-3-small (fast) or text-embedding-3-large (accurate)",
    )
    dimension: int = Field(
        default=1536,
        description="Embedding vector dimension (1536 for small, 3072 for large)",
    )

    # Performance
    batch_size: int = Field(
        default=100, description="Number of texts to embed in single API call"
    )
    max_retries: int = Field(
        default=3, description="Maximum API retry attempts on failure"
    )

    # Caching
    cache_enabled: bool = Field(
        default=True, description="Enable file-based embedding cache"
    )
    cache_dir: str = Field(
        default="data/embeddings/cache", description="Directory for cached embeddings"
    )

    def explain_config(self) -> str:
        """
        Generate human-readable explanation of configuration.

        Returns:
            Formatted string explaining all configuration values
        """
        return f"""
Embedding Configuration:
========================================================================

Model Settings:
  Provider: OpenAI
  Model: {self.model}
  Dimension: {self.dimension}

Performance:
  Batch Size: {self.batch_size} texts/batch
  Max Retries: {self.max_retries}

Caching:
  Enabled: {self.cache_enabled}
  Directory: {self.cache_dir}

Cost Estimate (text-embedding-3-small):
  ~$0.02 per 1M tokens
  ~150 tokens per dataset = ~$3 per 1M datasets

Performance:
  ~100ms per batch of 100 texts
  Cache hit: <1ms
========================================================================
"""
