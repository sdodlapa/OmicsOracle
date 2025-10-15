# Phase 2 Investigation Results

**Date:** October 15, 2025  
**Status:** 🔍 ANALYSIS COMPLETE → Ready for execution

---

## 📊 Investigation Summary

### **Merge Group 1: Infrastructure + Performance → NO MERGE** ❌

**Findings:**
- `infrastructure/` - Redis cache infrastructure (RedisCache, AsyncRedisCache)
- `performance/` - Application-level cache management (CacheManager, SearchOptimizer)
- **Different concerns:** Infrastructure vs. Application layer

**Usage:**
- infrastructure/cache: 17 imports (production code uses RedisCache directly)
- performance: 10 imports (only extras/ and tests use CacheManager)

**Decision:** **KEEP SEPARATE**
- infrastructure = low-level Redis connectivity
- performance = high-level application optimization
- Merging would violate separation of concerns

---

### **Merge Group 2: Search_Orchestration → Keep Separate** ⚠️

**Findings:**
- `search_orchestration/` - High-level search coordination (4 files)
  - orchestrator.py (27KB)
  - config.py, models.py
  - Used by production API: `api/routes/agents.py`

**Usage:**
- 13 imports, including production code
- Orchestrates multiple search engines
- **SearchOrchestrator DOES EXIST** (contradicts archived publications/ docs)

**Decision:** **KEEP SEPARATE**
- Active production component
- Clear responsibility: coordinates search across engines
- Used by API layer

---

### **Merge Group 3: Registry → Merge into Storage** ✅ **RECOMMENDED**

**Findings:**
- `registry/` - Only 2 files:
  - geo_registry.py (18KB) - GEO dataset registry
  - __init__.py
- Purpose: Centralized data storage for GEO datasets
  
**Usage:**
- 7 imports total
- 1 production import: `api/routes/agents.py`
- Semantic fit: Registry IS a form of storage

