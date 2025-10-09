# OmicsOracle API v2 Reference

**⚠️ DEPRECATED - DO NOT USE**  
**Status:** 🗑️ SUPERSEDED BY API_REFERENCE.md v3.0  
**Version:** 2.0 (Phase 3)  
**Date:** October 4, 2025  
**Deprecated:** October 8, 2025 (Phase 4)

---

## ⚠️ DEPRECATION NOTICE

**This document is DEPRECATED and should NOT be used.**

**Reasons:**
1. ❌ **Outdated:** Shows Phase 3 status ("Production Ready" without authentication)
2. ❌ **Security:** States "does not require authentication" - FALSE in Phase 4
3. ❌ **Redundant:** Completely superseded by `API_REFERENCE.md` v3.0
4. ❌ **Confusing:** Using `/api/v1/` paths that are now deprecated
5. ❌ **Incomplete:** Missing Phase 4 features (auth, quotas, multi-agent, etc.)

**Use Instead:**
- 📄 **API_REFERENCE.md v3.0** - Complete Phase 4 API documentation
  - All endpoints with JWT authentication
  - Multi-agent system documented
  - Quotas and rate limiting
  - Cost tracking
  - Phase 4 complete features

- 📄 **API_ENDPOINT_MAPPING.md v2.0** - Endpoint mapping with auth requirements
  - Modern `/api/` paths (not `/api/v1/`)
  - Authentication flow
  - Workflow, Batch, WebSocket APIs
  - Migration guide

**Action:** This file should be **archived** or **deleted** from active documentation.

---

## 📋 Original Overview (OUTDATED - DO NOT USE)

The OmicsOracle v2 API provides a modern, production-ready interface for genomics data processing through an agent-based architecture. Built on FastAPI with comprehensive monitoring, batch processing, and real-time updates via WebSocket.

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.omicsoracle.com`

### API Features
- 🤖 **Agent-Based Architecture**: Specialized agents for different genomics tasks
- 🔄 **Workflow Orchestration**: Coordinated multi-agent workflows
- 📦 **Batch Processing**: Efficient bulk data processing
- ⚡ **Real-time Updates**: WebSocket support for live progress
- 📊 **Monitoring**: Prometheus metrics integration
- 🎨 **Web Dashboard**: Interactive HTML interface
- 📖 **Auto-generated Docs**: OpenAPI/Swagger documentation

### Quick Links
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Dashboard**: http://localhost:8000/dashboard
- **Metrics**: http://localhost:8000/metrics
- **Health**: http://localhost:8000/health

---

## 🔐 Authentication

Currently, the API does not require authentication for development. Production deployments should add authentication middleware.

### Future: API Key Authentication
```http
Authorization: Bearer your-api-key-here
```

---

## 🏥 Health & Status

### Health Check
Check API health and service status.

```http
GET /health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T14:30:00Z",
  "version": "2.0.0",
  "components": {
    "api": "healthy",
    "agents": "healthy",
    "workflows": "healthy"
  }
}
```

### Root Information
Get API information and available endpoints.

```http
GET /
```

**Example Response:**
```json
{
  "name": "OmicsOracle Agent API",
  "version": "2.0.0",
  "description": "Production-ready API for genomics data processing agents",
  "docs": "/docs",
  "dashboard": "/dashboard",
  "health": "/health"
}
```

---

## 🤖 Agent Endpoints

### List Available Agents
Get all available agent types and their capabilities.

```http
GET /api/v1/agents
```

**Example Response:**
```json
{
  "agents": [
    {
      "name": "QueryAgent",
      "description": "Processes natural language queries about genomics data",
      "capabilities": ["query_understanding", "entity_extraction"],
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        }
      }
    },
    {
      "name": "SearchAgent",
      "description": "Searches GEO database for relevant datasets",
      "capabilities": ["geo_search", "dataset_retrieval"],
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "limit": {"type": "integer"}
        }
      }
    },
    {
      "name": "SummaryAgent",
      "description": "Generates AI-powered summaries of genomics datasets",
      "capabilities": ["summarization", "key_points_extraction"],
      "input_schema": {
        "type": "object",
        "properties": {
          "dataset_id": {"type": "string"},
          "max_length": {"type": "integer"}
        }
      }
    }
  ]
}
```

### Query an Agent
Execute a specific agent with input data.

```http
POST /api/v1/agents/{agent_name}
```

**Path Parameters:**
- `agent_name` (string, required): Name of the agent (QueryAgent, SearchAgent, SummaryAgent)

**Request Body:**
```json
{
  "input": {
    "query": "brain cancer methylation studies"
  }
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/QueryAgent" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "brain cancer methylation studies"
    }
  }'
