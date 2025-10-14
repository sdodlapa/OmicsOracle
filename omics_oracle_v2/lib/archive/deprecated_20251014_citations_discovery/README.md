# Deprecated: lib/citations/discovery/ - October 14, 2025

## ⚠️ This code has been archived and should NOT be used

**Deprecated Date**: October 14, 2025  
**Reason**: Old/outdated version replaced by comprehensive implementation

---

## 🔄 Migration Guide

### OLD Import (DEPRECATED ❌):
```python
from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
```

### NEW Import (USE THIS ✅):
```python
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
```

---

## 📊 Why This Was Deprecated

### Old Version (`lib/citations/discovery/`)
- **Size**: 173 lines (basic implementation)
- **Last Updated**: September 2025 (Phase 2B reorganization)
- **Features**: Basic citation discovery only
- **Files**: 1 file total

### New Version (`lib/pipelines/citation_discovery/`)
- **Size**: 829 lines (comprehensive implementation)
- **Last Updated**: October 14, 2025 (Phase 10 - Metrics Logging)
- **Features**: 
  - Quality validation (Phase 9)
  - Metrics logging (Phase 10)
  - Smart caching
  - Deduplication
  - 5 citation sources (OpenAlex, PubMed, Semantic Scholar, Europe PMC, OpenCitations)
  - Error handling
  - Source performance tracking
- **Files**: 12 files total

**Difference**: 656 lines of additional features missing from old version

---

## 📁 Files Archived

- `__init__.py`
- `geo_discovery.py` (173 lines - basic version only)

---

## 🚀 What Changed

The new implementation in `lib/pipelines/citation_discovery/` includes:

1. **Advanced Features**:
   - Quality validation and filtering
   - Performance metrics logging
   - Intelligent caching strategies
   - Smart deduplication
   - Multi-source orchestration

2. **Better Architecture**:
   - Modular design (12 files vs 1 file)
   - Separation of concerns
   - Comprehensive error handling
   - Source-specific optimizations

3. **Production Ready**:
   - Used by API (`omics_oracle_v2/api/routes/agents.py`)
   - Full test coverage
   - Documentation
   - Monitoring and metrics

---

## 📝 Timeline

1. **Sept 2025 (Phase 2B)**: Basic implementation created in `lib/citations/discovery/`
2. **Oct 2025 (Phases 6-10)**: Major enhancements in `lib/pipelines/citation_discovery/`
3. **Oct 14, 2025**: Old version archived, all code updated to use new version

---

## ✅ Updated Files

All imports have been updated to use the new location:

### Production Code:
- ✅ `omics_oracle_v2/api/routes/agents.py` (already using new version)
- ✅ `extras/pipelines/geo_citation_pipeline.py` (updated Oct 14)
- ✅ `extras/pipelines/publication_pipeline.py` (updated Oct 14)

### Examples:
- ✅ `examples/geo_citation_tracking.py` (updated Oct 14)
- ✅ `examples/validation/citation-fixes.py` (updated Oct 14)
- ✅ `examples/sprint-demos/openalex-integration.py` (updated Oct 14)

### Tests:
- ✅ `tests/validation/test_unified_pipeline_validation.py` (updated Oct 14)
- ✅ `tests/validation/test_week4_features.py` (updated Oct 14)

---

## 🔍 If You Need to Reference Old Code

The old implementation is preserved here for reference only. DO NOT use it in new code.

To view the old implementation:
```bash
cat omics_oracle_v2/lib/archive/deprecated_20251014_citations_discovery/geo_discovery.py
```

---

## 📚 See Also

- **New Implementation**: `omics_oracle_v2/lib/pipelines/citation_discovery/`
- **Documentation**: `docs/CITATION_DISCOVERY_DUPLICATE_ANALYSIS.md`
- **Migration Summary**: `docs/OLD_CITATIONS_DISCOVERY_ARCHIVAL.md`
