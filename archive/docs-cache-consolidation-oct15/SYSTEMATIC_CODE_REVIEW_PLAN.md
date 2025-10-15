# Systematic Code Review Plan
**Date**: October 15, 2025  
**Scope**: Complete GEO query processing pipeline  
**Objective**: Audit every file for bugs, redundancy, and optimization opportunities

---

## Review Strategy

### Phase 1: Cache Consolidation (Priority 1) ⚡
**Duration**: 2-3 days  
**Why First**: Root cause of GSE189158 bug and 50+ hours of debugging  
**Deliverable**: Single source of truth for all cached data

See: `CACHE_ARCHITECTURE_AUDIT_OCT15.md`

---

### Phase 2: GEO Query Pipeline Review (Priority 2) 📊
**Duration**: 3-4 days  
**Files**: All files involved in GEO search → display  
**Objective**: End-to-end correctness and performance

---

## GEO Query Pipeline Architecture

```
USER REQUEST
    ↓
[API Layer] dashboard_v2.html → /api/agents/search
    ↓
[Route Layer] agents.py → search_datasets()
    ↓
[Orchestration Layer] orchestrator.py → execute_search()
    ↓                                        ↓
[Cache Layer]                        [GEO Client Layer]
RedisCache.get()                    client.py → search()
    ↓ (miss)                                ↓
    ↓                                [GEOparse Layer]
    ↓                                get_GEO(), NCBI API
    ↓                                        ↓
    └──────────← metadata ←─────────────────┘
             ↓
    [Transform Layer]
    GEOSeriesMetadata
             ↓
    [Response Layer]
    SearchResult → JSON
             ↓
    [Display Layer]
    dataset_card.html
```

---

## File-by-File Review Checklist

### 1. API Entry Point
**File**: `omics_oracle_v2/api/routes/agents.py`

**Functions to Review**:
- `search_datasets()` (lines 100-200)
  - [ ] Input validation (search_terms, max_results)
  - [ ] Cache key generation
  - [ ] Error handling
  - [ ] Response transformation

**Current Issues**:
```python
# LINE 143: Cache hit log
search_logs.append("[FAST] Cache hit - results returned from cache")
```
❌ **ISSUE**: Logs append to list but never shown to user  
✅ **FIX**: Return logs in response or remove

**Questions**:
1. Should we validate `search_terms` is not empty?
2. Should we limit `max_results` (currently unbounded)?
3. Should we sanitize search terms (SQL injection risk)?

**Metrics to Add**:
- Search latency (orchestrator time)
- Cache hit rate per request
- Number of datasets returned

---

### 2. Search Orchestrator
**File**: `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Functions to Review**:
- `execute_search()` (lines 200-500)
  - [ ] Query optimization
  - [ ] Cache check logic
  - [ ] Batch fetching
  - [ ] Error recovery

**Current Issues**:
```python
# LINE 425: Reconstruct from cache
# Reconstruct GEOSeriesMetadata from cached dict
datasets.append(GEOSeriesMetadata(**cached))
```
❌ **ISSUE**: Assumes cached dict has exact same schema  
✅ **FIX**: Validate keys or use .get() with defaults

```python
# LINE 436-448: Debug logs that never appear
logger.warning(f"[DEBUG] Missing IDs: {missing_ids}")
logger.warning(f"[DEBUG] Calling get_metadata for {geo_id}")
```
❌ **ISSUE**: These logs never appeared during GSE189158 debugging  
🔍 **INVESTIGATE**: Why is this code path never reached?

**Questions**:
1. When does `missing_ids` populate? (Never in our tests!)
2. Should we force cache invalidation on errors?
3. Should we retry failed fetches?

**Optimization Opportunities**:
```python
# Current: Sequential fetch
for geo_id in missing_ids:
    metadata = await self.geo_client.get_metadata(geo_id)

