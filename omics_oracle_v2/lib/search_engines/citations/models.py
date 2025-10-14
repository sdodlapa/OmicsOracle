"""
Data models for publication search and analysis.

These Pydantic models ensure type safety and validation throughout
the publications pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PublicationSource(str, Enum):
    """Sources for publication data."""

    PUBMED = "pubmed"
    PMC = "pmc"
    GOOGLE_SCHOLAR = "google_scholar"
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    EUROPEPMC = "europepmc"
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    MEDRXIV = "medrxiv"


class Publication(BaseModel):
    """
    Core publication data model.

    Attributes:
        pmid: PubMed ID (if from PubMed)
        pmcid: PubMed Central ID (if available)
        doi: Digital Object Identifier
        title: Publication title
        abstract: Abstract text
        authors: List of author names
        journal: Journal name
        publication_date: Publication date
        source: Data source (PubMed, PMC, Scholar, etc.)
        citations: Citation count (if available)
        mesh_terms: MeSH terms (if from PubMed)
        keywords: Author keywords
        url: Publication URL
        pdf_url: Direct PDF URL (if available)
        metadata: Additional source-specific metadata
    """

    # Identifiers
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None

    # Core metadata
    title: str
    abstract: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    publication_date: Optional[datetime] = None

    # Source information
    source: PublicationSource
    citations: Optional[int] = 0
    paper_type: Optional[str] = None  # "original" or "citing"

    # Indexing and categorization
    mesh_terms: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    # Links
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    fulltext_url: Optional[str] = None  # URL for PDF download (set by FullTextManager)
    fulltext_source: Optional[str] = None  # Source that provided the URL (institutional, pmc, etc.)

    # Full-text content (Week 4 - PDF download feature)
    full_text: Optional[str] = None
    pdf_path: Optional[str] = None
    full_text_source: Optional[str] = None  # "pdf", "html", "pmc"
    text_length: Optional[int] = None
    extraction_date: Optional[datetime] = None

    # Additional metadata
    metadata: Dict = Field(default_factory=dict)

    @validator("publication_date", pre=True)
    def parse_date(cls, v):
        """Parse various date formats."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return None

    @property
    def has_full_text(self) -> bool:
        """Check if publication has full text available."""
        return bool(self.pmcid or self.pdf_url)

    @property
    def id(self) -> str:
        """Alias for primary_id - used by FullTextManager and other components."""
        return self.primary_id

    @property
    def primary_id(self) -> str:
        """Get the primary identifier for this publication."""
        return self.pmid or self.pmcid or self.doi or f"unknown_{hash(self.title)}"

    def __hash__(self):
        """Hash based on primary identifier for deduplication."""
        return hash(self.primary_id)

    def __eq__(self, other):
        """Equality based on primary identifier."""
        if not isinstance(other, Publication):
            return False
        return self.primary_id == other.primary_id


class PublicationSearchResult(BaseModel):
    """
    Single publication search result with relevance scoring.

    Attributes:
        publication: The publication data
        relevance_score: Overall relevance score (0-100)
        score_breakdown: Breakdown of scoring components
        rank: Result rank position
        query_matches: Terms from query that matched
    """

    publication: Publication
    relevance_score: float = Field(ge=0.0, le=100.0)
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    rank: int = 0
    query_matches: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PublicationResult(BaseModel):
    """
    Complete publication search results.

    Attributes:
        query: Original search query
        publications: Ranked list of publication results
        total_found: Total number of publications found
        sources_used: List of sources queried
        search_time_ms: Search execution time in milliseconds
        metadata: Additional search metadata
    """

    query: str
    publications: List[PublicationSearchResult] = Field(default_factory=list)
    total_found: int = 0
    sources_used: List[str] = Field(default_factory=list)
    search_time_ms: float = 0.0
    metadata: Dict = Field(default_factory=dict)

    @property
    def top_result(self) -> Optional[PublicationSearchResult]:
        """Get the top-ranked result."""
        return self.publications[0] if self.publications else None

    @property
    def has_results(self) -> bool:
        """Check if any results were found."""
        return len(self.publications) > 0

    def get_by_rank(self, rank: int) -> Optional[PublicationSearchResult]:
        """Get result by rank position (1-indexed)."""
        idx = rank - 1
        return self.publications[idx] if 0 <= idx < len(self.publications) else None

    def filter_by_score(self, min_score: float) -> List[PublicationSearchResult]:
        """Filter results by minimum relevance score."""
        return [r for r in self.publications if r.relevance_score >= min_score]

    def filter_by_citations(self, min_citations: int) -> List[PublicationSearchResult]:
        """Filter results by minimum citation count."""
        return [
            r
            for r in self.publications
            if r.publication.citations and r.publication.citations >= min_citations
        ]


class CitationAnalysis(BaseModel):
    """
    Citation analysis for a publication (Week 3).

    Attributes:
        publication: The publication being analyzed
        total_citations: Total citation count
        citations_per_year: Average citations per year
        h_index_contribution: Contribution to author's h-index
        citing_papers: List of papers citing this one
        co_citation_network: Papers frequently co-cited with this one
    """

    publication: Publication
    total_citations: int = 0
    citations_per_year: float = 0.0
    h_index_contribution: int = 0
    citing_papers: List[Publication] = Field(default_factory=list)
    co_citation_network: List[Publication] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
