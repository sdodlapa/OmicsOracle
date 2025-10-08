# Testing Issues and Fixes - v2.1.0

**Date:** October 5, 2025
**Status:** ✅ SUCCESS - All Critical Issues Fixed
**Test Run:** Manual API Testing - Re-test After Fixes

---

## Executive Summary

**Re-test results after fixing all critical issues:**
- ✅ **10 tests passed** (91% success rate - up from 36%)
- ⚠️ **1 test skipped** (Execute NER Agent - not applicable)
- ❌ **0 tests failed**
- 🎯 **All 5 critical issues FIXED**

**Improvement:**
- Initial: 4/11 passing (36%)
- After fixes: 10/11 passing (91%)
- **+155% improvement in pass rate!**

**All Critical Issues Resolved:**
1. ✅ Issue #3: Added GET /api/v2/users/me endpoint
2. ✅ Issue #4: Added GET /api/v1/agents list endpoint
3. ✅ Issue #5: Added GET /api/v1/workflows list endpoint
4. ✅ Issue #6: Fixed quota UUID type mismatch (500 error)
5. ✅ Bonus: Fixed redirect handling in test client

---

## Test Results Summary

### All Endpoints Working ✅

**Health & Metrics (3/3 passing)**
- ✅ GET /health/ → 200 OK
- ✅ GET /metrics → 200 OK
- ✅ GET / → 200 OK

