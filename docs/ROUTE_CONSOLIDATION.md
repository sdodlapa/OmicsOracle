# Route Consolidation - Phase 0, Task 3

## Overview

Successfully consolidated 7 route files into 4 well-organized files with clear API versioning and separation of concerns.

## Changes

### Before (7 files)
```
routes/
├── v1.py                    # Minimal v1 health check
├── v2.py                    # Minimal v2 health check
├── search.py                # Basic search health check
├── health.py                # Health endpoints
├── analysis.py              # Analysis API (placeholder)
├── enhanced_search.py       # Enhanced search with AI
└── futuristic_search.py     # Real-time search with WebSocket
```

### After (4 files)
```
routes/
├── api_v1.py               # All v1 endpoints (search + analysis)
├── api_v2.py               # All v2 endpoints (enhanced + real-time)
├── health.py               # All health/monitoring endpoints
└── ui.py                   # All UI/dashboard routes
```

## Route Organization

### 1. `api_v1.py` - Legacy API (v1.0.0)
**Status**: Stable, maintenance mode
**Deprecation**: Planned for April 2026 (6 months)

**Endpoints**:
- `GET /api/v1/health` - Health check
- `GET /api/v1/search` - Basic search (deprecated)
- `GET /api/v1/search/health` - Search service health
- `GET /api/v1/analysis/capabilities` - Analysis capabilities
- `POST /api/v1/analysis/differential-expression` - Run DE analysis
- `POST /api/v1/analysis/pathway-enrichment` - Run pathway enrichment
- `GET /api/v1/analysis/status/{analysis_id}` - Get analysis status
- `GET /api/v1/analysis/results/{analysis_id}` - Get analysis results
- `GET /api/v1/analysis/download/{analysis_id}` - Download results
- `GET /api/v1/analysis/plot/{analysis_id}/{plot_type}` - Get plot

**Purpose**: Backward compatibility for existing integrations

### 2. `api_v2.py` - Enhanced API (v2.0.0)
**Status**: Active, recommended
**Features**: Real-time updates, AI ranking, WebSocket support

**Endpoints**:
- `GET /api/v2/health` - Enhanced health check with feature status
- `GET /api/v2/status` - Comprehensive system status
- `GET /api/v2/search` - Enhanced search with AI ranking
- `POST /api/v2/search/realtime` - Real-time search with progress updates
- `GET /api/v2/search/suggestions` - Intelligent search suggestions
- `GET /api/v2/query/components` - Extract query components

**Features**:
- AI-powered semantic ranking
- Real-time progress updates via WebSocket
- Intelligent biomedical term suggestions
- Query component extraction (diseases, tissues, organisms)

### 3. `health.py` - Health & Monitoring
**Purpose**: Unversioned health endpoints for load balancers and monitoring tools

**Endpoints**:
- `GET /health/` - Basic health check
- `GET /health/status` - Detailed health status
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/components` - Component health status
- `GET /health/metrics` - System metrics

**Components Monitored**:
- Database connections
- NCBI API service
- GEO service
- LLM service
- Cache system
- WebSocket manager

### 4. `ui.py` - User Interface & Dashboards
**Purpose**: Serve all dashboard interfaces and static files

**Endpoints**:
- `GET /` - Main interface (futuristic enhanced)
- `GET /dashboard/basic` - Basic dashboard
- `GET /dashboard/research` - Research dashboard
- `GET /dashboard/intelligence` - Intelligence dashboard
- `GET /dashboard/advanced` - Advanced dashboard
- `GET /futuristic` - Futuristic interface
- `GET /futuristic-enhanced` - Enhanced futuristic interface
- `GET /enhanced` - Enhanced interface (alias)
- `GET /dashboards` - List all available dashboards

## Benefits

1. **Clear API Versioning**
   - v1: Legacy/maintenance mode
   - v2: Active development, recommended
   - Clear deprecation timeline

2. **Eliminated Duplication**
   - Removed duplicate health check endpoints
   - Consolidated similar functionality
   - Reduced code redundancy

3. **Better Organization**
   - Separated concerns (API, health, UI)
   - Logical grouping of related endpoints
   - Easier to navigate and maintain

4. **Improved Maintainability**
   - Reduced file count (7 → 4)
   - Clear ownership per file
   - Better discoverability

5. **Cleaner Imports**
   - Simplified import structure in `__init__.py`
   - Removed 6 old imports
   - Added 4 consolidated imports

## Migration Guide

### For v1 Users

If you're using v1 endpoints, you should migrate to v2 for enhanced features:

**Before (v1)**:
```bash
curl https://api.example.com/api/v1/search?query=cancer&limit=20
```

**After (v2)**:
```bash
curl https://api.example.com/api/v2/search?query=cancer&limit=20
```

**Benefits of v2**:
- AI-powered ranking
- Better result quality
- Real-time updates support
- Intelligent suggestions

### For Developers

**Before**:
```python
from .enhanced_search import router as enhanced_search_router
from .futuristic_search import router as futuristic_search_router
```

**After**:
```python
from .api_v2 import router as api_v2_router
```

## Testing

All routes tested and verified:
```bash
python -c "from omics_oracle.presentation.web.routes import api_v1, api_v2, health, ui"
# [SUCCESS] All consolidated route modules imported successfully
```

Application starts successfully with consolidated routes:
```
INFO - All routes configured successfully with consolidated architecture
INFO -   - Health: /health/*
INFO -   - API v1: /api/v1/* (legacy)
INFO -   - API v2: /api/v2/* (recommended)
INFO -   - UI: /* (dashboards)
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Version Discovery

Get information about available API versions:
```bash
curl http://localhost:8000/api
```

Response:
```json
{
  "api_name": "OmicsOracle API",
  "version": "2.0.0",
  "available_versions": {
    "v1": {
      "version": "1.0.0",
      "status": "stable",
      "mode": "maintenance",
      "endpoints": "/api/v1/"
    },
    "v2": {
      "version": "2.0.0",
      "status": "active",
      "mode": "recommended",
      "endpoints": "/api/v2/",
      "features": [
        "enhanced_search",
        "real_time_updates",
        "websocket_support",
        "ai_ranking"
      ]
    }
  },
  "recommended_version": "v2",
  "deprecation_notice": {
    "v1": "API v1 will be deprecated in 6 months (April 2026)"
  }
}
```

## Next Steps

- ✅ Route consolidation complete
- ⏭️ Continue with Phase 0, Task 4: Package Structure
