# Phase 4: Presentation Layer Integration

## 🎯 Goal
Integrate the new Clean Architecture with existing FastAPI interfaces and create a unified presentation layer.

## 📋 Phase 4 Objectives

### 4.1 FastAPI Integration
- [ ] Create FastAPI application using dependency injection container
- [ ] Integrate existing routes with new use cases
- [ ] Add WebSocket endpoints for real-time communication
- [ ] Update middleware to work with new architecture

### 4.2 Interface Consolidation
- [ ] Consolidate multiple interfaces into unified presentation layer
- [ ] Archive legacy interfaces properly
- [ ] Create modern interface using new architecture
- [ ] Maintain backward compatibility where needed

### 4.3 WebSocket Integration
- [ ] Integrate WebSocketService with FastAPI
- [ ] Create real-time search progress endpoints
- [ ] Add event streaming capabilities
- [ ] Test WebSocket connectivity and performance

### 4.4 Middleware Enhancement
- [ ] Security middleware integration
- [ ] Rate limiting with new infrastructure
- [ ] Error handling middleware with domain exceptions
- [ ] Logging middleware with structured logging

### 4.5 Route Integration
- [ ] Search endpoints using new SearchDatasetsUseCase
- [ ] Analysis endpoints with event publishing
- [ ] Health check endpoints
- [ ] API versioning strategy

## 🏗️ Implementation Strategy

### Step 1: Create Unified FastAPI App
```python
# src/omics_oracle/presentation/web/main.py
from fastapi import FastAPI
from .dependencies import setup_dependencies
from .routes import setup_routes
from .middleware import setup_middleware
from .websockets import setup_websockets
```

### Step 2: Dependency Injection Setup
```python
# src/omics_oracle/presentation/web/dependencies.py
from fastapi import Depends
from ...infrastructure.dependencies.container import Container
```

### Step 3: Route Integration
```python
# src/omics_oracle/presentation/web/routes/search.py
from fastapi import APIRouter, Depends
from ...application.use_cases.enhanced_search_datasets import EnhancedSearchDatasetsUseCase
```

### Step 4: WebSocket Endpoints
```python
# src/omics_oracle/presentation/web/websockets.py
from fastapi import WebSocket
from ...infrastructure.messaging.websocket_service import WebSocketService
```

## 🧪 Testing Strategy

### Integration Tests
- [ ] FastAPI app creation and configuration
- [ ] Route integration with dependency injection
- [ ] WebSocket connection and messaging
- [ ] Middleware functionality

### End-to-End Tests
- [ ] Complete search journey through new architecture
- [ ] Real-time progress tracking
- [ ] Error handling across all layers
- [ ] Performance benchmarks

## ✅ Success Criteria

1. **Unified Application**: Single FastAPI app using clean architecture
2. **Dependency Injection**: All dependencies properly injected
3. **WebSocket Integration**: Real-time communication working
4. **Middleware Stack**: Security, rate limiting, error handling
5. **API Compatibility**: Existing endpoints still functional
6. **Test Coverage**: 95%+ coverage on presentation layer
7. **Performance**: Response times under 500ms for search
8. **Documentation**: OpenAPI documentation complete

## 🚀 Deliverables

1. `src/omics_oracle/presentation/web/main.py` - Unified FastAPI application
2. `src/omics_oracle/presentation/web/dependencies.py` - DI setup
3. `src/omics_oracle/presentation/web/routes/` - Route handlers
4. `src/omics_oracle/presentation/web/middleware/` - Middleware stack
5. `src/omics_oracle/presentation/web/websockets.py` - WebSocket handlers
6. `tests/presentation/` - Comprehensive test suite
7. Integration with existing interfaces
8. Performance benchmarks and monitoring

## 📊 Quality Targets

- **Architecture Compliance**: 100% Clean Architecture
- **Test Coverage**: 95%+ on presentation layer
- **Performance**: <500ms API response times
- **Security**: All OWASP guidelines followed
- **Documentation**: Complete OpenAPI docs
- **Compatibility**: Zero breaking changes to existing APIs

---

**Target Completion**: Week 4 of 8-week plan
**Dependencies**: Phase 3 infrastructure layer complete ✅
**Next Phase**: Phase 5 - Legacy Decomposition and Plugin Architecture
