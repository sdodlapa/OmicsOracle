# v2 Comprehensive Testing Plan

**Date:** October 4, 2024
**Scope:** Complete testing of OmicsOracle v2 system before v2.1.0 release
**Status:** 🔴 CRITICAL - Testing gaps identified
**Timeline:** 5-6 weeks

---

## Executive Summary

The critical review identified **major testing gaps** in the v2 system. While authentication and rate limiting have excellent test coverage (69 tests), the core API functionality (agents, workflows, batch processing, WebSocket) has **ZERO tests**.

### Current Test Coverage

```
Authentication:        ✅ 25 tests (95% coverage)
Rate Limiting:         ✅ 44 tests (98% coverage)
Agents API:            🔴 0 tests (0% coverage)
Workflows API:         🔴 0 tests (0% coverage)
Batch API:             🔴 0 tests (0% coverage)
WebSocket API:         🔴 0 tests (0% coverage)
Middleware:            ⚠️ 24 tests (partial coverage)
Integration Tests:     🔴 0 tests
End-to-End Tests:      🔴 0 tests
Load Tests:            🔴 0 tests
```

### Testing Priorities

1. **🔴 CRITICAL (Week 1-2)** - Release blockers
   - Manual testing of all API endpoints
   - Automated tests for agents, workflows, batch, WebSocket
   - Web dashboard testing
   - Basic integration tests

2. **🟡 MEDIUM (Week 3)** - Important for production
   - Security testing
   - Load testing
   - Error handling tests
   - Middleware tests completion

3. **🟢 LOW (Week 4-5)** - Nice to have
   - Advanced integration tests
   - Performance benchmarks
   - Chaos engineering tests

---

## Part 1: Manual Testing (Week 1)

### 1.1 Environment Setup

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Start Redis
docker-compose up -d redis

# Run migrations
alembic upgrade head

# Start server
uvicorn omics_oracle_v2.api.main:app --reload --log-level debug

# Server runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
# Alternative docs: http://localhost:8000/redoc
```

### 1.2 Manual API Testing Checklist

#### Step 1: Health & Metrics Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

# Metrics
curl http://localhost:8000/metrics

# Expected: Prometheus metrics format
```

#### Step 2: Authentication Flow
```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "username": "testuser"
  }'

# Expected: {"id": 1, "email": "test@example.com", "username": "testuser", ...}

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'

# Expected: {"access_token": "eyJ...", "token_type": "bearer"}
# Save token for next requests: export TOKEN="<access_token>"
```

#### Step 3: Agents API Testing
```bash
# List available agents
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/agents

# Expected: [{"id": "ner", "name": "Named Entity Recognition", ...}, ...]

# Execute agent (NER example)
curl -X POST http://localhost:8000/api/agents/ner/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aspirin is used to treat fever and pain.",
    "parameters": {}
  }'

# Expected: {"task_id": "abc123", "status": "queued", ...}

# Get agent results
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/agents/tasks/abc123

# Expected: {"task_id": "abc123", "status": "completed", "result": {...}}

# Test all agents:
# - ner (Named Entity Recognition)
# - rel_extraction (Relation Extraction)
# - pathway_analysis (Pathway Analysis)
# - literature_search (Literature Search)
# - data_integration (Data Integration)
```

#### Step 4: Workflows API Testing
```bash
# List workflows
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/workflows

# Expected: [{"id": "workflow-1", "name": "Drug Discovery", ...}, ...]

# Create new workflow
curl -X POST http://localhost:8000/api/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "Testing workflow creation",
    "steps": [
      {"agent": "ner", "order": 1},
      {"agent": "rel_extraction", "order": 2}
    ]
  }'

# Expected: {"id": "workflow-xyz", "name": "Test Workflow", ...}

# Execute workflow
curl -X POST http://localhost:8000/api/workflows/workflow-xyz/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"text": "Aspirin treats pain."},
    "parameters": {}
  }'

# Expected: {"execution_id": "exec-123", "status": "running", ...}

# Get workflow results
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/workflows/executions/exec-123

# Expected: {"execution_id": "exec-123", "status": "completed", "results": {...}}
```

