# 🏗️ OmicsOracle Complete Architecture Overview

**Date:** October 6, 2025
**Status:** Phase 4 - Production Features
**Current Branch:** phase-4-production-features

---

## 📊 **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  • Web UI: semantic_search.html (Tasks 1, 2, 3)                 │
│  • API Documentation: /docs (FastAPI auto-generated)            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      REST API LAYER                              │
│  • FastAPI application (omics_oracle_v2/api/main.py)           │
│  • Routes: /api/agents, /api/workflows, /api/auth              │
│  • Middleware: Rate limiting, logging, metrics                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  • SearchAgent: Query → GEO datasets                            │
│  • QueryAgent: NLP query understanding                          │
│  • DataAgent: Dataset download & validation                     │
│  • ReportAgent: Generate analysis reports                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    LIBRARY LAYER (lib/)                          │
│  • geo/: NCBI GEO API integration                               │
│  • nlp/: Query processing & entity extraction                   │
│  • search/: Keyword & semantic search engines                   │
│  • vector_db/: FAISS embeddings (NOT BUILT YET)                │
│  • ranking/: Result ranking & reranking                         │
│  • rag/: Retrieval augmented generation (for LLM)              │
│  • ai/: LLM integration (OpenAI, Anthropic, local)             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
│  • cache/: Redis (optional) + in-memory caching                 │
│  • database/: SQLite/PostgreSQL for users/sessions              │
│  • auth/: JWT authentication, rate limiting, quotas             │
│  • middleware/: Request handling, logging, metrics              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 **Directory Structure Explained**

### **ROOT LEVEL**

```
OmicsOracle/
├── omics_oracle_v2/          # MAIN SOURCE CODE
├── tests/                     # Test suites
├── scripts/                   # Utility scripts
├── docs/                      # Documentation (200+ files!)
├── config/                    # Configuration files
├── data/                      # Runtime data & cache
├── backups/                   # Old code (40% of repo - SHOULD DELETE)
├── examples/                  # Usage examples
├── pyproject.toml            # Python project config
├── requirements.txt          # Dependencies
├── Dockerfile                # Docker setup
├── docker-compose.yml        # Multi-container orchestration
└── start_dev_server.sh       # Development server launcher
```

---

## 🎯 **CORE: omics_oracle_v2/ (Main Application)**

### **1. API Layer** (`omics_oracle_v2/api/`)

```
api/
├── main.py                    # FastAPI app factory ⭐ ENTRY POINT
├── config.py                  # API settings & configuration
├── middleware.py              # Request/response middleware
│
├── routes/                    # REST endpoints
│   ├── agents.py              # Agent execution endpoints ⭐
│   ├── auth.py                # Login, register, tokens
│   ├── users.py               # User management
│   ├── quotas.py              # Rate limits & usage tracking
│   ├── workflows.py           # Multi-agent workflows
│   ├── batch.py               # Batch processing
│   └── websocket.py           # Real-time updates
│
├── models/                    # Pydantic schemas
│   ├── requests.py            # Request models (SearchRequest, etc.)
│   └── responses.py           # Response models (SearchResponse, etc.)
│
└── static/                    # Frontend files
    └── semantic_search.html   # Main search UI ⭐ WHAT YOU SEE
```

**Key Files:**
- **`main.py`**: Application startup, route registration, middleware setup
- **`routes/agents.py`**: Search endpoint (`POST /api/agents/search`) ⭐
- **`static/semantic_search.html`**: Full search interface (2,288 lines!)

---

### **2. Agents Layer** (`omics_oracle_v2/agents/`)

```
agents/
├── __init__.py                # Agent exports
├── base.py                    # BaseAgent class (all agents inherit)
│
├── search_agent.py            # ⭐ SearchAgent - Main search logic
├── query_agent.py             # QueryAgent - NLP query understanding
├── data_agent.py              # DataAgent - Dataset download/validation
├── report_agent.py            # ReportAgent - Generate reports
│
└── models/                    # Agent-specific data models
    ├── search.py              # SearchInput, RankedDataset, etc.
    ├── query.py               # QueryInput, QueryResult
    ├── data.py                # DataInput, DataResult
    └── report.py              # ReportInput, ReportResult
```

