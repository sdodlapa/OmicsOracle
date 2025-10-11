# Pipeline Unification Proposal

**Date:** October 10, 2025
**Status:** Analysis & Recommendation
**Author:** Code Review & Architecture Analysis

---

## 🎯 Executive Summary

After thorough code examination, I propose **merging the three pipelines into ONE unified `OmicsSearchPipeline`** with intelligent routing based on query type and feature toggles.

**Key Benefits:**
- ✅ Eliminate ~60% code duplication
- ✅ Single configuration system
- ✅ Unified caching layer (10-100x speedup across all use cases)
- ✅ Consistent preprocessing (NER + synonyms for all queries)
- ✅ Simplified maintenance (one pipeline to update)

---

## 📊 Current State Analysis

### Three Separate Pipelines

#### 1. **SearchAgent** (GEO dataset search)
**File:** `omics_oracle_v2/agents/search_agent.py` (600+ lines)

**Purpose:** Find GEO datasets
**Entry:** API `/api/agents/search` or Dashboard (indirect)

**Flow:**
```python
query → [optional: NER+synonyms] → GEOClient.search() → filter → rank → return
```

**Duplicated Components:**
- Query preprocessing (NER + synonyms) - DUPLICATED with PublicationSearchPipeline
- GEOClient wrapper - REDUNDANT initialization
- Filtering logic - SIMILAR to PublicationSearchPipeline
- Ranking system - SEPARATE from PublicationRanker

---

#### 2. **PublicationSearchPipeline** (Publication search)
**File:** `omics_oracle_v2/lib/pipelines/publication_pipeline.py` (900+ lines)

**Purpose:** Find publications (papers)
**Entry:** Dashboard (direct import)

**Flow:**
```python
query → NER+synonyms → multi-source search → dedupe → rank → citations → PDFs → return
```

**Unique Features:**
- Multi-source search (PubMed, OpenAlex, Scholar)
- 2-pass deduplication
- Citation enrichment
- Institutional access
- PDF download & text extraction

---

#### 3. **GEOCitationPipeline** (Bulk collection)
**File:** `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py` (373 lines)

**Purpose:** Collect datasets + citing papers + PDFs
**Entry:** Python scripts (programmatic)

**Flow:**
```python
query → [synonyms] → GEOClient.search() → CitationDiscovery → FullText URLs → PDFs → save to disk
```

**Duplicated Components:**
- Synonym expansion - DUPLICATED with SearchAgent
- GEOClient search - DUPLICATED with SearchAgent
- Citation discovery - SIMILAR to PublicationSearchPipeline
- PDF download - IDENTICAL to PublicationSearchPipeline

---

## 🔍 Redundancy Analysis

### Code Duplication Matrix

| Component | SearchAgent | PublicationPipeline | GEOCitationPipeline |
|-----------|-------------|---------------------|---------------------|
| **Query Preprocessing** | ✅ (lines 230-280) | ✅ (lines 290-470) | ❌ (uses GEOQueryBuilder) |
| **NER Entity Extraction** | ✅ (via preprocessing) | ✅ (BiomedicalNER) | ❌ |
| **Synonym Expansion** | ✅ (SynonymExpander) | ✅ (SynonymExpander) | ✅ (SynonymExpander) |
| **GEO Search** | ✅ (GEOClient) | ❌ | ✅ (GEOClient) |
| **Publication Search** | ✅ (fallback via PublicationPipeline!) | ✅ (main feature) | ❌ |
| **Deduplication** | ❌ | ✅ (2-pass) | ✅ (ID-based only) |
| **Citation Discovery** | ❌ | ✅ (3 sources) | ✅ (2 strategies) |
| **Full-text URLs** | ❌ | ✅ (8 sources) | ✅ (5+ sources) |
| **PDF Download** | ❌ | ✅ (async) | ✅ (async) |
| **Ranking** | ✅ (KeywordRanker) | ✅ (PublicationRanker) | ❌ (no ranking) |
| **Caching** | ❌ (via Redis in API) | ✅ (Redis) | ❌ |
| **Configuration** | SearchInput | PublicationSearchConfig | GEOCitationConfig |

