# Critical Fixes - October 13, 2025

## Issues to Address

### Issue 1: URL Collection Not Finding Open Access Papers
**Problem**: PMID 41034176 is Open Access but system only found paywalled URLs
- Only found: institutional (403), unpaywall (403)
- Missing: Open Access version from publisher

**Root Cause**: URL collection sources may not be:
1. Trying multiple URL patterns for same paper
2. Checking publisher OA status properly
3. Using all available identifiers (PMID, DOI, title)

**Solution**:
- [ ] Improve source implementations to try multiple URL patterns
- [ ] Add better OA detection (copyright checking)
- [ ] Ensure all sources use PMID, DOI, and title for lookups
- [ ] Add direct publisher OA checks

### Issue 2: Frontend "Download Papers" Only Gets Original Paper
**Problem**: System downloads paper that generated the dataset, NOT papers that cited it
- Users want to see how the dataset was USED, not how it was created
- Citation search exists in `geo_discovery.py` but not integrated with enrichment

**Solution**:
- [ ] Integrate citation discovery into `/enrich-fulltext` endpoint
- [ ] Change behavior: "Download Papers" = citing papers (NOT original paper)
- [ ] Original paper should still be downloaded but stored separately
- [ ] Map downloads to GEO ID: `data/pdfs/{geo_id}/citing/` and `data/pdfs/{geo_id}/original/`

### Issue 3: Storage Organization
**Problem**: PDFs not organized by GEO dataset

**Solution**:
```
data/pdfs/
  {geo_id}/
    original/          # Paper that generated the dataset
      {pmid}.pdf
    citing/           # Papers that cited/used the dataset
      {pmid}.pdf
    metadata.json     # Tracking info
```

## Implementation Steps

### Step 1: Fix URL Collection (HIGH PRIORITY)
**Files**: `omics_oracle_v2/lib/enrichment/fulltext/sources/*.py`

1. **Improve PMC Source** (`sources/pmc_client.py`)
   - Use PMID to get PMC ID via E-utilities
   - Try multiple URL patterns: `/pmc/articles/{PMCID}/pdf/`, etc.
   - Check for OA status in PMC metadata

2. **Improve Unpaywall Source** (`sources/unpaywall.py`)
   - Use DOI AND title for lookup
   - Check `is_oa` flag before returning URLs
   - Try `best_oa_location.url_for_pdf` first

3. **Add Publisher OA Check** (NEW source)
   - Query publisher API for OA status
   - Use Crossref API to check license info
   - Return direct OA URLs when available

### Step 2: Integrate Citation Search (CRITICAL)
**Files**: `omics_oracle_v2/api/routes/agents.py`

Modify `/enrich-fulltext` endpoint:

```python
@router.post("/enrich-fulltext")
async def enrich_fulltext(
    datasets: List[DatasetResponse],
    max_papers: int = Query(default=None),
    include_citations: bool = Query(
        default=True,  # NEW: Enable citation search by default
        description="Download papers that CITED this dataset (not just original paper)"
    ),
    max_citing_papers: int = Query(
        default=10,
        description="Maximum citing papers to download per dataset"
    ),
):
    """
    Enrich datasets with full-text content.

    By default, downloads papers that CITED the dataset (how it was used).
    Original paper that generated the dataset is stored separately.
    """

    for dataset in datasets:
        # 1. Download ORIGINAL paper (background - for reference)
        original_papers = await download_original_papers(dataset)

        # 2. Find CITING papers (what users want to see)
        if include_citations:
            citing_papers = await discover_and_download_citing_papers(
                dataset,
                max_citing_papers
            )
            dataset.fulltext = citing_papers  # Display citing papers in frontend
        else:
            dataset.fulltext = original_papers
```

### Step 3: Update Storage Structure
**Files**:
- `omics_oracle_v2/lib/enrichment/fulltext/pdf_downloader.py`
- `omics_oracle_v2/api/routes/agents.py`

```python
def get_pdf_path(geo_id: str, pmid: str, paper_type: str = "citing") -> Path:
    """
    Get organized PDF path.

    Args:
        geo_id: GEO dataset ID (e.g., "GSE12345")
        pmid: Publication PMID
        paper_type: "citing" or "original"

    Returns:
        Path: data/pdfs/{geo_id}/{paper_type}/{pmid}.pdf
    """
    base_dir = Path("data/pdfs") / geo_id / paper_type
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{pmid}.pdf"
```

## Testing Plan

### Test 1: Verify URL Collection Improvements
```python
# Should find Open Access version
pub = Publication(pmid="41034176", doi="10.1111/imm.70047")
urls = await fulltext_manager.get_all_fulltext_urls(pub)

# Should have multiple sources including OA version
assert len(urls.all_urls) > 2
assert any("Open Access" in str(u.metadata) for u in urls.all_urls)
```

### Test 2: Verify Citation Integration
```python
# Should download citing papers, not just original
datasets = [DatasetResponse(geo_id="GSE12345", pubmed_ids=["12345"])]
enriched = await enrich_fulltext(datasets, include_citations=True)

# Should have citing papers
assert len(enriched[0].fulltext) > 0
assert enriched[0].fulltext[0].citation_context  # Citing paper metadata
```

### Test 3: Verify Storage Organization
```python
geo_id = "GSE12345"
original_dir = Path(f"data/pdfs/{geo_id}/original")
citing_dir = Path(f"data/pdfs/{geo_id}/citing")

assert original_dir.exists()
assert citing_dir.exists()
assert len(list(citing_dir.glob("*.pdf"))) > 0
```

## Priority

1. **IMMEDIATE**: Integrate citation search into enrichment endpoint
2. **HIGH**: Improve URL collection to find OA versions
3. **MEDIUM**: Update storage structure
4. **LOW**: Add publisher OA checks (nice-to-have)

## Expected Outcome

After fixes:
- ✅ "Download Papers" button downloads papers that CITED the dataset
- ✅ System finds Open Access versions (not just paywalled URLs)
- ✅ PDFs organized by GEO ID and paper type
- ✅ Original paper stored separately for reference
- ✅ Users can see how their dataset was USED in research

## Notes

- Keep original paper download in background (don't remove functionality)
- Frontend should display CITING papers by default
- Add toggle in UI: "Show original paper" vs "Show citing papers"
- Maintain backward compatibility with existing API
