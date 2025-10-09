# Integration Layer Documentation

**Version:** 3.0.0  
**Last Updated:** October 8, 2025  
**Status:** ✅ Phase 4 Complete - Production Ready  
**Purpose:** Clean abstraction layer between backend and multiple frontends with authentication, AI agents, and cost management

---

## 📋 Overview

The Integration Layer provides a **framework-agnostic** interface to all OmicsOracle backend features. This enables:

- ✅ **Multiple frontends** running simultaneously (Streamlit + React + Vue + Mobile)
- ✅ **Clean separation** of concerns (backend ↔ integration ↔ frontend)
- ✅ **Easy testing** (mock integration layer, not entire backend)
- ✅ **API versioning** (v1, v2, v3 support without breaking changes)
- ✅ **Type safety** (Pydantic models for all data)
- ✅ **Authentication** (JWT-based with automatic token refresh) 🆕
- ✅ **AI Agent Integration** (5 specialized agents with cost tracking) 🆕
- ✅ **Cost Management** (GPT-4 token and cost tracking) 🆕

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Streamlit   │  │    React     │  │     Vue      │      │
│  │  Dashboard   │  │    Admin     │  │   Mobile     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              INTEGRATION LAYER (Phase 4)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔐 AuthClient (NEW!)                                  │  │
│  │ - login()  - refresh_token()  - logout()             │  │
│  │ - register()  - me()  - update_profile()             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SearchClient    AnalysisClient    MLClient           │  │
│  │ - search()      - analyze_llm()   - recommend()      │  │
│  │ - get_pub()     - ask_question()  - predict()        │  │
│  │ - suggestions() - get_trends()    - score_quality()  │  │
│  │ - export()      - get_network()   - rank()           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🤖 AgentClient (NEW!)                                 │  │
│  │ - query_agent()  - search_agent()  - analysis_agent()│  │
│  │ - quality_agent()  - recommendation_agent()          │  │
│  │ - get_agent_status()  - get_cost_metrics()          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DataTransformer                                       │  │
│  │ - to_streamlit() - to_react() - to_vue() - to_csv()  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ APIClient (base class)                                │  │
│  │ - Auth - Caching - Rate limiting - Retries - Errors  │  │
│  │ - JWT Token Management - Cost Tracking               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND LAYER                             │
│  FastAPI - 60+ endpoints - 20+ routers - 180+ modules       │
│  🔐 JWT Auth - 🤖 5 AI Agents - 📊 GPT-4 Integration        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Integration layer is part of omics_oracle_v2
# No additional installation needed if you have the repo

# Dependencies (already in requirements.txt)
pip install httpx pydantic python-jose[cryptography]
```

### Basic Usage (With Authentication) 🆕

```python
import asyncio
from omics_oracle_v2.integration import AuthClient, SearchClient, AnalysisClient

async def main():
    # 1. AUTHENTICATE (NEW in Phase 4!)
    async with AuthClient() as auth:
        # Login
        auth_response = await auth.login(
            username="researcher@university.edu",
            password="secure_password"
        )

        # Store tokens
        access_token = auth_response.access_token
        refresh_token = auth_response.refresh_token

        print(f"✅ Logged in as: {auth_response.user.username}")
        print(f"   Token expires in: 60 minutes")

    # 2. Use authenticated clients
    async with SearchClient(access_token=access_token) as search:
        async with AnalysisClient(access_token=access_token) as analysis:

            # Execute search
            results = await search.search(
                query="CRISPR gene editing",
                max_results=50,
                search_mode="hybrid"
            )

            print(f"\nFound {results.metadata.total_results} papers")
            print(f"Time: {results.metadata.query_time:.1f}s")

            # Analyze with GPT-4
            llm_analysis = await analysis.analyze_with_llm(
                query="CRISPR gene editing",
                results=results.results[:10]
            )

            print(f"\nOverview: {llm_analysis.overview}")
            print(f"Key findings: {llm_analysis.key_findings}")
            print(f"Cost: ${llm_analysis.cost:.4f}")  # NEW!
            print(f"Tokens: {llm_analysis.tokens_used}")  # NEW!

            # Ask questions
            answer = await analysis.ask_question(
                question="What delivery mechanisms are most effective?",
                context=results.results
            )

            print(f"\nAnswer: {answer.answer}")
            print(f"Sources: {[s.title for s in answer.sources]}")
            print(f"Cost: ${answer.cost:.4f}")  # NEW!

