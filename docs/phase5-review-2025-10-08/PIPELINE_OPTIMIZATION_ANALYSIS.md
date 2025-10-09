# Pipeline Exploration and Optimization Analysis

**Date:** October 8, 2025  
**Focus:** End-to-end search pipeline performance analysis  
**Goal:** Identify optimization opportunities and enhancement areas

---

## 🎯 Pipeline Overview

### Current End-to-End Flow

```
User Query
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Query Processing (QueryAgent)                     │
│ • NLP entity extraction                                     │
│ • Intent classification                                     │
│ • Search term generation                                    │
│ Performance: <100ms | Cost: $0                              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Database Search (SearchAgent)                     │
│ • GEO database queries                                      │
│ • Optional semantic search                                  │
│ • Relevance ranking                                         │
│ Performance: 20-30s (keyword) | 5-10s (semantic)           │
│ Cost: $0 (free NCBI API)                                   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: Quality Assessment (DataAgent)                    │
│ • Quality scoring                                           │
│ • Metadata validation                                       │
│ • Filtering                                                 │
│ Performance: <1s | Cost: $0                                 │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: Report Generation (ReportAgent)                   │
│ • AI-powered summarization (optional)                       │
│ • Insight extraction                                        │
│ • Recommendations                                           │
│ Performance: 1-2s (no GPT) | 13-15s (with GPT)            │
│ Cost: $0 (fallback) | ~$0.04 (GPT-4)                      │
└─────────────────────────────────────────────────────────────┘
    ↓
Final Report
```

**Total Time (FULL_ANALYSIS):**
- First run: 25-45 seconds
- Cached: <2 seconds

---

## 🔍 Stage-by-Stage Analysis

### STAGE 1: QueryAgent - NLP Entity Extraction

#### Current Implementation
```python
# File: omics_oracle_v2/agents/query_agent.py
class QueryAgent(Agent[QueryInput, QueryOutput]):
    def __init__(self, settings: Settings):
        self._ner = BiomedicalNER(settings.nlp)  # Local NER model
        self._intent_keywords = {...}  # Rule-based intent detection
```

#### Performance Profile
- **Time:** <100ms
- **CPU:** Low (local model)
- **Memory:** Moderate (NER model loaded)
- **Cost:** $0

#### Strengths ✅
- ✅ Very fast (<100ms)
- ✅ No external API dependencies
- ✅ Configurable NER model
- ✅ No cost

#### Bottlenecks ⚠️
- ⚠️ **NER model loading time** - One-time cost at startup
- ⚠️ **Entity linking** - Optional, adds latency if enabled
- ⚠️ **Synonym expansion** - Can slow down with large vocabularies

#### Optimization Opportunities 🚀

**1. Model Caching** (LOW EFFORT, HIGH IMPACT)
```python
# Current: Model loaded per agent instance
# Optimization: Singleton pattern for NER model

class BiomedicalNER:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._model = load_model()  # Load once
        return cls._instance
```
**Impact:** Faster agent initialization, lower memory

**2. Lazy Entity Linking** (LOW EFFORT, MEDIUM IMPACT)
```python
# Current: Always link entities if enabled
# Optimization: Only link when synonyms needed

def extract_entities(self, query, include_entity_linking=False):
    entities = self._extract_basic_entities(query)
    
    if include_entity_linking:
        # Only fetch KB IDs when explicitly requested
        entities = self._link_to_knowledge_base(entities)
    
    return entities
```
**Impact:** Reduce latency when synonyms not needed

**3. Intent Detection Cache** (LOW EFFORT, LOW IMPACT)
```python
# Cache common query patterns
intent_cache = {
    "find": QueryIntent.SEARCH,
    "search for": QueryIntent.SEARCH,
    "analyze": QueryIntent.ANALYZE,
    ...
}
```
**Impact:** Marginal improvement (<5ms)

**Priority:** MEDIUM (QueryAgent already very fast)

---

### STAGE 2: SearchAgent - GEO Database Search

#### Current Implementation
```python
# File: omics_oracle_v2/agents/search_agent.py
class SearchAgent(Agent[SearchInput, SearchOutput]):
    def __init__(self, settings: Settings, enable_semantic=False):
        self._geo_client = GEOClient(settings.geo)
        self._ranker = KeywordRanker(settings.ranking)
        self._semantic_pipeline = None  # Optional
```

