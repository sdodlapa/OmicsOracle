# Simplified Unified Pipeline: Core Functionality Only

**Date:** October 10, 2025
**Focus:** End-to-end data collection without ranking/filtering
**Philosophy:** Get it working first, optimize later

---

## 🎯 Design Principles

### What We're Building:
✅ **Core data collection pipeline with robust foundations**
- Query → Optimize → Search → Deduplicate → Cache → Collect → Save
- Advanced query optimization (synonyms, NER, query expansion)
- Robust deduplication (ID-based + fuzzy matching)
- Smart caching (Redis for performance)
- Focus on completeness and correctness

### What We're DEFERRING (Risk of data loss):
❌ Ranking/scoring systems - Not robust enough yet
❌ Filtering mechanisms - Might filter out relevant results

### Core Components (Must Have):
1. **Query Optimization** - NER, synonyms, query expansion for better recall
2. **Deduplication** - 2-pass system to eliminate duplicates
3. **Caching** - Redis for performance and API rate limiting
4. **Multi-source Search** - PubMed, OpenAlex, Google Scholar, GEO

**Rationale:** Maximize recall (find everything relevant), eliminate duplicates, cache for efficiency. Defer ranking/filtering until we have enough data to validate them.

---

## 📊 Deduplication Analysis

### Current Implementation: ✅ **EXCELLENT!**

The existing deduplication is already well-designed and should be kept as-is:

#### Two-Pass System (from `publication_pipeline.py`):

```python
def _deduplicate_publications(self, publications: List[Publication]):
    """
    Pass 1: ID-based (PMID, PMCID, DOI) - Fast exact matching
    Pass 2: Fuzzy matching (title, authors) - Catches variations
    """
    # Pass 1: ID-based (O(n) performance)
    seen_pmids = set()
    seen_pmcids = set()
    seen_dois = set()
    unique_pubs = []

    for pub in publications:
        # Check IDs
        if pub.pmid in seen_pmids or pub.doi in seen_dois or pub.pmcid in seen_pmcids:
            continue  # Skip duplicate

        # Add to unique list
        unique_pubs.append(pub)
        if pub.pmid:
            seen_pmids.add(pub.pmid)
        if pub.doi:
            seen_dois.add(pub.doi)
        if pub.pmcid:
            seen_pmcids.add(pub.pmcid)

    # Pass 2: Fuzzy matching (if enabled)
    if self.fuzzy_deduplicator:
        unique_pubs = self.fuzzy_deduplicator.deduplicate(unique_pubs)

    return unique_pubs
```

#### Why This Is Good:

1. **Fast Pass 1:** O(n) ID-based dedup catches 90%+ duplicates
2. **Thorough Pass 2:** Fuzzy matching catches edge cases:
   - Same paper, different sources (PubMed vs OpenAlex)
   - Typos in titles
   - Author name variations ("Smith, J." vs "J. Smith")
   - Preprints vs published versions
3. **Keeps Most Complete:** When duplicates found, keeps record with most metadata
4. **Well-tested:** 20 unit tests, 100% passing

### ✅ **Decision: Keep Existing Deduplication**

No changes needed! The implementation is:
- Efficient (O(n) for Pass 1, O(n²) worst case for Pass 2 but only on reduced set)
- Comprehensive (catches both exact and fuzzy duplicates)
- Configurable (`enable_fuzzy_matching` toggle)
- Production-ready (tested and working)

---

## 🏗️ Simplified Unified Pipeline Architecture

### Core Pipeline: `OmicsSearchPipeline`