# Better: Parallel fetch (10x faster for large batches)
tasks = [self.geo_client.get_metadata(geo_id) for geo_id in missing_ids]
metadata_list = await asyncio.gather(*tasks, return_exceptions=True)
```

---

### 3. GEO Client (Metadata Fetcher)
**File**: `omics_oracle_v2/lib/search_engines/geo/client.py`

**Functions to Review**:
- `search()` (lines 100-200)
  - [ ] NCBI E-Search API call
  - [ ] Result parsing
  - [ ] Error handling
  
- `get_metadata()` (lines 300-450)
  - [ ] GEOparse integration
  - [ ] Organism extraction ← **GSE189158 BUG**
  - [ ] Metadata transformation

**Current Issues**:
```python
# LINE 239: SimpleCache initialization
self.cache = SimpleCache(cache_dir=Path(self.settings.cache_dir), default_ttl=self.settings.cache_ttl)
```
❌ **ISSUE**: Using redundant SimpleCache  
✅ **FIX**: Replace with RedisCache (Phase 1 of consolidation)

```python
# LINE 402-420: Organism extraction
organism = ""
gpls = getattr(gse, "gpls", {})
if gpls:
    first_platform = list(gpls.values())[0]
    platform_meta = getattr(first_platform, "metadata", {})
    organism = platform_meta.get("organism", [""])[0]
    logger.info(f"[ORGANISM FIX] Extracted organism for {geo_id}: {repr(organism)}")
```
❓ **MYSTERY**: Code is correct but GSE189158 still returns empty  
🔍 **ROOT CAUSE HYPOTHESIS**: 
- `get_metadata()` is NEVER called during search!
- Organism comes from E-Search API result, not GEOparse
- E-Search might have stale/incomplete data for GSE189158

**Investigation Steps**:
```bash
# Test E-Search directly
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GSE189158&retmode=json"

# Check if organism is in E-Search result
# If missing → that's the root cause!
```

**Questions**:
1. Does `search()` method populate organism field?
2. Should we ALWAYS call `get_metadata()` to get full data?
3. Or should we populate missing fields post-search?

---

### 4. GEO Models
**File**: `omics_oracle_v2/lib/search_engines/geo/models.py`

**Classes to Review**:
- `GEOSeriesMetadata`
  - [ ] Field definitions
  - [ ] Default values
  - [ ] Validation

**Current Issues**:
```python
@dataclass
class GEOSeriesMetadata:
    geo_id: str
    title: str
    summary: str
    organism: str  # ← DEFAULT VALUE?
    ...
```
❓ **QUESTION**: What's the default for `organism` if not provided?  
✅ **RECOMMENDATION**: Add default empty string

```python
@dataclass
class GEOSeriesMetadata:
    organism: str = ""  # ← Explicit default
```

---

### 5. Search Settings
**File**: `omics_oracle_v2/lib/search_engines/geo/settings.py`

**Settings to Review**:
- Cache TTL
- Rate limits
- API endpoints
- Default values

**Current Issues**:
```python
cache_ttl: int = 3600  # 1 hour
```
❌ **ISSUE**: Too short for stable GEO metadata  
✅ **FIX**: Increase to 2592000 (30 days) to match RedisCache

---

### 6. Response Transformation
**File**: `omics_oracle_v2/api/routes/agents.py`

**Functions to Review**:
- Dataset → JSON conversion
  - [ ] Field mapping
  - [ ] Null handling
  - [ ] Citation count calculation

**Current Issues**:
```python
# LINE 1072-1100: Citation count calculation
original_count = len(metadata["papers"]["original"]["papers"])
citing_count = len(metadata["papers"]["citing"]["papers"])
dataset.citation_count = original_count + citing_count
```
✅ **VERIFIED**: Logic is correct  
⚠️ **UNTESTED**: User hasn't tested "Download Papers" yet

---

### 7. Frontend Display
**File**: `omics_oracle_v2/api/static/templates/dataset_card.html`

**Elements to Review**:
- Organism display
- Citation count
- Completion rate
- Error states

**Current Issues**:
```html
<div class="organism">
    🧬 {{ dataset.organism || 'Unknown organism' }}
