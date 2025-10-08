# Comprehensive Architecture Improvement Plan: OmicsOracle

## Executive Summary

This document outlines a detailed 8-week plan to transform the OmicsOracle codebase from its current state (4/10 architectural quality) to a clean, maintainable, and scalable architecture (9/10 target quality).

**Transformation Goals:**
- Eliminate 51+ sys.path manipulations
- Consolidate duplicate interfaces
- Implement Clean Architecture + DDD principles
- Achieve 90%+ test coverage
- Reduce cyclomatic complexity to <10
- Establish proper Python packaging structure

## Current State Assessment

### 🚨 Critical Issues
- **Code Duplication:** 60-70% duplicate code between interfaces
- **Import Hell:** 51+ sys.path manipulations across codebase
- **Monolithic Files:** 5+ files >500 lines (pipeline.py ~970 lines)
- **Circular Dependencies:** 10+ circular import chains
- **Test Coverage:** Only 28% (critically low)
- **Configuration Chaos:** Config scattered across multiple locations

### 📊 Quality Metrics Baseline
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Architecture Score | 4/10 | 9/10 | 🔴 Critical |
| Test Coverage | 28% | 90%+ | 🔴 Critical |
| sys.path Usage | 51+ | 0 | 🔴 Critical |
| Files >500 LOC | 5+ | 0 | 🔴 Critical |
| Circular Dependencies | 10+ | 0 | 🔴 Critical |
| Import Depth | 6+ levels | 3 levels | 🔴 Critical |

## Implementation Strategy

### 🎯 Phase 1: Foundation & Backup (Week 1)
**Goal:** Create solid foundation and preserve existing work

#### 1.1 Backup & Archive Current Interfaces
```bash
# Create comprehensive backup of existing interfaces
mkdir -p archive/interfaces/
mv interfaces/ archive/interfaces/futuristic/
```

#### 1.2 Create New Package Structure
```
src/omics_oracle/
├── domain/                    # Core business logic
│   ├── __init__.py
│   ├── entities/             # Business entities
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── search_query.py
│   │   └── search_result.py
│   ├── value_objects/        # Value objects
│   │   ├── __init__.py
│   │   ├── geo_id.py
│   │   └── search_parameters.py
│   ├── repositories/         # Abstract repositories
│   │   ├── __init__.py
│   │   ├── search_repository.py
│   │   └── dataset_repository.py
│   └── services/             # Domain services
│       ├── __init__.py
│       └── search_orchestrator.py
├── application/              # Use cases & app services
│   ├── __init__.py
│   ├── use_cases/           # Business use cases
│   │   ├── __init__.py
│   │   ├── search_datasets.py
│   │   └── analyze_dataset.py
│   ├── dto/                 # Data transfer objects
│   │   ├── __init__.py
│   │   └── search_dto.py
│   └── services/            # Application services
│       ├── __init__.py
│       └── search_service.py
├── infrastructure/          # External concerns
│   ├── __init__.py
│   ├── persistence/         # Data persistence
│   │   ├── __init__.py
│   │   └── file_storage.py
│   ├── external_apis/       # External API clients
│   │   ├── __init__.py
│   │   ├── geo_client.py
│   │   └── ncbi_client.py
│   ├── messaging/           # Event/message handling
│   │   ├── __init__.py
│   │   └── websocket_service.py
│   └── configuration/       # Configuration management
│       ├── __init__.py
│       └── config.py
├── presentation/            # Interface layer
│   ├── __init__.py
│   ├── web/                 # Web interface
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app factory
│   │   ├── routes/          # Route modules
│   │   ├── middleware/      # Custom middleware
│   │   ├── static/          # Frontend assets
│   │   └── templates/       # HTML templates
│   ├── api/                 # Pure REST API
│   │   ├── __init__.py
│   │   └── routes.py
│   └── cli/                 # Command-line interface
│       ├── __init__.py
│       └── commands.py
└── shared/                  # Shared utilities
    ├── __init__.py
    ├── exceptions/          # Common exceptions
    │   ├── __init__.py
    │   └── domain_exceptions.py
    ├── logging/             # Logging utilities
    │   ├── __init__.py
    │   └── logger.py
    ├── validation/          # Validation utilities
    │   ├── __init__.py
    │   └── validators.py
    └── types/               # Shared types
        ├── __init__.py
        └── common_types.py
```

