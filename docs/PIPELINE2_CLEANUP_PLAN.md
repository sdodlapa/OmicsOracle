# Pipeline 2 (URL Collection) Cleanup Plan

**Date:** October 14, 2024  
**Status:** 🔄 In Progress  
**File:** `omics_oracle_v2/lib/pipelines/url_collection/manager.py`  
**Current Size:** 1,322 lines  
**Target Size:** ~400 lines  
**Lines to Remove:** ~900 lines

---

## 🎯 Objective

**Remove methods that don't belong in Pipeline 2 (URL Collection)**:
- Pipeline 2 should ONLY collect fulltext URLs from multiple sources
- Pipeline 3 (PDF Download) should handle actual downloading
- Pipeline 4 (Text Enrichment) should handle parsing

---

## 📊 Current State Analysis

### ✅ Methods to KEEP (URL Collection Only)

1. **`__init__`** - Initialization
2. **`initialize()`** - Setup sources
3. **`cleanup()`** - Cleanup resources
4. **`__aenter__`, `__aexit__`** - Context manager
5. **`_check_cache()`** - Check URL cache (not content cache!)
6. **`_try_institutional_access()`** - Get URLs from institutional access
7. **`_try_pmc()`** - Get URLs from PMC
8. **`_try_openalex_oa_url()`** - Get URLs from OpenAlex
9. **`_try_core()`** - Get URLs from CORE
10. **`_try_biorxiv()`** - Get URLs from bioRxiv
11. **`_try_arxiv()`** - Get URLs from arXiv
12. **`_try_crossref()`** - Get URLs from Crossref
13. **`_try_unpaywall()`** - Get URLs from Unpaywall
14. **`_try_scihub()`** - Get URLs from Sci-Hub
15. **`_try_libgen()`** - Get URLs from LibGen
16. **`get_all_fulltext_urls()`** - **PRIMARY METHOD** - Collect URLs from ALL sources
17. **`get_fulltext_batch()`** - Batch URL collection

**Total:** ~17 methods = ~400-500 lines

---

### ❌ Methods to REMOVE (Mixed Responsibilities)

1. **`get_parsed_content()`** (lines 882-1000, ~118 lines)
   - **Why remove:** This downloads PDFs AND parses them
   - **Belongs in:** Pipeline 4 (Text Enrichment)
   - **Replacement:** Users should call Pipeline 3 → Pipeline 4 directly
   - **Impact:** Breaking change, need deprecation warning

2. **`get_fulltext()`** (lines 1002-1093, ~91 lines)
   - **Why remove:** This downloads actual PDFs (waterfall strategy)
   - **Belongs in:** Pipeline 3 (PDF Download) should use collected URLs
   - **Replacement:** `get_all_fulltext_urls()` → Pipeline 3's `download_with_fallback()`
   - **Impact:** Breaking change, already deprecated in favor of `get_all_fulltext_urls()`

**Total to remove:** ~209 lines of mixed-responsibility code

---

## 🔄 Migration Strategy

### Phase 1: Mark as Deprecated (SAFE)

Add deprecation warnings to methods that will be removed:

```python
async def get_parsed_content(self, publication: Publication) -> Optional[Dict]:
    """
    DEPRECATED: Use Pipeline 3 + Pipeline 4 instead.
    
    This method violates single responsibility by:
    1. Downloading PDFs (Pipeline 3's job)
    2. Parsing content (Pipeline 4's job)
    
    Correct approach:
        # Pipeline 2: Collect URLs
        urls_result = await url_manager.get_all_fulltext_urls(publication)
        
        # Pipeline 3: Download PDF
        from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
        pdf_manager = PDFDownloadManager()
        pdf_path = await pdf_manager.download_with_fallback(
            publication, urls_result.all_urls, output_dir
        )
        
        # Pipeline 4: Parse content
        from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
        extractor = PDFExtractor(enable_enrichment=True)
        parsed = extractor.extract_text(pdf_path, metadata={...})
    
    Deprecated: October 14, 2025
    Will be removed in: v3.0.0
    """
    import warnings
    warnings.warn(
        "get_parsed_content() is deprecated. Use separate pipelines: "
        "get_all_fulltext_urls() → PDFDownloadManager → PDFExtractor",
        DeprecationWarning,
        stacklevel=2,
    )
    # Keep implementation for now
    ...


async def get_fulltext(self, publication: Publication, ...) -> FullTextResult:
    """
    DEPRECATED: Use get_all_fulltext_urls() + PDFDownloadManager instead.
    
    This method downloads PDFs which belongs in Pipeline 3.
    
    Correct approach:
        # Pipeline 2: Collect ALL URLs
        result = await url_manager.get_all_fulltext_urls(publication)
        
        # Pipeline 3: Download with fallback
        from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
        pdf_manager = PDFDownloadManager()
        pdf_path = await pdf_manager.download_with_fallback(
            publication, result.all_urls, output_dir
        )
    
    Deprecated: October 14, 2025
    Will be removed in: v3.0.0
    """
    import warnings
    warnings.warn(
        "get_fulltext() is deprecated. Use get_all_fulltext_urls() + PDFDownloadManager",
        DeprecationWarning,
        stacklevel=2,
    )
    # Keep implementation for now
    ...
```

### Phase 2: Update Documentation

Update all docs to show correct pipeline separation:

**BEFORE (Incorrect - Mixed Responsibilities):**
```python
# ❌ BAD: P2 doing P3+P4 work
manager = FullTextManager()
content = await manager.get_parsed_content(publication)
```

