# API Routes Refactoring - Service Layer Extraction

**Date:** October 15, 2025  
**Objective:** Extract business logic from `api/routes/agents.py` to service layer

---

## Summary

**Status:** Phase 1 Complete ✅  
**LOC Reduction:** 368 LOC (1,817 → 1,449)  
**Architecture Discovery:** Found major duplication between agents.py and PipelineCoordinator

---

## Phase 1: /search Endpoint ✅

**Completed:** `/search` endpoint refactored to use service layer

### Changes:
- **Created:** `services/search_service.py` (425 LOC)
  - `SearchService` class with clean separation of concerns
  - Methods: `execute_search()`, `_build_query()`, `_rank_datasets()`, etc.
  - Extracted all business logic from route handler

- **Updated:** `api/routes/agents.py`
  - Reduced from 1,817 → 1,449 LOC (368 LOC extracted)
  - Route handler now thin controller (~35 LOC)
  - Clean pattern: Route → Service → Response

### Benefits:
- ✅ Business logic testable in isolation
- ✅ Route handler is minimal (request validation + error handling)
- ✅ Service can be reused by other endpoints
- ✅ Clear separation of concerns

---

## Architecture Discovery: Pipeline Duplication 🔍

### Finding:
**`api/routes/agents.py` duplicates `lib/pipelines/coordinator.py` functionality**

### Evidence:

**PipelineCoordinator (536 LOC):**
- `save_citation_discovery()` - P1: Citation Discovery
- `save_url_discovery()` - P2: URL Collection
- `save_pdf_acquisition()` - P3: PDF Download
- `save_content_extraction()` - P4: Content Extraction
- `save_enriched_content()` - P4: Enrichment

**agents.py /enrich-fulltext endpoint (906 LOC):**
- Manually imports individual pipeline components
- Reimplements P1→P2→P3→P4 orchestration
- Duplicates database persistence logic
- Does NOT use PipelineCoordinator

### Current Architecture:

```
✅ CORRECT (/search):
Frontend → API /search → SearchService → SearchOrchestrator → PipelineCoordinator

❌ WRONG (/enrich-fulltext):
Frontend → API /enrich-fulltext → [manual pipeline orchestration] → [scattered DB calls]
```

### Root Cause:
- SearchOrchestrator uses PipelineCoordinator ✅
- enrich-fulltext endpoint bypasses it ❌
- Result: ~800 LOC of duplicated coordination logic

---

## Phase 2: /enrich-fulltext Endpoint (Pending)

**Status:** Service skeleton created, needs full implementation

### Current State:
- **File:** `services/fulltext_service.py` (275 LOC)
- **Status:** Partial implementation with method stubs
- **Challenge:** Endpoint has complex frontend-specific requirements:
  - Paper type organization (original vs citing)
  - Comprehensive metadata.json generation
  - Frontend-specific response formatting
  - Graceful partial failure handling

### Recommendation:
**Option A: Proper Refactoring (Recommended)**
1. Complete `FullTextEnrichmentService` implementation
2. Refactor to use PipelineCoordinator for database operations
3. Keep frontend-specific logic in service layer
4. **Result:** ~800 LOC reduction by eliminating duplication

**Option B: Quick Extract (Current)**
1. Extract existing logic as-is to service
2. Keep pipeline duplication for now
3. File TODO for coordinator integration
4. **Result:** ~400 LOC reduction, duplication remains

### Next Steps:
- [ ] Complete `_gather_papers()` implementation
- [ ] Complete `_download_pdfs()` implementation  
- [ ] Complete `_parse_and_attach_content()` implementation
- [ ] Add PipelineCoordinator integration for P1→P4
- [ ] Update route to use service

---

## Phase 3: /analyze Endpoint (Not Started)

**Size:** 406 LOC  
**Status:** Not started  
**Plan:** Extract SummarizationClient logic to `services/analysis_service.py`

---

## Phase 4: /complete-geo-data Endpoint (Not Started)

**Size:** 55 LOC  
**Status:** Not started  
**Assessment:** Small enough, may not need extraction

---

## Metrics

### Before Refactoring:
```
api/routes/agents.py: 1,817 LOC
services/: 9 LOC (empty)
Total: 1,826 LOC
```

### After Phase 1:
```
api/routes/agents.py: 1,449 LOC (-368)
services/search_service.py: 425 LOC (new)
services/fulltext_service.py: 275 LOC (new, partial)
services/__init__.py: 9 LOC
Total: 2,158 LOC (+332 for service layer, but with better architecture)
```

### Target After All Phases:
```
api/routes/agents.py: ~400 LOC (thin controllers only)
services/: ~1,200 LOC (business logic)
Net reduction: ~600 LOC by eliminating duplication
Architecture: Clean service layer + pipeline integration
```

---

## Cumulative Cleanup Progress

1. **lib/ folder cleanup:** 3,867 LOC
2. **Folder investigations:** 808 LOC (tracing, debug, config)
3. **agents/ folder deletion:** 1,220 LOC
4. **SearchService extraction:** 368 LOC reduction in routes

**Total Eliminated:** 6,263 LOC  
**Architecture Improvements:** Service layer pattern, pipeline integration identified

---

## Recommendations

