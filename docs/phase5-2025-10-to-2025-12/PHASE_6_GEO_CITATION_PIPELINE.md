# Phase 6: GEO-to-Citation-to-PDF Collection Pipeline

**Date:** October 10, 2025
**Status:** Planning & Design
**Sprint:** Phase 5 (October 2025 - December 2025)
**Priority:** High - Core Research Workflow

---

## 🎯 Executive Summary

**Objective:** Build an end-to-end automated pipeline that:
1. Takes a user's research query
2. Finds relevant GEO datasets
3. Discovers all publications citing those datasets
4. Collects full-text PDFs of citing papers
5. Organizes collected resources for downstream LLM analysis

**Key Principle:** **SEPARATION OF CONCERNS**
- **Phase 6:** Pure data collection (search + download)
- **Phase 7 (Future):** LLM analysis of collected PDFs

**Budget Impact:** $0 for collection phase (no LLM calls)

---

## 📊 Problem Statement

### Current Limitation
The existing `PublicationSearchPipeline` was designed for:
- Direct publication search (PubMed, Google Scholar)
- Citation enrichment WITH LLM analysis (expensive!)
- Mixed concerns (search + analysis in same layer)

### User's Actual Workflow
Biomedical researchers need to:
1. Find datasets relevant to their query (e.g., "breast cancer RNA-seq")
2. Identify all papers that **reused** those datasets
3. Collect full-text papers to **manually review** dataset usage
4. Later decide: analyze with LLM or read manually

**Gap:** No pipeline connects GEO → Citations → PDFs without expensive LLM analysis

---

## 🏗️ Architecture Design

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: GEO Citation Collection Pipeline                   │
│ (NO LLM - Pure Data Collection)                             │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ 1. Query Input   │ User: "breast cancer RNA-seq TCGA"
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Synonym Expansion (Optional)                              │
│ ────────────────────────────────────────────────────────────│
│ • breast cancer → mammary carcinoma, breast neoplasm        │
│ • RNA-seq → transcriptome sequencing, RNA sequencing        │
│                                                              │
│ Component: omics_oracle_v2/lib/nlp/synonym_expansion.py    │
│ Config: SynonymExpansionConfig                              │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. GEO Dataset Discovery                                     │
│ ────────────────────────────────────────────────────────────│
│ • Search NCBI GEO with expanded terms                       │
│ • Retrieve datasets: GSE12345, GSE23456, ...                │
│ • Extract metadata:                                          │
│   - GEO ID                                                   │
│   - Title                                                    │
│   - Summary                                                  │
│   - PubMed IDs (original publication)                       │
│   - Sample count, platform info                             │
│                                                              │
│ Component: omics_oracle_v2/lib/geo/client.py               │
│ Model: GEOSeriesMetadata                                    │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Citation Discovery (Dual Strategy)                        │
│ ────────────────────────────────────────────────────────────│
│ Strategy A: Papers citing original publication              │
│   • Use PMID from GEO metadata                              │
│   • OpenAlex: get_citing_papers(doi=...)                   │
│   • Semantic Scholar: search citations                      │
│                                                              │
│ Strategy B: Papers mentioning GEO ID                        │
│   • PubMed search: GSE12345[All Fields]                    │
│   • Google Scholar: "GSE12345"                              │
│   • Text mining: full-text mentions                         │
│                                                              │
│ Output: Merged list of citing publications (deduplicated)   │
│                                                              │
│ Component: omics_oracle_v2/lib/publications/citations/      │
│ Analyzer: CitationAnalyzer (existing)                       │
│ NEW: GEOCitationDiscovery (to be built)                    │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Full-Text URL Collection                                  │
│ ────────────────────────────────────────────────────────────│
│ WATERFALL STRATEGY (optimized order):                       │
│                                                              │
│ Priority 1: Institutional Access (Georgia Tech)             │
│   • Direct DOI links                                        │
│   • Coverage: ~50% (highest quality)                        │
│   • Cost: $0                                                │
│                                                              │
│ Priority 2: Unpaywall (Open Access)                         │
│   • Legal OA repositories                                   │
│   • Coverage: +30-40%                                       │
│   • Cost: $0                                                │
│                                                              │
│ Priority 3: CORE.ac.uk                                      │
│   • Academic paper repository                               │
│   • Coverage: +10-15%                                       │
│   • Cost: $0                                                │
│                                                              │
│ Priority 4: Europe PMC                                      │
│   • European biomedical repository                          │
│   • Coverage: +5-10%                                        │
│   • Cost: $0                                                │
│                                                              │
│ Priority 5: Sci-Hub (OPTIMIZED - only working mirrors)      │
│   • Mirrors: se, ru, ren, ee (4 working)                   │
│   • Patterns: embed_any_src, iframe_any_src (2 working)    │
│   • Coverage: +15-20%                                       │
│   • Cost: $0, Legal: ⚠️ Gray area                          │
│                                                              │
│ Priority 6: LibGen                                          │
│   • Book Gen mirrors                                        │
│   • Coverage: +5-10%                                        │
│   • Cost: $0, Legal: ⚠️ Gray area                          │
│                                                              │
│ Component: omics_oracle_v2/lib/publications/fulltext_manager.py │
│ OPTIMIZATION: Skip source if paper found in higher priority │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. PDF Download & Organization                               │
│ ────────────────────────────────────────────────────────────│
│ Download Strategy:                                           │
│   • Use aiohttp for async parallel downloads                │
│   • Rate limiting per source                                │
│   • Retry failed downloads (3 attempts)                     │
│   • Validate PDF integrity (magic bytes)                    │
│                                                              │
│ Storage Structure:                                           │
│   data/geo_citation_collections/                            │
│   └── GSE12345_collection/                                  │
│       ├── metadata.json            # GEO + publication info │
│       ├── citing_papers.json       # All citing papers      │
│       ├── fulltext_urls.json       # URLs by source         │
│       ├── collection_report.json   # Coverage metrics       │
│       └── pdfs/                                             │
│           ├── original_PMID12345.pdf                        │
│           ├── citing_PMID23456.pdf                          │
│           └── citing_PMID34567.pdf                          │
│                                                              │
│ Component: NEW - PDFDownloadManager (to be built)          │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. Collection Report                                         │
│ ────────────────────────────────────────────────────────────│
│ Metrics:                                                     │
│   • Total datasets found                                    │
│   • Total citing papers discovered                          │
│   • Full-text coverage by source                            │
│   • PDF download success rate                               │
│   • Failed papers (for manual review)                       │
│   • Storage size                                            │
│   • Collection duration                                     │
│                                                              │
│ Output: JSON report + Human-readable summary                │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Components