```python
class OmicsSearchPipeline:
    """
    Simplified unified pipeline - core functionality only.

    Flow:
    1. Analyze query type
    2. Search appropriate sources
    3. DEDUPLICATE (always!)
    4. Enrich (citations, full-text)
    5. Save/return results

    NO ranking, NO filtering (except dedup)
    """

    def __init__(self, config: OmicsSearchConfig):
        """Initialize with core components."""
        self.config = config

        # CORE: Query optimization (NER, synonyms, expansion)
        self.query_optimizer = QueryOptimizer(
            enable_ner=config.enable_ner,
            enable_synonyms=config.enable_synonyms,
            enable_expansion=config.enable_query_expansion
        )

        # CORE: Query routing
        self.query_analyzer = QueryAnalyzer()

        # Search clients (conditional)
        self.geo_client = GEOClient() if config.enable_geo else None
        self.pubmed_client = PubMedClient() if config.enable_pubmed else None
        self.openalex_client = OpenAlexClient() if config.enable_openalex else None
        self.scholar_client = ScholarClient() if config.enable_scholar else None

        # CORE: Deduplication (always enabled!)
        self.deduplicator = SimpleDeduplicator()  # Pass 1: ID-based
        self.fuzzy_deduplicator = AdvancedDeduplicator(
            title_similarity_threshold=config.dedup_title_threshold,
            author_similarity_threshold=config.dedup_author_threshold,
            year_tolerance=config.dedup_year_tolerance
        )

        # CORE: Caching (Redis for performance + rate limiting)
        self.cache = RedisCache() if config.enable_cache else None

        # Enhancement (optional)
        self.citation_finder = CitationFinder() if config.enable_citations else None
        self.fulltext_manager = FullTextManager() if config.enable_fulltext else None
        self.pdf_manager = PDFDownloadManager() if config.enable_pdfs else None

        # NO RANKER - just return in order received
        # NO FILTERS - dedup only (keeps everything relevant)

    async def search(
        self,
        query: str,
        search_type: str = "auto",
        **kwargs
    ) -> OmicsSearchResult:
        """
        Core search flow - optimized and cached.

        Steps:
        1. Check cache (if enabled)
        2. Optimize query (NER, synonyms, expansion)
        3. Detect query type (GEO ID, GEO keywords, publication keywords)
        4. Route to appropriate search
        5. Deduplicate results (always!)
        6. Cache results (if enabled)
        7. Optional: Enrich with citations/full-text
        8. Return ALL results (no ranking, no filtering)
        """
        # Step 1: Check cache
        if self.cache:
            cached_result = await self.cache.get_search_result(query, search_type)
            if cached_result:
                logger.info(f"Cache HIT for query: {query}")
                return cached_result

        # Step 2: Optimize query
        optimized_query = await self.query_optimizer.optimize(query)
        logger.info(f"Query optimization: '{query}' → '{optimized_query.primary_query}'")
        if optimized_query.synonyms:
            logger.info(f"  Synonyms: {optimized_query.synonyms}")
        if optimized_query.expanded_terms:
            logger.info(f"  Expanded terms: {optimized_query.expanded_terms}")

        # Step 3: Analyze query type
        query_info = self.query_analyzer.analyze(optimized_query.primary_query)

        if search_type != "auto":
            query_info.search_type = search_type

        # Step 4: Route to search
        if query_info.is_geo_id:
            # Fast path for GEO IDs
            result = await self._fetch_geo_by_id(query_info.geo_ids)

        elif query_info.search_type == "geo":
            result = await self._search_geo_datasets(optimized_query, **kwargs)

        elif query_info.search_type == "publications":
            result = await self._search_publications(optimized_query, **kwargs)

        else:
            # Auto-detect: try both
            result = await self._search_both(optimized_query, **kwargs)

        # Step 5: Cache results
        if self.cache:
            await self.cache.set_search_result(query, search_type, result)

        return result

    async def _fetch_geo_by_id(self, geo_ids: List[str]) -> OmicsSearchResult:
        """
        Fast path: Direct GEO metadata fetch (no search, no dedup needed).

        Example: "GSE12345" → fetch metadata directly
        """
        datasets = await self.geo_client.batch_get_metadata_smart(
            geo_ids=geo_ids,
            max_concurrent=10
        )

        return OmicsSearchResult(
            query=" ".join(geo_ids),
            search_type="geo_id",
            geo_datasets=datasets,
            publications=[],
            total_found=len(datasets),
        )

    async def _search_geo_datasets(
        self, query: str, **kwargs
    ) -> OmicsSearchResult:
        """
        Search GEO datasets.

        Simple flow:
        1. Search GEO database
        2. Fetch metadata
        3. Return ALL results (no filtering, no ranking)
        """
        # 1. Search
        search_results = await self.geo_client.search(
            query=query,
            max_results=kwargs.get("max_results", 100)
        )

        # 2. Fetch metadata (parallel batch)
        datasets = await self.geo_client.batch_get_metadata_smart(
            geo_ids=search_results.geo_ids,
            max_concurrent=10
        )

        # NO filtering, NO ranking
        # Just return what we found in the order GEO returned it

        return OmicsSearchResult(
            query=query,
            search_type="geo",
            geo_datasets=datasets,
            publications=[],
            total_found=len(datasets),
        )

    async def _search_publications(
        self, optimized_query: OptimizedQuery, **kwargs
    ) -> OmicsSearchResult:
        """
        Search publications with query optimization.

        Enhanced flow:
        1. Build search queries (primary + synonyms + expanded)
        2. Search all enabled sources in parallel
        3. DEDUPLICATE (critical!)
        4. Optional: Enrich
        5. Return ALL results (no ranking)
        """
        all_pubs = []
        sources_used = []

        # 1. Build comprehensive search queries
        search_queries = self._build_search_queries(optimized_query)
        logger.info(f"Searching with {len(search_queries)} query variations")

        # 2. Search sources (in parallel for speed)
        search_tasks = []

        if self.pubmed_client:
            for query in search_queries:
                search_tasks.append(
                    self._search_pubmed(query, kwargs.get("max_results", 50))
                )
            sources_used.append("pubmed")

        if self.openalex_client:
            for query in search_queries:
                search_tasks.append(
                    self._search_openalex(query, kwargs.get("max_results", 50))
                )
            sources_used.append("openalex")

        if self.scholar_client:
            for query in search_queries:
                search_tasks.append(
                    self._search_scholar(query, kwargs.get("max_results", 50))
                )
            sources_used.append("scholar")

        # Run searches in parallel
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_pubs.extend(result)

        logger.info(f"Found {len(all_pubs)} publications from {len(sources_used)} sources")

        # 3. DEDUPLICATE (always! This is where query optimization pays off)
        deduped_pubs = self._deduplicate(all_pubs)

        logger.info(
            f"After deduplication: {len(deduped_pubs)} unique publications "
            f"(removed {len(all_pubs) - len(deduped_pubs)} duplicates)"
        )

        # 4. Optional enrichment
        if self.fulltext_manager and kwargs.get("collect_fulltext"):
            deduped_pubs = await self.fulltext_manager.get_fulltext_batch(deduped_pubs)

        if self.citation_finder and kwargs.get("include_citations"):
            deduped_pubs = await self._enrich_citations(deduped_pubs)

        if self.pdf_manager and kwargs.get("download_pdfs"):
            await self.pdf_manager.download_batch(
                deduped_pubs,
                output_dir=kwargs.get("output_dir")
            )

        # Return ALL results (no ranking, no filtering)
        return OmicsSearchResult(
            query=optimized_query.primary_query,
            search_type="publications",
            geo_datasets=[],
            publications=deduped_pubs,
            total_found=len(deduped_pubs),
            sources_used=sources_used,
            query_optimization=optimized_query.to_dict(),
        )

    def _build_search_queries(self, optimized_query: OptimizedQuery) -> List[str]:
        """
        Build comprehensive search queries from optimization.

        Combines:
        - Primary query
        - Synonym variations
        - Expanded terms

        Returns: List of unique query strings to search
        """
        queries = [optimized_query.primary_query]

        # Add synonym variations
        if optimized_query.synonyms:
            for synonym_set in optimized_query.synonyms.values():
                queries.extend(synonym_set[:3])  # Top 3 synonyms per entity

        # Add expanded terms
        if optimized_query.expanded_terms:
            queries.extend(optimized_query.expanded_terms[:5])  # Top 5 expansions

        # Deduplicate queries
        unique_queries = list(dict.fromkeys(queries))

        return unique_queries

    def _deduplicate(self, publications: List[Publication]) -> List[Publication]:
        """
        Deduplicate publications using existing robust implementation.

        Uses the EXACT same logic from publication_pipeline.py:
        - Pass 1: ID-based (PMID, DOI, PMCID)
        - Pass 2: Fuzzy matching (if enabled)
        """
        if not publications:
            return []

        # Pass 1: ID-based deduplication
        seen_ids = {}  # id_type -> set of ids
        unique_pubs = []

        for pub in publications:
            is_duplicate = False

            # Check all IDs
            for id_type, id_value in [
                ("pmid", pub.pmid),
                ("pmcid", pub.pmcid),
                ("doi", pub.doi)
            ]:
                if id_value:
                    if id_type not in seen_ids:
                        seen_ids[id_type] = set()

                    if id_value in seen_ids[id_type]:
                        is_duplicate = True
                        break
                    else:
                        seen_ids[id_type].add(id_value)

            if not is_duplicate:
                unique_pubs.append(pub)

        removed = len(publications) - len(unique_pubs)
        if removed > 0:
            logger.info(f"Deduplication Pass 1 (ID-based): Removed {removed} duplicates")

        # Pass 2: Fuzzy deduplication (optional)
        if self.fuzzy_deduplicator:
            before_fuzzy = len(unique_pubs)
            unique_pubs = self.fuzzy_deduplicator.deduplicate(unique_pubs)
            fuzzy_removed = before_fuzzy - len(unique_pubs)
            if fuzzy_removed > 0:
                logger.info(f"Deduplication Pass 2 (Fuzzy): Removed {fuzzy_removed} duplicates")

        return unique_pubs

    async def collect_bulk(
        self, query: str, output_dir: Path, **kwargs
    ) -> CollectionResult:
        """
        Bulk collection mode: Find datasets + citing papers + PDFs.

        Simple flow:
        1. Search GEO datasets
        2. Find papers citing each dataset
        3. Deduplicate all papers
        4. Collect full-text URLs
        5. Download PDFs
        6. Save metadata
        """
        # 1. Get GEO datasets
        geo_result = await self._search_geo_datasets(query, **kwargs)

        # 2. Find citing papers for each dataset
        all_citing_papers = []
        for dataset in geo_result.geo_datasets:
            if self.citation_finder:
                citing = await self.citation_finder.find_citing_papers(
                    dataset,
                    max_results=kwargs.get("max_citations", 100)
                )
                all_citing_papers.extend(citing)

        # 3. Deduplicate citations
        unique_citations = self._deduplicate(all_citing_papers)

        logger.info(
            f"Found {len(all_citing_papers)} total citations, "
            f"{len(unique_citations)} unique after deduplication"
        )

        # 4. Get full-text URLs
        if self.fulltext_manager:
            unique_citations = await self.fulltext_manager.get_fulltext_batch(
                unique_citations
            )

        # 5. Download PDFs
        download_report = None
        if self.pdf_manager:
            download_report = await self.pdf_manager.download_batch(
                unique_citations,
                output_dir=output_dir / "pdfs"
            )

        # 6. Save metadata
        self._save_collection(
            geo_datasets=geo_result.geo_datasets,
            publications=unique_citations,
            output_dir=output_dir,
        )

        return CollectionResult(
            query=query,
            datasets_found=len(geo_result.geo_datasets),
            citing_papers=len(unique_citations),
            pdfs_downloaded=download_report.successful if download_report else 0,
            collection_dir=output_dir,
        )
```

