# Citation Discovery Flow - Complete Trace Diagram

**Date:** October 14, 2025  
**Status:** Active Production Code  
**Entry Point:** FastAPI `/api/search/geo` endpoint

---

## 🌳 Complete Citation Discovery Tree

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (User Request)                          │
│                    "Find papers citing GSE189158"                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API ENDPOINT (FastAPI Route)                          │
│  File: omics_oracle_v2/api/routes/agents.py                             │
│  Route: POST /api/search/geo                                             │
│  Handler: enrich_with_fulltext()                                         │
│                                                                           │
│  Parameters:                                                              │
│  - include_citing_papers: bool = True                                    │
│  - max_citing_papers: int = 100                                          │
│  - download_original: bool = True                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              CITATION DISCOVERY INITIALIZATION (Line 416)                │
│  citation_discovery = GEOCitationDiscovery()                             │
│                                                                           │
│  Creates:                                                                 │
│  ├─ OpenAlexClient (for Strategy A: citation-based)                     │
│  └─ PubMedClient   (for Strategy B: mention-based + metadata)           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     │                       │
          For each GEO dataset              │
                     │                       │
                     ▼                       ▼
┌─────────────────────────────────┐ ┌──────────────────────────────┐
│  STEP 1: Original Papers        │ │  STEP 2: Citing Papers       │
│  (Line 438-455)                 │ │  (Line 457-488)              │
│                                 │ │                              │
│  Fetch original publication     │ │  Convert to GEOSeriesMetadata│
│  metadata from PubMed           │ │  (geo_id, title, pubmed_ids) │
│                                 │ │                              │
│  pubmed_client.fetch_by_id()    │ │  ▼                           │
│                                 │ │  Call citation_discovery     │
└─────────────────────────────────┘ └──────────────┬───────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    GEO CITATION DISCOVERY CORE                           │
│  File: omics_oracle_v2/lib/citations/discovery/geo_discovery.py         │
│  Class: GEOCitationDiscovery                                             │
│  Method: find_citing_papers() [Line 73]                                  │
│                                                                           │
│  Input: GEOSeriesMetadata (geo_id, title, pubmed_ids)                   │
│  Output: CitationDiscoveryResult (citing_papers, strategy_breakdown)    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                │
                 ▼                                ▼
┌────────────────────────────────┐  ┌────────────────────────────────┐
│  STRATEGY A: Citation-Based    │  │  STRATEGY B: Mention-Based     │
│  (Line 95-102)                 │  │  (Line 104-112)                │
│                                │  │                                │
│  _find_via_citation()          │  │  _find_via_geo_mention()       │
│  [Line 124]                    │  │  [Line 159]                    │
└────────────┬───────────────────┘  └────────────┬───────────────────┘
             │                                   │
             ▼                                   ▼
