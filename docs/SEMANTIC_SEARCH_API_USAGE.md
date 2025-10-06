# Semantic Search API Usage Guide

## Overview

The OmicsOracle Search Agent API now supports **AI-powered semantic search** in addition to traditional keyword search. Semantic search uses advanced natural language processing to:

- **Expand queries** with related scientific terms
- **Hybrid ranking** combining keyword and vector similarity
- **Cross-encoder reranking** for higher precision
- **Intelligent caching** for faster repeated queries

## Quick Start

### Traditional Keyword Search (Default)

```bash
curl -X POST "http://localhost:8000/api/v1/agents/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": ["breast cancer", "RNA-seq"],
    "max_results": 20,
    "enable_semantic": false
  }'
```

### Semantic Search (AI-Powered)

```bash
curl -X POST "http://localhost:8000/api/v1/agents/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": ["breast cancer", "RNA-seq"],
    "max_results": 20,
    "enable_semantic": true
  }'
```

## API Endpoint

**POST** `/api/v1/agents/search`

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_terms` | `List[str]` | Yes | - | List of search terms or phrases |
| `filters` | `Dict[str, str]` | No | `None` | Optional filters (organism, min_samples, etc.) |
| `max_results` | `int` | No | `20` | Maximum number of results (1-100) |
| `enable_semantic` | `bool` | No | `false` | Enable AI-powered semantic search |

### Response Format

```json
{
  "success": true,
  "execution_time_ms": 1234.56,
  "timestamp": "2025-10-05T12:34:56Z",
  "total_found": 150,
  "datasets": [
    {
      "geo_id": "GSE12345",
      "title": "Breast cancer RNA-seq study",
      "summary": "Comprehensive RNA-seq analysis of breast cancer...",
      "organism": "Homo sapiens",
      "sample_count": 48,
      "platform": "Illumina HiSeq 2500",
      "relevance_score": 0.95,
      "match_reasons": [
        "High semantic similarity",
        "Cross-encoder score: 0.95",
        "Keywords: breast cancer, RNA-seq"
      ]
    }
  ],
  "search_terms_used": ["breast cancer", "RNA-seq"],
  "filters_applied": {
    "search_mode": "semantic"
  }
}
```

## Python Client Examples

### Using `requests` Library

```python
import requests

# API configuration
API_URL = "http://localhost:8000/api/v1/agents/search"
TOKEN = "your_auth_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Semantic search request
payload = {
    "search_terms": ["alzheimer's disease", "proteomics"],
    "max_results": 10,
    "enable_semantic": True,
    "filters": {
        "organism": "Homo sapiens",
        "min_samples": "20"
    }
}

response = requests.post(API_URL, json=payload, headers=headers)
data = response.json()

# Process results
if data["success"]:
    print(f"Found {data['total_found']} datasets")
    print(f"Search mode: {data['filters_applied']['search_mode']}")

    for dataset in data["datasets"][:5]:
        print(f"\n{dataset['geo_id']}: {dataset['title']}")
        print(f"  Relevance: {dataset['relevance_score']:.2f}")
        print(f"  Samples: {dataset['sample_count']}")
        print(f"  Reasons: {', '.join(dataset['match_reasons'])}")
```

### Using `httpx` (Async)

```python
import asyncio
import httpx

