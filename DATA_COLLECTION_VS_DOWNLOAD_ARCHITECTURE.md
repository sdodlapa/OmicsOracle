# Data Collection vs Data Download Architecture

## Overview

OmicsOracle has **TWO SEPARATE PIPELINES**:

1. **Metadata Collection Pipeline** (Search & Discovery) - Lightweight, automatic
2. **Data Download Pipeline** (Approved Downloads) - Heavy, user-controlled

This separation ensures:
- ✅ Fast browsing without storage burden
- ✅ User approval required for all downloads
- ✅ Clear distinction between metadata and actual data
- ✅ No accidental multi-GB downloads

---

## Pipeline 1: Metadata Collection (Current Implementation)

### Purpose
Collect **information ABOUT datasets**, not the datasets themselves.

### What Gets Downloaded
- ✅ SOFT files (~2-10 KB each)
- ✅ Study descriptions
- ✅ Sample annotations
- ✅ Publication references
- ✅ **FTP links to actual data** (stored for later)

### What Does NOT Get Downloaded
- ❌ Raw sequencing data (.fastq files)
- ❌ Processed expression matrices
- ❌ Microarray CEL files
- ❌ Any files > 100 KB

### Example Metadata
```json
{
  "geo_id": "GSE123456",
  "title": "RNA-seq of diabetic pancreatic islets",
  "summary": "Gene expression profiling...",
  "samples": ["GSM1", "GSM2", "GSM3"],
  "sample_count": 50,
  "organism": "Homo sapiens",
  "publication_date": "2023-01-15",
  "pubmed_ids": ["34567890"],

  "supplementary_files": [
    "ftp://ftp.ncbi.nlm.nih.gov/geo/.../GSE123456_RAW.tar",  ← Link stored, NOT downloaded
    "ftp://ftp.ncbi.nlm.nih.gov/geo/.../GSE123456_matrix.txt"
  ],

  "data_downloads": [
    {
      "file_url": "ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_RAW.tar",
      "file_type": "RAW",
      "file_format": "tar",
      "description": "Raw data archive (CEL files)",
      "estimated_size": "500 MB - 5 GB"
    }
  ]
}
```

### Usage
```python
from omics_oracle_v2.lib.geo.client import GEOClient

# Initialize client
client = GEOClient()

# Search (returns GEO IDs only)
results = await client.search("diabetes RNA-seq", max_results=100)
print(f"Found {len(results.geo_ids)} datasets")  # Fast! No downloads

# Get metadata (downloads ~5 KB SOFT file per dataset)
for geo_id in results.geo_ids[:10]:
    metadata = await client.get_metadata(geo_id)

    print(f"Dataset: {metadata.title}")
    print(f"Samples: {metadata.sample_count}")
    print(f"Has raw data: {metadata.has_raw_data()}")

    # Show available downloads (NOT downloading them!)
    for download in metadata.data_downloads:
        print(f"  Available: {download.file_type} - {download.file_url}")
        print(f"  Estimated: {metadata.estimate_download_size_mb()}")
```

**Total Downloaded:** ~50 KB for 10 datasets (metadata only)

---

## Pipeline 2: Data Download (New Implementation)

### Purpose
Download **actual experimental data** after user approval.

### What Gets Downloaded
- ✅ Raw data archives (100 MB - 50 GB)
- ✅ Processed expression matrices (10 MB - 500 MB)
- ✅ FASTQ sequencing files (1 GB - 500 GB)
- ✅ Microarray CEL files (100 MB - 2 GB)
- ✅ **Only approved datasets**

### Approval Required
Every download requires explicit user approval:
```python
# User must call this BEFORE any download
pipeline.approve_dataset(geo_id="GSE123456", approved_by="user@example.com")
```

