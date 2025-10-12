# Code Cleanup & Consolidation Plan
**Date**: October 12, 2025
**Branch**: fulltext-implementation-20251011

## Current State

### ✅ JUST COMMITTED (Working Code)
- `omics_oracle_v2/api/routes/agents.py` - Tiered waterfall retry implementation
- `omics_oracle_v2/lib/fulltext/manager.py` - PMC OA API fix, skip_sources support
- `omics_oracle_v2/lib/storage/pdf/download_manager.py` - Session fixes
- `omics_oracle_v2/api/models/responses.py` - Response models
- `omics_oracle_v2/lib/publications/models.py` - Publication models
- DELETED: `omics_oracle_v2/lib/fulltext/download_utils.py` (redundant)

---

## Root Directory Analysis

### 📝 Documentation Files (*.md)

#### **KEEP** (Active Reference)
- `README.md` - Main project documentation
- `CURRENT_STATUS.md` - Current state (Oct 11)
- `NEXT_STEPS.md` - Future work

#### **ARCHIVE** (Historical/Session Notes)
```
BUG_FIX_PDF_DOWNLOAD_COUNT.md          → archive/docs-2025-10-12/
INSTITUTIONAL_ACCESS_EXPLANATION.md     → archive/docs-2025-10-12/
PDF_DOWNLOAD_CLEANUP_SUMMARY.md         → archive/docs-2025-10-12/
PDF_DOWNLOAD_EXPLANATION.md             → archive/docs-2025-10-12/
ROOT_CAUSE_ANALYSIS.md                  → archive/docs-2025-10-12/
SESSION_HANDOFF_PDF_DOWNLOAD.md         → archive/docs-2025-10-12/
SESSION_STATE_PDF_DOWNLOAD_ISSUE.md     → archive/docs-2025-10-12/
TIERED_WATERFALL_IMPLEMENTATION.md      → archive/docs-2025-10-12/
VALIDATION_RESULTS.md                   → archive/docs-2025-10-12/
CURRENT_STATUS_OLD.md                   → archive/docs-2025-10-12/
COMMIT_ORGANIZATION_COMPLETE.md         → archive/docs-2025-10-12/
PHASE1_FINAL_SUMMARY.md                 → archive/docs-2025-10-12/
WEEK2_DAY4_SESSION_HANDOFF.md          → archive/docs-2025-10-12/
WEEK2_DAY4_TEST_ANALYSIS.md            → archive/docs-2025-10-12/
TESTING_INSTRUCTIONS.md                 → archive/docs-2025-10-12/
```

### 🧪 Test Files (*.py in root)

#### **ARCHIVE** (PDF Download Debug Tests - COMPLETED)
```
test_critical_fixes.py              → archive/tests-2025-10-12/pdf-download/
test_pdf_download_fixes.py          → archive/tests-2025-10-12/pdf-download/
test_pdf_download_integration.py    → archive/tests-2025-10-12/pdf-download/
test_tiered_waterfall.py            → archive/tests-2025-10-12/pdf-download/
test_tiered_waterfall_live.py       → archive/tests-2025-10-12/pdf-download/
test_waterfall_retry.py             → archive/tests-2025-10-12/pdf-download/
debug_pmid_39997216.py              → archive/tests-2025-10-12/pdf-download/
```

#### **ARCHIVE** (Redundancy Test - COMPLETED)
```
test_removed_redundancy.py          → archive/tests-2025-10-12/redundancy/
```

#### **KEEP** (Utility Scripts)
```
setup_logging.py                    → Keep (utility)
chrome_cookies.py                   → Keep (utility for future Shibboleth work)
```

### 🗄️ Shell Scripts

#### **ARCHIVE**
```
cleanup_root.sh                     → archive/scripts-2025-10-12/
validate_pdf_cleanup.sh             → archive/scripts-2025-10-12/
test_api_download.sh                → archive/scripts-2025-10-12/
```

#### **KEEP**
```
start_omics_oracle.sh               → Keep (active)
```

---

## Archive Structure

```
archive/
├── docs-2025-10-12-pdf-download/
│   ├── BUG_FIX_PDF_DOWNLOAD_COUNT.md
│   ├── INSTITUTIONAL_ACCESS_EXPLANATION.md
│   ├── PDF_DOWNLOAD_CLEANUP_SUMMARY.md
│   ├── ROOT_CAUSE_ANALYSIS.md
│   ├── SESSION_HANDOFF_PDF_DOWNLOAD.md
│   ├── SESSION_STATE_PDF_DOWNLOAD_ISSUE.md
│   ├── TIERED_WATERFALL_IMPLEMENTATION.md
│   └── VALIDATION_RESULTS.md
│
├── docs-2025-10-12-historical/
│   ├── COMMIT_ORGANIZATION_COMPLETE.md
│   ├── CURRENT_STATUS_OLD.md
│   ├── PHASE1_FINAL_SUMMARY.md
│   ├── WEEK2_DAY4_SESSION_HANDOFF.md
│   ├── WEEK2_DAY4_TEST_ANALYSIS.md
│   └── TESTING_INSTRUCTIONS.md
│
├── tests-2025-10-12-pdf-download/
│   ├── test_critical_fixes.py
│   ├── test_pdf_download_fixes.py
│   ├── test_pdf_download_integration.py
│   ├── test_tiered_waterfall.py
│   ├── test_tiered_waterfall_live.py
│   ├── test_waterfall_retry.py
│   └── debug_pmid_39997216.py
│
├── tests-2025-10-12-redundancy/
│   └── test_removed_redundancy.py
│
└── scripts-2025-10-12/
    ├── cleanup_root.sh
    ├── validate_pdf_cleanup.sh
    └── test_api_download.sh
```

---

## Summary

### Files to Archive: 29
- **Documentation**: 14 markdown files
- **Test Files**: 8 Python test scripts
- **Shell Scripts**: 3 shell scripts
- **Utilities**: 1 Python utility (test_removed_redundancy.py)

### Files to Keep: 5
- **Core Docs**: README.md, CURRENT_STATUS.md, NEXT_STEPS.md
- **Utilities**: setup_logging.py, chrome_cookies.py
- **Scripts**: start_omics_oracle.sh

### Commit Changes: 6 files modified
- All critical fixes committed successfully
- Redundant download_utils.py deleted

---

## Next Steps

1. Create archive directories
2. Move files to archive
3. Commit cleanup
4. Create final STATUS.md with current state
