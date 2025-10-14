# Complete Data Flow: GEO ID as Root Node

## Architecture Overview

**YES, GEO ID is the root/center** - everything else connects to it through the registry.

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER QUERY: "breast cancer"                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: SEARCH FOR GEO DATASETS                       │
│                    (SearchOrchestrator + GEO API)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌───────────────────────────┐
                    │   GEO Dataset Found:       │
                    │   GSE12345                 │  ← ROOT NODE
                    │   - title                  │
                    │   - summary                │
                    │   - organism               │
                    │   - pubmed_ids: [11111]    │  ← Link to publications
                    └───────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         REGISTRY STORAGE                                 │
│                    (GEORegistry - SQLite database)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌───────────────────────────┐
                    │ TABLE: geo_datasets        │
                    │ geo_id (PRIMARY KEY)       │  ← GEO ID is the ROOT
                    │ title, summary, organism   │
                    │ pubmed_ids (from GEO API)  │
                    │ metadata (JSON)            │
                    └───────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 2: DISCOVER CITING PAPERS (Optional)                   │
│              (GEOCitationDiscovery)                                      │
│              - Strategy A: Papers that CITE the original paper           │
│              - Strategy B: Papers that MENTION the GEO ID                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
            ┌──────────────────────┴──────────────────────┐
            │                                              │
    ┌───────────────┐                           ┌─────────────────┐
    │ Original Paper│                           │  Citing Papers  │
    │ PMID: 11111   │                           │  PMID: 22222    │
    │ (from GEO)    │                           │  PMID: 33333    │
    └───────────────┘                           │  (discovered)   │
            │                                    └─────────────────┘
            │                                              │
            └──────────────────────┬──────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│          STEP 3: FETCH PUBLICATION METADATA FROM PUBMED                  │
│          (PubMedClient.fetch_by_id)                                      │
│          Enriches PMID with: DOI, PMC ID, Title, Authors, etc.          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
            ┌──────────────────────────────────────────┐
            │        Publication Object:                │
            │        - pmid: "11111"                    │
            │        - doi: "10.1234/example"           │
            │        - pmc_id: "PMC5678910"             │
            │        - title: "Study of..."             │
            │        - authors: [...]                   │
            └──────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         REGISTRY STORAGE                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ TABLE: publications                                         │
    │ id (AUTO INCREMENT PRIMARY KEY)                            │
    │ pmid (UNIQUE) ← Used for lookups                           │
    │ doi                                                         │
    │ pmc_id                                                      │
    │ title, authors, journal, year                              │
    │ urls (JSON) ← ALL fulltext URLs stored here!               │
    │ metadata (JSON)                                             │
    └────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ TABLE: geo_publications (JOIN TABLE)                       │
    │ id (PRIMARY KEY)                                            │
    │ geo_id (FOREIGN KEY → geo_datasets.geo_id) ← ROOT          │
    │ publication_id (FOREIGN KEY → publications.id)             │
    │ relationship_type: 'original' OR 'citing'                  │
    │ citation_strategy: 'strategy_a' OR 'strategy_b'            │
    │ discovered_at (TIMESTAMP)                                   │
    │                                                             │
    │ UNIQUE(geo_id, publication_id) ← One relationship per pair │
    └────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│        STEP 4: COLLECT FULLTEXT URLs FROM 11 SOURCES                    │
│        (FullTextManager.get_all_fulltext_urls)                          │
│                                                                          │
│        For EACH publication (using PMID, DOI, PMC ID):                  │
│        1. PMC (4 patterns) → PDF URLs                                   │
│        2. Unpaywall (DOI) → PDF + Landing URLs                          │
│        3. OpenAlex (DOI) → PDF URLs                                     │
│        4. CORE (DOI/title) → PDF URLs                                   │
│        5. bioRxiv/medRxiv (DOI) → PDF URLs                              │
│        6. arXiv (arXiv ID) → PDF URLs                                   │
│        7. Institutional (DOI) → Repository URLs                         │
│        8. CrossRef (DOI) → Landing URLs                                 │
│        9. Sci-Hub (DOI) → PDF URLs                                      │
│        10. LibGen (DOI/title) → PDF URLs                                │
│        11. Google Scholar (fallback)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
            ┌──────────────────────────────────────────┐
            │        SourceURL Collection:              │
            │        [                                  │
            │          {                                │
            │            url: "https://pmc/pdf/...",    │
            │            source: "pmc",                 │
            │            priority: 2,                   │
            │            url_type: "pdf_direct",        │ ← NEW (Phase 2)
            │            confidence: 0.95,              │ ← NEW (Phase 2)
            │            requires_auth: false,          │ ← NEW (Phase 2)
            │            metadata: {...}                │
            │          },                               │
            │          {                                │
            │            url: "https://unpaywall/...",  │
            │            source: "unpaywall",           │
            │            priority: 3,                   │
            │            url_type: "landing_page",      │
            │            confidence: 0.80,              │
            │            requires_auth: false,          │
            │            metadata: {...}                │
            │          },                               │
            │          ... 10+ more URLs                │
            │        ]                                  │
            └──────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STORE URLs IN REGISTRY                                │