#### Performance Profile
- **Time:** 20-30s (keyword) | 5-10s (semantic with index)
- **Network:** High (NCBI API calls)
- **CPU:** Low (keyword) | Medium (semantic)
- **Cost:** $0 (free NCBI API)

#### Strengths ✅
- ✅ Semantic search available (5-10s vs 20-30s)
- ✅ Free NCBI API
- ✅ Comprehensive results

#### Bottlenecks 🔴 **MAJOR BOTTLENECK**

**1. GEO API Latency** (20-30 seconds!)
```python
# Current: Sequential API calls
search_result = await self._geo_client.search(query, max_results=50)
# ↓ 15-20s for initial search

for geo_id in top_ids:
    metadata = await self._geo_client.get_metadata(geo_id)
    # ↓ 0.5-1s per dataset × 50 = 25-50s more!
```

**Root Causes:**
- Sequential metadata fetching (50 × 0.5s = 25s)
- No request batching
- NCBI API rate limits (3 req/s without key)
- Network latency per request

#### Optimization Opportunities 🚀

**1. Parallel Metadata Fetching** 🔴 **HIGH PRIORITY**

**Current:**
```python
for geo_id in top_ids:
    metadata = await self._geo_client.get_metadata(geo_id)
    geo_datasets.append(metadata)
# Sequential: 50 requests × 0.5s = 25s
```

**Optimized:**
```python
import asyncio

# Batch fetch with concurrency limit
async def fetch_metadata_batch(self, geo_ids, batch_size=10):
    semaphore = asyncio.Semaphore(batch_size)
    
    async def fetch_one(geo_id):
        async with semaphore:
            return await self._geo_client.get_metadata(geo_id)
    
    tasks = [fetch_one(geo_id) for geo_id in geo_ids]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
geo_datasets = await self.fetch_metadata_batch(top_ids, batch_size=10)
# Parallel: 50 requests / 10 concurrent = 5 batches × 0.5s = 2.5s!
```

**Impact:** 🎯 **20-30s → 5-7s (70-80% reduction!)**

**2. Metadata Caching** 🔴 **HIGH PRIORITY**

```python
# Add Redis cache for GEO metadata
class GEOClient:
    def __init__(self, settings):
        self.cache = AsyncRedisCache()
        self.cache_ttl = 7 * 24 * 3600  # 7 days (metadata rarely changes)
    
    async def get_metadata(self, geo_id):
        # Try cache first
        cache_key = f"geo_metadata:{geo_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from API
        metadata = await self._fetch_from_ncbi(geo_id)
        
        # Cache for 7 days
        await self.cache.set(cache_key, metadata, ttl=self.cache_ttl)
        return metadata
```

**Impact:** 
- First search: 20-30s (cache miss)
- Subsequent searches: <1s (cache hit)
- Shared across users!

**3. Search Result Caching** 🟡 **MEDIUM PRIORITY**

```python
# Cache search results by query hash
cache_key = f"geo_search:{hash(search_query)}:{max_results}"
cached_results = await self.cache.get(cache_key)
if cached_results:
    return cached_results  # <100ms vs 20-30s!

# Execute search + cache
results = await self._execute_search(query, max_results)
await self.cache.set(cache_key, results, ttl=3600)  # 1 hour
```

**Impact:**
- Identical queries: Instant (<100ms)
- Similar queries: Still benefit from metadata cache

**4. Semantic Search Prioritization** 🟡 **MEDIUM PRIORITY**

```python
# Default to semantic search if index available
if self._semantic_index_loaded:
    # Use semantic search (5-10s)
    results = await self._semantic_search(query, input_data)
else:
    # Fall back to keyword (20-30s)
    results = await self._keyword_search(query, input_data)
```

**Impact:** 
- 5-10s vs 20-30s (50-66% faster)
- Better relevance
- Requires vector index pre-built

**5. Smart Query Optimization** 🟢 **LOW PRIORITY**

```python
def _optimize_query(self, search_terms):
    # Remove redundant terms
    # Use NCBI search syntax optimally
    # Limit results intelligently
    
    # Example: Use MeSH terms when available
    if has_mesh_term(term):
        return f"{term}[MeSH]"  # More precise, faster
```

**Impact:** Marginal (5-10% faster)