#### Step 5: Batch Processing Testing
```bash
# Create batch job
curl -X POST http://localhost:8000/api/batch/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "ner",
    "inputs": [
      {"text": "Aspirin treats pain."},
      {"text": "Ibuprofen reduces inflammation."},
      {"text": "Acetaminophen lowers fever."}
    ]
  }'

# Expected: {"job_id": "batch-456", "status": "queued", "total_items": 3}

# Get batch status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/batch/jobs/batch-456

# Expected: {"job_id": "batch-456", "status": "processing", "completed": 2, "total": 3}

# Get batch results
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/batch/jobs/batch-456/results

# Expected: [{"input": {...}, "result": {...}, "status": "completed"}, ...]
```

#### Step 6: WebSocket Testing
```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/ws?token=$TOKEN"

# Send message
> {"type": "subscribe", "channel": "tasks"}

# Expected: Real-time task updates
< {"type": "task_update", "task_id": "abc123", "status": "completed"}
```

#### Step 7: Quota Management Testing
```bash
# Get current quota
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v2/quotas/me

# Expected: {"user_id": 1, "tier": "free", "requests_remaining": 100, ...}

# Update quota (admin only)
curl -X PUT http://localhost:8000/api/v2/quotas/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "premium",
    "monthly_limit": 10000
  }'

# Expected: {"user_id": 1, "tier": "premium", "monthly_limit": 10000}
```

### 1.3 Web Dashboard Testing

```bash
# Open dashboard in browser
open http://localhost:8000/static/dashboard.html
# or: python -m webbrowser http://localhost:8000/static/dashboard.html
```

#### Dashboard Checklist
- [ ] **Login Page**
  - [ ] Login form displays correctly
  - [ ] Can login with valid credentials
  - [ ] Error message on invalid credentials
  - [ ] Can register new account
  - [ ] Can logout

- [ ] **Dashboard Home**
  - [ ] User info displays (email, tier, quota)
  - [ ] Navigation menu works
  - [ ] Quota usage charts display

- [ ] **Agents Page**
  - [ ] List of agents displays
  - [ ] Can select an agent
  - [ ] Can execute agent with text input
  - [ ] Results display correctly
  - [ ] Error handling works

- [ ] **Workflows Page**
  - [ ] List of workflows displays
  - [ ] Can create new workflow
  - [ ] Can execute workflow
  - [ ] Results display correctly
  - [ ] Can delete workflow

- [ ] **Batch Processing Page**
  - [ ] Can create batch job
  - [ ] Progress bar updates
  - [ ] Can view results
  - [ ] Can download results

- [ ] **Real-time Updates**
  - [ ] WebSocket connects successfully
  - [ ] Real-time task updates display
  - [ ] Notifications work
  - [ ] Connection loss handled gracefully

### 1.4 Manual Testing Results Template

Create: `docs/testing/MANUAL_TESTING_RESULTS.md`

```markdown
# Manual Testing Results - Date: YYYY-MM-DD

## Health & Metrics
- [ ] Health check: ✅ / ❌ - Notes:
- [ ] Metrics endpoint: ✅ / ❌ - Notes:

## Authentication
- [ ] Register: ✅ / ❌ - Notes:
- [ ] Login: ✅ / ❌ - Notes:
- [ ] Logout: ✅ / ❌ - Notes:

## Agents API
- [ ] List agents: ✅ / ❌ - Notes:
- [ ] Execute NER: ✅ / ❌ - Notes:
- [ ] Execute Rel Extraction: ✅ / ❌ - Notes:
- [ ] Get task results: ✅ / ❌ - Notes:

## Workflows API
- [ ] List workflows: ✅ / ❌ - Notes:
- [ ] Create workflow: ✅ / ❌ - Notes:
- [ ] Execute workflow: ✅ / ❌ - Notes:
- [ ] Get results: ✅ / ❌ - Notes:

## Batch API
- [ ] Create batch job: ✅ / ❌ - Notes:
- [ ] Get status: ✅ / ❌ - Notes:
- [ ] Get results: ✅ / ❌ - Notes:

## WebSocket
- [ ] Connect: ✅ / ❌ - Notes:
- [ ] Subscribe: ✅ / ❌ - Notes:
- [ ] Receive updates: ✅ / ❌ - Notes:

## Web Dashboard
- [ ] Login: ✅ / ❌ - Notes:
- [ ] Agents page: ✅ / ❌ - Notes:
- [ ] Workflows page: ✅ / ❌ - Notes:
- [ ] Batch page: ✅ / ❌ - Notes:

## Issues Found
1. Issue: ...
   - Severity: Critical / High / Medium / Low
   - Steps to reproduce: ...
   - Expected: ...
   - Actual: ...

2. Issue: ...
   ...
```