```

**Example Response:**
```json
{
  "agent": "QueryAgent",
  "status": "success",
  "result": {
    "processed_query": "brain cancer methylation studies",
    "entities": {
      "disease": ["brain cancer"],
      "data_type": ["methylation"],
      "study_type": ["studies"]
    },
    "intent": "search_datasets"
  },
  "execution_time": 0.234
}
```

### SearchAgent Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/SearchAgent" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "WGBS brain cancer",
      "limit": 5
    }
  }'
```

**Response:**
```json
{
  "agent": "SearchAgent",
  "status": "success",
  "result": {
    "datasets": [
      {
        "accession": "GSE123456",
        "title": "Whole genome bisulfite sequencing of brain tumors",
        "organism": "Homo sapiens",
        "samples": 24,
        "summary": "Study investigating DNA methylation patterns..."
      }
    ],
    "total_found": 5
  },
  "execution_time": 1.456
}
```

### SummaryAgent Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/SummaryAgent" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "dataset_id": "GSE123456",
      "max_length": 500
    }
  }'
```

**Response:**
```json
{
  "agent": "SummaryAgent",
  "status": "success",
  "result": {
    "summary": "This study investigates DNA methylation patterns in brain tumors using whole genome bisulfite sequencing (WGBS). The research analyzed 24 patient samples and identified significant hypermethylation in tumor suppressor genes associated with poor prognosis.",
    "key_points": [
      "WGBS analysis of 24 brain tumor samples",
      "Hypermethylation in tumor suppressor genes",
      "Association with patient prognosis"
    ],
    "confidence": 0.95
  },
  "execution_time": 2.345
}
```

---

## 🔄 Workflow Endpoints

### Execute Complete Workflow
Run a complete genomics analysis workflow with multiple agents.

```http
POST /api/v1/workflows/{workflow_type}
```

**Path Parameters:**
- `workflow_type` (string, required): Type of workflow
  - `complete` - Full query → search → summarize → export
  - `search` - Query understanding and dataset search only
  - `summarize` - Search and summarization
  - `export` - Full workflow with data export

**Request Body:**
```json
{
  "query": "brain cancer methylation studies",
  "parameters": {
    "max_results": 10,
    "summary_length": 500,
    "export_format": "json"
  }
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/workflows/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "WGBS brain cancer",
    "parameters": {
      "max_results": 5,
      "summary_length": 300
    }
  }'