**Priority:** 🔴 **CRITICAL (Biggest bottleneck in pipeline)**

---

### STAGE 3: DataAgent - Quality Assessment

#### Current Implementation
```python
# File: omics_oracle_v2/agents/data_agent.py
class DataAgent(Agent[DataInput, DataOutput]):
    def __init__(self, settings: Settings):
        self._scorer = QualityScorer(settings.quality)
```

#### Performance Profile
- **Time:** <1s for 50 datasets
- **CPU:** Low (rule-based scoring)
- **Memory:** Low
- **Cost:** $0

#### Strengths ✅
- ✅ Very fast (<1s)
- ✅ Configurable quality metrics
- ✅ No external dependencies
- ✅ Already efficient

#### Bottlenecks ⚠️
- ⚠️ Sequential dataset processing (minor)
- ⚠️ Repeated quality calculations for same datasets

#### Optimization Opportunities 🚀

**1. Quality Score Caching** (LOW EFFORT, MEDIUM IMPACT)

```python
class DataAgent:
    def __init__(self, settings):
        self._scorer = QualityScorer(settings.quality)
        self._quality_cache = {}  # Simple in-memory cache
    
    def _process_dataset(self, ranked_dataset, context):
        geo_id = ranked_dataset.dataset.geo_id
        
        # Check cache
        if geo_id in self._quality_cache:
            return self._quality_cache[geo_id]
        
        # Calculate quality
        processed = self._calculate_quality(ranked_dataset)
        
        # Cache result
        self._quality_cache[geo_id] = processed
        return processed
```

**Impact:** 
- Same dataset in multiple searches: Instant
- Batch searches: Faster

**2. Vectorized Quality Scoring** (MEDIUM EFFORT, LOW IMPACT)

```python
# Use NumPy for batch scoring
import numpy as np

def calculate_quality_batch(self, datasets):
    # Vectorize calculations where possible
    sample_counts = np.array([d.sample_count for d in datasets])
    ages = np.array([d.get_age_days() for d in datasets])
    
    # Batch score calculation
    scores = self._vectorized_score(sample_counts, ages, ...)
    return scores
```

**Impact:** Marginal (<100ms savings)

**Priority:** LOW (Already very fast)

---

### STAGE 4: ReportAgent - AI-Powered Reports

#### Current Implementation
```python
# File: omics_oracle_v2/agents/report_agent.py
class ReportAgent(Agent[ReportInput, ReportOutput]):
    def __init__(self, settings):
        self._ai_client = SummarizationClient(settings.ai)  # Optional GPT-4
```

#### Performance Profile
- **Time:** 1-2s (no GPT) | 13-15s (with GPT-4)
- **Network:** None (no GPT) | High (GPT-4)
- **CPU:** Low
- **Cost:** $0 (no GPT) | ~$0.04 (GPT-4)

#### Strengths ✅
- ✅ Fast without GPT-4 (1-2s)
- ✅ Multiple report formats
- ✅ Graceful fallback
- ✅ Low cost

#### Bottlenecks ⚠️
- ⚠️ **GPT-4 API latency** (13-15s)
- ⚠️ GPT-4 cost (~$0.04 per analysis)
- ⚠️ Sequential summary generation

#### Optimization Opportunities 🚀

**1. Summary Caching** 🟡 **MEDIUM PRIORITY**

```python
class ReportAgent:
    async def _generate_summary(self, input_data, datasets):
        # Generate cache key from datasets
        dataset_hash = hash(tuple(d.geo_id for d in datasets[:5]))
        cache_key = f"summary:{dataset_hash}:{input_data.report_type}"
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached  # <100ms vs 13-15s!
        
        # Generate with GPT-4
        summary = await self._ai_client.summarize(...)
        
        # Cache for 24h
        await self.cache.set(cache_key, summary, ttl=86400)
        return summary
```

**Impact:**
- Same datasets: Instant (<100ms vs 13-15s)
- Cost savings: $0 (cache hit) vs $0.04

**2. Batch GPT-4 Summarization** 🟡 **MEDIUM PRIORITY**

