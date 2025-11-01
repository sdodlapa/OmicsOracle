# Cache Invalidation & Freshness Analysis

## Problem Statement

**Current Issue**: Our cache system stores "incomplete" data (GEO metadata without citations), which prevents future enrichment attempts because the cache hit indicates "data exists" even though it's incomplete.

```
Current Flow (BROKEN):
1. Search for GSE307750
2. Not in cache → Fetch GEO metadata → Auto-discover citations (FAILS silently)
3. Store incomplete data: {geo: {...}, papers: {original: [], citing: []}}
4. Second search for GSE307750
5. Cache HIT → Returns incomplete data → No re-enrichment attempted
```

## Industry Standard Solutions

### 1. **Cache Versioning with Completeness Levels** (Recommended ✅)

**Used by**: Redis, Elasticsearch, AWS DynamoDB

**Approach**: Store metadata about data completeness alongside cached data.

```python
{
    "geo_id": "GSE307750",
    "cache_metadata": {
        "version": "2.0",
        "created_at": "2025-10-16T10:00:00Z",
        "last_updated": "2025-10-16T10:00:00Z",
        "completeness_level": "metadata_only",  # or "with_citations", "fully_enriched"
        "enrichment_status": {
            "geo_metadata": {"status": "complete", "timestamp": "..."},
            "citations": {"status": "pending", "timestamp": null, "retry_count": 0},
            "pdfs": {"status": "not_started", "timestamp": null},
            "extractions": {"status": "not_started", "timestamp": null}
        },
        "ttl_seconds": 86400,  # 24 hours
        "requires_refresh": false
    },
    "data": {
        "geo": {...},
        "papers": {...}
    }
}
```

**Benefits**:
- Can detect incomplete data programmatically
- Allows progressive enrichment
- Supports retry logic for failed operations
- Clear audit trail

### 2. **Time-to-Live (TTL) with Lazy Refresh** 

**Used by**: Memcached, CDNs, HTTP caching

**Approach**: Data expires after a time period, but can be refreshed in background.

```python
{
    "geo_id": "GSE307750",
    "cached_at": "2025-10-16T10:00:00Z",
    "expires_at": "2025-10-17T10:00:00Z",  # 24h TTL
    "stale_while_revalidate": 3600,  # Serve stale for 1h while refreshing
    "data": {...}
}
```

**Benefits**:
- Automatic staleness detection
- Background refresh doesn't block requests
- Configurable freshness guarantees

### 3. **Event-Driven Cache Invalidation**

**Used by**: Kafka, RabbitMQ-based systems, Microservices

**Approach**: Emit events when data changes; consumers invalidate cache.

```python
# When citations discovered
event_bus.publish("citations.discovered", {
    "geo_id": "GSE307750",
    "citation_count": 42,
    "timestamp": "..."
})

# Cache listener
@event_bus.subscribe("citations.discovered")
def invalidate_cache(event):
    cache.delete(event.geo_id)
    cache.set(event.geo_id, fetch_fresh_data(event.geo_id))
```

**Benefits**:
- Reactive and efficient
- No polling needed
- Immediate consistency

### 4. **Write-Behind with Completion Tracking**

**Used by**: MongoDB, Cassandra, Write-heavy systems

**Approach**: Track operation completion status separately from data.

```python
# Separate tables
geo_datasets:
  - geo_id, title, summary, organism...

enrichment_jobs:
  - job_id, geo_id, job_type (citations/pdfs/extraction)
  - status (pending/running/complete/failed)
  - created_at, updated_at, retry_count
  - error_message

# Query logic
def get_geo_with_enrichment_status(geo_id):
    geo_data = db.get_geo(geo_id)
    jobs = db.get_enrichment_jobs(geo_id)
    
    # Re-trigger failed/pending jobs
    for job in jobs:
        if job.status in ['failed', 'pending'] and job.retry_count < 3:
            trigger_enrichment(job)
```

**Benefits**:
- Clear separation of data and processing state
- Built-in retry logic
- Visibility into pipeline progress

### 5. **Multi-Tier Cache with Freshness Tags**

**Used by**: Varnish, Cloudflare, Multi-CDN setups

**Approach**: Tag cache entries with freshness indicators.

```python
class CacheEntry:
    data: dict
    tags: Set[str]  # {"fresh", "stale", "incomplete", "enriching"}
    
# Tag-based invalidation
cache.invalidate_by_tag("incomplete")
cache.promote_tag("incomplete", "fresh")
```

## Recommended Solution for OmicsOracle

**Hybrid Approach: Completeness Levels + TTL + Job Tracking**

### Architecture

