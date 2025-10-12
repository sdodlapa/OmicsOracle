# Hybrid Search Strategy: Why We Need Both GEO + Publication Search

**Date**: October 12, 2025  
**Issue**: Missing relevant datasets due to GEO-only search limitation

---

## Problem Discovery

### User Query
```
"single cell DNA methylation and 3D genome architecture"
```

### Expected Results (User Knowledge)
1. **Paper**: "Single-cell DNA methylation and 3D genome architecture in the human brain"
   - **GEO Dataset**: GSE215353
   - **Why missed**: GEO metadata says "Epigenetic landscape of Human Brain by Single Nucleus Methylation Sequencing" (no mention of "3D genome" or "HiC")

2. **Paper**: "Simultaneous profiling of 3D genome structure and DNA methylation in single human cells"
   - **GEO Datasets**: GSE124391, GSE130711
   - **Why missed**: Similar metadata mismatch

### Actual Results
- Found 9 datasets
- **Missing** GSE215353, GSE124391, GSE130711

---

## Root Cause Analysis

### The Disconnect

```
┌─────────────────────────────────┐
│  PUBLICATION (PubMed/PMC)       │
│                                 │
│  Title: "Single-cell DNA        │
│  methylation and 3D genome      │  ← Contains ALL semantic terms
│  architecture in human brain"   │     (methylation + 3D genome)
│                                 │
│  GEO Accession: GSE215353       │  ← Mentioned in supplementary
│  (in data availability section) │     materials or full text
└─────────────────────────────────┘
           ↓ Link only in full text
┌─────────────────────────────────┐
│  GEO DATASET (NCBI GEO)         │
│                                 │
│  ID: GSE215353                  │
│  Title: "Epigenetic landscape   │  ← MISSING key terms!
│  of Human Brain by Single       │     (no "3D genome", no "HiC")
│  Nucleus Methylation Seq"       │
│                                 │
└─────────────────────────────────┘
```

### Why Current GEO-Only Search Fails

1. **Sparse GEO Metadata**: Dataset titles/summaries often focus on methodology, not biology
2. **Rich Publication Content**: Paper titles/abstracts contain full semantic context
3. **Missing Link in PubMed**: GEO accessions are in supplementary/data sections, NOT indexed fields
4. **NCBI's Limitation**: No direct PubMed→GEO linking in searchable metadata

---

## Solution: Hybrid Search Strategy

### Approach 1: GEO Direct Search (Current)
**What it finds**: Datasets with matching terms in GEO metadata

```python
Query: "methylation 3D genome architecture"
       ↓
NCBI GEO Search (db=gds)
       ↓
Results: Datasets where title/summary contains these terms
```

**Strengths**:
- Direct access to dataset metadata
- Fast (single API call)
- High precision for well-documented datasets

**Weaknesses**:
- ❌ Misses datasets with sparse metadata
- ❌ Doesn't leverage publication semantic richness
- ❌ Limited by GEO curator's keyword choices

### Approach 2: Publication-Driven Search (NEEDED!)
**What it finds**: Datasets linked to semantically relevant papers

```python
Query: "methylation 3D genome architecture"
       ↓
PubMed Search (db=pubmed)
       ↓
Find papers with matching title/abstract
       ↓
Extract GEO accessions from papers
       ↓
Fetch those GEO datasets
```

**Strengths**:
- ✅ Leverages rich publication semantics
- ✅ Finds datasets even with sparse GEO metadata
- ✅ Captures author's full research context

**Weaknesses**:
- Slower (multiple API calls)
- Requires full-text access or data section parsing
- Some papers don't mention GEO in abstract

### Approach 3: Hybrid (OPTIMAL!)
**Combine both strategies in parallel**

```python
async def hybrid_search(query):
    # Run both searches in parallel
    geo_results, pub_results = await asyncio.gather(
        search_geo_direct(query),
        search_via_publications(query)
    )
    
    # Merge and deduplicate
    all_datasets = merge_and_deduplicate(geo_results, pub_results)
    
    # Rank by relevance
    return rank_by_relevance(all_datasets, query)
```

**Benefits**:
- ✅ Maximum recall (finds datasets via both routes)
- ✅ Parallel execution (no speed penalty)
- ✅ Robust to metadata quality issues
- ✅ Captures both direct and indirect associations

