# /enrich-fulltext Refactoring Plan

**Date:** October 15, 2025  
**Objective:** Refactor /enrich-fulltext endpoint to use PipelineCoordinator (eliminate ~800 LOC duplication)

---

## Problem Analysis

### Current State

**/enrich-fulltext endpoint** (906 LOC):
- Lines 118-1024 in agents.py
- Manually orchestrates P1→P2→P3→P4 pipeline
- Duplicates PipelineCoordinator functionality
- Complex frontend-specific response formatting
- Comprehensive metadata generation

### Architecture Issue

**Duplication:**
```python
# Current /enrich-fulltext (WRONG):
1. Manual PubMed client initialization
2. Manual citation discovery
3. Manual URL collection (FullTextManager)
4. Manual PDF download orchestration
5. Manual content extraction
6. Manual database storage
7. Manual registry updates
8. Manual metadata.json generation

# PipelineCoordinator (CORRECT):
- save_citation_discovery()  # P1
- save_url_discovery()       # P2
- save_pdf_acquisition()     # P3
- save_content_extraction()  # P4
- Unified database operations
- GEO-centric file organization
```

**Result:** ~800 LOC of duplicated coordination logic

---

## Solution Strategy

### Option A: Full Coordinator Integration (Recommended)

**Approach:**
1. Complete `FulltextService` implementation
2. Use PipelineCoordinator for P1→P4 orchestration
3. Add frontend-specific response formatting in service
4. Keep metadata generation but simplify

**Benefits:**
- ~800 LOC reduction
- Proper architecture
- Reusable pipeline components
- Unified database operations

**Challenges:**
- Must maintain frontend compatibility
- metadata.json structure must match
- Response format must match exactly

### Option B: Hybrid Approach (Faster)

**Approach:**
1. Extract existing logic to service (as-is)
2. Document TODOs for coordinator integration
3. ~400 LOC reduction immediately
4. Phase 2: Integrate coordinator later

**Benefits:**
- Faster completion
- Less risk of breaking frontend
- Incremental improvement

**Challenges:**
- Still has duplication
- Architecture issue remains

---

## Decision: Option A (Full Integration)

**Rationale:**
- We've invested time in understanding both systems
- Proper fix now vs technical debt later
- ~800 LOC reduction justifies effort
- Final cleanup of major architecture issue

---

## Implementation Plan

### Phase 1: Analysis ✅

**Understand endpoint requirements:**
- ✅ Input: datasets, max_papers, include_citing_papers, etc.
- ✅ Output: enriched datasets with fulltext arrays
- ✅ Side effects: PDFs, metadata.json, registry updates
- ✅ Frontend dependencies: metadata structure, response format

### Phase 2: Service Structure (1 hour)

**Create FulltextService class:**

```python
class FulltextService:
    def __init__(self):
        self.coordinator = PipelineCoordinator()
        self.registry = get_registry()
        
    async def enrich_fulltext(
        self,
        datasets: List[DatasetResponse],
        max_papers: int,
        include_citing_papers: bool,
        max_citing_papers: int,
        download_original: bool,
        include_full_content: bool,
        settings
    ) -> List[DatasetResponse]:
        """Main entry point - orchestrate enrichment"""
        
    async def _process_dataset(self, dataset, ...):
        """Process single dataset through pipeline"""
        
    async def _discover_citations(self, dataset, ...):
        """P1: Citation discovery using coordinator"""
        
    async def _collect_urls(self, publications):
        """P2: URL collection using coordinator"""
        
    async def _download_pdfs(self, publications, output_dir):
        """P3: PDF download using coordinator"""
        
    async def _extract_content(self, publications):
        """P4: Content extraction using coordinator"""
        
    def _build_metadata(self, dataset, ...):
        """Build metadata.json (frontend-specific)"""
        
    def _build_response(self, dataset, ...):
        """Build API response (frontend-specific)"""
```

### Phase 3: Coordinator Integration (2-3 hours)

**Map endpoint logic to coordinator methods:**

| Endpoint Logic | Coordinator Method | Notes |
|---------------|-------------------|-------|
| PubMed metadata fetch | save_citation_discovery() | Pass citation_data |
| Citation discovery | save_citation_discovery() | For citing papers |
| URL collection | save_url_discovery() | Pass URL results |
| PDF download | save_pdf_acquisition() | Pass download results |
| Content extraction | save_content_extraction() | Pass parsed content |

**Key Integration Points:**

1. **P1 - Citation Discovery:**
   ```python
   # Instead of manual PubMedClient calls:
   coordinator.save_citation_discovery(
       geo_id=dataset.geo_id,
       pmid=pmid,
       citation_data={
           "title": pub.title,
           "authors": pub.authors,
           "doi": pub.doi,
           ...
       }
   )
   ```

2. **P2 - URL Discovery:**
   ```python
   # Instead of manual FullTextManager:
   url_results = await fulltext_manager.get_fulltext_batch(publications)
   coordinator.save_url_discovery(
       geo_id=dataset.geo_id,
       pmid=pmid,
       urls=[...],
       source=result.source
   )
   ```

