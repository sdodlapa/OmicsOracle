# Archived Databases

This directory contains validation databases from Phase 5 testing that are no longer actively used.

## Archived Files

### 1. `test_validation.db`
- **Created**: Phase D (Full Pipeline Validation)
- **Purpose**: Validated full 4-stage pipeline with 3 GEO datasets
- **Content**: 
  - 3 GEO datasets
  - 5 publications
  - Full pipeline processing (P1-P4)
- **Status**: ✅ Validation successful, archived Oct 15, 2024

### 2. `quick_validation.db`
- **Created**: Phase E (Quick Production Validation)
- **Purpose**: Fast validation with 5 GEO datasets
- **Content**:
  - 5 GEO datasets
  - 6 publications
  - Streamlined processing
- **Status**: ✅ Validation successful, archived Oct 15, 2024

### 3. `extended_validation.db`
- **Created**: Phase F (Extended Production Validation)
- **Purpose**: Large-scale validation with 10 GEO datasets
- **Content**:
  - 10 GEO datasets
  - 11 publications
  - Production-scale processing
- **Status**: ✅ Validation successful (100% success rate), archived Oct 15, 2024

### 4. `production_validation.db`
- **Created**: Validation testing
- **Purpose**: Production readiness validation
- **Status**: Archived Oct 15, 2024

## Why Archived?

These databases served their purpose during development and validation phases but are no longer needed for production operation.

**Production Database**: `/data/database/search_data.db`

## Data Preservation

All validation data is preserved in these archived databases. They can be restored if needed for:
- Historical reference
- Debugging validation issues
- Comparing production vs validation results
- Research and analysis

## Restore Instructions

If you need to access validation data:

```bash
# View database contents
sqlite3 data/database/archive/extended_validation.db ".tables"

# Query specific data
sqlite3 data/database/archive/extended_validation.db "SELECT * FROM universal_identifiers;"

# Restore to active directory (if needed)
cp data/database/archive/extended_validation.db data/database/
```

## Archive Date

**Archived**: October 15, 2024  
**Reason**: Transition from validation to production deployment (Phase 6)  
**Total Size**: ~200 KB combined

## Related Documentation

- `/docs/IMPLEMENTATION_COMPLETE_OCT14.md` - Phase 5 validation results
- `/docs/DATABASE_INTEGRATION_COMPLETE.md` - Production integration details
- `/docs/COMPREHENSIVE_ARCHITECTURE.md` - System architecture