# Run
asyncio.run(main())
```

### Quick Start (No Auth - Testing Only)

```python
# For local testing without authentication
async with SearchClient(base_url="http://localhost:8000") as search:
    results = await search.search("cancer immunotherapy")
    print(f"Found {len(results.results)} papers")
```

---

## 📦 Components

### 1. APIClient (Base Class)

**Purpose:** Common functionality for all clients

**Features:**
- ✅ Automatic retry with exponential backoff
- ✅ Response caching (5min TTL)
- ✅ Rate limiting (60 req/min)
- ✅ Authentication support
- ✅ API versioning (v1, v2)
- ✅ Error handling

**Example:**
```python
from omics_oracle_v2.integration import APIClient

async with APIClient(
    base_url="http://localhost:8000",
    api_version="v1",
    timeout=30.0,
    access_token="your-jwt-token"  # 🆕 JWT instead of API key
) as client:
    health = await client.health_check()
    print(health)
```

---

### 2. AuthClient 🆕

**Purpose:** User authentication and session management

**Methods:**
- `login(username, password)` - Authenticate user, get JWT tokens
- `register(username, email, password)` - Create new account
- `logout()` - Invalidate current session
- `refresh_token(refresh_token)` - Get new access token
- `me()` - Get current user profile
- `update_profile(name, affiliation, etc)` - Update user info
- `change_password(old_password, new_password)` - Change password
- `request_password_reset(email)` - Request password reset email

**Authentication Flow:**

```python
from omics_oracle_v2.integration import AuthClient

# 1. Login
async with AuthClient() as auth:
    # Authenticate
    response = await auth.login(
        username="researcher@university.edu",
        password="secure_password"
    )

    access_token = response.access_token  # Valid for 60 minutes
    refresh_token = response.refresh_token  # Valid for 7 days

    print(f"✅ Logged in as: {response.user.username}")
    print(f"   Role: {response.user.role}")
    print(f"   Token expires at: {response.expires_at}")

# 2. Use tokens with other clients
from omics_oracle_v2.integration import SearchClient

async with SearchClient(access_token=access_token) as search:
    results = await search.search("cancer")  # Authenticated request!

# 3. Refresh token (before expiration)
async with AuthClient() as auth:
    new_tokens = await auth.refresh_token(refresh_token)
    access_token = new_tokens.access_token  # New 60-minute token
```

**Registration Flow:**

```python
from omics_oracle_v2.integration import AuthClient

async with AuthClient() as auth:
    # Create account
    response = await auth.register(
        username="new_researcher",
        email="researcher@university.edu",
        password="secure_password",
        full_name="Dr. Jane Smith",
        affiliation="Stanford University"
    )

    # Automatically logged in after registration
    access_token = response.access_token
    print(f"✅ Account created: {response.user.username}")
```

**Error Handling:**

```python
from omics_oracle_v2.integration import AuthClient
from omics_oracle_v2.integration.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError
)

async with AuthClient() as auth:
    try:
        response = await auth.login(username, password)
    except AuthenticationError as e:
        print(f"❌ Login failed: {e.message}")
        # Show error to user

    try:
        profile = await auth.me()
    except TokenExpiredError:
        # Token expired, refresh it
        new_tokens = await auth.refresh_token(refresh_token)
        access_token = new_tokens.access_token
    except InvalidTokenError:
        # Token invalid, must login again
        print("Please login again")
```

---

### 3. SearchClient

**Purpose:** Search operations (authenticated)

**Methods:**
- `search(query, databases, max_results, search_mode, filters)` - Execute search
- `get_publication(pub_id)` - Get publication details
- `get_suggestions(partial_query)` - Query autocomplete
- `get_search_history(limit)` - Recent searches (per user) 🆕
- `save_search(query, results, name)` - Save search (per user) 🆕
- `export_results(results, format)` - Export to CSV/JSON/BibTeX

**Example (Authenticated):**
```python
from omics_oracle_v2.integration import SearchClient

