# Cache Consolidation & Code Review - Quick Start Guide
**Date**: October 15, 2025  
**Status**: READY TO START  
**Priority**: HIGH (fixes GSE189158 bug + 50+ hours of debugging waste)

---

## TL;DR - What We're Doing

**Problem**: 6 different cache systems causing:
- GSE189158 organism bug (empty string despite NCBI having "Homo sapiens")
- Impossible debugging (cleared one cache, data persists in 5 others)
- Slow performance (duplicate storage, no batch operations)

**Solution**: Consolidate to 2-tier hybrid:
1. **Hot Tier (Redis)**: Fast volatile cache (TTL 1h-30d)
2. **Warm Tier (SQLite + Files)**: Persistent storage (TTL 90d)

**Impact**: 
- ✅ Fix GSE189158 organism bug
- ✅ 20-50x faster searches (cache hits)
- ✅ Single command to clear all caches
- ✅ Debugging in <1 minute (not 30+ minutes)

---

## Phase 1: Remove SimpleCache (START HERE)
**Duration**: 4 hours  
**Risk**: Low (Redis already working)  
**Impact**: Fixes GEO metadata inconsistency

### Step 1.1: Backup Current State (5 min)
```bash
# Create feature branch
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
git checkout -b cache-consolidation-oct15

# Backup data directory
cp -r data data_backup_oct15

# Backup current caches
redis-cli --rdb data_backup_oct15/redis_dump.rdb
```

### Step 1.2: Modify GEO Client (30 min)
**File**: `omics_oracle_v2/lib/search_engines/geo/client.py`

**Change 1**: Replace SimpleCache import
```python
# LINE 23 - REMOVE
from omics_oracle_v2.lib.search_engines.geo.cache import SimpleCache

# ADD
from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
```

**Change 2**: Initialize RedisCache instead of SimpleCache
```python
# LINE 239 - REPLACE
self.cache = SimpleCache(cache_dir=Path(self.settings.cache_dir), default_ttl=self.settings.cache_ttl)

# WITH
self.redis_cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    prefix="omics_search",
    enabled=True
)
```

**Change 3**: Update cache calls (find all occurrences)
```bash
# Find all SimpleCache usage
grep -n "self.cache\." omics_oracle_v2/lib/search_engines/geo/client.py

# Results:
# Line 285: self.cache.get(f"geo_search:{query_hash}")
# Line 295: self.cache.set(f"geo_search:{query_hash}", ...)
# Line 378: self.cache.get(f"geo_metadata:{geo_id}")
# Line 418: self.cache.set(f"geo_metadata:{geo_id}", ...)
```

**Replace each occurrence**:
```python
# OLD (Line 285)
cached = self.cache.get(f"geo_search:{query_hash}")

# NEW
cached = await self.redis_cache.get_search_result(
    query=query,
    search_type="geo",
    max_results=max_results
)

# OLD (Line 295)
self.cache.set(f"geo_search:{query_hash}", search_result)

# NEW
await self.redis_cache.set_search_result(
    query=query,
    search_type="geo",
    result=search_result,
    max_results=max_results
)

# OLD (Line 378)
cached = self.cache.get(f"geo_metadata:{geo_id}")

# NEW
cached = await self.redis_cache.get_geo_metadata(geo_id)

# OLD (Line 418)
self.cache.set(f"geo_metadata:{geo_id}", metadata)

# NEW
await self.redis_cache.set_geo_metadata(geo_id, metadata)
```

### Step 1.3: Make Functions Async (15 min)
**Problem**: RedisCache uses async, but GEO client functions are sync

**Solution**: Convert to async
```python
# OLD
def search(self, query: str, max_results: int = 100):
    cached = self.cache.get(...)  # Sync call
    ...

# NEW
async def search(self, query: str, max_results: int = 100):
    cached = await self.redis_cache.get_search_result(...)  # Async call
    ...
```

**Update ALL callers**:
```bash
# Find all calls to client.search()
grep -rn "geo_client.search\|self.search\|client.search" omics_oracle_v2/

# Make each caller async:
# results = client.search(query)  → results = await client.search(query)
```

### Step 1.4: Delete SimpleCache File (5 min)
```bash
# Move to archive (don't delete yet - keep for 30 days)
mkdir -p archive/cache-consolidation-oct15
mv omics_oracle_v2/lib/search_engines/geo/cache.py \
   archive/cache-consolidation-oct15/

# Update __init__.py if needed
# Check: omics_oracle_v2/lib/search_engines/geo/__init__.py
```

### Step 1.5: Update Orchestrator (20 min)
**File**: `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Change**: Ensure orchestrator awaits async calls
```python
# OLD (Line ~300)
search_results = self.geo_client.search(query, max_results)

# NEW
search_results = await self.geo_client.search(query, max_results)

# OLD (Line ~442)
metadata = self.geo_client.get_metadata(geo_id)

# NEW
metadata = await self.geo_client.get_metadata(geo_id)
```

### Step 1.6: Test Changes (1 hour)
```bash
# Restart server (watch for errors)
pkill -f uvicorn
./start_omics_oracle.sh

