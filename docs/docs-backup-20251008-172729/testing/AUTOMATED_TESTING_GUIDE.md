# Automated Testing Implementation Guide - OmicsOracle v2

**Date:** October 5, 2025
**Baseline:** Manual test suite with 91% pass rate
**Target:** 100+ automated pytest tests with >85% coverage
**Timeline:** 10 days

---

## 🎯 Overview

This guide provides step-by-step instructions to convert the successful manual API tests into a comprehensive automated pytest suite. We'll build upon the existing manual test suite (`manual_api_test.py`) which achieved 91% pass rate (10/11 tests).

---

## 📊 Current Test Coverage

**Manual Tests (Completed):**
- ✅ Health & Metrics (3 tests)
- ✅ Authentication (3 tests)
- ✅ Agents (1 test + 1 skip)
- ✅ Workflows (1 test)
- ✅ Batch (1 test)
- ✅ Quotas (1 test)

**Total:** 11 tests, 10 passing (91%)

**Target Automated Tests:**
- Auth: 25+ tests
- Users: 15+ tests
- Agents: 30+ tests
- Workflows: 25+ tests
- Batch: 20+ tests
- Quotas: 15+ tests
- Integration: 15+ tests

**Total Target:** 145+ tests

---

## 🔧 Day 1-2: Infrastructure Setup

### Step 1: Install Dependencies

**Update `requirements-dev.txt`:**
```txt
# Existing dev dependencies
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
bandit>=1.7.0

# Add testing dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.24.0
faker>=19.0.0
factory-boy>=3.3.0
pytest-env>=0.8.0
pytest-xdist>=3.3.0  # Parallel test execution
```

**Install:**
```bash
pip install -r requirements-dev.txt
```

---

### Step 2: Create Test Structure

```bash
mkdir -p tests/{api,integration,fixtures,factories}
touch tests/__init__.py
touch tests/conftest.py
touch tests/factories.py
touch tests/api/__init__.py
touch tests/integration/__init__.py
```

**Final Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── factories.py             # Data factories
├── pytest.ini               # Pytest configuration
├── .env.test                # Test environment variables
├── api/                     # API endpoint tests
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_agents.py
│   ├── test_workflows.py
│   ├── test_batch.py
│   └── test_quotas.py
└── integration/             # Integration tests
    ├── __init__.py
    ├── test_auth_flow.py
    ├── test_workflow_execution.py
    └── test_quota_enforcement.py
```

---

### Step 3: Configure Pytest

**tests/pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=omics_oracle_v2
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
env_files =
    .env.test
```

**tests/.env.test:**
```bash
# Test Environment Configuration
OMICS_DB_URL=sqlite+aiosqlite:///:memory:
OMICS_DB_ECHO=False
OMICS_REDIS_URL=redis://localhost:6379/15
OMICS_RATE_LIMIT_ENABLED=True
OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=True
OMICS_AUTH_SECRET_KEY=test_secret_key_for_testing_only_do_not_use_in_production
OMICS_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
OMICS_ENVIRONMENT=test
OMICS_LOG_LEVEL=ERROR
```

---

### Step 4: Create Base Fixtures

**tests/conftest.py:**
```python
"""
Pytest configuration and shared fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from omics_oracle_v2.api.main import app
from omics_oracle_v2.database import Base, get_db
from omics_oracle_v2.database.session import engine as default_engine


# Test database engine (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "username": "testuser",
    }


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient, test_user_data: dict
) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """Create authenticated HTTP client with token."""
    # Register user
    response = await client.post("/api/v2/auth/register", json=test_user_data)
    assert response.status_code in [201, 409]  # 409 if user exists

    # Login
    response = await client.post("/api/v2/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]

    # Set auth header
    client.headers["Authorization"] = f"Bearer {token}"

    yield client, data

    # Cleanup
    client.headers.pop("Authorization", None)
```

---

### Step 5: Create Data Factories

**tests/factories.py:**
```python
"""
Factory classes for generating test data.
"""
import factory
from factory import faker

from omics_oracle_v2.auth.models import User, APIKey
from omics_oracle_v2.auth.quota.models import QuotaUsage


class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    id = factory.Faker("uuid4")
    email = factory.Faker("email")
    username = factory.Faker("user_name")
    hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7JYdHfZWYi"  # "password"
    is_active = True
    tier = "free"
    created_at = factory.Faker("date_time")


class APIKeyFactory(factory.Factory):
    """Factory for API Key model."""

    class Meta:
        model = APIKey

    id = factory.Faker("uuid4")
    user_id = factory.Faker("uuid4")
    key = factory.Faker("sha256")
    name = factory.Faker("word")
    is_active = True
    created_at = factory.Faker("date_time")


class QuotaUsageFactory(factory.Factory):
    """Factory for Quota Usage model."""

    class Meta:
        model = QuotaUsage

    id = factory.Faker("uuid4")
    user_id = factory.Faker("uuid4")
    tier = "free"
    requests_used = factory.Faker("random_int", min=0, max=100)
    requests_limit = 1000
    workflows_used = factory.Faker("random_int", min=0, max=10)
    workflows_limit = 100
```

