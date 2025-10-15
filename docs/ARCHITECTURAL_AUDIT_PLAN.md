# Architectural Audit Plan: Unified Database Integration

**Date:** October 14, 2025  
**Goal:** Verify frontend/routes use NEW unified database, not old duplicate pipelines  
**Critical:** Ensure no parallel search flows or duplicate code paths

---

## 🔍 Audit Strategy

### **Step 1: Map All Search Entry Points** (5 min)
Find every place a search can be initiated:
- Frontend dashboard routes
- API endpoints
- CLI commands
- Background jobs

### **Step 2: Trace Search Flow** (10 min)
For each entry point, follow the code path:
```
Frontend → API Route → Orchestrator → Pipeline → Database
```
Verify each step uses the NEW unified components.

### **Step 3: Identify Duplicate/Legacy Code** (10 min)
Search for:
- Old database classes (not UnifiedDatabase)
- Old storage classes (not GEOStorage)
- Old pipeline coordinators (not new PipelineCoordinator)
- Parallel search implementations

### **Step 4: Check Import Statements** (5 min)
Verify routes import from:
- ✅ `omics_oracle_v2.lib.database.database.UnifiedDatabase`
- ✅ `omics_oracle_v2.lib.storage.geo_storage.GEOStorage`
- ✅ `omics_oracle_v2.lib.pipelines.coordinator.PipelineCoordinator`
- ❌ NOT old paths or legacy classes

### **Step 5: Database Connection Audit** (5 min)
Find all database connections:
- Should use UnifiedDatabase ONLY
- No direct sqlite3 or SQLAlchemy connections
- No old database.py files

### **Step 6: Verify No Orphaned Code** (5 min)
Check for unused/orphaned:
- Old pipeline implementations
- Duplicate search orchestrators
- Legacy database schemas

---

## 🔬 Detailed Audit Steps

### **Step 1: Find All Search Entry Points**

```bash
# Find API routes that handle searches
grep -r "POST.*search" omics_oracle_v2/api/routes/ --include="*.py"
grep -r "GET.*search" omics_oracle_v2/api/routes/ --include="*.py"

# Find search orchestrator usage
grep -r "SearchOrchestrator\|Orchestrator" omics_oracle_v2/api/ --include="*.py"

# Find all API route files
ls -la omics_oracle_v2/api/routes/
```

### **Step 2: Trace Search Flow from Frontend**

**From logs, we know:**
- Endpoint: `POST /api/agents/search`
- File: `omics_oracle_v2/api/routes/agents.py`

**Audit this file for:**
1. What orchestrator does it use?
2. Does it use UnifiedDatabase?
3. Does it use new PipelineCoordinator?
4. Are there any old imports?

### **Step 3: Check Orchestrator Implementation**

**From logs:**
- File: `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Questions:**
1. Does it import UnifiedDatabase?
2. Does it import PipelineCoordinator?
3. Does it use GEOStorage?
4. Or does it use old/legacy database code?

### **Step 4: Database Usage Audit**

```bash
# Find all UnifiedDatabase imports
grep -r "from.*UnifiedDatabase\|import.*UnifiedDatabase" omics_oracle_v2/ --include="*.py"

# Find old database imports (should be NONE in active code)
grep -r "from.*database import\|import.*database" omics_oracle_v2/api/ --include="*.py" | grep -v UnifiedDatabase

# Find direct sqlite3 usage (should be minimal, only in UnifiedDatabase)
grep -r "import sqlite3" omics_oracle_v2/api/ --include="*.py"

# Find SQLAlchemy usage (should not exist in new code)
grep -r "from sqlalchemy\|import sqlalchemy" omics_oracle_v2/api/ --include="*.py"
```

### **Step 5: Pipeline Coordinator Audit**

```bash
# Find PipelineCoordinator imports
grep -r "PipelineCoordinator" omics_oracle_v2/ --include="*.py"

# Find old coordinator imports (should be NONE)
grep -r "class.*Coordinator" omics_oracle_v2/lib/ --include="*.py"

# Check for duplicate pipeline implementations
find omics_oracle_v2/lib -name "*pipeline*" -o -name "*coordinator*"
```

### **Step 6: GEOStorage Integration Audit**

```bash
# Find GEOStorage usage
grep -r "GEOStorage" omics_oracle_v2/ --include="*.py"

# Find old storage implementations
grep -r "class.*Storage" omics_oracle_v2/lib/ --include="*.py" | grep -v GEOStorage
```

---

## 🎯 Expected Findings

### **GOOD (Using New Unified System):**

```python
# In omics_oracle_v2/api/routes/agents.py or orchestrator.py:
from omics_oracle_v2.lib.database.database import UnifiedDatabase
from omics_oracle_v2.lib.storage.geo_storage import GEOStorage
from omics_oracle_v2.lib.pipelines.coordinator import PipelineCoordinator

