# Manual Testing Results - 2025-10-05 04:15:16

**Base URL:** http://localhost:8000

---

## Summary

- **Total Tests:** 11
- **Passed:** 4 ✅
- **Failed:** 6 ❌
- **Errors:** 0 ⚠️
- **Issues Found:** 5 🐛

## Health Tests

- ❌ **Health Check:** FAIL
  - Notes: Status: 307
- ✅ **Metrics Endpoint:** PASS
  - Notes: Prometheus metrics returned
- ✅ **Root Endpoint:** PASS
  - Notes: API Info: OmicsOracle Agent API

## Auth Tests

- ❌ **User Registration:** FAIL
  - Notes: Status: 201, Response: {"email":"testuser@example.com","full_name":null,"id":"0782269d-8f74-4fa3-a8f9-ebd8f4c17d67","is_active":true,"is_admin":false,"is_verified":false,"tier":"free","request_count":0,"last_request_at":null,"created_at":"2025-10-05T08:15:15.732742","updated_at":"2025-10-05T08:15:15.732747","last_login_at":null}
- ✅ **User Login:** PASS
  - Notes: Token received
- ❌ **Get Current User:** FAIL
  - Notes: Status: 404

## Agents Tests

- ❌ **List Agents:** FAIL
  - Notes: Status: 404
- ⚠️ **Execute NER Agent:** SKIP
  - Notes: NER agent not found

## Workflows Tests

- ❌ **List Workflows:** FAIL
  - Notes: Status: 404

## Batch Tests

- ✅ **List Batch Jobs:** PASS
  - Notes: Found 2 jobs

## Quotas Tests

- ❌ **Get My Quota:** FAIL
  - Notes: Status: 500

## Issues Found

### Issue #1: Health check failed

- **Severity:** HIGH
- **Steps to Reproduce:** GET /health
- **Expected:** 200 OK
- **Actual:** 307
- **Timestamp:** 2025-10-05T04:15:15.386562

### Issue #2: User registration failed

- **Severity:** HIGH
- **Steps to Reproduce:** POST /api/v2/auth/register with {'email': 'testuser@example.com', 'password': 'TestPassword123!', 'username': 'testuser'}
- **Expected:** 200 OK or 400 (already exists)
- **Actual:** 201 {"email":"testuser@example.com","full_name":null,"id":"0782269d-8f74-4fa3-a8f9-ebd8f4c17d67","is_active":true,"is_admin":false,"is_verified":false,"tier":"free","request_count":0,"last_request_at":null,"created_at":"2025-10-05T08:15:15.732742","updated_at":"2025-10-05T08:15:15.732747","last_login_at":null}
- **Timestamp:** 2025-10-05T04:15:15.748463

### Issue #3: List agents failed

- **Severity:** CRITICAL
- **Steps to Reproduce:** GET /api/v1/agents with auth
- **Expected:** 200 OK with agent list
- **Actual:** 404 {"detail":"Not Found"}
- **Timestamp:** 2025-10-05T04:15:16.047875

### Issue #4: List workflows failed

- **Severity:** CRITICAL
- **Steps to Reproduce:** GET /api/v1/workflows with auth
- **Expected:** 200 OK with workflow list
- **Actual:** 404 {"detail":"Not Found"}
- **Timestamp:** 2025-10-05T04:15:16.080288

### Issue #5: Get quota failed

- **Severity:** HIGH
- **Steps to Reproduce:** GET /api/v2/quotas/me with auth
- **Expected:** 200 OK with quota info
- **Actual:** 500 {"error":"internal_server_error","message":"An internal server error occurred","detail":"1 validation error for QuotaUsageResponse\nuser_id\n  Input should be a valid integer [type=int_type, input_value=UUID('0782269d-8f74-4fa3-a8f9-ebd8f4c17d67'), input_type=UUID]\n    For further information visit https://errors.pydantic.dev/2.9/v/int_type"}
- **Timestamp:** 2025-10-05T04:15:16.160659

## Raw Results (JSON)

