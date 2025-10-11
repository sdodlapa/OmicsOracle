# OmicsOracle: Actual Implementation & End-to-End Flow

**Date:** October 10, 2025
**Status:** Current State Documentation

---

## 🎯 Overview

This document describes the **actual implemented flow** based on the codebase, not theoretical pipelines. It clarifies what works today and what's planned for the future.

---

## 📊 Current Architecture: Two Main Workflows

### Workflow 1: GEO Search via Web UI/API
**Entry Point:** User enters query in frontend
**Current Status:** ✅ **FULLY IMPLEMENTED**

### Workflow 2: GEO → Citations → PDFs Collection
**Entry Point:** Programmatic via `GEOCitationPipeline`
**Current Status:** ✅ **FULLY IMPLEMENTED** (Collection phase only)

---

## 🔍 WORKFLOW 1: Publication Search via Streamlit Dashboard (ACTUAL!)

### ⚠️ CRITICAL DISCOVERY: Dashboard Uses PublicationSearchPipeline, NOT SearchAgent!

**The actual flow is completely different from what I initially described!**

### End-to-End Flow

```
User Query (Streamlit Dashboard)
    ↓
Dashboard SearchPanel.render()
    ↓
User clicks "Search" button
    ↓
DashboardApp._execute_search()
    ↓
┌─────────────────────────────────────┐
│  Step 1: Query Preprocessing         │
│  (if enable_query_preprocessing)     │
│  - BiomedicalNER entity extraction   │
│  - Extract: Genes, Diseases,         │
│    Techniques, Organisms             │
│  - Build source-specific queries:    │
│    * PubMed: Add field tags          │
│      [Gene Name], [MeSH], etc.       │
│    * OpenAlex: Prioritize entities   │
│    * Scholar: Use expanded query     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 2: Synonym Expansion           │
│  (if enable_synonym_expansion)       │
│  - SynonymExpander.expand_query()    │
│  - Use ontology gazetteers           │
│  - Add technique synonyms            │
│    Example: "HiC" → "Hi-C", "3C"     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 3: Multi-Source Search         │
│  - PubMed (if enable_pubmed)         │
│    Uses optimized query with tags    │
│  - OpenAlex (if enable_openalex)     │
│    Prioritizes entity terms          │
│  - Google Scholar (if enable_scholar)│
│    Uses expanded query               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 4: Deduplication               │
│  - Pass 1: ID-based (PMID, DOI)      │
│  - Pass 2: Fuzzy matching            │
│    Title/author similarity           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 5: Institutional Access        │
│  (if enable_institutional_access)    │
│  - Check Georgia Tech/ODU access     │
│  - Add access_url to metadata        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 6: Full-Text URL Collection    │
│  (if enable_fulltext_retrieval)      │
│  - FullTextManager waterfall:        │
│    1. CORE                           │
│    2. BioRxiv                        │
│    3. ArXiv                          │
│    4. CrossRef                       │
│    5. OpenAlex OA URLs               │
│    6. Unpaywall                      │
│    7. Sci-Hub (optional)             │
│    8. LibGen (optional)              │
│  - Add fulltext_url to metadata      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 7: Ranking                     │
│  - PublicationRanker.rank()          │
│  - Multi-factor scoring              │
│  - Return top N results              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 8: Citation Enrichment         │
│  (if enable_citations)               │
│  - Find citing papers (CitationFinder)│
│    Uses OpenAlex + Scholar + S2      │
│  - LLM analysis of citations         │
│  - Dataset reuse detection           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 9: Semantic Scholar Enrichment │
│  - Add citation counts               │
│  - Add influence scores              │
│  - Free alternative to Scholar       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 10: PDF Download (Optional)    │
│  (if enable_pdf_download)            │
│  - PDFDownloadManager                │
│  - Async parallel downloads          │
│  - Validation & retries              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 11: Text Extraction (Optional) │
│  (if enable_fulltext)                │
│  - PDFTextExtractor                  │
│  - Extract text from downloaded PDFs │
│  - Add full_text to Publication      │
└─────────────────────────────────────┘
    ↓
Results Displayed in Dashboard
    ↓
Tabs: Results | Visualizations | Analytics
```