---

## Implementation Plan

### Phase 1: Enable Publication Search ✅ (Already exists)
```python
# omics_oracle_v2/lib/pipelines/unified_search_pipeline.py

# Currently DISABLED by this override:
if analysis.search_type == SearchType.PUBLICATIONS:
    logger.info("Overriding PUBLICATIONS → GEO")
    analysis.search_type = SearchType.GEO  # ← REMOVE THIS!
```

### Phase 2: Implement GEO Extraction from Publications
```python
async def extract_geo_accessions_from_publications(publications: List[Publication]) -> List[str]:
    """
    Extract GEO accessions (GSE IDs) from publication metadata.
    
    Search in:
    1. Abstract text
    2. Full text (if available)
    3. Data availability statements
    4. Supplementary materials
    """
    geo_ids = []
    pattern = re.compile(r'\bGSE\d{5,}\b')
    
    for pub in publications:
        # Search abstract
        if pub.abstract:
            geo_ids.extend(pattern.findall(pub.abstract))
        
        # Search full text
        if pub.full_text:
            geo_ids.extend(pattern.findall(pub.full_text))
    
    return list(set(geo_ids))  # Deduplicate
```

### Phase 3: Implement Hybrid Search
```python
async def search(self, query: str, max_results: int = 10) -> AgentResult:
    """
    Hybrid search: GEO direct + Publication-driven
    """
    
    # Strategy 1: Direct GEO search
    geo_direct_task = self._search_geo_direct(query, max_results)
    
    # Strategy 2: Publication-driven GEO search
    pub_driven_task = self._search_geo_via_publications(query, max_results)
    
    # Run in parallel
    geo_direct, geo_via_pubs = await asyncio.gather(
        geo_direct_task,
        pub_driven_task,
        return_exceptions=True
    )
    
    # Merge results
    all_datasets = self._merge_datasets(geo_direct, geo_via_pubs)
    
    # Deduplicate by GEO ID
    unique_datasets = self._deduplicate_by_geo_id(all_datasets)
    
    # Rank by relevance
    ranked = self._rank_datasets(unique_datasets, query)
    
    return AgentResult(
        datasets=ranked[:max_results],
        metadata={
            "geo_direct_count": len(geo_direct),
            "pub_driven_count": len(geo_via_pubs),
            "total_unique": len(unique_datasets),
        }
    )

async def _search_geo_via_publications(self, query: str, max_results: int) -> List[Dataset]:
    """
    Search publications, extract GEO IDs, fetch datasets
    """
    # 1. Search PubMed for relevant papers
    publications = await self._search_publications(query, max_results=50)
    
    # 2. Extract GEO accessions from papers
    geo_ids = await self._extract_geo_accessions(publications)
    
    # 3. Fetch those datasets
    datasets = await self._fetch_geo_datasets(geo_ids)
    
    # 4. Attach publication context
    for dataset in datasets:
        dataset.linked_publications = [
            pub for pub in publications 
            if dataset.geo_id in (pub.abstract or "") + (pub.full_text or "")
        ]
    
    return datasets
```

### Phase 4: Configuration
```python
# config/development.yml
search:
  hybrid_mode:
    enabled: true
    strategies:
      - geo_direct  # Search GEO metadata directly
      - pub_driven  # Search via publications
    weights:
      geo_direct: 0.6    # Weight for direct GEO match
      pub_driven: 0.4    # Weight for publication-driven match
```

---

## Expected Improvements

### Before (GEO-only)
```
Query: "single cell DNA methylation and 3D genome architecture"
Results: 9 datasets
Missing: GSE215353, GSE124391, GSE130711 ❌
```

### After (Hybrid)
```
Query: "single cell DNA methylation and 3D genome architecture"

GEO Direct Search:
  → 9 datasets (original results)

Publication-Driven Search:
  → Find PMID 37824674: "Single-cell DNA methylation and 3D genome architecture..."
  → Extract GSE215353 from paper
  → Fetch GSE215353 dataset
  → Find other papers with GSE124391, GSE130711
  
Combined Results: 12 datasets (9 + 3 new)
Including: GSE215353, GSE124391, GSE130711 ✅
```

---

## Performance Considerations

### API Calls Comparison

**Current (GEO-only)**:
```
1 GEO search API call
Total: 1 call
```