### 1. New Components (To Build)

#### `GEOCitationPipeline` (Main Orchestrator)
**File:** `omics_oracle_v2/lib/workflows/geo_citation_pipeline.py`

```python
class GEOCitationPipeline:
    """
    End-to-end pipeline: Query → GEO → Citations → PDFs

    Features:
    - No LLM analysis (pure collection)
    - Optimized full-text retrieval (waterfall strategy)
    - Progress tracking & resumable downloads
    - Comprehensive reporting
    """

    async def collect(
        self,
        query: str,
        max_datasets: int = 10,
        max_citing_papers: int = 100,
        download_pdfs: bool = True
    ) -> CollectionResult
```

#### `GEOCitationDiscovery` (Citation Search)
**File:** `omics_oracle_v2/lib/publications/citations/geo_citation_discovery.py`

```python
class GEOCitationDiscovery:
    """
    Find papers citing GEO datasets.

    Two strategies:
    1. Papers citing original publication (PMID)
    2. Papers mentioning GEO ID in text
    """

    async def find_citing_papers(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100
    ) -> List[Publication]
```

#### `PDFDownloadManager` (PDF Downloads)
**File:** `omics_oracle_v2/lib/publications/pdf_download_manager.py`

```python
class PDFDownloadManager:
    """
    Async PDF download with validation and organization.

    Features:
    - Parallel downloads (configurable concurrency)
    - Rate limiting per source
    - Retry logic
    - PDF validation
    - Progress tracking
    """

    async def download_batch(
        self,
        publications: List[Publication],
        output_dir: Path,
        max_concurrent: int = 5
    ) -> DownloadReport
```

### 2. Modified Components (Optimizations)

#### `FullTextManager` Optimization
**File:** `omics_oracle_v2/lib/publications/fulltext_manager.py`

