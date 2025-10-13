# Phase 2B Migration Guide: Import Path Changes

## Overview

**Date:** October 2025
**Phase:** 2B - Flow-Based Reorganization
**Files Affected:** 50+ files moved, 100+ imports updated
**Test Status:** 143/145 tests passing (98%)

This guide helps developers update their code to work with the new flow-based architecture.

## Quick Reference: Old → New Import Paths

### Query Processing (Stage 3)

**NLP Components:**
```python
# OLD
from omics_oracle_v2.lib.nlp.biomedical_ner import ...
from omics_oracle_v2.lib.nlp.query_expander import ...
from omics_oracle_v2.lib.nlp.synonym_expansion import ...

# NEW
from omics_oracle_v2.lib.query_processing.nlp.biomedical_ner import ...
from omics_oracle_v2.lib.query_processing.nlp.query_expander import ...
from omics_oracle_v2.lib.query_processing.nlp.synonym_expansion import ...
```

**Query Optimization:**
```python
# OLD
from omics_oracle_v2.lib.query.analyzer import ...
from omics_oracle_v2.lib.query.optimizer import ...

# NEW
from omics_oracle_v2.lib.query_processing.optimization.analyzer import ...
from omics_oracle_v2.lib.query_processing.optimization.optimizer import ...
```

### Search Orchestration (Stage 4)

```python
# OLD
from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator
from omics_oracle_v2.lib.search.models import SearchResult

# NEW
from omics_oracle_v2.lib.search_orchestration.orchestrator import SearchOrchestrator
from omics_oracle_v2.lib.search_orchestration.models import SearchResult
```

### GEO Search Engine (Stage 5a - PRIMARY)

```python
# OLD
from omics_oracle_v2.lib.geo.client import GEOClient
from omics_oracle_v2.lib.geo.query_builder import GEOQueryBuilder
from omics_oracle_v2.lib.geo.models import GEODataset

# NEW
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient
from omics_oracle_v2.lib.search_engines.geo.query_builder import GEOQueryBuilder
from omics_oracle_v2.lib.search_engines.geo.models import GEODataset
```

**Key Change:** GEO is now recognized as a PRIMARY search engine, not just a data source client.

### Citation Search Engines (Stage 5b)

```python
# OLD (Multiple inconsistent locations)
from omics_oracle_v2.lib.citations.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient  # Alternative
from omics_oracle_v2.lib.citations.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient
from omics_oracle_v2.lib.citations.clients.semantic_scholar import SemanticScholarClient
from omics_oracle_v2.lib.publications.models import Publication

# NEW (Consolidated in search_engines/citations/)
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.search_engines.citations.scholar import GoogleScholarClient
from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient
from omics_oracle_v2.lib.search_engines.citations.semantic_scholar import SemanticScholarClient
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.citations.config import CitationSearchConfig
```

### Full-text Enrichment (Stages 6-8)

**Core Components:**
```python
# OLD
from omics_oracle_v2.lib.fulltext.manager import FullTextManager
from omics_oracle_v2.lib.fulltext.cache_db import CacheDB
from omics_oracle_v2.lib.fulltext.normalizer import normalize_identifier
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

# NEW
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
from omics_oracle_v2.lib.enrichment.fulltext.cache_db import CacheDB
from omics_oracle_v2.lib.enrichment.fulltext.normalizer import normalize_identifier
from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager
```

**Full-text Sources:**
```python
# OLD
from omics_oracle_v2.lib.publications.clients.institutional_access import InstitutionalAccessClient
from omics_oracle_v2.lib.publications.clients.oa_sources.arxiv_client import ArXivClient
from omics_oracle_v2.lib.publications.clients.oa_sources.biorxiv_client import BioRxivClient
from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREClient
from omics_oracle_v2.lib.publications.clients.oa_sources.crossref_client import CrossrefClient
from omics_oracle_v2.lib.publications.clients.oa_sources.unpaywall_client import UnpaywallClient
from omics_oracle_v2.lib.fulltext.sources.scihub_client import SciHubClient
from omics_oracle_v2.lib.fulltext.sources.libgen_client import LibGenClient

# NEW (All in enrichment/fulltext/sources/)
from omics_oracle_v2.lib.enrichment.fulltext.sources.institutional_access import InstitutionalAccessClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.arxiv_client import ArXivClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.biorxiv_client import BioRxivClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.core_client import COREClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.crossref_client import CrossrefClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.unpaywall_client import UnpaywallClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.scihub_client import SciHubClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.libgen_client import LibGenClient
```

### AI Analysis (Stage 9)

**AI/LLM Components:**
```python
# OLD
from omics_oracle_v2.lib.ai.client import SummarizationClient
from omics_oracle_v2.lib.ai.models import SummaryResult
from omics_oracle_v2.lib.ai.prompts import SUMMARIZATION_PROMPT
from omics_oracle_v2.lib.ai.utils import format_summary

# NEW
from omics_oracle_v2.lib.analysis.ai.client import SummarizationClient
from omics_oracle_v2.lib.analysis.ai.models import SummaryResult
from omics_oracle_v2.lib.analysis.ai.prompts import SUMMARIZATION_PROMPT
from omics_oracle_v2.lib.analysis.ai.utils import format_summary
```

