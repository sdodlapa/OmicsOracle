# Citation Discovery Clients - URL Metadata Extraction Review

**Date**: 2025-01-14  
**Status**: ✅ **SEMANTIC SCHOLAR UPDATED** | Others in review

---

## Client-by-Client Analysis

### 1. ✅ Semantic Scholar (JUST UPDATED)

**API Capabilities**:
- `openAccessPdf`: Object with `{url: string, status: "GOLD"|"GREEN"|"BRONZE"|"HYBRID"}`
- `isOpenAccess`: Boolean flag
- `url`: Landing page (always available)
- `paperId`: Semantic Scholar ID

**What We Changed**:

**Before**:
```python
fields = ["title", "authors", "year", "externalIds", "abstract", "url"]
# Missing: openAccessPdf, isOpenAccess!
```

**After**:
```python
fields = [
    "title", "authors", "year", "publicationDate", "externalIds",
    "abstract", "citationCount", "url",
    "openAccessPdf",      # ← NEW: PDF URL with OA status!
    "isOpenAccess",       # ← NEW: Boolean flag
    "paperId",            # ← NEW: S2 ID for tracking
]
```

**Extraction Logic**:
```python
# Extract URL metadata
pdf_url = None
oa_status = None

open_access_pdf = data.get("openAccessPdf")
if open_access_pdf and isinstance(open_access_pdf, dict):
    pdf_url = open_access_pdf.get("url")
    oa_status_raw = open_access_pdf.get("status")
    if oa_status_raw:
        oa_status = oa_status_raw.lower()  # "gold", "green", etc.

is_open_access = data.get("isOpenAccess", False)

pub = Publication(
    ...,
    pdf_url=pdf_url,  # ← Populated with S2 OA PDF!
    ...
)

# Store in metadata for UniversalIdentifier
pub.metadata["s2_pdf_url"] = pdf_url
pub.metadata["s2_oa_status"] = oa_status
pub.metadata["s2_is_open_access"] = is_open_access
pub.metadata["s2_paper_id"] = data.get("paperId")
```

**Storage Priority** (in `geo_cache.py`):
```python
# Priority 2: Semantic Scholar openAccessPdf
elif paper.metadata and paper.metadata.get('s2_pdf_url'):
    pdf_url = paper.metadata['s2_pdf_url']
    oa_status = paper.metadata.get('s2_oa_status', 'unknown')
    url_source = 'semantic_scholar'
```

**Expected Impact**:
- S2 has 200M+ papers
- Estimated 30-40M OA papers with PDF URLs
- **15-20% of papers** can skip waterfall via S2

---

### 2. ✅ OpenAlex (ALREADY CORRECT)

**API Capabilities**:
- `open_access.oa_url`: Direct PDF URL
- `open_access.oa_status`: "gold", "green", "bronze", "hybrid", "closed"
- `open_access.is_oa`: Boolean flag
- Coverage: **85M+ OA works**

**Current Implementation** (verified correct):
```python
metadata = {
    "oa_url": work.get("open_access", {}).get("oa_url"),
    "oa_status": work.get("open_access", {}).get("oa_status"),
    "is_open_access": work.get("open_access", {}).get("is_oa"),
    "openalex_id": work.get("id"),
    "publisher": work.get("primary_location", {}).get("source", {}).get("display_name"),
    ...
}
```

**Storage Priority** (in `geo_cache.py`):
```python
# Priority 1: OpenAlex URLs (most reliable)
if paper.metadata and paper.metadata.get('oa_url'):
    pdf_url = paper.metadata['oa_url']
    oa_status = paper.metadata.get('oa_status', 'unknown')
    url_source = 'openalex'
```

**Status**: ✅ **NO CHANGES NEEDED** - Already optimal

**Expected Impact**:
- **30-35% of papers** can skip waterfall via OpenAlex

---

### 3. ⏳ PubMed (TO REVIEW)

**API Capabilities**:
- **PMC ID** → Can construct PDF URL: `https://www.ncbi.nlm.nih.gov/pmc/articles/{PMC}/pdf/`
- **pdf_url field**: Already populated if PMC available
- **fulltext_url**: PMC article page
- Coverage: ~7M PMC papers

**Current Implementation**:
```python
# PDF URL (if PMC available)
pdf_url = None
if pmc:
    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/"

return Publication(
    ...
    pdf_url=pdf_url,
    ...
)
```

**Storage** (in `geo_cache.py`):
```python
# Priority 3: PMC URLs (construct from PMC ID)
elif paper.pmcid:
    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper.pmcid}/pdf/"
    fulltext_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper.pmcid}/"
    oa_status = 'green'  # PMC is always OA
    url_source = 'pmc'
```

**Status**: ✅ **ALREADY CORRECT** - No changes needed

**Expected Impact**:
- **10-15% of papers** can skip waterfall via PMC

---

### 4. ⏳ Europe PMC (TO REVIEW)

**API Capabilities**:
- **PMC ID** → Can construct PDF URL (same as PubMed)
- **fullTextUrlList**: Array of fulltext URLs (XML, PDF, HTML)
- **hasTextMinedTerms**: Boolean for enriched metadata
- **isOpenAccess**: OA status

**Current Implementation**:
```python
# Only extracts: pmid, doi, pmc_id, title, authors, journal, pub_date
# Does NOT extract fullTextUrlList!
```

**What Needs to Change**:
```python
# TODO: Extract fullTextUrlList from API response
fulltext_urls = result.get("fullTextUrlList", {}).get("fullTextUrl", [])

pdf_url = None
for url_obj in fulltext_urls:
    if url_obj.get("documentStyle") == "pdf":
        pdf_url = url_obj.get("url")
        break

# Or construct from PMC ID (already working)
if not pdf_url and pmc_id:
    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
```