```python
# Combine multiple dataset summaries in one GPT-4 call
async def _generate_summary_batch(self, datasets):
    # Current: 5 datasets × 3s each = 15s + 5× cost
    # Optimized: 1 call with all 5 = 3s + 1× cost
    
    combined_text = "\n\n".join([
        f"Dataset {d.geo_id}: {d.title}\n{d.summary[:200]}"
        for d in datasets[:5]
    ])
    
    summary = await self._ai_client.summarize(combined_text)
    return summary
```

**Impact:**
- Time: 13-15s → 3-5s
- Cost: 5× → 1× (80% savings!)

**3. Smart GPT-4 Usage** 🟢 **LOW PRIORITY**

```python
def should_use_gpt4(self, datasets, user_tier):
    # Only use GPT-4 when it adds value
    
    if user_tier == "free":
        return False  # Use fallback for free users
    
    if len(datasets) < 3:
        return False  # Not enough to summarize
    
    if all(d.quality_score < 0.5 for d in datasets):
        return False  # Low quality, not worth cost
    
    return True  # Premium user + good data = use GPT-4
```

**Impact:** Cost optimization (reduce unnecessary GPT-4 calls)

**Priority:** MEDIUM (Cost + performance optimization)

---

## 📊 Optimization Priority Matrix

### 🔴 CRITICAL (High Impact, High Priority)

**1. Parallel Metadata Fetching in SearchAgent**
- **Impact:** 70-80% time reduction (20-30s → 5-7s)
- **Effort:** Medium (2-4 hours)
- **Risk:** Low (well-tested pattern)
- **ROI:** VERY HIGH

**2. Metadata Caching (Redis)**
- **Impact:** Subsequent searches <1s (vs 20-30s)
- **Effort:** Low (1-2 hours, Redis already configured)
- **Risk:** Very Low
- **ROI:** VERY HIGH

### 🟡 HIGH (Medium-High Impact)

**3. Search Result Caching**
- **Impact:** Identical queries instant (<100ms)
- **Effort:** Low (1 hour)
- **Risk:** Very Low
- **ROI:** HIGH

**4. GPT-4 Summary Caching**
- **Impact:** 13-15s → <100ms (cached), $0.04 → $0 saved
- **Effort:** Low (1 hour)
- **Risk:** Very Low
- **ROI:** HIGH (time + cost savings)

**5. Enable Semantic Search by Default**
- **Impact:** 20-30s → 5-10s (if index available)
- **Effort:** Low (configuration change)
- **Risk:** Low (fallback exists)
- **ROI:** HIGH

### 🟢 MEDIUM (Nice to Have)

**6. Quality Score Caching**
- **Impact:** Faster for repeated datasets
- **Effort:** Very Low (30 min)
- **Risk:** Very Low
- **ROI:** MEDIUM

**7. Batch GPT-4 Calls**
- **Impact:** 13-15s → 3-5s, 80% cost reduction
- **Effort:** Medium (2-3 hours)
- **Risk:** Low
- **ROI:** MEDIUM

**8. NER Model Caching**
- **Impact:** Faster agent initialization
- **Effort:** Low (1 hour)
- **Risk:** Low
- **ROI:** MEDIUM

---

## 🎯 Recommended Implementation Plan

### Sprint 1: Critical Optimizations (Week 1)

**Goal:** Reduce search time from 25-45s to 7-12s

**Tasks:**
1. ✅ **Parallel Metadata Fetching** (2-4 hours)
   - Implement async batch fetching with semaphore
   - Add error handling for failed requests
   - Test with various batch sizes (5, 10, 20)

2. ✅ **Metadata Caching** (1-2 hours)
   - Add Redis cache to GEOClient
   - 7-day TTL for metadata (rarely changes)
   - Test cache hit/miss scenarios

3. ✅ **Search Result Caching** (1 hour)
   - Cache by query hash
   - 1-hour TTL for search results
   - Add cache invalidation logic

**Expected Results:**
- First search: 20-30s → 7-10s (65-70% faster)
- Cached metadata: 20-30s → 2-3s (90% faster)
- Identical queries: <100ms (99% faster)

### Sprint 2: High-Value Optimizations (Week 2)

**Goal:** Optimize cost and enable semantic search

**Tasks:**
4. ✅ **GPT-4 Summary Caching** (1 hour)
   - Cache summaries by dataset hash
   - 24-hour TTL
   - Monitor cache hit rate

5. ✅ **Enable Semantic Search** (2 hours)
   - Set default to semantic if index available
   - Build/load vector index
   - Add fallback mechanism

