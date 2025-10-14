# Quick Answer: How Everything Connects to GEO ID

## TL;DR

**YES, GEO ID is the root/center**. Everything else connects to it:

```
                        GEO ID: "GSE12345"
                               │
                ┌──────────────┼──────────────┐
                │              │              │
         Original Paper   Citing Paper 1  Citing Paper 2
         PMID: 11111      PMID: 22222     PMID: 33333
                │              │              │
         15 URLs          12 URLs         18 URLs
                │              │              │
         Downloaded       Downloaded      Downloaded
         PMID_11111.pdf   PMID_22222.pdf  PMID_33333.pdf
```

All files stored under: `data/pdfs/GSE12345/`

## Step-by-Step Flow

### 1. User Searches → GEO Dataset Found

```
User: "breast cancer"
    ↓
SearchOrchestrator finds: GSE12345
    ↓
Registry stores: geo_datasets.geo_id = "GSE12345" ← ROOT NODE
```

### 2. GEO Dataset Has PubMed IDs

```
GEO API response includes:
{
  "geo_id": "GSE12345",
  "title": "Breast Cancer Study",
  "pubmed_ids": ["11111"]  ← Link to publication
}
```

### 3. Citation Discovery Finds More Papers

```
GEOCitationDiscovery searches for:
- Papers that CITE PMID 11111 (Strategy A)
- Papers that MENTION "GSE12345" (Strategy B)

Discovers: PMID 22222, PMID 33333
```

### 4. Registry Links Everything to GEO ID

```sql
-- Table: geo_publications (JOIN TABLE)
geo_id    | publication_id | relationship | strategy
----------|----------------|--------------|----------
GSE12345  | 1 (PMID 11111) | original     | NULL
GSE12345  | 2 (PMID 22222) | citing       | strategy_a
GSE12345  | 3 (PMID 33333) | citing       | strategy_b
```

### 5. Fetch Publication Metadata

```
PubMedClient.fetch_by_id("11111")
    ↓
Returns:
{
  "pmid": "11111",
  "doi": "10.1234/example",     ← Used for URL collection
  "pmc_id": "PMC5678910",       ← Used for URL collection
  "title": "Original Paper",
  "authors": [...]
}
```

### 6. Collect URLs Using Publication IDs

```
FullTextManager.get_all_fulltext_urls(publication)

Uses PMID, DOI, PMC ID to query 11 sources:
1. PMC (using PMC ID) → 4 URLs
2. Unpaywall (using DOI) → 2 URLs
3. OpenAlex (using DOI) → 1 URL
4. CORE (using DOI) → 2 URLs
5. bioRxiv (using DOI) → 1 URL
... 6 more sources

Total: 15 URLs for this publication
```

### 7. Store URLs in Registry

```sql
-- Table: publications
id | pmid  | doi           | pmc_id      | urls (JSON)
---|-------|---------------|-------------|-------------
1  | 11111 | 10.1234/...   | PMC5678910  | [15 URLs]
2  | 22222 | 10.5678/...   | PMC9999999  | [12 URLs]
3  | 33333 | 10.9012/...   | NULL        | [18 URLs]

-- Each URLs array contains:
[
  {
    "url": "https://pmc/.../paper.pdf",
    "source": "pmc",
    "priority": 2,
    "url_type": "pdf_direct",
    "confidence": 0.95
  },
  { ... 14 more URLs ... }
]
```

### 8. Sort URLs by Type (Phase 3)

```
For PMID 11111's 15 URLs:

Before sorting (random order):
1. Landing page (CrossRef)
2. PDF (PMC)
3. Landing page (Unpaywall)
4. PDF (OpenAlex)
5. HTML (bioRxiv)
...

After sorting (type-aware):
1. PDF (PMC) priority=2           ← Try FIRST (fastest)
2. PDF (OpenAlex) priority=3
3. PDF (CORE) priority=4
4. HTML (bioRxiv) priority=3      ← Try SECOND
5. Landing (CrossRef) priority=5  ← Try LAST (slowest)
...
```

### 9. Download with Fallback

```
PDFDownloadManager.download_with_fallback()

Try sorted URLs in order:
1. Try PDF from PMC → SUCCESS! ← Stop here
   File size: 1.2 MB
   Validated as PDF: ✓
   
   Save to: data/pdfs/GSE12345/original/PMID_11111.pdf
   
   (Skip remaining 14 URLs)

Record in download_history:
- url: "https://pmc/..."
- source: "pmc"
- status: "success"
- file_path: "data/pdfs/GSE12345/original/PMID_11111.pdf"
```

### 10. File Naming: Universal Identifier

```python
UniversalIdentifier.generate(publication)

Hierarchy (first available wins):
1. PMID: "11111" → "PMID_11111.pdf"           ✓ Used
2. DOI: "10.1234/example" → "DOI_10.1234_example.pdf"
3. PMC: "PMC5678910" → "PMC_5678910.pdf"
4. arXiv: "2101.12345" → "ARXIV_2101.12345.pdf"
5. Hash: "abc123..." → "HASH_abc123.pdf"

Result: PMID_11111.pdf
```

### 11. Organize by GEO ID

```
File structure:
data/pdfs/
  GSE12345/                    ← GEO ID folder
    original/                  ← Original paper(s)
      PMID_11111.pdf
    citing/                    ← Citing papers
      PMID_22222.pdf
      PMID_33333.pdf
    metadata.json              ← Complete record
```

### 12. metadata.json: Complete Record

