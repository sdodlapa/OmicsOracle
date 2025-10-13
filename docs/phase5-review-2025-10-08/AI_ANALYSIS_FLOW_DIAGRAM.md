# AI Analysis Flow - Visual Diagram

**Version:** 2.0
**Last Updated:** October 8, 2025
**Phase:** 4 Complete - Production Ready
**Purpose:** Document the complete AI analysis workflow with authentication, multi-agent system, and cost tracking

---

## 📋 Overview

This document shows the **end-to-end flow** of AI-powered dataset analysis in OmicsOracle, including:
- 🔐 **Authentication** (JWT tokens) 🆕
- 🤖 **Multi-Agent Pipeline** (Query → Search → Analysis → Quality → Recommendation) 🆕
- 💰 **Cost Tracking** (GPT-4 token usage and quotas) 🆕
- ⚡ **Performance Metrics** (13-15 seconds typical)
- 📊 **Response Formatting** (Markdown rendering)

---

## 🔐 Phase 4: Authentication Flow (NEW)

Before the analysis can run, users must authenticate:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION CHECK (Phase 4)                         │
│                                                                           │
│  Frontend checks for valid JWT token:                                    │
│                                                                           │
│  const access_token = localStorage.getItem('access_token');             │
│  const expires_at = localStorage.getItem('token_expires_at');           │
│                                                                           │
│  if (!access_token || Date.now() > expires_at) {                        │
│    // Token missing or expired, redirect to login                       │
│    window.location.href = '/login';                                     │
│    return;                                                               │
│  }                                                                        │
│                                                                           │
│  // Token valid, proceed with analysis                                   │
│  fetch('/api/agents/analyze', {                                          │
│    method: 'POST',                                                        │
│    headers: {                                                             │
│      'Authorization': `Bearer ${access_token}`,  // JWT token here!      │
│      'Content-Type': 'application/json'                                  │
│    },                                                                     │
│    body: JSON.stringify(requestData)                                     │
│  });                                                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

**Backend validates token:**
```python
# In omics_oracle_v2/api/routes/agents.py
from omics_oracle_v2.api.middleware.auth import require_auth

@router.post("/analyze")
@require_auth  # Validates JWT token, extracts user
async def analyze_datasets(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user)  # User from JWT
):
    # Check user's quota before expensive GPT-4 call
    if current_user.quota_remaining < 0.04:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient quota. ${current_user.quota_remaining:.2f} remaining, need $0.04"
        )

    # Proceed with analysis...
```

---

## 🤖 Phase 4: Multi-Agent System (NEW)

The analysis now flows through **5 specialized AI agents**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      MULTI-AGENT PIPELINE (Phase 4)                       │
│                                                                           │
│  1. QUERY AGENT (~1s, FREE)                                              │
│     ├─ Extract entities from user query                                  │
│     ├─ Expand synonyms and related terms                                 │
│     └─ Generate optimized search queries                                 │
│                                                                           │
│  2. SEARCH AGENT (20-30s first, <1s cached, FREE)                        │
│     ├─ Execute searches across databases                                 │
│     ├─ Deduplicate results                                               │
│     └─ Rank by relevance                                                 │
│                                                                           │
│  3. ANALYSIS AGENT (13-15s, ~$0.04 GPT-4) ⭐ THIS DIAGRAM                │
│     ├─ Load GPT-4 model                                                  │
│     ├─ Construct analysis prompt                                         │
│     ├─ Generate overview, insights, recommendations                      │
│     ├─ Track token usage and cost                                        │
│     └─ Update user's quota                                               │
│                                                                           │
│  4. QUALITY AGENT (<1s, FREE)                                            │
│     ├─ Score publication quality (0-5.0)                                 │
│     ├─ Assess citation metrics                                           │
│     └─ Flag low-quality sources                                          │
│                                                                           │
│  5. RECOMMENDATION AGENT (1-2s, FREE)                                    │
│     ├─ Find similar papers via embedding similarity                      │
│     ├─ Suggest related searches                                          │
│     └─ Identify trending topics                                          │
│                                                                           │
│  Total Pipeline: ~35-50 seconds (first run), ~15 seconds (cached)        │
│  Total Cost: ~$0.04 (only Analysis Agent uses GPT-4)                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**This document focuses on Agent #3: Analysis Agent** (the GPT-4 powered component)

