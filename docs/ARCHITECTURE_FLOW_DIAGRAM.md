# OmicsOracle Architecture - Complete Execution Stack

**Date:** October 16, 2025  
**Complete layer-wise data flow from frontend to external APIs**

---

## Layer-by-Layer Architecture

```mermaid
flowchart TB
    subgraph L0["🌐 LAYER 0: Frontend (User Interface)"]
        dashboard[dashboard_v2.html<br/>• Search input<br/>• Results display<br/>• Button clicks]
    end

    subgraph L1["⚡ LAYER 1: API Gateway (HTTP Interface)"]
        fastapi[main.py<br/>FastAPI Application]
        routes[routes/agents.py<br/>• /api/search<br/>• /api/datasets/{id}/discover<br/>• /api/enrich-fulltext]
    end

    subgraph L2["🧠 LAYER 2: Business Logic (Service Layer)"]
        search_svc[search_service.py<br/>SearchService<br/>• execute_search()]
        discover_svc[routes/agents.py<br/>• discover_citations()]
    end

    subgraph L3["🔄 LAYER 3: Orchestration (Pipeline Coordination)"]
        orchestrator[search_orchestration/<br/>orchestrator.py<br/>SearchOrchestrator<br/>• Parallel execution<br/>• Query analysis]
        geo_cache[storage/registry/<br/>geo_cache.py<br/>GEOCache<br/>• 2-tier caching<br/>• Auto-discovery]
    end

    subgraph L4["💾 LAYER 4: Cache & Storage (Hot/Warm Tier)"]
        redis[redis_cache.py<br/>RedisCache<br/>• Hot tier (7d TTL)<br/>• <1ms retrieval]
        unified_db[storage/unified_db.py<br/>UnifiedDatabase<br/>• SQLite/PostgreSQL<br/>• Warm tier<br/>• Permanent storage]
    end

    subgraph L5["🔍 LAYER 5: Data Discovery (Citation & Metadata)"]
        geo_client[search_engines/geo/<br/>client.py<br/>GEOClient<br/>• get_metadata()]
        citation_disc[citation_discovery/<br/>geo_discovery.py<br/>GEOCitationDiscovery<br/>• find_citing_papers()]
    end

    subgraph L6["🌍 LAYER 6: External API Clients (Third-Party)"]
        ncbi[NCBI API Clients]
        openalex[OpenAlex Client]
        pubmed[PubMed Client]
        semantic[Semantic Scholar]
        europepmc[Europe PMC]
    end

    subgraph L7["🗄️ LAYER 7: External Data Sources"]
        ncbi_api[(NCBI E-utilities<br/>GEO Database)]
        openalex_api[(OpenAlex API<br/>Citation Graph)]
        pubmed_api[(PubMed API<br/>Literature)]
        s2_api[(Semantic Scholar<br/>Citations)]
        pmc_api[(Europe PMC<br/>Full-text)]
    end

    %% Frontend → API Gateway
    dashboard -->|HTTP POST /api/search| fastapi
    dashboard -->|HTTP POST /api/datasets/{id}/discover| fastapi

    %% API Gateway → Business Logic
    fastapi --> routes
    routes -->|Search request| search_svc
    routes -->|Discovery request| discover_svc

    %% Business Logic → Orchestration
    search_svc -->|Orchestrate search| orchestrator
    search_svc -->|Get enriched metadata| geo_cache
    discover_svc -->|Trigger discovery| citation_disc

    %% Orchestration → Cache & Storage
    orchestrator -->|Check cache| redis
    orchestrator -->|Persist results| unified_db
    geo_cache -->|Check Redis| redis
    geo_cache -->|Query database| unified_db
    geo_cache -->|Auto-discover| geo_client
    geo_cache -->|Auto-discover| citation_disc

    %% Data Discovery → External Clients
    geo_client -->|Fetch metadata| ncbi
    citation_disc -->|Find citations| openalex
    citation_disc -->|Search papers| pubmed
    citation_disc -->|Get citations| semantic
    citation_disc -->|Full-text URLs| europepmc

    %% External Clients → External APIs
    ncbi -->|E-utilities| ncbi_api
    openalex -->|REST API| openalex_api
    pubmed -->|E-search/E-fetch| pubmed_api
    semantic -->|API| s2_api
    europepmc -->|REST API| pmc_api

    style L0 fill:#e1f5ff
    style L1 fill:#fff4e1
    style L2 fill:#ffe1f5
    style L3 fill:#e1ffe1
    style L4 fill:#fff0e1
    style L5 fill:#f0e1ff
    style L6 fill:#ffe1e1
    style L7 fill:#f5f5f5
```

