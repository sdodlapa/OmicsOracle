# Phase 3: Agent Framework API & Web Interface

**Project**: OmicsOracle v2 Refactoring
**Phase**: 3 - Agent API & Web Interface
**Status**: 🚀 **PLANNING**
**Start Date**: October 4, 2025
**Estimated Duration**: 2-3 weeks
**Branch**: `phase-3-agent-api`

---

## 🎯 Phase 3 Objectives

Build a comprehensive REST API and web interface on top of the Phase 2 agent framework, enabling:
- RESTful API for agent workflows
- Real-time progress tracking via WebSockets
- Interactive web dashboard
- Batch processing capabilities
- Monitoring and observability

---

## 📋 Prerequisites

### Phase 2 Completion Status
- ✅ All 5 agents implemented and tested (Query, Search, Data, Report, Orchestrator)
- ✅ 173 agent tests passing (100%)
- ✅ Integration tests complete (24 tests)
- ✅ Comprehensive documentation
- ✅ Working examples

### Technical Requirements
- ✅ Python 3.11+
- ✅ FastAPI framework
- ✅ WebSocket support
- ✅ PostgreSQL (optional, for persistence)
- ✅ Redis (optional, for caching)

---

## 🗓️ Implementation Plan

### **Task 1: FastAPI Application Setup** (Days 1-2)

**Goal**: Create base FastAPI application with agent integration

**Deliverables**:
1. `omics_oracle_v2/api/__init__.py` - API package
2. `omics_oracle_v2/api/main.py` - FastAPI application factory
3. `omics_oracle_v2/api/config.py` - API configuration
4. `omics_oracle_v2/api/dependencies.py` - Dependency injection
5. `omics_oracle_v2/api/middleware.py` - CORS, auth, logging

**API Structure**:
```python
from fastapi import FastAPI
from omics_oracle_v2.core import Settings
from omics_oracle_v2.agents import Orchestrator

def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="OmicsOracle Agent API",
        description="Multi-agent biomedical research platform",
        version="2.0.0"
    )

    # Add middleware
    app.add_middleware(CORSMiddleware, ...)
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers
    app.include_router(agent_router, prefix="/api/v1/agents")
    app.include_router(workflow_router, prefix="/api/v1/workflows")
    app.include_router(health_router, prefix="/health")

    return app
```

**Success Criteria**:
- FastAPI app starts successfully
- Health check endpoint working
- OpenAPI docs accessible at `/docs`
- CORS configured for web interface
- Logging middleware capturing requests

**Tests**: 10 tests
- App creation
- Health endpoint
- OpenAPI schema
- Middleware functionality
- CORS headers

---

### **Task 2: Agent Execution Endpoints** (Days 3-4)

**Goal**: Create REST endpoints for executing individual agents

**Deliverables**:
1. `omics_oracle_v2/api/routes/__init__.py`
2. `omics_oracle_v2/api/routes/agents.py` - Agent execution endpoints
3. `omics_oracle_v2/api/models/requests.py` - Request models
4. `omics_oracle_v2/api/models/responses.py` - Response models

**Endpoints**:

#### 1. **Query Agent**
```
POST /api/v1/agents/query
Body: {"query": "breast cancer RNA-seq"}
Response: {
  "entities": [...],
  "intent": "search_datasets",
  "search_terms": ["breast cancer", "RNA-seq"],
  "confidence": 0.95
}
```

#### 2. **Search Agent**
```
POST /api/v1/agents/search
Body: {
  "search_terms": ["breast cancer"],
  "filters": {"organism": "Homo sapiens"},
  "max_results": 20
}
Response: {
  "total_found": 150,
  "ranked_datasets": [...],
  "execution_time_ms": 5234
}
```

#### 3. **Data Agent**
```
POST /api/v1/agents/data
Body: {"datasets": [...]}
Response: {
  "processed_datasets": [...],
  "quality_stats": {...}
}
```