</div>
```
✅ **LOGIC CORRECT**: Shows "Unknown organism" if empty  
❌ **DATA ISSUE**: Backend returns empty string for GSE189158

---

## Critical Questions to Answer

### Q1: Where does organism data come from during search?

**Hypothesis 1**: E-Search API result (most likely)
```python
# In client.py search() method
# Does NCBI E-Search return organism?
```

**Hypothesis 2**: Cached from previous `get_metadata()` call
```python
# Maybe organism was cached when user viewed details?
```

**Hypothesis 3**: Database lookup (geo_datasets table)
```python
# Maybe orchestrator checks SQLite before API?
```

**Action**: Add logging to EVERY place organism is set:
```python
# In client.py search()
logger.warning(f"[ORGANISM TRACE] search() set organism={organism} for {geo_id}")

# In orchestrator.py execute_search()
logger.warning(f"[ORGANISM TRACE] orchestrator got organism={dataset.organism} for {dataset.geo_id}")

# In agents.py search_datasets()
logger.warning(f"[ORGANISM TRACE] API returning organism={dataset.organism} for {dataset.geo_id}")
```

---

### Q2: Why does `get_metadata()` never log during search?

**Evidence**:
- Added `logger.warning("[DEBUG] Calling get_metadata...")` on line 442
- Searched GSE189158 multiple times
- **ZERO logs appeared**

**Possible Explanations**:
1. ❌ Code not deployed → **DISPROVEN** (grep verified it's there)
2. ❌ Wrong log level → **DISPROVEN** (used warning level)
3. ✅ **Code path never reached** → Most likely!

**Why code path never reached**:
```python
# LINE 436: Check if missing_ids has items
if missing_ids:
    # This block never executes!
```

**Root cause**: `missing_ids` is ALWAYS empty because:
1. Search happens
2. Results cached in Redis
3. Next search is cache hit
4. `missing_ids = []` (everything cached)
5. `get_metadata()` never called!

**Action**: Force cache miss and verify:
```bash
redis-cli FLUSHALL
sqlite3 data/omics_oracle.db "DELETE FROM geo_datasets"
curl -X POST .../search -d '{"search_terms": ["GSE189158"]}'

# NOW check if get_metadata() logs appear
tail -f logs/omics_api.log | grep "ORGANISM"
```

---

### Q3: Should search() populate organism or only get_metadata()?

**Current Architecture**:
- `search()` → Calls NCBI E-Search → Gets minimal metadata (ID, title)
- `get_metadata()` → Downloads SOFT file → Gets full metadata (organism, samples)

**Problem**: We rely on E-Search for organism, but it's incomplete!

**Solution Options**:

**Option A**: ALWAYS call `get_metadata()` after search
```python
# In orchestrator.py execute_search()
# After getting search results
for geo_id in search_results:
    full_metadata = await self.geo_client.get_metadata(geo_id)
    datasets.append(full_metadata)
```
✅ **Pro**: Complete, accurate data  
❌ **Con**: Slow (downloads SOFT files for every result)

**Option B**: Lazy load organism on-demand
```python
# In dataset_card.html
<div class="organism">
    🧬 {{ dataset.organism || '...' }}
    <button onclick="fetchOrganism('{{ dataset.geo_id }}')">Load</button>
</div>
```
✅ **Pro**: Fast initial search  
❌ **Con**: Extra click, poor UX

**Option C**: Background population ← **RECOMMENDED**
```python
# In orchestrator.py execute_search()
# Return search results immediately
datasets = search_results

# Start background task to populate missing fields
asyncio.create_task(self._populate_missing_metadata(datasets))

return SearchResult(datasets=datasets, total_found=len(datasets))
```
✅ **Pro**: Fast initial response, complete data after ~1 second  
✅ **Pro**: Progressive loading (organism appears when ready)

---

## Action Plan

### Step 1: Trace Organism Data Flow (1 hour)
```bash
# Add comprehensive logging
git checkout -b organism-trace-oct15

