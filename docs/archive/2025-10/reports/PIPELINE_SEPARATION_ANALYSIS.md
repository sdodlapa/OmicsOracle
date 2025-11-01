# Pipeline 2, 3, 4 Separation Analysis & Reorganization Plan

**Date**: October 14, 2025  
**Status**: Analysis Complete, Ready for Implementation

---

## 🎯 Executive Summary

Currently, Pipelines 2, 3, and 4 are **tightly coupled** in `lib/enrichment/fulltext/`, making them difficult to test, maintain, and evolve independently. This document analyzes the current organization and proposes a clean separation strategy with well-defined integration points.

---

## 📊 Current Organization

### Current File Structure

```
omics_oracle_v2/lib/enrichment/fulltext/
├── manager.py                    # Pipeline 2: URL Collection (1,323 lines) ⚠️ MIXED
├── download_manager.py           # Pipeline 3: PDF Download (543 lines) ✅ CLEAN
├── pdf_parser.py                 # Pipeline 4: Text Parsing (46 lines) ✅ CLEAN but INCOMPLETE
│
├── sources/                      # Pipeline 2 components
│   ├── institutional_access.py
│   ├── scihub_client.py
│   ├── libgen_client.py
│   └── oa_sources/
│       ├── pmc_client.py
│       ├── core_client.py
│       ├── biorxiv_client.py
│       ├── arxiv_client.py
│       ├── crossref_client.py
│       └── unpaywall_client.py
│
├── utils/                        # Shared utilities
│   ├── pdf_utils.py
│   └── logging_utils.py
│
└── support/                      # Supporting modules
    ├── cache_db.py
    ├── smart_cache.py
    ├── parsed_cache.py
    ├── landing_page_parser.py    # Used by Pipeline 3
    ├── url_validator.py
    └── normalizer.py
```

---

## 🔍 Pipeline Responsibilities Analysis

### Pipeline 2: URL Collection (`manager.py`)

**Primary Purpose**: Collect full-text URLs from 11+ sources using waterfall strategy

**Key Classes**:
- `FullTextManager` - Main orchestrator (1,323 lines)
- `FullTextManagerConfig` - Configuration
- `FullTextResult` - Output format
- `SourceURL` - URL metadata

**Public API Methods**:
```python
# Main API (what other pipelines should use)
async def get_fulltext_batch(publications: List[Publication]) -> List[FullTextResult]
async def get_all_fulltext_urls(publication: Publication) -> FullTextResult

# Internal waterfall methods (should be private)
async def _try_pmc(publication: Publication) -> FullTextResult
async def _try_unpaywall(publication: Publication) -> FullTextResult
async def _try_core(publication: Publication) -> FullTextResult
# ... 8 more _try_* methods
```

**Current Issues** ⚠️:
1. **Mixes concerns**: URL collection + PDF downloading + text parsing
2. **Tight coupling**: Directly instantiates source clients
3. **Hard to test**: 11 sources = complex mocking
4. **No clear boundaries**: Public API vs internal methods not well separated

**Dependencies**:
- Input: `Publication` objects from Pipeline 1
- Output: `FullTextResult` with URLs
- Uses: 11 source clients, cache, URL validator

---

### Pipeline 3: PDF Download (`download_manager.py`)

**Primary Purpose**: Download and validate PDFs from URLs

**Key Classes**:
- `PDFDownloadManager` - Main downloader (543 lines)
- `DownloadResult` - Single download result
- `DownloadReport` - Batch summary

**Public API Methods**:
```python
async def download_with_fallback(
    publication: Publication,
    urls: List[SourceURL],  # From Pipeline 2
    output_dir: Path
) -> DownloadResult

async def download_batch(
    publications: List[Publication],
    output_dir: Path
) -> DownloadReport
```

**Current Status** ✅:
- **Well separated**: Clear input/output boundaries
- **Single responsibility**: Only downloads and validates PDFs
- **Testable**: Easy to mock HTTP requests
- **Clean API**: Clear integration point with Pipeline 2

**Dependencies**:
- Input: URLs from Pipeline 2 (`FullTextResult.all_urls`)
- Output: `DownloadResult` with PDF paths
- Uses: `landing_page_parser`, `pdf_utils`, HTTP client

---

