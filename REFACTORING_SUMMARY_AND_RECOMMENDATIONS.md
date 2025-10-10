# Refactoring Summary & Architecture Reorganization

**Date:** October 10, 2025  
**Purpose:** Document refactoring completed and recommend folder/file reorganization for clarity

---

## ✅ Refactoring Completed

### 1. Class Renaming (DONE)

**Problem:** `CitationAnalyzer` was misleading - suggested LLM analysis but only did API data retrieval

**Solution:**
```
CitationAnalyzer → CitationFinder
```

**Files Changed:**
1. ✅ `omics_oracle_v2/lib/publications/citations/analyzer.py` → `citation_finder.py`
2. ✅ `omics_oracle_v2/lib/publications/citations/__init__.py` - Updated imports
3. ✅ `omics_oracle_v2/lib/publications/citations/geo_citation_discovery.py` - Updated imports/usage
4. ✅ `omics_oracle_v2/lib/publications/pipeline.py` - Updated imports/usage
5. ✅ `test_openalex_implementation.py` - Updated test code
6. ✅ `test_citation_fixes.py` - Updated test code

### 2. Method Renaming (DONE)

**Changes in CitationFinder:**
```python
# BEFORE (Inconsistent)
class CitationAnalyzer:
    def get_citing_papers(...)        # Inconsistent verb: "get"
    def get_citation_contexts(...)
    def analyze_citation_network(...)  # Wrong verb: "analyze"
    def get_citation_statistics(...)

# AFTER (Consistent)
class CitationFinder:
    def find_citing_papers(...)       # Consistent verb: "find"
    def get_citation_contexts(...)    # "get" is ok for contexts (extracting from already-found papers)
    def find_citation_network(...)    # Consistent verb: "find"
    def get_citation_statistics(...)  # "get" is ok for stats (aggregating data)
```

**Reasoning:**
- **"find"** → Discovery action (external APIs, searching)
- **"get"** → Retrieval action (extracting from known objects)

### 3. Bug Fixes (DONE)

**Bug 1: Wrong Method Call**
- ❌ Called `citation_finder.find_citing_papers()` but method was `get_citing_papers()`
- ✅ Fixed: Renamed method to `find_citing_papers()` for consistency

**Bug 2: Async Handling**
- ❌ Used `await self.pubmed_client.search()` but method is synchronous
- ✅ Fixed: Removed `await` from synchronous call

**Bug 3: Publication Model Validation**
- ❌ Missing required `source` field when creating Publication
- ✅ Fixed: Added `source=PublicationSource.PUBMED`

### 4. Documentation Updates (DONE)

**Updated docstrings to clarify:**
```python
class CitationFinder:
    """
    Find papers that cite a given publication using multiple API sources.

    This class performs PURE DATA RETRIEVAL - no LLM analysis.
    It discovers citing papers via APIs and web scraping only.
    
    NOTE: For LLM-based citation content analysis, see CitationContentAnalyzer (Phase 7).
    """
```

---

## 📊 Current Architecture Analysis

### Current Flow (Query → Citations → PDFs)

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: API Routes (FastAPI)                                   │
│ Location: omics_oracle_v2/api/routes/workflows.py               │
│ Purpose: HTTP endpoints, authentication, request validation      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: Multi-Agent Orchestration (LLM)                        │
│ Location: omics_oracle_v2/agents/                               │
│ Purpose: Query understanding, search planning, reporting         │
│ Components: QueryAgent, SearchAgent, DataAgent, ReportAgent     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: Pipeline Orchestration (No LLM)                        │
│ Location: omics_oracle_v2/lib/workflows/                        │
│ Purpose: End-to-end data collection workflows                   │
│ Components: GEOCitationPipeline                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
         ┌──────────────────┴──────────────────┐
         ↓                                     ↓
