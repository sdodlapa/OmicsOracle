# Dependency Injection Implementation Plan

## Current State Assessment
- Sophisticated DI system exists in `backups/clean_architecture/`
- Current implementation in `src/omics_oracle/presentation/web/dependencies.py` is minimal
- Hard-coded dependencies throughout the codebase

## Recommended Architecture

### 1. Service Container Pattern
```python
# src/omics_oracle/core/container.py
from typing import TypeVar, Type, Callable, Any, Dict
import asyncio

T = TypeVar('T')

class ServiceContainer:
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    async def register_singleton(self, service_type: Type[T], instance: T):
        """Register a singleton service instance."""
        self._singletons[service_type] = instance

    async def register_factory(self, service_type: Type[T], factory: Callable[[], T]):
        """Register a factory function for service creation."""
        self._factories[service_type] = factory

    async def get(self, service_type: Type[T]) -> T:
        """Get service instance, creating if necessary."""
        if service_type in self._singletons:
            return self._singletons[service_type]
        elif service_type in self._factories:
            instance = await self._factories[service_type]()
            return instance
        else:
            raise ValueError(f"Service {service_type} not registered")
```

### 2. FastAPI Integration
```python
# src/omics_oracle/presentation/web/dependencies.py
from fastapi import Depends, Request
from typing import Annotated

from ...core.container import ServiceContainer
from ...services.summarizer import SummarizationService
from ...pipeline.pipeline import OmicsOracle

async def get_container(request: Request) -> ServiceContainer:
    """Get the service container from app state."""
    return request.app.state.container

async def get_summarizer(
    container: Annotated[ServiceContainer, Depends(get_container)]
) -> SummarizationService:
    """Get summarization service via DI."""
    return await container.get(SummarizationService)

async def get_pipeline(
    container: Annotated[ServiceContainer, Depends(get_container)]
) -> OmicsOracle:
    """Get pipeline via DI."""
    return await container.get(OmicsOracle)
```

### 3. Application Bootstrap
```python
# src/omics_oracle/presentation/web/main.py
async def create_app() -> FastAPI:
    # ... existing code ...

    # Setup dependency injection
    container = ServiceContainer()

    # Register services
    await container.register_singleton(Config, Config())
    await container.register_factory(SummarizationService, create_summarizer)
    await container.register_factory(OmicsOracle, create_pipeline)

    # Store in app state
    app.state.container = container

    return app
```

## Benefits
- Loose coupling between components
- Easy testing with mock dependencies
- Clear service lifecycle management
- Facilitates clean architecture patterns