---

## Detailed Layer Breakdown

### 🌐 **LAYER 0: Frontend (User Interface)**

**Single File:**
```
dashboard_v2.html (2,500+ lines)
├── HTML Structure
├── CSS Styling
└── JavaScript Functions:
    ├── performSearch()           → Calls /api/search
    ├── discoverCitationsForDataset() → Calls /api/datasets/{id}/discover
    ├── downloadPapersForDataset()    → Calls /api/enrich-fulltext
    └── displayResults()          → Renders data
```

**User Actions:**
1. Type query in search box
2. Click "Search" button
3. View results
4. Click "🔍 Discover Citations" (if citation_count=0)
5. Click "📥 Download Papers" (if citation_count>0)
6. Click "🤖 AI Analysis" (if PDFs exist)

---

### ⚡ **LAYER 1: API Gateway (HTTP Interface)**

**Files:**
```
omics_oracle_v2/api/
├── main.py                  → FastAPI app, CORS, middleware
└── routes/
    ├── agents.py            → Search & discovery endpoints
    ├── auth.py              → Authentication (JWT)
    ├── health.py            → Health checks
    └── websocket.py         → Real-time updates
```

**Endpoints Used:**
```python
POST /api/search
  ↓ Request: SearchRequest(search_terms, filters, max_results)
  ↓ Response: SearchResponse(datasets, publications, metadata)

POST /api/datasets/{geo_id}/discover-citations
  ↓ Request: geo_id (path parameter)
  ↓ Response: {citations_found, success}

POST /api/enrich-fulltext
  ↓ Request: List[DatasetResponse]
  ↓ Response: List[DatasetResponse] (enriched)
```

**Parallel Processing:**
```
┌─────────────────┐
│  FastAPI App    │
├─────────────────┤
│ • CORS          │ → Cross-origin requests
│ • Rate Limiting │ → Redis-based throttling
│ • Auth Middleware│ → JWT validation
│ • Logging       │ → Request tracking
└─────────────────┘
```

---

### 🧠 **LAYER 2: Business Logic (Service Layer)**

**Files:**
```
omics_oracle_v2/services/
└── search_service.py
    └── SearchService
        ├── execute_search()         → Main search logic
        ├── _build_dataset_responses() → Enrichment
        ├── _rank_datasets()          → Relevance scoring
        └── _build_query()            → Query construction

omics_oracle_v2/api/routes/
└── agents.py
    └── discover_citations()          → Citation discovery endpoint
```

**Responsibilities:**
- Input validation
- Business rule enforcement
- Data transformation
- Response formatting
- Error handling

**Parallel Operations:**
```
┌─────────────────────┬─────────────────────┐
│  Search Flow        │  Discovery Flow     │
├─────────────────────┼─────────────────────┤
│ 1. Validate request │ 1. Validate GEO ID  │
│ 2. Call orchestrator│ 2. Create metadata  │
│ 3. Enrich results   │ 3. Run discovery    │
│ 4. Format response  │ 4. Store in DB      │
└─────────────────────┴─────────────────────┘
```

---

### 🔄 **LAYER 3: Orchestration (Pipeline Coordination)**

**Files:**
```
omics_oracle_v2/lib/
├── search_orchestration/
│   └── orchestrator.py
│       └── SearchOrchestrator
│           ├── search()              → Main search method
│           ├── _detect_query_type()  → GEO ID vs keyword
│           ├── _search_geo()         → Parallel GEO search
│           └── _search_publications() → Parallel publication search
│
└── pipelines/storage/registry/
    └── geo_cache.py
        └── GEOCache
            ├── get()                 → 2-tier cache lookup
            ├── _auto_discover_and_populate() → NEW! Auto-discovery
            └── update()              → Write-through caching
```

