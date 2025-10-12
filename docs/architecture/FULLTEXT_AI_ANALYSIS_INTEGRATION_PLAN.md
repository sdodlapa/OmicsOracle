# Full-Text AI Analysis Integration Plan

**Date:** October 12, 2025  
**Goal:** Make GPT-4 analyze normalized full-text PDFs instead of just GEO summaries

---

## Current System Analysis

### 1. Search Flow (✅ Already Using UnifiedSearchPipeline)

```
User: "breast cancer RNA-seq" → Click [Search]
    ↓
Dashboard → POST /api/agents/search
    ↓
agents.py:search() → SearchAgent.execute()
    ↓
SearchAgent._process_unified() → UnifiedSearchPipeline.search()
    ↓
Returns: Dataset[] with PMIDs
    {
        geo_id: "GSE306759",
        title: "Effect of palmitate...",
        summary: "GEO summary text...",
        pubmed_ids: ["12345678", "87654321"],  ✅ HAS PMIDs!
        relevance_score: 0.95
    }
```

**Status:** ✅ **SearchAgent IS using UnifiedSearchPipeline**
- File: `omics_oracle_v2/agents/search_agent.py`
- Line 69: `self._use_unified_pipeline = True`
- Returns datasets with PMIDs

### 2. AI Analysis Flow (❌ Only Uses GEO Summary)

```
User: Click [🤖 AI Analysis] on dataset card
    ↓
Dashboard → POST /api/agents/analyze
    {
        datasets: [dataset],  // Only has GEO metadata
        query: "breast cancer RNA-seq",
        max_datasets: 1
    }
    ↓
routes/agents.py:analyze_datasets()
    ↓
Build prompt with GEO summary only:
    dataset_summaries.append(
        f"Title: {ds.title}\n"
        f"Summary: {ds.summary[:300]}..."  ❌ Only GEO summary!
    )
    ↓
GPT-4 analyzes → Returns insights
```

**Status:** ❌ **AI Analysis is MISSING full-text content**
- File: `omics_oracle_v2/api/routes/agents.py`, line 546
- Only uses: `ds.title`, `ds.summary`, `ds.organism`, `ds.sample_count`
- Does NOT use: PDFs, full-text, methods, results, discussion

---

## The Gap

### What We Have:
1. ✅ UnifiedSearchPipeline returns datasets with PMIDs
2. ✅ GEOCitationPipeline can download PDFs
3. ✅ ContentNormalizer can parse PDFs to structured format
4. ✅ ParsedCache can store and retrieve normalized content

### What's Missing:
1. ❌ SearchAgent doesn't automatically download PDFs
2. ❌ Dataset model doesn't include full-text field
3. ❌ AI analysis endpoint doesn't receive full-text
4. ❌ GPT-4 prompt doesn't include full-text content

---

## Solution Architecture

### Option 1: Auto-Download in SearchAgent (Recommended)
**Pros:**
- Full-text available immediately after search
- Single pipeline integration point
- Consistent for all uses (dashboard, API, workflows)

**Cons:**
- Slower search (10-30s per dataset with PDFs)
- More API calls to PubMed/PMC
- Higher storage usage

### Option 2: On-Demand Download in AI Analysis
**Pros:**
- Faster search results
- Only download when user requests analysis
- Lower resource usage

**Cons:**
- Delay when clicking AI Analysis button
- Duplicate downloads if multiple analyses
- More complex error handling

### Option 3: Hybrid Approach (BEST)
**Pros:**
- Fast search results (no PDF download)
- Download PDFs in background after search
- Cache prevents duplicate downloads
- AI analysis has full-text when clicked

**Implementation:**
```
Search → Returns datasets with PMIDs
      → Trigger background PDF download (async)
      → Store in cache with GEO ID as key

AI Analysis → Check cache for full-text
           → If available: Use full-text
           → If not available: Use GEO summary only
           → Show status: "Analyzing with 2 full papers"
```

---

## Implementation Plan (Hybrid Approach)

### Phase 1: Add Full-Text Field to Dataset Model

**File:** `omics_oracle_v2/agents/models/search.py`

**Current:**
```python
class Dataset(BaseModel):
    geo_id: str
    title: str
    summary: str
    organism: Optional[str]
    platform: Optional[str]
    sample_count: Optional[int]
    pubmed_ids: List[str] = []
    relevance_score: float = 0.0
```

