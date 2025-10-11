# Pipeline Decision Guide - Which Pipeline Should I Use?

**Last Updated:** October 10, 2025
**Purpose:** Help users choose the right pipeline for their use case

---

## 🚀 Quick Decision Tree

```
┌─ Do you have a GEO dataset ID (GSE123456)?
│  └─ YES → Use GEOCitationPipeline
│
┌─ Do you want to search for publications by topic/keyword?
│  └─ YES → Use PublicationSearchPipeline
│
┌─ Do you want to search your indexed local data semantically?
│  └─ YES → Use AdvancedSearchPipeline
│
┌─ Do you want to ask questions about specific papers?
│  └─ YES → Use RAGPipeline
│
└─ Do you just need to generate embeddings?
   └─ YES → Use GEOEmbeddingPipeline
```

---

## 📊 Pipeline Comparison Matrix

| Pipeline | Data Source | Input | Output | Use Case | Speed |
|----------|-------------|-------|--------|----------|-------|
| **GEOCitationPipeline** | GEO + PubMed + Scholar | GEO ID or query | Datasets + Citations + PDFs | Complete GEO workflow | Medium |
| **PublicationSearchPipeline** | PubMed, OpenAlex, Scholar APIs | Search query | Publications + Citations + PDFs | General publication search | Medium |
| **AdvancedSearchPipeline** | Local vector DB (FAISS) | Search query | Indexed docs + RAG answer | Semantic search over local data | Fast |
| **RAGPipeline** | Documents you provide | Question + Documents | Natural language answer | Q&A over specific papers | Fast |
| **GEOEmbeddingPipeline** | GEO datasets | Dataset metadata | Vector embeddings | Index datasets for search | Medium |

---

## 🎯 Detailed Pipeline Guide

### 1. GEOCitationPipeline

**When to use:**
- ✅ You have GEO dataset IDs (e.g., GSE123456)
- ✅ You want to find papers that cite those datasets
- ✅ You need a complete workflow: GEO → Citations → PDFs
- ✅ You're researching dataset reuse and impact

**What it does:**
1. Searches GEO for datasets (by ID or topic)
2. Extracts associated publication PMIDs
3. Finds papers that cite those publications
4. Downloads PDFs when available
5. Analyzes citation contexts

**Example:**
```python
from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline

# Initialize pipeline
pipeline = GEOCitationPipeline()

# Option 1: Search by GEO ID
result = await pipeline.collect(geo_id="GSE123456")

# Option 2: Search by topic
result = await pipeline.collect(query="breast cancer RNA-seq")

# Results include:
# - GEO datasets found
# - Original publications (from GEO metadata)
# - Citing papers (who reused the data)
# - PDFs downloaded
# - Citation analysis
```

**Output structure:**
```python
{
    'geo_datasets': [GEODataset(...)],
    'original_publications': [Publication(...)],
    'citing_papers': [Publication(...)],
    'pdfs_downloaded': ['path/to/pdf1.pdf', ...],
    'citation_analyses': [CitationAnalysis(...)],
    'total_citations': 42
}
```

**Best for:**
- 📊 Dataset impact analysis
- 🔬 Finding novel applications of existing datasets
- 📚 Literature review starting from GEO
- 🎯 Reproducibility research

---

### 2. PublicationSearchPipeline

**When to use:**
- ✅ You want to search for publications by topic/keywords
- ✅ You need results from multiple sources (PubMed, OpenAlex, Scholar)
- ✅ You want automatic deduplication and ranking
- ✅ You need institutional access or PDF downloads
- ✅ You're doing a comprehensive literature search

**What it does:**
1. Searches multiple publication databases (PubMed, OpenAlex, Google Scholar)
2. Deduplicates results across sources
3. Ranks by relevance
4. Enriches with citation data
5. Downloads PDFs via institutional access or open sources
6. Extracts full text from PDFs

**Example:**
```python
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

# Configure which sources to use
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_scholar=True,
    enable_citations=True,
    enable_pdf_download=True,
    enable_institutional_access=True,
    primary_institution="gatech"
)

# Initialize pipeline
pipeline = PublicationSearchPipeline(config)

# Search for publications
result = pipeline.search(
    query="CRISPR gene editing in cancer",
    max_results=50,
    min_relevance_score=0.7
)

# Results include:
# - Ranked publications from all enabled sources
# - Citation counts and metrics
# - PDF paths (if downloaded)
# - Full text (if extracted)
# - Institutional access status
```

**Output structure:**
```python
PublicationResult(
    query="CRISPR gene editing",
    publications=[PublicationSearchResult(...)],  # Ranked results
    total_found=127,
    sources_used=['pubmed', 'openalex', 'scholar'],
    search_time_ms=3542.1
)
```