```json
{
  "geo": {
    "geo_id": "GSE12345",      ← ROOT NODE
    "title": "Breast Cancer Study",
    "pubmed_ids": ["11111"]
  },
  "papers": {
    "original": [
      {
        "pmid": "11111",
        "doi": "10.1234/example",
        "pmc_id": "PMC5678910",
        "pdf_path": "original/PMID_11111.pdf",
        "fulltext_source": "pmc",
        "all_urls": [          ← RETRY CAPABILITY!
          {
            "url": "https://pmc/.../paper.pdf",
            "source": "pmc",
            "url_type": "pdf_direct",
            "priority": 2
          },
          { ... 14 more URLs for retry ... }
        ]
      }
    ],
    "citing": [
      { ... PMID 22222 with 12 URLs ... },
      { ... PMID 33333 with 18 URLs ... }
    ]
  }
}
```

### 13. Query Everything by GEO ID

```python
registry.get_complete_geo_data("GSE12345")

Returns in ONE query:
{
  "geo_id": "GSE12345",        ← ROOT
  "title": "Breast Cancer Study",
  "publications": [
    {
      "pmid": "11111",
      "relationship": "original",
      "urls": [15 URLs],       ← All URLs available
      "download_history": [
        {
          "url": "https://pmc/...",
          "status": "success",
          "file_path": "data/pdfs/GSE12345/original/PMID_11111.pdf"
        }
      ]
    },
    {
      "pmid": "22222",
      "relationship": "citing",
      "citation_strategy": "strategy_a",
      "urls": [12 URLs],
      "download_history": [...]
    },
    {
      "pmid": "33333",
      "relationship": "citing",
      "citation_strategy": "strategy_b",
      "urls": [18 URLs],
      "download_history": [...]
    }
  ]
}
```

## Key Insights

### Two Identifier Systems

**1. Registry IDs** (Internal - for relationships)
- `geo_id`: "GSE12345" (PRIMARY KEY)
- `pmid`: "11111" (UNIQUE, for lookups)
- `publications.id`: Auto-increment integer (FOREIGN KEY target)

**2. Universal IDs** (External - for file naming)
- Used for **consistent filenames** across all sources
- Hierarchy: PMID → DOI → PMC → arXiv → Hash
- **Same ID = same file** (no duplicates!)

### URL Collection Uses Publication IDs

```
Publication has:
- PMID: "11111"        ← Query PubMed, PMC
- DOI: "10.1234/..."   ← Query Unpaywall, OpenAlex, CrossRef, CORE, etc.
- PMC ID: "PMC5678910" ← Query PMC (4 patterns)

Each source returns 1-4 URLs
Total: 10-20 URLs per publication
```

### Everything Connected Through GEO ID

```
Database structure:

geo_datasets (geo_id="GSE12345")
    ↓ 1:N
geo_publications (geo_id="GSE12345", publication_id=1)
    ↓ N:1
publications (id=1, pmid="11111", urls=[15 URLs])
    ↓ 1:N
download_history (publication_id=1, url="...", status="success")

File structure:

data/pdfs/GSE12345/
    ↓
  original/PMID_11111.pdf
  citing/PMID_22222.pdf
  citing/PMID_33333.pdf
  metadata.json (complete record)
```

### URLs Stored for Retry

**Why store ALL URLs?**
1. Primary URL might fail later
2. Frontend can show alternative sources
3. Analytics: Which sources work best?
4. Historical record: What was available?

**Example**: PMID 11111 has 15 URLs stored
- Try URL #1 (PMC PDF) → Success! Use this one
- URLs #2-15 stored in registry for retry if needed

### Type-Aware Optimization (Phase 3)

**Before**:
- Try URLs in random order
- Might hit slow landing page first (5-10s)

**After**:
- Sort by type: PDF → HTML → Landing
- Try fast PDF URLs first (0.5s)
- Only try landing pages if PDFs fail

**Result**: 20-30% faster downloads!

## Summary Table

| Component | Purpose | Root Connection |
|-----------|---------|-----------------|
| **GEO ID** | Root node | N/A (this IS the root) |
| **PMID** | Publication identifier | Linked via `geo_publications.publication_id` |
| **DOI** | Alternative pub ID | Stored in `publications.doi`, used for URL queries |
| **PMC ID** | Alternative pub ID | Stored in `publications.pmc_id`, used for URL queries |
| **URLs** | Download sources | Stored in `publications.urls` JSON (10-20 per pub) |
| **PDFs** | Downloaded files | Saved to `data/pdfs/{geo_id}/` |
| **Universal ID** | File naming | Generated from PMID→DOI→PMC→arXiv→Hash |
| **Download History** | Tracking | Links to `publications.id` via `publication_id` |

## Final Answer

**Q: Is GEO ID the root/center?**

**A: YES!** 

- GEO ID is the PRIMARY KEY in `geo_datasets`
- All publications link to GEO via `geo_publications.geo_id`
- All files organized by GEO: `data/pdfs/{geo_id}/`
- Single query by GEO ID returns everything: dataset + publications + URLs + downloads
- **Everything traces back to GEO ID**

**Q: How are URLs collected?**

**A: Using publication identifiers (PMID, DOI, PMC ID)**

1. GEO dataset has PMID(s) → Original paper(s)
2. Citation discovery finds more PMIDs → Citing papers
3. PubMed enriches each PMID with DOI, PMC ID
4. 11 sources queried using these IDs → 10-20 URLs per publication
5. URLs stored in `publications.urls` (JSON) → Retry capability

**Q: How are PDFs downloaded?**

**A: Type-aware waterfall with universal naming**

1. Sort URLs: PDF (fast) → HTML → Landing (slow)
2. Try URLs in order with retries
3. First success: Validate + Save with Universal ID filename
4. Organize by GEO: `data/pdfs/{geo_id}/{original|citing}/`
5. Track every attempt in `download_history`

**Result**: Complete traceability from query → GEO ID → publications → URLs → downloads!
