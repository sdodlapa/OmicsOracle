# Task 2: Rate Limiting & Quotas - Implementation Plan

**Status:** 🚧 IN PROGRESS
**Started:** October 4, 2025
**Estimated Duration:** 3-5 days
**Dependencies:** Task 1 (Authentication) ✅

---

## Overview

Implement a comprehensive rate limiting and quota management system using Redis for distributed rate limiting. This ensures fair usage, prevents abuse, and enforces tier-based access limits.

---

## Objectives

1. **Redis Integration** - Set up Redis for distributed rate limiting
2. **Per-User Rate Limiting** - Track and enforce request limits per user
3. **Tier-Based Quotas** - Different limits for free/pro/enterprise tiers
4. **Rate Limit Headers** - Standard HTTP headers (X-RateLimit-*)
5. **Quota Management API** - Admin endpoints for quota overrides
6. **Graceful Degradation** - System works without Redis (fallback to memory)

---

## Technical Approach

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  Rate Limiting Middleware       │
│  - Extract user ID/API key      │
│  - Check Redis for quota        │
│  - Increment counter            │
│  - Add X-RateLimit-* headers    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Application Endpoint           │
└─────────────────────────────────┘

┌─────────────┐
│   Redis     │
│  - Counters │
│  - TTL keys │
└─────────────┘
```

### Rate Limiting Strategy

**Token Bucket Algorithm:**
- Each user has a "bucket" of tokens (requests)
- Tokens refill at a constant rate
- Request consumes one token
- If bucket is empty, request is denied (429 Too Many Requests)

**Implementation with Redis:**
```python
# Key: "ratelimit:user:{user_id}:hour"
# Value: Request count
# TTL: 3600 seconds (1 hour)

# On each request:
1. INCR ratelimit:user:{user_id}:hour
2. If count == 1, set EXPIRE 3600
3. If count > limit, return 429
4. Continue to endpoint
```

---

## Implementation Plan

### Phase 2.1: Redis Setup (Day 1)

**Files to Create:**
- `omics_oracle_v2/cache/__init__.py` - Cache module exports
- `omics_oracle_v2/cache/redis_client.py` - Redis connection management
- `omics_oracle_v2/cache/rate_limiter.py` - Rate limiting logic

**Features:**
- Async Redis client (aioredis)
- Connection pooling
- Health checks
- Graceful fallback (in-memory cache if Redis unavailable)

**Configuration:**
```python
# omics_oracle_v2/core/config.py
class RedisSettings(BaseSettings):
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
```

### Phase 2.2: Rate Limiting Core (Day 1-2)

**Files to Create:**
- `omics_oracle_v2/middleware/rate_limit.py` - FastAPI middleware
- `omics_oracle_v2/auth/quota.py` - Quota definitions and logic

**Tier Quotas:**
```python
TIER_QUOTAS = {
    "free": {
        "requests_per_hour": 100,
        "requests_per_day": 1000,
        "concurrent_requests": 5,
    },
    "pro": {
        "requests_per_hour": 1000,
        "requests_per_day": 20000,
        "concurrent_requests": 20,
    },
    "enterprise": {
        "requests_per_hour": 10000,
        "requests_per_day": 200000,
        "concurrent_requests": 100,
    },
}
```

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1696435200
X-RateLimit-Retry-After: 3600
```

### Phase 2.3: Middleware Integration (Day 2)

**Files to Modify:**
- `omics_oracle_v2/api/main.py` - Add rate limiting middleware

**Middleware Flow:**
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 1. Extract user (from JWT/API key or use IP for anonymous)
    user = await get_optional_user(request)

    # 2. Get rate limit for user's tier
    limit, window = get_rate_limit(user)

    # 3. Check Redis counter
    current_count, reset_time = await check_rate_limit(user.id, window)

    # 4. Add headers
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count))
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    # 5. Enforce limit
    if current_count > limit:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"},
            headers={"Retry-After": str(reset_time - now)}
        )

    # 6. Continue to endpoint
    response = await call_next(request)
    return response
```

### Phase 2.4: Quota Management API (Day 2-3)

**Files to Create:**
- `omics_oracle_v2/api/routes/quotas.py` - Quota management endpoints

**Endpoints:**
```python
# User endpoints
GET    /api/v2/users/me/quota              # View current quota usage
GET    /api/v2/users/me/quota/history      # Usage history (last 30 days)