### Usage
```python
from omics_oracle_v2.lib.geo.client import GEOClient
from omics_oracle_v2.lib.downloads import DataDownloadPipeline

# Step 1: Search and get metadata (metadata pipeline)
client = GEOClient()
results = await client.search("diabetes RNA-seq")
metadata = await client.get_metadata(results.geo_ids[0])

print(f"\nDataset: {metadata.title}")
print(f"Available files:")
for download in metadata.data_downloads:
    print(f"  - {download.file_type}: {download.description}")
    print(f"    URL: {download.file_url}")
    print(f"    Estimated size: {metadata.estimate_download_size_mb()}")

# Step 2: USER REVIEWS AND APPROVES
user_choice = input("\nDownload this dataset? (yes/no): ")

if user_choice == "yes":
    # Step 3: Initialize download pipeline
    download_pipeline = DataDownloadPipeline(
        download_dir="./data/approved_datasets"
    )

    # Step 4: APPROVE DATASET (REQUIRED)
    download_pipeline.approve_dataset(
        geo_id=metadata.geo_id,
        approved_by="user@example.com"
    )

    # Step 5: Download actual data
    requests = await download_pipeline.download_dataset(
        geo_id=metadata.geo_id,
        metadata=metadata,
        approved_by="user@example.com",
        file_types=["RAW"]  # Only raw data
    )

    # Step 6: Monitor progress
    for request in requests:
        print(f"Download: {request.status}")
        print(f"Progress: {request.get_progress_percent():.1f}%")
else:
    print("Download cancelled")
```

**Total Downloaded:** 500 MB - 50 GB (actual dataset)

---

## Complete Workflow

```
User Query: "diabetes RNA-seq"
    ↓
┌─────────────────────────────────────────────────────────┐
│  PIPELINE 1: METADATA COLLECTION (Automatic)            │
└─────────────────────────────────────────────────────────┘
    ↓
1. Search GEO Database
   └→ Found 1,000 dataset IDs
   └→ Downloaded: 0 bytes (just IDs from NCBI API)
    ↓
2. Get Metadata for Top 100 Results
   └→ Downloads: 100 × 5 KB = 500 KB (SOFT files)
   └→ Time: ~2 minutes
   └→ Contains: Descriptions, samples, FTP links
    ↓
3. Find Publications That Used These Datasets
   └→ Search PubMed, OpenAlex, Semantic Scholar
   └→ Found: 50 papers citing these datasets
    ↓
4. Download PDFs of Those Papers
   └→ Downloads: 50 × 2 MB = 100 MB (PDFs)
   └→ Extract full text
    ↓
┌─────────────────────────────────────────────────────────┐
│  USER REVIEW POINT                                      │
│  Total downloaded so far: ~100.5 MB (metadata + PDFs)   │
│  User sees 100 datasets with descriptions               │
└─────────────────────────────────────────────────────────┘
    ↓
User Reviews Results:
  - Dataset 1: "Pancreatic islet RNA-seq" - 50 samples
    Available: RAW data (5 GB), Processed matrix (50 MB)
    Publications: 3 papers cited this dataset

  - Dataset 2: "Beta cell transcriptomics" - 12 samples
    Available: RAW data (1 GB), Processed matrix (10 MB)
    Publications: 1 paper cited this dataset

  - ... (98 more datasets)
    ↓
User Selects: "I want datasets 1 and 2"
    ↓
┌─────────────────────────────────────────────────────────┐
│  USER APPROVAL REQUIRED                                 │
└─────────────────────────────────────────────────────────┘
    ↓
User Approves: Dataset 1, Dataset 2
    ↓
┌─────────────────────────────────────────────────────────┐
│  PIPELINE 2: DATA DOWNLOAD (User-Controlled)            │
└─────────────────────────────────────────────────────────┘
    ↓
5. Download Approved Datasets
   └→ Dataset 1 RAW: 5 GB (downloading...)
   └→ Dataset 2 RAW: 1 GB (downloading...)
   └→ Time: ~30 minutes (depending on connection)
    ↓
6. Verify Downloaded Files
   └→ Check file integrity
   └→ Store in approved_datasets/
    ↓
┌─────────────────────────────────────────────────────────┐
│  COMPLETE                                               │
│  Total downloaded:                                      │
│  - Metadata: 500 KB                                     │
│  - PDFs: 100 MB                                         │
│  - Datasets: 6 GB                                       │
│  Total: ~6.1 GB (only approved items)                   │
└─────────────────────────────────────────────────────────┘
```

---

## File Sizes Comparison

### Metadata Collection (Pipeline 1)
| File Type | Size | Purpose |
|-----------|------|---------|
| SOFT file | 2-10 KB | Dataset description |
| Publication PDF | 1-5 MB | Full text paper |
| Search results | < 1 KB | List of IDs |

**Total for 100 datasets + 50 papers:** ~100-300 MB

### Data Download (Pipeline 2)
| File Type | Size | Purpose |
|-----------|------|---------|
| RAW tar archive | 500 MB - 50 GB | Raw experimental data |
| Processed matrix | 10 MB - 500 MB | Normalized expression values |
| FASTQ files | 1 GB - 500 GB | Sequencing reads |
| BAM files | 5 GB - 200 GB | Aligned reads |