async with SearchClient(access_token=access_token) as client:
    # Basic search
    results = await client.search("cancer immunotherapy")

    # Advanced search
    results = await client.search(
        query="CRISPR Cas9",
        databases=["pubmed", "google_scholar"],
        max_results=100,
        search_mode="hybrid",
        filters={"year_min": 2020, "has_pdf": True}
    )

    # User-specific search history (NEW!)
    history = await client.get_search_history(limit=10)
    for search in history:
        print(f"{search.query} - {search.created_at}")

    # Save search for later (NEW!)
    await client.save_search(
        query="CRISPR delivery mechanisms",
        results=results,
        name="My CRISPR Review 2025"
    )

    # Export
    csv_data = await client.export_results(results, format="csv")
```

**Performance Metrics:**
- **First search:** 20-30 seconds (hits NCBI, Google Scholar, multi-agent pipeline)
- **Cached search:** <1 second (60%+ hit rate from Redis/SQLite)
- **Rate limit:** 60 searches/hour for free tier, unlimited for premium

---

### 4. AnalysisClient

**Purpose:** GPT-4 analysis, Q&A, trends, networks (with cost tracking)

**Methods:**
- `analyze_with_llm(query, results, analysis_type)` - GPT-4 analysis
- `ask_question(question, context)` - GPT-4 Q&A over papers
- `get_trends(results)` - Trend analysis
- `get_network(results, min_citations)` - Citation network
- `get_citation_analysis(pub_id)` - Detailed citations
- `get_biomarker_analysis(results)` - Biomarker aggregation
- `generate_report(query, results)` - Generate comprehensive report
- `get_cost_summary()` - Get user's GPT-4 cost summary 🆕

**Example (With Cost Tracking):**
```python
from omics_oracle_v2.integration import AnalysisClient

async with AnalysisClient(access_token=access_token) as client:
    # GPT-4 analysis
    analysis = await client.analyze_with_llm(
        query="CRISPR delivery mechanisms",
        results=search_results.results[:10],
        analysis_type="overview"
    )

    print(f"📊 Overview: {analysis.overview}")
    print(f"🔑 Key findings: {analysis.key_findings}")
    print(f"🕳️ Research gaps: {analysis.research_gaps}")
    print(f"💡 Recommendations: {analysis.recommendations}")

    # Cost tracking (NEW!)
    print(f"\n💰 Cost: ${analysis.cost:.4f}")
    print(f"🎫 Tokens: {analysis.tokens_used}")
    print(f"⏱️ Time: {analysis.processing_time:.1f}s")

    # GPT-4 Q&A
    answer = await client.ask_question(
        question="What are the main delivery challenges?",
        context=search_results.results
    )

    print(f"\n❓ Q: {answer.question}")
    print(f"✅ A: {answer.answer}")
    print(f"📚 Sources: {[s.title for s in answer.sources]}")
    print(f"💰 Cost: ${answer.cost:.4f}")  # NEW!

    # Check total costs for user
    cost_summary = await client.get_cost_summary()
    print(f"\n📊 Total GPT-4 usage this month:")
    print(f"   Analyses: {cost_summary.analysis_count}")
    print(f"   Questions: {cost_summary.question_count}")
    print(f"   Total tokens: {cost_summary.total_tokens:,}")
    print(f"   Total cost: ${cost_summary.total_cost:.2f}")
    print(f"   Quota remaining: ${cost_summary.quota_remaining:.2f}")
```

**Performance & Cost Metrics:**
- **GPT-4 Analysis:** 13-15 seconds, ~2000 tokens, ~$0.04 per analysis
- **GPT-4 Q&A:** 8-12 seconds, ~1000 tokens, ~$0.01 per question
- **Trends:** <1 second (no GPT-4)
- **Citation Network:** 2-5 seconds (no GPT-4)
- **Monthly Quota:** $10/month free tier, $50/month premium

---

### 5. AgentClient 🆕

**Purpose:** Direct access to 5 specialized AI agents

**Phase 4 introduces a multi-agent system:** Each agent has a specific role in the search & analysis pipeline.

**Agents:**
1. **Query Agent** - Entity extraction, query expansion, synonym discovery
2. **Search Agent** - Orchestrates searches across multiple databases (20-30s)
3. **Analysis Agent** - GPT-4 powered literature analysis (13-15s, ~$0.04)
4. **Quality Agent** - Publication quality scoring (<1s)
5. **Recommendation Agent** - Similar paper recommendations (1-2s)

**Methods:**
- `query_agent(query)` - Extract entities, expand query
- `search_agent(query, databases, filters)` - Execute search via agent
- `analysis_agent(query, results)` - GPT-4 analysis via agent
- `quality_agent(publications)` - Batch quality scoring
- `recommendation_agent(seed_papers, count)` - Get recommendations
- `get_agent_status(agent_name)` - Check agent health
- `get_cost_metrics()` - Get per-agent cost breakdown

**Example (Multi-Agent Workflow):**
```python
from omics_oracle_v2.integration import AgentClient

