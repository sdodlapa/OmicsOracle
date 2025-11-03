# OmicsOracle Search & Access Waterfall System

## Overview

OmicsOracle uses a sophisticated **multi-tier waterfall system** to maximize full-text paper retrieval success rates. The system queries 9+ sources in optimized priority order, automatically falling back when one source fails.

**Success Rate**: ~90-95% for biomedical papers (combined across all sources)

---

## Table of Contents
1. [High-Level Architecture](#1-high-level-architecture)
2. [Waterfall Strategy](#2-waterfall-strategy)
3. [Source Details](#3-source-details)
4. [Execution Flow](#4-execution-flow)
5. [URL Classification System](#5-url-classification-system)
6. [Optimization Strategies](#6-optimization-strategies)
7. [Error Handling & Fallback](#7-error-handling--fallback)

---

## 1. High-Level Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                  OMICSORACLE RETRIEVAL SYSTEM                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE 1: Citation Discovery                                  │
│  • GEO metadata → PMIDs                                          │
│  • PubMed search                                                 │
│  • Semantic Scholar search                                       │
│  • OpenAlex search                                               │
│  → Result: List of Publication objects                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE 2: URL Collection (FullTextManager)                    │
│  • Waterfall: 9 sources tried in priority order                 │
│  • Parallel: Query ALL sources simultaneously (optional)         │
│  • Caching: Check local files first                             │
│  → Result: FullTextResult with all_urls[]                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE 3: PDF Download (PDFDownloadManager)                   │
│  • Try URLs in priority order                                    │
│  • Validate PDF magic bytes                                      │
│  • Automatic retry with fallback URLs                           │
│  → Result: Valid PDF file saved to disk                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE 4: Text Extraction (PDFExtractor)                      │
│  • Extract sections, tables, figures                             │
│  • Parse references, metadata                                    │
│  • Quality scoring                                               │
│  → Result: Structured fulltext content                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Waterfall Strategy

### 2.1 Priority Order (Optimized)

```
┌─────────────────────────────────────────────────────────────────┐
│  WATERFALL PRIORITY ORDER                                        │
│  (Based on: effectiveness > legality > speed)                    │
└─────────────────────────────────────────────────────────────────┘

Priority 0: Discovery URL
├─ Source: URL extracted during citation discovery
├─ Coverage: ~80-85% of papers
├─ Speed: Instant (already have URL)
└─ Use: Skip waterfall if URL exists

Priority 1: Cache
├─ Source: Local filesystem (data/fulltext/pdf/)
├─ Coverage: Papers already downloaded
├─ Latency: <10ms (disk read)
└─ Status: ✅ Always checked first

Priority 2: Institutional Access
├─ Source: Georgia Tech / Old Dominion subscriptions
├─ Coverage: ~45-50% (journal subscriptions)
├─ Method: DOI URL / EZProxy
├─ Requires: VPN or on-campus network
├─ Latency: ~100-500ms
├─ Quality: Highest (official publisher PDFs)
└─ Status: ✅ Legal, highest priority

Priority 3: PubMed Central (PMC)
├─ Source: NIH public repository
├─ Coverage: ~6M+ free articles
├─ Method: PMC ID → XML/PDF
├─ Latency: ~200-800ms
├─ Quality: Very high (peer-reviewed)
├─ Note: Moved to Priority 11 for programmatic access (403 errors)
└─ Status: ✅ Legal, best free source

Priority 4: Unpaywall
├─ Source: OA aggregator (20M+ papers)
├─ Coverage: ~25-30% additional
├─ Method: DOI → OA locations
├─ Latency: ~300-1000ms
├─ Quality: High (verifies is_oa=true)
└─ Status: ✅ Legal, comprehensive

Priority 5: CORE
├─ Source: Academic repository aggregator
├─ Coverage: ~45M papers, ~10-15% unique
├─ Method: DOI/title → download URL
├─ Latency: ~500-1500ms
├─ Requires: API key (optional)
└─ Status: ✅ Legal

Priority 6: OpenAlex OA URLs
├─ Source: Metadata from OpenAlex
├─ Coverage: Varies (metadata-driven)
├─ Method: Extract oa_url from metadata
├─ Latency: <50ms (in memory)
└─ Status: ✅ Legal

Priority 7: Crossref
├─ Source: DOI metadata service
├─ Coverage: Publisher full-text links
├─ Method: DOI → publisher URLs
├─ Latency: ~300-800ms
├─ Note: Often returns paywalled links
└─ Status: ✅ Legal (metadata)

Priority 8: bioRxiv/medRxiv
├─ Source: Biomedical preprint servers
├─ Coverage: ~2M preprints
├─ Method: DOI → PDF
├─ Latency: ~200-600ms
├─ Quality: Preprints (not peer-reviewed)
└─ Status: ✅ Legal

Priority 9: arXiv
├─ Source: Physics/CS/Math preprints
├─ Coverage: ~2.5M papers
├─ Method: arXiv ID / title → PDF
├─ Latency: ~200-500ms
├─ Quality: Preprints
└─ Status: ✅ Legal

Priority 10: Sci-Hub
├─ Source: Shadow library
├─ Coverage: ~88M papers, ~15-20% unique
├─ Method: DOI/PMID → PDF
├─ Latency: ~1000-3000ms
├─ Mirrors: Multiple with load balancing
├─ Note: Legal gray area, blocked in some countries
└─ Status: ⚠️  Use responsibly (disabled by default)

Priority 11: LibGen
├─ Source: Academic library mirror
├─ Coverage: ~5-10% unique
├─ Method: DOI → PDF
├─ Latency: ~1000-4000ms
├─ Note: Legal gray area
└─ Status: ⚠️  Use responsibly (disabled by default)
```

### 2.2 Coverage Analysis

```
┌──────────────────────────────────────────────────────────────┐
│  CUMULATIVE COVERAGE BY SOURCE                                │
│  (Based on empirical testing with biomedical papers)          │
└──────────────────────────────────────────────────────────────┘

 100%│                                              ████  ~95%
     │                                          ████
     │                                      ████
  80%│                                  ████
     │                              ████
     │                          ████
  60%│                      ████
     │                  ████
     │              ████
  40%│          ████
     │      ████
     │  ████
  20%│██
     │
   0%└─────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────
       Cache Inst PMC  Unp CORE OA  Cross Bio arXiv Sci Lib
        (5%) (45)(60) (75)(82)(85) (87) (88) (89) (93)(95)

Legend:
Cache: Already downloaded
Inst:  Institutional access (VPN required)
PMC:   PubMed Central
Unp:   Unpaywall
CORE:  CORE.ac.uk
OA:    OpenAlex OA URLs
Cross: Crossref publisher links
Bio:   bioRxiv/medRxiv
arXiv: arXiv preprints
Sci:   Sci-Hub (gray area)
Lib:   LibGen (gray area)
```

---

## 3. Source Details

### 3.1 Institutional Access (Priority 1)

```
┌──────────────────────────────────────────────────────────────┐
│  INSTITUTIONAL ACCESS WORKFLOW                                │
└──────────────────────────────────────────────────────────────┘

Input: Publication with DOI
  ↓
┌────────────────────────────────┐
│ Institution: Georgia Tech      │
│ Method: DOI URL                │
│ URL: https://doi.org/10.xxx    │
└────────────────┬───────────────┘
                 │
          ┌──────┴───────┐
          │              │
     ON CAMPUS        VPN/OFF CAMPUS
          │              │
          ▼              ▼
    ┌─────────┐    ┌──────────┐
    │ HTTP    │    │ HTTP 403 │
    │ 200 OK  │    │ Forbidden│
    └────┬────┘    └─────┬────┘
         │               │
         ▼               ▼
    Download         Waterfall
    Success          Fallback
                     (PMC, Unpaywall...)
```

**Configuration:**
```python
InstitutionalAccessManager(
    institution=InstitutionType.GEORGIA_TECH  # or OLD_DOMINION
)
```

**Expected Behavior:**
- ✅ ON CAMPUS: Returns 200 OK, downloads PDF
- ⚠️  OFF CAMPUS: Returns 403 Forbidden, falls back to next source
- This is CORRECT - waterfall automatically tries other sources

### 3.2 PubMed Central (Priority 2)

```
┌──────────────────────────────────────────────────────────────┐
│  PMC RETRIEVAL STRATEGY                                       │
└──────────────────────────────────────────────────────────────┘

Input: Publication with PMID or PMC_ID
  ↓
Try Multiple URL Patterns (Priority Order):
  1. Direct PDF:  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/pdf/
  2. XML Download: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/?report=xml
  3. Landing Page: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/
  4. PMID Variant: https://www.ncbi.nlm.nih.gov/pmc/articles/pmid/{pmid}/
  ↓
Return Best URL (PDF preferred)
```

**Why Multiple Patterns?**
- PMC has inconsistent URL structure
- Some papers: PDF available
- Some papers: XML only
- Some papers: Landing page with links
- Trying all patterns increases success rate by ~20%

**Issue (Oct 31, 2025):**
PMC returns HTTP 403 for programmatic access to PDFs. Moved to Priority 11 as fallback.

### 3.3 Unpaywall (Priority 3)

```
┌──────────────────────────────────────────────────────────────┐
│  UNPAYWALL OA VERIFICATION WORKFLOW                           │
└──────────────────────────────────────────────────────────────┘

Input: DOI
  ↓
GET https://api.unpaywall.org/v2/{doi}?email={email}
  ↓
Response:
{
  "is_oa": true/false,              ← Verify this first!
  "oa_status": "gold/hybrid/green",
  "best_oa_location": {
    "url_for_pdf": "https://...",   ← Prefer PDF URLs
    "url": "https://...",
    "version": "publishedVersion",
    "license": "cc-by"
  },
  "oa_locations": [...]             ← Try all if best fails
}
  ↓
Verification Steps:
1. Check is_oa == true (reject if false)
2. Try best_oa_location.url_for_pdf first
3. Fallback to best_oa_location.url
4. Try all oa_locations[] if best fails
5. Classify URL type (PDF direct vs landing page)
  ↓
Return: Verified OA URL with metadata
```

**Enhancement (Oct 13, 2025):**
- Now verifies `is_oa=true` before returning URLs
- Reduces 403 errors from paywalled content
- Tries ALL `oa_locations`, not just `best_oa_location`
- Prefers `url_for_pdf` over landing pages

### 3.4 Sci-Hub (Priority 8)

```
┌──────────────────────────────────────────────────────────────┐
│  SCI-HUB MIRROR STRATEGY                                      │
└──────────────────────────────────────────────────────────────┘

Mirrors (with load balancing):
┌─────────────────────────┬────────────┬──────────────┐
│ Mirror                  │ Status     │ Success Rate │
├─────────────────────────┼────────────┼──────────────┤
│ sci-hub.se              │ Active     │ 23.9%        │
│ sci-hub.st              │ Active     │ 23.9%        │
│ sci-hub.ru              │ Variable   │ 15-20%       │
│ sci-hub.ren             │ Backup     │ 10-15%       │
└─────────────────────────┴────────────┴──────────────┘

Workflow:
Input: DOI or PMID
  ↓
Try Mirror 1 (sci-hub.se)
  ↓
  Success? → Return PDF URL
  ↓
  Timeout/403? → Try Mirror 2 (sci-hub.st)
  ↓
  Success? → Return PDF URL
  ↓
  All mirrors failed → Return None
```

**Legal Considerations:**
- ⚠️  Gray area: Legal in some countries, blocked in others
- Use responsibly and in compliance with local laws
- Disabled by default
- Enable only if necessary: `enable_scihub=True`
- Downloads saved to `data/fulltext/pdf/scihub/` for easy deletion

---

## 4. Execution Flow

### 4.1 Sequential Waterfall (Original)

```
┌──────────────────────────────────────────────────────────────┐
│  SEQUENTIAL WATERFALL (get_fulltext)                          │
│  DEPRECATED: Use Parallel Collection instead                  │
└──────────────────────────────────────────────────────────────┘

START
  ↓
Check Cache → Found? ──YES──> STOP (return cached)
  │                              
  NO                              
  ↓                              
Try Institutional → Success? ──YES──> STOP (return URL)
  │                                   
  NO                                  
  ↓                                   
Try PMC → Success? ──YES──> STOP (return URL)
  │                              
  NO                              
  ↓                              
Try Unpaywall → Success? ──YES──> STOP (return URL)
  │                                   
  NO                                  
  ↓                                   
Try CORE → Success? ──YES──> STOP (return URL)
  │                              
  NO                              
  ↓                              
Try OpenAlex → Success? ──YES──> STOP (return URL)
  │                                   
  NO                                  
  ↓                                   
... (continue for all sources)
  │
  NO (all failed)
  ↓
FAILURE (no sources found URL)

Characteristics:
• STOPS at first success
• Sources tried SEQUENTIALLY (one at a time)
• Total time: ~2-10 seconds (depends on which source succeeds)
• Benefit: Doesn't waste API calls
• Drawback: No fallback URLs for download retry
```

### 4.2 Parallel Collection (New)

```
┌──────────────────────────────────────────────────────────────┐
│  PARALLEL COLLECTION (get_all_fulltext_urls)                  │
│  NEW (Oct 13, 2025): Recommended for batch operations         │
└──────────────────────────────────────────────────────────────┘

START
  ↓
Check Cache → Found? ──YES──> STOP (return cached)
  │
  NO
  ↓
Query ALL sources in PARALLEL:
┌──────────────────────────────────────────────────────────┐
│  Institutional │ PMC │ Unpaywall │ CORE │ OpenAlex │...  │
│       ↓            ↓        ↓        ↓         ↓         │
│   await asyncio.gather(                                  │
│       institutional_task,                                │
│       pmc_task,                                          │
│       unpaywall_task,                                    │
│       ...                                                │
│   )                                                      │
└──────────────────────────────────────────────────────────┘
  ↓
Collect ALL results:
[
  SourceURL(url="...", source="institutional", priority=1),
  SourceURL(url="...", source="unpaywall", priority=3),
  SourceURL(url="...", source="core", priority=4),
  ...
]
  ↓
Sort by priority (lower = better)
  ↓
Return FullTextResult with all_urls populated

Characteristics:
• Queries ALL sources simultaneously
• Total time: ~2-3 seconds (limited by slowest source)
• Returns ALL found URLs (not just first)
• Benefit: Built-in fallback URLs for download retry
• Benefit: Higher success rate (PDFDownloadManager tries all)
• Use case: Batch downloads, unreliable networks
```

### 4.3 Discovery URL Optimization (Oct 16, 2025)

```
┌──────────────────────────────────────────────────────────────┐
│  DISCOVERY URL SKIP OPTIMIZATION                              │
│  Skips waterfall if URL already exists from citation         │
│  discovery (80-85% of papers)                                 │
└──────────────────────────────────────────────────────────────┘

Input: Publication
  ↓
Has pdf_url attribute? ──NO──> Run waterfall as usual
  │
  YES (80-85% of papers)
  ↓
Check url_source attribute:
  • "semantic_scholar" (most common)
  • "openalex"
  • "pubmed"
  ↓
Classify URL type:
  • URLType.PDF_DIRECT (best)
  • URLType.PMC_XML
  • URLType.LANDING_PAGE
  ↓
Create SourceURL with priority=0:
{
  url: publication.pdf_url,
  source: "discovery",
  priority: 0,  ← Highest priority
  url_type: URLType.PDF_DIRECT,
  metadata: {
    "source": "discovery",
    "original_source": "semantic_scholar",
    "oa_status": "gold"
  }
}
  ↓
FIXED (Oct 31): Still collect fallback URLs from other sources
  ↓
Return: FullTextResult with all_urls = [discovery_url, ...fallbacks]

Benefits:
• 80-85% of papers skip waterfall (saves 2-3 seconds)
• Still have fallback URLs if discovery URL fails (403, etc.)
• Discovery URLs often more reliable (direct from source metadata)
```

---

## 5. URL Classification System

### 5.1 URL Types

```python
class URLType(str, Enum):
    """
    URL type classification for smart prioritization.
    
    NEW (Oct 13, 2025): Helps download manager prioritize 
    PDF links over landing pages.
    """
    PDF_DIRECT = "pdf_direct"       # Direct PDF download
    PMC_XML = "pmc_xml"             # PMC XML (preferred over PDF)
    PMC_PDF = "pmc_pdf"             # PMC PDF endpoint
    LANDING_PAGE = "landing_page"   # Publisher landing page
    INSTITUTIONAL = "institutional" # Institutional access URL
    PREPRINT = "preprint"           # bioRxiv/arXiv PDF
    UNKNOWN = "unknown"             # Cannot determine
```

### 5.2 URL Classification Logic

```
┌──────────────────────────────────────────────────────────────┐
│  URL CLASSIFICATION RULES                                     │
└──────────────────────────────────────────────────────────────┘

URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/
  ↓
Pattern: /pmc/.*pdf
  ↓
Type: PMC_PDF

────────────────────────────────────────────────────────────────

URL: https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1.full.pdf
  ↓
Pattern: biorxiv|medrxiv.*\.pdf
  ↓
Type: PREPRINT

────────────────────────────────────────────────────────────────

URL: https://arxiv.org/pdf/2401.12345.pdf
  ↓
Pattern: arxiv\.org/pdf/
  ↓
Type: PREPRINT

────────────────────────────────────────────────────────────────

URL: https://doi.org/10.1038/nature12345
  ↓
Pattern: ^https?://doi\.org/
  ↓
Type: INSTITUTIONAL (requires subscription)

────────────────────────────────────────────────────────────────

URL: https://www.nature.com/articles/nature12345
  ↓
Pattern: No .pdf extension
  ↓
Type: LANDING_PAGE (lower priority)

────────────────────────────────────────────────────────────────

URL: https://example.com/papers/paper.pdf
  ↓
Pattern: \.pdf$ (ends with .pdf)
  ↓
Type: PDF_DIRECT
```

### 5.3 Priority Adjustment Based on URL Type

```python
def get_priority_boost(url: str) -> int:
    """
    Adjust priority based on URL type.
    
    Returns:
        Negative number = boost priority (higher)
        Positive number = lower priority
        0 = no change
    """
    url_type = URLValidator.classify_url(url)
    
    if url_type == URLType.PMC_XML:
        return -2  # Boost (XML is best quality)
    elif url_type == URLType.PDF_DIRECT:
        return -1  # Boost (direct PDF)
    elif url_type == URLType.PMC_PDF:
        return 0   # Keep as is
    elif url_type == URLType.PREPRINT:
        return 0   # Keep as is
    elif url_type == URLType.LANDING_PAGE:
        return +2  # Lower priority (requires scraping)
    elif url_type == URLType.INSTITUTIONAL:
        return 0   # Keep as is (may need auth)
    else:
        return +1  # Unknown, slightly lower
```

---

## 6. Optimization Strategies

### 6.1 Cache-First Strategy

```
┌──────────────────────────────────────────────────────────────┐
│  SMART CACHE LOOKUP                                           │
│  Checks multiple locations before hitting network            │
└──────────────────────────────────────────────────────────────┘

Publication: PMID 12345678
  ↓
Check source-specific directories:
  1. data/fulltext/pdf/institutional/12345678.pdf
  2. data/fulltext/pdf/pmc/PMC9876543.pdf
  3. data/fulltext/xml/pmc/PMC9876543.nxml
  4. data/fulltext/pdf/unpaywall/12345678.pdf
  5. data/fulltext/pdf/biorxiv/10.1101_2024.01.01.123456.pdf
  6. data/fulltext/pdf/arxiv/2401.12345.pdf
  7. data/fulltext/pdf/scihub/12345678.pdf
  8. data/fulltext/pdf/libgen/12345678.pdf
  ↓
Prefer XML over PDF (higher quality):
  XML found? → Return XML
  PDF found? → Return PDF
  ↓
Fallback to hash-based cache (legacy):
  data/cache/fulltext_{hash}.pdf
  ↓
Not found → Proceed to waterfall

Benefits:
• <10ms latency (disk read)
• Prevents unnecessary API calls
• Source tracking for compliance
• Easy deletion if needed
```

### 6.2 Concurrent Source Querying

```
┌──────────────────────────────────────────────────────────────┐
│  PARALLEL EXECUTION WITH SEMAPHORE                            │
└──────────────────────────────────────────────────────────────┘

Configuration:
max_concurrent = 3  # Query up to 3 sources simultaneously

Implementation:
semaphore = asyncio.Semaphore(3)

async def query_source(source_func):
    async with semaphore:
        return await source_func()

# Launch all sources
tasks = [
    query_source(try_institutional),
    query_source(try_pmc),
    query_source(try_unpaywall),
    query_source(try_core),
    ...
]

results = await asyncio.gather(*tasks)

Benefits:
• 3x faster than sequential (if max_concurrent=3)
• Efficient use of network I/O
• Doesn't overwhelm APIs
• Total time ≈ slowest source (~2-3 seconds)
```

### 6.3 Timeout Management

```
┌──────────────────────────────────────────────────────────────┐
│  PER-SOURCE TIMEOUT STRATEGY                                  │
└──────────────────────────────────────────────────────────────┘

Configuration:
timeout_per_source = 30  # seconds

async def try_source_with_timeout(source_func, timeout=30):
    try:
        return await asyncio.wait_for(
            source_func(),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.debug(f"{source_name} timeout after {timeout}s")
        return FullTextResult(success=False, error="Timeout")

Timeouts by source:
┌─────────────────┬─────────┬──────────────────┐
│ Source          │ Timeout │ Typical Duration │
├─────────────────┼─────────┼──────────────────┤
│ Cache           │ N/A     │ <10ms            │
│ Institutional   │ 30s     │ 100-500ms        │
│ PMC             │ 30s     │ 200-800ms        │
│ Unpaywall       │ 30s     │ 300-1000ms       │
│ CORE            │ 30s     │ 500-1500ms       │
│ OpenAlex        │ N/A     │ <50ms (memory)   │
│ Crossref        │ 30s     │ 300-800ms        │
│ bioRxiv         │ 30s     │ 200-600ms        │
│ arXiv           │ 30s     │ 200-500ms        │
│ Sci-Hub         │ 30s     │ 1000-3000ms      │
│ LibGen          │ 30s     │ 1000-4000ms      │
└─────────────────┴─────────┴──────────────────┘

Benefits:
• Prevents hanging on slow sources
• Moves to next source quickly
• Total time bounded (< 30s per source)
```

---

## 7. Error Handling & Fallback

### 7.1 Download Retry Logic (PDFDownloadManager)

```
┌──────────────────────────────────────────────────────────────┐
│  TIERED WATERFALL WITH RETRY                                  │
│  Pipeline 3: PDFDownloadManager                               │
└──────────────────────────────────────────────────────────────┘

Input: all_urls from FullTextManager
[
  SourceURL(url="https://doi.org/...", priority=1),
  SourceURL(url="https://unpaywall.org/...", priority=3),
  SourceURL(url="https://core.ac.uk/...", priority=4),
  ...
]
  ↓
Try URL 1 (priority 1):
  ↓
  Download → Validate PDF magic bytes
  ↓
  Valid? ──YES──> STOP (success)
  │
  NO (HTTP 403 / Invalid PDF)
  ↓
Try URL 2 (priority 3):
  ↓
  Download → Validate PDF magic bytes
  ↓
  Valid? ──YES──> STOP (success)
  │
  NO
  ↓
Try URL 3 (priority 4):
  ↓
  ... (continue with all URLs)
  ↓
All URLs failed → FAILURE

Per-URL Retry:
┌─────────────────────────────────────────────┐
│ Try URL (attempt 1/2)                       │
│   ↓                                         │
│ HTTP Error (403/404/500)?                   │
│   ↓                                         │
│ Retry with different headers (attempt 2/2) │
│   ↓                                         │
│ Still failed? → Next URL                    │
└─────────────────────────────────────────────┘
```

### 7.2 Error Categories

```
┌──────────────────────────────────────────────────────────────┐
│  ERROR HANDLING BY CATEGORY                                   │
└──────────────────────────────────────────────────────────────┘

HTTP 403 Forbidden:
├─ Cause: Paywall / institutional access required
├─ Action: Skip to next URL
└─ Log: DEBUG level (expected for institutional URLs)

HTTP 404 Not Found:
├─ Cause: Paper removed / URL changed
├─ Action: Skip to next URL
└─ Log: WARNING level

HTTP 500 Server Error:
├─ Cause: Temporary server issue
├─ Action: Retry once, then skip
└─ Log: WARNING level

Timeout:
├─ Cause: Slow network / server
├─ Action: Skip to next URL
└─ Log: DEBUG level

Invalid PDF:
├─ Cause: HTML page returned instead of PDF
├─ Detection: Check magic bytes (%PDF-1.)
├─ Action: Skip to next URL
└─ Log: WARNING level

Network Error (ConnectionError):
├─ Cause: Network unreachable
├─ Action: Retry once with exponential backoff
└─ Log: ERROR level
```

### 7.3 Success Tracking

```python
class FullTextManager:
    def __init__(self):
        self.stats = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "by_source": {
                "institutional": 0,
                "pmc": 0,
                "unpaywall": 0,
                ...
            },
            "skipped_already_have_url": 0,  # Discovery URL optimization
        }
    
    def get_statistics(self) -> Dict:
        """
        Returns:
        {
            "total_attempts": 1000,
            "successes": 923,
            "failures": 77,
            "success_rate": "92.3%",
            "by_source": {
                "institutional": 450,
                "pmc": 200,
                "unpaywall": 150,
                "core": 50,
                "biorxiv": 30,
                "arxiv": 20,
                "scihub": 15,
                "libgen": 8
            },
            "skipped_already_have_url": 800
        }
        """
```

---

## Example Usage

### Basic Waterfall (Sequential)

```python
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.search_engines.citations.models import Publication

# Create publication object
pub = Publication(
    pmid="12345678",
    doi="10.1038/nature12345",
    title="Example Paper",
    ...
)

# Initialize manager
manager = FullTextManager()
await manager.initialize()

# Get full-text (waterfall, stops at first success)
result = await manager.get_fulltext(pub)

if result.success:
    print(f"✓ Found via {result.source.value}: {result.url}")
else:
    print(f"✗ Failed: {result.error}")

await manager.cleanup()
```

### Parallel Collection with Fallback

```python
# Get ALL URLs from ALL sources (parallel)
result = await manager.get_all_fulltext_urls(pub)

if result.success:
    print(f"Found {len(result.all_urls)} URLs:")
    for url_obj in result.all_urls:
        print(f"  [{url_obj.priority}] {url_obj.source.value}: {url_obj.url}")
    
    # Now use PDFDownloadManager to try all URLs with fallback
    from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
    
    pdf_manager = PDFDownloadManager()
    pdf_path = await pdf_manager.download_with_fallback(
        publication=pub,
        urls=result.all_urls,
        output_dir=Path("data/pdfs")
    )
    
    if pdf_path:
        print(f"✓ Downloaded: {pdf_path}")
else:
    print(f"✗ No URLs found from any source")
```

### Batch Processing

```python
# Process multiple publications
publications = [pub1, pub2, pub3, ...]

# Get URLs for all (3 concurrent)
results = await manager.get_fulltext_batch(
    publications,
    max_concurrent=3,
    collect_all_urls=True  # Use parallel collection
)

# Check statistics
stats = manager.get_statistics()
print(f"Success rate: {stats['success_rate']}")
print(f"By source: {stats['by_source']}")
```

---

## Performance Metrics

### Typical Latencies

```
┌──────────────────────────────────────────────────────────────┐
│  LATENCY BY RETRIEVAL STRATEGY                                │
└──────────────────────────────────────────────────────────────┘

Cache Hit (best case):
  • Duration: <10ms
  • Network calls: 0
  • Success rate: ~5% (previously downloaded)

Discovery URL (optimized, Oct 16):
  • Duration: <50ms
  • Network calls: 0 (URL from metadata)
  • Success rate: ~80-85%
  • Savings: 2-3 seconds per paper

Sequential Waterfall (DEPRECATED):
  • Best case: 100ms (institutional success)
  • Average case: 1-2 seconds (PMC/Unpaywall success)
  • Worst case: 5-10 seconds (late source success)
  • Network calls: 1-9 (stops at success)

Parallel Collection (NEW):
  • Duration: 2-3 seconds (limited by slowest source)
  • Network calls: All sources (9+)
  • Benefit: ALL URLs collected for fallback
  • Use case: Batch downloads, unreliable networks

Complete Pipeline (URL + Download + Extract):
  • URL collection: 2-3 seconds
  • PDF download: 1-5 seconds (depends on file size)
  • PDF extraction: 2-10 seconds (depends on pages)
  • Total: 5-18 seconds per paper
```

### Success Rates by Source

```
┌──────────────────────────────────────────────────────────────┐
│  EMPIRICAL SUCCESS RATES (Biomedical Papers)                  │
└──────────────────────────────────────────────────────────────┘

Source              | Unique Coverage | Cumulative | Legal
--------------------|-----------------|------------|--------
Discovery URL       | 80-85%          | 85%        | ✅
Institutional       | 45-50%          | 50%        | ✅ (requires VPN)
PMC                 | 15-20%          | 60%        | ✅
Unpaywall           | 15-20%          | 75%        | ✅
CORE                | 7-10%           | 82%        | ✅
OpenAlex OA         | 3-5%            | 85%        | ✅
Crossref            | 2-3%            | 87%        | ✅
bioRxiv/medRxiv     | 1-2%            | 88%        | ✅
arXiv               | 1-2%            | 89%        | ✅
Sci-Hub             | 4-5%            | 93%        | ⚠️
LibGen              | 2-3%            | 95%        | ⚠️

Overall Success Rate: 90-95%
```

---

## Summary

**Key Principles:**
1. **Legality First**: Legal sources prioritized over gray area
2. **Quality Matters**: Official PDFs preferred over preprints
3. **Speed Optimization**: Cache checked first, parallel queries when needed
4. **Fallback Built-in**: All URLs collected for retry logic
5. **Transparency**: Source tracking for compliance

**Best Practices:**
- ✅ Use `get_all_fulltext_urls()` for batch operations
- ✅ Enable `collect_all_urls=True` for higher success rates
- ✅ Check cache first (instant results)
- ✅ Use discovery URL optimization (80-85% skip waterfall)
- ✅ Enable Sci-Hub/LibGen only if necessary
- ✅ Log all source attempts for debugging

**Common Issues:**
- HTTP 403 from institutional URLs: **EXPECTED** (requires VPN)
- PMC 403 errors: **KNOWN ISSUE** (moved to low priority)
- Slow performance: Use parallel collection
- Low success rate: Check if Sci-Hub/LibGen needed

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025  
**Author**: OmicsOracle Development Team
