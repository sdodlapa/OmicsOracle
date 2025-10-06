# 📅 Week 1-2: Publications Module Implementation

**Phase:** Foundation  
**Duration:** 2 weeks  
**Goal:** Implement publication search with PubMed integration

---

## 🎯 Objectives

### **Primary Goals**
1. Create `lib/publications/` module structure
2. Implement `PubMedClient` for publication search
3. Create `PublicationSearchPipeline` following golden pattern
4. Integrate with `SearchAgent` via feature toggle
5. Write comprehensive tests
6. Deploy and validate

### **Success Criteria**
- ✅ PubMed search returns relevant publications
- ✅ Publications integrated with dataset search
- ✅ All tests passing (unit + integration)
- ✅ Documentation complete
- ✅ Feature toggle working (`enable_publications`)

---

## 📁 File Structure to Create

```
omics_oracle_v2/lib/publications/
├── __init__.py
├── config.py                      # Configuration classes
├── models.py                      # Data models
├── pipeline.py                    # PublicationSearchPipeline
│
├── clients/
│   ├── __init__.py
│   ├── base.py                   # BasePublicationClient
│   └── pubmed.py                 # PubMedClient
│
└── ranking/
    ├── __init__.py
    └── ranker.py                 # PublicationRanker
```

---

## 📝 Detailed Implementation Tasks

### **Day 1: Setup & Models**

#### **Task 1.1: Create module structure**
```bash
# Create directories
mkdir -p omics_oracle_v2/lib/publications/clients
mkdir -p omics_oracle_v2/lib/publications/ranking

# Create __init__.py files
touch omics_oracle_v2/lib/publications/__init__.py
touch omics_oracle_v2/lib/publications/clients/__init__.py
touch omics_oracle_v2/lib/publications/ranking/__init__.py
```

#### **Task 1.2: Implement data models** (`models.py`)

```python
"""
Data models for publications module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class PublicationType(str, Enum):
    """Types of publications"""
    JOURNAL_ARTICLE = "journal_article"
    REVIEW = "review"
    PREPRINT = "preprint"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE = "conference"
    OTHER = "other"


class Publication(BaseModel):
    """
    Single publication record.
    
    Represents a scientific publication from any source
    (PubMed, Scholar, PMC, etc.)
    """
    
    # Identifiers
    pmid: Optional[str] = Field(None, description="PubMed ID")
    pmcid: Optional[str] = Field(None, description="PubMed Central ID")
    doi: Optional[str] = Field(None, description="DOI")
    
    # Core metadata
    title: str = Field(..., description="Publication title")
    abstract: Optional[str] = Field(None, description="Abstract text")
    authors: List[str] = Field(default_factory=list, description="Author names")
    journal: Optional[str] = Field(None, description="Journal name")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    publication_type: PublicationType = Field(
        default=PublicationType.JOURNAL_ARTICLE,
        description="Type of publication"
    )
    
    # Citations & Impact
    citation_count: int = Field(default=0, description="Number of citations")
    
    # Full-text availability
    has_fulltext: bool = Field(default=False, description="Full-text available")
    fulltext_url: Optional[str] = Field(None, description="Full-text URL")
    pdf_url: Optional[str] = Field(None, description="PDF URL")
    
    # Source
    source: str = Field(..., description="Source database (pubmed, scholar, etc.)")
    
    # Additional metadata
    keywords: List[str] = Field(default_factory=list, description="Keywords/MeSH terms")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PublicationSearchResult(BaseModel):
    """Result from publication search"""
    
    publication: Publication = Field(..., description="Publication record")
    relevance_score: float = Field(..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0)
    match_reasons: List[str] = Field(default_factory=list, description="Why this publication matched")


class PublicationResult(BaseModel):
    """
    Complete result from PublicationSearchPipeline.
    """
    
    query: str = Field(..., description="Search query used")
    publications: List[PublicationSearchResult] = Field(
        default_factory=list,
        description="Ranked publications"
    )
    total_found: int = Field(..., description="Total publications found", ge=0)
    sources_used: List[str] = Field(default_factory=list, description="Sources queried")
    features_enabled: List[str] = Field(default_factory=list, description="Features that were enabled")
    
    def get_top_publications(self, n: int = 10) -> List[PublicationSearchResult]:
        """Get top N publications by relevance"""
        return sorted(
            self.publications,
            key=lambda p: p.relevance_score,
            reverse=True
        )[:n]
    
    def filter_by_score(self, min_score: float) -> List[PublicationSearchResult]:
        """Filter publications by minimum relevance score"""
        return [p for p in self.publications if p.relevance_score >= min_score]
```

