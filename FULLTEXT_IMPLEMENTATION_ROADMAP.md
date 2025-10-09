# Full-Text Access Implementation Roadmap

**Goal**: Increase full-text coverage from 40% to 70%+ using **100% legal sources**
**Timeline**: 2 weeks
**Risk**: NONE (all legal)

---

## Week 1: New OA Source Integration

### Day 1-2: CORE API Client

**CORE (Connecting Repositories)**: 45M+ open access full texts

```python
# omics_oracle_v2/lib/publications/oa_sources/core_client.py

import aiohttp
from typing import Optional, List
from pathlib import Path

class COREClient:
    """
    CORE API client for open access full-text discovery.

    API Docs: https://core.ac.uk/documentation/api
    Free API key: https://core.ac.uk/api-keys/register
    """

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None

    async def search_by_doi(self, doi: str) -> Optional[dict]:
        """
        Search for paper by DOI.

        Returns:
            {
                'id': CORE ID,
                'title': Paper title,
                'downloadUrl': PDF download URL,
                'fullText': Full text if available,
                ...
            }
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/works/search"
            params = {
                'q': f'doi:"{doi}"',
                'api_key': self.api_key,
                'limit': 1
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        return data['results'][0]
        return None

    async def download_pdf(self, download_url: str, output_path: Path) -> bool:
        """Download PDF from CORE."""
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with session.get(download_url, headers=headers) as response:
                if response.status == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(await response.read())
                    return True
        return False


# Usage
async def test_core():
    client = COREClient(api_key="YOUR_API_KEY")

    # Search for a paper
    result = await client.search_by_doi("10.1038/nature12373")

    if result and result.get('downloadUrl'):
        print(f"Found PDF: {result['title']}")
        success = await client.download_pdf(
            result['downloadUrl'],
            Path("data/pdfs/core/nature12373.pdf")
        )
        print(f"Downloaded: {success}")

    # Or get full text directly
    if result and result.get('fullText'):
        print(f"Full text available ({len(result['fullText'])} chars)")
```

**Integration Checklist**:
- [ ] Get free CORE API key
- [ ] Implement `core_client.py`
- [ ] Add to `FullTextManager` waterfall
- [ ] Test with 100 sample DOIs
- [ ] Measure coverage improvement

**Expected Impact**: +10-15% coverage

---

### Day 3-4: arXiv & bioRxiv Clients

**arXiv**: 2M+ physics/CS/math preprints
**bioRxiv/medRxiv**: 200K+ biomedical preprints

```python
# omics_oracle_v2/lib/publications/oa_sources/arxiv_client.py

import aiohttp
import feedparser
from typing import Optional

class ArXivClient:
    """
    arXiv API client for preprint access.

    API Docs: https://info.arxiv.org/help/api/index.html
    No API key required!
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    async def search_by_arxiv_id(self, arxiv_id: str) -> Optional[dict]:
        """
        Get paper by arXiv ID.

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
                            'authors': [author.name for author in entry.authors]
                        }
        return None

    async def download_pdf(self, pdf_url: str, output_path: Path) -> bool:
        """Download PDF from arXiv (no auth required)."""
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(await response.read())
                    return True
        return False


# omics_oracle_v2/lib/publications/oa_sources/biorxiv_client.py

class BioRxivClient:
    """
    bioRxiv/medRxiv API client.

    API Docs: https://api.biorxiv.org/
    No API key required!
    """

    BASE_URL = "https://api.biorxiv.org/details"

    async def search_by_doi(self, doi: str) -> Optional[dict]:
        """
        Get preprint by DOI.

        Example: doi = "10.1101/2023.01.01.123456"
        """
        # bioRxiv DOIs: 10.1101/*
        # medRxiv DOIs: 10.1101/* (same prefix)

        server = "biorxiv"  # or "medrxiv"
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
                            'version': paper['version']
                        }
        return None
```

