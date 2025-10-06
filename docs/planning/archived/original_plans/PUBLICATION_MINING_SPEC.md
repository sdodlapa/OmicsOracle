# Publication Mining Technical Specification

**Date:** October 6, 2025  
**Version:** 1.0  
**Module:** `omics_oracle_v2/lib/publications/`  
**Priority:** High

---

## Overview

This document provides detailed technical specifications for the Publication Mining module, which will enable OmicsOracle to retrieve, process, and analyze biomedical publications from multiple sources.

---

## Module Architecture

```
omics_oracle_v2/lib/publications/
├── __init__.py
├── models.py              # Data models for publications
├── pubmed_client.py       # PubMed/NCBI E-utilities client
├── pmc_client.py          # PubMed Central full-text client
├── europe_pmc_client.py   # Europe PMC client
├── preprint_client.py     # bioRxiv/medRxiv client
├── crossref_client.py     # CrossRef metadata client
├── publication_service.py # High-level service orchestrator
├── cache.py               # Publication caching layer
└── exceptions.py          # Custom exceptions
```

---

## Data Models

### Core Models (`models.py`)

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class PublicationType(str, Enum):
    """Types of publications."""
    RESEARCH_ARTICLE = "research-article"
    REVIEW = "review"
    CASE_REPORT = "case-report"
    META_ANALYSIS = "meta-analysis"
    PREPRINT = "preprint"
    EDITORIAL = "editorial"
    LETTER = "letter"
    OTHER = "other"


class PublicationSource(str, Enum):
    """Publication data sources."""
    PUBMED = "pubmed"
    PMC = "pmc"
    EUROPE_PMC = "europe_pmc"
    BIORXIV = "biorxiv"
    MEDRXIV = "medrxiv"
    CROSSREF = "crossref"


@dataclass
class Author:
    """Publication author."""
    first_name: Optional[str] = None
    last_name: str = ""
    initials: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    email: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name


@dataclass
class Reference:
    """Publication reference/citation."""
    ref_id: str
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    pmid: Optional[str] = None
    doi: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class Journal:
    """Journal information."""
    name: str
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    impact_factor: Optional[float] = None


@dataclass
class MeSHTerm:
    """Medical Subject Heading term."""
    descriptor: str
    qualifier: Optional[str] = None
    is_major_topic: bool = False


@dataclass
class PublicationMetadata:
    """Core publication metadata."""
    
    # Identifiers
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    
    # Core fields
    title: str = ""
    abstract: str = ""
    authors: List[Author] = field(default_factory=list)
    
    # Journal info
    journal: Optional[Journal] = None
    
    # Dates
    publication_date: Optional[date] = None
    epub_date: Optional[date] = None
    revised_date: Optional[date] = None
    
    # Classification
    publication_type: PublicationType = PublicationType.OTHER
    mesh_terms: List[MeSHTerm] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Metrics
    citation_count: int = 0
    
    # Availability
    has_full_text: bool = False
    has_pdf: bool = False
    is_open_access: bool = False
    
    # Source
    source: PublicationSource = PublicationSource.PUBMED
    retrieved_at: datetime = field(default_factory=datetime.now)
    
    # Raw data
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FullTextArticle:
    """Full-text article with sections."""
    
    # Core metadata
    metadata: PublicationMetadata
    
    # Full text
    full_text: str = ""
    
    # Structured sections
    sections: Dict[str, str] = field(default_factory=dict)
    # Example: {
    #     'abstract': '...',
    #     'introduction': '...',
    #     'methods': '...',
    #     'results': '...',
    #     'discussion': '...',
    #     'conclusion': '...'
    # }
    
    # References
    references: List[Reference] = field(default_factory=list)
    
    # Additional content
    figures: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    
    # Extraction metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    extraction_method: str = "unknown"
    extraction_quality: float = 0.0  # 0-1 confidence score


@dataclass
class SearchQuery:
    """Publication search query."""
    
    query: str
    max_results: int = 20
    
    # Filters
    publication_date_from: Optional[date] = None
    publication_date_to: Optional[date] = None
    publication_types: List[PublicationType] = field(default_factory=list)
    has_full_text: Optional[bool] = None
    has_abstract: Optional[bool] = None
    is_open_access: Optional[bool] = None
    
    # Sorting
    sort_by: str = "relevance"  # relevance, date, citation_count
    sort_order: str = "desc"  # asc, desc
    
    # Pagination
    offset: int = 0


