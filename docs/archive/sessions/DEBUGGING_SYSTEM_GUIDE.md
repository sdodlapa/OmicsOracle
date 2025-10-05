# 🔍 Comprehensive End-to-End Debugging System

## Overview

A complete observability system to track every query from frontend input to final response, with detailed event tracing, performance metrics, and error tracking.

---

## System Architecture

### 1. **Request Tracing System**

Every query gets a unique `trace_id` that follows it through the entire pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                     Request Trace Lifecycle                  │
└─────────────────────────────────────────────────────────────┘

1. Frontend: User enters query
   └─> trace_id: req_abc123 created

2. API Gateway: Request received
   └─> Event: REQUEST_STARTED logged

3. Workflow Orchestrator: Execution begins
   └─> Event: WORKFLOW_STARTED logged

4. QueryAgent: NLP processing
   ├─> Event: AGENT_STARTED (QueryAgent)
   ├─> External API: OpenAI GPT-4 call
   │   ├─> Event: EXTERNAL_API_CALL (OpenAI)
   │   └─> Event: EXTERNAL_API_RESPONSE (2.3s)
   └─> Event: AGENT_COMPLETED (QueryAgent, 2.5s total)

5. SearchAgent: NCBI GEO search
   ├─> Event: AGENT_STARTED (SearchAgent)
   ├─> External API: NCBI GEO query
   │   ├─> Event: EXTERNAL_API_CALL (NCBI)
   │   └─> Event: EXTERNAL_API_RESPONSE (5.1s)
   ├─> Cache: Check for existing results
   │   └─> Event: CACHE_MISS
   └─> Event: AGENT_COMPLETED (SearchAgent, 5.3s total)

6. DataAgent: Metadata extraction
   ├─> Event: AGENT_STARTED (DataAgent)
   ├─> Database: Query for stored metadata
   │   ├─> Event: DATABASE_QUERY
   │   └─> Event: DATABASE_RESPONSE (0.02s)
   └─> Event: AGENT_COMPLETED (DataAgent, 1.2s total)

7. ReportAgent: Generate final report
   ├─> Event: AGENT_STARTED (ReportAgent)
   ├─> External API: OpenAI GPT-4 for report
   │   ├─> Event: EXTERNAL_API_CALL (OpenAI)
   │   └─> Event: EXTERNAL_API_RESPONSE (3.8s)
   └─> Event: AGENT_COMPLETED (ReportAgent, 4.0s total)

8. Response: Sent to frontend
   └─> Event: REQUEST_COMPLETED

Total Duration: 13.2s
Total Events: 24
Success: ✅
```

---

## Components

### 1. **Core Tracing Module**

**File**: `omics_oracle_v2/tracing/__init__.py`

**Key Classes**:
- `RequestTrace`: Complete trace of a request
- `TraceEvent`: Individual event in the timeline
- `RequestTracer`: Global tracer managing all traces
- `TraceContext`: Context manager for automatic event logging

**Usage in Agents**:
```python
from omics_oracle_v2.tracing import RequestTracer, TraceContext

# Start trace
trace_id = RequestTracer.start_trace(
    query="Find breast cancer datasets",
    workflow_type="full_analysis",
    user_id="user_123"
)

# Trace agent execution
with TraceContext(trace_id, "QueryAgent", "process_query"):
    result = process_nlp(query)

# Complete trace
RequestTracer.complete_trace(
    trace_id,
    success=True,
    datasets_found=25,
    datasets_analyzed=25,
    report_generated=True
)
```

### 2. **Debug Dashboard API**

**File**: `omics_oracle_v2/api/routes/debug.py`

**Endpoints**:
- `GET /debug/dashboard` - Interactive web dashboard
- `GET /debug/traces` - List all traces
- `GET /debug/traces/{trace_id}` - Get specific trace
- `GET /debug/traces/{trace_id}/timeline` - Visual timeline
- `GET /debug/traces/{trace_id}/export` - Export as JSON
- `POST /debug/traces/clear` - Clear old traces

**Access**: http://localhost:8000/debug/dashboard

---

## What You Can Debug

### 1. **Query Journey**

Track exactly what happens to each query:
- When it entered the system
- Which workflow type was selected
- Each agent that processed it
- How long each stage took
- What data was passed between stages
- External API calls made
- Cache hits/misses
- Database queries executed

### 2. **Performance Bottlenecks**

Identify slow components:
```
Agent Performance Breakdown:
- QueryAgent: 2.5s (19%)
- SearchAgent: 5.3s (40%) ⚠️ SLOW
- DataAgent: 1.2s (9%)
- ReportAgent: 4.0s (30%)
Total: 13.0s