**Orchestrator Flow:**
```
SearchOrchestrator.search()
    ├── Query Analysis
    │   ├── Detect type (GEO ID / keyword / hybrid)
    │   ├── NER extraction (diseases, genes)
    │   └── Query optimization (synonyms, expansion)
    │
    ├── Parallel Execution
    │   ├── Thread 1: GEO search
    │   ├── Thread 2: PubMed search
    │   └── Thread 3: OpenAlex search
    │
    └── Result Merging
        ├── Deduplication
        ├── Ranking
        └── Cache storage
```

**GEOCache Auto-Discovery:**
```
GEOCache.get(geo_id)
    ├── Check Redis → HIT/MISS
    ├── Check UnifiedDB → HIT/MISS
    │
    └── If MISS:
        └── _auto_discover_and_populate()
            ├── GEOClient.get_metadata()
            ├── GEOCitationDiscovery.find_citing_papers()
            ├── UnifiedDB.insert_geo_dataset()
            ├── UnifiedDB.insert_universal_identifier()
            └── Return enriched data
```

---

### 💾 **LAYER 4: Cache & Storage (Hot/Warm Tier)**

**Files & Architecture:**

```
┌──────────────────────────────────────────────────────┐
│                  2-TIER CACHING                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  HOT TIER (Redis)                          │    │
│  │  omics_oracle_v2/cache/redis_cache.py     │    │
│  ├────────────────────────────────────────────┤    │
│  │  • In-memory key-value store               │    │
│  │  • TTL: 7 days                             │    │
│  │  • Latency: <1ms                           │    │
│  │  • Volatile (data can be lost)             │    │
│  │                                             │    │
│  │  Keys:                                      │    │
│  │  ├─ search:<query_hash> → SearchResult    │    │
│  │  ├─ geo_metadata:<geo_id> → GEO metadata  │    │
│  │  └─ geo_complete:<geo_id> → Full data     │    │
│  └────────────────────────────────────────────┘    │
│                       ↓                             │
│                  Cache Miss                         │
│                       ↓                             │
│  ┌────────────────────────────────────────────┐    │
│  │  WARM TIER (UnifiedDatabase)               │    │
│  │  omics_oracle_v2/lib/pipelines/storage/   │    │
│  │  unified_db.py                             │    │
│  ├────────────────────────────────────────────┤    │
│  │  • SQLite/PostgreSQL                       │    │
│  │  • TTL: Permanent                          │    │
│  │  • Latency: ~50ms                          │    │
│  │  • Durable (ACID transactions)             │    │
│  │                                             │    │
│  │  Tables:                                    │    │
│  │  ├─ universal_identifiers                  │    │
│  │  │   (geo_id, pmid, doi, title, authors)  │    │
│  │  ├─ geo_datasets                           │    │
│  │  │   (geo_id, title, organism, stats)     │    │
│  │  ├─ url_discovery                          │    │
│  │  ├─ pdf_acquisition                        │    │
│  │  ├─ content_extraction                     │    │
│  │  └─ processing_logs                        │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Data Models:**
```
omics_oracle_v2/lib/pipelines/storage/
└── models.py
    ├── UniversalIdentifier    → Links GEO ↔ Publications
    ├── GEODataset             → GEO metadata + stats
    ├── URLDiscovery           → PDF URLs per paper
    ├── PDFAcquisition         → Download status
    ├── ContentExtraction      → Parsed text
    └── EnrichedContent        → AI analysis