#### 1.3 Remove sys.path Manipulations
- Audit all files with sys.path usage
- Create proper __init__.py files for package discovery
- Implement relative imports

#### 1.4 Success Criteria Week 1
- ✅ All interfaces archived safely
- ✅ New package structure created
- ✅ Zero new sys.path manipulations
- ✅ Basic package imports working

### 🏗️ Phase 2: Domain Layer Implementation (Week 2)
**Goal:** Extract and implement core domain logic

#### 2.1 Extract Domain Entities
```python
# src/omics_oracle/domain/entities/dataset.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Dataset:
    """Core dataset entity representing a biomedical dataset."""
    geo_id: str
    title: str
    summary: Optional[str] = None
    organism: Optional[str] = None
    platform: Optional[str] = None
    samples_count: Optional[int] = None
    submission_date: Optional[datetime] = None
    last_update_date: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_valid(self) -> bool:
        """Check if dataset has minimum required information."""
        return bool(self.geo_id and self.title)
```

#### 2.2 Extract Value Objects
```python
# src/omics_oracle/domain/value_objects/search_query.py
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class SearchType(str, Enum):
    COMPREHENSIVE = "comprehensive"
    TARGETED = "targeted"
    ADVANCED = "advanced"

@dataclass(frozen=True)
class SearchQuery:
    """Immutable search query value object."""
    query_text: str
    max_results: int = 10
    search_type: SearchType = SearchType.COMPREHENSIVE
    organisms: Optional[List[str]] = None
    platforms: Optional[List[str]] = None

    def __post_init__(self):
        if not self.query_text.strip():
            raise ValueError("Query text cannot be empty")
        if self.max_results <= 0 or self.max_results > 1000:
            raise ValueError("Max results must be between 1 and 1000")
```

#### 2.3 Define Repository Interfaces
```python
# src/omics_oracle/domain/repositories/search_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.dataset import Dataset
from ..value_objects.search_query import SearchQuery

class SearchRepository(ABC):
    """Abstract repository for dataset search operations."""

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[Dataset]:
        """Search for datasets matching the query."""
        pass

    @abstractmethod
    async def get_by_geo_id(self, geo_id: str) -> Optional[Dataset]:
        """Retrieve a specific dataset by GEO ID."""
        pass

    @abstractmethod
    async def get_similar(self, dataset: Dataset, limit: int = 10) -> List[Dataset]:
        """Find datasets similar to the given dataset."""
        pass
```

#### 2.4 Success Criteria Week 2
- ✅ Core domain entities implemented
- ✅ Value objects with validation
- ✅ Repository interfaces defined
- ✅ Domain logic isolated from infrastructure

### ⚙️ Phase 3: Application Layer (Week 3)
**Goal:** Implement use cases and application services

#### 3.1 Create Use Cases
```python
# src/omics_oracle/application/use_cases/search_datasets.py
from typing import List
from ..dto.search_dto import SearchRequestDTO, SearchResponseDTO
from ...domain.repositories.search_repository import SearchRepository
from ...domain.value_objects.search_query import SearchQuery
from ...shared.logging.logger import get_logger

logger = get_logger(__name__)

class SearchDatasetsUseCase:
    """Use case for searching biomedical datasets."""

    def __init__(self, search_repository: SearchRepository):
        self._search_repository = search_repository

    async def execute(self, request: SearchRequestDTO) -> SearchResponseDTO:
        """Execute the search use case."""
        try:
            # Convert DTO to domain object
            search_query = SearchQuery(
                query_text=request.query,
                max_results=request.max_results,
                search_type=request.search_type
            )

            # Execute domain operation
            datasets = await self._search_repository.search(search_query)

            # Convert back to DTO
            return SearchResponseDTO(
                query=request.query,
                results=[dataset.__dict__ for dataset in datasets],
                total_found=len(datasets),
                search_time=0.0  # TODO: Implement timing
            )

        except Exception as e:
            logger.error(f"Search use case failed: {e}")
            raise
```