│        (GEORegistry.register_publication with urls parameter)            │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ publications.urls (JSON column):                           │
    │ [                                                           │
    │   {                                                         │
    │     "url": "https://pmc.ncbi.nlm.nih.gov/articles/...",   │
    │     "source": "pmc",                                       │
    │     "priority": 2,                                         │
    │     "url_type": "pdf_direct",      ← Stored!              │
    │     "confidence": 0.95,             ← Stored!              │
    │     "requires_auth": false,         ← Stored!              │
    │     "metadata": {...}                                      │
    │   },                                                        │
    │   { ... more URLs ... }                                    │
    │ ]                                                           │
    │                                                             │
    │ ✓ ALL URLs stored for retry capability                     │
    │ ✓ Can retrieve later if download fails                     │
    │ ✓ Frontend can show alternative sources                    │
    └────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│        STEP 5: SORT URLs BY TYPE AND PRIORITY (Phase 3)                 │
│        (PDFDownloadManager._sort_urls_by_type_and_priority)             │
│                                                                          │
│        Intelligent sorting:                                              │
│        1. Group by type: PDF → HTML → Landing → Unknown                 │
│        2. Within each group: Sort by source priority                    │
│                                                                          │
│        Result: Try fastest/best URLs first!                             │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
            ┌──────────────────────────────────────────┐
            │        Sorted URLs:                       │
            │        [                                  │
            │          PDF URLs (priority 1-4),         │ ← Tried FIRST
            │          HTML URLs (priority 3-5),        │ ← Tried SECOND
            │          Landing URLs (priority 2-6)      │ ← Tried LAST
            │        ]                                  │
            └──────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│        STEP 6: DOWNLOAD PDF WITH WATERFALL FALLBACK                     │
│        (PDFDownloadManager.download_with_fallback)                      │
│                                                                          │
│        For each URL (in sorted order):                                  │
│        1. Try URL with 2 retries                                        │
│        2. If success: Validate PDF, save to disk, STOP                  │
│        3. If fail: Try next URL                                         │
│        4. Record attempt in download_history                            │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL IDENTIFIER SYSTEM                           │
│        (Determines filename for saved PDF)                               │
│                                                                          │
│        Hierarchy (first available wins):                                │
│        1. PMID → "PMID_11111.pdf"                                       │
│        2. DOI → "DOI_10.1234_example.pdf"                               │
│        3. PMC ID → "PMC_5678910.pdf"                                    │
│        4. arXiv ID → "ARXIV_2101.12345.pdf"                             │
│        5. Hash → "HASH_abc123.pdf"                                      │
│                                                                          │
│        ✓ No duplicate downloads (same ID = same file)                   │
│        ✓ Works for publications without PMID                            │
│        ✓ Filesystem-safe (DOI slashes → underscores)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
            ┌──────────────────────────────────────────┐
            │        File Structure:                    │
            │        data/pdfs/                         │
            │          GSE12345/              ← GEO ID  │
            │            original/                      │
            │              PMID_11111.pdf               │
            │            citing/                        │
            │              PMID_22222.pdf               │
            │              PMID_33333.pdf               │
            │            metadata.json        ← URLs!   │
            └──────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STORE DOWNLOAD HISTORY                                │
│        (After each download attempt)                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ TABLE: download_history                                     │
    │ id (PRIMARY KEY)                                            │
    │ publication_id (FOREIGN KEY → publications.id)             │
    │ url (which URL was tried)                                  │
    │ source (pmc, unpaywall, etc.)                              │
    │ status (success, failed, retry, skipped)                   │
    │ file_path (where PDF saved)                                │
    │ file_size (bytes)                                           │
    │ error_message (if failed)                                   │
    │ attempt_number (1, 2, 3...)                                │
    │ downloaded_at (TIMESTAMP)                                   │
    │                                                             │
    │ ✓ Track success/failure per URL                            │
    │ ✓ Analytics: Which sources work best?                      │
    │ ✓ Retry logic: Skip URLs that failed before                │
    └────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    METADATA.JSON FILE                                    │
