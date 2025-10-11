# LLM Citation Analysis Control Guide

## What's Happening? 🔍

The test is currently calling **GPT-4 via OpenAI API** to analyze citation relevance. This is part of the citation enrichment pipeline.

### Where LLM is Being Used

**File:** `omics_oracle_v2/lib/pipelines/publication_pipeline.py`

**Lines 978-1010:** LLM citation analysis is triggered in `_enrich_with_citations()`:

```python
if self.llm_citation_analyzer and citing_papers:
    logger.debug(f"Analyzing {len(citing_papers)} citations with LLM...")

    # Analyze in batches
    usage_analyses = self.llm_citation_analyzer.analyze_batch(
        contexts, batch_size=self.config.llm_config.batch_size
    )
```

**Purpose:**
- Analyzes whether citing papers actually **reused the dataset** or just cited it
- Extracts key findings, novel biomarkers, clinical relevance
- Determines usage type (data reuse, methodology, citation only)
- Provides confidence scores

### Why It's Running

**Root Cause:** `enable_citations=True` in the configuration

**Configuration Chain:**

1. **unified_search_pipeline.py (Line 512):**
   ```python
   pub_config = PublicationSearchConfig(
       enable_pubmed=True,
       enable_openalex=True,
       enable_scholar=False,
       enable_citations=True,  # ← THIS ENABLES LLM ANALYSIS
       deduplication=True,
   )
   ```

2. **publication_pipeline.py (Line 121-139):**
   ```python
   if config.enable_citations:
       # Initialize citation finder
       self.citation_finder = CitationFinder(...)

       # Initialize LLM-powered analysis
       self.llm_client = LLMClient(...)
       self.llm_citation_analyzer = LLMCitationAnalyzer(self.llm_client)
   ```

3. **Default Config (config.py Line 278):**
   ```python
   enable_citations: bool = True  # Default is TRUE
   ```

### LLM Configuration Details

**From config.py (Lines 171-208):**

```python
class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4-turbo-preview"
    batch_size: int = 5  # Papers per batch
    max_papers_to_analyze: int = 20  # Cost control
    max_cost_per_search: float = 5.0  # $5 limit
    enable_cost_preview: bool = True
```

**Current Test:**
- Processing **50 citing papers** in batches of 5
- Using GPT-4-turbo-preview
- Cost: ~$0.01-0.02 per paper
- **Total estimated cost:** $0.50 - $1.00 for this test

---

## Solutions to Control LLM Usage 🛠️

### Option 1: Disable LLM Analysis Completely (RECOMMENDED FOR TESTING)

**Quick Fix - Modify unified_search_pipeline.py:**

```python
# File: omics_oracle_v2/lib/pipelines/unified_search_pipeline.py
# Line 512

pub_config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_scholar=False,
    enable_citations=False,  # ← CHANGE TO FALSE
    deduplication=True,
)
```

**Impact:**
- ✅ No LLM calls
- ✅ No OpenAI costs
- ✅ Still gets citation counts from Semantic Scholar
- ✅ Still finds citing papers via OpenAlex
- ❌ No dataset reuse analysis
- ❌ No usage type classification

---

### Option 2: Add Feature Flag to UnifiedSearchConfig

**Better Solution - Add granular control:**

**Step 1: Modify UnifiedSearchConfig**

```python
# File: omics_oracle_v2/lib/pipelines/unified_search_pipeline.py
# Lines ~50-100

@dataclass
class UnifiedSearchConfig:
    enable_geo_search: bool = True
    enable_publication_search: bool = True
    enable_query_optimization: bool = True
    enable_caching: bool = True
    enable_deduplication: bool = True
    enable_sapbert: bool = False
    enable_ner: bool = True

    # NEW - Citation control
    enable_citation_discovery: bool = True  # Find citing papers
    enable_citation_llm_analysis: bool = False  # LLM analysis (costly)

    max_geo_results: int = 100
    max_publication_results: int = 100
```

**Step 2: Modify publication pipeline initialization:**

```python
# File: omics_oracle_v2/lib/pipelines/unified_search_pipeline.py
# Lines ~508-516

pub_config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_scholar=False,
    enable_citations=self.config.enable_citation_discovery,  # ← Use flag
    deduplication=True,
)
```

**Step 3: Add LLM control to PublicationSearchConfig:**

```python
# File: omics_oracle_v2/lib/publications/config.py
# Add new field to PublicationSearchConfig

enable_citation_llm_analysis: bool = False  # Disable by default
```

**Step 4: Modify publication_pipeline.py to respect the flag:**

```python
# File: omics_oracle_v2/lib/pipelines/publication_pipeline.py
# Line 121-139

if config.enable_citations:
    self.citation_finder = CitationFinder(...)

    # Only initialize LLM if explicitly enabled
    if config.enable_citation_llm_analysis:
        logger.info("Initializing LLM citation analyzer")
        self.llm_client = LLMClient(...)
        self.llm_citation_analyzer = LLMCitationAnalyzer(self.llm_client)
    else:
        logger.info("LLM citation analysis disabled")
        self.llm_citation_analyzer = None
```

