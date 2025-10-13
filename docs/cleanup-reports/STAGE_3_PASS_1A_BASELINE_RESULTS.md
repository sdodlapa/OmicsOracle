# Stage 3 Pass 1a - Baseline Test Results

**Date**: 2025-10-12
**Test**: Baseline before removing duplicate preprocessing
**Status**: ✅ COMPLETE - All 5 queries successful

---

## Test Fixes Applied

1. **Fixed GEO model attribute**: Changed `dataset.accession` → `dataset.geo_id`
2. **Disabled async features**: Turned off fulltext/PDF download to avoid asyncio event loop conflicts
3. **Fixed publication_date handling**: Added type checking for datetime vs string

---

## Baseline Results Summary

| Metric | Value |
|--------|-------|
| **Total queries** | 5 |
| **Successful** | 5 (100%) |
| **Failed** | 0 |
| **Avg latency** | 31.4 seconds |
| **Avg GEO results** | 10.2 datasets |
| **Avg publications** | 8.0 papers |

---

## Query-by-Query Results

### Query 1: "diabetes RNA-seq"
- **Latency**: 96.2ms (FAST - cache/simple query)
- **Query type**: GEO
- **GEO datasets**: 10
- **Publications**: 0
- **Top result**: GSE271480 - IRE1α and XBP1 in β-cells of NOD mice

### Query 2: "cancer genomics BRCA1"
- **Latency**: 41.6 seconds (publication search)
- **Query type**: Hybrid (GEO + Publications)
- **GEO datasets**: 11
- **Publications**: 10
- **Top GEO**: GSE288315 - BRCA1-associated breast tumors
- **Top pub**: [2025] Androgen receptor-mediated regulation of BRCA1

### Query 3: "Alzheimer's disease proteomics"
- **Latency**: 39.2 seconds
- **Query type**: Hybrid
- **GEO datasets**: 10
- **Publications**: 10
- **Top GEO**: GSE220548 - iPSC-derived mononuclear phagocytes
- **Top pub**: [2025] HIF-1alpha-dependent paracrine factors

### Query 4: "CRISPR gene editing"
- **Latency**: 35.9 seconds
- **Query type**: Hybrid
- **GEO datasets**: 10
- **Publications**: 10
- **Top GEO**: GSE309443 - PTPN2 targeting in CAR T cells
- **Top pub**: [2025] Efficient CRISPR/Cas-based gene editing in cotton

### Query 5: "COVID-19 vaccine development"
- **Latency**: 40.0 seconds
- **Query type**: Hybrid
- **GEO datasets**: 10
- **Publications**: 10
- **Top GEO**: GSE219098 - B Cell responses to mRNA-1273 vaccine
- **Top pub**: [2025] Vaccination rates among long-term care staff

---

## Performance Observations

### Fast Queries (< 1 second)
- **Query 1** (96ms): Simple GEO-only query, likely hit cache or used fast path

### Slow Queries (35-42 seconds)
- **Queries 2-5**: All hybrid searches with publication enrichment
- **Bottleneck**: Publication search (PubMed + OpenAlex API calls)
- **Note**: This is BEFORE removing duplicate preprocessing

### Expected Improvements After Pass 1a
- **Target**: 10-20% latency reduction by removing duplicate NER/preprocessing
- **Current**: NER runs TWICE (once in QueryOptimizer, once in PublicationSearchPipeline)
- **After cleanup**: NER runs ONCE → faster preprocessing

---

## Validation Criteria for Pass 1a

After removing duplicate preprocessing, we should see:

✅ **Result counts**: Within ±10% (9-11 GEO, 7-9 publications)
✅ **Top results**: Same datasets/papers in top 3
✅ **Latency**: Similar or 10-20% faster (target: 28-32 seconds for hybrid queries)
✅ **Query optimization**: Still working (optimized_query present)
✅ **No errors**: All 5 queries complete successfully

---

## Next Steps

1. ✅ **Baseline established** - All queries working
2. 🔄 **Remove duplicate preprocessing** - Delete ~160 LOC from PublicationSearchPipeline
3. 🔄 **Run validation test** - Compare with baseline
4. 🔄 **If pass validation** - Proceed to Pass 1b (remove SearchAgent)

---

## Raw Data

Full results saved to: `data/test_results/stage3_pass1a_baseline.json`