# Admin endpoints
GET    /api/v2/admin/quotas/{user_id}      # View user quota
PUT    /api/v2/admin/quotas/{user_id}      # Override user quota
POST   /api/v2/admin/quotas/{user_id}/reset # Reset user quota counter
GET    /api/v2/admin/quotas/usage          # System-wide usage stats
```

**Schemas:**
```python
class QuotaUsage(BaseModel):
    user_id: int
    tier: str
    requests_hour_limit: int
    requests_hour_used: int
    requests_hour_remaining: int
    requests_day_limit: int
    requests_day_used: int
    requests_day_remaining: int
    reset_at: datetime
    quota_exceeded: bool

class QuotaOverride(BaseModel):
    user_id: int
    custom_requests_per_hour: Optional[int] = None
    custom_requests_per_day: Optional[int] = None
    expires_at: Optional[datetime] = None
```

### Phase 2.5: Advanced Features (Day 3)

**1. IP-Based Rate Limiting (Anonymous Users):**
```python
# For unauthenticated requests
key = f"ratelimit:ip:{client_ip}:hour"
limit = 10  # Much lower for anonymous users
```

**2. Endpoint-Specific Limits:**
```python
# Heavy endpoints get stricter limits
ENDPOINT_LIMITS = {
    "/api/v1/agents": {"multiplier": 2},  # Costs 2 requests
    "/api/v1/batch": {"multiplier": 5},   # Costs 5 requests
    "/ws": {"multiplier": 0},              # WebSocket doesn't count
}
```

**3. Burst Protection:**
```python
# Allow short bursts but enforce overall average
# Sliding window algorithm
async def check_sliding_window(user_id: int, limit: int, window: int):
    now = time.time()
    key = f"ratelimit:sliding:{user_id}"

    # Remove old timestamps
    await redis.zremrangebyscore(key, 0, now - window)

    # Count recent requests
    count = await redis.zcard(key)

    if count >= limit:
        return False, count

    # Add current timestamp
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window)

    return True, count + 1
```

**4. Quota Reset Schedule:**
```python
# Daily quota reset at midnight UTC
# Hourly quota reset at top of hour
# Custom reset schedules for enterprise users
```

### Phase 2.6: Testing & Monitoring (Day 4)

**Tests to Write:**
- `tests/cache/test_redis_client.py` - Redis connection tests
- `tests/cache/test_rate_limiter.py` - Rate limiting logic tests
- `tests/middleware/test_rate_limit.py` - Middleware integration tests
- `tests/api/test_quotas.py` - Quota API tests

**Test Scenarios:**
1. User stays within quota
2. User exceeds hourly quota
3. User exceeds daily quota
4. Admin overrides quota
5. Redis failure (fallback to memory)
6. Concurrent requests
7. Rate limit headers correct
8. Different tiers have different limits
9. IP-based limiting for anonymous users
10. Endpoint-specific multipliers

**Monitoring:**
- Track quota usage per tier
- Alert on high usage patterns
- Dashboard showing top users
- Redis performance metrics

### Phase 2.7: Documentation (Day 4-5)

**Documents to Create:**
- `docs/RATE_LIMITING.md` - Complete rate limiting guide
- Update `docs/AUTH_SYSTEM.md` - Add quota information
- Update API reference with rate limit headers

---

## File Structure

```
omics_oracle_v2/
├── cache/
│   ├── __init__.py              # NEW - Cache module exports
│   ├── redis_client.py          # NEW - Redis connection
│   ├── rate_limiter.py          # NEW - Rate limiting logic
│   └── fallback.py              # NEW - In-memory fallback cache
├── middleware/
│   ├── __init__.py              # NEW - Middleware exports
│   └── rate_limit.py            # NEW - Rate limiting middleware
├── auth/
│   └── quota.py                 # NEW - Quota definitions
├── api/
│   ├── routes/
│   │   └── quotas.py            # NEW - Quota management API
│   └── main.py                  # MODIFY - Add middleware
└── core/
    └── config.py                # MODIFY - Add Redis settings

tests/
├── cache/
│   ├── test_redis_client.py     # NEW
│   └── test_rate_limiter.py     # NEW
├── middleware/
│   └── test_rate_limit.py       # NEW
└── api/
    └── test_quotas.py           # NEW

docs/
├── RATE_LIMITING.md             # NEW
└── AUTH_SYSTEM.md               # UPDATE
```

---

## Dependencies

**New Python Packages:**
```toml
[tool.poetry.dependencies]
redis = ">=5.0.0"              # Redis client
aioredis = ">=2.0.0"           # Async Redis (may be included in redis)
hiredis = ">=2.0.0"            # Fast Redis parser (optional, performance)
```

**Infrastructure:**
- Redis server (6.0+)
- Docker Compose update (add Redis service)

---

## Configuration

**Environment Variables:**
```bash
# Redis Configuration
OMICS_REDIS_URL=redis://localhost:6379/0
OMICS_REDIS_MAX_CONNECTIONS=10
OMICS_REDIS_PASSWORD=  # Optional
OMICS_REDIS_SSL=false