│        (Comprehensive paper organization + URLs)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ data/pdfs/GSE12345/metadata.json:                          │
    │ {                                                           │
    │   "geo": {                                                  │
    │     "geo_id": "GSE12345",           ← ROOT                 │
    │     "title": "...",                                        │
    │     "pubmed_ids": [11111]                                  │
    │   },                                                        │
    │   "papers": {                                               │
    │     "original": [                                           │
    │       {                                                     │
    │         "pmid": "11111",                                   │
    │         "doi": "10.1234/example",                          │
    │         "pmc_id": "PMC5678910",                            │
    │         "title": "...",                                    │
    │         "pdf_path": "original/PMID_11111.pdf",            │
    │         "fulltext_source": "pmc",                          │
    │         "all_urls": [        ← RETRY CAPABILITY!          │
    │           {                                                 │
    │             "url": "https://pmc/...",                      │
    │             "source": "pmc",                               │
    │             "priority": 2,                                 │
    │             "url_type": "pdf_direct",                      │
    │             "confidence": 0.95                             │
    │           },                                                │
    │           { ... 10+ more URLs ... }                        │
    │         ]                                                   │
    │       }                                                     │
    │     ],                                                      │
    │     "citing": [                                             │
    │       { ... PMID 22222 ... },                              │
    │       { ... PMID 33333 ... }                               │
    │     ]                                                       │
    │   },                                                        │
    │   "download_summary": {                                     │
    │     "total_papers": 3,                                     │
    │     "successful_downloads": 2,                             │
    │     "failed_downloads": 1                                  │
    │   }                                                         │
    │ }                                                           │
    │                                                             │
    │ ✓ Complete record of what was attempted                    │
    │ ✓ Frontend can retry failed downloads                      │
    │ ✓ Shows alternative URLs if primary fails                  │
    └────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    RETRIEVE COMPLETE GEO DATA                            │
│        (GEORegistry.get_complete_geo_data)                              │
│        Single query returns EVERYTHING!                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
    ┌────────────────────────────────────────────────────────────┐
    │ Returns:                                                    │
    │ {                                                           │
    │   "geo_id": "GSE12345",              ← ROOT NODE           │
    │   "title": "...",                                          │
    │   "summary": "...",                                        │
    │   "organism": "Homo sapiens",                              │
    │   "publications": [                  ← All linked papers   │
    │     {                                                       │
    │       "pmid": "11111",                                     │
    │       "doi": "10.1234/example",                            │
    │       "title": "...",                                      │
    │       "relationship": "original",                          │
    │       "urls": [                      ← ALL URLs available  │
    │         {                                                   │
    │           "url": "https://pmc/...",                        │
    │           "source": "pmc",                                 │
    │           "url_type": "pdf_direct",                        │
    │           "confidence": 0.95                               │
    │         },                                                  │
    │         { ... more URLs ... }                              │
    │       ],                                                    │
    │       "download_history": [          ← What happened       │
    │         {                                                   │
    │           "url": "https://pmc/...",                        │
    │           "status": "success",                             │
    │           "file_path": "data/pdfs/GSE12345/original/..."  │
    │         }                                                   │
    │       ]                                                     │
    │     },                                                      │
    │     {                                                       │
    │       "pmid": "22222",                                     │
    │       "relationship": "citing",                            │
    │       "citation_strategy": "strategy_a",                   │
    │       ...                                                   │
    │     }                                                       │
    │   ]                                                         │
    │ }                                                           │
    │                                                             │
    │ ✓ Everything connected through GEO ID                      │
    │ ✓ All publications linked to dataset                       │
    │ ✓ All URLs stored for each publication                     │
    │ ✓ Download history tracked                                 │
    └────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. GEO ID as Root Node ✓

**YES**, the GEO ID (e.g., GSE12345) is the **root/center** of everything:

```sql
-- Schema shows this clearly
geo_datasets (geo_id PRIMARY KEY)    ← ROOT
    ↓
geo_publications (geo_id FOREIGN KEY)    ← Links to publications
    ↓
publications (id PRIMARY KEY, pmid UNIQUE)    ← Publications
    ↓
download_history (publication_id FOREIGN KEY)    ← Download tracking
```

### 2. Two Identifier Systems

#### A. **Registry IDs** (Internal Database)
- `geo_datasets.geo_id` - GEO ID (e.g., "GSE12345")
- `publications.id` - Auto-increment integer (internal)
- `publications.pmid` - PMID string for lookups (e.g., "11111")

