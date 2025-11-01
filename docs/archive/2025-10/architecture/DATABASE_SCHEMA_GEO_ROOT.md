# Database Schema: GEO-Centric Architecture

## Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         geo_datasets                              │
│  ---------------------------------------------------------------- │
│  geo_id (TEXT PRIMARY KEY) ← ROOT NODE                           │
│  title (TEXT NOT NULL)                                            │
│  summary (TEXT)                                                   │
│  organism (TEXT)                                                  │
│  platform (TEXT)                                                  │
│  sample_count (INTEGER)                                           │
│  submission_date (TEXT)                                           │
│  publication_date (TEXT)                                          │
│  relevance_score (REAL)                                           │
│  metadata (JSON NOT NULL) - Complete GEO API response            │
│  created_at (TIMESTAMP)                                           │
│  updated_at (TIMESTAMP)                                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N relationship
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      geo_publications                             │
│  ---------------------------------------------------------------- │
│  id (INTEGER PRIMARY KEY AUTOINCREMENT)                          │
│  geo_id (TEXT NOT NULL) ← FOREIGN KEY to geo_datasets.geo_id    │
│  publication_id (INTEGER NOT NULL) ← FK to publications.id      │
│  relationship_type (TEXT NOT NULL) - 'original' OR 'citing'     │
│  citation_strategy (TEXT) - 'strategy_a' OR 'strategy_b'        │
│  discovered_at (TIMESTAMP)                                        │
│                                                                   │
│  UNIQUE(geo_id, publication_id) - One relationship per pair      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ N:1 relationship
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                         publications                              │
│  ---------------------------------------------------------------- │
│  id (INTEGER PRIMARY KEY AUTOINCREMENT) - Internal ID            │
│  pmid (TEXT UNIQUE) - PubMed ID for lookups                      │
│  doi (TEXT) - Digital Object Identifier                          │
│  pmc_id (TEXT) - PubMed Central ID                               │
│  title (TEXT NOT NULL)                                            │
│  authors (TEXT) - JSON array                                     │
│  journal (TEXT)                                                   │
│  year (INTEGER)                                                   │
│  metadata (JSON NOT NULL) - Complete PubMed response             │
│  urls (JSON) - ALL collected fulltext URLs ← CRITICAL!           │
│  created_at (TIMESTAMP)                                           │
│  updated_at (TIMESTAMP)                                           │
│                                                                   │
│  Indexes: pmid (UNIQUE), doi, year                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N relationship
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      download_history                             │
│  ---------------------------------------------------------------- │
│  id (INTEGER PRIMARY KEY AUTOINCREMENT)                          │
│  publication_id (INTEGER NOT NULL) ← FK to publications.id      │
│  url (TEXT NOT NULL) - Which URL was tried                       │
│  source (TEXT NOT NULL) - pmc, unpaywall, etc.                   │
│  status (TEXT NOT NULL) - success, failed, retry, skipped        │
│  file_path (TEXT) - Where PDF saved (if success)                 │
│  file_size (INTEGER) - Bytes (if success)                        │
│  error_message (TEXT) - Error details (if failed)                │
│  attempt_number (INTEGER DEFAULT 1) - 1, 2, 3...                │
│  downloaded_at (TIMESTAMP)                                        │
│                                                                   │
│  Indexes: publication_id, status, downloaded_at                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

### Example: GSE12345 with 3 papers

