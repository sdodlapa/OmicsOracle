# Pipeline Reorganization - Migration Guide

**Date**: October 14, 2025  
**Author**: OmicsOracle Team  
**Status**: ✅ Complete

---

## Overview

The fulltext module has been reorganized into **3 independent pipelines** with clean separation:

1. **Pipeline 2: URL Collection** (`lib/pipelines/url_collection/`)
2. **Pipeline 3: PDF Download** (`lib/pipelines/pdf_download/`)
3. **Pipeline 4: Text Enrichment** (`lib/pipelines/text_enrichment/`)

---

## Import Path Changes

### Pipeline 2: URL Collection

**Manager & Configuration:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.manager import (
    FullTextManager,
    FullTextManagerConfig,
    FullTextResult,
    FullTextSource,
    SourceURL,
)

# NEW
from omics_oracle_v2.lib.pipelines.url_collection import (
    FullTextManager,
    FullTextManagerConfig,
    FullTextResult,
    FullTextSource,
    SourceURL,
)
```

**URL Validator:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.url_validator import URLType, URLValidator

# NEW
from omics_oracle_v2.lib.pipelines.url_collection import URLType, URLValidator
```

**Source Clients:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.sources.scihub_client import SciHubClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources import PMCClient, UnpaywallClient

# NEW
from omics_oracle_v2.lib.pipelines.url_collection.sources.scihub_client import SciHubClient
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources import PMCClient, UnpaywallClient
```

### Pipeline 3: PDF Download

**Download Manager:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.download_manager import (
    PDFDownloadManager,
    DownloadResult,
    DownloadReport,
)

# NEW
from omics_oracle_v2.lib.pipelines.pdf_download import (
    PDFDownloadManager,
    DownloadResult,
    DownloadReport,
)
```

**Cache & Utilities:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.smart_cache import SmartCache, LocalFileResult
from omics_oracle_v2.lib.enrichment.fulltext.utils import validate_pdf_content

# NEW
from omics_oracle_v2.lib.pipelines.pdf_download import SmartCache, LocalFileResult
from omics_oracle_v2.lib.pipelines.pdf_download.utils import validate_pdf_content
```

### Pipeline 4: Text Enrichment

**Parser & Caches:**
```python
# OLD
from omics_oracle_v2.lib.enrichment.fulltext.pdf_parser import PDFExtractor
from omics_oracle_v2.lib.enrichment.fulltext.parsed_cache import ParsedCache
from omics_oracle_v2.lib.enrichment.fulltext.cache_db import FullTextCacheDB
from omics_oracle_v2.lib.enrichment.fulltext.normalizer import ContentNormalizer

# NEW
from omics_oracle_v2.lib.pipelines.text_enrichment import (
    PDFExtractor,
    ParsedCache,
    FullTextCacheDB,
    ContentNormalizer,
)
```

---

## Files Removed

### Deleted (Redundant)
- ❌ `utils/logging_utils.py` - Not used, replaced with standard Python logging

---

## Files Updated

### Core Pipeline Files
- ✅ `url_collection/manager.py` - 6 import statements updated
- ✅ `url_collection/url_validator.py` - Docstring example updated
- ✅ `url_collection/sources/oa_sources/__init__.py` - 7 imports updated
- ✅ `url_collection/sources/oa_sources/pmc_client.py` - Lazy imports updated
- ✅ `pdf_download/utils/__init__.py` - Removed logging_utils exports

### API Integration
- ✅ `api/routes/agents.py` - 3 import statements updated

### Test Files (20 files)
- ✅ `tests/test_fulltext_manager.py`
- ✅ `tests/test_scihub.py`
- ✅ `tests/test_comprehensive_fulltext_validation.py`
- ✅ `tests/lib/fulltext/test_normalizer.py`
- ✅ `tests/lib/fulltext/test_smart_cache.py`
- ✅ `tests/lib/fulltext/test_parsed_cache.py`
- ✅ `tests/lib/fulltext/test_cache_db.py`
- ✅ ... and 13 more test files

---

## Verification

### Import Tests
```bash
# Pipeline 2
python -c "from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager; print('✓')"