### Actual Code Components (Dashboard → PublicationSearchPipeline)

#### 1. **Frontend: Streamlit Dashboard**
- Location: `omics_oracle_v2/lib/dashboard/app.py`
- Framework: Streamlit (NOT static HTML!)
- Port: 8502 (default)

**Code:**
```python
# dashboard/app.py line ~150
def _execute_search(self, params: Dict[str, Any]) -> None:
    """Execute search with given parameters."""
    query = params["query"]

    with st.spinner(f"Searching for: {query}..."):
        # Import PublicationSearchPipeline (NOT SearchAgent!)
        from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
        from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

        # Create pipeline config
        pipeline_config = PublicationSearchConfig(
            enable_pubmed="pubmed" in params["databases"],
            enable_scholar="scholar" in params["databases"],
            enable_citations=params.get("use_llm", False),
            max_total_results=params["max_results"],
        )

        # Execute search via pipeline
        pipeline = PublicationSearchPipeline(pipeline_config)
        search_result = pipeline.search(
            query=query,
            max_results=params["max_results"],
        )
```

**Key Discovery:** Dashboard uses `PublicationSearchPipeline`, not `SearchAgent`!

#### 2. **PublicationSearchPipeline** (Main Orchestrator)
- File: `omics_oracle_v2/lib/pipelines/publication_pipeline.py`
- 11-step pipeline with conditional execution based on feature toggles

**Main Search Method:**
```python
# publication_pipeline.py line ~470
def search(self, query: str, max_results: int = 50, **kwargs) -> PublicationResult:
    """Search for publications across enabled sources."""

    # Step 0: Preprocess query (NEW - Phase 1)
    preprocessed = self._preprocess_query(query)
    # Extracts entities, expands synonyms, builds source-specific queries

    # Step 1: Search enabled sources
    all_publications = []

    # 1a. PubMed (conditional)
    if self.pubmed_client:
        pubmed_query = preprocessed.get("pubmed", query)
        pubmed_results = self.pubmed_client.search(pubmed_query, max_results)
        all_publications.extend(pubmed_results)

    # 1b. Google Scholar (conditional)
    if self.scholar_client:
        scholar_query = preprocessed.get("scholar", query)
        scholar_results = self.scholar_client.search(scholar_query, max_results)
        all_publications.extend(scholar_results)

    # 1c. OpenAlex (conditional)
    if self.openalex_client:
        openalex_query = preprocessed.get("openalex", query)
        openalex_results = self.openalex_client.search(openalex_query, max_results)
        all_publications.extend(openalex_results)

    # Step 2: Deduplicate (2-pass: ID-based + fuzzy)
    all_publications = self._deduplicate_publications(all_publications)

    # Step 3: Institutional access enrichment
    if self.institutional_manager:
        # Add access_url, access_status to metadata
        # ...

    # Step 3.5: Full-text URL enrichment
    if self.fulltext_manager:
        # Waterfall through 8 sources to find PDFs
        # ...

    # Step 4: Rank publications
    ranked_results = self.ranker.rank(all_publications, query, max_results)

    # Step 5: Citation enrichment
    if self.citation_finder:
        # Find citing papers using OpenAlex/Scholar/S2
        ranked_results = self._enrich_citations(ranked_results)

    # Step 5.5: Semantic Scholar enrichment
    if self.semantic_scholar_client:
        # Add citation counts, influence scores
        # ...

    # Step 6: PDF download
    if self.pdf_downloader:
        self._download_pdfs(ranked_results)

    # Step 7: Text extraction
    if self.pdf_text_extractor:
        ranked_results = self._extract_fulltext(ranked_results)

    return PublicationResult(
        query=query,
        publications=ranked_results,
        sources_used=sources_used,
        # ...
    )
```

#### 3. **Query Preprocessing** (NEW! - This is what I missed!)
- File: `omics_oracle_v2/lib/pipelines/publication_pipeline.py`
- Uses: BiomedicalNER + SynonymExpander