**Integration Checklist**:
- [ ] Implement `arxiv_client.py`
- [ ] Implement `biorxiv_client.py`
- [ ] Handle arXiv ID extraction from metadata
- [ ] Handle bioRxiv/medRxiv DOI detection (10.1101/*)
- [ ] Add to `FullTextManager` waterfall
- [ ] Test preprint coverage

**Expected Impact**: +5-10% coverage (especially for recent papers)

---

### Day 5: Crossref Full-Text Links

**Crossref**: Metadata for 130M+ works, some with full-text links

```python
# omics_oracle_v2/lib/publications/oa_sources/crossref_client.py

class CrossrefClient:
    """
    Crossref API for publisher full-text links.

    API Docs: https://api.crossref.org/
    No API key required (polite pool with email)
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, email: str):
        self.email = email  # For polite pool (faster rate limits)

    async def get_fulltext_links(self, doi: str) -> List[str]:
        """
        Get full-text links from Crossref.

        Returns list of URLs to full text (PDF, HTML, etc.)
        """
        url = f"{self.BASE_URL}/{doi}"
        headers = {'User-Agent': f'OmicsOracle/2.0 (mailto:{self.email})'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get('message', {})

                    # Extract links
                    links = []

                    # Check for open access links
                    if message.get('link'):
                        for link in message['link']:
                            if link.get('content-type') == 'application/pdf':
                                links.append(link['URL'])
                            elif link.get('content-type') == 'text/html':
                                links.append(link['URL'])

                    # Check for license (indicates OA)
                    if message.get('license'):
                        # Has open license, try to construct PDF URL
                        if message.get('URL'):
                            links.append(message['URL'])

                    return links
        return []
```

**Integration Checklist**:
- [ ] Implement `crossref_client.py`
- [ ] Extract full-text URLs from metadata
- [ ] Verify PDFs are actually accessible
- [ ] Add to `FullTextManager` waterfall
- [ ] Cache Crossref metadata

**Expected Impact**: +3-5% coverage

---

## Week 2: Integration & Optimization

### Day 6-7: FullTextManager Orchestrator

```python
# omics_oracle_v2/lib/publications/fulltext_manager.py

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class SourceType(Enum):
    INSTITUTIONAL = "institutional"
    PMC = "pmc"
    UNPAYWALL = "unpaywall"
    CORE = "core"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    CROSSREF = "crossref"


@dataclass
class FullTextResult:
    """Result of full-text acquisition attempt."""

    success: bool
    source: Optional[SourceType] = None
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

    Tries sources in priority order:
    1. Institutional access (highest quality)
    2. PubMed Central (peer-reviewed, validated)
    3. Unpaywall (OA discovery)
    4. CORE (large OA aggregator)
    5. Crossref (publisher links)
    6. arXiv (preprints)
    7. bioRxiv/medRxiv (biomedical preprints)
    """

    def __init__(self, config: FullTextConfig):
        self.config = config

        # Initialize all sources
        self.sources = {
            SourceType.INSTITUTIONAL: InstitutionalAccessManager()
                if config.enable_institutional else None,
            SourceType.PMC: PMCClient()
                if config.enable_pmc else None,
            SourceType.UNPAYWALL: UnpaywallClient(config.unpaywall_email)
                if config.enable_unpaywall else None,
            SourceType.CORE: COREClient(config.core_api_key)
                if config.enable_core else None,
            SourceType.ARXIV: ArXivClient()
                if config.enable_arxiv else None,
            SourceType.BIORXIV: BioRxivClient()
                if config.enable_biorxiv else None,
            SourceType.CROSSREF: CrossrefClient(config.crossref_email)
                if config.enable_crossref else None,
        }

        # Remove None values
        self.sources = {k: v for k, v in self.sources.items() if v is not None}

    async def get_fulltext(
        self,
        doi: str,
        pmid: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        timeout: float = 30.0
    ) -> FullTextResult:
        """
        Try to acquire full text from all available sources.

        Args:
            doi: Paper DOI
            pmid: Optional PubMed ID
            arxiv_id: Optional arXiv ID
            timeout: Max time to spend (seconds)

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

                # Try to get full text
                result = await self._try_source(
                    client, source_type, doi, pmid, arxiv_id
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

        # Not found in any source
        logger.warning(f"Full text not found for {doi} in {len(attempts)} sources")
        return FullTextResult(
            success=False,
            attempts=attempts,
            total_time=time.time() - start_time
        )

    async def _try_source(
        self,
        client,
        source_type: SourceType,
        doi: str,
        pmid: Optional[str],
        arxiv_id: Optional[str]
    ) -> Optional[dict]:
        """Try to get full text from a specific source."""

        # Different sources use different identifiers
        if source_type == SourceType.PMC and pmid:
            return await client.get_fulltext(pmid=pmid)

        elif source_type == SourceType.ARXIV and arxiv_id:
            return await client.get_fulltext(arxiv_id=arxiv_id)

        elif source_type == SourceType.BIORXIV and doi and '10.1101/' in doi:
            return await client.get_fulltext(doi=doi)

        else:
            # Most sources use DOI
            return await client.get_fulltext(doi=doi)

    def get_statistics(self) -> dict:
        """Get coverage statistics."""
        stats = {}
        for source_type, client in self.sources.items():
            if hasattr(client, 'get_stats'):
                stats[source_type.value] = client.get_stats()
        return stats
```

**Integration Checklist**:
- [ ] Implement waterfall logic
- [ ] Add timeout handling
- [ ] Implement statistics tracking
- [ ] Add caching layer
- [ ] Test with 1000 sample DOIs

---

### Day 8-9: Testing & Benchmarking

```python
# test_fulltext_coverage.py

import asyncio
from pathlib import Path

async def test_coverage():
    """Test full-text coverage on sample dataset."""

    manager = FullTextManager(config)

    # Load test DOIs (mix of OA and paywalled)
    test_dois = [
        "10.1038/nature12373",  # Nature (likely paywalled)
        "10.1371/journal.pone.0123456",  # PLOS (OA)
        "10.1101/2023.01.01.123456",  # bioRxiv (OA)
        # ... 1000 more
    ]

    results = {
        'found': 0,
        'not_found': 0,
        'by_source': {},
        'avg_time': []
    }

    for doi in test_dois:
        result = await manager.get_fulltext(doi)

        if result.success:
            results['found'] += 1
            source = result.source.value
            results['by_source'][source] = results['by_source'].get(source, 0) + 1
            results['avg_time'].append(result.total_time)
        else:
            results['not_found'] += 1

    # Print statistics
    total = len(test_dois)
    print(f"\nCoverage: {results['found']}/{total} ({results['found']/total*100:.1f}%)")
    print(f"\nBy source:")
    for source, count in results['by_source'].items():
        print(f"  {source}: {count} ({count/results['found']*100:.1f}%)")

    avg_time = sum(results['avg_time']) / len(results['avg_time'])
    print(f"\nAvg time: {avg_time:.2f}s")

# Run
asyncio.run(test_coverage())
```

**Testing Checklist**:
- [ ] Test with 1000 DOIs
- [ ] Measure coverage by source
- [ ] Benchmark speed
- [ ] Test error handling
- [ ] Validate PDF quality

---

### Day 10: Documentation & Deployment

```markdown
# Full-Text Access Documentation

## Supported Sources

### Institutional Access (Georgia Tech)
- Coverage: Variable (depends on subscriptions)
- Quality: Highest (publisher PDFs)
- Cost: Free (via GT)

### PubMed Central
- Coverage: 6M+ articles
- Quality: High (peer-reviewed)
- Cost: Free

### Unpaywall
- Coverage: 30M+ articles
- Quality: Good (validated OA)
- Cost: Free

### CORE
- Coverage: 45M+ full texts
- Quality: Variable (aggregated)
- Cost: Free API key

### arXiv
- Coverage: 2M+ preprints
- Quality: Preprints (not peer-reviewed)
- Cost: Free

### bioRxiv/medRxiv
- Coverage: 200K+ preprints
- Quality: Preprints (not peer-reviewed)
- Cost: Free

### Crossref
- Coverage: Some full-text links
- Quality: Good (publisher links)
- Cost: Free

## Configuration

```yaml
fulltext:
  enable_institutional: true
  enable_pmc: true
  enable_unpaywall: true
  enable_core: true         # NEW
  enable_arxiv: true        # NEW
  enable_biorxiv: true      # NEW
  enable_crossref: true     # NEW

  # API keys
  core_api_key: "YOUR_KEY_HERE"  # Get free at https://core.ac.uk/api-keys/register
  unpaywall_email: "your@email.com"
  crossref_email: "your@email.com"
```

## Usage

```python
from omics_oracle_v2.lib.publications import FullTextManager

manager = FullTextManager(config)

# Get full text
result = await manager.get_fulltext(doi="10.1038/nature12373")

if result.success:
    print(f"Found in: {result.source.value}")

    if result.pdf_path:
        print(f"PDF: {result.pdf_path}")

    if result.full_text:
        print(f"Text: {len(result.full_text)} chars")
else:
    print("Not found")
    print(f"Tried {len(result.attempts)} sources")
```
```

---

## Success Metrics

### Target Coverage (Legal Sources Only):

| Metric | Current | Phase 1 Target | Improvement |
|--------|---------|----------------|-------------|
| **Overall Coverage** | 40-50% | 60-70% | +20-30% |
| **OA Papers** | 80% | 95%+ | +15% |
| **Recent Papers (<2yr)** | 30% | 60% | +30% |
| **Preprints** | 10% | 80% | +70% |
| **Avg. Time/Paper** | 2-3s | 1-2s | Faster |

### By Source (Projected):

| Source | Coverage | Quality | Speed |
|--------|----------|---------|-------|
| Institutional | 20-30% | ★★★★★ | Fast |
| PMC | 15-20% | ★★★★★ | Fast |
| Unpaywall | 10-15% | ★★★★☆ | Medium |
| CORE | 10-15% | ★★★☆☆ | Medium |
| arXiv | 3-5% | ★★★☆☆ | Fast |
| bioRxiv | 2-3% | ★★★☆☆ | Fast |
| Crossref | 2-3% | ★★★★☆ | Fast |
| **Total** | **60-70%** | - | **1-2s avg** |

---

## Quick Start Checklist

### Day 1:
- [ ] Get CORE API key (free): https://core.ac.uk/api-keys/register
- [ ] Implement `core_client.py`
- [ ] Add CORE to waterfall
- [ ] Test with 10 sample DOIs

### Day 2-3:
- [ ] Implement `arxiv_client.py`
- [ ] Implement `biorxiv_client.py`
- [ ] Test preprint access

### Day 4-5:
- [ ] Implement `crossref_client.py`
- [ ] Build `FullTextManager`
- [ ] Integrate all sources

### Day 6-7:
- [ ] Test coverage (1000 DOIs)
- [ ] Benchmark performance
- [ ] Fix bugs

### Day 8-10:
- [ ] Write documentation
- [ ] Deploy to production
- [ ] Monitor metrics

---

## Estimated Outcomes

**After 2 weeks**:
- ✅ 60-70% coverage (up from 40-50%)
- ✅ 100% legal sources
- ✅ No legal risk
- ✅ Production-ready
- ✅ Fully documented

**Investment**:
- Time: 2 weeks (1 developer)
- Cost: $0 (all APIs free)
- Risk: None

**Return**:
- +20-30% more papers accessible
- Better user experience
- Competitive advantage
- Foundation for future enhancements