**Publication Analytics:**
```python
# OLD
from omics_oracle_v2.lib.publications.analysis.knowledge_graph import KnowledgeGraph
from omics_oracle_v2.lib.publications.analysis.qa_system import QASystem
from omics_oracle_v2.lib.publications.analysis.reports import generate_report
from omics_oracle_v2.lib.publications.analysis.trends import analyze_trends

# NEW
from omics_oracle_v2.lib.analysis.publications.knowledge_graph import KnowledgeGraph
from omics_oracle_v2.lib.analysis.publications.qa_system import QASystem
from omics_oracle_v2.lib.analysis.publications.reports import generate_report
from omics_oracle_v2.lib.analysis.publications.trends import analyze_trends
```

### Infrastructure Cache

```python
# OLD
from omics_oracle_v2.lib.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.cache.redis_client import RedisClient

# NEW
from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.infrastructure.cache.redis_client import RedisClient
```

## Automated Migration Script

For bulk updates, use this `sed` command pattern:

```bash
# Example: Update all GEO imports
find . -name "*.py" -type f -exec sed -i '' \
  's|from omics_oracle_v2\.lib\.geo\.|from omics_oracle_v2.lib.search_engines.geo.|g' {} +

# Example: Update all citation client imports
find . -name "*.py" -type f -exec sed -i '' \
  's|from omics_oracle_v2\.lib\.citations\.clients\.|from omics_oracle_v2.lib.search_engines.citations.|g' {} +

# Example: Update fulltext imports
find . -name "*.py" -type f -exec sed -i '' \
  's|from omics_oracle_v2\.lib\.fulltext\.|from omics_oracle_v2.lib.enrichment.fulltext.|g' {} +
```

**Note:** Always backup your code before running bulk updates!

## Testing Your Changes

After updating imports:

1. **Run Import Tests:**
```bash
python3 -c "
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
from omics_oracle_v2.lib.analysis.ai.client import SummarizationClient
print('✅ All imports successful!')
"
```

2. **Run Relevant Tests:**
```bash
# Run all library tests
pytest tests/lib/ -v

# Or run specific module tests
pytest tests/lib/fulltext/ -v
pytest tests/lib/search_engines/ -v  # If they exist
```

3. **Check for Deprecation Warnings:**
```bash
python3 -W all your_script.py
```

## Common Issues and Solutions

### Issue 1: ModuleNotFoundError

**Symptom:**
```
ModuleNotFoundError: No module named 'omics_oracle_v2.lib.geo'
```

**Solution:**
Update import to new path:
```python
# Change this
from omics_oracle_v2.lib.geo.client import GEOClient

# To this
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient
```

### Issue 2: ImportError for Specific Symbols

**Symptom:**
```
ImportError: cannot import name 'Publication' from 'omics_oracle_v2.lib.publications'
```

**Solution:**
Publications model moved to citations:
```python
# Change this
from omics_oracle_v2.lib.publications.models import Publication

# To this
from omics_oracle_v2.lib.search_engines.citations.models import Publication
```

### Issue 3: Relative Imports Broken

**Symptom:**
```
ImportError: attempted relative import beyond top-level package
```

**Solution:**
All imports should now be absolute. Convert relative imports:
```python
# Change this
from ..models import SomeModel
from .utils import some_function

# To this
from omics_oracle_v2.lib.search_engines.citations.models import SomeModel
from omics_oracle_v2.lib.search_engines.citations.utils import some_function
```

### Issue 4: Circular Import Errors

If you encounter circular imports after migration:

1. **Check import order** - Some modules may have implicit dependencies that changed
2. **Use TYPE_CHECKING** for type hints:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omics_oracle_v2.lib.search_engines.geo.client import GEOClient

# Then use string annotations
def process_geo_data(client: "GEOClient") -> None:
    ...
```

## Breaking Changes

### 1. GEO Client Import Path
**Impact:** High - affects all GEO-related code

**Old:**
```python
from omics_oracle_v2.lib.geo.client import GEOClient
```

**New:**
```python
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient
```

### 2. Citation Search Consolidation
**Impact:** High - multiple paths consolidated

All citation search engines now under `search_engines/citations/`:
- PubMed
- Google Scholar
- OpenAlex
- Semantic Scholar

### 3. Full-text Source Reorganization
**Impact:** Medium - affects PDF download code

All full-text sources consolidated under `enrichment/fulltext/sources/`.

### 4. AI Analysis Split
**Impact:** Medium - affects analysis code

AI components split into:
- `analysis/ai/` - LLM integration
- `analysis/publications/` - Publication-specific analytics

## Validation Checklist

Use this checklist to verify your migration:

- [ ] All imports updated to new paths
- [ ] Code runs without ImportError
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No deprecation warnings
- [ ] Pre-commit hooks pass
- [ ] Documentation updated (if applicable)

## Getting Help

**Documentation:**
- [Phase 2B Complete Report](PHASE2B_COMPLETE.md) - Full reorganization details
- [Test Validation Report](PHASE3_TEST_VALIDATION_REPORT.md) - Test status
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md) - New architecture details

**Common Commands:**
```bash
# Find old import patterns
grep -r "from omics_oracle_v2.lib.geo" .

# Check for broken imports
python3 -m py_compile your_file.py

# Run comprehensive tests
pytest tests/ -v
```

## Timeline

- **Phase 2A:** Archived 1,097 LOC of redundant code
- **Phase 2B:** Reorganized 50+ files, updated 100+ imports
- **Phase 3:** Test validation (143/145 passing)
- **Current:** Documentation and migration support

## Support

If you encounter issues not covered in this guide:

1. Check [PHASE3_TEST_VALIDATION_REPORT.md](PHASE3_TEST_VALIDATION_REPORT.md) for known issues
2. Review commit history: `git log --oneline --all --graph`
3. Search for similar import paths: `grep -r "YourImport" omics_oracle_v2/`

---

**Last Updated:** October 12, 2025
**Version:** Phase 2B Complete