### Pipeline 4: Text Parsing/Enrichment (`pdf_parser.py`)

**Primary Purpose**: Extract and enrich text from PDFs

**Key Classes**:
- `PDFExtractor` - Basic text extraction (46 lines)

**Public API Methods**:
```python
@staticmethod
def extract_text(pdf_path: Path) -> Optional[Dict[str, any]]
```

**Current Status** ⚠️:
- **Incomplete**: Only basic pypdf extraction (10% complete)
- **Missing GROBID**: No structured extraction
- **Missing enrichment**: No section detection, table extraction, etc.
- **No batch processing**: Only single-file API

**What's Missing** (from spec):
1. GROBID integration (structured extraction)
2. Multi-strategy parsing (GROBID → pdfminer → pypdf fallback)
3. Text normalization and cleaning
4. Section extraction (Intro, Methods, Results, Discussion)
5. Table/figure extraction
6. Reference parsing
7. ChatGPT-ready formatting

**Dependencies**:
- Input: PDF paths from Pipeline 3
- Output: Structured text data
- Uses: pypdf (currently), GROBID (planned)

---

## 🚨 Current Integration Problems

### Problem 1: Tight Coupling in `manager.py`

**Issue**: `FullTextManager` does too much:

```python
# manager.py lines 883-1001
async def get_parsed_content(self, publication: Publication) -> Optional[Dict]:
    """
    PROBLEM: Pipeline 2 (URL collection) calling Pipeline 4 (text parsing)
    This violates separation of concerns!
    """
    # 1. Get URLs (Pipeline 2 responsibility) ✅
    result = await self.get_fulltext(publication)
    
    # 2. Download PDF (Pipeline 3 responsibility) ⚠️
    if result.success and result.url:
        # Downloads PDF here...
    
    # 3. Parse PDF (Pipeline 4 responsibility) ⚠️
    if pdf_path.exists():
        from omics_oracle_v2.lib.enrichment.fulltext.pdf_parser import PDFExtractor
        # Parses PDF here...
```

**Impact**: Can't test/use pipelines independently

---

### Problem 2: Unclear Data Flow

**Current flow** (mixed responsibilities):

```
Publication → manager.get_parsed_content() → Dict
                 ├─ URL collection (P2) ✅
                 ├─ PDF download (P3) ⚠️ Should be separate
                 └─ Text parsing (P4) ⚠️ Should be separate
```

**Should be**:

```
Publication → P2.get_urls() → FullTextResult
              ↓
FullTextResult → P3.download() → DownloadResult  
                  ↓
DownloadResult → P4.parse() → ParsedContent
```

---

### Problem 3: No Integration Contracts

**Missing**:
- Clear input/output types for each pipeline
- Batch processing at each stage
- Error handling between stages
- Progress tracking across pipelines

---

## 💡 Proposed Reorganization

### New Structure

```
omics_oracle_v2/lib/pipelines/
├── 1_citation_discovery/        # Pipeline 1 ✅ (already organized)
│   ├── geo_discovery.py
│   └── clients/
│
├── 2_url_collection/            # Pipeline 2 (NEW - move from enrichment/)
│   ├── __init__.py
│   ├── manager.py               # URL collection orchestrator
│   ├── config.py                # Configuration
│   ├── models.py                # FullTextResult, SourceURL
│   └── sources/                 # Source clients
│       ├── __init__.py
│       ├── institutional_access.py
│       ├── pmc_client.py
│       ├── unpaywall_client.py
│       └── ... (11 total)
│
├── 3_pdf_download/              # Pipeline 3 (NEW - move from enrichment/)
│   ├── __init__.py
│   ├── manager.py               # PDFDownloadManager
│   ├── config.py                # Configuration
│   ├── models.py                # DownloadResult, DownloadReport
│   └── utils/
│       ├── landing_page_parser.py
│       └── validators.py
│
└── 4_text_enrichment/           # Pipeline 4 (NEW - expand from pdf_parser.py)
    ├── __init__.py
    ├── manager.py               # TextEnrichmentManager (NEW)
    ├── config.py                # Configuration
    ├── models.py                # ParsedContent, EnrichmentResult
    ├── extractors/
    │   ├── grobid_client.py     # GROBID integration (TODO)
    │   ├── pypdf_extractor.py   # Current implementation
    │   └── pdfminer_extractor.py # Fallback (TODO)
    ├── enrichers/
    │   ├── section_detector.py  # Extract sections (TODO)
    │   ├── table_extractor.py   # Extract tables (TODO)
    │   └── normalizer.py        # Text cleaning
    └── formatters/
        └── chatgpt_formatter.py # ChatGPT-ready output (TODO)

# Shared utilities (used by multiple pipelines)
omics_oracle_v2/lib/shared/
├── cache/
│   ├── cache_db.py
│   ├── smart_cache.py
│   └── parsed_cache.py
├── validators/
│   ├── pdf_validator.py
│   └── url_validator.py
└── utils/
    ├── pdf_utils.py
    └── logging_utils.py
```

