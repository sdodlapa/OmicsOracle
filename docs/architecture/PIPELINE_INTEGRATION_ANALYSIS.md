# Pipeline Integration Analysis & Implementation Plan

**Date:** October 12, 2025
**Purpose:** Trace current pipeline flow and identify integration points for automatic PDF download → parse → normalize → AI analysis

---

## Current System Architecture

### Frontend Flow (HTML Dashboard)

**File:** `omics_oracle_v2/api/static/dashboard.html`

```
User Input: "breast cancer RNA-seq"
    ↓
Click [Search] button
    ↓
JavaScript: executeWorkflow()
    ↓
POST /api/v1/workflows/dev/execute
    {
        "workflow_type": "simple_search" | "full_analysis",
        "query": "breast cancer RNA-seq"
    }
```

**Key Code (dashboard.html, line 513):**
```javascript
const response = await fetch('/api/v1/workflows/dev/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        workflow_type: selectedWorkflowType,
        query: query
    })
});
```

### Backend Flow (API Routes → Orchestrator → Agents)

**File:** `omics_oracle_v2/api/routes/workflows_dev.py`

```
POST /api/v1/workflows/dev/execute
    ↓
execute_workflow(request: WorkflowRequest)
    ↓
orchestrator.execute(orchestrator_input)
    ↓
[Workflow Execution Based on Type]
```

**Current Workflow Types:**
1. **simple_search**: Query Agent → Search Agent → Report Agent
2. **full_analysis**: Query Agent → Search Agent → Data Agent → Report Agent
3. **quick_report**: Search Agent → Report Agent
4. **data_validation**: Data Agent → Report Agent

### Agent Flow (Orchestrator → Agents)

**File:** `omics_oracle_v2/agents/orchestrator.py`

**Simple Search Workflow:**
```
1. QueryAgent (query preprocessing)
   ↓ Outputs: optimized_query, extracted_entities

2. SearchAgent (GEO search)
   ↓ Outputs: datasets (GEO metadata)

3. ReportAgent (generate summary)
   ↓ Outputs: GPT-4 analysis report
```

### SearchAgent Details

**File:** `omics_oracle_v2/agents/search_agent.py`

**Current Implementation (Line 69-82):**
```python
self._use_unified_pipeline = True  # ✅ Using UnifiedSearchPipeline
self._unified_pipeline_config = UnifiedSearchConfig(
    enable_geo_search=True,
    enable_publication_search=enable_publications,
    enable_query_optimization=enable_query_preprocessing,  # NER + SapBERT
    enable_caching=True,
    enable_sapbert=enable_semantic,
    enable_ner=enable_query_preprocessing,
    max_geo_results=100,
)
```

**Search Execution:**
```python
def _process_unified(self, input_data, context):
    pipeline = UnifiedSearchPipeline(config=self._unified_pipeline_config)
    result = pipeline.search(
        query=input_data.original_query,
        search_terms=input_data.search_terms,
        max_results=input_data.max_results
    )
    return SearchOutput(datasets=result.datasets, ...)
```

**What SearchAgent Currently Returns:**
```python
SearchOutput(
    datasets=[
        Dataset(
            geo_id="GSE306759",
            title="Effect of palmitate on breast cancer cells...",
            summary="...",
            organism="Homo sapiens",
            platform="GPL34281",
            samples=8,
            pubmed_ids=["12345678"],  # ✅ Has PMIDs!
            relevance_score=0.95
        ),
        ...
    ]
)
```

---

## Gap Analysis: What's Missing

### Current State ❌

**What happens after SearchAgent returns results:**
```
SearchAgent returns Dataset objects with PMIDs
    ↓
ReportAgent receives datasets
    ↓
ReportAgent calls GPT-4 with only GEO metadata
    ✗ NO PDF download
    ✗ NO fulltext parsing
    ✗ NO content normalization
    ✗ GPT-4 only sees: title, summary, organism, samples
```

### Desired State ✅

**What should happen:**
```
SearchAgent returns Dataset objects with PMIDs
    ↓
NEW STEP: Auto-download PDFs for each PMID
    ↓
NEW STEP: Parse PDFs to fulltext
    ↓
NEW STEP: Normalize content format
    ↓
ReportAgent receives datasets + fulltext
    ↓
ReportAgent calls GPT-4 with GEO metadata + fulltext
    ✓ GPT-4 analyzes methods, results, discussion
    ✓ Rich insights based on actual paper content
```

---

## Integration Points (Where to Add Code)

### Integration Point 1: SearchAgent Output Enhancement

**File:** `omics_oracle_v2/agents/search_agent.py`
**Location:** After `_process_unified()` returns results
**Action:** Add PDF download + parsing step

**Current Code (Line 150-160):**
```python
def _process_unified(self, input_data, context):
    pipeline = UnifiedSearchPipeline(config=self._unified_pipeline_config)
    result = pipeline.search(...)

    return SearchOutput(
        datasets=result.datasets,
        total_results=result.total_results,
        # ...
    )
```

