# Pipeline 1 Enhancement Plan: Robust Citation Discovery

**Date:** October 14, 2025  
**Goal:** Make Pipeline 1 (Citation Discovery) more robust, accurate, and comprehensive  
**Current Status:** 2 sources (PubMed + OpenAlex), basic strategies  
**Target:** Multi-source, intelligent, resilient citation discovery

---

## 🎯 Executive Summary

### Current State (Pipeline 1)
- **Sources:** 2 (PubMed, OpenAlex)
- **Strategies:** 2 (citation-based, mention-based)
- **Weaknesses:** Limited coverage, no fallback, basic deduplication, no relevance scoring

### Proposed Enhancements (7 Major Areas)
1. **Add More Discovery Sources** (4 new sources)
2. **Intelligent Strategy Selection** (adaptive algorithms)
3. **Advanced Deduplication & Merging** (smart conflict resolution)
4. **Relevance Scoring & Ranking** (ML-based scoring)
5. **Robust Error Handling** (retry, fallback, partial success)
6. **Caching & Performance** (avoid re-discovery)
7. **Quality Validation** (filter false positives)

---

## 📊 Current Architecture Analysis

### Strengths ✅
1. **Clean separation of concerns** (discovery vs URL collection)
2. **Two complementary strategies** (citation graph + text search)
3. **Async support** (ready for parallel operations)
4. **Configurable** (can enable/disable strategies)
5. **Good logging** (debuggable)

### Weaknesses ❌
1. **Limited sources** (only 2 discovery sources)
2. **No fallback** (if OpenAlex fails, no citation discovery)
3. **Basic deduplication** (uses Python sets, no intelligent merging)
4. **No relevance scoring** (all papers treated equally)
5. **No validation** (accepts all results without quality checks)
6. **No caching** (re-discovers same papers every time)
7. **Synchronous PubMed** (not truly async)
8. **Only uses first PMID** (ignores additional PMIDs)
9. **No GEO accession variations** (GSE123, GSE000123)
10. **No citation context extraction** (why paper cited dataset)

---

## 🚀 Enhancement 1: Add More Discovery Sources

### New Sources to Add

#### 1.1. Semantic Scholar (Priority: HIGH)
**Status:** Used to exist in codebase, was deleted  
**Why add back:** 
- 200M+ papers, strong in CS/biology
- Citation graph with influence scores
- Paper recommendations (similar papers)
- Free API (100 req/sec)

**Implementation:**
```python
class SemanticScholarClient:
    """
    Semantic Scholar API client for citation discovery.
    API: https://api.semanticscholar.org/
    """
    
    async def get_citing_papers(self, doi: str, max_results: int = 100):
        """Get papers that cite this work"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/citations"
        params = {
            "fields": "title,authors,year,citationCount,isOpenAccess,url",
            "limit": max_results
        }
        # Returns papers WITH influence scores
        
    async def search_by_doi(self, doi: str):
        """Get paper details by DOI"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        
    async def get_recommendations(self, doi: str, max_results: int = 10):
        """Get similar/related papers (uses ML)"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/recommendations"
```

**Benefits:**
- Influence scores (know which citations are important)
- Recommendations (find related papers not citing directly)
- Fast API (100 req/sec)
- Good for CS + biology papers

**Integration:**
```python
# geo_discovery.py

def _find_via_citation(self, pmid: str, max_results: int):
    results = []
    
    # Try OpenAlex first
    openalex_results = self.openalex.get_citing_papers(doi, max_results)
    results.extend(openalex_results)
    
    # Try Semantic Scholar as fallback/supplement
    if self.semantic_scholar:
        s2_results = await self.semantic_scholar.get_citing_papers(doi, max_results)
        results.extend(s2_results)
    
    return self._deduplicate(results)
```

---

#### 1.2. Crossref (Priority: MEDIUM)
**API:** https://api.crossref.org/  
**Coverage:** 140M+ records (DOIs, journal metadata)  
**Use case:** Find papers via reference metadata

**Implementation:**
```python
class CrossrefClient:
    """Crossref API for citation metadata"""
    
    async def get_works_that_reference(self, doi: str, max_results: int = 100):
        """Get works that reference this DOI"""
        url = f"https://api.crossref.org/works/{doi}"
        # Check "is-referenced-by-count"
        
    async def search_by_geo_id(self, geo_id: str, max_results: int = 100):
        """Search Crossref full-text for GEO ID mentions"""
        url = "https://api.crossref.org/works"
        params = {"query": geo_id, "rows": max_results}
```

**Benefits:**
- Authoritative DOI registry
- Publisher metadata
- No API key needed (polite pool with email)

---

