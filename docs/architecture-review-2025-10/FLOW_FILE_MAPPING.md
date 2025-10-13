# OmicsOracle: Complete Flow Stage File Mapping

**Date:** October 13, 2025
**Purpose:** Map every file to its actual flow stage for accurate reorganization

---

## Flow Overview

```
User Query → Query Processing → Search (GEO + Citations) → Display →
Full-text Download → PDF Parse → Display → AI Analysis → Display
```

---

## Stage 1: User Interface (Frontend)

### Files Involved

**Active:**
- `omics_oracle_v2/api/static/dashboard_v2.html` (1,913 LOC)
  - User input form
  - Search button handler
  - Results display
  - Download Papers button
  - Analyze with AI button
  - All JavaScript frontend logic

**Purpose:** User interaction and display

**Triggers:**
- Stage 2 (Query Processing) - when user clicks "Search"
- Stage 7 (Full-text Download) - when user clicks "Download Papers"
- Stage 11 (AI Analysis) - when user clicks "Analyze with AI"

---

## Stage 2: API Gateway (Request Routing)

### Files Involved

**Active:**
- `omics_oracle_v2/api/routes/agents.py` (881 LOC)
  - `/search` endpoint (lines 34-275)
  - `/enrich-fulltext` endpoint (lines 283-656)
  - `/analyze` endpoint (lines 700-790)
- `omics_oracle_v2/api/main.py`
  - FastAPI app initialization
  - Route registration
  - CORS middleware
- `omics_oracle_v2/api/models/requests.py`
  - SearchRequest
  - EnrichmentRequest
  - AnalysisRequest
- `omics_oracle_v2/api/models/responses.py`
  - SearchResponse
  - DatasetResponse
  - PublicationResponse
  - AIAnalysisResponse

**Purpose:** HTTP request handling and routing

**Flow:**
- Receives HTTP POST from frontend
- Validates request models
- Routes to appropriate stage
- Returns JSON responses

---

## Stage 3: Query Processing (NLP)

### Files Involved

**Active:**
- `omics_oracle_v2/lib/nlp/biomedical_ner.py` (401 LOC)
  - Named Entity Recognition (NER)
  - Extract: genes, diseases, proteins, chemicals
  - Uses: SciSpacy models (en_ner_bc5cdr_md, en_ner_bionlp13cg_md)
- `omics_oracle_v2/lib/nlp/query_expander.py` (186 LOC)
  - Synonym expansion
  - Query broadening
- `omics_oracle_v2/lib/nlp/synonym_expansion.py` (255 LOC)
  - Medical terminology synonyms
  - MeSH term expansion
- `omics_oracle_v2/lib/query/analyzer.py` (392 LOC)
  - Detect query type: GEO_ID, KEYWORD, HYBRID
  - Pattern matching: "GSE\d+" for GEO IDs
  - Confidence scoring
- `omics_oracle_v2/lib/query/optimizer.py` (370 LOC)
  - Query optimization pipeline
  - NER + SapBERT semantic expansion
  - Entity extraction and ranking

**Supporting:**
- `omics_oracle_v2/lib/nlp/models.py`
  - NER entity models
  - Query analysis models

**Purpose:** Transform user query into optimized search terms

**Input:** "diabetes" (raw user query)
**Output:** "diabetes mellitus OR hyperglycemia" (optimized query)

---

## Stage 4: Search Orchestration (Coordination)

### Files Involved

**Active:**
- `omics_oracle_v2/lib/search/orchestrator.py` (489 LOC)
  - Main orchestration logic
  - Parallel execution coordinator
  - Result combination and deduplication
  - Cache integration
- `omics_oracle_v2/lib/search/config.py`
  - SearchConfig
  - OrchestratorConfig
  - Enable/disable sources
- `omics_oracle_v2/lib/search/models.py`
  - SearchResult
  - SearchMetadata

**Purpose:** Coordinate parallel searches across multiple sources

**Flow:**
1. Initialize clients (GEO, PubMed, OpenAlex)
2. Launch parallel searches with `asyncio.gather()`
3. Combine results
4. Deduplicate
5. Cache results

---

## Stage 5a: GEO Dataset Search (PRIMARY SEARCH)

### Files Involved

**Active:**
- `omics_oracle_v2/lib/geo/client.py` (662 LOC) ⭐ **CORE SEARCH ENGINE**
  - `search()` - Query NCBI GEO database
  - `get_metadata()` - Fetch full dataset metadata
  - Uses: NCBI E-utilities API
- `omics_oracle_v2/lib/geo/query_builder.py` (246 LOC)
  - Build GEO-specific Entrez queries
  - Add field tags: [Organism], [DataSet Type], [All Fields]
  - Modes: aggressive, balanced, precise
