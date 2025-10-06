# Week 3 Implementation Plan: Google Scholar + Citation Analysis

**Goal:** Increase coverage from 90% → 95%+ by adding Google Scholar and citation metrics

**Timeline:** 10 days (Days 11-20)  
**Branch:** phase-4-production-features  
**Dependencies:** Week 1-2 complete ✅

---

## Overview

### Current State (Week 1-2)
```python
PublicationSearchConfig(
    enable_pubmed=True,           # ✅ Implemented
    enable_scholar=False,          # ⏳ Week 3
    enable_citations=False,        # ⏳ Week 3
    enable_pdf_download=False,     # 📅 Week 4
    enable_fulltext=False,         # 📅 Week 4
    enable_institutional_access=True  # ✅ Implemented
)

# Current coverage: 90%
# - PubMed: 35M+ articles
# - Institutional access: GT + ODU
```

### Week 3 Goals
```python
PublicationSearchConfig(
    enable_pubmed=True,           # ✅ Already working
    enable_scholar=True,          # 🎯 Week 3 - NEW
    enable_citations=True,        # 🎯 Week 3 - NEW
    enable_pdf_download=False,     # 📅 Week 4
    enable_fulltext=False,         # 📅 Week 4
    enable_institutional_access=True  # ✅ Already working
)

# Week 3 coverage: 95%+
# - PubMed: 35M+ articles
# - Google Scholar: Additional preprints, conference papers, theses
# - Citations: Paper influence metrics
# - Institutional access: GT + ODU
```

---

## Week 3 Architecture

### New Components

```
omics_oracle_v2/lib/publications/
├── clients/
│   ├── base.py                    # ✅ Already exists
│   ├── pubmed.py                  # ✅ Already exists
│   ├── institutional_access.py    # ✅ Already exists
│   ├── scholar.py                 # 🆕 Week 3 Day 11-13
│   └── citations.py               # 🆕 Week 3 Day 14-16
├── ranking/
│   └── ranker.py                  # 🔄 Update for citation metrics
├── config.py                      # 🔄 Add Scholar + Citation configs
├── pipeline.py                    # 🔄 Integrate new clients
└── models.py                      # 🔄 Add citation fields
```

---

## Implementation Timeline

### Days 11-13: Google Scholar Client (3 days)

#### Day 11: Scholar Client Foundation
**File:** `omics_oracle_v2/lib/publications/clients/scholar.py`

**Implementation:**
```python
from typing import List, Optional
from scholarly import scholarly
import time

from ..models import Publication, PublicationSource
from .base import BasePublicationClient

class GoogleScholarClient(BasePublicationClient):
    """
    Google Scholar client using scholarly library.
    
    Provides:
    - Broader coverage (preprints, conference papers, theses)
    - Citation counts
    - Related papers
    - Author profiles
    
    Rate Limits:
    - No official API (web scraping)
    - Recommended: 1 request per 3-5 seconds
    - Use proxies for higher volume
    """
    
    def __init__(self, config: GoogleScholarConfig):
        super().__init__()
        self.config = config
        self._rate_limiter = RateLimiter(
            calls_per_second=1/3  # 1 call every 3 seconds
        )
        
    def search(
        self, 
        query: str, 
        max_results: int = 50,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None
    ) -> List[Publication]:
        """Search Google Scholar."""
        pass
        
    def fetch_by_doi(self, doi: str) -> Optional[Publication]:
        """Fetch single paper by DOI."""
        pass
        
    def get_citations(self, publication: Publication) -> int:
        """Get citation count for a paper."""
        pass
```

**Config Update:**
```python
# config.py
class GoogleScholarConfig(BaseModel):
    """Google Scholar client configuration."""
    
    enable: bool = False
    max_results: int = 50
    rate_limit_seconds: float = 3.0
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    timeout_seconds: int = 30
```

**Tasks:**
- [ ] Create `scholar.py` with base structure
- [ ] Implement `scholarly` library integration
- [ ] Add rate limiting (1 req/3s)
- [ ] Add error handling
- [ ] Update `config.py` with `GoogleScholarConfig`