#### 1.3. Europe PMC (Priority: MEDIUM)
**API:** https://europepmc.org/RestfulWebService  
**Coverage:** 40M+ life sciences papers  
**Use case:** Life sciences focused search

**Implementation:**
```python
class EuropePMCClient:
    """Europe PMC API for life sciences papers"""
    
    async def search(self, query: str, max_results: int = 100):
        """Search Europe PMC"""
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {
            "query": query,
            "format": "json",
            "pageSize": max_results
        }
        
    async def get_citations(self, pmid: str, max_results: int = 100):
        """Get papers citing this PMID"""
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations"
```

**Benefits:**
- Life sciences focus (good for GEO datasets)
- Free full-text search
- Citation data
- Alternative to PubMed

---

#### 1.4. Dimensions AI (Priority: LOW - Requires Subscription)
**API:** https://app.dimensions.ai/  
**Coverage:** 130M+ publications, grants, patents  
**Use case:** Comprehensive citation data

**Note:** Requires institutional access or subscription

---

### Source Priority Matrix

| Source | Coverage | Free | Rate Limit | Citation Graph | Text Search | Priority |
|--------|----------|------|------------|----------------|-------------|----------|
| **OpenAlex** | 250M+ | ✅ | 10/sec | ✅ | ✅ | **HIGH** |
| **PubMed** | 35M+ | ✅ | 10/sec* | ❌ | ✅ | **HIGH** |
| **Semantic Scholar** | 200M+ | ✅ | 100/sec | ✅ | ✅ | **HIGH** |
| **Crossref** | 140M+ | ✅ | 50/sec | ✅ | ⚠️ | **MEDIUM** |
| **Europe PMC** | 40M+ | ✅ | No limit | ✅ | ✅ | **MEDIUM** |
| **Dimensions** | 130M+ | ❌ | Varies | ✅ | ✅ | **LOW** |

*with API key

**Recommendation:** Add Semantic Scholar (HIGH), Europe PMC (MEDIUM), Crossref (MEDIUM)

---

## 🧠 Enhancement 2: Intelligent Strategy Selection

### Current Strategy
```python
# Fixed strategies - always runs both
if self.use_strategy_a:
    results_a = self._find_via_citation(pmid)
if self.use_strategy_b:
    results_b = self._find_via_geo_mention(geo_id)
```

### Problem
- Wastes API calls on low-quality sources
- No adaptation based on results
- No early stopping

### Proposed: Adaptive Strategy System

```python
class StrategySelector:
    """
    Intelligently selects and prioritizes discovery strategies.
    """
    
    async def select_strategies(self, geo_metadata: GEOSeriesMetadata) -> List[Strategy]:
        """
        Select optimal strategies based on dataset characteristics.
        
        Decision factors:
        - Dataset age (newer → more citations expected)
        - Original paper quality (high impact → more citations)
        - Field (CS papers → Semantic Scholar, bio → PubMed)
        - Previous success rate (cached statistics)
        """
        strategies = []
        
        # Strategy A: Citation-based (if has PMID + DOI)
        if geo_metadata.pubmed_ids and self._has_doi(geo_metadata.pubmed_ids[0]):
            strategies.append(
                Strategy(
                    name="citation_openalex",
                    method=self._find_via_citation_openalex,
                    priority=1,
                    expected_results=self._estimate_citations(geo_metadata),
                    cost=1,  # API calls
                )
            )
        
        # Strategy B: Mention-based (always available)
        strategies.append(
            Strategy(
                name="mention_pubmed",
                method=self._find_via_mention_pubmed,
                priority=2,
                expected_results=self._estimate_mentions(geo_metadata),
                cost=1,
            )
        )
        
        # Strategy C: Semantic Scholar (if DOI available)
        if self._has_doi(geo_metadata.pubmed_ids[0]):
            strategies.append(
                Strategy(
                    name="citation_s2",
                    method=self._find_via_citation_s2,
                    priority=1,  # Same priority as OpenAlex
                    expected_results=self._estimate_citations(geo_metadata) * 0.8,
                    cost=1,
                )
            )
        
        # Sort by priority and expected value
        strategies.sort(key=lambda s: (s.priority, -s.expected_results))
        
        return strategies
```

### Waterfall Execution with Early Stopping

