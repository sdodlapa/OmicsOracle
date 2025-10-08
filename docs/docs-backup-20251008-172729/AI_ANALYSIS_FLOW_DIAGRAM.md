# AI Analysis Flow - Visual Diagram

## Complete Request/Response Cycle

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
│    headers: { 'Content-Type': 'application/json' },                      │
│    body: JSON.stringify(requestData)                                     │
│  });                                                                      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTP POST
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     BACKEND API ENDPOINT                                  │
│  File: omics_oracle_v2/api/routes/agents.py                              │
│  Function: analyze_datasets()                                            │
│                                                                           │
│  Step 1: Validate request                                                │
│    ✓ Check datasets array                                                │
│    ✓ Check query string                                                  │
│    ✓ Limit to max_datasets (5)                                           │
│                                                                           │
│  Step 2: Check configuration                                             │
│    if not settings.ai.openai_api_key:                                    │
│      raise HTTPException(503, "OpenAI API key not configured")           │
│                                                                           │
│  Step 3: Initialize AI client                                            │
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
│    model_used="gpt-4-turbo-preview"                                      │
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

## Cost Breakdown

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

Cost with GPT-4-turbo: $0.01 per 1K input + $0.03 per 1K output
  = (450 × $0.01 / 1000) + (650 × $0.03 / 1000)
  = $0.0045 + $0.0195
  = $0.024 per analysis
  ≈ $0.03 rounded
```

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

4. **Batch processing:**
   - Analyze multiple searches together
   - Amortize API overhead