```sql
-- 1. GEO Dataset (ROOT)
INSERT INTO geo_datasets (geo_id, title, organism, metadata, ...)
VALUES ('GSE12345', 'Breast Cancer Study', 'Homo sapiens', '{}', ...);

-- 2. Publications (3 papers)
INSERT INTO publications (pmid, doi, pmc_id, title, urls, metadata, ...)
VALUES 
  ('11111', '10.1234/original', 'PMC5678910', 'Original Paper', '[...]', '{}', ...),
  ('22222', '10.1234/citing1', 'PMC9999999', 'Citing Paper 1', '[...]', '{}', ...),
  ('33333', '10.1234/citing2', NULL, 'Citing Paper 2', '[...]', '{}', ...);

-- 3. Link GEO to Publications (JOIN TABLE)
INSERT INTO geo_publications (geo_id, publication_id, relationship_type, citation_strategy)
VALUES 
  ('GSE12345', 1, 'original', NULL),          -- Original paper
  ('GSE12345', 2, 'citing', 'strategy_a'),    -- Paper that cited original
  ('GSE12345', 3, 'citing', 'strategy_b');    -- Paper that mentioned GEO ID

-- 4. Download attempts tracked
INSERT INTO download_history (publication_id, url, source, status, file_path, ...)
VALUES 
  (1, 'https://pmc.ncbi.nlm.nih.gov/...', 'pmc', 'success', 'data/pdfs/GSE12345/original/PMID_11111.pdf', ...),
  (1, 'https://unpaywall.org/...', 'unpaywall', 'failed', NULL, ...),  -- Fallback not needed
  (2, 'https://pmc.ncbi.nlm.nih.gov/...', 'pmc', 'success', 'data/pdfs/GSE12345/citing/PMID_22222.pdf', ...),
  (3, 'https://unpaywall.org/...', 'unpaywall', 'success', 'data/pdfs/GSE12345/citing/PMID_33333.pdf', ...);
```

### Retrieve Complete Data

```sql
-- Single query to get EVERYTHING for GSE12345
SELECT 
    g.geo_id,
    g.title AS geo_title,
    g.organism,
    p.pmid,
    p.doi,
    p.title AS paper_title,
    p.urls AS all_urls,              -- All fulltext URLs
    gp.relationship_type,             -- 'original' or 'citing'
    gp.citation_strategy,             -- How discovered
    dh.status AS download_status,
    dh.file_path,
    dh.source AS download_source
FROM geo_datasets g
LEFT JOIN geo_publications gp ON g.geo_id = gp.geo_id
LEFT JOIN publications p ON gp.publication_id = p.id
LEFT JOIN download_history dh ON p.id = dh.publication_id
WHERE g.geo_id = 'GSE12345'
ORDER BY gp.relationship_type, p.year DESC;
```

**Result**:
```
┌──────────┬─────────────┬──────┬─────────┬─────────────┬───────────┬─────────────────┐
│ geo_id   │ geo_title   │ pmid │ doi     │ paper_title │ relation  │ download_status │
├──────────┼─────────────┼──────┼─────────┼─────────────┼───────────┼─────────────────┤
│ GSE12345 │ Breast...   │11111 │10.1234..│ Original... │ original  │ success         │
│ GSE12345 │ Breast...   │22222 │10.1234..│ Citing...   │ citing    │ success         │
│ GSE12345 │ Breast...   │33333 │10.1234..│ Citing...   │ citing    │ success         │
└──────────┴─────────────┴──────┴─────────┴─────────────┴───────────┴─────────────────┘
```

## publications.urls JSON Structure

### What's Stored in `publications.urls`

```json
[
  {
    "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5678910/pdf/paper.pdf",
    "source": "pmc",
    "priority": 2,
    "url_type": "pdf_direct",
    "confidence": 0.95,
    "requires_auth": false,
    "metadata": {
      "pattern": "direct_pdf",
      "filename": "paper.pdf"
    }
  },
  {
    "url": "https://api.unpaywall.org/v2/10.1234/original",
    "source": "unpaywall",
    "priority": 3,
    "url_type": "pdf_direct",
    "confidence": 0.90,
    "requires_auth": false,
    "metadata": {
      "is_oa": true,
      "oa_status": "gold",
      "host_type": "publisher"
    }
  },
  {
    "url": "https://doi.org/10.1234/original",
    "source": "crossref",
    "priority": 5,
    "url_type": "landing_page",
    "confidence": 0.50,
    "requires_auth": false,
    "metadata": {
      "publisher": "Springer Nature"
    }
  },
  // ... 10-15 more URLs from other sources
]
```

### Why Store ALL URLs?

1. **Retry capability**: If primary URL fails, try others
2. **Analytics**: Track which sources work best
3. **Frontend options**: Show alternative download sources
4. **Debugging**: Understand why downloads fail
5. **Historical record**: What URLs were available at collection time

## Query Patterns

### 1. Get All Data for GEO ID (O(1) lookup)

```python
registry.get_complete_geo_data("GSE12345")
```

Returns:
- GEO dataset metadata
- All linked publications (original + citing)
- All URLs for each publication
- Download history for each publication