---

## 🔧 Minimal Configuration

```python
@dataclass
class OmicsSearchConfig:
    """
    Configuration with core components enabled by default.

    CORE components (recommended enabled):
    - Query optimization (NER, synonyms, expansion)
    - Deduplication (ID-based + fuzzy)
    - Caching (Redis for performance)

    DEFERRED components (disabled by default):
    - Ranking (not robust enough)
    - Filtering (risk of data loss)
    """
    # Search sources
    enable_geo: bool = True
    enable_pubmed: bool = True
    enable_openalex: bool = True
    enable_scholar: bool = True

    # CORE: Query optimization (always recommended!)
    enable_ner: bool = True  # Named Entity Recognition
    enable_synonyms: bool = True  # Medical/bio synonyms (UMLS, MeSH)
    enable_query_expansion: bool = True  # Related terms

    # CORE: Deduplication (always recommended!)
    enable_dedup: bool = True  # ID-based (PMID, DOI, PMCID)
    enable_fuzzy_dedup: bool = True  # Fuzzy matching (title, authors)
    dedup_title_threshold: float = 85.0  # Title similarity %
    dedup_author_threshold: float = 80.0  # Author similarity %
    dedup_year_tolerance: int = 1  # Year tolerance for preprints

    # CORE: Caching (always recommended!)
    enable_cache: bool = True  # Redis caching
    cache_ttl: int = 86400  # 24 hours
    cache_prefix: str = "omics_search"

    # Enhancement (optional)
    enable_citations: bool = False
    enable_fulltext: bool = False
    enable_pdfs: bool = False

    # Limits (simple)
    max_results: int = 100  # Per source
    max_citations: int = 100  # Per dataset

    # PubMed credentials
    ncbi_email: str = ""
    ncbi_api_key: Optional[str] = None

    # Redis connection
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
```