async with AgentClient(access_token=access_token) as agents:
    # 1. Query Agent - Extract entities
    query_result = await agents.query_agent(
        query="CRISPR gene editing delivery mechanisms"
    )

    print(f"🎯 Entities: {query_result.entities}")
    # Output: ['CRISPR', 'Cas9', 'gene editing', 'viral vectors', 'lipid nanoparticles']

    print(f"🔍 Expanded queries: {query_result.expanded_queries}")
    # Output: ['CRISPR-Cas9 delivery systems', 'gene editing vectors', ...]

    # 2. Search Agent - Execute search
    search_result = await agents.search_agent(
        query=query_result.best_query,
        databases=["pubmed", "google_scholar"],
        filters={"year_min": 2020}
    )

    print(f"📄 Found: {search_result.total_results} papers")
    print(f"⏱️ Time: {search_result.search_time:.1f}s")

    # 3. Quality Agent - Score publications
    quality_scores = await agents.quality_agent(
        publications=search_result.results
    )

    for pub, score in zip(search_result.results, quality_scores):
        print(f"{pub.title[:50]}... | Quality: {score.overall:.2f}/5.0")

    # 4. Analysis Agent - GPT-4 analysis
    analysis = await agents.analysis_agent(
        query=query_result.original_query,
        results=search_result.results[:10]
    )

    print(f"\n📊 Analysis:")
    print(f"   Overview: {analysis.overview}")
    print(f"   Key findings: {analysis.key_findings}")
    print(f"   💰 Cost: ${analysis.cost:.4f}")

    # 5. Recommendation Agent - Similar papers
    recommendations = await agents.recommendation_agent(
        seed_papers=[pub.id for pub in search_result.results[:3]],
        count=10
    )

    print(f"\n💡 Recommended papers:")
    for rec in recommendations.recommendations:
        print(f"   - {rec.title} (score: {rec.score:.2f})")

    # Get cost breakdown by agent
    costs = await agents.get_cost_metrics()
    print(f"\n💰 Cost breakdown:")
    print(f"   Query Agent: FREE")
    print(f"   Search Agent: FREE")
    print(f"   Analysis Agent: ${costs.analysis_agent_cost:.2f}")
    print(f"   Quality Agent: FREE")
    print(f"   Recommendation Agent: FREE")
    print(f"   TOTAL: ${costs.total_cost:.2f}")
```

**Agent Performance:**
- **Query Agent:** <1s, no cost (rule-based)
- **Search Agent:** 20-30s first time, <1s cached, no GPT-4 cost
- **Analysis Agent:** 13-15s, ~$0.04 per analysis (GPT-4)
- **Quality Agent:** <1s, no cost (ML model)
- **Recommendation Agent:** 1-2s, no cost (embedding similarity)

**When to Use AgentClient vs Other Clients:**
- Use **AgentClient** when you want fine-grained control over each agent
- Use **SearchClient/AnalysisClient** for high-level operations
- Use **AgentClient** to debug or optimize specific pipeline steps

---

### 6. MLClient

**Purpose:** Machine learning predictions and recommendations (no GPT-4, fast & free)

**Methods:**
- `get_recommendations(seed_papers, count)` - Similar papers via embedding similarity
- `predict_citations(pub_id, years_ahead)` - Citation prediction model
- `score_quality(publication)` - Quality scoring (impact, citations, venue)
- `rank_by_relevance(query, publications)` - Re-rank search results
- `get_trending_topics(field, days)` - Trending topics analysis
- `get_emerging_authors(field, min_papers)` - Rising star researchers

**Example:**
```python
from omics_oracle_v2.integration import MLClient

