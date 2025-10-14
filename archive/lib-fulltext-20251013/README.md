# Archived: Old Full-Text System

**Archived:** October 13, 2025
**Reason:** Superseded by new system in `omics_oracle_v2/lib/enrichment/fulltext/`

## What Was Archived

This directory contains the OLD fulltext system that was originally located at `/lib/fulltext/`.

**Files Archived (~1,577 lines):**
- `manager_integration.py` (386 lines) - Integration layer
- `pdf_extractor.py` (204 lines) - PDF parsing
- `pdf_downloader.py` (191 lines) - OLD download logic
- `validators.py` (73 lines) - URL validation
- `models.py` (194 lines) - Data models
- `content_fetcher.py` (167 lines) - Content fetching
- `content_extractor.py` (333 lines) - Text extraction
- `__init__.py` (29 lines) - Package exports

## Why Was It Archived?

1. **Not Used by Active API:**
   - The production API (`omics_oracle_v2/api/`) uses the NEW system
   - No active endpoints import from this old system

2. **Superseded by Better Implementation:**
   - NEW system: `omics_oracle_v2/lib/enrichment/fulltext/`
   - NEW system has 11+ sources vs old system's basic implementation
   - NEW system has waterfall fallback, smart caching, better validation

3. **Causing Confusion:**
   - Two parallel implementations
   - Import path confusion (`lib.fulltext` vs `omics_oracle_v2.lib.enrichment.fulltext`)
   - Maintenance burden

## What Still Uses This Old System?

**Before archiving, these files imported from old system:**
- `/extras/pipelines/publication_pipeline.py` (not in production)
- `/extras/pipelines/geo_citation_pipeline.py` (not in production)
- Various files in `/extras/legacy_tests/` (old tests)

These imports will need to be updated to use the NEW system if those files are ever activated.

## Migration Path

If you need functionality from the old system:

**OLD Import:**
```python
from lib.fulltext.manager import FullTextManager
from lib.fulltext.pdf_downloader import PDFDownloader
```

**NEW Import:**
```python
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager
```

## Restoration Instructions

If you need to restore this code:

```bash
# Copy files back to original location
cp -r archive/lib-fulltext-20251013/* lib/fulltext/

# Or reference in-place
# (Not recommended - defeats the purpose of archiving)
```

## Related Documentation

- `/docs/WATERFALL_FIX_COMPLETE.md` - Details about waterfall fallback fix
- `/docs/FULLTEXT_REDUNDANCY_ANALYSIS.md` - Complete analysis of redundant code
- `/docs/FULLTEXT_ARCHITECTURE_ANALYSIS.md` - Architecture comparison

## Archive Metadata

- **Date Archived:** October 13, 2025
- **Archived By:** Automated cleanup process
- **Total Lines:** ~1,577 lines
- **Reason:** Dead code (unused by production)
- **Safe to Delete:** After 30 days (November 13, 2025)
