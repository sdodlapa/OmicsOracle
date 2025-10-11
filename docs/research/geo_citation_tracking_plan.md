# GEO Dataset Citation Tracking - Implementation Plan

**Date:** October 11, 2025
**Purpose:** Add citation tracking for GEO datasets using existing infrastructure

---

## Overview

Add ability to find and download recent papers that cite a GEO dataset's original publication.

**Key Insight:** We already have 90% of what we need!
- ✅ GEO metadata with PubMed IDs
- ✅ Publication search pipeline
- ✅ PDF downloader with institutional access
- ✅ Brand new dataset detection (is_recent())

**Missing:** Only citation API integration (Semantic Scholar)

---

## Architecture

```
GEO Dataset (GSE12345)
    ↓ (already have)
GEO Metadata (includes pubmed_ids=['23456789'])
    ↓ (NEW: add this)
Semantic Scholar API (get citations of PMID:23456789)
    ↓
List of citing papers (filtered: 2020-2025, ranked by relevance)
    ↓ (already have)
PDF Downloader (institutional access + downloads)
    ↓
PDFs in data/pdfs/citations/GSE12345/
```

---

## Implementation Tasks

### Task 1: Semantic Scholar Client (2 hours)

**File:** `omics_oracle_v2/lib/publications/semantic_scholar.py` (NEW)

```python
"""Semantic Scholar API client for citation tracking."""

import asyncio
import logging
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """
    Client for Semantic Scholar API.

    Free tier limits:
    - 100 requests per 5 minutes
    - 1 request per second

    No API key required for basic access.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)
        self._last_request_time = 0

    async def get_paper(self, identifier: str) -> dict:
        """
        Get paper metadata by DOI, PMID, or Semantic Scholar ID.

        Args:
            identifier: DOI, PMID:12345, or Semantic Scholar ID

        Returns:
            Paper metadata with citations
        """
        # Rate limiting: 1 request per second
        now = time.time()
        if now - self._last_request_time < 1.0:
            await asyncio.sleep(1.0 - (now - self._last_request_time))

        url = f"{self.BASE_URL}/paper/{identifier}"
        params = {
            'fields': 'title,year,authors,citationCount,citations,citations.title,citations.year,citations.citationCount'
        }

        headers = {}
        if self.api_key:
            headers['x-api-key'] = self.api_key

        response = await self.client.get(url, params=params, headers=headers)
        self._last_request_time = time.time()

        if response.status_code == 404:
            return None
        response.raise_for_status()

        return response.json()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

**Testing:**
```bash
pytest tests/unit/publications/test_semantic_scholar.py -v
```

---

### Task 2: Citation Tracker (3 hours)

**File:** `omics_oracle_v2/lib/publications/citations.py` (NEW)

```python
"""Citation tracking for GEO datasets and publications."""

import logging
from datetime import datetime
from typing import List

from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.publications.semantic_scholar import SemanticScholarClient

logger = logging.getLogger(__name__)