┌──────────────────────┐          ┌───────────────────────────┐
│ BLOCK A: GEO Search  │          │ BLOCK B: Citation Discovery│
│ Location: lib/geo/   │          │ Location: lib/publications/│
│                      │          │          citations/        │
│ 1. Query Builder     │          │                           │
│ 2. GEO Client        │          │ 1. GEO Citation Discovery │
│ 3. Metadata Fetch    │          │ 2. Citation Finder        │
└──────────────────────┘          │ 3. PubMed/OpenAlex Clients│
                                  └───────────────────────────┘
                                              ↓
                            ┌─────────────────────────────────┐
                            │ BLOCK C: Full-Text Collection   │
                            │ Location: lib/publications/     │
                            │                                 │
                            │ 1. FullTextManager (waterfall)  │
                            │ 2. Institutional Access         │
                            │ 3. Open Access Sources          │
                            └─────────────────────────────────┘
                                              ↓
                            ┌─────────────────────────────────┐
                            │ BLOCK D: PDF Download & Storage │
                            │ Location: lib/publications/     │
                            │                                 │
                            │ 1. PDF Download Manager         │
                            │ 2. PDF Validator                │
                            │ 3. Local Storage                │
                            └─────────────────────────────────┘
```

### Current Folder Issues

**Problem 1: Mixed Responsibilities**
```
omics_oracle_v2/lib/publications/
├── citations/              ← Citation discovery (Block B)
├── clients/                ← API clients (used in Block B & C)
├── fulltext_manager.py     ← Full-text collection (Block C)
├── pdf_download_manager.py ← PDF download (Block D)
└── pipeline.py             ← Legacy general pipeline (confusing!)
```

**Issues:**
- `pipeline.py` is generic, not GEO-specific
- Full-text and PDF management mixed with citation discovery
- Not clear which files belong to which "block" of the flow

**Problem 2: Workflow Location**
```
omics_oracle_v2/lib/workflows/
└── geo_citation_pipeline.py  ← Only 1 file in whole directory!
```

**Issues:**
- Workflows folder has only ONE pipeline
- Should this be promoted or moved?

**Problem 3: Scattered Components**
```
Block A (GEO):     omics_oracle_v2/lib/geo/
Block B (Citations): omics_oracle_v2/lib/publications/citations/
Block C (Full-text): omics_oracle_v2/lib/publications/
Block D (PDFs):      omics_oracle_v2/lib/publications/
```

**Issues:**
- Blocks B, C, D all in same parent folder
- Hard to see the flow visually
- Not obvious which files are used in which block

---

## 🎯 Recommended Reorganization

### Option 1: Flow-Based Organization (RECOMMENDED)

**Organize by data flow stages:**

```
omics_oracle_v2/lib/
├── pipelines/                          ← NEW: All end-to-end workflows
│   ├── __init__.py
│   ├── base.py                         ← Base pipeline class
│   ├── geo_citation_pipeline.py        ← Moved from workflows/
│   └── publication_pipeline.py         ← Moved from publications/pipeline.py
│
├── geo/                                ← BLOCK A: GEO Dataset Discovery
│   ├── __init__.py
│   ├── client.py                       ← NCBI GEO API client
│   ├── query_builder.py                ← Smart query optimization
│   ├── models.py                       ← GEO data models
│   ├── cache.py                        ← GEO-specific caching
│   └── utils.py
│
├── citations/                          ← BLOCK B: Citation Discovery (NEW TOP-LEVEL)
│   ├── __init__.py
│   ├── discovery/                      ← Discovery layer
│   │   ├── __init__.py
│   │   ├── citation_finder.py          ← Core finder (APIs)
│   │   └── geo_citation_discovery.py   ← GEO-specific discovery
│   ├── analysis/                       ← Analysis layer (LLM - Phase 7)
│   │   ├── __init__.py
│   │   └── llm_analyzer.py             ← LLM-based analysis
│   ├── clients/                        ← API clients
│   │   ├── __init__.py
│   │   ├── openalex.py
│   │   ├── semantic_scholar.py
│   │   ├── pubmed.py
│   │   └── scholar.py
│   └── models.py                       ← Citation data models
│
├── fulltext/                           ← BLOCK C: Full-Text Collection (NEW)
│   ├── __init__.py
│   ├── manager.py                      ← Orchestrates waterfall
│   ├── extractor.py                    ← Text extraction from PDFs
│   ├── sources/                        ← Different access methods
│   │   ├── __init__.py
│   │   ├── pmc.py                      ← PubMed Central
│   │   ├── institutional.py            ← Georgia Tech proxy, etc.
│   │   ├── unpaywall.py                ← Unpaywall API
│   │   ├── core.py                     ← CORE repository
│   │   ├── scihub.py                   ← (Optional) SciHub
│   │   └── libgen.py                   ← (Optional) LibGen
│   └── models.py
│
├── storage/                            ← BLOCK D: Storage & Download (NEW)
│   ├── __init__.py
│   ├── pdf/                            ← PDF-specific
│   │   ├── __init__.py
│   │   ├── download_manager.py         ← Parallel PDF downloads
│   │   ├── validator.py                ← PDF validation
│   │   └── organizer.py                ← File organization
│   ├── cache/                          ← Caching layer
│   │   ├── __init__.py
│   │   ├── redis_cache.py
│   │   └── file_cache.py
│   └── models.py
│
├── publications/                       ← General publication handling
│   ├── __init__.py
│   ├── models.py                       ← Core Publication model
│   ├── deduplication.py                ← Deduplication logic
│   └── ranking/                        ← Ranking/relevance
│       ├── __init__.py
│       └── ranker.py
│
└── workflows/                          ← DEPRECATED (move to pipelines/)
    └── (empty - files moved to pipelines/)