6. ✅ **Smart GPT-4 Usage** (1 hour)
   - Implement tier-based logic
   - Quality threshold checks
   - Add GPT-4 budget controls

**Expected Results:**
- GPT-4 costs: ~$0.04 → ~$0.01 (75% reduction via caching)
- Search time: 7-10s → 5-7s (semantic search)
- Better relevance with semantic search

### Sprint 3: Polish & Monitoring (Week 3)

**Goal:** Add monitoring and fine-tune

**Tasks:**
7. ✅ **Performance Monitoring** (2-3 hours)
   - Add detailed timing metrics
   - Track cache hit rates
   - Monitor API latency

8. ✅ **Quality Score Caching** (30 min)
   - Add simple cache
   - Track reuse rate

9. ✅ **Batch GPT-4 Calls** (2-3 hours)
   - Implement batch summarization
   - Test quality vs speed tradeoff

**Expected Results:**
- Full visibility into performance
- Data-driven optimization decisions
- Additional 10-20% improvements

---

## 📈 Expected Performance Improvements

### Current State
```
FULL_ANALYSIS Workflow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query Processing:     <100ms
GEO Search:           20-30s  ← BOTTLENECK
Quality Assessment:   <1s
Report Generation:    1-2s (no GPT) | 13-15s (GPT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total (no GPT):       22-32s
Total (with GPT):     34-46s
Cached:               <2s
```

### After Sprint 1 (Critical Optimizations)
```
FULL_ANALYSIS Workflow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query Processing:     <100ms
GEO Search:           7-10s   ✅ 60-70% faster
Quality Assessment:   <1s
Report Generation:    1-2s (no GPT) | 13-15s (GPT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total (no GPT):       9-13s   ✅ 50-60% faster
Total (with GPT):     21-27s  ✅ 38-42% faster
Cached (metadata):    2-3s    ✅ 85% faster
Cached (full):        <500ms  ✅ 95% faster
```

### After Sprint 2 (High-Value Optimizations)
```
FULL_ANALYSIS Workflow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query Processing:     <100ms
GEO Search:           5-7s    ✅ 75-80% faster (semantic)
Quality Assessment:   <1s
Report Generation:    1-2s (no GPT) | 3-5s (GPT cached)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total (no GPT):       7-10s   ✅ 68-75% faster
Total (with GPT):     9-13s   ✅ 70-75% faster (cached)
Cached:               <500ms  ✅ 98% faster
Cost per search:      $0.01   ✅ 75% cost reduction
```

---

## 🔧 Technical Implementation Details

### 1. Parallel Metadata Fetching

**File:** `omics_oracle_v2/lib/geo/client.py`

```python
import asyncio
from typing import List

class GEOClient:
    async def fetch_metadata_batch(
        self, 
        geo_ids: List[str], 
        max_concurrent: int = 10
    ) -> List[GEOSeriesMetadata]:
        """
        Fetch metadata for multiple GEO IDs in parallel.
        
        Args:
            geo_ids: List of GEO accession IDs
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of metadata objects (None for failed requests)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_one(geo_id: str):
            async with semaphore:
                try:
                    return await self.get_metadata(geo_id)
                except Exception as e:
                    logger.warning(f"Failed to fetch {geo_id}: {e}")
                    return None
        
        tasks = [fetch_one(geo_id) for geo_id in geo_ids]
        results = await asyncio.gather(*tasks)
        
        # Filter out None (failed requests)
        return [r for r in results if r is not None]
```

**Usage in SearchAgent:**
```python
# Replace:
# for geo_id in top_ids:
#     metadata = await self._geo_client.get_metadata(geo_id)
#     geo_datasets.append(metadata)

# With:
geo_datasets = await self._geo_client.fetch_metadata_batch(
    top_ids, 
    max_concurrent=10
)
```

### 2. Metadata Caching

**File:** `omics_oracle_v2/lib/geo/client.py`