```json
{
  "health": [
    {
      "test": "Health Check",
      "status": "FAIL",
      "notes": "Status: 307",
      "timestamp": "2025-10-05T04:15:15.386535"
    },
    {
      "test": "Metrics Endpoint",
      "status": "PASS",
      "notes": "Prometheus metrics returned",
      "timestamp": "2025-10-05T04:15:15.391381"
    },
    {
      "test": "Root Endpoint",
      "status": "PASS",
      "notes": "API Info: OmicsOracle Agent API",
      "timestamp": "2025-10-05T04:15:15.407142"
    }
  ],
  "auth": [
    {
      "test": "User Registration",
      "status": "FAIL",
      "notes": "Status: 201, Response: {\"email\":\"testuser@example.com\",\"full_name\":null,\"id\":\"0782269d-8f74-4fa3-a8f9-ebd8f4c17d67\",\"is_active\":true,\"is_admin\":false,\"is_verified\":false,\"tier\":\"free\",\"request_count\":0,\"last_request_at\":null,\"created_at\":\"2025-10-05T08:15:15.732742\",\"updated_at\":\"2025-10-05T08:15:15.732747\",\"last_login_at\":null}",
      "timestamp": "2025-10-05T04:15:15.748431"
    },
    {
      "test": "User Login",
      "status": "PASS",
      "notes": "Token received",
      "timestamp": "2025-10-05T04:15:16.015568"
    },
    {
      "test": "Get Current User",
      "status": "FAIL",
      "notes": "Status: 404",
      "timestamp": "2025-10-05T04:15:16.031786"
    }
  ],
  "agents": [
    {
      "test": "List Agents",
      "status": "FAIL",
      "notes": "Status: 404",
      "timestamp": "2025-10-05T04:15:16.047805"
    },
    {
      "test": "Execute NER Agent",
      "status": "SKIP",
      "notes": "NER agent not found",
      "timestamp": "2025-10-05T04:15:16.064255"
    }
  ],
  "workflows": [
    {
      "test": "List Workflows",
      "status": "FAIL",
      "notes": "Status: 404",
      "timestamp": "2025-10-05T04:15:16.080190"
    }
  ],
  "batch": [
    {
      "test": "List Batch Jobs",
      "status": "PASS",
      "notes": "Found 2 jobs",
      "timestamp": "2025-10-05T04:15:16.098893"
    }
  ],
  "websocket": [],
  "quotas": [
    {
      "test": "Get My Quota",
      "status": "FAIL",
      "notes": "Status: 500",
      "timestamp": "2025-10-05T04:15:16.160588"
    }
  ],
  "issues": [
    {
      "severity": "HIGH",
      "issue": "Health check failed",
      "steps": "GET /health",
      "expected": "200 OK",
      "actual": "307 ",
      "timestamp": "2025-10-05T04:15:15.386562"
    },
    {
      "severity": "HIGH",
      "issue": "User registration failed",
      "steps": "POST /api/v2/auth/register with {'email': 'testuser@example.com', 'password': 'TestPassword123!', 'username': 'testuser'}",
      "expected": "200 OK or 400 (already exists)",
      "actual": "201 {\"email\":\"testuser@example.com\",\"full_name\":null,\"id\":\"0782269d-8f74-4fa3-a8f9-ebd8f4c17d67\",\"is_active\":true,\"is_admin\":false,\"is_verified\":false,\"tier\":\"free\",\"request_count\":0,\"last_request_at\":null,\"created_at\":\"2025-10-05T08:15:15.732742\",\"updated_at\":\"2025-10-05T08:15:15.732747\",\"last_login_at\":null}",
      "timestamp": "2025-10-05T04:15:15.748463"
    },
    {
      "severity": "CRITICAL",
      "issue": "List agents failed",
      "steps": "GET /api/v1/agents with auth",
      "expected": "200 OK with agent list",
      "actual": "404 {\"detail\":\"Not Found\"}",
      "timestamp": "2025-10-05T04:15:16.047875"
    },
    {
      "severity": "CRITICAL",
      "issue": "List workflows failed",
      "steps": "GET /api/v1/workflows with auth",
      "expected": "200 OK with workflow list",
      "actual": "404 {\"detail\":\"Not Found\"}",
      "timestamp": "2025-10-05T04:15:16.080288"
    },
    {
      "severity": "HIGH",
      "issue": "Get quota failed",
      "steps": "GET /api/v2/quotas/me with auth",
      "expected": "200 OK with quota info",
      "actual": "500 {\"error\":\"internal_server_error\",\"message\":\"An internal server error occurred\",\"detail\":\"1 validation error for QuotaUsageResponse\\nuser_id\\n  Input should be a valid integer [type=int_type, input_value=UUID('0782269d-8f74-4fa3-a8f9-ebd8f4c17d67'), input_type=UUID]\\n    For further information visit https://errors.pydantic.dev/2.9/v/int_type\"}",
      "timestamp": "2025-10-05T04:15:16.160659"
    }
  ]
}
```
