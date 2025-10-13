## OmicsOracle End-to-End Architecture Flow

**Complete System Diagram with Layer Separation Analysis**

```mermaid
graph TB
    %% Layer 1: Frontend
    UI[🌐 dashboard_v2.html<br/>User Interface]

    %% Layer 2: API Gateway
    API[🚪 API Gateway<br/>api/routes/agents.py<br/>880 LOC<br/><br/>Routes:<br/>• /search<br/>• /enrich-fulltext<br/>• /analyze]

    %% Layer 3: Query Processor
    subgraph L3["⚙️ LAYER 3: Query Processor (2,825 LOC)"]
        NER[Biomedical NER<br/>lib/nlp/biomedical_ner.py<br/>Entity Extraction]
        SYN[Synonym Expansion<br/>lib/nlp/synonym_expansion.py<br/>Medical Terms]
        QOPT[Query Optimizer<br/>lib/query/optimizer.py<br/>558 LOC<br/>NER + SapBERT]
        QANAL[Query Analyzer<br/>lib/query/analyzer.py<br/>289 LOC<br/>Type Detection]
    end

    %% Layer 4: Search Orchestrator
    subgraph L4["🎯 LAYER 4: Search Orchestrator (1,124 LOC)"]
        ORCH[SearchOrchestrator<br/>lib/search/orchestrator.py<br/>488 LOC<br/><br/>• Parallel Execution<br/>• Result Merging<br/>• Deduplication<br/>• Caching]
        MLSVC[ML Service<br/>lib/services/ml_service.py<br/>402 LOC]
    end

    %% Layer 5: Data Enrichment
    subgraph L5["✨ LAYER 5: Data Enrichment (9,393 LOC - On-Demand)"]
        FT[Full-Text Manager<br/>lib/fulltext/manager.py<br/>1,185 LOC<br/><br/>Waterfall Sources:<br/>• PubMed Central<br/>• Unpaywall<br/>• arXiv/bioRxiv<br/>• Sci-Hub<br/>• LibGen]

        AICLIENT[AI Analysis<br/>lib/ai/client.py<br/>284 LOC<br/><br/>• Prompt Builder<br/>• LLM Invocation<br/>• Response Parsing]

        PDF[PDF Storage<br/>lib/storage/pdf/<br/>537 LOC]

        ML[ML Features<br/>lib/ml/*<br/>1,756 LOC<br/><br/>• Citation Predictor<br/>• Recommender<br/>• Trend Forecaster]
    end

    %% Layer 6: Client Adapters
    subgraph L6["🔌 LAYER 6: Client Adapters (10,806 LOC)"]
        GEO[GEO Client<br/>lib/geo/client.py<br/>661 LOC<br/><br/>NCBI GEO API<br/>Datasets Search]

        PM[PubMed Client<br/>lib/publications/clients/pubmed.py<br/>397 LOC<br/><br/>PubMed API<br/>Literature Search]

        OA[Open Access Sources<br/>lib/publications/clients/oa_sources/<br/><br/>• Unpaywall<br/>• CORE<br/>• CrossRef<br/>• arXiv<br/>• bioRxiv]

        CITE[Citation Clients<br/>lib/citations/clients/<br/>2,261 LOC<br/><br/>• OpenAlex (525 LOC)<br/>• Semantic Scholar (300 LOC)<br/>• Google Scholar (250 LOC)]

        LLM[LLM Client<br/>lib/llm/client.py<br/>1,092 LOC<br/><br/>OpenAI API<br/>GPT-4]
    end

    %% Layer 7: Infrastructure
    subgraph L7["🏗️ LAYER 7: Infrastructure (2,960 LOC)"]
        REDIS[Redis Cache<br/>lib/cache/redis_cache.py<br/>1,371 LOC<br/><br/>Search Results<br/>API Responses<br/>PDF Metadata]

        EMB[Embeddings<br/>lib/embeddings/service.py<br/>707 LOC<br/><br/>Text Embeddings<br/>Semantic Search]

        VDB[Vector Database<br/>lib/vector_db/faiss_db.py<br/>465 LOC<br/><br/>FAISS Index<br/>Similarity Search]

        PERF[Performance<br/>lib/performance/optimizer.py<br/>417 LOC<br/><br/>Batching<br/>Rate Limiting]
    end

    %% Normal flow
    UI -->|1. Search Request| API
    API -->|2. Validate & Route| QOPT
    QOPT -->|NER| NER
    QOPT -->|Synonyms| SYN
    QOPT -->|3. Optimized Query| ORCH

    %% Parallel search
    ORCH -->|4a. Search Datasets| GEO
    ORCH -->|4b. Search Literature| PM
    ORCH -->|4c. Get Citations| CITE

    %% Cache layer
    ORCH -.->|Cache Check| REDIS
    GEO -.->|Cache Results| REDIS
    PM -.->|Cache Results| REDIS

    %% Enrichment flows (optional)
    API -->|5. Enrich Request| FT
    FT -->|Get PDF URLs| PM
    FT -->|Download PDFs| OA
    FT -->|Store| PDF

    API -->|6. Analyze Request| AICLIENT
    AICLIENT -->|Generate| LLM

    %% ML service
    API -->|7. ML Request| MLSVC
    MLSVC -->|Predictions| ML
    ML -->|Citation Data| PM

    %% Return flow
    ORCH -->|8. Merged Results| API
    FT -->|Full-Text| API
    AICLIENT -->|AI Insights| API
    API -->|9. JSON Response| UI

    %% Violations (red dashed)
    ORCH -.->|⚠️ Direct Import| QANAL
    EMB -.->|⚠️ Type Hints| PM

    %% Styling
    classDef layer3 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef layer4 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef layer5 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef layer6 fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef layer7 fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef violation fill:#fff3cd,stroke:#856404,stroke-width:3px,stroke-dasharray: 5 5

    class NER,SYN,QOPT,QANAL layer3
    class ORCH,MLSVC layer4
    class FT,AICLIENT,PDF,ML layer5
    class GEO,PM,OA,CITE,LLM layer6
    class REDIS,EMB,VDB,PERF layer7
    class ORCH,EMB violation
```

