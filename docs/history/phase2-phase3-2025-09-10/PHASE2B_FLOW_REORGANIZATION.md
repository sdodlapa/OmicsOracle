# Phase 2B: Flow-Based Reorganization Plan

**Date:** October 13, 2025
**Status:** 🚧 In Progress
**Approach:** Incremental with validation at each step

---

## Overview

Reorganize codebase to match actual production flow stages (not theoretical layers).

**Key Principle:** Test after EACH step before proceeding to next.

---

## Current vs. Proposed Structure

### Current (Confusing)
```
lib/
├── geo/                    # GEO search - but where in flow?
├── publications/           # Mixed: Search + URL sources
├── citations/              # Citation search
├── fulltext/               # Mixed: URL discovery + parsing
├── storage/                # PDF download
├── search/                 # Orchestration
├── query/                  # Query processing
├── nlp/                    # Query processing
├── ai/                     # AI analysis
└── cache/                  # Infrastructure
```

### Proposed (Flow-Based)
```
lib/
├── query_processing/       # Stage 3: NLP + Query optimization
│   ├── nlp/               # NER, expansion, synonyms
│   └── optimization/       # analyzer, optimizer
│
├── search_orchestration/   # Stage 4: Orchestration
│   └── orchestrator.py    # Coordinates parallel search
│
├── search_engines/         # Stage 5: PRIMARY search engines
│   ├── geo/               # 5a: GEO search (PRIMARY)
│   └── citations/          # 5b: PubMed, OpenAlex, Scholar
│
├── enrichment/             # Stages 6-8: Full-text pipeline
│   └── fulltext/
│       ├── manager.py      # Stage 6: URL discovery
│       ├── downloader.py   # Stage 7: PDF download
│       ├── parser.py       # Stage 8: Text extraction
│       └── sources/        # 11 URL sources (organized)
│
├── analysis/               # Stage 9: AI analysis
│   └── ai/
│
└── infrastructure/         # Cross-cutting concerns
    └── cache/              # Redis caching
```

**Note:** Numbers removed from directory names - Python modules cannot start with digits.

---

## Step-by-Step Execution Plan

### STEP 1: Create New Directory Structure
**Goal:** Set up empty directories for new organization
**Risk:** None (just creating dirs)
**Time:** 2 minutes

```bash
# Create main flow directories
mkdir -p omics_oracle_v2/lib/1_query_processing/{nlp,optimization}
mkdir -p omics_oracle_v2/lib/2_search
mkdir -p omics_oracle_v2/lib/3_search_engines/{geo,citations}
mkdir -p omics_oracle_v2/lib/4_enrichment/fulltext/{sources,caching}
mkdir -p omics_oracle_v2/lib/5_analysis/ai
mkdir -p omics_oracle_v2/lib/infrastructure/cache

# Create organized fulltext sources
mkdir -p omics_oracle_v2/lib/4_enrichment/fulltext/sources/{free,aggregators,institutional,academic,fallback}
```

**Validation:**
```bash
# Verify directories created
ls -la omics_oracle_v2/lib/
tree omics_oracle_v2/lib/ -L 2
```

---

### STEP 2: Move Query Processing (Stage 3)
**Goal:** Consolidate NLP + query optimization
**Risk:** LOW - these are early in flow
**Files:** 5 files, ~1,604 LOC

```bash
# Copy first (safe - keeps originals)
cp -r omics_oracle_v2/lib/nlp/* omics_oracle_v2/lib/1_query_processing/nlp/
cp -r omics_oracle_v2/lib/query/* omics_oracle_v2/lib/1_query_processing/optimization/

# Create __init__.py files
touch omics_oracle_v2/lib/1_query_processing/__init__.py
touch omics_oracle_v2/lib/1_query_processing/nlp/__init__.py
touch omics_oracle_v2/lib/1_query_processing/optimization/__init__.py
```

**Update imports in new location:**
```python
# In 1_query_processing/nlp/*.py files
# Change: from omics_oracle_v2.lib.nlp import X
# To: from omics_oracle_v2.lib.1_query_processing.nlp import X
```

**Validation:**
```bash
# Test imports
python3 -c "
from omics_oracle_v2.lib.1_query_processing.nlp.biomedical_ner import BiomedicalNER
from omics_oracle_v2.lib.1_query_processing.optimization.analyzer import QueryAnalyzer
print('✓ Query processing imports work')
"

# Check for errors
python3 -m py_compile omics_oracle_v2/lib/1_query_processing/nlp/*.py
python3 -m py_compile omics_oracle_v2/lib/1_query_processing/optimization/*.py
```

