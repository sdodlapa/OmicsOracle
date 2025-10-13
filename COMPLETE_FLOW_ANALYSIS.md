# OmicsOracle: Complete Flow Analysis & Reorganization Plan

**Date:** October 13, 2025
**Status:** ✅ Complete file mapping with usage verification

---

## Executive Summary

After analyzing the complete production flow and verifying actual file usage, here are the findings:

### ✅ Files Actually Used in Production

**Total Active Code:** ~19,000 LOC across 12 flow stages

### ❌ Files NOT Used in Production (Candidates for Archival)

1. **Embeddings** (278 LOC) - Only used in test script
2. **Vector DB** (465 LOC) - Only used in test script
3. **AsyncPubMedClient** (354 LOC) - Not imported anywhere
4. **Storage/dataset_storage.py** - Not used
5. **Storage/publication_storage.py** - Not used

### 🔄 Duplicate/Overlapping Files

1. **PDF Downloader** - TWO implementations:
   - `lib/storage/pdf/download_manager.py` (USED in agents.py)
   - `lib/fulltext/pdf_downloader.py` (447 LOC) - ❓ Status unknown

---

## Complete Flow with Verified Files

### Stage 1: Frontend UI
```
File: api/static/dashboard_v2.html (1,913 LOC)
Status: ✅ ACTIVE
Purpose: User interface, search form, results display
```

### Stage 2: API Gateway
```
Files:
  ✅ api/routes/agents.py (881 LOC) - Main endpoints
  ✅ api/main.py - FastAPI app
  ✅ api/models/requests.py - Request models
  ✅ api/models/responses.py - Response models
```

### Stage 3: Query Processing (NLP)
```
Files:
  ✅ lib/nlp/biomedical_ner.py (401 LOC) - NER
  ✅ lib/nlp/query_expander.py (186 LOC) - Expansion
  ✅ lib/nlp/synonym_expansion.py (255 LOC) - Synonyms
  ✅ lib/query/analyzer.py (392 LOC) - Type detection
  ✅ lib/query/optimizer.py (370 LOC) - Optimization
```

### Stage 4: Search Orchestration
```
Files:
  ✅ lib/search/orchestrator.py (489 LOC) - Coordinator
  ✅ lib/search/config.py - Configuration
  ✅ lib/search/models.py - Data models
```

### Stage 5a: GEO Search (PRIMARY SEARCH ENGINE)
```
Files:
  ✅ lib/geo/client.py (662 LOC) - NCBI GEO API client
  ✅ lib/geo/query_builder.py (246 LOC) - Query optimization
  ✅ lib/geo/models.py (266 LOC) - GEO data models
  ✅ lib/geo/utils.py (132 LOC) - Rate limiting, retry
  ✅ lib/geo/cache.py (45 LOC) - Simple cache

Total: 1,351 LOC
```

### Stage 5b: Citation Search
```
Files:
  ✅ lib/publications/clients/pubmed.py (398 LOC) - PubMed search
  ✅ lib/citations/clients/openalex.py (526 LOC) - OpenAlex
  ✅ lib/citations/clients/scholar.py (287 LOC) - Google Scholar
  ✅ lib/citations/clients/semantic_scholar.py (312 LOC) - Semantic Scholar
  ✅ lib/publications/clients/base.py (158 LOC) - Base class
  ✅ lib/publications/models.py (398 LOC) - Publication models
  ✅ lib/publications/config.py - Configuration

  ❌ lib/publications/clients/async_pubmed.py (354 LOC) - NOT USED

Total Active: 2,079 LOC
Total Unused: 354 LOC
```

### Stage 6: Full-text URL Discovery
```
Files:
  ✅ lib/fulltext/manager.py (1,185 LOC) - URL discovery orchestrator

  URL Sources (11 total):
  ✅ lib/publications/clients/oa_sources.py (892 LOC)
     - PMC, DOAJ, Europe PMC, BASE, CORE
  ✅ lib/fulltext/sources/unpaywall_client.py (179 LOC)
  ✅ lib/fulltext/sources/scihub_client.py (156 LOC) - Pirate
  ✅ lib/fulltext/sources/libgen_client.py (203 LOC) - Pirate
  ✅ lib/publications/clients/institutional_access.py (586 LOC)

  ✅ lib/fulltext/models.py (158 LOC) - Data models

Total: 3,359 LOC
```

### Stage 7: PDF Download
```
Files:
  ✅ lib/storage/pdf/download_manager.py - USED in agents.py (line 350)
  ❓ lib/fulltext/pdf_downloader.py (447 LOC) - Duplicate? Need to verify

  ⚠️ ISSUE: Two PDF downloaders exist!
```

