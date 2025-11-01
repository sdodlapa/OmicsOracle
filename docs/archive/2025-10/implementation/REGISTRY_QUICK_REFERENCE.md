# GEO Registry - Quick Reference

## For Frontend Developers

### Get Complete GEO Data

```javascript
// ONE API call gets everything
const response = await fetch(`/api/geo/${geoId}/complete`);
const data = await response.json();

// Response structure:
{
  geo: {
    geo_id, title, organism, platform, sample_count, ...
  },
  papers: {
    original: [{ pmid, title, urls[], download_history[], ... }],
    citing: [{ pmid, title, urls[], download_history[], ... }]
  },
  statistics: {
    original_papers, citing_papers, total_papers,
    successful_downloads, failed_downloads, success_rate
  }
}
```

### Check If Papers Downloaded

```javascript
const data = await fetch(`/api/geo/${geoId}/complete`).then(r => r.json());

const allPapers = [...data.papers.original, ...data.papers.citing];
const downloaded = allPapers.filter(p =>
  p.download_history.some(h => h.status === 'success')
);

console.log(`${downloaded.length}/${allPapers.length} downloaded`);
```

### Retry Failed Downloads

```javascript
const data = await fetch(`/api/geo/${geoId}/complete`).then(r => r.json());

// Get papers that need retry
const failed = [...data.papers.original, ...data.papers.citing]
  .filter(p => !p.download_history.some(h => h.status === 'success'));

for (const paper of failed) {
  // Try all URLs in priority order
  for (const url of paper.urls) {
    try {
      await downloadPDF(url.url, paper.pmid);
      break;  // Success!
    } catch (e) {
      // Try next URL
    }
  }
}
```

### Show Download Progress

```javascript
const data = await fetch(`/api/geo/${geoId}/complete`).then(r => r.json());

return (
  <Progress
    value={data.statistics.successful_downloads}
    max={data.statistics.total_papers}
    label={`${data.statistics.success_rate}% complete`}
  />
);
```

---

## For Backend Developers

### Registry Usage

```python
from omics_oracle_v2.lib.registry import get_registry

# Get registry instance
registry = get_registry()

# Register GEO dataset
registry.register_geo_dataset("GSE48968", {
    "geo_id": "GSE48968",
    "title": "...",
    "organism": "...",
    # ... more metadata
})

# Register publication with ALL URLs
registry.register_publication(
    pmid="24385618",
    metadata={"title": "...", "authors": [...], ...},
    urls=[
        {"url": "...", "source": "pmc", "priority": 1, "metadata": {}},
        {"url": "...", "source": "unpaywall", "priority": 2, "metadata": {}},
        # ... more URLs
    ],
    doi="10.1234/..."
)

# Link GEO to publication
registry.link_geo_to_publication(
    geo_id="GSE48968",
    pmid="24385618",
    relationship_type="original",  # or "citing"
    citation_strategy="strategy_a"  # optional
)

# Record download attempt
registry.record_download_attempt(
    pmid="24385618",
    url="https://...",
    source="pmc",
    status="success",  # or "failed"
    file_path="data/pdfs/GSE48968/original/24385618.pdf",
    file_size=1234567,
    error_message=None  # or error message if failed
)

# Get complete data (O(1) lookup)
data = registry.get_complete_geo_data("GSE48968")

# Get URLs for retry
urls = registry.get_urls_for_retry("24385618")

# Get statistics
stats = registry.get_statistics()
```

### Database Location

**Default**: `data/omics_oracle.db`

**Custom**:
```python
from omics_oracle_v2.lib.registry import GEORegistry

registry = GEORegistry("/custom/path/to/db.sqlite")
```

### Transaction Example

```python
registry = get_registry()

try:
    # Multiple operations in transaction
    registry.register_geo_dataset(...)
    registry.register_publication(...)
    registry.link_geo_to_publication(...)
    # Auto-commits on success
except Exception as e:
    # Auto-rolls back on error
    logger.error(f"Transaction failed: {e}")
```

