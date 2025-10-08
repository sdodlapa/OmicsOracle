# Performance Optimization & Production Readiness Plan

## Current Performance Issues

### Identified Bottlenecks
1. **Synchronous Operations**: Some I/O operations still blocking
2. **Memory Usage**: No memory optimization in large data processing
3. **API Rate Limiting**: External API calls not optimally managed
4. **Resource Management**: No connection pooling or resource limits

## Optimization Strategy

### 1. Async/Await Optimization

#### Current Issues
```python
# Found in some parts of the codebase - blocking operations
def process_data(data):
    result = requests.get(external_api_url)  # Blocking
    return result.json()
```

#### Target Implementation
```python
# Optimized async implementation
import aiohttp
import asyncio
from typing import List

class AsyncDataProcessor:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

    async def process_batch(self, items: List[str]) -> List[dict]:
        """Process items concurrently with rate limiting."""
        tasks = [self._process_item(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_item(self, item: str) -> dict:
        async with self._semaphore:  # Rate limiting
            async with self._session.get(f"external_api/{item}") as response:
                return await response.json()
```

### 2. Memory Optimization

#### Streaming Processing
```python
# Large dataset processing with streaming
async def process_large_dataset(data_stream):
    """Process data in chunks to avoid memory issues."""
    chunk_size = 1000
    async for chunk in async_chunked(data_stream, chunk_size):
        processed_chunk = await process_chunk(chunk)
        yield processed_chunk
        # Memory cleanup between chunks
        gc.collect()
```

#### Connection Pooling
```python
# HTTP connection pooling for external APIs
import aiohttp

class OptimizedHTTPClient:
    def __init__(self):
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection limit
            limit_per_host=30,  # Per-host limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

    async def close(self):
        await self._session.close()
```

### 3. Caching Strategy

#### Multi-Level Caching
```python
from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass
class CacheConfig:
    memory_ttl: int = 300  # 5 minutes
    redis_ttl: int = 3600  # 1 hour
    disk_ttl: int = 86400  # 24 hours

class MultiLevelCache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self._memory_cache = {}
        self._redis_client = None  # Initialize if Redis available

    async def get(self, key: str) -> Optional[Any]:
        # L1: Memory cache
        if key in self._memory_cache:
            return self._memory_cache[key]

        # L2: Redis cache (if available)
        if self._redis_client:
            value = await self._redis_client.get(key)
            if value:
                self._memory_cache[key] = value
                return value

        # L3: Disk cache
        return await self._get_from_disk(key)
```

### 4. Resource Monitoring

#### Performance Metrics Collection
```python
import time
import psutil
import logging
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss

            metrics = {
                'function': func.__name__,
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': start_time
            }

            # Log performance metrics
            logging.info(f"Performance: {metrics}")

            # Alert on performance issues
            if metrics['duration'] > 5.0:  # Slow operation
                logging.warning(f"Slow operation detected: {metrics}")

    return wrapper
```

### 5. Production Configuration

#### Environment-Specific Optimization
```python
# src/omics_oracle/core/config.py
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class PerformanceConfig:
    environment: Environment

    # Database connections
    db_pool_size: int = field(default_factory=lambda: 20 if Environment.PRODUCTION else 5)
    db_pool_timeout: int = 30

    # HTTP client settings
    http_connection_limit: int = field(default_factory=lambda: 100 if Environment.PRODUCTION else 20)
    http_timeout: int = 30

    # Cache settings
    cache_enabled: bool = field(default_factory=lambda: True if Environment.PRODUCTION else False)
    cache_ttl: int = field(default_factory=lambda: 3600 if Environment.PRODUCTION else 300)

    # Rate limiting
    rate_limit_per_minute: int = field(default_factory=lambda: 1000 if Environment.PRODUCTION else 100)
```

#### Docker Optimization
```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Multi-stage build for smaller image
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local

# Performance optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/root/.local/bin:$PATH

# Resource limits
ENV WORKERS=4
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=50

COPY . /app
WORKDIR /app

CMD ["gunicorn", "src.omics_oracle.presentation.web.main:app", \
     "--workers", "$WORKERS", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--max-requests", "$MAX_REQUESTS", \
     "--max-requests-jitter", "$MAX_REQUESTS_JITTER", \
     "--bind", "0.0.0.0:8000"]
```

## Performance Targets

### Response Time Targets
| Endpoint | Current | Target | Strategy |
|----------|---------|--------|----------|
| Health Check | ~50ms | <10ms | Memory cache |
| Simple Search | ~2-5s | <1s | Async + caching |
| Enhanced Search | ~5-10s | <3s | Parallel processing |
| AI Summary | ~10-15s | <5s | Streaming response |

### Resource Limits
- **Memory Usage**: <512MB per worker process
- **CPU Usage**: <80% under normal load
- **Concurrent Requests**: 100+ per second
- **Database Connections**: Pool size 20-50

### Monitoring & Alerting
```python
# Performance monitoring middleware
async def performance_monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Alert on slow requests
    if process_time > 5.0:
        logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")

    return response
```

## Implementation Timeline

### Week 1: Async Optimization
- Convert remaining synchronous operations to async
- Implement connection pooling
- Add rate limiting for external APIs

### Week 2: Caching Implementation
- Implement multi-level caching
- Add cache invalidation strategies
- Performance testing and tuning

### Week 3: Resource Monitoring
- Add performance monitoring middleware
- Implement alerting for performance issues
- Memory optimization and profiling

### Week 4: Production Hardening
- Docker optimization
- Environment-specific configuration
- Load testing and final tuning

## Success Metrics
- **API Response Time**: 90th percentile <2s
- **Memory Usage**: <512MB per process
- **Throughput**: 100+ requests/second
- **Uptime**: 99.9% availability
- **Error Rate**: <0.1% of requests
