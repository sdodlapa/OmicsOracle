# Hybrid Search Implementation Plan

## Objective
Enable parallel GEO + Publication search to maximize dataset recall

## Phase 1: Quick Fix (Enable Both Searches)

### Step 1: Remove GEO-Only Override
**File**: `omics_oracle_v2/lib/pipelines/unified_search_pipeline.py`

**Current Code (Lines 320-326)**:
```python
# OVERRIDE: For GEO-focused application, always search GEO datasets
# (not publications) unless it's a pure GEO ID lookup
if analysis.search_type == SearchType.PUBLICATIONS:
    logger.info("Overriding PUBLICATIONS → GEO (GEO-focused application)")
    analysis.search_type = SearchType.GEO
elif analysis.search_type == SearchType.AUTO:
    logger.info("Overriding AUTO → GEO (GEO-focused application)")
    analysis.search_type = SearchType.GEO
```

**New Code**:
```python
# HYBRID MODE: Enable BOTH GEO and publication search for maximum recall
# Publications often contain richer semantic context than GEO metadata
# and link to datasets via data availability statements
if analysis.search_type == SearchType.AUTO:
    logger.info("AUTO mode: Will search BOTH GEO and publications (hybrid)")
    analysis.search_type = SearchType.HYBRID  # New type!
elif analysis.search_type == SearchType.PUBLICATIONS:
    # Allow publication search (don't override)
    logger.info("Publication search requested - will extract GEO IDs from papers")
```

### Step 2: Add HYBRID Search Type
**File**: `omics_oracle_v2/lib/models/query_analysis.py` (or wherever SearchType is defined)

```python
class SearchType(str, Enum):
    GEO = "geo"
    GEO_ID = "geo_id"
    PUBLICATIONS = "publications"
    HYBRID = "hybrid"  # NEW!
    AUTO = "auto"
```

### Step 3: Implement Hybrid Execution
**File**: `omics_oracle_v2/lib/pipelines/unified_search_pipeline.py`

**Find this section (around line 360)**:
```python
# Step 4: Route and execute searches
geo_datasets = []
publications = []

# GEO ID fast path
if analysis.search_type == SearchType.GEO_ID and analysis.geo_ids:
    logger.info(f"GEO ID detected: {analysis.geo_ids[0]} - fast path")
    geo_datasets = await self._search_geo_by_id(analysis.geo_ids[0])
```

**Add HYBRID case**:
```python
# Step 4: Route and execute searches
geo_datasets = []
publications = []
geo_from_publications = []

# GEO ID fast path
if analysis.search_type == SearchType.GEO_ID and analysis.geo_ids:
    logger.info(f"GEO ID detected: {analysis.geo_ids[0]} - fast path")
    geo_datasets = await self._search_geo_by_id(analysis.geo_ids[0])

# HYBRID: Run both GEO and publication searches in parallel
elif analysis.search_type == SearchType.HYBRID:
    logger.info("Hybrid search: Running GEO + Publication searches in parallel")

    # Run both in parallel for speed
    geo_task = self._search_geo(optimized_query, max_results)
    pub_task = self._search_publications(optimized_query, max_results)

    geo_direct, publications = await asyncio.gather(
        geo_task,
        pub_task,
        return_exceptions=True
    )

    # Handle exceptions
    if isinstance(geo_direct, Exception):
        logger.error(f"GEO search failed: {geo_direct}")
        geo_datasets = []
    else:
        geo_datasets = geo_direct

    if isinstance(publications, Exception):
        logger.error(f"Publication search failed: {publications}")
        publications = []

    # Extract GEO IDs from publications
    if publications:
        geo_ids_from_pubs = await self._extract_geo_ids_from_publications(publications)
        if geo_ids_from_pubs:
            logger.info(f"Extracted {len(geo_ids_from_pubs)} GEO IDs from {len(publications)} publications")
            geo_from_publications = await self._fetch_geo_datasets_by_ids(geo_ids_from_pubs)

    # Merge GEO results (direct + from publications)
    all_geo = self._merge_and_deduplicate_datasets(geo_datasets, geo_from_publications)
    geo_datasets = all_geo

    logger.info(f"Hybrid results: {len(geo_datasets)} unique datasets ({len(geo_direct)} direct + {len(geo_from_publications)} from pubs)")

# GEO search only
elif analysis.search_type == SearchType.GEO:
    if self.config.enable_geo_search:
        geo_optimized_query = self.geo_query_builder.build_query(
            optimized_query, mode="balanced"
        )
        if geo_optimized_query != optimized_query:
            logger.info(f"GEO query optimized: '{optimized_query}' -> '{geo_optimized_query}'")
        geo_datasets = await self._search_geo(geo_optimized_query, max_results)

# Publication search only
elif analysis.search_type == SearchType.PUBLICATIONS:
    logger.info("Publication-driven search: Finding papers and extracting GEO IDs")
    publications = await self._search_publications(optimized_query, max_results)

    # Extract GEO IDs from publications
    if publications:
        geo_ids_from_pubs = await self._extract_geo_ids_from_publications(publications)
        if geo_ids_from_pubs:
            logger.info(f"Found {len(geo_ids_from_pubs)} GEO datasets mentioned in publications")
            geo_datasets = await self._fetch_geo_datasets_by_ids(geo_ids_from_pubs)
```