---

### Option 3: Frontend Toggle (Full Control)

**Add to API endpoint parameters:**

```python
# In your API route (e.g., routes/search.py)

@router.post("/search")
async def search(
    query: str,
    enable_llm_analysis: bool = False,  # User-controlled
    max_results: int = 100,
):
    config = UnifiedSearchConfig(
        enable_citation_discovery=True,
        enable_citation_llm_analysis=enable_llm_analysis,  # User choice
    )
    pipeline = OmicsSearchPipeline(config)
    results = await pipeline.search(query, max_results)
```

**Frontend UI (React example):**

```jsx
<Checkbox
  label="Enable AI-powered citation analysis ($0.01-0.02 per paper)"
  checked={enableLLMAnalysis}
  onChange={(e) => setEnableLLMAnalysis(e.target.checked)}
  tooltip="Analyzes whether citing papers reused the dataset. Requires OpenAI API."
/>
```

---

### Option 4: Per-Dataset Control (Selective Analysis)

**Modify search agent to allow selective LLM analysis:**

```python
# File: omics_oracle_v2/agents/search_agent.py

async def analyze_citations_for_dataset(
    self,
    dataset_id: str,
    enable_llm: bool = False
) -> dict:
    """
    Analyze citations for a specific dataset.

    Args:
        dataset_id: GEO dataset ID (e.g., "GSE12345")
        enable_llm: Enable expensive LLM analysis

    Returns:
        Citation analysis results
    """
    # Get publication for dataset
    pub = await self.get_publication_for_dataset(dataset_id)

    # Find citing papers
    citing_papers = self.citation_finder.find_citing_papers(pub)

    # Optionally analyze with LLM
    if enable_llm and self.llm_citation_analyzer:
        analyses = self.llm_citation_analyzer.analyze_batch(citing_papers)
        return {"citing_papers": citing_papers, "llm_analyses": analyses}

    return {"citing_papers": citing_papers}
```

---

## Quick Action Items 🚀

### To Stop LLM Calls RIGHT NOW:

**Option A: Kill the test and restart with flag disabled**

```bash
# Kill current test
pkill -f test_searchagent_migration

# Disable citations in unified_search_pipeline.py (Line 512)
# Change: enable_citations=True → enable_citations=False

# Restart test
source venv/bin/activate
python test_searchagent_migration.py
```

### To Silence LLM Logs (Keep Running But Hide Output):

**Modify logging level:**

```python
# Add to test file at top
import logging
logging.getLogger("omics_oracle_v2.lib.publications.citations.llm_analyzer").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Hide OpenAI API calls
```

---

## Cost Analysis 💰

### Current Test Cost Estimate:

**What's happening:**
- 50 publications being enriched
- Each analyzed in batches of 5
- GPT-4-turbo-preview pricing:
  - Input: $10 / 1M tokens
  - Output: $30 / 1M tokens
- Average ~1,000 tokens per analysis
- **Estimated cost: $0.50 - $1.00 for this test**

### Production Considerations:

**If enabled for all searches:**
- 100 searches/day × 20 papers/search × $0.02/paper = **$40/day**
- Monthly: **$1,200/month**

**Recommendation:** Keep disabled by default, enable only when user explicitly requests dataset reuse analysis.

---

## Recommended Configuration 🎯

### For Development/Testing:

```python
UnifiedSearchConfig(
    enable_geo_search=True,
    enable_publication_search=True,
    enable_citation_discovery=True,  # Free - just finds citing papers
    enable_citation_llm_analysis=False,  # Expensive - disable
    enable_query_optimization=True,
    enable_caching=True,
    enable_deduplication=True,
)
```

### For Production (User-Controlled):

```python
# Default search (free)
default_config = UnifiedSearchConfig(
    enable_citation_llm_analysis=False
)

# Premium feature (user requests)
premium_config = UnifiedSearchConfig(
    enable_citation_llm_analysis=True,
    max_papers_to_analyze=20,  # Cost control
    max_cost_per_search=5.0,  # $5 limit
)
```

---

## Summary

**What's calling LLM:** Citation analysis in `publication_pipeline.py` via `LLMCitationAnalyzer`

**Why:** `enable_citations=True` in `unified_search_pipeline.py` (Line 512)

**How to disable:**
1. **Quick:** Set `enable_citations=False` in unified_search_pipeline.py
2. **Better:** Add granular flags to separate citation discovery from LLM analysis
3. **Best:** Make it user-controllable via frontend toggle

**Cost:** ~$0.01-0.02 per paper analyzed, can add up quickly

**Recommendation:** Disable for testing, make it an opt-in feature for production with clear cost warnings.