**If validation passes, commit:**
```bash
git add omics_oracle_v2/lib/1_query_processing/
git commit -m "Step 2: Copy query processing to new structure (validation pending)"
```

---

### STEP 3: Update Search Orchestrator to Use New Query Processing
**Goal:** Point orchestrator to new query paths
**Risk:** MEDIUM - orchestrator is critical
**Files:** lib/search/orchestrator.py

```bash
# Find all query/nlp imports in search module
grep -n "from.*lib\.query\|from.*lib\.nlp" omics_oracle_v2/lib/search/*.py
```

**Update imports:**
```python
# In lib/search/orchestrator.py
# OLD:
from omics_oracle_v2.lib.query.analyzer import QueryAnalyzer
from omics_oracle_v2.lib.nlp.biomedical_ner import BiomedicalNER

# NEW:
from omics_oracle_v2.lib.1_query_processing.optimization.analyzer import QueryAnalyzer
from omics_oracle_v2.lib.1_query_processing.nlp.biomedical_ner import BiomedicalNER
```

**Validation:**
```bash
# Test search orchestrator imports
python3 -c "
from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator
print('✓ Search orchestrator imports work')
"

# Test server startup
python3 -c "from omics_oracle_v2.api.main import app; print('✓ Server imports successfully')"
```

**If validation passes:**
```bash
git add omics_oracle_v2/lib/search/
git commit -m "Step 3: Update orchestrator to use new query processing paths"
```

---

### STEP 4: Update API Routes to Use New Query Processing
**Goal:** Point API to new query paths
**Risk:** HIGH - API is entry point
**Files:** api/routes/agents.py

```bash
# Find query/nlp imports in API
grep -n "from.*lib\.query\|from.*lib\.nlp" omics_oracle_v2/api/routes/*.py
```

**Update imports in api/routes/agents.py**

**Validation:**
```bash
# Full server test
./start_omics_oracle.sh &
sleep 5

# Test health endpoint
curl http://localhost:8000/health

# Test search endpoint with sample query
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "BRCA1 breast cancer", "max_results": 5}'

# Kill server
pkill -f "uvicorn.*omics_oracle"
```

**If validation passes:**
```bash
git add omics_oracle_v2/api/
git commit -m "Step 4: Update API to use new query processing paths"
```

---

### STEP 5: Remove Old Query/NLP Directories
**Goal:** Clean up old locations
**Risk:** LOW (already validated new paths work)

```bash
# Final check - nothing should import from old paths
grep -r "from.*lib\.query\|from.*lib\.nlp" omics_oracle_v2/ \
  --include="*.py" \
  --exclude-dir=1_query_processing \
  --exclude-dir=__pycache__

# If clear, remove old directories
git rm -r omics_oracle_v2/lib/query/
git rm -r omics_oracle_v2/lib/nlp/

git commit -m "Step 5: Remove old query/nlp directories (migrated to 1_query_processing)"
```

**Validation:**
```bash
# Full search flow test
./start_omics_oracle.sh &
sleep 5

# Run comprehensive search
python3 -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/search',
    json={'query': 'GSE12345 BRCA1', 'max_results': 10}
)
print('Status:', response.status_code)
print('Results:', len(response.json().get('results', [])))
assert response.status_code == 200, 'Search failed!'
print('✓ Full search flow works')
"

pkill -f "uvicorn.*omics_oracle"
```

---