```

**Migration Plan:**
```bash
# Move pipeline files
mv omics_oracle_v2/lib/workflows/geo_citation_pipeline.py \
   omics_oracle_v2/lib/pipelines/

mv omics_oracle_v2/lib/publications/pipeline.py \
   omics_oracle_v2/lib/pipelines/publication_pipeline.py

# Create new structure
mkdir -p omics_oracle_v2/lib/pipelines
mkdir -p omics_oracle_v2/lib/citations/{discovery,analysis,clients}
mkdir -p omics_oracle_v2/lib/fulltext/sources
mkdir -p omics_oracle_v2/lib/storage/{pdf,cache}

# Move citation files
mv omics_oracle_v2/lib/publications/citations/citation_finder.py \
   omics_oracle_v2/lib/citations/discovery/

mv omics_oracle_v2/lib/publications/citations/geo_citation_discovery.py \
   omics_oracle_v2/lib/citations/discovery/

mv omics_oracle_v2/lib/publications/citations/llm_analyzer.py \
   omics_oracle_v2/lib/citations/analysis/

# Move full-text files
mv omics_oracle_v2/lib/publications/fulltext_manager.py \
   omics_oracle_v2/lib/fulltext/manager.py

mv omics_oracle_v2/lib/publications/fulltext_extractor.py \
   omics_oracle_v2/lib/fulltext/extractor.py

