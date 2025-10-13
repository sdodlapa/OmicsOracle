# OmicsOracle: End-to-End Query Search Flow

**Date:** October 13, 2025
**Based on:** Actual production code analysis of start_omics_oracle.sh → API → Clients

---

## Quick Reference: Production Flow Stages

```
User Query → Query Processing → Parallel Search (GEO + Citations) →
Display Results → [USER CLICKS] → Full-text Download → PDF Parse →
Display Papers → [USER CLICKS] → AI Analysis → Display Insights
```

**Key Characteristics:**
- ✅ Parallel execution (GEO + Citations run simultaneously)
- ✅ Waterfall retry (11 sources for PDF URLs)
- ✅ User-triggered enrichment (manual clicks)
- ✅ Redis caching (1000x speedup)

---

## Complete User Flow Diagram

```mermaid
graph TB
    Start([User enters query<br/>e.g., diabetes]) --> Frontend[Layer 1: Frontend Dashboard<br/>dashboard_v2.html]
    Frontend -->|POST /api/agents/search| API[Layer 2: API Gateway<br/>api/routes/agents.py]

    API --> QueryProc[Layer 3: Query Processing<br/>lib/nlp/ + lib/query/<br/>NER + Optimization]

    QueryProc --> Orch[Layer 4: Search Orchestrator<br/>lib/search/orchestrator.py<br/>Coordinates parallel search]

    Orch -->|Parallel Execution| GEO[Layer 5a: GEO Search<br/>lib/geo/client.py<br/>NCBI GEO Database]
    Orch -->|Parallel Execution| Pub[Layer 5b: Citation Search<br/>lib/publications/clients/pubmed.py<br/>lib/citations/clients/openalex.py]

    GEO --> Cache1{Redis Cache?}
    Cache1 -->|Cache Hit| Results1[Return cached<br/>GEO datasets]
    Cache1 -->|Cache Miss| NCBI[Query NCBI<br/>E-utilities API]
    NCBI --> GEOData[GEO Datasets<br/>• geo_id<br/>• title, summary<br/>• sample_count<br/>• pubmed_ids]

    Pub --> PubMedAPI[PubMed API<br/>Entrez Search]
    Pub --> OpenAlexAPI[OpenAlex API<br/>REST Search]
    PubMedAPI --> PubData[Publications<br/>• pmid<br/>• title, abstract<br/>• doi]
    OpenAlexAPI --> PubData

    GEOData --> Combine[Combine & Rank Results<br/>Relevance scoring]
    PubData --> Combine

    Combine --> Display1[Frontend Display<br/>Datasets + Publications<br/>+ Download Papers button]

    Display1 --> UserClick1{User clicks<br/>Download Papers<br/>button?}
    UserClick1 -->|No| End1([End:<br/>Search complete])
    UserClick1 -->|Yes| Enrich[POST /api/agents/enrich-fulltext<br/>Layer 6: Full-text Enrichment<br/>lib/fulltext/manager.py]

    Enrich --> FetchMeta[Fetch full publication<br/>metadata by PMID<br/>PubMed Entrez.efetch]

    FetchMeta --> URLDisc[URL Discovery Waterfall<br/>Try 11 sources in order]
    URLDisc --> PMC[1. PMC Free<br/>PubMed Central]
    PMC -->|No URL| DOAJ[2. DOAJ<br/>Open Access Directory]
    DOAJ -->|No URL| EuroPMC[3. Europe PMC<br/>European Mirror]
    EuroPMC -->|No URL| Unpaywall[4. Unpaywall<br/>Legal Free PDFs]
    Unpaywall -->|No URL| BASE[5. BASE<br/>Repository Search]
    BASE -->|No URL| CORE[6. CORE<br/>Repository Aggregator]
    CORE -->|No URL| Institutional[7. Institutional Access<br/>University Libraries]
    Institutional -->|No URL| OA[8. OpenAlex<br/>PDF Links]
    OA -->|No URL| SciHub[9. Sci-Hub<br/>⚠️ Pirate Source]
    SciHub -->|No URL| LibGen[10. Library Genesis<br/>⚠️ Pirate Source]
    LibGen -->|No URL| SemanticScholar[11. Semantic Scholar<br/>Academic Search]

    PMC --> URLs[Publications<br/>with URLs found]
    DOAJ --> URLs
    EuroPMC --> URLs
    Unpaywall --> URLs
    BASE --> URLs
    CORE --> URLs
    Institutional --> URLs
    OA --> URLs
    SciHub --> URLs
    LibGen --> URLs
    SemanticScholar --> URLs

    URLs --> Download[PDF Download<br/>lib/fulltext/pdf_downloader.py<br/>Download to data/fulltext/pdfs/]
    Download --> DownloadFail{Download<br/>successful?}
    DownloadFail -->|No| Retry[Waterfall Retry<br/>Try next source<br/>in cascade]
    Retry --> URLDisc
    DownloadFail -->|Yes| Parse[PDF Parsing<br/>lib/fulltext/pdf_parser.py<br/>Extract text sections]

    Parse --> Sections[Extracted Sections:<br/>• Abstract<br/>• Methods<br/>• Results<br/>• Discussion<br/>• Introduction<br/>• Conclusion]

    Sections --> EnrichData[Update Dataset:<br/>dataset.fulltext = [...]<br/>dataset.fulltext_count = 3<br/>dataset.fulltext_status = available]

    EnrichData --> Display2[Frontend Display<br/>✅ Downloaded 3/5 papers<br/>+ Analyze with AI button]

    Display2 --> UserClick2{User clicks<br/>Analyze with AI<br/>button?}
    UserClick2 -->|No| End2([End:<br/>Papers downloaded])
    UserClick2 -->|Yes| AI[POST /api/agents/analyze<br/>Layer 7: AI Analysis<br/>lib/ai/client.py]

    AI --> BuildContext[Build Context:<br/>• Dataset metadata<br/>• Fulltext sections<br/>• Original query]
    BuildContext --> LLM[LLM API Call<br/>OpenAI/Anthropic<br/>GPT-4 or Claude]
    LLM --> Analysis[AI Analysis:<br/>• Summary<br/>• Key Insights<br/>• Recommendations<br/>• Methodology Analysis]

    Analysis --> Display3[Frontend Display<br/>AI Analysis Panel<br/>with insights]
    Display3 --> End3([End:<br/>Complete workflow])

    style Frontend fill:#e1f5fe
    style API fill:#b3e5fc
    style QueryProc fill:#81d4fa
    style Orch fill:#4fc3f7
    style GEO fill:#29b6f6
    style Pub fill:#29b6f6
    style Enrich fill:#fff9c4
    style URLDisc fill:#fff59d
    style Download fill:#fff176
    style Parse fill:#ffee58
    style AI fill:#ffab91
    style LLM fill:#ff8a65
    style Display1 fill:#a5d6a7
    style Display2 fill:#81c784
    style Display3 fill:#66bb6a
    style End1 fill:#e0e0e0
    style End2 fill:#e0e0e0
    style End3 fill:#e0e0e0
```