```python
from omics_oracle_v2.lib.cache.redis_client import AsyncRedisCache

class GEOClient:
    def __init__(self, settings):
        self.settings = settings
        self.cache = AsyncRedisCache()
        self.cache_ttl = {
            'metadata': 7 * 24 * 3600,      # 7 days
            'search_results': 3600,          # 1 hour
        }
    
    async def get_metadata(self, geo_id: str) -> GEOSeriesMetadata:
        """Get metadata with Redis caching."""
        cache_key = f"geo:metadata:{geo_id}"
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {geo_id}")
            return GEOSeriesMetadata(**cached)
        
        # Fetch from NCBI
        logger.debug(f"Cache miss for {geo_id}, fetching from NCBI")
        metadata = await self._fetch_from_ncbi(geo_id)
        
        # Cache for 7 days
        await self.cache.set(
            cache_key, 
            metadata.dict(), 
            ttl=self.cache_ttl['metadata']
        )
        
        return metadata
```

### 3. Search Result Caching

**File:** `omics_oracle_v2/agents/search_agent.py`

```python
import hashlib

class SearchAgent:
    def _generate_search_cache_key(self, search_query: str, max_results: int) -> str:
        """Generate consistent cache key for search query."""
        key_str = f"{search_query}:{max_results}"
        hash_key = hashlib.md5(key_str.encode()).hexdigest()
        return f"search:results:{hash_key}"
    
    async def _cached_search(
        self, 
        search_query: str, 
        max_results: int
    ) -> Optional[SearchOutput]:
        """Try to get search results from cache."""
        cache_key = self._generate_search_cache_key(search_query, max_results)
        cached = await self.cache.get(cache_key)
        
        if cached:
            logger.info(f"Search cache hit: {search_query[:50]}...")
            return SearchOutput(**cached)
        
        return None
    
    async def _process(self, input_data: SearchInput, context: AgentContext):
        # Try cache first
        search_query = self._build_search_query(input_data)
        cached_result = await self._cached_search(search_query, input_data.max_results)
        
        if cached_result:
            context.set_metric("cache_hit", True)
            return cached_result
        
        # Execute search
        result = await self._execute_search(input_data, context)
        
        # Cache result
        cache_key = self._generate_search_cache_key(search_query, input_data.max_results)
        await self.cache.set(
            cache_key, 
            result.dict(), 
            ttl=3600  # 1 hour
        )
        
        return result
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

```python
# Add to AgentContext
context.set_metric("stage_duration_ms", {
    "query": 50,
    "search": 7200,
    "quality": 850,
    "report": 1200,
    "total": 9300
})

context.set_metric("cache_stats", {
    "metadata_hits": 35,
    "metadata_misses": 15,
    "search_hits": 1,
    "search_misses": 0,
    "gpt4_hits": 0,
    "gpt4_misses": 1
})

context.set_metric("search_stats", {
    "mode": "semantic",  # or "keyword"
    "concurrent_requests": 10,
    "total_requests": 50,
    "failed_requests": 2,
    "api_latency_avg_ms": 450
})

context.set_metric("cost", {
    "gpt4_calls": 1,
    "gpt4_cost_usd": 0.04,
    "total_cost_usd": 0.04
})
```

### Performance Dashboard

Track over time:
- Average search duration (by mode)
- Cache hit rates (metadata, search, GPT-4)
- Cost per search
- User tier distribution
- Error rates

---

## ✅ Success Criteria

### Sprint 1 Success
- ✅ Average search time < 12s (from 25-45s)
- ✅ Metadata cache hit rate > 60%
- ✅ Search cache hit rate > 20%
- ✅ Error rate < 2%

### Sprint 2 Success
- ✅ Average search time < 8s
- ✅ GPT-4 cache hit rate > 40%
- ✅ Cost per search < $0.02
- ✅ Semantic search adoption > 50%

### Sprint 3 Success
- ✅ Full monitoring dashboard
- ✅ All cache hit rates > 50%
- ✅ Average search time < 7s
- ✅ Cost per search < $0.01

---

## 🚀 Next Steps

1. **Review this analysis** - Confirm priorities align with goals
2. **Start Sprint 1** - Implement critical optimizations
3. **Measure baselines** - Establish current performance metrics
4. **Implement & test** - One optimization at a time
5. **Monitor & iterate** - Track improvements, adjust as needed

---

**Status:** Ready for implementation  
**Priority:** High (major performance gains available)  
**Estimated Timeline:** 3 weeks (3 sprints)  
**Expected ROI:** Very High (70-80% time reduction, 75% cost reduction)

**Ready to start with Sprint 1?**