```

---

### 🔍 **LAYER 5: Data Discovery (Citation & Metadata)**

**Files & Parallel Operations:**

```
┌───────────────────────────────────────────────────────┐
│              DATA DISCOVERY LAYER                     │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────────┐  ┌─────────────────────┐  │
│  │  GEO Metadata        │  │  Citation Discovery │  │
│  │  Fetching            │  │  (Multi-source)     │  │
│  ├──────────────────────┤  ├─────────────────────┤  │
│  │ search_engines/geo/  │  │ citation_discovery/ │  │
│  │ client.py            │  │ geo_discovery.py    │  │
│  │                      │  │                     │  │
│  │ GEOClient            │  │ GEOCitationDiscovery│  │
│  │ ├─ get_metadata()    │  │ ├─ find_citing_papers()│
│  │ ├─ search()          │  │ │                   │  │
│  │ └─ batch_get()       │  │ └─ Two Strategies: │  │
│  │                      │  │   ├─ Strategy A:   │  │
│  │ Returns:             │  │   │  Citation-based│  │
│  │ GEOSeriesMetadata    │  │   │  (OpenAlex,    │  │
│  │ ├─ geo_id            │  │   │   S2, PMC)     │  │
│  │ ├─ title             │  │   └─ Strategy B:   │  │
│  │ ├─ summary           │  │      Mention-based │  │
│  │ ├─ organism          │  │      (PubMed)      │  │
│  │ ├─ platforms         │  │                     │  │
│  │ ├─ sample_count      │  │ Returns:            │  │
│  │ └─ pubmed_ids        │  │ CitationDiscoveryResult│
│  │                      │  │ ├─ citing_papers[]  │  │
│  │                      │  │ ├─ original_pmid    │  │
│  │                      │  │ └─ sources_used     │  │
│  └──────────────────────┘  └─────────────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**GEOClient Methods:**
```python
# omics_oracle_v2/lib/search_engines/geo/client.py

class GEOClient:
    async def search(query: str) -> SearchResult
    async def get_metadata(geo_id: str) -> GEOSeriesMetadata
    async def batch_get_metadata(geo_ids: List[str]) -> Dict[str, GEOSeriesMetadata]
    async def _get_sra_metadata(geo_id: str) -> SRAInfo
```

**Citation Discovery Methods:**
```python
# omics_oracle_v2/lib/pipelines/citation_discovery/geo_discovery.py

class GEOCitationDiscovery:
    def find_citing_papers(metadata: GEOSeriesMetadata, max_results: int) -> CitationDiscoveryResult
    def _find_via_citation(pmid: str) -> List[Publication]
    def _find_via_geo_mention(geo_id: str) -> List[Publication]
```

---

### 🌍 **LAYER 6: External API Clients (Third-Party Integrations)**

**Files & Client Implementations:**

```
omics_oracle_v2/lib/pipelines/citation_discovery/clients/
├── ncbi.py
│   └── NCBIClient
│       ├── esearch()           → Search NCBI databases
│       ├── efetch()            → Fetch records
│       └── esummary()          → Get summaries
│
├── openalex.py
│   └── OpenAlexClient
│       ├── get_work()          → Get paper by DOI/PMID
│       ├── get_citations()     → Find citing papers
│       └── search_works()      → Keyword search
│
├── pubmed.py
│   └── PubMedClient
│       ├── search()            → Search PubMed
│       ├── fetch_details()     → Get metadata
│       └── get_pmids_by_geo()  → Find GEO mentions
│
├── semantic_scholar.py
│   └── SemanticScholarClient
│       ├── get_paper()         → Get paper info
│       └── get_citations()     → Get citing papers
│
└── europepmc.py
    └── EuropePMCClient
        ├── search()            → Search Europe PMC
        ├── get_citations()     → Get citations
        └── get_fulltext_urls() → Get PDF URLs
```