Recommendation: SearchAgent is the bottleneck
```

### 3. **Error Analysis**

When something fails, you see:
- Exact error message
- Full stack trace
- Which component failed
- What input caused the failure
- All events leading up to the error

Example:
```json
{
  "event_type": "agent_failed",
  "component": "SearchAgent",
  "action": "search_geo_datasets",
  "error": "NCBI API rate limit exceeded",
  "stack_trace": "...",
  "input_data": {
    "query": "breast cancer RNA-seq",
    "max_results": 50
  },
  "duration_ms": 125.3
}
```

### 4. **External API Monitoring**

Track all external service calls:
- **NCBI GEO**: Search queries, retrieval requests
- **OpenAI**: GPT-4 calls for NLP and report generation
- **Redis**: Cache operations
- **PostgreSQL**: Database queries

```
External API Calls for trace req_abc123:
┌──────────┬────────────────┬──────────┬─────────┬────────┐
│ Service  │ Endpoint       │ Method   │ Duration│ Status │
├──────────┼────────────────┼──────────┼─────────┼────────┤
│ OpenAI   │ /completions   │ POST     │ 2.3s    │ 200    │
│ NCBI     │ /esearch.fcgi  │ GET      │ 5.1s    │ 200    │
│ NCBI     │ /esummary.fcgi │ GET      │ 0.8s    │ 200    │
│ OpenAI   │ /completions   │ POST     │ 3.8s    │ 200    │
└──────────┴────────────────┴──────────┴─────────┴────────┘
Total API Time: 12.0s (91% of total execution)
```

### 5. **Success/Failure Rates**

Monitor system health:
```
Last 100 Queries:
✅ Successful: 87 (87%)
❌ Failed: 13 (13%)

Failure Breakdown:
- NCBI timeout: 7
- Invalid query: 3
- Database error: 2
- Unknown: 1
```

---

## Integration with Existing Code

### Step 1: Add Tracing to Workflow Routes

**File**: `omics_oracle_v2/api/routes/workflows_dev.py`

```python
from omics_oracle_v2.tracing import RequestTracer, TraceContext

@router.post("/dev/execute")
async def execute_workflow(request: WorkflowRequest, orchestrator: Orchestrator):
    # Start trace
    trace_id = RequestTracer.start_trace(
        query=request.query,
        workflow_type=request.workflow_type.value,
        user_id="dev_user"
    )

    try:
        with TraceContext(trace_id, "API", "execute_workflow"):
            result = orchestrator.execute(orchestrator_input)

        # Complete trace
        RequestTracer.complete_trace(
            trace_id,
            success=result.success,
            datasets_found=result.output.total_datasets_found,
            datasets_analyzed=result.output.total_datasets_analyzed,
            report_generated=bool(result.output.final_report)
        )

        # Add trace_id to response for debugging
        response["trace_id"] = trace_id
        return response

    except Exception as e:
        RequestTracer.complete_trace(trace_id, success=False, error_message=str(e))
        raise
```

### Step 2: Add Tracing to Agents

**Example**: `omics_oracle_v2/agents/query_agent.py`

```python
from omics_oracle_v2.tracing import TraceContext, trace_external_api

class QueryAgent(Agent):
    def execute(self, input_data: Dict, trace_id: Optional[str] = None):
        with TraceContext(trace_id, "QueryAgent", "execute"):
            # Process query
            with TraceContext(trace_id, "QueryAgent", "extract_entities"):
                entities = self._extract_entities(input_data["query"])

            # Call OpenAI
            with trace_external_api(trace_id, "OpenAI", "/v1/chat/completions", "POST"):
                response = openai_client.chat.completions.create(...)

            return result
```

### Step 3: Add Tracing to External API Calls

**Example**: NCBI GEO Client

```python
from omics_oracle_v2.tracing import trace_external_api

class GEOClient:
    def search(self, query: str, trace_id: Optional[str] = None):
        with trace_external_api(trace_id, "NCBI_GEO", "/esearch.fcgi", "GET"):
            response = requests.get(url, params=params)
            return response.json()
```

### Step 4: Register Debug Routes

**File**: `omics_oracle_v2/api/main.py`

```python
from omics_oracle_v2.api.routes import debug_router

