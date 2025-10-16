"""
Data Models for Unified Database

Type-safe dataclasses representing database records.
All models use optional fields to support partial updates.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UniversalIdentifier:
    """
    Central identifier linking GEO datasets to publications.

    Uses multi-tier identifier strategy:
    - Tier 1: Primary identifiers (DOI, PMID, PMC, arXiv) - at least one should exist
    - Tier 2: Content hash (computed from title+authors+year) - fallback if no primary ID
    - Tier 3: Source-specific IDs (OpenAlex ID, S2 ID, etc.) - for tracking and enrichment

    At least one identifier (primary or content_hash) must be present.
    Title is now optional to handle malformed API data gracefully.
    """

    geo_id: str

    # Tier 1: Primary identifiers (all optional, but at least one should exist)
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc_id: Optional[str] = None
    arxiv_id: Optional[str] = None

    # Tier 2: Computed identifier (fallback when no primary ID available)
    content_hash: Optional[
        str
    ] = None  # 16-char hex from normalized(title+authors+year)

    # Tier 3: Source-specific identifiers (for tracking and future enrichment)
    source_id: Optional[str] = None  # OpenAlex ID (W12345), Semantic Scholar ID, etc.
    source_name: Optional[str] = None  # 'openalex', 'pubmed', 'semantic_scholar', etc.

    # Metadata (all optional - handle malformed API data)
    title: Optional[
        str
    ] = None  # Can be NULL if malformed data (e.g., OpenAlex title: null)
    authors: Optional[str] = None  # JSON string
    journal: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None

    # URL collection optimization fields (NEW!)
    pdf_url: Optional[str] = None  # Direct PDF URL from discovery source
    fulltext_url: Optional[str] = None  # Landing page or fulltext URL
    oa_status: Optional[str] = None  # 'gold', 'green', 'bronze', 'hybrid', 'closed'
    url_source: Optional[str] = None  # 'openalex', 'pmc', 'europepmc', 'waterfall'
    url_discovered_at: Optional[str] = None  # ISO 8601 timestamp

    # Timestamps
    first_discovered_at: Optional[str] = None
    last_updated_at: Optional[str] = None


@dataclass
class GEODataset:
    """GEO dataset metadata and statistics."""

    geo_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    organism: Optional[str] = None
    platform: Optional[str] = None
    publication_count: int = 0
    pdfs_downloaded: int = 0
    pdfs_extracted: int = 0
    avg_extraction_quality: float = 0.0
    created_at: Optional[str] = None
    last_processed_at: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None


@dataclass
class URLDiscovery:
    """URL discovery results from Pipeline 2."""

    geo_id: str
    pmid: str
    urls_json: str  # JSON array of URL objects
    sources_queried: str  # JSON array of source names
    url_count: int = 0
    pubmed_urls: int = 0
    unpaywall_urls: int = 0
    europepmc_urls: int = 0
    other_urls: int = 0
    has_pdf_url: bool = False
    has_html_url: bool = False
    best_url_type: Optional[str] = None
    discovered_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class PDFAcquisition:
    """PDF download results from Pipeline 3."""

    geo_id: str
    pmid: str
    pdf_path: str
    pdf_hash_sha256: str
    pdf_size_bytes: Optional[int] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    download_method: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    downloaded_at: Optional[str] = None
    verified_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ContentExtraction:
    """Basic content extraction results from Pipeline 4."""

    geo_id: str
    pmid: str
    full_text: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    extractor_used: Optional[str] = None
    extraction_method: Optional[str] = None
    extraction_quality: Optional[float] = None
    extraction_grade: Optional[str] = None
    has_readable_text: bool = False
    needs_ocr: bool = False
    extracted_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class EnrichedContent:
    """Advanced enrichment results from Pipeline 4."""

    geo_id: str
    pmid: str
    sections_json: Optional[str] = None
    tables_json: Optional[str] = None
    references_json: Optional[str] = None
    figures_json: Optional[str] = None
    chatgpt_prompt: Optional[str] = None
    chatgpt_metadata: Optional[str] = None
    grobid_xml: Optional[str] = None
    grobid_tei_json: Optional[str] = None
    enrichers_applied: Optional[str] = None  # JSON array
    enrichment_quality: Optional[float] = None
    enriched_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ProcessingLog:
    """Audit trail entry for pipeline events."""

    geo_id: str
    pipeline: str  # 'P1', 'P2', 'P3', 'P4', 'system'
    event_type: str  # 'start', 'success', 'error', 'retry', 'skip'
    pmid: Optional[str] = None
    message: Optional[str] = None
    duration_ms: Optional[int] = None
    memory_mb: Optional[float] = None
    error_type: Optional[str] = None
    error_traceback: Optional[str] = None
    logged_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class CacheMetadata:
    """Cache file metadata and expiration tracking."""

    cache_key: str
    cache_type: str  # 'citation', 'url', 'pdf', 'parsed', 'enriched'
    geo_id: Optional[str] = None
    pmid: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash_sha256: Optional[str] = None
    ttl_days: int = 30
    expires_at: Optional[str] = None
    is_valid: bool = True
    last_accessed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[int] = None


# Helper functions for timestamp management
def now_iso() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat() + "Z"


def expires_at_iso(days: int) -> str:
    """Calculate expiration timestamp."""
    from datetime import timedelta

    return (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