---

## 🔗 Integration Points (Contracts)

### Integration Point 1→2: Citation Discovery → URL Collection

**Input**: `List[Publication]` from Pipeline 1

**Output**: `List[FullTextResult]`

**Contract**:
```python
@dataclass
class FullTextResult:
    """Output from Pipeline 2 (URL Collection)"""
    success: bool
    publication: Publication  # Original publication
    url: Optional[str]        # Best URL found
    all_urls: List[SourceURL] # All URLs for fallback
    source: Optional[FullTextSource]
    error: Optional[str]
    metadata: Dict = field(default_factory=dict)
```

**API**:
```python
# In lib/pipelines/2_url_collection/manager.py
class URLCollectionManager:
    async def collect_urls_batch(
        self, 
        publications: List[Publication]
    ) -> List[FullTextResult]:
        """Collect URLs for batch of publications."""
        pass
```

---

### Integration Point 2→3: URL Collection → PDF Download

**Input**: `List[FullTextResult]` from Pipeline 2

**Output**: `List[DownloadResult]`

**Contract**:
```python
@dataclass
class DownloadResult:
    """Output from Pipeline 3 (PDF Download)"""
    success: bool
    publication: Publication  # Original publication
    pdf_path: Optional[Path]  # Downloaded PDF location
    source: Optional[str]     # Which URL worked
    file_size: int
    error: Optional[str]
```

**API**:
```python
# In lib/pipelines/3_pdf_download/manager.py
class PDFDownloadManager:
    async def download_batch(
        self,
        fulltext_results: List[FullTextResult],  # From Pipeline 2
        output_dir: Path
    ) -> List[DownloadResult]:
        """Download PDFs from fulltext results."""
        pass
```

---

### Integration Point 3→4: PDF Download → Text Enrichment

**Input**: `List[DownloadResult]` from Pipeline 3

**Output**: `List[EnrichmentResult]`

**Contract**:
```python
@dataclass
class ParsedContent:
    """Parsed and structured PDF content"""
    full_text: str
    sections: Dict[str, str]  # {section_name: text}
    tables: List[Dict]        # Extracted tables
    figures: List[Dict]       # Figure captions
    references: List[str]     # Citations
    metadata: Dict            # Page count, etc.
    extraction_method: str    # "grobid", "pypdf", etc.
    quality_score: float      # 0.0-1.0

@dataclass
class EnrichmentResult:
    """Output from Pipeline 4 (Text Enrichment)"""
    success: bool
    publication: Publication  # Original publication
    pdf_path: Path           # Input PDF
    content: Optional[ParsedContent]  # Parsed content
    chatgpt_ready: Optional[Dict]     # Formatted for LLM
    error: Optional[str]
```

**API**:
```python
# In lib/pipelines/4_text_enrichment/manager.py
class TextEnrichmentManager:
    async def enrich_batch(
        self,
        download_results: List[DownloadResult],  # From Pipeline 3
        include_chatgpt_format: bool = True
    ) -> List[EnrichmentResult]:
        """Enrich PDFs with structured extraction and formatting."""
        pass
```

---

## 🔄 End-to-End Integration Example

### Current (Tightly Coupled)

```python
# In API - everything in one place
fulltext_manager = FullTextManager(config)
await fulltext_manager.initialize()

for publication in publications:
    # This does EVERYTHING - can't test independently
    parsed_data = await fulltext_manager.get_parsed_content(publication)
    # ⚠️ Mixed: URL collection + download + parsing
```

---

### Proposed (Clean Separation)