#### Day 12: Scholar Search Implementation
**Focus:** Core search functionality

**Implementation:**
```python
def search(self, query: str, max_results: int = 50) -> List[Publication]:
    """Search Google Scholar with rate limiting."""
    self.logger.info(f"Searching Scholar: '{query}', max={max_results}")
    
    try:
        with self._rate_limiter:
            # Search using scholarly
            search_query = scholarly.search_pubs(query)
            
            publications = []
            for i, result in enumerate(search_query):
                if i >= max_results:
                    break
                    
                # Parse result into Publication model
                pub = self._parse_scholar_result(result)
                publications.append(pub)
                
                # Rate limit between results
                time.sleep(self.config.rate_limit_seconds)
            
            self.logger.info(f"Found {len(publications)} publications")
            return publications
            
    except Exception as e:
        self.logger.error(f"Scholar search failed: {e}")
        raise PublicationSearchError(f"Failed to search Scholar: {e}")


def _parse_scholar_result(self, result: dict) -> Publication:
    """Convert Scholar result to Publication model."""
    return Publication(
        title=result.get('bib', {}).get('title', ''),
        abstract=result.get('bib', {}).get('abstract', ''),
        authors=self._parse_authors(result.get('bib', {}).get('author', [])),
        journal=result.get('bib', {}).get('venue', ''),
        publication_date=self._parse_date(result.get('bib', {}).get('pub_year')),
        doi=result.get('doi'),
        citations=result.get('num_citations', 0),
        source=PublicationSource.SCHOLAR,
        metadata={
            'scholar_url': result.get('url_pdf'),
            'scholar_id': result.get('scholar_id'),
            'eprint_url': result.get('eprint_url'),
        }
    )
```

**Tasks:**
- [ ] Implement `search()` method
- [ ] Implement `_parse_scholar_result()`
- [ ] Add author parsing
- [ ] Add date parsing
- [ ] Test with real Scholar searches

#### Day 13: Scholar Integration + Testing
**Focus:** Integration and unit tests

**Pipeline Update:**
```python
# pipeline.py
def _initialize_clients(self):
    """Initialize all enabled clients."""
    # Existing PubMed
    if self.config.enable_pubmed:
        self.pubmed_client = PubMedClient(self.config.pubmed_config)
    
    # NEW - Google Scholar
    if self.config.enable_scholar:
        self.scholar_client = GoogleScholarClient(self.config.scholar_config)
        self.logger.info("Google Scholar client initialized")


def search(self, query: str, max_results: int = 50) -> PublicationSearchResult:
    """Search all enabled sources."""
    all_publications = []
    sources_used = []
    
    # PubMed search
    if self.pubmed_client:
        pubmed_pubs = self.pubmed_client.search(query, max_results)
        all_publications.extend(pubmed_pubs)
        sources_used.append('pubmed')
    
    # NEW - Scholar search
    if self.scholar_client:
        scholar_pubs = self.scholar_client.search(query, max_results)
        all_publications.extend(scholar_pubs)
        sources_used.append('scholar')
    
    # Deduplicate (DOI + title matching)
    unique_pubs = self._deduplicate(all_publications)
    
    # Rank
    ranked_pubs = self.ranker.rank(unique_pubs, query, top_k=max_results)
    
    return PublicationSearchResult(
        query=query,
        publications=ranked_pubs,
        total_found=len(unique_pubs),
        metadata={
            'sources_used': sources_used,
            # ...
        }
    )
```

**Tests:**
```python
# tests/lib/publications/test_scholar_client.py
def test_scholar_search():
    """Test Scholar search."""
    config = GoogleScholarConfig(enable=True)
    client = GoogleScholarClient(config)
    
    results = client.search("CRISPR cancer", max_results=5)
    
    assert len(results) > 0
    assert all(pub.source == PublicationSource.SCHOLAR for pub in results)


def test_scholar_rate_limiting():
    """Test rate limiting."""
    # Ensure 3 second delay between requests
    pass
```