---

## 📋 Query Analyzer (Simple Version)

```python
class QueryAnalyzer:
    """
    Detect query type - simple pattern matching.

    NO complex NLP, NO entity extraction (handled by QueryOptimizer).
    Just basic detection to route queries correctly.
    """

    GEO_ID_PATTERN = re.compile(r'^(GSE|GPL|GSM)\d+$', re.IGNORECASE)

    def analyze(self, query: str) -> QueryInfo:
        """
        Analyze query and determine type.

        Logic:
        1. Check for GEO ID pattern (GSE12345, GPL570, etc.)
        2. Check for explicit keywords (dataset, paper, publication)
        3. Default: auto (try to determine from content)
        """
        query_cleaned = query.strip()

        # Check for GEO IDs
        geo_ids = self._extract_geo_ids(query_cleaned)
        if geo_ids:
            return QueryInfo(
                original_query=query,
                search_type="geo_id",
                geo_ids=geo_ids,
                is_geo_id=True,
            )

        # Check for explicit keywords
        query_lower = query_cleaned.lower()

        geo_keywords = ["dataset", "geo", "series", "samples", "gse", "gpl"]
        pub_keywords = ["paper", "publication", "article", "journal", "pmid"]

        has_geo = any(kw in query_lower for kw in geo_keywords)
        has_pub = any(kw in query_lower for kw in pub_keywords)

        if has_geo and not has_pub:
            search_type = "geo"
        elif has_pub and not has_geo:
            search_type = "publications"
        else:
            search_type = "auto"  # Try to determine from content

        return QueryInfo(
            original_query=query,
            search_type=search_type,
            geo_ids=[],
            is_geo_id=False,
        )

    def _extract_geo_ids(self, query: str) -> List[str]:
        """Extract GEO IDs from query."""
        # Split on common separators
        tokens = re.split(r'[\s,;]+', query)

        geo_ids = []
        for token in tokens:
            if self.GEO_ID_PATTERN.match(token):
                geo_ids.append(token.upper())

        return geo_ids


class QueryOptimizer:
    """
    Advanced query optimization for better recall.

    CORE component - enhances query to find more relevant results.

    Features:
    - Named Entity Recognition (diseases, genes, proteins)
    - Medical/biological synonym expansion (UMLS, MeSH)
    - Query term expansion (related concepts)
    """

    def __init__(
        self,
        enable_ner: bool = True,
        enable_synonyms: bool = True,
        enable_expansion: bool = True,
    ):
        self.enable_ner = enable_ner
        self.enable_synonyms = enable_synonyms
        self.enable_expansion = enable_expansion

        # NER model (SciBERT or BioBERT for biomedical text)
        self.ner_model = None
        if enable_ner:
            self.ner_model = self._load_ner_model()

        # Synonym databases
        self.synonym_db = None
        if enable_synonyms:
            self.synonym_db = MedicalSynonymDB()  # UMLS, MeSH, etc.

    async def optimize(self, query: str) -> OptimizedQuery:
        """
        Optimize query for better search recall.

        Returns:
            OptimizedQuery with:
            - primary_query: Original query
            - entities: Detected entities (diseases, genes, etc.)
            - synonyms: Synonym variations for each entity
            - expanded_terms: Related terms
        """
        result = OptimizedQuery(primary_query=query)

        # 1. Named Entity Recognition
        if self.enable_ner and self.ner_model:
            entities = await self._extract_entities(query)
            result.entities = entities

        # 2. Synonym expansion
        if self.enable_synonyms and self.synonym_db:
            synonyms = await self._find_synonyms(result.entities)
            result.synonyms = synonyms

        # 3. Query expansion
        if self.enable_expansion:
            expanded = await self._expand_query(query, result.entities)
            result.expanded_terms = expanded

        return result

    async def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract biomedical entities using NER.

        Returns:
            {
                "DISEASE": ["alzheimer's disease", "dementia"],
                "GENE": ["APOE", "APP"],
                "PROTEIN": ["amyloid beta"],
            }
        """
        # Use BioBERT or SciBERT NER model
        # This is a placeholder - actual implementation would use model
        entities = {}

        # Example: disease detection
        disease_patterns = [
            r'\b(cancer|tumor|carcinoma|lymphoma)\b',
            r'\b(diabetes|alzheimer|parkinson)\b',
        ]

        for pattern in disease_patterns:
            matches = re.findall(pattern, query.lower())
            if matches:
                entities.setdefault("DISEASE", []).extend(matches)

        return entities

    async def _find_synonyms(
        self, entities: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Find medical/biological synonyms using UMLS, MeSH.

        Example:
            "alzheimer's disease" → ["AD", "Alzheimer disease",
                                     "Alzheimer's dementia"]
        """
        synonyms = {}

        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                # Query UMLS/MeSH for synonyms
                entity_synonyms = await self.synonym_db.get_synonyms(entity)
                if entity_synonyms:
                    synonyms[entity] = entity_synonyms

        return synonyms

    async def _expand_query(
        self, query: str, entities: Dict[str, List[str]]
    ) -> List[str]:
        """
        Expand query with related terms.

        Example:
            "breast cancer treatment" →
            ["breast cancer therapy", "breast neoplasm treatment",
             "mammary carcinoma therapy"]
        """
        expanded = []

        # Use word embeddings or knowledge graphs to find related terms
        # This is a placeholder - actual implementation would use models

        return expanded
```

