# Manual Testing Results - 2025-10-05 04:43:23

**Base URL:** http://localhost:8000

---

## Summary

- **Total Tests:** 11
- **Passed:** 10 ✅
- **Failed:** 0 ❌
- **Errors:** 0 ⚠️
- **Issues Found:** 0 🐛

## Health Tests

- ✅ **Health Check:** PASS
  - Notes: Response: {'status': 'healthy', 'timestamp': '2025-10-05T08:43:23.428395Z', 'version': '2.0.0'}
- ✅ **Metrics Endpoint:** PASS
  - Notes: Prometheus metrics returned
- ✅ **Root Endpoint:** PASS
  - Notes: API Info: OmicsOracle Agent API

## Auth Tests

- ✅ **User Registration:** PASS
  - Notes: User already exists (expected)
- ✅ **User Login:** PASS
  - Notes: Token received
- ✅ **Get Current User:** PASS
  - Notes: Email: testuser@example.com

## Agents Tests

- ✅ **List Agents:** PASS
  - Notes: Found 4 agents
- ⚠️ **Execute NER Agent:** SKIP
  - Notes: NER agent not found

## Workflows Tests

- ✅ **List Workflows:** PASS
  - Notes: Found 4 workflows

## Batch Tests

- ✅ **List Batch Jobs:** PASS
  - Notes: Found 2 jobs

## Quotas Tests

- ✅ **Get My Quota:** PASS
  - Notes: Tier: free, Remaining: None

## Raw Results (JSON)

```json
{
  "health": [
    {
      "test": "Health Check",
      "status": "PASS",
      "notes": "Response: {'status': 'healthy', 'timestamp': '2025-10-05T08:43:23.428395Z', 'version': '2.0.0'}",
      "timestamp": "2025-10-05T04:43:23.432161"
    },
    {
      "test": "Metrics Endpoint",
      "status": "PASS",
      "notes": "Prometheus metrics returned",
      "timestamp": "2025-10-05T04:43:23.437398"
    },
    {
      "test": "Root Endpoint",
      "status": "PASS",
      "notes": "API Info: OmicsOracle Agent API",
      "timestamp": "2025-10-05T04:43:23.455266"
    }
  ],
  "auth": [
    {
      "test": "User Registration",
      "status": "PASS",
      "notes": "User already exists (expected)",
      "timestamp": "2025-10-05T04:43:23.475118"
    },
    {
      "test": "User Login",
      "status": "PASS",
      "notes": "Token received",
      "timestamp": "2025-10-05T04:43:23.752991"
    },
    {
      "test": "Get Current User",
      "status": "PASS",
      "notes": "Email: testuser@example.com",
      "timestamp": "2025-10-05T04:43:23.776334"
    }
  ],
  "agents": [
    {
      "test": "List Agents",
      "status": "PASS",
      "notes": "Found 4 agents",
      "timestamp": "2025-10-05T04:43:23.809310"
    },
    {
      "test": "Execute NER Agent",
      "status": "SKIP",
      "notes": "NER agent not found",
      "timestamp": "2025-10-05T04:43:23.825195"
    }
  ],
  "workflows": [
    {
      "test": "List Workflows",
      "status": "PASS",
      "notes": "Found 4 workflows",
      "timestamp": "2025-10-05T04:43:23.858491"
    }
  ],
  "batch": [
    {
      "test": "List Batch Jobs",
      "status": "PASS",
      "notes": "Found 2 jobs",
      "timestamp": "2025-10-05T04:43:23.874740"
    }
  ],
  "websocket": [],
  "quotas": [
    {
      "test": "Get My Quota",
      "status": "PASS",
      "notes": "Tier: free, Remaining: None",
      "timestamp": "2025-10-05T04:43:23.928267"
    }
  ],
  "issues": []
}
```
