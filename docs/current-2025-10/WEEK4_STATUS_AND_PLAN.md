# Week 4 Status & Execution Plan
**Created**: 2025-01-08
**Status**: Infrastructure discovered, minimal work remaining
**Context**: User proposed GEO citation tracking - we already have 90% built!

---

## Executive Summary

### Discovery 🎯
**CRITICAL REALIZATION**: We already have a complete citation infrastructure that can do what the user wants!

### User Request Recap
> "How about collecting/extracting full-text and PDFs of only most recent (2 to 5 years) 10 or max 20 cited papers that cite each GEO dataset? This will show examples of how current methodology is being applied."

### Infrastructure Status
✅ **90% COMPLETE** - Everything we need already exists:
- ✅ Semantic Scholar client (production-ready)
- ✅ OpenAlex client (production-ready)
- ✅ CitationFinder (multi-source citation discovery)
- ✅ **GEOCitationDiscovery** (EXACTLY what user wants!)
- ✅ GEO metadata with pubmed_ids field
- ✅ PDF downloader (assumed complete)
- ✅ Publication pipeline with citation enrichment

### Work Remaining
**3-4 HOURS** (not 9 hours initially proposed!)
1. Test existing infrastructure (1 hour)
2. Add recency filter (15 min)
3. Create usage example (1 hour)
4. Documentation (30 min)
5. Integration test (1 hour)

---

## Week 4 Timeline

### Week 4 Day 1: Citation Scoring Research ✅ COMPLETE
**Duration**: 3 hours
**Output**: 4 comprehensive research documents (~18,600 words)

**Documents Created**:
1. `citation_scoring_analysis.md` (8,600 words)
2. `citation_scoring_implementations.md` (6,800 words)
3. `citation_scoring_decision_framework.md` (3,200 words)
4. `README.md` (summary)
5. `EXECUTIVE_SUMMARY.txt` (visual summary)
6. `geo_citation_tracking_plan.md` (implementation plan)

**Key Finding**:
- Multiple approaches analyzed (Google Scholar, Semantic Scholar, PubMed, ML)
- Recommendation: Tier 1 approach (4-6 hours) - citations per year + query intent
- Decision pending: Implement now or defer to Month 2

**Status**: ✅ Research complete, awaiting user decision

---

### Week 4 Day 2: GEO Citation Tracking (NEW PLAN)
**Duration**: 3-4 hours (revised from 9 hours)
**Status**: About to start

**Why Revised?**
- Discovered existing infrastructure during code review
- GEOCitationDiscovery class already implements user's request
- Only need integration + testing, not building from scratch

**Plan**:
1. **Test Existing Code** (1 hour)
   - Validate `GEOCitationDiscovery.find_citing_papers()`
   - Test with real GEO dataset (e.g., GSE103322)
   - Verify both strategies work (citation + mention)
   - Check if papers have publication dates

2. **Add Recency Filter** (15 minutes)
   - Create utility function to filter 2020-2025 papers
   - Add to `omics_oracle_v2/lib/citations/filters.py`
   - Simple list comprehension

3. **Create Usage Example** (1 hour)
   - File: `examples/geo_citation_tracking_example.py`
   - Show complete workflow: GEO → citing papers → recent papers → PDFs
   - Add command-line interface

4. **Documentation** (30 minutes)
   - Update README with GEO citation tracking feature
   - Add to user guide
   - Document API usage

5. **Integration Test** (1 hour)
   - End-to-end test with real GEO dataset
   - Verify PDF downloads work
   - Performance validation

---

## Existing Infrastructure Deep-Dive

### 1. GEOCitationDiscovery Class ✅
**File**: `omics_oracle_v2/lib/citations/discovery/geo_discovery.py`
**Status**: COMPLETE - This is EXACTLY what user wants!

**Capabilities**:
```python
class GEOCitationDiscovery:
    async def find_citing_papers(
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100
    ) -> CitationDiscoveryResult
```

**Two Strategies**:
1. **Strategy A**: Papers citing original publication (via PMID from GEO metadata)
2. **Strategy B**: Papers mentioning GEO ID in their text (via PubMed search)

