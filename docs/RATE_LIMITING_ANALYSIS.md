# Rate Limiting Analysis & Solutions

**Date:** October 8, 2025  
**Status:** Phase 3 - Testing Challenges  
**Question:** Why are we hitting rate limits, and how can we avoid them?

---

## TL;DR: The Problem

We're hitting **anonymous tier rate limits** (10 requests/hour) because:
1. We're not authenticating when testing
2. Backend treats unauthenticated requests as "anonymous" tier
3. Anonymous tier has strict limits: **10 requests/hour** (1 every 6 minutes!)
4. Our earlier API exploration tests exhausted the quota

---

## Part 1: Rate Limiting Architecture Explained

### 1.1 Tier-Based System

OmicsOracle uses a **sophisticated multi-tier rate limiting system**:

| Tier | Hourly Limit | Daily Limit | Concurrent | Use Case |
|------|--------------|-------------|------------|----------|
| **Anonymous** | 10 | 240 | 1 | No auth, IP-based |
| **Free** | 100 | 1,000 | 5 | Registered users |
| **Pro** | 1,000 | 20,000 | 20 | Paid users |
| **Enterprise** | 10,000 | 200,000 | 100 | Large orgs |

**Source:** `omics_oracle_v2/core/config.py` lines 130-145

### 1.2 How It Works

```python
# From middleware/rate_limit.py
async def dispatch(request, call_next):
    # 1. Try to get authenticated user
    user = await get_optional_user(request)
    
    # 2. Determine tier
    if user:
        tier = user.tier  # "free", "pro", or "enterprise"
        user_id = user.id
    else:
        tier = "anonymous"  # ⚠️ This is our problem!
        user_id = None
    
    # 3. Check quota (uses Redis or in-memory cache)
    rate_info = await check_rate_limit(
        user_id=user_id,
        ip_address=request.client.host,
        tier=tier,
        window="hour"
    )
    
    # 4. Block if exceeded
    if rate_info.quota_exceeded:
        return JSONResponse(status_code=429, ...)  # 😞
```

### 1.3 Tracking Mechanism

**Primary:** Redis-based counter
```python
# Key format: "rate_limit:{user_id or ip}:hour:{timestamp}"
# Example: "rate_limit:127.0.0.1:hour:1696723200"
await redis_incr(key, ttl=3600)  # Increment with 1-hour expiry
```

**Fallback:** In-memory dictionary (if Redis unavailable)
```python
# Stored in Python dict with timestamps
memory_store = {
    "127.0.0.1": (count, expires_at)
}
```

### 1.4 Why We Hit the Limit

**Our testing sequence:**
```
1. test_api_endpoints.py       → 5 requests  (5/10 used)
2. integration_layer_examples.py → 9 requests  (14/10 - BLOCKED!)
3. test_search_client_updated.py → BLOCKED immediately
```

**Anonymous limit:** 10 requests/hour from the same IP (127.0.0.1)

**Window reset:** 3600 seconds (1 hour) from the first request in the window

---

## Part 2: Solutions to Avoid Rate Limiting

### Solution 1: **Authenticate with a Test User** (RECOMMENDED)

Create a test user in the "free" tier (100 req/hour):

```bash
# Register a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@omicsoracle.local",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@omicsoracle.local",
    "password": "TestPassword123!"
  }'
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

**Update integration layer to use token:**

```python
# omics_oracle_v2/integration/base_client.py
class APIClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = None,  # Add this!
        timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.api_key = api_key  # Store token
        # ...
    
    async def _request(self, method, endpoint, **kwargs):
        # Add auth header if token exists
        if self.api_key:
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {self.api_key}"
            kwargs["headers"] = headers
        
        # ... rest of request logic
```

**Benefits:**
- ✅ 100 requests/hour (10x more!)
- ✅ 5 concurrent requests
- ✅ Proper user attribution in logs
- ✅ Access to user-specific features

---

### Solution 2: **Disable Rate Limiting for Development** (EASIEST)

**Temporary disable in config:**

```bash
# Set environment variable
export OMICS_RATE_LIMIT_ENABLED=false

# Or create .env file
echo "OMICS_RATE_LIMIT_ENABLED=false" >> .env

# Restart server
./start_omics_oracle.sh
```

**Or edit config programmatically:**

```python
# omics_oracle_v2/core/config.py
class RateLimitSettings(BaseSettings):
    enabled: bool = Field(default=False, ...)  # Change True → False
```

**Benefits:**
- ✅ Unlimited requests during development
- ✅ No authentication needed
- ✅ Faster testing iterations

**Risks:**
- ⚠️ Don't deploy to production with this!
- ⚠️ Can't test rate limiting behavior
- ⚠️ May mask performance issues

---

### Solution 3: **Increase Anonymous Tier Limits** (QUICK FIX)

**Edit config:**

```python
# omics_oracle_v2/core/config.py
class RateLimitSettings(BaseSettings):
    anonymous_limit_hour: int = Field(
        default=1000,  # Changed from 10!
        ge=1,
        description="Anonymous hourly limit"
    )