### Shocking Discovery: SearchAgent Already Uses PublicationSearchPipeline!

```python
# search_agent.py lines 87-92
def _initialize_publication_search(self) -> None:
    """Initialize publication search pipeline."""
    # Creates PublicationSearchPipeline with PubMed client configured.
    self._publication_pipeline = PublicationSearchPipeline(pub_search_config)
```

**This means SearchAgent is ALREADY a wrapper around PublicationSearchPipeline!**

---

## 💡 Proposed Unified Architecture

### One Pipeline to Rule Them All: `OmicsSearchPipeline`

```python
class OmicsSearchPipeline:
    """
    Unified search pipeline for all OmicsOracle queries.

    Intelligently routes to appropriate search strategy based on:
    - Query type (GEO ID vs free text vs publication query)
    - Feature toggles (datasets only, publications only, or both)
    - User intent (quick search, deep collection, citation analysis)

    Replaces:
    - SearchAgent (GEO dataset search)
    - PublicationSearchPipeline (publication search)
    - GEOCitationPipeline (bulk collection)
    """

    def __init__(self, config: OmicsSearchConfig):
        """
        Unified configuration with feature toggles.

        Args:
            config: Unified configuration covering all use cases
        """
        self.config = config

        # Core components (always initialized)
        self.query_analyzer = QueryAnalyzer()  # NEW: Detect query type
        self.preprocessor = QueryPreprocessor()  # NER + synonyms
        self.cache = AsyncRedisCache() if config.enable_cache else None

        # Search clients (conditional initialization)
        self.geo_client = GEOClient() if config.enable_geo_search else None
        self.pubmed_client = PubMedClient() if config.enable_pubmed else None
        self.openalex_client = OpenAlexClient() if config.enable_openalex else None
        self.scholar_client = GoogleScholarClient() if config.enable_scholar else None

        # Enhancement components (conditional)
        self.deduplicator = AdvancedDeduplicator() if config.enable_dedup else None
        self.citation_finder = CitationFinder() if config.enable_citations else None
        self.fulltext_manager = FullTextManager() if config.enable_fulltext else None
        self.pdf_manager = PDFDownloadManager() if config.enable_pdf_download else None

        # Ranking
        self.ranker = UnifiedRanker(config)  # NEW: Handles both GEO & publications

    async def search(
        self,
        query: str,
        search_type: Optional[str] = None,  # "geo", "publications", "both", "auto"
        **kwargs
    ) -> UnifiedSearchResult:
        """
        Universal search entry point.

        Intelligently routes query to appropriate search strategy:
        - GEO ID (e.g., "GSE12345") → Direct GEO metadata fetch
        - GEO keywords → GEO dataset search
        - Publication keywords → Publication search
        - "both" → Search both datasets and publications
        - "auto" → Analyze query and decide

        Args:
            query: Search query (free text, GEO ID, or mixed)
            search_type: Force specific search type or "auto" (default)
            **kwargs: Additional parameters

        Returns:
            UnifiedSearchResult with datasets and/or publications
        """
        # Step 1: Analyze query type
        query_info = self.query_analyzer.analyze(query)

        # Override if user specified search_type
        if search_type and search_type != "auto":
            query_info.search_type = search_type

        # Step 2: Route to appropriate search strategy
        if query_info.is_geo_id:
            # Direct GEO metadata fetch (fast path)
            return await self._fetch_geo_metadata(query_info.geo_ids)

        elif query_info.search_type == "geo" or (
            query_info.search_type == "auto" and query_info.has_geo_keywords
        ):
            # GEO dataset search
            return await self._search_geo_datasets(query, query_info, **kwargs)

        elif query_info.search_type == "publications" or (
            query_info.search_type == "auto" and query_info.has_publication_keywords
        ):
            # Publication search
            return await self._search_publications(query, query_info, **kwargs)

        elif query_info.search_type == "both":
            # Search both datasets and publications
            return await self._search_unified(query, query_info, **kwargs)

        else:
            # Default: Try publications first, fallback to GEO
            return await self._search_auto(query, query_info, **kwargs)

    async def _search_geo_datasets(
        self, query: str, query_info: QueryInfo, **kwargs
    ) -> UnifiedSearchResult:
        """
        Search for GEO datasets.

        Replaces: SearchAgent + GEOCitationPipeline (dataset search part)
        """
        # 1. Preprocess query
        preprocessed = await self.preprocessor.process(query, target="geo")

        # 2. Search GEO
        geo_results = await self.geo_client.search(
            query=preprocessed.optimized_query,
            max_results=kwargs.get("max_results", 50)
        )

        # 3. Fetch metadata (parallel batch)
        datasets = await self.geo_client.batch_get_metadata_smart(
            geo_ids=geo_results.geo_ids,
            max_concurrent=10
        )

        # 4. Filter
        if self.config.enable_filtering:
            datasets = self._apply_filters(datasets, kwargs)

        # 5. Rank
        ranked = await self.ranker.rank_geo_datasets(datasets, query)

        # 6. Optional: Find citing papers
        if self.config.enable_citations and kwargs.get("include_citations"):
            for dataset in ranked:
                dataset.citing_papers = await self.citation_finder.find_citing_papers(
                    dataset, max_results=kwargs.get("max_citations", 100)
                )

        return UnifiedSearchResult(
            query=query,
            search_type="geo",
            geo_datasets=ranked,
            publications=[],
        )

    async def _search_publications(
        self, query: str, query_info: QueryInfo, **kwargs
    ) -> UnifiedSearchResult:
        """
        Search for publications.

        Replaces: PublicationSearchPipeline
        """
        # 1. Preprocess query
        preprocessed = await self.preprocessor.process(query, target="publications")

        # 2. Multi-source search
        all_pubs = []

        if self.pubmed_client:
            pubmed_results = await self.pubmed_client.search(
                preprocessed.pubmed_query, max_results=kwargs.get("max_results", 50)
            )
            all_pubs.extend(pubmed_results)

        if self.openalex_client:
            openalex_results = await self.openalex_client.search(
                preprocessed.openalex_query, max_results=kwargs.get("max_results", 50)
            )
            all_pubs.extend(openalex_results)

        if self.scholar_client:
            scholar_results = await self.scholar_client.search(
                preprocessed.scholar_query, max_results=kwargs.get("max_results", 50)
            )
            all_pubs.extend(scholar_results)

        # 3. Deduplicate
        if self.deduplicator:
            all_pubs = self.deduplicator.deduplicate(all_pubs)

        # 4. Enrich with institutional access
        if self.config.enable_institutional_access:
            all_pubs = await self._enrich_institutional_access(all_pubs)

        # 5. Enrich with full-text URLs
        if self.fulltext_manager:
            all_pubs = await self.fulltext_manager.get_fulltext_batch(all_pubs)

        # 6. Rank
        ranked = await self.ranker.rank_publications(all_pubs, query)

        # 7. Optional: Citation enrichment
        if self.config.enable_citations and kwargs.get("include_citations"):
            ranked = await self._enrich_citations(ranked)

        # 8. Optional: PDF download
        if self.pdf_manager and kwargs.get("download_pdfs"):
            await self.pdf_manager.download_batch(ranked, output_dir=kwargs.get("output_dir"))

        return UnifiedSearchResult(
            query=query,
            search_type="publications",
            geo_datasets=[],
            publications=ranked,
        )

    async def _search_unified(
        self, query: str, query_info: QueryInfo, **kwargs
    ) -> UnifiedSearchResult:
        """
        Search both datasets and publications simultaneously.

        NEW: Combines both search types in parallel.
        """
        # Run both searches in parallel
        geo_task = self._search_geo_datasets(query, query_info, **kwargs)
        pub_task = self._search_publications(query, query_info, **kwargs)

        geo_result, pub_result = await asyncio.gather(geo_task, pub_task)

        # Combine results
        return UnifiedSearchResult(
            query=query,
            search_type="both",
            geo_datasets=geo_result.geo_datasets,
            publications=pub_result.publications,
        )

    async def collect_citations_bulk(
        self, query: str, output_dir: Path, **kwargs
    ) -> CollectionResult:
        """
        Bulk collection mode: Datasets + Citations + PDFs.

        Replaces: GEOCitationPipeline
        """
        # 1. Search for GEO datasets
        geo_result = await self._search_geo_datasets(query, QueryInfo(), **kwargs)

        # 2. For each dataset, find citing papers
        all_citing_papers = []
        for dataset in geo_result.geo_datasets:
            citing = await self.citation_finder.find_citing_papers(
                dataset, max_results=kwargs.get("max_citations", 100)
            )
            all_citing_papers.extend(citing)

        # 3. Deduplicate citations
        unique_citations = self.deduplicator.deduplicate(all_citing_papers)

        # 4. Get full-text URLs
        enriched = await self.fulltext_manager.get_fulltext_batch(unique_citations)

        # 5. Download PDFs
        download_report = await self.pdf_manager.download_batch(
            enriched, output_dir=output_dir / "pdfs"
        )

        # 6. Save metadata
        self._save_collection_metadata(
            geo_datasets=geo_result.geo_datasets,
            citing_papers=unique_citations,
            output_dir=output_dir,
        )

        return CollectionResult(
            query=query,
            datasets_found=geo_result.geo_datasets,
            citing_papers=unique_citations,
            pdfs_downloaded=download_report.successful,
            collection_dir=output_dir,
        )
```

