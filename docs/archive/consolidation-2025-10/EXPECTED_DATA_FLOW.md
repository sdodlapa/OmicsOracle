# Expected Data Flow - Phase 6 Pipeline (When Citations Work)

## Current State (Test Run)
```
Query: "breast cancer RNA-seq"
  ↓
GEO Search → 2 datasets found (GSE267442, GSE267552)
  ↓
Metadata Fetch → ✅ Complete (2.7 KB JSON)
  ↓
Citation Discovery → ⚠️ 0 papers (datasets have no pubmed_ids)
  ↓
Full-Text URLs → ⚠️ Skipped (no papers)
  ↓
PDF Download → ⚠️ Skipped (no URLs)
  ↓
Output: JSON metadata only
```

## Expected Flow (With Older Datasets Having Citations)

```
Query: "breast cancer 2016[PDAT]"
  ↓
GEO Search → 5 datasets found
  ↓
Metadata Fetch → ✅ Complete (e.g., GSE16791 has PMID: 23660628)
  ↓
Citation Discovery:
  ├─ Strategy A (Citation-based)
  │  └─ Find papers citing PMID 23660628
  │     └─ ~20-50 citing papers found
  │
  └─ Strategy B (Mention-based)
     └─ Find papers mentioning "GSE16791"
        └─ ~5-10 papers found
  ↓
Deduplicate → ~25-55 unique papers
  ↓
Full-Text URL Collection:
  ├─ Check Institutional Access → ~15 papers (60%)
  ├─ Check Unpaywall → ~8 papers (32%)
  ├─ Check CORE API → ~3 papers (12%)
  └─ Total coverage: ~26 papers (85%)
  ↓
PDF Download:
  ├─ Institutional: 15 PDFs (~15-30 MB)
  ├─ Unpaywall: 8 PDFs (~8-16 MB)
  └─ CORE: 3 PDFs (~3-6 MB)
  ↓
Output:
  ├─ geo_datasets.json (15 KB - 5 datasets)
  ├─ citing_papers.json (100 KB - 55 papers)
  ├─ collection_report.json (1 KB)
  └─ pdfs/ (26 PDFs, ~30-50 MB total)
```

## Full Example Output Structure

```
data/geo_citation_collections/breast_cancer_2016_20251010_180000/
│
├─ geo_datasets.json (15 KB)
│  └─ 5 GEO datasets with metadata
│
├─ citing_papers.json (100 KB)
│  └─ 55 papers with full metadata:
│     ├─ PMID, DOI, title, authors
│     ├─ Journal, year
│     ├─ fulltext_url
│     └─ fulltext_source
│
├─ collection_report.json (1 KB)
│  └─ Summary:
│     ├─ "datasets_found": 5
│     ├─ "citing_papers_found": 55
│     ├─ "fulltext_coverage": 85%
│     └─ "pdfs_downloaded": 26
│
└─ pdfs/
   ├─ institutional/
   │  ├─ 12345678.pdf (1.2 MB)
   │  ├─ 23456789.pdf (0.8 MB)
   │  └─ ... (15 total)
   │
   ├─ unpaywall/
   │  ├─ 34567890.pdf (1.5 MB)
   │  └─ ... (8 total)
   │
   └─ core/
      ├─ 45678901.pdf (0.9 MB)
      └─ ... (3 total)
```

## Data Volume Estimates

### Small Query (1-2 datasets, 20-30 papers)
- **JSON metadata:** 50-80 KB
- **PDFs:** 20-40 MB (assuming 80% coverage)
- **Total:** ~20-40 MB

### Medium Query (5-10 datasets, 100-200 papers)
- **JSON metadata:** 200-400 KB
- **PDFs:** 80-200 MB (assuming 80% coverage)
- **Total:** ~80-200 MB

### Large Query (20+ datasets, 500+ papers)
- **JSON metadata:** 1-2 MB
- **PDFs:** 400-800 MB (assuming 80% coverage)
- **Total:** ~400-800 MB

## Actual vs Expected - Comparison

| Metric | Current Test | Expected (With Citations) |
|--------|--------------|---------------------------|
| Datasets | 2 | 5 |
| Papers | 0 | 55 |
| Full-text coverage | N/A | 85% |
| PDFs downloaded | 0 | 26 |
| JSON size | 2.8 KB | 115 KB |
| PDF size | 0 MB | 30-50 MB |
| Total size | 2.8 KB | 30-50 MB |

## Why Current Test Shows Empty Results

1. **Datasets are too new (2024-2025)**
   - Not yet published in peer-reviewed journals
   - No PubMed IDs assigned
   - No papers can cite them yet

2. **Empty pubmed_ids arrays**
   ```json
   "pubmed_ids": []  ← No PMIDs to search citations for
   ```

3. **Citation discovery skipped**
   - Strategy A needs PMID → No PMID available
   - Strategy B searches PubMed → Found 0 results (datasets too new)

## What Happens With Older Datasets

Using GSE16791 (from our citation test) as example:

```json
{
  "geo_id": "GSE16791",
  "title": "Expression data from CD138+ cells from MM patients",
  "pubmed_ids": ["23660628"],  ← Has PMID!
  "sample_count": 32
}
```

**This enables:**
1. ✅ Strategy A: Find papers citing PMID 23660628
2. ✅ Strategy B: Find papers mentioning "GSE16791"
3. ✅ Get full-text URLs for citing papers
4. ✅ Download PDFs from available sources

## Next Session Goals

1. **Fix citation discovery** (2 minor issues)
2. **Test with older datasets** (2015-2018 era)
3. **Verify full pipeline** with real citations
4. **Measure actual coverage** and performance
5. **Validate PDF downloads** work correctly

## Documentation Files

- ✅ `DATA_ORGANIZATION.md` - Current structure
- ✅ `EXPECTED_DATA_FLOW.md` - This file
- ✅ `PHASE_6_IMPLEMENTATION_COMPLETE.md` - Session summary