- `omics_oracle_v2/lib/geo/models.py` (266 LOC)
  - GEOSeriesMetadata (main dataset model)
  - SearchResult
  - SRAInfo
  - ClientInfo
- `omics_oracle_v2/lib/geo/utils.py` (132 LOC)
  - RateLimiter
  - retry_with_backoff decorator
- `omics_oracle_v2/lib/geo/cache.py` (45 LOC)
  - SimpleCache (in-memory caching)

**Purpose:** Search NCBI GEO database for omics datasets

**API Flow:**
```
query → query_builder.build_query() → client.search() → NCBI E-utilities
→ Parse XML/JSON → GEOSeriesMetadata objects
```

**Output:**
```python
GEOSeriesMetadata(
    geo_id="GSE123456",
    title="Diabetes gene expression study",
    summary="...",
    organism="Homo sapiens",
    sample_count=120,
    platform="GPL570",
    pubmed_ids=["12345678", "87654321"]  # ← Critical for next stages!
)
```

---

## Stage 5b: Citation/Publication Search

### Files Involved

**Active:**

**PubMed Search:**
- `omics_oracle_v2/lib/publications/clients/pubmed.py` (398 LOC)
  - `search()` - Search PubMed database
  - `fetch_by_id()` - Get publication by PMID
  - Uses: Biopython Entrez
- `omics_oracle_v2/lib/publications/clients/async_pubmed.py` (354 LOC)
  - Async version of PubMed client
  - Batch fetching

**OpenAlex Search:**
- `omics_oracle_v2/lib/citations/clients/openalex.py` (526 LOC)
  - `search_publications()` - Search OpenAlex
  - `get_citing_papers()` - Find citing papers
  - Uses: OpenAlex REST API
- `omics_oracle_v2/lib/citations/clients/openalex_config.py`
  - OpenAlexConfig

**Google Scholar Search:**
- `omics_oracle_v2/lib/citations/clients/scholar.py` (287 LOC)
  - Google Scholar scraping (if enabled)

**Semantic Scholar:**
- `omics_oracle_v2/lib/citations/clients/semantic_scholar.py` (312 LOC)
  - Semantic Scholar API

**Supporting:**
- `omics_oracle_v2/lib/publications/clients/base.py` (158 LOC)
  - BasePublicationClient
  - Common interface for all clients
- `omics_oracle_v2/lib/publications/models.py` (398 LOC)
  - Publication (main publication model)
  - PublicationSource enum
  - PublicationResult
- `omics_oracle_v2/lib/publications/config.py`
  - PubMedConfig

**Purpose:** Search for related publications

**Output:**
```python
Publication(
    pmid="12345678",
    title="...",
    abstract="...",
    doi="10.1234/...",
    authors=[...],
    journal="Nature",
    year=2023,
    source=PublicationSource.PUBMED
)
```

---

## Stage 6: Results Display (Frontend)

**Same as Stage 1** - `dashboard_v2.html` displays results

**Shows:**
- Dataset cards with metadata
- Publication list
- "Download Papers" button (triggers Stage 7)

---

## Stage 7: Full-text URL Discovery (Waterfall)

### Files Involved

**Orchestrator:**
- `omics_oracle_v2/lib/fulltext/manager.py` (1,185 LOC) ⭐ **URL DISCOVERY COORDINATOR**
  - `get_fulltext()` - Single publication URL discovery
  - `get_fulltext_batch()` - Batch URL discovery
  - Waterfall logic through 11 sources
  - `get_statistics()` - Source usage stats

**11 URL Sources:**

**1. Free/Official Sources:**
- `omics_oracle_v2/lib/publications/clients/oa_sources.py` (892 LOC)
  - PMC (PubMed Central) - Official free PDFs
  - DOAJ (Directory of Open Access Journals)
  - Europe PMC (European mirror)
  - BASE (Bielefeld Academic Search Engine)
  - CORE (COnnecting REpositories)

**2. Aggregator Sources:**
- `omics_oracle_v2/lib/fulltext/sources/unpaywall_client.py` (179 LOC)
  - Unpaywall API - Legal free PDFs
  - Uses: DOI lookup

**3. Institutional Access:**
- `omics_oracle_v2/lib/publications/clients/institutional_access.py` (586 LOC)
  - University/library subscriptions
  - Proxy servers
  - Authentication handling

**4. Alternative Sources:**
- Already covered in openalex.py (has PDF links)
- Already covered in semantic_scholar.py (has PDF links)