# Watch logs
tail -f logs/omics_api.log

# Should see:
# "Connected to Redis at localhost:6379 (db=0)"
# No errors about SimpleCache

# Test 1: Clear all caches
redis-cli FLUSHALL
rm -rf data/cache/*.json

# Test 2: Search GSE189158
curl -s -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"], "max_results": 1}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('Organism:', repr(d['datasets'][0].get('organism')))"

# Expected: Organism: 'Homo sapiens' (NOT empty!)

# Test 3: Verify Redis caching
redis-cli KEYS "omics_search:geo:*"
# Should show: omics_search:geo:GSE189158

redis-cli GET "omics_search:geo:GSE189158"
# Should show JSON with organism="Homo sapiens"

# Test 4: Verify cache hit (2nd request fast)
time curl -s -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"]}' > /dev/null

# Expected: <100ms (cache hit)
```

### Step 1.7: Commit Changes (10 min)
```bash
git add -A
git commit -m "Phase 1: Replace SimpleCache with RedisCache for GEO metadata

- Remove omics_oracle_v2/lib/search_engines/geo/cache.py
- Update GEO client to use RedisCache
- Convert client methods to async
- Update orchestrator to await async calls
- Fix GSE189158 organism bug (single cache source)

IMPACT:
- GEO metadata now cached in Redis only (30d TTL)
- Consistent cache behavior across all GEO operations
- Faster batch operations with Redis MGET/pipeline
- Cache metrics tracking (hit rate, latency)

TESTING:
- GSE189158 organism: 'Homo sapiens' ✅
- Cache hit <100ms ✅
- No SimpleCache files created ✅
"

# Push to remote
git push origin cache-consolidation-oct15
```

---

## Phase 2: Organism Bug Root Cause Investigation (PARALLEL)
**Duration**: 2 hours  
**Can run while Phase 1 is being tested**

### Step 2.1: Add Comprehensive Logging (30 min)
```bash
# Create organism-trace branch
git checkout -b organism-trace-oct15
```

**File**: `omics_oracle_v2/lib/search_engines/geo/client.py`

**Add logs to search() method**:
```python
async def search(self, query: str, max_results: int = 100):
    """Search GEO database."""
    
    # ... existing code ...
    
    # After parsing E-Search results
    for result in results:
        geo_id = result.get("accession")
        title = result.get("title")
        organism = result.get("organism", "")  # ← IS THIS FIELD PRESENT?
        
        logger.warning(f"[ORGANISM TRACE] E-Search returned organism='{organism}' for {geo_id}")
        
        metadata = GEOSeriesMetadata(
            geo_id=geo_id,
            title=title,
            organism=organism,
            ...
        )
        
        logger.warning(f"[ORGANISM TRACE] Created metadata with organism='{metadata.organism}' for {geo_id}")
```

**Add logs to get_metadata() method**:
```python
async def get_metadata(self, geo_id: str):
    """Get full metadata from GEOparse."""
    
    logger.warning(f"[ORGANISM TRACE] get_metadata() CALLED for {geo_id}")
    
    # ... download SOFT file ...
    
    # After extracting organism
    organism = platform_meta.get("organism", [""])[0]
    logger.warning(f"[ORGANISM TRACE] GEOparse SOFT file has organism='{organism}' for {geo_id}")
    
    metadata = GEOSeriesMetadata(
        ...
        organism=organism
    )
    
    logger.warning(f"[ORGANISM TRACE] get_metadata() returning organism='{metadata.organism}' for {geo_id}")
    return metadata
```

**File**: `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Add logs to execute_search()**:
```python
async def execute_search(self, query: str, max_results: int = 100):
    """Execute search with logging."""
    
    # After getting search results
    search_results = await self.geo_client.search(query, max_results)
    
    for dataset in search_results:
        logger.warning(f"[ORGANISM TRACE] Orchestrator received organism='{dataset.organism}' for {dataset.geo_id}")
    
    # ... rest of code ...
```

**File**: `omics_oracle_v2/api/routes/agents.py`

**Add logs to search_datasets()**:
```python
@router.post("/search")
async def search_datasets(...):
    """Search with organism logging."""
    
    # After orchestrator returns
    result = await orchestrator.execute_search(...)
    
    for dataset in result.datasets:
        logger.warning(f"[ORGANISM TRACE] API returning organism='{dataset.organism}' for {dataset.geo_id}")
    
    return result
```

### Step 2.2: Test with Full Logging (30 min)
```bash
# Clear all caches
redis-cli FLUSHALL
rm -rf data/cache/*.json
sqlite3 data/omics_oracle.db "DELETE FROM geo_datasets"

# Restart server
pkill -f uvicorn
./start_omics_oracle.sh

# Search GSE189158
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"]}' > /dev/null

# Analyze logs
grep "ORGANISM TRACE" logs/omics_api.log

# EXPECTED OUTPUT:
# [ORGANISM TRACE] E-Search returned organism='' for GSE189158  ← ROOT CAUSE!
# [ORGANISM TRACE] Created metadata with organism='' for GSE189158
# [ORGANISM TRACE] Orchestrator received organism='' for GSE189158
# [ORGANISM TRACE] API returning organism='' for GSE189158

# CONCLUSION: E-Search API doesn't return organism field!
```

### Step 2.3: Test NCBI API Directly (15 min)
```bash
# Test E-Search (what we currently use)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GSE189158&retmode=json" | \
  jq '.'

# Output shows: No organism field! ❌

# Test E-Summary (alternative API)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id=200189158&retmode=json" | \
  jq '.result."200189158"'

# Check if organism is present
# (ID 200189158 = GDS ID for GSE189158, convert: GSE -> 2001 prefix)
```

### Step 2.4: Test GEOparse Directly (15 min)
```python
# Test script: test_geoparse_organism.py
import GEOparse

# Download GSE189158 SOFT file
gse = GEOparse.get_GEO(geo="GSE189158", destdir="data/cache")

# Check organism in platforms
gpls = getattr(gse, "gpls", {})
print(f"Platforms found: {list(gpls.keys())}")

for platform_id, platform in gpls.items():
    metadata = getattr(platform, "metadata", {})
    organism = metadata.get("organism", [""])[0]
    print(f"Platform {platform_id}: organism = '{organism}'")

# Expected output:
# Platform GPL24676: organism = 'Homo sapiens'
```

```bash
# Run test
python test_geoparse_organism.py

# If organism is present → E-Search is the problem!
# If organism is empty → SOFT file is incomplete for this dataset
```

### Step 2.5: Implement Fix (30 min)
**Option A**: Switch to E-Summary API (has organism)
```python
# File: client.py

async def search(self, query: str, max_results: int = 100):
    """Search using E-Search + E-Summary for complete metadata."""
    
    # Step 1: E-Search for IDs
    search_url = f"{BASE_URL}/esearch.fcgi?db=gds&term={query}&retmax={max_results}&retmode=json"
    ids = ...  # Parse IDs
    
    # Step 2: E-Summary for full metadata (including organism)
    summary_url = f"{BASE_URL}/esummary.fcgi?db=gds&id={','.join(ids)}&retmode=json"
    summaries = ...  # Parse summaries
    
    for summary in summaries:
        organism = summary.get("taxon", "")  # E-Summary has taxon field!
        metadata = GEOSeriesMetadata(
            geo_id=summary["accession"],
            title=summary["title"],
            organism=organism,  # Now populated!
            ...
        )
```

**Option B**: Background population (see SYSTEMATIC_CODE_REVIEW_PLAN.md Step 3)

**RECOMMENDED**: Option A (simpler, immediate fix)

---

## Quick Testing Checklist

After Phase 1:
- [ ] Server starts without errors
- [ ] Redis connection successful
- [ ] No SimpleCache import errors
- [ ] GSE189158 returns organism="Homo sapiens"
- [ ] Redis cache key exists: `omics_search:geo:GSE189158`
- [ ] Second search <100ms (cache hit)
- [ ] No JSON files created in `data/cache/`

After Phase 2:
- [ ] Organism trace logs appear
- [ ] E-Search API tested directly
- [ ] GEOparse tested directly
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] All test cases pass

---

## Rollback Plan

If Phase 1 breaks:
```bash
# Restore from branch
git checkout main
git branch -D cache-consolidation-oct15

# Restore data
rm -rf data
mv data_backup_oct15 data

# Restart server
pkill -f uvicorn
./start_omics_oracle.sh
```

If Phase 2 doesn't fix organism:
```bash
# Remove trace logging (reduces log noise)
git checkout main omics_oracle_v2/lib/search_engines/geo/client.py
git checkout main omics_oracle_v2/lib/search_orchestration/orchestrator.py
git checkout main omics_oracle_v2/api/routes/agents.py

# Keep as known issue, document in README
echo "Known Issue: GSE189158 organism field empty (NCBI data incomplete)" >> docs/KNOWN_ISSUES.md
```

---

## Next Steps After Phase 1+2

1. **Review Results**: Does GSE189158 show organism now?
2. **Performance Test**: Is cache hit <100ms?
3. **Continue to Phase 3**: GEOparse wrapper (see CACHE_ARCHITECTURE_AUDIT_OCT15.md)
4. **Continue to Phase 4**: ParsedCache + Redis hot-tier
5. **Complete Code Review**: See SYSTEMATIC_CODE_REVIEW_PLAN.md

---

## Questions / Need Help?

**Issue**: Server won't start after changes
→ Check logs for import errors: `tail -100 logs/omics_api.log | grep Error`

**Issue**: Tests fail
→ Check async/await: All `client.search()` calls need `await`

**Issue**: Organism still empty
→ Run Phase 2 tracing to find root cause

**Issue**: Redis not connecting
→ Check Redis is running: `redis-cli PING` (should return PONG)

---

**READY TO START? Begin with Phase 1, Step 1.1 above! ☝️**