async def semantic_search(query_terms: list[str]):
    """Execute semantic search asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agents/search",
            json={
                "search_terms": query_terms,
                "max_results": 20,
                "enable_semantic": True
            },
            headers={
                "Authorization": "Bearer YOUR_TOKEN",
                "Content-Type": "application/json"
            }
        )
        return response.json()

# Run
results = asyncio.run(semantic_search(["diabetes", "metabolomics"]))
print(f"Search mode: {results['filters_applied']['search_mode']}")
```

## JavaScript/TypeScript Examples

### Using Fetch API

```javascript
async function semanticSearch(searchTerms, enableSemantic = true) {
  const response = await fetch('http://localhost:8000/api/v1/agents/search', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      search_terms: searchTerms,
      max_results: 20,
      enable_semantic: enableSemantic
    })
  });

  const data = await response.json();

  if (data.success) {
    console.log(`Found ${data.total_found} datasets`);
    console.log(`Search mode: ${data.filters_applied.search_mode}`);
    return data.datasets;
  } else {
    throw new Error('Search failed');
  }
}

// Usage
const datasets = await semanticSearch(['lung cancer', 'scRNA-seq'], true);
```

### Using Axios

```typescript
import axios from 'axios';

interface SearchRequest {
  search_terms: string[];
  max_results?: number;
  enable_semantic?: boolean;
  filters?: Record<string, string>;
}

interface SearchResponse {
  success: boolean;
  total_found: number;
  datasets: Array<{
    geo_id: string;
    title: string;
    relevance_score: number;
    // ... other fields
  }>;
  filters_applied: {
    search_mode: 'semantic' | 'keyword';
  };
}

async function searchDatasets(request: SearchRequest): Promise<SearchResponse> {
  const response = await axios.post<SearchResponse>(
    'http://localhost:8000/api/v1/agents/search',
    request,
    {
      headers: {
        'Authorization': 'Bearer YOUR_TOKEN',
        'Content-Type': 'application/json'
      }
    }
  );

  return response.data;
}

// Example: Semantic search with filters
const results = await searchDatasets({
  search_terms: ['cardiovascular disease', 'genomics'],
  max_results: 15,
  enable_semantic: true,
  filters: {
    organism: 'Homo sapiens',
    min_samples: '30'
  }
});

console.log(`Mode: ${results.filters_applied.search_mode}`);
```

## Comparison: Keyword vs Semantic Search

### Keyword Search (Traditional)
- ✅ Fast and predictable
- ✅ Works without index pre-computation
- ✅ Good for exact matches
- ❌ Limited to exact term matching
- ❌ Misses synonyms and related concepts
- ❌ No understanding of scientific relationships

### Semantic Search (AI-Powered)
- ✅ Understands scientific concepts and relationships
- ✅ Automatically expands queries with related terms
- ✅ Finds relevant results even without exact keyword matches
- ✅ Cross-encoder reranking for higher precision
- ✅ Cached for faster repeated queries
- ⚠️ Requires FAISS index (pre-computed embeddings)
- ⚠️ Slightly slower on first query (no cache)

## Example Use Cases

### Use Case 1: Broad Scientific Concept Search

**Query:** "immune response in viral infections"

**Keyword Search:** Finds datasets with exact terms "immune response" or "viral infections"

**Semantic Search:**
- Expands to: innate immunity, adaptive immunity, antiviral response, cytokine signaling
- Finds related concepts: interferon response, T-cell activation, antibody production
- Higher recall and precision

### Use Case 2: Disease Synonym Handling

**Query:** "alzheimer's disease"

**Keyword Search:** Only matches "alzheimer's disease" or "alzheimer"

**Semantic Search:**
- Understands synonyms: AD, alzheimer, neurodegenerative disease
- Finds related: cognitive decline, dementia, tau protein, amyloid beta
- Matches datasets even if they use different terminology

### Use Case 3: Cross-Domain Research

**Query:** "gut microbiome and mental health"

**Keyword Search:** Requires exact phrase matches

**Semantic Search:**
- Connects concepts: gut-brain axis, psychobiotics, dysbiosis
- Finds datasets studying: depression + microbiota, anxiety + gut flora
- Discovers connections across research domains

## Requirements

### For Keyword Search (Default)
- None - works out of the box

### For Semantic Search
- **FAISS Index:** Pre-computed dataset embeddings
- **Index Location:** `data/vector_db/geo_index.faiss`
- **Creation:** Run `python -m omics_oracle_v2.scripts.embed_geo_datasets`

### Creating the Index

```bash
# Embed all GEO datasets (one-time setup)
python -m omics_oracle_v2.scripts.embed_geo_datasets \
  --batch-size 32 \
  --output-dir data/vector_db

# This creates:
# - data/vector_db/geo_index.faiss (FAISS index)
# - data/vector_db/geo_metadata.json (dataset metadata)
```

## Automatic Fallback

If semantic search is requested but the index is unavailable:

1. **Warning logged:** "Semantic search requested but index unavailable"
2. **Automatic fallback:** Uses keyword search instead
3. **Response indicates mode:** `filters_applied.search_mode = "keyword"`
4. **No error thrown:** Search still succeeds

## Performance Considerations

### Keyword Search
- **Speed:** Very fast (~100-500ms)
- **Scalability:** Linear with GEO database size
- **Resource Usage:** Minimal

### Semantic Search
- **First Query:** ~1-3 seconds (query expansion + embedding + search + reranking)
- **Cached Query:** ~200-500ms (cache hit)
- **Resource Usage:** Higher (LLM calls, vector search, cross-encoder)
- **Scalability:** Logarithmic with dataset count (FAISS)

### Recommendations
- **Use keyword search** for: Simple exact-match queries, high-volume API calls
- **Use semantic search** for: Complex research questions, exploratory searches, concept-based queries

## Error Handling

```python
try:
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()  # Raise exception for HTTP errors

    data = response.json()

    if not data["success"]:
        print(f"Search failed: {data.get('error', 'Unknown error')}")
    else:
        # Check which mode was used
        mode = data["filters_applied"].get("search_mode", "unknown")
        if mode == "keyword" and payload.get("enable_semantic"):
            print("Warning: Semantic search unavailable, used keyword search")

        # Process results
        for dataset in data["datasets"]:
            print(f"{dataset['geo_id']}: {dataset['title']}")

except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.exceptions.ConnectionError:
    print("Could not connect to API server")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Cache Management**
   - Semantic search caches results automatically
   - Cache key includes query + filters
   - TTL: 1 hour (configurable)

2. **Query Formulation**
   - **Keyword search:** Use specific terms (e.g., "GSE12345", "breast cancer")
   - **Semantic search:** Use natural language (e.g., "studies on immune response in cancer patients")

3. **Filter Usage**
   - Filters apply to both search modes
   - Combine semantic search with filters for best results
   - Example: `{"organism": "Homo sapiens", "min_samples": "50"}`

4. **Result Interpretation**
   - Check `match_reasons` to understand why datasets matched
   - `relevance_score` ranges from 0-1 (higher = more relevant)
   - Semantic search may return different results than keyword search

5. **Index Management**
   - Rebuild index periodically to include new datasets
   - Index size grows with dataset count (~500MB for 100K datasets)
   - Consider incremental updates for production systems

## API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Troubleshooting

### Problem: Semantic search returns keyword results

**Solution:** Index not found. Create index:
```bash
python -m omics_oracle_v2.scripts.embed_geo_datasets
```

### Problem: Slow first query in semantic mode

**Expected:** First query is slower due to:
1. Query expansion (LLM call)
2. Embedding generation
3. FAISS search
4. Cross-encoder reranking

**Solution:** Results are cached for subsequent queries. Consider warming up cache for common queries.

### Problem: Different results between modes

**Expected:** Semantic and keyword search use different algorithms:
- Keyword: Exact term matching + TF-IDF ranking
- Semantic: Vector similarity + hybrid ranking + cross-encoder

**Solution:** This is normal. Choose the mode that fits your use case.

## Support

For issues or questions:
- GitHub Issues: https://github.com/sdodlapati3/OmicsOracle/issues
- Documentation: https://omicsoracle.readthedocs.io
- Email: support@omicsoracle.io

---

**Last Updated:** 2025-10-05
**API Version:** v1
**Feature Status:** ✅ Production Ready