**5. Last Resort (Pirate Sources):**
- `omics_oracle_v2/lib/fulltext/sources/scihub_client.py` (156 LOC)
  - Sci-Hub pirate access
  - DOI-based lookup
- `omics_oracle_v2/lib/fulltext/sources/libgen_client.py` (203 LOC)
  - Library Genesis
  - DOI/title-based lookup

**Supporting:**
- `omics_oracle_v2/lib/fulltext/models.py` (158 LOC)
  - FullTextSource enum (11 sources)
  - FullTextResult
  - PDFDownloadResult

**Purpose:** Find PDF URLs using waterfall strategy (try free → institutional → pirate)

**Waterfall Order:**
```
1. PMC (free, official)
2. DOAJ (open access)
3. Europe PMC (European)
4. Unpaywall (legal aggregator)
5. BASE (repository)
6. CORE (repository)
7. Institutional (university)
8. OpenAlex (academic)
9. Sci-Hub (⚠️ pirate)
10. LibGen (⚠️ pirate)
11. Semantic Scholar
```

**Output:**
```python
FullTextResult(
    success=True,
    source=FullTextSource.PMC,
    url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/pdf/",
    pmid="12345678"
)
```

---

## Stage 8: PDF Download

### Files Involved

**Active:**
- `omics_oracle_v2/lib/fulltext/pdf_downloader.py` (447 LOC) ⭐ **PDF DOWNLOAD ENGINE**
  - `download_single()` - Download one PDF
  - `download_batch()` - Download multiple PDFs in parallel
  - Retry logic with exponential backoff
  - Waterfall fallback on failure
  - Saves to: `data/fulltext/pdfs/`

**Supporting:**
- `omics_oracle_v2/lib/fulltext/download_manager.py` (deprecated? check usage)
- Uses `aiohttp` for async HTTP requests
- Uses `aiofiles` for async file I/O

**Purpose:** Download PDFs from URLs with retry logic

**Flow:**
```
URL → aiohttp GET request → Save to data/fulltext/pdfs/PMID_12345678.pdf
If fail → Retry with next source from waterfall
```

**Output:**
- PDF file: `data/fulltext/pdfs/PMID_12345678.pdf`
- Updates publication object: `pub.pdf_path = Path("...")`

---

## Stage 9: PDF Parsing

### Files Involved

**Active:**
- `omics_oracle_v2/lib/fulltext/pdf_parser.py` (568 LOC) ⭐ **TEXT EXTRACTION ENGINE**
  - `parse_pdf()` - Extract text from PDF
  - Section detection (Abstract, Methods, Results, Discussion)
  - Uses: PyMuPDF (fitz) for PDF text extraction
  - Pattern matching for section headers

**Supporting:**
- `omics_oracle_v2/lib/fulltext/text_extractor.py` (if exists)
- Regular expressions for section detection

**Purpose:** Extract structured text from PDFs

**Sections Extracted:**
- Title
- Abstract
- Introduction
- Methods/Materials
- Results
- Discussion
- Conclusion
- References (optional)

**Output:**
```python
{
    "title": "...",
    "abstract": "Background: ... Methods: ... Results: ...",
    "introduction": "...",
    "methods": "We performed RNA-seq on...",
    "results": "We identified 1,234 differentially expressed genes...",
    "discussion": "Our findings suggest...",
    "conclusion": "..."
}
```

---

## Stage 10: Enriched Results Display (Frontend)

**Same as Stage 1** - `dashboard_v2.html`

**Shows:**
- "✅ Downloaded 3/5 papers"
- PDF status per publication
- "Analyze with AI" button (triggers Stage 11)

---

## Stage 11: AI Analysis

### Files Involved

**Active:**
- `omics_oracle_v2/lib/ai/client.py` (284 LOC) ⭐ **LLM CLIENT**
  - `analyze()` - Generate AI analysis
  - `summarize()` - Summarize text
  - Uses: OpenAI API or Anthropic API
  - Model: GPT-4 or Claude

**Prompt Engineering:**
- `omics_oracle_v2/lib/ai/prompts.py` (212 LOC)
  - PromptBuilder
  - Analysis prompt templates
  - System prompts
  - Few-shot examples

**Supporting:**
- `omics_oracle_v2/lib/ai/models.py` (186 LOC)
  - AIAnalysisRequest
  - AIAnalysisResponse
  - SummarizationResult
- `omics_oracle_v2/lib/ai/config.py`
  - AISettings

**Purpose:** Generate AI-powered insights from fulltext