---

## Database Schema (Quick Reference)

```sql
-- GEO Datasets
geo_datasets (
  geo_id PRIMARY KEY,
  title, organism, platform, sample_count,
  metadata JSON,
  created_at, updated_at
)

-- Publications
publications (
  id PRIMARY KEY AUTOINCREMENT,
  pmid UNIQUE, doi, pmc_id, title,
  metadata JSON,
  urls JSON,  -- ALL URLs for retry
  created_at, updated_at
)

-- Relationships
geo_publications (
  geo_id, publication_id,
  relationship_type,  -- "original" or "citing"
  citation_strategy,
  PRIMARY KEY (geo_id, publication_id)
)

-- Download History
download_history (
  id PRIMARY KEY AUTOINCREMENT,
  publication_id, url, source,
  status,  -- "success" or "failed"
  file_path, file_size, error_message,
  downloaded_at
)
```

---

## API Endpoints

### Get Complete GEO Data

```http
GET /api/geo/{geo_id}/complete

Response 200:
{
  "geo": {...},
  "papers": {"original": [...], "citing": [...]},
  "statistics": {...}
}

Response 404:
{
  "detail": "GEO dataset GSE48968 not found in registry. Have you enriched it yet?"
}
```

### Enrich with Fulltext

```http
POST /api/enrich-fulltext
{
  "datasets": [{"geo_id": "GSE48968", ...}],
  "include_citing_papers": true,
  "max_citing_papers": 10,
  "download_original": true
}

# Automatically stores in registry
```

---

## Testing

```bash
# Unit test
python tests/test_geo_registry.py

# Integration test
python tests/test_registry_integration.py

# All tests
pytest tests/test_geo_registry.py tests/test_registry_integration.py -v
```

---

## Common Queries

### Get all GEO datasets

```python
cursor = registry.conn.execute("SELECT geo_id, title FROM geo_datasets")
datasets = [{"geo_id": row[0], "title": row[1]} for row in cursor.fetchall()]
```

### Get papers by organism

```python
cursor = registry.conn.execute("""
    SELECT geo_id, title
    FROM geo_datasets
    WHERE json_extract(metadata, '$.organism') = ?
""", ("Homo sapiens",))
```

### Get papers with failed downloads

```python
cursor = registry.conn.execute("""
    SELECT p.pmid, p.title, COUNT(dh.id) as failed_attempts
    FROM publications p
    JOIN download_history dh ON p.id = dh.publication_id
    WHERE dh.status = 'failed'
    GROUP BY p.pmid
    HAVING failed_attempts > 0
""")
```

### Get download statistics by source

```python
cursor = registry.conn.execute("""
    SELECT source,
           COUNT(*) as total,
           SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
    FROM download_history
    GROUP BY source
""")
```

---

## Performance Tips

1. **Use indexes**: Already created on geo_id, pmid, doi
2. **Batch operations**: Use transactions for multiple inserts
3. **Limit queries**: Don't fetch all data if you only need counts
4. **Close connections**: Call `registry.close()` when done (or use context manager)

---

## Troubleshooting

### "Database locked"
- SQLite is single-writer
- Wait and retry (automatic)
- Consider PostgreSQL for high concurrency

### "GEO dataset not found"
- Run enrichment first: `POST /api/enrich-fulltext`
- Check geo_id spelling

### "No URLs for retry"
- Paper may not have accessible sources
- Check original paper metadata

---

## Links

- **Full Guide**: `docs/REGISTRY_INTEGRATION_GUIDE.md`
- **Architecture**: `docs/DATA_ORGANIZATION_ANALYSIS.md`
- **Implementation**: `docs/IMPLEMENTATION_COMPLETE_OCT14.md`
- **Code**: `omics_oracle_v2/lib/registry/geo_registry.py`
- **Tests**: `tests/test_geo_registry.py`, `tests/test_registry_integration.py`