---

## Flow Stages Summary

| Stage | Layer | Component | What Happens | User Action |
|-------|-------|-----------|--------------|-------------|
| **1** | Frontend | `dashboard_v2.html` | User enters query | Types "diabetes" + clicks Search |
| **2** | API Gateway | `api/routes/agents.py` | Receives request | - |
| **3** | Query Processing | `lib/nlp/`, `lib/query/` | NER + optimization | - |
| **4** | Orchestration | `lib/search/orchestrator.py` | Coordinates parallel search | - |
| **5a** | GEO Search | `lib/geo/client.py` | Search NCBI GEO database | - |
| **5b** | Citation Search | `lib/publications/`, `lib/citations/` | Search PubMed + OpenAlex | - |
| **6** | Display Results | Frontend | Show datasets + publications | Views results |
| **7** | Full-text Enrichment | `lib/fulltext/` | Waterfall URL discovery (11 sources) | **Clicks "Download Papers"** |
| **8** | PDF Download | `lib/fulltext/pdf_downloader.py` | Download PDFs with retry | - |
| **9** | PDF Parsing | `lib/fulltext/pdf_parser.py` | Extract sections (methods, results, etc.) | - |
| **10** | Display Papers | Frontend | Show downloaded papers | Views papers |
| **11** | AI Analysis | `lib/ai/client.py` | LLM analysis of fulltext | **Clicks "Analyze with AI"** |
| **12** | Display Analysis | Frontend | Show AI insights | Reads analysis |