**Context Building:**
```python
# Build context from fulltext
context = f"""
Dataset: {dataset.geo_id} - {dataset.title}
Organism: {dataset.organism}
Samples: {dataset.sample_count}

Publications analyzed:

PMID {pmid}: {title}
Abstract: {abstract}
Methods: {methods}
Results: {results}
Discussion: {discussion}
"""

# Send to LLM
analysis = await llm_client.analyze(query="diabetes", context=context)
```

**Output:**
```python
AIAnalysisResponse(
    success=True,
    analysis="This dataset investigates diabetes...",
    insights=[
        "Key finding 1: ...",
        "Key finding 2: ...",
    ],
    recommendations=[
        "Consider validating with...",
        "Future work should focus on...",
    ],
    model_used="gpt-4"
)
```

---

## Stage 12: AI Results Display (Frontend)

**Same as Stage 1** - `dashboard_v2.html`

**Shows:**
- AI analysis text
- Key insights (bullet points)
- Recommendations
- Datasets analyzed count

---

## Infrastructure (Cross-cutting Concerns)

### Caching Layer

**Files:**
- `omics_oracle_v2/lib/cache/redis_cache.py` (608 LOC)
  - RedisCache client
  - `get_search_result()`, `set_search_result()`
  - TTL management
- `omics_oracle_v2/lib/cache/redis_client.py` (269 LOC)
  - AsyncRedisCache
  - Connection pooling

**Used by:**
- Stage 4 (Search Orchestrator) - Cache search results
- Stage 7 (Full-text Manager) - Cache URL discovery results

---

### Embeddings Layer (Currently Unused?)

**Files:**
- `omics_oracle_v2/lib/embeddings/service.py` (278 LOC)
  - OpenAI embeddings
  - Text → Vector conversion
- `omics_oracle_v2/lib/embeddings/models.py`
  - EmbeddingRequest, EmbeddingResponse

**Status:** ⚠️ Check if actually used in production flow

---

### Vector Database (Currently Unused?)

**Files:**
- `omics_oracle_v2/lib/vector_db/faiss_db.py` (213 LOC)
  - FAISS vector database
  - Similarity search
- `omics_oracle_v2/lib/vector_db/chroma_db.py` (252 LOC)
  - ChromaDB alternative

**Status:** ⚠️ Check if actually used in production flow

---

### Storage Layer

**Files:**
- `omics_oracle_v2/lib/storage/dataset_storage.py` (295 LOC)
  - Dataset persistence
  - SQLite/PostgreSQL storage
- `omics_oracle_v2/lib/storage/publication_storage.py` (242 LOC)
  - Publication persistence

**Status:** ⚠️ Check if actually used in production flow

---

## Complete File Mapping by Stage

| Stage | Purpose | Core Files | Supporting Files | LOC |
|-------|---------|------------|------------------|-----|
| **1. Frontend** | User Interface | `api/static/dashboard_v2.html` | - | 1,913 |
| **2. API Gateway** | Request Routing | `api/routes/agents.py`<br/>`api/main.py` | `api/models/*.py` | 881 + 200 |
| **3. Query Processing** | NLP Analysis | `lib/nlp/biomedical_ner.py`<br/>`lib/nlp/query_expander.py`<br/>`lib/query/analyzer.py`<br/>`lib/query/optimizer.py` | `lib/nlp/synonym_expansion.py`<br/>`lib/nlp/models.py` | 1,604 |
| **4. Search Orchestration** | Coordination | `lib/search/orchestrator.py` | `lib/search/config.py`<br/>`lib/search/models.py` | 489 + 150 |
| **5a. GEO Search** | Dataset Search | `lib/geo/client.py`<br/>`lib/geo/query_builder.py` | `lib/geo/models.py`<br/>`lib/geo/utils.py`<br/>`lib/geo/cache.py` | 1,351 |
| **5b. Citation Search** | Publication Search | `lib/publications/clients/pubmed.py`<br/>`lib/citations/clients/openalex.py` | `lib/publications/clients/async_pubmed.py`<br/>`lib/publications/clients/base.py`<br/>`lib/publications/models.py`<br/>`lib/citations/clients/scholar.py`<br/>`lib/citations/clients/semantic_scholar.py` | 2,435 |
| **6. Results Display** | Frontend | `api/static/dashboard_v2.html` | - | (same as Stage 1) |
| **7. URL Discovery** | Find PDF URLs | `lib/fulltext/manager.py` | `lib/fulltext/sources/scihub_client.py`<br/>`lib/fulltext/sources/libgen_client.py`<br/>`lib/fulltext/sources/unpaywall_client.py`<br/>`lib/publications/clients/oa_sources.py`<br/>`lib/publications/clients/institutional_access.py`<br/>`lib/fulltext/models.py` | 3,359 |
| **8. PDF Download** | Download PDFs | `lib/fulltext/pdf_downloader.py` | - | 447 |
| **9. PDF Parsing** | Extract Text | `lib/fulltext/pdf_parser.py` | - | 568 |
| **10. Papers Display** | Frontend | `api/static/dashboard_v2.html` | - | (same as Stage 1) |
| **11. AI Analysis** | LLM Insights | `lib/ai/client.py`<br/>`lib/ai/prompts.py` | `lib/ai/models.py`<br/>`lib/ai/config.py` | 682 |
| **12. AI Display** | Frontend | `api/static/dashboard_v2.html` | - | (same as Stage 1) |
| **Infrastructure** | Cross-cutting | `lib/cache/redis_cache.py` | `lib/cache/redis_client.py`<br/>`lib/embeddings/*`<br/>`lib/vector_db/*`<br/>`lib/storage/*` | 2,257 |