**SearchAgent** (`search_agent.py`) - **MOST IMPORTANT FOR YOU**:
```python
class SearchAgent(BaseAgent):
    def execute(self, input_data: SearchInput) -> AgentResult:
        # 1. Parse query terms
        # 2. Search NCBI GEO (keyword OR semantic)
        # 3. Fetch metadata for each dataset
        # 4. Rank by relevance
        # 5. Return top N results
```

**Current Flow:**
```
User query → SearchAgent.execute()
           → lib/search/keyword_search.py (WORKING ✅)
           → lib/geo/ncbi_client.py (fetch metadata)
           → Rank results by keyword match
           → Return to frontend
```

**Planned Flow (with semantic):**
```
User query → SearchAgent.execute()
           → lib/search/semantic_search.py (NOT BUILT ❌)
           → lib/vector_db/faiss_index.py (embedding search)
           → Hybrid ranking (keyword + vector similarity)
           → lib/ranking/cross_encoder_reranker.py
           → Return to frontend
```

---

### **3. Library Layer** (`omics_oracle_v2/lib/`)

This is where the **REAL MAGIC** happens:

```
lib/
├── geo/                       # NCBI GEO Integration ⭐
│   ├── ncbi_client.py         # API calls to NCBI
│   ├── geo_parser.py          # Parse GEO dataset files
│   └── metadata_fetcher.py    # Fetch dataset metadata
│
├── search/                    # Search Engines ⭐
│   ├── keyword_search.py      # Keyword matching (WORKING ✅)
│   ├── semantic_search.py     # Vector similarity (NEEDS FAISS ❌)
│   └── hybrid_search.py       # Combine keyword + semantic
│
├── vector_db/                 # Vector Database (FAISS) ⭐
│   ├── faiss_index.py         # FAISS index management
│   ├── embeddings_generator.py # Generate embeddings
│   └── similarity_search.py   # Vector similarity search
│
├── nlp/                       # Natural Language Processing
│   ├── query_processor.py     # Parse & expand queries
│   ├── entity_extractor.py    # Extract scientific entities
│   └── ontology_mapper.py     # Map terms to ontologies
│
├── ranking/                   # Result Ranking
│   ├── bm25_ranker.py         # BM25 keyword ranking
│   ├── vector_ranker.py       # Cosine similarity ranking
│   └── cross_encoder_reranker.py # Re-rank with transformer
│
├── rag/                       # Retrieval Augmented Generation
│   ├── context_builder.py     # Build LLM context
│   ├── prompt_templates.py    # Prompt engineering
│   └── response_parser.py     # Parse LLM responses
│
├── ai/                        # LLM Integration
│   ├── openai_client.py       # OpenAI (GPT-4, etc.)
│   ├── anthropic_client.py    # Claude
│   ├── local_llm.py           # Llama, Mistral (local)
│   └── llm_factory.py         # LLM selection/switching
│
├── embeddings/                # Text → Vector conversion
│   ├── sentence_transformers.py
│   ├── openai_embeddings.py
│   └── cache.py               # Cache embeddings
│
└── performance/               # Optimization
    ├── caching.py             # Smart caching
    └── batch_processor.py     # Batch API calls
```

**Status of Each Module:**

| Module | Status | Purpose |
|--------|--------|---------|
| `geo/` | ✅ **WORKING** | Fetch GEO datasets from NCBI |
| `search/keyword_search.py` | ✅ **WORKING** | Keyword matching (current mode) |
| `search/semantic_search.py` | ⚠️ **CODE EXISTS** | Needs FAISS index |
| `vector_db/` | ❌ **NOT BUILT** | No embeddings generated yet |
| `nlp/` | ⚠️ **PARTIAL** | Basic query parsing works |
| `ranking/` | ✅ **WORKING** | BM25 ranking active |
| `rag/` | ⚠️ **SKELETON** | Structure exists, not integrated |
| `ai/` | ⚠️ **SKELETON** | Code exists, not used in search yet |
| `embeddings/` | ⚠️ **PARTIAL** | Code exists, no embeddings cached |

