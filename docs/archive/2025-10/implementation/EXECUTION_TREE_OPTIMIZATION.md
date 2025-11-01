# OmicsOracle Complete Execution Tree - DFS/BFS Analysis

**Date:** October 16, 2025  
**Purpose:** Depth-First tracing and Breadth-First visualization for optimization

---

## Tree Structure - Complete Execution Graph

```
ROOT: dashboard_v2.html (User Action: Search)
│
├─[USER INTERACTION TREE]
│   │
│   ├─ performSearch()
│   │   ├─ Validate input
│   │   ├─ Build request payload
│   │   ├─ HTTP POST /api/search
│   │   └─ Wait for response
│   │
│   ├─ discoverCitationsForDataset(index)
│   │   ├─ Get dataset from results[index]
│   │   ├─ HTTP POST /api/datasets/{geo_id}/discover-citations
│   │   └─ Refresh search results
│   │
│   └─ downloadPapersForDataset(index)
│       ├─ Get dataset from results[index]
│       ├─ HTTP POST /api/enrich-fulltext
│       └─ Update UI with PDFs
│
├─[API GATEWAY TREE - POST /api/search]
│   │
│   ├─ main.py
│   │   ├─ FastAPI app initialization
│   │   ├─ Middleware chain
│   │   │   ├─ CORS middleware
│   │   │   ├─ Rate limit middleware
│   │   │   ├─ Request logging middleware
│   │   │   └─ Error handling middleware
│   │   │
│   │   └─ Route to agents_router
│   │
│   └─ routes/agents.py::execute_search()
│       ├─ Parse SearchRequest (Pydantic)
│       ├─ Call SearchService.execute_search()
│       ├─ Format SearchResponse
│       └─ Return HTTP 200 + JSON
│
├─[SERVICE LAYER TREE]
│   │
│   └─ services/search_service.py::SearchService
│       │
│       ├─ execute_search(request)
│       │   │
│       │   ├─ _build_search_config()
│       │   │   └─ Return OrchestratorConfig
│       │   │
│       │   ├─ _build_query()
│       │   │   ├─ Parse search_terms
│       │   │   ├─ Apply filters (organism, study_type)
│       │   │   └─ Return optimized query string
│       │   │
│       │   ├─ SearchOrchestrator.search()  [ASYNC CALL]
│       │   │   └─ [BRANCHES TO ORCHESTRATOR TREE]
│       │   │
│       │   ├─ _rank_datasets()
│       │   │   ├─ Calculate relevance_score
│       │   │   ├─ Generate match_reasons
│       │   │   └─ Sort by score
│       │   │
│       │   └─ _build_dataset_responses()  [ASYNC CALL]
│       │       └─ [BRANCHES TO ENRICHMENT TREE]
│       │
│       └─ Properties
│           └─ geo_cache (lazy-loaded)
│               ├─ Import UnifiedDatabase
│               ├─ Import create_geo_cache
│               └─ Initialize GEOCache instance
│
├─[ORCHESTRATOR TREE - Parallel Execution]
│   │
│   └─ search_orchestration/orchestrator.py::SearchOrchestrator
│       │
│       └─ search(query, max_geo_results, max_publication_results)
│           │
│           ├─ _detect_query_type(query)
│           │   ├─ Check if GEO ID pattern (GSE\d+)
│           │   ├─ Check if PMID pattern
│           │   └─ Default to keyword search
│           │
│           ├─ _optimize_query(query)  [IF semantic=True]
│           │   ├─ QueryOptimizer.optimize()
│           │   │   ├─ NER extraction (BiomedicalNER)
│           │   │   │   ├─ Extract diseases
│           │   │   │   ├─ Extract genes
│           │   │   │   └─ Extract organisms
│           │   │   │
│           │   │   ├─ SynonymExpander.expand()
│           │   │   │   ├─ Query SapBERT embeddings
│           │   │   │   └─ Add semantic synonyms
│           │   │   │
│           │   │   └─ Return optimized query
│           │   │
│           │   └─ Update query string
│           │
│           ├─ Cache Check
│           │   ├─ RedisCache.get_search_result(query_hash)
│           │   ├─ IF HIT: Return cached SearchResult (ENDS HERE)
│           │   └─ IF MISS: Continue to parallel search
│           │
│           ├─ PARALLEL SEARCH (asyncio.gather)
│           │   │
│           │   ├─[BRANCH 1: GEO Search Thread]
│           │   │   └─ _search_geo(query)
│           │   │       ├─ GEOClient.search(query)
│           │   │       │   ├─ NCBIClient.esearch(db="gds", term=query)
│           │   │       │   │   ├─ HTTP GET to eutils.ncbi.nlm.nih.gov
│           │   │       │   │   ├─ Parse XML response
│           │   │       │   │   └─ Return GEO IDs list
│           │   │       │   │
│           │   │       │   ├─ GEOClient.batch_get_metadata(geo_ids)
│           │   │       │   │   ├─ For each geo_id:
│           │   │       │   │   │   ├─ NCBIClient.esummary(db="gds", id=geo_id)
│           │   │       │   │   │   ├─ Parse GEO metadata
│           │   │       │   │   │   └─ Create GEOSeriesMetadata object
│           │   │       │   │   └─ Return metadata dict
│           │   │       │   │
│           │   │       │   └─ Return SearchResult
│           │   │       │
│           │   │       └─ Store in UnifiedDB
│           │   │           └─ PipelineCoordinator.save_search_result()
│           │   │
│           │   ├─[BRANCH 2: PubMed Search Thread]
│           │   │   └─ _search_publications_pubmed(query)
│           │   │       └─ PubMedClient.search(query)
│           │   │           ├─ NCBIClient.esearch(db="pubmed", term=query)
│           │   │           │   ├─ HTTP GET to eutils.ncbi.nlm.nih.gov
│           │   │           │   └─ Return PMID list
│           │   │           │
│           │   │           ├─ PubMedClient.fetch_details(pmids)
│           │   │           │   ├─ NCBIClient.efetch(db="pubmed", ids=pmids)
│           │   │           │   ├─ Parse XML for each paper
│           │   │           │   └─ Create Publication objects
│           │   │           │
│           │   │           └─ Return List[Publication]
│           │   │
│           │   └─[BRANCH 3: OpenAlex Search Thread]
│           │       └─ _search_publications_openalex(query)
│           │           └─ OpenAlexClient.search_works(query)
│           │               ├─ HTTP GET to api.openalex.org/works
│           │               ├─ Parse JSON response
│           │               └─ Return List[Publication]
│           │
│           ├─ Merge Results
│           │   ├─ Combine geo_datasets
│           │   ├─ Deduplicate publications (by PMID/DOI)
│           │   └─ Create unified SearchResult
│           │
│           ├─ Cache Result
│           │   └─ RedisCache.set_search_result(query_hash, result, ttl=3600)
│           │
│           └─ Return SearchResult
│
├─[ENRICHMENT TREE - Dataset Response Building]
│   │
│   └─ services/search_service.py::_build_dataset_responses()
│       │
│       └─ For each ranked_dataset:
│           │
│           ├─ geo_cache.get(geo_id)  [ASYNC CALL]
│           │   └─ [BRANCHES TO GEOCACHE TREE]
│           │
│           ├─ Extract metrics from geo_data
│           │   ├─ papers = geo_data["papers"]["original"]
│           │   ├─ citation_count = len(papers)
│           │   ├─ pdf_count = count(download_history=="downloaded")
│           │   ├─ processed_count = count(extraction != None)
│           │   └─ completion_rate = (pdf_count / citation_count) * 100
│           │
│           └─ Create DatasetResponse
│               ├─ geo_id
│               ├─ title, summary, organism
│               ├─ relevance_score, match_reasons
│               ├─ citation_count  [ENRICHED FROM DB]
│               ├─ pdf_count       [ENRICHED FROM DB]
│               └─ completion_rate [ENRICHED FROM DB]
│
├─[GEOCACHE TREE - 2-Tier Cache with Auto-Discovery]
│   │
│   └─ storage/registry/geo_cache.py::GEOCache
│       │
│       └─ get(geo_id)  [ASYNC METHOD]
│           │
│           ├─[TIER 1: Redis Hot Cache]
│           │   ├─ RedisCache.get_geo_metadata(geo_id)
│           │   │   ├─ redis.get(f"geo_complete:{geo_id}")
│           │   │   └─ IF HIT: Return data (ENDS HERE - 0.2ms)
│           │   │
│           │   └─ Check memory_fallback dict
│           │       └─ IF HIT: Return data (ENDS HERE - <0.1ms)
│           │
│           ├─[TIER 2: UnifiedDB Warm Cache]
│           │   ├─ UnifiedDatabase.get_complete_geo_data(geo_id)
│           │   │   ├─ Query geo_datasets table
│           │   │   ├─ Query universal_identifiers (JOIN)
│           │   │   ├─ Query url_discovery (LEFT JOIN)
│           │   │   ├─ Query pdf_acquisition (LEFT JOIN)
│           │   │   ├─ Query content_extraction (LEFT JOIN)
│           │   │   │
│           │   │   └─ Build response dict:
│           │   │       ├─ geo: {metadata}
│           │   │       └─ papers: {original: [], citing: []}
│           │   │
│           │   ├─ IF HIT: 
│           │   │   ├─ Promote to Redis (_promote_to_hot_tier)
│           │   │   └─ Return data (ENDS HERE - 50ms)
│           │   │
│           │   └─ IF MISS: Continue to auto-discovery
│           │
│           └─[TIER 3: Auto-Discovery (NEW!)]
│               └─ _auto_discover_and_populate(geo_id)  [ASYNC METHOD]
│                   └─ [BRANCHES TO AUTO-DISCOVERY TREE]
│
├─[AUTO-DISCOVERY TREE - Citation Discovery Pipeline]
│   │
│   └─ storage/registry/geo_cache.py::_auto_discover_and_populate()
│       │
│       ├─[STEP 1: Fetch GEO Metadata]
│       │   └─ GEOClient.get_metadata(geo_id)
│       │       ├─ NCBIClient.esummary(db="gds", id=geo_id)
│       │       │   ├─ HTTP GET to eutils.ncbi.nlm.nih.gov
│       │       │   ├─ Parse XML response
│       │       │   └─ Extract: title, summary, organism, platforms, pubmed_ids
│       │       │
│       │       └─ Return GEOSeriesMetadata
│       │           ├─ geo_id: "GSE189158"
│       │           ├─ title: "NOMe-HiC: joint profiling..."
│       │           ├─ organism: "Homo sapiens"
│       │           ├─ pubmed_ids: ["36927507"]
│       │           └─ sample_count, platforms, etc.
│       │
│       ├─[STEP 2: Citation Discovery]
│       │   └─ GEOCitationDiscovery.find_citing_papers(metadata, max_results=100)
│       │       └─ [BRANCHES TO CITATION DISCOVERY TREE]
│       │
│       ├─[STEP 3: Store in Database]
│       │   │
│       │   ├─ Store GEO Dataset
│       │   │   └─ UnifiedDatabase.insert_geo_dataset(GEODataset)
│       │   │       ├─ INSERT INTO geo_datasets
│       │   │       └─ ON CONFLICT UPDATE (upsert)
│       │   │
│       │   └─ Store Citations (for each paper)
│       │       └─ UnifiedDatabase.insert_universal_identifier(UniversalIdentifier)
│       │           ├─ INSERT INTO universal_identifiers
│       │           │   (geo_id, pmid, doi, title, authors, journal, pub_date)
│       │           └─ ON CONFLICT UPDATE (upsert)
│       │
│       ├─[STEP 4: Retrieve Complete Data]
│       │   └─ UnifiedDatabase.get_complete_geo_data(geo_id)
│       │       └─ Return enriched data with citations
│       │
│       └─ Return geo_data (or None if failed)
│
├─[CITATION DISCOVERY TREE - Multi-Source Parallel Discovery]
│   │
│   └─ citation_discovery/geo_discovery.py::GEOCitationDiscovery
│       │
│       └─ find_citing_papers(geo_metadata, max_results)
│           │
│           ├─ Extract original PMID
│           │   └─ original_pmid = geo_metadata.pubmed_ids[0]
│           │
│           ├─[STRATEGY A: Citation-Based Discovery]
│           │   └─ _find_via_citation(original_pmid)
│           │       │
│           │       ├─ Check Cache
│           │       │   └─ DiscoveryCache.get(f"citation_{pmid}")
│           │       │       └─ IF HIT: Return cached (ENDS HERE)
│           │       │
│           │       └─ PARALLEL CITATION SOURCES (ThreadPoolExecutor)
│           │           │
│           │           ├─[THREAD 1: OpenAlex]
│           │           │   └─ fetch_openalex()
│           │           │       ├─ OpenAlexClient.get_work(f"pmid:{pmid}")
│           │           │       │   ├─ HTTP GET /works/pmid:{pmid}
│           │           │       │   └─ Get work_id
│           │           │       │
│           │           │       ├─ OpenAlexClient.get_citations(work_id)
│           │           │       │   ├─ HTTP GET /works?filter=cites:{work_id}
│           │           │       │   ├─ Parse JSON (up to 50 results)
│           │           │       │   └─ Extract: pmid, doi, title, authors, etc.
│           │           │       │
│           │           │       └─ Return List[Publication]
│           │           │
│           │           ├─[THREAD 2: Semantic Scholar]
│           │           │   └─ fetch_semantic_scholar()
│           │           │       ├─ SemanticScholarClient.get_paper(f"PMID:{pmid}")
│           │           │       │   ├─ HTTP GET /paper/PMID:{pmid}
│           │           │       │   └─ Get paper_id
│           │           │       │
│           │           │       ├─ SemanticScholarClient.get_citations(paper_id)
│           │           │       │   ├─ HTTP GET /paper/{paper_id}/citations
│           │           │       │   ├─ Parse JSON (up to 100 results)
│           │           │       │   └─ Extract metadata
│           │           │       │
│           │           │       └─ Return List[Publication]
│           │           │
│           │           ├─[THREAD 3: Europe PMC]
│           │           │   └─ fetch_europepmc()
│           │           │       └─ EuropePMCClient.get_citations(pmid)
│           │           │           ├─ HTTP GET /europepmc/webservices/rest/MED/{pmid}/citations
│           │           │           ├─ Parse XML response
│           │           │           └─ Return List[Publication]
│           │           │
│           │           ├─[THREAD 4: PubMed Citations]
│           │           │   └─ fetch_pubmed_citations()
│           │           │       └─ PubMedClient.get_citing_papers(pmid)
│           │           │           ├─ HTTP GET eutils (elink)
│           │           │           ├─ Get linked PMIDs
│           │           │           └─ Return List[Publication]
│           │           │
│           │           └─ Wait for all threads (futures.as_completed)
│           │               ├─ Merge results from all sources
│           │               ├─ Deduplicate by PMID/DOI
│           │               └─ Return combined list
│           │
│           ├─[STRATEGY B: Mention-Based Discovery]
│           │   └─ _find_via_geo_mention(geo_id)
│           │       │
│           │       ├─ Check Cache
│           │       │   └─ DiscoveryCache.get(f"mention_{geo_id}")
│           │       │
│           │       └─ PubMed Search
│           │           └─ PubMedClient.search(f'"{geo_id}"[All Fields]')
│           │               ├─ HTTP GET esearch
│           │               ├─ Get PMIDs mentioning GEO ID
│           │               ├─ Fetch metadata for each PMID
│           │               └─ Return List[Publication]
│           │
│           ├─ Merge Results
│           │   ├─ Combine Strategy A + Strategy B
│           │   ├─ Deduplicate by PMID
│           │   ├─ Filter by quality (if enabled)
│           │   └─ Limit to max_results
│           │
│           ├─ Cache Results
│           │   └─ DiscoveryCache.set(cache_key, results, ttl=604800)
│           │
│           └─ Return CitationDiscoveryResult
│               ├─ geo_id
│               ├─ original_pmid
│               ├─ citing_papers: List[Publication]
│               ├─ total_found: int
│               └─ sources_used: List[str]
│
├─[EXTERNAL API CLIENT TREE - HTTP Request Layer]
│   │
│   ├─ NCBIClient (E-utilities)
│   │   ├─ esearch(db, term) → HTTP GET
│   │   ├─ efetch(db, ids) → HTTP GET
│   │   ├─ esummary(db, ids) → HTTP GET
│   │   └─ Rate limiting: 3 req/s (10 with API key)
│   │
│   ├─ OpenAlexClient
│   │   ├─ get_work(id) → HTTP GET /works/{id}
│   │   ├─ get_citations(id) → HTTP GET /works?filter=cites:{id}
│   │   ├─ search_works(query) → HTTP GET /works?search={query}
│   │   └─ Rate limiting: 10 req/s (polite pool)
│   │
│   ├─ PubMedClient
│   │   ├─ search(query) → esearch + efetch
│   │   ├─ fetch_details(pmids) → efetch
│   │   └─ Rate limiting: 3 req/s
│   │
│   ├─ SemanticScholarClient
│   │   ├─ get_paper(id) → HTTP GET /paper/{id}
│   │   ├─ get_citations(id) → HTTP GET /paper/{id}/citations
│   │   └─ Rate limiting: 1 req/s (5 with API key)
│   │
│   └─ EuropePMCClient
│       ├─ search(query) → HTTP GET /search
│       ├─ get_citations(pmid) → HTTP GET /citations/{pmid}
│       └─ Rate limiting: Best effort
│
└─[EXTERNAL DATA SOURCES - API Endpoints]
    │
    ├─ NCBI E-utilities
    │   ├─ https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
    │   ├─ Databases: gds, pubmed, sra
    │   └─ Response: XML
    │
    ├─ OpenAlex API
    │   ├─ https://api.openalex.org/
    │   └─ Response: JSON
    │
    ├─ PubMed Central
    │   ├─ https://eutils.ncbi.nlm.nih.gov/
    │   └─ Response: XML
    │
    ├─ Semantic Scholar API
    │   ├─ https://api.semanticscholar.org/
    │   └─ Response: JSON
    │
    └─ Europe PMC API
        ├─ https://www.ebi.ac.uk/europepmc/
        └─ Response: XML/JSON
```