#### **Task 1.3: Implement configuration** (`config.py`)

```python
"""
Configuration for publications module.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PubMedConfig:
    """Configuration for PubMed client"""
    
    api_key: Optional[str] = None
    email: Optional[str] = None  # Required by NCBI
    max_results: int = 50
    request_timeout: int = 30
    rate_limit_delay: float = 0.34  # NCBI allows 3 requests/sec (10 with API key)
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.email:
            raise ValueError("email is required for PubMed API")


@dataclass
class PublicationSearchConfig:
    """
    Configuration for PublicationSearchPipeline.
    
    Follows AdvancedSearchPipeline pattern with feature toggles.
    """
    
    # Feature toggles (Week 1-2: Only PubMed)
    enable_pubmed: bool = True
    enable_scholar: bool = False      # Week 3
    enable_pmc: bool = False          # Week 3
    enable_citations: bool = False    # Week 3
    enable_pdf_download: bool = False # Week 4
    enable_fulltext: bool = False     # Week 4
    
    # Component configs
    pubmed_config: PubMedConfig = field(default_factory=PubMedConfig)
    
    # Ranking config
    ranking_weight_title: float = 0.4
    ranking_weight_abstract: float = 0.3
    ranking_weight_recency: float = 0.2
    ranking_weight_citations: float = 0.1
```

---

### **Day 2: PubMed Client (Base)**

#### **Task 2.1: Base publication client** (`clients/base.py`)

```python
"""
Base class for publication clients.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models import Publication


class BasePublicationClient(ABC):
    """
    Abstract base class for publication clients.
    
    All publication sources (PubMed, Scholar, PMC) implement this interface.
    """
    
    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Publication]:
        """
        Search for publications.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            filters: Optional filters (year, journal, etc.)
        
        Returns:
            List of Publication objects
        """
        pass
    
    @abstractmethod
    def get_by_id(self, publication_id: str) -> Optional[Publication]:
        """
        Get publication by ID.
        
        Args:
            publication_id: Publication identifier (PMID, DOI, etc.)
        
        Returns:
            Publication if found, None otherwise
        """
        pass
```

#### **Task 2.2: PubMed client implementation** (`clients/pubmed.py`)