---

## Part 2: Automated Testing (Week 1-2)

### 2.1 Test Directory Structure

Create the following test files:

```
tests/
├── api/
│   ├── routes/
│   │   ├── test_agents.py           # 🔴 NEW - Agent API tests
│   │   ├── test_workflows.py        # 🔴 NEW - Workflow API tests
│   │   ├── test_batch.py            # 🔴 NEW - Batch API tests
│   │   ├── test_websockets.py       # 🔴 NEW - WebSocket API tests
│   │   ├── test_auth.py             # ✅ EXISTS (25 tests)
│   │   ├── test_quotas.py           # ✅ EXISTS (20 tests)
│   │   └── test_users.py            # ⚠️ EXISTS (partial)
│   └── test_main.py                 # 🔴 NEW - Main app tests
├── middleware/
│   ├── test_rate_limit.py           # ✅ EXISTS (24 tests)
│   ├── test_error_handler.py        # 🔴 NEW
│   └── test_logging.py              # 🔴 NEW
├── integration/
│   ├── test_complete_workflow.py    # 🔴 NEW - End-to-end workflows
│   ├── test_auth_flow.py            # 🔴 NEW - Complete auth journeys
│   └── test_quota_enforcement.py    # 🔴 NEW - Quota integration
├── load/
│   ├── test_api_load.py             # 🔴 NEW - Locust load tests
│   └── test_concurrent_users.py     # 🔴 NEW - Concurrent user simulation
└── security/
    ├── test_sql_injection.py        # 🔴 NEW - SQL injection tests
    ├── test_xss.py                  # 🔴 NEW - XSS tests
    └── test_authentication.py       # 🔴 NEW - Auth vulnerability tests
```

### 2.2 Agents API Tests (HIGH PRIORITY 🔴)

**File:** `tests/api/routes/test_agents.py`

**Test Count Target:** 30+ tests

#### Test Categories

1. **Agent Listing (5 tests)**
   - List all agents (authenticated)
   - List agents without authentication (401)
   - Agent list includes correct fields
   - Agent list pagination
   - Filter agents by capability

2. **Agent Execution (15 tests)**
   - Execute NER agent successfully
   - Execute Rel Extraction agent
   - Execute Pathway Analysis agent
   - Execute with invalid agent ID (404)
   - Execute without authentication (401)
   - Execute with invalid input format (422)
   - Execute with missing required fields (422)
   - Execute respects rate limits
   - Execute respects quotas
   - Execute creates background task
   - Execute returns task ID
   - Execute with custom parameters
   - Execute with empty text (400)
   - Execute with very long text (>10MB)
   - Execute concurrent requests

3. **Task Results (10 tests)**
   - Get task status (queued)
   - Get task status (running)
   - Get task status (completed)
   - Get task status (failed)
   - Get task results
   - Get task without authentication (401)
   - Get nonexistent task (404)
   - Get task results pagination
   - Get task logs
   - Cancel running task

#### Sample Test Code

```python
"""Tests for agent API endpoints."""
import pytest
from httpx import AsyncClient
from omics_oracle_v2.api.main import app


@pytest.mark.asyncio
async def test_list_agents_authenticated(auth_client: AsyncClient):
    """Test listing agents with authentication."""
    response = await auth_client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check agent structure
    agent = data[0]
    assert "id" in agent
    assert "name" in agent
    assert "description" in agent
    assert "capabilities" in agent


@pytest.mark.asyncio
async def test_list_agents_unauthenticated(client: AsyncClient):
    """Test listing agents without authentication."""
    response = await client.get("/api/agents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_execute_ner_agent(auth_client: AsyncClient):
    """Test executing NER agent."""
    response = await auth_client.post(
        "/api/agents/ner/execute",
        json={
            "text": "Aspirin is used to treat fever and pain.",
            "parameters": {}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] in ["queued", "running"]


@pytest.mark.asyncio
async def test_execute_agent_invalid_id(auth_client: AsyncClient):
    """Test executing nonexistent agent."""
    response = await auth_client.post(
        "/api/agents/invalid_agent/execute",
        json={"text": "Test text", "parameters": {}}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_results(auth_client: AsyncClient, completed_task):
    """Test getting task results."""
    response = await auth_client.get(f"/api/agents/tasks/{completed_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == completed_task.id
    assert data["status"] == "completed"
    assert "result" in data


# Add 25+ more tests...
```

