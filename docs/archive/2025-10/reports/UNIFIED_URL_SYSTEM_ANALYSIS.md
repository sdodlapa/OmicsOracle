# Unified URL System - Complete Analysis

**Date**: October 14, 2025
**Status**: ✅ **IMPLEMENTED AND IN USE**

## Executive Summary

Yes, we **DO have** a unified/standardized URL system! It's implemented in `url_validator.py` and actively used throughout the fulltext collection pipeline. Here's what we have and how we can leverage it better.

---

## Current Implementation

### 1. URL Classification System (`url_validator.py`)

**Purpose**: Classify URLs WITHOUT making HTTP requests, using pattern matching and domain knowledge.

**URL Types** (`URLType` enum):
```python
class URLType(str, Enum):
    PDF_DIRECT = "pdf_direct"          # Direct PDF link - download immediately
    HTML_FULLTEXT = "html_fulltext"     # HTML page with full text
    LANDING_PAGE = "landing_page"       # Article page - needs extraction
    DOI_RESOLVER = "doi_resolver"       # DOI.org resolver - redirects
    UNKNOWN = "unknown"                 # Cannot determine type
```

**Key Features**:
- ✅ Pattern-based classification (no HTTP requests)
- ✅ Domain-specific rules (arXiv, bioRxiv, PMC, etc.)
- ✅ Smart prioritization (PDF > HTML > Landing > DOI)
- ✅ Skip known problematic domains
- ✅ Priority adjustment based on URL type

### 2. Standardized URL Object (`SourceURL` dataclass)

**Purpose**: Unified representation of URLs from all sources.

```python
@dataclass
class SourceURL:
    url: str                    # The actual URL
    source: FullTextSource      # Where it came from (pmc, unpaywall, etc.)
    priority: int               # 1 = highest, 11 = lowest
    url_type: URLType           # ✅ Classified type
    confidence: float           # 0.0-1.0 confidence score
    requires_auth: bool         # Needs authentication
    metadata: Dict              # Additional info
```

**Benefits**:
- All URLs have same structure regardless of source
- Can be sorted, filtered, compared consistently
- Metadata preserved for debugging/retry

### 3. How It's Currently Used

**In `FullTextManager.get_all_fulltext_urls()`** (lines 1180-1280):

```python
# Step 1: Query ALL sources in parallel
results = await asyncio.gather(*tasks, return_exceptions=True)

# Step 2: For each successful result, classify URL
for result in results:
    if result.success and result.url:
        # ✅ Classify URL type automatically
        url_type = URLValidator.classify_url(result.url)

        # ✅ Adjust priority based on URL type
        # PDF links get higher priority (-2), landing pages get lower (+2)
        priority_adjustment = URLValidator.get_priority_boost(result.url)
        adjusted_priority = base_priority + priority_adjustment

        # ✅ Create standardized SourceURL object
        source_url = SourceURL(
            url=result.url,
            source=result.source,
            priority=adjusted_priority,
            url_type=url_type,  # ✅ Stored on object
            confidence=1.0,
            requires_auth=(result.source == FullTextSource.INSTITUTIONAL),
            metadata=result.metadata or {}
        )
        all_urls.append(source_url)

# Step 3: Sort by adjusted priority
all_urls.sort(key=lambda x: x.priority)

# Step 4: Return ALL URLs (for retry capability)
return FullTextResult(success=True, all_urls=all_urls)
```

**Benefits**:
- ✅ Direct PDFs tried first (arXiv.org/pdf/xxx.pdf)
- ✅ Landing pages tried later (doi.org/xxx)
- ✅ All URLs preserved for retry
- ✅ Consistent sorting across all sources

---

## How We Can Use It Better

### Problem 1: Not Leveraging URL Types in Registry

**Current Issue**: Registry stores URLs as simple dict, doesn't preserve `url_type` classification.

**Registry currently stores**:
```python
{
    "url": "https://arxiv.org/pdf/xxx.pdf",
    "source": "arxiv",
    "priority": 8,
    "metadata": {}
    # ❌ url_type NOT stored!
}
```

**Solution**: Store complete URL classification in registry:

```python
# In agents.py registry integration (line ~890)
for url_info in paper["all_urls"]:
    registry.record_url(
        pmid=paper["pmid"],
        url=url_info["url"],
        source=url_info["source"],
        priority=url_info["priority"],
        url_type=url_info.get("url_type", "unknown"),  # ✅ ADD THIS
        metadata=url_info["metadata"]
    )
```

**Benefits**:
- Frontend can show "PDF" vs "Landing Page" indicators
- Retry logic can skip landing pages if PDF failed
- Analytics can track "% of PDFs vs landing pages"

### Problem 2: URL Type Not Used in Download Manager

**Current Issue**: `PDFDownloadManager.download_with_fallback()` doesn't leverage URL types.

**What happens now**:
```python
# Download manager tries URLs in order, regardless of type
for url in all_urls:
    result = await self.download_pdf(url.url)  # Same logic for all
    if result.success:
        break
```

**Solution**: Add type-specific download strategies:

```python
async def download_with_fallback(self, all_urls: List[SourceURL]):
    """Smart download with URL type awareness"""

    # Strategy 1: Try all PDF_DIRECT URLs first
    pdf_urls = [u for u in all_urls if u.url_type == URLType.PDF_DIRECT]
    for url in pdf_urls:
        result = await self.download_pdf(url.url)
        if result.success:
            return result

    # Strategy 2: Try extracting PDFs from landing pages
    landing_urls = [u for u in all_urls if u.url_type == URLType.LANDING_PAGE]
    for url in landing_urls:
        # Extract PDF link from landing page
        pdf_link = await self.extract_pdf_from_landing_page(url.url)
        if pdf_link:
            result = await self.download_pdf(pdf_link)
            if result.success:
                return result

    # Strategy 3: Try remaining URLs
    other_urls = [u for u in all_urls if u.url_type not in [URLType.PDF_DIRECT, URLType.LANDING_PAGE]]
    for url in other_urls:
        result = await self.download_pdf(url.url)
        if result.success:
            return result

    return DownloadResult(success=False, error="All sources failed")
```

**Benefits**:
- ✅ Skip landing page extraction if PDF exists
- ✅ More efficient (try direct PDFs first)
- ✅ Better error handling per URL type

### Problem 3: Missing URL Type in Source Implementations

**Current Issue**: Some sources return URLs without classifying them.

**Example - Unpaywall** (what it should do):
```python
async def get_fulltext_url(self, publication):
    """Get URL from Unpaywall with classification"""
    # ... fetch from API ...

    if response.get("best_oa_location"):
        url = response["best_oa_location"]["url"]

        # ✅ Classify URL before returning
        url_type = URLValidator.classify_url(url)

        return FullTextResult(
            success=True,
            url=url,
            source=FullTextSource.UNPAYWALL,
            metadata={
                "url_type": url_type,  # ✅ Include in metadata
                "is_pdf": url_type == URLType.PDF_DIRECT,
                "evidence": response["best_oa_location"].get("evidence")
            }
        )
```

**Solution**: Update all source clients to include URL type in metadata.

**Benefits**:
- ✅ Source knows if it found PDF vs landing page
- ✅ Can skip source if it only returns landing pages
- ✅ Better logging/debugging

### Problem 4: Not Using URL Patterns for Bug Fixing

**Your Original Bug**: PMID 41034176 - Open Access paper but only found paywalled URLs.

**How URL Classifier Can Help**:

```python
# In PMC source client
async def get_fulltext_url(self, publication):
    """Get URL from PMC with multiple patterns"""

    # Try multiple URL patterns (ordered by likelihood)
    url_patterns = [
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/",
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/?report=reader",
        f"https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{subdir}/PMC{pmcid}.pdf",
        f"https://europepmc.org/articles/PMC{pmcid}?pdf=render",
    ]

    # Classify each URL
    classified_urls = []
    for url in url_patterns:
        url_type = URLValidator.classify_url(url)
        classified_urls.append({
            "url": url,
            "type": url_type,
            "priority": 1 if url_type == URLType.PDF_DIRECT else 3
        })

    # Sort by type (PDF first)
    classified_urls.sort(key=lambda x: x["priority"])

    # Try each URL
    for item in classified_urls:
        if await self.check_url_accessible(item["url"]):
            return FullTextResult(success=True, url=item["url"], ...)

    return FullTextResult(success=False, error="No PMC URLs accessible")
```