```python
async def find_citing_papers_adaptive(
    self, 
    geo_metadata: GEOSeriesMetadata, 
    max_results: int = 100,
    min_results: int = 10
) -> CitationDiscoveryResult:
    """
    Adaptive citation discovery with early stopping.
    """
    strategies = await self.strategy_selector.select_strategies(geo_metadata)
    
    all_papers = set()
    strategy_results = {}
    
    for strategy in strategies:
        logger.info(f"Trying strategy: {strategy.name} (expect ~{strategy.expected_results} results)")
        
        try:
            results = await strategy.method(geo_metadata, max_results)
            strategy_results[strategy.name] = len(results)
            all_papers.update(results)
            
            logger.info(f"  ✓ {strategy.name}: {len(results)} results (total: {len(all_papers)})")
            
            # Early stopping conditions
            if len(all_papers) >= max_results:
                logger.info(f"  → Reached max_results ({max_results}), stopping")
                break
                
            if len(all_papers) >= min_results and strategy.priority > 1:
                logger.info(f"  → Got minimum results ({min_results}), skipping lower priority")
                break
                
        except Exception as e:
            logger.error(f"  ✗ {strategy.name} failed: {e}")
            continue
    
    return CitationDiscoveryResult(
        geo_id=geo_metadata.geo_id,
        citing_papers=list(all_papers),
        strategy_breakdown=strategy_results,
        strategy_order=[s.name for s in strategies]
    )
```

**Benefits:**
- Adaptive to dataset characteristics
- Early stopping saves API calls
- Prioritizes high-value sources
- Graceful degradation on failures

---

## 🔀 Enhancement 3: Advanced Deduplication & Merging

### Current Deduplication
```python
# Simple set-based deduplication
all_papers: Set[Publication] = set()
for paper in citing_via_pmid:
    all_papers.add(paper)  # Uses Publication.__hash__
```

**Problem:**
- Only removes exact duplicates
- Doesn't merge partial data (one source has PMID, other has DOI)
- No conflict resolution (different abstracts from different sources)

### Proposed: Intelligent Deduplication

```python
class PublicationDeduplicator:
    """
    Intelligently deduplicate and merge publications from multiple sources.
    """
    
    def deduplicate_and_merge(self, publications: List[Publication]) -> List[Publication]:
        """
        Deduplicate using multiple identifiers and merge metadata.
        
        Deduplication keys (in order of preference):
        1. DOI (most reliable)
        2. PMID (PubMed ID)
        3. Title + First author + Year (fuzzy match)
        """
        # Group by DOI
        doi_groups = self._group_by_doi(publications)
        
        # Group by PMID
        pmid_groups = self._group_by_pmid(publications)
        
        # Fuzzy match remaining papers
        title_groups = self._fuzzy_group_by_title(publications)
        
        # Merge groups
        merged = []
        for group in self._merge_groups(doi_groups, pmid_groups, title_groups):
            merged_pub = self._merge_publications(group)
            merged.append(merged_pub)
        
        return merged
    
    def _merge_publications(self, publications: List[Publication]) -> Publication:
        """
        Merge multiple publication records into one, resolving conflicts.
        
        Conflict resolution rules:
        - Prefer DOI from most authoritative source (Crossref > OpenAlex)
        - Prefer PMID from PubMed
        - Take longest abstract
        - Merge author lists (union)
        - Prefer most recent metadata
        - Average citation counts
        """
        if len(publications) == 1:
            return publications[0]
        
        # Source authority ranking
        source_priority = {
            PublicationSource.PUBMED: 1,
            PublicationSource.OPENALEX: 2,
            PublicationSource.SEMANTIC_SCHOLAR: 3,
            PublicationSource.CROSSREF: 4,
        }
        
        # Sort by source authority
        pubs = sorted(publications, key=lambda p: source_priority.get(p.source, 99))
        
        # Start with most authoritative
        merged = pubs[0]
        
        # Merge data from other sources
        for pub in pubs[1:]:
            # Take DOI from most authoritative
            if pub.doi and not merged.doi:
                merged.doi = pub.doi
            
            # Take PMID preferably from PubMed
            if pub.pmid and pub.source == PublicationSource.PUBMED:
                merged.pmid = pub.pmid
            
            # Take longest abstract
            if pub.abstract and len(pub.abstract) > len(merged.abstract or ""):
                merged.abstract = pub.abstract
            
            # Merge authors (union, preserve order)
            if pub.authors:
                merged.authors = self._merge_author_lists(merged.authors, pub.authors)
            
            # Average citation counts
            if pub.citations:
                merged.citations = int((merged.citations + pub.citations) / 2)
            
            # Merge metadata
            if pub.metadata:
                merged.metadata = {**merged.metadata, **pub.metadata}
        
        return merged
    
    def _fuzzy_match_title(self, title1: str, title2: str) -> float:
        """
        Fuzzy match titles (handle case, punctuation, small differences).
        Returns similarity score 0.0-1.0
        """
        # Normalize
        t1 = title1.lower().strip().replace("-", " ").replace(":", "")
        t2 = title2.lower().strip().replace("-", " ").replace(":", "")
        
        # Use Levenshtein distance or similar
        from difflib import SequenceMatcher
        return SequenceMatcher(None, t1, t2).ratio()
```