**Code:**
```python
# publication_pipeline.py line ~290
def _preprocess_query(self, query: str) -> dict:
    """
    Preprocess query to extract biological entities and build optimized queries.

    Phase 1: Basic entity extraction + field tagging
    Phase 2B: Synonym expansion with ontologies
    """
    # Step 1: Synonym expansion
    expanded_query = query
    if self.synonym_expander:
        expanded_query = self.synonym_expander.expand_query(query)
        # Example: "DNA methylation HiC" → "DNA methylation (HiC OR Hi-C OR 3C)"

    # Step 2: Entity extraction
    if self.ner:
        ner_result = self.ner.extract_entities(expanded_query)
        entities_by_type = ner_result.entities_by_type
        # Extracts: GENE, DISEASE, TECHNIQUE, ORGANISM

    # Step 3: Build source-specific queries
    return {
        "original": query,
        "expanded": expanded_query,
        "entities": entities_by_type,
        "pubmed": self._build_pubmed_query(expanded_query, entities_by_type),
        "openalex": self._build_openalex_query(expanded_query, entities_by_type),
        "scholar": expanded_query,
    }
```

**PubMed Query Builder:**
```python
# publication_pipeline.py line ~320
def _build_pubmed_query(self, original_query: str, entities_by_type: dict) -> str:
    """Build PubMed-optimized query with field tags."""
    parts = []

    # Add genes with field tag
    if EntityType.GENE in entities_by_type:
        genes = entities_by_type[EntityType.GENE]
        gene_terms = " OR ".join(f'"{g.text}"[Gene Name]' for g in genes[:5])
        parts.append(f"({gene_terms})")

    # Add diseases with MeSH tag
    if EntityType.DISEASE in entities_by_type:
        diseases = entities_by_type[EntityType.DISEASE]
        disease_terms = " OR ".join(f'"{d.text}"[MeSH]' for d in diseases[:5])
        parts.append(f"({disease_terms})")

    # Combine enhanced query with original
    if parts:
        enhanced = " AND ".join(parts)
        return f"({enhanced}) OR ({original_query})"

    return original_query
```

**Real Example:**
```
Input:  "breast cancer BRCA1"
↓ Synonym Expansion
"breast cancer (BRCA1 OR BRCA1 gene)"
↓ Entity Extraction
Entities: DISEASE=["breast cancer"], GENE=["BRCA1"]
↓ PubMed Query
("breast cancer"[MeSH]) AND ("BRCA1"[Gene Name] OR "BRCA1 gene"[Gene Name]) OR (breast cancer BRCA1)
```

#### 4. **Multi-Source Search Clients**

**PubMed Client:**
- File: `omics_oracle_v2/lib/publications/clients/pubmed.py`
- Uses NCBI E-utilities API with optimized queries

**OpenAlex Client:**
- File: `omics_oracle_v2/lib/citations/clients/openalex.py`
- Free, sustainable alternative to Google Scholar
- 250M+ works, citation data, open access URLs

**Google Scholar Client:**
- File: `omics_oracle_v2/lib/citations/clients/scholar.py`
- Fallback for citations and hard-to-find papers

#### 5. **Deduplication System** (2-pass)
- File: `omics_oracle_v2/lib/publications/deduplication.py`

**Code:**
```python
def _deduplicate_publications(self, publications: List[Publication]) -> List[Publication]:
    """
    Multi-pass deduplication:
    - Pass 1: ID-based (PMID, DOI) - exact matching
    - Pass 2: Fuzzy (title, authors, year) - catches variations
    """
    # Pass 1: ID-based
    seen_pmids, seen_dois = set(), set()
    unique_pubs = []
    for pub in publications:
        if pub.pmid not in seen_pmids and pub.doi not in seen_dois:
            unique_pubs.append(pub)
            seen_pmids.add(pub.pmid)
            seen_dois.add(pub.doi)

    # Pass 2: Fuzzy matching (if enabled)
    if self.fuzzy_deduplicator:
        unique_pubs = self.fuzzy_deduplicator.deduplicate(unique_pubs)

    return unique_pubs
```

#### 6. **Full-Text URL Collection** (8-source waterfall)
- File: `omics_oracle_v2/lib/fulltext/manager.py`