#### 4. **Report Agent**
```
POST /api/v1/agents/report
Body: {
  "datasets": [...],
  "report_type": "comprehensive",
  "format": "markdown"
}
Response: {
  "full_report": "...",
  "key_findings": [...],
  "recommendations": [...]
}
```

**Success Criteria**:
- All 4 agent endpoints working
- Proper error handling
- Request validation with Pydantic
- Response serialization
- Execution time tracking

**Tests**: 20 tests
- Each endpoint with valid input
- Invalid input validation
- Error scenarios
- Response format validation
- Performance tracking

---

### **Task 3: Workflow Orchestration Endpoints** (Days 5-6)

**Goal**: Create endpoints for orchestrated multi-agent workflows

**Deliverables**:
1. `omics_oracle_v2/api/routes/workflows.py` - Workflow endpoints
2. `omics_oracle_v2/api/models/workflows.py` - Workflow models
3. `omics_oracle_v2/api/services/workflow_manager.py` - Workflow state management

**Endpoints**:

#### 1. **Start Workflow**
```
POST /api/v1/workflows
Body: {
  "query": "breast cancer RNA-seq studies",
  "workflow_type": "full_analysis",
  "options": {
    "max_datasets": 10,
    "report_type": "comprehensive"
  }
}
Response: {
  "workflow_id": "wf_abc123",
  "status": "running",
  "created_at": "2025-10-04T10:00:00Z"
}
```

#### 2. **Get Workflow Status**
```
GET /api/v1/workflows/{workflow_id}
Response: {
  "workflow_id": "wf_abc123",
  "status": "completed",
  "current_stage": "report_generation",
  "progress": 0.75,
  "results": {...}
}
```

#### 3. **List Workflows**
```
GET /api/v1/workflows?status=completed&limit=20
Response: {
  "workflows": [...],
  "total": 45,
  "page": 1
}
```

#### 4. **Cancel Workflow**
```
DELETE /api/v1/workflows/{workflow_id}
Response: {
  "workflow_id": "wf_abc123",
  "status": "cancelled"
}
```

**Success Criteria**:
- Workflow creation and tracking
- Async execution support
- Status polling working
- Cancellation functionality
- Workflow history storage

**Tests**: 15 tests
- Workflow creation
- Status tracking
- Listing with filters
- Cancellation
- Error handling

---

### **Task 4: WebSocket Real-time Updates** (Days 7-8)

**Goal**: Implement WebSocket endpoints for real-time progress updates

**Deliverables**:
1. `omics_oracle_v2/api/websockets/__init__.py`
2. `omics_oracle_v2/api/websockets/workflow.py` - Workflow WebSocket handler
3. `omics_oracle_v2/api/websockets/manager.py` - Connection manager
4. `omics_oracle_v2/api/models/events.py` - Event models

**WebSocket Endpoints**:

#### 1. **Workflow Progress Stream**
```
WS /ws/workflows/{workflow_id}

Events:
{
  "type": "stage_started",
  "stage": "query_processing",
  "timestamp": "2025-10-04T10:00:01Z"
}

{
  "type": "stage_completed",
  "stage": "query_processing",
  "result": {...},
  "execution_time_ms": 1500
}

{
  "type": "workflow_completed",
  "final_result": {...}
}
```

#### 2. **Agent Activity Stream**
```
WS /ws/agents

Events:
{
  "type": "agent_started",
  "agent": "query_agent",
  "workflow_id": "wf_abc123"
}
```

**Success Criteria**:
- WebSocket connections established
- Real-time event streaming
- Connection management
- Reconnection handling
- Multiple client support

**Tests**: 12 tests
- Connection establishment
- Event streaming
- Disconnection handling
- Multiple connections
- Error scenarios

---

### **Task 5: Batch Processing API** (Days 9-10)

**Goal**: Enable batch processing of multiple queries

**Deliverables**:
1. `omics_oracle_v2/api/routes/batch.py` - Batch endpoints
2. `omics_oracle_v2/api/services/batch_processor.py` - Batch processing logic
3. `omics_oracle_v2/api/models/batch.py` - Batch models