**Returns**:
```python
@dataclass
class CitationDiscoveryResult:
    geo_id: str                           # GSE12345
    original_pmid: Optional[str]          # Original paper's PMID
    citing_papers: List[Publication]      # Papers citing this GEO dataset
    strategy_breakdown: dict              # Which strategy found each paper
```

**Perfect Match for User Request!**

---

### 2. CitationFinder Class ✅
**File**: `omics_oracle_v2/lib/citations/discovery/finder.py`
**Status**: PRODUCTION-READY

**Multi-Source Discovery**:
- OpenAlex (primary) - Free, official API
- Google Scholar (fallback) - Comprehensive coverage
- Semantic Scholar (enrichment) - Citation metrics

**Key Methods**:
```python
find_citing_papers(publication, max_results=100) -> List[Publication]
get_citation_contexts(cited_pub, citing_pub) -> List[CitationContext]
find_citation_network(publication, depth=1) -> dict
get_citation_statistics(publication) -> dict
```

---

### 3. Semantic Scholar Client ✅
**File**: `omics_oracle_v2/lib/citations/clients/semantic_scholar.py`
**Status**: PRODUCTION - Already used in publication pipeline

**Capabilities**:
- Paper lookup by DOI
- Citation count enrichment
- Influential citation tracking
- Batch enrichment
- Rate limiting (100 req/5min)

**Already Integrated**:
```python
# From publication_pipeline.py
self.semantic_scholar_client = SemanticScholarClient(SemanticScholarConfig(enable=True))
enriched_pubs = self.semantic_scholar_client.enrich_publications(publications)
```

---

### 4. OpenAlex Client ✅
**File**: `omics_oracle_v2/lib/citations/clients/openalex.py`
**Status**: PRODUCTION-READY

**Capabilities**:
- Find citing papers by DOI
- Citation context extraction
- 10,000 requests/day (free tier with email)
- 10 req/second rate limit

**Example Usage**:
```python
client = OpenAlexClient(email="researcher@university.edu")
citing_papers = client.get_citing_papers(doi="10.1038/nature12345")
```

---

### 5. GEO Metadata Model ✅
**File**: `omics_oracle_v2/lib/geo/models.py`
**Status**: COMPLETE (Week 3)

**Relevant Fields**:
```python
class GEOSeriesMetadata:
    geo_id: str                           # GSE12345
    pubmed_ids: List[str]                 # PMIDs of papers describing dataset
    submission_date: Optional[datetime]   # When dataset was submitted
    last_update_date: Optional[datetime]  # Last update

    def is_recent(self) -> bool:
        """Check if dataset is recent (< 180 days)"""

    def get_age_days(self) -> Optional[int]:
        """Get dataset age in days"""
```

---

## What's Missing (Minimal Gaps)

### Gap 1: Recency Filter ❌ (15 MINUTES)
**Need**: Filter citing papers to 2020-2025 only

**Implementation**:
```python
# File: omics_oracle_v2/lib/citations/filters.py (NEW FILE)
from datetime import datetime
from typing import List
from omics_oracle_v2.lib.publications.models import Publication

def filter_recent_publications(
    publications: List[Publication],
    min_year: int = 2020,
    max_year: int = 2025
) -> List[Publication]:
    """Filter publications by year range."""
    return [
        p for p in publications
        if p.publication_date
        and min_year <= p.publication_date.year <= max_year
    ]

def filter_last_n_years(
    publications: List[Publication],
    years: int = 5
) -> List[Publication]:
    """Filter to publications from last N years."""
    current_year = datetime.now().year
    min_year = current_year - years
    return filter_recent_publications(publications, min_year=min_year)
```

**Usage**:
```python
# All citing papers
all_citing = await discovery.find_citing_papers(geo_metadata, max_results=100)

# Filter to 2020-2025 only
recent_citing = filter_recent_publications(all_citing.citing_papers, min_year=2020)

# Take top 20 by citations
top_20 = sorted(recent_citing, key=lambda p: p.citations or 0, reverse=True)[:20]
```

---

### Gap 2: Top-N Selection ✅ (NO GAP!)
**Need**: Limit to 10-20 most relevant papers