### 2.3 Workflows API Tests (HIGH PRIORITY 🔴)

**File:** `tests/api/routes/test_workflows.py`

**Test Count Target:** 25+ tests

#### Test Categories

1. **Workflow CRUD (10 tests)**
   - List workflows
   - Get single workflow
   - Create workflow
   - Update workflow
   - Delete workflow
   - Create workflow without auth (401)
   - Create workflow with invalid steps (422)
   - Create workflow with duplicate name
   - Update nonexistent workflow (404)
   - Delete nonexistent workflow (404)

2. **Workflow Execution (10 tests)**
   - Execute simple workflow (2 steps)
   - Execute complex workflow (5+ steps)
   - Execute workflow with parameters
   - Execute workflow respects quotas
   - Execute workflow respects rate limits
   - Execute workflow with invalid input (422)
   - Get execution status
   - Get execution results
   - Cancel running execution
   - Retry failed execution

3. **Workflow Validation (5 tests)**
   - Validate workflow DAG (no cycles)
   - Validate workflow step order
   - Validate agent dependencies
   - Validate parameter compatibility
   - Validate output → input mapping

### 2.4 Batch API Tests (HIGH PRIORITY 🔴)

**File:** `tests/api/routes/test_batch.py`

**Test Count Target:** 20+ tests

#### Test Categories

1. **Batch Job Creation (8 tests)**
   - Create batch job with 10 items
   - Create batch job with 100 items
   - Create batch job with 1000 items
   - Create batch with invalid agent (404)
   - Create batch without auth (401)
   - Create batch with empty inputs (422)
   - Create batch with mixed input formats
   - Create batch respects quotas

2. **Batch Job Status (6 tests)**
   - Get job status (queued)
   - Get job status (processing)
   - Get job status (completed)
   - Get job status (failed)
   - Get job progress percentage
   - Get job estimated completion time

3. **Batch Results (6 tests)**
   - Get partial results
   - Get complete results
   - Download results as CSV
   - Download results as JSON
   - Filter results by status
   - Pagination for large result sets

### 2.5 WebSocket API Tests (HIGH PRIORITY 🔴)

**File:** `tests/api/routes/test_websockets.py`

**Test Count Target:** 15+ tests

#### Test Categories

1. **Connection (5 tests)**
   - Connect with valid token
   - Connect without token (403)
   - Connect with invalid token (403)
   - Connect with expired token (403)
   - Disconnect gracefully

2. **Subscriptions (5 tests)**
   - Subscribe to task updates
   - Subscribe to workflow updates
   - Subscribe to batch updates
   - Unsubscribe from channel
   - Subscribe to multiple channels

3. **Real-time Updates (5 tests)**
   - Receive task status update
   - Receive workflow progress update
   - Receive batch job progress
   - Receive error notifications
   - Receive completion notifications

---

## Part 3: Integration Testing (Week 2-3)

### 3.1 Complete User Journeys

**File:** `tests/integration/test_complete_workflow.py`

#### Test Scenarios

1. **New User Journey**
   ```
   Register → Login → View Quota → Execute Agent → View Results → Logout
   ```

2. **Workflow Creation Journey**
   ```
   Login → Create Workflow → Execute Workflow → Monitor Progress → View Results
   ```

3. **Batch Processing Journey**
   ```
   Login → Upload Dataset → Create Batch Job → Monitor Progress → Download Results
   ```

4. **Quota Management Journey**
   ```
   Login → Check Quota → Execute Until Quota Exhausted → Verify Rate Limit → Upgrade Tier
   ```

### 3.2 Authentication Integration Tests

**File:** `tests/integration/test_auth_flow.py`

1. Full registration flow with email verification
2. Login → Token refresh → Token expiration → Re-login
3. Password reset flow
4. User profile update
5. Admin user management

### 3.3 Quota Enforcement Integration Tests

**File:** `tests/integration/test_quota_enforcement.py`

