# Semantic Search POC (Archived)

**Archived:** October 13, 2025
**Reason:** Not used in production flow
**Total LOC:** 743

---

## Contents

### Embeddings Module (278 LOC)
- `embeddings/service.py` - OpenAI embeddings service
- `embeddings/__init__.py` - Module exports

**Usage:** Only imported in `scripts/test_semantic_search.py` (test script)

**Why Archived:**
- Not used in production search flow
- Search uses direct API calls (GEO, PubMed, OpenAlex)
- No semantic search in current implementation

### Vector Database Module (465 LOC)
- `vector_db/faiss_db.py` (213 LOC) - FAISS vector database
- `vector_db/chroma_db.py` (252 LOC) - ChromaDB alternative
- `vector_db/interface.py` - Vector DB interface

**Usage:** Only imported in `scripts/test_semantic_search.py` (test script)

**Why Archived:**
- Not used in production search flow
- No vector similarity search implemented
- Proof of concept only

---

## Recovery Instructions

If you want to implement semantic search in the future:

```bash
# Restore embeddings
git mv extras/semantic-search-poc/embeddings omics_oracle_v2/lib/

# Restore vector_db
git mv extras/semantic-search-poc/vector_db omics_oracle_v2/lib/

# Install dependencies
pip install sentence-transformers faiss-cpu chromadb

# Test
python omics_oracle_v2/scripts/test_semantic_search.py
```

---

## Implementation Notes

**Semantic search was explored as POC for:**
- Finding similar biomarkers using embeddings
- Semantic query expansion beyond keyword matching
- Citation similarity scoring

**Not implemented because:**
- Current keyword-based search meets requirements
- GEO/PubMed APIs provide sufficient recall
- Added complexity without clear benefit
- Performance overhead from embedding generation

**If implementing:**
1. Generate embeddings for dataset titles/summaries
2. Store in FAISS/ChromaDB
3. Add `/semantic-search` endpoint
4. Hybrid: Combine keyword + semantic results