**Current State**: Already exists via `max_results` parameter!
```python
find_citing_papers(geo_metadata, max_results=20)  # Already supported!
```

**Additional Ranking**: Can sort by citations + recency
```python
ranked = sorted(
    citing_papers,
    key=lambda p: (p.citations or 0, p.publication_date or datetime.min),
    reverse=True
)[:20]
```

---

### Gap 3: Usage Example ❌ (1 HOUR)
**Need**: Complete example showing GEO → citing papers → PDFs

**File to Create**: `examples/geo_citation_tracking_example.py`

```python
"""
Find Recent Papers Citing GEO Datasets

Shows how to discover papers from 2020-2025 that cite a specific GEO dataset,
demonstrating current methodology usage.

Usage:
    python examples/geo_citation_tracking_example.py GSE103322 --max-papers 20
"""

import asyncio
import argparse
from datetime import datetime
from typing import List

from omics_oracle_v2.lib.geo.fetcher import GEOFetcher
from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.citations.filters import filter_recent_publications
from omics_oracle_v2.lib.publications.models import Publication


async def find_recent_citing_papers(
    geo_id: str,
    min_year: int = 2020,
    max_year: int = 2025,
    max_papers: int = 20
) -> List[Publication]:
    """
    Find recent papers citing a GEO dataset.

    Args:
        geo_id: GEO accession (e.g., GSE103322)
        min_year: Minimum publication year (default: 2020)
        max_year: Maximum publication year (default: 2025)
        max_papers: Maximum papers to return (default: 20)

    Returns:
        List of recent citing publications, ranked by relevance
    """

    print(f"\n{'='*80}")
    print(f"Finding recent papers citing {geo_id}")
    print(f"Year range: {min_year}-{max_year}")
    print(f"Max papers: {max_papers}")
    print(f"{'='*80}\n")

    # Step 1: Fetch GEO metadata
    print("Step 1: Fetching GEO metadata...")
    geo_fetcher = GEOFetcher()
    metadata = await geo_fetcher.fetch_geo_series(geo_id)

    print(f"✓ Found dataset: {metadata.title}")
    print(f"  Original papers: {len(metadata.pubmed_ids)} PMIDs")
    if metadata.submission_date:
        print(f"  Submitted: {metadata.submission_date.strftime('%Y-%m-%d')}")

    # Step 2: Find all citing papers
    print("\nStep 2: Finding papers that cite this dataset...")
    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=200)

    print(f"✓ Found {len(result.citing_papers)} total citing papers")
    print(f"  Strategy A (citing original paper): {len(result.strategy_breakdown['strategy_a'])}")
    print(f"  Strategy B (mentioning GEO ID): {len(result.strategy_breakdown['strategy_b'])}")

    # Step 3: Filter for recent papers
    print(f"\nStep 3: Filtering to {min_year}-{max_year}...")
    recent_papers = filter_recent_publications(
        result.citing_papers,
        min_year=min_year,
        max_year=max_year
    )

    print(f"✓ {len(recent_papers)} papers from {min_year}-{max_year}")

    # Step 4: Rank by citations + recency
    print(f"\nStep 4: Ranking by relevance (citations + recency)...")
    ranked_papers = sorted(
        recent_papers,
        key=lambda p: (
            p.citations or 0,                    # Primary: citation count
            p.publication_date or datetime.min   # Secondary: recency
        ),
        reverse=True
    )[:max_papers]

    print(f"✓ Selected top {len(ranked_papers)} papers")

    # Step 5: Display results
    print(f"\n{'='*80}")
    print(f"TOP {len(ranked_papers)} RECENT PAPERS CITING {geo_id}")
    print(f"{'='*80}\n")

    for i, paper in enumerate(ranked_papers, 1):
        print(f"{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")

        if paper.publication_date:
            print(f"   Year: {paper.publication_date.year}")

        if paper.citations:
            print(f"   Citations: {paper.citations}")

        if paper.doi:
            print(f"   DOI: {paper.doi}")
        elif paper.pmid:
            print(f"   PMID: {paper.pmid}")

        print()

    return ranked_papers


async def download_pdfs(papers: List[Publication], output_dir: str = "data/pdfs"):
    """
    Download PDFs for papers (if PDF downloader exists).

    Args:
        papers: Publications to download
        output_dir: Output directory for PDFs
    """
    try:
        from omics_oracle_v2.lib.publications.clients.pdf_downloader import PDFDownloader

        print(f"\nStep 5: Downloading PDFs to {output_dir}...")
        downloader = PDFDownloader()
        downloaded = await downloader.download_batch(
            publications=papers,
            output_dir=output_dir
        )

        print(f"✓ Downloaded {len(downloaded)}/{len(papers)} PDFs")

        return downloaded

    except ImportError:
        print("⚠ PDF downloader not available - skipping PDF downloads")
        return []


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Find recent papers citing GEO datasets"
    )
    parser.add_argument(
        "geo_id",
        help="GEO accession ID (e.g., GSE103322)"
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=2020,
        help="Minimum publication year (default: 2020)"
    )
    parser.add_argument(
        "--max-year",
        type=int,
        default=2025,
        help="Maximum publication year (default: 2025)"
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=20,
        help="Maximum papers to return (default: 20)"
    )
    parser.add_argument(
        "--download-pdfs",
        action="store_true",
        help="Download PDFs for found papers"
    )
    parser.add_argument(
        "--output-dir",
        default="data/pdfs",
        help="Output directory for PDFs (default: data/pdfs)"
    )

    args = parser.parse_args()

    # Run async function
    papers = asyncio.run(find_recent_citing_papers(
        geo_id=args.geo_id,
        min_year=args.min_year,
        max_year=args.max_year,
        max_papers=args.max_papers
    ))

    # Download PDFs if requested
    if args.download_pdfs:
        asyncio.run(download_pdfs(papers, output_dir=args.output_dir))


if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Find recent papers citing GSE103322
python examples/geo_citation_tracking_example.py GSE103322

# Custom parameters
python examples/geo_citation_tracking_example.py GSE103322 \
    --min-year 2022 \
    --max-year 2025 \
    --max-papers 10 \
    --download-pdfs
```