```python
# 1. Add completeness tracking to cache entries
class GEOCacheEntry:
    geo_id: str
    data: Dict[str, Any]
    metadata: CacheMetadata
    
class CacheMetadata:
    version: str = "2.0"
    created_at: datetime
    last_updated: datetime
    completeness_level: CompletenessLevel
    enrichment_attempts: Dict[str, EnrichmentAttempt]
    ttl_seconds: int
    
class CompletenessLevel(Enum):
    METADATA_ONLY = "metadata_only"           # GEO metadata fetched
    WITH_CITATIONS = "with_citations"         # Citations discovered
    WITH_PDFS = "with_pdfs"                   # PDFs downloaded
    FULLY_ENRICHED = "fully_enriched"         # Extractions complete
    
class EnrichmentAttempt:
    status: str  # "not_started", "pending", "complete", "failed"
    last_attempt: Optional[datetime]
    retry_count: int
    max_retries: int = 3
    error_message: Optional[str]
    backoff_until: Optional[datetime]  # Exponential backoff

# 2. Smart cache retrieval logic
async def get(self, geo_id: str, required_level: CompletenessLevel = CompletenessLevel.WITH_CITATIONS):
    """
    Get GEO data with minimum required completeness level.
    
    Args:
        geo_id: GEO accession ID
        required_level: Minimum completeness level required
        
    Returns:
        GEO data if it meets required completeness, or triggers enrichment
    """
    # Try cache first
    entry = await self._get_from_cache(geo_id)
    
    if entry is None:
        # Not in cache - full pipeline
        return await self._fetch_and_enrich(geo_id, required_level)
    
    # Check if data meets required completeness
    if entry.metadata.completeness_level.value >= required_level.value:
        # Check TTL
        if not self._is_stale(entry):
            self.stats["cache_hits"] += 1
            return entry.data
        else:
            # Stale - refresh in background, return existing
            asyncio.create_task(self._refresh_entry(geo_id, required_level))
            return entry.data
    
    # Data exists but incomplete - check if we can enrich
    if self._can_attempt_enrichment(entry, "citations"):
        # Trigger progressive enrichment
        return await self._progressive_enrich(entry, required_level)
    else:
        # Failed too many times or in backoff period
        logger.warning(f"Cannot enrich {geo_id} - in backoff or max retries reached")
        return entry.data  # Return what we have

# 3. Progressive enrichment
async def _progressive_enrich(self, entry: GEOCacheEntry, target_level: CompletenessLevel):
    """Enrich existing cache entry to reach target completeness level."""
    
    current_level = entry.metadata.completeness_level
    
    # Citations needed
    if current_level == CompletenessLevel.METADATA_ONLY and target_level.value >= CompletenessLevel.WITH_CITATIONS.value:
        try:
            await self._enrich_citations(entry)
            entry.metadata.completeness_level = CompletenessLevel.WITH_CITATIONS
            entry.metadata.enrichment_attempts["citations"].status = "complete"
        except Exception as e:
            self._record_enrichment_failure(entry, "citations", str(e))
            return entry.data
    
    # PDFs needed
    if current_level.value <= CompletenessLevel.WITH_CITATIONS.value and target_level.value >= CompletenessLevel.WITH_PDFS.value:
        try:
            await self._enrich_pdfs(entry)
            entry.metadata.completeness_level = CompletenessLevel.WITH_PDFS
            entry.metadata.enrichment_attempts["pdfs"].status = "complete"
        except Exception as e:
            self._record_enrichment_failure(entry, "pdfs", str(e))
            return entry.data
    
    # Update cache
    await self._update_cache(entry)
    return entry.data

# 4. Exponential backoff for failed enrichments
def _can_attempt_enrichment(self, entry: GEOCacheEntry, enrichment_type: str) -> bool:
    """Check if we can attempt enrichment based on retry policy."""
    
    attempt = entry.metadata.enrichment_attempts.get(enrichment_type)
    if not attempt:
        return True
    
    # Check max retries
    if attempt.retry_count >= attempt.max_retries:
        logger.warning(f"Max retries reached for {entry.geo_id} {enrichment_type}")
        return False
    
    # Check backoff period
    if attempt.backoff_until and datetime.now() < attempt.backoff_until:
        logger.debug(f"In backoff period for {entry.geo_id} {enrichment_type}")
        return False
    
    return True

def _record_enrichment_failure(self, entry: GEOCacheEntry, enrichment_type: str, error: str):
    """Record failed enrichment attempt with exponential backoff."""
    
    attempt = entry.metadata.enrichment_attempts.setdefault(
        enrichment_type, 
        EnrichmentAttempt(status="failed", retry_count=0)
    )
    
    attempt.retry_count += 1
    attempt.last_attempt = datetime.now()
    attempt.error_message = error
    attempt.status = "failed"
    
    # Exponential backoff: 1min, 5min, 30min, 2h, ...
    backoff_seconds = min(60 * (5 ** attempt.retry_count), 7200)
    attempt.backoff_until = datetime.now() + timedelta(seconds=backoff_seconds)
    
    logger.warning(
        f"Enrichment failed for {entry.geo_id} {enrichment_type} "
        f"(attempt {attempt.retry_count}/{attempt.max_retries}). "
        f"Next retry after {attempt.backoff_until}"
    )
```