**Sources (in priority order):**
1. CORE - Academic papers
2. BioRxiv - Preprints
3. ArXiv - Scientific preprints
4. CrossRef - DOI metadata
5. OpenAlex - OA URLs from metadata
6. Unpaywall - Legal OA repository (50% improvement)
7. Sci-Hub - Mirror repository (25% improvement, optional)
8. LibGen - Document repository (5-10% improvement, optional)

### Key Differences from Initial Understanding

✅ **HAS query preprocessing** (BiomedicalNER + SynonymExpander)
- Entity extraction (genes, diseases, techniques)
- Synonym expansion with ontologies
- Source-specific query optimization

✅ **HAS multi-source search** (PubMed + OpenAlex + Scholar)
- Not just GEO datasets
- Publication search across databases
- 250M+ papers available

✅ **HAS advanced deduplication** (2-pass system)
- ID-based exact matching
- Fuzzy title/author matching
- Handles preprint/published pairs

✅ **HAS full-text collection** (8-source waterfall)
- Institutional access first
- Multiple OA sources
- Optional mirror sites

❌ **Dashboard does NOT use SearchAgent**
- Uses PublicationSearchPipeline directly
- SearchAgent is for GEO datasets only (different use case)

---

## 🧬 WORKFLOW 2: GEO Search via API (SearchAgent)

**This is a SEPARATE workflow from the dashboard!**

### End-to-End Flow

```
API Request
    ↓
POST /api/agents/search
    ↓
SearchAgent.execute()
    ↓
┌─────────────────────────────────────┐
│  GEO Client Search                   │
│  - Query sent AS-IS to NCBI          │
│  - NO preprocessing                  │
│  - NO synonym expansion              │
│  - Esearch + Esummary                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Semantic Search (Optional)          │
│  - If enable_semantic=true           │
│  - FAISS vector search               │
│  - Hybrid TF-IDF + vector ranking    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  7-Dimension Quality Scoring         │
│  1. Sample count                     │
│  2. Metadata completeness            │
│  3. Recency                          │
│  4. Citation count                   │
│  5. Platform diversity               │
│  6. Data availability                │
│  7. Publication status               │
└─────────────────────────────────────┘
    ↓
Return JSON Response
```

### Code Implementation

**API Endpoint:**
```python
# omics_oracle_v2/api/routes/agents.py
@router.post("/search")
async def execute_search_agent(request: SearchRequest):
    agent = SearchAgent(settings, enable_semantic=request.enable_semantic)

    search_input = SearchInput(
        search_terms=request.search_terms,
        filters=request.filters,
        max_results=request.max_results
    )

    result = agent.execute(search_input)
    return SearchResponse(datasets=ranked_datasets)
```

**GEO Client:**
```python
# omics_oracle_v2/lib/geo/client.py
async def search(self, query: str, max_results: int) -> GEOSearchResult:
    # Direct NCBI E-utilities call - NO preprocessing!
    esearch_url = f"{BASE_URL}/esearch.fcgi"
    params = {
        "db": "gds",
        "term": query,  # ← Query used AS-IS
        "retmax": max_results,
        "retmode": "json"
    }
    # ...
```

### Key Differences from Dashboard Workflow

| Feature | Dashboard (PublicationSearchPipeline) | API (SearchAgent) |
|---------|--------------------------------------|-------------------|
| **Query Preprocessing** | ✅ YES (BiomedicalNER + Synonyms) | ❌ NO (direct to NCBI) |
| **Target Database** | PubMed, OpenAlex, Scholar | GEO datasets only |
| **Data Type** | Publications (papers) | GEO Series (datasets) |
| **Citation Discovery** | ✅ YES (multi-source) | ❌ NO |
| **PDF Download** | ✅ YES (optional) | ❌ NO |
| **Full-text Collection** | ✅ YES (8 sources) | ❌ NO |
| **Use Case** | Find papers on a topic | Find GEO datasets |

---

## 📚 WORKFLOW 3: GEO Citation Pipeline (Programmatic)

### End-to-End Flow