---

## Complete Request/Response Cycle (Agent #3: Analysis Agent)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                                 │
│  User searches: "joint DNA methylation and HiC profiling"                │
│  Clicks: 🤖 Analyze with AI                                              │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (JavaScript)                               │
│  File: semantic_search.html                                              │
│  Function: analyzeWithAI()                                               │
│                                                                           │
│  const requestData = {                                                    │
│    datasets: [                                                            │
│      {                                                                    │
│        geo_id: "GSE281238",                                              │
│        title: "Generalization of the sci-L3 method...",                  │
│        summary: "Single-cell combinatorial indexing...",                 │
│        relevance_score: 0.10,                                            │
│        organism: "N/A",                                                   │
│        sample_count: 7                                                    │
│      },                                                                   │
│      {                                                                    │
│        geo_id: "GSE189158",                                              │
│        title: "NOMe-HiC: joint profiling...",                            │
│        summary: "Cis-regulatory elements coordinate...",                 │
│        relevance_score: 0.05,                                            │
│        organism: "N/A",                                                   │
│        sample_count: 12                                                   │
│      }                                                                    │
│    ],                                                                     │
│    query: "joint DNA methylation and HiC profiling",                     │
│    max_datasets: 5                                                        │
│  };                                                                       │
│                                                                           │
│  fetch('/api/agents/analyze', {                                          │
│    method: 'POST',                                                        │
│    headers: {                                                             │
│      'Authorization': `Bearer ${access_token}`,  // JWT token (Phase 4)  │
│      'Content-Type': 'application/json'                                  │
│    },                                                                     │
│    body: JSON.stringify(requestData)                                     │
│  });                                                                      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTP POST
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     BACKEND API ENDPOINT                                  │
│  File: omics_oracle_v2/api/routes/agents.py                              │
│  Function: analyze_datasets()                                            │
│  Auth: Required (JWT token validation) 🆕                                │
│                                                                           │
│  Step 1: Validate JWT token 🆕                                           │
│    ✓ Extract and verify Bearer token                                     │
│    ✓ Decode JWT (60-minute expiry)                                       │
│    ✓ Get current_user from token                                         │
│    ✗ Reject if token invalid/expired                                     │
│                                                                           │
│  Step 2: Check user quota 🆕                                             │
│    current_quota = current_user.quota_remaining                          │
│    required_cost = 0.04  # GPT-4 analysis cost                           │
│    if current_quota < required_cost:                                     │
│      raise HTTPException(402, "Insufficient quota")                      │
│                                                                           │
│  Step 3: Validate request                                                │
│    ✓ Check datasets array                                                │
│    ✓ Check query string                                                  │
│    ✓ Limit to max_datasets (5)                                           │
│                                                                           │
│  Step 4: Check configuration                                             │
│    if not settings.ai.openai_api_key:                                    │
│      raise HTTPException(503, "OpenAI API key not configured")           │
│                                                                           │
│  Step 5: Initialize AI client                                            │
│    ai_client = SummarizationClient(settings=settings)                    │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        PROMPT CONSTRUCTION                                │
│                                                                           │
│  For each dataset (i=1 to 2):                                            │
│    Build summary string:                                                 │
│                                                                           │
│    "1. **GSE281238** (Relevance: 10%)"                                   │
│    "   Title: Generalization of the sci-L3 method..."                    │
│    "   Organism: N/A, Samples: 7"                                        │
│    "   Summary: Single-cell combinatorial indexing..."                   │
│    ""                                                                     │
│    "2. **GSE189158** (Relevance: 5%)"                                    │
│    "   Title: NOMe-HiC: joint profiling..."                              │
│    "   Organism: N/A, Samples: 12"                                       │
│    "   Summary: Cis-regulatory elements coordinate..."                   │
│                                                                           │
│  Combine into full prompt:                                               │
│                                                                           │
│    analysis_prompt = f"""                                                │
│    User searched for: "joint DNA methylation and HiC profiling"          │
│                                                                           │
│    Found 2 relevant datasets:                                            │
│    {dataset_summaries}                                                   │
│                                                                           │
│    Analyze these datasets and provide:                                   │
│    1. **Overview**: Which datasets are most relevant and why?            │
│    2. **Comparison**: How do they differ in methodology?                 │
│    3. **Key Insights**: Main scientific findings?                        │
│    4. **Recommendations**: Which for basic/advanced/method dev?          │
│                                                                           │
│    Write for a researcher. Be specific, cite GSE numbers.                │
│    """                                                                    │
│                                                                           │
│    system_message = "You are an expert bioinformatics advisor..."        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         AI CLIENT                                         │
│  File: omics_oracle_v2/lib/ai/client.py                                 │
│  Class: SummarizationClient                                              │
│  Method: _call_llm()                                                     │
│                                                                           │
│  openai_client.chat.completions.create(                                  │
│    model="gpt-4-turbo-preview",                                          │
│    messages=[                                                             │
│      {                                                                    │
│        "role": "system",                                                  │
│        "content": "You are an expert bioinformatics advisor..."          │
│      },                                                                   │
│      {                                                                    │
│        "role": "user",                                                    │
│        "content": [THE FULL PROMPT ABOVE]                                │
│      }                                                                    │
│    ],                                                                     │
│    max_tokens=800,                                                        │
│    temperature=0.7                                                        │
│  )                                                                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ API Call to OpenAI
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         OPENAI API                                        │
│  Service: https://api.openai.com/v1/chat/completions                    │
│                                                                           │
│  Processing Time: 15-30 seconds                                          │
│                                                                           │
│  GPT-4's Internal Reasoning (simplified):                                │
│  1. Parse user query: "joint DNA methylation and HiC profiling"          │
│  2. Analyze GSE281238:                                                   │
│     - Focus: sci-L3 method (amplification technique)                     │
│     - Mentions: genome conformation, RNA, chromatin                      │
│     - NOT specific to methylation + Hi-C combo                           │
│  3. Analyze GSE189158:                                                   │
│     - Focus: NOMe-HiC (specific method for query topic)                  │
│     - Explicitly mentions: DNA methylation + 3D genome                   │
│     - DIRECTLY addresses user's query                                    │
│  4. Compare methodologies                                                │
│  5. Extract key scientific insights                                      │
│  6. Generate recommendations for different use cases                     │
│  7. Format as markdown with headers                                      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ Returns completion
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      GPT-4 RESPONSE                                       │
│                                                                           │
│  {                                                                        │
│    "choices": [{                                                          │
│      "message": {                                                         │
│        "content": "### Overview\n\nBased on your query for \"joint DNA   │
│          methylation and HiC profiling,\" the most relevant dataset is   │
│          **GSE189158**. This dataset directly addresses the simultaneous │
│          profiling of DNA methylation, chromatin accessibility, and 3D   │
│          genome organization...\n\n### Comparison\n\n**GSE281238**      │
│          employs the sci-L3 method...\n\n**GSE189158**, on the other     │
│          hand, introduces NOMe-HiC...\n\n### Key Insights\n\n-          │
│          **GSE281238** highlights the versatility...\n- **GSE189158**    │
│          provides critical insights...\n\n### Recommendations\n\n**For   │
│          Basic Understanding:**\n**GSE189158** is recommended..."        │
│      }                                                                    │
│    }],                                                                    │
│    "usage": {                                                             │
│      "prompt_tokens": 450,                                               │
│      "completion_tokens": 650,                                           │
│      "total_tokens": 1100                                                │
│    }                                                                      │
│  }                                                                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    BACKEND RESPONSE PROCESSING                            │
│  File: omics_oracle_v2/api/routes/agents.py                              │
│                                                                           │
│  analysis = ai_client._call_llm(...)  # Returns the markdown text        │
│  tokens_used = response.usage.total_tokens  # 1100 tokens 🆕             │
│  cost_usd = calculate_cost(tokens_used)  # ~$0.04 🆕                     │
│                                                                           │
│  # Update user's quota 🆕                                                │
│  current_user.quota_remaining -= cost_usd                                │
│  current_user.total_cost_this_month += cost_usd                          │
│  db.session.commit()                                                     │
│                                                                           │
│  # Simple parsing (optional, for structured data)                        │
│  insights = []                                                            │
│  recommendations = []                                                     │
│  # Extract from markdown headings and lists...                           │
│                                                                           │
│  return AIAnalysisResponse(                                              │
│    success=True,                                                          │
│    execution_time_ms=14864,                                              │
│    timestamp=datetime.now(),                                             │
│    query="joint DNA methylation and HiC profiling",                      │
│    analysis="### Overview\n\nBased on your query...",                   │
│    insights=[...],  # Parsed                                             │
│    recommendations=[...],  # Parsed                                      │
│    model_used="gpt-4-turbo-preview",                                     │
│    cost_info={  # NEW! Phase 4 🆕                                        │
│      "tokens_used": 1100,                                                │
│      "cost_usd": 0.04,                                                   │
│      "quota_remaining": current_user.quota_remaining                     │
│    }                                                                      │
│  )                                                                        │
│  )                                                                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTP Response
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND RECEIVES RESPONSE                             │
│  File: semantic_search.html                                              │
│  Function: analyzeWithAI() → then() handler                              │
│                                                                           │
│  const data = await response.json();                                     │
│  // data = {                                                              │
│  //   success: true,                                                      │
│  //   analysis: "### Overview\n\nBased on your query...",                │
│  //   execution_time_ms: 14864,                                          │
│  //   model_used: "gpt-4-turbo-preview"                                  │
│  // }                                                                     │
│                                                                           │
│  displayAIAnalysis(data);                                                │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      MARKDOWN PARSING & RENDERING                         │
│  File: semantic_search.html                                              │
│  Function: displayAIAnalysis(data)                                       │
│                                                                           │
│  Step 1: Configure marked.js                                             │
│    marked.setOptions({                                                   │
│      breaks: true,        // Line breaks → <br>                          │
│      gfm: true,           // GitHub Flavored Markdown                    │
│      headerIds: false,    // Don't add IDs to headers                    │
│      mangle: false        // Don't escape email addresses                │
│    });                                                                    │
│                                                                           │
│  Step 2: Parse markdown to HTML                                          │
│    const analysisHtml = marked.parse(data.analysis);                     │
│                                                                           │
│    Input (markdown):                                                     │
│      "### Overview\n\n**GSE189158** is most relevant..."                │
│                                                                           │
│    Output (HTML):                                                        │
│      "<h3>Overview</h3>                                                  │
│       <p><strong>GSE189158</strong> is most relevant...</p>"             │
│                                                                           │
│  Step 3: Inject into DOM                                                 │
│    aiResults.innerHTML = `                                               │
│      <div class="ai-section">                                            │
│        <div class="ai-section-content">${analysisHtml}</div>             │
│      </div>                                                               │
│      <div style="text-align: center;">                                   │
│        <p>Powered by ${data.model_used} |                                │
│           Analysis completed in ${Math.round(data.execution_time_ms)}ms  │
│        </p>                                                               │
│      </div>                                                               │
│    `;                                                                     │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        CSS STYLING APPLIED                                │
│  File: semantic_search.html (styles section)                             │
│                                                                           │
│  .ai-analysis-panel {                                                    │
│    background: linear-gradient(135deg, #667eea, #764ba2);  /* Purple */  │
│    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);                     │
│  }                                                                        │
│                                                                           │
│  .ai-section-content h3 {                                                │
│    color: white;                                                          │
│    font-size: 1.3em;                                                     │
│    border-bottom: 2px solid rgba(255, 255, 255, 0.3);                   │
│  }                                                                        │
│                                                                           │
│  .ai-section-content strong {                                            │
│    color: white;                                                          │
│    font-weight: 600;  /* Makes **GSE189158** bold */                    │
│  }                                                                        │
│                                                                           │
│  .ai-section-content p {                                                 │
│    margin-bottom: 15px;                                                   │
│    color: rgba(255, 255, 255, 0.95);                                     │
│  }                                                                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      FINAL RENDERED OUTPUT                                │
│                                                                           │
│  ╔════════════════════════════════════════════════════════════════╗      │
│  ║  🤖 AI Analysis                                            ✕   ║      │
│  ╠════════════════════════════════════════════════════════════════╣      │
│  ║                                                                ║      │
│  ║  Overview                                                      ║      │
│  ║  ─────────────────────────────────────────────────────────    ║      │
│  ║  Based on your query for "joint DNA methylation and HiC       ║      │
│  ║  profiling," the most relevant dataset is GSE189158. This     ║      │
│  ║  dataset directly addresses the simultaneous profiling of     ║      │
│  ║  DNA methylation, chromatin accessibility, and 3D genome      ║      │
│  ║  organization...                                              ║      │
│  ║                                                                ║      │
│  ║  Comparison                                                    ║      │
│  ║  ─────────────────────────────────────────────────────────    ║      │
│  ║  GSE281238 employs the sci-L3 method, which is an             ║      │
│  ║  advancement in single-cell combinatorial indexing...         ║      │
│  ║                                                                ║      │
│  ║  GSE189158, on the other hand, introduces NOMe-HiC, a novel   ║      │
│  ║  methodology specifically designed for the concurrent...      ║      │
│  ║                                                                ║      │
│  ║  Key Insights                                                  ║      │
│  ║  ─────────────────────────────────────────────────────────    ║      │
│  ║  • GSE281238 highlights the versatility and efficiency...     ║      │
│  ║  • GSE189158 provides critical insights into the interplay... ║      │
│  ║                                                                ║      │
│  ║  Recommendations                                               ║      │
│  ║  ─────────────────────────────────────────────────────────    ║      │
│  ║  For Basic Understanding of the Topic:                        ║      │
│  ║  GSE189158 is recommended. It offers a direct look at...      ║      │
│  ║                                                                ║      │
│  ║  For Advanced Analysis:                                        ║      │
│  ║  GSE189158 would again be the go-to dataset...                ║      │
│  ║                                                                ║      │
│  ║  ──────────────────────────────────────────────────────────   ║      │
│  ║  Powered by gpt-4-turbo-preview | Analysis completed in 14864ms║      │
│  ╚════════════════════════════════════════════════════════════════╝      │
│                                                                           │
│  Beautiful purple gradient background with glassmorphism effect!         │
└──────────────────────────────────────────────────────────────────────────┘
```

## Key Takeaways

1. **User Query** drives the entire analysis
2. **Dataset metadata** provides scientific context to AI
3. **Structured prompt** ensures consistent, actionable responses
4. **GPT-4** understands biology and can disagree with search scores
5. **Markdown parsing** creates beautiful, readable output
6. **Total time:** ~15-30 seconds from click to display

## Cost Breakdown (Phase 4 Pricing)

**GPT-4 Turbo Pricing (October 2025):**
- Input: $0.01 per 1K tokens
- Output: $0.03 per 1K tokens

**Typical Analysis:**
```
Prompt tokens: ~450 tokens
  - System message: ~25 tokens
  - User query: ~10 tokens
  - Dataset metadata: ~400 tokens (2 datasets × 200)
  - Instructions: ~15 tokens