**Changes:**
1. **Reorder sources** by effectiveness (institutional → OA → Sci-Hub)
2. **Skip sources** for papers already found
3. **Remove broken Sci-Hub mirrors** (st, si, wf, tf, mksa.top)
4. **Remove ineffective patterns** (12 patterns with 0% success rate)
5. **Add success tracking** for performance metrics

**Before:**
```python
self.sources = [
    "unpaywall", "core", "europe_pmc", "crossref",
    "institutional", "scihub", "libgen", "arxiv", "biorxiv"
]
```

**After:**
```python
self.sources = [
    "institutional",  # Priority 1: Georgia Tech (~50%)
    "unpaywall",      # Priority 2: Legal OA (~30-40%)
    "core",           # Priority 3: CORE.ac.uk (~10-15%)
    "europe_pmc",     # Priority 4: Europe PMC (~5-10%)
    "scihub",         # Priority 5: Sci-Hub (optimized, ~15-20%)
    "libgen",         # Priority 6: LibGen (~5-10%)
    # Removed: crossref (no full-text), arxiv/biorxiv (specialized)
]
```

#### `SciHubClient` Optimization
**File:** `omics_oracle_v2/lib/publications/clients/scihub_client.py`

**Changes:**
1. **Remove broken mirrors:** st, si, wf, tf, mksa.top
2. **Keep working mirrors:** se, ru, ren, ee (23.9% success rate each)
3. **Remove ineffective patterns:** All patterns except:
   - `embed_any_src` (14.3% success rate)
   - `iframe_any_src` (5.3% success rate)
4. **Faster failure detection:** Try 2 patterns instead of 14

**Performance Impact:**
- **Before:** 92 papers × 9 mirrors × 14 patterns = 11,592 attempts (19.56 min)
- **After:** 92 papers × 4 mirrors × 2 patterns = 736 attempts (~2-3 min)
- **Speedup:** ~7x faster with same success rate

---

## 📂 Data Organization

### Collection Directory Structure

```
data/
└── geo_citation_collections/
    ├── GSE12345_breast_cancer_collection/
    │   ├── metadata.json
    │   ├── citing_papers.json
    │   ├── fulltext_urls.json
    │   ├── collection_report.json
    │   └── pdfs/
    │       ├── original_PMID12345.pdf
    │       ├── citing_PMID23456.pdf
    │       └── ...
    │
    ├── GSE23456_lung_cancer_collection/
    │   └── ...
    │
    └── index.json  # All collections metadata
```

### File Formats

#### `metadata.json`
```json
{
  "collection_id": "GSE12345_breast_cancer_collection",
  "created_at": "2025-10-10T16:30:00Z",
  "query": "breast cancer RNA-seq",
  "geo_dataset": {
    "geo_id": "GSE12345",
    "title": "Breast Cancer RNA-seq Study",
    "summary": "...",
    "pubmed_ids": ["12345678"],
    "sample_count": 96
  },
  "original_publication": {
    "pmid": "12345678",
    "doi": "10.1038/nature...",
    "title": "...",
    "authors": ["..."]
  }
}
```

#### `citing_papers.json`
```json
{
  "total_citing_papers": 145,
  "discovery_methods": {
    "citation_of_original_pmid": 120,
    "geo_id_mentions": 25
  },
  "citing_papers": [
    {
      "pmid": "23456789",
      "doi": "10.1016/j.cell...",
      "title": "...",
      "citation_context": "used dataset GSE12345"
    }
  ]
}
```

#### `fulltext_urls.json`
```json
{
  "total_papers": 145,
  "fulltext_found": 125,
  "coverage_rate": 0.862,
  "sources_breakdown": {
    "institutional": {"count": 65, "percentage": 44.8},
    "unpaywall": {"count": 35, "percentage": 24.1},
    "core": {"count": 15, "percentage": 10.3},
    "scihub": {"count": 10, "percentage": 6.9}
  },
  "urls": [
    {
      "pmid": "23456789",
      "source": "institutional",
      "url": "https://doi.org/10.1016/j.cell...",
      "pdf_downloaded": true,
      "filename": "citing_PMID23456789.pdf"
    }
  ]
}
```

