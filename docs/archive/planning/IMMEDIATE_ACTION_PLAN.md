# 🚨 IMMEDIATE ACTION PLAN - OmicsOracle Backend Refactoring

## URGENT: Critical Corruption Detected

The OmicsOracle web interface backend is **severely corrupted** with mixed Python/JavaScript syntax in the search endpoint. **Immediate action required** to prevent complete system failure.

## Quick Start Implementation

### Step 1: Create New Structure (30 minutes)
```bash
# Create new modular structure
mkdir -p interfaces/modern/{app,api/{routes,schemas},services,models,utils,templates,static/{css,js},config,tests}

# Create initial files
touch interfaces/modern/app/{__init__.py,main.py,dependencies.py}
touch interfaces/modern/api/{__init__.py,routes/{__init__.py,search.py},schemas/{__init__.py,search.py}}
touch interfaces/modern/services/{__init__.py,search_service.py,cache_service.py}
```

### Step 2: Fix Search Endpoint (1 hour)
- Extract clean search logic from `interfaces/current/search_function_clean.py`
- Create properly structured `SearchService` class
- Implement dataset-specific caching (fix duplicate summaries issue)

### Step 3: Basic API Structure (1 hour)
- Set up FastAPI application factory
- Create essential API routes
- Add error handling and logging

## Priority Order:
1. **URGENT**: Fix corrupted search function (Day 1)
2. **HIGH**: Implement core services (Day 2-3)
3. **MEDIUM**: Add advanced features (Day 4-5)
4. **LOW**: Migration and optimization (Day 6-8)

## Files to Create First:
1. `interfaces/modern/services/search_service.py` - Core search logic
2. `interfaces/modern/api/routes/search.py` - Search endpoints
3. `interfaces/modern/app/main.py` - FastAPI app
4. `interfaces/modern/services/cache_service.py` - Fix caching issues

## Key Fixes:
- **Search Corruption**: Replace mixed Python/JS with pure Python
- **Caching Bug**: Change from query-level to dataset-specific cache keys
- **Metadata Extraction**: Fix "unknown" GEO ID issues
- **Separation of Concerns**: Extract HTML/CSS/JS to separate files

## Next Steps:
1. Review and approve this plan
2. Begin Phase 1 implementation immediately
3. Set up parallel deployment for safe migration
4. Create comprehensive test suite

**Time Estimate**: 8 days for complete refactoring
**Risk Level**: Medium (with proper testing and gradual migration)
**Impact**: High (dramatically improved maintainability and functionality)

See `BACKEND_REFACTORING_PLAN.md` for complete technical details.