@dataclass
class SearchResults:
    """Publication search results."""
    
    publications: List[PublicationMetadata]
    total: int
    query: str
    query_time: float
    source: PublicationSource
    has_more: bool = False
```

---

## PubMed Client (`pubmed_client.py`)

### Implementation

```python
import asyncio
import logging
from typing import List, Optional
from datetime import date
import aiohttp
from Bio import Entrez

from .models import (
    PublicationMetadata,
    SearchQuery,
    SearchResults,
    PublicationSource,
    PublicationType,
    Author,
    Journal,
    MeSHTerm,
)
from .exceptions import PublicationAPIError, RateLimitError


logger = logging.getLogger(__name__)


class PubMedClient:
    """
    Client for NCBI PubMed E-utilities API.
    
    Provides methods to search PubMed, retrieve article details,
    and access related articles and citations.
    
    Uses NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(
        self,
        email: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        Initialize PubMed client.
        
        Args:
            email: Required by NCBI for tracking (good practice)
            api_key: Optional API key for higher rate limits
                    (10 req/sec with key vs 3 req/sec without)
            max_retries: Maximum number of retry attempts
        """
        self.email = email
        self.api_key = api_key
        self.max_retries = max_retries
        
        # Configure Biopython Entrez
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        
        # Rate limiting (3 req/sec without key, 10 req/sec with key)
        self.rate_limit = 10 if api_key else 3
        self._last_request_time = 0
        self._request_lock = asyncio.Lock()
    
    async def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting."""
        async with self._request_lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_request_time
            min_interval = 1.0 / self.rate_limit
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
    
    async def search(
        self,
        query: SearchQuery,
    ) -> SearchResults:
        """
        Search PubMed for articles.
        
        Args:
            query: Search query with filters
        
        Returns:
            Search results with metadata
        
        Raises:
            PublicationAPIError: If API call fails
            RateLimitError: If rate limit exceeded
        """
        await self._wait_for_rate_limit()
        
        try:
            import time
            start_time = time.time()
            
            # Build search term with filters
            search_term = self._build_search_term(query)
            
            logger.info(f"Searching PubMed: {search_term}")
            
            # ESearch: Get PMIDs
            with Entrez.esearch(
                db="pubmed",
                term=search_term,
                retmax=query.max_results,
                retstart=query.offset,
                sort=self._get_sort_param(query.sort_by),
            ) as handle:
                search_results = Entrez.read(handle)
            
            pmids = search_results["IdList"]
            total = int(search_results["Count"])
            
            logger.info(f"Found {total} results, retrieving {len(pmids)} PMIDs")
            
            # EFetch: Get full records
            publications = []
            if pmids:
                publications = await self._fetch_details(pmids)
            
            query_time = time.time() - start_time
            
            return SearchResults(
                publications=publications,
                total=total,
                query=query.query,
                query_time=query_time,
                source=PublicationSource.PUBMED,
                has_more=(query.offset + len(pmids)) < total,
            )
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise PublicationAPIError(f"PubMed search failed: {e}") from e
    
    def _build_search_term(self, query: SearchQuery) -> str:
        """Build PubMed search term with filters."""
        terms = [query.query]
        
        # Date filter
        if query.publication_date_from:
            date_str = query.publication_date_from.strftime("%Y/%m/%d")
            terms.append(f"{date_str}[PDAT]:3000[PDAT]")
        
        if query.publication_date_to:
            date_str = query.publication_date_to.strftime("%Y/%m/%d")
            terms.append(f"1900[PDAT]:{date_str}[PDAT]")
        
        # Publication type filter
        if query.publication_types:
            type_terms = " OR ".join(
                f"{pt.value}[PT]" for pt in query.publication_types
            )
            terms.append(f"({type_terms})")
        
        # Full text filter
        if query.has_full_text:
            terms.append("free full text[SB]")
        
        # Abstract filter
        if query.has_abstract:
            terms.append("hasabstract")
        
        return " AND ".join(terms)
    
    def _get_sort_param(self, sort_by: str) -> str:
        """Convert sort parameter to PubMed format."""
        sort_map = {
            "relevance": "relevance",
            "date": "pub_date",
            "citation_count": "relevance",  # PubMed doesn't have citation sort
        }
        return sort_map.get(sort_by, "relevance")
    
    async def _fetch_details(self, pmids: List[str]) -> List[PublicationMetadata]:
        """Fetch detailed article information for PMIDs."""
        await self._wait_for_rate_limit()
        
        try:
            with Entrez.efetch(
                db="pubmed",
                id=pmids,
                rettype="medline",
                retmode="xml",
            ) as handle:
                records = Entrez.read(handle)
            
            publications = []
            for record in records["PubmedArticle"]:
                try:
                    pub = self._parse_pubmed_record(record)
                    publications.append(pub)
                except Exception as e:
                    logger.warning(f"Failed to parse PubMed record: {e}")
                    continue
            
            return publications
            
        except Exception as e:
            logger.error(f"Failed to fetch PubMed details: {e}")
            raise PublicationAPIError(f"Failed to fetch details: {e}") from e
    
    def _parse_pubmed_record(self, record: dict) -> PublicationMetadata:
        """Parse PubMed XML record into PublicationMetadata."""
        medline = record["MedlineCitation"]
        article = medline["Article"]
        
        # Extract PMID
        pmid = str(medline["PMID"])
        
        # Extract title
        title = article.get("ArticleTitle", "")
        
        # Extract abstract
        abstract_parts = article.get("Abstract", {}).get("AbstractText", [])
        if isinstance(abstract_parts, list):
            abstract = " ".join(str(part) for part in abstract_parts)
        else:
            abstract = str(abstract_parts)
        
        # Extract authors
        authors = []
        for author_data in article.get("AuthorList", []):
            if "LastName" in author_data:
                author = Author(
                    first_name=author_data.get("ForeName"),
                    last_name=author_data["LastName"],
                    initials=author_data.get("Initials"),
                    affiliation=author_data.get("AffiliationInfo", [{}])[0].get(
                        "Affiliation"
                    ),
                )
                authors.append(author)
        
        # Extract journal info
        journal_data = article.get("Journal", {})
        journal = Journal(
            name=journal_data.get("Title", ""),
            issn=journal_data.get("ISSN"),
            volume=article.get("Volume"),
            issue=article.get("Issue"),
            pages=article.get("Pagination", {}).get("MedlinePgn"),
        )
        
        # Extract publication date
        pub_date = article.get("ArticleDate", [{}])[0]
        if pub_date:
            try:
                publication_date = date(
                    int(pub_date.get("Year", 1900)),
                    int(pub_date.get("Month", 1)),
                    int(pub_date.get("Day", 1)),
                )
            except (ValueError, TypeError):
                publication_date = None
        else:
            publication_date = None
        
        # Extract MeSH terms
        mesh_terms = []
        for mesh_data in medline.get("MeshHeadingList", []):
            descriptor = mesh_data.get("DescriptorName", {})
            mesh_term = MeSHTerm(
                descriptor=str(descriptor),
                is_major_topic=descriptor.attributes.get("MajorTopicYN") == "Y",
            )
            mesh_terms.append(mesh_term)
        
        # Extract keywords
        keywords = [
            str(kw) for kw in medline.get("KeywordList", [[]])[0]
        ]
        
        # Check for PMC ID and full text
        article_ids = record.get("PubmedData", {}).get("ArticleIdList", [])
        pmcid = None
        doi = None
        for id_data in article_ids:
            id_type = id_data.attributes.get("IdType")
            if id_type == "pmc":
                pmcid = str(id_data)
            elif id_type == "doi":
                doi = str(id_data)
        
        return PublicationMetadata(
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            publication_date=publication_date,
            mesh_terms=mesh_terms,
            keywords=keywords,
            has_full_text=pmcid is not None,
            has_pdf=pmcid is not None,
            source=PublicationSource.PUBMED,
            raw_data=record,
        )
    
    async def get_article(self, pmid: str) -> PublicationMetadata:
        """
        Get detailed information for a single article.
        
        Args:
            pmid: PubMed ID
        
        Returns:
            Publication metadata
        """
        publications = await self._fetch_details([pmid])
        if not publications:
            raise PublicationAPIError(f"Article not found: {pmid}")
        return publications[0]
    
    async def get_related(
        self,
        pmid: str,
        max_results: int = 20,
    ) -> List[str]:
        """
        Get related article PMIDs.
        
        Args:
            pmid: PubMed ID
            max_results: Maximum number of related articles
        
        Returns:
            List of related PMIDs
        """
        await self._wait_for_rate_limit()
        
        try:
            with Entrez.elink(
                dbfrom="pubmed",
                db="pubmed",
                id=pmid,
                linkname="pubmed_pubmed",
            ) as handle:
                results = Entrez.read(handle)
            
            if not results or not results[0].get("LinkSetDb"):
                return []
            
            pmids = [
                link["Id"]
                for link in results[0]["LinkSetDb"][0]["Link"][:max_results]
            ]
            
            return pmids
            
        except Exception as e:
            logger.error(f"Failed to get related articles: {e}")
            return []
    
    async def get_citations(
        self,
        pmid: str,
        max_results: int = 100,
    ) -> List[str]:
        """
        Get PMIDs of articles citing this article.
        
        Args:
            pmid: PubMed ID
            max_results: Maximum number of citing articles
        
        Returns:
            List of citing PMIDs
        """
        await self._wait_for_rate_limit()
        
        try:
            with Entrez.elink(
                dbfrom="pubmed",
                db="pubmed",
                id=pmid,
                linkname="pubmed_pubmed_citedin",
            ) as handle:
                results = Entrez.read(handle)
            
            if not results or not results[0].get("LinkSetDb"):
                return []
            
            pmids = [
                link["Id"]
                for link in results[0]["LinkSetDb"][0]["Link"][:max_results]
            ]
            
            return pmids
            
        except Exception as e:
            logger.error(f"Failed to get citations: {e}")
            return []
```

---

## PMC Client (`pmc_client.py`)

### Implementation Outline

```python
class PMCClient:
    """
    Client for PubMed Central (PMC) full-text articles.
    
    Provides access to full-text XML and PDF files for open-access articles.
    """
    
    BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
    FTP_BASE = "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/"
    
    async def get_full_text(self, pmcid: str) -> FullTextArticle:
        """
        Get full-text article from PMC.
        
        Args:
            pmcid: PMC ID (e.g., 'PMC1234567')
        
        Returns:
            Full-text article with sections
        """
        # 1. Fetch PMC XML via OAI-PMH
        # 2. Parse XML to extract sections
        # 3. Parse references
        # 4. Return FullTextArticle
        pass
    
    async def download_pdf(self, pmcid: str) -> bytes:
        """Download PDF from PMC FTP."""
        pass
    
    async def get_sections(self, pmcid: str) -> Dict[str, str]:
        """Extract article sections."""
        pass
    
    async def extract_references(self, pmcid: str) -> List[Reference]:
        """Extract references from article."""
        pass
```

---

## Service Layer (`publication_service.py`)

### High-Level Service

```python
class PublicationService:
    """
    High-level service for publication management.
    
    Orchestrates multiple clients and provides unified interface.
    """
    
    def __init__(self, config: PublicationConfig):
        self.pubmed = PubMedClient(
            email=config.email,
            api_key=config.ncbi_api_key,
        )
        self.pmc = PMCClient()
        self.europe_pmc = EuropePMCClient(
            email=config.email,
        )
        self.cache = PublicationCache(config.cache_dir)
    
    async def search(
        self,
        query: str,
        sources: List[PublicationSource] = None,
        **filters,
    ) -> SearchResults:
        """
        Search across multiple sources.
        
        Automatically tries multiple sources and merges results.
        """
        if sources is None:
            sources = [PublicationSource.PUBMED, PublicationSource.EUROPE_PMC]
        
        # Search each source in parallel
        tasks = []
        for source in sources:
            if source == PublicationSource.PUBMED:
                task = self.pubmed.search(SearchQuery(query=query, **filters))
            elif source == PublicationSource.EUROPE_PMC:
                task = self.europe_pmc.search(SearchQuery(query=query, **filters))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge and deduplicate results
        return self._merge_results(results)
    
    async def get_full_text(
        self,
        pmid: Optional[str] = None,
        pmcid: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> Optional[FullTextArticle]:
        """
        Get full-text article from any available source.
        
        Tries multiple methods:
        1. PMC if PMCID available
        2. Europe PMC as fallback
        3. PDF parsing if available
        """
        # Check cache first
        cache_key = pmid or pmcid or doi
        if cached := self.cache.get(cache_key):
            return cached
        
        # Try PMC first
        if pmcid:
            try:
                article = await self.pmc.get_full_text(pmcid)
                self.cache.set(cache_key, article)
                return article
            except Exception as e:
                logger.warning(f"PMC fetch failed: {e}")
        
        # Try Europe PMC
        if pmcid:
            try:
                article = await self.europe_pmc.get_full_text(pmcid)
                self.cache.set(cache_key, article)
                return article
            except Exception as e:
                logger.warning(f"Europe PMC fetch failed: {e}")
        
        return None
```

---

## Configuration

### Settings (`core/config.py` additions)

```python
@dataclass
class PublicationConfig:
    """Configuration for publication mining."""
    
    # NCBI/PubMed
    ncbi_email: str
    ncbi_api_key: Optional[str] = None
    
    # Europe PMC
    europe_pmc_email: str
    
    # Caching
    cache_dir: Path = Path("data/publications/cache")
    cache_ttl_days: int = 7
    
    # Rate limiting
    max_requests_per_second: int = 3
    
    # PDF processing
    enable_pdf_download: bool = True
    pdf_storage_dir: Path = Path("data/publications/pdfs")
    max_pdf_size_mb: int = 50
    
    # Full-text
    enable_full_text: bool = True
    preferred_sources: List[PublicationSource] = field(
        default_factory=lambda: [
            PublicationSource.PMC,
            PublicationSource.EUROPE_PMC,
        ]
    )
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/lib/publications/test_pubmed_client.py

import pytest
from omics_oracle_v2.lib.publications import PubMedClient, SearchQuery

@pytest.mark.asyncio
async def test_pubmed_search():
    """Test basic PubMed search."""
    client = PubMedClient(email="test@example.com")
    
    query = SearchQuery(
        query="breast cancer",
        max_results=10,
    )
    
    results = await client.search(query)
    
    assert results.total > 0
    assert len(results.publications) <= 10
    assert all(pub.pmid for pub in results.publications)

@pytest.mark.asyncio
async def test_pubmed_get_article():
    """Test fetching single article."""
    client = PubMedClient(email="test@example.com")
    
    # Use a known PMID
    article = await client.get_article("36006037")
    
    assert article.pmid == "36006037"
    assert article.title
    assert article.abstract
    assert article.authors

@pytest.mark.asyncio
async def test_pubmed_rate_limiting():
    """Test that rate limiting is enforced."""
    client = PubMedClient(email="test@example.com")
    
    # Make multiple rapid requests
    start = time.time()
    for _ in range(5):
        await client.get_article("36006037")
    elapsed = time.time() - start
    
    # Should take at least 1 second (3 req/sec limit)
    assert elapsed >= 1.0
```

---

## API Integration

### New Endpoints

```python
# api/routes/publications.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..dependencies import get_publication_service

router = APIRouter(prefix="/api/publications", tags=["publications"])

@router.post("/search")
async def search_publications(
    query: str,
    max_results: int = 20,
    publication_date_from: Optional[str] = None,
    has_full_text: Optional[bool] = None,
    service: PublicationService = Depends(get_publication_service),
):
    """Search publications across multiple sources."""
    search_query = SearchQuery(
        query=query,
        max_results=max_results,
        publication_date_from=publication_date_from,
        has_full_text=has_full_text,
    )
    
    results = await service.search(search_query)
    return results

@router.get("/publications/{pmid}")
async def get_publication(
    pmid: str,
    service: PublicationService = Depends(get_publication_service),
):
    """Get publication metadata by PMID."""
    try:
        article = await service.pubmed.get_article(pmid)
        return article
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/publications/{pmid}/fulltext")
async def get_full_text(
    pmid: str,
    service: PublicationService = Depends(get_publication_service),
):
    """Get full-text article."""
    article = await service.get_full_text(pmid=pmid)
    
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Full text not available"
        )
    
    return article
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| PubMed search | < 2s | For 20 results |
| Get article | < 1s | Single PMID |
| Full-text retrieval | < 3s | PMC XML |
| PDF download | < 5s | Depends on size |
| Batch operations | 100/min | With API key |

---

## Dependencies

```toml
# pyproject.toml additions

[project.dependencies]
# Existing dependencies...
biopython = ">=1.81"
aiohttp = ">=3.8.5"
beautifulsoup4 = ">=4.12.2"
lxml = ">=4.9.3"
tenacity = ">=8.2.3"
```

---

## Next Steps

1. ✅ Review and approve specification
2. ⏭️ Implement core models
3. ⏭️ Implement PubMedClient
4. ⏭️ Write comprehensive tests
5. ⏭️ Integrate with API
6. ⏭️ Deploy to dev environment

---

**Specification Status:** ✅ Complete  
**Ready for:** Implementation (Phase 1)
