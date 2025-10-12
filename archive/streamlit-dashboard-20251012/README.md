# Streamlit Dashboard (Archived)

**Archived Date:** October 12, 2025  
**Reason:** Replaced with HTML/FastAPI dashboard with authentication

## What was archived

- `omics_oracle_v2/lib/dashboard/` - Streamlit dashboard application
- `scripts/run_dashboard.py` - Streamlit dashboard launcher
- `tests/lib/dashboard/` - Streamlit dashboard tests

## Why archived

The Streamlit dashboard lacked authentication and used the old `PublicationSearchPipeline` instead of the new `UnifiedSearchPipeline`. We decided to use the HTML/FastAPI dashboard which:

1. ✅ Has built-in authentication (login/register)
2. ✅ Better integration with FastAPI backend
3. ✅ Consistent with the rest of the API architecture
4. ✅ Easier to integrate with UnifiedSearchPipeline and GEO search

## Streamlit Dashboard Features (preserved for reference)

- Search interface with query preprocessing
- Publication results display
- Search history tracking
- User preferences
- Configurable layouts (default, minimal, research)

## Migration Path

To use the HTML dashboard instead:

1. Access at: `http://localhost:8000/dashboard`
2. Register/Login with authentication
3. Use the same search interface but with:
   - ✅ User authentication
   - ✅ UnifiedSearchPipeline (GEO + Publications)
   - ✅ Full-text PDF download and parsing
   - ✅ AI analysis integration (planned)

## Restoration

If needed, restore with:
```bash
cp -r archive/streamlit-dashboard-20251012/dashboard omics_oracle_v2/lib/
cp archive/streamlit-dashboard-20251012/run_dashboard.py scripts/
cp -r archive/streamlit-dashboard-20251012/dashboard-tests tests/lib/dashboard
```

## Components Archived

### Main Application
- `app.py` (360 lines) - Main Streamlit application
- `components.py` - Reusable UI components
- `config.py` - Dashboard configuration
- `preferences.py` - User preferences management
- `search_history.py` - Search history tracking

### Tests
- `test_app.py` - Application tests
- `test_components.py` - Component tests
- `test_config.py` - Configuration tests
- `test_preferences.py` - Preferences tests
- `test_search_history.py` - Search history tests

### Scripts
- `run_dashboard.py` - Dashboard launcher script

## Related Issues/Commits

This archival is part of the frontend consolidation effort to:
1. Fix CORS authentication issues
2. Integrate UnifiedSearchPipeline with frontend
3. Implement simplified workflow (Search → Auto-process → AI Analysis)
4. Reduce frontend complexity and maintenance burden
