# Full-Text Access Enhancement Plan
**For Academic Research Purposes Only**

**Created**: October 9, 2025
**Objective**: Increase full-text coverage from 40-50% to 70-90% using primarily legal sources

---

## 📊 Current State Assessment

### ✅ What We Already Have

| Component | Status | Coverage | Notes |
|-----------|--------|----------|-------|
| **PDFDownloader** | ✅ Implemented | - | Batch downloads, retry logic, validation |
| **FullTextExtractor** | ✅ Implemented | - | pdfplumber, PyPDF2, HTML extraction |
| **InstitutionalAccess** | ✅ Implemented | 20-30% | Georgia Tech VPN, ODU EZProxy |
| **Unpaywall (built-in)** | ✅ Implemented | 10-15% | Via institutional_access.py |
| **PMC Access** | ✅ Implemented | 15-20% | Via PubMed client |
| **OpenAlex** | ✅ Implemented | - | Has OA URL metadata! |

**Current Total Coverage**: ~40-50% (legal sources only)

### 🔍 Key Findings from Code Review

1. **Unpaywall Already Integrated**: `institutional_access.py` has `_try_unpaywall()` method
2. **OpenAlex Has OA URLs**: Stores `oa_url` and `is_open_access` in metadata
3. **PDF Infrastructure Solid**: Concurrent downloads, deduplication, validation
4. **Missing**: Dedicated OA source clients (CORE, arXiv, bioRxiv, Crossref)

---

## 🎯 Enhancement Strategy (Legal-First Approach)

### Phase 1: Legal OA Source Expansion (PRIORITY)
**Goal**: +20-30% coverage, 100% legal, $0 cost
**Timeline**: 2 weeks
**Risk**: NONE

### Phase 2: Sci-Hub Fallback (OPTIONAL)
**Goal**: +30-40% additional coverage
**Timeline**: 3-4 weeks
**Risk**: Moderate-High (requires legal review)
**Status**: Only implement if Phase 1 insufficient

---

## 📋 Phase 1: Legal OA Enhancement (RECOMMENDED START)

### Week 1: New OA Source Clients

#### Task 1.1: CORE API Client (Days 1-2)
**Priority**: HIGH
**Expected Coverage**: +10-15%

**Implementation**:
```python
# File: omics_oracle_v2/lib/publications/clients/oa_sources/core_client.py

class COREClient(BasePublicationClient):
    """
    CORE (Connecting Open Access REpositories) API client.

    Coverage: 45M+ open access full texts
    API Docs: https://core.ac.uk/documentation/api
    Rate Limits: Free tier with API key
    """

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        super().__init__()

    async def get_fulltext_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get full text or PDF URL from CORE.

        Returns:
            {
                'downloadUrl': PDF URL,
                'fullText': Full text if available,
                'metadata': {...}
            }
        """
        url = f"{self.BASE_URL}/works/search"
        params = {
            'q': f'doi:"{doi}"',
            'api_key': self.api_key,
            'limit': 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        return data['results'][0]
        return None

    async def download_pdf(self, download_url: str, output_path: Path) -> bool:
        """Download PDF from CORE."""
        # Implementation here
        pass
```

**Tasks**:
- [ ] Sign up for free CORE API key: https://core.ac.uk/api-keys/register
- [ ] Implement `core_client.py` with async support
- [ ] Add DOI-based search
- [ ] Add title-based search (fallback)
- [ ] Add to `BasePublicationClient` family
- [ ] Write 5+ unit tests
- [ ] Test with 100 sample DOIs

**Integration Point**: Add to `FullTextManager` (to be created)

---

#### Task 1.2: arXiv API Client (Days 2-3)
**Priority**: MEDIUM
**Expected Coverage**: +3-5% (mostly CS/physics/math)

