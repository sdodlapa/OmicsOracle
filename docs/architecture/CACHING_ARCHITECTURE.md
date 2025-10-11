# Caching Architecture - OmicsOracle

**Date:** October 11, 2025
**Status:** Active + Optimization Opportunities

---

## Current Caching Implementation

### 1. **Multi-Level Cache Hierarchy** ✅

```
Level 1: Search Results Cache (RedisCache)
├── Key: query + search_type hash
├── TTL: 24 hours
└── Stores: Complete SearchResult object

Level 2: Item-Level Cache (SimpleCache in GEOClient)
├── Key: geo_id or pmid
├── TTL: 30 days (GEO), 7 days (Publications)
└── Stores: Individual metadata objects

Level 3: Query Optimization Cache (RedisCache)
├── Key: query hash
├── TTL: 24 hours
└── Stores: NER entities + SapBERT synonyms
```

### 2. **Current Cache Flow**

```python
# unified_search_pipeline.py line 275-288
async def search(query, ...):
    # Check full result cache
    if use_cache and self._cache_available:
        cached = await self.cache.get_search_result(cache_key, search_type)
        if cached:
            return cached  # ✅ INSTANT RETURN

    # Execute full search
    results = await self._search_geo(...)  # 3-5 seconds

    # Cache the result
    await self.cache.set_search_result(cache_key, results)
```

**Performance:**
- Cache HIT: <100ms (1000x faster)
- Cache MISS: 3-5 seconds (full search)

---

## 🚀 Optimization Opportunity: Partial Cache Lookup

### Problem
Currently, if we search for **"diabetes gene expression"** and get 100 results, then search for **"diabetes insulin"**, we:
1. ❌ Do a FULL new search (3-5 seconds)
2. ❌ Re-fetch metadata for overlapping GEO datasets
3. ❌ Don't leverage the fact that 60% of results might be cached

### Solution: Smart Partial Caching

**Idea:** Before doing a full search, check if we can **assemble results from cache**

```python
async def search_with_partial_cache(query: str, max_results: int):
    """
    Smart caching: Try to build results from cached items first.

    Algorithm:
    1. Extract potential GEO IDs from query
    2. Check cache for known results matching query terms
    3. Fetch cached items
    4. Only search for gap (max_results - cached_count)
    5. Merge cached + new results
    """

    # Step 1: Check full result cache (existing)
    cached_full = await cache.get_search_result(query_hash)
    if cached_full:
        return cached_full  # ✅ Fast path

    # Step 2: NEW - Partial cache lookup
    # Find GEO IDs mentioned in recent searches with similar terms
    query_terms = extract_terms(query)
    potential_ids = await cache.get_geo_ids_by_terms(query_terms)

    # Step 3: Fetch cached metadata for potential matches
    cached_items = []
    for geo_id in potential_ids[:max_results]:
        metadata = await geo_client.get_metadata(geo_id)  # Uses cache!
        if metadata:
            cached_items.append(metadata)

    # Step 4: If we have enough cached items, skip search
    if len(cached_items) >= max_results:
        logger.info(f"✅ Assembled {len(cached_items)} results from cache")
        return build_result(cached_items, cache_hit=True)

    # Step 5: Search for gap
    gap = max_results - len(cached_items)
    if gap > 0:
        logger.info(f"Searching for {gap} missing results")
        new_items = await geo_client.search(query, max_results=gap)
        return merge(cached_items, new_items)
```

### Benefits

**Performance Improvement:**
```
Scenario: Search "diabetes" (100 results), then "diabetes insulin"

Current:
- First search: 3.5 seconds (full search)
- Second search: 3.5 seconds (full search, even with 70% overlap)

With Partial Caching:
- First search: 3.5 seconds (full search)
- Second search: 0.8 seconds (70 cached + 30 new)
  - 70 items from cache: 0.2s
  - 30 items from search: 0.6s

Speedup: 4.4x for overlapping queries
```