---

## Depth-First Search (DFS) - Critical Paths

### Path 1: Fast Path (Cached Search)
```
DFS Path: User → Result (Cached)
═════════════════════════════════

Depth 0: dashboard_v2.html::performSearch()
    ↓
Depth 1: POST /api/search
    ↓
Depth 2: routes/agents.py::execute_search()
    ↓
Depth 3: search_service.py::execute_search()
    ↓
Depth 4: orchestrator.py::search()
    ↓
Depth 5: redis_cache.py::get_search_result()
    ↓ CACHE HIT
Depth 6: Return cached SearchResult
    ↓
Depth 5: orchestrator returns
    ↓
Depth 4: search_service enrichment (skipped)
    ↓
Depth 3: Format SearchResponse
    ↓
Depth 2: HTTP 200 + JSON
    ↓
Depth 1: dashboard receives
    ↓
Depth 0: displayResults()

Total Depth: 6 levels
Total Time: ~100ms
Bottleneck: Network latency (HTTP round-trip)
Optimization: ✅ Optimal (Redis cache hit)
```

### Path 2: Slow Path (First Search + Auto-Discovery)
```
DFS Path: User → Auto-Discovery → Result
═══════════════════════════════════════════

Depth 0: dashboard_v2.html::performSearch()
    ↓
Depth 1: POST /api/search
    ↓
Depth 2: routes/agents.py::execute_search()
    ↓
Depth 3: search_service.py::execute_search()
    ↓
Depth 4: orchestrator.py::search()
    ↓
Depth 5: redis_cache.py::get_search_result() → MISS
    ↓
Depth 6: PARALLEL EXECUTION (3 threads)
    ├─ Thread 1: geo_client.py::search()
    │   ↓
    │   Depth 7: ncbi_client.py::esearch(db="gds")
    │       ↓
    │       Depth 8: HTTP GET to eutils.ncbi.nlm.nih.gov
    │           ↓
    │           Depth 9: NCBI GEO Database (EXTERNAL)
    │
    ├─ Thread 2: pubmed_client.py::search()
    │   └─ (Similar depth to Thread 1)
    │
    └─ Thread 3: openalex_client.py::search_works()
        └─ (Similar depth to Thread 1)
    ↓
Depth 6: Merge results
    ↓
Depth 5: search_service.py::_build_dataset_responses()
    ↓
Depth 6: geo_cache.py::get(geo_id)
    ↓
Depth 7: redis_cache.py::get_geo_metadata() → MISS
    ↓
Depth 8: unified_db.py::get_complete_geo_data() → MISS
    ↓
Depth 9: geo_cache.py::_auto_discover_and_populate()
    ↓
    Depth 10: geo_client.py::get_metadata()
        ↓
        Depth 11: ncbi_client.py::esummary()
            ↓
            Depth 12: HTTP GET to NCBI
                ↓
                Depth 13: NCBI GEO Database (EXTERNAL)
    ↓
    Depth 10: geo_discovery.py::find_citing_papers()
        ↓
        Depth 11: PARALLEL THREADS (4 citation sources)
            ├─ Thread A: openalex_client.py
            │   ↓
            │   Depth 12: HTTP GET to api.openalex.org
            │       ↓
            │       Depth 13: OpenAlex API (EXTERNAL)
            │           ↓
            │           Depth 14: OpenAlex Database
            │
            ├─ Thread B: semantic_scholar_client.py
            │   └─ Similar depth
            │
            ├─ Thread C: europepmc_client.py
            │   └─ Similar depth
            │
            └─ Thread D: pubmed_client.py
                └─ Similar depth
        ↓
        Depth 11: Merge & deduplicate citations
    ↓
    Depth 10: unified_db.py::insert_geo_dataset()
        ↓
        Depth 11: SQLite INSERT
    ↓
    Depth 10: For each citation:
        └─ unified_db.py::insert_universal_identifier()
            ↓
            Depth 11: SQLite INSERT
    ↓
    Depth 10: unified_db.py::get_complete_geo_data()
        ↓
        Depth 11: SQLite SELECT with JOINs
    ↓
Depth 9: Return enriched geo_data
    ↓
Depth 8: geo_cache promotes to Redis
    ↓
Depth 7: Return to search_service
    ↓
Depth 6: Build DatasetResponse with enriched metrics
    ↓
Depth 5: Format SearchResponse
    ↓
Depth 4: Return to routes
    ↓
Depth 3: HTTP 200 + JSON
    ↓
Depth 2: dashboard receives
    ↓
Depth 1: displayResults()
    ↓
Depth 0: User sees results

Total Depth: 14 levels (deepest path)
Total Time: 5-30 seconds
Bottleneck: Citation discovery parallel threads (Depth 11-14)
Optimization Opportunities: 🎯 See optimization section below
```