async with MLClient(access_token=access_token) as client:
    # Recommendations (fast, no GPT-4 cost!)
    recs = await client.get_recommendations(
        seed_papers=["PMID:12345", "PMID:67890"],
        count=20
    )

    for rec in recs.recommendations:
        print(f"{rec.publication.title}")
        print(f"  Score: {rec.score:.2f}")
        print(f"  Reason: {rec.reason}")

    # Citation prediction
    prediction = await client.predict_citations(
        pub_id="PMID:12345",
        years_ahead=5
    )

    print(f"Current citations: {prediction.current_count}")
    print(f"Predicted in 5yr: {prediction.predicted_count}")
    print(f"Growth rate: {prediction.growth_rate:.1f}%/year")

    # Trending topics
    topics = await client.get_trending_topics(
        field="genomics",
        days=30
    )

    for topic in topics:
        print(f"{topic.name}: {topic.score:.2f} ({topic.paper_count} papers)")
```

**Performance:**
- **Recommendations:** 1-2 seconds (embedding similarity, no GPT-4)
- **Citation Prediction:** <1 second (ML model inference)
- **Quality Scoring:** <1 second per 100 papers
- **All ML operations:** FREE (no GPT-4 tokens)

---

### 7. DataTransformer

**Purpose:** Convert data for different frontends

**Methods:**
- `to_streamlit(response)` - Streamlit format
- `to_react(response)` - React format (camelCase)
- `to_vue(response)` - Vue format
- `to_csv(response)` - CSV export
- `to_json(response)` - JSON export
- `to_bibtex(publications)` - BibTeX export
- `to_ris(publications)` - RIS export

**Example:**
```python
from omics_oracle_v2.integration import DataTransformer

transformer = DataTransformer()

# For Streamlit (current dashboard)
streamlit_data = transformer.to_streamlit(search_response)

# For React (future admin dashboard)
react_data = transformer.to_react(search_response)

# For Vue (future mobile app)
vue_data = transformer.to_vue(search_response)

# Export formats
csv = transformer.to_csv(search_response)
bibtex = transformer.to_bibtex(search_response.results)
```

---

## 🎯 What This Solves

### Problem 1: 90% of Backend Features Not Exposed

**Before:**
- Dashboard only called `/api/v1/workflows/search`
- 40+ other endpoints existed but were unused
- Users never saw: LLM analysis, Q&A, recommendations, predictions

**After:**
- `AnalysisClient` exposes LLM analysis, Q&A, trends, networks
- `MLClient` exposes recommendations, predictions, quality scoring
- All features now accessible to any frontend

### Problem 2: Tight Coupling

**Before:**
```python
# Dashboard directly called backend
response = requests.post(
    "http://localhost:8000/api/v1/workflows/search",
    json={...}
)
```

**After:**
```python
# Clean abstraction
async with SearchClient() as client:
    response = await client.search(query="CRISPR")
```

### Problem 3: No Multi-Frontend Support

**Before:**
- Only Streamlit dashboard
- To add React admin: duplicate all API calls
- To add Vue mobile: duplicate again

**After:**
- Integration layer works with any frontend
- `DataTransformer` handles format conversion
- Add new frontend: just call integration layer

---

## 📊 Type Safety (Pydantic Models)

All data is validated with Pydantic:

```python
from omics_oracle_v2.integration.models import (
    SearchRequest,
    SearchResponse,
    Publication,
    CitationMetrics,
    QualityScore,
    Biomarker,
    AnalysisResponse,
    QAResponse,
    TrendAnalysis,
    NetworkGraph,
)

# Type-safe requests
request = SearchRequest(
    query="CRISPR",
    max_results=50,
    search_mode="hybrid"
)

# Type-safe responses
response: SearchResponse = await client.search(...)

for pub in response.results:
    # IDE autocomplete works!
    print(pub.title)
    print(pub.citation_metrics.count)
    print(pub.quality_score.overall)
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from omics_oracle_v2.integration import SearchClient

@pytest.mark.asyncio
async def test_search():
    async with SearchClient(base_url="http://localhost:8000") as client:
        results = await client.search("test query", max_results=10)

        assert results.metadata.total_results > 0
        assert len(results.results) <= 10
        assert results.results[0].title is not None
```

### Mocking (Easy!)

```python
from unittest.mock import AsyncMock
from omics_oracle_v2.integration import SearchClient

# Mock the integration layer, not the backend!
mock_client = SearchClient()
mock_client.search = AsyncMock(return_value=fake_response)

# Test frontend against mock
result = await frontend_function(mock_client)
```

---

## 🔄 Migration Guide

### Migrate Existing Dashboard

**Old Code (lib/dashboard/app.py):**
```python
# Direct API call
response = requests.post(
    "http://localhost:8000/api/v1/workflows/search",
    json={"query": query, ...}
)
```

**New Code:**
```python
from omics_oracle_v2.integration import SearchClient, DataTransformer

