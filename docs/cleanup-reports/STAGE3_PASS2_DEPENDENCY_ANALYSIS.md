# Stage 3 Pass 2: Dependency Analysis

**Date**: October 12, 2025
**Scope**: Complete dependency mapping for flattening search architecture

---

## Current Architecture Map

### Layer 1: OmicsSearchPipeline (unified_search_pipeline.py - 861 LOC)

**Purpose**: Main search orchestrator

**Key Methods**:
- `search()` - Main entry point (async)
- `_search_geo()` - Search GEO datasets
- `_search_geo_by_id()` - Fast path for GEO IDs
- `_search_publications()` - **CALLS PublicationSearchPipeline** (nested!)
- `_extract_geo_ids_from_publications()` - Extract GSE IDs from pubs
- `_deduplicate_geo_datasets()` - Remove duplicate GEO results

**Dependencies**:
```python
from omics_oracle_v2.lib.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.geo import GEOClient
from omics_oracle_v2.lib.geo.query_builder import GEOQueryBuilder
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline  # ← NESTED!
from omics_oracle_v2.lib.publications.deduplication import AdvancedDeduplicator
from omics_oracle_v2.lib.query.analyzer import QueryAnalyzer, SearchType
from omics_oracle_v2.lib.query.optimizer import QueryOptimizer
```

**Key Flow**:
```python
async def search(query, ...):
    # 1. Check cache
    # 2. Analyze query type
    # 3. Optimize query (NER + SapBERT)
    # 4. Route based on type:
    if type == GEO_ID:
        geo_datasets = await _search_geo_by_id(geo_id)
    elif type == HYBRID:
        # Run in parallel
        geo_task = _search_geo(query)
        pub_task = _search_publications(query)  # ← Calls nested pipeline!
        geo_datasets, publications = await asyncio.gather(geo_task, pub_task)
    # 5. Deduplicate
    # 6. Cache result
    # 7. Return SearchResult
```

**The Problem**:
```python
async def _search_publications(self, query: str, max_results: int):
    # Calls PublicationSearchPipeline.search() - NESTED ARCHITECTURE!
    search_result = self.publication_pipeline.search(query, max_results=max_results)
    publications = [result.publication for result in search_result.publications]
    return publications
```

---

### Layer 2: PublicationSearchPipeline (publication_pipeline.py - 943 LOC after Pass 1a)

**Purpose**: Search publications across multiple sources

**Key Methods**:
- `search()` - Main entry point (synchronous!)
- `_search_pubmed()` - Search PubMed
- `_search_openalex()` - Search OpenAlex
- `_search_scholar()` - Search Google Scholar (optional)
- `_enrich_with_citations()` - Add citation metrics
- `_deduplicate()` - Remove duplicate publications
- `_rank()` - Rank by relevance

**Dependencies**:
```python
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient
from omics_oracle_v2.lib.citations.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.citations.clients.semantic_scholar import SemanticScholarClient
from omics_oracle_v2.lib.publications.deduplication import AdvancedDeduplicator
from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker
```

**Key Flow**:
```python
def search(query, max_results):
    # 1. Search PubMed
    pubmed_results = _search_pubmed(query, max_results)

    # 2. Search OpenAlex
    openalex_results = _search_openalex(query, max_results)

    # 3. Search Scholar (optional)
    scholar_results = _search_scholar(query, max_results) if enabled

    # 4. Combine results
    all_results = pubmed_results + openalex_results + scholar_results

    # 5. Deduplicate
    unique_results = deduplicator.deduplicate(all_results)

    # 6. Enrich with citations (optional)
    if enable_citations:
        enriched = _enrich_with_citations(unique_results)

    # 7. Rank
    ranked = ranker.rank(enriched)

    # 8. Return PublicationSearchResult
    return PublicationSearchResult(publications=ranked)
```

---

## Current Callers

### 1. api/routes/agents.py (Primary Production API)

**Location**: Lines 41, 221, 251, 263

**Usage**:
```python
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import (
    OmicsSearchPipeline,
    UnifiedSearchConfig
)

@router.post("/search", response_model=UnifiedSearchResponse)
async def unified_search_endpoint(...):
    config = UnifiedSearchConfig(...)
    pipeline = OmicsSearchPipeline(config)
    result = await pipeline.search(query, ...)
    return response
```

**Migration Strategy**:
- Replace `OmicsSearchPipeline` with `SearchOrchestrator`
- Keep same config (or simplify)
- Keep same return type (`SearchResult`)

---

### 2. agents/orchestrator.py (Multi-Agent Workflow)

**Location**: Lines 24, 32, 35, 56, 57, 413, 467, 486

**Usage**:
```python
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import (
    OmicsSearchPipeline,
    UnifiedSearchConfig
)

class Orchestrator:
    def __init__(self, settings):
        search_config = UnifiedSearchConfig(...)
        self.search_pipeline = OmicsSearchPipeline(search_config)

    async def _execute_search_stage(self, ...):
        search_result = asyncio.run(
            self.search_pipeline.search(query, ...)
        )
        return WorkflowResult(agent_name="OmicsSearchPipeline", ...)
```

**Migration Strategy**:
- Replace `OmicsSearchPipeline` with `SearchOrchestrator`
- Update agent_name to "SearchOrchestrator"
- Keep same interface

---

## Target Architecture

### New: SearchOrchestrator (lib/search/orchestrator.py - ~600 LOC)

**Purpose**: Flat, single-layer search coordinator

**Key Features**:
- ✅ Direct calls to all clients (no nesting)
- ✅ Parallel execution with asyncio.gather()
- ✅ Clear separation of concerns
- ✅ Same public interface as OmicsSearchPipeline