# Edit files to add [ORGANISM TRACE] logs at every step
# - client.py search()
# - client.py get_metadata()
# - orchestrator.py execute_search()
# - agents.py search_datasets()

# Clear all caches
python scripts/utilities/clear_all_caches.py

# Test with GSE189158
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"]}' | jq '.datasets[0].organism'

# Analyze logs
grep "ORGANISM TRACE" logs/omics_api.log
```

**Expected Output**:
```
[ORGANISM TRACE] search() set organism='' for GSE189158  ← ROOT CAUSE!
[ORGANISM TRACE] orchestrator got organism='' for GSE189158
[ORGANISM TRACE] API returning organism='' for GSE189158
```

---

### Step 2: Test E-Search API Directly (30 min)
```bash
# Call NCBI E-Search manually
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GSE189158&retmode=json" | \
  jq '.'

# Check if organism is in result
# Expected: Organism field missing or empty

# Compare with E-Summary (more complete)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id=200189158&retmode=json" | \
  jq '.result."200189158"'

# Check for organism field
```

---

### Step 3: Implement Option C - Background Population (2 hours)
```python
# File: omics_oracle_v2/lib/search_orchestration/orchestrator.py

async def execute_search(self, query: str, max_results: int = 100):
    """Execute search with progressive metadata loading."""
    
    # Step 1: Fast search (E-Search only)
    search_results = await self.geo_client.search(query, max_results)
    
    # Step 2: Check cache for full metadata
    cached = await self._check_cache_batch(search_results)
    
    # Step 3: Return immediately with partial data
    datasets = cached + search_results
    
    # Step 4: Start background task for missing data
    missing = [d for d in datasets if not d.organism]
    if missing:
        asyncio.create_task(self._populate_missing_metadata(missing))
    
    return SearchResult(datasets=datasets, total_found=len(datasets))

async def _populate_missing_metadata(self, datasets: List[GEOSeriesMetadata]):
    """Background task to populate missing organism field."""
    for dataset in datasets:
        try:
            # Download SOFT file and extract organism
            full_metadata = await self.geo_client.get_metadata(dataset.geo_id)
            
            # Update dataset in-place
            dataset.organism = full_metadata.organism
            
            # Update cache
            await self.cache.set_geo_metadata(dataset.geo_id, full_metadata)
            
            logger.info(f"[BACKGROUND] Populated organism for {dataset.geo_id}: {dataset.organism}")
            
        except Exception as e:
            logger.warning(f"[BACKGROUND] Failed to populate {dataset.geo_id}: {e}")
```

**Testing**:
```bash
# Search GSE189158
curl -X POST .../search -d '{"search_terms": ["GSE189158"]}'

# Initial response: organism = ""
# After 1-2 seconds: organism = "Homo sapiens" (via websocket update?)
```

---

### Step 4: Add Websocket Push for Progressive Updates (3 hours)
```python
# File: omics_oracle_v2/api/routes/websocket.py (NEW)

from fastapi import WebSocket