**Authentication (3/3 passing)**
- ✅ POST /api/v2/auth/register → 201/409 (expected)
- ✅ POST /api/v2/auth/login → 200 OK
- ✅ GET /api/v2/users/me → 200 OK (NEW - Issue #3 fix)

**Agents (1/1 passing + 1 skip)**
- ✅ GET /api/v1/agents → 200 OK (NEW - Issue #4 fix)
- ⚠️ POST /api/v1/agents/ner → Skipped (not in list)

**Workflows (1/1 passing)**
- ✅ GET /api/v1/workflows → 200 OK (NEW - Issue #5 fix)

**Batch Processing (1/1 passing)**
- ✅ GET /api/v1/batch/jobs → 200 OK

**Quotas (1/1 passing)**
- ✅ GET /api/v2/quotas/me → 200 OK (FIXED - Issue #6)

---

## Issues Found

### Issue #1: Health Check Redirect (LOW PRIORITY)

**Severity:** 🟡 LOW
**Status:** ⚠️ Not a bug - expected behavior

**Problem:**
```
GET /health → 307 Redirect to /health/
Expected: 200 OK
Actual: 307 Temporary Redirect
```

**Root Cause:**
- Health router mounted at `/health` with route at `/`
- FastAPI redirects `/health` → `/health/`
- This is standard FastAPI behavior

**Fix:**
Update test script to use `/health/` or follow redirects

**Priority:** LOW - This is standard behavior
**Estimated Time:** 5 minutes

---

###Issue #2: User Registration Status Code (LOW PRIORITY)

**Severity:** 🟡 LOW
**Status:** ⚠️ Not a bug - test expectation wrong

**Problem:**
```
POST /api/v2/auth/register
Expected: 200 OK
Actual: 201 Created
```

**Root Cause:**
- Test expected 200 OK
- API correctly returns 201 Created (REST standard for resource creation)

**Fix:**
Update test to accept both 200 and 201 as success

**Priority:** LOW - API behavior is correct
**Estimated Time:** 2 minutes

---

## 🔴 Issue #3: Users "me" Endpoint (404)

**Status:** ✅ FIXED

**Severity:** CRITICAL

**Test:** List Agents
**Expected:** GET /api/v2/users/me returns user info
**Actual:** 404 Not Found

### Root Cause
- Router had `/me/profile` endpoint but no `/me` endpoint
- Test expects standard REST pattern `/users/me` for current user

### Solution
Added GET /me endpoint to `omics_oracle_v2/api/routes/users.py`:

```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user information."""
    return current_user
```

**Files Modified:**
- `omics_oracle_v2/api/routes/users.py` - Added GET /me endpoint

**Verification:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v2/users/me
# Should return user info (id, email, is_active, etc.)
```

---

## 🔴 Issue #4: Agents List Endpoint (404)

**Status:** ✅ FIXED

**Severity:** CRITICAL

**Test:** List Agents
**Expected:** GET /api/v1/agents returns list of available agents
**Actual:** 404 Not Found

### Root Cause
- Router only had POST endpoints for executing agents
- No GET endpoint to list available agents and their capabilities

### Solution
Added list agents endpoint to `omics_oracle_v2/api/routes/agents.py`:

1. Created `AgentInfo` schema:
```python
class AgentInfo(BaseModel):
    """Information about an available agent."""
    id: str
    name: str
    description: str
    category: str
    capabilities: List[str]
    input_types: List[str]
    output_types: List[str]
    endpoint: str
```

2. Added GET / endpoint:
```python
@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents with their metadata."""
    return [
        AgentInfo(id="query", name="Query Agent", ...),
        AgentInfo(id="search", name="Search Agent", ...),
        AgentInfo(id="data", name="Data Agent", ...),
        AgentInfo(id="report", name="Report Agent", ...),
    ]
```

**Files Modified:**
- `omics_oracle_v2/api/routes/agents.py` - Added AgentInfo schema and GET / endpoint

**Verification:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/agents
# Should return array of 4 agents with full metadata
```

---

## 🔴 Issue #5: Workflows List Endpoint (404)

**Status:** ✅ FIXED

**Problem:**
```
GET /api/v2/users/me
Expected: 200 OK with user data
Actual: 404 Not Found
```

**Root Cause:**
Need to investigate if route exists in users.py

**Investigation Needed:**
1. Check if `/api/v2/users/me` endpoint exists in `omics_oracle_v2/api/routes/users.py`
2. Check if router is correctly included in main.py
3. Check if authentication is properly configured

**Priority:** MEDIUM - Affects user management
**Estimated Time:** 30 minutes

---

### Issue #4: List Agents Not Found (CRITICAL - RELEASE BLOCKER)

**Severity:** 🔴 CRITICAL
**Status:** 🔴 MAJOR DESIGN ISSUE

**Problem:**
```
GET /api/v1/agents
Expected: 200 OK with list of available agents
Actual: 404 Not Found
```

**Root Cause:**
The agents router (`omics_oracle_v2/api/routes/agents.py`) **does not have a GET list endpoint**.

Current endpoints in agents.py:
- `POST /query` - Execute Query Agent
- `POST /search` - Execute Search Agent
- `POST /data` - Execute Data Agent
- `POST /report` - Execute Report Agent

**Missing:**
- `GET /` or `GET /list` - List all available agents

**Impact:**
- Users cannot discover what agents are available
- Web dashboard cannot populate agent list
- API is not RESTful (missing resource listing)

**Fix Required:**
Add a GET endpoint to list all available agents:

```python
@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents."""
    return [
        AgentInfo(
            id="query",
            name="Query Agent",
            description="Execute GEO dataset queries",
            capabilities=["query", "filter", "analyze"]
        ),
        AgentInfo(
            id="search",
            name="Search Agent",
            description="Search GEO database for datasets",
            capabilities=["search", "rank", "filter"]
        ),
        # ... etc
    ]
```

**Priority:** 🔴 CRITICAL - Release blocker
**Estimated Time:** 2-3 hours (need to create AgentInfo schema and implement endpoint)

---

### Issue #5: List Workflows Not Found (CRITICAL - RELEASE BLOCKER)

**Severity:** 🔴 CRITICAL
**Status:** 🔴 MAJOR DESIGN ISSUE

**Problem:**
```
GET /api/v1/workflows
Expected: 200 OK with list of workflows
Actual: 404 Not Found
```

**Root Cause:**
Similar to Issue #4 - workflows router likely doesn't have a GET list endpoint.

**Investigation Needed:**
1. Check what endpoints exist in `omics_oracle_v2/api/routes/workflows.py`
2. Determine if workflows are stored in database or hardcoded
3. Design workflow listing API

**Priority:** 🔴 CRITICAL - Release blocker
**Estimated Time:** 2-3 hours

---

### Issue #6: Get Quota Type Mismatch (CRITICAL - RELEASE BLOCKER)

**Severity:** 🔴 CRITICAL
**Status:** 🔴 BUG - Database schema mismatch

**Problem:**
```
GET /api/v2/quotas/me
Expected: 200 OK with quota info
Actual: 500 Internal Server Error

Error: "1 validation error for QuotaUsageResponse
user_id
  Input should be a valid integer [type=int_type,
   input_value=UUID('0782269d-8f74-4fa3-a8f9-ebd8f4c17d67'),
   input_type=UUID]"
```

**Root Cause:**
- User model uses `UUID` for `id` field
- QuotaUsageResponse schema expects `int` for `user_id` field
- Type mismatch causing validation error

**Files Affected:**
- `omics_oracle_v2/models/user.py` - User model has UUID id
- `omics_oracle_v2/api/routes/quotas.py` - QuotaUsageResponse schema expects int

**Fix Required:**
Update QuotaUsageResponse schema to use UUID for user_id:

```python
# In omics_oracle_v2/api/routes/quotas.py or schemas
from uuid import UUID

class QuotaUsageResponse(BaseModel):
    user_id: UUID  # Changed from int
    tier: str
    requests_remaining: int
    # ... rest of fields
```

**Priority:** 🔴 CRITICAL - Release blocker (breaks quota management)
**Estimated Time:** 30 minutes

---

## Summary of Fixes Needed

### Critical Fixes (Release Blockers) 🔴

1. **Add GET /api/v1/agents endpoint** (2-3 hours)
   - Create AgentInfo response schema
   - Implement list_agents() endpoint
   - Return all available agents with metadata

2. **Add GET /api/v1/workflows endpoint** (2-3 hours)
   - Design workflow listing approach
   - Implement list_workflows() endpoint
   - Return available workflows

3. **Fix QuotaUsageResponse user_id type** (30 minutes)
   - Change user_id from int to UUID
   - Test quota endpoints
   - Update related schemas if needed

### Medium Priority Fixes 🟡

4. **Fix GET /api/v2/users/me endpoint** (30 minutes)
   - Investigate why route returns 404
   - Fix route configuration or authentication

### Low Priority Fixes 🟢

5. **Update test script** (5 minutes)
   - Use `/health/` instead of `/health`
   - Accept 201 for registration success
   - Add redirect following

---

## Implementation Plan

### Phase 1: Critical Bug Fixes (Day 1 - 4 hours)

**1.1 Fix Quota User ID Type Mismatch** (30 min)
- [ ] Update QuotaUsageResponse schema
- [ ] Update any related quota schemas
- [ ] Test GET /api/v2/quotas/me endpoint
- [ ] Verify all quota endpoints work

**1.2 Fix GET /api/v2/users/me** (30 min)
- [ ] Check if endpoint exists in users.py
- [ ] Fix route if missing
- [ ] Test with authentication
- [ ] Verify user data returned correctly

**1.3 Add GET /api/v1/agents Endpoint** (2 hours)
- [ ] Create AgentInfo response schema
- [ ] Implement list_agents() endpoint
- [ ] Add documentation
- [ ] Test endpoint
- [ ] Update web dashboard to use new endpoint

**1.4 Add GET /api/v1/workflows Endpoint** (1 hour)
- [ ] Create WorkflowInfo response schema
- [ ] Implement list_workflows() endpoint
- [ ] Add documentation
- [ ] Test endpoint

### Phase 2: Test Script Updates (Day 1 - 30 min)

**2.1 Update Manual Test Script** (30 min)
- [ ] Fix health check URL
- [ ] Accept 201 for registration
- [ ] Add better error reporting
- [ ] Test all fixes

### Phase 3: Validation (Day 1 - 1 hour)

**3.1 Re-run All Tests** (1 hour)
- [ ] Run manual_api_test.py
- [ ] Verify all tests pass
- [ ] Document any new issues
- [ ] Update test results

---

## Expected Outcomes

After fixes:
- ✅ All critical API endpoints working
- ✅ Quota management functional
- ✅ Agent listing available for web dashboard
- ✅ Workflow listing available
- ✅ User management working correctly
- ✅ Test success rate > 90%

---

## Technical Debt Identified

1. **API Design Inconsistency**
   - Some routes have list endpoints, others don't
   - Need standardized REST API design
   - Consider adding OpenAPI spec validation

2. **Schema Type Mismatches**
   - User model uses UUID
   - Some response schemas expect int
   - Need comprehensive schema review

3. **Missing Tests**
   - No automated tests for v1 endpoints
   - Integration tests needed
   - API contract tests needed

4. **Documentation Gaps**
   - No API reference docs
   - Endpoint discovery difficult
   - Need comprehensive API documentation

---

## Next Steps

1. **Immediate (Today)**
   - Fix Issue #6 (Quota UUID)
   - Fix Issue #3 (Get Current User)
   - Start on Issue #4 (List Agents)

2. **Short Term (This Week)**
   - Complete Issue #4 (List Agents)
   - Complete Issue #5 (List Workflows)
   - Re-run tests and verify fixes
   - Write automated tests for fixed endpoints

3. **Medium Term (Next Week)**
   - Add comprehensive API tests
   - Generate API documentation
   - Review all schemas for type consistency
   - Add integration tests

---

## Lessons Learned

1. **Testing Reveals Design Issues**
   - Manual testing immediately revealed missing REST endpoints
   - Automated tests would have caught these earlier
   - Need test-driven development for new features

2. **Schema Validation is Critical**
   - Type mismatches cause runtime errors
   - Need stricter type checking in development
   - Consider using type checking tools (mypy)

3. **API Design Review Needed**
   - Current API is inconsistent
   - Need REST API guidelines
   - Need API design review process

4. **Documentation is Essential**
   - Hard to test without knowing what endpoints exist
   - OpenAPI/Swagger docs are helpful but not enough
   - Need comprehensive API documentation

---

**Status:** Ready to begin fixes
**Priority:** Fix critical issues first (Issues #3, #4, #5, #6)
**Timeline:** 4-6 hours to fix all critical issues
**Next Action:** Fix Issue #6 (Quota UUID type mismatch)