#### 3.2 Implement DTOs
```python
# src/omics_oracle/application/dto/search_dto.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ...domain.value_objects.search_query import SearchType

@dataclass
class SearchRequestDTO:
    """Data transfer object for search requests."""
    query: str
    max_results: int = 10
    search_type: SearchType = SearchType.COMPREHENSIVE
    organisms: Optional[List[str]] = None
    platforms: Optional[List[str]] = None

@dataclass
class SearchResponseDTO:
    """Data transfer object for search responses."""
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    search_time: float
    timestamp: Optional[float] = None
```

#### 3.3 Success Criteria Week 3
- ✅ Use cases implemented
- ✅ DTOs for data transfer
- ✅ Application services created
- ✅ Clean separation between layers

### 🔌 Phase 4: Infrastructure Layer (Week 4)
**Goal:** Implement external integrations and configuration

#### 4.1 Implement Repository Concrete Classes
```python
# src/omics_oracle/infrastructure/external_apis/geo_search_repository.py
from typing import List, Optional
from ...domain.repositories.search_repository import SearchRepository
from ...domain.entities.dataset import Dataset
from ...domain.value_objects.search_query import SearchQuery
from .geo_client import GEOClient

class GEOSearchRepository(SearchRepository):
    """Concrete implementation of search repository using GEO API."""

    def __init__(self, geo_client: GEOClient):
        self._geo_client = geo_client

    async def search(self, query: SearchQuery) -> List[Dataset]:
        """Search datasets using GEO API."""
        raw_results = await self._geo_client.search(
            query.query_text,
            max_results=query.max_results
        )

        return [self._map_to_dataset(raw_result) for raw_result in raw_results]

    def _map_to_dataset(self, raw_result: dict) -> Dataset:
        """Map raw API result to domain entity."""
        return Dataset(
            geo_id=raw_result.get('geo_id'),
            title=raw_result.get('title'),
            summary=raw_result.get('summary'),
            organism=raw_result.get('organism'),
            # ... map other fields
        )
```

#### 4.2 Centralized Configuration
```python
# src/omics_oracle/infrastructure/configuration/config.py
from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///omics_oracle.db"
    echo: bool = False

@dataclass
class GEOConfig:
    """GEO API configuration."""
    base_url: str = "https://www.ncbi.nlm.nih.gov/geo/"
    email: str = os.getenv("NCBI_EMAIL", "omicsoracle@example.com")
    api_key: Optional[str] = os.getenv("NCBI_API_KEY")

@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool = False
    log_level: str = "INFO"
    max_concurrent_requests: int = 10
    cache_ttl: int = 3600

    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    geo: GEOConfig = GEOConfig()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            # ... load other settings
        )
```

#### 4.3 Success Criteria Week 4
- ✅ Repository implementations created
- ✅ Configuration centralized
- ✅ External API clients properly abstracted
- ✅ Infrastructure isolated from domain

### 🌐 Phase 5: Presentation Layer (Week 5)
**Goal:** Consolidate and improve web interfaces

#### 5.1 Create Unified FastAPI Application
```python
# src/omics_oracle/presentation/web/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import search_router, analysis_router, websocket_router
from .middleware.security import SecurityHeadersMiddleware
from .middleware.rate_limiting import RateLimitMiddleware
from ...infrastructure.configuration.config import AppConfig

def create_app(config: AppConfig) -> FastAPI:
    """Factory function to create FastAPI application."""

    app = FastAPI(
        title="OmicsOracle API",
        description="Biomedical research platform",
        version="3.0.0",
        debug=config.debug
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Specific origins
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Include routers
    app.include_router(search_router, prefix="/api/search", tags=["search"])
    app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

    return app
```