### Path 3: Manual Discovery Button Click
```
DFS Path: User Click → Discovery → Update
═════════════════════════════════════════

Depth 0: dashboard_v2.html::discoverCitationsForDataset(index)
    ↓
Depth 1: POST /api/datasets/{geo_id}/discover-citations
    ↓
Depth 2: routes/agents.py::discover_citations()
    ↓
Depth 3: geo_discovery.py::find_citing_papers()
    ↓
Depth 4: [Same as auto-discovery from Depth 11 onwards]
    ↓
... (citation discovery tree)
    ↓
Depth 2: Return {citations_found, success}
    ↓
Depth 1: dashboard receives response
    ↓
Depth 0: Alert user + refresh search

Total Depth: 13 levels
Total Time: 8-25 seconds
Note: Now redundant with auto-discovery!
Optimization: ⚠️ Can be removed (auto-discovery handles this)
```

---

## Breadth-First Search (BFS) - Level-by-Level Analysis

### BFS Level Map

```
LEVEL 0 (Frontend)
═══════════════════
Nodes: 1
├─ dashboard_v2.html
│   ├─ performSearch()
│   ├─ discoverCitationsForDataset()
│   └─ downloadPapersForDataset()

Connections: 3 user actions
Latency: <1ms (client-side JS)
Parallelization: None
Bottleneck: User input
Optimization: ✅ Already minimal


LEVEL 1 (HTTP Layer)
═══════════════════
Nodes: 3
├─ HTTP POST /api/search
├─ HTTP POST /api/datasets/{geo_id}/discover-citations
└─ HTTP POST /api/enrich-fulltext

Connections: Network → API Gateway
Latency: 5-20ms (network round-trip)
Parallelization: None (sequential user actions)
Bottleneck: Network latency
Optimization: ✅ Can't optimize (network-bound)


LEVEL 2 (API Gateway)
═══════════════════
Nodes: 4
├─ main.py (FastAPI app)
├─ routes/agents.py::execute_search()
├─ routes/agents.py::discover_citations()
└─ routes/agents.py::enrich_fulltext()

Connections: Routes → Services
Latency: <5ms (routing + middleware)
Parallelization: None (request handling)
Bottleneck: Middleware chain
Optimization: 
  ⚠️ Consider:
    - Remove unnecessary middleware for read-only endpoints
    - Cache CORS headers
    - Optimize Pydantic validation


LEVEL 3 (Service Layer)
═══════════════════
Nodes: 2
├─ search_service.py::SearchService
│   ├─ execute_search()
│   ├─ _build_dataset_responses()
│   └─ _rank_datasets()
│
└─ Citation discovery service (in routes/agents.py)

Connections: Services → Orchestration
Latency: 5-10ms (business logic)
Parallelization: None at this level
Bottleneck: Sequential dataset enrichment
Optimization: 
  🎯 HIGH IMPACT:
    - Parallelize _build_dataset_responses() 
      (Currently enriches datasets sequentially!)
    - Use asyncio.gather() for batch enrichment


LEVEL 4 (Orchestration)
═══════════════════
Nodes: 3
├─ orchestrator.py::SearchOrchestrator
│   ├─ search() - Main coordinator
│   ├─ _search_geo() - GEO search thread
│   ├─ _search_publications_pubmed() - PubMed thread
│   └─ _search_publications_openalex() - OpenAlex thread
│
├─ geo_cache.py::GEOCache
│   ├─ get() - Cache lookup
│   └─ _auto_discover_and_populate() - Discovery
│
└─ geo_discovery.py::GEOCitationDiscovery
    └─ find_citing_papers() - Citation search

Connections: Orchestrators → Cache/Database/Clients
Latency: 10-50ms (coordination overhead)
Parallelization: ✅ ACTIVE
  - SearchOrchestrator: 3 parallel threads
  - GEOCitationDiscovery: 4 parallel threads
Bottleneck: Waiting for slowest thread
Optimization:
  ✅ Already parallelized
  🎯 Consider:
    - Add timeout for slow threads
    - Return partial results if one fails
    - Load balancing across sources


LEVEL 5 (Cache & Storage)
═══════════════════
Nodes: 2
├─ redis_cache.py::RedisCache
│   ├─ get_search_result()
│   ├─ set_search_result()
│   └─ get_geo_metadata()
│
└─ unified_db.py::UnifiedDatabase
    ├─ get_complete_geo_data()
    ├─ insert_geo_dataset()
    ├─ insert_universal_identifier()
    └─ get_publications_by_geo()

Connections: Cache ↔ Database ↔ Orchestration
Latency:
  - Redis: 0.2-1ms
  - UnifiedDB: 50-200ms (depending on query complexity)
Parallelization: None (cache lookups are sequential)
Bottleneck: UnifiedDB JOIN queries
Optimization:
  🎯 MEDIUM IMPACT:
    - Add database indexes:
      CREATE INDEX idx_geo_id ON universal_identifiers(geo_id)
      CREATE INDEX idx_pmid ON universal_identifiers(pmid)
    - Use connection pooling
    - Consider PostgreSQL for production (faster than SQLite)
    - Denormalize frequently-accessed data


LEVEL 6 (Data Discovery)
═══════════════════
Nodes: 2
├─ geo_client.py::GEOClient
│   ├─ search()
│   ├─ get_metadata()
│   └─ batch_get_metadata()
│
└─ geo_discovery.py::GEOCitationDiscovery
    ├─ _find_via_citation()
    └─ _find_via_geo_mention()

Connections: Discovery → API Clients
Latency: 1-5 seconds (aggregated)
Parallelization: ✅ ACTIVE (citation discovery uses threads)
Bottleneck: External API rate limits
Optimization:
  ✅ Already parallelized
  🎯 Consider:
    - Implement request batching
    - Add circuit breaker for failing sources
    - Cache negative results (404s)


LEVEL 7 (API Clients)
═══════════════════
Nodes: 5
├─ ncbi_client.py::NCBIClient
├─ openalex_client.py::OpenAlexClient
├─ pubmed_client.py::PubMedClient
├─ semantic_scholar_client.py::SemanticScholarClient
└─ europepmc_client.py::EuropePMCClient

Connections: Clients → External APIs
Latency: 500ms - 5 seconds per request
Parallelization: ✅ ACTIVE (multiple clients in parallel)
Bottleneck: 
  - Rate limits (NCBI: 3 req/s, S2: 1 req/s)
  - Network latency
  - API response time
Optimization:
  🎯 HIGH IMPACT:
    - Implement request queuing with priority
    - Add exponential backoff for 429 errors
    - Use HTTP/2 multiplexing
    - Batch requests where APIs support it
    - Add API health monitoring


LEVEL 8 (External APIs)
═══════════════════
Nodes: 5
├─ NCBI E-utilities (eutils.ncbi.nlm.nih.gov)
├─ OpenAlex API (api.openalex.org)
├─ PubMed API (same as NCBI)
├─ Semantic Scholar API (api.semanticscholar.org)
└─ Europe PMC API (www.ebi.ac.uk/europepmc)

Connections: HTTP → External servers
Latency: 200ms - 10 seconds (variable)
Parallelization: N/A (external systems)
Bottleneck: External API performance
Optimization:
  ⚠️ Out of our control
  🎯 Mitigation strategies:
    - Aggressive caching
    - Fallback to alternative sources
    - Request deduplication
    - Monitor API status
```