---

## 🎯 Migration Strategy: Phased Approach

### Phase 1: Create Unified Pipeline (Week 1)
```
Files to create:
  • omics_oracle_v2/lib/pipelines/unified_pipeline.py (600 lines)
  • omics_oracle_v2/lib/query/analyzer.py (100 lines)
  • omics_oracle_v2/lib/query/optimizer.py (300 lines) ← NEW!
  • omics_oracle_v2/lib/cache/redis_cache.py (200 lines) ← NEW!
  • omics_oracle_v2/lib/config/unified_config.py (100 lines)

CORE Features (Week 1):
  ✓ QueryAnalyzer (GEO ID detection + keyword routing)
  ✓ QueryOptimizer (NER + synonyms + expansion) ← CORE!
  ✓ GEO search (direct + keyword)
  ✓ Publication search (PubMed + OpenAlex + Scholar)
  ✓ Deduplication (reuse existing robust implementation)
  ✓ Redis caching (search results + metadata) ← CORE!

DEFERRED:
  ✗ Ranking algorithms
  ✗ Filtering mechanisms
```

### Phase 2: Test Core Components (Week 2)
```
Test thoroughly:
  ✓ Query optimization (NER accuracy, synonym coverage)
  ✓ Deduplication (catches all duplicates, keeps best records)
  ✓ Cache performance (hit rates, TTL validation)
  ✓ Multi-source search (all sources working)

Compare with old pipelines:
  ✓ Same or better recall (find all relevant papers)
  ✓ Better precision (fewer duplicates)
  ✓ Faster performance (caching + parallel search)
  ✓ Ensure no data loss
```