**Example:**
```python
# Before deduplication: 3 records for same paper
Paper A (OpenAlex): DOI=10.1038/..., PMID=None, abstract=short
Paper B (PubMed):   DOI=None, PMID=34567890, abstract=long
Paper C (S2):       DOI=10.1038/..., PMID=34567890, abstract=None

# After merge: 1 record with best data
Merged: DOI=10.1038/..., PMID=34567890, abstract=long (from PubMed)
```

---

## 📊 Enhancement 4: Relevance Scoring & Ranking

### Current Approach
- All papers treated equally
- No ranking or filtering
- User gets unsorted list

### Problem
- Some papers barely mention dataset (false positives)
- Some papers extensively use dataset (highly relevant)
- No way to prioritize downloads

### Proposed: Relevance Scoring System

```python
class RelevanceScorer:
    """
    Score papers by relevance to GEO dataset.
    """
    
    def score_publication(
        self, 
        publication: Publication, 
        geo_metadata: GEOSeriesMetadata,
        discovery_context: Dict
    ) -> float:
        """
        Calculate relevance score (0.0-1.0).
        
        Factors:
        - Citation context (how cited)
        - Title relevance
        - Abstract keywords
        - Author overlap
        - Recency
        - Citation count
        - Discovery method
        """
        score = 0.0
        
        # Factor 1: Citation context (20%)
        if discovery_context.get("method") == "citation_graph":
            score += 0.2  # Cited = highly relevant
        elif discovery_context.get("method") == "text_mention":
            # Check how many times mentioned
            mention_count = self._count_mentions(
                publication, 
                geo_metadata.geo_id
            )
            score += min(0.2, mention_count * 0.05)
        
        # Factor 2: Title relevance (15%)
        title_score = self._calculate_title_relevance(
            publication.title, 
            geo_metadata
        )
        score += title_score * 0.15
        
        # Factor 3: Abstract keywords (20%)
        if publication.abstract:
            keyword_score = self._calculate_keyword_relevance(
                publication.abstract,
                geo_metadata
            )
            score += keyword_score * 0.20
        
        # Factor 4: Author overlap (10%)
        if self._has_author_overlap(publication, geo_metadata):
            score += 0.10
        
        # Factor 5: Recency (15%)
        recency_score = self._calculate_recency_score(
            publication.publication_date
        )
        score += recency_score * 0.15
        
        # Factor 6: Citation count / impact (10%)
        impact_score = self._calculate_impact_score(
            publication.citations or 0
        )
        score += impact_score * 0.10
        
        # Factor 7: Open access bonus (5%)
        if publication.metadata.get("is_open_access"):
            score += 0.05
        
        # Factor 8: Data availability (5%)
        if self._mentions_data_availability(publication):
            score += 0.05
        
        return min(1.0, score)
    
    def _count_mentions(self, publication: Publication, geo_id: str) -> int:
        """Count GEO ID mentions in title + abstract"""
        text = f"{publication.title} {publication.abstract or ''}"
        return text.upper().count(geo_id.upper())
    
    def _calculate_keyword_relevance(
        self, 
        text: str, 
        geo_metadata: GEOSeriesMetadata
    ) -> float:
        """
        Calculate keyword overlap score.
        
        Keywords from GEO metadata:
        - Organism
        - Platform
        - Study type
        - Key terms from title
        """
        keywords = self._extract_keywords(geo_metadata)
        text_lower = text.lower()
        
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return min(1.0, matches / len(keywords))
    
    def _has_author_overlap(
        self, 
        publication: Publication, 
        geo_metadata: GEOSeriesMetadata
    ) -> bool:
        """Check if any authors overlap with original dataset authors"""
        # Fetch original paper authors
        # Compare with publication authors
        pass
```

### Ranking Publications

```python
def rank_publications(
    self, 
    publications: List[Publication],
    geo_metadata: GEOSeriesMetadata
) -> List[Tuple[Publication, float]]:
    """
    Rank publications by relevance score.
    
    Returns:
        List of (publication, score) tuples sorted by score
    """
    scored = []
    for pub in publications:
        score = self.score_publication(pub, geo_metadata, {})
        scored.append((pub, score))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored
```

**Usage:**
```python
result = await citation_discovery.find_citing_papers(geo_metadata)

# Rank by relevance
scorer = RelevanceScorer()
ranked = scorer.rank_publications(result.citing_papers, geo_metadata)

# Filter low-quality results
high_quality = [(pub, score) for pub, score in ranked if score > 0.5]

logger.info(f"Found {len(high_quality)} high-quality citing papers")
for pub, score in high_quality[:10]:
    logger.info(f"  {score:.2f} - {pub.title[:60]}")
```

