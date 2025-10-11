# Deduplication Implementation Analysis

## 🎯 Summary: What's Currently Implemented

**Yes, we DO have deduplication, but it's ONLY for Publications, NOT for GEO datasets!**

---

## ✅ What IS Deduplicated

### 1. Publications (Comprehensive 2-Pass System)

**Location:** `omics_oracle_v2/lib/publications/deduplication.py`

**Class:** `AdvancedDeduplicator`

#### Pass 1: ID-Based Deduplication (Exact Matching)

**Dedups by:**
- ✅ PMID (PubMed ID)
- ✅ PMCID (PubMed Central ID)
- ✅ DOI (Digital Object Identifier)

**How it works:**
```python
# From publication_pipeline.py Line 891-910
seen_pmids = set()
seen_pmcids = set()
seen_dois = set()

for pub in publications:
    is_duplicate = False

    if pub.pmid and pub.pmid in seen_pmids:
        is_duplicate = True
    if pub.pmcid and pub.pmcid in seen_pmcids:
        is_duplicate = True
    if pub.doi and pub.doi in seen_dois:
        is_duplicate = True

    if not is_duplicate:
        unique_pubs.append(pub)
        # Record all IDs
        if pub.pmid: seen_pmids.add(pub.pmid)
        if pub.pmcid: seen_pmcids.add(pub.pmcid)
        if pub.doi: seen_dois.add(pub.doi)
```

**Performance:** ⚡ Very fast (O(n) with set lookups)

#### Pass 2: Fuzzy Deduplication (Similarity Matching)

**Dedups by:**
- ✅ Title similarity (85% threshold using fuzzy matching)
- ✅ Author names (80% threshold, handles variations)
- ✅ Publication year (±1 year tolerance for preprints)

**How it works:**
```python
# From deduplication.py Line 117-144
def _are_duplicates(self, pub1: Publication, pub2: Publication) -> bool:
    # 1. Title similarity (case-insensitive, fuzzy)
    title_ratio = fuzz.ratio(pub1.title.lower(), pub2.title.lower())
    if title_ratio < 85.0:  # Threshold
        return False

    # 2. Author matching (handles "Smith J" vs "J. Smith")
    if pub1.authors and pub2.authors:
        if not self._authors_match(pub1.authors, pub2.authors):
            return False

    # 3. Year tolerance (preprint 2023 vs published 2024)
    if pub1.publication_date and pub2.publication_date:
        year_diff = abs(pub1.publication_date.year - pub2.publication_date.year)
        if year_diff > 1:  # Year tolerance
            return False

    return True  # All checks passed - duplicate!
```

**Handles:**
- Typos in titles: "Insulin Resistence" vs "Insulin Resistance" ✓
- Formatting: "DIABETES STUDY" vs "diabetes study" ✓
- Author variations: "Smith, John A." vs "J.A. Smith" ✓
- Preprints: bioRxiv (2023) vs Journal (2024) ✓

**Performance:** ⚠️ Slower (O(n²) comparison needed)

#### Completeness Scoring

**When duplicates found, keeps the MOST COMPLETE record:**

```python
# From deduplication.py Line 218-249
def _completeness_score(self, pub: Publication) -> int:
    score = 0

    # IDs (most valuable)
    if pub.pmid: score += 100     # PMID is gold standard
    if pub.pmcid: score += 50
    if pub.doi: score += 30

    # Content
    if pub.abstract: score += 20
    if pub.authors: score += len(pub.authors) * 2
    if pub.journal: score += 10
    if pub.publication_date: score += 10

    # Metadata
    if pub.mesh_terms: score += 15
    if pub.keywords: score += 10
    if pub.citations > 0: score += 5

    return score
```

**Example:**
- Publication A: PMID only, no abstract → Score: 100
- Publication B: DOI, full abstract, 5 authors → Score: 30 + 20 + 10 = 60
- **Keeps: Publication A** (PMID is more valuable!)

---

## ❌ What is NOT Deduplicated

### GEO Datasets

**Current Status:** ❌ **NO DEDUPLICATION**

**Problem:**
Multiple searches or sources could return the same GEO dataset (e.g., GSE12345) multiple times, and we're NOT deduping them!

**Where it should happen:**
- `unified_search_pipeline.py` (when combining results)
- `search_agent.py` (before ranking)

**Why it matters:**
```python
# Hypothetical scenario WITHOUT dedup:
results = [
    GSE12345,  # From keyword search
    GSE12345,  # From related datasets
    GSE54321,
    GSE12345,  # From citation discovery
]

# User sees same dataset 3 times! ❌
```

---

## 📊 Current Implementation Details

### Publication Pipeline

