# OmicsOracle API Reference

**Version:** 3.0
**Date:** October 8, 2025
**Status:** Production API (Phase 4 Complete)
**Major Changes:** Added Authentication, AI Agents, Enhanced Search, Performance Metrics

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

### JWT Token Authentication (NEW - Phase 4)

All protected endpoints require JWT token authentication.

```http
Authorization: Bearer <access_token>
```

**Token Lifetime:**
- Access token: 60 minutes
- Refresh token: 7 days

---

### Authentication Endpoints (NEW)

#### Register User
Create a new user account.

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "institution": "University of Example",
  "research_area": "Genomics"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "institution": "University of Example",
    "created_at": "2025-10-08T14:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Performance:** <500ms

---

#### Login
Authenticate and receive JWT tokens.

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "researcher"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Performance:** <500ms

---

#### Refresh Token
Get a new access token using refresh token.

```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Performance:** <200ms

---

#### Get Current User
Get authenticated user information.

```http
GET /api/auth/me
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "institution": "University of Example",
  "research_area": "Genomics",
  "role": "researcher",
  "created_at": "2025-10-08T14:30:00Z",
  "last_login": "2025-10-08T15:45:00Z"
}
```

---

#### Logout
Invalidate current session and tokens.

```http
POST /api/auth/logout
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

### API Key Authentication (Legacy)

> **Deprecated:** API key authentication is maintained for backward compatibility but JWT tokens are recommended.

```http
Authorization: Bearer your-api-key-here
```

### Rate Limiting (Enhanced)

**Per User (Authenticated):**
- Standard: 100 requests/hour
- Premium: 1000 requests/hour

**Per IP (Unauthenticated):**
- 20 requests/hour

**Per Endpoint:**
- Search: 50 requests/hour
- AI Analysis: 20 requests/hour
- Export: 10 requests/hour

