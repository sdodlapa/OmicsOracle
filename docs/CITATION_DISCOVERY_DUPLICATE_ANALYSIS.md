# Citation Discovery Pipeline - Duplicate Analysis

**Date**: October 14, 2025  
**Question**: Is citation discovery in `lib/pipelines/` being used, or is it also unused like `citation_url_collection`?

---

## 🎯 Answer: YES, IT'S BEING USED! ✅

**The API uses**: `omics_oracle_v2/lib/pipelines/citation_discovery/`  
**Status**: ✅ ACTIVE, PRODUCTION CODE

---

## 📊 Evidence

### 1. API Import (Line 24 in agents.py)

```python
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
```

**Verdict**: ✅ API actively uses `lib/pipelines/citation_discovery/`

---

### 2. BUT There's ALSO an Older Version! ⚠️

**Two locations exist**:

1. **`omics_oracle_v2/lib/pipelines/citation_discovery/`** ← API uses THIS ✅
   - 829 lines in `geo_discovery.py`
   - Last updated: Oct 14, 2025 (Phase 10 - Metrics Logging)
   - Has advanced features: quality validation, metrics, caching, etc.
   - **12 files total** (complete implementation)

2. **`omics_oracle_v2/lib/citations/discovery/`** ← OLDER VERSION ⚠️
   - 173 lines in `geo_discovery.py` (basic version)
   - Last updated: Sept 2025 (Phase 2B reorganization)
   - Only 1 file (minimal implementation)
   - **Used by**: `extras/pipelines/` and some old examples

---

## 🔍 Detailed Comparison

| Aspect | `lib/pipelines/citation_discovery/` | `lib/citations/discovery/` |
|--------|-----------------------------------|---------------------------|
| **Status** | ✅ ACTIVE (API uses this) | ⚠️ OLD (not used by API) |
| **Size** | 829 lines | 173 lines |
| **Files** | 12 files (complete) | 1 file (minimal) |
| **Features** | Quality validation, metrics, caching, deduplication | Basic discovery only |
| **Last Update** | Oct 14, 2025 (Phase 10) | Sept 2025 (Phase 2B) |
| **Used By** | API, production code | extras/, examples/ |
| **Imports** | 20+ matches (API + tests) | 20+ matches (extras + docs) |

---

## 📁 File Structure Comparison

### `lib/pipelines/citation_discovery/` (ACTIVE ✅)
```
citation_discovery/
├── README.md
├── __init__.py
├── geo_discovery.py           # 829 lines - FULL IMPLEMENTATION
├── cache.py                   # Caching logic
├── deduplication.py           # Smart deduplication
├── error_handling.py          # Error handling
├── metrics_logger.py          # Phase 10 - Metrics
├── quality_validation.py      # Phase 9 - Quality checks
├── relevance_scoring.py       # Relevance scoring
├── source_metrics.py          # Source performance tracking
└── clients/                   # API clients
    ├── __init__.py
    ├── config.py
    ├── openalex.py
    ├── pubmed.py
    ├── semantic_scholar.py
    ├── europepmc.py
    └── opencitations.py
```

**Total**: ~12 files, comprehensive implementation

---

### `lib/citations/discovery/` (OLD ⚠️)
```
discovery/
├── __init__.py
└── geo_discovery.py           # 173 lines - BASIC VERSION ONLY
```

**Total**: 1 file, minimal implementation

---

## 🚨 Key Finding: This is NOT the Same as `citation_url_collection`

### `citation_url_collection` (CORRECTLY DELETED)
- ❌ 100% duplicate of `enrichment/fulltext/`
- ❌ Never used by API
- ❌ Exact same code in two places
- ✅ **Correctly deleted** in Phase 1 cleanup

### `citations/discovery/` (DIFFERENT SITUATION)
- ⚠️ NOT a duplicate - it's an OLDER VERSION
- ⚠️ Not used by API (API uses `pipelines/` version)
- ⚠️ Used by some extras/ and examples/
- ❓ **Should be deprecated/archived**, not deleted immediately

---

## 📊 What's Using Each Version?

### `lib/pipelines/citation_discovery/` (Current/Active)

**API** (PRODUCTION):
- ✅ `omics_oracle_v2/api/routes/agents.py` line 24

**Tests**:
- ✅ `tests/test_pipeline_1_2_integration.py`
- ✅ `tests/validation/test_week4_features.py`

**Core Library**:
- ✅ `omics_oracle_v2/lib/pipelines/__init__.py`

---

### `lib/citations/discovery/` (Old/Deprecated)

**Extras** (NON-PRODUCTION):
- ⚠️ `extras/pipelines/geo_citation_pipeline.py`
- ⚠️ `extras/pipelines/publication_pipeline.py`