### Stage 8: PDF Parsing
```
Files:
  ✅ lib/fulltext/pdf_parser.py (568 LOC) - Text extraction
  ✅ lib/fulltext/normalizer.py - Text normalization
  ✅ lib/storage/pdf/landing_page_parser.py - HTML parsing
```

### Stage 9: AI Analysis
```
Files:
  ✅ lib/ai/client.py (284 LOC) - LLM client
  ✅ lib/ai/prompts.py (212 LOC) - Prompt templates
  ✅ lib/ai/models.py (186 LOC) - Data models
  ✅ lib/ai/config.py - Configuration

Total: 682 LOC
```

### Infrastructure (Cross-cutting)
```
Caching:
  ✅ lib/cache/redis_cache.py (608 LOC) - Redis client
  ✅ lib/cache/redis_client.py (269 LOC) - Async Redis
  ✅ lib/fulltext/cache_db.py - Full-text cache
  ✅ lib/fulltext/parsed_cache.py - Parsed PDF cache
  ✅ lib/fulltext/smart_cache.py - Smart caching

Embeddings (UNUSED):
  ❌ lib/embeddings/service.py (278 LOC) - Only in test_semantic_search.py
  ❌ lib/embeddings/models.py

Vector DB (UNUSED):
  ❌ lib/vector_db/faiss_db.py (213 LOC) - Only in test_semantic_search.py
  ❌ lib/vector_db/chroma_db.py (252 LOC)
  ❌ lib/vector_db/interface.py

Storage (UNUSED):
  ❌ lib/storage/dataset_storage.py (295 LOC) - Not imported
  ❌ lib/storage/publication_storage.py (242 LOC) - Not imported
```

---

## Files to Archive (NOT Used in Production)

### 1. Embeddings Module (278 LOC)
```
Files:
  - lib/embeddings/service.py (278 LOC)
  - lib/embeddings/models.py

Usage: Only in scripts/test_semantic_search.py
Reason: Not used in production flow
Action: Move to extras/semantic-search-poc/embeddings/
```

### 2. Vector Database (465 LOC)
```
Files:
  - lib/vector_db/faiss_db.py (213 LOC)
  - lib/vector_db/chroma_db.py (252 LOC)
  - lib/vector_db/interface.py

Usage: Only in scripts/test_semantic_search.py
Reason: Not used in production flow
Action: Move to extras/semantic-search-poc/vector_db/
```

### 3. Storage Module (537 LOC)
```
Files:
  - lib/storage/dataset_storage.py (295 LOC)
  - lib/storage/publication_storage.py (242 LOC)

Usage: Not imported anywhere
Reason: Data not persisted to database in production
Action: Move to extras/database-persistence/storage/
```

### 4. Async PubMed Client (354 LOC)
```
File:
  - lib/publications/clients/async_pubmed.py (354 LOC)

Usage: Not imported anywhere
Reason: Sync PubMedClient is used instead
Action: Move to extras/async-clients/async_pubmed.py
```

**Total to Archive: 1,634 LOC**

---

## Critical Issue: Duplicate PDF Downloaders

### TWO PDF Downloaders Found:

**1. Currently Used:**
```python
# lib/storage/pdf/download_manager.py
# Imported in api/routes/agents.py line 350
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

pdf_downloader = PDFDownloadManager(
    output_dir=Path("data/fulltext/pdfs"),
    max_concurrent=3
)
```

**2. Alternative Implementation:**
```python
# lib/fulltext/pdf_downloader.py (447 LOC)
# ❓ Status: Need to verify if imported anywhere
```

### Investigation Needed:
1. Check if `lib/fulltext/pdf_downloader.py` is imported anywhere
2. If not, archive it
3. If yes, determine which is better and consolidate

---

## Reorganization Plan (By Flow Stage)

### Current Structure (Confusing)
```
lib/
├── geo/                    # GEO search (Stage 5a)
├── publications/           # Mixed: Search (5b) + URL sources (6)
├── citations/              # Citation search (Stage 5b)
├── fulltext/               # Mixed: URL discovery (6) + parsing (8)
├── storage/                # PDF download (7) + unused storage
├── search/                 # Orchestration (Stage 4)
├── query/                  # Query processing (Stage 3)
├── nlp/                    # Query processing (Stage 3)
├── ai/                     # AI analysis (Stage 9)
├── cache/                  # Infrastructure
├── embeddings/             # ❌ UNUSED
├── vector_db/              # ❌ UNUSED
```