**Headers:** Rate limit info in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1696776000
X-RateLimit-Policy: user
```

---

## 🤖 AI Agent Endpoints (NEW - Phase 4)

The multi-agent system provides specialized AI-powered capabilities for dataset discovery, analysis, and insights.

---

### Search Agent
Execute intelligent GEO dataset search with advanced filtering.

```http
POST /api/agents/search
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "breast cancer RNA-seq",
  "filters": {
    "organism": "Homo sapiens",
    "platform": ["GPL16791", "GPL20301"],
    "study_type": "Expression profiling by high throughput sequencing",
    "sample_count_min": 10,
    "sample_count_max": 1000,
    "date_range": {
      "start": "2020-01-01",
      "end": "2025-12-31"
    },
    "quality_threshold": 0.7
  },
  "sort_by": "relevance",
  "limit": 20,
  "include_quality_scores": true,
  "use_cache": true
}
```

**Response (200 OK):**
```json
{
  "query": "breast cancer RNA-seq",
  "processing_time_ms": 24500,
  "cache_hit": false,
  "total_results": 156,
  "results": [
    {
      "accession": "GSE123456",
      "title": "RNA-seq profiling of breast cancer tissues",
      "organism": "Homo sapiens",
      "platform": "GPL16791",
      "samples": 48,
      "study_type": "Expression profiling by high throughput sequencing",
      "summary": "Comprehensive RNA-seq analysis of breast cancer...",
      "quality_score": 0.92,
      "relevance_score": 0.88,
      "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123456",
      "last_updated": "2025-03-15T10:30:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 156,
    "has_next": true
  },
  "applied_filters": {
    "organism": "Homo sapiens",
    "platform_count": 2,
    "quality_threshold": 0.7
  }
}
```

**Performance:** 20-30 seconds (cached: <1 second)

---

### Analysis Agent (GPT-4)
Generate AI-powered insights and analysis for datasets.

```http
POST /api/agents/analyze
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "analysis_type": "comprehensive",
  "focus_areas": [
    "methodology",
    "key_findings",
    "clinical_relevance",
    "limitations"
  ],
  "include_citations": true,
  "output_format": "structured"
}
```

**Response (200 OK):**
```json
{
  "accession": "GSE123456",
  "analysis": {
    "summary": "This RNA-seq study comprehensively analyzes gene expression patterns in breast cancer tissues...",
    "methodology": {
      "description": "Illumina HiSeq 2500 platform with paired-end 100bp reads",
      "sample_size": 48,
      "controls": 24,
      "technical_replicates": true,
      "quality_metrics": "High quality (Q30 > 90%)"
    },
    "key_findings": [
      "Identification of 2,345 differentially expressed genes",
      "Novel tumor-specific isoforms discovered",
      "Validation of known breast cancer biomarkers"
    ],
    "clinical_relevance": {
      "score": 0.85,
      "summary": "High clinical relevance with potential diagnostic applications",
      "applications": [
        "Biomarker discovery",
        "Therapeutic target identification",
        "Patient stratification"
      ]
    },
    "limitations": [
      "Single-center study",
      "Limited ethnic diversity",
      "No long-term follow-up data"
    ],
    "recommendations": [
      "Validation in independent cohort recommended",
      "Consider integration with proteomics data",
      "Investigate clinical outcomes correlation"
    ]
  },
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 1850,
    "processing_time_ms": 13500,
    "confidence_score": 0.94,
    "generated_at": "2025-10-08T15:30:00Z"
  }
}
```

**Performance:** 13-15 seconds
**Cost:** ~$0.04 per analysis (GPT-4 tokens)

---

### Q&A Agent
Answer questions about specific datasets using GPT-4.

```http
POST /api/agents/qa
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "question": "What are the main findings and how were they validated?",
  "context_length": "full",
  "include_citations": true
}
```

**Response (200 OK):**
```json
{
  "accession": "GSE123456",
  "question": "What are the main findings and how were they validated?",
  "answer": "The study identified 2,345 differentially expressed genes in breast cancer tissues. The main findings include:\n\n1. Discovery of novel tumor-specific isoforms\n2. Validation of known biomarkers (ER, PR, HER2)\n3. Identification of potential therapeutic targets\n\nValidation approaches:\n- qRT-PCR validation in subset of samples (n=12)\n- Cross-platform validation using microarray data\n- Independent validation cohort (GSE789012)\n- Protein-level validation via Western blot",
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 450,
    "processing_time_ms": 8500,
    "confidence_score": 0.91,
    "sources": ["dataset_metadata", "publication_abstract", "sample_descriptions"]
  }
}
```

**Performance:** 8-12 seconds

---

### Quality Agent
Get data quality predictions and scores for datasets.

```http
POST /api/agents/quality
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accessions": ["GSE123456", "GSE789012"],
  "include_breakdown": true
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "accession": "GSE123456",
      "quality_score": 0.92,
      "quality_grade": "A",
      "breakdown": {
        "metadata_completeness": 0.95,
        "sample_count_adequacy": 0.90,
        "publication_status": 1.0,
        "data_availability": 0.88,
        "platform_quality": 0.92
      },
      "flags": [],
      "recommendations": [
        "Excellent quality dataset suitable for meta-analysis"
      ]
    },
    {
      "accession": "GSE789012",
      "quality_score": 0.65,
      "quality_grade": "C",
      "breakdown": {
        "metadata_completeness": 0.70,
        "sample_count_adequacy": 0.60,
        "publication_status": 0.0,
        "data_availability": 0.80,
        "platform_quality": 0.75
      },
      "flags": [
        "unpublished",
        "incomplete_metadata",
        "small_sample_size"
      ],
      "recommendations": [
        "Use with caution",
        "Supplement with additional datasets",
        "Verify metadata manually"
      ]
    }
  ],
  "processing_time_ms": 450
}
```

**Performance:** <1 second

---

### Recommendation Agent
Get related datasets and research recommendations.

```http
POST /api/agents/recommend
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "recommendation_types": [
    "similar_studies",
    "complementary_data",
    "related_publications",
    "trending_datasets"
  ],
  "max_results": 10,
  "min_similarity": 0.7
}
```

**Response (200 OK):**
```json
{
  "accession": "GSE123456",
  "recommendations": {
    "similar_studies": [
      {
        "accession": "GSE789012",
        "title": "RNA-seq analysis of breast cancer subtypes",
        "similarity_score": 0.88,
        "reason": "Same organism, technology, and disease focus"
      }
    ],
    "complementary_data": [
      {
        "accession": "GSE456789",
        "title": "Proteomics of breast cancer tissues",
        "relevance_score": 0.82,
        "reason": "Same samples, different -omics layer"
      }
    ],
    "related_publications": [
      {
        "pubmed_id": "12345678",
        "title": "Breast cancer transcriptomics review",
        "relevance_score": 0.75,
        "cited_datasets": ["GSE123456", "GSE789012"]
      }
    ],
    "trending_datasets": [
      {
        "accession": "GSE999999",
        "title": "Single-cell RNA-seq of breast tumors",
        "trend_score": 0.92,
        "access_count_7d": 450
      }
    ]
  },
  "metadata": {
    "total_recommendations": 25,
    "processing_time_ms": 1800
  }
}
```

**Performance:** 1-2 seconds

---

## 🔍 Search Endpoints (Enhanced)

### Basic Search (Updated)
Search GEO datasets using natural language queries.

> **Note:** For advanced AI-powered search with quality filtering, use `/api/agents/search`

```http
GET /api/search/datasets
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Results per page (default: 10, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `format` (string, optional): Response format (`json`, `csv`)
- `include_quality` (boolean, optional): Include quality scores (default: false)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/search/datasets?q=WGBS%20brain%20cancer&limit=5&include_quality=true" \
  -H "Authorization: Bearer <access_token>"
```

**Example Response:**
```json
{
  "query": "WGBS brain cancer",
  "total_results": 25,
  "processing_time_ms": 850,
  "results": [
    {
      "accession": "GSE123456",
      "title": "Whole genome bisulfite sequencing of brain cancer samples",
      "organism": "Homo sapiens",
      "platform": "GPL13534",
      "samples": 24,
      "summary": "This study investigates DNA methylation patterns...",
      "quality_score": 0.89,
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

**Performance:** <2 seconds (simple query)

### Advanced Search (Updated)
Perform structured searches with multiple filters.

> **Recommended:** Use `/api/agents/search` for AI-enhanced search with quality filtering

```http
POST /api/search/advanced
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
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

**Performance:** 2-5 seconds

---

### Get Dataset Details
Retrieve complete metadata for a specific GEO dataset.

```http
GET /api/search/datasets/{accession}
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Parameters:**
- `accession` (string, required): GEO accession number (GSE, GDS, GPL, GSM)
- `include_samples` (boolean, optional): Include sample details (default: false)
- `include_analysis` (boolean, optional): Include AI analysis (default: false)
- `include_quality` (boolean, optional): Include quality score (default: true)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/search/datasets/GSE123456?include_samples=true&include_analysis=true" \
  -H "Authorization: Bearer <access_token>"
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
  "quality_score": 0.92,
  "ai_analysis": {
    "summary": "This study analyzed DNA methylation patterns in brain cancer using WGBS...",
    "key_findings": [
      "Hypermethylation in tumor suppressor genes",
      "Novel methylation signatures identified"
    ],
    "clinical_relevance": "Potential biomarkers for brain cancer diagnosis",
    "confidence_score": 0.95,
    "generated_at": "2025-10-08T14:30:00Z"
  },
  "last_updated": "2024-06-15T10:30:00Z"
}
```

**Performance:** <1 second (cached), 2-3 seconds (fresh)

---

## 📊 Analysis Endpoints (Enhanced)

### Citation Analysis
Extract and analyze citations from datasets.

```http
POST /api/analysis/citations
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "include_network": true,
  "depth": 2
}
```

**Response (200 OK):**
```json
{
  "accession": "GSE123456",
  "publication": {
    "pubmed_id": "12345678",
    "title": "DNA methylation patterns in brain cancer",
    "citation_count": 245,
    "year": 2023
  },
  "cited_by": [
    {
      "pubmed_id": "98765432",
      "title": "Follow-up study on methylation",
      "year": 2024
    }
  ],
  "citation_network": {
    "nodes": 50,
    "edges": 120,
    "clusters": 3
  }
}
```

---

### Biomarker Detection
Identify potential biomarkers in datasets.

```http
POST /api/analysis/biomarkers
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accession": "GSE123456",
  "biomarker_types": ["gene", "protein", "metabolite"],
  "significance_threshold": 0.05
}
```

**Response (200 OK):**
```json
{
  "accession": "GSE123456",
  "biomarkers": [
    {
      "name": "TP53",
      "type": "gene",
      "fold_change": 4.5,
      "p_value": 0.001,
      "confidence": "high"
    }
  ]
}
```

---

### Research Trends
Analyze research trends for specific topics or datasets.

```http
POST /api/analysis/trends
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "topic": "breast cancer genomics",
  "time_range": {
    "start": "2020-01-01",
    "end": "2025-12-31"
  },
  "granularity": "month"
}
```

**Response (200 OK):**
```json
{
  "topic": "breast cancer genomics",
  "trends": {
    "publications_per_month": [
      {"month": "2020-01", "count": 45},
      {"month": "2020-02", "count": 52}
    ],
    "trending_technologies": [
      {"technology": "single-cell RNA-seq", "growth_rate": 0.35}
    ],
    "emerging_topics": [
      {"topic": "tumor microenvironment", "score": 0.82}
    ]
  }
}
```

---

## � Metadata Endpoints (Updated)

### Bulk Metadata
Retrieve metadata for multiple datasets.

```http
POST /api/metadata/bulk
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "accessions": ["GSE123456", "GSE789012", "GSE345678"],
  "include_samples": false,
  "include_quality": true,
  "include_analysis": false
}
```

**Response:** Array of metadata objects.

**Performance:** 2-4 seconds for 3 datasets

---

## 🤖 AI Endpoints (Legacy - Deprecated)

> **Deprecated:** The following endpoints are superseded by the new `/api/agents/*` endpoints which provide enhanced AI capabilities.

### Generate Summary (Deprecated)

**Use Instead:** `POST /api/agents/analyze`

```http
POST /api/v1/ai/summarize
```

### Query Suggestions (Deprecated)

**Use Instead:** Query Agent capabilities in `POST /api/agents/search`

```http
POST /api/v1/ai/suggest
```
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

## 📤 Export Endpoints (Enhanced)

### Export Search Results
Export search results in various formats.

```http
POST /api/export
```

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "brain cancer",
  "filters": {
    "organism": "Homo sapiens"
  },
  "format": "csv|json|pdf",
  "include_summaries": true,
  "include_quality_scores": true,
  "fields": ["accession", "title", "organism", "summary", "quality_score"]
}
```

**Response (202 Accepted):**
```json
{
  "export_id": "export_abc123",
  "status": "processing",
  "format": "csv",
  "estimated_completion_seconds": 30,
  "download_url": null
}
```

**Performance:** 30-60 seconds for large exports

---

### Check Export Status
Check the status of an export job.

```http
GET /api/export/{export_id}/status
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "export_id": "export_abc123",
  "status": "completed",
  "format": "csv",
  "file_size_bytes": 524288,
  "record_count": 150,
  "download_url": "/api/export/export_abc123/download",
  "expires_at": "2025-10-09T14:30:00Z"
}
```

---

### Download Export
Download completed export file.

```http
GET /api/export/{export_id}/download
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response:** File download with appropriate content-type.
- `text/csv` for CSV
- `application/json` for JSON
- `application/pdf` for PDF

**File Retention:** 24 hours

---

## � Analytics Endpoints (Updated)

### User Analytics
Get analytics for the authenticated user.

```http
GET /api/analytics/user
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "user_abc123",
  "period": "30_days",
  "metrics": {
    "total_searches": 145,
    "total_analyses": 32,
    "total_exports": 8,
    "favorite_organisms": [
      {"organism": "Homo sapiens", "count": 98},
      {"organism": "Mus musculus", "count": 47}
    ],
    "most_used_agents": [
      {"agent": "search", "count": 145},
      {"agent": "analysis", "count": 32},
      {"agent": "quality", "count": 28}
    ],
    "tokens_used": 45000,
    "estimated_cost_usd": 1.12
  }
}
```

---

### System Analytics (Admin Only)
Get system-wide analytics.

```http
GET /api/analytics/system
```

**Headers:**
```http
Authorization: Bearer <admin_access_token>
```

**Parameters:**
- `period` (string, optional): `day`, `week`, `month` (default: week)

**Response (200 OK):**
```json
{
  "period": "week",
  "metrics": {
    "total_users": 342,
    "active_users": 189,
    "total_requests": 8450,
    "total_searches": 4200,
    "total_analyses": 850,
    "cache_hit_rate": 0.64,
    "avg_search_time_ms": 24500,
    "avg_analysis_time_ms": 13800,
    "total_tokens_used": 1250000,
    "total_cost_usd": 31.25
  },
  "top_queries": [
    {
      "query": "cancer genomics",
      "count": 125,
      "success_rate": 0.94
    }
  ],
  "trending_datasets": [
    {
      "accession": "GSE123456",
      "access_count": 245,
      "trend": "up"
    }
  ]
}
```

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
- `401 UNAUTHORIZED`: Missing or invalid JWT token
- `403 FORBIDDEN`: Access denied or insufficient permissions
- `404 NOT_FOUND`: Resource not found
- `429 RATE_LIMITED`: Rate limit exceeded
- `500 INTERNAL_ERROR`: Server error
- `503 SERVICE_UNAVAILABLE`: External service unavailable (NCBI, OpenAI)

### Authentication Error Codes (NEW)
- `401 INVALID_TOKEN`: JWT token is invalid or expired
- `401 TOKEN_EXPIRED`: Access token has expired (use refresh token)
- `403 INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `429 AUTH_RATE_LIMITED`: Too many authentication attempts

---

## 📈 Performance Metrics (Phase 4)

### Endpoint Performance Summary

| Endpoint Category | Avg Response Time | Cached | Notes |
|------------------|-------------------|--------|-------|
| **Authentication** | | | |
| Register/Login | <500ms | N/A | Password hashing |
| Token Refresh | <200ms | N/A | Fast token ops |
| **AI Agents** | | | |
| Search Agent | 20-30s | <1s | NCBI API bound |
| Analysis Agent (GPT-4) | 13-15s | N/A | GPT-4 bound |
| Q&A Agent | 8-12s | N/A | GPT-4 bound |
| Quality Agent | <1s | <100ms | Fast algorithm |
| Recommendation Agent | 1-2s | <500ms | Similarity calc |
| **Search & Metadata** | | | |
| Basic Search | 1-2s | <500ms | Simple queries |
| Advanced Search | 2-5s | <1s | Complex filters |
| Dataset Details | <1s | <200ms | Single dataset |
| **Analysis** | | | |
| Citations | 2-3s | <1s | Network analysis |
| Biomarkers | 3-5s | <1s | Statistical |
| Trends | 5-8s | <2s | Time series |
| **Export** | | | |
| Generate Export | 30-60s | N/A | Large files |
| Download | Instant | N/A | Pre-generated |

### Cost Estimates (AI Operations)

| Operation | GPT-4 Tokens | Est. Cost | Daily (10x) | Monthly (300x) |
|-----------|--------------|-----------|-------------|----------------|
| Dataset Analysis | ~2000 | $0.04 | $0.40 | $12.00 |
| Q&A Query | ~450 | $0.01 | $0.10 | $3.00 |
| Comprehensive (Both) | ~2450 | $0.05 | $0.50 | $15.00 |

**Note:** Based on GPT-4 pricing (~$0.02/1K tokens). Caching reduces costs by ~40%.

---

## 📊 Response Schemas (Enhanced)

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
    "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
    "url": {"type": "string", "format": "uri"},
    "last_updated": {"type": "string", "format": "date-time"}
  }
}
```

### User Schema (NEW)
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string"},
    "email": {"type": "string", "format": "email"},
    "full_name": {"type": "string"},
    "institution": {"type": "string"},
    "research_area": {"type": "string"},
    "role": {"type": "string", "enum": ["researcher", "admin"]},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```

### AI Analysis Schema (NEW)
```json
{
  "type": "object",
  "properties": {
    "accession": {"type": "string"},
    "analysis": {
      "type": "object",
      "properties": {
        "summary": {"type": "string"},
        "methodology": {"type": "object"},
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "clinical_relevance": {"type": "object"},
        "limitations": {"type": "array"},
        "recommendations": {"type": "array"}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "model": {"type": "string"},
        "tokens_used": {"type": "integer"},
        "processing_time_ms": {"type": "integer"},
        "confidence_score": {"type": "number"},
        "generated_at": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

---

## 🔄 Migration Guide (v2.0 → v3.0)

### Breaking Changes

1. **Authentication Required**
   - All endpoints now require JWT authentication (except `/api/health`)
   - Old API key authentication deprecated but supported for 6 months
   - **Action:** Register users and obtain JWT tokens

2. **Endpoint Paths Changed**
   - `/api/v1/search` → `/api/search/datasets`
   - `/api/v1/metadata/{id}` → `/api/search/datasets/{id}`
   - `/api/v1/ai/summarize` → `/api/agents/analyze` (deprecated)
   - **Action:** Update client code to use new paths

3. **New Required Headers**
   ```http
   Authorization: Bearer <access_token>
   Content-Type: application/json
   ```

4. **Rate Limits Reduced for Unauthenticated**
   - Unauthenticated: 1000/hour → 20/hour
   - **Action:** Authenticate to get higher limits (100-1000/hour)

### New Features in v3.0

1. **Multi-Agent System** - 5 specialized AI agents
2. **GPT-4 Integration** - Advanced analysis capabilities
3. **Quality Scoring** - Data quality predictions
4. **Recommendations** - Related dataset suggestions
5. **Enhanced Analytics** - User and system metrics
6. **Performance Metrics** - Detailed timing information

### Recommended Upgrade Path

**Step 1:** Register and authenticate
```http
POST /api/auth/register
POST /api/auth/login
```

**Step 2:** Update client to use JWT tokens
```javascript
// Old
headers: { 'Authorization': 'Bearer api-key-123' }

// New
headers: { 'Authorization': `Bearer ${access_token}` }
```

**Step 3:** Migrate to new agent endpoints
```javascript
// Old
POST /api/v1/ai/summarize

// New
POST /api/agents/analyze
```

**Step 4:** Implement token refresh
```javascript
if (error.code === 'TOKEN_EXPIRED') {
  const newToken = await refreshToken(refresh_token);
  // Retry request with new token
}
```

---

## 📚 Code Examples

### Python SDK (Updated for v3.0)

```python
from omics_oracle import OmicsOracleClient

# Initialize with authentication
client = OmicsOracleClient()

# Register and login
user = client.auth.register(
    email="researcher@university.edu",
    password="SecurePass123!",
    full_name="Dr. Jane Doe",
    institution="Example University"
)

# Or login if already registered
tokens = client.auth.login(
    email="researcher@university.edu",
    password="SecurePass123!"
)

# Search with AI agent (20-30s)
results = client.agents.search(
    query="breast cancer RNA-seq",
    filters={"organism": "Homo sapiens"},
    limit=10
)

# Analyze dataset with GPT-4 (13-15s)
analysis = client.agents.analyze(
    accession="GSE123456",
    analysis_type="comprehensive"
)

# Get quality scores (<1s)
quality = client.agents.quality(
    accessions=["GSE123456", "GSE789012"]
)

# Get recommendations (1-2s)
recommendations = client.agents.recommend(
    accession="GSE123456",
    max_results=10
)

# Export results
export_job = client.export.create(
    query="brain cancer",
    format="csv",
    include_quality_scores=True
)

# Wait for export and download
export_file = client.export.download(export_job.id)
```

### JavaScript SDK (Updated for v3.0)

```javascript
import { OmicsOracleClient } from 'omics-oracle-js';

// Initialize client
const client = new OmicsOracleClient();

// Authenticate
const { tokens, user } = await client.auth.login({
  email: 'researcher@university.edu',
  password: 'SecurePass123!'
});

// Auto-refresh tokens
client.setTokens(tokens.access_token, tokens.refresh_token);

// Search with AI agent
const results = await client.agents.search({
  query: 'breast cancer RNA-seq',
  filters: { organism: 'Homo sapiens' },
  limit: 10
});

// Analyze with GPT-4
const analysis = await client.agents.analyze({
  accession: 'GSE123456',
  analysis_type: 'comprehensive'
});

// Q&A about dataset
const answer = await client.agents.qa({
  accession: 'GSE123456',
  question: 'What are the main findings?'
});

// Export results
const exportJob = await client.export.create({
  query: 'brain cancer',
  format: 'pdf',
  include_summaries: true
});

const file = await client.export.download(exportJob.id);
```

---

## 🎯 Best Practices

### Authentication
- ✅ **DO:** Store refresh tokens securely (encrypted)
- ✅ **DO:** Implement automatic token refresh
- ✅ **DO:** Use environment variables for sensitive data
- ❌ **DON'T:** Store tokens in client-side localStorage (use httpOnly cookies)
- ❌ **DON'T:** Share tokens between users

### Performance Optimization
- ✅ **DO:** Use `/api/agents/search` with `use_cache: true`
- ✅ **DO:** Batch requests when possible
- ✅ **DO:** Implement client-side caching (respect cache headers)
- ❌ **DON'T:** Make redundant AI agent calls (they're expensive)
- ❌ **DON'T:** Poll for export status too frequently (use callbacks if available)

### Cost Management (AI Operations)
- ✅ **DO:** Cache AI analysis results on client side
- ✅ **DO:** Use `include_analysis: false` when you don't need AI summaries
- ✅ **DO:** Share analysis results across team members
- ✅ **DO:** Monitor token usage via `/api/analytics/user`
- ❌ **DON'T:** Re-analyze same datasets repeatedly
- ❌ **DON'T:** Request comprehensive analysis when brief is sufficient

### Rate Limit Management
- ✅ **DO:** Respect `X-RateLimit-*` headers
- ✅ **DO:** Implement exponential backoff on 429 errors
- ✅ **DO:** Upgrade to Premium for higher limits if needed
- ❌ **DON'T:** Ignore rate limit warnings
- ❌ **DON'T:** Create multiple accounts to bypass limits

---

## 📞 Support & Resources

### Documentation
- **API Reference:** This document
- **Getting Started Guide:** `/docs/guides/QUICK_START.md`
- **Architecture:** `/docs/phase5-review-2025-10-08/SYSTEM_ARCHITECTURE.md`
- **Integration Guide:** `/docs/current-2025-10/integration/INTEGRATION_LAYER_GUIDE.md`

### SDKs & Libraries
- **Python SDK:** `pip install omics-oracle-sdk`
- **JavaScript SDK:** `npm install omics-oracle-js`
- **R Package:** Coming soon

### Support Channels
- **GitHub Issues:** [github.com/your-org/OmicsOracle/issues](https://github.com/your-org/OmicsOracle/issues)
- **Email:** support@omicsoracle.com
- **Community Forum:** [community.omicsoracle.com](https://community.omicsoracle.com)

### Status Page
- **System Status:** [status.omicsoracle.com](https://status.omicsoracle.com)
- **Incident History:** Available on status page
- **Planned Maintenance:** Announced 48h in advance

---

**Version History:**
- **v3.0** (Oct 8, 2025): Added authentication, multi-agent system, GPT-4 integration, quality scoring
- **v2.0** (Jun 25, 2025): Enhanced search, AI summarization, analytics
- **v1.0** (Jan 15, 2025): Initial release

*For the latest API updates and changelogs, visit our documentation repository.*