mv omics_oracle_v2/lib/publications/clients/oa_sources/* \
   omics_oracle_v2/lib/fulltext/sources/

# Move storage files
mv omics_oracle_v2/lib/publications/pdf_download_manager.py \
   omics_oracle_v2/lib/storage/pdf/download_manager.py

mv omics_oracle_v2/lib/publications/pdf_downloader.py \
   omics_oracle_v2/lib/storage/pdf/downloader.py
```

**Benefits:**
- ✅ **Clear flow visualization** - Folder names match process blocks
- ✅ **Easy navigation** - Find files by asking "which block does this belong to?"
- ✅ **Separation of concerns** - Each block is independent
- ✅ **Scalability** - Easy to add new pipelines or blocks
- ✅ **Testability** - Can test each block independently

---

### Option 2: Layer-Based Organization (Alternative)

**Organize by architectural layer:**

```
omics_oracle_v2/lib/
├── domain/                  ← Core domain models
│   ├── geo/
│   ├── publications/
│   └── citations/
│
├── services/                ← Business logic
│   ├── geo_service.py
│   ├── citation_service.py
│   └── fulltext_service.py
│
├── repositories/            ← Data access
│   ├── geo_repository.py
│   ├── publication_repository.py
│   └── cache_repository.py
│
├── integrations/            ← External APIs
│   ├── ncbi/
│   ├── openalex/
│   └── institutional/
│
└── workflows/               ← Orchestration
    └── geo_citation_workflow.py
```

**Pros:**
- Clean separation by architectural layer
- Follows DDD (Domain-Driven Design)
- Good for large teams

**Cons:**
- ❌ Harder to see data flow
- ❌ Files for one process scattered across layers
- ❌ More cognitive load for developers

**Recommendation:** Use Option 1 (Flow-Based) for this project

---

## 📁 Detailed Block Organization

### BLOCK A: GEO Dataset Discovery

**Current:**
```
omics_oracle_v2/lib/geo/
├── client.py               ← NCBI API client
├── query_builder.py        ← NEW! Smart query optimization
├── models.py               ← GEO data models
├── cache.py                ← GEO caching
└── utils.py
```

**Status:** ✅ **Well-organized - No changes needed**

**Responsibilities:**
1. Query optimization (semantic search)
2. NCBI E-utilities API calls
3. Metadata parsing (SOFT files)
4. GEO-specific caching

---

### BLOCK B: Citation Discovery

**Current (SCATTERED):**
```
omics_oracle_v2/lib/publications/citations/
├── citation_finder.py           ← Core discovery
├── geo_citation_discovery.py    ← GEO-specific
├── llm_analyzer.py              ← LLM analysis (Phase 7)
└── models.py

omics_oracle_v2/lib/publications/clients/
├── openalex.py                  ← Should be with citations
├── semantic_scholar.py          ← Should be with citations
├── pubmed.py                    ← Shared (used in multiple blocks)
└── scholar.py                   ← Should be with citations
```

**Recommended (ORGANIZED):**
```
omics_oracle_v2/lib/citations/
├── discovery/
│   ├── citation_finder.py       ← Multi-source API discovery
│   └── geo_citation_discovery.py← GEO-specific orchestration
├── analysis/
│   └── llm_analyzer.py          ← Phase 7: LLM-based analysis
├── clients/
│   ├── openalex.py              ← Moved from publications/clients/
│   ├── semantic_scholar.py      ← Moved from publications/clients/
│   ├── pubmed.py                ← Shared with Block C
│   └── scholar.py               ← Moved from publications/clients/
└── models.py
```

**Responsibilities:**
1. **Discovery:** Find citing papers via APIs
2. **Analysis:** Understand why/how papers cite (Phase 7)
3. **Clients:** API integrations for citation sources

---

### BLOCK C: Full-Text Collection

**Current (SCATTERED):**
```
omics_oracle_v2/lib/publications/
├── fulltext_manager.py          ← Orchestrator
├── fulltext_extractor.py        ← Text extraction
└── clients/
    ├── institutional_access.py  ← Should be with fulltext
    └── oa_sources/              ← Should be with fulltext
        ├── unpaywall_client.py
        ├── core_client.py
        ├── scihub_client.py
        └── libgen_client.py
```

**Recommended (ORGANIZED):**
```
omics_oracle_v2/lib/fulltext/
├── manager.py                   ← Waterfall orchestrator
├── extractor.py                 ← PDF → text extraction
├── sources/
│   ├── pmc.py                   ← PubMed Central
│   ├── institutional.py         ← Proxy access (GT, ODU)
│   ├── unpaywall.py             ← Open access
│   ├── core.py                  ← Academic repository
│   ├── scihub.py                ← (Optional) SciHub
│   └── libgen.py                ← (Optional) LibGen
└── models.py
```

**Responsibilities:**
1. **Waterfall strategy:** Try sources in priority order
2. **Access methods:** Institutional, open access, etc.
3. **Text extraction:** PDF → structured text

---

### BLOCK D: Storage & Download

**Current (SCATTERED):**
```
omics_oracle_v2/lib/publications/
├── pdf_download_manager.py      ← Parallel downloads
└── pdf_downloader.py            ← Single download

omics_oracle_v2/lib/cache/
└── (various cache implementations)
```

**Recommended (ORGANIZED):**
```
omics_oracle_v2/lib/storage/
├── pdf/
│   ├── download_manager.py      ← Parallel batch downloads
│   ├── downloader.py            ← Single download
│   ├── validator.py             ← PDF validation
│   └── organizer.py             ← File organization by collection
├── cache/
│   ├── redis_cache.py           ← Redis caching
│   ├── file_cache.py            ← File-based caching
│   └── strategy.py              ← Cache invalidation strategy
└── models.py
```

**Responsibilities:**
1. **PDF Download:** Parallel, retry logic, validation
2. **File Organization:** Collections, timestamped folders
3. **Caching:** Redis, file-based, TTL management

---

## 🔄 Migration Impact Assessment

### Low Impact (Easy to migrate):
1. ✅ **Moving workflows/ → pipelines/** - Only 1 file
2. ✅ **Creating top-level citations/** - Clean extraction
3. ✅ **Creating top-level fulltext/** - Clean extraction

### Medium Impact (Requires import updates):
4. ⚠️ **Moving fulltext sources** - Update imports in ~5 files
5. ⚠️ **Moving PDF managers** - Update imports in ~3 files

### High Impact (Many dependencies):
6. ⚠️ **Restructuring publications/** - Core module, many imports

### Recommended Approach:

**Phase 1 (Low Risk - Do Now):**
1. Create new folder structure
2. Move workflow files
3. Move citation discovery files
4. Update imports in tests

**Phase 2 (Medium Risk - Next Session):**
5. Move full-text collection files
6. Move PDF download/storage files
7. Update imports in pipelines

**Phase 3 (Deferred - Future):**
8. Refactor core publications/ module
9. Clean up deprecated folders
10. Update all documentation

---

## 📊 Before & After Comparison

### Before (Current - Confusing)

```
User Query
    ↓
API Route (omics_oracle_v2/api/routes/)
    ↓
Orchestrator (omics_oracle_v2/agents/)
    ↓
Pipeline (omics_oracle_v2/lib/workflows/geo_citation_pipeline.py)
    ↓
┌─────────────────────────────────────────────────────────┐
│ GEO Search                                               │
│ Location: omics_oracle_v2/lib/geo/                      │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Citation Discovery                                       │
│ Location: omics_oracle_v2/lib/publications/citations/   │
│          + omics_oracle_v2/lib/publications/clients/    │ ← SCATTERED!
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Full-Text Collection                                     │
│ Location: omics_oracle_v2/lib/publications/             │
│          + omics_oracle_v2/lib/publications/clients/    │ ← MIXED!
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PDF Download                                             │
│ Location: omics_oracle_v2/lib/publications/             │ ← MIXED!
└─────────────────────────────────────────────────────────┘
    ↓
Local Storage (data/geo_citation_collections/)
```

### After (Proposed - Clear)

```
User Query
    ↓
API Route (omics_oracle_v2/api/routes/)
    ↓
Orchestrator (omics_oracle_v2/agents/)
    ↓
Pipeline (omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py)
    ↓
┌─────────────────────────────────────────────────────────┐
│ BLOCK A: GEO Dataset Discovery                          │
│ Location: omics_oracle_v2/lib/geo/                      │
│ Purpose: Find datasets matching query                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ BLOCK B: Citation Discovery                             │
│ Location: omics_oracle_v2/lib/citations/                │ ← CLEAN!
│ Purpose: Find papers citing datasets                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ BLOCK C: Full-Text Collection                           │
│ Location: omics_oracle_v2/lib/fulltext/                 │ ← CLEAN!
│ Purpose: Get PDF/HTML URLs for papers                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ BLOCK D: Storage & Download                             │
│ Location: omics_oracle_v2/lib/storage/                  │ ← CLEAN!
│ Purpose: Download PDFs, validate, organize               │
└─────────────────────────────────────────────────────────┘
    ↓
Local Storage (data/geo_citation_collections/)
```

---

## 💡 Key Improvements

### 1. Visual Clarity
**Before:** Files scattered across `publications/` folder  
**After:** Each block has dedicated top-level folder

### 2. Easier Navigation
**Before:** "Where is full-text URL discovery?" → Search through publications/  
**After:** "Where is full-text URL discovery?" → `lib/fulltext/`

### 3. Clear Separation
**Before:** Citations, full-text, PDFs all mixed in `publications/`  
**After:** Each block independent: `citations/`, `fulltext/`, `storage/`

### 4. Scalability
**Before:** Adding new pipeline → Unclear where files go  
**After:** Adding new pipeline → Clear block-based structure

### 5. Testing
**Before:** Hard to test blocks independently (mixed dependencies)  
**After:** Each block can be tested in isolation

---

## 🎯 Recommended Action Plan

### Immediate (This Session):
1. ✅ **DONE:** Renamed CitationAnalyzer → CitationFinder
2. ✅ **DONE:** Fixed citation discovery bugs
3. ✅ **DONE:** Updated documentation
4. ⏳ **TODO:** Create summary document (this file)

### Next Session (Low Risk):
5. Create new folder structure:
   ```bash
   mkdir -p omics_oracle_v2/lib/{pipelines,citations/discovery,citations/analysis,citations/clients}
   ```
6. Move workflow files:
   ```bash
   mv omics_oracle_v2/lib/workflows/geo_citation_pipeline.py \
      omics_oracle_v2/lib/pipelines/
   ```
7. Move citation files:
   ```bash
   mv omics_oracle_v2/lib/publications/citations/citation_finder.py \
      omics_oracle_v2/lib/citations/discovery/
   ```
8. Update imports and test

### Future Sessions (Medium Risk):
9. Create fulltext/ and storage/ structure
10. Move full-text and PDF files
11. Update all imports
12. Comprehensive testing

### Long-term (Deferred):
13. Refactor core publications/ module
14. Clean up deprecated folders
15. Update all documentation
16. Create migration guide for other developers

---

## 📝 Summary

### What We Fixed Today:
1. ✅ **Naming:** CitationAnalyzer → CitationFinder (clearer purpose)
2. ✅ **Methods:** Consistent verb usage (find vs. get)
3. ✅ **Bugs:** 3 bugs fixed in citation discovery
4. ✅ **Docs:** Updated docstrings to clarify no LLM analysis

### What We Recommend:
1. 🎯 **Reorganize by Flow Blocks:** geo/ → citations/ → fulltext/ → storage/
2. 🎯 **Move Pipelines:** workflows/ → pipelines/
3. 🎯 **Separate Concerns:** Each block in own top-level folder
4. 🎯 **Phase Migration:** Low-risk files first, test thoroughly

### Why This Matters:
- **For You:** Easier to understand flow at a glance
- **For Team:** Clear structure = faster onboarding
- **For Maintenance:** Each block testable independently
- **For Scaling:** Easy to add new pipelines or blocks

---

## 🚀 Next Steps

**Option A: Proceed with Reorganization**
- Start with Phase 1 (low-risk migrations)
- I'll help update all imports
- Run tests after each move

**Option B: Test Current Changes First**
- Run full pipeline with renamed classes
- Verify citations work end-to-end
- Reorganize in next session

**Your Choice!** What would you like to do next?

