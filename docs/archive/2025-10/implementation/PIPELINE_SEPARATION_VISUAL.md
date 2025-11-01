# Pipeline Separation - Visual Guide

**Date**: October 14, 2025

---

## Current State (Tightly Coupled)

```
┌─────────────────────────────────────────────────────────────┐
│  lib/enrichment/fulltext/  (ALL MIXED TOGETHER)            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  manager.py (1,323 lines) ⚠️ DOES EVERYTHING               │
│  ├─ URL Collection (Pipeline 2) ✅                          │
│  ├─ PDF Download (Pipeline 3) ⚠️ Shouldn't be here        │
│  └─ Text Parsing (Pipeline 4) ⚠️ Shouldn't be here        │
│                                                             │
│  download_manager.py (543 lines) ✅ CLEAN                   │
│  └─ PDF Download (Pipeline 3) ✅                            │
│                                                             │
│  pdf_parser.py (46 lines) ⚠️ INCOMPLETE                     │
│  └─ Text Parsing (Pipeline 4) ⚠️ Only 10% done             │
│                                                             │
│  sources/ (11 source clients)                              │
│  └─ Used by Pipeline 2 ✅                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Problems:
❌ Can't test pipelines independently
❌ Changes ripple across pipelines
❌ Pipeline 4 incomplete and trapped
❌ Unclear responsibilities
```

---

## Proposed State (Clean Separation)

```
┌──────────────────────────────────────────────────────────────┐
│  lib/pipelines/                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 1_citation_discovery/  ✅ ALREADY ORGANIZED        │     │
│  │ └─ Pipeline 1: GEO → Papers                        │     │
│  └────────────────────────────────────────────────────┘     │
│                              │                               │
│                              ▼                               │
│                    [List[Publication]]                       │
│                              │                               │
│  ┌───────────────────────────▼────────────────────────┐     │
│  │ 2_url_collection/  🆕 MOVE FROM enrichment/        │     │
│  │ ├─ manager.py (URL collection only)                │     │
│  │ ├─ sources/ (11 sources)                           │     │
│  │ └─ models.py (FullTextResult)                      │     │
│  │                                                     │     │
│  │ INPUT:  List[Publication]                          │     │
│  │ OUTPUT: List[FullTextResult]                       │     │
│  └─────────────────────────────────────────────────────┘     │
│                              │                               │
│                              ▼                               │
│                  [List[FullTextResult]]                      │
│                              │                               │
│  ┌───────────────────────────▼────────────────────────┐     │
│  │ 3_pdf_download/  🆕 MOVE FROM enrichment/          │     │
│  │ ├─ manager.py (PDFDownloadManager)                 │     │
│  │ ├─ utils/ (landing_page_parser)                    │     │
│  │ └─ models.py (DownloadResult)                      │     │
│  │                                                     │     │
│  │ INPUT:  List[FullTextResult]                       │     │
│  │ OUTPUT: List[DownloadResult]                       │     │
│  └─────────────────────────────────────────────────────┘     │
│                              │                               │
│                              ▼                               │
│                  [List[DownloadResult]]                      │
│                              │                               │
│  ┌───────────────────────────▼────────────────────────┐     │
│  │ 4_text_enrichment/  🆕 IMPLEMENT (was incomplete)  │     │
│  │ ├─ manager.py (TextEnrichmentManager)              │     │
│  │ ├─ extractors/                                     │     │
│  │ │   ├─ grobid_client.py (GROBID integration) 🆕    │     │
│  │ │   ├─ pypdf_extractor.py (current)               │     │
│  │ │   └─ pdfminer_extractor.py (fallback) 🆕        │     │
│  │ ├─ enrichers/                                      │     │
│  │ │   ├─ section_detector.py 🆕                      │     │
│  │ │   ├─ table_extractor.py 🆕                       │     │
│  │ │   └─ normalizer.py                               │     │
│  │ ├─ formatters/                                     │     │
│  │ │   └─ chatgpt_formatter.py 🆕                     │     │
│  │ └─ models.py (EnrichmentResult, ParsedContent)     │     │
│  │                                                     │     │
│  │ INPUT:  List[DownloadResult]                       │     │
│  │ OUTPUT: List[EnrichmentResult]                     │     │
│  └─────────────────────────────────────────────────────┘     │
│                              │                               │
│                              ▼                               │
│                  [List[EnrichmentResult]]                    │
│                              │                               │
│                              ▼                               │
│                         ChatGPT ✅                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Benefits:
✅ Each pipeline testable independently
✅ Clear input/output contracts
✅ Single responsibility per pipeline
✅ Easy to add features to specific pipeline
✅ Pipeline 4 fully implemented
```

---

## Data Flow Comparison

### Current (Mixed)