**Tasks:**
- [ ] Integrate Scholar client into pipeline
- [ ] Update deduplication (DOI + title fuzzy matching)
- [ ] Create `test_scholar_client.py`
- [ ] Test multi-source search (PubMed + Scholar)
- [ ] Verify rate limiting

---

### Days 14-16: Citation Analysis (3 days)

#### Day 14: Citation Analyzer Foundation
**File:** `omics_oracle_v2/lib/publications/clients/citations.py`

**Implementation:**
```python
from typing import Dict, List
from datetime import datetime

from ..models import Publication, CitationMetrics

class CitationAnalyzer:
    """
    Analyzes citation metrics for publications.
    
    Provides:
    - Citation count
    - Citation velocity (citations per year)
    - h-index influence
    - Relative citation ratio (RCR)
    - Field-normalized metrics
    """
    
    def __init__(self, config: CitationAnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, publication: Publication) -> CitationMetrics:
        """Analyze citation metrics for a publication."""
        pass
        
    def batch_analyze(self, publications: List[Publication]) -> Dict[str, CitationMetrics]:
        """Analyze multiple publications."""
        pass
        
    def get_citation_velocity(self, publication: Publication) -> float:
        """Calculate citations per year."""
        pass
        
    def get_relative_citation_ratio(self, publication: Publication) -> float:
        """Calculate field-normalized RCR."""
        pass
```

**Model Update:**
```python
# models.py
class CitationMetrics(BaseModel):
    """Citation analysis metrics."""
    
    citation_count: int = 0
    citation_velocity: float = 0.0  # Citations per year
    h_index: Optional[int] = None
    relative_citation_ratio: Optional[float] = None  # Field-normalized
    percentile: Optional[float] = None  # Compared to similar papers
    
    # Temporal
    citations_recent_year: int = 0
    citations_peak_year: Optional[int] = None
    
    # Influence
    influential_citations: int = 0  # Highly influential citations
    self_citations: int = 0
    
    # Sources
    citation_sources: Dict[str, int] = Field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)


class Publication(BaseModel):
    # ... existing fields ...
    
    # NEW - Citation metrics
    citation_metrics: Optional[CitationMetrics] = None
```

**Tasks:**
- [ ] Create `citations.py` with base structure
- [ ] Add `CitationMetrics` to `models.py`
- [ ] Update `Publication` model
- [ ] Implement basic citation analysis

#### Day 15: Citation Metrics Implementation
**Focus:** Core metric calculations

**Implementation:**
```python
def analyze(self, publication: Publication) -> CitationMetrics:
    """Analyze all citation metrics."""
    
    # Get base citation count (from Scholar or PubMed)
    citation_count = publication.citations or 0
    
    # Calculate citation velocity
    velocity = self.get_citation_velocity(publication)
    
    # Calculate RCR (if available)
    rcr = self.get_relative_citation_ratio(publication)
    
    # Determine percentile
    percentile = self._calculate_percentile(publication)
    
    return CitationMetrics(
        citation_count=citation_count,
        citation_velocity=velocity,
        relative_citation_ratio=rcr,
        percentile=percentile,
        last_updated=datetime.now()
    )


def get_citation_velocity(self, publication: Publication) -> float:
    """Citations per year since publication."""
    if not publication.publication_date or not publication.citations:
        return 0.0
    
    years_since_pub = (datetime.now() - publication.publication_date).days / 365
    if years_since_pub < 0.1:  # Avoid division by zero
        return 0.0
    
    return publication.citations / years_since_pub


def get_relative_citation_ratio(self, publication: Publication) -> float:
    """
    Field-normalized RCR.
    
    RCR > 1.0: Above average for field
    RCR = 1.0: Average for field
    RCR < 1.0: Below average for field
    """
    # For Week 3, use simple normalization
    # Week 5: Use NIH iCite API for real RCR
    
    if not publication.citations or not publication.publication_date:
        return 1.0
    
    # Simple normalization by age
    years = (datetime.now() - publication.publication_date).days / 365
    if years < 1:
        expected = 5  # Expected citations in first year
    elif years < 3:
        expected = 15
    else:
        expected = 30
    
    return publication.citations / expected
```