**Enhanced:**
```python
from typing import List, Optional

class FullTextContent(BaseModel):
    """Parsed and normalized full-text from publication."""
    pmid: str
    title: str
    abstract: str
    methods: str
    results: str
    discussion: str
    introduction: Optional[str] = ""
    conclusion: Optional[str] = ""
    references: List[str] = []
    figures_captions: List[str] = []
    tables_captions: List[str] = []
    format: str  # "jats", "pdf", "latex"
    parse_date: str
    
class Dataset(BaseModel):
    geo_id: str
    title: str
    summary: str
    organism: Optional[str]
    platform: Optional[str]
    sample_count: Optional[int]
    pubmed_ids: List[str] = []
    relevance_score: float = 0.0
    
    # NEW: Full-text content
    fulltext: List[FullTextContent] = []
    fulltext_status: str = "not_downloaded"  # "downloading", "available", "failed", "partial"
    fulltext_count: int = 0
```

### Phase 2: Add Background PDF Download Service

**New File:** `omics_oracle_v2/services/fulltext_service.py`

```python
"""
Background service for downloading and parsing full-text papers.
"""

import asyncio
import logging
from typing import List, Optional
from pathlib import Path

from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline
from omics_oracle_v2.lib.fulltext.normalizer import ContentNormalizer
from omics_oracle_v2.lib.fulltext.parsed_cache import ParsedCache
from omics_oracle_v2.agents.models.search import Dataset, FullTextContent

logger = logging.getLogger(__name__)


class FullTextService:
    """Service for managing full-text downloads and parsing."""
    
    def __init__(self):
        self.citation_pipeline = GEOCitationPipeline()
        self.normalizer = ContentNormalizer()
        self.cache = ParsedCache()
    
    async def enrich_dataset_with_fulltext(
        self, 
        dataset: Dataset,
        max_papers: int = 3
    ) -> Dataset:
        """
        Download and parse PDFs for a dataset's linked publications.
        
        Args:
            dataset: Dataset with PMIDs
            max_papers: Maximum number of papers to download
            
        Returns:
            Dataset with fulltext field populated
        """
        if not dataset.pubmed_ids:
            dataset.fulltext_status = "no_pmids"
            return dataset
        
        dataset.fulltext_status = "downloading"
        fulltext_list = []
        
        try:
            # Limit to max_papers
            pmids_to_fetch = dataset.pubmed_ids[:max_papers]
            
            # Download PDFs using GEOCitationPipeline
            citations = await self.citation_pipeline.discover_and_download(
                geo_id=dataset.geo_id,
                pmids=pmids_to_fetch
            )
            
            # Parse each PDF to normalized format
            for citation in citations:
                if citation.pdf_path and Path(citation.pdf_path).exists():
                    try:
                        # Get normalized content (uses cache if available)
                        normalized = self.cache.get_normalized(
                            file_path=citation.pdf_path,
                            normalizer=self.normalizer
                        )
                        
                        if normalized:
                            fulltext_list.append(FullTextContent(
                                pmid=citation.pmid,
                                title=normalized.get('title', ''),
                                abstract=normalized.get('abstract', ''),
                                methods=normalized.get('methods', ''),
                                results=normalized.get('results', ''),
                                discussion=normalized.get('discussion', ''),
                                introduction=normalized.get('introduction', ''),
                                conclusion=normalized.get('conclusion', ''),
                                references=normalized.get('references', []),
                                figures_captions=normalized.get('figures', []),
                                tables_captions=normalized.get('tables', []),
                                format=normalized.get('format', 'unknown'),
                                parse_date=normalized.get('timestamp', '')
                            ))
                    except Exception as e:
                        logger.error(f"Failed to parse PDF for PMID {citation.pmid}: {e}")
                        continue
            
            # Update dataset
            dataset.fulltext = fulltext_list
            dataset.fulltext_count = len(fulltext_list)
            dataset.fulltext_status = "available" if fulltext_list else "failed"
            
            logger.info(
                f"Enriched {dataset.geo_id} with {len(fulltext_list)} "
                f"full-text papers out of {len(pmids_to_fetch)} PMIDs"
            )
            
        except Exception as e:
            logger.error(f"Failed to enrich {dataset.geo_id}: {e}")
            dataset.fulltext_status = "failed"
        
        return dataset
    
    async def enrich_datasets_batch(
        self,
        datasets: List[Dataset],
        max_papers_per_dataset: int = 3
    ) -> List[Dataset]:
        """
        Enrich multiple datasets with full-text in parallel.
        
        Args:
            datasets: List of datasets
            max_papers_per_dataset: Max papers per dataset
            
        Returns:
            List of enriched datasets
        """
        tasks = [
            self.enrich_dataset_with_fulltext(ds, max_papers_per_dataset)
            for ds in datasets
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Phase 3: Update SearchAgent to Trigger Background Enrichment

**File:** `omics_oracle_v2/agents/search_agent.py`

**Add after search completes:**
```python
def _process_unified(self, input_data, context):
    # Existing search logic
    pipeline = UnifiedSearchPipeline(config=self._unified_pipeline_config)
    result = pipeline.search(...)
    
    # NEW: Trigger background full-text enrichment
    if input_data.enable_fulltext_enrichment:
        self._trigger_fulltext_enrichment_async(result.datasets)
    
    return SearchOutput(
        datasets=result.datasets,
        total_results=result.total_results,
        # ...
    )