**Parallel Citation Discovery:**
```
┌────────────────────────────────────────────────────┐
│  Citation Discovery Parallel Execution             │
├────────────────────────────────────────────────────┤
│                                                    │
│  Thread 1: OpenAlex        Thread 2: Semantic S.  │
│  ├─ Query by PMID          ├─ Query by PMID       │
│  ├─ Get citing papers      ├─ Get citing papers   │
│  └─ Return ~50 results     └─ Return ~30 results  │
│          ↓                          ↓              │
│          └──────────┬───────────────┘              │
│                     ↓                              │
│  Thread 3: Europe PMC      Thread 4: PubMed       │
│  ├─ Query by PMID          ├─ Search "GSE189158"  │
│  ├─ Get citations          ├─ Find mentions       │
│  └─ Return ~20 results     └─ Return ~10 results  │
│          ↓                          ↓              │
│          └──────────┬───────────────┘              │
│                     ↓                              │
│            Merge & Deduplicate                     │
│            ├─ By PMID                              │
│            ├─ By DOI                               │
│            └─ Return unique papers                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Rate Limiting & Retry:**
```
┌─────────────────────────────────────┐
│  Client Resilience Features         │
├─────────────────────────────────────┤
│  • Rate limiting (per-API)          │
│    ├─ NCBI: 3 req/s (no key)        │
│    ├─ OpenAlex: 10 req/s (polite)   │
│    ├─ PubMed: 3 req/s               │
│    └─ Semantic Scholar: 1 req/s     │
│                                     │
│  • Exponential backoff              │
│    └─ Retries: 1s, 2s, 4s, 8s       │
│                                     │
│  • Timeout handling                 │
│    └─ Default: 30s per request      │
│                                     │
│  • Connection pooling               │
│    └─ aiohttp sessions              │
└─────────────────────────────────────┘
```

---

### 🗄️ **LAYER 7: External Data Sources (APIs)**

**API Endpoints & Protocols:**

```
┌──────────────────────────────────────────────────────┐
│                EXTERNAL APIS                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🧬 NCBI E-utilities                                 │
│  ├─ URL: https://eutils.ncbi.nlm.nih.gov/entrez/   │
│  ├─ Protocol: REST (XML responses)                  │
│  ├─ Databases:                                       │
│  │  ├─ gds (GEO DataSets)                           │
│  │  ├─ pubmed (Literature)                          │
│  │  └─ sra (Sequence Read Archive)                  │
│  ├─ Operations:                                      │
│  │  ├─ esearch → Search for IDs                     │
│  │  ├─ efetch → Fetch full records                  │
│  │  └─ esummary → Get summaries                     │
│  └─ Rate Limit: 3 req/s (10 req/s with API key)    │
│                                                      │
│  📚 OpenAlex                                         │
│  ├─ URL: https://api.openalex.org/                  │
│  ├─ Protocol: REST (JSON responses)                 │
│  ├─ Features:                                        │
│  │  ├─ Citation graph (200M+ papers)                │
│  │  ├─ Paper metadata (DOI, authors, etc.)          │
│  │  └─ Citation counts & relationships              │
│  ├─ Operations:                                      │
│  │  ├─ GET /works/{id} → Get paper                  │
│  │  └─ GET /works?filter=cites:{id} → Citations     │
│  └─ Rate Limit: 10 req/s (polite pool)             │
│                                                      │
│  🔬 PubMed (NCBI)                                    │
│  ├─ URL: https://eutils.ncbi.nlm.nih.gov/          │
│  ├─ Protocol: REST (XML responses)                  │
│  ├─ Features:                                        │
│  │  ├─ 35M+ biomedical citations                    │
│  │  ├─ MeSH term indexing                           │
│  │  └─ Full abstracts                               │
│  ├─ Operations:                                      │
│  │  ├─ esearch → Query literature                   │
│  │  └─ efetch → Get paper details                   │
│  └─ Rate Limit: 3 req/s (10 req/s with API key)    │
│                                                      │
│  🎓 Semantic Scholar                                 │
│  ├─ URL: https://api.semanticscholar.org/          │
│  ├─ Protocol: REST (JSON responses)                 │
│  ├─ Features:                                        │
│  │  ├─ 200M+ papers with AI-powered features        │
│  │  ├─ Citation context extraction                  │
│  │  └─ Influential citations ranking                │
│  ├─ Operations:                                      │
│  │  ├─ GET /paper/{id} → Get paper                  │
│  │  └─ GET /paper/{id}/citations → Get citations    │
│  └─ Rate Limit: 1 req/s (5 req/s with API key)     │
│                                                      │
│  📖 Europe PMC                                       │
│  ├─ URL: https://www.ebi.ac.uk/europepmc/          │
│  ├─ Protocol: REST (JSON/XML responses)             │
│  ├─ Features:                                        │
│  │  ├─ 40M+ life science publications               │
│  │  ├─ Full-text articles                           │
│  │  └─ Citation links                               │
│  ├─ Operations:                                      │
│  │  ├─ GET /search → Search literature              │
│  │  └─ GET /citations/{id} → Get citations          │
│  └─ Rate Limit: No official limit (be polite)      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Data Flow Example:**
```
User searches "GSE189158"
    ↓
NCBI GEO → Returns:
  {
    geo_id: "GSE189158",
    title: "NOMe-HiC: joint profiling...",
    pubmed_ids: ["36927507"],
    organism: "Homo sapiens"
  }
    ↓
OpenAlex → Query paper PMID:36927507
  Returns: 45 citing papers
    ↓
Semantic Scholar → Query paper PMID:36927507
  Returns: 38 citing papers
    ↓
Europe PMC → Query paper PMID:36927507
  Returns: 12 citing papers
    ↓
PubMed → Search "GSE189158"
  Returns: 5 papers mentioning GEO ID
    ↓
Merge & Deduplicate → 67 unique citations
    ↓
Store in UnifiedDB
```