**AFTER (Correct - Clean Separation):**
```python
# ✅ GOOD: Each pipeline does its job
from omics_oracle_v2.lib.pipelines import (
    FullTextManager,              # P2: URL collection
)
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager  # P3
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor     # P4

# P2: Collect URLs from ALL sources
url_manager = FullTextManager()
urls_result = await url_manager.get_all_fulltext_urls(publication)

# P3: Download PDF with fallback through URLs
pdf_manager = PDFDownloadManager()
pdf_path = await pdf_manager.download_with_fallback(
    publication, 
    urls_result.all_urls,
    output_dir=Path("data/pdfs")
)

# P4: Parse and enrich content
extractor = PDFExtractor(enable_enrichment=True)
parsed = extractor.extract_text(
    pdf_path,
    metadata={
        "pmid": publication.pmid,
        "doi": publication.doi,
        "title": publication.title,
    }
)

# Result: Fully enriched content
print(f"Sections: {list(parsed['sections'].keys())}")
print(f"Tables: {parsed['table_count']}")
print(f"Quality: {parsed['quality_score']}")
```

### Phase 3: Update Integration Tests

Update tests to use correct pipeline separation:

```python
# tests/test_pipeline_integration.py

async def test_p2_p3_p4_integration():
    """Test P2→P3→P4 integration with correct separation."""
    
    # P2: Get URLs (ONLY)
    url_manager = FullTextManager()
    urls_result = await url_manager.get_all_fulltext_urls(publication)
    
    assert urls_result.success
    assert len(urls_result.all_urls) > 0
    
    # P3: Download PDF (ONLY)
    pdf_manager = PDFDownloadManager()
    pdf_path = await pdf_manager.download_with_fallback(
        publication,
        urls_result.all_urls,
        output_dir
    )
    
    assert pdf_path.exists()
    
    # P4: Parse and enrich (ONLY)
    extractor = PDFExtractor(enable_enrichment=True)
    parsed = extractor.extract_text(pdf_path, metadata={...})
    
    assert parsed['quality_score'] > 0.5
    assert len(parsed['sections']) > 0
```

### Phase 4: Remove Deprecated Methods (v3.0.0)

After 3-6 months of deprecation warnings:
1. Remove `get_parsed_content()` completely
2. Remove `get_fulltext()` completely
3. Update version to v3.0.0
4. Archive removed code

---

## 📋 Implementation Steps

### Step 1: Add Deprecation Warnings (TODAY)
- ✅ Add warnings to `get_parsed_content()`
- ✅ Add warnings to `get_fulltext()`
- ✅ Keep implementations working
- ✅ Commit: "deprecate: Mark P2 mixed-responsibility methods for removal"

### Step 2: Update All Documentation (TODAY)
- ✅ Update `README.md` with correct pipeline flow
- ✅ Create `docs/INTEGRATION_GUIDE.md` with examples
- ✅ Update all code examples in docs/
- ✅ Commit: "docs: Update to show correct pipeline separation"

### Step 3: Update Integration Tests (TODAY)
- ✅ Update `test_waterfall_fix.py` to use P2→P3→P4
- ✅ Create new test showing correct approach
- ✅ Verify old tests still pass (deprecated methods work)
- ✅ Commit: "test: Update integration tests for pipeline separation"

### Step 4: Create Migration Guide (TODAY)
- ✅ Document how to migrate from old to new approach
- ✅ Provide before/after examples
- ✅ List breaking changes in v3.0.0
- ✅ Commit: "docs: Add migration guide for P2 cleanup"

### Step 5: Monitor Usage (NEXT 3 MONTHS)
- Track deprecation warnings in logs
- Help users migrate to new approach
- Fix any issues found

### Step 6: Remove in v3.0.0 (FUTURE)
- Delete deprecated methods
- Update tests
- Release v3.0.0

---

## 🎯 Expected Outcomes

### Before Cleanup
```python
# Pipeline 2 (URL Collection) - 1,322 lines
- ✅ URL collection methods
- ❌ PDF download method (get_fulltext)
- ❌ Content parsing method (get_parsed_content)
- ❌ Mixed responsibilities
```

### After Cleanup
```python
# Pipeline 2 (URL Collection) - ~400 lines
- ✅ URL collection methods ONLY
- ✅ Single responsibility
- ✅ Clean API surface
- ✅ Easy to test
- ✅ Easy to maintain
```

---

## 📊 Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Lines of Code** | 1,322 | ~400 | -922 (-70%) |
| **Methods** | 20 | 17 | -3 |
| **Responsibilities** | 3 (URLs, Download, Parse) | 1 (URLs only) | -2 |
| **Complexity** | High (mixed) | Low (focused) | ⬇️ |
| **Testability** | Medium | High | ⬆️ |
| **Maintainability** | Medium | High | ⬆️ |

---

## 🚨 Breaking Changes (v3.0.0)

### Removed Methods

1. **`get_parsed_content()`** - REMOVED
   - **Migration:** Use P2→P3→P4 pipeline
   - **Example:** See "Correct approach" in migration guide

2. **`get_fulltext()`** - REMOVED
   - **Migration:** Use `get_all_fulltext_urls()` + `PDFDownloadManager.download_with_fallback()`
   - **Example:** See "Correct approach" in migration guide

---

## ✅ Checklist

- [ ] Add deprecation warnings to methods
- [ ] Update README.md
- [ ] Create INTEGRATION_GUIDE.md
- [ ] Update code examples in docs/
- [ ] Update integration tests
- [ ] Create migration guide
- [ ] Commit all changes
- [ ] Monitor usage for 3 months
- [ ] Schedule removal for v3.0.0

---

**Status:** Ready to implement Step 1 (Deprecation warnings)  
**Next:** Add deprecation warnings and update documentation