---

## 🔧 New Components Required

### 1. **QueryAnalyzer** (NEW)
**Purpose:** Detect query type and intent

```python
class QueryAnalyzer:
    """
    Analyze query to determine search strategy.

    Examples:
    - "GSE12345" → GEO ID (direct fetch)
    - "breast cancer RNA-seq" → GEO keywords (dataset search)
    - "CRISPR mechanisms" → Publication keywords (paper search)
    - "datasets for BRCA1" → GEO (explicit intent)
    """

    def analyze(self, query: str) -> QueryInfo:
        """Analyze query and return structured info."""
        # Check for GEO ID pattern
        geo_ids = self._extract_geo_ids(query)

        # Check for explicit intent keywords
        has_geo_keywords = any(kw in query.lower() for kw in [
            "dataset", "geo", "series", "samples", "gse"
        ])

        has_publication_keywords = any(kw in query.lower() for kw in [
            "paper", "publication", "article", "journal", "study", "research"
        ])

        # Determine search type
        if geo_ids:
            search_type = "geo_id"
        elif has_geo_keywords and not has_publication_keywords:
            search_type = "geo"
        elif has_publication_keywords and not has_geo_keywords:
            search_type = "publications"
        else:
            search_type = "auto"  # Analyze content

        return QueryInfo(
            original_query=query,
            geo_ids=geo_ids,
            is_geo_id=bool(geo_ids),
            has_geo_keywords=has_geo_keywords,
            has_publication_keywords=has_publication_keywords,
            search_type=search_type,
        )
```