Completion tokens: ~650 tokens
  - Overview: ~150 tokens
  - Comparison: ~200 tokens
  - Key Insights: ~150 tokens
  - Recommendations: ~150 tokens

Total: ~1100 tokens

Cost Calculation:
  Input cost:  450 × $0.01 / 1000 = $0.0045
  Output cost: 650 × $0.03 / 1000 = $0.0195
  TOTAL:       $0.024 ≈ $0.04 (rounded for user display)
```

**Monthly Quotas (Phase 4):**
- **Free Tier:** $10/month (~250 analyses)
- **Premium Tier:** $50/month (~1,250 analyses)
- **Enterprise:** Custom pricing

**Cost Tracking:**
- Every analysis updates `user.quota_remaining`
- Users can check remaining quota via `/api/v1/analysis/cost-summary`
- Frontend warns when quota < $1.00
- Analysis blocked when quota ≤ $0.00

---

## Optimization Opportunities

1. **Reduce prompt size:**
   - Shorten summaries to 200 chars (saves ~100 tokens)
   - Use abbreviations (e.g., "GSE" instead of "GEO Series")

2. **Faster model:**
   - Use GPT-3.5-turbo: 3-8 seconds, $0.002
   - Trade quality for speed/cost

3. **Caching:**
   - Cache analyses for common queries
   - Save 100% cost on repeat searches
   - Phase 4 implements 3-level caching (Redis → SQLite → File)

4. **Batch processing:**
   - Analyze multiple searches together
   - Amortize API overhead

5. **User quotas** (Phase 4): 🆕
   - Prevent runaway costs with monthly limits
   - Encourage efficient query patterns
   - Upsell premium tier for heavy users

---

## Phase 4 Enhancements Summary

**What's New:**

1. **🔐 Authentication Required**
   - All analysis requests must include JWT token
   - Token validation before expensive GPT-4 call
   - User identification for cost tracking

2. **💰 Cost Tracking & Quotas**
   - Real-time quota checking
   - Per-analysis cost calculation
   - Monthly spending limits ($10 free, $50 premium)
   - Cost transparency in API responses

3. **🤖 Multi-Agent System**
   - Analysis Agent is Agent #3 of 5
   - Orchestrated by Search Agent (Agent #2)
   - Quality scoring by Quality Agent (Agent #4)
   - Recommendations by Recommendation Agent (Agent #5)

4. **⚡ Performance Metrics**
   - 13-15 seconds typical analysis time
   - <1 second for cached results
   - ~$0.04 per analysis (GPT-4 cost)

5. **📊 Enhanced Response**
   - Includes `cost_info` object
   - Shows tokens used and cost
   - Reports remaining quota
   - Enables frontend cost warnings

**Breaking Changes from v1.0:**
- ❌ Unauthenticated requests now rejected (401)
- ❌ No more unlimited free analyses
- ✅ All users get $10 free quota to start
- ✅ Premium users get $50/month quota

**Migration from v1.0:**
```javascript
// OLD (v1.0 - no auth)
fetch('/api/agents/analyze', {
  method: 'POST',
  body: JSON.stringify(data)
});

// NEW (v2.0 - Phase 4)
fetch('/api/agents/analyze', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,  // Required!
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
}).then(res => {
  const { cost_info } = res;
  console.log(`Analysis cost: $${cost_info.cost_usd}`);
  console.log(`Quota remaining: $${cost_info.quota_remaining}`);
});
```

---

**Document Version:** 2.0
**Last Updated:** October 8, 2025
**Phase:** 4 Complete - Production Ready with Authentication & Cost Management