@router.websocket("/ws/metadata-updates")
async def metadata_updates(websocket: WebSocket):
    """
    Websocket endpoint for progressive metadata updates.
    
    Client subscribes to geo_ids, server pushes updates when available.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive geo_ids to subscribe to
            data = await websocket.receive_json()
            geo_ids = data.get("subscribe", [])
            
            # Start background population
            for geo_id in geo_ids:
                asyncio.create_task(
                    _fetch_and_push(websocket, geo_id)
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected from metadata updates")

async def _fetch_and_push(websocket: WebSocket, geo_id: str):
    """Fetch full metadata and push update to client."""
    try:
        metadata = await geo_client.get_metadata(geo_id)
        
        # Push update to client
        await websocket.send_json({
            "type": "metadata_update",
            "geo_id": geo_id,
            "organism": metadata.organism,
            "samples_count": len(metadata.samples) if metadata.samples else 0
        })
    except Exception as e:
        logger.warning(f"Failed to fetch {geo_id}: {e}")
```

**Frontend Integration**:
```javascript
// File: dashboard_v2.html

// Connect to websocket
const ws = new WebSocket('ws://localhost:8000/ws/metadata-updates');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    if (update.type === 'metadata_update') {
        // Find dataset card and update organism
        const card = document.querySelector(`[data-geo-id="${update.geo_id}"]`);
        const organismEl = card.querySelector('.organism');
        
        // Animate update
        organismEl.classList.add('updating');
        organismEl.textContent = `🧬 ${update.organism}`;
        setTimeout(() => organismEl.classList.remove('updating'), 500);
    }
};

// After search, subscribe to updates
function searchDatasets() {
    // ... existing search logic ...
    
    // Subscribe to metadata updates
    const geoIds = results.datasets.map(d => d.geo_id);
    ws.send(JSON.stringify({subscribe: geoIds}));
}
```

---

### Step 5: Complete Code Review Checklist (4 hours)

**For Each File**:
- [ ] Read entire file (understand flow)
- [ ] Check error handling (try/except blocks)
- [ ] Verify logging (appropriate level, useful messages)
- [ ] Check type hints (all parameters typed?)
- [ ] Review SQL queries (injection risk?)
- [ ] Check async/await (no blocking calls?)
- [ ] Look for TODOs/FIXMEs
- [ ] Check for dead code (unreachable branches)
- [ ] Verify caching strategy (TTL appropriate?)
- [ ] Check resource cleanup (connections closed?)

**Example Review**:
```python
# File: client.py
# Function: get_metadata()

# ✅ GOOD: Error handling
try:
    gse = GEOparse.get_GEO(geo=geo_id)
except Exception as e:
    logger.error(f"Failed to fetch {geo_id}: {e}")
    return None

# ❌ BAD: No type hints
def get_metadata(geo_id):  # Should be: def get_metadata(geo_id: str) -> Optional[GEOSeriesMetadata]:
    ...

# ❌ BAD: Blocking call in async function
async def get_metadata(geo_id: str):
    gse = GEOparse.get_GEO(geo=geo_id)  # BLOCKS! Should use executor
    
# ✅ FIX:
async def get_metadata(geo_id: str):
    loop = asyncio.get_event_loop()
    gse = await loop.run_in_executor(None, GEOparse.get_GEO, geo_id)
```

---

## Deliverables

### 1. Cache Consolidation (See separate doc)
- [ ] Remove SimpleCache
- [ ] GEOparse wrapper
- [ ] Database integration
- [ ] Redis hot-tier for parsed content

### 2. Organism Fix
- [ ] Trace data flow (identify source)
- [ ] Test E-Search API directly
- [ ] Implement background population OR
- [ ] Switch to E-Summary API (has organism)

### 3. Code Quality
- [ ] Add type hints to all functions
- [ ] Fix blocking calls in async functions
- [ ] Remove dead code
- [ ] Add comprehensive error handling
- [ ] Improve logging (structured, contextualized)

### 4. Testing
- [ ] Unit tests for each layer
- [ ] Integration test for full pipeline
- [ ] Performance benchmarks
- [ ] Edge case testing (empty results, API errors, etc.)

### 5. Documentation
- [ ] Architecture diagram
- [ ] API documentation
- [ ] Developer guide
- [ ] Troubleshooting guide

---

## Timeline

**Week 1**:
- Day 1-2: Cache consolidation (Phase 1)
- Day 3: Organism trace + fix
- Day 4-5: Code review (client.py, orchestrator.py)

**Week 2**:
- Day 1-2: Background population + websocket
- Day 3: Code review (agents.py, models.py)
- Day 4: Testing + benchmarks
- Day 5: Documentation + handoff

**Total**: 10 days (~80 hours)

---

## Success Criteria

- [ ] GSE189158 shows "Homo sapiens" ✅
- [ ] All 6 cache layers consolidated to 2 tiers
- [ ] GEO search <100ms on cache hit
- [ ] 100% code coverage for critical paths
- [ ] Zero blocking calls in async functions
- [ ] All functions have type hints
- [ ] Architecture document complete

---

**End of Review Plan**