```python
"""
PubMed client implementation.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from Bio import Entrez
from Bio import Medline

from .base import BasePublicationClient
from ..config import PubMedConfig
from ..models import Publication, PublicationType

logger = logging.getLogger(__name__)


class PubMedClient(BasePublicationClient):
    """
    PubMed client using Biopython Entrez.
    
    Provides access to PubMed database via NCBI E-utilities.
    """
    
    def __init__(self, config: PubMedConfig):
        """
        Initialize PubMed client.
        
        Args:
            config: PubMed configuration
        """
        self.config = config
        
        # Configure Entrez
        Entrez.email = config.email
        if config.api_key:
            Entrez.api_key = config.api_key
        
        logger.info(f"PubMed client initialized (email: {config.email})")
    
    def search(
        self,
        query: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Publication]:
        """
        Search PubMed for publications.
        
        Args:
            query: Search query (PubMed query syntax)
            max_results: Maximum number of results
            filters: Optional filters (year, journal, etc.)
        
        Returns:
            List of Publication objects
        """
        try:
            # Build search query
            search_query = self._build_query(query, filters)
            
            logger.info(f"Searching PubMed: {search_query}")
            
            # Search PubMed
            search_handle = Entrez.esearch(
                db="pubmed",
                term=search_query,
                retmax=max_results,
                sort="relevance"
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            pmids = search_results["IdList"]
            logger.info(f"Found {len(pmids)} PubMed IDs")
            
            if not pmids:
                return []
            
            # Fetch details
            publications = self._fetch_details(pmids)
            
            return publications
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    def get_by_id(self, publication_id: str) -> Optional[Publication]:
        """
        Get publication by PMID.
        
        Args:
            publication_id: PubMed ID
        
        Returns:
            Publication if found, None otherwise
        """
        try:
            publications = self._fetch_details([publication_id])
            return publications[0] if publications else None
        except Exception as e:
            logger.error(f"Failed to fetch PMID {publication_id}: {e}")
            return None
    
    def _build_query(self, query: str, filters: Optional[Dict[str, Any]]) -> str:
        """Build PubMed search query with filters"""
        query_parts = [query]
        
        if filters:
            if "year_min" in filters:
                query_parts.append(f"{filters['year_min']}[PDAT]:3000[PDAT]")
            if "year_max" in filters:
                query_parts.append(f"1900[PDAT]:{filters['year_max']}[PDAT]")
            if "journal" in filters:
                query_parts.append(f"{filters['journal']}[JOUR]")
        
        return " AND ".join(query_parts)
    
    def _fetch_details(self, pmids: List[str]) -> List[Publication]:
        """Fetch publication details for PMIDs"""
        publications = []
        
        try:
            # Rate limiting
            time.sleep(self.config.rate_limit_delay)
            
            # Fetch details
            fetch_handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="medline",
                retmode="text"
            )
            records = Medline.parse(fetch_handle)
            
            for record in records:
                pub = self._parse_medline_record(record)
                if pub:
                    publications.append(pub)
            
            fetch_handle.close()
            
        except Exception as e:
            logger.error(f"Failed to fetch details: {e}")
        
        return publications
    
    def _parse_medline_record(self, record: Dict) -> Optional[Publication]:
        """Parse Medline record into Publication"""
        try:
            # Parse publication date
            pub_date = None
            if "DP" in record:
                try:
                    pub_date = datetime.strptime(record["DP"][:4], "%Y")
                except:
                    pass
            
            # Determine publication type
            pub_type = PublicationType.JOURNAL_ARTICLE
            if "PT" in record:
                if "Review" in record["PT"]:
                    pub_type = PublicationType.REVIEW
            
            # Create Publication
            publication = Publication(
                pmid=record.get("PMID", ""),
                doi=record.get("AID", [None])[0] if "AID" in record else None,
                title=record.get("TI", ""),
                abstract=record.get("AB", ""),
                authors=record.get("AU", []),
                journal=record.get("TA", ""),
                publication_date=pub_date,
                publication_type=pub_type,
                keywords=record.get("MH", []),
                source="pubmed"
            )
            
            return publication
            
        except Exception as e:
            logger.error(f"Failed to parse record: {e}")
            return None
```

---

### **Day 3: Publication Ranking**

#### **Task 3.1: Publication ranker** (`ranking/ranker.py`)

```python
"""
Publication ranking and relevance scoring.
"""

import logging
from typing import List
from datetime import datetime

from ..models import Publication, PublicationSearchResult
from ..config import PublicationSearchConfig

logger = logging.getLogger(__name__)


class PublicationRanker:
    """
    Rank publications by relevance to query.
    
    Scoring factors:
    - Title match
    - Abstract match
    - Recency
    - Citation count
    """
    
    def __init__(self, config: PublicationSearchConfig):
        """Initialize ranker with config"""
        self.config = config
    
    def rank(
        self,
        publications: List[Publication],
        query: str
    ) -> List[PublicationSearchResult]:
        """
        Rank publications by relevance.
        
        Args:
            publications: Publications to rank
            query: Search query
        
        Returns:
            Ranked PublicationSearchResult list
        """
        results = []
        query_lower = query.lower()
        
        for pub in publications:
            score, reasons = self._calculate_score(pub, query_lower)
            
            results.append(PublicationSearchResult(
                publication=pub,
                relevance_score=score,
                match_reasons=reasons
            ))
        
        # Sort by score (descending)
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return results
    
    def _calculate_score(
        self,
        pub: Publication,
        query_lower: str
    ) -> tuple[float, List[str]]:
        """Calculate relevance score and match reasons"""
        score = 0.0
        reasons = []
        
        # 1. Title match (40% weight)
        if pub.title:
            title_lower = pub.title.lower()
            if query_lower in title_lower:
                title_score = 1.0
                reasons.append("Title contains query")
            else:
                # Partial match
                query_terms = query_lower.split()
                matches = sum(1 for term in query_terms if term in title_lower)
                title_score = matches / len(query_terms) if query_terms else 0
                if title_score > 0:
                    reasons.append(f"Title matches {matches}/{len(query_terms)} terms")
            
            score += title_score * self.config.ranking_weight_title
        
        # 2. Abstract match (30% weight)
        if pub.abstract:
            abstract_lower = pub.abstract.lower()
            if query_lower in abstract_lower:
                abstract_score = 1.0
                reasons.append("Abstract contains query")
            else:
                query_terms = query_lower.split()
                matches = sum(1 for term in query_terms if term in abstract_lower)
                abstract_score = matches / len(query_terms) if query_terms else 0
                if abstract_score > 0:
                    reasons.append(f"Abstract matches {matches}/{len(query_terms)} terms")
            
            score += abstract_score * self.config.ranking_weight_abstract
        
        # 3. Recency (20% weight)
        if pub.publication_date:
            current_year = datetime.now().year
            pub_year = pub.publication_date.year
            years_old = current_year - pub_year
            # Newer publications score higher (decay over 10 years)
            recency_score = max(0, 1 - (years_old / 10))
            score += recency_score * self.config.ranking_weight_recency
            if years_old <= 2:
                reasons.append(f"Recent ({pub_year})")
        
        # 4. Citation count (10% weight)
        if pub.citation_count > 0:
            # Normalize citation count (log scale, max 1000 citations = 1.0)
            import math
            citation_score = min(1.0, math.log(pub.citation_count + 1) / math.log(1001))
            score += citation_score * self.config.ranking_weight_citations
            reasons.append(f"{pub.citation_count} citations")
        
        # Ensure score is in [0, 1]
        score = max(0.0, min(1.0, score))
        
        return score, reasons
```