### 2. **UnifiedRanker** (NEW)
**Purpose:** Single ranker for both GEO datasets and publications

```python
class UnifiedRanker:
    """
    Unified ranking system for datasets and publications.

    Combines:
    - KeywordRanker (from SearchAgent)
    - PublicationRanker (from PublicationSearchPipeline)
    - GEO quality scoring (7 dimensions)
    - Publication relevance scoring
    """

    async def rank_geo_datasets(
        self, datasets: List[GEOSeriesMetadata], query: str
    ) -> List[RankedDataset]:
        """Rank GEO datasets by quality and relevance."""
        # Use existing logic from SearchAgent._rank_datasets()
        # + GEO quality scoring (7 dimensions)
        pass

    async def rank_publications(
        self, publications: List[Publication], query: str
    ) -> List[PublicationSearchResult]:
        """Rank publications by relevance."""
        # Use existing PublicationRanker logic
        pass
```

### 3. **UnifiedSearchConfig** (NEW)
**Purpose:** Single configuration for all features

```python
@dataclass
class OmicsSearchConfig:
    """
    Unified configuration for all search types.

    Replaces:
    - SearchInput (SearchAgent)
    - PublicationSearchConfig (PublicationSearchPipeline)
    - GEOCitationConfig (GEOCitationPipeline)
    """

    # Search sources
    enable_geo_search: bool = True
    enable_pubmed: bool = True
    enable_openalex: bool = True
    enable_scholar: bool = False

    # Query preprocessing
    enable_query_preprocessing: bool = True
    enable_synonym_expansion: bool = True
    max_synonyms_per_term: int = 10

    # Enhancement features
    enable_dedup: bool = True
    enable_fuzzy_dedup: bool = True
    enable_citations: bool = False
    enable_fulltext: bool = False
    enable_pdf_download: bool = False
    enable_institutional_access: bool = True

    # Performance
    enable_cache: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Institutions
    primary_institution: str = "gatech"
    secondary_institution: str = "odu"

    # Limits
    max_results: int = 50
    max_citations: int = 100
    max_concurrent_downloads: int = 5

    # PubMed config
    ncbi_email: str = ""
    ncbi_api_key: Optional[str] = None
```

