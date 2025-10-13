# Complete End-to-End Integration Flow
**Date:** October 12, 2025
**Purpose:** Visual guide for connecting GEO search → PDFs/Fulltext → Frontend display

## Executive Summary

**Current State:**
- ✅ GEO search working (UnifiedSearchPipeline)
- ✅ PDF download working (GEOCitationPipeline)
- ✅ Fulltext parsing working (ContentNormalizer)
- ❌ Frontend doesn't connect these pieces

**Goal:** Connect GEO dataset metadata → Citations → PDFs/Fulltext → Display on demand

**Key Insight:** We need a **lazy loading pattern** - fetch PDFs/fulltext only when user clicks, not during search.

---

## 1. Complete Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Streamlit Dashboard)                   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 1. USER INPUT                                                     │  │
│  │                                                                   │  │
│  │   [Search: "diabetes RNA-seq"]  [Database: GEO ▼]  [Search →]   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
└───────────────────────────────────┼──────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │  2. QUERY PREPROCESSING       │
                    │  (QueryAgent - Optional)      │
                    │                               │
                    │  • NER: extract entities      │
                    │  • Synonyms: diabetes →       │
                    │    "diabetes mellitus"        │
                    │  • Organisms: detect species  │
                    │                               │
                    │  Input: "diabetes RNA-seq"    │
                    │  Output: optimized query      │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  3. GEO SEARCH                │
                    │  (UnifiedSearchPipeline)      │
                    │                               │
                    │  • Check cache (Redis)        │
                    │  • Query E-utilities          │
                    │  • Fetch metadata (parallel)  │
                    │  • Rank by relevance          │
                    │                               │
                    │  Returns: List of GEO IDs     │
                    │  + metadata (NO PDFs yet)     │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌───────────────────────────────────┼──────────────────────────────────────┐