**Implementation**:
```python
# File: omics_oracle_v2/lib/publications/clients/oa_sources/arxiv_client.py

class ArXivClient(BasePublicationClient):
    """
    arXiv preprint repository API client.

    Coverage: 2M+ preprints (physics, CS, math, some bio)
    API Docs: https://info.arxiv.org/help/api/index.html
    Rate Limits: 1 request/3 seconds (no API key needed)
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    async def search_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Get preprint by arXiv ID.

        Example: arxiv_id = "2301.12345"
        """
        params = {
            'id_list': arxiv_id,
            'max_results': 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    feed = feedparser.parse(await response.text())
                    if feed.entries:
                        entry = feed.entries[0]
                        return {
                            'title': entry.title,
                            'pdf_url': entry.link.replace('/abs/', '/pdf/') + '.pdf',
                            'abstract': entry.summary,
                            'published': entry.published,
                            'authors': [a.name for a in entry.authors]
                        }
        return None

    async def search_by_title(self, title: str) -> Optional[Dict]:
        """Search by title (fuzzy matching)."""
        # Implementation here
        pass
```

**Tasks**:
- [ ] Implement `arxiv_client.py`
- [ ] Add arXiv ID extraction from metadata
- [ ] Add title-based search
- [ ] Handle rate limiting (1 req/3s)
- [ ] Write 3+ unit tests
- [ ] Test with known arXiv papers

**Note**: arXiv IDs can be in publication metadata, DOIs (10.48550/arXiv.*), or URLs

---

#### Task 1.3: bioRxiv/medRxiv Client (Days 3-4)
**Priority**: HIGH
**Expected Coverage**: +2-3% (biomedical preprints)

**Implementation**:
```python
# File: omics_oracle_v2/lib/publications/clients/oa_sources/biorxiv_client.py

class BioRxivClient(BasePublicationClient):
    """
    bioRxiv and medRxiv preprint repository client.

    Coverage: 200K+ biomedical preprints
    API Docs: https://api.biorxiv.org/
    Rate Limits: None specified (be polite)
    """

    BASE_URL = "https://api.biorxiv.org/details"

    async def get_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get preprint by DOI.

        bioRxiv DOIs: 10.1101/*
        medRxiv DOIs: 10.1101/* (same prefix)
        """
        if not doi.startswith("10.1101/"):
            return None  # Not a bioRxiv/medRxiv DOI

        # Try bioRxiv first
        for server in ["biorxiv", "medrxiv"]:
            url = f"{self.BASE_URL}/{server}/{doi}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('collection'):
                            paper = data['collection'][0]
                            return {
                                'title': paper['title'],
                                'pdf_url': f"https://www.biorxiv.org/content/{doi}v1.full.pdf",
                                'abstract': paper['abstract'],
                                'date': paper['date'],
                                'server': server
                            }
        return None
```