# Rate Limiting
OMICS_ENABLE_RATE_LIMITING=true
OMICS_RATE_LIMIT_FALLBACK=memory  # Use in-memory if Redis fails

# Default Quotas (can override in DB)
OMICS_FREE_TIER_LIMIT_HOUR=100
OMICS_PRO_TIER_LIMIT_HOUR=1000
OMICS_ENTERPRISE_TIER_LIMIT_HOUR=10000
```

---

## Success Criteria

### Functionality
- ✅ Redis connection established and monitored
- ✅ Rate limiting enforces tier quotas
- ✅ Correct X-RateLimit-* headers in all responses
- ✅ 429 status code when quota exceeded
- ✅ Quota management API functional
- ✅ Admin can override quotas
- ✅ Graceful fallback when Redis unavailable

### Performance
- ✅ Rate limit check < 5ms (Redis overhead)
- ✅ No impact on response time for users within quota
- ✅ Redis connection pool prevents connection exhaustion
- ✅ Memory usage stable with in-memory fallback

### Testing
- ✅ 30+ tests written and passing
- ✅ Load testing confirms rate limits work under load
- ✅ Concurrent request testing passes
- ✅ Failover testing (Redis down scenario)

### Documentation
- ✅ Complete rate limiting guide
- ✅ API examples with rate limit handling
- ✅ Troubleshooting guide
- ✅ Admin quota management guide

---

## Risk Mitigation

### Risk 1: Redis Single Point of Failure
**Mitigation:**
- Implement in-memory fallback cache
- Log warnings when fallback is active
- Monitor Redis health continuously
- Production: Use Redis Sentinel or Cluster

### Risk 2: Distributed Rate Limiting Race Conditions
**Mitigation:**
- Use Redis atomic operations (INCR)
- Lua scripts for complex operations
- Accept eventual consistency (slight over-quota OK)

### Risk 3: High Redis Load
**Mitigation:**
- Connection pooling (max 10 connections)
- Pipeline operations where possible
- Monitor Redis CPU/memory
- Scale Redis vertically if needed

### Risk 4: Clock Skew Between Servers
**Mitigation:**
- Use Redis time (not server time)
- TIME command for consistent timestamps
- NTP synchronization on all servers

---

## Phase 4 Integration

### Task 1 (Complete) → Task 2 Integration
- Use User model's `tier` field for quota lookup
- Leverage `get_optional_user()` dependency
- Extend usage tracking from Task 1

### Task 2 → Task 3 Integration
- Store quota overrides in PostgreSQL
- Historical usage data in PostgreSQL
- Redis for real-time counting only

### Task 2 → Task 4 Integration
- Share Redis connection with caching layer
- Unified Redis configuration
- Single connection pool

### Task 2 → Task 5 Integration
- Export quota metrics to Prometheus
- Alert on quota violations
- Dashboard showing rate limit patterns

---

## Timeline

**Day 1: Redis Setup & Core Logic**
- Set up Redis client
- Implement rate limiter class
- Basic quota definitions

**Day 2: Middleware & API**
- Rate limiting middleware
- Quota management endpoints
- Integration with main app

**Day 3: Advanced Features**
- IP-based limiting
- Endpoint multipliers
- Sliding window algorithm
- Quota reset scheduling

**Day 4: Testing**
- Write comprehensive tests
- Load testing
- Failover testing
- Performance benchmarks

**Day 5: Documentation & Polish**
- Write RATE_LIMITING.md
- Update existing docs
- Code cleanup
- Final commit

---

## Next Steps After Task 2

**Task 3: Persistent Storage**
- Quota override persistence
- Historical usage analytics
- Long-term storage optimization

**Task 4: Enhanced Caching**
- Share Redis for response caching
- Cache invalidation strategies
- Cache warming

**Task 5: Advanced Monitoring**
- Grafana dashboards
- Quota violation alerts
- Usage trend analysis

---

## Open Questions

1. Should we support per-endpoint custom quotas?
   - **Decision:** Yes, via multiplier system

2. How to handle quota for batch operations?
   - **Decision:** Each item in batch counts as 1 request

3. Should websocket connections count against quota?
   - **Decision:** No, but limit concurrent WS connections separately

4. How to handle quota during migrations (tier upgrades)?
   - **Decision:** Immediate effect, current hour counter carries over

5. Should we expose rate limit info in API responses always?
   - **Decision:** Yes, always include X-RateLimit-* headers

---

**Status:** Ready to implement
**Next:** Create Redis client and rate limiter core
