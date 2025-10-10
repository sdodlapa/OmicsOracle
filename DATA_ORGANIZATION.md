# Phase 6 Pipeline - Data Organization

## Overview

The GEO Citation Pipeline organizes collected data in a structured format optimized for downstream analysis and archival.

## Directory Structure

```
data/
├── geo_citation_collections/     # Main collection directory
│   └── [query_name]_[timestamp]/ # One directory per collection run
│       ├── geo_datasets.json     # GEO metadata
│       ├── citing_papers.json    # Citing publications
│       └── collection_report.json # Summary statistics
│
└── pdfs/                         # PDF storage (when enabled)
    └── [source]/                 # Organized by source
        └── [pmid].pdf            # PDFs named by PMID
```

## Current Collections

### Test Run: "breast cancer RNA-seq" (Oct 10, 2025 17:09)

**Location:** `data/geo_citation_collections/breast cancer RNA_seq_20251010_170951/`

**Files:**
- `geo_datasets.json` (2.7 KB) - 2 GEO datasets with full metadata
- `citing_papers.json` (2 B) - Empty array (datasets too new)
- `collection_report.json` (161 B) - Collection summary

**Datasets Collected:**

1. **GSE267442** - CLIC3 biomarker in triple-negative breast cancer
   - Samples: 16
   - PubMed IDs: None (unpublished)
   - Summary: RNA-seq study identifying CLIC3 as prognostic biomarker

2. **GSE267552** - Tumor-associated T cells study
   - Samples: 9
   - PubMed IDs: None (unpublished)
   - Summary: TRM vs TEX cell populations in cancer

## File Formats

### 1. geo_datasets.json

Contains metadata for all GEO datasets found:

```json
[
  {
    "geo_id": "GSE267442",
    "title": "Dataset title...",
    "summary": "Study description...",
    "pubmed_ids": [],
    "sample_count": 16
  }
]
```

**Fields:**
- `geo_id`: GEO accession (e.g., GSE267442)
- `title`: Dataset title
- `summary`: Full study description
- `pubmed_ids`: Array of associated PubMed IDs
- `sample_count`: Number of samples in dataset

### 2. citing_papers.json

Contains metadata for papers citing the GEO datasets:

```json
[
  {
    "pmid": "12345678",
    "doi": "10.1234/journal.12345",
    "title": "Paper title",
    "authors": ["Author A", "Author B"],
    "journal": "Journal Name",
    "year": 2024,
    "fulltext_url": "https://...",
    "fulltext_source": "institutional|unpaywall|core|..."
  }
]
```

**Fields:**
- `pmid`: PubMed ID
- `doi`: Digital Object Identifier
- `title`: Paper title
- `authors`: Author list
- `journal`: Journal name
- `year`: Publication year
- `fulltext_url`: URL to full-text (if available)
- `fulltext_source`: Source that provided the URL

### 3. collection_report.json

Summary statistics for the collection:

```json
{
  "query": "breast cancer RNA-seq",
  "timestamp": "2025-10-10T17:09:51.818730",
  "datasets_found": 2,
  "citing_papers_found": 0,
  "download_report": {
    "total_attempted": 0,
    "successful": 0,
    "failed": 0,
    "success_rate": 0.0
  }
}
```

## Data Organization Strategy

### Naming Convention

Collections are named using the pattern:
```
[sanitized_query]_[YYYYMMDD]_[HHMMSS]/
```

**Examples:**
- `breast cancer RNA_seq_20251010_170951/`
- `alzheimer disease RNA_seq_20251010_171245/`
- `TCGA breast cancer_20251010_171012/`

**Benefits:**
- Sortable by timestamp
- Human-readable query name
- No file conflicts
- Easy to identify old vs new runs

### PDF Organization

When PDF download is enabled, files are organized:

```
data/pdfs/
├── institutional/    # From institutional access
│   ├── 12345678.pdf
│   └── 23456789.pdf
├── unpaywall/       # From Unpaywall
│   └── 34567890.pdf
├── core/            # From CORE API
│   └── 45678901.pdf
└── pubmed/          # From PubMed Central
    ├── 24651512.pdf  # Existing from earlier test
    └── 29451881.pdf  # Existing from earlier test
```

**Benefits:**
- Track which source provided each PDF
- Avoid duplicate downloads
- Easy to audit coverage by source
- Support for future citation tracking

### Alternative: Organization by GEO ID

Can also organize by GEO dataset (set `organize_by_geo_id=True`):

```
data/geo_citation_collections/
└── GSE267442/
    ├── metadata.json
    ├── citing_papers.json
    └── pdfs/
        ├── 12345678.pdf
        └── 23456789.pdf
```

**Use when:**
- Multiple queries might return same dataset
- Need to aggregate all citations for specific dataset
- Building dataset-specific knowledge base

## Storage Estimates

### Typical Collection (50 papers)

- **Metadata JSON:** ~100 KB
  - GEO datasets: 20-50 KB (2-5 datasets)
  - Citing papers: 50-80 KB (50 papers × 1-1.5 KB)
  - Collection report: 1 KB
  
- **PDFs:** ~25-75 MB
  - Average: 0.5-1.5 MB per paper
  - 50 papers × 0.5-1.5 MB = 25-75 MB

### Large-Scale Collection (500 papers)

- **Metadata JSON:** ~1 MB
- **PDFs:** ~250-750 MB

### Recommended Limits

- **Papers per query:** 100-200 (balance breadth vs depth)
- **Datasets per query:** 5-10 (manageable scope)
- **Concurrent downloads:** 3-5 (respect rate limits)

## Data Access Patterns

### Programmatic Access

```python
import json
from pathlib import Path

# Load collection
collection_dir = Path("data/geo_citation_collections/breast cancer RNA_seq_20251010_170951")

# Read datasets
with open(collection_dir / "geo_datasets.json") as f:
    datasets = json.load(f)

# Read citations
with open(collection_dir / "citing_papers.json") as f:
    papers = json.load(f)

# Read report
with open(collection_dir / "collection_report.json") as f:
    report = json.load(f)
```

### Analysis Workflow

1. **Load metadata** → Filter by relevance
2. **Check full-text availability** → Prioritize papers with URLs
3. **Download PDFs** → Batch download from saved URLs
4. **Extract text** → Use PDF extraction pipeline
5. **Analyze** → LLM analysis (Phase 7)

## Future Enhancements

### Phase 7 (LLM Analysis)

Additional files to be created:
```
collection_dir/
├── analysis/
│   ├── llm_summaries.json      # Paper summaries
│   ├── relevance_scores.json   # Relevance ratings
│   ├── methodology_extract.json # Extracted methods
│   └── findings_extract.json    # Key findings
└── embeddings/
    └── paper_embeddings.npz     # Vector embeddings
```

### Advanced Features

- **Deduplication index** → Track papers across collections
- **Citation graph** → Build paper-to-paper citation network
- **Temporal analysis** → Track research trends over time
- **Source attribution** → Detailed provenance tracking

## Current Status

✅ **Implemented:**
- Query-based directory naming
- JSON metadata storage
- Collection report generation
- PDF path configuration

⚠️ **Partially Tested:**
- PDF download (infrastructure ready, not tested with actual citations)
- Multi-source PDF organization

🔲 **Not Yet Implemented:**
- GEO ID-based organization (code exists, not tested)
- Deduplication across collections
- Citation graph generation
- Embedding storage

## Recommendations

### For Single-Query Research
- Use timestamp-based naming
- Download PDFs immediately
- Store in single collection directory

### For Systematic Reviews
- Use GEO ID-based organization
- Build cross-collection index
- Track duplicate papers
- Generate citation graphs

### For Production Deployment
- Set up automated backups
- Monitor storage usage
- Implement retention policies
- Add compression for old collections
