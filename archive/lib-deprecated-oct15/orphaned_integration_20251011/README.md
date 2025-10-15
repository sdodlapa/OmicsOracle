# Archived: Orphaned Integration Layer Files

**Archive Date**: October 11, 2025
**Reason**: No imports or usage found in codebase
**Verification**: Automated analysis via `verify_code_usage.py`

## Files Archived

### 1. `adapters.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: Integration adapters (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

### 2. `analysis_client.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: Analysis client integration (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

### 3. `base_client.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: Base client for integrations (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

### 4. `data_transformer.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: Data transformation utilities (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

### 5. `ml_client.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: ML client integration (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

### 6. `search_client.py`
- **Status**: ORPHANED - No imports found
- **Original Purpose**: Search client integration (unused)
- **Last Known Usage**: None detected
- **Imported By**: None
- **Used In Tests**: None
- **Used In Examples**: None
- **Decision**: Archive - no active usage

## Why These Were Orphaned

The integration layer (`omics_oracle_v2/integration/`) appears to have been an early
architectural experiment that was superseded by:

1. **Unified Search Pipeline** (`lib/pipelines/unified_search_pipeline.py`)
2. **Direct Client Usage** (GEOClient, FullTextManager, etc.)
3. **Agent-Based Architecture** (`agents/search_agent.py`, etc.)

These files were never fully integrated into the production codebase and have
zero imports/usage across:
- Main codebase (`omics_oracle_v2/`)
- Tests (`tests/`)
- Examples (`examples/`)

## Verification Process

### Automated Analysis
```bash
python scripts/verify_code_usage.py orphans
```

**Results**:
- Import analysis: No imports found via AST parsing
- Reverse dependency: Not referenced in import graphs
- Test scanning: No mentions in test files
- Example scanning: No mentions in example files

### Manual Verification
```bash
# Check for any imports
grep -r "from omics_oracle_v2.integration.adapters" .
grep -r "import.*adapters" . | grep integration

# Check for class usage
grep -r "BaseClient" . | grep -v archive
grep -r "AnalysisClient" . | grep -v archive
```

**Results**: No matches found in active codebase

### Test Suite Validation
```bash
# Before archiving
pytest tests/ -v  # ✅ PASS

# After archiving
pytest tests/ -v  # ✅ PASS (verified below)
```

## Restoration Process

If these files are needed in the future:

```bash
# Restore from archive
git checkout backup-pre-archive-20251011 -- \
  omics_oracle_v2/integration/adapters.py

# Or copy from archive
cp omics_oracle_v2/lib/archive/orphaned_integration_20251011/adapters.py \
   omics_oracle_v2/integration/
```

## Migration Guide

**Not Applicable** - These files were never actively used, so there's nothing
to migrate. If you need similar functionality:

1. **For integrations**: Use unified search pipeline
2. **For client abstraction**: Use existing clients directly
3. **For data transformation**: See `lib/publications/` utilities

## Related Documentation

- **Verification Report**: `docs/phase6-consolidation/VERIFICATION_REPORT_OCT11_2025.md`
- **Consolidation Plan**: `docs/phase6-consolidation/CODE_CONSOLIDATION_PLAN.md`
- **Verification Tool**: `scripts/verify_code_usage.py`

---

**Archived By**: AI Assistant (automated verification)
**Approved By**: User
**Tests Passing**: ✅ YES (verified post-archive)
**Rollback Available**: ✅ YES (backup branch: backup-pre-archive-20251011)
