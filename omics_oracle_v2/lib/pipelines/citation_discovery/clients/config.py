"""
Configuration models for the publications module.

All configurations use Pydantic for validation and follow the
feature toggle pattern from AdvancedSearchPipeline.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field, validator


class RedisConfig(BaseModel):
    """
    Configuration for Redis caching (Day 26).

    Attributes:
        enable: Enable Redis caching
        host: Redis server host
        port: Redis server port
        db: Redis database number (0-15)
        password: Redis password (optional)
        default_ttl: Default TTL in seconds (1 hour)
        search_ttl: TTL for search results (1 hour)
        llm_ttl: TTL for LLM responses (24 hours)
    """

    enable: bool = Field(True, description="Enable Redis caching")
    host: str = Field("localhost", description="Redis server host")
    port: int = Field(6379, ge=1, le=65535, description="Redis server port")
    db: int = Field(0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(None, description="Redis password (if required)")

    # TTL settings (in seconds)
    default_ttl: int = Field(3600, ge=60, description="Default TTL (1 hour)")
    search_ttl: int = Field(3600, ge=60, description="Search results TTL (1 hour)")
    llm_ttl: int = Field(86400, ge=3600, description="LLM responses TTL (24 hours)")
    citation_ttl: int = Field(604800, ge=3600, description="Citation data TTL (1 week)")

    class Config:
        """Pydantic config."""

        validate_assignment = True


class PubMedConfig(BaseModel):
    """
    Configuration for PubMed/Entrez API integration.

    Attributes:
        email: Email for NCBI API (required by Entrez)
        api_key: NCBI API key for higher rate limits (optional but recommended)
        tool_name: Tool name for API requests
        max_results: Maximum results per query
        retries: Number of retries on API errors
        timeout: Request timeout in seconds
        use_history: Use Entrez history for large result sets
        return_type: Return format (xml, medline, etc.)
        database: Database to search (pubmed, pmc, etc.)
    """

    # Required
    email: str = Field(..., description="Email address for NCBI API")

    # Optional
    api_key: Optional[str] = Field(None, description="NCBI API key for higher limits")
    tool_name: str = Field("OmicsOracle", description="Tool name for API requests")

    # Query limits
    max_results: int = Field(100, ge=1, le=10000, description="Max results per query")
    batch_size: int = Field(50, ge=1, le=500, description="Batch size for fetching")

    # Network settings
    retries: int = Field(3, ge=0, le=10, description="Number of retries")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout (seconds)")

    # Advanced settings
    use_history: bool = Field(True, description="Use Entrez history for large sets")
    return_type: str = Field("medline", description="Return format")
    database: str = Field("pubmed", description="Database to search")

    # Rate limiting
    requests_per_second: float = Field(
        3.0, ge=0.1, le=10.0, description="API requests per second (3 without key, 10 with key)"
    )

    @validator("requests_per_second")
    def validate_rate_limit(cls, v, values):
        """Adjust rate limit based on API key presence."""
        has_key = values.get("api_key") is not None
        max_rate = 10.0 if has_key else 3.0
        if v > max_rate:
            return max_rate
        return v

    class Config:
        """Pydantic config."""

        validate_assignment = True


class EuropePMCConfig(BaseModel):
    """
    Configuration for Europe PMC API integration.

    Attributes:
        requests_per_second: API requests per second (conservative: 3)
        max_results: Maximum results per query
        retries: Number of retries on API errors
        timeout: Request timeout in seconds
    """

    # Rate limiting
    requests_per_second: float = Field(
        3.0, ge=0.1, le=10.0, description="API requests per second (conservative)"
    )

    # Query limits
    max_results: int = Field(100, ge=1, le=1000, description="Max results per query")

    # Network settings
    retries: int = Field(3, ge=0, le=10, description="Number of retries")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout (seconds)")

    class Config:
        """Pydantic config."""

        validate_assignment = True


class CrossrefConfig(BaseModel):
    """
    Configuration for Crossref API integration.

    Attributes:
        mailto: Email for polite pool (higher rate limits)
        requests_per_second: API requests per second (50 with mailto, 10 without)
        max_results: Maximum results per query
        retries: Number of retries on API errors
        timeout: Request timeout in seconds
    """

    # Optional mailto for polite pool
    mailto: Optional[str] = Field(None, description="Email for polite pool (recommended)")

    # Rate limiting (50 req/s with mailto, 10 without)
    requests_per_second: float = Field(
        50.0, ge=0.1, le=50.0, description="API requests per second (50 with mailto, 10 without)"
    )

    # Query limits
    max_results: int = Field(100, ge=1, le=1000, description="Max results per query")

    # Network settings
    retries: int = Field(3, ge=0, le=10, description="Number of retries")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout (seconds)")

    @validator("requests_per_second")
    def validate_rate_limit(cls, v, values):
        """Adjust rate limit based on mailto presence."""
        has_mailto = values.get("mailto") is not None
        max_rate = 50.0 if has_mailto else 10.0
        if v > max_rate:
            return max_rate
        return v

    class Config:
        """Pydantic config."""

        validate_assignment = True


class LLMConfig(BaseModel):
    """
    Configuration for LLM-powered citation analysis (Week 3 Day 15-17).

    Enables deep semantic understanding of how datasets are used in citing papers.

    💰 COST CONTROLS (Added Oct 9, 2025):
    - max_papers_to_analyze: Limit analysis to top N papers (default: 20)
    - max_cost_per_search: Budget limit per search (default: $5.00)
    - enable_cost_preview: Show estimated cost before running (default: True)

    Estimated costs:
    - GPT-4: ~$0.05 per paper analysis
    - 20 papers: ~$1.00
    - 100 papers: ~$5.00

    Attributes:
        provider: LLM provider ("openai", "anthropic", "ollama")
        model: Model name
        api_key: API key (for cloud providers)
        base_url: Base URL (for Ollama)
        cache_enabled: Enable response caching
        batch_size: Papers to analyze per batch
        max_tokens: Maximum tokens per response
        temperature: Generation temperature
        max_papers_to_analyze: Maximum papers to analyze (cost control)
        max_cost_per_search: Maximum cost per search in USD (cost control)
        enable_cost_preview: Show cost estimate before running
    """

    provider: str = Field("openai", description="LLM provider")
    model: str = Field("gpt-4-turbo-preview", description="Model name")
    api_key: Optional[str] = Field(None, description="API key for cloud providers")
    base_url: Optional[str] = Field(None, description="Base URL for Ollama")
    cache_enabled: bool = Field(True, description="Enable response caching")
    batch_size: int = Field(5, ge=1, le=20, description="Papers per batch")
    max_tokens: int = Field(2000, ge=100, le=4000, description="Max tokens per response")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Generation temperature")

    # Cost controls (NEW - Oct 9, 2025)
    max_papers_to_analyze: int = Field(
        20, ge=1, le=1000, description="Maximum papers to analyze (cost control, default: 20)"
    )
    max_cost_per_search: float = Field(
        5.0, ge=0.1, le=100.0, description="Maximum cost per search in USD (default: $5.00)"
    )
    enable_cost_preview: bool = Field(True, description="Show estimated cost before running analysis")

    class Config:
        """Pydantic config."""

        validate_assignment = True


@dataclass
class FuzzyDeduplicationConfig:
    """
    Configuration for advanced fuzzy deduplication (Week 3 Day 14).

    Uses fuzzy string matching to identify duplicates beyond exact ID matching.
    Handles title variations, author name differences, and preprint/published pairs.

    Attributes:
        enable: Enable fuzzy deduplication
        title_threshold: Minimum fuzzy ratio for title match (0-100)
        author_threshold: Minimum fuzzy ratio for author match (0-100)
        year_tolerance: Max year difference for same publication (handles preprints)
    """

    enable: bool = False  # DISABLED - Too slow, basic dedup sufficient
    title_threshold: float = 85.0  # 0-100 fuzzy ratio
    author_threshold: float = 80.0  # 0-100 fuzzy ratio
    year_tolerance: int = 1  # Years


@dataclass
class PublicationSearchConfig:
    """
    Main configuration for publication search pipeline.

    This follows the feature toggle pattern from AdvancedSearchPipeline,
    allowing incremental adoption of features.

    Feature Toggles (Week-by-Week):
    - Week 1-2: enable_pubmed
    - Week 3: enable_scholar, enable_citations
    - Week 4: enable_pdf_download, enable_fulltext, enable_institutional_access

    Attributes:
        enable_pubmed: Enable PubMed search
        enable_scholar: Enable Google Scholar search
        enable_citations: Enable citation analysis
        enable_pdf_download: Enable PDF downloading
        enable_fulltext: Enable full-text extraction
        enable_institutional_access: Enable institutional access (Georgia Tech/ODU)

        pubmed_config: PubMed configuration
        scholar_config: Google Scholar configuration
        pdf_config: PDF processing configuration
        fuzzy_dedup_config: Fuzzy deduplication configuration (Week 3 Day 14)

        primary_institution: Primary institution for access ("gatech" or "odu")
        secondary_institution: Fallback institution

        ranking_weights: Scoring weights for ranking
        deduplication: Enable cross-source deduplication
    """

    # Feature toggles - UPDATED Oct 14, 2025
    # OpenAlex is the only citation source (Scholar deleted)
    enable_pubmed: bool = True
    enable_openalex: bool = True  # ✅ Free, sustainable citation source
    enable_citations: bool = True  # ✅ Uses OpenAlex only
    enable_pdf_download: bool = True  # ✅ Week 4 - ENABLED
    enable_fulltext: bool = True  # ✅ Week 4 - ENABLED (PDF extraction)
    enable_fulltext_retrieval: bool = True  # ✅ NEW - OA source full-text URLs (Oct 9, 2025)
    enable_institutional_access: bool = True  # ✅ Week 4 - ENABLED
    enable_cache: bool = True  # ✅ Day 26 - Redis caching
    enable_query_preprocessing: bool = (
        True  # ✅ Phase 1 - Query preprocessing with BiomedicalNER (Oct 9, 2025)
    )
    enable_synonym_expansion: bool = True  # ✅ Phase 2B - Synonym expansion with ontologies (Oct 9, 2025)

    # Component configurations
    pubmed_config: PubMedConfig = field(
        default_factory=lambda: PubMedConfig(
            email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
            api_key=os.getenv("NCBI_API_KEY"),
        )
    )
    llm_config: LLMConfig = field(default_factory=LLMConfig)  # Week 3 Day 15-17
    fuzzy_dedup_config: FuzzyDeduplicationConfig = field(
        default_factory=FuzzyDeduplicationConfig
    )  # Week 3 Day 14
    redis_config: RedisConfig = field(default_factory=RedisConfig)  # Day 26 - Redis caching

    # Institutional access (Week 4 - NEW)
    primary_institution: str = "gatech"  # "gatech" or "odu"
    secondary_institution: str = "odu"  # Fallback institution

    # Synonym expansion (Phase 2B - NEW)
    max_synonyms_per_term: int = 10  # Maximum synonyms to add per technique

    # Ranking configuration
    ranking_weights: dict = field(
        default_factory=lambda: {
            "title_match": 0.4,
            "abstract_match": 0.3,
            "recency": 0.2,
            "citations": 0.1,
        }
    )

    # Advanced features
    deduplication: bool = True
    max_total_results: int = 100
    min_relevance_score: float = 0.0

    def validate(self) -> None:
        """Validate configuration settings."""
        # Check PubMed config if enabled
        if self.enable_pubmed:
            if not self.pubmed_config.email:
                raise ValueError("PubMed email is required when enable_pubmed=True")

        # Check ranking weights sum to 1.0
        weight_sum = sum(self.ranking_weights.values())
        if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Ranking weights must sum to 1.0, got {weight_sum}")

        # Validate feature dependencies
        if self.enable_fulltext and not self.enable_pdf_download:
            raise ValueError("enable_fulltext requires enable_pdf_download=True")

    def __post_init__(self):
        """Post-initialization validation."""
        self.validate()


@dataclass
class RankingConfig:
    """
    Configuration for publication ranking.

    Attributes:
        weights: Scoring weights for different factors
        recency_decay_years: Years for recency decay
        citation_scaling: How to scale citation counts
        boost_open_access: Boost score for open access papers
    """

    weights: dict = field(
        default_factory=lambda: {
            "title_match": 0.4,
            "abstract_match": 0.3,
            "recency": 0.2,
            "citations": 0.1,
        }
    )

    recency_decay_years: float = 5.0
    citation_scaling: str = "log"  # "log", "sqrt", "linear"
    boost_open_access: float = 1.1  # 10% boost
    boost_review_articles: float = 1.05  # 5% boost

    def validate(self) -> None:
        """Validate ranking configuration."""
        weight_sum = sum(self.weights.values())
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        if self.citation_scaling not in ["log", "sqrt", "linear"]:
            raise ValueError(f"Invalid citation_scaling: {self.citation_scaling}")


# =============================================================================
# Configuration Presets (Added Oct 9, 2025)
# =============================================================================
# Quick-start configuration presets for different use cases.
#
# Usage:
#     from omics_oracle_v2.lib.search_engines.citations.config import PRESET_CONFIGS
#
#     # For fast, free searches:
#     config = PRESET_CONFIGS["minimal"]
#
#     # For comprehensive analysis (recommended):
#     config = PRESET_CONFIGS["full"]
#
#     # For research with cost control:
#     config = PRESET_CONFIGS["research"]

PRESET_CONFIGS = {
    "minimal": PublicationSearchConfig(
        # Fast, free, PubMed only
        enable_pubmed=True,
        enable_citations=False,
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_institutional_access=False,
        enable_cache=True,
    ),
    "standard": PublicationSearchConfig(
        # Good coverage, free, no LLM costs
        enable_pubmed=True,
        enable_citations=False,  # No LLM costs
        enable_pdf_download=True,
        enable_fulltext=True,
        enable_institutional_access=True,
        enable_cache=True,
    ),
    "full": PublicationSearchConfig(
        # Complete analysis, all features enabled (RECOMMENDED)
        enable_pubmed=True,
        enable_citations=True,  # ✅ Full citation analysis with OpenAlex
        enable_pdf_download=True,
        enable_fulltext=True,
        enable_institutional_access=True,
        enable_cache=True,
        llm_config=LLMConfig(
            max_papers_to_analyze=20,  # Cost control: top 20 papers
            max_cost_per_search=5.0,  # Budget: $5 per search
            enable_cost_preview=True,  # Show cost before running
        ),
    ),
    "research": PublicationSearchConfig(
        # For deep research, higher limits but cost-controlled
        enable_pubmed=True,
        enable_citations=True,
        enable_pdf_download=True,
        enable_fulltext=True,
        enable_institutional_access=True,
        enable_cache=True,
        llm_config=LLMConfig(
            max_papers_to_analyze=50,  # Analyze top 50 papers
            max_cost_per_search=15.0,  # Higher budget: $15
            enable_cost_preview=True,
            batch_size=10,  # Larger batches for efficiency
        ),
    ),
    "enterprise": PublicationSearchConfig(
        # No cost limits, maximum analysis
        enable_pubmed=True,
        enable_citations=True,
        enable_pdf_download=True,
        enable_fulltext=True,
        enable_institutional_access=True,
        enable_cache=True,
        max_total_results=200,  # More papers
        llm_config=LLMConfig(
            max_papers_to_analyze=100,  # Analyze up to 100
            max_cost_per_search=50.0,  # High budget: $50
            enable_cost_preview=True,
            batch_size=10,
        ),
    ),
}


# Convenience function for getting presets
def get_preset_config(preset_name: str = "full") -> PublicationSearchConfig:
    """
    Get a preset configuration by name.

    Args:
        preset_name: One of "minimal", "standard", "full", "research", "enterprise"

    Returns:
        PublicationSearchConfig instance

    Example:
        >>> config = get_preset_config("full")  # Recommended default
        >>> config = get_preset_config("research")  # For deep analysis
    """
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset: {preset_name}. " f"Available: {', '.join(PRESET_CONFIGS.keys())}")
    return PRESET_CONFIGS[preset_name]