### Proposed Structure (Clear Flow)
```
lib/
├── query_processing/       # Stage 3
│   ├── nlp/               # biomedical_ner, query_expander, synonyms
│   └── optimization/       # analyzer, optimizer
│
├── search/                 # Stage 4
│   ├── orchestrator.py    # Coordination only
│   ├── config.py
│   └── models.py
│
├── search_engines/         # Stage 5
│   ├── geo/               # Stage 5a: PRIMARY search
│   │   ├── client.py      # NCBI GEO API
│   │   ├── query_builder.py
│   │   ├── models.py
│   │   ├── utils.py
│   │   └── cache.py
│   │
│   └── citations/          # Stage 5b: Citation search
│       ├── pubmed.py       # PubMed search
│       ├── openalex.py     # OpenAlex search
│       ├── scholar.py      # Google Scholar
│       ├── semantic_scholar.py
│       ├── base.py         # Base class
│       ├── models.py       # Publication models
│       └── config.py
│
├── enrichment/             # Stages 6-8 (Full-text pipeline)
│   └── fulltext/
│       ├── manager.py      # Stage 6: URL discovery orchestrator
│       ├── downloader.py   # Stage 7: PDF download (CONSOLIDATED)
│       ├── parser.py       # Stage 8: Text extraction
│       ├── normalizer.py   # Text normalization
│       ├── models.py       # Data models
│       │
│       ├── caching/        # Full-text caching
│       │   ├── cache_db.py
│       │   ├── parsed_cache.py
│       │   └── smart_cache.py
│       │
│       └── sources/        # All 11 URL sources
│           ├── free/       # Official free sources
│           │   └── pmc_doaj_europmc.py (from oa_sources.py)
│           │
│           ├── aggregators/ # Legal aggregators
│           │   ├── unpaywall.py
│           │   ├── base.py
│           │   └── core.py (from oa_sources.py)
│           │
│           ├── institutional/
│           │   └── access.py (from institutional_access.py)
│           │
│           ├── academic/    # Academic search engines
│           │   ├── openalex.py (link from citations/)
│           │   └── semantic_scholar.py (link from citations/)
│           │
│           └── fallback/    # Last resort (pirates)
│               ├── scihub.py
│               └── libgen.py
│
├── analysis/               # Stage 9
│   └── ai/
│       ├── client.py       # LLM client
│       ├── prompts.py      # Prompt engineering
│       ├── models.py       # Request/response models
│       └── config.py
│
└── infrastructure/         # Cross-cutting
    └── cache/              # Redis caching
        ├── redis_cache.py
        └── redis_client.py
```

### Archive Structure (Unused Code)
```
extras/
├── semantic-search-poc/    # Unused semantic search
│   ├── embeddings/
│   │   ├── service.py
│   │   └── models.py
│   └── vector_db/
│       ├── faiss_db.py
│       ├── chroma_db.py
│       └── interface.py
│
├── database-persistence/   # Unused database storage
│   └── storage/
│       ├── dataset_storage.py
│       └── publication_storage.py
│
└── async-clients/          # Unused async implementations
    └── async_pubmed.py
```

---

## File Consolidation Tasks

### Task 1: Resolve PDF Downloader Duplication
```bash
# Check if fulltext/pdf_downloader.py is used
grep -r "pdf_downloader" omics_oracle_v2/

# If not used:
git mv omics_oracle_v2/lib/fulltext/pdf_downloader.py \
       extras/duplicate-downloaders/pdf_downloader_v2.py

# If used, compare implementations and merge
```

### Task 2: Consolidate Full-text Sources
```bash
# Create organized structure
mkdir -p omics_oracle_v2/lib/enrichment/fulltext/sources/{free,aggregators,institutional,academic,fallback}

# Move files
git mv omics_oracle_v2/lib/fulltext/sources/scihub_client.py \
       omics_oracle_v2/lib/enrichment/fulltext/sources/fallback/scihub.py

git mv omics_oracle_v2/lib/fulltext/sources/libgen_client.py \
       omics_oracle_v2/lib/enrichment/fulltext/sources/fallback/libgen.py

git mv omics_oracle_v2/lib/fulltext/sources/unpaywall_client.py \
       omics_oracle_v2/lib/enrichment/fulltext/sources/aggregators/unpaywall.py

# Split oa_sources.py into logical groups
# PMC, DOAJ, Europe PMC → free/
# BASE, CORE → aggregators/
```