**Endpoints**:

#### 1. **Submit Batch**
```
POST /api/v1/batch
Body: {
  "queries": [
    {"query": "breast cancer", "workflow_type": "simple_search"},
    {"query": "lung cancer", "workflow_type": "simple_search"}
  ],
  "options": {"parallel": true, "max_concurrent": 3}
}
Response: {
  "batch_id": "batch_xyz789",
  "total_jobs": 2,
  "status": "queued"
}
```

#### 2. **Get Batch Status**
```
GET /api/v1/batch/{batch_id}
Response: {
  "batch_id": "batch_xyz789",
  "total_jobs": 2,
  "completed": 1,
  "failed": 0,
  "progress": 0.5,
  "results": [...]
}
```

**Success Criteria**:
- Batch submission working
- Parallel execution
- Progress tracking
- Result aggregation
- Error handling

**Tests**: 10 tests
- Batch creation
- Parallel execution
- Progress tracking
- Result collection
- Error scenarios

---

### **Task 6: Web Dashboard Interface** (Days 11-13)

**Goal**: Create interactive web dashboard for agent workflows

**Deliverables**:
1. `omics_oracle_v2/web/index.html` - Main dashboard
2. `omics_oracle_v2/web/static/css/dashboard.css` - Styles
3. `omics_oracle_v2/web/static/js/dashboard.js` - Dashboard logic
4. `omics_oracle_v2/web/static/js/websocket-client.js` - WebSocket client
5. `omics_oracle_v2/web/templates/` - HTML templates

**Dashboard Features**:

1. **Query Interface**
   - Text input for natural language queries
   - Workflow type selection
   - Advanced options panel

2. **Real-time Progress**
   - Stage progression visualization
   - Live execution time
   - Agent status indicators

3. **Results Display**
   - Dataset cards with metadata
   - Quality scores visualization
   - Report preview

4. **Workflow History**
   - Past workflows list
   - Status filters
   - Result access

5. **Batch Interface**
   - Multi-query input
   - Batch progress tracking
   - Results export

**UI Components**:
```html
<!-- Query Interface -->
<div class="query-panel">
  <textarea id="query-input" placeholder="Enter your research query..."></textarea>
  <select id="workflow-type">
    <option value="simple_search">Quick Search</option>
    <option value="full_analysis">Full Analysis</option>
  </select>
  <button id="submit-btn">Run Workflow</button>
</div>

<!-- Progress Tracker -->
<div class="progress-panel">
  <div class="stage active">Query Processing</div>
  <div class="stage">Dataset Search</div>
  <div class="stage">Quality Validation</div>
  <div class="stage">Report Generation</div>
</div>

<!-- Results Display -->
<div class="results-panel">
  <!-- Dataset cards populated via JavaScript -->
</div>
```

**Success Criteria**:
- Responsive web interface
- Real-time updates via WebSocket
- Interactive visualizations
- Mobile-friendly design
- Fast page load (<2s)

**Tests**: 8 integration tests
- Page load
- Query submission
- WebSocket connection
- Result display
- Error handling

---

### **Task 7: Monitoring & Observability** (Days 14-15)

**Goal**: Add monitoring, metrics, and logging

**Deliverables**:
1. `omics_oracle_v2/api/monitoring/__init__.py`
2. `omics_oracle_v2/api/monitoring/metrics.py` - Prometheus metrics
3. `omics_oracle_v2/api/monitoring/logging.py` - Structured logging
4. `omics_oracle_v2/api/routes/monitoring.py` - Monitoring endpoints

**Endpoints**:

#### 1. **Metrics**
```
GET /metrics
Response: Prometheus format metrics

# Agent execution metrics
agent_executions_total{agent="query_agent",status="success"} 1234
agent_execution_duration_seconds{agent="query_agent"} 2.5

# Workflow metrics
workflow_executions_total{workflow_type="full_analysis"} 567
workflow_duration_seconds{workflow_type="full_analysis"} 25.3

# API metrics
http_requests_total{method="POST",endpoint="/api/v1/workflows"} 890
http_request_duration_seconds{endpoint="/api/v1/workflows"} 0.5
```