┌────────────────────────────────┐  ┌────────────────────────────────┐
│  Strategy A Implementation     │  │  Strategy B Implementation     │
│  (Lines 124-157)               │  │  (Lines 159-175)               │
│                                │  │                                │
│  1. Fetch original publication │  │  1. Build PubMed query         │
│     pubmed_client.fetch_by_id()│  │     query = "{geo_id}[All]"    │
│     → Get DOI                  │  │                                │
│                                │  │  2. Search PubMed              │
│  2. Find citing papers         │  │     pubmed_client.search()     │
│     openalex.get_citing_papers()│  │     → Papers mentioning GEO ID │
│     → Papers citing DOI        │  │                                │
└────────────┬───────────────────┘  └────────────┬───────────────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL API CALLS (Leaf Nodes)                       │
│                                                                           │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │ PubMedClient            │  │ OpenAlexClient                       │  │
│  │ (NCBI E-utilities)      │  │ (OpenAlex API)                       │  │
│  │                         │  │                                      │  │
│  │ • fetch_by_id(pmid)     │  │ • get_citing_papers(doi)             │  │
│  │   → Publication metadata│  │   → List[Publication]                │  │
│  │   → DOI, PMCID, etc.    │  │   → Papers citing this DOI           │  │
│  │                         │  │                                      │  │
│  │ • search(query)         │  │ Rate Limit: 10 req/sec               │  │
│  │   → List[Publication]   │  │ Free, no API key needed              │  │
│  │   → Papers matching     │  │                                      │  │
│  │     query string        │  │                                      │  │
│  └─────────────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESULT AGGREGATION & DEDUPLICATION                    │
│  (geo_discovery.py, Lines 114-121)                                       │
│                                                                           │
│  1. Combine Strategy A + Strategy B results                              │
│  2. Deduplicate by Publication object equality                           │
│  3. Track which papers came from which strategy                          │
│  4. Return CitationDiscoveryResult                                       │
│     - citing_papers: List[Publication]                                   │
│     - strategy_breakdown: {"strategy_a": [...], "strategy_b": [...]}    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACK TO API HANDLER (agents.py)                       │
│  (Lines 475-488)                                                          │
│                                                                           │
│  citation_result = await citation_discovery.find_citing_papers(...)      │
│                                                                           │
│  Store results:                                                           │
│  - papers_to_download["citing"] = citation_result.citing_papers          │
│  - Log: Found X citing papers                                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FULLTEXT URL COLLECTION                               │
│  (agents.py, Lines 496-530)                                              │
│                                                                           │
│  For all papers (original + citing):                                     │
│  1. Get fulltext URLs from all sources (PMC, Unpaywall, etc.)           │
│  2. Store URLs on publication objects                                    │
│  3. Build fulltext metadata list                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RETURN TO FRONTEND                                    │
│                                                                           │
│  DatasetResponse {                                                        │
│    geo_id: "GSE189158"                                                   │
│    fulltext: [                                                            │
│      {pmid, doi, title, url, source, paper_type: "citing"},             │
│      {pmid, doi, title, url, source, paper_type: "citing"},             │
│      {pmid, doi, title, url, source, paper_type: "original"}            │
│    ]                                                                      │
│    fulltext_count: 8                                                     │
│    fulltext_status: "available"                                          │
│  }                                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
GEO Dataset (GSE189158)
    │
    ├─ pubmed_ids: ["12345"]  ──────────────┐
    ├─ geo_id: "GSE189158"    ──────┐       │
    └─ title, summary, etc.         │       │
                                    │       │
                                    ▼       ▼
                            Strategy B  Strategy A
                            (Mention)   (Citation)
                                │           │
                                │           ├─ Fetch PMID 12345 metadata
                                │           │  → Get DOI
                                │           │
                                │           ├─ Query OpenAlex
                                │           │  "Papers citing DOI X"
                                │           │
                    Query PubMed◄───┘       │
                    "GSE189158[All]"        │
                          │                 │
                          │                 │
                          ▼                 ▼
                    Papers mentioning   Papers citing
                    GEO ID in text      original paper
                          │                 │
                          └────────┬────────┘
                                   │
                                   ▼
                          Deduplicated List
                          of Citing Papers
                                   │
                                   ▼
                          Get Fulltext URLs
                          (PMC, Unpaywall, etc.)
                                   │
                                   ▼
                          Return to Frontend
```

---

## 🔍 Method Call Hierarchy

```
agents.enrich_with_fulltext()
    │
    ├─ GEOCitationDiscovery.__init__()
    │   ├─ OpenAlexClient.__init__()
    │   └─ PubMedClient.__init__()
    │
    ├─ For original papers:
    │   └─ PubMedClient.fetch_by_id(pmid)
    │       └─ HTTP: NCBI E-utilities API
    │
    └─ For citing papers:
        └─ GEOCitationDiscovery.find_citing_papers(geo_metadata)
            │
            ├─ Strategy A: _find_via_citation(pmid)
            │   ├─ PubMedClient.fetch_by_id(pmid)  # Get DOI
            │   │   └─ HTTP: NCBI E-utilities API
            │   │
            │   └─ OpenAlexClient.get_citing_papers(doi)
            │       └─ HTTP: OpenAlex API
            │
            └─ Strategy B: _find_via_geo_mention(geo_id)
                └─ PubMedClient.search(query)
                    └─ HTTP: NCBI E-utilities API
```

---

## 🗂️ File Dependencies

```
omics_oracle_v2/api/routes/agents.py
    │
    ├─ imports: GEOCitationDiscovery
    │   from omics_oracle_v2.lib.citations.discovery.geo_discovery
    │
    └─ imports: PubMedClient
        from omics_oracle_v2.lib.search_engines.citations.pubmed

omics_oracle_v2/lib/citations/discovery/geo_discovery.py
    │
    ├─ imports: OpenAlexClient, OpenAlexConfig
    │   from omics_oracle_v2.lib.search_engines.citations.openalex
    │
    ├─ imports: PubMedClient, PubMedConfig
    │   from omics_oracle_v2.lib.search_engines.citations.pubmed
    │
    ├─ imports: Publication
    │   from omics_oracle_v2.lib.search_engines.citations.models
    │
    └─ imports: GEOSeriesMetadata
        from omics_oracle_v2.lib.search_engines.geo.models