**Total for 1 dataset:** 500 MB - 500 GB

---

## Security & Storage

### Metadata Collection
- ✅ Safe to run automatically
- ✅ Minimal disk usage
- ✅ Fast browsing
- ✅ Can cache indefinitely

### Data Download
- ⚠️ Requires user approval
- ⚠️ Large disk usage
- ⚠️ Slow transfer
- ⚠️ Storage management needed

---

## Current Implementation Status

### ✅ Implemented (Metadata Collection)
- [x] GEO search (NCBI E-utilities)
- [x] Metadata retrieval (SOFT files)
- [x] Publication search (PubMed, OpenAlex)
- [x] PDF download (institutional access)
- [x] FTP link extraction
- [x] Structured download info (`data_downloads` field)
- [x] File type detection
- [x] Size estimation

### ✅ Implemented (Data Download)
- [x] `DataDownloadPipeline` class
- [x] Approval workflow
- [x] Download queue management
- [x] Progress tracking
- [x] Concurrent downloads
- [x] Error handling
- [x] Status reporting

### 🚧 Future Enhancements
- [ ] Checksum verification (MD5/SHA256)
- [ ] Resume capability for interrupted downloads
- [ ] Bandwidth limiting
- [ ] Storage quota management
- [ ] Automatic decompression
- [ ] Download scheduling
- [ ] Web UI for approval workflow

---

## API Reference

### Metadata Models

```python
from omics_oracle_v2.lib.geo.models import (
    GEOSeriesMetadata,
    DataDownloadInfo,
)

# Get dataset metadata
metadata: GEOSeriesMetadata = await client.get_metadata("GSE123456")

# Check available downloads
print(f"Has raw data: {metadata.has_raw_data()}")
print(f"Download summary: {metadata.get_download_summary()}")
print(f"Estimated size: {metadata.estimate_download_size_mb()}")

# Get structured download info
for download in metadata.data_downloads:
    print(f"Type: {download.file_type}")
    print(f"URL: {download.file_url}")
    print(f"Format: {download.file_format}")
    print(f"Description: {download.description}")
```

### Download Pipeline

```python
from omics_oracle_v2.lib.downloads import (
    DataDownloadPipeline,
    DownloadStatus,
)

# Initialize pipeline
pipeline = DataDownloadPipeline(
    download_dir="./data/approved",
    max_concurrent_downloads=3,
    verify_checksums=True,
)

# Approve dataset (REQUIRED)
pipeline.approve_dataset(
    geo_id="GSE123456",
    approved_by="user@example.com"
)

# Check approval
if pipeline.is_approved("GSE123456"):
    # Download dataset
    requests = await pipeline.download_dataset(
        geo_id="GSE123456",
        metadata=metadata,
        approved_by="user@example.com",
        file_types=["RAW"],  # Optional filter
    )

    # Monitor progress
    for request in requests:
        print(f"File: {request.file_url}")
        print(f"Status: {request.status}")
        print(f"Progress: {request.get_progress_percent():.1f}%")

# Get statistics
stats = pipeline.get_download_stats()
print(f"Completed: {stats['completed']}")
print(f"Failed: {stats['failed']}")
```

---

## Testing

### Test Metadata Collection
```bash
# Run Week 2 Day 3 cache tests
python test_week2_cache_integration.py

# This downloads metadata only (~30-100 KB total)
# Measures cache speedup for fast browsing
```

### Test Data Download
```bash
# Run data download tests (future)
python test_data_download_pipeline.py

# This will download actual data (after approval)
# Tests approval workflow, progress tracking, etc.
```

---

## Summary

### What OmicsOracle Does NOW (Metadata Collection)
1. ✅ Searches GEO database
2. ✅ Downloads **metadata** (SOFT files, ~5 KB each)
3. ✅ Finds publications
4. ✅ Downloads PDFs
5. ✅ Stores FTP links for later
6. ✅ **Total: ~100-300 MB for 100 datasets**

### What OmicsOracle Does LATER (Data Download)
7. ✅ User reviews available datasets
8. ✅ User approves specific datasets
9. ✅ Downloads actual data (GB-TB scale)
10. ✅ **Only approved datasets**
11. ✅ **User in full control**

### Key Principle
**Metadata First, Data Later, Always with Approval**

This architecture ensures users can:
- Browse thousands of datasets instantly
- See what's available without commitment
- Make informed decisions
- Download only what they need
- Control storage and bandwidth usage