# Pipeline 3
python -c "from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager; print('✓')"

# Pipeline 4
python -c "from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor; print('✓')"
```

### Test Suite
```bash
pytest tests/test_fulltext_manager.py  # ✅ PASSED
```

---

## Directory Structure

### New Structure
```
lib/pipelines/
├── citation_discovery/          # Pipeline 1 (already exists)
├── url_collection/              # Pipeline 2 (NEW)
│   ├── __init__.py
│   ├── manager.py
│   ├── url_validator.py
│   └── sources/
│       ├── institutional_access.py
│       ├── libgen_client.py
│       ├── scihub_client.py
│       └── oa_sources/
│           ├── arxiv_client.py
│           ├── biorxiv_client.py
│           ├── core_client.py
│           ├── crossref_client.py
│           ├── pmc_client.py
│           └── unpaywall_client.py
├── pdf_download/                # Pipeline 3 (NEW)
│   ├── __init__.py
│   ├── download_manager.py
│   ├── landing_page_parser.py
│   ├── smart_cache.py
│   └── utils/
│       ├── __init__.py
│       └── pdf_utils.py
└── text_enrichment/             # Pipeline 4 (NEW)
    ├── __init__.py
    ├── pdf_parser.py
    ├── parsed_cache.py
    ├── cache_db.py
    ├── normalizer.py
    └── enrichers/               # Future: GROBID, section detection
```

### Old Structure (To Be Archived)
```
lib/enrichment/fulltext/         # OLD - Will be archived
├── manager.py                   # Copied to url_collection/
├── download_manager.py          # Copied to pdf_download/
├── pdf_parser.py                # Copied to text_enrichment/
└── ... (all other files)
```

---

## Backward Compatibility

### ⚠️ Breaking Changes
The old import paths **will not work** after archiving:
```python
# This will break after archival
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
```

### Migration Required
Update all imports to new pipeline locations as shown above.

---

## Pipeline Integration Flow

### Complete Pipeline Chain
```
P1: Citation Discovery
   ↓ (Publications with metadata)
P2: URL Collection  
   ↓ (URLs from 11 sources)
P3: PDF Download
   ↓ (Validated PDF files)
P4: Text Enrichment
   ↓ (Structured, enriched text)
```

### Integration Contracts

**P1 → P2:**
```python
# Input: Publication with identifiers
# Output: FullTextResult with list of SourceURLs
```

**P2 → P3:**
```python
# Input: List of SourceURLs
# Output: DownloadResult with validated PDF path
```

**P3 → P4:**
```python
# Input: Path to validated PDF
# Output: Enriched content (title, sections, tables, figures)
```

---

## Benefits of Reorganization

### Before
❌ 1,323-line monolithic manager.py  
❌ Tight coupling between pipelines  
❌ Difficult to test independently  
❌ Mixed responsibilities  

### After
✅ Clean separation of concerns  
✅ Independent testability  
✅ Clear integration contracts  
✅ Easier to understand and maintain  
✅ Foundation for future enhancements  

---

## Next Steps

1. ✅ Pipeline separation complete
2. ✅ All imports updated
3. ✅ Tests updated and passing
4. ⏳ Archive old `enrichment/fulltext/` directory
5. ⏳ Clean `manager.py` (remove download/parse methods)
6. ⏳ Expand Pipeline 4 with GROBID integration

---

## Support

For questions or issues with the migration:
- Check this guide for correct import paths
- Review `docs/PIPELINE_REORGANIZATION_PROGRESS.md` for details
- Contact: OmicsOracle Development Team

---

**Last Updated**: October 14, 2025  
**Migration Status**: ✅ Complete