### Step 4: Implement GEO ID Extraction
**File**: `omics_oracle_v2/lib/pipelines/unified_search_pipeline.py`

**Add new method**:
```python
async def _extract_geo_ids_from_publications(self, publications: List[Publication]) -> List[str]:
    """
    Extract GEO accession numbers (GSE IDs) from publication metadata.

    Args:
        publications: List of publication objects

    Returns:
        List of unique GEO IDs found
    """
    import re

    geo_pattern = re.compile(r'\bGSE\d{5,}\b')  # Match GSE12345 (5+ digits)
    geo_ids = set()

    for pub in publications:
        # Search in abstract
        if pub.abstract:
            matches = geo_pattern.findall(pub.abstract)
            geo_ids.update(matches)

        # Search in full text (if available)
        if hasattr(pub, 'full_text') and pub.full_text:
            matches = geo_pattern.findall(pub.full_text)
            geo_ids.update(matches)

        # Search in title (less common but possible)
        if pub.title:
            matches = geo_pattern.findall(pub.title)
            geo_ids.update(matches)

    logger.info(f"Extracted {len(geo_ids)} unique GEO IDs from {len(publications)} publications")
    return list(geo_ids)

async def _fetch_geo_datasets_by_ids(self, geo_ids: List[str]) -> List[Any]:
    """
    Fetch GEO datasets by their accession IDs.

    Args:
        geo_ids: List of GEO accession IDs (e.g., ['GSE12345', 'GSE67890'])

    Returns:
        List of GEO dataset objects
    """
    if not geo_ids:
        return []

    datasets = []

    # Use batch fetch for efficiency
    try:
        # Assuming your GEO client has batch fetch capability
        batch_results = await self.geo_client.batch_get_metadata_smart(geo_ids)
        datasets = [ds for ds in batch_results if ds is not None]
        logger.info(f"Fetched {len(datasets)}/{len(geo_ids)} datasets via batch fetch")
    except Exception as e:
        logger.error(f"Batch fetch failed: {e}, falling back to individual fetches")

        # Fallback: Fetch individually
        for geo_id in geo_ids:
            try:
                dataset = await self._search_geo_by_id(geo_id)
                if dataset:
                    datasets.extend(dataset)  # _search_geo_by_id returns list
            except Exception as e:
                logger.warning(f"Failed to fetch {geo_id}: {e}")

    return datasets

def _merge_and_deduplicate_datasets(self, list1: List[Any], list2: List[Any]) -> List[Any]:
    """
    Merge two lists of datasets and remove duplicates by GEO ID.

    Args:
        list1: First list of datasets
        list2: Second list of datasets

    Returns:
        Merged list with no duplicate GEO IDs
    """
    seen_ids = set()
    merged = []

    for dataset in list1 + list2:
        geo_id = getattr(dataset, 'geo_id', None) or getattr(dataset, 'accession', None)
        if geo_id and geo_id not in seen_ids:
            seen_ids.add(geo_id)
            merged.append(dataset)

    return merged
```

---

## Phase 2: Enhanced Publication Search

### Improve Full-Text Access
**Goal**: Access data availability sections in papers

**Options**:
1. **PubMed Central (PMC)**: Free full-text access for many papers
2. **BioRxiv/MedRxiv**: Preprints with full text
3. **PDF Parsing**: Extract from downloaded PDFs (you already have this!)

**Implementation**:
```python
async def _get_publication_fulltext(self, pub: Publication) -> str:
    """
    Get full text from various sources.
    """
    # Try PMC first
    if pub.pmc_id:
        fulltext = await self.pmc_client.fetch_fulltext(pub.pmc_id)
        if fulltext:
            return fulltext

    # Try downloaded PDFs
    pdf_path = self._get_pdf_path(pub)
    if pdf_path and os.path.exists(pdf_path):
        fulltext = self._extract_text_from_pdf(pdf_path)
        if fulltext:
            return fulltext

    # Fallback to abstract
    return pub.abstract or ""
```