# Add debug routes
app.include_router(debug_router, tags=["Debug"])
```

---

## Debug Dashboard Features

### Live Monitoring

Access at: **http://localhost:8000/debug/dashboard**

**Features**:
1. **Real-time Updates**: Auto-refreshes every 5 seconds
2. **Success/Failure Stats**: Visual metrics
3. **Recent Traces**: Click to view details
4. **Performance Metrics**: Average execution time
5. **Timeline View**: Visual event timeline for each trace

### Timeline Format

```
================================================================================
TRACE TIMELINE: req_abc123
Query: Find breast cancer RNA-seq datasets
Workflow: full_analysis
Started: 2025-10-05T10:30:45.123Z
Duration: 13200.45ms
Success: True
================================================================================

  1. 🔄 [10:30:45.123] API: execute_workflow
  2. 🔄 [10:30:45.125] Workflow: start_workflow
  3. 🔄 [10:30:45.127] QueryAgent: execute
  4. 🔄 [10:30:45.130] QueryAgent: extract_entities (45.2ms)
  5. 🔄 [10:30:45.175] OpenAI: POST /v1/chat/completions
  6. ✅ [10:30:47.483] OpenAI: POST /v1/chat/completions (2308.0ms)
  7. ✅ [10:30:47.485] QueryAgent: execute (2358.0ms)
  8. 🔄 [10:30:47.487] SearchAgent: execute
  9. 🔄 [10:30:47.490] NCBI_GEO: GET /esearch.fcgi
 10. ✅ [10:30:52.590] NCBI_GEO: GET /esearch.fcgi (5100.0ms)
 11. 🔄 [10:30:52.595] SearchAgent: parse_results (150.3ms)
 12. ✅ [10:30:52.745] SearchAgent: execute (5258.0ms)
 13. 🔄 [10:30:52.750] DataAgent: execute
 14. 🔄 [10:30:52.755] Database: SELECT * FROM dataset_metadata
 15. ✅ [10:30:52.775] Database: SELECT * FROM dataset_metadata (20.0ms)
 16. ✅ [10:30:53.950] DataAgent: execute (1200.0ms)
 17. 🔄 [10:30:53.955] ReportAgent: execute
 18. 🔄 [10:30:53.960] OpenAI: POST /v1/chat/completions
 19. ✅ [10:30:57.760] OpenAI: POST /v1/chat/completions (3800.0ms)
 20. ✅ [10:30:57.955] ReportAgent: execute (4000.0ms)
 21. ✅ [10:30:57.960] Workflow: complete_workflow
 22. ✅ [10:30:57.965] API: execute_workflow

================================================================================
Total Events: 22
Datasets Found: 25
Datasets Analyzed: 25
Report Generated: True
================================================================================
```

---

## Advanced Features

### 1. **Custom Metadata**

Add context-specific data to events:
```python
with TraceContext(trace_id, "SearchAgent", "filter_results") as ctx:
    ctx.metadata = {
        "filter_criteria": {"organism": "human", "min_samples": 10},
        "results_before": 100,
        "results_after": 25
    }
```

### 2. **Nested Events**

Track hierarchical operations:
```python
with TraceContext(trace_id, "Orchestrator", "execute_workflow") as workflow_ctx:
    for agent in agents:
        with TraceContext(trace_id, agent.name, "execute") as agent_ctx:
            agent_ctx.parent_event_id = workflow_ctx.event_id
            agent.execute(...)
```

### 3. **Export for Analysis**

```bash
# Export specific trace
curl http://localhost:8000/debug/traces/req_abc123/export > trace.json

# Analyze in Python
import json
with open('trace.json') as f:
    trace = json.load(f)

# Find slowest operations
events = trace['events']
slowest = sorted(events, key=lambda e: e.get('duration_ms', 0), reverse=True)[:5]
```

---

## Benefits

### For Development
- **Instant Debugging**: See exactly where errors occur
- **Performance Optimization**: Identify bottlenecks immediately
- **Behavior Understanding**: Trace complex multi-agent workflows
- **Testing**: Verify each component works correctly

### For Production
- **Monitoring**: Track system health and performance
- **Error Analysis**: Diagnose production issues quickly
- **User Support**: Understand what went wrong with specific queries
- **Optimization**: Data-driven performance improvements

### For Users
- **Transparency**: Show query processing steps in UI
- **Trust**: Explain why results were returned
- **Feedback**: Help users refine queries
- **Debugging**: Users can report trace IDs for support

---

## Memory Management

Traces are stored in memory. To prevent memory issues:

```python
# Clear old traces automatically (run periodically)
RequestTracer.clear_old_traces(max_age_hours=24)

# Or via API
POST /debug/traces/clear?max_age_hours=24
```

For production, consider:
1. **Persistent Storage**: Store traces in database/S3
2. **Sampling**: Only trace 10% of requests
3. **Async Processing**: Process traces in background
4. **Aggregation**: Store summary metrics, not full traces

---

## Next Steps to Implement

1. **Add tracing to workflow routes** ✅ (Code ready)
2. **Integrate into agents** (20 min)
3. **Add external API tracing** (15 min)
4. **Register debug routes** (5 min)
5. **Test with real queries** (10 min)
6. **Add frontend trace viewer** (optional, 1 hour)

Total implementation time: **~1 hour**

---

## Example: Full Integration

See the complete example in the created files:
- `/omics_oracle_v2/tracing/__init__.py` - Core tracing system
- `/omics_oracle_v2/api/routes/debug.py` - Debug API routes

Ready to integrate when you want end-to-end visibility! 🔍