---

## 🛡️ Enhancement 5: Robust Error Handling

### Current Error Handling
```python
try:
    citing_papers = self.openalex.get_citing_papers(doi, max_results)
except Exception as e:
    logger.error(f"OpenAlex citation search failed: {e}")
    return []  # Returns empty, loses all results
```

**Problems:**
- Single source failure = complete failure
- No retry logic
- No partial success handling
- No fallback strategies

### Proposed: Resilient Error Handling

```python
class ResilientDiscovery:
    """
    Citation discovery with comprehensive error handling.
    """
    
    async def find_citing_papers_resilient(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100
    ) -> CitationDiscoveryResult:
        """
        Find citing papers with retry, fallback, and partial success.
        """
        all_papers = set()
        strategy_results = {}
        errors = []
        
        # Try each strategy with error handling
        for strategy in self.strategies:
            try:
                results = await self._try_strategy_with_retry(
                    strategy, 
                    geo_metadata, 
                    max_results
                )
                all_papers.update(results)
                strategy_results[strategy.name] = {
                    "count": len(results),
                    "status": "success"
                }
                
            except RateLimitError as e:
                logger.warning(f"{strategy.name} rate limited, trying next")
                errors.append(f"{strategy.name}: rate_limited")
                strategy_results[strategy.name] = {
                    "count": 0,
                    "status": "rate_limited"
                }
                continue
                
            except APIError as e:
                logger.error(f"{strategy.name} API error: {e}")
                errors.append(f"{strategy.name}: {str(e)}")
                strategy_results[strategy.name] = {
                    "count": 0,
                    "status": "api_error"
                }
                continue
                
            except Exception as e:
                logger.error(f"{strategy.name} unexpected error: {e}", exc_info=True)
                errors.append(f"{strategy.name}: {str(e)}")
                strategy_results[strategy.name] = {
                    "count": 0,
                    "status": "error"
                }
                continue
        
        # Determine overall success
        success = len(all_papers) > 0
        
        if not success:
            logger.error(f"All strategies failed for {geo_metadata.geo_id}")
            logger.error(f"Errors: {errors}")
        elif len(errors) > 0:
            logger.warning(f"Partial success: {len(errors)} strategies failed")
        
        return CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            citing_papers=list(all_papers),
            strategy_breakdown=strategy_results,
            errors=errors,
            partial_success=success and len(errors) > 0
        )
    
    async def _try_strategy_with_retry(
        self,
        strategy: Strategy,
        geo_metadata: GEOSeriesMetadata,
        max_results: int,
        max_retries: int = 3
    ) -> List[Publication]:
        """
        Try strategy with exponential backoff retry.
        """
        for attempt in range(max_retries):
            try:
                return await strategy.method(geo_metadata, max_results)
                
            except (TimeoutError, ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"{strategy.name} failed (attempt {attempt+1}/{max_retries}), "
                        f"retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        return []
```

### Fallback Chains

```python
class FallbackChain:
    """
    Define fallback strategies when primary sources fail.
    """
    
    def __init__(self):
        self.chains = {
            "citation_discovery": [
                ("openalex", self._find_via_openalex),
                ("semantic_scholar", self._find_via_s2),  # Fallback 1
                ("crossref", self._find_via_crossref),    # Fallback 2
            ],
            "text_search": [
                ("pubmed", self._find_via_pubmed),
                ("europepmc", self._find_via_europepmc),  # Fallback
            ]
        }
    
    async def execute_with_fallback(
        self, 
        chain_name: str, 
        *args, 
        **kwargs
    ) -> List[Publication]:
        """
        Try each source in chain until one succeeds.
        """
        for source_name, method in self.chains[chain_name]:
            try:
                results = await method(*args, **kwargs)
                if results:
                    logger.info(f"✓ {source_name} succeeded ({len(results)} results)")
                    return results
                else:
                    logger.warning(f"⚠ {source_name} returned 0 results, trying next")
            except Exception as e:
                logger.error(f"✗ {source_name} failed: {e}, trying next")
                continue
        
        logger.error(f"All sources in chain '{chain_name}' failed")
        return []
```

---

## 💾 Enhancement 6: Caching & Performance

### Current Performance Issues
- Re-discovers same papers every time
- No caching of API responses
- Wastes API quota on repeated searches
- Slow for frequently accessed datasets

### Proposed: Multi-Layer Caching