**Tasks:**
- [ ] Implement `analyze()` method
- [ ] Implement `get_citation_velocity()`
- [ ] Implement `get_relative_citation_ratio()`
- [ ] Implement `batch_analyze()` for multiple papers
- [ ] Add percentile calculation

#### Day 16: Citation Integration + Testing
**Focus:** Integration with pipeline and ranking

**Pipeline Update:**
```python
# pipeline.py
def search(self, query: str, max_results: int = 50) -> PublicationSearchResult:
    """Search with citation analysis."""
    # ... existing search logic ...
    
    # NEW - Citation analysis
    if self.config.enable_citations and self.citation_analyzer:
        self.logger.info("Analyzing citations...")
        for pub in unique_pubs:
            pub.citation_metrics = self.citation_analyzer.analyze(pub)
    
    # Rank (now includes citation metrics)
    ranked_pubs = self.ranker.rank(unique_pubs, query, top_k=max_results)
    
    return result
```

**Ranker Update:**
```python
# ranking/ranker.py
def _calculate_citation_score(self, pub: Publication) -> float:
    """Score based on citation metrics."""
    if not pub.citation_metrics:
        return 0.5  # Neutral score
    
    metrics = pub.citation_metrics
    
    # Velocity score (0-1)
    velocity_score = min(metrics.citation_velocity / 50, 1.0)
    
    # RCR score (0-1)
    rcr_score = min(metrics.relative_citation_ratio or 0, 1.0)
    
    # Citation count score (0-1)
    count_score = min(metrics.citation_count / 500, 1.0)
    
    # Weighted combination
    return (
        0.4 * velocity_score +
        0.4 * rcr_score +
        0.2 * count_score
    )


def rank(self, publications: List[Publication], query: str, top_k: int = 50):
    """Rank with enhanced citation scoring."""
    for pub in publications:
        # ... existing scores ...
        
        # NEW - Citation score
        citation_score = self._calculate_citation_score(pub)
        total_score += self.config.ranking_weights.get('citations', 0.1) * citation_score
```

**Tests:**
```python
# tests/lib/publications/test_citations.py
def test_citation_velocity():
    """Test citation velocity calculation."""
    pass

def test_relative_citation_ratio():
    """Test RCR calculation."""
    pass

def test_citation_integration():
    """Test citation analysis in pipeline."""
    pass
```

**Tasks:**
- [ ] Integrate citation analyzer into pipeline
- [ ] Update ranker with citation scoring
- [ ] Create `test_citations.py`
- [ ] Test end-to-end with citations
- [ ] Verify ranking improvements

---

### Days 17-18: Multi-Source Deduplication (2 days)

#### Challenge
With PubMed + Scholar, same papers appear multiple times:
- PubMed: Official records
- Scholar: May include preprints, duplicates

#### Solution: Smart Deduplication