---

### **4. Authentication & Security** (`omics_oracle_v2/auth/`)

```
auth/
├── dependencies.py            # FastAPI dependencies (get_current_user)
├── models.py                  # User, Token models
├── jwt.py                     # JWT token handling
├── quota.py                   # Rate limiting & quotas
└── password.py                # Password hashing
```

**Current State:**
- ✅ JWT authentication implemented
- ✅ Rate limiting with quotas
- ✅ Search endpoint made public (for demo/testing)
- ⚠️ No user registration flow in UI yet

---

### **5. Caching Layer** (`omics_oracle_v2/cache/`)

```
cache/
├── redis_client.py            # Redis connection (optional)
└── memory_cache.py            # In-memory fallback (ACTIVE ✅)
```

**Current:** Using in-memory cache (Redis not required)

---

### **6. Database** (`omics_oracle_v2/database/`)

```
database/
├── models.py                  # SQLAlchemy models (User, Session, etc.)
├── session.py                 # Database session management
└── migrations/                # Alembic migrations
```

**Current:** SQLite (simple, works for dev/demo)

---

### **7. Core Utilities** (`omics_oracle_v2/core/`)

```
core/
├── config.py                  # Global settings
├── logging.py                 # Logging setup
└── exceptions.py              # Custom exceptions
```

---

### **8. Scripts** (`omics_oracle_v2/scripts/`)

```
scripts/
├── embed_geo_datasets.py      # ⭐ BUILD SEMANTIC INDEX (NOT RUN YET)
├── download_geo_metadata.py   # Bulk download metadata
├── create_sample_data.py      # Generate test data
└── validate_database.py       # Check database integrity
```

**CRITICAL:** `embed_geo_datasets.py` is what you need to run to enable semantic search!

---

## 🔄 **Current Search Flow (Keyword Mode)**

```
1. User types query in browser (semantic_search.html)
   ↓
2. JavaScript sends POST /api/agents/search
   {
     "search_terms": ["cancer"],
     "enable_semantic": false,
     "max_results": 20
   }
   ↓
3. FastAPI routes/agents.py → SearchAgent.execute()
   ↓
4. SearchAgent uses lib/search/keyword_search.py
   ↓
5. Calls lib/geo/ncbi_client.py → NCBI Entrez API
   ↓
6. NCBI returns GEO IDs (GSE123456, GSE789012, ...)
   ↓
7. Fetch metadata for each dataset
   ↓
8. Rank by keyword relevance (BM25)
   ↓
9. Return top N results as JSON
   ↓
10. Frontend displays dataset cards
```

**Time:** ~1-5 seconds per search

---

## 🚀 **Planned Search Flow (Semantic Mode - NOT BUILT)**

```
1. User types query in browser
   ↓
2. JavaScript sends POST /api/agents/search
   {
     "search_terms": ["cancer"],
     "enable_semantic": true,  ← Semantic mode
     "max_results": 20
   }
   ↓
3. SearchAgent checks if FAISS index exists
   ↓
4. IF EXISTS:
   - Convert query to embedding (sentence-transformers)
   - Search FAISS index for similar dataset embeddings
   - Get top 100 candidates by vector similarity
   - Re-rank with cross-encoder (more accurate)
   - Return top 20 results
   ↓
5. IF NOT EXISTS (CURRENT STATE):
   - Log warning: "FAISS index not found"
   - Fall back to keyword search
   - Continue as normal
```

**To Build:**
```bash
# This would take 1-2 hours:
python -m omics_oracle_v2.scripts.embed_geo_datasets

# Would create:
data/vector_db/geo_index.faiss        # Vector index (FAISS)
data/embeddings/cache/                # Cached embeddings
```

---