1. Free tier quota enforcement across all endpoints
2. Premium tier quota enforcement
3. Quota reset at month boundary
4. Rate limit enforcement with quotas
5. Concurrent request quota handling

---

## Part 4: Load Testing (Week 3)

### 4.1 Locust Load Tests

**File:** `tests/load/test_api_load.py`

```python
"""Load tests for OmicsOracle v2 API."""
from locust import HttpUser, task, between


class OmicsOracleUser(HttpUser):
    """Simulated OmicsOracle user."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    token = None

    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/auth/login", json={
            "email": "loadtest@example.com",
            "password": "LoadTest123!"
        })
        self.token = response.json()["access_token"]

    @task(10)  # 10x weight
    def execute_ner_agent(self):
        """Execute NER agent."""
        self.client.post(
            "/api/agents/ner/execute",
            json={"text": "Aspirin treats pain.", "parameters": {}},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(5)  # 5x weight
    def list_agents(self):
        """List available agents."""
        self.client.get(
            "/api/agents",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(3)  # 3x weight
    def execute_workflow(self):
        """Execute workflow."""
        self.client.post(
            "/api/workflows/default/execute",
            json={"input": {"text": "Test"}, "parameters": {}},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)  # 1x weight
    def create_batch_job(self):
        """Create batch job."""
        self.client.post(
            "/api/batch/jobs",
            json={
                "agent": "ner",
                "inputs": [{"text": f"Test {i}"} for i in range(10)]
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

#### Load Testing Targets

- **100 concurrent users** - p95 < 500ms
- **500 concurrent users** - p95 < 1000ms
- **1000 concurrent users** - p95 < 2000ms
- **10,000 requests/min** - No errors
- **Database connection pool** - No exhaustion
- **Redis cache** - >90% hit rate

### 4.2 Running Load Tests

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/test_api_load.py --host http://localhost:8000

# Open browser to: http://localhost:8089
# Set: Number of users: 100, Spawn rate: 10

# Run headless
locust -f tests/load/test_api_load.py --host http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m --headless

# Results will show:
# - Requests/sec
# - Response times (p50, p95, p99)
# - Error rate
# - Concurrent users
```

---

## Part 5: Security Testing (Week 3)

### 5.1 Security Audit Tools

```bash
# 1. Bandit - Python security scanner
bandit -r omics_oracle_v2/ -ll

# Expected: No HIGH or MEDIUM severity issues

# 2. Safety - Dependency vulnerability scanner
safety check --json

# Expected: No known vulnerabilities

# 3. OWASP Dependency Check
dependency-check --project OmicsOracle --scan requirements.txt

# 4. Semgrep - Static analysis
semgrep --config=auto omics_oracle_v2/
```

### 5.2 Manual Security Testing

**File:** `docs/testing/SECURITY_TESTING_CHECKLIST.md`

#### Authentication Security
- [ ] SQL injection in login (test with `' OR 1=1 --`)
- [ ] XSS in user inputs (test with `<script>alert('XSS')</script>`)
- [ ] CSRF protection
- [ ] Brute force protection on login
- [ ] Password strength requirements
- [ ] JWT token expiration
- [ ] JWT token signature validation
- [ ] Session fixation
- [ ] Session hijacking

#### Authorization Security
- [ ] Vertical privilege escalation (user → admin)
- [ ] Horizontal privilege escalation (user A → user B data)
- [ ] Insecure direct object references (IDOR)
- [ ] Missing function level access control

#### Input Validation
- [ ] SQL injection in all endpoints
- [ ] NoSQL injection
- [ ] Command injection
- [ ] Path traversal
- [ ] XXE (XML External Entity)
- [ ] File upload vulnerabilities

#### API Security
- [ ] Rate limiting bypass
- [ ] Mass assignment
- [ ] API key exposure
- [ ] Sensitive data in URLs
- [ ] HTTPS enforcement
- [ ] CORS misconfiguration

#### Infrastructure Security
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] TLS configuration
- [ ] Cookie security (HttpOnly, Secure, SameSite)
- [ ] Clickjacking protection
- [ ] Information disclosure (stack traces, version info)

---

## Part 6: Test Execution Plan

### Week 1: Critical Manual Testing
**Goal:** Verify core functionality works