```
Python Script Call
    ↓
pipeline = GEOCitationPipeline(config)
result = await pipeline.collect(query="breast cancer RNA-seq")
    ↓
┌─────────────────────────────────────┐
│  Step 1: Query Optimization          │
│  - GEOQueryBuilder                   │
│  - Extract key scientific terms      │
│  - Remove stop words                 │
│  - Add field restrictions [Title]    │
│  - Create Boolean query with OR      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 2: GEO Search                  │
│  - Use optimized query               │
│  - GEOClient.search()                │
│  - Batch metadata fetching (parallel)│
│  - Returns: List<GEOSeriesMetadata>  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 3: Citation Discovery          │
│  - For each GEO dataset:             │
│    - Strategy 1: Find papers         │
│      citing original publication     │
│    - Strategy 2: Find papers         │
│      mentioning GEO ID (e.g. GSE123)│
│  - Deduplicate by PMID/DOI          │
│  - Returns: List<Publication>        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 4: Full-Text URL Collection    │
│  - FullTextManager (waterfall)       │
│  - Try sources in order:             │
│    1. Institutional access           │
│    2. Unpaywall                      │
│    3. CORE                           │
│    4. Sci-Hub (optional)             │
│    5. LibGen (optional)              │
│  - Add fulltext_url to Publication   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 5: PDF Download                │
│  - PDFDownloadManager                │
│  - Parallel downloads (5 concurrent) │
│  - Validation & retry logic          │
│  - Save to: data/geo_citation_       │
│    collections/{query}_{timestamp}/  │
│    pdfs/                             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 6: Metadata Storage            │
│  - Save to collection directory:     │
│    - geo_datasets.json               │
│    - citing_papers.json              │
│    - collection_report.json          │
└─────────────────────────────────────┘
    ↓
Return CollectionResult
```

### Actual Code Implementation

#### Step 1: Query Optimization

**File:** `omics_oracle_v2/lib/geo/query_builder.py`

```python
class GEOQueryBuilder:
    def build_query(self, query: str, mode="balanced") -> str:
        """
        Transform natural language to optimized NCBI query.

        Example:
        Input:  "DNA methylation HiC"
        Output: ("DNA"[Title] OR "methylation"[Title]) AND
                (HiC[Title] OR "Hi-C"[Title] OR "3C"[Title])
        """
        # 1. Extract key terms (remove stop words)
        terms = self._extract_key_terms(query)

        # 2. Expand technique synonyms
        expanded_terms = self._expand_synonyms(terms)

        # 3. Build Boolean query with field restrictions
        if mode == "comprehensive":
            # Search in Title OR Description
            query_parts = [
                f'({term}[Title] OR {term}[Description])'
                for term in expanded_terms
            ]
        else:  # balanced (default)
            # Title-only for precision
            query_parts = [f'{term}[Title]' for term in expanded_terms]

        return " AND ".join(query_parts)
```

**Real Example:**
```
Input:  "DNA methylation HiC"
Output: ("DNA"[Title] OR "methylation"[Title]) AND
        (HiC[Title] OR "Hi-C"[Title])

Result: Found 18 datasets (vs 1 with naive query)
```

#### Step 2: GEO Search (Same as Workflow 1)

Uses `GEOClient` but with optimized query from Step 1.

#### Step 3: Citation Discovery

**File:** `omics_oracle_v2/lib/citations/discovery/geo_discovery.py`

```python
class GEOCitationDiscovery:
    async def find_citing_papers(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100
    ) -> CitationDiscoveryResult:
        """
        Find papers citing this GEO dataset.

        Two strategies:
        1. Citation-based: Papers citing original publication
        2. Mention-based: Papers mentioning GEO ID in text
        """
        citing_papers = []

        # Strategy 1: Citation discovery
        if geo_metadata.pmid:
            cited_by = await self._find_citing_via_pubmed(
                geo_metadata.pmid
            )
            citing_papers.extend(cited_by)

        # Strategy 2: Mention discovery
        mentioned_in = await self._find_mentioning_geo_id(
            geo_metadata.geo_id
        )
        citing_papers.extend(mentioned_in)

        # Deduplicate
        unique_papers = self._deduplicate(citing_papers)

        return CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            citing_papers=unique_papers
        )
```

#### Step 4: Full-Text URL Collection

**File:** `omics_oracle_v2/lib/fulltext/manager.py`