---

## Performance Analysis - Critical Bottlenecks

### Identified Bottlenecks (Sorted by Impact)

```
┌─────┬──────────────────────────────┬─────────┬──────────┬─────────────┐
│ #   │ Bottleneck                   │ Level   │ Latency  │ Impact      │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 1   │ Sequential Dataset Enrichment│ L3      │ N*50ms   │ 🔴 CRITICAL │
│     │ (_build_dataset_responses)   │         │ N=50→2.5s│             │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 2   │ Citation Discovery (4 sources│ L6-L8   │ 8-25s    │ 🔴 CRITICAL │
│     │ in parallel, wait for slowest│         │          │             │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 3   │ UnifiedDB JOIN Queries       │ L5      │ 50-200ms │ 🟡 HIGH     │
│     │ (no indexes on geo_id, pmid) │         │          │             │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 4   │ External API Rate Limits     │ L7-L8   │ Variable │ 🟡 HIGH     │
│     │ (NCBI: 3/s, S2: 1/s)         │         │          │             │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 5   │ Middleware Chain (CORS, Auth)│ L2      │ 3-5ms    │ 🟢 MEDIUM   │
│     │ on every request             │         │          │             │
├─────┼──────────────────────────────┼─────────┼──────────┼─────────────┤
│ 6   │ GEO Metadata Fetch (NCBI)    │ L6-L8   │ 1-3s     │ 🟢 MEDIUM   │
│     │ (sequential esummary calls)  │         │          │             │
└─────┴──────────────────────────────┴─────────┴──────────┴─────────────┘
```