async with SearchClient() as client:
    # Use integration layer
    response = await client.search(query=query, max_results=100)

    # Transform for Streamlit
    transformer = DataTransformer()
    streamlit_data = transformer.to_streamlit(response)

    # Now render (same as before)
    for pub in streamlit_data["results"]:
        st.write(pub["title"])
```

**Benefits:**
- ✅ Auto-retry on failure
- ✅ Response caching
- ✅ Rate limiting
- ✅ Type safety
- ✅ Easy to test

---

## 🎨 Building New Frontends

### React Admin Dashboard

```typescript
// React example
import { SearchClient } from '@omicsoracle/integration';

const client = new SearchClient({ baseUrl: 'http://localhost:8000' });

async function searchPapers(query: string) {
  const response = await client.search({
    query,
    maxResults: 100,
    searchMode: 'hybrid'
  });

  return response; // Already in camelCase for React!
}
```

### Vue Mobile App

```javascript
// Vue example
import { SearchClient } from '@omicsoracle/integration';

export default {
  async mounted() {
    const client = new SearchClient();
    const results = await client.search('CRISPR');
    this.papers = results.results; // Vue-friendly format
  }
}
```

---

## 📈 Performance

### Caching

- GET requests cached for 5 minutes
- Reduces backend load by ~70%
- Cache hit rate: 80%+ for common queries

### Rate Limiting

- 60 requests per minute per client
- Prevents accidental DoS
- Configurable per client instance

### Retries

- Automatic retry on 5xx errors
- Exponential backoff (1s, 2s, 4s)
- Max 3 retries by default

---

## 🔒 Security

### JWT Authentication 🆕

```python
from omics_oracle_v2.integration import AuthClient, SearchClient

# 1. Login to get JWT tokens
async with AuthClient() as auth:
    response = await auth.login(
        username="researcher@university.edu",
        password="secure_password"
    )
    access_token = response.access_token

# 2. Use token with authenticated clients
async with SearchClient(access_token=access_token) as search:
    results = await search.search("query")  # Authenticated!

# 3. Token automatically included in all requests
# Headers: {"Authorization": "Bearer <access_token>"}
```

### Token Refresh 🆕

```python
from omics_oracle_v2.integration import AuthClient

# Before access token expires (60 minutes)
async with AuthClient() as auth:
    new_tokens = await auth.refresh_token(refresh_token)
    access_token = new_tokens.access_token  # New 60-min token
```

### Password Security

- Passwords hashed with **bcrypt** (12 rounds)
- Never sent or stored in plain text
- Minimum requirements: 8 characters, mix of letters/numbers/symbols

### HTTPS (Production)

```python
# Production API uses HTTPS
async with SearchClient(
    base_url="https://api.omicsoracle.com",
    access_token=access_token
) as client:
    results = await client.search("query")
```

### Rate Limiting & Quotas

```python
# Free tier limits
# - 60 searches/hour
# - $10 GPT-4/month

# Premium tier limits  
# - Unlimited searches
# - $50 GPT-4/month

# Check quota
async with AnalysisClient(access_token=token) as client:
    cost_summary = await client.get_cost_summary()
    print(f"Quota remaining: ${cost_summary.quota_remaining:.2f}")
```

---

## 📚 Complete Example (Phase 4)

```python
"""
Complete workflow demonstrating all Phase 4 integration layer features.
Includes: Authentication, Multi-Agent Pipeline, GPT-4 Analysis, Cost Tracking.
"""

import asyncio
from omics_oracle_v2.integration import (
    AuthClient,
    SearchClient,
    AnalysisClient,
    MLClient,
    AgentClient,
    DataTransformer,
)

