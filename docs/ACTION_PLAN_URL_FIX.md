# Action Plan - URL Collection Bug Fix

**Date**: October 14, 2025
**Goal**: Fix PMID 41034176 bug using our unified URL system

---

## Problem

**PMID 41034176**: Open Access paper but waterfall fix only found paywalled URLs (institutional, unpaywall 403).

**Root Cause**: PMC source not trying multiple URL patterns.

---

## Solution (Using Unified URL System)

### Phase 1: Fix PMC Source (3 hours) ⭐ START HERE

**File**: `omics_oracle_v2/lib/enrichment/fulltext/sources/pmc.py`

**Changes**:

```python
async def get_fulltext_url(self, publication: PubMedPublication) -> FullTextResult:
    """Get PMC URL with multiple pattern attempts"""

    # Try multiple URL patterns (in priority order)
    url_patterns = [
        # Pattern 1: Direct PDF (highest priority)
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/",

        # Pattern 2: FTP mirror (also PDF)
        f"https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{subdir}/PMC{pmcid}.pdf",

        # Pattern 3: EuropePMC PDF
        f"https://europepmc.org/articles/PMC{pmcid}?pdf=render",

        # Pattern 4: PMC reader (landing page, last resort)
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/?report=reader",
    ]

    # Classify and prioritize each URL
    classified_urls = []
    for url in url_patterns:
        url_type = URLValidator.classify_url(url)
        classified_urls.append({
            "url": url,
            "type": url_type,
            "priority": 1 if url_type == URLType.PDF_DIRECT else 3
        })

    # Try each URL (PDF first)
    for item in sorted(classified_urls, key=lambda x: x["priority"]):
        if await self._check_url_accessible(item["url"]):
            return FullTextResult(
                success=True,
                url=item["url"],
                source=FullTextSource.PMC,
                metadata={
                    "url_type": item["type"].value,
                    "pattern": "multiple_patterns"
                }
            )

    return FullTextResult(success=False, error="No PMC URLs accessible")
```

**Test**:
```bash
# Test with PMID 41034176 specifically
python -c "
from omics_oracle_v2.lib.enrichment.fulltext.sources.pmc import PMCSource
import asyncio

async def test():
    source = PMCSource()
    pub = PubMedPublication(pmid='41034176', pmcid='PMC11460852')
    result = await source.get_fulltext_url(pub)
    print(f'Success: {result.success}')
    print(f'URL: {result.url}')
    print(f'Type: {result.metadata.get(\"url_type\")}')

asyncio.run(test())
"
```

### Phase 2: Enhance Unpaywall (2 hours)

**File**: `omics_oracle_v2/lib/enrichment/fulltext/sources/unpaywall.py`

**Changes**:
1. Check OA status BEFORE returning URL
2. Try alternative URLs from Unpaywall response
3. Classify URL types

```python
async def get_fulltext_url(self, publication):
    """Enhanced Unpaywall with OA checking"""

    # ... fetch from API ...

    # Check if truly OA
    if not response.get("is_oa"):
        return FullTextResult(success=False, error="Not Open Access")

    # Try all available locations
    locations = response.get("oa_locations", [])
    for location in sorted(locations, key=lambda x: x.get("evidence") == "open"):
        url = location["url"]

        # Classify URL
        url_type = URLValidator.classify_url(url)

        # Try URL
        if await self._check_accessible(url):
            return FullTextResult(
                success=True,
                url=url,
                source=FullTextSource.UNPAYWALL,
                metadata={
                    "url_type": url_type.value,
                    "evidence": location.get("evidence")
                }
            )

    return FullTextResult(success=False, error="No accessible Unpaywall URLs")
```

### Phase 3: Store URL Types in Registry (1 hour)

**File**: `omics_oracle_v2/lib/registry/geo_registry.py`

**Add column to publications table**:
```python
# In _init_schema()
CREATE TABLE IF NOT EXISTS publications (
    ...
    urls TEXT,  -- Change structure to include url_type
    ...
)

# URLs stored as:
[
    {
        "url": "...",
        "source": "pmc",
        "priority": 1,
        "url_type": "pdf_direct",  # ✅ ADD THIS
        "metadata": {}
    }
]
```