---

### Gap 4: Integration Test ❌ (1 HOUR)
**Need**: End-to-end test to validate everything works

**File to Create**: `tests/integration/test_geo_citation_tracking.py`

```python
"""
Integration test for GEO citation tracking.

Tests the complete workflow:
1. Fetch GEO metadata
2. Find citing papers
3. Filter by recency
4. Rank by relevance
5. (Optional) Download PDFs
"""

import pytest
from datetime import datetime

from omics_oracle_v2.lib.geo.fetcher import GEOFetcher
from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.citations.filters import filter_recent_publications


@pytest.mark.asyncio
async def test_geo_citation_discovery_basic():
    """Test basic GEO citation discovery."""

    # Use well-known GEO dataset
    geo_id = "GSE103322"

    # Fetch metadata
    fetcher = GEOFetcher()
    metadata = await fetcher.fetch_geo_series(geo_id)

    assert metadata.geo_id == geo_id
    assert len(metadata.pubmed_ids) > 0, "No PMIDs found"

    # Find citing papers
    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=50)

    assert result.geo_id == geo_id
    assert result.original_pmid
    assert len(result.citing_papers) > 0, "No citing papers found"

    print(f"✓ Found {len(result.citing_papers)} citing papers")


@pytest.mark.asyncio
async def test_recency_filtering():
    """Test filtering papers by publication year."""

    geo_id = "GSE103322"

    # Get citing papers
    fetcher = GEOFetcher()
    metadata = await fetcher.fetch_geo_series(geo_id)

    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=100)

    # Filter for recent papers (2020-2025)
    recent = filter_recent_publications(result.citing_papers, min_year=2020)

    # Verify all papers are from 2020+
    for paper in recent:
        if paper.publication_date:
            assert paper.publication_date.year >= 2020, \
                f"Paper from {paper.publication_date.year} should be filtered out"

    print(f"✓ {len(recent)} papers from 2020-2025")
    assert len(recent) > 0, "No recent papers found"


@pytest.mark.asyncio
async def test_citation_strategies():
    """Test that both citation strategies work."""

    geo_id = "GSE103322"

    fetcher = GEOFetcher()
    metadata = await fetcher.fetch_geo_series(geo_id)

    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=50)

    # Check strategy breakdown
    strategy_a = len(result.strategy_breakdown['strategy_a'])
    strategy_b = len(result.strategy_breakdown['strategy_b'])

    print(f"✓ Strategy A (citation): {strategy_a} papers")
    print(f"✓ Strategy B (mention): {strategy_b} papers")

    # At least one strategy should find papers
    assert strategy_a > 0 or strategy_b > 0, "No papers found by either strategy"


@pytest.mark.asyncio
async def test_ranking_by_citations():
    """Test ranking papers by citations + recency."""

    geo_id = "GSE103322"

    fetcher = GEOFetcher()
    metadata = await fetcher.fetch_geo_series(geo_id)

    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=100)

    # Filter and rank
    recent = filter_recent_publications(result.citing_papers, min_year=2020)
    ranked = sorted(
        recent,
        key=lambda p: (p.citations or 0, p.publication_date or datetime.min),
        reverse=True
    )[:20]

    # Verify ranking (first paper should have >= citations as second)
    if len(ranked) >= 2:
        assert (ranked[0].citations or 0) >= (ranked[1].citations or 0), \
            "Papers not properly ranked by citations"

    print(f"✓ Ranked {len(ranked)} papers by citations")

    # Print top 5 for visual verification
    for i, paper in enumerate(ranked[:5], 1):
        year = paper.publication_date.year if paper.publication_date else "Unknown"
        cites = paper.citations or 0
        print(f"  {i}. {paper.title[:60]}... ({year}, {cites} citations)")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_end_to_end_workflow():
    """Test complete workflow with all features."""

    geo_id = "GSE103322"
    min_year = 2020
    max_papers = 10

    print(f"\n{'='*60}")
    print(f"End-to-end test: {geo_id}")
    print(f"{'='*60}\n")

    # Step 1: Fetch GEO
    print("Step 1: Fetching GEO metadata...")
    fetcher = GEOFetcher()
    metadata = await fetcher.fetch_geo_series(geo_id)
    assert metadata.geo_id == geo_id
    print(f"✓ {metadata.title}")

    # Step 2: Find citing papers
    print("\nStep 2: Finding citing papers...")
    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=100)
    print(f"✓ Found {len(result.citing_papers)} total papers")

    # Step 3: Filter recent
    print(f"\nStep 3: Filtering to {min_year}+...")
    recent = filter_recent_publications(result.citing_papers, min_year=min_year)
    print(f"✓ {len(recent)} recent papers")

    # Step 4: Rank and select top N
    print(f"\nStep 4: Selecting top {max_papers}...")
    ranked = sorted(
        recent,
        key=lambda p: (p.citations or 0, p.publication_date or datetime.min),
        reverse=True
    )[:max_papers]
    print(f"✓ Top {len(ranked)} papers selected")

    # Step 5: Verify results
    print(f"\nStep 5: Verifying results...")
    for paper in ranked:
        assert paper.title, "Missing title"
        assert paper.authors, "Missing authors"
        # Year check
        if paper.publication_date:
            assert paper.publication_date.year >= min_year

    print(f"✓ All {len(ranked)} papers validated")

    print(f"\n{'='*60}")
    print("✅ End-to-end test PASSED")
    print(f"{'='*60}\n")
```