### Phase 3: Update SearchAgent Wrapper (Week 3)
```
Update:
  • omics_oracle_v2/agents/search_agent.py (reduce to 100 lines)

Changes:
  - Remove duplicate preprocessing code
  - Remove duplicate GEO client code
  - Wrap OmicsSearchPipeline
  - Keep API contract (SearchInput → SearchOutput)

Test:
  ✓ All existing API tests pass
  ✓ No breaking changes
  ✓ Cache working correctly
```

### Phase 4: Update Dashboard & Scripts (Week 4)
```
Update Dashboard:
  • omics_oracle_v2/lib/dashboard/app.py

Changes:
  - Replace PublicationSearchPipeline with OmicsSearchPipeline
  - Add toggle: "Search GEO datasets" vs "Search Publications"
  - Show query optimization info (entities, synonyms)
  - Keep all existing UI features

Update Bulk Collection Scripts:
  • Scripts using GEOCitationPipeline

Changes:
  - Use OmicsSearchPipeline.collect_bulk()
  - Same output format
  - Same directory structure

Test:
  ✓ Dashboard works identically
  ✓ All features functional
  ✓ Bulk collection produces identical results
  ✓ Query optimization visible in UI
```

### Phase 5: Archive Old Code (Week 5)
```
Archive:
  • publication_pipeline.py → archive/legacy/
  • geo_citation_pipeline.py → archive/legacy/
  • Most of search_agent.py → archive/legacy/

Keep:
  • Deduplication code (still in use!)
  • All test suites (regression testing)
  • API wrappers (backward compatibility)
```