```
Publication
    │
    ▼
┌─────────────────────────────────┐
│ FullTextManager                 │
│ .get_parsed_content()           │
│                                 │
│ ⚠️ DOES EVERYTHING:             │
│  1. Collect URLs                │
│  2. Download PDF                │
│  3. Parse PDF                   │
│  4. Return text                 │
│                                 │
│ Problem: Can't test stages     │
└─────────────────────────────────┘
    │
    ▼
Dict[str, any]
```

### Proposed (Separated)

```
Publication
    │
    ▼
┌─────────────────────────────────┐
│ Pipeline 2: URLCollectionManager│
│ .collect_urls_batch()           │
│                                 │
│ ✅ ONLY collects URLs           │
└─────────────────────────────────┘
    │
    ▼
FullTextResult (with all_urls)
    │
    ▼
┌─────────────────────────────────┐
│ Pipeline 3: PDFDownloadManager  │
│ .download_batch()               │
│                                 │
│ ✅ ONLY downloads PDFs          │
└─────────────────────────────────┘
    │
    ▼
DownloadResult (with pdf_path)
    │
    ▼
┌─────────────────────────────────┐
│ Pipeline 4: TextEnrichmentMgr   │
│ .enrich_batch()                 │
│                                 │
│ ✅ ONLY parses & enriches text  │
└─────────────────────────────────┘
    │
    ▼
EnrichmentResult (with structured content)
```

---

## Integration Contracts

### Contract 1→2: Publication → FullTextResult

```python
# INPUT (from Pipeline 1)
@dataclass
class Publication:
    title: str
    doi: Optional[str]
    pmid: Optional[str]
    pmcid: Optional[str]
    # ... other metadata

# OUTPUT (from Pipeline 2)
@dataclass
class FullTextResult:
    success: bool
    publication: Publication    # Original
    url: Optional[str]          # Best URL
    all_urls: List[SourceURL]   # All URLs (for fallback)
    source: Optional[str]
    error: Optional[str]
```

**Integration Point**:
```python
results = await url_collector.collect_urls_batch(publications)
```

---

### Contract 2→3: FullTextResult → DownloadResult

```python
# INPUT (from Pipeline 2)
@dataclass
class FullTextResult:
    all_urls: List[SourceURL]   # URLs to try
    publication: Publication

# OUTPUT (from Pipeline 3)
@dataclass
class DownloadResult:
    success: bool
    publication: Publication    # Original
    pdf_path: Optional[Path]    # Downloaded file
    source: Optional[str]       # Which URL worked
    file_size: int
    error: Optional[str]
```

**Integration Point**:
```python
download_results = await pdf_downloader.download_batch(
    fulltext_results,
    output_dir
)
```

---

### Contract 3→4: DownloadResult → EnrichmentResult

```python
# INPUT (from Pipeline 3)
@dataclass
class DownloadResult:
    pdf_path: Optional[Path]    # PDF to parse
    publication: Publication

# OUTPUT (from Pipeline 4)
@dataclass
class EnrichmentResult:
    success: bool
    publication: Publication    # Original
    pdf_path: Path             # Input PDF
    content: Optional[ParsedContent]  # Structured content
    chatgpt_ready: Optional[Dict]     # LLM-formatted
    error: Optional[str]

@dataclass
class ParsedContent:
    full_text: str
    sections: Dict[str, str]    # {section_name: text}
    tables: List[Dict]          # Extracted tables
    figures: List[Dict]         # Figure captions
    references: List[str]
    metadata: Dict
    extraction_method: str      # "grobid", "pypdf"
    quality_score: float        # 0.0-1.0
```

**Integration Point**:
```python
enrichment_results = await text_enricher.enrich_batch(
    download_results,
    include_chatgpt_format=True
)
```

---

## File Count Comparison

### Current Structure

```
lib/enrichment/fulltext/
├── manager.py                    # 1 file (1,323 lines - does too much)
├── download_manager.py           # 1 file (543 lines)
├── pdf_parser.py                 # 1 file (46 lines - incomplete)
├── sources/                      # 11 files
├── utils/                        # 2 files
└── support/                      # 7 files
                                  ─────────
Total: 23 files, ~3,500 lines
```

### Proposed Structure

```
lib/pipelines/
├── 2_url_collection/
│   ├── manager.py                # 1 file (~600 lines - URL only)
│   ├── config.py                 # 1 file
│   ├── models.py                 # 1 file
│   └── sources/                  # 11 files
│
├── 3_pdf_download/
│   ├── manager.py                # 1 file (543 lines)
│   ├── config.py                 # 1 file
│   ├── models.py                 # 1 file
│   └── utils/                    # 2 files
│
└── 4_text_enrichment/
    ├── manager.py                # 1 file (~400 lines - NEW)
    ├── config.py                 # 1 file
    ├── models.py                 # 1 file
    ├── extractors/               # 3 files (GROBID, pypdf, pdfminer)
    ├── enrichers/                # 3 files (sections, tables, normalizer)
    └── formatters/               # 1 file (ChatGPT formatter)

lib/shared/                       # Shared utilities
├── cache/                        # 3 files
├── validators/                   # 2 files
└── utils/                        # 2 files
                                  ─────────
Total: ~40 files, ~5,000 lines
(More files but better organized, +1,500 lines for Pipeline 4)
```

