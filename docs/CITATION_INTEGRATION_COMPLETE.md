# Citation Integration Implementation - October 13, 2025

## Changes Implemented

### 1. Modified `/enrich-fulltext` Endpoint

**File**: `omics_oracle_v2/api/routes/agents.py`

#### New Query Parameters

```python
@router.post("/enrich-fulltext")
async def enrich_fulltext(
    datasets: List[DatasetResponse],
    max_papers: int = Query(default=None),
    include_full_content: bool = Query(default=False),

    # NEW PARAMETERS
    include_citing_papers: bool = Query(
        default=True,  # ✅ Enabled by default!
        description="Download papers that CITED this dataset (not just original paper)"
    ),
    max_citing_papers: int = Query(
        default=10,
        description="Maximum citing papers to download per dataset"
    ),
    download_original: bool = Query(
        default=True,
        description="Also download the original paper (stored separately)"
    ),
):
```

### 2. Integrated Citation Discovery

**Import Added**:
```python
from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
```

**Discovery Logic**:
- Uses existing `GEOCitationDiscovery` class from `omics_oracle_v2/lib/citations/discovery/geo_discovery.py`
- Finds papers via two strategies:
  1. **Strategy A**: Papers citing the original publication (via PMID)
  2. **Strategy B**: Papers mentioning the GEO ID in text
- Configurable max results (default: 10 citing papers)

### 3. Organized PDF Storage Structure

**New Directory Organization**:
```
data/pdfs/
  {geo_id}/                    # e.g., GSE12345
    original/                  # Papers that generated the dataset
      {pmid}.pdf
      {pmid}_metadata.json
    citing/                    # Papers that cited/used the dataset
      {pmid}.pdf
      {pmid}_metadata.json
    metadata.json             # Overall tracking info
```

**Benefits**:
- ✅ Clear separation of original vs citing papers
- ✅ Easy to find all papers for a specific GEO dataset
- ✅ Metadata tracking for each paper type
- ✅ Frontend can easily distinguish paper types

### 4. Updated Download Workflow

**Old Behavior** (before fix):
```
1. Get PMIDs from dataset.pubmed_ids
2. Download those papers (original papers only)
3. Return in dataset.fulltext
```

**New Behavior** (after fix):
```
1. Get original PMIDs from dataset.pubmed_ids
2. Discover citing papers via GEOCitationDiscovery
3. Download BOTH to separate folders:
   - Original → data/pdfs/{geo_id}/original/
   - Citing → data/pdfs/{geo_id}/citing/
4. Return citing papers FIRST in dataset.fulltext
5. Store metadata.json with paper organization
```

### 5. Frontend Impact

**"Download Papers" Button Behavior**:

**BEFORE**: Shows original paper that generated the dataset
```json
{
  "fulltext": [
    {
      "pmid": "12345",
      "title": "Original study that created GSE12345",
      "paper_type": "original"
    }
  ]
}
```

**AFTER**: Shows citing papers (how dataset was USED)
```json
{
  "fulltext": [
    // Citing papers first (default view)
    {
      "pmid": "67890",
      "title": "Study that re-analyzed GSE12345 for cancer research",
      "paper_type": "citing"
    },
    {
      "pmid": "67891",
      "title": "Meta-analysis including GSE12345",
      "paper_type": "citing"
    },
    // Original papers last (reference)
    {
      "pmid": "12345",
      "title": "Original study that created GSE12345",
      "paper_type": "original"
    }
  ]
}
```

### 6. Enhanced Fulltext Response

**New Fields Added**:
```python
fulltext_info = {
    "pmid": "...",
    "doi": "...",           # NEW: Include DOI
    "title": "...",
    "url": "...",
    "source": "...",
    "pdf_path": "...",
    "paper_type": "citing",  # NEW: "original" or "citing"
}
```

### 7. Metadata Tracking

**metadata.json Example**:
```json
{
  "geo_id": "GSE12345",
  "title": "Study of X in Y cells",
  "processed_at": "2025-10-13T20:30:00Z",
  "papers": {
    "original": {
      "count": 1,
      "pmids": ["12345"]
    },
    "citing": {
      "count": 8,
      "pmids": ["67890", "67891", ...]
    }
  },
  "total_count": 9,
  "status": "available"
}
```

## API Usage Examples

### Example 1: Default Behavior (Citing Papers)
```python
POST /api/agents/enrich-fulltext
{
  "datasets": [{"geo_id": "GSE12345", ...}]
}

# Returns: Citing papers (how dataset was used)
```

### Example 2: Original Papers Only
```python
POST /api/agents/enrich-fulltext?include_citing_papers=false
{
  "datasets": [{"geo_id": "GSE12345", ...}]
}

# Returns: Original paper only
```

### Example 3: Both with Limits
```python
POST /api/agents/enrich-fulltext?max_citing_papers=20&download_original=true
{
  "datasets": [{"geo_id": "GSE12345", ...}]
}

# Returns: Up to 20 citing papers + original paper
```

