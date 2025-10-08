# OmicsOracle API Reference

**Version:** 2.0
**Date:** June 25, 2025
**Status:** Production API

---

## 📋 Overview

The OmicsOracle API provides programmatic access to genomics metadata search and summarization capabilities. Built with FastAPI, it offers high-performance, well-documented endpoints for integration with research workflows.

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.omicsoracle.com`

### API Version
- **Current Version**: `v1`
- **Versioning Strategy**: URL-based (`/api/v1/`)

---

## 🔐 Authentication

### API Key Authentication
```http
Authorization: Bearer your-api-key-here
```

### Rate Limiting
- **Authenticated**: 1000 requests/hour
- **Unauthenticated**: 100 requests/hour
- **Headers**: Rate limit info in response headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

---

## 🔍 Search Endpoints

### Basic Search
Search GEO datasets using natural language queries.

```http
GET /api/v1/search
```

**Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Results per page (default: 10, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `format` (string, optional): Response format (`json`, `csv`, `bibtex`)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/search?q=WGBS%20brain%20cancer&limit=5" \
  -H "Authorization: Bearer your-api-key"
```

**Example Response:**
```json
{
  "query": "WGBS brain cancer",
  "total_results": 25,
  "results": [
    {
      "accession": "GSE123456",
      "title": "Whole genome bisulfite sequencing of brain cancer samples",
      "organism": "Homo sapiens",
      "platform": "GPL13534",
      "samples": 24,
      "summary": "This study investigates DNA methylation patterns...",
      "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123456",
      "last_updated": "2024-06-15T10:30:00Z"
    }
  ],
  "pagination": {
    "limit": 5,
    "offset": 0,
    "total": 25,
    "has_next": true
  }
}
```

### Advanced Search
Perform structured searches with multiple filters.

```http
POST /api/v1/search/advanced
```

**Request Body:**
```json
{
  "query": "brain cancer",
  "filters": {
    "organism": "Homo sapiens",
    "platform": ["GPL13534", "GPL16791"],
    "study_type": "Expression profiling by high throughput sequencing",
    "sample_count_min": 10,
    "date_range": {
      "start": "2020-01-01",
      "end": "2024-12-31"
    }
  },
  "sort": {
    "field": "date",
    "order": "desc"
  },
  "limit": 20,
  "offset": 0
}
```

**Response:** Same format as basic search with filtered results.

---

## 📊 Metadata Endpoints

### Get Dataset Details
Retrieve complete metadata for a specific GEO dataset.

```http
GET /api/v1/metadata/{accession}
```

**Parameters:**
- `accession` (string, required): GEO accession number (GSE, GDS, GPL, GSM)
- `include_samples` (boolean, optional): Include sample details (default: false)
- `include_summary` (boolean, optional): Include AI-generated summary (default: true)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/metadata/GSE123456?include_samples=true" \
  -H "Authorization: Bearer your-api-key"