---

## 📝 Day 3: Health & Authentication Tests

### tests/api/test_health.py

```python
"""
Tests for health and metrics endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health and metrics endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint returns healthy status."""
        response = await client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint returns Prometheus format."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Should contain prometheus metrics
        assert "http_requests_total" in response.text or "process_cpu" in response.text

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
```

---

### tests/api/test_auth.py

```python
"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration."""

    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/api/v2/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "username": "newuser",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Try to register again
        response = await client.post("/api/v2/auth/register", json=test_user_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post("/api/v2/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "username": "testuser",
        })
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post("/api/v2/auth/register", json={
            "email": "test@example.com",
            "password": "weak",
            "username": "testuser",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUserLogin:
    """Test user login."""

    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Login
        response = await client.post("/api/v2/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Try to login with wrong password
        response = await client.post("/api/v2/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post("/api/v2/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!",
        })
        assert response.status_code == 401

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials fails."""
        response = await client.post("/api/v2/auth/login", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestTokenAuthentication:
    """Test JWT token authentication."""

    async def test_access_protected_route_with_token(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test accessing protected route with valid token."""
        client, _ = authenticated_client
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 200

    async def test_access_protected_route_without_token(self, client: AsyncClient):
        """Test accessing protected route without token fails."""
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 401

    async def test_access_protected_route_invalid_token(self, client: AsyncClient):
        """Test accessing protected route with invalid token fails."""
        client.headers["Authorization"] = "Bearer invalid_token"
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 401
```

**Day 3 Deliverables:**
- ✅ 3 health endpoint tests
- ✅ 12 authentication tests
- ✅ Total: 15 tests

---

## 📝 Day 4-5: Agent API Tests

### tests/api/test_agents.py

```python
"""
Tests for agent endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAgentDiscovery:
    """Test agent discovery endpoints."""

    async def test_list_agents(self, authenticated_client: tuple[AsyncClient, dict]):
        """Test listing all available agents."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # Query, Search, Data, Report

        # Check structure
        agent = data[0]
        assert "id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "capabilities" in agent
        assert "endpoint" in agent

    async def test_list_agents_unauthenticated(self, client: AsyncClient):
        """Test listing agents without authentication fails."""
        response = await client.get("/api/v1/agents")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestQueryAgent:
    """Test Query Agent execution."""

    async def test_execute_query_agent(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing Query Agent with valid query."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/query", json={
            "query": "breast cancer BRCA1 mutation",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "execution_time_ms" in data

    async def test_query_agent_empty_query(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test Query Agent with empty query fails."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/query", json={
            "query": "",
        })
        assert response.status_code == 422

    async def test_query_agent_complex_query(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test Query Agent with complex biomedical query."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/query", json={
            "query": "lung cancer adenocarcinoma EGFR mutation treatment response",
        })
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data["data"]
        assert "intent" in data["data"]


@pytest.mark.asyncio
class TestSearchAgent:
    """Test Search Agent execution."""

    async def test_execute_search_agent(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing Search Agent."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/search", json={
            "query": "cancer",
            "max_results": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "datasets" in data["data"]

    async def test_search_agent_with_filters(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test Search Agent with filters."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/search", json={
            "query": "cancer",
            "max_results": 5,
            "organisms": ["Homo sapiens"],
            "min_samples": 10,
        })
        assert response.status_code == 200


@pytest.mark.asyncio
class TestDataAgent:
    """Test Data Agent execution."""

    async def test_execute_data_agent(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing Data Agent."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/data", json={
            "dataset_ids": ["GSE12345"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
class TestReportAgent:
    """Test Report Agent execution."""

    async def test_execute_report_agent(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing Report Agent."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/agents/report", json={
            "data": {"datasets": [], "analysis": {}},
            "report_type": "summary",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data["data"]
```

**Day 4-5 Deliverables:**
- ✅ 2 discovery tests
- ✅ 3 Query Agent tests
- ✅ 2 Search Agent tests
- ✅ 1 Data Agent test
- ✅ 1 Report Agent test
- ✅ Total: 9 new tests (24 cumulative)

---