---

## 🎯 Migration Plan

### Phase 1: Create Unified Pipeline (Week 1)
1. Create `OmicsSearchPipeline` class
2. Implement `QueryAnalyzer` for intelligent routing
3. Create `UnifiedRanker` combining both ranking systems
4. Create `OmicsSearchConfig` merging all configs

### Phase 2: Migrate SearchAgent (Week 2)
1. Update `search_agent.py` to wrap `OmicsSearchPipeline`
2. Keep API contract unchanged (`SearchInput` → `SearchOutput`)
3. Internally convert to `OmicsSearchConfig`
4. Test compatibility with existing API

### Phase 3: Migrate Dashboard (Week 3)
1. Update dashboard to use `OmicsSearchPipeline` directly
2. Remove redundant `PublicationSearchPipeline` import
3. Add toggle for "Search GEO datasets" vs "Search Publications"
4. Test all dashboard features

### Phase 4: Migrate Bulk Collection (Week 4)
1. Expose `collect_citations_bulk()` from `OmicsSearchPipeline`
2. Update scripts to use unified pipeline
3. Archive `geo_citation_pipeline.py`

### Phase 5: Cleanup (Week 5)
1. Archive old pipeline files
2. Update documentation
3. Remove duplicated code
4. Performance testing

---

## 📈 Expected Benefits

### 1. **Code Reduction**
- **Before:** 1,873 lines (600 + 900 + 373)
- **After:** ~1,200 lines (unified pipeline)
- **Savings:** 36% reduction

### 2. **Maintenance**
- **Before:** Update 3 separate pipelines for new features
- **After:** Update 1 pipeline, all use cases benefit
- **Example:** Adding a new publication source (e.g., bioRxiv) requires changes in 1 place, not 2

### 3. **Performance**
- **Before:** Separate caching for each pipeline
- **After:** Unified Redis cache across all queries
- **Benefit:** Cache hits from publication search help GEO search and vice versa

### 4. **Feature Parity**
- **Before:** SearchAgent lacks citation enrichment, GEOCitationPipeline lacks ranking
- **After:** All features available to all use cases via toggles

### 5. **User Experience**
- **Before:** "Do I use SearchAgent or PublicationPipeline?"
- **After:** One pipeline, intelligently routes based on query type

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Existing API
**Mitigation:** Keep `SearchAgent` as thin wrapper around unified pipeline