### Task 3: Archive Unused Modules
```bash
# Create archive directories
mkdir -p extras/semantic-search-poc/{embeddings,vector_db}
mkdir -p extras/database-persistence/storage
mkdir -p extras/async-clients

# Move embeddings
git mv omics_oracle_v2/lib/embeddings/* extras/semantic-search-poc/embeddings/

# Move vector_db
git mv omics_oracle_v2/lib/vector_db/* extras/semantic-search-poc/vector_db/

# Move storage (keep pdf/ subfolder)
git mv omics_oracle_v2/lib/storage/dataset_storage.py extras/database-persistence/storage/
git mv omics_oracle_v2/lib/storage/publication_storage.py extras/database-persistence/storage/

# Move async_pubmed
git mv omics_oracle_v2/lib/publications/clients/async_pubmed.py extras/async-clients/

# Commit
git commit -m "Archive unused modules (1,634 LOC): embeddings, vector_db, storage, async_pubmed"
```

### Task 4: Reorganize by Flow Stage
```bash
# Create new structure
mkdir -p omics_oracle_v2/lib/{query_processing,search_engines,enrichment,analysis}

# Move query processing
mkdir -p omics_oracle_v2/lib/query_processing/{nlp,optimization}
git mv omics_oracle_v2/lib/nlp/* omics_oracle_v2/lib/query_processing/nlp/
git mv omics_oracle_v2/lib/query/* omics_oracle_v2/lib/query_processing/optimization/

# Move search engines
mkdir -p omics_oracle_v2/lib/search_engines/{geo,citations}
git mv omics_oracle_v2/lib/geo/* omics_oracle_v2/lib/search_engines/geo/
git mv omics_oracle_v2/lib/publications/clients/pubmed.py omics_oracle_v2/lib/search_engines/citations/
git mv omics_oracle_v2/lib/citations/clients/* omics_oracle_v2/lib/search_engines/citations/
git mv omics_oracle_v2/lib/publications/models.py omics_oracle_v2/lib/search_engines/citations/

# Move enrichment
mkdir -p omics_oracle_v2/lib/enrichment/fulltext
git mv omics_oracle_v2/lib/fulltext/* omics_oracle_v2/lib/enrichment/fulltext/
git mv omics_oracle_v2/lib/storage/pdf/* omics_oracle_v2/lib/enrichment/fulltext/

# Move AI analysis
git mv omics_oracle_v2/lib/ai omics_oracle_v2/lib/analysis/ai

# Update all imports
# ... (use find/replace or script)

# Commit
git commit -m "Reorganize by flow stage: query_processing, search_engines, enrichment, analysis"
```

---

## Summary of Changes

### Archival (Phase 1)
- ✅ Archive 1,634 LOC of unused code
  - Embeddings: 278 LOC
  - Vector DB: 465 LOC
  - Storage: 537 LOC
  - Async PubMed: 354 LOC

### Consolidation (Phase 2)
- 🔄 Resolve PDF downloader duplication
- 🔄 Consolidate 11 full-text sources into organized structure
- 🔄 Move oa_sources.py logic to specific categories

### Reorganization (Phase 3)
- 🔄 Restructure by flow stage (not abstract layers)
- 🔄 Clear separation: query → search → enrich → analyze
- 🔄 Update all imports to match new structure

### Expected Results
- **Code reduction:** 1,634 LOC archived (additional 5.7% reduction)
- **Clarity:** Directory structure matches user flow
- **Maintainability:** Related files grouped together
- **Discoverability:** Easy to find files by stage

---

## Verification Commands

```bash
# Check embeddings usage
grep -r "from.*embeddings" omics_oracle_v2/ --include="*.py" | grep -v "__pycache__"

# Check vector_db usage
grep -r "from.*vector_db" omics_oracle_v2/ --include="*.py" | grep -v "__pycache__"

# Check storage usage
grep -r "from.*storage.*dataset|from.*storage.*publication" omics_oracle_v2/ --include="*.py"

# Check async_pubmed usage
grep -r "AsyncPubMedClient|async_pubmed" omics_oracle_v2/ --include="*.py"

# Check PDF downloader status
grep -r "pdf_downloader|PDFDownloadManager" omics_oracle_v2/ --include="*.py"

# Verify all imports work
python -m omics_oracle_v2.api.main --help
```

---

## Next Steps

**Ready to execute:**

1. ✅ **Verify PDF downloader status** - Determine which implementation is active
2. ✅ **Archive unused modules** - Move embeddings, vector_db, storage, async_pubmed
3. ✅ **Consolidate full-text sources** - Organize 11 sources into logical groups
4. ✅ **Reorganize by flow** - Match directory structure to user journey
5. ✅ **Update imports** - Fix all import paths
6. ✅ **Test thoroughly** - Ensure production flow still works

**Total cleanup impact:**
- Previous: 11,876 LOC archived (Phase 1)
- This phase: 1,634 LOC to archive
- **Grand total: 13,510 LOC archived (43% reduction from original 31K LOC)**

Would you like to proceed with Phase 2 cleanup?