### Smart GEO Extraction
**Goal**: Find GEO IDs even in complex text

**Implementation**:
```python
def _extract_geo_ids_smart(self, text: str) -> List[str]:
    """
    Extract GEO IDs with context awareness.
    """
    # Pattern: GSE followed by 5+ digits
    pattern = r'\b(GSE\d{5,})\b'

    # Find all matches
    matches = re.findall(pattern, text, re.IGNORECASE)

    # Filter out false positives
    # (e.g., mentions in citations of other papers)
    valid_ids = []
    for geo_id in set(matches):
        # Check context - should be near data availability keywords
        context_pattern = rf'.{{0,200}}{re.escape(geo_id)}.{{0,200}}'
        context = re.search(context_pattern, text, re.IGNORECASE | re.DOTALL)

        if context:
            context_text = context.group().lower()
            # Data availability indicators
            if any(keyword in context_text for keyword in [
                'data availab', 'deposited', 'accession',
                'geo', 'ncbi', 'sra', 'raw data'
            ]):
                valid_ids.append(geo_id.upper())

    return valid_ids
```

---

## Phase 3: Performance Optimization

### Caching
```python
# Cache publication → GEO mappings
@lru_cache(maxsize=10000)
def get_geo_ids_for_pmid(pmid: str) -> List[str]:
    """Cache GEO IDs for each PMID"""
    pass
```

### Parallel Batch Processing
```python
async def _fetch_multiple_publications_fulltext(self, pubs: List[Publication]) -> Dict[str, str]:
    """Fetch full text for multiple publications in parallel"""
    tasks = [self._get_publication_fulltext(pub) for pub in pubs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {pub.pmid: text for pub, text in zip(pubs, results) if not isinstance(text, Exception)}
```

---

## Testing Plan

### Test Case 1: User's Example
```python
async def test_hybrid_search_user_example():
    query = "single cell DNA methylation and 3D genome architecture"

    result = await pipeline.search(query, max_results=20)

    # Should find these datasets
    expected = ["GSE215353", "GSE124391"]
    found_ids = [ds.geo_id for ds in result.datasets]

    for expected_id in expected:
        assert expected_id in found_ids, f"Missing {expected_id}!"

    print(f"✅ Found all expected datasets: {expected}")
```

### Test Case 2: Performance
```python
async def test_hybrid_search_performance():
    query = "methylation chromatin"

    start = time.time()
    result = await pipeline.search(query)
    duration = time.time() - start

    assert duration < 3.0, f"Too slow: {duration}s"
    print(f"✅ Hybrid search completed in {duration:.2f}s")
```

### Test Case 3: Deduplication
```python
async def test_no_duplicates():
    query = "methylation"

    result = await pipeline.search(query)
    geo_ids = [ds.geo_id for ds in result.datasets]

    assert len(geo_ids) == len(set(geo_ids)), "Duplicate datasets found!"
    print(f"✅ No duplicates in {len(geo_ids)} results")
```

---

## Rollout Plan

### Step 1: Feature Flag (Week 1)
```python
# config/development.yml
search:
  hybrid_mode:
    enabled: true  # Can disable if issues
    publication_weight: 0.3  # Start conservative
```

### Step 2: A/B Test (Week 2)
- 50% users get hybrid
- 50% users get GEO-only
- Compare:
  - Result counts
  - User satisfaction
  - Click-through rates

### Step 3: Full Rollout (Week 3)
- Enable for 100% if metrics improve
- Monitor performance
- Gather user feedback

---

## Success Metrics

### Must Have
- ✅ Find all datasets user knows exist
- ✅ No performance degradation (< 3s response time)
- ✅ No duplicate results

### Nice to Have
- 📈 20%+ increase in unique datasets found
- 📈 Higher user satisfaction scores
- 📈 More dataset details (linked publications)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Slower response | High | Parallel execution, caching, timeouts |
| Lower precision | Medium | Rank by relevance, show source (direct vs pub) |
| API rate limits | Medium | Respect limits, implement backoff, cache |
| Complex code | Low | Modular design, comprehensive tests |

---

## Decision

**PROCEED with hybrid search implementation**

**Rationale**:
1. ✅ User complaint is valid - we're missing relevant datasets
2. ✅ Root cause understood - GEO metadata is sparse
3. ✅ Solution is clear - leverage publication semantics
4. ✅ Infrastructure exists - publication search already implemented
5. ✅ Performance acceptable - parallel execution minimizes latency

**Priority**: 🔴 **CRITICAL** - Directly impacts core value proposition

**Timeline**: Implement in current session, test with user's examples