## 📝 Day 6-7: Workflow & Batch Tests

### tests/api/test_workflows.py

```python
"""
Tests for workflow endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestWorkflowDiscovery:
    """Test workflow discovery."""

    async def test_list_workflows(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test listing all available workflows."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4

        workflow = data[0]
        assert "type" in workflow
        assert "name" in workflow
        assert "agents" in workflow


@pytest.mark.asyncio
@pytest.mark.slow
class TestWorkflowExecution:
    """Test workflow execution."""

    async def test_execute_full_analysis_workflow(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing full analysis workflow."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/workflows/execute", json={
            "query": "cancer research",
            "workflow_type": "full_analysis",
            "max_results": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_type"] == "full_analysis"
        assert "final_report" in data

    async def test_execute_simple_search_workflow(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test executing simple search workflow."""
        client, _ = authenticated_client
        response = await client.post("/api/v1/workflows/execute", json={
            "query": "diabetes",
            "workflow_type": "simple_search",
            "max_results": 3,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "simple_search"
```

### tests/api/test_batch.py

```python
"""
Tests for batch processing endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBatchJobs:
    """Test batch job endpoints."""

    async def test_create_batch_job(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test creating a batch job."""
        client, user_data = authenticated_client
        response = await client.post("/api/v1/batch/jobs", json={
            "queries": ["cancer", "diabetes", "alzheimer"],
            "workflow_type": "simple_search",
        })
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    async def test_list_batch_jobs(
        self, authenticated_client: tuple[AsyncClient, dict]
    ):
        """Test listing batch jobs."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/batch/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

**Day 6-7 Deliverables:**
- ✅ 3 workflow tests
- ✅ 2 batch job tests
- ✅ Total: 5 new tests (29 cumulative)

---

## 📝 Day 8-9: Integration Tests

### tests/integration/test_complete_flow.py

```python
"""
Integration tests for complete user flows.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete user journey from registration to results."""

    async def test_new_user_complete_flow(self, client: AsyncClient):
        """Test complete flow: register → login → execute → results."""
        # 1. Register
        register_response = await client.post("/api/v2/auth/register", json={
            "email": "journey@example.com",
            "password": "Journey123!",
            "username": "journeyuser",
        })
        assert register_response.status_code == 201

        # 2. Login
        login_response = await client.post("/api/v2/auth/login", json={
            "email": "journey@example.com",
            "password": "Journey123!",
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"

        # 3. Get current user
        me_response = await client.get("/api/v2/users/me")
        assert me_response.status_code == 200

        # 4. List agents
        agents_response = await client.get("/api/v1/agents")
        assert agents_response.status_code == 200

        # 5. Execute workflow
        workflow_response = await client.post("/api/v1/workflows/execute", json={
            "query": "test query",
            "workflow_type": "simple_search",
        })
        assert workflow_response.status_code == 200
        assert workflow_response.json()["success"] is True
```

**Day 8-9 Deliverables:**
- ✅ 5+ integration tests
- ✅ Total: 5 new tests (34 cumulative)

---

## 📝 Day 10: CI/CD Integration

### .github/workflows/tests.yml

```yaml
name: Run Tests

on:
  push:
    branches: [main, develop, phase-4-production-features]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ \
            --cov=omics_oracle_v2 \
            --cov-report=xml \
            --cov-report=term \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=85
```

**Day 10 Deliverables:**
- ✅ GitHub Actions workflow
- ✅ Automated test runs on PR
- ✅ Coverage reporting
- ✅ Documentation updated

---

## ✅ Success Criteria

### Test Coverage
- ✅ >85% code coverage
- ✅ All critical paths tested
- ✅ Edge cases covered
- ✅ Error scenarios tested

### Test Quality
- ✅ Tests are deterministic (no flaky tests)
- ✅ Tests run in <5 minutes
- ✅ Tests are well-documented
- ✅ Tests follow best practices

### CI/CD
- ✅ Tests run automatically on PR
- ✅ Coverage reports generated
- ✅ Failures block merge
- ✅ Fast feedback (<10 minutes)

---

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/api/test_auth.py
```

### Run with Coverage
```bash
pytest --cov=omics_oracle_v2 --cov-report=html
```

### Run Parallel Tests
```bash
pytest -n auto
```

### Run Only Fast Tests
```bash
pytest -m "not slow"
```

---

## 📊 Expected Results

After completing this guide:

- **Total Tests:** 145+
- **Coverage:** >85%
- **Pass Rate:** >95%
- **Test Duration:** <5 minutes
- **CI/CD:** Fully automated

---

**Status:** Ready for implementation
**Next Action:** Begin Day 1 - Install dependencies