**Best for:**
- 📚 Comprehensive literature searches
- 🔍 Finding papers across multiple databases
- 📄 Downloading and analyzing PDFs
- 🎓 Academic research requiring institutional access
- 🧬 Biomedical/life sciences research

**Feature toggles:**
```python
# Minimal setup (PubMed only)
config = PublicationSearchConfig(enable_pubmed=True)

# With citations but no PDFs
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_citations=True,
    enable_pdf_download=False
)

# Full featured
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_scholar=True,
    enable_citations=True,
    enable_pdf_download=True,
    enable_fulltext=True,
    enable_institutional_access=True
)
```

---

### 3. AdvancedSearchPipeline

**When to use:**
- ✅ You've already indexed documents locally
- ✅ You want semantic (meaning-based) search, not just keyword matching
- ✅ You need query expansion with biomedical synonyms
- ✅ You want reranked results for precision
- ✅ You need natural language answers (RAG) from your indexed data
- ✅ Speed is critical (searches local index, not external APIs)

**What it does:**
1. Expands query with biomedical synonyms
2. Performs hybrid search (keyword + semantic) on local vector DB
3. Reranks results with cross-encoder for precision
4. Generates natural language answers with RAG
5. Caches results for 10-100x speedup on repeated queries

**Example:**
```python
from omics_oracle_v2.lib.search.advanced import AdvancedSearchPipeline, AdvancedSearchConfig

# Configure features
config = AdvancedSearchConfig(
    enable_query_expansion=True,
    enable_reranking=True,
    enable_rag=True,
    enable_caching=True
)

# Initialize pipeline
pipeline = AdvancedSearchPipeline(config)

# First, index your documents
documents = [
    {
        'id': 'GSE123001',
        'text': 'ATAC-seq analysis of chromatin accessibility...',
        'metadata': {'title': 'Chromatin dynamics', 'year': 2024}
    },
    # ... more documents
]
pipeline.add_documents(documents)

# Then search semantically
result = pipeline.search(
    query="What is ATAC-seq used for?",
    top_k=10,
    return_answer=True
)

# Results include:
# - Expanded query (with synonyms)
# - Search results (ranked)
# - Reranked results (top N)
# - Natural language answer
# - Citations
```

**Output structure:**
```python
SearchResult(
    query="What is ATAC-seq used for?",
    expanded_query="What is ATAC-seq (Assay for Transposase-Accessible Chromatin...) used for?",
    results=[...],  # All search results
    reranked_results=[...],  # Top results after reranking
    answer="ATAC-seq is used to study chromatin accessibility...",
    citations=[...],
    confidence=0.92,
    total_time_ms=234.5,
    cache_hit=False
)
```

**Best for:**
- 🔬 Semantic search over your GEO dataset collection
- 💡 Finding conceptually similar documents (not just keyword matches)
- ❓ Getting direct answers to questions about your indexed data
- ⚡ Fast repeated searches (caching)
- 🧠 Research that requires understanding context and meaning

**Key difference from PublicationSearchPipeline:**
- ❌ Does NOT search external APIs (PubMed, Scholar, etc.)
- ✅ Only searches documents YOU have already indexed
- ✅ Much faster (local search)
- ✅ Semantic/meaning-based (not just keywords)

---

### 4. RAGPipeline

**When to use:**
- ✅ You have specific documents and want to ask questions about them
- ✅ You need natural language answers with citations
- ✅ You're doing deep analysis of a small set of papers
- ✅ You want to extract specific information from documents

**What it does:**
1. Takes your documents and question as input
2. Finds relevant passages in the documents
3. Generates natural language answer using LLM
4. Provides citations to source documents
5. Returns confidence score

**Example:**
```python
from omics_oracle_v2.lib.rag.pipeline import RAGPipeline, RAGConfig, LLMProvider

# Configure LLM provider
config = RAGConfig(
    llm_provider=LLMProvider.OPENAI,
    model="gpt-4",
    max_context_tokens=8000
)

# Initialize pipeline
pipeline = RAGPipeline(config)

# Provide documents and ask question
documents = [
    {'id': 'paper1', 'text': 'Full text of paper 1...', 'metadata': {...}},
    {'id': 'paper2', 'text': 'Full text of paper 2...', 'metadata': {...}},
]

answer = pipeline.generate_answer(
    query="What are the main findings about ATAC-seq?",
    documents=documents
)

# Results include:
# - Natural language answer
# - Citations to source documents
# - Confidence score
# - Reasoning
```

**Output structure:**
```python
RAGResponse(
    answer="The main findings show that ATAC-seq reveals...",
    citations=[
        Citation(doc_id='paper1', title='...', excerpt='...'),
        Citation(doc_id='paper2', title='...', excerpt='...')
    ],
    confidence=0.89,
    reasoning="Based on the provided papers..."
)
```