## 📦 **Data Directory Structure**

```
data/
├── vector_db/                 # Vector databases (FAISS)
│   └── geo_index.faiss        # ❌ NOT CREATED YET
│
├── embeddings/                # Cached embeddings
│   └── cache/                 # ❌ EMPTY
│
├── cache/                     # Runtime cache
│   ├── search/                # Search results cache
│   ├── rag/                   # RAG context cache
│   └── reranking/             # Reranking cache
│
├── references/                # Reference data
│   └── ontologies/            # GO, DO, etc.
│
├── exports/                   # User exports (CSV, JSON)
│
└── analytics/                 # Usage analytics
```

---

## 🧪 **Testing Structure**

```
tests/
├── unit/                      # Unit tests (individual functions)
│   ├── agents/                # Test each agent
│   ├── lib/                   # Test library functions
│   └── api/                   # Test API routes
│
├── integration/               # Integration tests (multiple components)
│   ├── search_flow/           # End-to-end search tests
│   └── api_workflows/         # API workflow tests
│
├── e2e/                       # End-to-end tests (browser automation)
│   └── selenium_tests/        # Browser tests
│
└── performance/               # Performance benchmarks
    └── load_tests/            # Load testing
```

---

## 🎨 **Frontend (semantic_search.html)**

**File:** `omics_oracle_v2/api/static/semantic_search.html` (2,288 lines!)

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 1200+ lines of CSS */
        - Modern gradient UI
        - Responsive design
        - Animations & transitions
    </style>
</head>
<body>
    <!-- Header -->
    <header>Search Datasets</header>

    <!-- Search Section -->
    <section class="search-section">
        - Query input with validation
        - Keyword/Semantic toggle
        - Query suggestions dropdown
        - Example query chips
        - Filter controls (organism, samples, etc.)
    </section>

    <!-- Results Section -->
    <section class="results-section">
        - Results stats (count, time, mode)
        - Dataset cards (GEO ID, title, summary, metadata)
        - Visualization panel (charts)
        - Export buttons (CSV, JSON)
    </section>

    <!-- Search History (Task 3) -->
    <aside class="history-panel">
        - Recent searches (localStorage)
        - Click to re-run search
    </aside>

    <script>
        /* 900+ lines of JavaScript */
        - performSearch() - Main search function
        - displayResults() - Render dataset cards
        - Query validation
        - Search history management
        - Export functionality
        - Chart generation (Chart.js)
    </script>