```python
class DiscoveryCache:
    """
    Cache discovery results to avoid re-querying APIs.
    
    Cache levels:
    1. In-memory (session cache)
    2. SQLite (persistent cache)
    3. TTL-based expiration
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.memory_cache = {}  # In-memory cache
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS citation_discovery_cache (
                geo_id TEXT PRIMARY KEY,
                discovery_result JSON,
                timestamp REAL,
                ttl_hours INTEGER DEFAULT 168  -- 1 week
            )
        """)
        conn.commit()
        conn.close()
    
    async def get_cached_result(
        self, 
        geo_id: str
    ) -> Optional[CitationDiscoveryResult]:
        """Get cached discovery result if not expired"""
        # Check memory cache first
        if geo_id in self.memory_cache:
            result, timestamp = self.memory_cache[geo_id]
            if time.time() - timestamp < 3600:  # 1 hour TTL
                logger.debug(f"Cache HIT (memory): {geo_id}")
                return result
        
        # Check SQLite cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT discovery_result, timestamp, ttl_hours 
            FROM citation_discovery_cache 
            WHERE geo_id = ?
            """,
            (geo_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result_json, timestamp, ttl_hours = row
            age_hours = (time.time() - timestamp) / 3600
            
            if age_hours < ttl_hours:
                logger.debug(f"Cache HIT (db): {geo_id} (age: {age_hours:.1f}h)")
                result = CitationDiscoveryResult.from_json(result_json)
                
                # Refresh memory cache
                self.memory_cache[geo_id] = (result, time.time())
                
                return result
            else:
                logger.debug(f"Cache EXPIRED: {geo_id} (age: {age_hours:.1f}h)")
        
        logger.debug(f"Cache MISS: {geo_id}")
        return None
    
    async def set_cached_result(
        self,
        geo_id: str,
        result: CitationDiscoveryResult,
        ttl_hours: int = 168  # 1 week default
    ):
        """Cache discovery result"""
        # Save to memory
        self.memory_cache[geo_id] = (result, time.time())
        
        # Save to SQLite
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO citation_discovery_cache 
            (geo_id, discovery_result, timestamp, ttl_hours)
            VALUES (?, ?, ?, ?)
            """,
            (geo_id, result.to_json(), time.time(), ttl_hours)
        )
        conn.commit()
        conn.close()
        
        logger.debug(f"Cached result for {geo_id} (TTL: {ttl_hours}h)")
```

### Usage with Caching

```python
async def find_citing_papers(
    self,
    geo_metadata: GEOSeriesMetadata,
    max_results: int = 100,
    use_cache: bool = True
) -> CitationDiscoveryResult:
    """
    Find citing papers with caching support.
    """
    # Check cache first
    if use_cache:
        cached = await self.cache.get_cached_result(geo_metadata.geo_id)
        if cached:
            logger.info(f"Using cached results for {geo_metadata.geo_id}")
            return cached
    
    # No cache, do discovery
    logger.info(f"No cache, discovering papers for {geo_metadata.geo_id}")
    result = await self._do_discovery(geo_metadata, max_results)
    
    # Cache result
    if use_cache:
        await self.cache.set_cached_result(geo_metadata.geo_id, result)
    
    return result
```

### Performance Optimizations

```python
# Batch API calls
async def find_citing_papers_batch(
    self,
    geo_datasets: List[GEOSeriesMetadata],
    max_results: int = 100
) -> List[CitationDiscoveryResult]:
    """
    Discover citations for multiple datasets in parallel.
    """
    tasks = [
        self.find_citing_papers(geo, max_results)
        for geo in geo_datasets
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions
    successful = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Discovery failed for {geo_datasets[i].geo_id}: {result}")
        else:
            successful.append(result)
    
    return successful
```

---

## ✅ Enhancement 7: Quality Validation

### Problem
- Some "citing" papers are false positives
- GEO ID might appear in unrelated context
- Low-quality papers pollute results

### Proposed: Validation Filters