```

**Example Response:**
```json
{
  "workflow_id": "wf_abc123def456",
  "workflow_type": "complete",
  "status": "completed",
  "query": "WGBS brain cancer",
  "results": {
    "query_analysis": {
      "processed_query": "WGBS brain cancer",
      "entities": {
        "disease": ["brain cancer"],
        "data_type": ["WGBS", "methylation"]
      }
    },
    "search_results": {
      "datasets": [
        {
          "accession": "GSE123456",
          "title": "Whole genome bisulfite sequencing of brain tumors",
          "summary": "..."
        }
      ],
      "total_found": 5
    },
    "summaries": [
      {
        "dataset": "GSE123456",
        "summary": "Comprehensive summary...",
        "key_points": ["..."]
      }
    ]
  },
  "execution_time": 4.567,
  "created_at": "2025-10-04T14:30:00Z",
  "completed_at": "2025-10-04T14:30:04Z"
}
```

### Get Workflow Status
Check the status of a running workflow.

```http
GET /api/v1/workflows/{workflow_id}/status
```

**Example Response:**
```json
{
  "workflow_id": "wf_abc123def456",
  "status": "running",
  "progress": {
    "current_step": "summarization",
    "completed_steps": ["query_analysis", "search"],
    "total_steps": 3,
    "percentage": 66
  },
  "started_at": "2025-10-04T14:30:00Z"
}
```

### Get Workflow Results
Retrieve results of a completed workflow.

```http
GET /api/v1/workflows/{workflow_id}/results
```

**Example Response:**
Same format as workflow execution response.

---

## 📦 Batch Processing Endpoints

### Submit Batch Job
Submit multiple queries for batch processing.

```http
POST /api/v1/batch/jobs
```

**Request Body:**
```json
{
  "workflow_type": "complete",
  "queries": [
    "brain cancer methylation",
    "lung cancer gene expression",
    "diabetes RNA-seq"
  ],
  "parameters": {
    "max_results": 5,
    "summary_length": 300
  },
  "metadata": {
    "project": "cancer_research_2025",
    "researcher": "Dr. Smith"
  }
}
```

**Example Response:**
```json
{
  "job_id": "batch_xyz789",
  "status": "pending",
  "total_workflows": 3,
  "created_at": "2025-10-04T14:30:00Z",
  "estimated_completion": "2025-10-04T14:35:00Z"
}
```

### Get Batch Job Status
Check the status and progress of a batch job.

```http
GET /api/v1/batch/jobs/{job_id}/status
```

**Example Response:**
```json
{
  "job_id": "batch_xyz789",
  "status": "running",
  "progress": {
    "total": 3,
    "completed": 2,
    "failed": 0,
    "percentage": 66.7
  },
  "workflows": [
    {
      "query": "brain cancer methylation",
      "status": "completed",
      "workflow_id": "wf_001"
    },
    {
      "query": "lung cancer gene expression",
      "status": "completed",
      "workflow_id": "wf_002"
    },
    {
      "query": "diabetes RNA-seq",
      "status": "running",
      "workflow_id": "wf_003"
    }
  ],
  "started_at": "2025-10-04T14:30:00Z"
}
```

### Get Batch Job Results
Retrieve all results from a completed batch job.

```http
GET /api/v1/batch/jobs/{job_id}/results
```

**Example Response:**
```json
{
  "job_id": "batch_xyz789",
  "status": "completed",
  "total_workflows": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "query": "brain cancer methylation",
      "workflow_id": "wf_001",
      "status": "completed",
      "result": {
        "datasets": [...],
        "summaries": [...]
      }
    },
    {
      "query": "lung cancer gene expression",
      "workflow_id": "wf_002",
      "status": "completed",
      "result": {
        "datasets": [...],
        "summaries": [...]
      }
    },
    {
      "query": "diabetes RNA-seq",
      "workflow_id": "wf_003",
      "status": "completed",
      "result": {
        "datasets": [...],
        "summaries": [...]
      }
    }
  ],
  "completed_at": "2025-10-04T14:32:30Z"
}
```

### Cancel Batch Job
Cancel a running batch job.

```http
DELETE /api/v1/batch/jobs/{job_id}
```

**Example Response:**
```json
{
  "job_id": "batch_xyz789",
  "status": "cancelled",
  "message": "Batch job cancelled successfully",
  "completed_workflows": 2,
  "cancelled_workflows": 1
}
```

### List Batch Jobs
List all batch jobs with optional filtering.

```http
GET /api/v1/batch/jobs
```

**Query Parameters:**
- `status` (string, optional): Filter by status (pending, running, completed, failed, cancelled)
- `limit` (integer, optional): Results per page (default: 10, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Example Response:**
```json
{
  "jobs": [
    {
      "job_id": "batch_xyz789",
      "status": "completed",
      "total_workflows": 3,
      "created_at": "2025-10-04T14:30:00Z"
    },
    {
      "job_id": "batch_abc456",
      "status": "running",
      "total_workflows": 5,
      "created_at": "2025-10-04T14:25:00Z"
    }
  ],
  "total": 2,
  "limit": 10,
  "offset": 0
}
```

---

## ⚡ WebSocket Endpoints

### Real-time Workflow Updates
Connect to receive real-time updates for workflow execution.

```
WS /ws/workflows/{workflow_id}
```

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflows/wf_abc123');

ws.onopen = () => {
  console.log('Connected to workflow updates');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Workflow update:', update);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from workflow updates');
};
```

**Message Types:**

**Status Update:**
```json
{
  "type": "status",
  "workflow_id": "wf_abc123",
  "status": "running",
  "current_step": "search",
  "timestamp": "2025-10-04T14:30:01Z"
}
```

**Progress Update:**
```json
{
  "type": "progress",
  "workflow_id": "wf_abc123",
  "step": "search",
  "percentage": 50,
  "message": "Searching GEO database...",
  "timestamp": "2025-10-04T14:30:02Z"
}
```

**Result Update:**
```json
{
  "type": "result",
  "workflow_id": "wf_abc123",
  "step": "search",
  "result": {
    "datasets_found": 5
  },
  "timestamp": "2025-10-04T14:30:03Z"
}
```

**Completion:**
```json
{
  "type": "complete",
  "workflow_id": "wf_abc123",
  "status": "completed",
  "final_result": {
    "datasets": [...],
    "summaries": [...]
  },
  "execution_time": 4.567,
  "timestamp": "2025-10-04T14:30:04Z"
}
```

**Error:**
```json
{
  "type": "error",
  "workflow_id": "wf_abc123",
  "error": "Search service unavailable",
  "step": "search",
  "timestamp": "2025-10-04T14:30:02Z"
}
```

---

## 📊 Metrics Endpoint

### Prometheus Metrics
Expose metrics for Prometheus scraping.

```http
GET /metrics
```

**Response Format:** Prometheus text exposition format