#### B. **Universal File Naming** (PDF Storage)
- Hierarchy: PMID → DOI → PMC → arXiv → Hash
- Used for **consistent filenames** across all sources
- Example: `PMID_11111.pdf`, `DOI_10.1234_example.pdf`
- **Same identifier = same file** (no duplicates!)

### 3. URL Collection Process

**11 Sources** try to find fulltext for EACH publication:

```python
# Uses Publication identifiers:
- PMID: "11111"           ← From GEO API or PubMed
- DOI: "10.1234/example"  ← From PubMed metadata
- PMC ID: "PMC5678910"    ← From PubMed metadata

# Sources try different URLs:
PMC:         4 URL patterns (OA API, Direct PDF, EuropePMC, Reader)
Unpaywall:   Uses DOI, returns PDF + landing URLs
OpenAlex:    Uses DOI
CORE:        Uses DOI or title
bioRxiv:     Uses DOI
arXiv:       Uses arXiv ID
...and 5 more sources

# Result: 10-20+ URLs per publication!
```

### 4. URL Type Classification (Phase 2)

Each URL is classified by **type**:

```python
URLType.PDF_DIRECT      # Direct PDF download
URLType.HTML_FULLTEXT   # HTML with full article text
URLType.LANDING_PAGE    # Publisher page (need extraction)
URLType.DOI_RESOLVER    # DOI redirect
URLType.UNKNOWN         # Unclassified
```

### 5. Type-Aware Sorting (Phase 3)

URLs sorted **before download** for efficiency:

```python
Sorted order:
1. PDF_DIRECT (fastest)      # Try these FIRST
2. HTML_FULLTEXT (parsing)   # Try these SECOND
3. LANDING_PAGE (slowest)    # Try these LAST

Within each type: sorted by source priority
```

### 6. Download Waterfall

```python
For each publication:
    1. Get ALL URLs from 11 sources (10-20 URLs)
    2. Sort by type (PDF → HTML → Landing)
    3. Try URLs in order with 2 retries each
    4. First success: STOP, save PDF
    5. Record EVERY attempt in download_history
```

### 7. Everything Tied to GEO ID

```
Query for GEO dataset
    ↓
GEO API returns: GSE12345 + [PMID 11111]  ← Root connection
    ↓
Citation discovery adds: [PMID 22222, 33333]  ← Citing papers
    ↓
Registry stores:
    - geo_datasets: GSE12345
    - publications: 11111, 22222, 33333
    - geo_publications: Links between them
    ↓
URL collection for EACH publication:
    - PMID 11111 → 15 URLs
    - PMID 22222 → 12 URLs
    - PMID 33333 → 18 URLs
    ↓
Registry stores URLs:
    - publications.urls (JSON column)
    ↓
Download PDFs:
    - data/pdfs/GSE12345/original/PMID_11111.pdf
    - data/pdfs/GSE12345/citing/PMID_22222.pdf
    - data/pdfs/GSE12345/citing/PMID_33333.pdf
    ↓
Registry stores download history:
    - download_history: Success/failure per URL
    ↓
Retrieve everything:
    registry.get_complete_geo_data("GSE12345")
    Returns: GEO + all publications + all URLs + download history
```

## Summary

**Answer to your question:**

1. **GEO ID is the root** ✓
   - All data connects through `geo_datasets.geo_id`

2. **Publication identifiers** (PMID, DOI, PMC) are:
   - Stored in `publications` table
   - Linked to GEO via `geo_publications` table
   - Used to **query fulltext sources**

3. **URLs are collected** from 11 sources:
   - Using PMID, DOI, PMC ID as query parameters
   - Each source returns 1-4 URLs
   - Total: 10-20+ URLs per publication

4. **URLs are registered** in database:
   - Stored in `publications.urls` (JSON column)
   - Includes url_type, confidence, priority
   - Available for retry if download fails

5. **URLs are sorted** by type:
   - PDF → HTML → Landing (fastest to slowest)
   - Within type: sorted by source priority

6. **PDFs are downloaded**:
   - Using UniversalIdentifier for filename (PMID → DOI → PMC → arXiv → Hash)
   - Organized by GEO ID: `data/pdfs/{geo_id}/{original|citing}/`
   - Each attempt recorded in `download_history`

7. **Everything queryable by GEO ID**:
   - Single query returns: dataset + publications + URLs + download history
   - GEO ID is the **root node** that ties everything together

**Result**: Complete traceability from query → GEO ID → publications → URLs → downloads!
