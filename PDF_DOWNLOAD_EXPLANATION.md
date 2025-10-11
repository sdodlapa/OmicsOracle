# PDF Download Configuration - Why It's Disabled

**Date:** October 11, 2025
**Question:** Why are PDF downloads disabled? Are we passing output_dir or can it figure out where to save?

---

## 🎯 Answer: Intentionally Disabled in SearchAgent

### The Default Config Says "ENABLED"
```python
# omics_oracle_v2/lib/publications/config.py line 276
class PublicationSearchConfig:
    enable_pdf_download: bool = True  # ✅ Week 4 - ENABLED (default)
```

### But SearchAgent OVERRIDES It to "DISABLED"
```python
# omics_oracle_v2/agents/search_agent.py line 900
pub_search_config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_citations=self.enable_semantic,
    enable_pdf_download=False,  # ❌ EXPLICITLY DISABLED
    enable_fulltext=False,
    ...
)
```

**Why?** SearchAgent disables PDFs for **performance and scope**:
1. PDF downloads are slow (network I/O, large files)
2. Most use cases only need access URLs, not full PDFs
3. Storage costs (100 papers × 2MB = 200MB per search)
4. Week 4 feature not needed for Week 2 Day 4 validation

---

## 📁 Output Directory Configuration - HARDCODED

### PDFDownloadManager Requires output_dir Parameter
```python
# omics_oracle_v2/lib/storage/pdf/download_manager.py line 81
async def download_batch(
    self,
    publications: List[Publication],
    output_dir: Path,  # ✅ REQUIRED - Must be provided by caller
    url_field: str = "fulltext_url",
) -> DownloadReport:
    """Download PDFs for a batch of publications."""
    output_dir.mkdir(parents=True, exist_ok=True)  # Creates if doesn't exist
```

**The manager CANNOT figure out where to save on its own** - caller must specify.

### Pipeline HARDCODES the Path
```python
# omics_oracle_v2/lib/pipelines/publication_pipeline.py line 1040
def _download_pdfs(self, results: List[PublicationSearchResult]) -> None:
    """Download PDFs and extract full text."""

    # HARDCODED path - not configurable
    pdf_dir = Path("data/pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    download_report = asyncio.run(
        self.pdf_downloader.download_batch(
            publications=publications,
            output_dir=pdf_dir,  # ✅ Passes hardcoded path
            url_field="fulltext_url"
        )
    )
```

**Issue:** The output directory is **NOT configurable** - always saves to `data/pdfs/`.

---

## 🔍 Where PDFs Would Be Saved (If Enabled)

### Current Hardcoded Structure
```
data/pdfs/
├── <publication files>
└── ...
```

### Better Structure (Not Implemented)
```
data/pdfs/
├── pubmed/
│   ├── 12345678.pdf
│   └── 87654321.pdf
├── institutional/
│   ├── 10.1016_j.example.2025.01.001.pdf
│   └── 10.1038_s41586-025-12345-6.pdf
├── unpaywall/
│   └── ...
└── core/
    └── ...
```

The `PDFDownloadManager` doesn't organize by source - that would need to be added.

---

## 🚨 Configuration Gaps

### Gap #1: Output Directory Not Configurable

**Problem:** Hardcoded `Path("data/pdfs")` in pipeline

**Should be:**
```python
# In PublicationSearchConfig
pdf_output_dir: Path = Path("data/pdfs/publications")

# In pipeline
def _download_pdfs(self, results: List[PublicationSearchResult]) -> None:
    pdf_dir = self.config.pdf_output_dir  # ✅ Use config
    pdf_dir.mkdir(parents=True, exist_ok=True)
    ...
```

### Gap #2: No Source-Based Organization

**Problem:** All PDFs dumped in same directory

**Should be:**
```python
# PDFDownloadManager should accept source parameter
async def download_batch(
    self,
    publications: List[Publication],
    output_dir: Path,
    url_field: str = "fulltext_url",
    source_subdirs: bool = True,  # ✅ NEW - organize by source
) -> DownloadReport:
    if source_subdirs:
        # Detect source from URL or metadata
        source = self._detect_source(pub)
        pdf_path = output_dir / source / filename
    else:
        pdf_path = output_dir / filename
```

### Gap #3: Config Inconsistency

**Problem:** Default config says TRUE, SearchAgent says FALSE

**Options:**
1. **Keep as-is** - SearchAgent controls behavior (current)
2. **Make configurable** - Add parameter to SearchAgent constructor
3. **Respect default** - Remove override in SearchAgent

**Recommendation:** Add SearchAgent parameter for user control:
```python
class SearchAgent:
    def __init__(
        self,
        settings: Settings,
        enable_semantic: bool = False,
        enable_publications: bool = False,
        enable_pdf_download: bool = False,  # ✅ NEW - Let user decide
    ):
        self.enable_pdf_download = enable_pdf_download
        ...

        if self._use_unified_pipeline and enable_publications:
            pub_search_config = PublicationSearchConfig(
                enable_pdf_download=enable_pdf_download,  # ✅ Use parameter
                ...
            )
```

---

## 🔄 Current Flow (PDF Downloads Disabled)

### What Actually Happens in Tests