def _trigger_fulltext_enrichment_async(self, datasets: List[Dataset]):
    """
    Trigger background task to download and parse PDFs.
    Does not block search results.
    """
    import asyncio
    from omics_oracle_v2.services.fulltext_service import FullTextService
    
    async def enrich_in_background():
        service = FullTextService()
        await service.enrich_datasets_batch(datasets, max_papers_per_dataset=2)
    
    # Run in background without blocking
    asyncio.create_task(enrich_in_background())
```

### Phase 4: Update AI Analysis to Use Full-Text

**File:** `omics_oracle_v2/api/routes/agents.py`, function `analyze_datasets()`

**Current prompt building (line 590-598):**
```python
dataset_summaries.append(
    f"{i}. **{ds.geo_id}** (Relevance: {int(ds.relevance_score * 100)}%)\n"
    f"   Title: {ds.title}\n"
    f"   Organism: {ds.organism or 'N/A'}, Samples: {ds.sample_count or 0}\n"
    f"   Summary: {ds.summary[:300]}..."
)
```

**Enhanced with full-text:**
```python
# Build dataset summary
dataset_info = [
    f"{i}. **{ds.geo_id}** (Relevance: {int(ds.relevance_score * 100)}%)",
    f"   Title: {ds.title}",
    f"   Organism: {ds.organism or 'N/A'}, Samples: {ds.sample_count or 0}",
    f"   GEO Summary: {ds.summary[:200]}...",
]

# Add full-text content if available
if ds.fulltext and len(ds.fulltext) > 0:
    dataset_info.append(f"\n   📄 Full-text content from {len(ds.fulltext)} linked publications:")
    
    for j, ft in enumerate(ds.fulltext[:3], 1):  # Max 3 papers
        dataset_info.extend([
            f"\n   Paper {j}: {ft.title} (PMID: {ft.pmid})",
            f"   Abstract: {ft.abstract[:300]}...",
            f"   Methods: {ft.methods[:500]}...",
            f"   Results: {ft.results[:500]}...",
            f"   Discussion: {ft.discussion[:300]}...",
        ])
else:
    dataset_info.append("   ⚠️ No full-text available (analyzing GEO summary only)")

dataset_summaries.append("\n".join(dataset_info))
```

**Updated GPT-4 prompt:**
```python
analysis_prompt = f"""
User searched for: "{request.query}"

Found {len(datasets_to_analyze)} relevant datasets:

{chr(10).join(dataset_summaries)}

Analyze these datasets using the provided full-text papers (when available) and provide:

1. **Overview**: Which datasets are most relevant based on their methods and findings?
2. **Methodology Comparison**: How do these studies differ in experimental design and approach?
3. **Key Scientific Findings**: What are the main discoveries from the full papers?
4. **Recommendations**: 
   - For basic understanding of the topic
   - For advanced analysis and replication
   - For method development

Focus on insights from the Methods, Results, and Discussion sections.
Be specific and cite dataset IDs (GSE numbers) and PMIDs.
"""
```

### Phase 5: Update Dashboard to Show Full-Text Status

**File:** `omics_oracle_v2/api/static/dashboard_v2.html`

**Display full-text status in card:**
```html
<div class="dataset-summary">${dataset.summary || 'No summary available'}</div>

