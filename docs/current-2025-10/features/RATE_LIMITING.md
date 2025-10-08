# Rate Limiting System

OmicsOracle implements a robust tier-based rate limiting system to ensure fair usage and prevent API abuse. This document explains how the system works and how to use it effectively.

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Tier Limits](#tier-limits)
4. [API Headers](#api-headers)
5. [Quota Management](#quota-management)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

## Overview

The rate limiting system provides:

- **Tier-based quotas**: Different limits for free, pro, and enterprise users
- **Multiple time windows**: Hourly and daily limits
- **Endpoint-specific costs**: Higher costs for expensive operations
- **Distributed tracking**: Redis-backed with in-memory fallback
- **Real-time feedback**: X-RateLimit headers on every response
- **Graceful degradation**: Automatic fallback when Redis is unavailable

## How It Works

### Request Flow

```
┌──────────────┐
│   Request    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Rate Limit Middleware   │
│  1. Extract user/IP      │
│  2. Get endpoint cost    │
│  3. Check quota          │
└──────┬───────────────────┘
       │
       ├─── Quota Exceeded ───► 429 Too Many Requests
       │                         + Retry-After header
       │
       └─── Quota OK ────────► Continue
                                 + X-RateLimit-* headers
```

### Token Bucket Algorithm

The system uses a token bucket algorithm with:

1. **Fixed capacity**: Based on tier (e.g., 100 requests/hour for free)
2. **Token consumption**: Each request consumes tokens (1-5x based on endpoint)
3. **Token refresh**: Bucket resets every window (hourly/daily)
4. **Atomic operations**: Redis INCR ensures race-free counting

## Tier Limits

### Free Tier

Perfect for individual developers and small projects.

| Window | Limit | Concurrent |
|--------|-------|------------|
| Hourly | 100   | 5          |
| Daily  | 1,000 | 5          |

**Best for**: Testing, personal projects, learning

### Pro Tier

Designed for production applications with moderate traffic.

| Window | Limit   | Concurrent |
|--------|---------|------------|
| Hourly | 1,000   | 20         |
| Daily  | 20,000  | 20         |

**Best for**: Production apps, small-medium businesses

### Enterprise Tier

High-volume access for large-scale applications.

| Window | Limit    | Concurrent |
|--------|----------|------------|
| Hourly | 10,000   | 100        |
| Daily  | 200,000  | 100        |

**Best for**: Enterprise applications, high-traffic services

### Anonymous Tier

For unauthenticated requests (IP-based tracking).

| Window | Limit | Concurrent |
|--------|-------|------------|
| Hourly | 10    | 1          |
| Daily  | 50    | 1          |

**Best for**: Public documentation, trial access

## Endpoint-Specific Costs

Different endpoints have different computational costs:

| Endpoint Pattern | Cost Multiplier | Examples |
|------------------|-----------------|----------|
| Health/Docs      | 0x (free)       | `/health`, `/docs`, `/auth/login` |
| Standard         | 1x              | `/api/v2/users/me`, `/api/v1/agents` |
| AI/Workflows     | 2x              | `/api/v1/agents/query`, `/api/v1/workflows` |
| Batch Operations | 5x              | `/api/v1/batch/process` |

### Example Calculation

For a **Pro tier** user (1,000 req/hour):

- 1,000 standard requests
- OR 500 AI agent requests (2x cost)
- OR 200 batch requests (5x cost)
- OR any combination that totals ≤1,000 tokens

## API Headers

Every API response includes rate limit information in headers:

### Response Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1704376800
X-RateLimit-Tier: pro  (debug mode only)
```

**Header Descriptions**:

- `X-RateLimit-Limit`: Total quota for current window
- `X-RateLimit-Remaining`: Requests remaining before limit
- `X-RateLimit-Reset`: Unix timestamp when quota resets
- `X-RateLimit-Tier`: User's tier (only in development)

### 429 Too Many Requests

When quota is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3542
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704376800

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again in 3542 seconds.",
  "limit": 1000,
  "reset_at": 1704376800
}
```

## Quota Management

### User Endpoints

#### Get My Quota

Check your current quota usage:

```bash
GET /api/v2/quotas/me
Authorization: Bearer <token>
```

**Response:**

```json
{
  "user_id": 123,
  "tier": "pro",
  "hourly_limit": 1000,
  "hourly_used": 247,
  "hourly_remaining": 753,
  "hourly_reset_at": 1704376800,
  "daily_limit": 20000,
  "daily_used": 5234,
  "daily_remaining": 14766,
  "daily_reset_at": 1704409200,
  "quota_exceeded": false,
  "checked_at": "2024-01-04T12:00:00Z"
}
```

#### Get Usage History

View your usage over time:

```bash
GET /api/v2/quotas/me/history?days=30
Authorization: Bearer <token>
```

**Response:**

```json
{
  "user_id": 123,
  "period_start": "2023-12-05T00:00:00Z",
  "period_end": "2024-01-04T00:00:00Z",
  "total_requests": 45230,
  "average_daily_requests": 1507.67,
  "peak_daily_requests": 3214,
  "current_tier": "pro",
  "history": [
    {
      "date": "2024-01-03T00:00:00Z",
      "requests": 2341,
      "tier": "pro"
    }
  ]
}
```

### Admin Endpoints

Administrators can manage quotas for any user.

#### Get User Quota

```bash
GET /api/v2/quotas/{user_id}
Authorization: Bearer <admin_token>
```

#### Update User Tier

```bash
PUT /api/v2/quotas/{user_id}/tier
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "tier": "enterprise"
}
```

#### Reset User Quota

```bash
POST /api/v2/quotas/{user_id}/reset
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "window": "hour"  // or "day" or "all"
}
```

#### Get System Stats

```bash
GET /api/v2/quotas/stats/overview
Authorization: Bearer <admin_token>
```

## Configuration

### Environment Variables

Configure rate limiting via environment variables:

```bash
# Enable/disable rate limiting
OMICS_RATE_LIMIT_ENABLED=true
OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=true

# Free tier limits
OMICS_FREE_TIER_LIMIT_HOUR=100
OMICS_FREE_TIER_LIMIT_DAY=1000
OMICS_FREE_TIER_CONCURRENT=5

# Pro tier limits
OMICS_PRO_TIER_LIMIT_HOUR=1000
OMICS_PRO_TIER_LIMIT_DAY=20000
OMICS_PRO_TIER_CONCURRENT=20

# Enterprise tier limits
OMICS_ENTERPRISE_TIER_LIMIT_HOUR=10000
OMICS_ENTERPRISE_TIER_LIMIT_DAY=200000
OMICS_ENTERPRISE_TIER_CONCURRENT=100

# Anonymous limits (IP-based)
OMICS_ANONYMOUS_LIMIT_HOUR=10
```

### Redis Configuration

Rate limiting requires Redis for distributed tracking:

```bash
# Redis connection
OMICS_REDIS_URL=redis://localhost:6379/0
OMICS_REDIS_PASSWORD=your_password
OMICS_REDIS_MAX_CONNECTIONS=10

# Timeouts (seconds)
OMICS_REDIS_SOCKET_TIMEOUT=5
OMICS_REDIS_SOCKET_CONNECT_TIMEOUT=5
OMICS_REDIS_HEALTH_CHECK_INTERVAL=30
```

### Redis Setup (Docker)

Quick start with Docker:

```bash
docker run -d \
  --name omics-redis \
  -p 6379:6379 \
  -e REDIS_PASSWORD=your_password \
  redis:7-alpine \
  redis-server --requirepass your_password
```

### Fallback Mode

If Redis is unavailable, the system automatically falls back to in-memory caching:

⚠️ **Warning**: In-memory fallback is **per-process** and not distributed. For production with multiple workers, Redis is required for accurate rate limiting.

## Troubleshooting

### Common Issues

#### 1. Rate Limit Too Restrictive

**Symptoms**: Legitimate requests getting 429 errors

**Solutions**:
- Check tier limits match your usage
- Consider upgrading to higher tier
- Contact admin for quota increase
- Implement exponential backoff

#### 2. Inconsistent Rate Limiting

**Symptoms**: Different limits between requests

**Possible Causes**:
- Multiple API workers without Redis (in-memory mode)
- Network issues with Redis
- Clock skew between servers

**Solutions**:
- Ensure Redis is running and accessible
- Use NTP to sync server clocks
- Check Redis connection logs

#### 3. Quota Not Resetting

**Symptoms**: Quota doesn't refresh after time window

**Solutions**:
- Verify server time is correct
- Check Redis TTL: `redis-cli TTL "ratelimit:user:123:hour"`
- Clear quota manually (admin): `POST /api/v2/quotas/{user_id}/reset`

### Monitoring

Check rate limiting health:

```bash
# Redis connection
curl http://localhost:8000/health

# User quota status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v2/quotas/me

# Redis CLI
redis-cli
> KEYS ratelimit:*
> TTL ratelimit:user:123:hour
> GET ratelimit:user:123:hour
```

### Best Practices

1. **Check Headers**: Always check `X-RateLimit-Remaining` header
2. **Implement Backoff**: Use exponential backoff for 429 responses
3. **Batch Operations**: Use batch endpoints for multiple items
4. **Cache Responses**: Cache API responses when possible
5. **Monitor Usage**: Track quota usage proactively
6. **Plan Upgrades**: Upgrade tier before hitting limits

### Example Client Implementation

```python
import time
import requests

class OmicsOracleClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

    def make_request(self, endpoint: str, max_retries: int = 3):
        """Make request with automatic retry on 429."""
        for attempt in range(max_retries):
            response = self.session.get(f"{self.base_url}{endpoint}")

            # Log rate limit info
            remaining = response.headers.get("X-RateLimit-Remaining")
            print(f"Quota remaining: {remaining}")

            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            return response.json()

        raise Exception("Max retries exceeded")

# Usage
client = OmicsOracleClient(
    api_key="your_token",
    base_url="http://localhost:8000"
)

data = client.make_request("/api/v2/users/me")
```

## Support

For rate limit increases or questions:

- **Documentation**: `/docs` endpoint
- **Support Email**: support@omicsoracle.com
- **GitHub Issues**: Report bugs or request features
- **Status Page**: Check system status

## Version History

- **v2.1.0** (2024-01-04): Initial rate limiting implementation
  - Tier-based quotas
  - Redis-backed distributed tracking
  - In-memory fallback
  - Quota management API
  - Comprehensive monitoring