---

### **Day 4: Publication Pipeline**

#### **Task 4.1: PublicationSearchPipeline** (`pipeline.py`)

```python
"""
Publication search pipeline following golden pattern.
"""

import logging
from typing import List, Optional, Dict, Any

from .config import PublicationSearchConfig
from .models import PublicationResult, Publication
from .clients.pubmed import PubMedClient
from .ranking.ranker import PublicationRanker

logger = logging.getLogger(__name__)


class PublicationSearchPipeline:
    """
    Publication search pipeline following AdvancedSearchPipeline pattern.
    
    Features (toggle via config):
    - PubMed search (enable_pubmed) - Week 1-2
    - Google Scholar (enable_scholar) - Week 3
    - PMC full-text (enable_pmc) - Week 3
    - Citation analysis (enable_citations) - Week 3
    - PDF download (enable_pdf_download) - Week 4
    - Full-text extraction (enable_fulltext) - Week 4
    """
    
    def __init__(self, config: PublicationSearchConfig):
        """
        Initialize pipeline with conditional components.
        
        Args:
            config: Pipeline configuration with feature toggles
        """
        self.config = config
        
        # Conditional initialization based on feature toggles
        if config.enable_pubmed:
            self.pubmed_client = PubMedClient(config.pubmed_config)
            logger.info("PubMed client enabled")
        else:
            self.pubmed_client = None
            logger.info("PubMed client disabled")
        
        # Week 3 features (disabled for now)
        self.scholar_client = None
        self.pmc_client = None
        self.citation_analyzer = None
        
        # Week 4 features (disabled for now)
        self.pdf_downloader = None
        self.fulltext_extractor = None
        
        # Core component (always initialized)
        self.ranker = PublicationRanker(config)
        logger.info("PublicationRanker initialized")
    
    def search(
        self,
        query: str,
        max_results: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> PublicationResult:
        """
        Execute publication search with conditional features.
        
        Args:
            query: Search query
            max_results: Maximum results per source
            filters: Optional filters (year, journal, etc.)
        
        Returns:
            PublicationResult with ranked publications
        """
        logger.info(f"Publication search: {query}")
        
        publications = []
        
        # Step 1: Search PubMed (if enabled)
        if self.pubmed_client:
            logger.info("Searching PubMed...")
            pubmed_results = self.pubmed_client.search(
                query,
                max_results=max_results,
                filters=filters
            )
            publications.extend(pubmed_results)
            logger.info(f"PubMed returned {len(pubmed_results)} publications")
        
        # Step 2: Search Google Scholar (if enabled) - Week 3
        if self.scholar_client:
            logger.info("Searching Google Scholar...")
            scholar_results = self.scholar_client.search(query, max_results=max_results)
            publications.extend(scholar_results)
        
        # Step 3: Search PMC (if enabled) - Week 3
        if self.pmc_client:
            logger.info("Searching PMC...")
            pmc_results = self.pmc_client.search(query, max_results=max_results)
            publications.extend(pmc_results)
        
        # Step 4: Rank and deduplicate (always executed)
        logger.info(f"Ranking {len(publications)} publications...")
        ranked_results = self.ranker.rank(publications, query)
        
        # Step 5: Analyze citations (if enabled) - Week 3
        if self.citation_analyzer:
            logger.info("Analyzing citations...")
            ranked_results = self.citation_analyzer.analyze(ranked_results)
        
        # Step 6: Download PDFs (if enabled) - Week 4
        if self.pdf_downloader:
            logger.info("Downloading PDFs...")
            ranked_results = self.pdf_downloader.download(ranked_results)
        
        # Step 7: Extract full text (if enabled) - Week 4
        if self.fulltext_extractor:
            logger.info("Extracting full text...")
            ranked_results = self.fulltext_extractor.extract(ranked_results)
        
        # Build result
        result = PublicationResult(
            query=query,
            publications=ranked_results,
            total_found=len(ranked_results),
            sources_used=self._get_sources_used(),
            features_enabled=self._get_enabled_features()
        )
        
        logger.info(f"Publication search complete: {result.total_found} results")
        return result
    
    def _get_sources_used(self) -> List[str]:
        """Get list of enabled sources"""
        sources = []
        if self.pubmed_client:
            sources.append("pubmed")
        if self.scholar_client:
            sources.append("scholar")
        if self.pmc_client:
            sources.append("pmc")
        return sources
    
    def _get_enabled_features(self) -> List[str]:
        """Get list of enabled features"""
        features = []
        if self.citation_analyzer:
            features.append("citations")
        if self.pdf_downloader:
            features.append("pdf_download")
        if self.fulltext_extractor:
            features.append("fulltext")
        return features
```