<!-- NEW: Full-text status indicator -->
${dataset.fulltext_count > 0 ? `
    <div class="fulltext-status">
        <span class="status-icon">✓</span>
        <span class="status-text">${dataset.fulltext_count} PDF(s) available for AI analysis</span>
    </div>
` : dataset.fulltext_status === 'downloading' ? `
    <div class="fulltext-status downloading">
        <span class="status-icon">⏳</span>
        <span class="status-text">Downloading PDFs...</span>
    </div>
` : ''}
```

**CSS:**
```css
.fulltext-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #e7f5e7;
    border-radius: 6px;
    font-size: 13px;
    margin-bottom: 12px;
    border-left: 3px solid #43e97b;
}

.fulltext-status.downloading {
    background: #fff8e1;
    border-left-color: #ffa726;
}

.status-icon {
    font-size: 16px;
}

.status-text {
    color: #2d3748;
    font-weight: 500;
}
```

---

## Implementation Timeline

### Week 1: Backend Foundation
- **Day 1-2:** Add FullTextContent model to Dataset
- **Day 2-3:** Create FullTextService with enrichment logic
- **Day 3-4:** Update SearchAgent with background enrichment
- **Day 4-5:** Test PDF download and parsing pipeline

### Week 2: AI Integration
- **Day 1-2:** Update AI analysis endpoint to use full-text
- **Day 2-3:** Optimize GPT-4 prompts with full-text
- **Day 3-4:** Handle token limits (truncation strategy)
- **Day 4-5:** Test AI analysis quality with full-text

### Week 3: Frontend & Polish
- **Day 1-2:** Update dashboard to show full-text status
- **Day 2-3:** Add loading indicators and error handling
- **Day 3-4:** Performance optimization and caching
- **Day 4-5:** End-to-end testing and documentation

**Total Estimated Time:** 3 weeks

---

## Success Criteria

### Phase 1: Data Availability
- [ ] SearchAgent returns datasets with PMIDs
- [ ] Background service downloads PDFs successfully
- [ ] PDFs are parsed to normalized format
- [ ] Full-text stored in dataset.fulltext field
- [ ] Cache prevents duplicate downloads

### Phase 2: AI Quality
- [ ] GPT-4 receives full-text content (methods, results, discussion)
- [ ] Analysis includes insights from full papers
- [ ] Recommendations reference specific experimental details
- [ ] Token limits handled gracefully (smart truncation)

### Phase 3: User Experience
- [ ] Dashboard shows "✓ 2 PDFs available for AI analysis"
- [ ] AI analysis button indicates full-text usage
- [ ] Loading states show "Analyzing 2 full papers..."
- [ ] Results show richer, more detailed insights
- [ ] Performance: Search <3s, Analysis <10s

---

## Risks & Mitigation

### Risk 1: Slow PDF Downloads
**Mitigation:** 
- Background downloads don't block search
- Cache prevents duplicate downloads
- Limit to 2-3 papers per dataset
- Show progress indicators

### Risk 2: GPT-4 Token Limits
**Mitigation:**
- Truncate sections intelligently (keep methods + results, truncate discussion)
- Limit to 3 papers per dataset
- Use GPT-4 Turbo (128K context window)
- Summarize long papers first

### Risk 3: PDF Parsing Failures
**Mitigation:**
- Graceful fallback to GEO summary only
- Show status: "Analyzing with GEO summary (PDF unavailable)"
- Log errors for debugging
- Retry failed downloads

### Risk 4: Storage Growth
**Mitigation:**
- Cache with TTL (7 days)
- Clean up old PDFs automatically
- Store only normalized text (not raw PDFs)
- Compress cached data

---

## Next Steps

1. **Confirm Approach:** User approves hybrid background enrichment strategy
2. **Start Phase 1:** Implement FullTextContent model
3. **Test Integration:** Verify PDF download → parse → cache → AI analysis flow
4. **Iterate:** Refine based on quality and performance

---

## Questions for User

1. **Timing:** Should we download PDFs immediately after search (background) or only when user clicks AI Analysis?
2. **Limits:** How many papers per dataset? (Recommended: 2-3 to balance quality vs token limits)
3. **Priority:** Focus on quality (more papers) or speed (fewer papers)?
4. **Fallback:** If PDFs unavailable, should AI analysis still run with GEO summary only?

**My Recommendation:** Hybrid approach with background download, 2-3 papers per dataset, graceful fallback to GEO summary.