```
1. SearchAgent initialized
   └─> PublicationSearchConfig(enable_pdf_download=False)

2. PublicationSearchPipeline created
   └─> if config.enable_pdf_download:  # FALSE, so SKIPPED
           self.pdf_downloader = PDFDownloadManager(...)

3. Pipeline.search() executes
   ├─> Step 1: Search PubMed ✅
   ├─> Step 2: Get institutional access URLs ✅
   ├─> Step 3: Full-text waterfall (URL verification) ✅
   ├─> Step 4: Rank publications ✅
   ├─> Step 5: Semantic Scholar citations ✅
   └─> Step 6: PDF download ❌ SKIPPED (self.pdf_downloader is None)
```

**Result:** 398 institutional access URLs found, **0 PDFs downloaded**

---

## ✅ How to Enable PDF Downloads

### Option 1: Modify SearchAgent (Temporary)

```python
# In search_agent.py line 900
pub_search_config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_citations=self.enable_semantic,
    enable_pdf_download=True,  # ✅ CHANGE TO TRUE
    enable_fulltext=False,  # Keep FALSE for now (text extraction)
    ...
)
```

**Impact:**
- PDFs will download to `data/pdfs/`
- ~200MB storage per 100 papers (if 2MB average)
- Slower searches (~5-10s additional time)

### Option 2: Add Constructor Parameter (Better)

```python
# In search_agent.py
class SearchAgent:
    def __init__(
        self,
        settings: Settings,
        enable_semantic: bool = False,
        enable_publications: bool = False,
        enable_pdf_download: bool = False,  # ✅ NEW
    ):
        self.enable_pdf_download = enable_pdf_download
        ...

# In test file
agent = SearchAgent(
    settings,
    enable_semantic=True,
    enable_publications=True,
    enable_pdf_download=True  # ✅ Enable PDFs
)
```

### Option 3: Configuration File (Production)

```python
# config/settings.yaml
publication_search:
  enable_pdf_download: true
  pdf_output_dir: "data/pdfs/publications"
  pdf_organize_by_source: true
```

---

## 📊 Performance Impact of Enabling PDFs

### Current Performance (URLs Only)
```
Full-text enrichment: ~20s for 100 publications
  - Institutional access: 100/100 URLs (100% success)
  - No downloads: 0 bytes transferred
```

### Expected Performance (With PDFs)
```
Full-text enrichment: ~50-80s for 100 publications
  - URL discovery: ~20s (same)
  - PDF downloads: ~30-60s additional
    - 5 concurrent downloads
    - ~6-12s per batch of 5
    - ~100-200 MB total data transfer

Storage requirements:
  - 100 papers × 2MB avg = 200 MB per search
  - 1000 searches = 200 GB (need cleanup strategy)
```

---

## 🎯 Recommendations

### For Week 2 Day 4 (Current)
✅ **Keep PDFs disabled** - URL discovery is sufficient for validation
- All institutional access working (100% success)
- URLs can be used for on-demand download later
- Faster tests, less storage

### For Week 4 (Future)
1. **Make output_dir configurable**
   ```python
   class PublicationSearchConfig:
       pdf_output_dir: Path = Path("data/pdfs/publications")
   ```

2. **Add source-based organization**
   ```python
   data/pdfs/publications/
   ├── institutional/
   ├── unpaywall/
   ├── pmc/
   └── core/
   ```

3. **Add cleanup strategy**
   ```python
   # Delete PDFs older than 30 days
   # Keep only top N papers per search
   # Compress older PDFs
   ```

4. **Make SearchAgent configurable**
   ```python
   agent = SearchAgent(
       settings,
       enable_pdf_download=True,  # User control
       pdf_output_dir=Path("custom/path")  # Optional override
   )
   ```

### For Production
1. **Implement caching** - Don't re-download same paper
2. **Add storage limits** - Maximum storage quota
3. **Background downloads** - Don't block search results
4. **Deduplication** - Same paper from multiple sources = 1 PDF
5. **Monitoring** - Track storage usage, download success rates

---

## 📝 Summary

### Why PDFs Are Disabled
1. ❌ **SearchAgent explicitly sets** `enable_pdf_download=False` (line 900)
2. ✅ **Design decision** - Week 2-3 focus on URL discovery, not downloads
3. ✅ **Performance** - Faster tests, less storage
4. ✅ **Scope** - PDF text extraction is Week 4 feature

### Output Directory Handling
1. ✅ **Caller must provide** - `PDFDownloadManager.download_batch(output_dir=...)`
2. ❌ **Currently hardcoded** - Pipeline uses `Path("data/pdfs")`
3. ❌ **Not configurable** - No config option for custom path
4. ❌ **No source organization** - All PDFs in same directory

### To Enable Downloads
1. **Quick fix:** Change line 900 to `enable_pdf_download=True`
2. **Better fix:** Add constructor parameter
3. **Best fix:** Full configuration system with storage management

### Current State
- **URLs found:** 398/398 (100% success) ✅
- **PDFs downloaded:** 0/398 (disabled by design) ⚠️
- **Storage used:** 2.4 MB (2 old PDFs from Oct 7)
- **Test impact:** None (URLs are sufficient for validation)

---

**Next Steps:**
- ✅ Week 2 Day 4: Keep disabled (focus on URL discovery)
- ⏳ Week 4: Implement configurable PDF downloads with storage management
- ⏳ Production: Add caching, cleanup, and monitoring

**Document Created:** October 11, 2025 - 05:25 AM