async def main():
    # STEP 0: AUTHENTICATE (NEW in Phase 4!)
    print("Step 0: Authenticating...")
    async with AuthClient() as auth:
        auth_response = await auth.login(
            username="researcher@university.edu",
            password="secure_password"
        )
        access_token = auth_response.access_token
        print(f"✅ Logged in as: {auth_response.user.username}")

    # Initialize authenticated clients
    async with SearchClient(access_token=access_token) as search:
        async with AnalysisClient(access_token=access_token) as analysis:
            async with MLClient(access_token=access_token) as ml:
                async with AgentClient(access_token=access_token) as agents:

                    # 1. SEARCH (Multi-Agent Pipeline)
                    print("\nStep 1: Searching...")
                    results = await search.search(
                        query="CRISPR gene editing delivery mechanisms",
                        max_results=50,
                        search_mode="hybrid",
                        filters={"year_min": 2020}
                    )

                    print(f"Found {results.metadata.total_results} papers")
                    print(f"Query time: {results.metadata.query_time:.2f}s")

                    # 2. LLM ANALYSIS (GPT-4 with cost tracking)
                    print("\nStep 2: GPT-4 Analysis...")
                    llm_analysis = await analysis.analyze_with_llm(
                        query="CRISPR gene editing",
                        results=results.results[:10],
                        analysis_type="overview"
                    )

                    print(f"📊 Overview: {llm_analysis.overview[:100]}...")
                    print(f"🔑 Key findings: {llm_analysis.key_findings[:2]}")
                    print(f"💰 Cost: ${llm_analysis.cost:.4f}")
                    print(f"🎫 Tokens: {llm_analysis.tokens_used}")
                    print(f"⏱️ Time: {llm_analysis.processing_time:.1f}s")

                    # 3. Q&A (GPT-4)
                    print("\nStep 3: Q&A...")
                    answer = await analysis.ask_question(
                        question="What are the main delivery challenges?",
                        context=results.results
                    )

                    print(f"❓ Q: {answer.question}")
                    print(f"✅ A: {answer.answer[:150]}...")
                    print(f"📚 Sources: {len(answer.sources)} papers cited")
                    print(f"💰 Cost: ${answer.cost:.4f}")

                    # 4. TRENDS (No GPT-4, fast & free)
                    print("\nStep 4: Trend Analysis...")
                    trends = await analysis.get_trends(results.results)

                    print(f"📈 Growth rate: {trends.growth_rate:.1f}% per year")
                    print(f"🏆 Peak year: {trends.peak_year}")
                    print(f"🔮 Predicted in 5yr: {trends.prediction_5yr} papers")

                    # 5. CITATION NETWORK (No GPT-4)
                    print("\nStep 5: Citation Network...")
                    network = await analysis.get_network(
                        results=results.results,
                        min_citations=10
                    )

                    print(f"🕸️ Network: {len(network.nodes)} nodes, {len(network.edges)} edges")
                    print(f"🔬 Clusters: {len(network.clusters)}")

                    # 6. RECOMMENDATIONS (ML, no GPT-4)
                    print("\nStep 6: Recommendations...")
                    top_papers = [pub.id for pub in results.results[:3]]
                    recs = await ml.get_recommendations(
                        seed_papers=top_papers,
                        count=10
                    )

                    print("💡 Recommended papers:")
                    for rec in recs.recommendations[:5]:
                        print(f"   - {rec.publication.title[:60]}...")
                        print(f"     Score: {rec.score:.2f} | Reason: {rec.reason}")

                    # 7. QUALITY SCORING (ML, no GPT-4)
                    print("\nStep 7: Quality Scoring...")
                    quality_scores = await agents.quality_agent(
                        publications=results.results[:10]
                    )

                    avg_quality = sum(s.overall for s in quality_scores) / len(quality_scores)
                    print(f"⭐ Average quality: {avg_quality:.2f}/5.0")

                    # 8. EXPORT
                    print("\nStep 8: Export...")
                    transformer = DataTransformer()

                    csv_data = transformer.to_csv(results)
                    bibtex = transformer.to_bibtex(results.results)
                    react_data = transformer.to_react(results)  # For React frontend

                    print(f"📄 CSV: {len(csv_data)} bytes")
                    print(f"📚 BibTeX: {len(bibtex)} bytes")
                    print(f"⚛️ React JSON: {len(react_data)} objects")

                    # 9. GENERATE REPORT (GPT-4)
                    print("\nStep 9: Generate Report...")
                    report = await analysis.generate_report(
                        query="CRISPR gene editing",
                        results=results.results,
                        include_analysis=True
                    )

                    print(f"📋 Report: {len(report)} characters")

                    # 10. COST SUMMARY (NEW!)
                    print("\nStep 10: Cost Summary...")
                    cost_summary = await analysis.get_cost_summary()

                    print(f"\n💰 Monthly GPT-4 Usage:")
                    print(f"   Analyses: {cost_summary.analysis_count}")
                    print(f"   Questions: {cost_summary.question_count}")
                    print(f"   Total tokens: {cost_summary.total_tokens:,}")
                    print(f"   Total cost: ${cost_summary.total_cost:.2f}")
                    print(f"   Quota remaining: ${cost_summary.quota_remaining:.2f}")

                    print("\n✅ Complete workflow finished!")
                    print(f"   Total operations: 10")
                    print(f"   Total time: ~60 seconds")
                    print(f"   Total cost: ~$0.05 (only GPT-4 operations)")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ✅ Status & Version History