#### 5.2 Implement Dependency Injection
```python
# src/omics_oracle/presentation/web/dependencies.py
from fastapi import Depends
from typing import Annotated
from ...application.use_cases.search_datasets import SearchDatasetsUseCase
from ...infrastructure.external_apis.geo_search_repository import GEOSearchRepository
from ...infrastructure.external_apis.geo_client import GEOClient
from ...infrastructure.configuration.config import AppConfig

# Configuration dependency
def get_config() -> AppConfig:
    return AppConfig.from_env()

# Repository dependencies
def get_geo_client(config: Annotated[AppConfig, Depends(get_config)]) -> GEOClient:
    return GEOClient(config.geo)

def get_search_repository(
    geo_client: Annotated[GEOClient, Depends(get_geo_client)]
) -> GEOSearchRepository:
    return GEOSearchRepository(geo_client)

# Use case dependencies
def get_search_use_case(
    repository: Annotated[GEOSearchRepository, Depends(get_search_repository)]
) -> SearchDatasetsUseCase:
    return SearchDatasetsUseCase(repository)
```

#### 5.3 Success Criteria Week 5
- ✅ Single unified web interface
- ✅ Proper dependency injection
- ✅ Clean route organization
- ✅ Middleware properly structured

### 🧪 Phase 6: Testing Infrastructure (Week 6)
**Goal:** Achieve comprehensive test coverage

#### 6.1 Domain Layer Tests
```python
# tests/domain/test_entities.py
import pytest
from src.omics_oracle.domain.entities.dataset import Dataset
from datetime import datetime

class TestDataset:
    def test_dataset_creation(self):
        """Test basic dataset creation."""
        dataset = Dataset(
            geo_id="GSE12345",
            title="Test Dataset"
        )
        assert dataset.geo_id == "GSE12345"
        assert dataset.title == "Test Dataset"
        assert dataset.is_valid

    def test_dataset_validation(self):
        """Test dataset validation."""
        dataset = Dataset(geo_id="", title="")
        assert not dataset.is_valid
```

#### 6.2 Use Case Tests
```python
# tests/application/test_search_use_case.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.omics_oracle.application.use_cases.search_datasets import SearchDatasetsUseCase
from src.omics_oracle.application.dto.search_dto import SearchRequestDTO

@pytest.mark.asyncio
class TestSearchDatasetsUseCase:
    async def test_successful_search(self):
        """Test successful dataset search."""
        # Arrange
        mock_repository = Mock()
        mock_repository.search = AsyncMock(return_value=[])
        use_case = SearchDatasetsUseCase(mock_repository)
        request = SearchRequestDTO(query="cancer", max_results=10)

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.query == "cancer"
        assert result.total_found == 0
        mock_repository.search.assert_called_once()
```

#### 6.3 Integration Tests
```python
# tests/integration/test_search_flow.py
import pytest
from fastapi.testclient import TestClient
from src.omics_oracle.presentation.web.main import create_app
from src.omics_oracle.infrastructure.configuration.config import AppConfig

@pytest.fixture
def test_app():
    config = AppConfig(debug=True)
    return create_app(config)

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

def test_search_endpoint_integration(client):
    """Test complete search flow integration."""
    response = client.post(
        "/api/search/datasets",
        json={"query": "cancer", "max_results": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_found" in data
```

#### 6.4 Success Criteria Week 6
- ✅ 90%+ test coverage achieved
- ✅ All layers have comprehensive tests
- ✅ Integration tests cover major flows
- ✅ Performance tests implemented

### 🚀 Phase 7: Performance & Monitoring (Week 7)
**Goal:** Optimize performance and implement monitoring

#### 7.1 Performance Optimizations
```python
# src/omics_oracle/infrastructure/caching/redis_cache.py
from typing import Any, Optional
import redis
import json
from ...shared.logging.logger import get_logger

logger = get_logger(__name__)

class CacheService:
    """Redis-based caching service."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        try:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cached value with TTL."""
        try:
            serialized = json.dumps(value)
            return self._redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False
```

#### 7.2 Monitoring Integration
```python
# src/omics_oracle/shared/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Metrics
search_requests_total = Counter('search_requests_total', 'Total search requests')
search_duration_seconds = Histogram('search_duration_seconds', 'Search duration')
active_connections = Gauge('active_websocket_connections', 'Active WebSocket connections')

def monitor_search_performance(func):
    """Decorator to monitor search performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        search_requests_total.inc()

        try:
            result = await func(*args, **kwargs)
            search_duration_seconds.observe(time.time() - start_time)
            return result
        except Exception as e:
            # Log error metrics
            raise

    return wrapper
```