---

## Optimization Recommendations

### 🔴 CRITICAL PRIORITY

#### 1. Parallelize Dataset Enrichment (L3)
**Current Code:**
```python
# services/search_service.py::_build_dataset_responses()
datasets = []
for ranked in ranked_datasets:
    geo_data = await self.geo_cache.get(ranked.dataset.geo_id)  # SEQUENTIAL!
    # ... enrichment ...
    datasets.append(dataset_response)
```

**Optimized Code:**
```python
# NEW: Parallel enrichment
async def _build_dataset_responses(self, ranked_datasets):
    async def enrich_single(ranked):
        geo_data = await self.geo_cache.get(ranked.dataset.geo_id)
        # ... enrichment logic ...
        return dataset_response
    
    # Execute all enrichments in parallel
    dataset_responses = await asyncio.gather(*[
        enrich_single(ranked) for ranked in ranked_datasets
    ])
    
    return dataset_responses
```

**Impact:**
- Current: 50 datasets * 50ms = 2.5 seconds (sequential)
- Optimized: max(50ms) = 50ms (parallel)
- **Speedup: 50x for uncached datasets**

---

#### 2. Add Database Indexes (L5)
**Current Schema:**
```sql
-- No indexes on foreign keys!
CREATE TABLE universal_identifiers (
    geo_id TEXT,
    pmid TEXT,
    -- ...
);
```