</body>
</html>
```

**Features Implemented:**
- ✅ Task 1: Query suggestions (10+ templates)
- ✅ Task 2: Example queries (5 chips)
- ✅ Task 3: Search history (10 recent, localStorage)
- ✅ Query validation (min 3 chars)
- ✅ Real-time feedback
- ✅ Results display with metadata
- ✅ Export to CSV/JSON
- ✅ Visualization panel
- ✅ Responsive design

---

## 🗑️ **backups/ (40% of Repository - SHOULD DELETE)**

```
backups/
├── legacy_v1_system/          # Old v1 codebase (~15,000 LOC)
├── clean_architecture/        # Abandoned refactor attempt
├── final_cleanup/             # Old cleanup attempt
└── ... (many more)
```

**Recommendation:** DELETE ALL OF THIS (see COMPREHENSIVE_ARCHITECTURE_AUDIT.md)

---

## 📚 **docs/ (200+ Documentation Files!)**

```
docs/
├── COMPREHENSIVE_ARCHITECTURE_AUDIT.md  # ⭐ Our audit
├── SYSTEM_STATUS_WARNINGS_EXPLAINED.md  # Warning messages
├── WHY_THESE_ARE_NOT_BUGS.md            # Your questions answered
├── QUICK_TESTING_GUIDE.md               # 5-minute test guide
├── TESTING_PROGRESS.md                  # 53-item checklist
├── ERROR_ANALYSIS_AND_RESOLUTION.md     # Error debugging
│
├── API_REFERENCE.md
├── DEPLOYMENT_GUIDE.md
├── DEVELOPER_GUIDE.md
│
├── archive/                   # Old docs (50+ files)
├── planning/                  # Planning docs
├── reports/                   # Analysis reports
└── ... (many more)
```

**Recommendation:** Keep only 10 essential docs, archive the rest

---

## 🔌 **Configuration Files**

```
config/
├── development.yml            # Dev settings
├── production.yml             # Prod settings
├── testing.yml                # Test settings
├── nginx.conf                 # Nginx reverse proxy
└── prometheus.yml             # Metrics monitoring
```

---

## 🐳 **Docker Setup**

```
├── Dockerfile                 # Main container
├── Dockerfile.production      # Production optimized
└── docker-compose.yml         # Multi-container setup
```

---

## ⚙️ **Configuration Files**

```
├── pyproject.toml             # Python project metadata
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── requirements-web.txt       # Web-specific dependencies
├── .pre-commit-config.yaml    # Pre-commit hooks (linting)
└── Makefile                   # Build commands
```

---

## 🎯 **KEY FINDINGS**

### **What's WORKING:**
1. ✅ **Keyword Search** - Full pipeline working
2. ✅ **NCBI GEO Integration** - Fetching real datasets
3. ✅ **Frontend UI** - All Task 1, 2, 3 features
4. ✅ **API Layer** - FastAPI with all routes
5. ✅ **Authentication** - JWT, rate limiting
6. ✅ **Results Display** - Cards, export, visualization

### **What's MISSING:**
1. ❌ **Semantic Search** - No FAISS index built
2. ❌ **LLM Analysis** - Not integrated into search flow
3. ❌ **Vector Embeddings** - Not generated
4. ❌ **User Registration UI** - No signup page
5. ❌ **Production Deployment** - Not deployed anywhere

### **What Should Be DELETED:**
1. 🗑️ `backups/` folder - 40% of repository
2. 🗑️ 190 documentation files - keep only 10
3. 🗑️ Duplicate test suites

---

## 🚀 **NEXT STEPS (Your Options)**

### **Option 1: Enable Semantic Search** (5-8 hours)
```bash
# 1. Run embedding script (1-2 hours)
python -m omics_oracle_v2.scripts.embed_geo_datasets

# 2. Test semantic search
# 3. Compare keyword vs semantic results
# 4. Tune ranking parameters
```

### **Option 2: Add LLM Analysis** (8-12 hours)
```python
# 1. Integrate OpenAI/Anthropic API
# 2. Build prompt templates
# 3. Add "Analyze with AI" button to results
# 4. Display insights below dataset cards
```

### **Option 3: Clean Up Codebase** (4-6 hours)
```bash
# 1. Delete backups/ folder
# 2. Consolidate test suites
# 3. Reduce docs from 200 to 10 files
# 4. Organize package structure
```

### **Option 4: Production Deployment** (8-12 hours)
```bash
# 1. Docker containerization
# 2. PostgreSQL instead of SQLite
# 3. Redis for caching
# 4. Nginx reverse proxy
# 5. HTTPS/SSL setup
# 6. Deploy to cloud (AWS/GCP/Azure)
```

---

## 📊 **SUMMARY**

**Your Application:**
- **Type:** AI-powered biomedical dataset search engine
- **Architecture:** Multi-layer (API → Agents → Libraries → Infrastructure)
- **Current State:** Keyword search working, semantic search ready but not enabled
- **Frontend:** Full-featured search UI with all planned features
- **Backend:** Solid agent-based architecture
- **Missing Piece:** FAISS embeddings + LLM integration

**Code Quality:**
- ✅ Well-structured agent architecture
- ✅ Clean separation of concerns
- ✅ Good API design (FastAPI)
- ⚠️ 40% dead code in backups/
- ⚠️ Too much documentation (200+ files)
- ⚠️ Some duplicate code

**Ready For:**
1. Adding semantic search (just need to build index)
2. LLM integration (structure exists)
3. Production deployment (with cleanup)

---

**What would you like to focus on next?**