**Examples**:
- ⚠️ `examples/geo_citation_tracking.py`
- ⚠️ `examples/validation/citation-fixes.py`
- ⚠️ `examples/sprint-demos/openalex-integration.py`

**Old Tests**:
- ⚠️ `tests/validation/test_unified_pipeline_validation.py`

---

## 💡 Why Two Versions Exist?

### Timeline:

1. **Sept 2025 (Phase 2B)**: Reorganization moved citations to `lib/citations/discovery/`
   - Created basic 173-line version
   - Moved search engines to `search_engines/citations/`

2. **Oct 2025 (Phases 7-10)**: Major enhancements in `lib/pipelines/citation_discovery/`
   - Added Europe PMC (Phase 6)
   - Added Crossref (Phase 7)
   - Added Quality Validation (Phase 9)
   - Added Metrics Logging (Phase 10)
   - Grew from 173 to 829 lines

3. **Result**: Two versions diverged
   - Old version (173 lines) stayed in `lib/citations/discovery/`
   - New version (829 lines) evolved in `lib/pipelines/citation_discovery/`

---

## 🎯 Recommendation

### Option 1: Deprecate Old Version (RECOMMENDED) ✅

1. **Update `extras/pipelines/`** to use new version:
   ```python
   # Change from:
   from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
   
   # To:
   from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
   ```

2. **Update examples/** to use new version

3. **Archive old version**:
   ```bash
   mv omics_oracle_v2/lib/citations/discovery/ \
      omics_oracle_v2/lib/archive/deprecated_20251014/citations_discovery/
   ```

4. **Add deprecation notice** in old `__init__.py`

---

### Option 2: Keep Both (NOT RECOMMENDED) ❌

**Problems**:
- Confusing for developers
- Bug fixes must be applied twice
- Old version missing 656 lines of features
- Maintenance burden

---

## ✅ Summary

| Question | Answer |
|----------|--------|
| Is `lib/pipelines/citation_discovery/` used? | ✅ YES - API uses it |
| Is it a duplicate like `citation_url_collection`? | ❌ NO - it's the ACTIVE version |
| Should we delete it? | ❌ NO - it's PRODUCTION CODE |
| Is `lib/citations/discovery/` a duplicate? | ⚠️ It's an OLD VERSION (173 vs 829 lines) |
| Should we delete `lib/citations/discovery/`? | ⚠️ Deprecate/archive, don't delete yet (used by extras/) |

---

## 🚀 Action Items

### Immediate (This Week):

1. ✅ **Keep** `lib/pipelines/citation_discovery/` (ACTIVE, PRODUCTION)
2. ⚠️ **Update** `extras/pipelines/` to use new version
3. ⚠️ **Update** `examples/` to use new version
4. ⚠️ **Deprecate** `lib/citations/discovery/` (add notice)

### Future (Next Sprint):

1. Archive old `lib/citations/discovery/` after updating all references
2. Remove old version completely
3. Update documentation

---

## 📝 Corrected Pipeline Location Map

```
✅ CORRECT STRUCTURE:

omics_oracle_v2/lib/
├── pipelines/
│   ├── citation_discovery/         # Pipeline 1 ✅ ACTIVE (829 lines)
│   │   ├── geo_discovery.py        # Full implementation
│   │   ├── clients/                # 5 API clients
│   │   ├── quality_validation.py   # Phase 9
│   │   ├── metrics_logger.py       # Phase 10
│   │   └── ... (12 files total)
│   │
│   └── citation_download/          # ⚠️ DUPLICATE of Pipeline 3 (delete?)
│
├── citations/
│   └── discovery/                  # ⚠️ OLD VERSION (173 lines, deprecate)
│       └── geo_discovery.py        # Basic implementation
│
└── enrichment/fulltext/
    ├── manager.py                  # Pipeline 2 ✅ ACTIVE
    ├── download_manager.py         # Pipeline 3 ✅ ACTIVE
    └── pdf_parser.py               # Pipeline 4 (incomplete)
```

**Status**:
- ✅ Pipeline 1 ACTIVE in `lib/pipelines/citation_discovery/` (API uses this)
- ⚠️ Pipeline 1 OLD in `lib/citations/discovery/` (used by extras/, should deprecate)
- ✅ Pipeline 2 ACTIVE in `lib/enrichment/fulltext/manager.py`
- ⚠️ Pipeline 3 DUPLICATE - `lib/pipelines/citation_download/` vs `lib/enrichment/fulltext/download_manager.py`
- ⚠️ Pipeline 4 INCOMPLETE in `lib/enrichment/fulltext/pdf_parser.py`