### Immediate (This Commit):
1. ✅ Commit SearchService extraction
2. ✅ Document pipeline duplication finding
3. ✅ Create service skeleton for fulltext

### Short-term (Next Session):
1. Complete FullTextEnrichmentService with PipelineCoordinator integration
2. Extract AnalysisService for /analyze endpoint
3. Review /complete-geo-data (may not need extraction)

### Long-term:
1. Standardize all API endpoints to use service layer
2. Eliminate pipeline duplication across codebase
3. Add comprehensive service layer tests
4. Document service layer patterns in architecture guide

---

## Files Changed

### New Files:
- `omics_oracle_v2/services/search_service.py` (425 LOC)
- `omics_oracle_v2/services/fulltext_service.py` (275 LOC, partial)
- `docs/API_ROUTES_REFACTORING.md` (this file)

### Modified Files:
- `omics_oracle_v2/api/routes/agents.py` (1,817 → 1,449 LOC)

### Total Change:
- Lines added: 700 (services)
- Lines removed: 368 (routes)
- Net: +332 LOC (better architecture, clearer separation)

---

## Phase 2: /analyze Endpoint ✅

**Completed:** `/analyze` endpoint refactored to use service layer

### Changes:
- **Created:** `services/analysis_service.py` (544 LOC)
  - `AnalysisService` class with complete business logic
  - Methods:
    - `analyze_datasets()` - Main entry point
    - `_check_content_availability()` - Validates fulltext exists
    - `_build_no_content_response()` - Helpful blocking response
    - `_build_dataset_summaries()` - Comprehensive summaries with fulltext
    - `_load_paper_content()` - Retrieves from ParsedCache
    - `_build_analysis_prompt()` - LLM prompt construction
    - `_call_llm()` - OpenAI API integration
    - `_parse_analysis_results()` - Extract insights/recommendations

- **Updated:** `api/routes/agents.py`
  - Reduced from 1,449 → 1,081 LOC (368 LOC extracted)
  - Route handler now thin controller (~38 LOC)
  - Total extraction: 736 LOC (Phases 1+2)

### Benefits:
- ✅ Complex AI analysis logic isolated and testable
- ✅ Paper prioritization logic reusable
- ✅ LLM integration cleanly separated
- ✅ Content validation logic extracted

---

## Cumulative Metrics

| Phase | LOC Removed | File Size |
|-------|-------------|-----------|
| **Start** | - | 1,817 LOC |
| Phase 1 (SearchService) | -368 | 1,449 LOC |
| Phase 2 (AnalysisService) | -368 | **1,081 LOC** |
| **Total Extracted** | **-736** | **40% reduction** |

### Service Layer Created:
- `search_service.py`: 425 LOC
- `analysis_service.py`: 544 LOC
- `fulltext_service.py`: 275 LOC (skeleton)
- **Total Service Layer:** 1,244 LOC

### Cumulative Cleanup Across Project:
| Phase | Description | LOC |
|-------|-------------|-----|
| 1 | lib/ folder cleanup | 3,867 |
| 2 | Folder investigations | 808 |
| 3 | agents/ deletion | 1,220 |
| 4 | SearchService extraction | 368 |
| 5 | AnalysisService extraction | 368 |
| **Total** | | **6,631** |

---

## Next Steps

1. ✅ Phase 1: SearchService - **COMPLETE**
2. ✅ Phase 2: AnalysisService - **COMPLETE**
3. ❌ Review `/complete-geo-data` endpoint (~55 LOC)
4. ❌ Phase 3: Complete FulltextService with PipelineCoordinator integration (~906 LOC)
5. ❌ Investigate `tests/` folder for cleanup opportunities


---

## Phase 3: /complete-geo-data Endpoint Review ✅

**Completed:** Reviewed endpoint - **NO EXTRACTION NEEDED**

### Assessment:
- **Size:** 57 LOC (well within thin controller guidelines)
- **Complexity:** Low - simple registry lookup
- **Pattern:** Already follows best practices

### Why No Extraction:
✅ Single responsibility (registry.get_complete_geo_data())  
✅ No complex business logic  
✅ Proper error handling  
✅ Clean logging  
✅ Direct response (no transformation)  

**Conclusion:** This endpoint is already a good example of what a thin controller should look like after refactoring.

---

## Remaining Work

### agents.py Status:
- **Current:** 1,081 LOC
- **Endpoints:**
  - ✅ `/search` - 35 LOC (thin controller)
  - ✅ `/analyze` - 38 LOC (thin controller)
  - ✅ `/complete-geo-data` - 57 LOC (already thin, no extraction needed)
  - ❌ `/enrich-fulltext` - ~906 LOC (MAJOR REFACTORING NEEDED)

### Next Priority: /enrich-fulltext Architecture Fix

**Problem:** Duplicates PipelineCoordinator (~800 LOC duplication)

**Required Work:**
1. Complete `FulltextService` implementation
2. Integrate with PipelineCoordinator (eliminate duplication)
3. Maintain frontend-specific response formatting
4. **Impact:** ~800 LOC reduction + proper architecture

**Estimated Result:**
- agents.py: 1,081 → ~300 LOC (mostly enrich-fulltext reduction)
- Proper use of existing pipeline infrastructure
- Elimination of duplicate database operations