---

## Complete Data Flow (Search Request)

### Timeline Visualization

```
TIME →
│
├─ T0: User clicks "Search"
│   └─ dashboard_v2.html → performSearch()
│
├─ T+10ms: HTTP request sent
│   └─ POST /api/search
│
├─ T+15ms: API Gateway receives
│   ├─ main.py → FastAPI routing
│   └─ routes/agents.py → execute_search endpoint
│
├─ T+20ms: Service layer processing
│   ├─ search_service.py → SearchService.execute_search()
│   └─ Build query, validate inputs
│
├─ T+50ms: Orchestration begins
│   ├─ orchestrator.py → SearchOrchestrator.search()
│   ├─ Query analysis (NER, type detection)
│   └─ Launch parallel threads:
│       ├─ Thread 1: GEO search
│       ├─ Thread 2: PubMed search
│       └─ Thread 3: OpenAlex search
│
├─ T+100ms: Cache check
│   ├─ redis_cache.py → Check Redis
│   └─ Cache HIT → Return immediately (ends at T+120ms)
│   └─ Cache MISS → Continue to external APIs
│
├─ T+500ms: External API calls (parallel)
│   ├─ NCBI → esearch GEO database
│   ├─ PubMed → esearch publications
│   └─ OpenAlex → search works
│
├─ T+2000ms: Results received
│   ├─ GEO: 50 datasets
│   ├─ PubMed: 100 papers
│   └─ OpenAlex: 75 papers
│
├─ T+2100ms: Enrichment begins
│   ├─ search_service.py → _build_dataset_responses()
│   └─ For each dataset:
│       ├─ geo_cache.get(geo_id)
│       ├─ Check Redis → MISS
│       ├─ Check UnifiedDB → MISS
│       └─ AUTO-DISCOVERY TRIGGERED:
│           ├─ T+2200ms: GEOClient.get_metadata()
│           ├─ T+5000ms: Metadata received
│           ├─ T+5100ms: GEOCitationDiscovery.find_citing_papers()
│           │   ├─ OpenAlex → 45 citations
│           │   ├─ Semantic Scholar → 38 citations
│           │   ├─ Europe PMC → 12 citations
│           │   └─ PubMed → 5 mentions
│           ├─ T+28000ms: All citations found (67 unique)
│           ├─ T+28100ms: Store in UnifiedDB
│           └─ T+28200ms: Return enriched data
│
├─ T+28300ms: Response formatting
│   ├─ search_service.py → Build SearchResponse
│   └─ Include: datasets, publications, metadata
│
├─ T+28350ms: HTTP response sent
│   └─ JSON payload (gzipped)
│
└─ T+28400ms: Frontend receives
    ├─ dashboard_v2.html → displayResults()
    └─ Render:
        ├─ Dataset cards with citation counts
        ├─ Download buttons (if citations > 0)
        └─ AI Analysis buttons (if PDFs exist)
```

