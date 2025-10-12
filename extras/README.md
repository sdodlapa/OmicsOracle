# Extras - Unused Features

This directory contains features that are built but not yet integrated into the main application flow.

## 📁 Directory Structure

### ✅ Ready for Integration
- **workflows/** - Multi-agent workflow orchestration system
  - `routes_workflows.py` - Workflow execution endpoints
  - `routes_workflows_dev.py` - Development workflow endpoints
  - `routes_batch.py` - Batch processing endpoints
  - **Status:** Complete, tested, ready to integrate when needed

### 🔮 Future Features
- **ml_features/** - Machine learning enhanced features
  - `routes_analytics.py` - Biomarker analytics (mock data)
  - `routes_predictions.py` - Trend predictions (mock data)
  - `routes_recommendations.py` - Dataset recommendations (mock data)
  - **Status:** Endpoints defined, need ML model implementation

- **auth_quotas/** - Production authentication and quota system
  - `routes_quotas.py` - User quota management
  - **Status:** Complete, disabled for demo mode

## 🔄 Integration Instructions

### To restore a feature:
1. Move the route file back to `omics_oracle_v2/api/routes/`
2. Update `omics_oracle_v2/api/routes/__init__.py` to import it
3. Update `omics_oracle_v2/api/main.py` to include the router
4. Update frontend to call the new endpoints

### Example (restoring workflows):
```bash
# 1. Move file back
mv extras/workflows/routes_workflows.py omics_oracle_v2/api/routes/workflows.py

# 2. Update routes/__init__.py
# Add: from omics_oracle_v2.api.routes.workflows import router as workflows_router

# 3. Update main.py
# Add: app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])

# 4. Update frontend to call /api/workflows/execute
```

## 📊 Why These Were Moved

Based on analysis of actual frontend usage (dashboard_v2.html), only 3 endpoints are actively used:
- ✅ `/api/agents/search`
- ✅ `/api/agents/enrich-fulltext`
- ✅ `/api/agents/analyze`

All routes in this directory were not called by the production frontend, making them safe to move here temporarily.

## 🎯 Next Steps

See `../STAGE_BY_STAGE_CLEANUP_PLAN.md` for the complete cleanup roadmap.
