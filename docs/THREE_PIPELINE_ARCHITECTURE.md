# Complete Three-Pipeline Architecture: Citation → URLs → Downloads

**Date:** October 14, 2025  
**Discovery:** User identified the system actually has **3 separate pipelines**, not 2!  
**Status:** Production System - Complete Flow Documented

---

## 🎯 Executive Summary

OmicsOracle uses **THREE DISTINCT PIPELINES**:

1. **PIPELINE 1: Citation Discovery** (2 sources)
   - **Purpose:** Find WHICH papers cite/use GEO dataset
   - **Sources:** PubMed + OpenAlex
   - **Output:** List[Publication] with metadata only

2. **PIPELINE 2: URL Collection** (11 sources) 
   - **Purpose:** Find WHERE to download each paper
   - **Sources:** Institutional, PMC, Unpaywall, CORE, OpenAlex, Crossref, bioRxiv, arXiv, Sci-Hub, LibGen, Cache
   - **Output:** URLs (sorted by priority) for each paper

3. **PIPELINE 3: PDF Download** (waterfall with retry)
   - **Purpose:** Actually DOWNLOAD PDFs from URLs
   - **Sources:** Uses URLs from Pipeline 2
   - **Output:** Downloaded PDF files + validation

**Critical Understanding:**
- Pipeline 2 does **NOT download** - it only collects URLs
- Pipeline 3 does the actual downloading using those URLs
- Pipeline 2 queries 11 APIs to find URLs
- Pipeline 3 tries those URLs in priority order with retry logic

---

