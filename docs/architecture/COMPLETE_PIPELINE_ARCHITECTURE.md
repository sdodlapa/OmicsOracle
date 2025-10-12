# Complete Pipeline Architecture: Frontend → Backend → Storage → Display

**Created:** October 12, 2025  
**Purpose:** Map the complete data flow from user query to GEO-specific fulltext/PDF display

---

## Executive Summary

This document maps the **complete end-to-end pipeline** for how a user query flows through the system:

1. **Frontend** (User Interface) → sends query
2. **API Layer** (FastAPI routes) → receives request
3. **Agent/Workflow Layer** (Orchestration) → coordinates processing
4. **Pipeline Layer** (Business Logic) → executes search & collection
5. **Storage Layer** (File System) → saves PDFs/fulltext
6. **Database Layer** (SQLite/Redis) → caches metadata
7. **Display Layer** (Frontend API) → returns GEO-specific results

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Diagram](#data-flow-diagram)
3. [Layer-by-Layer Breakdown](#layer-by-layer-breakdown)
4. [File Organization](#file-organization)
5. [GEO ID → PDF/Fulltext Mapping](#geo-id-pdf-fulltext-mapping)
6. [API Endpoints](#api-endpoints)
7. [Storage Structure](#storage-structure)
8. [Integration Points](#integration-points)
9. [Example Flows](#example-flows)

---

## System Overview

### Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND LAYER                         │
│  (Not implemented yet - future React/Vue/Streamlit)     │
│  - Search interface                                      │
│  - Results display (GEO datasets + PDFs/fulltext)       │
│  - Dataset detail view (GEO-specific)                   │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                    API LAYER                             │
│  omics_oracle_v2/api/                                   │
│  - FastAPI (main.py)                                    │
│  - Routes: /api/v1/workflows/execute                    │
│  - Routes: /api/v1/agents/search                        │
│  - Authentication (JWT)                                  │
│  - Rate limiting (Redis)                                 │
└─────────────────────────────────────────────────────────┘
                          ↓ Function Calls
┌─────────────────────────────────────────────────────────┐
│                  AGENT/WORKFLOW LAYER                    │
│  omics_oracle_v2/agents/                                │
│  - Orchestrator (multi-agent coordination)              │
│  - QueryAgent (NLP entity extraction)                   │
│  - SearchAgent (GEO + citation search)                  │
│  - DataAgent (quality validation)                       │
│  - ReportAgent (result formatting)                      │
└─────────────────────────────────────────────────────────┘
                          ↓ Delegates to
┌─────────────────────────────────────────────────────────┐
│                    PIPELINE LAYER                        │
│  omics_oracle_v2/lib/pipelines/                         │
│  - GEOCitationPipeline (main: GEO → citations → PDFs)  │
│  - UnifiedSearchPipeline (search orchestration)         │
│  - PublicationSearchPipeline (publication search)       │
└─────────────────────────────────────────────────────────┘
                          ↓ Uses
┌─────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                          │
│  omics_oracle_v2/lib/storage/                           │
│  - PDFDownloadManager (async PDF downloads)             │
│  omics_oracle_v2/lib/fulltext/                          │
│  - ParsedCache (fulltext caching)                       │
│  - ContentNormalizer (format unification)               │
└─────────────────────────────────────────────────────────┘
                          ↓ Saves to
┌─────────────────────────────────────────────────────────┐
│                 FILE SYSTEM (data/)                      │
│  data/pdfs/{geo_id}/                    <- PDFs          │
│  data/fulltext/pdf/{source}/            <- PDFs          │
│  data/fulltext/parsed/                  <- JSON cache    │
│  data/geo_citation_collections/{geo_id}/<- Collections   │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Complete Query Flow (User → Results)

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                                     │
│    Query: "breast cancer gene expression"                        │
│    Filters: organism=human, study_type=expression               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (Future)                                              │
│    POST /api/v1/workflows/execute                                │
│    {                                                              │
│      "query": "breast cancer gene expression",                   │
│      "workflow_type": "full_analysis",                           │
│      "max_results": 10                                           │
│    }                                                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. API ROUTES (omics_oracle_v2/api/routes/workflows.py)         │
│    - Validates request                                           │
│    - Checks authentication (JWT)                                 │
│    - Applies rate limiting (Redis)                               │
│    - Calls: orchestrator.execute(input)                         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. ORCHESTRATOR (omics_oracle_v2/agents/orchestrator.py)        │
│    Workflow: full_analysis                                       │
│    Stages:                                                       │
│      → QueryAgent.process(query)       # Extract entities        │
│      → SearchAgent.search(entities)    # Find GEO datasets       │
│      → DataAgent.validate(datasets)    # Quality check           │
│      → ReportAgent.generate(results)   # Format response         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. QUERY AGENT (omics_oracle_v2/agents/query_agent.py)          │
│    Input: "breast cancer gene expression"                       │
│    Output:                                                       │
│      entities: [                                                │
│        {type: "disease", text: "breast cancer"},                │
│        {type: "assay", text: "gene expression"}                 │
│      ]                                                           │
│      search_terms: ["breast neoplasms", "RNA-seq", ...]        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. SEARCH AGENT (omics_oracle_v2/agents/search_agent.py)        │
│    Uses: UnifiedSearchPipeline                                   │
│    Calls: pipeline.search(query, max_results=10)                │
│                                                                   │
│    Pipeline delegates to:                                        │
│      → GEOClient.search(query) -> [GSE123, GSE456, ...]         │
│      → GEOClient.batch_get_metadata(geo_ids)                    │
│                                                                   │
│    Returns: [                                                    │
│      GEOSeriesMetadata(geo_id="GSE123", title="...", ...)       │
│    ]                                                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. CITATION DISCOVERY (GEOCitationPipeline)                     │
│    For each GEO dataset:                                         │
│      → Extract PMID from metadata.pubmed_ids                    │
│      → CitationClient.get_citations(pmid)                       │
│      → FullTextManager.get_fulltext(publication)                │
│                                                                   │
│    Sources tried (waterfall):                                    │
│      1. PMC XML (if pmcid available)                            │
│      2. Institutional Access (if configured)                     │
│      3. Unpaywall PDF (DOI required)                            │
│      4. OpenAlex PDF                                             │
│      5. CORE PDF                                                 │
│      6. bioRxiv/arXiv PDF                                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. PDF DOWNLOAD (PDFDownloadManager)                            │
│    Input: List[Publication] with pdf_url                        │
│                                                                   │
│    For each publication:                                         │
│      → download_single(url, output_dir)                         │
│      → Validate PDF (check %PDF- magic bytes)                   │
│      → Save to: data/pdfs/{geo_id}/{pmid}.pdf                   │
│      → Update publication.pdf_path                               │
│                                                                   │
│    Output: DownloadReport(successful=8, failed=2, ...)          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 9. FULLTEXT EXTRACTION (Future - Phase 5)                       │
│    For each downloaded PDF:                                      │
│      → PDFExtractor.extract(pdf_path)                           │
│      → ContentNormalizer.normalize(content)                     │
│      → ParsedCache.save(publication_id, content)                │
│                                                                   │
│    Saves to:                                                     │
│      data/fulltext/parsed/{publication_id}.json.gz              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 10. COLLECTION STORAGE                                           │
│     GEOCitationPipeline saves complete results:                 │
│                                                                   │
│     data/geo_citation_collections/{geo_id}/                     │
│       ├── collection.json          # Complete metadata           │
│       ├── citations.json           # Citation graph              │
│       ├── pdfs/                    # Downloaded PDFs             │
│       │   ├── PMID12345.pdf                                     │
│       │   └── PMID67890.pdf                                     │
│       └── fulltext/                # Extracted fulltext          │
│           ├── PMID12345.json.gz                                 │
│           └── PMID67890.json.gz                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 11. REPORT AGENT (Formats Response)                             │
│     Aggregates:                                                  │
│       - GEO metadata (from SearchAgent)                         │
│       - Citation counts (from CitationClient)                   │
│       - PDF paths (from PDFDownloadManager)                     │
│       - Fulltext availability (from ParsedCache)                │
│                                                                   │
│     Creates structured response:                                 │
│       {                                                          │
│         "datasets": [                                            │
│           {                                                      │
│             "geo_id": "GSE123",                                  │
│             "title": "...",                                      │
│             "citations": [...],                                  │
│             "pdfs": ["data/pdfs/GSE123/PMID12345.pdf"],         │
│             "fulltext_available": true                           │
│           }                                                      │
│         ]                                                        │
│       }                                                          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 12. API RESPONSE                                                 │
│     Returns to frontend:                                         │
│     {                                                            │
│       "success": true,                                           │
│       "workflow_type": "full_analysis",                         │
│       "results": {                                               │
│         "datasets": [...],                                       │
│         "report": "...",                                         │
│         "stage_results": [...]                                   │
│       }                                                          │
│     }                                                            │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 13. FRONTEND DISPLAY (Future)                                    │
│     For each GEO dataset:                                        │
│       ┌──────────────────────────────────────┐                  │
│       │ GSE123456: Breast Cancer Study       │                  │
│       │ Organism: Homo sapiens               │                  │
│       │ Samples: 48                          │                  │
│       │                                       │                  │
│       │ Citations (5):                       │                  │
│       │  [PDF] PMID12345 - Original paper    │ <- Click opens PDF│
│       │  [PDF] PMID67890 - Follow-up study   │                  │
│       │  [View] PMID11111 - Citation #3      │                  │
│       │                                       │                  │
│       │ [View Fulltext] [Download PDFs]      │                  │
│       └──────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 1: Frontend (Future - Not Implemented)

**Location:** Will be separate React/Vue app or Streamlit dashboard

**Responsibilities:**
- User authentication (login/register)
- Search interface (query input + filters)
- Results display (GEO dataset cards)
- GEO detail view (expandable with citations/PDFs)
- PDF viewer (inline or download)
- Fulltext viewer (formatted text display)

**API Calls:**
```javascript
// Search for GEO datasets
POST /api/v1/workflows/execute
{
  "query": "diabetes gene expression",
  "workflow_type": "full_analysis",
  "max_results": 10
}

// Get GEO-specific details (including PDFs/fulltext)
GET /api/v1/agents/search/geo/{geo_id}

// Download PDF
GET /api/v1/files/pdf/{geo_id}/{pmid}

// View fulltext
GET /api/v1/fulltext/{publication_id}
```

---

### Layer 2: API Layer

**Location:** `omics_oracle_v2/api/`

#### Files:
```
omics_oracle_v2/api/
├── main.py                  # FastAPI app factory
├── routes/
│   ├── workflows.py         # Workflow orchestration endpoints
│   ├── agents.py            # Individual agent endpoints
│   ├── auth.py              # Authentication endpoints
│   └── health.py            # Health check endpoints
├── dependencies.py          # Dependency injection
├── middleware.py            # Request logging, error handling
└── models/
    ├── requests.py          # Request schemas
    └── responses.py         # Response schemas
```

#### Key Endpoints:

**Workflow Execution:**
```python
POST /api/v1/workflows/execute
- Executes complete workflow (Query -> Search -> Validate -> Report)
- Returns: WorkflowResponse with datasets, citations, PDFs

GET /api/v1/workflows/
- Lists available workflows
```

**Individual Agents:**
```python
POST /api/v1/agents/query
- Extract entities from query
- Returns: QueryResponse with entities

POST /api/v1/agents/search
- Search GEO datasets
- Returns: SearchResponse with GEO datasets

GET /api/v1/agents/search/geo/{geo_id}
- Get specific GEO dataset with citations/PDFs
- Returns: GEO metadata + citation list + PDF paths
```

---

### Layer 3: Agent/Workflow Layer

**Location:** `omics_oracle_v2/agents/`

#### Files:
```
omics_oracle_v2/agents/
├── orchestrator.py          # Multi-agent coordinator
├── query_agent.py           # NLP entity extraction
├── search_agent.py          # GEO + citation search
├── data_agent.py            # Quality validation
├── report_agent.py          # Result formatting
└── models/
    ├── orchestrator.py      # Workflow definitions
    ├── query.py             # Query models
    ├── search.py            # Search models
    └── report.py            # Report models
```

#### Workflow Types:

**1. full_analysis** (Most Common)
```
Query -> Search -> Validate -> Report
- QueryAgent: Extract entities from natural language
- SearchAgent: Find GEO datasets + citations
- DataAgent: Validate dataset quality
- ReportAgent: Format comprehensive report
```

**2. simple_search** (Faster)
```
Query -> Search -> Report
- Skip quality validation for speed
```

**3. quick_report** (Direct GEO IDs)
```
Search -> Report
- Use when you already have GEO IDs
```

**4. data_validation**
```
Validate -> Report
- Quality analysis only
```

---

### Layer 4: Pipeline Layer

**Location:** `omics_oracle_v2/lib/pipelines/`

#### Key Pipelines:

**1. GEOCitationPipeline** (Main: GEO → Citations → PDFs)
```python
File: omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py

Class: GEOCitationPipeline

Purpose: Connect GEO datasets to their citations and download PDFs

Flow:
1. Input: GEO ID (e.g., "GSE123456")
2. Get GEO metadata (title, samples, pubmed_ids)
3. For each PMID:
   a. Get citation metadata
   b. Get citing papers (who cited this?)
   c. Get fulltext (PMC XML or PDF)
4. Save collection to: data/geo_citation_collections/{geo_id}/

Output: CollectionResult
- geo_metadata: GEOSeriesMetadata
- publications: List[Publication]
- citation_graph: Dict
- pdfs_downloaded: int
- storage_path: Path
```

**2. UnifiedSearchPipeline** (Search Orchestration)
```python
File: omics_oracle_v2/lib/pipelines/unified_search_pipeline.py

Class: OmicsSearchPipeline

Purpose: Search GEO + Publications + unified results

Flow:
1. Input: Query string
2. Route query:
   - If "GSE123456" -> Direct GEO ID lookup
   - Else -> GEO keyword search
3. Batch fetch metadata for all GEO IDs
4. Cache results (Redis, 1 hour TTL)

Output: SearchResult
- geo_datasets: List[GEOSeriesMetadata]
- publications: List[Publication]
- query_metadata: Dict
```

**3. PublicationSearchPipeline** (Publications Only)
```python
File: omics_oracle_v2/lib/pipelines/publication_pipeline.py

Class: PublicationSearchPipeline

Purpose: Search publications (PubMed, Semantic Scholar, etc.)

Flow:
1. Input: Query
2. Search PubMed
3. Get metadata (DOI, PMID, abstract)
4. Download PDFs (if enabled)
5. Extract fulltext (if enabled)

Output: List[PublicationSearchResult]
```

---

### Layer 5: Storage Layer

**Location:** `omics_oracle_v2/lib/storage/` and `omics_oracle_v2/lib/fulltext/`

#### PDF Download Manager

```python
File: omics_oracle_v2/lib/storage/pdf/download_manager.py

Class: PDFDownloadManager

Purpose: Async PDF download with validation

Features:
- Parallel downloads (configurable concurrency)
- PDF validation (magic bytes check)
- Retry logic (max 3 retries)
- Progress tracking

Usage:
downloader = PDFDownloadManager(max_concurrent=5)
report = await downloader.download_batch(
    publications=pubs,
    output_dir=Path("data/pdfs/GSE123"),
    url_field="pdf_url"
)

Output: DownloadReport
- total: 10
- successful: 8
- failed: 2
- results: List[DownloadResult]
```

#### Parsed Content Cache

```python
File: omics_oracle_v2/lib/fulltext/parsed_cache.py

Class: ParsedCache

Purpose: Cache parsed PDF/XML content (avoid re-parsing)

Features:
- JSON storage (human-readable)
- Compression (gzip)
- 90-day TTL
- Metadata tracking

Usage:
cache = ParsedCache()

# Check cache first
cached = await cache.get(publication_id)
if cached:
    return cached

# Parse and save
content = parse_pdf(pdf_path)
await cache.save(publication_id, content)

Storage:
data/fulltext/parsed/{publication_id}.json.gz
```

#### Content Normalizer (Phase 5 - New!)

```python
File: omics_oracle_v2/lib/fulltext/normalizer.py

Class: ContentNormalizer

Purpose: Convert all formats (JATS XML, PDF, LaTeX) to unified structure

Usage:
normalizer = ContentNormalizer()
normalized = normalizer.normalize(content)

# Or via cache (auto-normalizes)
cache = ParsedCache()
normalized = await cache.get_normalized(publication_id)

Output: Unified format
{
  "metadata": {...},
  "text": {
    "title": "...",
    "abstract": "...",
    "sections": {"introduction": "...", ...}
  },
  "tables": [...],
  "figures": [...],
  "references": [...]
}
```

---

## File Organization

### Complete Directory Structure

```
OmicsOracle/
├── omics_oracle_v2/                    # Source code
│   ├── api/                            # FastAPI application
│   │   ├── main.py                     # App factory
│   │   ├── routes/                     # API endpoints
│   │   │   ├── workflows.py            # Workflow orchestration
│   │   │   ├── agents.py               # Agent execution
│   │   │   └── ...
│   │   └── models/                     # Request/response schemas
│   │
│   ├── agents/                         # Multi-agent system
│   │   ├── orchestrator.py             # Workflow coordinator
│   │   ├── query_agent.py              # NLP processing
│   │   ├── search_agent.py             # Search orchestration
│   │   └── ...
│   │
│   └── lib/                            # Core libraries
│       ├── geo/                        # GEO client
│       │   ├── client.py               # GEO API client
│       │   └── models.py               # GEO data models
│       │
│       ├── citations/                  # Citation management
│       │   ├── pubmed.py               # PubMed client
│       │   ├── semantic_scholar.py     # S2 client
│       │   └── ...
│       │
│       ├── fulltext/                   # Full-text extraction
│       │   ├── manager.py              # Fulltext manager
│       │   ├── parsed_cache.py         # Parse cache
│       │   ├── normalizer.py           # Format normalizer (NEW!)
│       │   └── ...
│       │
│       ├── storage/                    # Storage management
│       │   └── pdf/
│       │       └── download_manager.py # PDF downloader
│       │
│       └── pipelines/                  # Business logic
│           ├── geo_citation_pipeline.py    # Main pipeline
│           ├── unified_search_pipeline.py  # Search pipeline
│           └── publication_pipeline.py     # Publication pipeline
│
└── data/                               # Application data
    ├── pdfs/                           # Downloaded PDFs (by GEO ID)
    │   ├── GSE123456/                  # GEO-specific directory
    │   │   ├── PMID12345.pdf           # Original paper
    │   │   ├── PMID67890.pdf           # Citing paper 1
    │   │   └── PMID11111.pdf           # Citing paper 2
    │   └── GSE789012/
    │       └── ...
    │
    ├── fulltext/                       # Full-text content
    │   ├── pdf/                        # PDFs (by source)
    │   │   ├── pmc/                    # From PMC
    │   │   ├── unpaywall/              # From Unpaywall
    │   │   ├── arxiv/                  # From arXiv
    │   │   └── ...
    │   │
    │   └── parsed/                     # Parsed content cache
    │       ├── PMC12345.json.gz        # Cached parsed content
    │       ├── PMC67890.json.gz
    │       └── ...
    │
    ├── geo_citation_collections/       # Complete GEO collections
    │   ├── GSE123456/                  # Collection for GSE123456
    │   │   ├── collection.json         # Complete metadata
    │   │   ├── citations.json          # Citation graph
    │   │   ├── pdfs/                   # Downloaded PDFs
    │   │   │   ├── PMID12345.pdf
    │   │   │   └── PMID67890.pdf
    │   │   └── fulltext/               # Extracted fulltext
    │   │       ├── PMID12345.json.gz
    │   │       └── PMID67890.json.gz
    │   └── ...
    │
    ├── cache/                          # Redis/file cache
    ├── embeddings/                     # Vector embeddings
    └── vector_db/                      # Vector database
```

---

## GEO ID → PDF/Fulltext Mapping

### How to Connect GEO Datasets to PDFs/Fulltext

#### Current Implementation

**Step 1: Get GEO Metadata**
```python
from omics_oracle_v2.lib.geo.client import GEOClient

client = GEOClient()
metadata = await client.get_metadata("GSE123456")

# Extract PMIDs
pmids = metadata.pubmed_ids  # ["12345", "67890"]
```

**Step 2: Get Citations**
```python
from omics_oracle_v2.lib.citations.pubmed import PubMedClient

pm_client = PubMedClient()
citations = await pm_client.get_citations(pmids[0])
```

**Step 3: Download PDFs**
```python
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

downloader = PDFDownloadManager()
report = await downloader.download_batch(
    publications=publications,
    output_dir=Path(f"data/pdfs/GSE123456"),
    url_field="pdf_url"
)
```

**Step 4: Cache Fulltext**
```python
from omics_oracle_v2.lib.fulltext.parsed_cache import ParsedCache

cache = ParsedCache()

for pub in publications:
    if pub.pdf_path:
        # Parse PDF
        content = parse_pdf(pub.pdf_path)
        
        # Normalize format
        normalized = await cache.get_normalized(pub.pmid)
        
        # Save to cache
        await cache.save(pub.pmid, normalized)
```

#### Complete Mapping Structure

```python
# In-memory data structure for frontend
geo_dataset = {
    "geo_id": "GSE123456",
    "title": "Breast Cancer Gene Expression Study",
    "organism": "Homo sapiens",
    "samples": 48,
    "platform": "GPL570",
    
    # Original publication
    "publication": {
        "pmid": "12345",
        "title": "Original paper title",
        "pdf_path": "data/pdfs/GSE123456/PMID12345.pdf",
        "fulltext_path": "data/fulltext/parsed/PMID12345.json.gz",
        "fulltext_available": True
    },
    
    # Citing papers
    "citations": [
        {
            "pmid": "67890",
            "title": "Follow-up study",
            "pdf_path": "data/pdfs/GSE123456/PMID67890.pdf",
            "fulltext_path": "data/fulltext/parsed/PMID67890.json.gz",
            "fulltext_available": True
        },
        {
            "pmid": "11111",
            "title": "Third paper",
            "pdf_path": None,  # PDF not available
            "fulltext_available": False
        }
    ],
    
    # Collection path (all files together)
    "collection_path": "data/geo_citation_collections/GSE123456/"
}
```

---

## API Endpoints

### Frontend Integration Endpoints

**1. Execute Complete Workflow**
```
POST /api/v1/workflows/execute
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "query": "breast cancer gene expression",
  "workflow_type": "full_analysis",
  "max_results": 10,
  "organisms": ["Homo sapiens"],
  "include_quality_analysis": true
}

Response:
{
  "success": true,
  "workflow_type": "full_analysis",
  "query": "breast cancer gene expression",
  "results": {
    "datasets": [
      {
        "geo_id": "GSE123456",
        "title": "...",
        "organism": "Homo sapiens",
        "samples": 48,
        "quality_score": 0.85,
        "publication": {
          "pmid": "12345",
          "title": "...",
          "pdf_available": true,
          "pdf_path": "/api/v1/files/pdf/GSE123456/PMID12345"
        },
        "citations": [...]
      }
    ],
    "report": "...",
    "summary": {
      "total_datasets": 10,
      "pdfs_downloaded": 15,
      "fulltext_available": 12
    }
  }
}
```

**2. Get GEO-Specific Details**
```
GET /api/v1/datasets/geo/{geo_id}
Authorization: Bearer {token}

Response:
{
  "geo_id": "GSE123456",
  "metadata": {...},
  "publication": {...},
  "citations": [...],
  "pdfs": [
    {
      "pmid": "12345",
      "title": "...",
      "download_url": "/api/v1/files/pdf/GSE123456/PMID12345",
      "fulltext_url": "/api/v1/fulltext/PMID12345"
    }
  ],
  "collection_path": "data/geo_citation_collections/GSE123456/"
}
```

**3. Download PDF**
```
GET /api/v1/files/pdf/{geo_id}/{pmid}
Authorization: Bearer {token}

Response:
Content-Type: application/pdf
Content-Disposition: attachment; filename="PMID12345.pdf"

<PDF binary data>
```

**4. View Fulltext**
```
GET /api/v1/fulltext/{publication_id}
Authorization: Bearer {token}

Response:
{
  "publication_id": "PMID12345",
  "source_format": "jats_xml",
  "normalized_version": "1.0",
  "text": {
    "title": "...",
    "abstract": "...",
    "sections": {
      "introduction": "...",
      "methods": "...",
      "results": "...",
      "discussion": "..."
    }
  },
  "tables": [...],
  "figures": [...],
  "references": [...]
}
```

---

## Storage Structure

### GEO Collection Storage

Each GEO dataset gets its own collection directory:

```
data/geo_citation_collections/GSE123456/
├── collection.json              # Master collection file
├── citations.json               # Citation graph
├── geo_metadata.json            # GEO dataset metadata
├── pdfs/                        # Downloaded PDFs
│   ├── PMID12345.pdf            # Original paper
│   ├── PMID67890.pdf            # Citing paper 1
│   └── PMID11111.pdf            # Citing paper 2
└── fulltext/                    # Extracted fulltext
    ├── PMID12345.json.gz        # Normalized fulltext
    ├── PMID67890.json.gz
    └── PMID11111.json.gz
```

**collection.json Format:**
```json
{
  "geo_id": "GSE123456",
  "created_at": "2025-10-12T10:30:00Z",
  "updated_at": "2025-10-12T11:00:00Z",
  "query": "breast cancer gene expression",
  "geo_metadata": {
    "title": "Breast Cancer Gene Expression Study",
    "organism": "Homo sapiens",
    "samples": 48,
    "platform": "GPL570",
    "pubmed_ids": ["12345"]
  },
  "publications": [
    {
      "pmid": "12345",
      "title": "Original paper",
      "doi": "10.1234/journal.2025.001",
      "pdf_path": "pdfs/PMID12345.pdf",
      "fulltext_path": "fulltext/PMID12345.json.gz",
      "is_original": true
    },
    {
      "pmid": "67890",
      "title": "Citing paper",
      "pdf_path": "pdfs/PMID67890.pdf",
      "fulltext_path": "fulltext/PMID67890.json.gz",
      "is_original": false,
      "cites_pmid": "12345"
    }
  ],
  "statistics": {
    "total_publications": 3,
    "pdfs_downloaded": 2,
    "fulltext_available": 2
  }
}
```

---

## Integration Points

### How Frontend Will Access Data

#### Option 1: Direct File Access (Not Recommended)
```javascript
// BAD: Don't access files directly
const pdfPath = `data/pdfs/GSE123456/PMID12345.pdf`;
```

#### Option 2: API-Based Access (Recommended)
```javascript
// GOOD: Use API endpoints
const response = await fetch(`/api/v1/datasets/geo/GSE123456`, {
  headers: { Authorization: `Bearer ${token}` }
});

const dataset = await response.json();

// Display dataset with PDFs
dataset.pdfs.forEach(pdf => {
  console.log(pdf.download_url);  // /api/v1/files/pdf/GSE123456/PMID12345
});
```

#### Option 3: Collection-Based Access
```javascript
// Get complete collection
const response = await fetch(
  `/api/v1/collections/geo/GSE123456`,
  { headers: { Authorization: `Bearer ${token}` } }
);

const collection = await response.json();

// Collection includes:
// - GEO metadata
// - All publications
// - All PDF paths
// - All fulltext paths
// - Citation graph
```

---

## Example Flows

### Example 1: Search → Display PDFs

**User Action:** Search for "diabetes gene expression"

**Backend Flow:**
```
1. Frontend sends: POST /api/v1/workflows/execute
   {query: "diabetes gene expression"}

2. Orchestrator executes workflow:
   - QueryAgent extracts entities
   - SearchAgent finds GEO datasets
   - For each GEO dataset:
     * Get metadata
     * Find citations
     * Download PDFs
   - ReportAgent formats response

3. Response includes:
   {
     datasets: [
       {
         geo_id: "GSE123",
         pdfs: [
           {download_url: "/api/v1/files/pdf/GSE123/PMID12345"}
         ]
       }
     ]
   }

4. Frontend displays:
   - GEO dataset card
   - "View PDFs" button
   - Click opens: /api/v1/files/pdf/GSE123/PMID12345
```

### Example 2: GEO Detail Page

**User Action:** Click on GEO dataset "GSE123456"

**Backend Flow:**
```
1. Frontend sends: GET /api/v1/datasets/geo/GSE123456

2. Backend:
   - Load collection.json from:
     data/geo_citation_collections/GSE123456/collection.json
   - Return GEO metadata + PDFs + fulltext

3. Response:
   {
     geo_id: "GSE123456",
     title: "...",
     pdfs: [
       {
         pmid: "12345",
         title: "Original paper",
         download_url: "/api/v1/files/pdf/GSE123456/PMID12345",
         fulltext_url: "/api/v1/fulltext/PMID12345"
       }
     ]
   }

4. Frontend displays:
   ┌────────────────────────────────┐
   │ GSE123456                      │
   │ Breast Cancer Study            │
   │                                │
   │ Publications:                  │
   │  [PDF] Original paper          │ <- Opens PDF
   │  [Text] View fulltext          │ <- Opens formatted text
   │  [PDF] Citing paper 1          │
   │  [PDF] Citing paper 2          │
   └────────────────────────────────┘
```

### Example 3: View Fulltext

**User Action:** Click "View fulltext" for PMID12345

**Backend Flow:**
```
1. Frontend sends: GET /api/v1/fulltext/PMID12345

2. Backend:
   - Check ParsedCache for PMID12345
   - If cached: return normalized content
   - If not cached:
     * Parse PDF
     * Normalize format
     * Cache result
     * Return normalized content

3. Response:
   {
     text: {
       title: "...",
       abstract: "...",
       sections: {
         introduction: "...",
         methods: "...",
         results: "...",
         discussion: "..."
       }
     },
     tables: [...],
     figures: [...]
   }

4. Frontend displays formatted text with sections
```

---

## Summary

### Key Takeaways

1. **Complete Pipeline:** Frontend → API → Agents → Pipelines → Storage → Response

2. **GEO-Centric Organization:** All PDFs/fulltext organized by GEO ID

3. **Three Storage Locations:**
   - `data/pdfs/{geo_id}/` - GEO-specific PDFs
   - `data/fulltext/parsed/` - Cached parsed content
   - `data/geo_citation_collections/{geo_id}/` - Complete collections

4. **API-Based Access:** Frontend should use API endpoints, not direct file access

5. **Unified Format:** Phase 5 normalizer ensures all formats (JATS, PDF, LaTeX) → same structure

6. **Current Status:**
   - ✅ Backend pipeline complete
   - ✅ PDF download working
   - ✅ Fulltext cache working
   - ✅ Format normalization working (Phase 5)
   - ❌ Frontend not implemented yet
   - ❌ API endpoints for file serving not implemented yet

### Next Steps for Frontend Integration

1. **Implement File Serving Endpoints:**
   ```python
   # Add to omics_oracle_v2/api/routes/
   
   @router.get("/files/pdf/{geo_id}/{pmid}")
   async def serve_pdf(geo_id: str, pmid: str):
       pdf_path = Path(f"data/pdfs/{geo_id}/PMID{pmid}.pdf")
       return FileResponse(pdf_path)
   
   @router.get("/fulltext/{publication_id}")
   async def get_fulltext(publication_id: str):
       cache = ParsedCache()
       content = await cache.get_normalized(publication_id)
       return content
   ```

2. **Build Frontend Display:**
   - Search interface
   - GEO dataset cards
   - PDF viewer/download buttons
   - Fulltext viewer (formatted sections)

3. **Connect Frontend to API:**
   - Use `/api/v1/workflows/execute` for search
   - Use `/api/v1/datasets/geo/{geo_id}` for details
   - Use `/api/v1/files/pdf/{geo_id}/{pmid}` for PDFs
   - Use `/api/v1/fulltext/{pub_id}` for fulltext

---

**Questions? Need clarification on any part of this pipeline?**