**Implementation:**
```python
# pipeline.py
def _deduplicate(self, publications: List[Publication]) -> List[Publication]:
    """
    Deduplicate across multiple sources.
    
    Priority:
    1. PubMed (official records)
    2. Scholar (additional metadata, citations)
    
    Matching:
    - DOI exact match
    - Title fuzzy match (>90% similarity)
    - PMID match
    """
    from difflib import SequenceMatcher
    
    unique_pubs = {}
    
    for pub in publications:
        # Match by DOI
        if pub.doi:
            key = f"doi:{pub.doi}"
            if key in unique_pubs:
                # Merge metadata (keep PubMed, add Scholar citations)
                unique_pubs[key] = self._merge_publications(unique_pubs[key], pub)
                continue
        
        # Match by PMID
        if pub.pmid:
            key = f"pmid:{pub.pmid}"
            if key in unique_pubs:
                unique_pubs[key] = self._merge_publications(unique_pubs[key], pub)
                continue
        
        # Match by title fuzzy match
        title_key = None
        for existing_key, existing_pub in unique_pubs.items():
            similarity = SequenceMatcher(None, 
                pub.title.lower(), 
                existing_pub.title.lower()
            ).ratio()
            
            if similarity > 0.9:  # 90% similar
                title_key = existing_key
                break
        
        if title_key:
            unique_pubs[title_key] = self._merge_publications(unique_pubs[title_key], pub)
        else:
            # New unique publication
            key = pub.doi or pub.pmid or pub.title
            unique_pubs[key] = pub
    
    return list(unique_pubs.values())


def _merge_publications(self, primary: Publication, secondary: Publication) -> Publication:
    """
    Merge two publications (same paper, different sources).
    
    Strategy:
    - Keep PubMed as primary (official metadata)
    - Add Scholar citations if higher
    - Combine metadata
    """
    # Prefer PubMed metadata
    if primary.source == PublicationSource.PUBMED:
        merged = primary
        # Add Scholar citation count if higher
        if secondary.citations and secondary.citations > (primary.citations or 0):
            merged.citations = secondary.citations
    else:
        merged = primary
    
    # Merge metadata
    merged.metadata = {**primary.metadata, **secondary.metadata}
    
    return merged
```

**Tasks:**
- [ ] Implement DOI-based deduplication
- [ ] Implement PMID-based deduplication
- [ ] Implement title fuzzy matching
- [ ] Implement publication merging
- [ ] Test deduplication with PubMed + Scholar results

---

### Days 19-20: Testing + Documentation (2 days)

#### Day 19: Integration Testing
**Focus:** End-to-end testing with all components

**Tests:**
```python
# tests/lib/publications/test_week3_integration.py
def test_multi_source_search():
    """Test PubMed + Scholar search."""
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=True,
        enable_citations=True,
        enable_institutional_access=True,
        pubmed_config=PubMedConfig(email="test@example.com"),
        scholar_config=GoogleScholarConfig(enable=True)
    )
    
    pipeline = PublicationSearchPipeline(config)
    result = pipeline.search("CRISPR cancer therapy", max_results=20)
    
    # Verify multi-source
    assert 'pubmed' in result.metadata['sources_used']
    assert 'scholar' in result.metadata['sources_used']
    
    # Verify deduplication
    dois = [pub.publication.doi for pub in result.publications if pub.publication.doi]
    assert len(dois) == len(set(dois))  # No duplicate DOIs
    
    # Verify citations
    assert all(pub.publication.citation_metrics for pub in result.publications)
    
    # Verify ranking considers citations
    # Higher cited papers should rank higher (all else equal)
    pass


def test_coverage_improvement():
    """Verify coverage improved from Week 1-2."""
    # Week 1-2: PubMed only
    config_week1 = PublicationSearchConfig(enable_pubmed=True)
    pipeline_week1 = PublicationSearchPipeline(config_week1)
    result_week1 = pipeline_week1.search("genomics", max_results=100)
    
    # Week 3: PubMed + Scholar
    config_week3 = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=True
    )
    pipeline_week3 = PublicationSearchPipeline(config_week3)
    result_week3 = pipeline_week3.search("genomics", max_results=100)
    
    # Week 3 should find more unique papers
    assert result_week3.total_found >= result_week1.total_found
```

**Tasks:**
- [ ] Create integration test suite
- [ ] Test multi-source search
- [ ] Test deduplication accuracy
- [ ] Test citation analysis
- [ ] Benchmark performance

#### Day 20: Documentation + Deployment Prep
**Focus:** Documentation and production readiness

**Documentation:**
```markdown
# docs/planning/WEEK_3_COMPLETE.md

## Week 3 Implementation Summary

### Goals Achieved ✅
- Google Scholar integration
- Citation analysis
- Multi-source deduplication
- Coverage: 90% → 95%+

### Components Delivered
1. GoogleScholarClient (250 lines)
2. CitationAnalyzer (200 lines)
3. Enhanced deduplication (150 lines)
4. Updated ranker with citations
5. 45 new unit tests

### Coverage Breakdown
- PubMed: 35M+ articles (peer-reviewed)
- Google Scholar: +preprints, conference papers, theses
- Total: 95%+ of relevant literature

### Citation Metrics
- Citation count
- Citation velocity (citations/year)
- Relative citation ratio (field-normalized)
- Percentile ranking

### Usage Example
```python
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_scholar=True,
    enable_citations=True,
    enable_institutional_access=True
)