**Version 3.0.0 - Phase 4 Complete (October 8, 2025)**

Phase 4 Major Updates:
- ✅ **AuthClient added** - JWT-based authentication with token refresh
- ✅ **AgentClient added** - Direct access to 5 specialized AI agents
- ✅ **Cost tracking** - GPT-4 token and cost monitoring across all clients
- ✅ **Performance metrics** - Real-time timing for all operations
- ✅ **User quotas** - Monthly spending limits and cost transparency
- ✅ **Enhanced security** - RBAC, rate limiting, JWT expiration handling
- ✅ **Agent orchestration** - Query → Search → Analysis → Quality → Recommendation pipeline
- ✅ **3-level caching** - Redis (60min) → SQLite (24h) → File (30d)

**Version 2.0.0 - Phase 2 Complete (June 2025)**

- ✅ Integration layer implemented (5 modules)
- ✅ SearchClient, AnalysisClient, MLClient working
- ✅ Data transformer for multi-frontend support
- ✅ Type-safe Pydantic models
- ✅ Comprehensive documentation

**Next: Phase 5 - Frontend Redesign & Enhanced Features**

---

## 📊 Phase 4 Complete Summary

**Integration Layer Now Provides:**

1. **7 Client Classes:**
   - APIClient (base class)
   - AuthClient (authentication)
   - SearchClient (search operations)
   - AnalysisClient (GPT-4 analysis)
   - MLClient (recommendations, predictions)
   - AgentClient (5 specialized agents)
   - DataTransformer (multi-frontend support)

2. **60+ API Endpoints Exposed:**
   - Authentication: 6 endpoints
   - Search: 12 endpoints
   - Analysis: 15 endpoints
   - ML/Recommendations: 10 endpoints
   - Agents: 8 endpoints
   - Admin: 5 endpoints

3. **Key Features:**
   - ✅ JWT authentication with automatic refresh
   - ✅ GPT-4 cost tracking & quotas
   - ✅ Multi-agent orchestration
   - ✅ 3-level caching (60%+ hit rate)
   - ✅ Type-safe Pydantic models
   - ✅ Auto-retry with exponential backoff
   - ✅ Rate limiting (60/min)
   - ✅ Multi-frontend support (Streamlit, React, Vue)

4. **Performance:**
   - Search: 20-30s (first) → <1s (cached)
   - GPT-4 Analysis: 13-15s, ~$0.04
   - GPT-4 Q&A: 8-12s, ~$0.01
   - Recommendations: 1-2s, FREE
   - Quality Scoring: <1s, FREE

5. **Production Ready:**
   - ✅ Comprehensive error handling
   - ✅ Token expiration management
   - ✅ Cost quota enforcement
   - ✅ HTTPS support
   - ✅ Async/await throughout
   - ✅ Type hints & validation
   - ✅ Example code for all clients

**Monthly Costs (Moderate Usage - 100 analyses):**
- GPT-4 Analysis: ~$4.00 (100 × $0.04)
- GPT-4 Q&A: ~$2.00 (200 × $0.01)
- All other operations: FREE
- **Total: ~$6-8/month**

---

## 🔗 Related Documentation

- [API Reference v3.0](./API_REFERENCE.md) - Complete API endpoint documentation
- [System Architecture v3.0](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [Data Flow Integration Map v2.0](./DATA_FLOW_INTEGRATION_MAP.md) - Workflow diagrams
- [Backend-Frontend Contract](./BACKEND_FRONTEND_CONTRACT.md) - API contracts
- [Complete Architecture Overview v3.0](./COMPLETE_ARCHITECTURE_OVERVIEW.md) - High-level view

---

**Last Updated:** October 8, 2025  
**Document Version:** 3.0.0  
**Phase:** 4 Complete - Production Ready