**Optimized Schema:**
```sql
-- Add indexes for JOIN optimization
CREATE INDEX idx_universal_geo_id ON universal_identifiers(geo_id);
CREATE INDEX idx_universal_pmid ON universal_identifiers(pmid);
CREATE INDEX idx_geo_dataset_id ON geo_datasets(geo_id);

-- Composite index for common queries
CREATE INDEX idx_geo_pmid_composite ON universal_identifiers(geo_id, pmid);
```

**Impact:**
- Current: 50-200ms for get_complete_geo_data() with JOINs
- Optimized: 5-20ms (10-40x faster)
- **Critical for auto-discovery performance**

---

### 🟡 HIGH PRIORITY

#### 3. Implement Timeout & Partial Results (L6)
**Current Code:**
```python
# geo_discovery.py - waits for ALL sources
results = []
for future in futures.as_completed(citation_futures):
    results.extend(future.result())  # Blocks until ALL complete
```

**Optimized Code:**
```python
# NEW: Timeout with partial results
results = []
timeout = 10  # seconds

try:
    for future in futures.as_completed(citation_futures, timeout=timeout):
        try:
            results.extend(future.result(timeout=1))
        except Exception as e:
            logger.warning(f"Source failed: {e}")
            continue  # Skip failed source
except concurrent.futures.TimeoutError:
    logger.warning(f"Citation discovery timeout after {timeout}s - returning partial results")

return results  # Return what we have so far
```