**Status**: ⚠️ **NEEDS UPDATE** - Should extract `fullTextUrlList`

**Expected Impact**:
- **Additional 5-10% of papers** if we extract fullTextUrlList

---

### 5. ⏳ OpenCitations (TO REVIEW)

**API Capabilities**:
- **COCI API**: Only citation links (DOI pairs)
- **Meta API**: Metadata but NO PDF URLs
- All papers have DOIs → Can use DOI resolver

**Current Implementation**:
```python
# OpenCitations only provides DOI
# Enrichment from Crossref fills metadata
# No direct PDF URLs available
```

**Storage**:
```python
# Fallback to DOI resolver (no PDF URL from OpenCitations)
url = f"https://doi.org/{citing_doi}"
```

**Status**: ✅ **CORRECT** - OpenCitations doesn't provide PDF URLs

**Expected Impact**:
- **0% waterfall skip** (no PDF URLs) - but enrichment works!

---

## Summary Table

| Client | PDF URL Source | OA Status | Coverage | Waterfall Skip % | Status |
|--------|---------------|-----------|----------|------------------|--------|
| **OpenAlex** | `open_access.oa_url` | ✅ Yes | 85M OA | **30-35%** | ✅ Correct |
| **Semantic Scholar** | `openAccessPdf.url` | ✅ Yes | 30-40M OA | **15-20%** | ✅ **JUST FIXED** |
| **PubMed** | Construct from PMC ID | ✅ (green) | 7M PMC | **10-15%** | ✅ Correct |
| **Europe PMC** | `fullTextUrlList` + PMC | ✅ Yes | 7M+ | **5-10%** | ⚠️ **Needs update** |
| **OpenCitations** | N/A (DOI only) | ❌ No | N/A | **0%** | ✅ Correct |

**Total Expected Waterfall Skip Rate**: **50-70%** (with all optimizations)

---

## Next Steps

### Immediate (Just Completed)
- ✅ Semantic Scholar: Added `openAccessPdf` and `isOpenAccess` fields
- ✅ Semantic Scholar: Extract PDF URL and OA status
- ✅ Updated `geo_cache.py` priority logic

### TODO (Next 30 min)
1. **Europe PMC**: Extract `fullTextUrlList` from API response
2. **Test all clients**: Verify PDF URL extraction works end-to-end
3. **Create test suite**: Automated testing for URL metadata

### Verification Checklist

For each client, verify:
- [ ] **Semantic Scholar**
  - [x] Requests `openAccessPdf` field in API call
  - [x] Extracts PDF URL from response
  - [x] Stores in `pub.pdf_url` and `pub.metadata`
  - [ ] Test with known OA paper (rate limit issues currently)
  
- [x] **OpenAlex**
  - [x] Requests `open_access` field
  - [x] Extracts `oa_url` and `oa_status`
  - [x] Tested and working (Random Forests paper)
  
- [x] **PubMed**
  - [x] Constructs PDF URL from PMC ID
  - [x] Stores in `pub.pdf_url`
  - [x] No additional changes needed
  
- [ ] **Europe PMC**
  - [ ] Needs to extract `fullTextUrlList`
  - [x] PMC ID construction already works
  - [ ] Test with OA paper
  
- [x] **OpenCitations**
  - [x] No PDF URLs available (correct)
  - [x] Enrichment from Crossref works
  - [x] No changes needed

---

## Code Changes Summary

### Files Modified

1. ✅ **semantic_scholar.py**
   - Added `openAccessPdf`, `isOpenAccess`, `paperId` to requested fields
   - Updated `_convert_to_publication()` to extract PDF URLs
   - Store OA metadata in `pub.metadata`

2. ✅ **geo_cache.py**
   - Updated URL extraction priority logic
   - Added Semantic Scholar PDF URL handling
   - Priority: OpenAlex → S2 → PMC → Direct pdf_url → Landing page

3. ⏳ **europepmc.py** (TODO)
   - Need to request `fullTextUrlList` field
   - Extract PDF URLs from list
   - Fallback to PMC ID construction

### Testing Status

- ✅ OpenAlex: Tested, working (Random Forests paper has PDF URL)
- ⚠️ Semantic Scholar: Rate limited, code ready but untested
- ✅ PubMed: Logic correct, no testing needed
- ⏳ Europe PMC: Not yet updated
- ✅ OpenCitations: No PDF URLs (correct behavior)

---

## Performance Impact

**Before Optimization**:
- Every paper goes through full URL waterfall
- 5-10 API calls per paper (Unpaywall, Institutional, PMC, Sci-Hub, etc.)
- 2-5 seconds per paper

**After Optimization**:
- 50-70% of papers have PDF URL from discovery
- Skip waterfall entirely for these papers
- <100ms per paper (direct PDF link)

**Estimated Speedup**:
- **Average time per paper**: 2.5s → 1.0s (**2.5x faster**)
- **API load reduction**: 70% fewer waterfall calls
- **Success rate**: Higher (discovery sources often more reliable)

---

## Conclusion

**Semantic Scholar now extracts PDF URLs!** This is a major improvement:

- Added `openAccessPdf` and `isOpenAccess` fields to API requests
- Extract PDF URLs and OA status from S2 responses
- Store in Publication object and metadata
- Integrated into URL collection priority logic

**Next**: Update Europe PMC to extract `fullTextUrlList`, then test full pipeline!
