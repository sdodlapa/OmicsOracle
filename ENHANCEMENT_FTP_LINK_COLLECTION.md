# Enhancement: FTP Link Collection & Structured Download Information

## What Was Changed

Enhanced the GEO metadata system to properly collect, store, and structure FTP links to actual datasets for future download with user approval.

---

## Summary

**Problem:** User correctly identified that the system shouldn't automatically download datasets - downloading should be a separate, approved pipeline.

**Solution:** Enhanced metadata collection to:
1. ✅ Store FTP links to actual data files (already working)
2. ✅ Parse and structure download information
3. ✅ Provide file type detection and size estimation
4. ✅ Create separate `DataDownloadPipeline` for approved downloads
5. ✅ Clear separation between metadata and data

---

## Files Modified

### 1. `omics_oracle_v2/lib/geo/models.py`

**Added New Model:**
```python
class DataDownloadInfo(BaseModel):
    """Information about downloadable dataset files."""
    file_url: str          # FTP/HTTP URL
    file_type: str         # RAW, processed, sequencing, etc.
    file_size_bytes: Optional[int]
    file_format: str       # tar, txt, fastq, CEL, etc.
    description: str       # Human-readable description
```

**Enhanced GEOSeriesMetadata:**
```python
class GEOSeriesMetadata(BaseModel):
    # ... existing fields ...

    supplementary_files: List[str]  # Raw FTP URLs (already existed)

    # NEW: Structured download information
    data_downloads: List[DataDownloadInfo]  # Parsed, structured info

    # NEW: Helper methods
    def parse_download_info(self) -> List[DataDownloadInfo]:
        """Parse FTP URLs into structured download information."""

    def get_download_summary(self) -> Dict[str, int]:
        """Get summary of files by type (RAW: 2, processed: 1, etc.)."""

    def has_raw_data(self) -> bool:
        """Check if raw experimental data is available."""

    def estimate_download_size_mb(self) -> str:
        """Estimate download size based on file types."""
```

### 2. `omics_oracle_v2/lib/geo/client.py`

**Enhanced metadata retrieval:**
```python
# After getting metadata from GEOparse
metadata = GEOSeriesMetadata(...)

# NEW: Parse and populate structured download info
metadata.data_downloads = metadata.parse_download_info()

logger.info(
    f"Found {len(metadata.supplementary_files)} downloadable files "
    f"({metadata.get_download_summary()})"
)
```

### 3. `omics_oracle_v2/lib/downloads/data_pipeline.py` (NEW)

**Created separate download pipeline:**
```python
class DataDownloadPipeline:
    """
    Pipeline for downloading approved dataset files.

    SEPARATE from search/metadata collection.
    All downloads require explicit user approval.
    """

    def approve_dataset(self, geo_id: str, approved_by: str):
        """Approve a dataset for download (REQUIRED)."""

    async def download_dataset(self, geo_id: str, metadata: GEOSeriesMetadata, ...):
        """Download approved dataset files."""
        # Checks approval first!
        if not self.is_approved(geo_id):
            raise DownloadError("Dataset not approved")
```

---

## How It Works Now

### Phase 1: Metadata Collection (Current Tests)

```python
from omics_oracle_v2.lib.geo.client import GEOClient

client = GEOClient()

# Search GEO (returns IDs only)
results = await client.search("diabetes RNA-seq")

# Get metadata (downloads ~5 KB SOFT file)
metadata = await client.get_metadata(results.geo_ids[0])

print(f"Title: {metadata.title}")
print(f"Samples: {metadata.sample_count}")

# NEW: Check available downloads (not downloading them!)
print(f"\nAvailable files:")
for download in metadata.data_downloads:
    print(f"  - {download.file_type}: {download.description}")
    print(f"    URL: {download.file_url}")
    print(f"    Format: {download.file_format}")

print(f"\nEstimated size: {metadata.estimate_download_size_mb()}")
print(f"Has raw data: {metadata.has_raw_data()}")
print(f"File types: {metadata.get_download_summary()}")
```

**Output:**
```
Title: Pancreatic islet RNA-seq in type 2 diabetes
Samples: 50

Available files:
  - RAW: Raw data archive (CEL files, IDAT files, etc.)
    URL: ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_RAW.tar
    Format: tar
  - processed: Processed expression matrix or normalized data
    URL: ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_matrix.txt
    Format: txt

Estimated size: 500 MB - 50 GB (depending on sample count)
Has raw data: True
File types: {'RAW': 1, 'processed': 1}
```

**Downloaded so far:** ~5 KB (metadata only)

### Phase 2: Data Download (Future/Manual)

```python
from omics_oracle_v2.lib.downloads import DataDownloadPipeline

# User has reviewed metadata and wants to download
pipeline = DataDownloadPipeline(download_dir="./data/approved")

# STEP 1: USER APPROVAL (REQUIRED!)
pipeline.approve_dataset(
    geo_id="GSE123456",
    approved_by="user@example.com"
)

# STEP 2: Download actual data
requests = await pipeline.download_dataset(
    geo_id="GSE123456",
    metadata=metadata,
    approved_by="user@example.com",
    file_types=["RAW"]  # Only download raw data
)

# STEP 3: Monitor progress
for request in requests:
    print(f"Downloading: {request.file_url}")
    print(f"Progress: {request.get_progress_percent():.1f}%")
    print(f"Status: {request.status}")
```

**Downloaded:** 500 MB - 50 GB (actual dataset, only after approval)

---

## File Type Detection

The system now automatically detects file types from URLs:

| Pattern | Type | Format | Description |
|---------|------|--------|-------------|
| `_RAW.tar` | RAW | tar | Raw data archive (CEL, IDAT, etc.) |
| `_processed` | processed | txt | Processed expression matrix |
| `_matrix.txt` | processed | txt | Normalized data matrix |
| `.fastq` | sequencing | fastq | Raw sequencing reads |
| `.bam` | alignment | bam | Aligned sequencing reads |
| `.CEL` | microarray | CEL | Microarray raw data |

### Size Estimation

Based on file types detected:

| File Type | Estimated Size |
|-----------|----------------|
| RAW | 500 MB - 50 GB |
| sequencing | 1 GB - 500 GB |
| microarray | 100 MB - 2 GB |
| processed | 10 MB - 500 MB |

---

## Benefits

### 1. Clear Separation
- ✅ Metadata collection: Fast, automatic, lightweight
- ✅ Data download: Slow, manual, user-controlled

### 2. Informed Decisions
- ✅ Users see what's available before committing
- ✅ File types, sizes, and formats clearly indicated
- ✅ Can filter by file type (RAW only, processed only, etc.)

### 3. Storage Control
- ✅ No accidental multi-GB downloads
- ✅ User approves each dataset
- ✅ Can prioritize which files to download

### 4. Better UX
- ✅ Browse thousands of datasets quickly
- ✅ Download only what you need
- ✅ Track download progress
- ✅ Resume failed downloads (future)

---

## Example Use Case

### Researcher Workflow

**1. Search for relevant datasets**
```python
results = await client.search("CRISPR Cas9 gene editing", max_results=100)
# Found 100 datasets in 2 seconds
```

**2. Browse metadata (fast!)**
```python
for geo_id in results.geo_ids[:10]:
    metadata = await client.get_metadata(geo_id)
    print(f"{geo_id}: {metadata.title}")
    print(f"  Samples: {metadata.sample_count}")
    print(f"  Files: {metadata.get_download_summary()}")
    print(f"  Size: {metadata.estimate_download_size_mb()}")
```

**Output:**
```
GSE123456: CRISPR screening in cancer cells
  Samples: 24
  Files: {'RAW': 1, 'processed': 1}
  Size: 500 MB - 50 GB

GSE123457: Cas9 off-target analysis
  Samples: 12
  Files: {'sequencing': 4}
  Size: 1 GB - 500 GB

... (8 more)
```

**Total time:** 20 seconds
**Total downloaded:** 50 KB (metadata only)

**3. User selects relevant datasets**
```python
# User reviews and picks 2 datasets
selected = ["GSE123456", "GSE123457"]
```

**4. Download approved datasets**
```python
pipeline = DataDownloadPipeline()

for geo_id in selected:
    metadata = await client.get_metadata(geo_id)

    # USER APPROVAL
    pipeline.approve_dataset(geo_id, approved_by="researcher@university.edu")

    # DOWNLOAD
    await pipeline.download_dataset(
        geo_id=geo_id,
        metadata=metadata,
        approved_by="researcher@university.edu",
        file_types=["processed"]  # Only processed data for now
    )
```

**Total downloaded:** ~100 MB (processed files only)
**Saved:** ~50-500 GB (didn't download RAW/sequencing)

---

## Integration with Current Code

### Backward Compatible
- ✅ Existing code still works
- ✅ `supplementary_files` field unchanged
- ✅ New fields are additive

### Current Tests
Week 2 Day 3 cache test **already using this correctly**:
- Downloads metadata (SOFT files, ~5 KB each)
- Stores FTP links in `supplementary_files`
- Does NOT download actual datasets
- Measures cache speedup for metadata retrieval

### Future Tests
Week 2 Day 4-5 should test:
- [ ] Data download pipeline
- [ ] Approval workflow
- [ ] Progress tracking
- [ ] Error handling
- [ ] File verification

---

## What Changed in Cache Test

**Before understanding:**
```
Downloading ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_RAW.tar
```
→ Looks like downloading dataset! (50 GB?) 😱

**Actually:**
```
Downloading ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_family.soft.gz (5 KB)
```
→ Downloading metadata only ✅

**What gets stored:**
```python
metadata.supplementary_files = [
    "ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_RAW.tar",  # Link stored, not downloaded
    "ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_matrix.txt"
]

metadata.data_downloads = [
    DataDownloadInfo(
        file_url="ftp://ftp.ncbi.nlm.nih.gov/.../GSE123456_RAW.tar",
        file_type="RAW",
        file_format="tar",
        description="Raw data archive (CEL files)",
        # file_size_bytes: None (would need to query FTP server)
    )
]
```

---

## Next Steps

### Immediate (This Session)
- [x] Enhanced metadata models
- [x] File type detection
- [x] Size estimation
- [x] Created `DataDownloadPipeline`
- [x] Documentation

### Short Term (Week 2 completion)
- [ ] Test enhanced metadata fields
- [ ] Validate file type detection accuracy
- [ ] Document usage examples

### Medium Term (Week 3)
- [ ] Add download approval UI
- [ ] Implement checksum verification
- [ ] Add resume capability
- [ ] Create download monitoring dashboard

### Long Term
- [ ] Storage quota management
- [ ] Download scheduling
- [ ] Bandwidth limiting
- [ ] Automatic decompression
- [ ] Integration with analysis pipeline

---

## Conclusion

**Question:** "Why is it downloading datasets?"

**Answer:** It's NOT! It's downloading tiny metadata files (~5 KB) that DESCRIBE the datasets and contain links to where the actual data is.

**Enhancement:** Now those links are properly parsed, structured, and stored for future use when user approves specific datasets for download.

**Benefit:** User can browse thousands of datasets in seconds, see what's available, and download only what they need with explicit approval.

**Architecture:** Clean separation between metadata collection (automatic) and data download (user-controlled).