**Impact:**
- Current: Wait up to 25 seconds for slowest source
- Optimized: Return after 10 seconds with partial results
- **User sees results 2.5x faster**

---

#### 4. Batch GEO Metadata Fetching (L6)
**Current:**
```python
# geo_client.py::batch_get_metadata() - calls esummary ONCE per ID
for geo_id in geo_ids:
    metadata = await self._fetch_single_metadata(geo_id)  # N requests!
```

**Optimized:**
```python
# NEW: Batch esummary (NCBI supports up to 200 IDs)
async def batch_get_metadata(self, geo_ids):
    batches = [geo_ids[i:i+200] for i in range(0, len(geo_ids), 200)]
    
    all_metadata = {}
    for batch in batches:
        # Single request for 200 IDs
        response = await self.ncbi_client.esummary(
            db="gds", 
            ids=",".join(batch)  # Comma-separated
        )
        # Parse all at once
        all_metadata.update(self._parse_batch_response(response))
    
    return all_metadata
```

**Impact:**
- Current: 50 datasets = 50 HTTP requests = 50 * 1s = 50 seconds
- Optimized: 50 datasets = 1 HTTP request = 1.5 seconds
- **Speedup: 33x**

---

### 🟢 MEDIUM PRIORITY

#### 5. Cache Negative Results (L7)
**Current:**
```python
# No caching for 404s - retries same failed requests
try:
    paper = await openalex_client.get_work(pmid)
except NotFoundError:
    return None  # No caching!
```