class CitationTracker:
    """
    Track papers that cite GEO dataset publications.

    Uses Semantic Scholar API to find recent papers citing
    the original publication associated with a GEO dataset.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.semantic_scholar = SemanticScholarClient(api_key=api_key)

    async def get_citing_papers_for_geo(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_papers: int = 10,
        years_back: int = 5
    ) -> List[Publication]:
        """
        Get recent papers citing the GEO dataset's original paper.

        Args:
            geo_metadata: GEO dataset metadata (must have pubmed_ids)
            max_papers: Maximum papers to return
            years_back: Only include papers from last N years

        Returns:
            List of citing publications, ranked by recency + impact

        Example:
            >>> tracker = CitationTracker()
            >>> geo_meta = await geo_client.get_metadata("GSE12345")
            >>> citing_papers = await tracker.get_citing_papers_for_geo(
            ...     geo_meta, max_papers=10, years_back=5
            ... )
            >>> print(f"Found {len(citing_papers)} recent papers using GSE12345")
        """
        # Check for brand new datasets
        if geo_metadata.is_recent(days=365):
            logger.info(
                f"{geo_metadata.geo_id} is <1 year old - "
                "likely has no citing papers yet"
            )
            # Return original paper instead
            return await self._get_original_papers(geo_metadata)

        # Extract PubMed ID
        if not geo_metadata.pubmed_ids:
            logger.warning(f"No PubMed ID for {geo_metadata.geo_id}")
            return []

        pmid = geo_metadata.pubmed_ids[0]
        logger.info(f"Finding papers citing PMID:{pmid} (for {geo_metadata.geo_id})")

        # Query Semantic Scholar
        try:
            paper_data = await self.semantic_scholar.get_paper(f"PMID:{pmid}")

            if not paper_data or 'citations' not in paper_data:
                logger.warning(f"No citation data for PMID:{pmid}")
                return []

            # Convert to Publication objects and filter by recency
            current_year = datetime.now().year
            min_year = current_year - years_back

            citing_papers = []
            for cite in paper_data['citations']:
                if cite.get('year', 0) >= min_year:
                    pub = self._semantic_scholar_to_publication(cite)
                    citing_papers.append(pub)

            logger.info(
                f"Found {len(citing_papers)} citing papers from "
                f"{min_year}-{current_year}"
            )

            # Rank by relevance
            ranked = self._rank_citing_papers(citing_papers)

            return ranked[:max_papers]

        except Exception as e:
            logger.error(f"Failed to get citations for PMID:{pmid}: {e}")
            return []

    def _rank_citing_papers(self, papers: List[Publication]) -> List[Publication]:
        """
        Rank citing papers by relevance.

        Factors:
        - Recency (newer = better)
        - Citation count (higher = more influential)
        - Open access (available = prioritized)
        """
        def score(pub: Publication) -> float:
            # Recency: 40%
            recency_score = (pub.year - 2020) / 5.0 if pub.year else 0

            # Impact: 30%
            citation_score = min((pub.citations or 0) / 100.0, 1.0)

            # Availability: 30%
            access_score = 1.0 if pub.is_open_access else 0.5

            return (
                recency_score * 0.4 +
                citation_score * 0.3 +
                access_score * 0.3
            )

        papers.sort(key=score, reverse=True)
        return papers

    def _semantic_scholar_to_publication(self, data: dict) -> Publication:
        """Convert Semantic Scholar data to Publication object."""
        return Publication(
            title=data.get('title', ''),
            year=data.get('year'),
            citations=data.get('citationCount', 0),
            # Note: Would need to enhance Publication model with more fields
            # or use existing pipeline to enrich with PubMed/OpenAlex data
        )

    async def _get_original_papers(
        self, geo_metadata: GEOSeriesMetadata
    ) -> List[Publication]:
        """
        Get the original paper(s) for a brand new GEO dataset.

        For datasets <1 year old with no citing papers yet.
        """
        if not geo_metadata.pubmed_ids:
            return []

        # Fetch original paper metadata
        # (Could integrate with existing PublicationSearchPipeline)
        papers = []
        for pmid in geo_metadata.pubmed_ids[:1]:  # Just first paper
            try:
                data = await self.semantic_scholar.get_paper(f"PMID:{pmid}")
                if data:
                    pub = self._semantic_scholar_to_publication(data)
                    papers.append(pub)
            except Exception as e:
                logger.warning(f"Could not fetch PMID:{pmid}: {e}")

        return papers

    async def close(self):
        """Clean up resources."""
        await self.semantic_scholar.close()
```

**Testing:**
```bash
pytest tests/unit/publications/test_citations.py -v
```

---

### Task 3: Integration with Unified Pipeline (2 hours)

**File:** `omics_oracle_v2/lib/pipelines/unified_search_pipeline.py` (MODIFY)

Add citation enrichment to search results:

```python
class OmicsSearchPipeline:
    def __init__(self, config: UnifiedSearchConfig):
        # ... existing init ...

        # NEW: Initialize citation tracker
        if config.enable_citation_tracking:
            from omics_oracle_v2.lib.publications.citations import CitationTracker
            self.citation_tracker = CitationTracker()
        else:
            self.citation_tracker = None

    async def search_with_citations(
        self,
        query: str,
        include_citing_papers: bool = True,
        max_citing_papers: int = 10
    ) -> SearchResult:
        """
        Search with optional citation enrichment.

        For each GEO dataset found, optionally fetch recent papers
        that cite the dataset's original publication.
        """
        # Regular search
        result = await self.search(query)

        # Enrich with citations
        if include_citing_papers and self.citation_tracker:
            await self._enrich_with_citations(
                result.geo_datasets, max_citing_papers
            )

        return result

    async def _enrich_with_citations(
        self,
        geo_datasets: List[GEOSeriesMetadata],
        max_papers: int
    ):
        """Add citing papers to each GEO dataset."""
        for dataset in geo_datasets:
            try:
                citing_papers = await self.citation_tracker.get_citing_papers_for_geo(
                    dataset, max_papers=max_papers
                )
                # Store in metadata
                dataset.citing_papers = citing_papers  # Need to add this field to model
                logger.info(
                    f"Found {len(citing_papers)} citing papers for {dataset.geo_id}"
                )
            except Exception as e:
                logger.warning(f"Could not fetch citations for {dataset.geo_id}: {e}")
```

---

### Task 4: Update GEO Model (1 hour)

**File:** `omics_oracle_v2/lib/geo/models.py` (MODIFY)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omics_oracle_v2.lib.publications.models import Publication

class GEOSeriesMetadata(BaseModel):
    # ... existing fields ...

    # NEW: Citing papers
    citing_papers: List['Publication'] = Field(
        default_factory=list,
        description="Recent papers that cite this dataset's original publication"
    )

    def get_methodology_examples(self) -> List['Publication']:
        """
        Get recent papers showing how this dataset was used.

        Returns papers from last 5 years that cite this dataset,
        ranked by recency and impact.
        """
        return self.citing_papers
```

---

### Task 5: PDF Download Integration (1 hour)

**File:** `omics_oracle_v2/lib/publications/fulltext/manager.py` (USE EXISTING)

```python
# Use existing PDF downloader!
async def download_citing_paper_pdfs(
    geo_metadata: GEOSeriesMetadata,
    output_dir: Path = Path("data/pdfs/citations")
):
    """
    Download PDFs for papers citing a GEO dataset.

    Uses existing PDF download infrastructure.
    """
    if not geo_metadata.citing_papers:
        logger.info(f"No citing papers for {geo_metadata.geo_id}")
        return

    # Create directory for this dataset
    dataset_dir = output_dir / geo_metadata.geo_id
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Use existing PDF downloader
    from omics_oracle_v2.lib.publications.fulltext import PDFDownloadManager

    downloader = PDFDownloadManager()

    download_report = await downloader.download_batch(
        publications=geo_metadata.citing_papers,
        output_dir=dataset_dir,
        url_field="fulltext_url"
    )

    logger.info(
        f"Downloaded {download_report.successful} PDFs for {geo_metadata.geo_id} "
        f"to {dataset_dir}"
    )

    return download_report
```

---

## Time Estimate

| Task | Hours |
|------|-------|
| 1. Semantic Scholar Client | 2 |
| 2. Citation Tracker | 3 |
| 3. Pipeline Integration | 2 |
| 4. Model Updates | 1 |
| 5. PDF Integration | 1 |
| **Total** | **9 hours** |

---

## Testing Plan

### Unit Tests
```bash
# Test Semantic Scholar client
pytest tests/unit/publications/test_semantic_scholar.py

# Test citation tracker
pytest tests/unit/publications/test_citations.py

# Test GEO model enhancements
pytest tests/unit/geo/test_models.py
```

### Integration Test
```python
# tests/integration/test_geo_citations.py

async def test_geo_citation_tracking():
    """Test full citation tracking flow."""

    # 1. Search for GEO dataset
    pipeline = OmicsSearchPipeline(config)
    result = await pipeline.search("GSE48968")  # Known dataset with citations

    assert len(result.geo_datasets) > 0
    dataset = result.geo_datasets[0]

    # 2. Get citing papers
    tracker = CitationTracker()
    citing_papers = await tracker.get_citing_papers_for_geo(
        dataset, max_papers=10, years_back=5
    )

    assert len(citing_papers) > 0
    assert all(p.year >= 2020 for p in citing_papers)

    # 3. Download PDFs
    download_report = await download_citing_paper_pdfs(dataset)

    assert download_report.successful > 0
```

---

## Example Usage

```python
# User searches for GEO dataset
pipeline = OmicsSearchPipeline(config)
result = await pipeline.search_with_citations(
    "breast cancer GSE12345",
    include_citing_papers=True,
    max_citing_papers=10
)

# Get first dataset
dataset = result.geo_datasets[0]

print(f"Dataset: {dataset.geo_id}")
print(f"Title: {dataset.title}")
print(f"Original paper: PMID {dataset.pubmed_ids[0]}")
print(f"\nRecent papers using this dataset ({len(dataset.citing_papers)}):")

for i, paper in enumerate(dataset.citing_papers, 1):
    print(f"{i}. [{paper.year}] {paper.title} ({paper.citations} cites)")

# Download PDFs for citing papers
await download_citing_paper_pdfs(dataset)
print(f"\nPDFs saved to: data/pdfs/citations/{dataset.geo_id}/")
```

---

## Success Criteria

- [ ] Semantic Scholar API integration working
- [ ] Citation tracking for GEO datasets functional
- [ ] Brand new datasets (<1 year) handled gracefully
- [ ] PDF download integration using existing infrastructure
- [ ] 60-80% PDF download success rate
- [ ] <2s latency for citation queries (with caching)
- [ ] All tests passing

---

## Next Steps

**Week 4 Decision:**
- Option A: Implement citation tracking (9 hours)
- Option B: Implement citation scoring improvements (4-6 hours)
- Option C: Do both (13-15 hours = ~2 days)

**Recommendation:** Start with citation tracking (higher user value)