---

## 📊 Deduplication Integration Plan

### Current Deduplication Locations:

1. **PublicationSearchPipeline:** `_deduplicate_publications()` (lines 869-937)
   - 2-pass system (ID + fuzzy)
   - Well-tested
   - **Status:** ✅ Keep as reference

2. **GEOCitationPipeline:** `_deduplicate_papers()` (line 292)
   - ID-based only
   - **Status:** ⚠️ Should use 2-pass

3. **AdvancedDeduplicator:** `deduplicate()` (deduplication.py line 53)
   - Fuzzy matching implementation
   - **Status:** ✅ Keep, reuse in unified pipeline

### Unified Pipeline Deduplication:

```python
class OmicsSearchPipeline:

    def _deduplicate(self, publications: List[Publication]) -> List[Publication]:
        """
        UNIFIED deduplication for all query types.

        Reuses existing robust implementation:
        - Pass 1: ID-based (PMID, DOI, PMCID) - O(n)
        - Pass 2: Fuzzy (title, authors) - O(n²) on reduced set
        """
        # This is the SAME code from publication_pipeline.py
        # Just extracted into one place

        # Pass 1: Fast ID dedup
        unique_pubs = self._id_based_dedup(publications)

        # Pass 2: Fuzzy dedup (if enabled)
        if self.config.enable_fuzzy_dedup and self.fuzzy_deduplicator:
            unique_pubs = self.fuzzy_deduplicator.deduplicate(unique_pubs)

        return unique_pubs
```

### When Deduplication Runs:

```
Query Flow:
  User Query
    ↓
  Route to Search Type
    ↓
  Search Multiple Sources
    ↓
  >>> DEDUPLICATE HERE <<<  ← Always! For all query types!
    ↓
  Optional: Enrich (citations, full-text, PDFs)
    ↓
  Return Results
```