#### 2. **System Health**
```
GET /health/detailed
Response: {
  "status": "healthy",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "ncbi_api": "healthy",
    "openai_api": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "total_workflows": 567,
    "active_workflows": 3
  }
}
```

#### 3. **Agent Statistics**
```
GET /api/v1/stats/agents
Response: {
  "query_agent": {
    "total_executions": 1234,
    "avg_duration_ms": 2500,
    "success_rate": 0.98
  },
  ...
}
```

**Success Criteria**:
- Prometheus metrics exposed
- Structured logging implemented
- Health checks comprehensive
- Performance dashboards
- Error tracking

**Tests**: 8 tests
- Metrics endpoint
- Health checks
- Statistics accuracy
- Logging format
- Performance tracking

---

### **Task 8: Documentation & Deployment** (Days 16-17)

**Goal**: Complete API documentation and deployment setup

**Deliverables**:
1. `docs/API_REFERENCE.md` - Complete API documentation
2. `docs/WEB_INTERFACE_GUIDE.md` - Web interface user guide
3. `docs/DEPLOYMENT.md` - Deployment instructions
4. `docker-compose-api.yml` - Docker Compose setup
5. `Dockerfile.api` - API container
6. `README-API.md` - Quick start guide

**Documentation Sections**:

1. **API Reference**
   - All endpoints documented
   - Request/response examples
   - Authentication guide
   - Rate limiting
   - Error codes

2. **Web Interface Guide**
   - Getting started
   - Feature overview
   - Workflow creation
   - Result interpretation
   - Troubleshooting

3. **Deployment Guide**
   - Docker deployment
   - Environment variables
   - Scaling considerations
   - Monitoring setup
   - Security best practices

**Docker Setup**:
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - NCBI_EMAIL=${NCBI_EMAIL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/omics
    depends_on:
      - db
      - redis

  web:
    build:
      context: omics_oracle_v2/web
    ports:
      - "3000:80"
    depends_on:
      - api

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  prometheus:
    image: prom/prometheus
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  postgres_data:
```

**Success Criteria**:
- Complete API documentation
- Docker Compose working
- Deployment guide clear
- Quick start functional
- All examples tested

---

## 📊 Success Metrics

### Code Metrics
| Metric | Target |
|--------|--------|
| API Endpoints | 20+ |
| WebSocket Endpoints | 2+ |
| Unit Tests | 70+ |
| Integration Tests | 20+ |
| Documentation Pages | 5+ |

### Quality Metrics
| Metric | Target |
|--------|--------|
| Test Coverage | >80% |
| API Response Time | <500ms (avg) |
| WebSocket Latency | <100ms |
| Page Load Time | <2s |
| Uptime | >99% |

### Performance Metrics
| Metric | Target |
|--------|--------|
| Concurrent Workflows | 10+ |
| Batch Size | 50+ queries |
| WebSocket Connections | 100+ |
| Requests/Second | 100+ |

---

## 🧪 Testing Strategy

### Unit Tests (~70 tests)
- FastAPI app creation
- Endpoint handlers
- Request validation
- Response serialization
- WebSocket handlers
- Batch processing logic
- Metrics collection

### Integration Tests (~20 tests)
- End-to-end workflow execution
- WebSocket real-time updates
- Batch processing
- Database persistence
- Cache functionality
- External API integration

### Load Tests
- 100 concurrent users
- 1000 workflows/hour
- WebSocket stability
- Database performance
- Cache effectiveness

---

## 🗂️ File Structure

```
omics_oracle_v2/
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # API configuration
│   ├── dependencies.py            # Dependency injection
│   ├── middleware.py              # Custom middleware
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── agents.py              # Agent endpoints
│   │   ├── workflows.py           # Workflow endpoints
│   │   ├── batch.py               # Batch endpoints
│   │   ├── monitoring.py          # Monitoring endpoints
│   │   └── health.py              # Health checks
│   ├── websockets/
│   │   ├── __init__.py
│   │   ├── workflow.py            # Workflow WebSocket
│   │   └── manager.py             # Connection manager
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py            # Request models
│   │   ├── responses.py           # Response models
│   │   ├── workflows.py           # Workflow models
│   │   ├── batch.py               # Batch models
│   │   └── events.py              # WebSocket events
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workflow_manager.py    # Workflow state
│   │   └── batch_processor.py     # Batch processing
│   └── monitoring/
│       ├── __init__.py
│       ├── metrics.py             # Prometheus metrics
│       └── logging.py             # Structured logging
├── web/
│   ├── index.html                 # Main dashboard
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   └── js/
│   │       ├── dashboard.js
│   │       └── websocket-client.js
│   └── templates/
│       ├── workflow.html
│       └── batch.html
└── tests/
    ├── api/
    │   ├── test_main.py
    │   ├── test_agents.py
    │   ├── test_workflows.py
    │   ├── test_batch.py
    │   └── test_websockets.py
    └── integration/
        ├── test_api_integration.py
        └── test_websocket_integration.py
```

---

## 🚀 Getting Started (After Completion)

### Start API Server
```bash
cd OmicsOracle
export NCBI_EMAIL="your@email.com"
export OPENAI_API_KEY="sk-..."

# Development
uvicorn omics_oracle_v2.api.main:app --reload --port 8000

# Production
docker-compose -f docker-compose-api.yml up
```

### Access Endpoints
- **API Docs**: http://localhost:8000/docs
- **Web Dashboard**: http://localhost:3000
- **Metrics**: http://localhost:8000/metrics
- **Health**: http://localhost:8000/health

### Example API Usage
```bash
# Start a workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "query": "breast cancer RNA-seq studies",
    "workflow_type": "full_analysis"
  }'