# Search handler:
async def search(query: str):
    db = UnifiedDatabase()
    coordinator = PipelineCoordinator(db_path="...")
    results = await coordinator.execute_search(query)
    return results
```

### **BAD (Using Old/Duplicate Code):**

```python
# Old database:
from omics_oracle_v2.database import Database  # ❌ Wrong!
from omics_oracle_v2.old_db import SessionLocal  # ❌ Legacy!

# Direct sqlite3:
import sqlite3  # ❌ Should only be in UnifiedDatabase!
conn = sqlite3.connect("old.db")  # ❌ Bypass new system!

# Old coordinator:
from omics_oracle_v2.lib.old_pipelines import OldCoordinator  # ❌ Deprecated!
```

---

## 📋 Audit Checklist

I will check each of these and report findings:

- [ ] **API Routes (`omics_oracle_v2/api/routes/agents.py`)**
  - [ ] Uses UnifiedDatabase?
  - [ ] Uses PipelineCoordinator?
  - [ ] Uses GEOStorage?
  - [ ] No old imports?

- [ ] **Search Orchestrator (`omics_oracle_v2/lib/search_orchestration/orchestrator.py`)**
  - [ ] Uses UnifiedDatabase?
  - [ ] Uses PipelineCoordinator?
  - [ ] Uses GEOStorage?
  - [ ] No parallel pipeline implementations?

- [ ] **Database Connections**
  - [ ] All use UnifiedDatabase?
  - [ ] No direct sqlite3 in routes/orchestrator?
  - [ ] No old database.py files in use?

- [ ] **Pipeline Implementations**
  - [ ] Only PipelineCoordinator in use?
  - [ ] No duplicate/legacy coordinators?
  - [ ] All 4 pipelines (P1-P4) integrated?

- [ ] **Storage Layer**
  - [ ] GEOStorage used for all file operations?
  - [ ] No old storage implementations?
  - [ ] SHA256 integrity checks active?

- [ ] **Dependency Injection**
  - [ ] Routes get dependencies from container?
  - [ ] No hardcoded paths/connections?
  - [ ] Proper lifecycle management?

---

## 🔧 Remediation Plan

### **If I Find Old Code:**

1. **Identify the duplicate code path**
2. **Map what it does**
3. **Find equivalent in new system**
4. **Replace imports and calls**
5. **Test the change**
6. **Remove/archive old code**

### **If I Find No Integration:**

1. **Identify the gap**
2. **Design integration approach**
3. **Implement integration**
4. **Test integration**
5. **Update documentation**

---

## 🚀 Execution Plan

### **Phase 1: Discovery (30 minutes)**

Execute all audit steps above and document findings in a report:
- What's using new unified system ✅
- What's using old/duplicate code ❌
- What's not integrated ⚠️

### **Phase 2: Analysis (15 minutes)**

Analyze findings:
- Is frontend using unified database?
- Is orchestrator using new pipelines?
- Are there parallel search flows?
- What needs to be fixed?

### **Phase 3: Integration Fix (1-2 hours)**

If issues found:
- Update routes to use UnifiedDatabase
- Update orchestrator to use PipelineCoordinator
- Remove duplicate code paths
- Test integration

### **Phase 4: Validation (30 minutes)**

- Test search from frontend
- Verify database writes to unified schema
- Verify no errors in logs
- Confirm single code path

---

## 📊 Success Criteria

**System is properly integrated when:**

✅ Frontend search → API route → Orchestrator → **NEW** PipelineCoordinator → UnifiedDatabase  
✅ No parallel/duplicate search implementations  
✅ No old database/storage/pipeline imports in active code  
✅ All database writes go to UnifiedDatabase (8-table schema)  
✅ All file operations use GEOStorage (SHA256, manifests)  
✅ Single source of truth for each component  

**Red Flags (will require fixes):**

❌ Multiple database classes in use  
❌ Multiple coordinator classes in use  
❌ Direct sqlite3 connections in routes/orchestrator  
❌ Old imports from legacy paths  
❌ Parallel search implementations  

---

## 🎯 Next Step

**I will now execute the audit:**

1. Read API route file (`agents.py`)
2. Read orchestrator file
3. Check all imports
4. Trace search flow
5. Identify issues
6. Generate findings report

**Then based on findings:**
- **If clean:** Proceed to fix PubMed/OpenAlex bugs only
- **If issues found:** Fix integration first, then bugs

**Estimated Time:**
- Audit: 30 minutes
- Report: 15 minutes
- Fixes (if needed): 1-2 hours
- Total: 2-3 hours worst case

---

**Ready to proceed with the audit?**

I'll read through the code systematically and give you a comprehensive report on what's connected to what, and what needs fixing.
