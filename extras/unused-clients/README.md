# Unused Clients (Archived)

**Archived:** October 13, 2025
**Reason:** Duplicate/unused implementations
**Total LOC:** 354

---

## Contents

### Async PubMed Client (354 LOC)
- `async_pubmed.py` - Asynchronous PubMed client using aiohttp

**Why Archived:**
- `lib/publications/clients/pubmed.py` (sync version) is used in production
- Not imported anywhere in the codebase
- Sync version meets performance requirements

**Production uses:**
```python
# What's actually used (sync version)
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient

client = PubMedClient(config)
results = client.search("diabetes")  # Blocking but fast enough
```

**What was archived:**
```python
# Not used anywhere
from omics_oracle_v2.lib.publications.clients.async_pubmed import AsyncPubMedClient

client = AsyncPubMedClient(email="...")
results = await client.search("diabetes")  # Async but unused
```

---

## Notes

### Why Sync Version is Sufficient

1. **PubMed search is already fast** (200-500ms)
2. **Parallel execution** handled at orchestrator level:
   ```python
   # SearchOrchestrator runs searches in parallel
   geo_task = self._search_geo(query)
   pubmed_task = self._search_pubmed(query)  # Sync client in executor
   openalex_task = self._search_openalex(query)

   results = await asyncio.gather(geo_task, pubmed_task, openalex_task)
   ```
3. **NCBI rate limits** make async less beneficial (max 10 req/sec)
4. **Biopython Entrez** (sync) is well-tested and stable

### If You Need Async PubMed

Consider using the archived version if:
- Need to make 100+ PubMed requests concurrently
- Building a different flow that benefits from async
- Want to avoid thread pool overhead

**To restore:**
```bash
git mv extras/unused-clients/async_pubmed.py \
       omics_oracle_v2/lib/publications/clients/
```

---

## Recovery Instructions

```bash
# Restore async_pubmed
git mv extras/unused-clients/async_pubmed.py \
       omics_oracle_v2/lib/publications/clients/

# Update imports in your code
from omics_oracle_v2.lib.publications.clients.async_pubmed import AsyncPubMedClient

# Use async client
client = AsyncPubMedClient(email="your@email.com")
results = await client.search("your query", max_results=100)
```