**Best for:**
- 📖 Deep reading and analysis of specific papers
- 🎯 Extracting targeted information
- 📝 Summarizing findings across papers
- 🔬 Comparing methodologies or results
- 💡 Literature synthesis

---

### 5. GEOEmbeddingPipeline

**When to use:**
- ✅ You want to generate embeddings for GEO datasets
- ✅ You're building a searchable index of datasets
- ✅ You need vector representations for similarity search
- ✅ You're setting up the AdvancedSearchPipeline

**What it does:**
1. Fetches GEO dataset metadata
2. Creates rich text representation (title + description + techniques)
3. Generates vector embeddings using embedding model
4. Stores embeddings in vector database

**Example:**
```python
from omics_oracle_v2.lib.embeddings.geo_pipeline import GEOEmbeddingPipeline

# Initialize pipeline
pipeline = GEOEmbeddingPipeline()

# Generate embeddings for datasets
geo_ids = ['GSE123001', 'GSE123002', 'GSE123003']
embeddings = await pipeline.generate_embeddings(geo_ids)

# Or batch process
all_embeddings = await pipeline.batch_process(
    geo_ids=geo_ids,
    batch_size=10
)

# Results: Vector embeddings stored in DB for later search
```

**Best for:**
- 🗂️ Building searchable dataset collections
- 🔍 Enabling semantic search over datasets
- 📊 Dataset similarity analysis
- ⚙️ Infrastructure setup for AdvancedSearchPipeline

---

## 🔄 Common Workflows & Pipeline Combinations

### Workflow 1: Complete GEO Research Pipeline
**Goal:** Find GEO datasets, analyze citations, download PDFs

```python
# Step 1: Find relevant datasets and citations
geo_pipeline = GEOCitationPipeline()
result = await geo_pipeline.collect(query="breast cancer methylation")

# Step 2: Generate embeddings for semantic search
embedding_pipeline = GEOEmbeddingPipeline()
await embedding_pipeline.generate_embeddings([d.geo_id for d in result.geo_datasets])

# Step 3: Search semantically over indexed datasets
search_pipeline = AdvancedSearchPipeline()
search_result = search_pipeline.search(
    "epigenetic modifications in breast cancer",
    return_answer=True
)
```

### Workflow 2: Comprehensive Literature Search + Analysis
**Goal:** Search publications, download PDFs, ask questions

```python
# Step 1: Search for publications
pub_pipeline = PublicationSearchPipeline(config)
pubs = pub_pipeline.search("CRISPR off-target effects")

# Step 2: Ask specific questions about the papers
rag_pipeline = RAGPipeline(config)
answer = rag_pipeline.generate_answer(
    query="What are the most common off-target sites?",
    documents=[p.publication for p in pubs.publications]
)
```

### Workflow 3: Dataset Discovery → Publication Search
**Goal:** Find datasets, then search for related papers

```python
# Step 1: Find GEO datasets
geo_pipeline = GEOCitationPipeline()
geo_result = await geo_pipeline.collect(query="single cell RNA-seq")

# Step 2: Search for publications on same topic
pub_pipeline = PublicationSearchPipeline(config)
pub_result = pub_pipeline.search("single cell RNA-seq analysis methods")

# Step 3: Combine and deduplicate results
# (both pipelines return Publication objects)
```

### Workflow 4: Build Searchable Knowledge Base
**Goal:** Index large collection, enable fast semantic search

```python
# Step 1: Generate embeddings for all datasets
embedding_pipeline = GEOEmbeddingPipeline()
await embedding_pipeline.batch_process(all_geo_ids)

# Step 2: Set up semantic search
search_pipeline = AdvancedSearchPipeline(config)
# Documents already indexed from step 1

# Step 3: Search semantically (with caching for speed)
result = search_pipeline.search("chromatin remodeling in stem cells")
```

---

## 🆚 Key Differences Summary

### AdvancedSearchPipeline vs PublicationSearchPipeline

**MOST COMMON CONFUSION** - These are COMPLETELY DIFFERENT:

| Aspect | AdvancedSearchPipeline | PublicationSearchPipeline |
|--------|------------------------|---------------------------|
| **Data Source** | Local vector DB (YOUR indexed data) | External APIs (PubMed, OpenAlex, Scholar) |
| **Search Type** | Semantic (meaning-based) | Keyword + metadata |
| **Speed** | Very fast (local) | Medium (API calls) |
| **Setup Required** | Must index documents first | Ready to use immediately |
| **Query Expansion** | Biomedical synonyms | Optional NER-based |
| **Results** | Only your indexed docs | All matching publications online |
| **Best For** | Searching YOUR dataset collection | Finding NEW papers from databases |
| **Use When** | You've built a local knowledge base | You're discovering publications |