**Example Metrics:**
```
# HELP omicsoracle_http_requests_total Total HTTP requests
# TYPE omicsoracle_http_requests_total counter
omicsoracle_http_requests_total{method="GET",endpoint="/health",status="200"} 1234.0

# HELP omicsoracle_http_request_duration_seconds Request duration
# TYPE omicsoracle_http_request_duration_seconds histogram
omicsoracle_http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/workflows/{workflow_type}",le="0.5"} 120.0

# HELP omicsoracle_agent_executions_total Total agent executions
# TYPE omicsoracle_agent_executions_total counter
omicsoracle_agent_executions_total{agent="SearchAgent",status="success"} 456.0

# HELP omicsoracle_workflow_executions_total Total workflow executions
# TYPE omicsoracle_workflow_executions_total counter
omicsoracle_workflow_executions_total{workflow_type="complete",status="completed"} 89.0

# HELP omicsoracle_batch_jobs_total Total batch jobs
# TYPE omicsoracle_batch_jobs_total counter
omicsoracle_batch_jobs_total{status="completed"} 23.0

# HELP omicsoracle_websocket_active_connections Active WebSocket connections
# TYPE omicsoracle_websocket_active_connections gauge
omicsoracle_websocket_active_connections 5.0
```

---

## 🎨 Web Dashboard

### Access Dashboard
Access the interactive web dashboard.

```http
GET /dashboard
```

**Features:**
- Single workflow execution
- Batch workflow submission
- Real-time progress monitoring
- Results visualization
- Job management

**URL:** http://localhost:8000/dashboard

---

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid workflow type",
    "details": {
      "field": "workflow_type",
      "allowed_values": ["complete", "search", "summarize", "export"]
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-10-04T14:30:00Z"
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Errors

**Agent Not Found:**
```json
{
  "error": {
    "type": "AgentNotFoundError",
    "message": "Agent 'InvalidAgent' not found",
    "details": {
      "available_agents": ["QueryAgent", "SearchAgent", "SummaryAgent"]
    }
  }
}
```

**Workflow Not Found:**
```json
{
  "error": {
    "type": "WorkflowNotFoundError",
    "message": "Workflow 'wf_invalid' not found"
  }
}
```

**Batch Job Not Found:**
```json
{
  "error": {
    "type": "BatchJobNotFoundError",
    "message": "Batch job 'batch_invalid' not found"
  }
}
```

---

## 📚 SDKs and Examples

### Python SDK (Coming Soon)
```bash
pip install omics-oracle-sdk
```

```python
from omics_oracle import OmicsOracleClient

# Initialize client
client = OmicsOracleClient(base_url="http://localhost:8000")

# Execute workflow
result = client.workflows.execute(
    workflow_type="complete",
    query="brain cancer methylation",
    parameters={"max_results": 5}
)

# Submit batch job
job = client.batch.submit(
    workflow_type="complete",
    queries=["brain cancer", "lung cancer", "diabetes"],
    parameters={"max_results": 5}
)

# Monitor progress
status = client.batch.get_status(job.job_id)
```

### JavaScript/TypeScript Example
```javascript
// Execute workflow
const response = await fetch('http://localhost:8000/api/v1/workflows/complete', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'brain cancer methylation',
    parameters: {
      max_results: 5
    }
  })
});

const result = await response.json();
console.log(result);
```

### cURL Examples
```bash
# Execute workflow
curl -X POST "http://localhost:8000/api/v1/workflows/complete" \
  -H "Content-Type: application/json" \
  -d '{"query": "brain cancer methylation", "parameters": {"max_results": 5}}'

# Submit batch job
curl -X POST "http://localhost:8000/api/v1/batch/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "complete",
    "queries": ["brain cancer", "lung cancer"],
    "parameters": {"max_results": 5}
  }'

# Get batch status
curl "http://localhost:8000/api/v1/batch/jobs/batch_xyz789/status"
```

---

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8001"]

# Agent Configuration
NCBI_EMAIL=your.email@example.com
NCBI_API_KEY=your_ncbi_api_key
OPENAI_API_KEY=your_openai_api_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 📈 Rate Limiting

Currently no rate limiting is enforced in development. For production:

**Recommended Limits:**
- Workflow execution: 10 requests/minute per IP
- Batch submission: 5 requests/minute per IP
- Agent queries: 20 requests/minute per IP

---

## 🔗 Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Web Dashboard**: http://localhost:8000/dashboard
- **Health Check**: http://localhost:8000/health
- **Prometheus Metrics**: http://localhost:8000/metrics
- **GitHub Repository**: https://github.com/your-org/OmicsOracle

---

*For additional API support and integration examples, visit our GitHub repository or consult the interactive documentation.*