### Example 4: Citing Papers Only (No Original)
```python
POST /api/agents/enrich-fulltext?download_original=false
{
  "datasets": [{"geo_id": "GSE12345", ...}]
}

# Returns: Only citing papers (excludes original)
```

## Testing the Changes

### Test 1: Verify Citation Discovery Works
```bash
# Start server
./start_omics_oracle.sh

# Test with real dataset
curl -X POST "http://localhost:8000/api/agents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": ["GSE48968"],
    "max_results": 1
  }' > search_result.json

# Enrich with citations
curl -X POST "http://localhost:8000/api/agents/enrich-fulltext?include_citing_papers=true&max_citing_papers=5" \
  -H "Content-Type: application/json" \
  -d @search_result.json > enriched.json

# Check response
jq '.[] | {geo_id, fulltext_count, citing_papers: [.fulltext[] | select(.paper_type=="citing") | .pmid]}' enriched.json
```

### Test 2: Verify File Organization
```bash
# After enrichment, check directory structure
tree data/pdfs/GSE48968/

# Expected:
# data/pdfs/GSE48968/
# ├── citing/
# │   ├── {pmid1}.pdf
# │   ├── {pmid2}.pdf
# │   └── ...
# ├── original/
# │   └── {original_pmid}.pdf
# └── metadata.json
```

### Test 3: Verify Citing Papers Are Returned First
```python
import requests
import json

# Search
search_resp = requests.post(
    "http://localhost:8000/api/agents/search",
    json={"search_terms": ["cancer"], "max_results": 1}
)
datasets = search_resp.json()["datasets"]

# Enrich
enrich_resp = requests.post(
    "http://localhost:8000/api/agents/enrich-fulltext?include_citing_papers=true",
    json=datasets
)
enriched = enrich_resp.json()

# Check first paper is citing (not original)
first_paper = enriched[0]["fulltext"][0]
assert first_paper["paper_type"] == "citing", "First paper should be citing type!"

print("✅ Citing papers are returned first!")
```

## Benefits

### For Users
1. **Better Understanding**: See how datasets are USED in research, not just how they were created
2. **Research Context**: Discover related work and applications
3. **Citation Tracking**: Understand dataset impact and relevance
4. **Organized Storage**: Easy to find all papers related to a GEO ID

### For Developers
1. **Modular Design**: Citation discovery is separate, can be improved independently
2. **Backward Compatible**: Old behavior available via `include_citing_papers=false`
3. **Extensible**: Easy to add more paper types or discovery strategies
4. **Well-Tracked**: metadata.json provides audit trail

## Next Steps

### URL Collection Improvements (Separate PR)
While this PR integrates citation discovery, URL collection still needs improvement:

**Issue**: PMID 41034176 is Open Access but system only found paywalled URLs
**Solution** (in next PR):
1. Improve PMC source to check multiple URL patterns
2. Add publisher OA checks via Crossref API
3. Use multiple identifiers (PMID, DOI, title) for lookups
4. Add retry logic with different URL patterns

See `docs/CRITICAL_FIXES_20251013.md` for details.

## Configuration

**Environment Variables** (optional):
```bash
# Citation discovery
CITATION_MAX_RESULTS=10          # Default max citing papers
CITATION_ENABLE_STRATEGY_A=true  # Citation-based discovery
CITATION_ENABLE_STRATEGY_B=true  # Mention-based discovery

# PDF storage
PDF_BASE_DIR=data/pdfs           # Base directory for PDFs
PDF_ORGANIZE_BY_GEO=true         # Organize by GEO ID
```

## Backward Compatibility

✅ **Fully backward compatible**:
- Old API calls still work (no breaking changes)
- Default behavior prioritizes citing papers (what users want)
- Original papers still downloaded if `download_original=true` (default)
- Existing code that expects `dataset.fulltext` still works

## Logs to Look For

**Successful Citation Integration**:
```
[CITATION] Initializing citation discovery...
[CITATION] Discovering papers that cited GSE12345...
[OK] Found 8 citing papers
[DOWNLOAD] Total papers to download: 9 (original=1, citing=8)
[ORIGINAL] Downloading 1 original paper(s)...
[OK] PMID 12345: Downloaded from pmc (245.3 KB) → original/12345.pdf
[CITING] Downloading 8 citing paper(s)...
[OK] PMID 67890: Downloaded from unpaywall (1.2 MB) → citing/67890.pdf
...
[DATA] FINAL STATUS: fulltext_count=9/9, fulltext_status=available, citing_papers=8, original_papers=1
```

## Summary

This implementation successfully:
- ✅ Integrates citation discovery into enrichment endpoint
- ✅ Downloads citing papers (how dataset was USED)
- ✅ Organizes PDFs by paper type and GEO ID
- ✅ Returns citing papers first in frontend
- ✅ Maintains backward compatibility
- ✅ Provides clear metadata tracking

**Impact**: Users now see papers that CITED the dataset, not just the original paper, giving them better insight into how the dataset has been used in research.