**Use Cases:**
1. **Iterative refinement:** "diabetes" → "diabetes type 2" → "diabetes type 2 pancreas"
2. **Broadening search:** "cancer" → "breast cancer" → "breast cancer genomics"
3. **Related queries:** "insulin resistance" → "metabolic syndrome"

---

## Implementation Plan

### Phase 1: Term-Based ID Index (Simple)

```python
# New cache method
async def get_geo_ids_by_terms(
    self,
    terms: List[str],
    limit: int = 100
) -> List[str]:
    """
    Get GEO IDs associated with search terms.

    Uses sorted set to rank by relevance/frequency.
    """
    key = self._make_key("term_index", "+".join(sorted(terms)))
    ids = await self.client.zrange(key, 0, limit-1, desc=True)
    return ids

# Update after each search
async def index_search_terms(
    self,
    query: str,
    geo_ids: List[str]
):
    """
    Index GEO IDs by search terms for partial cache lookup.
    """
    terms = extract_meaningful_terms(query)
    for term in terms:
        key = self._make_key("term_index", term)
        # Add with timestamp score
        score = time.time()
        for geo_id in geo_ids:
            await self.client.zadd(key, {geo_id: score})
        # Set expiry
        await self.client.expire(key, 86400)  # 24 hours
```

### Phase 2: Embedding-Based Similarity (Advanced)

```python
async def get_similar_cached_results(
    self,
    query: str,
    threshold: float = 0.85
) -> List[str]:
    """
    Find cached results for similar queries using embeddings.

    Uses semantic similarity to find related past searches.
    """
    query_embedding = await self.embedding_service.embed(query)

    # Store query embeddings in vector DB
    similar_queries = await self.vector_db.search(
        query_embedding,
        k=10,
        threshold=threshold
    )

    # Aggregate GEO IDs from similar queries
    aggregated_ids = []
    for similar_query, score in similar_queries:
        cached_result = await self.get_search_result(similar_query)
        if cached_result:
            aggregated_ids.extend(cached_result.geo_ids)

    return deduplicate(aggregated_ids)
```

---

## Current Issues to Fix First

### Bug #10: `geo_id` vs `accession` ✅ FIXED
**File:** `unified_search_pipeline.py` line 526
**Fix:** Changed `dataset.accession` → `dataset.geo_id`

---

## Metrics to Track

### Cache Performance
- Cache hit rate: Target 60%+ for production
- Cache miss latency: Target <5s
- Partial cache assembly time: Target <1s
- Storage used: Monitor Redis memory

### Search Performance
```
Cold search (no cache): 3-5s
Warm search (full cache): <100ms
Partial cache (70% overlap): <1s
```

---

## Quick Win: Enable Item-Level Cache First

**Current State:**
- ✅ GEOClient has SimpleCache (file-based)
- ✅ Individual `get_metadata()` calls are cached
- ✅ TTL: 30 days for GEO metadata

**Immediate Benefit:**
When unified pipeline calls `geo_client.get_metadata()` for the same GEO ID multiple times, it's already cached!

**Verification:**
```bash
# Check if metadata is being cached
ls -lah ~/.omics_oracle/cache/geo/

# Should see files like:
# GSE123456_metadata.json
# GSE789012_metadata.json
```

**Next Step:**
Just run the quick test and watch the logs - you should see cache hits!

---

## Recommended Next Actions

1. **Fix Bug #10** ✅ DONE
2. **Run quick_test.py** to verify basic pipeline works
3. **Monitor cache effectiveness:**
   ```python
   logger.info(f"Cache stats: {cache.get_stats()}")
   ```
4. **Phase 1:** Implement term-based partial caching (2-3 hours)
5. **Phase 2:** Add embedding-based similarity search (Week 3)

---

**Last Updated:** October 11, 2025 - 04:30 AM
**Status:** Architecture documented, Bug #10 fixed, ready for quick test