```python
class QualityValidator:
    """
    Validate and filter low-quality discovery results.
    """
    
    def validate_publication(
        self,
        publication: Publication,
        geo_metadata: GEOSeriesMetadata,
        context: Dict
    ) -> Tuple[bool, str]:
        """
        Validate if publication genuinely cites/uses dataset.
        
        Returns:
            (is_valid, reason)
        """
        reasons = []
        
        # Check 1: Has basic metadata
        if not publication.title:
            return False, "Missing title"
        
        # Check 2: Publication date after dataset
        if publication.publication_date and geo_metadata.submission_date:
            dataset_date = datetime.strptime(geo_metadata.submission_date, "%Y-%m-%d")
            if publication.publication_date < dataset_date:
                return False, f"Published before dataset ({publication.publication_date} < {dataset_date})"
        
        # Check 3: For mention-based discovery, verify GEO ID appears
        if context.get("discovery_method") == "mention":
            if not self._verify_geo_mention(publication, geo_metadata.geo_id):
                return False, "GEO ID not found in text"
        
        # Check 4: Not retracted
        if publication.metadata.get("is_retracted"):
            return False, "Paper retracted"
        
        # Check 5: Language (optional - prefer English)
        if publication.metadata.get("language") and publication.metadata["language"] != "eng":
            reasons.append(f"Non-English ({publication.metadata['language']})")
        
        # Check 6: Has DOI or PMID (preferably both)
        if not publication.doi and not publication.pmid:
            reasons.append("Missing DOI and PMID")
        
        # All checks passed
        return True, "; ".join(reasons) if reasons else "Valid"
    
    def filter_publications(
        self,
        publications: List[Publication],
        geo_metadata: GEOSeriesMetadata,
        min_quality_score: float = 0.3
    ) -> List[Publication]:
        """
        Filter publications by quality criteria.
        """
        valid_pubs = []
        
        for pub in publications:
            is_valid, reason = self.validate_publication(pub, geo_metadata, {})
            
            if not is_valid:
                logger.debug(f"Filtered out: {pub.title[:40]}... ({reason})")
                continue
            
            # Calculate quality score
            scorer = RelevanceScorer()
            score = scorer.score_publication(pub, geo_metadata, {})
            
            if score >= min_quality_score:
                valid_pubs.append(pub)
            else:
                logger.debug(f"Low quality score ({score:.2f}): {pub.title[:40]}...")
        
        logger.info(f"Filtered {len(publications)} → {len(valid_pubs)} publications")
        return valid_pubs
```

---

## 📐 Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal:** Add Semantic Scholar, improve error handling

1. **Add Semantic Scholar client** (2 days)
   - Implement `SemanticScholarClient`
   - Add to `geo_discovery.py`
   - Test citation discovery

2. **Implement resilient error handling** (2 days)
   - Add retry logic
   - Implement fallback chains
   - Handle partial failures

3. **Basic caching** (1 day)
   - SQLite cache for discovery results
   - TTL-based expiration

**Deliverables:**
- ✅ 3 discovery sources (PubMed, OpenAlex, Semantic Scholar)
- ✅ Retry + fallback
- ✅ Basic caching

---

### Phase 2: Intelligence (Week 2)
**Goal:** Add smart deduplication, relevance scoring

1. **Advanced deduplication** (2 days)
   - Fuzzy matching
   - Intelligent merging
   - Conflict resolution

2. **Relevance scoring** (2 days)
   - Implement `RelevanceScorer`
   - Keyword matching
   - Context analysis

3. **Quality validation** (1 day)
   - Filter false positives
   - Validate publication dates
   - Check retraction status

**Deliverables:**
- ✅ Smart deduplication
- ✅ Relevance scores
- ✅ Quality filtering

---

### Phase 3: Scale (Week 3)
**Goal:** Add more sources, optimize performance

1. **Add Europe PMC** (2 days)
   - Implement `EuropePMCClient`
   - Integrate into discovery

2. **Add Crossref** (2 days)
   - Implement `CrossrefClient`
   - Citation metadata

3. **Adaptive strategies** (1 day)
   - Implement `StrategySelector`
   - Early stopping logic

**Deliverables:**
- ✅ 5 discovery sources
- ✅ Adaptive strategy selection
- ✅ Performance optimization

---

## 📊 Expected Improvements

### Coverage
| Metric | Current | After Enhancement | Improvement |
|--------|---------|-------------------|-------------|
| **Discovery Sources** | 2 | 5 | +150% |
| **Papers Found** | ~15-30 | ~40-80 | +150% |
| **False Positives** | ~20% | ~5% | -75% |
| **API Failures** | Fatal | Graceful | Resilient |
| **Cache Hit Rate** | 0% | 60-80% | New |
| **Discovery Time** | 2-3s | 1-2s (cached) | -50% |

### Quality
- **Relevance:** All papers get relevance score (0.0-1.0)
- **Ranking:** Papers sorted by relevance
- **Filtering:** Low-quality papers removed
- **Validation:** False positives filtered

### Reliability
- **Retry logic:** 3 attempts per source
- **Fallback chains:** Alternative sources on failure
- **Partial success:** Returns results even if some sources fail
- **Error reporting:** Detailed error tracking

---

## 🎯 Success Metrics

### Key Performance Indicators (KPIs)

1. **Coverage Rate**
   - Target: Find 80%+ of papers actually citing dataset
   - Measure: Compare against manual search

2. **Precision Rate**
   - Target: 95%+ of discovered papers are relevant
   - Measure: Manual validation of random sample

3. **Discovery Time**
   - Target: <2 seconds per dataset (with cache)
   - Measure: Average discovery time

4. **Cache Hit Rate**
   - Target: 70%+ of requests served from cache
   - Measure: Cache hits / total requests