pipeline = PublicationSearchPipeline(config)
result = pipeline.search("machine learning genomics", max_results=50)

for pub_result in result.publications[:10]:
    pub = pub_result.publication
    metrics = pub.citation_metrics
    
    print(f"{pub.title}")
    print(f"  Citations: {metrics.citation_count}")
    print(f"  Velocity: {metrics.citation_velocity:.1f} citations/year")
    print(f"  RCR: {metrics.relative_citation_ratio:.2f}")
    print(f"  Percentile: {metrics.percentile}%")
```

**Tasks:**
- [ ] Create WEEK_3_COMPLETE.md
- [ ] Update ARCHITECTURE.md
- [ ] Update API_REFERENCE.md
- [ ] Create citation analysis guide
- [ ] Update requirements.txt (add `scholarly`)

---

## Dependencies

### New Python Packages
```txt
# Week 3 additions to requirements.txt
scholarly>=1.7.11    # Google Scholar scraping
fuzzywuzzy>=0.18.0  # Title fuzzy matching
python-Levenshtein>=0.21.0  # Faster string matching
```

### Installation
```bash
pip install scholarly fuzzywuzzy python-Levenshtein
```

---

## Expected Outcomes

### Metrics
- **Coverage:** 90% → 95%+
- **Sources:** PubMed → PubMed + Scholar
- **Citation Analysis:** Complete metrics for all papers
- **Deduplication:** <1% duplicate rate
- **Performance:** <10s for 50 results

### Quality
- **Architecture:** Golden pattern maintained
- **Testing:** 85%+ test coverage
- **Documentation:** Complete guides
- **Integration:** Zero breaking changes

### User Experience
```python
# Before (Week 1-2)
result = pipeline.search("CRISPR cancer")
# Returns: 45 papers (PubMed only)

# After (Week 3)
result = pipeline.search("CRISPR cancer")
# Returns: 68 papers (PubMed + Scholar, deduplicated)
# Each with citation metrics
```

---

## Risk Mitigation

### Google Scholar Rate Limits
- **Risk:** Scholar blocks frequent requests
- **Mitigation:** 
  - Rate limiting (1 req/3s)
  - Caching results
  - Optional proxy support
  - Fallback to PubMed only

### Citation Data Quality
- **Risk:** Scholar citations may be inaccurate
- **Mitigation:**
  - Cross-reference with PubMed when possible
  - Field normalization (RCR)
  - Clear metadata about source

### Deduplication Errors
- **Risk:** False positives/negatives
- **Mitigation:**
  - Multi-strategy matching (DOI + PMID + title)
  - Conservative thresholds (90% similarity)
  - Merge strategy preserves all metadata
  - Test suite validates accuracy

---

## Success Criteria

### Must Have (Week 3)
- ✅ Google Scholar client functional
- ✅ Citation analysis working
- ✅ Multi-source deduplication accurate
- ✅ Coverage ≥95%
- ✅ Tests passing ≥85%
- ✅ Zero breaking changes

### Nice to Have
- ⭐ Citation network visualization
- ⭐ Author profile integration
- ⭐ Proxy rotation for Scholar
- ⭐ Advanced RCR from NIH iCite API

### Week 4 Preview
- PDF download automation
- Full-text extraction (GROBID)
- Cookie-based institutional access
- Batch processing

---

## Next Session Handoff

**If implementation incomplete, continue from:**
1. Day 11: Start with GoogleScholarClient
2. Check `scholarly` library installation
3. Follow implementation timeline above
4. Run tests after each component
5. Document as you go

**Branch:** `phase-4-production-features`  
**Starting Point:** Week 1-2 complete, validation passed  
**Timeline:** 10 days total for Week 3
