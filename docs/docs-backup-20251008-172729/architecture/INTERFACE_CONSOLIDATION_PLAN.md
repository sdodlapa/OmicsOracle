# Interface Consolidation Plan

## Current Problem
- Multiple FastAPI applications serving the same purpose
- Code duplication between `src/omics_oracle/presentation/web/` and backup interfaces
- Inconsistent API endpoints and functionality

## Solution: Single Interface Architecture

### Target Structure
```
src/omics_oracle/presentation/web/
├── __init__.py
├── main.py                 # Single FastAPI application
├── dependencies.py         # Proper DI integration
├── middleware/            # Consolidated middleware
├── routes/                # Organized route modules
│   ├── __init__.py
│   ├── search.py          # All search endpoints
│   ├── health.py          # Health checks
│   └── analysis.py        # Analysis endpoints
├── static/                # Single static file location
└── templates/             # If using server-side rendering
```

### Migration Strategy
1. **Audit existing routes**: Identify unique functionality in each interface
2. **Merge capabilities**: Combine best features into single implementation
3. **Update frontend**: Point all frontend code to single API
4. **Archive duplicates**: Move old interfaces to backup/archive

### API Standardization
- Single API version strategy (v2 as primary)
- Consistent response formats
- Proper error handling patterns
- OpenAPI documentation generation

## Benefits
- 70% reduction in duplicate code
- Single source of truth for API functionality
- Easier maintenance and testing
- Clear upgrade path for future features