**Rule of Thumb:**
- 🏠 **Local search?** → AdvancedSearchPipeline
- 🌍 **Online search?** → PublicationSearchPipeline

### GEOCitationPipeline vs PublicationSearchPipeline

| Aspect | GEOCitationPipeline | PublicationSearchPipeline |
|--------|---------------------|---------------------------|
| **Starting Point** | GEO dataset ID or GEO search | Publication topic/keywords |
| **Focus** | Dataset-centric (who cited this dataset?) | Publication-centric (find papers on topic) |
| **Citation Analysis** | Dataset reuse tracking | General citation metrics |
| **GEO Integration** | Built-in, primary focus | Not included |
| **Best For** | Dataset impact analysis | General literature search |

---

## 🎓 Decision Examples

### Example 1: "I want to find papers about CRISPR"
**Answer:** Use **PublicationSearchPipeline**
- Searches external APIs for publications
- Returns ranked results from PubMed, OpenAlex, Scholar
- Can download PDFs

### Example 2: "I have GSE123456, who cited it?"
**Answer:** Use **GEOCitationPipeline**
- Designed exactly for this use case
- Finds citing papers automatically
- Analyzes dataset reuse

### Example 3: "I indexed 1000 GEO datasets, now I want to search them"
**Answer:** Use **AdvancedSearchPipeline**
- Semantic search over YOUR indexed data
- Fast local search
- RAG-based answers

### Example 4: "I have 5 PDFs, what do they say about X?"
**Answer:** Use **RAGPipeline**
- Q&A over specific documents
- Natural language answers
- Citations provided

### Example 5: "I want to build a searchable database of datasets"
**Answer:** Use **GEOEmbeddingPipeline** first, then **AdvancedSearchPipeline**
- GEOEmbeddingPipeline: Index the datasets
- AdvancedSearchPipeline: Search the index

---

## ⚙️ Configuration Cheat Sheet

### Minimal Setups

**Quick publication search:**
```python
config = PublicationSearchConfig(enable_pubmed=True)
pipeline = PublicationSearchPipeline(config)
```

**Quick semantic search:**
```python
config = AdvancedSearchConfig()  # All defaults
pipeline = AdvancedSearchPipeline(config)
```

**Quick GEO workflow:**
```python
pipeline = GEOCitationPipeline()  # No config needed
```

### Full-Featured Setups

**Complete publication pipeline:**
```python
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_scholar=True,
    enable_citations=True,
    enable_pdf_download=True,
    enable_fulltext=True,
    enable_institutional_access=True,
    primary_institution="gatech",
    enable_cache=True  # 10-100x speedup
)
```

**Complete semantic search:**
```python
config = AdvancedSearchConfig(
    enable_query_expansion=True,
    enable_reranking=True,
    enable_rag=True,
    enable_caching=True,
    top_k=20,
    rerank_top_k=10
)
```

---

## 🐛 Troubleshooting

### "Which pipeline should I use for [X]?"
1. **Starting with GEO ID?** → GEOCitationPipeline
2. **Searching for publications online?** → PublicationSearchPipeline
3. **Searching your indexed data?** → AdvancedSearchPipeline
4. **Asking questions about specific docs?** → RAGPipeline

### "Can I use multiple pipelines together?"
**Yes!** See "Common Workflows" section above.

### "AdvancedSearchPipeline returns no results"
- Did you index documents first with `add_documents()`?
- AdvancedSearchPipeline only searches YOUR indexed data, not external APIs

### "PublicationSearchPipeline is slow"
- It searches external APIs (PubMed, OpenAlex, Scholar) - this takes time
- Enable caching for 10-100x speedup on repeated queries:
  ```python
  config = PublicationSearchConfig(enable_cache=True)
  ```

### "I want semantic search over PubMed"
- Use **PublicationSearchPipeline** to get papers from PubMed
- Then use **AdvancedSearchPipeline** after indexing them locally

---

## 📚 Additional Resources

- **API Reference:** See each pipeline's docstrings for detailed API documentation
- **Examples:** Check `tests/` directory for working examples
- **Configuration:** See `lib/publications/config.py` for all available options
- **Architecture:** See `docs/architecture/` for system design details

---

## 🤝 Need Help?

**Still not sure which pipeline to use?**
1. Check the decision tree at the top
2. Look at the comparison matrix
3. Review the example scenarios
4. Check similar use cases in "Common Workflows"

**Found an issue or have a suggestion?**
- Open an issue on GitHub
- Contribute improvements to this guide

---

**Last Updated:** October 10, 2025
**Version:** 2.0
**Maintainer:** OmicsOracle Team
