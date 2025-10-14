# Shared Utilities

Cross-pipeline utilities that don't belong to any specific pipeline.

## Components

### UniversalIdentifier

Universal publication identifier system that works across all paper types and sources.

**Key Features:**
- Hierarchical fallback: PMID → DOI → PMC → arXiv → Hash
- Filesystem-safe filenames
- Consistent across all 11 full-text sources
- Works for papers WITHOUT PMIDs (40% of Unpaywall/CORE)

**Usage:**
```python
from omics_oracle_v2.lib.shared import UniversalIdentifier

# Create identifier
identifier = UniversalIdentifier(publication)

# Get cache key (for databases/caches)
cache_key = identifier.key  # "pmid:12345" or "doi:10.1234/abc"

# Get filename (for file storage)
filename = identifier.filename  # "pmid_12345.pdf" or "doi_10_1234__abc.pdf"

# Get display name (for UI)
display = identifier.display_name  # "PMID 12345" or "DOI 10.1234/abc"
```

**See Also:**
- `/docs/IDENTIFIER_OPTIMIZATION_ANALYSIS.md` - Usage optimization guide
- `/docs/DATABASE_ARCHITECTURE_CRITICAL_EVALUATION.md` - Integration with database architecture