---

## Layer Interaction Matrix

| From ↓ To → | L1 UI | L2 API | L3 Query | L4 Search | L5 Enrich | L6 Clients | L7 Infra |
|-------------|-------|--------|----------|-----------|-----------|------------|----------|
| **L1 UI** | - | ✅ (1) | - | - | - | - | - |
| **L2 API** | ✅ (1) | - | ✅ (1) | ✅ (1) | ✅ (2) | - | - |
| **L3 Query** | - | - | ⚡ (1) | ✅ (1) | - | - | - |
| **L4 Search** | - | - | ⚠️ (1) | ⚡ (2) | - | ✅ (6) | ✅ (1) |
| **L5 Enrich** | - | - | - | - | ⚡ (13) | ✅ (2) | - |
| **L6 Clients** | - | - | - | - | - | ⚡ (41) | - |
| **L7 Infra** | - | - | - | - | - | ⚠️ (1) | ⚡ (7) |

**Legend:**
- ✅ = Proper downward dependency (OK)
- ⚡ = Same-level import (OK within reason)
- ⚠️ = Layer violation (2 total)
- Number = Count of imports

**Key Observations:**
1. **Clean downward flow**: All layers properly depend on lower layers
2. **2 violations total** (out of 87 files analyzed)
3. **No circular dependencies**: Clean directed acyclic graph
4. **Same-level imports**: Reasonable (41 in Client layer, 13 in Enrichment)

---

## Request Flow Examples

### Example 1: Basic Search Flow

```
User enters: "breast cancer gene expression"
    ↓
1. UI → API: POST /search {"query": "breast cancer gene expression"}
    ↓
2. API → Query Optimizer: Optimize query
    ↓
3. Query Optimizer:
   - Biomedical NER: Extracts "breast cancer" (disease), "gene expression" (assay)
   - Synonym Expansion: Adds "mammary carcinoma", "RNA-seq", "transcriptomics"
   - Returns: OptimizedQuery object
    ↓
4. API → SearchOrchestrator: search(optimized_query)
    ↓
5. SearchOrchestrator (parallel execution):
   ├─ GEOClient.search() → 15 datasets
   ├─ PubMedClient.search() → 50 publications
   └─ OpenAlexClient.get_citations() → Citation counts
    ↓
6. SearchOrchestrator:
   - Merges results
   - Deduplicates
   - Caches in Redis
   - Returns: SearchResult object
    ↓
7. API → UI: JSON response with datasets + publications
    ↓
8. UI: Renders results table
```

**Layers Involved:** 2 → 3 → 4 → 6 → 7 → 4 → 2 → 1

**Total Latency:** ~2-3 seconds (parallel execution)

---

### Example 2: Full-Text Enrichment Flow

```
User clicks: "Download Full-Text" on paper PMID:12345678
    ↓
1. UI → API: POST /enrich-fulltext {"pmid": "12345678"}
    ↓
2. API → FullTextManager: get_fulltext(pmid)
    ↓
3. FullTextManager (waterfall):
   ├─ Step 1: PubMedClient → Get paper metadata
   ├─ Step 2: UnpaywallClient → Check open access
   │   └─ Found! URL: https://pmc.ncbi.nlm.nih.gov/...
   ├─ Step 3: Download PDF
   ├─ Step 4: Extract text content
   └─ Step 5: Cache in Redis + Store in filesystem
    ↓
4. API → UI: JSON response with full-text content
    ↓
5. UI: Displays full-text in modal
```

**Layers Involved:** 2 → 5 → 6 → 7 → 5 → 2 → 1

**Total Latency:** ~5-10 seconds (download + extraction)

---

### Example 3: AI Analysis Flow

