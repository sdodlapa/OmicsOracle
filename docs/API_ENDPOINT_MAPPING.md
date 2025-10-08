# API Endpoint Mapping

**Date:** October 8, 2025
**Status:** Phase 3 - Validation & Testing
**Purpose:** Map integration layer methods to actual backend API endpoints

---

## Discovery Summary

The backend has **both** `/api/` and `/api/v1/` routes (duplicated for backward compatibility).

**Available Endpoints:** (from `/openapi.json`)
- ✅ Health: `/health/`, `/health/detailed`, `/health/ready`
- ✅ Search: `/api/agents/search`, `/search` (same handler)
- ✅ Analysis: `/api/agents/analyze`
- ✅ Q&A: `/api/agents/query`
- ✅ Report: `/api/agents/report`
- ✅ Workflows: `/api/workflows/execute`, `/api/workflows/types`
- ✅ Recommendations: `/api/recommendations/similar`, `/api/recommendations/emerging`
- ✅ Predictions: `/api/predictions/citations`, `/api/predictions/trends`
- ✅ Analytics: `/api/analytics/*`
- ✅ Auth: `/api/auth/*` (all endpoints require authentication)

---

## Integration Layer → Backend Mapping

### SearchClient Methods

| Integration Method | Backend Endpoint | Request Schema | Auth Required |
|-------------------|------------------|----------------|---------------|
| `search(query, databases, max_results)` | `POST /api/agents/search` | `{search_terms: [str], max_results: int, enable_semantic: bool}` | No |
| `get_suggestions(partial_query)` | Not implemented yet | - | - |
| `get_publication(pub_id)` | Not implemented yet | - | - |
| `get_search_history()` | Not implemented yet | - | - |
| `save_search()` | Not implemented yet | - | - |
| `delete_search()` | Not implemented yet | - | - |
| `export_results()` | Client-side only | - | - |

### AnalysisClient Methods

| Integration Method | Backend Endpoint | Request Schema | Auth Required |
|-------------------|------------------|----------------|---------------|
| `analyze_with_llm(query, results)` | `POST /api/agents/analyze` | `{search_terms: [str], context: {...}}` | No |
| `ask_question(question, context)` | `POST /api/agents/query` | `{question: str, context: [pub]}` | No |
| `get_trends(query, years)` | `POST /api/predictions/trends` | TBD | No |
| `get_citation_network(results)` | Not implemented yet | - | - |
| `get_publication_quality(pub_id)` | Not implemented yet | - | - |
| `get_biomarkers(results)` | `GET /api/analytics/biomarker/{biomarker}` | - | No |
| `generate_report(query, results)` | `POST /api/agents/report` | `{search_terms: [str], results: [...]}` | No |

### MLClient Methods

| Integration Method | Backend Endpoint | Request Schema | Auth Required |
|-------------------|------------------|----------------|---------------|
| `get_recommendations(seed_papers)` | `POST /api/recommendations/similar` | `{publication_ids: [str]}` | No |
| `predict_citations(pub_id)` | `POST /api/predictions/citations` | `{publication_id: str}` | No |
| `get_trending_topics()` | `POST /api/predictions/trends` | `{years: int}` | No |
| `get_emerging_authors()` | `POST /api/recommendations/emerging` | `{field: str, years: int}` | No |
| `predict_impact(publication)` | Not implemented yet | - | - |
| `get_similar_authors(author_id)` | Not implemented yet | - | - |

---

## Request/Response Schema Differences

### Search Request
**Integration Layer (user-friendly):**
```python
SearchRequest(
    query="CRISPR gene therapy",  # Single string
    databases=["pubmed", "semantic_scholar"],  # List of databases
    max_results=50,
    filters={"year": "2023-2025"}
)
```

**Backend API (actual):**
```python
{
    "search_terms": ["CRISPR", "gene therapy"],  # Array of terms!
    "max_results": 50,
    "enable_semantic": true,
    "filters": {"year": "2023-2025"}
}
```

**Transformation Needed:**
- Split `query` string into `search_terms` array
- Map `databases` → `enable_semantic` boolean
- Keep `max_results` and `filters` as-is

---

### Analysis Request
**Integration Layer:**
```python
AnalysisRequest(
    query="CRISPR",
    context_publications=[Publication(...), ...]
)
```

**Backend API:**
```python
{
    "search_terms": ["CRISPR"],
    "context": {
        "publications": [...],
        "focus": "mechanisms"
    }
}
```

---

### Recommendation Request
**Integration Layer:**
```python
RecommendationRequest(
    seed_papers=["pmid:12345", "pmid:67890"],
    max_results=10
)
```

**Backend API:**
```python
{
    "publication_ids": ["pmid:12345", "pmid:67890"],
    "max_results": 10
}
```

---

## Authentication Notes

**Current Status:** Most endpoints do NOT require auth (for development)

**When Auth is Required:** (based on OpenAPI spec)
- `/api/workflows/execute` → 401 Unauthorized
- `/api/users/*` → Requires auth
- `/api/auth/*` → Public (login, register)

**Future:** All endpoints will require authentication in production

---

## Rate Limiting

**Current Status:** Rate limiting is active (429 errors observed)

**Limits:** (from backend logs)
- 60 requests per minute per IP (default)
- Can be adjusted in settings

**Integration Layer Handling:**
- Built-in retry with exponential backoff
- Client-side rate limiting (60 req/min)
- Request queueing

---

## Next Steps

1. ✅ Document actual API endpoints (DONE)
2. ⏳ Update integration layer to match backend schemas
3. ⏳ Add request transformers (query → search_terms, etc.)
4. ⏳ Add response transformers (backend format → integration models)
5. ⏳ Test all endpoints against live backend
6. ⏳ Add authentication support
7. ⏳ Document missing endpoints (need implementation)

---

**Key Discovery:**
The integration layer was designed with the *ideal* API in mind, but the backend uses different schemas. We need an **adapter layer** to bridge the gap!

**Solution:**
Add request/response transformers in each client to adapt between the user-friendly integration layer API and the actual backend API.