```python
class FullTextManager:
    async def get_fulltext_batch(
        self,
        publications: List[Publication]
    ) -> List[Publication]:
        """
        Add full-text URLs using waterfall strategy.

        Tries sources in priority order until one succeeds.
        """
        for pub in publications:
            # Try each source in order
            for source in self.sources:
                url = await source.get_fulltext_url(pub)
                if url:
                    pub.fulltext_url = url
                    pub.fulltext_source = source.name
                    break  # Stop at first success

        return publications
```

**Sources (in priority order):**
1. **Institutional Access** - Georgia Tech proxy, ezproxy
2. **Unpaywall** - Legal open access repository
3. **CORE** - Academic paper aggregator
4. **Sci-Hub** (optional) - Mirror repository
5. **LibGen** (optional) - Document repository

#### Step 5: PDF Download

**File:** `omics_oracle_v2/lib/storage/pdf/download_manager.py`

```python
class PDFDownloadManager:
    async def download_batch(
        self,
        publications: List[Publication],
        output_dir: Path
    ) -> DownloadReport:
        """
        Download PDFs with parallel processing and retries.
        """
        # Filter publications with URLs
        to_download = [p for p in publications if p.fulltext_url]

        # Download concurrently (max 5 at a time)
        tasks = []
        for pub in to_download:
            task = self._download_single(pub, output_dir)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate PDFs
        if self.validate_pdf:
            for result in results:
                if result.success:
                    is_valid = self._validate_pdf(result.file_path)
                    result.validated = is_valid

        return DownloadReport(
            total=len(to_download),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success)
        )
```

#### Step 6: Metadata Storage

**File:** `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py`

```python
async def _save_metadata(
    self,
    collection_dir: Path,
    query: str,
    datasets: List[GEOSeriesMetadata],
    papers: List[Publication],
    citation_results: List[CitationDiscoveryResult],
    download_report: dict
):
    """
    Save all collected data for future analysis.

    Directory structure:
    data/geo_citation_collections/
        {query}_{timestamp}/
            geo_datasets.json       ← GEO metadata
            citing_papers.json      ← Publication metadata
            collection_report.json  ← Summary stats
            pdfs/                   ← Downloaded PDFs
                {pmid}.pdf
    """
    # Save GEO datasets
    with open(collection_dir / "geo_datasets.json", "w") as f:
        json.dump([asdict(ds) for ds in datasets], f, indent=2)

    # Save citing papers
    with open(collection_dir / "citing_papers.json", "w") as f:
        json.dump([asdict(p) for p in papers], f, indent=2)

    # Save summary report
    report = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "datasets_count": len(datasets),
        "citing_papers_count": len(papers),
        "fulltext_coverage": sum(1 for p in papers if p.fulltext_url) / len(papers),
        "pdfs_downloaded": download_report.get("successful", 0),
        "download_report": download_report
    }
    with open(collection_dir / "collection_report.json", "w") as f:
        json.dump(report, f, indent=2)
```

---

## ⚠️ What's NOT Yet Implemented

### Phase 7: Analysis & Insights (Future Work)

**NOT YET BUILT:**
- ❌ PDF text extraction at scale
- ❌ LLM analysis of collected papers
- ❌ Chat interface over collected documents
- ❌ Report/summary generation
- ❌ Research idea generation
- ❌ Insight extraction

**Current State:**
```python
# geo_citation_pipeline.py line 7:
# NO LLM ANALYSIS - Pure data collection phase.
# Phase 7 will add LLM analysis of collected papers.
```

**What needs to be built:**

```python
# Future: Phase 7 - Analysis Pipeline
class AnalysisPipeline:
    """
    Analyze collected documents and generate insights.

    NOT YET IMPLEMENTED
    """

    async def analyze_collection(
        self,
        collection_dir: Path
    ) -> AnalysisResult:
        """
        1. Extract text from PDFs
        2. Chunk documents for LLM context
        3. Generate embeddings
        4. Enable RAG Q&A
        5. Generate summaries
        6. Extract key findings
        7. Suggest research directions
        """
        pass  # TODO: Implement Phase 7
```

---

## 🎯 Summary: What Actually Works Today

### ✅ Implemented & Working