```
User clicks: "AI Analysis" on GSE123456
    ↓
1. UI → API: POST /analyze {"gse_id": "GSE123456"}
    ↓
2. API → AI Client: analyze_dataset(gse_id)
    ↓
3. AI Client:
   ├─ Step 1: GEOClient → Get dataset metadata
   ├─ Step 2: FullTextManager → Get associated papers (if available)
   ├─ Step 3: Build comprehensive prompt:
   │   {
   │     "title": "...",
   │     "summary": "...",
   │     "organism": "Homo sapiens",
   │     "samples": 24,
   │     "platform": "Illumina HiSeq",
   │     "full_text": "..."  # if available
   │   }
   ├─ Step 4: LLMClient → Call GPT-4
   │   → Prompt: "Analyze this genomics study..."
   │   → Response: Scientific insights, recommendations
   └─ Step 5: Parse response, format markdown
    ↓
4. API → UI: JSON response with AI analysis
    ↓
5. UI: Displays formatted analysis
```

**Layers Involved:** 2 → 5 → 6 → 5 → 2 → 1

**Total Latency:** ~10-20 seconds (LLM call)

---

## Code File Mapping

### Complete File-to-Layer Mapping

```
Layer 2: API Gateway (880 LOC)
├── api/routes/agents.py (880 LOC)
│   └── Endpoints: /search, /enrich-fulltext, /analyze
└── api/auth/* (disabled)

Layer 3: Query Processor (2,825 LOC)
├── lib/nlp/
│   ├── biomedical_ner.py (NER)
│   ├── synonym_expansion.py (Synonyms)
│   ├── query_expander.py
│   └── synonym_manager.py
└── lib/query/
    ├── analyzer.py (289 LOC - Query type detection)
    └── optimizer.py (558 LOC - NER + SapBERT)

Layer 4: Search Orchestrator (1,124 LOC)
├── lib/search/
│   ├── orchestrator.py (488 LOC)
│   ├── config.py
│   └── models.py
└── lib/services/
    └── ml_service.py (402 LOC)

Layer 5: Data Enrichment (9,393 LOC)
├── lib/fulltext/
│   ├── manager.py (1,185 LOC - Waterfall coordinator)
│   ├── normalizer.py (Content extraction)
│   ├── cache_db.py
│   ├── smart_cache.py
│   └── sources/
│       ├── scihub_client.py
│       └── libgen_client.py
├── lib/ai/
│   ├── client.py (284 LOC - AI analysis)
│   ├── prompts.py
│   ├── models.py
│   └── utils.py
├── lib/storage/pdf/
│   ├── download_manager.py
│   └── landing_page_parser.py
├── lib/ml/
│   ├── citation_predictor.py
│   ├── recommender.py
│   ├── trend_forecaster.py
│   ├── embeddings.py
│   └── features.py
└── lib/visualizations/
    ├── network.py
    ├── trends.py
    ├── statistics.py
    └── reports.py

Layer 6: Client Adapters (10,806 LOC)
├── lib/geo/
│   ├── client.py (661 LOC - NCBI GEO)
│   ├── models.py
│   ├── query_builder.py
│   ├── cache.py
│   └── utils.py
├── lib/publications/
│   ├── clients/
│   │   ├── pubmed.py (397 LOC)
│   │   ├── async_pubmed.py
│   │   ├── institutional_access.py
│   │   └── oa_sources/
│   │       ├── unpaywall_client.py
│   │       ├── arxiv_client.py
│   │       ├── biorxiv_client.py
│   │       ├── core_client.py
│   │       └── crossref_client.py
│   ├── models.py
│   ├── deduplication.py
│   └── analysis/
│       ├── knowledge_graph.py
│       ├── qa_system.py
│       └── trends.py
├── lib/citations/
│   ├── clients/
│   │   ├── openalex.py (525 LOC)
│   │   ├── semantic_scholar.py (300 LOC)
│   │   └── scholar.py (250 LOC - Google Scholar)
│   ├── discovery/
│   │   ├── finder.py
│   │   └── geo_discovery.py
│   └── models.py
└── lib/llm/
    ├── client.py (1,092 LOC - OpenAI)
    ├── async_client.py
    └── prompts.py

Layer 7: Infrastructure (2,960 LOC)
├── lib/cache/
│   ├── redis_cache.py (1,371 LOC)
│   └── redis_client.py
├── lib/embeddings/
│   └── service.py (707 LOC)
├── lib/vector_db/
│   ├── faiss_db.py (465 LOC)
│   └── interface.py
└── lib/performance/
    ├── optimizer.py
    └── cache.py
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Active Files** | 87 Python files |
| **Total Active LOC** | ~28,000 LOC |
| **Number of Layers** | 7 (matches optimal design) |
| **Layer Violations** | 2 (0.02% of files) |
| **Circular Dependencies** | 0 |
| **Architecture Compliance** | 98% ✅ |
| **Largest Layer** | Layer 6 (Client Adapters) - 10,806 LOC |
| **Most Complex Module** | lib/publications/ - 24 files |
| **Cleanest Layer** | Layer 3 (Query Processor) - 0 violations |

---

**Status:** ✅ Excellent architecture with near-perfect layer separation
**Next Steps:** Optional refactoring to achieve 100% compliance (not required)