### STEP 6: Move Search Orchestrator (Stage 4)
**Goal:** Reorganize search module
**Risk:** MEDIUM
**Files:** lib/search/* → lib/2_search/

```bash
# Copy search module
cp -r omics_oracle_v2/lib/search/* omics_oracle_v2/lib/2_search/
touch omics_oracle_v2/lib/2_search/__init__.py
```

**Update imports in 2_search files:**
```python
# Update internal imports
# from omics_oracle_v2.lib.search.X → from omics_oracle_v2.lib.2_search.X
```

**Update API imports:**
```python
# In api/routes/agents.py
# OLD: from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator
# NEW: from omics_oracle_v2.lib.2_search.orchestrator import SearchOrchestrator
```

**Validation:** (Same as Step 4)

**If passes:**
```bash
git add omics_oracle_v2/lib/2_search/
git add omics_oracle_v2/api/
git commit -m "Step 6: Move search orchestrator to 2_search/"
git rm -r omics_oracle_v2/lib/search/
git commit -m "Step 6b: Remove old search/ directory"
```

---

### STEP 7: Move GEO Search Engine (Stage 5a - CRITICAL)
**Goal:** Recognize GEO as PRIMARY search engine
**Risk:** HIGH - GEO is core functionality
**Files:** lib/geo/* → lib/3_search_engines/geo/

```bash
# Copy GEO module
cp -r omics_oracle_v2/lib/geo/* omics_oracle_v2/lib/3_search_engines/geo/
touch omics_oracle_v2/lib/3_search_engines/__init__.py
touch omics_oracle_v2/lib/3_search_engines/geo/__init__.py
```

**Update imports in GEO files:**
```python
# Update internal imports
# from omics_oracle_v2.lib.geo.X → from omics_oracle_v2.lib.3_search_engines.geo.X
```

**Update orchestrator imports:**
```python
# In lib/2_search/orchestrator.py
# OLD: from omics_oracle_v2.lib.geo.client import GEOClient
# NEW: from omics_oracle_v2.lib.3_search_engines.geo.client import GEOClient
```

**Validation:**
```bash
# Test GEO search specifically
python3 -c "
from omics_oracle_v2.lib.3_search_engines.geo.client import GEOClient
client = GEOClient()
results = client.search('GSE12345', max_results=5)
print(f'✓ GEO search works: {len(results)} results')
"

# Full integration test
./start_omics_oracle.sh &
sleep 5

python3 -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/search',
    json={'query': 'GSE12345', 'search_geo': True, 'max_results': 5}
)
assert response.status_code == 200, 'GEO search failed!'
print('✓ GEO integration works')
"

pkill -f "uvicorn.*omics_oracle"
```

**If passes:**
```bash
git add omics_oracle_v2/lib/3_search_engines/
git add omics_oracle_v2/lib/2_search/
git commit -m "Step 7: Move GEO to 3_search_engines/geo/ (recognize as PRIMARY)"
git rm -r omics_oracle_v2/lib/geo/
git commit -m "Step 7b: Remove old geo/ directory"
```

---

### STEP 8: Move Citation Search Engines (Stage 5b)
**Goal:** Consolidate all search engines
**Risk:** MEDIUM
**Files:** lib/publications/clients/pubmed.py, lib/citations/clients/* → lib/3_search_engines/citations/

```bash
# Copy citation clients
cp omics_oracle_v2/lib/publications/clients/pubmed.py omics_oracle_v2/lib/3_search_engines/citations/
cp omics_oracle_v2/lib/citations/clients/*.py omics_oracle_v2/lib/3_search_engines/citations/
cp omics_oracle_v2/lib/publications/models.py omics_oracle_v2/lib/3_search_engines/citations/
cp omics_oracle_v2/lib/publications/config.py omics_oracle_v2/lib/3_search_engines/citations/
touch omics_oracle_v2/lib/3_search_engines/citations/__init__.py
```

**Update imports**

**Validation:**
```bash
# Test each citation engine
python3 -c "
from omics_oracle_v2.lib.3_search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.3_search_engines.citations.openalex import OpenAlexClient
print('✓ Citation engines import successfully')
"

# Integration test
./start_omics_oracle.sh &
sleep 5

python3 -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/search',
    json={'query': 'BRCA1', 'search_pubmed': True, 'max_results': 5}
)
assert response.status_code == 200, 'Citation search failed!'
print('✓ Citation search integration works')
"

pkill -f "uvicorn.*omics_oracle"
```

**If passes:** Commit and remove old directories

---

### STEP 9: Move Full-text Enrichment (Stages 6-8)
**Goal:** Consolidate full-text pipeline
**Risk:** HIGH - complex pipeline with many sources
**Files:** lib/fulltext/* + lib/storage/pdf/* → lib/4_enrichment/fulltext/

```bash
# Copy fulltext module
cp -r omics_oracle_v2/lib/fulltext/* omics_oracle_v2/lib/4_enrichment/fulltext/
cp -r omics_oracle_v2/lib/storage/pdf/* omics_oracle_v2/lib/4_enrichment/fulltext/

# Organize sources into categories
# TODO: Split oa_sources.py into specific categories
```

**Validation:**
```bash
# Test URL discovery
python3 -c "
from omics_oracle_v2.lib.4_enrichment.fulltext.manager import FulltextManager
manager = FulltextManager()
print('✓ Fulltext manager imports successfully')
"

# Test PDF download
./start_omics_oracle.sh &
sleep 5

# Test full pipeline: search → URL discovery → download
python3 -c "
import requests
# TODO: Test full-text download endpoint
"

pkill -f "uvicorn.*omics_oracle"
```

---

### STEP 10: Move AI Analysis (Stage 9)
**Goal:** Move AI module to analysis
**Risk:** LOW - AI is final stage
**Files:** lib/ai/* → lib/5_analysis/ai/

```bash
# Copy AI module
cp -r omics_oracle_v2/lib/ai/* omics_oracle_v2/lib/5_analysis/ai/
touch omics_oracle_v2/lib/5_analysis/__init__.py
```

**Validation:**
```bash
# Test AI client
python3 -c "
from omics_oracle_v2.lib.5_analysis.ai.client import AIClient
print('✓ AI client imports successfully')
"

# Integration test (if AI endpoint available)
```

---

### STEP 11: Move Infrastructure (Cache)
**Goal:** Separate cross-cutting concerns
**Risk:** LOW
**Files:** lib/cache/* → lib/infrastructure/cache/

```bash
# Copy cache module
cp -r omics_oracle_v2/lib/cache/* omics_oracle_v2/lib/infrastructure/cache/
```

**Validation:** Update all cache imports and test

---

### STEP 12: Final Cleanup
**Goal:** Remove all old directories, verify everything works
**Risk:** LOW (all already validated)

```bash
# List remaining old directories
ls -la omics_oracle_v2/lib/

# Remove any remaining old dirs
git rm -r omics_oracle_v2/lib/publications/
git rm -r omics_oracle_v2/lib/citations/
git rm -r omics_oracle_v2/lib/fulltext/
git rm -r omics_oracle_v2/lib/storage/
git rm -r omics_oracle_v2/lib/ai/
git rm -r omics_oracle_v2/lib/cache/

git commit -m "Step 12: Remove all old directory structure"
```

**Final Validation:**
```bash
# Full end-to-end test
./start_omics_oracle.sh &
sleep 10

# Test complete workflow
python3 scripts/test_complete_flow.py

# Manual test through UI
# 1. Open http://localhost:8000
# 2. Search for "GSE12345 BRCA1"
# 3. Verify results appear
# 4. Click "Get Full Text"
# 5. Verify PDFs download
# 6. Click "AI Analysis"
# 7. Verify analysis appears

pkill -f "uvicorn.*omics_oracle"
```

---

## Validation Checklist

After EACH step, verify:

- [ ] **Imports work** - `python3 -c "from X import Y"`
- [ ] **No syntax errors** - `python3 -m py_compile file.py`
- [ ] **Server starts** - `./start_omics_oracle.sh`
- [ ] **Health check** - `curl http://localhost:8000/health`
- [ ] **Search works** - Test API endpoint
- [ ] **No errors in logs** - Check `logs/omics_oracle.log`

**If ANY validation fails:** STOP, revert, debug before proceeding.

---

## Rollback Strategy

Each step is committed separately. If something breaks:

```bash
# See recent commits
git log --oneline -10

# Rollback last commit
git reset --hard HEAD~1

# Or rollback to specific commit
git reset --hard <commit-hash>

# Verify rollback worked
./start_omics_oracle.sh
```

---

## Estimated Timeline

| Step | Description | Time | Risk |
|------|-------------|------|------|
| 1 | Create directories | 2 min | None |
| 2 | Move query processing | 10 min | Low |
| 3 | Update orchestrator | 5 min | Med |
| 4 | Update API routes | 10 min | High |
| 5 | Remove old query/nlp | 2 min | Low |
| 6 | Move search orchestrator | 10 min | Med |
| 7 | Move GEO (CRITICAL) | 15 min | High |
| 8 | Move citations | 15 min | Med |
| 9 | Move fulltext | 20 min | High |
| 10 | Move AI | 10 min | Low |
| 11 | Move cache | 10 min | Low |
| 12 | Final cleanup | 5 min | Low |

**Total:** ~2 hours (with thorough testing)

---

## Success Criteria

✅ All imports work
✅ Server starts without errors
✅ Search flow works end-to-end
✅ GEO search returns results
✅ Citation search returns results
✅ PDF download works
✅ AI analysis works
✅ All tests pass
✅ Directory structure matches flow

---

## Ready to Start?

Shall we begin with **Step 1: Create Directory Structure**?