**Structure**:
```python
class SearchOrchestrator:
    def __init__(self, config: SearchConfig):
        # Stage 2: Query processing
        self.query_analyzer = QueryAnalyzer()
        self.query_optimizer = QueryOptimizer(config)

        # Stage 4: Direct client access (no nested pipelines!)
        self.geo_client = GEOClient()
        self.geo_query_builder = GEOQueryBuilder()
        self.pubmed_client = PubMedClient(config.pubmed_config)
        self.openalex_client = OpenAlexClient(config.openalex_config)
        self.scholar_client = GoogleScholarClient(config.scholar_config) if enabled

        # Stage 5: Result processing
        self.deduplicator = AdvancedDeduplicator()
        self.ranker = PublicationRanker()

        # Stage 7: Caching
        self.cache = RedisCache(config)

    async def search(self, query: str, ...) -> SearchResult:
        # 1. Check cache
        # 2. Analyze query
        # 3. Optimize query
        # 4. Execute searches IN PARALLEL
        async def search_all():
            geo_task = self._search_geo(optimized_query)
            pubmed_task = self._search_pubmed(optimized_query)
            openalex_task = self._search_openalex(optimized_query)

            return await asyncio.gather(
                geo_task,
                pubmed_task,
                openalex_task,
                return_exceptions=True
            )

        geo_results, pubmed_results, openalex_results = await search_all()

        # 5. Combine and deduplicate
        all_pubs = pubmed_results + openalex_results
        unique_pubs = self.deduplicator.deduplicate(all_pubs)

        # 6. Rank
        ranked_pubs = self.ranker.rank(unique_pubs)

        # 7. Cache and return
        result = SearchResult(...)
        await self.cache.set(cache_key, result)
        return result
```

---

## Logic to Migrate

### From OmicsSearchPipeline:

**Keep**:
- ✅ Cache integration (`_check_cache`, cache.get/set)
- ✅ Query analysis (QueryAnalyzer)
- ✅ Query optimization (QueryOptimizer)
- ✅ GEO search logic (`_search_geo`, `_search_geo_by_id`)
- ✅ GEO query building (GEOQueryBuilder)
- ✅ GEO deduplication (`_deduplicate_geo_datasets`)
- ✅ GEO ID extraction from publications (`_extract_geo_ids_from_publications`)
- ✅ Parallel search orchestration (asyncio.gather)
- ✅ SearchResult model

**Remove/Inline**:
- ❌ `_search_publications()` - inline the client calls instead
- ❌ PublicationSearchPipeline dependency

---

### From PublicationSearchPipeline:

**Migrate to SearchOrchestrator**:
- ✅ Direct PubMed search (`_search_pubmed`)
- ✅ Direct OpenAlex search (`_search_openalex`)
- ✅ Direct Scholar search (`_search_scholar`)
- ✅ Client initialization (PubMedClient, OpenAlexClient, etc.)

**Move to Stage 5 (Later)**:
- ⏳ Publication deduplication logic
- ⏳ Publication ranking logic
- ⏳ Citation enrichment logic

**Keep in PublicationSearchPipeline (for now)**:
- ✅ Full-text download orchestration
- ✅ PDF management
- ✅ LLM citation analysis
- ✅ Institutional access

---

## Migration Checklist

### Phase 2: Create SearchOrchestrator

- [ ] Create `lib/search/__init__.py`
- [ ] Create `lib/search/orchestrator.py`
- [ ] Create `lib/search/config.py` (simplified SearchConfig)
- [ ] Create `lib/search/models.py` (SearchResult, SearchInput)
- [ ] Implement core search() method
- [ ] Implement _search_geo() and _search_geo_by_id()
- [ ] Implement _search_pubmed()
- [ ] Implement _search_openalex()
- [ ] Implement _search_scholar()
- [ ] Add cache integration
- [ ] Add parallel execution with asyncio.gather()
- [ ] Add error handling
- [ ] Add logging

### Phase 3: Update Callers

- [ ] Update `api/routes/agents.py` imports
- [ ] Update `api/routes/agents.py` instantiation
- [ ] Update `agents/orchestrator.py` imports
- [ ] Update `agents/orchestrator.py` instantiation
- [ ] Update any test files

### Phase 4: Validation

- [ ] Test SearchOrchestrator imports
- [ ] Test SearchOrchestrator instantiation
- [ ] Test API endpoint /api/agents/search
- [ ] Test parallel execution (logs should show parallel)
- [ ] Test caching works
- [ ] Test GEO-only search
- [ ] Test publication-only search
- [ ] Test hybrid search
- [ ] Compare performance (should be faster)

### Phase 5: Archive

- [ ] Move `lib/pipelines/unified_search_pipeline.py` → `extras/pipelines/`
- [ ] Move `lib/pipelines/publication_pipeline.py` → `extras/pipelines/`
- [ ] Update `lib/pipelines/__init__.py`
- [ ] Create migration documentation
- [ ] Commit changes

---

## Risk Assessment

### High Risk:
1. **Breaking async/sync boundary** - OmicsSearchPipeline is async, PublicationSearchPipeline is sync
   - **Mitigation**: Make all SearchOrchestrator methods async

2. **Cache key compatibility** - Need same cache keys or invalidate cache
   - **Mitigation**: Use same cache key generation logic

3. **Missing edge cases** - Complex error handling in both pipelines
   - **Mitigation**: Copy all try/except blocks carefully

### Medium Risk:
1. **Performance regression** - Parallel execution must work correctly
   - **Mitigation**: Test with logging to verify parallelism

2. **Configuration mismatch** - Many config options to migrate
   - **Mitigation**: Start with minimal config, expand later

### Low Risk:
1. **Import errors** - Standard Python import issues
   - **Mitigation**: Test imports first

---

**Status**: ✅ ANALYSIS COMPLETE
**Next**: Phase 2 - Create SearchOrchestrator