#### `collection_report.json`
```json
{
  "collection_summary": {
    "geo_datasets_found": 3,
    "total_citing_papers": 287,
    "fulltext_coverage": 0.845,
    "pdfs_downloaded": 243,
    "failed_downloads": 44
  },
  "performance_metrics": {
    "total_duration_seconds": 450,
    "geo_search_time": 12.3,
    "citation_discovery_time": 78.5,
    "fulltext_retrieval_time": 245.8,
    "pdf_download_time": 113.4
  },
  "source_effectiveness": {
    "institutional": {"attempts": 287, "success": 140, "rate": 0.488},
    "unpaywall": {"attempts": 147, "success": 68, "rate": 0.463},
    "scihub": {"attempts": 79, "success": 35, "rate": 0.443}
  }
}
```

---

## 🎯 Success Criteria

### Phase 6.1: Core Pipeline (Week 1-2)
- [ ] GEOCitationPipeline class implemented
- [ ] Query → GEO dataset search working
- [ ] Citation discovery (both strategies) working
- [ ] Full-text URL collection working
- [ ] Basic reporting functional

### Phase 6.2: Optimization (Week 2-3)
- [ ] Sci-Hub client optimized (4 mirrors, 2 patterns)
- [ ] FullTextManager waterfall optimized
- [ ] Institutional access prioritized
- [ ] Skip-on-success logic implemented
- [ ] Performance metrics tracked

### Phase 6.3: PDF Download (Week 3-4)
- [ ] PDFDownloadManager implemented
- [ ] Async parallel downloads working
- [ ] PDF validation (magic bytes check)
- [ ] Retry logic functional
- [ ] Storage organization complete

### Phase 6.4: Testing & Validation (Week 4)
- [ ] Test with 1 dataset, ~20 citing papers
- [ ] Validate coverage > 80%
- [ ] Verify no LLM costs incurred
- [ ] Test resumable downloads
- [ ] Documentation complete

---

## 📊 Expected Performance

### Coverage Targets
| Source | Expected Coverage | Cumulative | Cost |
|--------|------------------|------------|------|
| Institutional | 45-50% | 50% | $0 |
| Unpaywall | 25-30% | 75-80% | $0 |
| CORE | 10-15% | 85-90% | $0 |
| Sci-Hub (optimized) | 5-10% | 90-95% | $0 |
| LibGen | 2-5% | 92-97% | $0 |

### Performance Targets
- **GEO search:** < 10s per query
- **Citation discovery:** < 60s per dataset
- **Full-text URL collection:** < 5s per paper
- **PDF download:** < 10s per PDF
- **Total for 100 papers:** < 20 minutes

### Cost Targets
- **LLM costs:** $0 (no analysis in Phase 6)
- **API costs:** $0 (free APIs only)
- **Storage:** ~500MB per 100 papers

---

## 🔍 Sci-Hub Optimization Analysis

### Data Source
File: `scihub_exploration_results.json`
Test Date: October 10, 2025, 02:36 AM
Papers Tested: 92
Total Attempts: 828 (9 mirrors × 92 papers)
Duration: 19.56 minutes

### Findings

#### Working Mirrors (Keep - 23.9% success rate)
1. **sci-hub.se** ✅
   - Success: 22/92 (23.9%)
   - Pattern: embed_any_src
   - Status: Active and reliable

2. **sci-hub.ru** ✅
   - Success: 22/92 (23.9%)
   - Pattern: embed_any_src
   - Status: Active and reliable

3. **sci-hub.ren** ✅
   - Success: 22/92 (23.9%)
   - Pattern: embed_any_src
   - Status: Active and reliable

4. **sci-hub.ee** ✅
   - Success: 22/92 (23.9%)
   - Pattern: iframe_any_src
   - Status: Active (uses different pattern)

#### Broken Mirrors (Remove - 0% success rate)
1. **sci-hub.st** ❌ - 0/0 attempts (timeout/unreachable)
2. **sci-hub.si** ❌ - 0/0 attempts (timeout/unreachable)
3. **sci-hub.wf** ❌ - 0/92 (0% success)
4. **sci-hub.tf** ❌ - 0/92 (0% success)
5. **sci-hub.mksa.top** ❌ - 0/92 (0% success)

#### Working Patterns (Keep)
1. **embed_any_src** ✅
   - Success: 66/460 (14.3%)
   - Used by: se, ru, ren
   - Description: `<embed src="...">`

2. **iframe_any_src** ✅
   - Success: 22/416 (5.3%)
   - Used by: ee
   - Description: `<iframe src="...">`