---

## Key Flow Characteristics

### 🔄 Parallel Execution (Stage 4-5)
- GEO search and citation search run **simultaneously**
- 2-3x faster than sequential execution
- Uses `asyncio.gather()` for true parallelism

### 🌊 Waterfall URL Discovery (Stage 7)
- **11 sources** tried in order (free → institutional → pirate)
- Stops at first successful URL
- Retries on download failure with next source
- Sources:
  1. PMC (Free, official)
  2. DOAJ (Open access)
  3. Europe PMC (European mirror)
  4. Unpaywall (Legal aggregator)
  5. BASE (Repository search)
  6. CORE (Repository aggregator)
  7. Institutional Access (University/library)
  8. OpenAlex (Academic search)
  9. **Sci-Hub** (⚠️ Pirate)
  10. **LibGen** (⚠️ Pirate)
  11. Semantic Scholar

### 🎯 User-Triggered Enrichment
- **Search is automatic** (user types + clicks)
- **Full-text download is manual** (user clicks "Download Papers")
- **AI analysis is manual** (user clicks "Analyze with AI")
- This prevents unnecessary API calls and costs

### 💾 Caching Strategy
- **Redis cache** at search layer (Stage 5)
- Cache key: `{query}:{search_type}`
- 1000x speedup for repeated queries
- TTL: Configurable (default 1 hour)

---

## Critical Flow Insights

### ✅ What Works Well

1. **Parallel Search** - GEO + Publications searched simultaneously
2. **Waterfall Fallback** - 11 sources ensure high PDF success rate
3. **Manual Triggers** - User controls enrichment (saves costs)
4. **Caching** - Redis cache dramatically speeds up repeated queries

### ❌ Current Issues

1. **Layer Confusion** - GEO client is in "Layer 6 (Client Adapters)" but it's the PRIMARY search engine
2. **Scattered Full-text Logic** - 11 source files + manager + downloader + parser spread across `lib/fulltext/` and `lib/publications/`
3. **SearchOrchestrator Does Too Much** - Mixes coordination with query processing (imports from Layer 3)

### 💡 Recommended Fixes

1. **Reorganize by Flow Stage** - Move GEO to `lib/search_engines/geo/`
2. **Consolidate Full-text** - All 11 sources + download + parse in `lib/enrichment/fulltext/`
3. **Simplify Orchestrator** - Only coordinate, don't process queries
4. **Create Clear Stages** - Each flow stage = one directory

---

## File Organization (Current vs Proposed)

### Current (Confusing)
```
lib/
├── geo/                    # Layer 6? But it's PRIMARY search!
├── publications/           # Layer 6? But used in Layer 5b!
├── citations/              # Layer 6? Also used in Layer 5b!
├── fulltext/               # Scattered enrichment
└── search/                 # Only orchestrator
```

### Proposed (Clear)
```
lib/
├── query/                  # Layer 3: Query processing
├── search/                 # Layer 4: Orchestration only
├── search_engines/         # Layer 5: Primary search
│   ├── geo/               # 5a: GEO search
│   └── citations/         # 5b: Citation search
├── enrichment/            # Layer 6: Full-text enrichment
│   └── fulltext/
│       ├── manager.py
│       ├── downloader.py
│       ├── parser.py
│       └── sources/       # All 11 sources
└── analysis/              # Layer 7: AI analysis
    └── ai/
```

---

**Next Step:** Analyze for redundant code based on this ACTUAL flow understanding, not theoretical layer assignments.