---

### **Day 5: SearchAgent Integration**

#### **Task 5.1: Update SearchAgent** 

Add to `omics_oracle_v2/agents/search_agent.py`:

```python
# Add to imports
from ..lib.publications.pipeline import PublicationSearchPipeline
from ..lib.publications.config import PublicationSearchConfig

# Update __init__
def __init__(
    self,
    settings: Settings,
    enable_semantic: bool = False,
    enable_publications: bool = False  # NEW
):
    super().__init__(settings, agent_name="SearchAgent")
    self.enable_semantic = enable_semantic
    self.enable_publications = enable_publications  # NEW

# Update _initialize_resources
def _initialize_resources(self) -> None:
    # ... existing code ...
    
    # NEW: Optional publication pipeline
    if self.enable_publications:
        pub_config = PublicationSearchConfig(
            pubmed_config=PubMedConfig(
                email=self.settings.ncbi_email,
                api_key=self.settings.ncbi_api_key
            )
        )
        self.publication_pipeline = PublicationSearchPipeline(pub_config)
        logger.info("Publication pipeline enabled")
    else:
        self.publication_pipeline = None
```

---

### **Days 6-7: Testing**

#### **Task 6.1: Unit tests** (`tests/lib/publications/test_pubmed_client.py`)

```python
"""Tests for PubMed client"""

import pytest
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.publications.config import PubMedConfig


@pytest.fixture
def pubmed_config():
    return PubMedConfig(email="test@example.com")


@pytest.fixture
def pubmed_client(pubmed_config):
    return PubMedClient(pubmed_config)


def test_pubmed_search(pubmed_client):
    """Test PubMed search"""
    results = pubmed_client.search("cancer genomics", max_results=10)
    
    assert len(results) > 0
    assert all(pub.source == "pubmed" for pub in results)
    assert all(pub.pmid for pub in results)


def test_pubmed_get_by_id(pubmed_client):
    """Test get publication by PMID"""
    pub = pubmed_client.get_by_id("34000000")
    
    assert pub is not None
    assert pub.pmid == "34000000"
    assert pub.title
```

#### **Task 6.2: Pipeline tests** (`tests/lib/publications/test_pipeline.py`)