**Optimized:**
```python
# Cache 404s for 24 hours
try:
    paper = await openalex_client.get_work(pmid)
except NotFoundError:
    # Cache negative result
    await redis.setex(f"not_found:openalex:{pmid}", 86400, "1")
    return None
```

**Impact:**
- Prevents redundant API calls for missing papers
- Reduces external API load by ~20%

---

#### 6. Request Deduplication (L7)
**Current:**
```python
# Multiple threads may request same paper simultaneously
# Thread 1: openalex.get_work("12345")
# Thread 2: semantic_scholar.get_paper("12345")  # Duplicate!
```

**Optimized:**
```python
# Global request deduplication with asyncio locks
_pending_requests = {}
_locks = defaultdict(asyncio.Lock)

async def deduplicated_request(key, fetch_fn):
    async with _locks[key]:
        if key in _pending_requests:
            return await _pending_requests[key]
        
        task = asyncio.create_task(fetch_fn())
        _pending_requests[key] = task
        
        try:
            result = await task
            return result
        finally:
            del _pending_requests[key]
```

**Impact:**
- Eliminates duplicate requests during parallel discovery
- Reduces API calls by 15-30%

---

## Optimization Implementation Plan

### Phase 1: Quick Wins (1-2 days)
```
1. Add database indexes (30 min)
   └─ Impact: 10-40x faster DB queries
   
2. Parallelize dataset enrichment (2 hours)
   └─ Impact: 50x faster search results
   
3. Add timeout to citation discovery (1 hour)
   └─ Impact: 2.5x faster for slow sources
```

### Phase 2: High-Value (3-5 days)
```
4. Batch GEO metadata fetching (4 hours)
   └─ Impact: 33x fewer API calls
   
5. Cache negative results (2 hours)
   └─ Impact: 20% reduction in API calls
   
6. Request deduplication (4 hours)
   └─ Impact: 15-30% fewer duplicate requests
```

### Phase 3: Infrastructure (1-2 weeks)
```
7. Migrate to PostgreSQL (if needed)
   └─ Impact: Better concurrency, faster JOINs
   
8. Implement connection pooling
   └─ Impact: Lower latency, better scalability
   
9. Add API health monitoring
   └─ Impact: Proactive failover, better reliability
```

---

## Expected Performance After Optimization

```
┌──────────────────────┬──────────┬──────────┬─────────────┐
│ Scenario             │ Current  │ Optimized│ Improvement │
├──────────────────────┼──────────┼──────────┼─────────────┤
│ Cached search        │ 100ms    │ 50ms     │ 2x faster   │
│ First search (50 GEOs│ 30s      │ 5s       │ 6x faster   │
│ Auto-discovery       │ 25s      │ 10s      │ 2.5x faster │
│ DB query (JOIN)      │ 200ms    │ 20ms     │ 10x faster  │
│ Enrichment (50 GEOs) │ 2.5s     │ 50ms     │ 50x faster  │
└──────────────────────┴──────────┴──────────┴─────────────┘
```

---

## Summary

**Tree Structure Benefits:**
- **DFS Analysis:** Identified critical path bottlenecks (14 depth levels)
- **BFS Analysis:** Found parallelization opportunities at each level
- **Optimization Targets:** 6 high-impact improvements identified

**Key Findings:**
1. **Sequential enrichment (L3)** is the #1 bottleneck → Parallelize with asyncio.gather()
2. **Missing DB indexes (L5)** cause slow JOINs → Add indexes on geo_id, pmid
3. **Citation discovery timeout (L6)** waits for slowest source → Add 10s timeout
4. **Batch metadata fetching (L6)** makes N requests → Use batch esummary (1 request)

**Expected Impact:**
- Overall search: **6x faster** (30s → 5s)
- Dataset enrichment: **50x faster** (2.5s → 50ms)
- Database queries: **10x faster** (200ms → 20ms)

**Implementation Priority:**
1. 🔴 Add DB indexes (30 min, 10x impact)
2. 🔴 Parallelize enrichment (2 hours, 50x impact)
3. 🟡 Batch GEO fetching (4 hours, 33x impact)
4. 🟡 Add discovery timeout (1 hour, 2.5x impact)