**Decision:** **MERGE registry/ → storage/**
- Both handle data persistence
- Registry is specialized storage
- Natural grouping

**Migration:**
```python
# Before
from omics_oracle_v2.lib.registry import GEORegistry, get_registry

# After
from omics_oracle_v2.lib.storage.registry import GEORegistry, get_registry
# OR keep backward compatibility in storage/__init__.py
```

---

### **Evaluate: LLM Module → Keep Separate** ✅

**Findings:**
- `llm/` - 4 files (async_client.py, client.py, prompts.py)
- **Active development:** Recent commits (Oct 2025)
  - d5d66f5: Archive unused semantic search
  - f9a8b57: Async LLM implementation
  - 29ce3d2: LLM validation testing
  - 8fd814f: Citation analysis

**Usage:**
- 20+ imports across codebase
- Production usage: `analysis/publications/qa_system.py`
- Core feature, not helper code

**Decision:** **KEEP SEPARATE**
- Growing module (new async features)
- Core business logic
- Clear domain separation from analysis

---

## 🚨 CRITICAL: Client Duplication Issue

### **Problem: Duplicate PubMed/OpenAlex Implementations**

**Two sets of citation clients exist:**

#### **Set A: `search_engines/citations/`**
```
├── pubmed.py       397 lines
├── openalex.py     525 lines
├── base.py         140 lines
├── config.py       423 lines
└── models.py       226 lines
```

#### **Set B: `pipelines/citation_discovery/clients/`**
```
├── pubmed.py       461 lines  ← DIFFERENT (64 lines more)
├── openalex.py     525 lines  ← SAME size
├── crossref.py     384 lines  ← EXTRA
├── europepmc.py    323 lines  ← EXTRA
├── opencitations.py 432 lines ← EXTRA
├── semantic_scholar.py 378 lines ← EXTRA
├── config.py       520 lines  ← DIFFERENT
```

### **Which is Used?**

**Production Code (`api/routes/agents.py`):**
```python
# Line 457: Uses search_engines version
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient

# Line 24: Uses pipelines version
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
```

**Both are used!** But GEOCitationDiscovery internally uses the clients from `pipelines/citation_discovery/clients/`.

### **Analysis:**

1. **pipelines version is RICHER:**
   - Has 4 additional clients (CrossRef, EuropePMC, OpenCitations, SemanticScholar)
   - PubMed implementation is 64 lines longer (more features?)
   - Actively used by GEOCitationDiscovery pipeline

2. **search_engines version is SIMPLER:**
   - Only PubMed + OpenAlex
   - Used directly in one place in API
   - Less feature-complete

### **Decision: CONSOLIDATE to `search_engines/citations/`** ✅

**Rationale:**
- **Domain-driven design:** Citation clients belong in search_engines, not pipelines
- **Pipelines should import from search_engines** (dependency inversion)
- **Location:** search_engines/citations/ is the canonical location

**Action Plan:**
1. Move 4 extra clients from pipelines → search_engines:
   - crossref.py
   - europepmc.py
   - opencitations.py
   - semantic_scholar.py

2. Compare PubMed implementations, merge best features into search_engines version

3. Update pipelines/citation_discovery/clients/ to re-export from search_engines:
   ```python
   # pipelines/citation_discovery/clients/__init__.py
   from omics_oracle_v2.lib.search_engines.citations import (
       PubMedClient,
       OpenAlexClient,
       CrossRefClient,
       # ...
   )
   ```

4. Eventually delete pipelines/citation_discovery/clients/ (after compatibility period)

---

## ✅ Phase 2 Execution Plan

### **Single Action: Merge registry/ → storage/**

**Step 1:** Create storage/registry/ subdirectory
```bash
mkdir -p omics_oracle_v2/lib/storage/registry
```

**Step 2:** Move registry files
```bash
mv omics_oracle_v2/lib/registry/geo_registry.py omics_oracle_v2/lib/storage/registry/
```

**Step 3:** Create storage/registry/__init__.py
```python
from omics_oracle_v2.lib.storage.registry.geo_registry import GEORegistry, get_registry
__all__ = ["GEORegistry", "get_registry"]
```

**Step 4:** Update storage/__init__.py for backward compatibility
```python
# Add to exports
from omics_oracle_v2.lib.storage.registry import GEORegistry, get_registry
```

**Step 5:** Update imports (7 files)
```bash
# api/routes/agents.py
# scripts/test_registry_url_types.py
# tests/test_geo_registry.py
# tests/test_registry_integration.py
```

**Step 6:** Delete old registry/
```bash
rm -rf omics_oracle_v2/lib/registry
```

---

## 📋 Final Package Structure (11 directories)

```
omics_oracle_v2/lib/
├── analysis/              11 files  ← Keep
├── infrastructure/         4 files  ← Keep (Redis cache)
├── llm/                    4 files  ← Keep (active development)
├── performance/            3 files  ← Keep (optimization layer)
├── pipelines/             54 files  ← Keep (main orchestration)
├── query_processing/      10 files  ← Keep
├── search_engines/        11 files  ← Keep (will grow with merged clients)
├── search_orchestration/   4 files  ← Keep (production component)
├── storage/                9 files  ← Grows: +2 files from registry
└── utils/                  2 files  ← Keep (core utilities)
```

**Total:** 11 directories (down from 12)

---

## 🎯 Deferred Actions (Phase 3)

### **Client Consolidation** (High Priority)
- Merge 4 extra clients from pipelines → search_engines
- Reconcile PubMed/OpenAlex implementations
- Update all imports
- Delete pipelines/citation_discovery/clients/

**Impact:** Reduces duplication, clarifies architecture

### **Consider Future Merges** (Low Priority)
- Could merge infrastructure + performance IF clear abstraction layer created
- Monitor llm/ growth - may need to split into llm/{clients, prompts, analysis}

---

## ✅ Success Metrics

- [x] All small directories investigated
- [x] Duplication identified (PubMed/OpenAlex)
- [x] Merge candidates evaluated
- [ ] 1 merge executed (registry → storage)
- [ ] 7 import statements updated
- [ ] Zero broken production code
- [ ] Tests passing

**Estimated Reduction:**
- Directories: 12 → 11 (8% reduction)
- Combined Phase 1+2: 18 → 11 (39% reduction)

---

*Next: Execute registry → storage merge*