### Database Schema Updates

```sql
-- Add completeness tracking to geo_datasets
ALTER TABLE geo_datasets ADD COLUMN completeness_level TEXT DEFAULT 'metadata_only';
ALTER TABLE geo_datasets ADD COLUMN cache_metadata TEXT;  -- JSON blob

-- Add enrichment jobs table
CREATE TABLE IF NOT EXISTS enrichment_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    geo_id TEXT NOT NULL,
    job_type TEXT NOT NULL,  -- 'citations', 'pdfs', 'extraction'
    status TEXT NOT NULL,     -- 'pending', 'running', 'complete', 'failed'
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    backoff_until TEXT,
    FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id),
    UNIQUE(geo_id, job_type)
);

CREATE INDEX idx_enrichment_jobs_status ON enrichment_jobs(status, backoff_until);
CREATE INDEX idx_enrichment_jobs_geo ON enrichment_jobs(geo_id);
```

## Migration Strategy

### Phase 1: Add Completeness Tracking (Immediate)
1. Add `completeness_level` and `cache_metadata` to cache entries
2. Update `get()` to check completeness before returning
3. Mark all existing entries as `metadata_only` if `citation_count == 0`

### Phase 2: Progressive Enrichment (Week 1)
1. Implement `_progressive_enrich()` 
2. Add retry logic with exponential backoff
3. Test with small dataset

### Phase 3: Job Tracking (Week 2)
1. Create `enrichment_jobs` table
2. Move enrichment attempts to job system
3. Add admin UI to view/retry failed jobs

### Phase 4: Monitoring & Observability (Week 3)
1. Add metrics: cache hit rate by completeness level
2. Track enrichment success rates
3. Alert on high failure rates

## Immediate Fix (Today)

```python
# Quick fix: Check citation count and re-enrich if needed
async def get(self, geo_id: str) -> Optional[Dict[str, Any]]:
    """Get GEO data from cache/database with smart re-enrichment."""
    
    # ... existing cache logic ...
    
    geo_data = self.unified_db.get_complete_geo_data(geo_id)
    
    if geo_data is None:
        # Not in DB - trigger full discovery
        logger.info(f"GEO not found in UnifiedDB: {geo_id} - triggering auto-discovery")
        geo_data = await self._auto_discover_and_populate(geo_id)
    else:
        # In DB - check if complete
        citation_count = len(geo_data.get("papers", {}).get("original", []))
        
        # Re-enrich if no citations AND not recently attempted
        if citation_count == 0:
            last_enrichment = geo_data.get("metadata", {}).get("last_enrichment_attempt")
            
            # Only retry if never tried or last attempt was >24h ago
            should_retry = (
                last_enrichment is None or 
                (datetime.now() - datetime.fromisoformat(last_enrichment)).total_seconds() > 86400
            )
            
            if should_retry:
                logger.info(f"Re-enriching incomplete data for {geo_id} (0 citations)")
                enriched_data = await self._auto_discover_and_populate(geo_id)
                if enriched_data:
                    geo_data = enriched_data
    
    if geo_data is None:
        logger.warning(f"Auto-discovery failed for {geo_id}")
        return None
    
    # Promote to hot tier
    await self._promote_to_hot_tier(geo_id, geo_data)
    return geo_data
```

## Comparison with Industry Standards

| System | Approach | Pros | Cons |
|--------|----------|------|------|
| **Redis** | TTL + manual invalidation | Simple, fast | No completeness tracking |
| **Elasticsearch** | Version numbers + refresh | Distributed, scalable | Complex setup |
| **GraphQL (DataLoader)** | Per-request batching | Avoids N+1 | No persistence |
| **AWS DynamoDB** | TTL + streams | Serverless, auto-scaling | Vendor lock-in |
| **Our Hybrid** | Completeness + TTL + Jobs | Smart re-enrichment | More complex |

## Recommended Action Plan

**Today (Immediate Fix)**:
- ✅ Fix missing `await` in auto-discovery (DONE)
- ✅ Add citation count check to trigger re-enrichment
- ✅ Add `last_enrichment_attempt` timestamp tracking

**This Week**:
- Implement completeness levels enum
- Add retry logic with exponential backoff
- Update database schema with enrichment metadata

**Next Week**:
- Create enrichment jobs table
- Add admin UI for job management
- Implement background job worker

**Long-term**:
- Add monitoring/metrics
- Implement cache warming for popular datasets
- Add A/B testing for different enrichment strategies

## Key Takeaway

**The root issue isn't the cache itself - it's the lack of completion/freshness metadata.**

Good caching systems don't just store "data exists" - they track:
1. **What level of data exists** (completeness)
2. **When it was fetched** (freshness/TTL)
3. **Why enrichment failed** (retry policy)
4. **When to retry** (backoff strategy)

Our current cache is too binary (exists/doesn't exist). We need a **spectrum of completeness** with smart re-enrichment logic.
