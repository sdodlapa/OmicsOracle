# Universal Identifier Strategy: Multi-Tier Approach

## Problem Statement
Papers discovered from different sources (OpenAlex, PubMed, Semantic Scholar, Europe PMC) may have:
- Different identifiers (some have DOI but no PMID, others vice versa)
- Missing metadata (OpenAlex occasionally has `title: null`)
- Same paper appearing with slight variations across sources

## Current Issues
1. **Schema Constraint Conflict**: `UNIQUE(geo_id, pmid, doi)` fails when pmid is NULL
2. **Title as Fallback**: Assuming all papers have titles, but 1% don't (data quality)
3. **Deduplication**: Same paper from multiple sources creates duplicates

## Proposed Solution: Multi-Tier Identifier

### Tier 1: Primary Identifiers (Authoritative)
```python
# Use in this priority order:
1. DOI (85% coverage, globally unique, persistent)
2. PMID (70% coverage, PubMed-centric, persistent)
3. PMC ID (40% coverage, open access only)
4. arXiv ID (10% coverage, preprints only)
```

### Tier 2: Computed Identifier (Fallback)
```python
def generate_content_hash(title: str, authors: List[str], year: Optional[int]) -> str:
    """
    Generate stable hash for papers without primary identifiers.
    
    Strategy:
    - Normalize title (lowercase, strip punctuation, collapse whitespace)
    - Use first 3 authors (sorted alphabetically for consistency)
    - Include publication year if available
    - SHA256 hash → 16-char hex (1 in 10^19 collision chance)
    """
    # Normalize title
    normalized_title = re.sub(r'[^\w\s]', '', title.lower().strip())
    normalized_title = ' '.join(normalized_title.split())  # Collapse whitespace
    
    # Normalize authors (first 3, sorted)
    author_str = ""
    if authors:
        normalized_authors = []
        for author in authors[:3]:
            # Extract last name (usually last part)
            parts = author.strip().split()
            last_name = parts[-1] if parts else ""
            normalized_authors.append(last_name.lower())
        author_str = "|".join(sorted(normalized_authors))
    
    # Combine components
    year_str = str(year) if year else ""
    composite = f"{normalized_title}|{author_str}|{year_str}"
    
    # Generate hash
    return hashlib.sha256(composite.encode('utf-8')).hexdigest()[:16]
```

### Tier 3: Source-Specific IDs (Last Resort)
```python
# If no primary ID and hash generation fails:
- OpenAlex ID (W12345678)
- Semantic Scholar ID (SSID)
- PubMed Central ID for PMC-only articles
```

## Database Schema Changes

### Option 1: Add Computed Hash Column (RECOMMENDED)
```sql
CREATE TABLE universal_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    geo_id TEXT NOT NULL,
    
    -- Primary identifiers (at least one should exist)
    doi TEXT,
    pmid TEXT,
    pmc_id TEXT,
    arxiv_id TEXT,
    
    -- Computed identifier (for papers without primary IDs)
    content_hash TEXT,  -- 16-char hex hash from title+authors+year
    
    -- Metadata (title is NOT required anymore)
    title TEXT,  -- Can be NULL if malformed data
    authors TEXT,
    journal TEXT,
    publication_year INTEGER,
    publication_date TEXT,
    
    -- Source tracking
    source_id TEXT,  -- OpenAlex ID, S2 ID, etc.
    source_name TEXT,  -- 'openalex', 'pubmed', etc.
    
    -- Timestamps
    first_discovered_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    
    -- Constraints
    CHECK (
        doi IS NOT NULL OR 
        pmid IS NOT NULL OR 
        pmc_id IS NOT NULL OR 
        arxiv_id IS NOT NULL OR 
        content_hash IS NOT NULL
    ),
    
    -- Deduplication: Use the best available identifier
    UNIQUE(geo_id, doi) WHERE doi IS NOT NULL,
    UNIQUE(geo_id, pmid) WHERE pmid IS NOT NULL,
    UNIQUE(geo_id, content_hash) WHERE content_hash IS NOT NULL
);

CREATE INDEX idx_ui_content_hash ON universal_identifiers(content_hash);
```

### Option 2: Composite Key (Simpler, Less Flexible)
```sql
-- Keep current schema but improve UNIQUE constraint
UNIQUE(geo_id, COALESCE(doi, pmid, pmc_id, arxiv_id, content_hash))
```

## Implementation Strategy

### Phase 1: Enhance Publication Model
```python
# Add computed identifier generation
class Publication(BaseModel):
    # ... existing fields ...
    
    @property
    def primary_identifier(self) -> Optional[str]:
        """Get the best available primary identifier."""
        return self.doi or self.pmid or self.pmcid or self.arxiv_id
    
    @property
    def content_hash(self) -> Optional[str]:
        """Generate content-based hash if no primary identifier."""
        if self.primary_identifier:
            return None  # Don't need hash if we have primary ID
        
        if not self.title:
            return None  # Can't generate hash without title
        
        return generate_content_hash(
            title=self.title,
            authors=self.authors,
            year=self.publication_date.year if self.publication_date else None
        )
```