**Days 1-2: Setup & Health Checks**
- [ ] Set up test environment
- [ ] Run health checks
- [ ] Test authentication flow
- [ ] Document baseline performance

**Days 3-4: API Endpoint Testing**
- [ ] Test all agent endpoints
- [ ] Test all workflow endpoints
- [ ] Test all batch endpoints
- [ ] Test WebSocket endpoints

**Day 5: Web Dashboard Testing**
- [ ] Test all dashboard features
- [ ] Document issues found
- [ ] Create issue tickets

### Week 2: Automated Test Creation
**Goal:** Write 100+ automated tests

**Days 1-2: Agent Tests**
- [ ] Write `test_agents.py` (30 tests)
- [ ] Write `test_workflows.py` (25 tests)

**Days 3-4: Batch & WebSocket Tests**
- [ ] Write `test_batch.py` (20 tests)
- [ ] Write `test_websockets.py` (15 tests)

**Day 5: Middleware Tests**
- [ ] Write `test_error_handler.py` (10 tests)
- [ ] Write `test_logging.py` (10 tests)

### Week 3: Integration & Load Testing
**Goal:** Validate complete user journeys

**Days 1-2: Integration Tests**
- [ ] Write `test_complete_workflow.py` (10 tests)
- [ ] Write `test_auth_flow.py` (8 tests)
- [ ] Write `test_quota_enforcement.py` (7 tests)

**Days 3-4: Load Testing**
- [ ] Set up Locust
- [ ] Write load test scenarios
- [ ] Run load tests (100, 500, 1000 users)
- [ ] Analyze performance bottlenecks

**Day 5: Security Testing**
- [ ] Run automated security scanners
- [ ] Manual security testing
- [ ] Document vulnerabilities

### Week 4: Bug Fixing & Hardening
**Goal:** Fix all critical issues

**Days 1-3: Bug Fixes**
- [ ] Fix critical bugs from testing
- [ ] Fix security vulnerabilities
- [ ] Add missing features

**Days 4-5: Regression Testing**
- [ ] Re-run all automated tests
- [ ] Manual smoke testing
- [ ] Load testing validation

### Week 5: Final Validation
**Goal:** Production readiness

**Days 1-2: Final Testing**
- [ ] Full test suite run
- [ ] Manual testing of all features
- [ ] Security audit

**Days 3-4: Documentation**
- [ ] API documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide

**Day 5: Release Preparation**
- [ ] Update CHANGELOG
- [ ] Create release notes
- [ ] Tag v2.1.0

---

## Part 7: Success Criteria

### Testing Coverage Goals
- [ ] **Unit tests:** >85% code coverage
- [ ] **Integration tests:** >10 complete user journeys
- [ ] **Load tests:** Support 100+ concurrent users
- [ ] **Security tests:** Zero critical vulnerabilities

### Functional Goals
- [ ] **All API endpoints tested:** Agents, Workflows, Batch, WebSocket
- [ ] **Web dashboard verified:** All features working
- [ ] **Authentication validated:** Complete auth flows
- [ ] **Quotas enforced:** All tiers working correctly

### Non-Functional Goals
- [ ] **Performance:** p95 < 500ms for 100 users
- [ ] **Reliability:** >99.9% uptime in load tests
- [ ] **Security:** Pass OWASP Top 10 checklist
- [ ] **Documentation:** API docs complete

---

## Part 8: Testing Tools & Dependencies

### Required Tools

```bash
# Testing framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1

# HTTP client
httpx>=0.24.1

# Load testing
locust>=2.15.1

# Security scanning
bandit>=1.7.5
safety>=2.3.5

# Code coverage
coverage>=7.3.0

# WebSocket testing
websockets>=11.0.3
```

### Installation

```bash
pip install -r requirements-dev.txt
```

---

## Conclusion

This comprehensive testing plan covers all critical gaps identified in the v2 system:

1. **🔴 Critical Testing (Weeks 1-2):** Manual and automated testing of all API endpoints
2. **🟡 Integration Testing (Week 3):** Complete user journey validation
3. **🟢 Load & Security Testing (Weeks 3-4):** Production readiness
4. **Final Validation (Week 5):** Release preparation

**Estimated Timeline:** 5-6 weeks to production-ready v2.1.0

**Next Step:** Begin manual testing with Step 1.1 (Environment Setup)