**File**: `omics_oracle_v2/api/routes/agents.py` (line ~890)

**Classify URLs before storing**:
```python
# In registry integration
for url_info in paper["all_urls"]:
    # Classify URL if not already classified
    url_type = url_info.get("url_type")
    if not url_type:
        url_type = URLValidator.classify_url(url_info["url"]).value

    # Store with type
    url_info["url_type"] = url_type
```

---

## Testing Plan

### Test 1: PMID 41034176 (Original Bug)

```bash
# Test full workflow
curl -X POST http://localhost:8000/api/enrich-fulltext \
  -H "Content-Type: application/json" \
  -d '{
    "datasets": [{
      "geo_id": "GSE279807",
      "pubmed_ids": ["41034176"]
    }],
    "include_citing_papers": false,
    "download_original": true
  }'

# Check if PMC URL found
cat data/pdfs/GSE279807/metadata.json | jq '.papers.original[0].all_urls[] | select(.source == "pmc")'

# Expected: Should see PMC URL with type "pdf_direct"
```

### Test 2: Multiple URL Patterns

```python
# Unit test
@pytest.mark.asyncio
async def test_pmc_multiple_patterns():
    """Test PMC tries multiple URL patterns"""
    source = PMCSource()
    pub = PubMedPublication(pmid="41034176", pmcid="PMC11460852")

    result = await source.get_fulltext_url(pub)

    assert result.success, "Should find PMC URL"
    assert "pmc" in result.url.lower(), "Should be PMC URL"
    assert result.metadata["url_type"] == "pdf_direct", "Should be direct PDF"
```

### Test 3: URL Type Storage

```python
# Integration test
def test_url_types_stored_in_registry():
    """Test URL types preserved in registry"""
    registry = get_registry()
    data = registry.get_complete_geo_data("GSE279807")

    original_paper = data["papers"]["original"][0]
    for url in original_paper["urls"]:
        assert "url_type" in url, "URL should have type"
        assert url["url_type"] in ["pdf_direct", "landing_page", "html_fulltext", "doi_resolver", "unknown"]
```

---

## Expected Results

### Before Fix:
```json
{
  "papers": {
    "original": [{
      "pmid": "41034176",
      "all_urls": [
        {"url": "https://onlinelibrary.wiley.com/doi/10.1111/imm.13862", "source": "institutional", "priority": 1},
        {"url": "https://api.unpaywall.org/...", "source": "unpaywall", "priority": 2}
      ]
    }]
  }
}
// ❌ Both return 403 Forbidden
```

### After Fix:
```json
{
  "papers": {
    "original": [{
      "pmid": "41034176",
      "all_urls": [
        {"url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11460852/pdf/", "source": "pmc", "priority": 2, "url_type": "pdf_direct"},
        {"url": "https://europepmc.org/articles/PMC11460852?pdf=render", "source": "pmc", "priority": 2, "url_type": "pdf_direct"},
        {"url": "https://onlinelibrary.wiley.com/doi/10.1111/imm.13862", "source": "institutional", "priority": 1, "url_type": "landing_page"},
        {"url": "https://api.unpaywall.org/...", "source": "unpaywall", "priority": 2, "url_type": "unknown"}
      ]
    }]
  }
}
// ✅ PMC PDFs should work!
```

---

## Implementation Order

1. **✅ Phase 1**: Fix PMC source (3 hours) - **START HERE**
2. **✅ Phase 2**: Enhance Unpaywall (2 hours)
3. **✅ Phase 3**: Store URL types (1 hour)
4. **✅ Test**: Validate with PMID 41034176

**Total Time**: ~6 hours

---

## Success Criteria

✅ PMID 41034176 downloads successfully
✅ PMC URL found with type "pdf_direct"
✅ Multiple PMC patterns tried
✅ URL types stored in registry
✅ All tests pass

---

## Notes

- Start fresh: `rm -rf data/pdfs/* data/cache/* data/omics_oracle.db`
- Focus on PMC fix first (biggest impact)
- Leverage existing URLValidator (already built!)
- Test with real PMID after each phase

Ready to implement? Start with Phase 1!