```python
"""Tests for PublicationSearchPipeline"""

import pytest
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig


@pytest.fixture
def pipeline_config():
    return PublicationSearchConfig(
        enable_pubmed=True,
        pubmed_config=PubMedConfig(email="test@example.com")
    )


@pytest.fixture
def pipeline(pipeline_config):
    return PublicationSearchPipeline(pipeline_config)


def test_pipeline_search(pipeline):
    """Test pipeline search"""
    result = pipeline.search("breast cancer genomics", max_results=10)
    
    assert result.total_found > 0
    assert len(result.publications) > 0
    assert "pubmed" in result.sources_used
    assert all(p.relevance_score >= 0 and p.relevance_score <= 1 for p in result.publications)


def test_pipeline_feature_toggles():
    """Test feature toggles"""
    # Disabled PubMed
    config = PublicationSearchConfig(enable_pubmed=False)
    pipeline = PublicationSearchPipeline(config)
    
    assert pipeline.pubmed_client is None
    
    result = pipeline.search("test")
    assert result.total_found == 0
    assert len(result.sources_used) == 0
```

---

### **Days 8-9: Integration & Documentation**

#### **Task 8.1: Integration test**

```python
"""Integration test with SearchAgent"""

def test_search_agent_with_publications():
    """Test SearchAgent with publications enabled"""
    settings = Settings(
        ncbi_email="test@example.com",
        ncbi_api_key="test-key"
    )
    
    agent = SearchAgent(
        settings,
        enable_semantic=False,
        enable_publications=True
    )
    
    agent.initialize()
    
    search_input = SearchInput(
        search_terms=["breast cancer", "genomics"],
        original_query="breast cancer genomics studies"
    )
    
    result = agent.execute(search_input)
    
    assert result.success
    assert result.output is not None
```

#### **Task 8.2: Update documentation**

Create `docs/guides/PUBLICATIONS_MODULE.md` with:
- Module overview
- Configuration guide
- Usage examples
- API reference

---

### **Day 10: Deployment & Validation**

#### **Task 10.1: Configuration**

Update `config/development.yml`:

```yaml
search_agent:
  enable_semantic: true
  enable_publications: true  # NEW
  
  publications_config:
    enable_pubmed: true
    enable_scholar: false
    enable_citations: false
    
    pubmed_config:
      email: ${NCBI_EMAIL}
      api_key: ${NCBI_API_KEY}
      max_results: 50
```

#### **Task 10.2: Deploy & validate**

```bash
# Run all tests
pytest tests/lib/publications/ -v

# Start development server
./start_dev_server.sh

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "breast cancer genomics",
    "enable_publications": true,
    "max_results": 20
  }'
```

---

## ✅ Completion Checklist

### **Code Complete**
- [ ] Module structure created
- [ ] Data models implemented (`models.py`)
- [ ] Configuration implemented (`config.py`)
- [ ] Base client implemented (`clients/base.py`)
- [ ] PubMed client implemented (`clients/pubmed.py`)
- [ ] Ranker implemented (`ranking/ranker.py`)
- [ ] Pipeline implemented (`pipeline.py`)
- [ ] SearchAgent integration complete

### **Tests Complete**
- [ ] PubMed client tests passing
- [ ] Ranker tests passing
- [ ] Pipeline tests passing
- [ ] Integration tests passing
- [ ] All tests ≥80% coverage

### **Documentation Complete**
- [ ] Module documentation (`PUBLICATIONS_MODULE.md`)
- [ ] API reference
- [ ] Configuration guide
- [ ] Usage examples

### **Deployment Complete**
- [ ] Configuration updated
- [ ] Feature toggle working
- [ ] Production deployment
- [ ] Validation tests passing

---

## 🎯 Success Metrics

### **Functionality**
- ✅ PubMed search returns relevant publications
- ✅ Ranking algorithm produces good relevance scores
- ✅ Feature toggle (`enable_publications`) works correctly
- ✅ Integration with SearchAgent seamless

### **Performance**
- ✅ PubMed queries complete in <2 seconds
- ✅ Ranking completes in <500ms for 50 publications
- ✅ Memory usage <100MB for pipeline

### **Quality**
- ✅ Test coverage ≥80%
- ✅ No critical bugs
- ✅ Code passes linting
- ✅ Documentation complete

---

## 📚 Next Phase

After Week 1-2 completion, proceed to:

**Week 3: Enhanced Publications**
- Add Google Scholar client
- Add citation analysis
- Enable `enable_scholar` and `enable_citations` toggles

See: `WEEK_3_ENHANCED_PUBLICATIONS_IMPLEMENTATION.md`