```

**Or use environment variable:**

```bash
export OMICS_RATE_LIMIT_ANONYMOUS_LIMIT_HOUR=1000
./start_omics_oracle.sh
```

**Benefits:**
- ✅ No code changes needed (env var)
- ✅ Still tests rate limiting (just higher limit)
- ✅ No authentication required

**Trade-offs:**
- ⚠️ Doesn't reflect production limits
- ⚠️ Increases server load risk

---

### Solution 4: **Use Multiple IPs or User Agents** (WORKAROUND)

The rate limiter tracks by IP address for anonymous users:

```python
# Different test approaches
async def test_with_proxy():
    # Use different proxy IPs (not practical)
    pass

async def test_with_different_ports():
    # Won't work - same IP (127.0.0.1)
    pass
```

**This doesn't work well** because:
- ❌ All local requests come from 127.0.0.1
- ❌ Requires complex proxy setup
- ❌ Doesn't test real authentication flow

---

### Solution 5: **Clear Redis Cache Between Tests** (NUCLEAR OPTION)

```bash
# Connect to Redis
redis-cli

# Clear all rate limit keys
KEYS rate_limit:*
# > "rate_limit:127.0.0.1:hour:1696723200"

DEL rate_limit:127.0.0.1:hour:1696723200

# Or clear entire Redis cache (⚠️ DANGER!)
FLUSHALL
```

**Or programmatically:**

```python
# In test setup
from omics_oracle_v2.cache import get_redis_client

async def setup_test():
    redis = await get_redis_client()
    if redis:
        # Clear rate limit keys for localhost
        pattern = "rate_limit:127.0.0.1:*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
```

**Benefits:**
- ✅ Instant quota reset
- ✅ Can test repeatedly

**Risks:**
- ⚠️ Clears production rate limit data if connected to prod Redis!
- ⚠️ Doesn't test realistic rate limit scenarios
- ⚠️ Can break other features relying on Redis

---

## Part 3: Recommended Approach for Phase 3 Testing

### Best Practice: **Combine Solutions 1 + 2**

**1. For Local Development: Disable Rate Limiting**
```bash
# .env.development
OMICS_RATE_LIMIT_ENABLED=false
```

**2. For Integration Tests: Use Test User**
```python
# tests/integration/conftest.py
@pytest.fixture
async def authenticated_client():
    """Create authenticated integration client."""
    # Register test user
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:8000/api/auth/register",
            json={
                "email": "integration-test@omicsoracle.local",
                "password": "IntegrationTest123!",
                "full_name": "Integration Test User"
            }
        )
        
        # Login
        response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "integration-test@omicsoracle.local",
                "password": "IntegrationTest123!"
            }
        )
        token = response.json()["access_token"]
    
    # Create authenticated integration client
    from omics_oracle_v2.integration import SearchClient
    client = SearchClient(api_key=token)
    yield client
    await client.close()
```

**3. For Production: Keep Rate Limiting Enabled**
```bash
# .env.production
OMICS_RATE_LIMIT_ENABLED=true
OMICS_RATE_LIMIT_ANONYMOUS_LIMIT_HOUR=10  # Strict limits
```

---

## Part 4: Immediate Action for Current Session

**Quick fix to continue testing RIGHT NOW:**

```bash
# Option A: Disable rate limiting (30 seconds)
export OMICS_RATE_LIMIT_ENABLED=false
pkill -f "uvicorn.*omics_oracle"  # Kill API server
./start_omics_oracle.sh  # Restart with disabled rate limiting

# Option B: Wait for window reset (already did this - 65 seconds)
# Rate limit window resets 1 hour after first request

# Option C: Increase anonymous limit (30 seconds)
export OMICS_RATE_LIMIT_ANONYMOUS_LIMIT_HOUR=1000
pkill -f "uvicorn.*omics_oracle"
./start_omics_oracle.sh
```

---

## Summary Table

| Solution | Setup Time | Pros | Cons | Recommended For |
|----------|-----------|------|------|-----------------|
| **1. Authenticate** | 2 min | Realistic, scales | Requires user mgmt | Integration tests |
| **2. Disable limiting** | 30 sec | Simple, unlimited | Unrealistic | Local dev |
| **3. Increase limits** | 30 sec | Quick, still limits | Unrealistic quotas | Quick testing |
| **4. Multiple IPs** | Complex | - | Impractical | ❌ Don't use |
| **5. Clear Redis** | 1 min | Instant reset | Dangerous | Emergency only |

---

## Recommendation for THIS Session

**Use Solution 2 (disable rate limiting) for Phase 3 validation:**

```bash
export OMICS_RATE_LIMIT_ENABLED=false
pkill -f "uvicorn.*omics_oracle"
./start_omics_oracle.sh
```

**Then immediately run:**
```bash
export PYTHONPATH=/Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle:$PYTHONPATH
python test_search_client_updated.py
```

**After Phase 3:** Implement Solution 1 (authentication) for proper integration tests.

---

**Next Steps:**
1. Disable rate limiting temporarily
2. Complete integration layer validation
3. Document working vs broken endpoints
4. Add authentication support to integration layer
5. Create proper test fixtures with authenticated clients