│                         FRONTEND (Results Display)                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 4. DISPLAY GEO RESULTS (Metadata Only)                           │  │
│  │                                                                   │  │
│  │  ┌────────────────────────────────────────────────────────────┐ │  │
│  │  │ GSE123456                                    Relevance: 95% │ │  │
│  │  │ "Diabetes RNA-seq in pancreatic islets"                    │ │  │
│  │  │                                                             │ │  │
│  │  │ Organism: Homo sapiens  │  Samples: 24  │  Platform: GPL123│ │  │
│  │  │                                                             │ │  │
│  │  │ Summary: This study investigates...                        │ │  │
│  │  │                                                             │ │  │
│  │  │ Publications: PMID:12345678, PMID:87654321 (2 found)       │ │  │
│  │  │                                                             │ │  │
│  │  │ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │  │
│  │  │ │ Get Citations│  │ View PDFs    │  │ View Fulltext│     │ │  │
│  │  │ └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │ │  │
│  │  │        │                  │                  │             │ │  │
│  │  │     (CLICK)            (CLICK)            (CLICK)          │ │  │
│  │  └────────┼──────────────────┼──────────────────┼─────────────┘ │  │
│  └───────────┼──────────────────┼──────────────────┼───────────────┘  │
└──────────────┼──────────────────┼──────────────────┼──────────────────┘
               │                  │                  │
               │                  │                  │
    ┌──────────▼──────────┐      │                  │
    │ 5. CITATION         │      │                  │
    │    DISCOVERY        │      │                  │
    │ (GEOCitationPipeline│      │                  │
    │                     │      │                  │
    │ • Query PubMed      │      │                  │
    │ • Extract PMIDs     │      │                  │
    │ • Get metadata      │      │                  │
    │ • Return list       │      │                  │
    │                     │      │                  │
    │ Stores: Nothing yet │      │                  │
    │ Returns: Citation   │      │                  │
    │          list       │      │                  │
    └──────────┬──────────┘      │                  │
               │                  │                  │
               ▼                  │                  │
    ┌─────────────────────┐      │                  │
    │ 6. UPDATE UI        │      │                  │
    │                     │      │                  │
    │ Show citation list: │      │                  │
    │ ✓ PMID:12345678     │      │                  │
    │ ✓ PMID:87654321     │      │                  │
    │                     │      │                  │
    │ "Get PDFs" enabled  │──────┘                  │
    └─────────────────────┘                         │
                                                    │
               ┌────────────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │ 7. PDF DOWNLOAD             │
    │    (GEOCitationPipeline)    │
    │                             │
    │ For each PMID:              │
    │ • Try Unpaywall             │
    │ • Try PMC                   │
    │ • Try publisher             │
    │ • Download PDF              │
    │ • Parse to text             │
    │ • Normalize format          │
    │                             │
    │ Stores:                     │
    │ data/pdfs/GSE123456/        │
    │   ├── PMID_12345678.pdf     │
    │   └── PMID_87654321.pdf     │
    │                             │
    │ data/fulltext/parsed/       │
    │   ├── PMID_12345678.json    │
    │   └── PMID_87654321.json    │
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │ 8. DISPLAY PDFs             │
    │                             │
    │ Show download status:       │
    │ ✓ PMID:12345678 - Downloaded│
    │ ✓ PMID:87654321 - Downloaded│
    │                             │
    │ [View PDF 1] [View PDF 2]   │
    │ [View All Fulltext]         │
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼ (User clicks "View Fulltext")
                   │
    ┌──────────────┴──────────────┐
    │ 9. FULLTEXT RETRIEVAL       │
    │    (ParsedCache)            │
    │                             │
    │ For GSE123456:              │
    │ • Load from cache:          │
    │   data/fulltext/parsed/     │
    │   PMID_12345678.json        │
    │                             │
    │ • Get normalized content:   │
    │   ParsedCache.get_normalized│
    │                             │
    │ • Return structured text:   │
    │   - Title                   │
    │   - Abstract                │
    │   - Introduction            │
    │   - Methods                 │
    │   - Results                 │
    │   - Discussion              │
    │   - Tables                  │
    │   - Figures                 │
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │ 10. DISPLAY FULLTEXT        │
    │                             │
    │ ┌─────────────────────────┐ │
    │ │ 📄 PMID:12345678        │ │
    │ │                         │ │
    │ │ Title: Diabetes and ... │ │
    │ │                         │ │
    │ │ Abstract:               │ │
    │ │ This study shows...     │ │
    │ │                         │ │
    │ │ [▼] Introduction        │ │
    │ │ [▼] Methods             │ │
    │ │ [▼] Results             │ │
    │ │ [▼] Discussion          │ │
    │ │                         │ │
    │ │ Tables:                 │ │
    │ │ [Table 1: Dataset info] │ │
    │ │                         │ │
    │ │ Figures:                │ │
    │ │ [Figure 1: Results]     │ │
    │ └─────────────────────────┘ │
    └─────────────────────────────┘
```

---

## 2. Data Flow & Storage Strategy

### Storage Locations

```
data/
├── pdfs/                          # Downloaded PDFs (organized by GEO ID)
│   └── {geo_id}/                  # e.g., GSE123456/
│       ├── PMID_{pmid}.pdf        # Original PDFs
│       ├── PMID_{pmid}.pdf        # Multiple PDFs per GEO dataset
│       └── metadata.json          # Citation metadata
│
├── fulltext/
│   └── parsed/                    # Parsed fulltext (organized by PMID)
│       ├── PMID_{pmid}.json       # Original parsed format (JATS/PDF/LaTeX)
│       └── PMID_{pmid}_normalized.json  # Normalized format (cached)
│
├── geo_citation_collections/      # Complete collections (optional)
│   └── {geo_id}/
│       ├── citations.json         # All citations for this GEO dataset
│       ├── download_status.json   # Which PDFs were downloaded
│       └── metadata.json          # Collection metadata
│
└── cache/
    └── geo_metadata/              # Cached GEO metadata (Redis or disk)
        └── GSE{number}.json
```

### Data Mapping Strategy

```
GEO Dataset (GSE123456)
│
├── Metadata (from E-utilities)
│   ├── geo_id: "GSE123456"
│   ├── title: "..."
│   ├── summary: "..."
│   ├── organism: "Homo sapiens"
│   ├── sample_count: 24
│   └── pubmed_ids: ["12345678", "87654321"]  ← Key linking field
│
└── Citations (lazy loaded)
    ├── PMID: 12345678
    │   ├── Citation metadata (from PubMed)
    │   │   ├── title
    │   │   ├── authors
    │   │   ├── journal
    │   │   └── doi
    │   │
    │   ├── PDF (from GEOCitationPipeline)
    │   │   └── Path: data/pdfs/GSE123456/PMID_12345678.pdf
    │   │
    │   └── Fulltext (from ParsedCache)
    │       ├── Original: data/fulltext/parsed/PMID_12345678.json
    │       └── Normalized: data/fulltext/parsed/PMID_12345678_normalized.json
    │
    └── PMID: 87654321
        └── (same structure)
```

---

## 3. Integration Points (What Needs to Connect)

### Current State (Disconnected)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GEO Search     │     │ PDF Download    │     │ Fulltext Parse  │
│  Returns:       │     │ Returns:        │     │ Returns:        │
│  - GEO metadata │ ✗   │ - PDF files     │ ✗   │ - Parsed text   │
│  - PMID list    │     │ - File paths    │     │ - Normalized    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     (isolated)              (isolated)              (isolated)
```

### Desired State (Connected)

```
┌─────────────────┐
│  GEO Search     │
│  GSE123456      │
│  PMIDs: [...]   │
└────────┬────────┘
         │
         │ User clicks "Get Citations"
         │
         ▼
┌─────────────────────────┐
│  Citation Discovery     │
│  Fetch citation metadata│
└────────┬────────────────┘
         │
         │ User clicks "Download PDFs"
         │
         ▼
┌─────────────────────────────────┐
│  PDF Download + Parse           │
│  1. Download PDFs               │
│  2. Parse to text               │
│  3. Normalize format            │
│  4. Store by GEO ID + PMID      │
└────────┬────────────────────────┘
         │
         │ User clicks "View Fulltext"
         │
         ▼
┌─────────────────────────────────┐
│  Fulltext Display               │
│  Load from:                     │
│  data/pdfs/GSE123456/           │
│  data/fulltext/parsed/PMID_*.json│
└─────────────────────────────────┘
```

---

## 4. Frontend Component Design

### GEO Result Card (Enhanced)

```python
# omics_oracle_v2/lib/dashboard/components.py

class GEODatasetCard:
    """Display card for a single GEO dataset with lazy-loaded content."""

    def __init__(self, dataset: GEODatasetResult):
        self.dataset = dataset
        self.citations: Optional[List[Citation]] = None
        self.pdfs_downloaded: bool = False
        self.fulltext_available: bool = False

    def render(self):
        """Render the dataset card with interactive buttons."""

        # PHASE 1: Always visible - Basic metadata
        st.markdown(f"### [{self.dataset.geo_id}](https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={self.dataset.geo_id})")
        st.markdown(f"**{self.dataset.title}**")
        st.caption(f"Organism: {self.dataset.organism} | Samples: {self.dataset.sample_count}")

        with st.expander("Summary"):
            st.write(self.dataset.summary)

        # PHASE 2: Lazy loaded - Citations
        if self.dataset.pubmed_ids:
            st.write(f"📚 Publications: {len(self.dataset.pubmed_ids)} linked")

            if st.button("🔍 Get Citations", key=f"cite_{self.dataset.geo_id}"):
                self._load_citations()

        # PHASE 3: Show citations if loaded
        if self.citations:
            self._render_citations()

        # PHASE 4: Download PDFs if citations available
        if self.citations and not self.pdfs_downloaded:
            if st.button("📥 Download PDFs", key=f"pdf_{self.dataset.geo_id}"):
                self._download_pdfs()

        # PHASE 5: View fulltext if PDFs downloaded
        if self.pdfs_downloaded:
            if st.button("📄 View Fulltext", key=f"fulltext_{self.dataset.geo_id}"):
                self._show_fulltext()

    def _load_citations(self):
        """STEP 1: Discover citations (no download yet)."""
        # Check cache first
        cache_path = f"data/geo_citation_collections/{self.dataset.geo_id}/citations.json"

        if Path(cache_path).exists():
            # Load from cache
            with open(cache_path) as f:
                self.citations = json.load(f)
            st.success(f"✓ Loaded {len(self.citations)} citations from cache")
        else:
            # Fetch from PubMed
            with st.spinner("Discovering citations..."):
                from omics_oracle_v2.lib.publications import PubMedClient

                client = PubMedClient()
                self.citations = []

                for pmid in self.dataset.pubmed_ids:
                    citation = client.get_citation(pmid)
                    self.citations.append(citation)

                # Cache for future use
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                with open(cache_path, 'w') as f:
                    json.dump(self.citations, f, indent=2)

                st.success(f"✓ Found {len(self.citations)} citations")

    def _render_citations(self):
        """STEP 2: Display citation metadata."""
        st.markdown("#### 📚 Citations")

        for i, citation in enumerate(self.citations, 1):
            with st.expander(f"{i}. PMID:{citation.pmid} - {citation.title}"):
                st.write(f"**Authors:** {citation.authors}")
                st.write(f"**Journal:** {citation.journal}")
                st.write(f"**Year:** {citation.year}")
                if citation.doi:
                    st.write(f"**DOI:** [{citation.doi}](https://doi.org/{citation.doi})")

    def _download_pdfs(self):
        """STEP 3: Download PDFs and parse to fulltext."""
        with st.spinner("Downloading PDFs and parsing fulltext..."):
            from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline

            # Use pipeline to download + parse
            pipeline = GEOCitationPipeline()
            result = asyncio.run(
                pipeline.discover_and_download(
                    geo_id=self.dataset.geo_id,
                    pmids=[c.pmid for c in self.citations]
                )
            )

            # Update state
            self.pdfs_downloaded = True
            self.fulltext_available = result.pdfs_downloaded > 0

            st.success(f"✓ Downloaded {result.pdfs_downloaded} PDFs")
            st.info(f"✓ Parsed {result.pdfs_parsed} fulltexts")

            # Show which PDFs were downloaded
            for pmid, status in result.download_status.items():
                if status == "success":
                    st.write(f"✓ PMID:{pmid} - Downloaded")
                else:
                    st.write(f"✗ PMID:{pmid} - {status}")

    def _show_fulltext(self):
        """STEP 4: Display normalized fulltext."""
        from omics_oracle_v2.lib.fulltext.cache import ParsedCache

        cache = ParsedCache()

        st.markdown("#### 📄 Fulltext")

        for citation in self.citations:
            pmid = citation.pmid

            # Get normalized content
            content = cache.get_normalized(pmid)

            if content:
                with st.expander(f"PMID:{pmid} - {citation.title}"):
                    # Display sections
                    for section in content.sections:
                        st.markdown(f"##### {section.title}")
                        st.write(section.content)

                    # Display tables
                    if content.tables:
                        st.markdown("##### Tables")
                        for table in content.tables:
                            st.dataframe(table.data)

                    # Display figures
                    if content.figures:
                        st.markdown("##### Figures")
                        for figure in content.figures:
                            st.write(f"**{figure.caption}**")
            else:
                st.warning(f"Fulltext not available for PMID:{pmid}")
```

---

## 5. State Management Strategy

### Session State Structure

```python
# Streamlit session state for dashboard

st.session_state = {
    # Search results
    "search_results": [
        {
            "geo_id": "GSE123456",
            "metadata": {...},  # From UnifiedSearchPipeline
            "citations": None,  # Lazy loaded
            "pdfs_downloaded": False,
            "fulltext_available": False,
        },
        # ... more results
    ],

    # Per-dataset state (keyed by GEO ID)
    "dataset_state": {
        "GSE123456": {
            "citations_loaded": False,
            "citations": [],
            "pdfs_downloaded": False,
            "fulltext_displayed": False,
        },
    },

    # File paths (for quick lookup)
    "file_map": {
        "GSE123456": {
            "pdfs": [
                "data/pdfs/GSE123456/PMID_12345678.pdf",
                "data/pdfs/GSE123456/PMID_87654321.pdf",
            ],
            "fulltext": [
                "data/fulltext/parsed/PMID_12345678.json",
                "data/fulltext/parsed/PMID_87654321.json",
            ],
        },
    },
}
```

### Progressive Enhancement Pattern

```python
def render_search_results(results):
    """Render results with progressive enhancement."""

    for result in results:
        geo_id = result.geo_id

        # Initialize state if needed
        if geo_id not in st.session_state.dataset_state:
            st.session_state.dataset_state[geo_id] = {
                "citations_loaded": False,
                "citations": [],
                "pdfs_downloaded": False,
                "fulltext_displayed": False,
            }

        state = st.session_state.dataset_state[geo_id]

        # Always show: Basic metadata
        render_basic_metadata(result)

        # Show if available: Citations (lazy load)
        if not state["citations_loaded"]:
            if st.button(f"Get Citations", key=f"cite_{geo_id}"):
                load_citations(geo_id, result.pubmed_ids)
                state["citations_loaded"] = True
        else:
            render_citations(state["citations"])

        # Show if citations loaded: PDF download
        if state["citations_loaded"] and not state["pdfs_downloaded"]:
            if st.button(f"Download PDFs", key=f"pdf_{geo_id}"):
                download_pdfs(geo_id, state["citations"])
                state["pdfs_downloaded"] = True

        # Show if PDFs downloaded: Fulltext viewer
        if state["pdfs_downloaded"]:
            if st.button(f"View Fulltext", key=f"fulltext_{geo_id}"):
                show_fulltext(geo_id)
                state["fulltext_displayed"] = True
```

---

## 6. Implementation Plan (Step-by-Step)

### Phase 1: Update Dashboard Search (2-3 hours)

**Goal:** Dashboard uses UnifiedSearchPipeline/SearchAgent

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py`

**Changes:**
```python
# Replace PublicationSearchPipeline with SearchAgent
from omics_oracle_v2.agents import SearchAgent
from omics_oracle_v2.agents.models.search import SearchInput

# In _execute_search method:
agent = SearchAgent(
    settings=st.session_state.settings,
    enable_publications=(params["database"] == "publications")
)

search_input = SearchInput(
    search_terms=[query],
    original_query=query,
    max_results=params["max_results"],
    organism=params.get("organism"),
)

result = agent.execute(search_input)
search_results = result.output.datasets
```

**Test:**
```bash
./start_omics_oracle.sh
# Navigate to http://localhost:8502
# Search "diabetes"
# Verify GEO datasets displayed
```

### Phase 2: Add GEO Dataset Display (2 hours)

**Goal:** Show GEO datasets with metadata

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/components.py`

**Changes:**
```python
class GEODatasetCard:
    def render(self, dataset):
        st.markdown(f"### {dataset.geo_id}")
        st.markdown(f"**{dataset.title}**")
        st.caption(f"Organism: {dataset.organism} | Samples: {dataset.sample_count}")

        with st.expander("Summary"):
            st.write(dataset.summary)

        # Show linked publications
        if dataset.pubmed_ids:
            st.write(f"📚 {len(dataset.pubmed_ids)} publications linked")
```

**Test:**
```bash
# Search "diabetes"
# Verify: GEO datasets show with metadata
# Verify: PMID count displayed
```

### Phase 3: Add Citation Discovery (2 hours)

**Goal:** Fetch citation metadata on button click

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py`
- `omics_oracle_v2/lib/dashboard/components.py`

**Changes:**
```python
def _get_citations(self, geo_id: str, pmids: List[str]):
    """Discover and display citation metadata."""
    from omics_oracle_v2.lib.publications import PubMedClient

    client = PubMedClient()
    citations = []

    for pmid in pmids:
        citation = client.get_citation(pmid)
        citations.append(citation)

    # Store in session state
    st.session_state.dataset_state[geo_id]["citations"] = citations
    st.session_state.dataset_state[geo_id]["citations_loaded"] = True

    return citations
```

**Test:**
```bash
# Search "diabetes"
# Click "Get Citations" on a result
# Verify: Citation list displayed with titles, authors, DOIs
```

### Phase 4: Add PDF Download (3 hours)

**Goal:** Download PDFs and parse to fulltext

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py`

**Changes:**
```python
def _download_pdfs(self, geo_id: str, citations: List[Citation]):
    """Download PDFs and parse fulltext."""
    from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline

    pipeline = GEOCitationPipeline()

    # Download + parse
    result = asyncio.run(
        pipeline.discover_and_download(
            geo_id=geo_id,
            pmids=[c.pmid for c in citations]
        )
    )

    # Update state
    st.session_state.dataset_state[geo_id]["pdfs_downloaded"] = True
    st.session_state.dataset_state[geo_id]["download_status"] = result.download_status

    return result
```

**Test:**
```bash
# Search "diabetes"
# Click "Get Citations"
# Click "Download PDFs"
# Verify: PDFs downloaded to data/pdfs/GSE*/
# Verify: Fulltext parsed to data/fulltext/parsed/
```

### Phase 5: Add Fulltext Viewer (2 hours)

**Goal:** Display normalized fulltext on demand

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/components.py`

**Changes:**
```python
def _show_fulltext(self, geo_id: str, pmid: str):
    """Display normalized fulltext."""
    from omics_oracle_v2.lib.fulltext.cache import ParsedCache

    cache = ParsedCache()
    content = cache.get_normalized(pmid)

    if content:
        # Display sections
        for section in content.sections:
            st.markdown(f"#### {section.title}")
            st.write(section.content)

        # Display tables
        if content.tables:
            st.markdown("#### Tables")
            for table in content.tables:
                st.dataframe(table.data)
    else:
        st.warning("Fulltext not available")
```

**Test:**
```bash
# Search "diabetes"
# Click "Get Citations"
# Click "Download PDFs"
# Click "View Fulltext"
# Verify: Normalized content displayed with sections, tables, figures
```

---

## 7. My Understanding (Summary)

### What I Understand:

1. **Current Disconnect:**
   - GEO search returns metadata (geo_id, title, summary, **PMIDs**)
   - PMIDs are the **linking key** to citations/PDFs/fulltext
   - But dashboard doesn't use PMIDs to fetch related content
   - User sees GEO datasets but can't access the linked papers

2. **What Needs to Connect:**
   ```
   GEO Dataset (GSE123456)
        │
        ├─ metadata (title, summary, organism)  ← Already displayed
        │
        └─ pubmed_ids: [12345678, 87654321]     ← KEY LINKING FIELD
             │
             ├─ Citation 1 (PMID:12345678)
             │    ├─ Metadata (title, authors, journal)
             │    ├─ PDF: data/pdfs/GSE123456/PMID_12345678.pdf
             │    └─ Fulltext: data/fulltext/parsed/PMID_12345678.json
             │
             └─ Citation 2 (PMID:87654321)
                  ├─ Metadata
                  ├─ PDF
                  └─ Fulltext
   ```

3. **Lazy Loading Strategy:**
   - **Step 1:** Show GEO metadata (fast - from search)
   - **Step 2:** User clicks "Get Citations" → Fetch citation metadata (medium speed)
   - **Step 3:** User clicks "Download PDFs" → Download + parse (slow - 10-30s)
   - **Step 4:** User clicks "View Fulltext" → Display from cache (fast)

4. **Why Lazy Loading?**
   - Don't download PDFs for ALL search results (wasteful)
   - User might only be interested in 1-2 datasets
   - Keep search fast (<5 seconds)
   - Download PDFs only on demand (when user explicitly requests)

5. **Storage Mapping:**
   - **By GEO ID:** data/pdfs/GSE123456/ (all PDFs for this dataset)
   - **By PMID:** data/fulltext/parsed/PMID_*.json (parsed content by paper)
   - **Link:** GEO dataset → PMIDs → PDF files + fulltext files

### Implementation Priority:

1. **HIGH:** Connect dashboard to UnifiedSearchPipeline (enable GEO search)
2. **HIGH:** Display GEO metadata + PMID count
3. **MEDIUM:** Add "Get Citations" button (fetch metadata only)
4. **MEDIUM:** Add "Download PDFs" button (download + parse)
5. **MEDIUM:** Add "View Fulltext" button (display normalized content)
6. **LOW:** Add batch operations (download all PDFs for a dataset)
7. **LOW:** Add export options (export fulltext as PDF, CSV, etc.)

### Questions to Confirm:

1. **Do we download PDFs for ALL search results automatically?**
   - **My recommendation:** NO - only on user request (lazy loading)
   - **Reason:** Saves bandwidth, storage, time

2. **Do we store fulltext by GEO ID or PMID?**
   - **My recommendation:** By PMID (more flexible - one paper can link to multiple GEO datasets)
   - **But also maintain mapping:** data/geo_citation_collections/GSE*/citations.json

3. **Do we show fulltext inline or in a modal/new page?**
   - **My recommendation:** Streamlit expander (collapsible section)
   - **Alternative:** New page with tabs (Abstract, Methods, Results, etc.)

4. **Do we cache citation metadata to avoid repeated PubMed queries?**
   - **My recommendation:** YES - cache in data/geo_citation_collections/
   - **TTL:** Long (citations don't change often) - 30 days

Is this understanding correct? Should I proceed with implementing the dashboard integration with this lazy loading approach?