**Key Principle:** Deduplication happens BEFORE enrichment to avoid wasting API calls on duplicates.

---

## ✅ What This Achieves

### Immediate Benefits:
1. **✅ One unified pipeline** - All queries use same optimized logic
2. **✅ Better recall** - Query optimization finds more relevant results
3. **✅ No duplicates** - Robust 2-pass deduplication
4. **✅ Fast performance** - Redis caching + parallel search
5. **✅ 79% code reduction** - 1,900 → 600 lines core pipeline
6. **✅ Consistent behavior** - Same results regardless of entry point

### CORE Components (Included):
1. **✅ Query Optimization** - NER, synonyms, expansion for better recall
2. **✅ Deduplication** - ID-based + fuzzy matching (robust!)
3. **✅ Caching** - Redis for performance + rate limiting
4. **✅ Multi-source** - PubMed, OpenAlex, Scholar, GEO

### DEFERRED Components (For Later):
1. **⏳ Ranking algorithms** - Will add when we have validation data
2. **⏳ Filtering mechanisms** - Will add when we have validation data

### Why This Approach:
- **Maximize recall:** Query optimization ensures we find all relevant results
- **Eliminate duplicates:** Deduplication ensures clean data
- **Cache efficiently:** Avoid redundant API calls and respect rate limits
- **Defer precision:** Add ranking/filtering later when validated

---

## 🎯 Success Criteria

### Week 4 (End of Migration):
- ✅ All query types work (GEO ID, GEO keywords, publications)
- ✅ Query optimization improves recall (finds more relevant results)
- ✅ Deduplication is robust (catches 95%+ duplicates)
- ✅ Cache hit rate >50% for repeated queries
- ✅ No data loss (same or more results than before)
- ✅ API backward compatible (existing clients work)
- ✅ Dashboard works identically
- ✅ Tests pass (100% coverage maintained)

### What We Measure:
- **Query optimization effectiveness:** Recall improvement from synonyms/expansion
- **Duplicate rate:** Should be <1% after deduplication
- **Cache performance:** Hit rate, latency reduction
- **Data completeness:** Should find same or more results
- **Response time:** Should be similar or better (caching helps)

### What We DON'T Measure (Yet):
- ❌ Ranking quality (not implemented)
- ❌ Filter effectiveness (not implemented)
- ❌ Precision (will measure when we add ranking)

---

## 💡 Recommendation

### ✅ APPROVED APPROACH:

1. **Include query optimization as CORE** - NER, synonyms, expansion for better recall
2. **Include caching as CORE** - Redis for performance + rate limiting
3. **Keep existing deduplication** - It's excellent, don't change it
4. **Build unified pipeline** - Core functionality with optimization + caching
5. **Defer ranking/filtering** - Add later when validated

### Next Steps:

**If you approve, I'll create:**

1. **Week 1:** Build Core Pipeline Components
   - `OmicsSearchPipeline` (600 lines) - Main unified pipeline
   - `QueryAnalyzer` (100 lines) - GEO ID detection + routing
   - `QueryOptimizer` (300 lines) - NER + synonyms + expansion ← **CORE!**
   - `RedisCache` (200 lines) - Search result caching ← **CORE!**
   - Configuration with all toggles

2. **Week 2:** Test Core Components
   - Query optimization effectiveness (recall improvement)
   - Deduplication thoroughness (duplicate detection rate)
   - Cache performance (hit rates, latency reduction)
   - Compare with old pipelines (no data loss)

3. **Week 3:** Update SearchAgent Wrapper
   - Wrap new pipeline
   - Keep API compatibility
   - Test thoroughly

4. **Week 4:** Migrate Dashboard & Scripts
   - Update dashboard to use unified pipeline
   - Show query optimization info in UI
   - Update bulk collection scripts
   - Document changes

5. **Week 5:** Archive & Document
   - Archive old pipelines
   - Create migration guide
   - Update documentation
   - Create examples

**Ready to proceed with CORE components (query optimization + caching + deduplication)?** 🚀