**Total Active LOC:** ~15,336 (not counting duplicates and infrastructure)

---

## Files Requiring Investigation (Potentially Unused)

### High Priority - Check Usage

1. **Embeddings Layer**
   - `lib/embeddings/service.py` (278 LOC)
   - `lib/embeddings/models.py`
   - ❓ Used in production flow?

2. **Vector Database**
   - `lib/vector_db/faiss_db.py` (213 LOC)
   - `lib/vector_db/chroma_db.py` (252 LOC)
   - ❓ Used in production flow?

3. **Storage Layer**
   - `lib/storage/dataset_storage.py` (295 LOC)
   - `lib/storage/publication_storage.py` (242 LOC)
   - ❓ Used in production flow?

4. **Duplicate Clients?**
   - `lib/publications/clients/async_pubmed.py` (354 LOC)
   - `lib/publications/clients/pubmed.py` (398 LOC)
   - ❓ Which one is used?

5. **Download Manager vs Downloader**
   - `lib/fulltext/download_manager.py`
   - `lib/fulltext/pdf_downloader.py` (447 LOC)
   - ❓ Which one is active?

---

## Reorganization Recommendations

### Current Issues

1. **GEO files are in wrong conceptual layer**
   - Currently: `lib/geo/` (treated as "client adapter")
   - Should be: Recognized as PRIMARY search engine (Stage 5a)

2. **Full-text files scattered across 3 locations**
   - `lib/fulltext/` - Manager, downloader, parser
   - `lib/fulltext/sources/` - Sci-Hub, LibGen, Unpaywall
   - `lib/publications/clients/` - OA sources, institutional

3. **Publication clients serve dual purposes**
   - Search (Stage 5b)
   - Metadata fetch (Stage 7)
   - Not clear which role each file plays

### Proposed Structure

```
lib/
├── query/                      # Stage 3
│   ├── nlp/                   # NER, expansion
│   └── optimization/          # Analyzer, optimizer
│
├── search/                     # Stage 4
│   ├── orchestrator.py        # Coordination only
│   ├── config.py
│   └── models.py
│
├── search_engines/            # Stage 5
│   ├── geo/                   # Stage 5a: GEO search
│   │   ├── client.py
│   │   ├── query_builder.py
│   │   └── models.py
│   └── citations/             # Stage 5b: Citation search
│       ├── pubmed.py
│       ├── openalex.py
│       ├── scholar.py
│       └── semantic_scholar.py
│
├── enrichment/                # Stages 7-9
│   └── fulltext/
│       ├── manager.py         # Stage 7: URL orchestrator
│       ├── downloader.py      # Stage 8: PDF download
│       ├── parser.py          # Stage 9: Text extraction
│       └── sources/           # All 11 sources together
│           ├── free/          # PMC, DOAJ, Europe PMC
│           ├── aggregators/   # Unpaywall, BASE, CORE
│           ├── institutional/ # University access
│           ├── academic/      # OpenAlex, Semantic Scholar
│           └── fallback/      # Sci-Hub, LibGen
│
├── analysis/                  # Stage 11
│   └── ai/
│       ├── client.py
│       ├── prompts.py
│       └── models.py
│
└── infrastructure/            # Cross-cutting
    ├── cache/
    ├── storage/
    └── monitoring/
```

---

## Next Steps

1. **Verify file usage** - Check which files are actually imported in production
2. **Identify redundancies** - Find duplicate logic across files
3. **Consolidate scattered logic** - Bring related files together
4. **Archive unused files** - Move to extras/ if not used
5. **Reorganize by flow** - Match directory structure to user journey

**Ready to proceed with:**
- ✅ File usage analysis (grep all imports)
- ✅ Redundancy detection (compare similar files)
- ✅ Reorganization plan (move files to match flow)