**Run Test**:
```bash
pytest tests/integration/test_geo_citation_tracking.py -v -s
```

---

## Implementation Checklist

### Day 2 Tasks (3-4 hours total)

- [ ] **Test Existing Code** (1 hour)
  - [ ] Create `tests/integration/test_geo_citation_tracking.py`
  - [ ] Run test with real GEO dataset (GSE103322)
  - [ ] Verify both citation strategies work
  - [ ] Check if publication dates are available
  - [ ] Document any issues found

- [ ] **Add Recency Filter** (15 minutes)
  - [ ] Create `omics_oracle_v2/lib/citations/filters.py`
  - [ ] Implement `filter_recent_publications()`
  - [ ] Implement `filter_last_n_years()`
  - [ ] Add unit tests

- [ ] **Create Usage Example** (1 hour)
  - [ ] Create `examples/geo_citation_tracking_example.py`
  - [ ] Add command-line interface
  - [ ] Add PDF download integration (if available)
  - [ ] Test with multiple GEO datasets
  - [ ] Add to `examples/README.md`

- [ ] **Documentation** (30 minutes)
  - [ ] Update main README with GEO citation tracking
  - [ ] Add to user guide
  - [ ] Document API usage
  - [ ] Add examples to documentation

- [ ] **Validation** (1 hour)
  - [ ] Run end-to-end integration test
  - [ ] Test with 3-5 different GEO datasets
  - [ ] Verify performance (< 30 seconds per dataset)
  - [ ] Check PDF downloads (if available)
  - [ ] User demo preparation