# Check status
curl http://localhost:8000/api/v1/workflows/{workflow_id}

# Get results
curl http://localhost:8000/api/v1/workflows/{workflow_id}/results
```

---

## 📝 Handoff to Phase 4

After Phase 3 completion, we will have:
- ✅ Full REST API for agent framework
- ✅ Real-time WebSocket updates
- ✅ Interactive web dashboard
- ✅ Batch processing capability
- ✅ Comprehensive monitoring
- ✅ Production-ready deployment

**Phase 4 Focus Areas**:
1. Advanced analytics and visualizations
2. User authentication and authorization
3. Workflow templates and presets
4. Advanced filtering and search
5. Export and sharing features
6. Performance optimization
7. Mobile application

---

## 🎯 Risk Management

### Identified Risks
1. **WebSocket Stability**: Complex state management
   - Mitigation: Thorough testing, reconnection logic

2. **Performance**: Large number of concurrent workflows
   - Mitigation: Queue system, rate limiting, caching

3. **API Breaking Changes**: Agent interface changes
   - Mitigation: API versioning, deprecation warnings

4. **Security**: API authentication required
   - Mitigation: JWT tokens, rate limiting, input validation

---

## ✅ Phase 3 Checklist

### Pre-Phase
- [ ] Phase 2 completion verified
- [ ] Development environment ready
- [ ] Branch created: `phase-3-agent-api`
- [ ] Dependencies installed

### Task Checklist
- [ ] Task 1: FastAPI app setup (10 tests)
- [ ] Task 2: Agent endpoints (20 tests)
- [ ] Task 3: Workflow endpoints (15 tests)
- [ ] Task 4: WebSocket support (12 tests)
- [ ] Task 5: Batch processing (10 tests)
- [ ] Task 6: Web dashboard (8 tests)
- [ ] Task 7: Monitoring (8 tests)
- [ ] Task 8: Documentation & deployment

### Post-Phase
- [ ] All tests passing (90+ tests)
- [ ] Documentation complete
- [ ] Docker Compose working
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Ready for Phase 4

---

**Phase 3 Status**: 🚀 **READY TO START**
**Next Action**: Create branch and begin Task 1 (FastAPI Setup)