**Tasks**:
- [ ] Implement `biorxiv_client.py`
- [ ] Add DOI-based lookup (10.1101/*)
- [ ] Try both bioRxiv and medRxiv servers
- [ ] Handle PDF URL generation
- [ ] Write 3+ unit tests
- [ ] Test with known bioRxiv papers

---

#### Task 1.4: Enhance OpenAlex Integration (Day 4)
**Priority**: HIGH
**Expected Coverage**: +5-10% (leveraging existing metadata)

**Enhancement**:
```python
# Update: omics_oracle_v2/lib/publications/clients/openalex.py

class OpenAlexClient(BasePublicationClient):
    # ... existing code ...

    def get_oa_pdf_url(self, publication: Publication) -> Optional[str]:
        """
        Extract OA PDF URL from OpenAlex metadata.

        Uses existing metadata already fetched during search/enrichment.
        """
        if not publication.metadata:
            return None

        # Check if we have OA URL in metadata
        oa_url = publication.metadata.get('oa_url')
        is_oa = publication.metadata.get('is_open_access', False)

        if is_oa and oa_url:
            # Check if it's a direct PDF
            if oa_url.endswith('.pdf'):
                return oa_url

            # Check if it's a known PDF pattern
            if 'europepmc.org' in oa_url:
                # Convert to PDF URL
                return oa_url.replace('/articles/', '/articles/pdf/')

            # Return landing page (can extract PDF from there)
            return oa_url

        return None

    async def fetch_oa_pdf(self, publication: Publication) -> Optional[bytes]:
        """Download OA PDF from OpenAlex metadata."""
        pdf_url = self.get_oa_pdf_url(publication)
        if not pdf_url:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status == 200:
                    return await response.read()
        return None
```

**Tasks**:
- [ ] Add `get_oa_pdf_url()` method
- [ ] Add `fetch_oa_pdf()` method
- [ ] Handle different OA URL types (PDF, landing page, Europe PMC)
- [ ] Update `enrich_publication()` to extract PDF URLs
- [ ] Write 3+ unit tests
- [ ] Test with OpenAlex OA papers

---

#### Task 1.5: Crossref Full-Text Links (Day 5)
**Priority**: MEDIUM
**Expected Coverage**: +2-3%

**Implementation**:
```python
# File: omics_oracle_v2/lib/publications/clients/oa_sources/crossref_client.py

class CrossrefClient(BasePublicationClient):
    """
    Crossref API for publisher full-text links.

    Coverage: 130M+ records, some with full-text links
    API Docs: https://api.crossref.org/
    Rate Limits: Polite pool (faster) with email in User-Agent
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, email: str):
        self.email = email
        super().__init__()

    async def get_fulltext_links(self, doi: str) -> List[str]:
        """
        Get full-text links from Crossref metadata.

        Returns list of URLs (PDF, HTML, XML).
        """
        url = f"{self.BASE_URL}/{doi}"
        headers = {
            'User-Agent': f'OmicsOracle/2.0 (mailto:{self.email})'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get('message', {})

                    links = []

                    # Extract link elements
                    if message.get('link'):
                        for link in message['link']:
                            content_type = link.get('content-type', '')
                            if 'pdf' in content_type or 'html' in content_type:
                                links.append(link['URL'])

                    # Check for license (indicates OA)
                    if message.get('license') and message.get('URL'):
                        links.append(message['URL'])

                    return links

        return []
```

**Tasks**:
- [ ] Implement `crossref_client.py`
- [ ] Extract full-text links from metadata
- [ ] Verify PDF accessibility
- [ ] Handle publisher variations
- [ ] Write 3+ unit tests

---

### Week 2: Integration & Orchestration

#### Task 2.1: Create FullTextManager (Days 6-7)
**Priority**: CRITICAL
**Purpose**: Orchestrate waterfall strategy across all sources

**Implementation**:
```python
# File: omics_oracle_v2/lib/publications/fulltext_manager.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

class FullTextSource(Enum):
    """Full-text sources in priority order."""
    INSTITUTIONAL = "institutional"      # Georgia Tech VPN, ODU EZProxy
    PMC = "pmc"                          # PubMed Central
    OPENALEX = "openalex"                # OpenAlex OA URLs
    UNPAYWALL = "unpaywall"              # Unpaywall (already in institutional)
    CORE = "core"                        # CORE aggregator
    BIORXIV = "biorxiv"                  # bioRxiv/medRxiv preprints
    CROSSREF = "crossref"                # Crossref publisher links
    ARXIV = "arxiv"                      # arXiv preprints
    # Future: SCIHUB_FALLBACK = "scihub_fallback"  # Phase 2 only


@dataclass
class FullTextResult:
    """Result of full-text acquisition."""

    success: bool
    source: Optional[FullTextSource] = None
    pdf_path: Optional[Path] = None
    full_text: Optional[str] = None
    metadata: dict = None
    attempts: List[dict] = None
    total_time: float = 0.0

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []
        if self.metadata is None:
            self.metadata = {}


class FullTextManager:
    """
    Intelligent full-text acquisition with waterfall strategy.

    Tries sources in priority order until success or exhaustion.

    Priority Order (Legal Sources Only):
    1. Institutional access (highest quality, Georgia Tech/ODU)
    2. PubMed Central (peer-reviewed, validated)
    3. OpenAlex OA URLs (comprehensive OA metadata)
    4. Unpaywall (OA discovery)
    5. CORE (large aggregator, 45M+ papers)
    6. bioRxiv/medRxiv (biomedical preprints)
    7. Crossref (publisher links)
    8. arXiv (CS/physics/math preprints)

    Future (Phase 2 - Requires Legal Review):
    9. Sci-Hub torrents (fallback only, opt-in required)
    """

    def __init__(self, config: FullTextConfig):
        self.config = config
        self.pdf_downloader = PDFDownloader(
            download_dir=Path(config.pdf_storage_path),
            institutional_manager=None  # Set below
        )

        # Initialize sources based on config
        self.sources = {}

        # Institutional access (Georgia Tech VPN, ODU EZProxy)
        if config.enable_institutional_access:
            from omics_oracle_v2.lib.publications.clients.institutional_access import (
                InstitutionalAccessManager, InstitutionType
            )
            institution = (
                InstitutionType.GEORGIA_TECH
                if config.primary_institution == "gatech"
                else InstitutionType.OLD_DOMINION
            )
            self.sources[FullTextSource.INSTITUTIONAL] = InstitutionalAccessManager(
                institution=institution
            )
            self.pdf_downloader.institutional_manager = self.sources[FullTextSource.INSTITUTIONAL]

        # PMC (built into PubMed client)
        if config.enable_pmc:
            # PMC access handled via PMCID in pdf_downloader
            self.sources[FullTextSource.PMC] = "built-in"

        # OpenAlex OA URLs
        if config.enable_openalex:
            from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient
            self.sources[FullTextSource.OPENALEX] = OpenAlexClient(
                config=config.openalex_config
            )

        # CORE
        if config.enable_core:
            from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREClient
            self.sources[FullTextSource.CORE] = COREClient(
                api_key=config.core_api_key
            )

        # bioRxiv/medRxiv
        if config.enable_biorxiv:
            from omics_oracle_v2.lib.publications.clients.oa_sources.biorxiv_client import BioRxivClient
            self.sources[FullTextSource.BIORXIV] = BioRxivClient()

        # Crossref
        if config.enable_crossref:
            from omics_oracle_v2.lib.publications.clients.oa_sources.crossref_client import CrossrefClient
            self.sources[FullTextSource.CROSSREF] = CrossrefClient(
                email=config.crossref_email
            )

        # arXiv
        if config.enable_arxiv:
            from omics_oracle_v2.lib.publications.clients.oa_sources.arxiv_client import ArXivClient
            self.sources[FullTextSource.ARXIV] = ArXivClient()

        logger.info(f"FullTextManager initialized with {len(self.sources)} sources")

    async def get_fulltext(
        self,
        publication: Publication,
        timeout: float = 30.0
    ) -> FullTextResult:
        """
        Try to acquire full text from all available sources.

        Args:
            publication: Publication to get full text for
            timeout: Maximum time to spend (seconds)

        Returns:
            FullTextResult with source and content
        """
        start_time = time.time()
        attempts = []

        # Try each source in priority order
        for source_type, client in self.sources.items():
            if time.time() - start_time > timeout:
                logger.warning(f"Timeout after {timeout}s")
                break

            try:
                logger.info(f"Trying {source_type.value}...")

                result = await self._try_source(
                    client, source_type, publication
                )

                attempts.append({
                    'source': source_type.value,
                    'success': result is not None,
                    'time': time.time() - start_time
                })

                if result:
                    logger.info(f"✓ Found in {source_type.value}")
                    return FullTextResult(
                        success=True,
                        source=source_type,
                        pdf_path=result.get('pdf_path'),
                        full_text=result.get('full_text'),
                        metadata=result.get('metadata', {}),
                        attempts=attempts,
                        total_time=time.time() - start_time
                    )

            except Exception as e:
                logger.error(f"Error in {source_type.value}: {e}")
                attempts.append({
                    'source': source_type.value,
                    'success': False,
                    'error': str(e),
                    'time': time.time() - start_time
                })

        # Not found
        logger.warning(
            f"Full text not found for {publication.title[:50]} "
            f"in {len(attempts)} sources"
        )
        return FullTextResult(
            success=False,
            attempts=attempts,
            total_time=time.time() - start_time
        )

    async def _try_source(
        self,
        client,
        source_type: FullTextSource,
        publication: Publication
    ) -> Optional[dict]:
        """Try to get full text from specific source."""

        # Different sources use different methods
        if source_type == FullTextSource.INSTITUTIONAL:
            # Already handled in pdf_downloader
            pdf_url = client.get_pdf_url(publication)
            if pdf_url:
                pdf_path = self.pdf_downloader.download(
                    pdf_url,
                    publication.pmid or publication.doi or publication.title[:50],
                    source="institutional"
                )
                if pdf_path:
                    return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.PMC:
            if publication.pmcid:
                pmc_pdf = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication.pmcid}/pdf/"
                pdf_path = self.pdf_downloader.download(
                    pmc_pdf,
                    publication.pmcid,
                    source="pmc"
                )
                if pdf_path:
                    return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.OPENALEX:
            pdf_url = client.get_oa_pdf_url(publication)
            if pdf_url:
                pdf_path = self.pdf_downloader.download(
                    pdf_url,
                    publication.doi or publication.title[:50],
                    source="openalex"
                )
                if pdf_path:
                    return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.CORE:
            if publication.doi:
                result = await client.get_fulltext_by_doi(publication.doi)
                if result and result.get('downloadUrl'):
                    pdf_path = self.pdf_downloader.download(
                        result['downloadUrl'],
                        publication.doi,
                        source="core"
                    )
                    if pdf_path:
                        return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.BIORXIV:
            if publication.doi and publication.doi.startswith("10.1101/"):
                result = await client.get_by_doi(publication.doi)
                if result and result.get('pdf_url'):
                    pdf_path = self.pdf_downloader.download(
                        result['pdf_url'],
                        publication.doi,
                        source="biorxiv"
                    )
                    if pdf_path:
                        return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.ARXIV:
            # Try to extract arXiv ID from metadata or DOI
            arxiv_id = self._extract_arxiv_id(publication)
            if arxiv_id:
                result = await client.search_by_arxiv_id(arxiv_id)
                if result and result.get('pdf_url'):
                    pdf_path = self.pdf_downloader.download(
                        result['pdf_url'],
                        arxiv_id,
                        source="arxiv"
                    )
                    if pdf_path:
                        return {'pdf_path': pdf_path}

        elif source_type == FullTextSource.CROSSREF:
            if publication.doi:
                links = await client.get_fulltext_links(publication.doi)
                for link in links:
                    pdf_path = self.pdf_downloader.download(
                        link,
                        publication.doi,
                        source="crossref"
                    )
                    if pdf_path:
                        return {'pdf_path': pdf_path}

        return None

    def _extract_arxiv_id(self, publication: Publication) -> Optional[str]:
        """Extract arXiv ID from metadata, DOI, or URL."""
        # Check metadata
        if publication.metadata and 'arxiv_id' in publication.metadata:
            return publication.metadata['arxiv_id']

        # Check DOI (10.48550/arXiv.2301.12345)
        if publication.doi and 'arxiv' in publication.doi.lower():
            parts = publication.doi.split('arxiv.')
            if len(parts) > 1:
                return parts[1]

        # Check URL
        if publication.url and 'arxiv.org' in publication.url:
            import re
            match = re.search(r'arxiv.org/abs/(\d+\.\d+)', publication.url)
            if match:
                return match.group(1)

        return None

    def get_coverage_stats(self) -> dict:
        """Get coverage statistics by source."""
        stats = self.pdf_downloader.get_download_stats()
        stats['sources_enabled'] = [s.value for s in self.sources.keys()]
        return stats
```

**Tasks**:
- [ ] Implement `FullTextManager` class
- [ ] Implement waterfall logic
- [ ] Add timeout handling
- [ ] Add statistics tracking
- [ ] Handle all source types
- [ ] Write 10+ unit tests
- [ ] Integration test with real publications

---

#### Task 2.2: Update Configuration (Day 7)
**Priority**: HIGH

**Updates to `config.py`**:
```python
# Add to PublicationSearchConfig

class PublicationSearchConfig:
    # ... existing code ...

    # NEW - OA Source Feature Toggles
    enable_core: bool = True
    enable_arxiv: bool = True
    enable_biorxiv: bool = True
    enable_crossref: bool = True

    # NEW - OA Source API Keys/Config
    core_api_key: Optional[str] = None
    crossref_email: str = "sdodl001@odu.edu"

    # NEW - OpenAlex config (already exists, enhance)
    openalex_config: OpenAlexConfig = field(default_factory=OpenAlexConfig)
```

**Tasks**:
- [ ] Add new feature toggles
- [ ] Add CORE API key config
- [ ] Add Crossref email config
- [ ] Update preset configs
- [ ] Update validation logic

---

#### Task 2.3: Update Pipeline Integration (Day 8)
**Priority**: HIGH

**Updates to `pipeline.py`**:
```python
# In PublicationSearchPipeline.__init__()

def __init__(self, config: PublicationSearchConfig):
    # ... existing code ...

    # NEW - Full-text manager
    if config.enable_fulltext:
        from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager
        self.fulltext_manager = FullTextManager(config)
        logger.info("FullTextManager initialized")
    else:
        self.fulltext_manager = None


# In search() method

async def search(self, query: str) -> SearchResults:
    # ... existing search logic ...

    # Existing: Deduplicate, rank, etc.

    # NEW - Acquire full text for top N papers
    if self.fulltext_manager and self.config.enable_fulltext:
        logger.info("Acquiring full text for top publications...")

        # Only get full text for top 20 papers (configurable)
        top_pubs = ranked_pubs[:20]

        for pub in top_pubs:
            try:
                result = await self.fulltext_manager.get_fulltext(pub)
                if result.success:
                    pub.pdf_path = result.pdf_path
                    pub.full_text = result.full_text
                    if not pub.metadata:
                        pub.metadata = {}
                    pub.metadata['fulltext_source'] = result.source.value
                    pub.metadata['fulltext_attempts'] = len(result.attempts)
            except Exception as e:
                logger.error(f"Error getting full text: {e}")

    return SearchResults(publications=ranked_pubs, ...)
```

**Tasks**:
- [ ] Add FullTextManager initialization
- [ ] Add full-text acquisition step
- [ ] Add configuration for how many papers to process
- [ ] Update SearchResults with full-text stats
- [ ] Write integration tests

---

#### Task 2.4: Testing & Benchmarking (Days 9-10)
**Priority**: CRITICAL

**Test Suite**:
```python
# File: tests/test_fulltext_manager.py

import pytest
from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager
from omics_oracle_v2.lib.publications.models import Publication

@pytest.fixture
def fulltext_manager():
    config = PublicationSearchConfig(
        enable_core=True,
        enable_arxiv=True,
        enable_biorxiv=True,
        core_api_key="YOUR_KEY"
    )
    return FullTextManager(config)


@pytest.mark.asyncio
async def test_pmc_access(fulltext_manager):
    """Test PMC full-text access."""
    pub = Publication(
        title="Test Paper",
        pmcid="PMC123456",
        doi="10.1234/test"
    )

    result = await fulltext_manager.get_fulltext(pub)
    assert result.success
    assert result.source == FullTextSource.PMC


@pytest.mark.asyncio
async def test_biorxiv_access(fulltext_manager):
    """Test bioRxiv preprint access."""
    pub = Publication(
        title="Test Preprint",
        doi="10.1101/2023.01.01.123456"
    )

    result = await fulltext_manager.get_fulltext(pub)
    assert result.success
    assert result.source == FullTextSource.BIORXIV


@pytest.mark.asyncio
async def test_waterfall_strategy(fulltext_manager):
    """Test that waterfall tries multiple sources."""
    pub = Publication(
        title="Test Paper",
        doi="10.1038/nature12345"
    )

    result = await fulltext_manager.get_fulltext(pub)
    assert len(result.attempts) > 1  # Should try multiple sources
```

**Coverage Benchmark Test**:
```python
# File: tests/test_fulltext_coverage.py

async def test_coverage_benchmark():
    """Test coverage on 1000 sample DOIs."""

    manager = FullTextManager(config)

    # Load test dataset
    test_dois = load_test_dois(1000)

    results = {
        'found': 0,
        'not_found': 0,
        'by_source': {},
        'times': []
    }

    for doi in test_dois:
        pub = Publication(doi=doi, title="Test")
        result = await manager.get_fulltext(pub)

        if result.success:
            results['found'] += 1
            source = result.source.value
            results['by_source'][source] = results['by_source'].get(source, 0) + 1
            results['times'].append(result.total_time)
        else:
            results['not_found'] += 1

    # Print results
    total = len(test_dois)
    coverage = results['found'] / total * 100
    avg_time = sum(results['times']) / len(results['times'])

    print(f"\nCoverage: {results['found']}/{total} ({coverage:.1f}%)")
    print(f"Avg time: {avg_time:.2f}s")
    print(f"\nBy source:")
    for source, count in results['by_source'].items():
        pct = count / results['found'] * 100
        print(f"  {source}: {count} ({pct:.1f}%)")

    # Assert targets
    assert coverage >= 60.0, f"Coverage below 60%: {coverage:.1f}%"
```

**Tasks**:
- [ ] Write 15+ unit tests
- [ ] Write integration tests
- [ ] Run coverage benchmark (1000 DOIs)
- [ ] Measure speed (avg time per paper)
- [ ] Generate coverage report by source
- [ ] Fix bugs found during testing
- [ ] Optimize slow sources

---

## 📊 Expected Outcomes (Phase 1)

### Coverage Projections

| Source | Coverage | Quality | Speed | Cost |
|--------|----------|---------|-------|------|
| Institutional | 20-30% | ★★★★★ | Fast | $0 |
| PMC | 15-20% | ★★★★★ | Fast | $0 |
| OpenAlex OA | 5-10% | ★★★★☆ | Fast | $0 |
| CORE | 10-15% | ★★★☆☆ | Medium | $0 (free API key) |
| bioRxiv/medRxiv | 2-3% | ★★★☆☆ | Fast | $0 |
| Crossref | 2-3% | ★★★★☆ | Fast | $0 |
| arXiv | 2-3% | ★★★☆☆ | Slow (rate limited) | $0 |
| **Total (Legal)** | **60-70%** | - | **1-2s avg** | **$0** |

### Success Metrics

**After 2 weeks**:
- ✅ 60-70% coverage (up from 40-50%)
- ✅ 100% legal sources
- ✅ No legal risk
- ✅ $0 cost
- ✅ Production-ready
- ✅ Fully documented
- ✅ Test coverage >80%

---

## 🔒 Phase 2: Sci-Hub Fallback (OPTIONAL - Requires Legal Review)

**⚠️ IMPORTANT**: Only implement after:
1. Phase 1 complete and coverage measured
2. Legal review with university counsel
3. Institutional approval documented
4. Written acknowledgment of legal risks
5. User opts in explicitly

### Implementation Approach (If Approved)

**NOT live scraping** - use LibGen torrents instead:
- More ethical (doesn't stress Sci-Hub servers)
- Faster (local access)
- Safer (no active scraping detection)
- Community-supported (Sci-Hub Rescue Mission)

**Architecture**:
```python
class SciHubTorrentClient:
    """
    LEGAL WARNING: Use only with institutional approval.

    Access Sci-Hub papers via LibGen torrents.
    Requires explicit opt-in and legal acknowledgment.
    """

    def __init__(self, enabled: bool = False, legal_approved: bool = False):
        if enabled and not legal_approved:
            raise ValueError(
                "Sci-Hub access requires legal_approved=True. "
                "Consult with legal counsel first."
            )

        self.enabled = enabled and legal_approved

        if self.enabled:
            # Use libgen-seedtools for torrent access
            import libgen_seedtools
            self.torrent_client = libgen_seedtools.Client()

    async def get_pdf(self, doi: str) -> Optional[bytes]:
        """Get PDF from torrents (if legal approval given)."""
        if not self.enabled:
            return None

        # Implementation here
        pass
```

**Add to FullTextManager**:
```python
# Only add as LAST fallback
if config.enable_scihub_fallback and config.scihub_legal_approved:
    self.sources[FullTextSource.SCIHUB_FALLBACK] = SciHubTorrentClient(
        enabled=True,
        legal_approved=True
    )
```

**Estimated Additional Coverage**: +30-40% (total 90-95%)

**Legal Requirements**:
1. University legal counsel approval
2. Research-only use documentation
3. Strict access controls (no redistribution)
4. Comprehensive audit logging
5. User acknowledgment of risks

---

## 📅 Implementation Timeline

### Week 1: OA Source Clients
- **Day 1-2**: CORE API client + tests
- **Day 2-3**: arXiv client + tests
- **Day 3-4**: bioRxiv client + tests
- **Day 4**: Enhance OpenAlex integration
- **Day 5**: Crossref client + tests

### Week 2: Integration & Testing
- **Day 6-7**: FullTextManager + waterfall logic
- **Day 7**: Update config + pipeline integration
- **Day 8**: Integration testing
- **Day 9-10**: Coverage benchmark + bug fixes

### Total: 10 working days (2 weeks)

---

## ✅ Implementation Checklist

### Setup
- [ ] Get CORE API key (free): https://core.ac.uk/api-keys/register
- [ ] Set up test dataset (1000 diverse DOIs)
- [ ] Create `oa_sources/` directory structure

### Week 1 (OA Clients)
- [ ] Implement COREClient
- [ ] Implement ArXivClient
- [ ] Implement BioRxivClient
- [ ] Enhance OpenAlexClient
- [ ] Implement CrossrefClient
- [ ] Write 20+ unit tests for clients

### Week 2 (Integration)
- [ ] Implement FullTextManager
- [ ] Update config.py
- [ ] Update pipeline.py
- [ ] Write 15+ integration tests
- [ ] Run coverage benchmark
- [ ] Measure performance
- [ ] Fix bugs
- [ ] Write documentation

### Documentation
- [ ] API documentation for each client
- [ ] User guide for FullTextManager
- [ ] Configuration guide
- [ ] Coverage report
- [ ] Performance benchmarks

---

## 🎯 Success Criteria

**Phase 1 Complete When**:
1. ✅ All 5 OA clients implemented and tested
2. ✅ FullTextManager working with waterfall strategy
3. ✅ Coverage ≥60% on benchmark dataset (1000 DOIs)
4. ✅ Average time <2s per paper
5. ✅ Test coverage ≥80%
6. ✅ Documentation complete
7. ✅ No critical bugs
8. ✅ Integrated into main pipeline

**Then Decide**: Is 60-70% coverage sufficient, or proceed to Phase 2?

---

## 📝 Notes

1. **All Phase 1 sources are 100% legal** - no copyright concerns
2. **$0 total cost** - all APIs are free
3. **Phase 2 requires legal review** - don't implement without approval
4. **Focus on legal sources first** - build solid foundation
5. **Measure coverage** - before deciding on Phase 2

---

**Ready to start? Let's begin with Task 1.1: CORE API Client!**