**File:** `omics_oracle_v2/lib/pipelines/publication_pipeline.py`

**Lines 611-613:**
```python
# Step 2: Deduplicate (if enabled)
if self.config.deduplication:
    all_publications = self._deduplicate_publications(all_publications)
```

**When it runs:**
1. After collecting publications from multiple sources (PubMed, OpenAlex, etc.)
2. Before ranking
3. Controlled by config flag: `enable_deduplication=True`

**Logging output:**
```
INFO - Pass 1 (ID-based): Removed 15 duplicates
INFO - Pass 2 (Fuzzy): Removed 3 additional duplicates
INFO - Total duplicates removed: 18/120
```

### Unified Search Pipeline

**File:** `omics_oracle_v2/lib/pipelines/unified_search_pipeline.py`

**Lines 343-347:**
```python
# Step 5: Deduplicate results
if self.config.enable_deduplication and self.deduplicator:
    logger.info("Deduplicating publications...")
    publications = self.deduplicator.deduplicate(publications)
    logger.info(f"After deduplication: {len(publications)} unique publications")
```

**Only applies to PUBLICATIONS, not GEO datasets!**

---

## 🔧 What Needs to Be Added: GEO Deduplication

### Missing Implementation

We need to add GEO dataset deduplication similar to publications.

### Proposed Implementation

#### Option 1: Simple GEO ID Deduplication (Fast)

```python
def deduplicate_geo_datasets(datasets: List[GEODataset]) -> List[GEODataset]:
    """
    Remove duplicate GEO datasets by accession ID.

    Args:
        datasets: List of GEO datasets

    Returns:
        Deduplicated list (keeps first occurrence)
    """
    seen_accessions = set()
    unique_datasets = []

    for dataset in datasets:
        if dataset.accession not in seen_accessions:
            unique_datasets.append(dataset)
            seen_accessions.add(dataset.accession)

    duplicates_removed = len(datasets) - len(unique_datasets)
    if duplicates_removed > 0:
        logger.info(f"GEO deduplication: Removed {duplicates_removed} duplicates")

    return unique_datasets
```

**Pros:**
- ✅ Very fast (O(n))
- ✅ 100% accurate (GEO IDs are unique)
- ✅ Simple to implement

**Cons:**
- ❌ Only handles exact ID matches
- ❌ Doesn't handle title variations (unlikely for GEO)

#### Option 2: Advanced GEO Deduplication (Thorough)

```python
class GEODeduplicator:
    """Advanced GEO dataset deduplication."""

    def deduplicate(self, datasets: List[GEODataset]) -> List[GEODataset]:
        """
        Two-pass deduplication:
        1. By GEO accession (GSE/GDS ID)
        2. By title similarity (catches data entry errors)
        """
        # Pass 1: ID-based
        seen_ids = set()
        unique = []

        for ds in datasets:
            if ds.accession not in seen_ids:
                unique.append(ds)
                seen_ids.add(ds.accession)

        # Pass 2: Title fuzzy matching (optional, catches manual entry errors)
        if len(unique) > 1:
            unique = self._fuzzy_deduplicate_titles(unique)

        return unique

    def _fuzzy_deduplicate_titles(self, datasets: List[GEODataset]) -> List[GEODataset]:
        """Handle rare cases where same study has different GEO IDs."""
        # Use fuzzywuzzy like publications
        # Threshold: 90% (higher than publications since GEO titles are standardized)
        pass
```

**Pros:**
- ✅ Handles edge cases
- ✅ More robust
- ✅ Future-proof

**Cons:**
- ❌ Slightly slower
- ❌ More complex
- ❌ Probably overkill (GEO IDs are highly reliable)

---

## 🎯 Recommendations

### 1. Add GEO ID Deduplication (High Priority)

**Where to add:**

```python
# File: omics_oracle_v2/lib/pipelines/unified_search_pipeline.py
# After Line 339

# Step 4.5: Deduplicate GEO datasets (NEW)
if geo_datasets and len(geo_datasets) > 1:
    logger.info(f"Deduplicating GEO datasets...")
    seen_accessions = set()
    unique_geo = []

    for ds in geo_datasets:
        if ds.accession not in seen_accessions:
            unique_geo.append(ds)
            seen_accessions.add(ds.accession)

    duplicates = len(geo_datasets) - len(unique_geo)
    if duplicates > 0:
        logger.info(f"Removed {duplicates} duplicate GEO datasets")

    geo_datasets = unique_geo
```

**Impact:**
- ✅ Prevents duplicate GEO datasets in results
- ✅ Improves user experience
- ✅ ~5 lines of code
- ✅ Negligible performance impact