omics_oracle_v2/lib/search_engines/citations/openalex.py
    └─ HTTP calls to: https://api.openalex.org/works

omics_oracle_v2/lib/search_engines/citations/pubmed.py
    └─ HTTP calls to: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

---

## 🎯 Key Design Decisions

### Why Two Strategies?

**Strategy A (Citation-Based):**
- **Purpose:** Find papers that formally cite the original publication
- **Pros:** High quality, peer-reviewed citations
- **Cons:** Misses papers that use the dataset but don't cite the paper
- **Source:** OpenAlex (free, comprehensive citation graph)

**Strategy B (Mention-Based):**
- **Purpose:** Find papers that mention the GEO ID in their text
- **Pros:** Catches papers that reuse the dataset without citing original
- **Cons:** May include false positives (just mentioning, not using)
- **Source:** PubMed (full-text search)

**Combined Result:** Maximum coverage with deduplication

### Why OpenAlex Instead of Google Scholar?

✅ **OpenAlex:**
- Free, open API
- 10 requests/second (no API key needed)
- 250M+ works with full citation graph
- Reliable, no CAPTCHA blocking

❌ **Google Scholar:**
- No official API
- Requires web scraping
- CAPTCHA blocking after few requests
- Rate limiting issues
- **Already deleted** (scholar.py removed in commit b7d9ed1)

### Why GEO Citation Discovery is Separate from General Citation Finding?

**GEO-specific requirements:**
1. Handle datasets without publications (geo_id-only search)
2. Two-strategy approach (citation + mention)
3. Convert between GEO models and Publication models
4. Track strategy breakdown for analytics
5. Handle missing PMIDs gracefully

---

## 📈 Performance Characteristics

### API Call Count per GEO Dataset:

**With 1 original paper + citing papers enabled:**
```
PubMed API calls:
  - 1 call: Fetch original paper metadata (get DOI)
  - 1 call: Search papers mentioning GEO ID
  Total: 2 calls

OpenAlex API calls:
  - 1 call: Get papers citing the DOI
  Total: 1 call

TOTAL: 3 external API calls per GEO dataset
```

### Rate Limits:

- **PubMed:** 3 req/sec (no key) or 10 req/sec (with API key)
- **OpenAlex:** 10 req/sec (no key needed)
- **Overall:** ~3 datasets/second = 180 datasets/minute

### Response Time (Typical):

```
Strategy A (Citation-based):  500-1000ms
Strategy B (Mention-based):   300-700ms
Deduplication:                 <10ms
-------------------------------------------
Total per dataset:             800-1700ms
```

---

## 🔄 Complete Request Flow Example

**User Action:** Search for "breast cancer RNA-seq", click "Download Papers" for GSE189158

```
1. Frontend → POST /api/search/geo
   Body: {
     "datasets": [{ geo_id: "GSE189158", ... }],
     "include_citing_papers": true,
     "max_citing_papers": 100
   }

2. API Handler → Initialize GEOCitationDiscovery
   - Creates OpenAlexClient
   - Creates PubMedClient

3. For GSE189158 (pubmed_ids: ["33199918"]):
   
   a. Strategy A (Citation):
      - Fetch PMID 33199918 → DOI: 10.1038/s41467-020-19517-z
      - Query OpenAlex for papers citing this DOI
      - Found: 8 papers
   
   b. Strategy B (Mention):
      - Query PubMed: "GSE189158[All Fields]"
      - Found: 3 papers
   
   c. Deduplicate:
      - Combined: 11 papers (8 + 3)
      - After dedup: 10 papers (1 overlap)

4. For each paper → Get fulltext URLs
   - Query PMC, Unpaywall, etc.
   - Store URLs on publication objects

5. Return to frontend:
   - 10 citing papers with URLs
   - 1 original paper with URL
   - Total: 11 papers ready for download
```

---

## 🚀 Future Enhancements

### Potential Strategy C: Crossref Integration
```python
# Strategy C: Papers citing via Crossref
def _find_via_crossref(self, doi: str) -> List[Publication]:
    """Alternative to OpenAlex, more comprehensive for recent papers"""
    pass
```

### Potential Strategy D: Semantic Search
```python
# Strategy D: Papers semantically similar to dataset
def _find_via_semantic(self, geo_metadata: GEOSeriesMetadata) -> List[Publication]:
    """Use embeddings to find related papers by content"""
    pass
```

---

**Author:** OmicsOracle Architecture Team  
**Last Updated:** October 14, 2025  
**Status:** Production-Ready ✅