**Hybrid**:
```
1 GEO search API call (parallel)
1 PubMed search API call (parallel)
N GEO fetch calls for extracted IDs (batch)
Total: ~3-5 calls (with batching)
```

### Optimization Strategies

1. **Parallel Execution**: Run GEO and PubMed searches simultaneously
2. **Batch Fetching**: Fetch multiple GEO datasets in single call
3. **Smart Caching**: Cache publication → GEO mappings
4. **Early Termination**: Stop publication parsing after finding enough GEO IDs
5. **Incremental Results**: Show GEO-direct results immediately, add pub-driven later

---

## Risk Assessment

### Risks
1. **Increased Latency**: More API calls → slower response
   - **Mitigation**: Parallel execution, caching, incremental results

2. **Lower Precision**: Publications might mention GEO IDs tangentially
   - **Mitigation**: Score by relevance, prioritize GEO-direct matches

3. **API Rate Limits**: More NCBI calls
   - **Mitigation**: Respect rate limits, implement backoff, cache aggressively

4. **Complexity**: More code to maintain
   - **Mitigation**: Modular design, comprehensive tests, feature flags

### Benefits
1. **Higher Recall**: Find ALL relevant datasets ✅
2. **Better User Experience**: No missing expected results ✅
3. **Semantic Richness**: Leverage publication context ✅
4. **Future-Proof**: Works even if GEO metadata quality varies ✅

---

## Testing Strategy

### Test Cases

**Test 1: Sparse GEO Metadata**
```python
query = "single cell DNA methylation and 3D genome architecture"
expected = ["GSE215353", "GSE124391", ...]  # From user knowledge
result = await hybrid_search(query)
assert all(gse_id in result for gse_id in expected)
```

**Test 2: Rich GEO Metadata**
```python
query = "joint profiling dna methylation hic"
# Should find via BOTH routes
result = await hybrid_search(query)
assert len(result) >= previous_geo_only_count
```

**Test 3: Publication-Only Match**
```python
# Dataset with terrible GEO metadata but great paper
query = "specific biological process described in paper"
result = await hybrid_search(query)
# Should find via publication route
```

**Test 4: Performance**
```python
start = time.time()
result = await hybrid_search(query)
duration = time.time() - start
assert duration < 2.0  # Must stay under 2 seconds
```

---

## Recommendation

**IMPLEMENT HYBRID SEARCH IMMEDIATELY**

### Justification
1. **User Complaint is Valid**: Current system misses known relevant datasets
2. **Root Cause Identified**: GEO metadata is often sparse
3. **Solution is Clear**: Leverage publication semantics
4. **Implementation Exists**: Publication search already built, just need integration
5. **Performance Acceptable**: Parallel execution keeps latency low

### Priority: 🔴 **CRITICAL**

This directly impacts core user value proposition: "Find ALL relevant datasets for my research question"

### Next Steps
1. ✅ Document problem (this file)
2. 🔄 Remove GEO-only override in unified_search_pipeline.py
3. 🔄 Implement GEO extraction from publications
4. 🔄 Implement hybrid merge/dedup logic
5. 🔄 Add search logs for transparency
6. 🔄 Test with user's examples
7. 🔄 Deploy and monitor

---

## Appendix: Alternative Approaches Considered

### Approach A: Pre-computed Publication→GEO Map
**Idea**: Build a database mapping all publications to their GEO IDs

**Pros**: Ultra-fast lookup, no API calls needed

**Cons**: Requires massive indexing effort, maintenance burden, data staleness

**Verdict**: ❌ Too complex for now, consider for Phase 2

### Approach B: Semantic Similarity on GEO Metadata
**Idea**: Use embeddings to find similar datasets even without keyword match

**Pros**: Finds conceptually related datasets

**Cons**: Doesn't solve the problem (GEO metadata is still sparse)

**Verdict**: ❌ Doesn't address root cause

### Approach C: GEO Metadata Enrichment
**Idea**: Enrich GEO metadata by pulling info from linked publications

**Pros**: Improves GEO search directly

**Cons**: Requires pre-processing all GEO datasets, API-intensive

**Verdict**: 🤔 Good long-term enhancement, but hybrid search is simpler

### Approach D: Hybrid (Chosen)
**Verdict**: ✅ Best balance of effectiveness, simplicity, and performance

