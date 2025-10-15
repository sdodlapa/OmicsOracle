# Tests Folder Assessment

**Date:** October 15, 2025  
**Objective:** Identify old/redundant test files for archival

---

## Summary

**Total Test Files:** 194  
**Test Directories:** 21 subdirectories  
**Root Test Files:** ~40 files  

**Pattern:** Many exploration, debug, and demo test files that may be outdated

---

## Potentially Redundant Test Files

### Category 1: Debug/Exploration Tests (11 files)

These appear to be one-off tests for debugging specific issues:

```
test_20_dois_quick.py                        # Quick validation test
test_core_api_debug.py                       # API debugging
test_robust_search_demo_fast.py              # Demo (fast variant)
test_robust_search_demo.py                   # Demo (original)
test_scihub_comprehensive_exploration.py     # 18K - Exploration
test_scihub_debug.py                         # 3.1K - Debugging
test_scihub_libgen_exploration.py            # 16K - Exploration
test_scihub_quick_exploration.py             # 2.5K - Quick test
test_scihub_response_debug.py                # 3.6K - Response debugging
test_single_doi_debug.py                     # Single DOI debugging
test_identify_failures.py                    # Failure analysis
```

**Total Size:** ~60K+ of exploration code

### Category 2: Duplicate/Similar Tests

Multiple scihub-related tests that may overlap:

```
test_scihub.py                               # 1.7K - Main test
test_scihub_comprehensive_exploration.py     # 18K - Comprehensive
test_scihub_libgen_exploration.py            # 16K - LibGen exploration  
test_scihub_strategies.py                    # 11K - Strategy testing
test_scihub_fills_gaps.py                    # 5.3K - Gap filling
test_scihub_full_html.py                     # 1.9K - HTML parsing
```

**Question:** Are all 9 scihub test files still needed?

### Category 3: Client Tests (Potentially Redundant)

Individual client tests that may be covered by integration tests:

```
test_arxiv_client.py                         # ArXiv client
test_biorxiv_client.py                       # BioRxiv client
test_core_client.py                          # Core client
test_crossref_client.py                      # Crossref client
test_unpaywall.py                            # Unpaywall client
```

**Check:** Are these covered by unit/client/ or integration/ tests?

### Category 4: Week-Based Organization

```
week2/                                       # Week 2 tests
week3/                                       # Week 3 tests
```

**Question:** Are these historical? Should they be archived?

---

## Archival History

Already archived test files:

```
archive/phase4-test-files-2025-10/          # 18 files
archive/test-files-oct15/                    # Unknown count
archive/tests-2025-10-12-pdf-download/       # PDF download tests
archive/tests-2025-10-12-redundancy/         # Redundancy tests
```

**Pattern:** Phase-based and date-based archival strategy already in use

---

## Recommended Actions

### Option 1: Archive Exploration/Debug Tests (Conservative)

**Archive** (11 files, ~60K):
- All `test_*debug*.py` files (5 files)
- All `test_*exploration*.py` files (4 files)  
- Demo files: `test_robust_search_demo*.py` (2 files)

**Rationale:** These are one-off debugging/exploration tests, not regression tests

**Create:** `archive/exploration-debug-tests-oct15/`

### Option 2: Consolidate SciHub Tests (Moderate)

**Keep:**
- `test_scihub.py` (main test, 1.7K)
- `tests/fulltext/` (organized tests)

**Archive:**
- `test_scihub_comprehensive_exploration.py` (18K)
- `test_scihub_libgen_exploration.py` (16K)
- `test_scihub_strategies.py` (11K)
- `test_scihub_fills_gaps.py` (5.3K)
- `test_scihub_debug.py` (3.1K)
- `test_scihub_quick_exploration.py` (2.5K)
- `test_scihub_response_debug.py` (3.6K)
- `test_scihub_full_html.py` (1.9K)

**Total:** 8 files, ~61K

**Rationale:** Exploration work complete, organized tests now in place

### Option 3: Archive Week Folders (Aggressive)

**Archive:**
- `tests/week2/` (entire folder)
- `tests/week3/` (entire folder)

**Rationale:** Time-based organization suggests these are historical

### Option 4: Comprehensive Review (Most Thorough)

**Process:**
1. Review each test file's purpose
2. Check if covered by organized test folders (unit/, integration/, e2e/)
3. Archive if:
   - One-off debugging test
   - Superseded by better organized tests
   - Historical/exploratory

**Estimate:** Could archive 20-40 files

---

## Test Organization Best Practices

**Current Good Structure:**
```
tests/
  unit/           # Unit tests (isolated)
  integration/    # Integration tests
  e2e/            # End-to-end tests
  api/            # API tests
  pipeline/       # Pipeline tests
  ...
```

**Problem:** 40+ root-level test files, many exploratory/debug

**Ideal:** Most tests in organized subdirectories, few root-level files

---

## Proposed Archival Plan

### Phase 1: Debug/Exploration Cleanup (Quick Win)

**Create:** `archive/exploration-debug-tests-oct15/`

**Move:**
```bash
# Debug tests (5 files)
test_core_api_debug.py
test_scihub_debug.py
test_scihub_response_debug.py
test_single_doi_debug.py
test_identify_failures.py

# Exploration tests (4 files)
test_scihub_comprehensive_exploration.py
test_scihub_libgen_exploration.py  
test_scihub_quick_exploration.py
test_20_dois_quick.py

# Demo tests (2 files)
test_robust_search_demo.py
test_robust_search_demo_fast.py
```

**Impact:** 11 files, ~60K archived

### Phase 2: SciHub Consolidation (Medium Priority)

**Review:** Determine if scihub strategy/fills_gaps/full_html tests still needed

**Potential Archive:** 3-4 additional files, ~20K

### Phase 3: Week Folder Review (Lower Priority)

**Review:** Check week2/, week3/ for current relevance

**Potential Archive:** 2 entire folders

---

## Next Steps

1. ✅ Review test files in categories above
2. ❌ Create `archive/exploration-debug-tests-oct15/`
3. ❌ Move debug/exploration files to archive
4. ❌ Update test documentation
5. ❌ Run remaining test suite to verify nothing broken
6. ❌ Commit cleanup

**Estimated Impact:** 11-20 files, 60-100K code archived

---

## Questions for Review

1. Are scihub exploration tests still needed now that pipeline is stable?
2. Are client tests duplicated in unit/client/ folder?
3. Should week2/week3 folders be archived as historical?
4. Are demo tests needed or can they be documented examples instead?
5. Which debug tests are for issues that are now resolved?