---

## Parallel Processing Architecture

```
┌────────────────────────────────────────────────────┐
│         PARALLEL EXECUTION MODEL                   │
├────────────────────────────────────────────────────┤
│                                                    │
│  Layer 3: Orchestration (SearchOrchestrator)      │
│  ┌──────────────────────────────────────────────┐ │
│  │  Main Thread                                  │ │
│  │  ├─ Analyze query                            │ │
│  │  ├─ Launch workers:                          │ │
│  │  │   ├─ asyncio.create_task(search_geo)     │ │
│  │  │   ├─ asyncio.create_task(search_pubmed)  │ │
│  │  │   └─ asyncio.create_task(search_openalex)│ │
│  │  ├─ await asyncio.gather(workers)           │ │
│  │  └─ Merge results                            │ │
│  └──────────────────────────────────────────────┘ │
│           ↓              ↓              ↓          │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐│
│  │ Worker 1    │  │ Worker 2    │  │ Worker 3   ││
│  │ GEO Search  │  │ PubMed      │  │ OpenAlex   ││
│  │             │  │ Search      │  │ Search     ││
│  │ ~1.5s       │  │ ~2.0s       │  │ ~1.8s      ││
│  └─────────────┘  └─────────────┘  └────────────┘│
│                                                    │
│  Layer 5: Citation Discovery (GEOCitationDiscovery)│
│  ┌──────────────────────────────────────────────┐ │
│  │  Main Thread                                  │ │
│  │  ├─ Launch citation workers:                 │ │
│  │  │   ├─ ThreadPoolExecutor.submit(openalex) │ │
│  │  │   ├─ ThreadPoolExecutor.submit(s2)       │ │
│  │  │   ├─ ThreadPoolExecutor.submit(europepmc)│ │
│  │  │   └─ ThreadPoolExecutor.submit(pubmed)   │ │
│  │  ├─ futures.as_completed(workers)           │ │
│  │  └─ Deduplicate & merge                      │ │
│  └──────────────────────────────────────────────┘ │
│           ↓              ↓              ↓          │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐│
│  │ Thread 1    │  │ Thread 2    │  │ Thread 3   ││
│  │ OpenAlex    │  │ Semantic S. │  │ Europe PMC ││
│  │ 45 citations│  │ 38 citations│  │ 12 citations││
│  │ ~8s         │  │ ~12s        │  │ ~6s        ││
│  └─────────────┘  └─────────────┘  └────────────┘│
│                                                    │
└────────────────────────────────────────────────────┘
```

**Performance Gains:**
- Sequential execution: 1.5s + 2.0s + 1.8s = **5.3 seconds**
- Parallel execution: max(1.5s, 2.0s, 1.8s) = **2.0 seconds**
- **Speedup: 2.65x**

---

## Error Handling Flow