```python
# In API - clear pipeline stages
from omics_oracle_v2.lib.pipelines import (
    URLCollectionManager,
    PDFDownloadManager,
    TextEnrichmentManager
)

# Initialize all pipelines
url_collector = URLCollectionManager(config)
pdf_downloader = PDFDownloadManager(download_config)
text_enricher = TextEnrichmentManager(enrichment_config)

await url_collector.initialize()

# Stage 1: Collect URLs (Pipeline 2)
logger.info("Stage 1: Collecting URLs...")
fulltext_results = await url_collector.collect_urls_batch(publications)
logger.info(f"Found URLs for {sum(r.success for r in fulltext_results)}/{len(publications)}")

# Stage 2: Download PDFs (Pipeline 3)
logger.info("Stage 2: Downloading PDFs...")
download_results = await pdf_downloader.download_batch(
    fulltext_results,
    output_dir=Path("data/pdfs")
)
logger.info(f"Downloaded {sum(r.success for r in download_results)}/{len(fulltext_results)}")

# Stage 3: Parse and Enrich (Pipeline 4)
logger.info("Stage 3: Enriching text...")
enrichment_results = await text_enricher.enrich_batch(
    download_results,
    include_chatgpt_format=True
)
logger.info(f"Enriched {sum(r.success for r in enrichment_results)}/{len(download_results)}")

# Now each publication has: URLs, PDF, and enriched content
for pub, url_res, dl_res, enrich_res in zip(
    publications, fulltext_results, download_results, enrichment_results
):
    if enrich_res.success:
        print(f"{pub.title}")
        print(f"  PDF: {dl_res.pdf_path}")
        print(f"  Sections: {list(enrich_res.content.sections.keys())}")
        print(f"  Quality: {enrich_res.content.quality_score:.1%}")
```

---

## 📋 Migration Steps

### Phase 1: Extract Pipeline 2 (URL Collection)

**Week 1**:

1. ✅ **Create new structure**:
   ```bash
   mkdir -p omics_oracle_v2/lib/pipelines/2_url_collection
   ```

2. ✅ **Move files**:
   - `manager.py` → `2_url_collection/manager.py`
   - `sources/` → `2_url_collection/sources/`
   - Create `models.py` with `FullTextResult`, `SourceURL`
   - Create `config.py` with `URLCollectionConfig`

3. ✅ **Refactor manager.py**:
   - Remove `get_parsed_content()` (Pipeline 4 responsibility)
   - Keep only URL collection methods
   - Simplify to pure URL collection

4. ✅ **Update imports** in:
   - `api/routes/agents.py`
   - `extras/pipelines/geo_citation_pipeline.py`
   - Tests

5. ✅ **Create tests**:
   - `tests/pipelines/test_url_collection.py`

---

### Phase 2: Extract Pipeline 3 (PDF Download)

**Week 2**:

1. ✅ **Create new structure**:
   ```bash
   mkdir -p omics_oracle_v2/lib/pipelines/3_pdf_download
   ```

2. ✅ **Move files**:
   - `download_manager.py` → `3_pdf_download/manager.py`
   - `landing_page_parser.py` → `3_pdf_download/utils/`
   - Create `models.py` with `DownloadResult`, `DownloadReport`
   - Create `config.py` with `DownloadConfig`

3. ✅ **Update API**:
   - Accept `List[FullTextResult]` instead of publications
   - Extract URLs from `FullTextResult.all_urls`

4. ✅ **Update imports** and tests

---

### Phase 3: Implement Pipeline 4 (Text Enrichment)

**Week 3-4**:

1. ✅ **Create structure**:
   ```bash
   mkdir -p omics_oracle_v2/lib/pipelines/4_text_enrichment/{extractors,enrichers,formatters}
   ```

2. ✅ **Implement GROBID**:
   - Deploy GROBID service (Docker)
   - Create `grobid_client.py`
   - Parse TEI XML → structured sections

3. ✅ **Implement enrichment**:
   - Section detection
   - Table extraction
   - Normalization
   - ChatGPT formatting

4. ✅ **Create manager**:
   - Multi-strategy extraction (GROBID → pdfminer → pypdf)
   - Quality scoring
   - Batch processing

5. ✅ **Create tests**

---

### Phase 4: Move Shared Utilities

