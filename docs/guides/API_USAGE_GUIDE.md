# OmicsOracle API Usage Guide

## Overview

OmicsOracle provides a RESTful API for biomedical literature search, machine learning-powered recommendations, citation predictions, and trend analysis.

**Base URL**: `https://api.omicsoracle.com` (production) or `http://localhost:8000` (local)

## Authentication

All API endpoints require authentication using an API key.

### Getting an API Key

```bash
# Generate a new API key
curl -X POST http://localhost:8000/api/auth/keys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "tier": "basic"
  }'
```

### Using Your API Key

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/health/
```

### Rate Limits

| Tier | Requests/Hour | Use Case |
|------|---------------|----------|
| Free | 100 | Testing, personal use |
| Basic | 1,000 | Small applications |
| Pro | 10,000 | Production applications |
| Enterprise | Unlimited | Large-scale deployments |

## Health Check Endpoints

### Basic Health Check

```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/health/
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Detailed Health Check

```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/health/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2.5
    },
    "ml_service": {
      "status": "healthy",
      "models_loaded": 4
    }
  }
}
```

## Search Endpoints

### Search Publications

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8000/api/search?query=CRISPR&limit=10"
```

Response:
```json
{
  "results": [
    {
      "pmid": "12345678",
      "title": "CRISPR gene editing...",
      "authors": ["Smith J", "Doe J"],
      "journal": "Nature",
      "year": 2023,
      "abstract": "...",
      "citations": 150
    }
  ],
  "total": 1234,
  "page": 1,
  "per_page": 10
}
```

## Recommendation Endpoints

### Similar Publications

Find publications similar to a given PMID:

```bash
curl -X POST http://localhost:8000/api/recommendations/similar \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmid": "12345678",
    "top_k": 5,
    "min_similarity": 0.7
  }'
```

Response:
```json
{
  "recommendations": [
    {
      "pmid": "87654321",
      "title": "Related CRISPR study...",
      "similarity_score": 0.92,
      "relevance_reason": "Similar methodology and findings"
    }
  ],
  "query_pmid": "12345678",
  "total_found": 5
}
```

### Emerging Research

Discover trending research in a field:

```bash
curl -X POST http://localhost:8000/api/recommendations/emerging \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "field": "cancer immunotherapy",
    "top_k": 10,
    "time_window_months": 6
  }'
```

Response:
```json
{
  "recommendations": [
    {
      "pmid": "99887766",
      "title": "Novel CAR-T cell approach...",
      "trend_score": 0.85,
      "citation_velocity": 15.2
    }
  ],
  "field": "cancer immunotherapy",
  "total_found": 10
}
```

### High-Impact Papers

Find influential papers in a research area:

```bash
curl -X POST http://localhost:8000/api/recommendations/high-impact \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "field": "machine learning",
    "top_k": 5,
    "min_citations": 100
  }'
```

Response:
```json
{
  "recommendations": [
    {
      "pmid": "11223344",
      "title": "Deep learning in genomics...",
      "impact_score": 0.95,
      "citations": 450,
      "h_index": 35
    }
  ],
  "field": "machine learning",
  "total_found": 5
}
```

## Prediction Endpoints

### Citation Prediction

Predict future citations for a publication:

```bash
curl -X POST http://localhost:8000/api/predictions/citations \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmid": "12345678",
    "months_ahead": 12
  }'
```

Response:
```json
{
  "pmid": "12345678",
  "current_citations": 150,
  "predicted_citations": 225,
  "prediction_months": 12,
  "confidence_interval": {
    "lower": 200,
    "upper": 250
  },
  "model_confidence": 0.88
}
```

### Trend Forecasting

Forecast research trends:

```bash
curl -X POST http://localhost:8000/api/predictions/trends \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "field": "gene therapy",
    "months_ahead": 6
  }'
```

Response:
```json
{
  "field": "gene therapy",
  "forecast_months": 6,
  "predictions": [
    {
      "month": 1,
      "publication_count": 120,
      "trend_score": 0.75
    }
  ],
  "overall_trend": "increasing",
  "confidence": 0.82
}
```

### Impact Prediction

Predict the future impact of a publication:

```bash
curl -X POST http://localhost:8000/api/predictions/impact \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmid": "12345678",
    "months_ahead": 24
  }'
```

Response:
```json
{
  "pmid": "12345678",
  "predicted_impact_score": 0.85,
  "predicted_h_index": 15,
  "predicted_citations": 300,
  "confidence": 0.80,
  "factors": [
    "High journal impact factor",
    "Novel methodology",
    "Active research area"
  ]
}
```

## Analytics Endpoints

### Topic Analysis

Analyze topics in a set of publications:

```bash
curl -X POST http://localhost:8000/api/analytics/topics \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmids": ["12345678", "87654321"],
    "num_topics": 5
  }'
```

Response:
```json
{
  "topics": [
    {
      "topic_id": 0,
      "keywords": ["CRISPR", "gene editing", "genome"],
      "weight": 0.45,
      "description": "Gene editing technologies"
    }
  ],
  "total_topics": 5,
  "pmids_analyzed": 2
}
```

### Citation Network

Analyze citation relationships:

```bash
curl -X POST http://localhost:8000/api/analytics/citation-network \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmid": "12345678",
    "depth": 2
  }'
```

Response:
```json
{
  "root_pmid": "12345678",
  "nodes": [
    {
      "pmid": "12345678",
      "title": "...",
      "citations": 150
    }
  ],
  "edges": [
    {
      "source": "12345678",
      "target": "87654321",
      "weight": 1.0
    }
  ],
  "network_depth": 2,
  "total_papers": 25
}
```

### Research Clusters

Identify research clusters:

```bash
curl -X POST http://localhost:8000/api/analytics/clusters \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "field": "neuroscience",
    "num_clusters": 5,
    "min_cluster_size": 10
  }'
```

Response:
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "size": 45,
      "central_topics": ["brain imaging", "fMRI"],
      "representative_papers": ["11111111", "22222222"]
    }
  ],
  "total_clusters": 5,
  "field": "neuroscience"
}
```

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Rate limit exceeded
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## Best Practices

### 1. Use Caching

Results are cached for 7 days. Identical requests return cached results.

### 2. Batch Requests

For multiple operations, use batch endpoints when available:

```bash
curl -X POST http://localhost:8000/api/recommendations/batch \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pmids": ["12345678", "87654321", "11223344"]
  }'
```

### 3. Monitor Rate Limits

Check rate limit headers in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705320000
```

### 4. Handle Errors Gracefully

Implement exponential backoff for rate limits:

```python
import time

def call_api_with_retry(url, max_retries=3):
    for i in range(max_retries):
        response = requests.get(url)
        if response.status_code == 429:
            time.sleep(2 ** i)  # 1s, 2s, 4s
            continue
        return response
    raise Exception("Max retries exceeded")
```

## Python SDK Example

```python
from omicsoracle_client import OmicsOracleClient

# Initialize client
client = OmicsOracleClient(api_key="your-key")

# Search publications
results = client.search("CRISPR", limit=10)

# Get recommendations
similar = client.get_similar_publications(pmid="12345678", top_k=5)

# Predict citations
prediction = client.predict_citations(pmid="12345678", months_ahead=12)

# Analyze topics
topics = client.analyze_topics(pmids=["12345678", "87654321"])
```

## Support

- Documentation: https://docs.omicsoracle.com
- API Status: https://status.omicsoracle.com
- Support: support@omicsoracle.com
- GitHub: https://github.com/omicsoracle/api