```
┌────────────────────────────────────────────────────┐
│           ERROR PROPAGATION CHAIN                  │
├────────────────────────────────────────────────────┤
│                                                    │
│  Layer 7: External API                            │
│  ├─ Network timeout (30s)                         │
│  ├─ Rate limit (429 status)                       │
│  └─ Service unavailable (503)                     │
│           ↓                                        │
│  Layer 6: API Client                              │
│  ├─ Catch exception                               │
│  ├─ Log error with context                        │
│  ├─ Retry with backoff (3 attempts)              │
│  └─ If all fail → Return empty list              │
│           ↓                                        │
│  Layer 5: Citation Discovery                      │
│  ├─ Merge results from successful sources         │
│  ├─ Log warning about failed sources              │
│  └─ Continue with partial results                 │
│           ↓                                        │
│  Layer 4: Database                                │
│  ├─ Transaction rollback on error                 │
│  ├─ Preserve existing data                        │
│  └─ Log error to processing_logs table            │
│           ↓                                        │
│  Layer 3: Orchestrator                            │
│  ├─ Catch worker exceptions                       │
│  ├─ Return partial results                        │
│  └─ Set error flags in response                   │
│           ↓                                        │
│  Layer 2: Service                                 │
│  ├─ Format error for user display                 │
│  ├─ Include search_logs with error details        │
│  └─ Return 200 OK with partial data               │
│           ↓                                        │
│  Layer 1: API Gateway                             │
│  ├─ Log request/response                          │
│  ├─ Track metrics (failed searches)               │
│  └─ Return JSON response                          │
│           ↓                                        │
│  Layer 0: Frontend                                │
│  └─ Display:                                       │
│      ├─ Available results                         │
│      ├─ Warning about missing data                │
│      └─ Retry button                              │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Graceful Degradation:**
- ✅ One API fails → Use other sources
- ✅ Cache miss → Fetch from external APIs
- ✅ Database error → Return cached data
- ✅ All sources fail → Return empty results + error message

---

## Key Integration Points

### 1. **Frontend ↔ Backend**
```
dashboard_v2.html (JavaScript)
    ↓ HTTP POST
routes/agents.py (FastAPI)
    ↓ Pydantic models
SearchRequest → SearchResponse
```

### 2. **Service ↔ Orchestrator**
```
search_service.py
    ↓ async call
orchestrator.py
    ↓ SearchResult
search_service.py (enrichment)
```

### 3. **Cache ↔ Database**
```
redis_cache.py (hot tier)
    ↓ Cache miss
unified_db.py (warm tier)
    ↓ Write-through
redis_cache.py (promotion)
```

### 4. **Discovery ↔ External APIs**
```
geo_discovery.py
    ↓ Parallel threads
[openalex, semantic_scholar, europepmc, pubmed]
    ↓ HTTP requests
External APIs (REST/XML)
```

### 5. **Auto-Discovery Trigger**
```
geo_cache.get(geo_id)
    ↓ Database miss
_auto_discover_and_populate()
    ↓ Parallel execution
[GEOClient, GEOCitationDiscovery]
    ↓ Store results
unified_db.insert_*()
```

---

## Performance Metrics by Layer

```
┌─────────┬──────────────────┬─────────┬──────────┐
│ Layer   │ Component        │ Latency │ Caching  │
├─────────┼──────────────────┼─────────┼──────────┤
│ L0      │ Frontend render  │ 50ms    │ Browser  │
│ L1      │ API Gateway      │ 5ms     │ None     │
│ L2      │ Service layer    │ 10ms    │ None     │
│ L3      │ Orchestrator     │ 20ms    │ None     │
│ L4 (Hot)│ Redis cache      │ 0.2ms   │ 7d TTL   │
│ L4 (Warm)│ UnifiedDB       │ 50ms    │ Permanent│
│ L5      │ GEOClient        │ 1.5s    │ None     │
│ L5      │ Citation Disc.   │ 8-25s   │ 7d cache │
│ L6      │ API Clients      │ 2-8s    │ None     │
│ L7      │ External APIs    │ 1-10s   │ N/A      │
└─────────┴──────────────────┴─────────┴──────────┘

Total Latency (worst case, no cache):
  L0-L7: ~30 seconds (with auto-discovery)
  L0-L4 (cached): <100ms
```

---

## Summary

**Architecture Highlights:**
1. **7-layer stack** from frontend to external APIs
2. **2-tier caching** (Redis hot + UnifiedDB warm) for <1ms responses
3. **Parallel execution** at multiple layers (2.65x speedup)
4. **Auto-discovery** seamlessly integrated in cache layer
5. **Graceful degradation** with comprehensive error handling
6. **Zero frontend changes** needed - enrichment is transparent

**Data Flow:**
- **Fast path (cached):** 50-100ms total
- **Slow path (discovery):** 5-30 seconds first time
- **Subsequent requests:** <1ms (Redis cache hit)

**Key Innovation:**
Auto-discovery in `GEOCache.get()` eliminates manual button clicks - citations populate automatically on first search!