**Dashboard Publication Search (Workflow 1):**
- ✅ Query preprocessing (BiomedicalNER + SynonymExpander)
- ✅ Entity extraction (genes, diseases, techniques, organisms)
- ✅ Synonym expansion with ontologies
- ✅ Source-specific query optimization (PubMed field tags, OpenAlex prioritization)
- ✅ Multi-source search (PubMed + OpenAlex + Google Scholar)
- ✅ 2-pass deduplication (ID-based + fuzzy matching)
- ✅ Institutional access checking (Georgia Tech + ODU)
- ✅ Full-text URL collection (8-source waterfall)
- ✅ Advanced ranking system
- ✅ Citation enrichment (OpenAlex + Scholar + Semantic Scholar)
- ✅ PDF download (async, parallel, validated)
- ✅ Text extraction from PDFs
- ✅ Streamlit dashboard with visualizations

**GEO Search API (Workflow 2):**
- ✅ Direct NCBI GEO search
- ✅ 7-dimension quality scoring
- ✅ Optional semantic search (FAISS)
- ✅ JSON API endpoint

**GEO Citation Collection (Workflow 3):**
- ✅ Query optimization (GEOQueryBuilder)
- ✅ GEO dataset discovery
- ✅ Citation discovery (2 strategies)
- ✅ Full-text URL collection (5+ sources)
- ✅ PDF download (parallel, validated)
- ✅ Metadata storage (structured JSON)

### ❌ Not Yet Implemented

**Phase 7 (Future - Analysis Pipeline):**
- ❌ LLM-based document analysis at scale
- ❌ RAG Q&A over collected papers
- ❌ Automated summary/report generation
- ❌ Research idea generation from literature
- ❌ Insight extraction and synthesis
- ❌ Trend analysis across documents
- ❌ Chat interface over knowledge base

### 🔍 Major Discovery Summary

**What I Got Wrong Initially:**
1. ❌ Thought dashboard used SearchAgent → Actually uses PublicationSearchPipeline
2. ❌ Thought there was NO query preprocessing → Actually has sophisticated NER + synonyms
3. ❌ Thought only GEO search was available → Actually has publication search too
4. ❌ Thought workflows were related → They're completely separate use cases

**What I Got Right:**
1. ✅ GEOCitationPipeline is for collection only (no analysis yet)
2. ✅ Future work is analysis/insights generation
3. ✅ Multiple sources with waterfall strategy
4. ✅ Async PDF download and validation

---

## 🚀 Recommended Next Steps

Based on this analysis, here's what we should focus on:

### Option A: Complete Workflow 1 (UI/API Enhancement)
**Goal:** Bring citation collection to the web UI

**Tasks:**
1. Add "Collect Citations" button to search results
2. Create API endpoint: `POST /api/citations/collect`
3. Background job for citation pipeline
4. Progress tracking (WebSocket or polling)
5. Display collection results in UI

**Timeline:** 1-2 days

### Option B: Start Phase 7 (Analysis Pipeline)
**Goal:** Extract value from collected documents

**Tasks:**
1. PDF text extraction service
2. Document chunking for LLM
3. Embedding generation
4. RAG interface (Q&A over papers)
5. Summary generation

**Timeline:** 1-2 weeks

### Option C: Fix Flow Diagram (Documentation)
**Goal:** Update docs to reflect actual implementation

**Tasks:**
1. Rewrite PIPELINE_FLOW_DIAGRAM.md
2. Create COLLECTION_VS_ANALYSIS.md
3. Update PIPELINE_DECISION_GUIDE.md
4. Add architecture diagrams

**Timeline:** 2-3 hours

---

## 💡 My Recommendation

**Start with Option C** (documentation fix), then **Option A** (UI integration), then **Option B** (analysis).

**Reasoning:**
1. Documentation ensures we have correct mental model
2. UI integration makes the tool usable for end users
3. Analysis phase is the most complex (needs careful design)

**What should we do now?**
- Fix the flow diagram to show actual implementation
- Create a clear separation: Collection vs Analysis
- Plan the Analysis Pipeline architecture

Would you like me to:
1. **Fix the flow diagram** to match actual code?
2. **Plan the Analysis Pipeline** architecture?
3. **Design the UI integration** for citation collection?

Let me know which direction you want to go! 🚀