#### Ineffective Patterns (Remove - 0% success)
1. embed_pdf_src ❌
2. iframe_pdf_src ❌
3. meta_redirect ❌
4. js_location ❌
5. button_onclick ❌
6. download_link ❌
7. protocol_relative ❌
8. absolute_https ❌
9. absolute_http ❌
10. data_attribute ❌
11. pdfjs_viewer ❌
12. response_url ❌

### Optimization Impact
- **Mirrors:** 9 → 4 (55% reduction)
- **Patterns:** 14 → 2 (86% reduction)
- **Attempts per paper:** 126 → 8 (94% reduction)
- **Expected speedup:** 7-10x faster
- **Success rate:** UNCHANGED (23.9%)

---

## 🚀 Implementation Plan

### Phase 6.1: Foundation (Days 1-3)
1. **Day 1:** Create `GEOCitationPipeline` skeleton
   - Define configuration classes
   - Setup directory structure
   - Implement basic flow

2. **Day 2:** Integrate existing components
   - GEO client integration
   - Citation analyzer integration
   - Full-text manager integration

3. **Day 3:** Build citation discovery
   - Implement `GEOCitationDiscovery`
   - Strategy A: PMID citations
   - Strategy B: GEO ID mentions
   - Deduplication logic

### Phase 6.2: Optimization (Days 4-6)
4. **Day 4:** Optimize Sci-Hub client
   - Remove 5 broken mirrors
   - Remove 12 ineffective patterns
   - Add performance metrics
   - Test speedup

5. **Day 5:** Optimize FullTextManager
   - Reorder sources by priority
   - Implement skip-on-success
   - Add source tracking
   - Performance benchmarks

6. **Day 6:** Integrate optimizations
   - Update pipeline to use optimized clients
   - Test coverage with optimized sources
   - Validate performance improvements

### Phase 6.3: PDF Downloads (Days 7-10)
7. **Day 7:** Build PDFDownloadManager
   - Async download logic
   - Rate limiting
   - Retry mechanism
   - PDF validation

8. **Day 8:** Storage organization
   - Implement directory structure
   - Metadata file generation
   - Report generation
   - Index management

9. **Day 9:** Progress tracking
   - Add progress bars
   - Implement resumable downloads
   - Failed download tracking
   - Logging system

10. **Day 10:** Error handling
    - Network error handling
    - Timeout handling
    - Invalid PDF handling
    - Cleanup on failure

### Phase 6.4: Testing (Days 11-14)
11. **Day 11:** Unit tests
    - Test GEOCitationPipeline
    - Test GEOCitationDiscovery
    - Test PDFDownloadManager
    - Test optimizations

12. **Day 12:** Integration tests
    - End-to-end flow test
    - Test with real GEO dataset
    - Validate coverage metrics
    - Test error scenarios

13. **Day 13:** Performance testing
    - Benchmark with 100 papers
    - Validate <20 min target
    - Test concurrent downloads
    - Memory usage profiling

14. **Day 14:** Documentation
    - User guide
    - API documentation
    - Configuration guide
    - Troubleshooting guide

---

## 📝 Configuration Examples

### Basic Usage
```python
from omics_oracle_v2.lib.workflows import GEOCitationPipeline

# Initialize pipeline
pipeline = GEOCitationPipeline(
    enable_synonym_expansion=True,
    max_concurrent_downloads=5,
    enable_scihub=True  # Optional: disable for legal-only
)

# Collect papers
result = await pipeline.collect(
    query="breast cancer RNA-seq TCGA",
    max_datasets=5,
    max_citing_papers=100,
    download_pdfs=True
)

print(f"Found {result.total_citing_papers} citing papers")
print(f"Coverage: {result.fulltext_coverage:.1%}")
print(f"Downloaded: {result.pdfs_downloaded} PDFs")
```

### Advanced Configuration
```python
from omics_oracle_v2.lib.workflows import (
    GEOCitationPipeline,
    GEOCitationConfig
)

config = GEOCitationConfig(
    # GEO search
    geo_max_results=10,
    geo_min_samples=10,

    # Citation discovery
    citation_max_results=100,
    include_geo_id_mentions=True,
    include_pmid_citations=True,

    # Full-text retrieval
    fulltext_sources=[
        "institutional",  # Prioritize institutional
        "unpaywall",
        "core",
        "scihub"
    ],
    skip_on_success=True,  # Skip sources after finding

    # PDF download
    download_pdfs=True,
    max_concurrent_downloads=5,
    pdf_validation=True,
    retry_failed=True,
    max_retries=3,

    # Storage
    output_dir="data/geo_citation_collections",
    organize_by_geo_id=True
)

pipeline = GEOCitationPipeline(config)
result = await pipeline.collect("breast cancer RNA-seq")
```

