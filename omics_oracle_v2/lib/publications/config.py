"""
Configuration models for the publications module.

All configurations use Pydantic for validation and follow the
feature toggle pattern from AdvancedSearchPipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import BaseModel, Field, validator


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


class GoogleScholarConfig(BaseModel):
    """
    Configuration for Google Scholar scraping (Week 3).

    Attributes:
        enable: Enable Google Scholar search
        max_results: Maximum results per query
        rate_limit_seconds: Seconds to wait between requests
        use_proxy: Use proxy for requests
        proxy_url: Proxy server URL
        timeout_seconds: Request timeout
        user_agent: User agent string (currently unused by scholarly)
    """

    enable: bool = Field(True, description="Enable Google Scholar search")
    max_results: int = Field(50, ge=1, le=100, description="Max results per query")
    rate_limit_seconds: float = Field(
        3.0, ge=0.5, le=10.0, description="Seconds between requests to avoid blocking"
    )
    use_proxy: bool = Field(False, description="Use proxy for requests")
    proxy_url: Optional[str] = Field(None, description="Proxy server URL")
    timeout_seconds: int = Field(30, ge=5, le=300, description="Request timeout")
    user_agent: str = Field(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        description="User agent string"
    )

    class Config:
        """Pydantic config."""

        validate_assignment = True


class PDFConfig(BaseModel):
    """
    Configuration for PDF processing (Week 4).

    Attributes:
        download_pdfs: Enable PDF downloading
        pdf_storage_path: Path to store PDFs
        use_grobid: Use GROBID for PDF extraction
        grobid_url: GROBID server URL
        max_file_size_mb: Maximum PDF file size
    """

    download_pdfs: bool = Field(True)
    pdf_storage_path: str = Field("./data/pdfs")
    use_grobid: bool = Field(False)
    grobid_url: Optional[str] = Field(None)
    max_file_size_mb: int = Field(50, ge=1, le=500)

    class Config:
        """Pydantic config."""

        validate_assignment = True


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

        primary_institution: Primary institution for access ("gatech" or "odu")
        secondary_institution: Fallback institution

        ranking_weights: Scoring weights for ranking
        deduplication: Enable cross-source deduplication
    """

    # Feature toggles (Week 1-2: only PubMed)
    enable_pubmed: bool = True
    enable_scholar: bool = False  # Week 3
    enable_citations: bool = False  # Week 3
    enable_pdf_download: bool = False  # Week 4
    enable_fulltext: bool = False  # Week 4
    enable_institutional_access: bool = True  # Week 4 - NEW

    # Component configurations
    pubmed_config: PubMedConfig = field(default_factory=lambda: PubMedConfig(email="user@example.com"))
    scholar_config: GoogleScholarConfig = field(default_factory=GoogleScholarConfig)
    pdf_config: PDFConfig = field(default_factory=PDFConfig)

    # Institutional access (Week 4 - NEW)
    primary_institution: str = "gatech"  # "gatech" or "odu"
    secondary_institution: str = "odu"  # Fallback institution

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