```

**Example Response:**
```json
{
  "accession": "GSE123456",
  "title": "Whole genome bisulfite sequencing of brain cancer samples",
  "description": "Complete dataset description...",
  "organism": "Homo sapiens",
  "platform": {
    "accession": "GPL13534",
    "title": "Illumina HumanMethylation450 BeadChip",
    "technology": "oligonucleotide beads"
  },
  "samples": [
    {
      "accession": "GSM987654",
      "title": "Brain cancer sample 1",
      "characteristics": {
        "tissue": "brain",
        "disease_state": "cancer",
        "age": "65"
      }
    }
  ],
  "publication": {
    "title": "DNA methylation patterns in brain cancer",
    "authors": ["Smith J", "Doe J"],
    "journal": "Nature Genetics",
    "pubmed_id": "12345678"
  },
  "ai_summary": {
    "brief": "This study analyzed DNA methylation...",
    "key_findings": ["Hypermethylation in tumor suppressor genes"],
    "methodology": "WGBS",
    "sample_size": 24,
    "confidence_score": 0.95
  },
  "last_updated": "2024-06-15T10:30:00Z"
}
```

### Bulk Metadata
Retrieve metadata for multiple datasets.

```http
POST /api/v1/metadata/bulk
```

**Request Body:**
```json
{
  "accessions": ["GSE123456", "GSE789012", "GSE345678"],
  "include_samples": false,
  "include_summary": true
}
```

**Response:** Array of metadata objects.

---

## 🤖 AI Endpoints

### Generate Summary
Generate AI-powered summaries for datasets.

```http
POST /api/v1/ai/summarize
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "summary_type": "brief|detailed|executive",
  "focus_areas": ["methodology", "key_findings", "clinical_relevance"],
  "include_citations": true
}
```

**Example Response:**
```json
{
  "accession": "GSE123456",
  "summary": {
    "brief": "This study investigates DNA methylation patterns...",
    "methodology": "Whole genome bisulfite sequencing (WGBS)",
    "key_findings": [
      "Significant hypermethylation in tumor suppressor genes",
      "Novel methylation signatures associated with prognosis"
    ],
    "clinical_relevance": "Potential biomarkers for brain cancer diagnosis",
    "confidence_score": 0.95,
    "generated_at": "2024-06-25T14:30:00Z"
  }
}
```

### Query Suggestions
Get search query suggestions and refinements.

```http
POST /api/v1/ai/suggest
```

**Request Body:**
```json
{
  "partial_query": "brain can",
  "max_suggestions": 5,
  "context": "genomics"
}
```

**Example Response:**
```json
{
  "suggestions": [
    {
      "query": "brain cancer methylation",
      "description": "DNA methylation studies in brain cancer",
      "count": 156
    },
    {
      "query": "brain cancer expression",
      "description": "Gene expression profiling in brain tumors",
      "count": 234
    }
  ]
}
```

---

## 📈 Analytics Endpoints

### Search Analytics
Get analytics on search patterns and popular queries.

```http
GET /api/v1/analytics/search
```

**Parameters:**
- `period` (string, optional): Time period (`day`, `week`, `month`) (default: week)
- `metric` (string, optional): Specific metric (`queries`, `results`, `users`)

**Example Response:**
```json
{
  "period": "week",
  "metrics": {
    "total_queries": 1250,
    "unique_users": 89,
    "avg_results_per_query": 15.2,
    "top_queries": [
      {
        "query": "cancer genomics",
        "count": 45,
        "success_rate": 0.92
      }
    ]
  }
}
```

### Dataset Analytics
Get analytics on dataset access and popularity.

```http
GET /api/v1/analytics/datasets
```

**Example Response:**
```json
{
  "trending_datasets": [
    {
      "accession": "GSE123456",
      "title": "Brain cancer WGBS",
      "access_count": 156,
      "trend": "up"
    }
  ],
  "popular_organisms": [
    {"organism": "Homo sapiens", "count": 890},
    {"organism": "Mus musculus", "count": 234}
  ],
  "platform_distribution": [
    {"platform": "GPL13534", "count": 123}
  ]
}
```

---

## 📤 Export Endpoints

### Export Search Results
Export search results in various formats.

```http
POST /api/v1/export
```

**Request Body:**
```json
{
  "query": "brain cancer",
  "format": "csv|json|bibtex|ris",
  "include_summaries": true,
  "fields": ["accession", "title", "organism", "summary"]
}
```

**Response:**
```json
{
  "export_id": "export_abc123",
  "status": "processing",
  "format": "csv",
  "estimated_completion": "2024-06-25T14:35:00Z",
  "download_url": null
}
```

### Download Export
Download completed export file.

```http
GET /api/v1/export/{export_id}/download
```

**Response:** File download with appropriate content-type.

---

## 🔧 Utility Endpoints

### Health Check
Check API health and service status.

```http
GET /api/v1/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-25T14:30:00Z",
  "version": "2.0.0",
  "services": {
    "ncbi_api": "healthy",
    "cache": "healthy",
    "nlp": "healthy",
    "database": "healthy"
  },
  "response_time_ms": 45
}
```

### Service Status
Detailed service status information.

```http
GET /api/v1/status
```

**Example Response:**
```json
{
  "uptime_seconds": 86400,
  "requests_today": 12450,
  "cache_hit_rate": 0.78,
  "avg_response_time_ms": 120,
  "active_connections": 15,
  "system_resources": {
    "cpu_usage": 0.35,
    "memory_usage": 0.62,
    "disk_usage": 0.45
  }
}
```

---

## 📚 SDKs and Libraries

### Python SDK
```bash
pip install omics-oracle-sdk
```

```python
from omics_oracle import OmicsOracleClient

client = OmicsOracleClient(api_key="your-api-key")

# Search datasets
results = client.search("brain cancer WGBS", limit=10)

# Get metadata
metadata = client.get_metadata("GSE123456")

# Generate summary
summary = client.generate_summary("GSE123456", type="brief")
```

### JavaScript SDK
```bash
npm install omics-oracle-js
```

```javascript
import { OmicsOracleClient } from 'omics-oracle-js';

const client = new OmicsOracleClient({ apiKey: 'your-api-key' });

// Search datasets
const results = await client.search('brain cancer WGBS', { limit: 10 });

// Get metadata
const metadata = await client.getMetadata('GSE123456');
```

---

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameter",
    "details": {
      "field": "limit",
      "constraint": "must be between 1 and 100"
    },
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes
- `400 BAD_REQUEST`: Invalid request parameters
- `401 UNAUTHORIZED`: Missing or invalid API key
- `403 FORBIDDEN`: Access denied
- `404 NOT_FOUND`: Resource not found
- `429 RATE_LIMITED`: Rate limit exceeded
- `500 INTERNAL_ERROR`: Server error
- `503 SERVICE_UNAVAILABLE`: External service unavailable

---

## 📊 Response Schemas

### Dataset Schema
```json
{
  "type": "object",
  "properties": {
    "accession": {"type": "string"},
    "title": {"type": "string"},
    "organism": {"type": "string"},
    "platform": {"type": "string"},
    "samples": {"type": "integer"},
    "summary": {"type": "string"},
    "url": {"type": "string", "format": "uri"},
    "last_updated": {"type": "string", "format": "date-time"}
  }
}
```

---

*For additional API support and integration examples, visit our [GitHub repository](https://github.com/your-org/OmicsOracle) or contact our support team.*