---

## Success Criteria

### Technical Validation ✅
- [ ] Can fetch GEO metadata with `pubmed_ids`
- [ ] Can find citing papers using both strategies
- [ ] Can filter papers by year range (2020-2025)
- [ ] Can rank papers by citations + recency
- [ ] Can limit to top N papers (10-20)
- [ ] (Optional) Can download PDFs

### Performance ✅
- [ ] GEO metadata fetch: < 5 seconds
- [ ] Citation discovery: < 20 seconds for 100 papers
- [ ] Recency filtering: < 1 second
- [ ] Total workflow: < 30 seconds
- [ ] PDF downloads: < 60 seconds for 10 papers

### User Experience ✅
- [ ] Simple command-line interface
- [ ] Clear progress messages
- [ ] Helpful error messages
- [ ] Results summary
- [ ] Optional PDF downloads

---

## Next Steps After Week 4 Day 2

### Option A: Implement Citation Scoring (Week 4 Day 3)
If user approves Tier 1 recommendation from research:
- Citations per year calculation
- Query intent detection
- Combined scoring
- **Estimated**: 4-6 hours

### Option B: Continue Original Plan (Week 4 Days 3-5)
- Day 3: Full-text extraction
- Day 4: Advanced ranking
- Day 5: Testing & validation

### Option C: User Feedback Loop
- Demo GEO citation tracking
- Gather user feedback
- Prioritize based on actual usage
- Defer advanced features to Month 2

---

## Files to Create (Summary)

### New Files (3):
1. `omics_oracle_v2/lib/citations/filters.py` - Recency filtering utilities
2. `examples/geo_citation_tracking_example.py` - Complete usage example
3. `tests/integration/test_geo_citation_tracking.py` - End-to-end test

### Files to Update (2):
1. `README.md` - Add GEO citation tracking to features
2. `examples/README.md` - Add geo_citation_tracking_example

### Documentation (Already Created):
1. `CITATION_INFRASTRUCTURE_INVENTORY.md` - This analysis ✅
2. `docs/research/citation_scoring_*.md` - Week 4 Day 1 research ✅

---

## Risk Assessment

### Low Risk ✅
- Infrastructure already exists and is production-ready
- Small code additions (< 200 lines total)
- No external dependencies
- Backward compatible

### Medium Risk ⚠️
- OpenAlex/Semantic Scholar API rate limits
- Publication dates may be missing for some papers
- PDF downloads may have institutional access issues

### Mitigation Strategies:
1. **Rate Limits**: Already handled with retry logic
2. **Missing Dates**: Filter gracefully, log warnings
3. **PDF Access**: Mark as "unavailable" rather than fail

---

## Conclusion

**We don't need to build this from scratch!**

The GEO citation tracking infrastructure is **90% complete**:
- `GEOCitationDiscovery` class does exactly what user wants
- All API clients are production-ready
- Only missing: recency filter (15 min) + examples (1-2 hours)

**Recommendation**:
1. Run integration test NOW to validate (1 hour)
2. Add recency filter (15 min)
3. Create example (1 hour)
4. Show user it works (demo)

**Total time**: 3-4 hours vs 9 hours originally proposed!

**Next action**: Run the integration test to verify everything works.