**Enhanced Code (NEW):**
```python
def _process_unified(self, input_data, context):
    pipeline = UnifiedSearchPipeline(config=self._unified_pipeline_config)
    result = pipeline.search(...)

    # NEW: Auto-download and parse PDFs for each dataset
    enriched_datasets = await self._enrich_with_fulltext(result.datasets)

    return SearchOutput(
        datasets=enriched_datasets,  # Now includes fulltext!
        total_results=result.total_results,
        # ...
    )

async def _enrich_with_fulltext(self, datasets: List[Dataset]) -> List[Dataset]:
    """
    Download and parse PDFs for each dataset's linked publications.

    For each dataset:
    1. Get PMIDs from dataset.pubmed_ids
    2. Download PDFs using GEOCitationPipeline
    3. Parse PDFs to fulltext
    4. Normalize content format
    5. Attach fulltext to dataset
    """
    from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline

    geo_pipeline = GEOCitationPipeline()
    enriched = []

    for dataset in datasets:
        if dataset.pubmed_ids:
            # Download and parse PDFs
            citations = await geo_pipeline.discover_and_download(
                geo_id=dataset.geo_id,
                pmids=dataset.pubmed_ids
            )

            # Get normalized fulltext
            fulltext_data = []
            for citation in citations:
                if citation.pdf_path:
                    normalized = self._get_normalized_content(citation.pdf_path)
                    fulltext_data.append(normalized)

            # Attach to dataset
            dataset.fulltext = fulltext_data  # NEW field!

        enriched.append(dataset)

    return enriched
```

### Integration Point 2: Dataset Model Enhancement

**File:** `omics_oracle_v2/agents/models/search.py`
**Location:** Dataset class definition
**Action:** Add fulltext field

**Current Model:**
```python
class Dataset(BaseModel):
    geo_id: str
    title: str
    summary: str
    organism: str
    platform: str
    samples: int
    pubmed_ids: List[str] = []
    relevance_score: float = 0.0
```

**Enhanced Model (NEW):**
```python
from typing import List, Optional, Dict, Any

class FulltextData(BaseModel):
    """Parsed and normalized fulltext content."""
    pmid: str
    title: str
    abstract: str
    methods: str
    results: str
    discussion: str
    figures: List[str] = []
    tables: List[str] = []
    raw_text: str
    format: str  # "jats", "pdf", "latex"

class Dataset(BaseModel):
    geo_id: str
    title: str
    summary: str
    organism: str
    platform: str
    samples: int
    pubmed_ids: List[str] = []
    relevance_score: float = 0.0

    # NEW: Fulltext data from linked publications
    fulltext: List[FulltextData] = []
    fulltext_status: str = "not_downloaded"  # "downloading", "downloaded", "failed"
    fulltext_count: int = 0
```

### Integration Point 3: ReportAgent Enhancement

**File:** `omics_oracle_v2/agents/report_agent.py`
**Location:** GPT-4 prompt construction
**Action:** Include fulltext in analysis

**Current Code:**
```python
def _generate_report(self, datasets: List[Dataset]) -> str:
    prompt = f"""
    Analyze these GEO datasets:

    {self._format_datasets_for_prompt(datasets)}
    """

    # Only includes: GEO ID, title, summary, organism, platform, samples
```

**Enhanced Code (NEW):**
```python
def _generate_report(self, datasets: List[Dataset]) -> str:
    prompt = f"""
    Analyze these GEO datasets with full-text paper content:

    {self._format_datasets_with_fulltext(datasets)}
    """

def _format_datasets_with_fulltext(self, datasets: List[Dataset]) -> str:
    """Format datasets including fulltext for GPT-4 analysis."""
    formatted = []

    for dataset in datasets:
        sections = [
            f"## Dataset: {dataset.geo_id}",
            f"Title: {dataset.title}",
            f"Organism: {dataset.organism}",
            f"Platform: {dataset.platform}",
            f"Samples: {dataset.samples}",
            f"\n### GEO Summary:",
            dataset.summary,
        ]

        # NEW: Include fulltext if available
        if dataset.fulltext:
            sections.append(f"\n### Linked Publications ({len(dataset.fulltext)} papers):")
            for ft in dataset.fulltext:
                sections.extend([
                    f"\n#### Paper: {ft.title} (PMID: {ft.pmid})",
                    f"\n**Abstract:**\n{ft.abstract}",
                    f"\n**Methods:**\n{ft.methods[:2000]}...",  # Truncate for token limits
                    f"\n**Results:**\n{ft.results[:2000]}...",
                    f"\n**Discussion:**\n{ft.discussion[:1000]}...",
                ])
        else:
            sections.append("\n*No full-text available for this dataset*")

        formatted.append("\n".join(sections))

    return "\n\n---\n\n".join(formatted)
```

### Integration Point 4: Frontend Display Enhancement

**File:** `omics_oracle_v2/api/static/dashboard.html`
**Location:** Results display section
**Action:** Show fulltext download status

**Current Display:**
```html
<div class="dataset-card">
    <h3>GSE306759</h3>
    <p>Relevance: 10%</p>
    <p>Effect of palmitate on breast cancer cells...</p>
    <p>🧬 Unknown organism</p>
    <p>🔬 GPL34281</p>
    <p>📊 8 samples</p>
</div>
```