### 2. Create Reusable GEO Deduplicator Class (Medium Priority)

**For consistency with publications:**

```python
# File: omics_oracle_v2/lib/geo/deduplication.py (NEW)

class GEODeduplicator:
    """Deduplicator for GEO datasets."""

    def deduplicate(self, datasets: List[GEODataset]) -> List[GEODataset]:
        """Remove duplicate GEO datasets by accession."""
        # Implementation here
        pass
```

**Use in unified pipeline:**
```python
# Initialize in __init__
self.geo_deduplicator = GEODeduplicator()

# Use in search()
geo_datasets = self.geo_deduplicator.deduplicate(geo_datasets)
```

### 3. Add Deduplication Metrics (Low Priority)

**Track deduplication stats:**

```python
dedup_stats = {
    "publications": {
        "id_based": 15,
        "fuzzy": 3,
        "total_removed": 18,
    },
    "geo_datasets": {
        "id_based": 5,
        "total_removed": 5,
    }
}

# Include in search result metadata
result.metadata["deduplication"] = dedup_stats
```

---

## 📈 Expected Impact

### Before (Current State):

**Publications:**
- ✅ Deduplicated (2-pass: ID + fuzzy)
- ✅ Smart completeness scoring
- ✅ Handles preprints vs published

**GEO Datasets:**
- ❌ NOT deduplicated
- ❌ Could show same dataset multiple times
- ❌ Confusing for users

### After (With GEO Dedup):

**Publications:**
- ✅ No change (already good)

**GEO Datasets:**
- ✅ Deduplicated by accession ID
- ✅ Clean results (no repeats)
- ✅ Better user experience

---

## 🔍 Testing Deduplication

### Current Test Cases

**File:** `test_week2_publication_integration.py`

**Tests:**
1. ✅ Cross-source deduplication (PubMed + OpenAlex)
2. ✅ ID-based matching
3. ✅ Fuzzy title matching

**Missing:**
- ❌ GEO dataset deduplication tests

### Proposed Tests

```python
def test_geo_deduplication():
    """Test GEO dataset deduplication."""
    datasets = [
        GEODataset(accession="GSE12345", title="Study A"),
        GEODataset(accession="GSE12345", title="Study A"),  # Duplicate
        GEODataset(accession="GSE54321", title="Study B"),
    ]

    deduplicator = GEODeduplicator()
    unique = deduplicator.deduplicate(datasets)

    assert len(unique) == 2
    assert unique[0].accession == "GSE12345"
    assert unique[1].accession == "GSE54321"
```

---

## 📝 Summary Table

| Component | ID Dedup | Fuzzy Dedup | Completeness Scoring | Status |
|-----------|----------|-------------|---------------------|---------|
| **Publications** | ✅ PMID, DOI, PMCID | ✅ Title, Authors, Year | ✅ Implemented | **DONE** |
| **GEO Datasets** | ❌ Not implemented | ❌ Not needed | ❌ Not needed | **TODO** |

**Key Deduplication Fields:**

| Type | Primary ID | Secondary IDs | Fuzzy Fields |
|------|-----------|---------------|--------------|
| Publications | PMID | DOI, PMCID | Title (85%), Authors (80%), Year (±1) |
| GEO Datasets | Accession (GSE/GDS) | - | Title (90%, optional) |

---

## ✅ Action Items

### Immediate (This Session):

1. **Add simple GEO ID deduplication** to `unified_search_pipeline.py`
   - 5 lines of code
   - Prevents duplicate datasets
   - Easy win!

### Short-term (Week 2 Day 5):

2. **Create `GEODeduplicator` class** for consistency
   - Matches publication pattern
   - Easier to test
   - More maintainable

3. **Add deduplication tests** for GEO datasets

### Long-term (Future):

4. **Add deduplication metrics** to search results
5. **Consider cross-type deduplication** (if GEO dataset links to publication)

---

## 🎓 Key Insights

**What's Working:**
- ✅ Publication deduplication is **excellent** (2-pass, fuzzy matching, completeness scoring)
- ✅ Handles real-world issues (preprints, typos, name variations)
- ✅ Well-tested and robust

**What's Missing:**
- ❌ GEO dataset deduplication
- ❌ Simple fix (just need ID-based dedup)
- ❌ Low priority but should be added

**Why It Matters:**
- Users could see duplicate GEO datasets in search results
- Confusing and unprofessional
- Easy to fix (5 lines of code)

**Your Question Was Spot-On:**
You correctly identified that we should be deduplicating by GEO IDs, titles, and DOIs. We ARE doing this for publications (DOIs, titles), but NOT for GEO datasets (GEO IDs). This should be fixed! 🎯
