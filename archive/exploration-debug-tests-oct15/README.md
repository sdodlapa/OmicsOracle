# Archived Exploration & Debug Tests

**Date Archived:** October 15, 2025  
**Reason:** Tests folder cleanup - Phase 1  
**Files Archived:** 11 files (~70K total)

---

## Summary

These test files were one-off debugging and exploration tests created during development. They served their purpose but are no longer needed for regression testing.

---

## Files Archived

### Debug Tests (5 files)

**test_core_api_debug.py** (1.9K)
- Purpose: API endpoint debugging
- Status: Issues resolved, organized tests now in tests/api/

**test_scihub_debug.py** (3.1K)
- Purpose: Sci-Hub waterfall behavior debugging
- Status: Waterfall fixed, covered by integration tests

**test_scihub_response_debug.py** (3.6K)
- Purpose: Sci-Hub response format debugging
- Status: Response handling working, covered by unit tests

**test_single_doi_debug.py** (1.9K)
- Purpose: Single DOI debugging
- Status: DOI handling working, covered by pipeline tests

**test_identify_failures.py** (3.7K)
- Purpose: Failure analysis during development
- Status: Issues resolved

### Exploration Tests (4 files)

**test_scihub_comprehensive_exploration.py** (18K)
- Purpose: Comprehensive Sci-Hub exploration
- Status: Exploration complete, findings integrated into pipeline

**test_scihub_libgen_exploration.py** (16K)
- Purpose: LibGen integration exploration
- Status: LibGen integration complete, tested in tests/fulltext/

**test_scihub_quick_exploration.py** (2.5K)
- Purpose: Quick Sci-Hub exploration
- Status: Superseded by comprehensive tests

**test_20_dois_quick.py** (4.2K)
- Purpose: Quick validation with 20 diverse DOIs
- Status: Coverage validated, organized tests in tests/validation/

### Demo Tests (2 files)

**test_robust_search_demo.py** (11K)
- Purpose: Demonstrate robust search capability
- Status: Feature stable, demo unnecessary, covered by e2e tests

**test_robust_search_demo_fast.py** (8.2K)
- Purpose: Fast variant of search demo
- Status: Same as above

---

## Impact

**Before Archival:**
- tests/ folder: ~40 root-level test files
- Many exploratory/debugging tests mixed with regression tests

**After Archival:**
- tests/ folder: ~29 root-level test files
- Cleaner separation between organized tests and one-off files

**LOC Archived:** ~70K

---

## Rationale

### Why Archive These Files?

1. **One-off debugging**: Created to debug specific issues that are now resolved
2. **Exploration work complete**: Findings integrated into main codebase
3. **Better organized tests exist**: Functionality covered by tests/unit/, tests/integration/, tests/e2e/
4. **Reduce noise**: Easier to find relevant tests without exploratory files

### Why Not Delete?

- Historical reference for development decisions
- May contain useful patterns or edge cases
- Can be restored if needed for specific investigations

---

## Test Coverage After Archival

**Sci-Hub functionality** is still tested by:
- `tests/test_scihub.py` (main test, 1.7K)
- `tests/test_scihub_strategies.py` (11K - strategy testing)
- `tests/test_scihub_fills_gaps.py` (5.3K - gap filling)
- `tests/test_scihub_full_html.py` (1.9K - HTML parsing)
- `tests/fulltext/` (organized fulltext tests)

**API functionality** is still tested by:
- `tests/api/` (organized API tests)
- `tests/integration/` (integration tests)
- `tests/e2e/` (end-to-end tests)

**DOI handling** is still tested by:
- `tests/pipeline/` (pipeline tests)
- `tests/unit/` (unit tests)

---

## Restoration

If any of these tests are needed, they can be restored with:

```bash
cd /path/to/OmicsOracle
cp archive/exploration-debug-tests-oct15/<filename> tests/
```

---

## Related Documentation

- See `docs/TESTS_FOLDER_ASSESSMENT.md` for full test cleanup strategy
- See `docs/API_ROUTES_REFACTORING.md` for overall cleanup progress