**Week 5**:

1. ✅ **Create shared structure**:
   ```bash
   mkdir -p omics_oracle_v2/lib/shared/{cache,validators,utils}
   ```

2. ✅ **Move shared code**:
   - `cache_db.py`, `smart_cache.py` → `shared/cache/`
   - `pdf_utils.py` → `shared/utils/`
   - `url_validator.py` → `shared/validators/`

3. ✅ **Update all imports**

---

### Phase 5: Integration & Testing

**Week 6**:

1. ✅ **Create integration tests**:
   - Test Pipeline 2 → 3 handoff
   - Test Pipeline 3 → 4 handoff
   - Test end-to-end flow

2. ✅ **Update API**:
   - Use new separated pipelines
   - Add progress tracking
   - Error handling between stages

3. ✅ **Performance testing**:
   - Benchmark each pipeline
   - Optimize bottlenecks

4. ✅ **Documentation**:
   - Update architecture docs
   - Create integration guides

---

## ✅ Benefits of Separation

### 1. **Independent Testing** ✅

```python
# Test Pipeline 2 alone
def test_url_collection():
    manager = URLCollectionManager()
    results = await manager.collect_urls_batch(mock_publications)
    assert all(isinstance(r, FullTextResult) for r in results)

# Test Pipeline 3 alone
def test_pdf_download():
    manager = PDFDownloadManager()
    results = await manager.download_batch(mock_fulltext_results, output_dir)
    assert all(isinstance(r, DownloadResult) for r in results)

# Test Pipeline 4 alone
def test_text_enrichment():
    manager = TextEnrichmentManager()
    results = await manager.enrich_batch(mock_download_results)
    assert all(isinstance(r, EnrichmentResult) for r in results)
```

---

### 2. **Independent Evolution** ✅

- Add new URL sources without touching download logic
- Upgrade PDF parser without affecting URL collection
- Swap GROBID for better parser without changing download

---

### 3. **Clear Contracts** ✅

Each pipeline has:
- Well-defined input type
- Well-defined output type
- Single responsibility
- Easy to understand

---

### 4. **Better Error Handling** ✅

```python
# Can fail gracefully at each stage
url_results = await url_collector.collect_urls_batch(pubs)
# 80% success rate - continue with successful ones

successful_urls = [r for r in url_results if r.success]
dl_results = await pdf_downloader.download_batch(successful_urls, output_dir)
# 70% success rate - continue

successful_dls = [r for r in dl_results if r.success]
enrich_results = await text_enricher.enrich_batch(successful_dls)
# 90% success rate
```

---

### 5. **Easier Debugging** ✅

- Know exactly which pipeline failed
- Can replay from any stage
- Clear input/output at each boundary

---

## 🎯 Recommendation

**I strongly recommend this separation**. Here's why:

### Current Problems:
1. ❌ Can't test pipelines independently
2. ❌ Changes to URL collection affect download logic
3. ❌ Pipeline 4 is incomplete and trapped in Pipeline 2
4. ❌ Hard to add new features (e.g., GROBID)
5. ❌ Unclear what each file is responsible for

### After Separation:
1. ✅ Each pipeline testable in isolation
2. ✅ Clear boundaries and contracts
3. ✅ Can implement Pipeline 4 properly
4. ✅ Easy to add features to specific pipelines
5. ✅ Clear, organized structure

### Effort vs Reward:
- **Effort**: ~6 weeks (with testing)
- **Reward**: 
  - Maintainable codebase
  - Testable components
  - Complete Pipeline 4
  - Ready for production ChatGPT integration

---

## 📝 Next Steps

**If you approve this plan**:

1. **Week 1-2**: Extract Pipeline 2 (URL Collection)
2. **Week 2-3**: Extract Pipeline 3 (PDF Download)  
3. **Week 3-5**: Implement Pipeline 4 (Text Enrichment + GROBID)
4. **Week 5-6**: Integration testing and deployment

**Or we can do phased rollout**:
- Phase 1: Extract P2 only (2 weeks)
- Phase 2: Extract P3 only (2 weeks)
- Phase 3: Implement P4 (2-3 weeks)

**What do you think?** Should we:
1. Go with full separation (recommended)
2. Start with just Pipeline 2 extraction
3. Something else?