### Phase 2: Update UniversalIdentifier Model
```python
class UniversalIdentifier(BaseModel):
    geo_id: str
    
    # Primary identifiers (all optional)
    pmid: Optional[str] = None
    doi: Optional[str] = None
    pmc_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    
    # Computed identifier (generated if no primary ID)
    content_hash: Optional[str] = None
    
    # Metadata (all optional now - handle malformed data)
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    
    # Source tracking
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    
    first_discovered_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @model_validator(mode='after')
    def validate_has_identifier(self):
        """Ensure at least one identifier exists."""
        if not any([self.pmid, self.doi, self.pmc_id, self.arxiv_id, self.content_hash]):
            raise ValueError("Must have at least one identifier (primary ID or content hash)")
        return self
```

### Phase 3: Update Storage Logic
```python
# In geo_cache.py or citation storage
def store_citation(paper: Publication, geo_id: str):
    """Store citation with robust identifier handling."""
    
    # Skip papers with absolutely no usable data
    if not paper.title and not paper.primary_identifier:
        logger.warning(f"Skipping paper with no title and no primary ID")
        return
    
    # Generate content hash if needed
    content_hash = None
    if not paper.primary_identifier and paper.title:
        content_hash = generate_content_hash(
            title=paper.title,
            authors=paper.authors,
            year=paper.publication_date.year if paper.publication_date else None
        )
    
    identifier = UniversalIdentifier(
        geo_id=geo_id,
        doi=paper.doi,
        pmid=paper.pmid,
        pmc_id=paper.pmcid,
        arxiv_id=paper.metadata.get('arxiv_id'),
        content_hash=content_hash,
        title=paper.title,  # Can be None for malformed data
        authors=json.dumps(paper.authors) if paper.authors else None,
        journal=paper.journal,
        publication_year=paper.publication_date.year if paper.publication_date else None,
        publication_date=paper.publication_date.isoformat() if paper.publication_date else None,
        source_id=paper.metadata.get('openalex_id') or paper.metadata.get('s2_id'),
        source_name=paper.source.value
    )
    
    db.insert_universal_identifier(identifier)
```

## Benefits of This Approach

### 1. **Data Quality**
- ✅ Handles malformed API data (title: null from OpenAlex)
- ✅ Accepts papers with any identifier type
- ✅ Generates fallback hash for papers without primary IDs

### 2. **Deduplication**
- ✅ Same paper from multiple sources deduped by DOI/PMID
- ✅ Papers without DOI/PMID deduped by content hash
- ✅ Source tracking enables metadata enrichment from multiple sources

### 3. **Robustness**
- ✅ Handles preprints (DOI-only, no PMID)
- ✅ Handles conference papers (title+authors only)
- ✅ Handles legacy papers (PMID-only, no DOI)
- ✅ Handles malformed data (missing title, skip gracefully)

### 4. **Flexibility**
- ✅ Can query by any identifier type
- ✅ Can reconstruct hash to find paper without knowing primary ID
- ✅ Source tracking enables future metadata updates

## Migration Strategy

### Step 1: Add content_hash column
```sql
ALTER TABLE universal_identifiers ADD COLUMN content_hash TEXT;
ALTER TABLE universal_identifiers ADD COLUMN source_id TEXT;
ALTER TABLE universal_identifiers ADD COLUMN source_name TEXT;
```

### Step 2: Make title nullable
```sql
-- Drop NOT NULL constraint on title
-- SQLite doesn't support ALTER COLUMN, need to recreate table
-- See migration script: scripts/migrate_universal_identifiers_schema.py
```

### Step 3: Update UNIQUE constraints
```sql
-- Drop old UNIQUE(geo_id, title, doi)
-- Add partial UNIQUE indexes (SQLite 3.8+)
CREATE UNIQUE INDEX idx_unique_geo_doi ON universal_identifiers(geo_id, doi) WHERE doi IS NOT NULL;
CREATE UNIQUE INDEX idx_unique_geo_pmid ON universal_identifiers(geo_id, pmid) WHERE pmid IS NOT NULL;
CREATE UNIQUE INDEX idx_unique_geo_hash ON universal_identifiers(geo_id, content_hash) WHERE content_hash IS NOT NULL;
```

### Step 4: Backfill content_hash
```python
# For existing records without primary IDs
UPDATE universal_identifiers 
SET content_hash = generate_hash(title, authors, publication_year)
WHERE doi IS NULL AND pmid IS NULL AND pmc_id IS NULL AND arxiv_id IS NULL;
```

## Edge Cases Handled

| Scenario | Primary ID | Title | Authors | Solution |
|----------|-----------|-------|---------|----------|
| Normal paper | ✅ DOI | ✅ | ✅ | Use DOI |
| Preprint (bioRxiv) | ✅ DOI | ✅ | ✅ | Use DOI |
| Old paper | ✅ PMID | ✅ | ✅ | Use PMID |
| Conference paper | ❌ | ✅ | ✅ | Generate hash |
| Malformed OpenAlex | ✅ DOI | ❌ NULL | ✅ | Use DOI, skip hash |
| Completely broken | ❌ | ❌ NULL | ❌ | **SKIP** (log warning) |

## Recommendation

**YES, implement multi-tier identifier strategy:**

1. **Remove title as required field** - It's unreliable (OpenAlex data quality issues)
2. **Add content_hash column** - Computed fallback for papers without primary IDs
3. **Use partial UNIQUE indexes** - Better than composite UNIQUE with NULLs
4. **Track source** - Enable future metadata enrichment

This is more robust, handles edge cases better, and doesn't rely on assuming "every paper must have a title" (which is wrong in practice due to API data quality issues).