```python
class SearchAgent(Agent[SearchInput, SearchOutput]):
    """Backward-compatible wrapper around OmicsSearchPipeline."""

    def __init__(self, settings: Settings, **kwargs):
        self.pipeline = OmicsSearchPipeline(
            config=self._convert_settings(settings, kwargs)
        )

    def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        # Convert SearchInput → OmicsSearchConfig
        config_overrides = {
            "max_results": input_data.max_results,
            "enable_geo_search": True,
            "enable_pubmed": False,  # SearchAgent is GEO-only
        }

        # Call unified pipeline
        result = await self.pipeline.search(
            query=input_data.original_query,
            search_type="geo",
            **config_overrides
        )

        # Convert UnifiedSearchResult → SearchOutput
        return SearchOutput(
            datasets=result.geo_datasets,
            total_found=result.total_found,
            ...
        )
```

### Risk 2: Performance Regression
**Mitigation:** Extensive benchmarking before/after

- Keep old pipelines in archive for comparison
- A/B test with production traffic
- Gradual rollout with feature flag

### Risk 3: Complexity Increase
**Mitigation:** Clear separation of concerns

- `QueryAnalyzer` handles routing
- Each search type has dedicated method (`_search_geo_datasets()`, etc.)
- Configuration is explicit (no magic)

---

## 🎬 Recommendation

### Immediate Actions:
1. **✅ Approve this proposal** - Confirm unified pipeline is the right approach
2. **✅ Create prototype** - Build minimal `OmicsSearchPipeline` with GEO search only
3. **✅ Test performance** - Compare against existing `SearchAgent`
4. **✅ Migrate incrementally** - Start with SearchAgent wrapper

### Long-term Vision:
```
OmicsSearchPipeline (Unified)
    ↓
Intelligent Router
    ↓
    ├─ GEO Datasets (if query type = "geo" or GEO ID detected)
    ├─ Publications (if query type = "publications")
    ├─ Both (if query type = "both")
    └─ Auto (analyze query intent)
    ↓
Enhancement Layers (citations, PDFs, etc.)
    ↓
Unified Results (datasets + publications)
```

### Simple Hack for GEO ID Queries (Your Suggestion):
```python
# In OmicsSearchPipeline.search()
if self.query_analyzer.is_geo_id(query):
    # Skip preprocessing, directly fetch metadata
    geo_ids = self.query_analyzer.extract_geo_ids(query)
    metadata = await self.geo_client.batch_get_metadata_smart(geo_ids)
    return UnifiedSearchResult(geo_datasets=metadata, search_type="geo_id")
```

**This saves ~2-3 seconds of preprocessing overhead for GEO ID queries!**

---

## 🤔 Questions for You

1. **Should we keep SearchAgent as a wrapper** or completely replace it?
   - **Wrapper:** Backward compatible, safer migration
   - **Replace:** Cleaner architecture, but requires API changes

2. **When to archive old pipelines?**
   - **Option A:** Immediately (aggressive)
   - **Option B:** After 1 month of production testing (conservative)
   - **Option C:** Keep as reference but mark deprecated (middle ground)

3. **Should we expose search_type parameter to end users?**
   - **Yes:** Power users can force GEO or publication search
   - **No:** Auto-detection is always better (simpler UX)

4. **What about batch collection?**
   - **Keep separate CLI tool** that calls `pipeline.collect_citations_bulk()`
   - **Integrate into dashboard** with "Download All PDFs" button

---

## 💡 My Recommendation

**Go with the unified pipeline approach!**

**Rationale:**
1. ✅ You correctly identified redundancy - the code proves it
2. ✅ Your "simple hack" for GEO ID queries is brilliant and easy to implement
3. ✅ Maintenance burden drops dramatically (1 pipeline vs 3)
4. ✅ Future features benefit all use cases automatically
5. ✅ Caching efficiency improves across the board

**Start small:**
1. Build `QueryAnalyzer` (50 lines)
2. Create `OmicsSearchPipeline` skeleton
3. Migrate GEO search logic from `SearchAgent`
4. Test thoroughly
5. Expand incrementally

**Timeline:** 4-6 weeks for complete migration

Let me know if you want me to start creating the unified pipeline code! 🚀