#### 7.3 Success Criteria Week 7
- ✅ Response times <500ms for search
- ✅ Comprehensive monitoring implemented
- ✅ Performance benchmarks established
- ✅ Caching layer operational

### 📚 Phase 8: Documentation & Deployment (Week 8)
**Goal:** Complete documentation and deployment preparation

#### 8.1 API Documentation
```python
# Enhanced FastAPI documentation
from fastapi import FastAPI
from .routes.search import search_router

app = FastAPI(
    title="OmicsOracle API",
    description="""
    ## Biomedical Research Platform

    OmicsOracle provides comprehensive search and analysis capabilities
    for biomedical datasets from various public repositories.

    ### Key Features
    - **Dataset Search**: Advanced search across GEO, SRA, and other repositories
    - **AI Summarization**: Intelligent summarization of research papers
    - **Real-time Updates**: WebSocket-based live search progress
    - **Batch Processing**: Handle multiple queries efficiently
    """,
    version="3.0.0",
    contact={
        "name": "OmicsOracle Team",
        "email": "support@omicsoracle.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
```

#### 8.2 Deployment Configuration
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  omics-oracle:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - NCBI_EMAIL=${NCBI_EMAIL}
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=omics_oracle
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

#### 8.3 Success Criteria Week 8
- ✅ Complete API documentation
- ✅ Deployment scripts ready
- ✅ Performance benchmarks documented
- ✅ Migration guide created

## Quality Assurance

### 🔍 Continuous Quality Checks

#### Daily Quality Gates
```bash
# Run all quality checks
make quality-check

# Individual checks
make test           # Run all tests
make lint           # Code quality checks
make security       # Security scanning
make performance    # Performance tests
```

#### Weekly Architecture Reviews
- Dependency analysis
- Coupling/cohesion metrics
- Performance benchmarks
- Technical debt assessment

### 📊 Success Metrics Tracking

| Week | Focus | Key Metrics | Target |
|------|-------|-------------|--------|
| 1 | Foundation | sys.path usage, package structure | 0 sys.path, clean structure |
| 2 | Domain | Domain logic isolation, entity design | 100% domain purity |
| 3 | Application | Use case implementation, DTO design | All use cases tested |
| 4 | Infrastructure | Repository implementation, config | All integrations working |
| 5 | Presentation | Interface consolidation, DI | Single interface, clean DI |
| 6 | Testing | Test coverage, integration tests | 90%+ coverage |
| 7 | Performance | Response times, monitoring | <500ms response |
| 8 | Documentation | API docs, deployment | Production ready |

## Risk Mitigation

### 🚨 High-Risk Areas
1. **Data Migration**: Careful handling of existing data
2. **Breaking Changes**: Maintain backward compatibility where possible
3. **Performance Degradation**: Continuous performance monitoring
4. **Team Productivity**: Gradual transition, comprehensive documentation

### 🛡️ Mitigation Strategies
1. **Comprehensive Backup**: Full system backup before each phase
2. **Feature Flags**: Gradual rollout of new architecture
3. **Parallel Development**: Keep old system running during transition
4. **Automated Testing**: Prevent regressions with comprehensive test suite

## Post-Implementation Maintenance

### 📈 Continuous Improvement
- Monthly architecture reviews
- Quarterly performance optimizations
- Bi-annual technology updates
- Annual architecture assessments

### 🎯 Long-term Goals (6 months)
- Microservices migration path
- Plugin architecture for extensions
- Multi-tenant support
- Advanced caching strategies

## Conclusion

This comprehensive 8-week plan will transform OmicsOracle from a technically debt-ridden codebase to a clean, maintainable, and scalable architecture. The phased approach ensures minimal disruption while maximizing architectural improvements.

**Expected Outcomes:**
- ✅ 90%+ test coverage
- ✅ Zero sys.path manipulations
- ✅ Clean Architecture implementation
- ✅ 2x faster development velocity
- ✅ 70% reduction in bugs
- ✅ Production-ready deployment

The investment in this refactoring will pay dividends in reduced maintenance costs, faster feature development, and improved system reliability.