---

## Testing Strategy

### Current (Hard to Test)

```python
# Must mock 11 sources + HTTP + file system
@pytest.mark.asyncio
async def test_get_parsed_content():
    manager = FullTextManager()
    
    # ⚠️ Mocks required:
    # - 11 URL sources
    # - HTTP downloader
    # - File system
    # - PDF parser
    
    result = await manager.get_parsed_content(pub)
    
    # ⚠️ What failed? URL? Download? Parse?
    assert result is not None
```

---

### Proposed (Easy to Test)

```python
# Test Pipeline 2 alone
@pytest.mark.asyncio
async def test_url_collection():
    manager = URLCollectionManager()
    
    # Mock only URL sources
    with patch.object(manager, '_try_pmc', return_value=mock_result):
        results = await manager.collect_urls_batch([pub])
    
    assert isinstance(results[0], FullTextResult)
    assert results[0].success


# Test Pipeline 3 alone
@pytest.mark.asyncio
async def test_pdf_download():
    manager = PDFDownloadManager()
    
    # Mock only HTTP
    with aioresponses() as mocked:
        mocked.get('http://example.com/paper.pdf', body=mock_pdf_bytes)
        
        results = await manager.download_batch(fulltext_results, output_dir)
    
    assert isinstance(results[0], DownloadResult)
    assert results[0].pdf_path.exists()


# Test Pipeline 4 alone
@pytest.mark.asyncio
async def test_text_enrichment():
    manager = TextEnrichmentManager()
    
    # Mock only GROBID client
    with patch.object(manager.grobid_client, 'process', return_value=mock_xml):
        results = await manager.enrich_batch(download_results)
    
    assert isinstance(results[0], EnrichmentResult)
    assert 'Introduction' in results[0].content.sections
```

---

## Migration Timeline

```
Week 1-2: Pipeline 2 Extraction
├─ Create lib/pipelines/2_url_collection/
├─ Move manager.py + sources/
├─ Remove download/parse from manager
├─ Update all imports
└─ Create tests
    │
    ▼
Week 2-3: Pipeline 3 Extraction
├─ Create lib/pipelines/3_pdf_download/
├─ Move download_manager.py
├─ Update API to accept FullTextResult
├─ Update imports
└─ Create tests
    │
    ▼
Week 3-5: Pipeline 4 Implementation
├─ Create lib/pipelines/4_text_enrichment/
├─ Deploy GROBID service (Docker)
├─ Implement GROBID client
├─ Implement section detection
├─ Implement table extraction
├─ Implement ChatGPT formatter
├─ Create manager
└─ Create tests
    │
    ▼
Week 5-6: Integration & Testing
├─ Create end-to-end tests
├─ Update API to use separated pipelines
├─ Performance benchmarking
├─ Documentation
└─ Deployment
```

---

## Success Metrics

### Before Separation
- ❌ 1 monolithic manager (1,323 lines)
- ❌ Pipelines can't be tested independently
- ❌ Pipeline 4 only 10% complete
- ❌ Changes to one pipeline affect others
- ❌ Hard to understand data flow

### After Separation
- ✅ 4 independent pipelines
- ✅ Each pipeline fully testable
- ✅ Pipeline 4 100% complete
- ✅ Clear boundaries and contracts
- ✅ Easy to understand and maintain
- ✅ Ready for ChatGPT integration

---

## Risk Assessment

### Low Risk ✅
- Pipeline 3 already clean (easy move)
- Clear contracts defined
- Phased rollout possible

### Medium Risk ⚠️
- Pipeline 2 needs refactoring (remove download/parse)
- Many import updates needed
- Integration testing required

### High Risk (Mitigated) 🔴→✅
- Pipeline 4 GROBID implementation (NEW)
- **Mitigation**: Start with pypdf, add GROBID incrementally
- Can deploy Pipeline 4 in phases:
  1. Basic pypdf (Week 3)
  2. GROBID integration (Week 4)
  3. Enrichment features (Week 5)

---

## Recommendation: GO AHEAD ✅

**Why?**
1. Current structure is unmaintainable
2. Pipeline 4 is incomplete and trapped
3. Testing is difficult
4. ChatGPT integration blocked
5. Clean separation is industry best practice

**How?**
- Phased rollout (6 weeks)
- Each phase independently tested
- No breaking changes for users
- Can pause/adjust between phases

**When?**
- Start this week with Pipeline 2 extraction
- Complete by end of November 2025