5. **Failure Resilience**
   - Target: 100% uptime (graceful degradation)
   - Measure: % of requests that return results

---

## 🚀 Quick Wins (Implement First)

### 1. Add Semantic Scholar (HIGH IMPACT, LOW EFFORT)
- Already have example code from deleted `semantic_scholar.py`
- Free API, 100 req/sec
- Doubles coverage immediately

### 2. Implement Caching (HIGH IMPACT, LOW EFFORT)
- Saves 80%+ of repeated API calls
- Simple SQLite implementation
- Instant performance boost

### 3. Add Retry Logic (MEDIUM IMPACT, LOW EFFORT)
- Prevents transient failures
- Simple exponential backoff
- More reliable

### 4. Basic Relevance Scoring (MEDIUM IMPACT, MEDIUM EFFORT)
- Start with simple keyword matching
- Add citation count weighting
- Improves result quality

---

## 📝 Code Examples

### Complete Enhanced Discovery Flow

```python
# Enhanced geo_discovery.py

class EnhancedGEOCitationDiscovery:
    """
    Robust multi-source citation discovery with:
    - Multiple discovery sources (5+)
    - Intelligent deduplication
    - Relevance scoring
    - Quality validation
    - Caching
    - Error resilience
    """
    
    def __init__(self):
        # Initialize clients
        self.openalex = OpenAlexClient()
        self.pubmed = PubMedClient()
        self.semantic_scholar = SemanticScholarClient()
        self.europepmc = EuropePMCClient()
        self.crossref = CrossrefClient()
        
        # Initialize utilities
        self.deduplicator = PublicationDeduplicator()
        self.scorer = RelevanceScorer()
        self.validator = QualityValidator()
        self.cache = DiscoveryCache(Path("data/omics_oracle.db"))
        self.fallback = FallbackChain()
    
    async def find_citing_papers(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100,
        min_quality_score: float = 0.5,
        use_cache: bool = True
    ) -> CitationDiscoveryResult:
        """
        Comprehensive citation discovery pipeline.
        """
        # 1. Check cache
        if use_cache:
            cached = await self.cache.get_cached_result(geo_metadata.geo_id)
            if cached:
                return cached
        
        # 2. Discover from multiple sources
        all_papers = []
        
        # Strategy A: Citation-based (with fallback)
        citations = await self.fallback.execute_with_fallback(
            "citation_discovery",
            geo_metadata
        )
        all_papers.extend(citations)
        
        # Strategy B: Mention-based (with fallback)
        mentions = await self.fallback.execute_with_fallback(
            "text_search",
            geo_metadata
        )
        all_papers.extend(mentions)
        
        # 3. Deduplicate and merge
        unique_papers = self.deduplicator.deduplicate_and_merge(all_papers)
        
        # 4. Score relevance
        scored_papers = [
            (pub, self.scorer.score_publication(pub, geo_metadata, {}))
            for pub in unique_papers
        ]
        
        # 5. Filter by quality
        high_quality = [
            pub for pub, score in scored_papers 
            if score >= min_quality_score
        ]
        
        # 6. Validate
        validated = self.validator.filter_publications(
            high_quality, 
            geo_metadata
        )
        
        # 7. Sort by score
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        final_papers = [pub for pub, score in scored_papers[:max_results]]
        
        # 8. Create result
        result = CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            citing_papers=final_papers,
            relevance_scores={pub.pmid: score for pub, score in scored_papers},
            total_found=len(all_papers),
            after_dedup=len(unique_papers),
            after_filtering=len(validated)
        )
        
        # 9. Cache result
        if use_cache:
            await self.cache.set_cached_result(geo_metadata.geo_id, result)
        
        return result
```

---

## 🎓 Summary

### What Makes Pipeline 1 Robust?

1. **Multi-Source Discovery** (5+ sources)
   - More coverage
   - Fallback on failures
   - Complementary strengths

2. **Intelligent Processing**
   - Smart deduplication
   - Relevance scoring
   - Quality validation

3. **Error Resilience**
   - Retry logic
   - Fallback chains
   - Partial success handling

4. **Performance**
   - Caching (70%+ hit rate)
   - Parallel execution
   - Early stopping

5. **Quality**
   - False positive filtering
   - Relevance ranking
   - Validation checks

---

**Next Steps:** Choose which enhancements to implement first!

**Recommendation:** Start with:
1. Add Semantic Scholar (doubles coverage)
2. Implement caching (instant speedup)
3. Add retry logic (more reliable)

These three quick wins will make Pipeline 1 significantly more robust with minimal effort.

---

**Author:** OmicsOracle Architecture Team  
**Date:** October 14, 2025  
**Status:** Enhancement Plan - Ready for Implementation ✅