3. **P3 - PDF Acquisition:**
   ```python
   # Instead of manual PDFDownloadManager:
   result = await pdf_downloader.download_with_fallback(...)
   coordinator.save_pdf_acquisition(
       geo_id=dataset.geo_id,
       pmid=pmid,
       pdf_path=result.pdf_path,
       source=result.source,
       file_size=result.file_size
   )
   ```

4. **P4 - Content Extraction:**
   ```python
   # Instead of manual PDFExtractor:
   parsed_content = extractor.extract_text(...)
   coordinator.save_content_extraction(
       geo_id=dataset.geo_id,
       pmid=pmid,
       content=parsed_content,
       source_file=pdf_path
   )
   ```

### Phase 4: Frontend Compatibility (1 hour)

**Maintain exact response format:**

1. **Fulltext array structure:**
   ```python
   fulltext_info = {
       "pmid": ...,
       "doi": ...,
       "title": ...,
       "url": ...,
       "source": ...,
       "pdf_path": ...,
       "paper_type": "original" | "citing",
       "abstract": ...,
       "methods": ...,
       "results": ...,
       "discussion": ...,
       "has_abstract": bool,
       "has_methods": bool,
       ...
   }
   ```

2. **metadata.json structure:**
   ```python
   {
       "geo": {...},
       "processing": {...},
       "papers": {
           "original": {...},
           "citing": {...}
       },
       "statistics": {...},
       "status": {...},
       "citation_discovery": {...}
   }
   ```

3. **Dataset metrics:**
   - citation_count
   - pdf_count
   - completion_rate
   - fulltext_status

### Phase 5: Route Update (30 min)

**Convert to thin controller:**

```python
@router.post("/enrich-fulltext", response_model=List[DatasetResponse])
async def enrich_with_fulltext(request: FulltextRequest):
    """Thin controller - delegates to service"""
    try:
        from omics_oracle_v2.services.fulltext_service import FulltextService
        from omics_oracle_v2.api.dependencies import get_settings
        
        settings = get_settings()
        service = FulltextService()
        
        return await service.enrich_fulltext(
            datasets=request.datasets,
            max_papers=request.max_papers,
            include_citing_papers=request.include_citing_papers,
            max_citing_papers=request.max_citing_papers,
            download_original=request.download_original,
            include_full_content=request.include_full_content,
            settings=settings
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fulltext enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enrichment error: {str(e)}"
        )
```

### Phase 6: Testing (1 hour)

**Test scenarios:**
1. Original papers only
2. Citing papers only  
3. Both original and citing
4. Partial download failures
5. PDF parsing failures
6. Registry updates
7. metadata.json structure
8. Frontend compatibility

---

## Expected Results

### LOC Reduction

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| /enrich-fulltext endpoint | 906 LOC | ~50 LOC | -856 |
| FulltextService (new) | 0 | ~350 LOC | +350 |
| **Net Reduction** | | | **-506** |

**Additional Benefits:**
- Eliminates ~800 LOC duplication with coordinator
- Proper architecture (no manual orchestration)
- Reusable service layer
- Unified database operations

### agents.py Final State

- Before refactoring: 1,817 LOC
- After Phase 1 (Search): 1,449 LOC
- After Phase 2 (Analysis): 1,081 LOC
- **After Phase 3 (Fulltext): ~225 LOC** (mostly thin controllers)

---

## Risks & Mitigation

### Risk 1: Frontend Breaking Changes

**Mitigation:**
- Maintain exact response format
- Test metadata.json structure
- Verify all frontend expectations
- Incremental deployment

### Risk 2: Coordinator Incompatibility

**Mitigation:**
- Review coordinator interface thoroughly
- Add adapter methods if needed
- Maintain backward compatibility
- Document any differences

### Risk 3: Performance Regression

**Mitigation:**
- Profile critical paths
- Compare execution times
- Optimize coordinator calls
- Batch database operations

---

## Success Criteria

✅ All tests pass  
✅ Frontend works identically  
✅ metadata.json structure unchanged  
✅ Response format matches exactly  
✅ ~500+ LOC reduction achieved  
✅ No coordinator duplication  
✅ Proper error handling  
✅ Registry updates working  

---

## Timeline Estimate

| Phase | Time | Status |
|-------|------|--------|
| 1. Analysis | 1h | ✅ Complete |
| 2. Service Structure | 1h | ❌ Pending |
| 3. Coordinator Integration | 2-3h | ❌ Pending |
| 4. Frontend Compatibility | 1h | ❌ Pending |
| 5. Route Update | 30min | ❌ Pending |
| 6. Testing | 1h | ❌ Pending |
| **Total** | **6-7h** | **In Progress** |

---

## Next Steps

1. ❌ Implement FulltextService structure
2. ❌ Integrate P1 (citation discovery)
3. ❌ Integrate P2 (URL collection)
4. ❌ Integrate P3 (PDF download)
5. ❌ Integrate P4 (content extraction)
6. ❌ Build metadata generation
7. ❌ Update route to thin controller
8. ❌ Test and verify

---

## Notes

- This is the final major refactoring
- Most complex due to coordinator integration
- Highest LOC reduction potential (~800 LOC)
- Fixes last major architecture issue
- After this, all endpoints will be thin controllers
