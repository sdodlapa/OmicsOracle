# Folder Investigation Plan - omics_oracle_v2/

**Date**: October 15, 2025  
**Status**: In Progress  
**Current cleanup**: 3,867 LOC eliminated from lib/

---

## Folders Overview (Sorted by Priority)

| Folder | Files | LOC | Priority | Status |
|--------|-------|-----|----------|--------|
| **api/** | 24 | 5,166 | 🔴 HIGH | 🔍 Investigating |
| **auth/** | 7 | 1,429 | 🟡 MEDIUM | ⏳ Pending |
| **agents/** | 9 | 1,220 | 🟡 MEDIUM | ⏳ Pending |
| **core/** | 4 | 958 | 🟡 MEDIUM | ⏳ Pending |
| **tracing/** | 1 | 456 | 🟢 LOW | ⏳ Pending |
| **database/** | 5 | 304 | 🟢 LOW | ⏳ Pending |
| **middleware/** | 2 | 156 | 🟢 LOW | ⏳ Pending |
| **config/** | 1 | 35 | 🟢 LOW | ⏳ Pending |
| **services/** | 1 | 9 | 🟢 LOW | ⏳ Pending |
| **lib/** | - | - | - | ✅ Partially cleaned |
| **cache/** | 8 | ~2,229 | - | ✅ Consolidated |

**Total code to investigate**: ~9,727 LOC (excluding lib/ and cache/)

---

## 1. api/ - REST API Endpoints (5,166 LOC) 🔴

### Structure
```
api/
├── routes/
│   ├── agents.py        1,813 LOC ⚠️ BLOATED - 4 endpoints
│   ├── users.py           369 LOC
│   ├── auth.py            340 LOC
│   ├── debug.py           317 LOC
│   ├── websockets.py      109 LOC
│   ├── health.py          148 LOC
│   └── metrics.py          30 LOC
├── models/
│   ├── responses.py       177 LOC
│   ├── ml_schemas.py      144 LOC
│   ├── workflow.py        117 LOC
│   └── requests.py         89 LOC
├── helpers/
│   └── llm.py              73 LOC
├── main.py                325 LOC
├── batch.py               314 LOC
├── metrics.py             289 LOC
├── websocket.py           188 LOC
├── middleware.py           84 LOC
├── dependencies.py         75 LOC
└── config.py               59 LOC
```

### Issues Identified

#### 🚨 **CRITICAL: `routes/agents.py` is 1,813 LOC**

**Problem**: Business logic embedded directly in API routes

**4 Endpoints breakdown**:
1. `/search` - Lines 42-447 (405 LOC)
2. `/enrich-fulltext` - Lines 447-1353 (906 LOC) ⚠️ **MASSIVE**
3. `/analyze` - Lines 1353-1759 (406 LOC)
4. `/complete-geo-data` - Lines 1759-1814 (55 LOC)

**Root cause**: `/enrich-fulltext` contains:
- PDF download logic
- Citation discovery logic
- Full-text parsing logic
- Error handling
- Logging
- Response formatting

**Should be**: Thin API layer calling pipeline services

**Recommendation**:
- Extract business logic to `lib/pipelines/` services
- API route should be ~50-100 LOC max per endpoint
- **Potential cleanup**: 600-800 LOC by refactoring to service layer

#### Analysis of other routes:
- `users.py` (369 LOC) - May have embedded business logic
- `auth.py` (340 LOC) - Authentication logic (reasonable size)
- `debug.py` (317 LOC) - Debug endpoints (investigate if needed in production)

### Investigation Tasks

- [ ] **agents.py refactoring**:
  - [ ] Check if `/enrich-fulltext` logic duplicates existing pipeline code
  - [ ] Extract to `lib/pipelines/fulltext_enrichment_service.py`
  - [ ] Reduce route to thin controller (<100 LOC)
  
- [ ] **debug.py review**:
  - [ ] Determine if debug endpoints needed in production
  - [ ] Consider moving to dev-only module
  
- [ ] **batch.py analysis** (314 LOC):
  - [ ] Check for duplicate logic with main routes
  
- [ ] **Overall API cleanup**:
  - [ ] Identify code that belongs in `services/` or `lib/`
  - [ ] Move business logic out of API layer

---

## 2. auth/ - Authentication & Authorization (1,429 LOC) 🟡

### Structure
```
auth/
├── dependencies.py    8,811 bytes (largest)
├── security.py        4,777 bytes
├── schemas.py         4,637 bytes
├── crud.py            6,879 bytes
├── models.py          3,395 bytes
└── quota.py           7,247 bytes
```

### Initial Assessment
- Size seems reasonable for auth system
- Contains: OAuth, JWT, API keys, rate limiting, quotas
- **Likely well-organized** - auth is typically isolated

### Investigation Tasks
- [ ] Check for unused authentication methods
- [ ] Verify quota.py isn't duplicating rate_limit logic in middleware/
- [ ] Look for any hardcoded secrets or config that should be in config/

---

## 3. agents/ - Agent Orchestration (1,220 LOC) 🟡

### Structure
```
agents/
├── models/
│   ├── orchestrator.py
│   ├── search.py
│   ├── report.py
│   └── data.py
├── base.py            11,633 bytes (largest)
├── context.py          5,651 bytes
└── exceptions.py         808 bytes
```

### Initial Assessment
- Agent pattern for orchestrating complex workflows
- `base.py` is large (11KB) - investigate for base classes
- Models for different agent types

### Investigation Tasks
- [ ] Check if agents/ duplicates functionality in lib/search_orchestration/
- [ ] Verify agent pattern is actually used (not dead code)
- [ ] Look for overlap with api/routes/agents.py

---

## 4. core/ - Core Configuration (958 LOC) 🟡

### Structure
```
core/
├── config.py         24,846 bytes ⚠️ LARGE
├── exceptions.py      1,342 bytes
└── types.py             718 bytes
```

### Issues Identified

#### ⚠️ **config.py is 24KB (958 LOC)**
- Potentially bloated configuration file
- May contain logic that should be in services/

### Investigation Tasks
- [ ] **config.py deep dive**:
  - [ ] Check for duplicate config with `config/` folder
  - [ ] Look for logic that should be in services
  - [ ] Identify environment-specific config vs. code
  
- [ ] **Overlap analysis**:
  - [ ] Compare with `omics_oracle_v2/config/` folder
  - [ ] Compare with `api/config.py`
  - [ ] Consolidate if duplicated

---

## 5. tracing/ - Observability (456 LOC) 🟢

### Structure
```
tracing/
└── __init__.py       456 LOC
```

### Initial Assessment
- Single file for tracing/telemetry
- Size is reasonable
- Likely OpenTelemetry or similar

### Investigation Tasks
- [ ] Quick review for unused tracing code
- [ ] Verify it's actually being used in production

---

## 6. database/ - Database Layer (304 LOC) 🟢

### Structure
```
database/
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 001_initial_user_apikey_tables.py
├── session.py        2,999 bytes
└── base.py             175 bytes
```

### Initial Assessment
- Small, focused on DB connection/session management
- Alembic migrations present
- **Likely well-organized**

### Investigation Tasks
- [ ] Quick scan for unused DB utilities
- [ ] Check if lib/pipelines/storage/ duplicates any logic

---

## 7. middleware/ - HTTP Middleware (156 LOC) 🟢

### Structure
```
middleware/
└── rate_limit.py     4,515 bytes
```

### Initial Assessment
- Single file for rate limiting
- Small and focused

### Investigation Tasks
- [ ] Check overlap with auth/quota.py
- [ ] Verify both rate limiting systems are needed

---

## 8. config/ - Environment Config (35 LOC) 🟢

### Structure
```
config/
└── production.py     35 LOC
```

### Initial Assessment
- Very small, production-specific config
- Part of multi-environment setup

### Investigation Tasks
- [ ] Compare with core/config.py (958 LOC)
- [ ] Determine why config is split between 3 places:
  - omics_oracle_v2/config/production.py (35 LOC)
  - omics_oracle_v2/core/config.py (958 LOC)
  - omics_oracle_v2/api/config.py (59 LOC)

---

## 9. services/ - Business Services (9 LOC) 🟢

### Structure
```
services/
└── __init__.py       9 LOC (just imports)
```

### Issues Identified

#### 🤔 **Services folder is empty but 5,166 LOC in api/**
- This is backwards! Business logic should be in `services/`, not `api/routes/`
- **Major architectural issue**: Fat controllers, thin services

### Recommendation
- Extract business logic from `api/routes/agents.py` to `services/`
- Structure:
  ```
  services/
  ├── search_service.py         # Extract from /search endpoint
  ├── enrichment_service.py     # Extract from /enrich-fulltext
  ├── analysis_service.py       # Extract from /analyze
  └── dataset_service.py        # Extract from /complete-geo-data
  ```

### Investigation Tasks
- [ ] **Design service layer** before refactoring API
- [ ] Identify all business logic currently in API routes
- [ ] Move to services/ with proper separation of concerns

---

## Summary of Red Flags

### 🚨 Critical Issues

1. **api/routes/agents.py (1,813 LOC)**
   - 906 LOC in single endpoint
   - Business logic in API layer
   - **Potential cleanup**: 600-800 LOC

2. **Empty services/ folder**
   - Business logic should live here, not in API routes
   - **Architectural debt**

3. **Config scattered across 3 locations**
   - core/config.py (958 LOC)
   - config/production.py (35 LOC)
   - api/config.py (59 LOC)
   - **Potential consolidation needed**

### ⚠️ Investigation Needed

1. **Overlap between**:
   - agents/ (1,220 LOC) vs. api/routes/agents.py (1,813 LOC)
   - auth/quota.py vs. middleware/rate_limit.py
   - Multiple config files

2. **Debug endpoints in production**:
   - api/routes/debug.py (317 LOC)
   - Should these be dev-only?

---

## Investigation Priority Order

### Phase 1: Quick Wins (Low-hanging fruit)
1. ✅ Check services/ - already done (empty)
2. ⏳ Review tracing/ (456 LOC) - single file
3. ⏳ Review middleware/ (156 LOC) - check overlap with auth/
4. ⏳ Review config consolidation (3 files)

### Phase 2: Medium Complexity
5. ⏳ agents/ folder (1,220 LOC) - check for duplication
6. ⏳ auth/ folder (1,429 LOC) - look for unused code
7. ⏳ database/ folder (304 LOC) - quick scan

### Phase 3: Major Refactoring
8. ⏳ **api/routes/agents.py (1,813 LOC)** - extract to services
9. ⏳ api/routes/debug.py (317 LOC) - production vs. dev
10. ⏳ core/config.py (958 LOC) - consolidate configs

---

## Next Steps

1. **Start with smallest folders first** (services/, tracing/, middleware/)
2. **Identify duplication patterns** before refactoring
3. **Extract business logic from API to services/** (biggest win)
4. **Consolidate configuration** (3 files → 1 clear structure)
5. **Continue pattern from lib/ cleanup** (evidence-based deletion)

---

## Expected Outcomes

**Conservative estimate**:
- api/ refactoring: 600-800 LOC reduction
- Config consolidation: 200-300 LOC reduction
- Duplication removal: 100-200 LOC reduction

**Total potential**: 900-1,300 LOC additional cleanup

**Combined with lib/ cleanup**: 3,867 + 1,000 = **~4,867 LOC eliminated**

---

## Questions for User

1. Should debug endpoints (api/routes/debug.py) be removed from production?
2. Are all authentication methods in auth/ actively used?
3. Is the agent pattern (agents/) still in use, or archived?
4. Should we prioritize refactoring api/routes/agents.py first (biggest impact)?
