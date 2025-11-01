# Pipeline 2 Cleanup Progress Tracker

**Date Started:** October 14, 2025  
**Status:** In Progress  
**Phase:** Phase 1 - High Priority Cleanup

---

## Discovered Additional Redundancy

### MAJOR FINDING: Duplicate Pipeline Directories ⚠️⚠️⚠️

**Location 1 (ACTIVE):**
```
omics_oracle_v2/lib/enrichment/fulltext/
├── manager.py (1,200 lines) - USED BY API
├── download_manager.py
├── sources/
│   ├── institutional_access.py
│   ├── scihub_client.py
│   ├── libgen_client.py
│   └── oa_sources/
```

**Location 2 (DUPLICATE/DEPRECATED):**
```
omics_oracle_v2/lib/pipelines/citation_url_collection/
├── manager.py - DUPLICATE
└── sources/
    └── institutional_access.py - DUPLICATE
```

**Verification:**
- ✅ API routes use: `from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager`
- ✅ Active location: `enrichment/fulltext/`
- ❌ Deprecated location: `pipelines/citation_url_collection/` (not imported)

**Action:** Delete entire `pipelines/citation_url_collection/` directory

---

## Cleanup Progress

### Phase 0: Remove Deprecated Directory (NEW - 10 minutes)

- [ ] **Step 0.1:** Verify no imports from `pipelines/citation_url_collection`
- [ ] **Step 0.2:** Delete `omics_oracle_v2/lib/pipelines/citation_url_collection/` directory
- [ ] **Step 0.3:** Update any references in documentation

**Expected Impact:**
- DELETE entire duplicate directory
- ~1,500+ lines of duplicate code removed
- Simplified architecture

---

### Phase 1: High-Priority Cleanup (4-6 hours)

#### Step 1.1: Remove Duplicate Unpaywall (50 lines)
- [ ] Remove `institutional_access.py::_try_unpaywall()` method (lines 222-271)
- [ ] Update calls to use manager's unpaywall instead
- [ ] Test institutional access still works

#### Step 1.2: Remove Duplicate PDF Downloads (145 lines)
- [ ] Remove `core_client.py::download_pdf()`
- [ ] Remove `biorxiv_client.py::download_pdf()`
- [ ] Remove `arxiv_client.py::download_pdf()`
- [ ] Verify all clients return URLs only
- [ ] Test download_manager handles all downloads

#### Step 1.3: Extract PMC Client (150 lines moved)
- [ ] Create `sources/oa_sources/pmc_client.py`
- [ ] Move logic from `manager.py::_try_pmc()` to new PMCClient
- [ ] Update manager to use PMCClient
- [ ] Test PMC source still works

#### Step 1.4: Standardize Error Handling
- [ ] Update all `_try_*` methods to return FullTextResult (not None)
- [ ] Ensure consistent error messages
- [ ] Update tests for new return pattern

---

### Phase 2: Medium-Priority Cleanup (2-4 hours)

#### Step 2.1: Create Shared PDF Utilities
- [ ] Create `utils/pdf_utils.py`
- [ ] Move PDF_MAGIC_BYTES constant
- [ ] Add validation functions
- [ ] Update download_manager to use utilities

#### Step 2.2: Standardize Configuration
- [ ] Convert institutional config to Pydantic
- [ ] Create PMCConfig class
- [ ] Update all configs to use Field descriptions

#### Step 2.3: Improve Logging
- [ ] Standardize log format: `[SOURCE] ✓/✗/⚠ Message`
- [ ] Update all source clients
- [ ] Add structured logging where needed

---

### Phase 3: Low-Priority Cleanup (1-2 hours)

#### Step 3.1: Review Convenience Functions
- [ ] Audit usage of convenience functions
- [ ] Add deprecation warnings or keep with docs
- [ ] Update documentation

#### Step 3.2: Documentation
- [ ] Update all docstrings
- [ ] Create migration guide
- [ ] Update architecture docs

---

## Test Validation Checkpoints

After each major change:
- [ ] Run relevant unit tests
- [ ] Test with real publication data
- [ ] Check API endpoints still work
- [ ] Verify no import errors

---

## Files Modified (Running List)

### Phase 0:
- [ ] DELETED: `omics_oracle_v2/lib/pipelines/citation_url_collection/` (entire directory)

### Phase 1:
- [ ] `enrichment/fulltext/sources/institutional_access.py` (removed _try_unpaywall)
- [ ] `enrichment/fulltext/sources/oa_sources/core_client.py` (removed download_pdf)
- [ ] `enrichment/fulltext/sources/oa_sources/biorxiv_client.py` (removed download_pdf)
- [ ] `enrichment/fulltext/sources/oa_sources/arxiv_client.py` (removed download_pdf)
- [ ] `enrichment/fulltext/sources/oa_sources/pmc_client.py` (NEW - created)
- [ ] `enrichment/fulltext/manager.py` (updated to use PMCClient)

### Phase 2:
- [ ] `utils/pdf_utils.py` (NEW - created)
- [ ] `enrichment/fulltext/download_manager.py` (use pdf_utils)
- [ ] All source configs (standardized to Pydantic)

---

## Phase 0 Complete ✅

### Completed:
- ✅ Discovered critical API import bug (using outdated GEOCitationDiscovery)
- ✅ Fixed API to use correct import path (pipelines/citation_discovery)
- ✅ Deleted duplicate directory: `citation_url_collection/` (~1,500 lines saved)
- ✅ Fixed `pipelines/__init__.py` to remove broken imports
- ✅ Verified API still works with corrected imports
- ✅ Created CRITICAL_FIX_API_IMPORTS.md documentation

### Impact:
- Production API now uses Phase 9-10 improvements (was using outdated code!)
- Removed ~1,500 lines of duplicate code
- Fixed 5-source discovery (was 2-source in production)

---

## Next: Starting Phase 1 - High Priority Cleanup