**Enhanced Display (NEW):**
```html
<div class="dataset-card">
    <h3>GSE306759</h3>
    <p>Relevance: 10%</p>
    <p>Effect of palmitate on breast cancer cells...</p>
    <p>🧬 Unknown organism</p>
    <p>🔬 GPL34281</p>
    <p>📊 8 samples</p>

    <!-- NEW: Fulltext status indicator -->
    <div class="fulltext-status">
        <span class="status-icon">✓</span>
        <span class="status-text">2 PDFs downloaded & parsed</span>
    </div>
</div>
```

**JavaScript Enhancement:**
```javascript
function displayResults(data) {
    const datasets = data.datasets || [];

    const html = datasets.map(dataset => `
        <div class="dataset-card">
            <h3>${dataset.geo_id}</h3>
            <!-- ... existing fields ... -->

            ${dataset.fulltext_count > 0 ? `
                <div class="fulltext-status success">
                    ✓ ${dataset.fulltext_count} PDF(s) downloaded & parsed
                </div>
            ` : `
                <div class="fulltext-status warning">
                    ⚠ No full-text available
                </div>
            `}
        </div>
    `).join('');

    document.getElementById('results').innerHTML = html;
}
```

---

## Implementation Plan

### Phase 1: Backend Integration (2-3 hours)

**Step 1.1: Update Dataset Model**
- File: `omics_oracle_v2/agents/models/search.py`
- Add `FulltextData` class
- Add `fulltext`, `fulltext_status`, `fulltext_count` fields to `Dataset`

**Step 1.2: Enhance SearchAgent**
- File: `omics_oracle_v2/agents/search_agent.py`
- Add `_enrich_with_fulltext()` method
- Integrate GEOCitationPipeline
- Make SearchAgent async (or use sync wrapper)

**Step 1.3: Update ReportAgent**
- File: `omics_oracle_v2/agents/report_agent.py`
- Add `_format_datasets_with_fulltext()` method
- Update GPT-4 prompt to include fulltext

### Phase 2: Frontend Integration (1-2 hours)

**Step 2.1: Update Result Display**
- File: `omics_oracle_v2/api/static/dashboard.html`
- Add fulltext status indicator
- Update CSS for status badges

**Step 2.2: Add Loading Indicators**
- Show "Downloading PDFs..." progress
- Show "Parsing fulltext..." progress

### Phase 3: Testing & Refinement (1-2 hours)

**Step 3.1: Test Complete Flow**
- Search for "breast cancer RNA-seq"
- Verify PDF download occurs
- Verify fulltext parsing works
- Verify GPT-4 receives fulltext
- Verify frontend shows status

**Step 3.2: Handle Edge Cases**
- No PMIDs available → graceful degradation
- PDF download fails → show warning, continue
- Parsing fails → fallback to abstract only
- Token limit exceeded → truncate smartly

---

## Key Files to Modify

| File | Purpose | Estimated LOC |
|------|---------|---------------|
| `omics_oracle_v2/agents/models/search.py` | Add fulltext fields | +30 lines |
| `omics_oracle_v2/agents/search_agent.py` | Add PDF enrichment | +50 lines |
| `omics_oracle_v2/agents/report_agent.py` | Include fulltext in GPT-4 | +40 lines |
| `omics_oracle_v2/api/static/dashboard.html` | Show fulltext status | +20 lines |

**Total Estimated Changes:** ~140 lines of code

---

## Success Criteria

✅ **Backend:**
- [ ] SearchAgent downloads PDFs for all datasets with PMIDs
- [ ] Fulltext is parsed and normalized
- [ ] Dataset objects contain fulltext data
- [ ] ReportAgent receives fulltext
- [ ] GPT-4 analysis includes methods, results, discussion

✅ **Frontend:**
- [ ] Results show "✓ 2 PDFs downloaded & parsed"
- [ ] Loading indicators during PDF download
- [ ] Graceful handling when no PDFs available

✅ **User Experience:**
- [ ] Search → automatic processing → enriched results
- [ ] NO extra button clicks needed
- [ ] AI analysis is richer with fulltext context

---

## Performance Considerations

### Async Processing
- PDF download can be slow (10-30 seconds per paper)
- Should be async to avoid blocking
- Consider progress callbacks

### Caching Strategy
- Cache downloaded PDFs by PMID
- Cache parsed fulltext by PMID
- Reuse across multiple searches

### Token Limits
- GPT-4 has 128K token limit
- Average paper: ~20K tokens
- Limit to 3-5 papers per dataset
- Smart truncation: keep methods + results, truncate discussion

---

## Next Steps

1. **Immediate:** Update `Dataset` model with fulltext fields
2. **Next:** Implement `_enrich_with_fulltext()` in SearchAgent
3. **Then:** Update ReportAgent to use fulltext
4. **Finally:** Update frontend to show status

**Estimated Total Time:** 4-7 hours for complete implementation

---

## Notes

- All components already exist (GEOCitationPipeline, ContentNormalizer)
- Just need to wire them together in SearchAgent
- Maintain backward compatibility (fulltext optional)
- Use feature flag: `enable_fulltext_enrichment=True`
