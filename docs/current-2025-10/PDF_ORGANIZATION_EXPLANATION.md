# PDF and Full-Text Organization System

## Current Status (October 11, 2025)

### Overview
OmicsOracle collects PDFs and full-text for two types of papers:
1. **Original papers** that generated the GEO dataset (the dataset's publication)
2. **Citing papers** that reference/cite the GEO dataset

### Storage Architecture

```
data/
├── pdfs/
│   ├── pubmed/                    # ❌ OLD - Generic PubMed downloads (to delete)
│   │   ├── 24651512.pdf          # Random paper 1
│   │   └── 29451881.pdf          # Random paper 2
│   └── geo_citations/             # ❌ OLD - Generic location (to replace)
│
└── geo_citation_collections/      # ✅ CORRECT - Organized by query/GEO
    ├── breast_cancer_RNA_seq_20251010_170516/
    │   ├── geo_datasets.json      # GEO metadata
    │   ├── citing_papers.json     # Papers that cite the dataset
    │   ├── collection_report.json # Summary
    │   └── pdfs/                  # ✅ PDFs organized by collection
    │       ├── PMID_12345678.pdf
    │       ├── DOI_10.1234_abcd.pdf
    │       └── ...
    │
    └── Joint_profiling_dna_methylation_20251010_182910/
        ├── geo_datasets.json
        ├── citing_papers.json
        ├── collection_report.json
        └── pdfs/
            └── ...
```

## How PDFs are Mapped to GEO Datasets

### Pipeline Flow

**GEO Citation Pipeline** (`omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py`):

```
User Query → GEO Search → Citation Discovery → Full-text URLs → PDF Download
    ↓            ↓              ↓                   ↓                ↓
"breast      GSE103322    Papers citing     URLs from          PDFs saved to:
 cancer      GSE298471    these datasets    Unpaywall,         data/geo_citation_collections/
 RNA-seq"    ...          (by PMID/DOI)     PubMed, etc.       breast_cancer_RNA_seq_TIMESTAMP/pdfs/
```

### Directory Naming Convention

**Pattern:** `{clean_query}_{timestamp}/`

- **Query:** User's search query (sanitized)
- **Timestamp:** `YYYYMMDD_HHMMSS`
- **Example:** `breast_cancer_RNA_seq_20251010_170516/`

### PDF Filename Convention

PDFs are named by their identifier:

1. **By PMID** (PubMed ID): `PMID_{pmid}.pdf`
   - Example: `PMID_24651512.pdf`

2. **By DOI** (if no PMID): `DOI_{sanitized_doi}.pdf`
   - Example: `DOI_10.1234_abcd.pdf`
   - Slashes replaced with underscores

3. **By Title Hash** (if no PMID/DOI): `paper_{hash}.pdf`
   - Example: `paper_a1b2c3d4e5f6.pdf`
   - MD5 hash of title (first 12 chars)

**Code Reference:**
```python
# From: omics_oracle_v2/lib/storage/pdf/download_manager.py

def _generate_filename(self, publication: Publication) -> str:
    if publication.pmid:
        return f"PMID_{publication.pmid}.pdf"
    elif publication.doi:
        clean_doi = publication.doi.replace("/", "_").replace("\\", "_")
        return f"DOI_{clean_doi}.pdf"
    else:
        title_hash = hashlib.md5(publication.title.encode()).hexdigest()[:12]
        return f"paper_{title_hash}.pdf"
```

## Metadata Files

Each collection directory contains:

### 1. `geo_datasets.json`
```json
[
  {
    "geo_id": "GSE103322",
    "title": "Breast cancer RNA-seq study",
    "summary": "...",
    "pubmed_ids": ["24651512"],  # Original paper(s)
    "sample_count": 150
  }
]
```

### 2. `citing_papers.json`
```json
[
  {
    "pmid": "29451881",
    "doi": "10.1234/example",
    "title": "A paper that used GSE103322",
    "authors": ["Smith J", "Doe J"],
    "journal": "Nature",
    "year": 2023,
    "fulltext_url": "https://...",
    "fulltext_source": "unpaywall"
  }
]
```

### 3. `collection_report.json`
```json
{
  "query": "breast cancer RNA-seq",
  "timestamp": "2025-10-10T17:05:16",
  "datasets_found": 5,
  "citing_papers_found": 23,
  "download_report": {
    "total": 23,
    "successful": 18,
    "failed": 5,
    "total_size_mb": 45.2
  }
}
```

## Mapping Logic

### GEO Dataset → Original Paper
```
GEO Series (GSE103322)
    └── metadata.pubmed_ids = ["24651512"]  # Original publication
            └── Download: PMID_24651512.pdf
```

### GEO Dataset → Citing Papers
```
GEO Series (GSE103322)
    └── Citation Discovery
            ├── Strategy 1: Papers citing PMID 24651512
            └── Strategy 2: Papers mentioning "GSE103322"
                    └── Results: [PMID_29451881, PMID_30123456, ...]
                            └── Download: PMID_29451881.pdf, etc.
```

## Example Scenarios

### Scenario 1: User searches "breast cancer RNA-seq"

**Directory created:**
```
data/geo_citation_collections/breast_cancer_RNA_seq_20251011_120000/
├── geo_datasets.json          # Contains: GSE103322, GSE298471, ...
├── citing_papers.json         # All papers citing those datasets
├── collection_report.json     # Summary statistics
└── pdfs/
    ├── PMID_24651512.pdf      # Original paper for GSE103322
    ├── PMID_29451881.pdf      # Paper citing GSE103322
    ├── PMID_30123456.pdf      # Paper citing GSE298471
    └── ...
```

**How to find which papers belong to which GEO dataset:**
1. Open `geo_datasets.json` → find `pubmed_ids` for each GEO ID
2. Open `citing_papers.json` → match PMIDs
3. Each PDF filename maps to PMID in JSON files

### Scenario 2: Direct GEO ID tracking

**Command:**
```bash
python examples/geo_citation_tracking.py GSE103322 --download-pdfs
```

**Default directory:**
```
data/pdfs/geo_citations/  # ❌ OLD LOCATION
```

**Should be:**
```
data/geo_citation_collections/GSE103322_20251011_120000/
├── geo_datasets.json
├── citing_papers.json
├── collection_report.json
└── pdfs/
    └── PMID_*.pdf
```

## Problems with Current Structure

### ❌ Issues Found:

1. **Old files in `data/pdfs/pubmed/`**
   - Random PDFs not linked to any GEO dataset
   - No metadata tracking
   - Should be deleted

2. **Generic `geo_citations/` directory**
   - Example script uses `data/pdfs/geo_citations/` (generic)
   - Should use organized structure like pipeline

3. **No GEO ID in directory name**
   - Hard to know which collection belongs to which dataset
   - Multiple queries can return same datasets

## Recommended Organization (NEW)

### Structure by GEO ID (Primary)

```
data/geo_citation_collections/
├── GSE103322_20251011_120000/
│   ├── metadata.json              # Combined metadata
│   ├── original_paper/
│   │   ├── PMID_24651512.pdf     # Original dataset paper
│   │   └── metadata.json
│   └── citing_papers/
│       ├── PMID_29451881.pdf
│       ├── PMID_30123456.pdf
│       └── metadata.json
│
└── GSE298471_20251011_120100/
    ├── metadata.json
    ├── original_paper/
    └── citing_papers/
```

**Benefits:**
- ✅ Clear GEO ID in directory name
- ✅ Separate original vs citing papers
- ✅ Easy to find all data for specific GEO dataset
- ✅ No confusion between queries

### Alternative: Structure by Query (Current)

```
data/geo_citation_collections/
└── breast_cancer_RNA_seq_20251011_120000/
    ├── geo_datasets.json          # Lists: GSE103322, GSE298471, ...
    ├── citing_papers.json
    └── pdfs/
        ├── PMID_24651512.pdf     # Could be from ANY dataset
        └── PMID_29451881.pdf     # Which GEO? Check JSON!
```

**Issues:**
- ⚠️ PDFs mixed together
- ⚠️ Need to cross-reference JSON to find GEO mapping
- ⚠️ One query can find multiple datasets

## Action Items

### Immediate Cleanup:

1. **Delete old files:**
   ```bash
   rm -rf data/pdfs/pubmed/
   rm -rf data/pdfs/geo_citations/  # if exists
   ```

2. **Update example script:**
   - Change default `output_dir` to use GEO ID
   - Match pipeline organization pattern

3. **Standardize on one approach:**
   - **Option A:** Keep query-based (current pipeline)
   - **Option B:** Switch to GEO-ID-based (clearer mapping)

### Recommended: GEO-ID-Based Organization

**Modify `geo_citation_tracking.py`:**
```python
# OLD (line 147)
async def download_pdfs(papers, output_dir="data/pdfs/geo_citations"):

# NEW
async def download_pdfs(papers, geo_id, output_dir=None):
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"data/geo_citation_collections/{geo_id}_{timestamp}"
```

**Modify pipeline to separate original vs citing:**
```python
collection_dir/
├── metadata.json
├── original_paper/
│   └── PMID_*.pdf
└── citing_papers/
    └── PMID_*.pdf
```
