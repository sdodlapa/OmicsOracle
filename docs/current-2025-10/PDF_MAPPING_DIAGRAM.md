## PDF & Full-Text Organization Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OmicsOracle Data Organization                     │
└─────────────────────────────────────────────────────────────────────┘

data/
│
├── pdfs/                           ✅ NOW CLEAN (old files deleted)
│   └── (empty or future ad-hoc downloads)
│
└── geo_citation_collections/       ✅ ORGANIZED STORAGE
    │
    ├── GSE103322_20251011_160612/  ← One GEO dataset collection
    │   ├── download_metadata.json  ← Stats & info
    │   └── citing_papers/          ← Papers that cite GSE103322
    │       ├── PMID_29451881.pdf   ← Maps to PubMed ID
    │       ├── PMID_30123456.pdf
    │       └── PMID_31789012.pdf
    │
    ├── GSE298471_20251011_170800/  ← Another GEO dataset
    │   ├── download_metadata.json
    │   └── citing_papers/
    │       └── PMID_*.pdf
    │
    └── breast_cancer_RNA_seq_20251010_170516/  ← Query-based (from pipeline)
        ├── geo_datasets.json       ← Multiple GEO datasets
        ├── citing_papers.json      ← All citing papers (mixed)
        ├── collection_report.json
        └── pdfs/                   ← ⚠️ Mixed PDFs from multiple GEOs
            └── PMID_*.pdf
```

---

## Mapping Flow: GEO Dataset → PDFs

```
┌──────────────┐
│  User Query  │ "Find papers citing GSE103322"
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  GEO Dataset Search  │ GSE103322 found
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│     Citation Discovery                    │
│  Two strategies:                          │
│  1. Papers citing original PMID (24651512)│
│  2. Papers mentioning "GSE103322"        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Citing Papers Found          │
│  - PMID: 29451881             │
│  - PMID: 30123456             │
│  - PMID: 31789012             │
│  - DOI: 10.1234/abc (no PMID) │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Full-Text URL Discovery     │
│  Sources:                     │
│  - Unpaywall                  │
│  - PubMed Central             │
│  - CORE                       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  PDF Download                             │
│  To: data/geo_citation_collections/       │
│      GSE103322_20251011_160612/           │
│      └── citing_papers/                   │
│          ├── PMID_29451881.pdf            │
│          ├── PMID_30123456.pdf            │
│          ├── PMID_31789012.pdf            │
│          └── DOI_10.1234_abc.pdf          │
└───────────────────────────────────────────┘
```

---

## File Naming Logic

```python
# From: omics_oracle_v2/lib/storage/pdf/download_manager.py

Publication                  →  Filename
──────────────────────────────────────────────────────
pmid = "29451881"           →  PMID_29451881.pdf
doi = "10.1234/abc"         →  DOI_10.1234_abc.pdf
doi = "10.1038/s41586..."   →  DOI_10.1038_s41586_....pdf
title = "Some Paper"        →  paper_a1b2c3d4e5f6.pdf (hash)
```

**Priority:** PMID > DOI > Title Hash

---

## Lookup Examples

### Example 1: Find all papers for GSE103322

```bash
# Navigate to collection
cd data/geo_citation_collections/GSE103322_20251011_160612/

# View metadata
cat download_metadata.json

# List all citing papers
ls citing_papers/

# Output:
# PMID_29451881.pdf
# PMID_30123456.pdf
# ...
```

### Example 2: Check which GEO dataset a PDF belongs to

```bash
# Find PDF
find data/geo_citation_collections -name "PMID_29451881.pdf"

# Output shows path:
# data/geo_citation_collections/GSE103322_20251011_160612/citing_papers/PMID_29451881.pdf
#                               ^^^^^^^^^ GEO ID
```

### Example 3: Get metadata for a PMID

```bash
# Check citing_papers.json in pipeline collections
cat data/geo_citation_collections/breast_cancer_RNA_seq_*/citing_papers.json | \
    jq '.[] | select(.pmid == "29451881")'

# Or lookup online:
open "https://pubmed.ncbi.nlm.nih.gov/29451881/"
```

---

## Collection Types

### Type 1: Single GEO Dataset (Example Script)

**Created by:** `examples/geo_citation_tracking.py`

```
GSE103322_20251011_160612/
├── download_metadata.json   # Simple stats
└── citing_papers/           # Papers citing THIS dataset only
    └── PMID_*.pdf
```

**Use case:** Focused analysis of one specific GEO dataset

---

### Type 2: Multi-GEO Query (Pipeline)

**Created by:** `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py`

```
breast_cancer_RNA_seq_20251010_170516/
├── geo_datasets.json        # Lists: GSE103322, GSE298471, ...
├── citing_papers.json       # Papers from ALL datasets
├── collection_report.json   # Comprehensive stats
└── pdfs/
    └── PMID_*.pdf           # Mixed from multiple GEO datasets
```

**Use case:** Broad research query finding multiple relevant datasets

**To determine GEO mapping:**
1. Check `geo_datasets.json` for each dataset's `pubmed_ids`
2. Check `citing_papers.json` for paper metadata
3. Cross-reference PMIDs between files

---

## Current Collections

```bash
$ ls -1 data/geo_citation_collections/

breast_cancer_RNA_seq_20251010_170516/
breast_cancer_RNA_seq_20251010_170723/
breast_cancer_RNA_seq_20251010_170951/
Joint_profiling_dna_methylation_HiC_data_20251010_182910/
```

**These are query-based (Type 2)** - Multiple GEO datasets per collection

**After update, new collections will be:**
- GEO-ID-based (Type 1) when using example script
- Query-based (Type 2) when using pipeline

---

## Summary

### ✅ What Changed

1. **Deleted:** `data/pdfs/pubmed/` (old unorganized files)
2. **Updated:** `examples/geo_citation_tracking.py` to use GEO-ID-based organization
3. **Created:** Proper subdirectory structure (`citing_papers/`)
4. **Added:** `download_metadata.json` for tracking

### ✅ How PDFs Map to GEO

**Single GEO Collections:**
- Directory name = GEO ID + timestamp
- All PDFs in `citing_papers/` cite that GEO dataset
- Clear 1:1 mapping

**Multi-GEO Collections:**
- Directory name = query + timestamp
- Check `geo_datasets.json` and `citing_papers.json`
- Cross-reference PMIDs for mapping

### ✅ File Naming

- **PMID-based:** `PMID_29451881.pdf` (preferred)
- **DOI-based:** `DOI_10.1234_abc.pdf` (fallback)
- **Hash-based:** `paper_a1b2c3d4e5f6.pdf` (rare)

### 📁 Storage Location

**All organized collections:** `data/geo_citation_collections/`

**Each collection contains:**
- Metadata JSON files
- PDFs in subdirectories
- Clear naming and timestamps

---

**Ready for fresh data collection!** 🎉
