# Comprehensive Testing Strategy

## Current Testing Issues
- **Only 28% test coverage** (industry standard: 80%+)
- Tests scattered across multiple directories
- Some test files are themselves too large (>500 LOC)
- Missing integration tests between architectural layers

## Target Testing Architecture

### 1. Test Organization
```
tests/
├── unit/                   # Unit tests (70% of test suite)
│   ├── core/              # Core business logic tests
│   ├── services/          # Service layer tests
│   ├── pipeline/          # Pipeline component tests
│   └── presentation/      # Web layer tests
├── integration/           # Integration tests (20% of test suite)
│   ├── api/              # API integration tests
│   ├── pipeline/         # End-to-end pipeline tests
│   └── external/         # External service integration
├── e2e/                   # End-to-end tests (10% of test suite)
│   ├── web/              # Web interface tests
│   └── cli/              # CLI interface tests
├── fixtures/              # Test data and fixtures
├── mocks/                # Mock implementations
└── conftest.py           # Pytest configuration
```

### 2. Testing Standards

#### Unit Tests
```python
# Example: Service layer unit test
import pytest
from unittest.mock import Mock, AsyncMock
from omics_oracle.services.search import SearchService

class TestSearchService:
    @pytest.fixture
    async def mock_geo_client(self):
        mock = AsyncMock()
        mock.search_datasets.return_value = [{"id": "GSE123"}]
        return mock

    @pytest.fixture
    async def search_service(self, mock_geo_client):
        return SearchService(geo_client=mock_geo_client)

    async def test_search_datasets_success(self, search_service, mock_geo_client):
        # Given
        query = "cancer genes"

        # When
        result = await search_service.search_datasets(query)

        # Then
        assert result is not None
        assert len(result.datasets) > 0
        mock_geo_client.search_datasets.assert_called_once_with(query)
```

#### Integration Tests
```python
# Example: API integration test
import pytest
from httpx import AsyncClient
from omics_oracle.presentation.web.main import create_app

class TestSearchAPI:
    @pytest.fixture
    async def client(self):
        app = await create_app()
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_search_endpoint_integration(self, client):
        # Given
        query = {"query": "cancer genes", "limit": 10}

        # When
        response = await client.get("/api/v2/search/enhanced", params=query)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert isinstance(data["metadata"], list)
```

### 3. Test Coverage Targets

| Component | Current Coverage | Target Coverage | Priority |
|-----------|------------------|-----------------|----------|
| Core Business Logic | 15% | 95% | High |
| Services Layer | 20% | 90% | High |
| Pipeline | 10% | 85% | High |
| Web Presentation | 30% | 80% | Medium |
| Infrastructure | 40% | 75% | Medium |
| CLI | 5% | 70% | Low |

### 4. Testing Tools & Configuration

#### pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    --strict-markers
    --strict-config
    --disable-warnings
    --cov=src/omics_oracle
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

#### Mock Strategy
- Use dependency injection for easy mocking
- Create reusable mock factories for external services
- Implement contract testing for API boundaries

### 5. Continuous Integration

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml (add to existing)
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
        args: [--cov-fail-under=80]
```

#### GitHub Actions (if using)
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run tests
        run: |
          pytest --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Implementation Plan

### Week 1: Foundation
- Set up test directory structure
- Configure pytest and coverage tools
- Write test utilities and fixtures

### Week 2: Unit Tests
- Core business logic tests
- Service layer tests
- Target: 60% coverage

### Week 3: Integration Tests
- API integration tests
- Pipeline integration tests
- Target: 75% coverage

### Week 4: E2E and Optimization
- End-to-end test suite
- Performance tests
- Target: 80%+ coverage

## Success Metrics
- **Coverage**: 80%+ across all components
- **Test Speed**: Full suite runs in <2 minutes
- **Reliability**: 99%+ test pass rate in CI
- **Maintainability**: Average 10 lines of test per line of production code