## 🌳 Complete Three-Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST (Frontend)                          │
│              "Find and download papers citing GSE189158"                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API ENDPOINT (FastAPI Route)                          │
│  File: omics_oracle_v2/api/routes/agents.py                             │
│  Route: POST /api/search/geo                                             │
│  Handler: enrich_with_fulltext()                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
    ┌────────────────────────┐      ┌────────────────────────┐
    │  STEP 1: Get original  │      │  STEP 2: Find citing   │
    │  paper metadata        │      │  papers                │
    │  (PubMedClient)        │      │  (GEOCitationDiscovery)│
    └────────────┬───────────┘      └───────────┬────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                    Combined: 11 papers
                    (1 original + 10 citing)
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
┌──────────────────────────────┐  ┌──────────────────────────────────┐
│   PIPELINE 1:                │  │   PIPELINE 2:                    │
│   CITATION DISCOVERY         │  │   URL COLLECTION                 │
│                              │  │                                  │
│   Who: GEOCitationDiscovery  │  │   Who: FullTextManager           │
│   File: geo_discovery.py     │  │   File: manager.py               │
│                              │  │                                  │
│   Purpose: Find WHICH papers │  │   Purpose: Find WHERE to         │
│            cite dataset      │  │            download papers       │
│                              │  │                                  │
│   Method: 2-strategy search  │  │   Method: 11-source waterfall    │
│   - PubMed (mentions)        │  │   - Queries each source's API    │
│   - OpenAlex (citations)     │  │   - Collects ALL URLs            │
│                              │  │   - Sorts by priority            │
│   API Calls: 3 per dataset   │  │   API Calls: Up to 11 per paper  │
│   Time: 0.8-1.7 sec          │  │   Time: 2-3 sec per paper        │
│                              │  │                                  │
│   Output:                    │  │   Output:                        │
│   List[Publication]          │  │   List[SourceURL]                │
│   - pmid                     │  │   - url                          │
│   - doi                      │  │   - source (institutional/pmc/   │
│   - title                    │  │            unpaywall/etc)        │
│   - authors                  │  │   - priority (1-11)              │
│   - NO URLs                  │  │   - url_type (PDF/HTML/landing)  │
│                              │  │   - confidence                   │
└──────────────┬───────────────┘  └──────────────┬───────────────────┘
               │                                 │
               │                                 │
               └────────────┬────────────────────┘
                            │
                            ▼
                  For each paper, we now have:
                  - Metadata (from Pipeline 1)
                  - URLs (from Pipeline 2)
                            │
                            ▼
               ┌────────────────────────────────┐
               │   PIPELINE 3:                  │
               │   PDF DOWNLOAD                 │
               │                                │
               │   Who: PDFDownloadManager      │
               │   File: download_manager.py    │
               │                                │
               │   Purpose: Actually DOWNLOAD   │
               │            PDFs from URLs      │
               │                                │
               │   Method: Waterfall with retry │
               │   - Try URL #1 (highest pri)   │
               │   - If fails, try URL #2       │
               │   - If fails, try URL #3       │
               │   - Stop at first success      │
               │                                │
               │   Retry Logic:                 │
               │   - 2 attempts per URL         │
               │   - 1.5 sec delay between      │
               │   - PDF validation (magic bytes│
               │   - Landing page detection &   │
               │     extraction                 │
               │                                │
               │   API Calls: NONE              │
               │   (uses URLs from Pipeline 2)  │
               │                                │
               │   HTTP Requests:               │
               │   - Downloads actual files     │
               │   - Follows redirects          │
               │   - SSL bypass for self-signed │
               │   - User-Agent spoofing        │
               │                                │
               │   Time: 0.5-2 sec per PDF      │
               │                                │
               │   Output:                      │
               │   DownloadResult               │
               │   - success: bool              │
               │   - pdf_path: Path             │
               │   - file_size: int             │
               │   - source: str (which URL won)│
               │   - error: str (if failed)     │
               └────────────┬───────────────────┘
                            │
                            ▼
                  Downloaded PDFs saved to:
                  data/pdfs/{geo_id}/{original|citing}/
                            │
                            ▼
                   Return to Frontend
                   (with PDF paths + URLs)
```

---

## 📊 PIPELINE 1: Citation Discovery (Find Papers)

### File
```
omics_oracle_v2/lib/citations/discovery/geo_discovery.py
```

### Class
```python
GEOCitationDiscovery
```

### Methods
```python
async def find_citing_papers(geo_metadata, max_results=100)
    ├─ _find_via_citation(pmid)      # Strategy A: OpenAlex
    └─ _find_via_geo_mention(geo_id) # Strategy B: PubMed
```

### Data Sources (2)

| Source | API | Purpose | Output |
|--------|-----|---------|--------|
| PubMed | NCBI E-utilities | Find papers mentioning "GSE189158" | Metadata only |
| OpenAlex | OpenAlex API | Find papers citing DOI | Metadata only |

### Example Output
```python
CitationDiscoveryResult(
    geo_id="GSE189158",
    original_pmid="33199918",
    citing_papers=[
        Publication(
            pmid="34567890",
            doi="10.1038/s41467-021-12345-x",
            title="Multi-omics analysis...",
            authors=["Smith J", "Doe A"],
            # NO URLS YET!
        ),
        # ... 9 more papers
    ],
    strategy_breakdown={
        "strategy_a": ["34567890", "35678901"],
        "strategy_b": ["36789012", "37890123"]
    }
)
```

---

## 📥 PIPELINE 2: URL Collection (Find Download Locations)

### File
```
omics_oracle_v2/lib/enrichment/fulltext/manager.py
```

### Class
```python
FullTextManager
```

### Methods
```python
async def get_all_fulltext_urls(publication) -> FullTextResult
    │
    ├─ _check_cache()                    # Priority 0
    ├─ _try_institutional_access()       # Priority 1
    ├─ _try_pmc()                        # Priority 2
    ├─ _try_unpaywall()                  # Priority 3
    ├─ _try_core()                       # Priority 4
    ├─ _try_openalex_oa_url()           # Priority 5
    ├─ _try_crossref()                   # Priority 6
    ├─ _try_biorxiv()                    # Priority 7a
    ├─ _try_arxiv()                      # Priority 7b
    ├─ _try_scihub()                     # Priority 8
    └─ _try_libgen()                     # Priority 9
```

### Data Sources (11)

| # | Source | API/Method | What It Returns |
|---|--------|------------|-----------------|
| 0 | Cache | SQLite DB | Previously found URLs |
| 1 | Institutional | Shibboleth/EZProxy | Authenticated URLs |
| 2 | PMC | NCBI E-utilities | PMC open access URLs |
| 3 | Unpaywall | REST API | Repository URLs |
| 4 | CORE | REST API | PDF download URLs |
| 5 | OpenAlex | REST API | Publisher OA URLs |
| 6 | Crossref | REST API | Publisher TDM URLs |
| 7a | bioRxiv | REST API | Preprint PDF URLs |
| 7b | arXiv | REST API | Preprint PDF URLs |
| 8 | Sci-Hub | Web scraping | Mirror URLs |
| 9 | LibGen | Web scraping | Download URLs |

### Important: This Pipeline Does NOT Download!

**What it DOES:**
- Queries APIs to find URLs
- Validates URL accessibility
- Sorts URLs by priority
- Returns URL list

**What it DOES NOT do:**
- Download PDFs
- Save files to disk
- Validate PDF content

### Example Output
```python
FullTextResult(
    success=True,
    source=FullTextSource.UNPAYWALL,  # Highest priority URL
    url="https://europepmc.org/articles/PMC8891234?pdf=render",
    all_urls=[
        SourceURL(
            url="https://example.edu/authenticated/paper.pdf",
            source=FullTextSource.INSTITUTIONAL,
            priority=1,
            url_type=URLType.PDF,
            confidence=0.95
        ),
        SourceURL(
            url="https://europepmc.org/articles/PMC8891234?pdf=render",
            source=FullTextSource.UNPAYWALL,
            priority=3,
            url_type=URLType.PDF,
            confidence=0.90
        ),
        SourceURL(
            url="https://www.biorxiv.org/content/10.1101/2023.01.01.123456v1.full.pdf",
            source=FullTextSource.BIORXIV,
            priority=7,
            url_type=URLType.PDF,
            confidence=0.85
        ),
        SourceURL(
            url="https://sci-hub.st/10.1038/nature12345",
            source=FullTextSource.SCIHUB,
            priority=8,
            url_type=URLType.LANDING_PAGE,
            confidence=0.75
        )
    ]
)
```

---

## ⬇️ PIPELINE 3: PDF Download (Actually Get Files)

### File
```
omics_oracle_v2/lib/enrichment/fulltext/download_manager.py
```

### Class
```python
PDFDownloadManager
```

### Methods
```python
async def download_with_fallback(publication, all_urls, output_dir)
    ├─ _sort_urls_by_type_and_priority()  # Sort: PDF > HTML > Landing
    └─ For each URL (in sorted order):
        ├─ _download_single(url)           # Try downloading
        │   ├─ HTTP GET request
        │   ├─ Follow redirects (max 10)
        │   ├─ Read content
        │   ├─ Validate PDF magic bytes
        │   ├─ Handle landing pages
        │   └─ Save to disk
        ├─ Retry if failed (max 2 attempts)
        └─ STOP at first success
```

### Key Features

**1. Type-Aware Sorting:**
```python
Priority Order:
1. PDF Direct URLs        (fastest)
2. HTML Full-text URLs    (need parsing)
3. Landing Pages          (slowest, need extraction)

Within each type, sorted by source priority.
```

**2. Retry Logic:**
```python
- 2 attempts per URL
- 1.5 second delay between attempts
- Exponential backoff
```

**3. PDF Validation:**
```python
- Check magic bytes: b"%PDF-"
- Detect HTML landing pages
- Extract PDF links from landing pages
- Validate file size (> 10KB)
```

**4. Landing Page Handling:**
```python
If HTML received:
  ├─ Parse page with BeautifulSoup
  ├─ Find <embed src="*.pdf"> tags
  ├─ Find <iframe src="*.pdf"> tags
  ├─ Extract PDF URL
  └─ Retry download with extracted URL
```

**5. HTTP Configuration:**
```python
- SSL verification disabled (self-signed certs)
- User-Agent spoofing (avoid bot detection)
- Follow redirects (DOI resolution)
- 30 second timeout per URL
- Rate limiting (semaphore)
```

### Example Execution Flow

```python
Input: 4 URLs from Pipeline 2

Step 1: Sort by type and priority
  └─ Sorted: [PDF/priority=1, PDF/priority=3, Landing/priority=8, HTML/priority=4]

Step 2: Try URL #1 (Institutional PDF)
  ├─ Attempt 1: HTTP GET → 403 Forbidden (not on campus)
  ├─ Attempt 2: HTTP GET → 403 Forbidden
  └─ FAIL (move to next URL)

Step 3: Try URL #2 (Unpaywall PDF)
  ├─ Attempt 1: HTTP GET → 200 OK
  ├─ Content: 2.3 MB
  ├─ Validate: Starts with b"%PDF-" ✓
  ├─ Save: data/pdfs/GSE189158/citing/pmid_34567890.pdf
  └─ SUCCESS! (stop here, skip remaining URLs)

Final result:
  - Downloaded from: Unpaywall
  - File: pmid_34567890.pdf (2.3 MB)
  - Status: success
```

### Example Output
```python
DownloadResult(
    publication=publication,
    success=True,
    pdf_path=Path("data/pdfs/GSE189158/citing/pmid_34567890.pdf"),
    source="unpaywall",  # Which URL succeeded
    file_size=2411520,   # 2.3 MB
    error=None
)
```

---

## 🔄 Complete End-to-End Flow Example

### User Request
**Search:** "breast cancer RNA-seq"  
**Dataset:** GSE189158  
**Action:** Click "Download Papers"

```
═══════════════════════════════════════════════════════════════════════════
PIPELINE 1: CITATION DISCOVERY (Find WHICH papers)
═══════════════════════════════════════════════════════════════════════════

Input: GEO metadata for GSE189158
  - geo_id: "GSE189158"
  - pubmed_ids: ["33199918"]

Step 1.1: Strategy A (Citation-Based)
  ├─ PubMed: Fetch PMID 33199918
  │  └─ DOI: 10.1038/s41467-020-19517-z
  │
  └─ OpenAlex: Query papers citing DOI
     └─ Found: 8 papers

Step 1.2: Strategy B (Mention-Based)
  └─ PubMed: Search "GSE189158[All Fields]"
     └─ Found: 3 papers

Step 1.3: Deduplicate
  └─ Combined: 10 unique papers (1 overlap removed)

Output: List[Publication] with NO URLs
  - Paper 1: PMID 34567890, DOI 10.1038/...
  - Paper 2: PMID 35678901, DOI 10.1016/...
  - ... (8 more)

═══════════════════════════════════════════════════════════════════════════
PIPELINE 2: URL COLLECTION (Find WHERE to download)
═══════════════════════════════════════════════════════════════════════════

For Paper #1 (PMID 34567890):

  Query all 11 sources in parallel:
  
  ├─ Cache → ❌ Not found
  ├─ Institutional → ✅ Found: https://example.edu/paper.pdf
  ├─ PMC → ❌ No PMCID
  ├─ Unpaywall → ✅ Found: https://europepmc.org/articles/PMC8891234.pdf
  ├─ CORE → ❌ Not found
  ├─ OpenAlex → ❌ No OA URL
  ├─ Crossref → ❌ No TDM link
  ├─ bioRxiv → ❌ Not a preprint
  ├─ arXiv → ❌ Not a preprint
  ├─ Sci-Hub → ✅ Found: https://sci-hub.st/10.1038/...
  └─ LibGen → ❌ Not found

  Output: 3 URLs found
    1. https://example.edu/paper.pdf (priority=1, type=PDF)
    2. https://europepmc.org/articles/PMC8891234.pdf (priority=3, type=PDF)
    3. https://sci-hub.st/10.1038/... (priority=8, type=LANDING)

═══════════════════════════════════════════════════════════════════════════
PIPELINE 3: PDF DOWNLOAD (Actually download PDFs)
═══════════════════════════════════════════════════════════════════════════

For Paper #1 (3 URLs from Pipeline 2):

  Sort URLs by type + priority:
    1. Institutional (PDF, priority=1)
    2. Unpaywall (PDF, priority=3)
    3. Sci-Hub (Landing, priority=8)

  Try URL #1: Institutional
    ├─ Attempt 1: HTTP GET → 403 Forbidden (not on campus network)
    ├─ Attempt 2: HTTP GET → 403 Forbidden
    └─ FAIL (try next URL)

  Try URL #2: Unpaywall
    ├─ Attempt 1: HTTP GET → 200 OK
    ├─ Read content: 2.3 MB
    ├─ Validate: Starts with b"%PDF-" ✓
    ├─ Save: data/pdfs/GSE189158/citing/pmid_34567890.pdf
    └─ SUCCESS! (stop, skip remaining URLs)

  Output:
    ✅ Downloaded from Unpaywall
    📄 File: pmid_34567890.pdf (2.3 MB)
    📁 Location: data/pdfs/GSE189158/citing/

═══════════════════════════════════════════════════════════════════════════
REPEAT FOR ALL 10 PAPERS
═══════════════════════════════════════════════════════════════════════════

... (Pipeline 2 + 3 repeated for remaining 9 papers)

Final Statistics:
  - Papers found: 10 (Pipeline 1)
  - Papers with URLs: 9 (Pipeline 2)
  - Papers downloaded: 8 (Pipeline 3)
  - Total size: 18.4 MB
  - Time: ~35 seconds
    * Pipeline 1: 1.2 sec
    * Pipeline 2: 22 sec (2.4 sec × 9 papers)
    * Pipeline 3: 12 sec (1.5 sec × 8 papers)
```

---

## 📈 Performance Comparison

### Per Paper Processing Time

| Pipeline | Purpose | API Calls | HTTP Requests | Time |
|----------|---------|-----------|---------------|------|
| **1: Citation Discovery** | Find papers | 3 | 0 | 0.8-1.7 sec per dataset |
| **2: URL Collection** | Find URLs | Up to 11 | 0-11 | 2-3 sec per paper |
| **3: PDF Download** | Get files | 0 | 1-4 | 0.5-2 sec per paper |

### For 1 GEO Dataset with 10 Citing Papers

```
Pipeline 1 (once): ~1 second
Pipeline 2 (10x): ~25 seconds  (2.5 sec × 10)
Pipeline 3 (10x): ~15 seconds  (1.5 sec × 10)
───────────────────────────────────────────
Total:            ~41 seconds

Success rate: 85-90%
```

---

## 🎯 Key Design Decisions

### Why Separate URL Collection from Download?

**Advantages:**
1. **Retry without re-querying APIs**
   - Collect URLs once
   - Try downloading multiple times
   - No repeated API calls

2. **Parallel fallback**
   - Have all URLs upfront
   - Try in priority order
   - Fast failover

3. **Caching**
   - Cache URLs (cheap, small)
   - Download on-demand (expensive, large)

4. **Rate limit management**
   - Batch API queries in Pipeline 2
   - Throttle downloads in Pipeline 3

**Disadvantages:**
- More complexity
- More code to maintain

### Why Not Query APIs During Download?

**Bad Alternative:**
```python
# DON'T DO THIS:
while not downloaded:
    url = query_next_api()  # Re-query for each attempt
    try_download(url)
```

**Problems:**
- Wastes API calls
- Slower (sequential API queries)
- Rate limit issues
- Can't prioritize across sources

**Current Approach:**
```python
# DO THIS:
urls = query_all_apis_parallel()  # Once
for url in sorted_by_priority(urls):
    if try_download(url):
        break  # Success!
```

**Benefits:**
- Single API query batch
- Fast parallel collection
- Smart prioritization
- Retry without re-querying

---

## 📁 File Structure

```
omics_oracle_v2/
├── api/routes/
│   └── agents.py                          # Orchestrator (all 3 pipelines)
│       ├─ initialize GEOCitationDiscovery    (Pipeline 1)
│       ├─ initialize FullTextManager          (Pipeline 2)
│       ├─ initialize PDFDownloadManager       (Pipeline 3)
│       └─ coordinate execution flow
│
├── lib/citations/discovery/
│   └── geo_discovery.py                   # PIPELINE 1
│       └── GEOCitationDiscovery
│           ├── find_citing_papers()
│           ├── _find_via_citation()       # OpenAlex
│           └── _find_via_geo_mention()    # PubMed
│
├── lib/enrichment/fulltext/
│   ├── manager.py                         # PIPELINE 2
│   │   └── FullTextManager
│   │       ├── get_all_fulltext_urls()    # Collect URLs
│   │       ├── _check_cache()
│   │       ├── _try_institutional_access()
│   │       ├── _try_pmc()
│   │       ├── _try_unpaywall()
│   │       ├── _try_core()
│   │       ├── _try_openalex_oa_url()
│   │       ├── _try_crossref()
│   │       ├── _try_biorxiv()
│   │       ├── _try_arxiv()
│   │       ├── _try_scihub()
│   │       └── _try_libgen()
│   │
│   └── download_manager.py                # PIPELINE 3
│       └── PDFDownloadManager
│           ├── download_with_fallback()   # Waterfall download
│           ├── _download_single()         # HTTP GET
│           ├── _sort_urls_by_type_and_priority()
│           └── _generate_filename()
│
└── lib/search_engines/citations/
    ├── openalex.py                        # OpenAlex API client
    ├── pubmed.py                          # PubMed API client
    └── models.py                          # Publication model
```

---

## 🔧 Configuration

### Enable/Disable Components

```python
# agents.py initialization

# PIPELINE 1: Citation Discovery (always enabled)
citation_discovery = GEOCitationDiscovery()

# PIPELINE 2: URL Collection (configure sources)
fulltext_manager = FullTextManager(
    FullTextManagerConfig(
        enable_institutional=True,
        enable_pmc=True,
        enable_unpaywall=True,
        enable_core=True,
        enable_openalex=True,
        enable_crossref=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_scihub=True,    # ⚠️ Gray area
        enable_libgen=True,    # ⚠️ Gray area
    )
)

# PIPELINE 3: PDF Download (configure behavior)
pdf_downloader = PDFDownloadManager(
    max_concurrent=3,           # Parallel downloads
    max_retries=2,              # Per URL
    timeout_seconds=30,         # HTTP timeout
    validate_pdf=True,          # Check magic bytes
)
```

---

## 🚀 Usage Examples

### Example 1: Full Pipeline

```python
# PIPELINE 1: Find citing papers
discovery = GEOCitationDiscovery()
citation_result = await discovery.find_citing_papers(geo_metadata)

# PIPELINE 2: Get URLs for each paper
manager = FullTextManager()
await manager.initialize()

urls_by_paper = {}
for paper in citation_result.citing_papers:
    result = await manager.get_all_fulltext_urls(paper)
    urls_by_paper[paper.pmid] = result.all_urls

# PIPELINE 3: Download PDFs
downloader = PDFDownloadManager()

for paper in citation_result.citing_papers:
    urls = urls_by_paper[paper.pmid]
    result = await downloader.download_with_fallback(
        paper, urls, Path("data/pdfs")
    )
    if result.success:
        print(f"Downloaded {paper.pmid} from {result.source}")
```

### Example 2: URLs Only (No Download)

```python
# Get URLs but don't download
discovery = GEOCitationDiscovery()
manager = FullTextManager()

citation_result = await discovery.find_citing_papers(geo_metadata)

for paper in citation_result.citing_papers:
    result = await manager.get_all_fulltext_urls(paper)
    print(f"{paper.pmid}: {len(result.all_urls)} URLs")
    for url in result.all_urls:
        print(f"  - {url.source.value}: {url.url}")
```

---

## 📊 Summary Table

| Aspect | Pipeline 1 | Pipeline 2 | Pipeline 3 |
|--------|------------|------------|------------|
| **Name** | Citation Discovery | URL Collection | PDF Download |
| **Purpose** | Find papers | Find URLs | Get files |
| **Sources** | 2 (PubMed, OpenAlex) | 11 (all sources) | 0 (uses Pipeline 2 URLs) |
| **API Calls** | 3 per dataset | Up to 11 per paper | 0 |
| **HTTP Requests** | 0 | 0-11 (API calls) | 1-4 (downloads) |
| **Output** | Metadata | URLs | PDF files |
| **Speed** | 0.8-1.7 sec | 2-3 sec | 0.5-2 sec |
| **File** | geo_discovery.py | manager.py | download_manager.py |
| **Class** | GEOCitationDiscovery | FullTextManager | PDFDownloadManager |

---

## 🎓 Conclusion

**Three Distinct Pipelines Working Together:**

1. **Citation Discovery** → Finds papers using scholarly databases
2. **URL Collection** → Queries 11 sources to find download locations
3. **PDF Download** → Actually downloads files with retry logic

**Why This Architecture?**
- **Separation of concerns:** Each pipeline does one thing well
- **Efficiency:** Collect all URLs once, retry downloads without re-querying
- **Flexibility:** Can get URLs without downloading, or vice versa
- **Maintainability:** Clear boundaries between components

**Total Data Sources: 13**
- 2 for citation discovery (what to download)
- 11 for URL collection (where to download)
- 0 for downloading (uses URLs from collection)

---

**Author:** OmicsOracle Architecture Team  
**Last Updated:** October 14, 2025  
**Status:** Production System - Complete Documentation ✅