**Benefits**:
- ✅ Tries multiple URL patterns automatically
- ✅ Prioritizes PDF URLs over landing pages
- ✅ Fixes the original bug (missing PMC PDFs)

---

## Recommendations

### 1. **Immediate** - Store URL Types in Registry

**Action**: Modify registry integration to preserve `url_type`.

**File**: `omics_oracle_v2/api/routes/agents.py` (line ~890)

```python
# Current (missing url_type):
for url_info in paper["all_urls"]:
    registry.record_url(pmid, url_info["url"], url_info["source"], ...)

# ✅ Fix (include url_type):
for url_info in paper["all_urls"]:
    # Get url_type if available, or classify now
    url_type = url_info.get("url_type")
    if not url_type:
        url_type = URLValidator.classify_url(url_info["url"]).value

    registry.record_url(
        pmid=paper["pmid"],
        url=url_info["url"],
        source=url_info["source"],
        priority=url_info["priority"],
        url_type=url_type,  # ✅ ADD THIS
        metadata=url_info["metadata"]
    )
```

**Benefit**: Frontend can show URL types, analytics can track them.

### 2. **High Priority** - Type-Aware Download Strategy

**Action**: Modify `PDFDownloadManager` to use URL types.

**File**: `omics_oracle_v2/lib/enrichment/fulltext/download_manager.py`

**Changes**:
1. Try all `PDF_DIRECT` URLs first
2. Extract PDFs from `LANDING_PAGE` URLs
3. Skip `DOI_RESOLVER` URLs (too slow)
4. Try `UNKNOWN` last

**Benefit**: Faster downloads, better success rate.

### 3. **High Priority** - Fix PMC Source with URL Patterns

**Action**: Update PMC source to try multiple URL patterns.

**File**: `omics_oracle_v2/lib/enrichment/fulltext/sources/pmc.py`

**Changes**:
1. Try `/pdf/` URL first (PDF_DIRECT)
2. Try FTP mirror (PDF_DIRECT)
3. Try EuropePMC (LANDING_PAGE)
4. Classify each before trying

**Benefit**: Fixes your original bug (PMID 41034176).

### 4. **Medium Priority** - Add URL Type to Source Metadata

**Action**: Update all source clients to include `url_type` in result metadata.

**Files**:
- `sources/pmc.py`
- `sources/unpaywall.py`
- `sources/openalex.py`
- `sources/core.py`
- etc.

**Benefit**: Better logging, debugging, analytics.

### 5. **Low Priority** - Add URL Type Analytics

**Action**: Track URL type distribution in statistics.

**Example**:
```python
# In FullTextManager.get_statistics()
stats = {
    "total_urls": 1234,
    "by_type": {
        "pdf_direct": 567,      # 46%
        "landing_page": 345,    # 28%
        "html_fulltext": 234,   # 19%
        "doi_resolver": 88      # 7%
    }
}
```

**Benefit**: Understand which sources provide PDFs vs landing pages.

---

## Implementation Plan

### Phase 1: Store URL Types (2 hours)

1. ✅ Modify registry schema to include `url_type` column
2. ✅ Update agents.py to store `url_type` when registering URLs
3. ✅ Update registry queries to return `url_type`
4. ✅ Test with real data

### Phase 2: Type-Aware Downloads (4 hours)

1. ✅ Add `URLType` filtering to download manager
2. ✅ Implement PDF extraction from landing pages
3. ✅ Add type-specific error handling
4. ✅ Test with various URL types

### Phase 3: Fix PMC Source (3 hours)

1. ✅ Add multiple PMC URL patterns
2. ✅ Classify each pattern
3. ✅ Try in priority order
4. ✅ Test with PMID 41034176 specifically

### Phase 4: Source Metadata (6 hours)

1. ✅ Update all source clients
2. ✅ Add URL type to metadata
3. ✅ Test each source individually
4. ✅ Integration testing