### 2. Get Publications by PMID

```sql
SELECT * FROM publications WHERE pmid = '11111';
```

Returns:
- Publication metadata
- ALL collected URLs (in `urls` JSON column)
- Can join to `download_history` for status

### 3. Get GEO Datasets by Organism

```sql
SELECT * FROM geo_datasets 
WHERE organism = 'Homo sapiens'
ORDER BY relevance_score DESC;
```

### 4. Get Download Success Rate

```sql
SELECT 
    source,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM download_history
GROUP BY source
ORDER BY success_rate DESC;
```

Result:
```
┌────────────┬────────────────┬───────────┬──────────────┐
│ source     │ total_attempts │ successes │ success_rate │
├────────────┼────────────────┼───────────┼──────────────┤
│ pmc        │ 150            │ 143       │ 95.33%       │
│ unpaywall  │ 200            │ 160       │ 80.00%       │
│ openalex   │ 180            │ 135       │ 75.00%       │
│ crossref   │ 100            │ 35        │ 35.00%       │
└────────────┴────────────────┴───────────┴──────────────┘
```

### 5. Get Failed Downloads for Retry

```sql
SELECT p.pmid, p.title, dh.url, dh.error_message
FROM publications p
JOIN download_history dh ON p.id = dh.publication_id
WHERE dh.status = 'failed'
  AND dh.attempt_number < 3;  -- Haven't exhausted retries
```

## Key Design Decisions

### 1. GEO ID as Primary Key

```python
# Why TEXT PRIMARY KEY instead of INTEGER?
# - GEO IDs are human-readable: "GSE12345"
# - Direct lookups without JOIN: registry.get_geo("GSE12345")
# - Matches external API format
# - No need for auto-increment
```

### 2. PMID as UNIQUE Index

```python
# Why UNIQUE index on pmid instead of PRIMARY KEY?
# - Some publications don't have PMID (preprints, etc.)
# - Need auto-increment id for FOREIGN KEY relationships
# - But PMID is unique when present
# - Fast lookups: SELECT * FROM publications WHERE pmid = '11111'
```

### 3. JSON Columns for URLs

```python
# Why JSON instead of separate url_table?
# - Each publication has 10-20 URLs (not millions)
# - URLs always retrieved together (no partial queries)
# - Flexible schema: New URL types don't need migration
# - Fast: Single query vs. 20 JOIN queries
# - SQLite has excellent JSON support (json_extract, json_each)
```

### 4. download_history Table

```python
# Why separate table instead of JSON in publications?
# - Each publication can have 30-50 download attempts (retries)
# - Need to query by status: "Show all failed downloads"
# - Need analytics: "Which source has best success rate?"
# - Append-only log: Never UPDATE, only INSERT
# - Indexed by publication_id for fast lookups
```

## Foreign Key Relationships

```
geo_datasets (geo_id)
    ↓ 1:N
geo_publications (geo_id, publication_id)
    ↓ N:1
publications (id)
    ↓ 1:N
download_history (publication_id)

CASCADE DELETE ensures:
- Delete GEO → Deletes all geo_publications links
- Delete publication → Deletes all download_history entries
- No orphaned records
```

## Summary

**GEO ID is the ROOT** that ties everything together:

1. **geo_datasets**: Stores GEO metadata (ROOT NODE)
2. **geo_publications**: Links GEO to publications (JOIN TABLE)
3. **publications**: Stores publication metadata + ALL URLs
4. **download_history**: Tracks every download attempt

**Identifiers**:
- **GEO ID** (e.g., "GSE12345"): Root node, primary key
- **PMID** (e.g., "11111"): Unique identifier for publications
- **DOI, PMC ID**: Alternative identifiers (not all papers have PMID)
- **Universal ID**: Used for PDF filenames (PMID → DOI → PMC → arXiv → Hash)

**URL Storage**:
- **publications.urls**: JSON array of ALL collected URLs
- Each URL includes: url, source, priority, url_type, confidence
- 10-20 URLs per publication from 11 sources

**Query Pattern**:
- Query by GEO ID → Get everything in single query
- O(1) lookup: Direct primary key access
- All URLs available for retry if download fails

**Result**: Complete traceability and retry capability for every publication linked to every GEO dataset!
