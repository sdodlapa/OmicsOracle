# Monolithic File Refactoring Plan

## Critical Files to Refactor

### 1. `src/omics_oracle/pipeline/pipeline.py` (~970 lines)

**Current Issues**:
- Single file handles entire query processing pipeline
- Mixed responsibilities: orchestration, business logic, data processing
- Hard to test individual components

**Refactoring Strategy**:
```
src/omics_oracle/pipeline/
├── __init__.py
├── orchestrator.py         # Main pipeline orchestration (200 lines)
├── query_processor.py      # Query processing logic (150 lines)
├── data_enhancer.py        # Data enhancement logic (150 lines)
├── result_assembler.py     # Result assembly logic (100 lines)
└── pipeline_config.py      # Pipeline configuration (50 lines)
```

**Implementation Steps**:
1. Extract query processing logic into separate module
2. Create result assembly service
3. Implement pipeline orchestrator that coordinates services
4. Update dependencies to use new modular structure

### 2. Route Files Consolidation

**Current Issues**:
- 7 different route files with minimal content
- Inconsistent patterns and duplicate health checks
- Version confusion (v1, v2, enhanced, futuristic)

**Target Structure**:
```
src/omics_oracle/presentation/web/routes/
├── __init__.py
├── search.py              # All search-related endpoints
├── analysis.py            # Analysis endpoints
├── health.py             # Health and monitoring
└── admin.py              # Administrative endpoints
```

### 3. Service Layer Reorganization

**Current State**: Mixed responsibilities in service classes

**Target Pattern**:
```python
# Service Interface Pattern
from abc import ABC, abstractmethod

class SearchService(ABC):
    @abstractmethod
    async def search_datasets(self, query: str) -> SearchResult:
        pass

class EnhancedSearchService(SearchService):
    def __init__(self, geo_client: GEOClient, summarizer: Summarizer):
        self._geo_client = geo_client
        self._summarizer = summarizer

    async def search_datasets(self, query: str) -> SearchResult:
        # Implementation with clear single responsibility
        pass
```

## Refactoring Guidelines

### File Size Limits
- **Maximum**: 300 lines per file
- **Target**: 150-200 lines per file
- **Functions**: Maximum 20 lines per function

### Single Responsibility Principle
- Each file should have one reason to change
- Clear separation between configuration, business logic, and infrastructure
- Interface segregation for better testability

### Testing Strategy
- Unit tests for each new module
- Integration tests for pipeline orchestration
- Mock dependencies for isolated testing

## Implementation Priority
1. **High Priority**: pipeline.py refactoring (critical path)
2. **Medium Priority**: Route consolidation
3. **Low Priority**: Service layer reorganization

## Success Metrics
- File count reduction: 30%
- Average file size reduction: 50%
- Improved test coverage: Target 80%
- Reduced cyclomatic complexity