### Phase 5: Analytics (2 hours)

1. ✅ Add URL type tracking to statistics
2. ✅ Add frontend display
3. ✅ Generate reports

**Total**: ~17 hours

---

## Testing Strategy

### Unit Tests

```python
def test_url_classification():
    """Test URL classifier"""
    assert URLValidator.classify_url("https://arxiv.org/pdf/xxx.pdf") == URLType.PDF_DIRECT
    assert URLValidator.classify_url("https://doi.org/10.1234/abc") == URLType.DOI_RESOLVER
    assert URLValidator.is_likely_pdf("https://example.com/paper.pdf") == True

def test_priority_adjustment():
    """Test priority boost/penalty"""
    pdf_url = "https://arxiv.org/pdf/xxx.pdf"
    landing_url = "https://doi.org/10.1234/abc"

    assert URLValidator.get_priority_boost(pdf_url) == -2  # Higher priority
    assert URLValidator.get_priority_boost(landing_url) == +3  # Lower priority
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_url_type_aware_download():
    """Test download manager uses URL types"""
    urls = [
        SourceURL("https://doi.org/10.1234/abc", FullTextSource.CROSSREF, 6, URLType.DOI_RESOLVER),
        SourceURL("https://arxiv.org/pdf/xxx.pdf", FullTextSource.ARXIV, 8, URLType.PDF_DIRECT),
    ]

    manager = PDFDownloadManager()
    result = await manager.download_with_fallback(urls)

    # Should try PDF first (even though DOI has lower priority number)
    assert result.source == FullTextSource.ARXIV
```

### Bug Fix Validation

```python
@pytest.mark.asyncio
async def test_pmid_41034176_fix():
    """Test original bug is fixed"""
    publication = PubMedPublication(pmid="41034176", ...)

    manager = FullTextManager()
    result = await manager.get_all_fulltext_urls(publication)

    # Should find PMC PDF URL
    pdf_urls = [u for u in result.all_urls if u.url_type == URLType.PDF_DIRECT]
    assert len(pdf_urls) > 0, "Should find at least one PDF URL"

    # PMC should be in the list
    pmc_urls = [u for u in pdf_urls if u.source == FullTextSource.PMC]
    assert len(pmc_urls) > 0, "Should find PMC PDF URL"
```

---

## Summary

### What We Have ✅

1. **URL Classification System** (`url_validator.py`)
   - 5 URL types (PDF, HTML, Landing, DOI, Unknown)
   - Pattern-based classification (no HTTP requests)
   - Smart prioritization

2. **Standardized URL Object** (`SourceURL`)
   - Unified structure for all sources
   - Includes url_type, priority, metadata
   - Used consistently throughout codebase

3. **Active Usage**
   - URLs classified automatically in `FullTextManager`
   - Priority adjusted based on type
   - All URLs preserved for retry

### What We Can Improve 🚀

1. **Store URL Types in Registry** (2 hours)
   - Frontend can show "PDF" vs "Landing Page"
   - Analytics can track distribution

2. **Type-Aware Download Strategy** (4 hours)
   - Try PDFs first, landing pages later
   - Extract PDFs from landing pages
   - Better error handling

3. **Fix PMC Source** (3 hours)
   - Try multiple URL patterns
   - Fixes PMID 41034176 bug
   - Higher success rate

4. **Source Metadata Enhancement** (6 hours)
   - All sources include URL type
   - Better debugging/logging

5. **Analytics** (2 hours)
   - Track URL type distribution
   - Understand source quality

**Total Effort**: ~17 hours for complete implementation

### Next Steps

**If you want to start fresh** (delete data/cache):
```bash
# Clean slate
rm -rf data/pdfs/*
rm -rf data/cache/*
rm -f data/omics_oracle.db
```

**Priority 1** - Fix URL Collection Bug (PMID 41034176):
1. Implement Phase 3 (PMC multiple URL patterns)
2. Test with real PMID
3. Verify Open Access URLs found

**Priority 2** - Leverage URL System Better:
1. Store URL types in registry
2. Type-aware download strategy
3. Better analytics

Would you like me to start with **Phase 3 (Fix PMC Source)** to solve your original bug?