---

## 🔒 Legal & Ethical Considerations

### Institutional Access (✅ Fully Legal)
- **Georgia Tech subscription** - Authorized use
- **Highest priority** - Use first before other sources

### Open Access Sources (✅ Fully Legal)
- **Unpaywall** - Legal OA aggregator
- **CORE** - Legal academic repository
- **Europe PMC** - Legal biomedical repository

### Sci-Hub & LibGen (⚠️ Gray Area)
- **Legal status:** Varies by jurisdiction
- **Recommendation:** Make optional (user choice)
- **Default:** Enabled but skippable via config
- **Priority:** Use only after legal sources exhausted

### Best Practices
1. **Prioritize legal sources** (institutional + OA)
2. **Measure coverage** before enabling Sci-Hub
3. **Respect rate limits** on all APIs
4. **Cache responsibly** to minimize requests
5. **Document all sources** in metadata

---

## 📈 Phase 7 Preview (Future)

**After Phase 6 collection completes**, Phase 7 will add:

### LLM Analysis Layer
- **PDF text extraction** (PyMuPDF, pdfplumber)
- **Dataset reuse detection** (mention of GEO ID)
- **Usage type classification** (validation, comparison, meta-analysis)
- **Relevance scoring** (how central is dataset to paper?)
- **Key findings extraction** (what did they discover?)

### Analysis Pipeline
```python
# Phase 7 (Future)
from omics_oracle_v2.lib.analysis import CitationAnalysisLLM

analyzer = CitationAnalysisLLM(
    provider="openai",  # or "anthropic" or "local"
    model="gpt-4-turbo",
    cache_enabled=True
)

# Analyze collected PDFs
analysis = await analyzer.analyze_collection(
    collection_id="GSE12345_breast_cancer_collection",
    focus="dataset_reuse"
)
```

**Key Separation:**
- **Phase 6:** Collection (this document) - $0 cost
- **Phase 7:** Analysis (future) - Optional LLM costs
- **User decides** when to spend on LLM analysis

---

## 🎯 Next Steps

### Immediate (This Session)
1. ✅ Create Phase 6 document (this file)
2. ⏳ Optimize Sci-Hub client (remove broken mirrors/patterns)
3. ⏳ Optimize FullTextManager (reorder sources, skip-on-success)
4. ⏳ Test optimized full-text retrieval (small scale)

### Short-term (Next Session)
5. Build GEOCitationPipeline skeleton
6. Implement GEOCitationDiscovery
7. Test end-to-end flow (1 dataset)

### Medium-term (Next Week)
8. Build PDFDownloadManager
9. Implement storage organization
10. Complete comprehensive testing

### Long-term (Phase 7)
11. PDF text extraction
12. LLM analysis integration
13. Results visualization

---

## 📚 References

### Existing Components
- `omics_oracle_v2/lib/geo/client.py` - GEO dataset search
- `omics_oracle_v2/lib/publications/citations/analyzer.py` - Citation discovery
- `omics_oracle_v2/lib/publications/fulltext_manager.py` - Full-text retrieval
- `omics_oracle_v2/lib/nlp/synonym_expansion.py` - Query expansion

### Data Sources
- **NCBI GEO:** https://www.ncbi.nlm.nih.gov/geo/
- **OpenAlex:** https://openalex.org/
- **Semantic Scholar:** https://www.semanticscholar.org/
- **Unpaywall:** https://unpaywall.org/
- **CORE:** https://core.ac.uk/

### Documentation
- Sci-Hub exploration: `scihub_exploration_results.json`
- Full-text strategy: `FULLTEXT_ACCESS_STRATEGY.md`
- Phase 5 overview: `docs/phase5-2025-10-to-2025-12/00-overview/`

---

**Document Version:** 1.0
**Last Updated:** October 10, 2025
**Next Review:** After Phase 6.1 completion
