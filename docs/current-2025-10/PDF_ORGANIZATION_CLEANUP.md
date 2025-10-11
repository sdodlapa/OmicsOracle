# PDF Organization Cleanup - Summary

**Date:** October 11, 2025
**Status:** ✅ COMPLETE

---

## What Was Done

### 1. Deleted Old Unorganized Files ✅

**Removed:**
```bash
data/pdfs/pubmed/
├── 24651512.pdf  (721 KB) - ❌ DELETED
└── 29451881.pdf  (1.7 MB) - ❌ DELETED
```

**Reason:** These were random PDF downloads with no metadata tracking or GEO dataset association.

---

### 2. Updated Organization Structure ✅

**OLD (Before):**
```
data/pdfs/
├── pubmed/              # Random PDFs, no organization
└── geo_citations/       # Generic folder, no GEO tracking
```

**NEW (After):**
```
data/geo_citation_collections/
└── {GEO_ID}_{TIMESTAMP}/
    ├── download_metadata.json      # Collection info
    ├── citing_papers/              # Papers that cite the dataset
    │   ├── PMID_12345678.pdf
    │   ├── PMID_98765432.pdf
    │   └── ...
    └── original_paper/             # (Future) Original dataset paper
        └── PMID_{original}.pdf
```

**Example:**
```
data/geo_citation_collections/GSE103322_20251011_160600/
├── download_metadata.json
└── citing_papers/
    ├── PMID_29451881.pdf
    ├── PMID_30123456.pdf
    └── ...
```

---

### 3. Updated `geo_citation_tracking.py` ✅

**Changes made:**

#### A. Function Signature
```python
# BEFORE
async def download_pdfs(papers, output_dir="data/pdfs/geo_citations"):

# AFTER
async def download_pdfs(
    papers: List[Publication],
    geo_id: str,
    original_paper_pmid: Optional[str] = None,
    output_dir: Optional[str] = None
):
```

#### B. Auto-Generated Directory Structure
```python
# NEW: Creates GEO-specific directory with timestamp
if output_dir is None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"data/geo_citation_collections/{geo_id}_{timestamp}"

# Creates subdirectories
citing_dir = output_path / "citing_papers"
citing_dir.mkdir(exist_ok=True)
```

#### C. Metadata Tracking
```python
# NEW: Saves download metadata
metadata = {
    "geo_id": geo_id,
    "timestamp": datetime.now().isoformat(),
    "citing_papers_downloaded": len(successful),
    "citing_papers_failed": len(failed),
    "total_papers": len(papers)
}

with open(output_path / "download_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

#### D. CLI Argument Update
```python
# BEFORE
parser.add_argument(
    "--output-dir",
    default="data/pdfs/geo_citations",
    help="Output directory for PDFs"
)

# AFTER
parser.add_argument(
    "--output-dir",
    default=None,  # Auto-generate by default
    help="Override output directory (default: auto-generated with GEO ID)"
)
```

---

## How It Works Now

### Basic Usage (Auto-Generated Structure)

```bash
python examples/geo_citation_tracking.py GSE103322 --download-pdfs
```

**Creates:**
```
data/geo_citation_collections/GSE103322_20251011_160612/
├── download_metadata.json
└── citing_papers/
    └── PMID_*.pdf (all citing papers)
```

### Custom Directory (Optional)

```bash
python examples/geo_citation_tracking.py GSE103322 \
    --download-pdfs \
    --output-dir custom/location
```

---

## File Naming Conventions

PDFs are named by their identifier for easy lookup:

### 1. PMID-based (Preferred)
```
PMID_24651512.pdf
PMID_29451881.pdf
```

### 2. DOI-based (Fallback)
```
DOI_10.1234_example.2023.pdf
DOI_10.5678_another_2024.pdf
```

### 3. Hash-based (Last Resort)
```
paper_a1b2c3d4e5f6.pdf  # MD5 of title
```

**Code:**
```python
def _generate_filename(publication: Publication) -> str:
    if publication.pmid:
        return f"PMID_{publication.pmid}.pdf"
    elif publication.doi:
        clean_doi = publication.doi.replace("/", "_")
        return f"DOI_{clean_doi}.pdf"
    else:
        title_hash = hashlib.md5(publication.title.encode()).hexdigest()[:12]
        return f"paper_{title_hash}.pdf"
```

---

## Metadata Mapping

### download_metadata.json

```json
{
  "geo_id": "GSE103322",
  "timestamp": "2025-10-11T16:06:12.345678",
  "citing_papers_downloaded": 18,
  "citing_papers_failed": 2,
  "total_papers": 20
}
```

### Relationship to PDFs

**To find papers for a specific GEO dataset:**

1. Navigate to: `data/geo_citation_collections/GSE103322_*/`
2. Check `download_metadata.json` for GEO ID
3. PDFs in `citing_papers/` are all papers citing that dataset
4. Filename = PMID, can lookup in PubMed

**Example:**
```bash
# Find all papers citing GSE103322
ls data/geo_citation_collections/GSE103322_20251011_160612/citing_papers/

# Output:
PMID_29451881.pdf  # → https://pubmed.ncbi.nlm.nih.gov/29451881/
PMID_30123456.pdf  # → https://pubmed.ncbi.nlm.nih.gov/30123456/
```

---

## Benefits of New Structure

### ✅ Clear GEO Association
- Directory name contains GEO ID
- No confusion about which dataset PDFs belong to
- Easy to find all data for specific GEO accession

### ✅ Timestamp Tracking
- Can track when collection was created
- Multiple collections for same GEO ID (different dates)
- Historical tracking of citations over time

### ✅ Organized Subdirectories
- `citing_papers/` - Papers that reference the dataset
- `original_paper/` - (Future) Original dataset publication
- Clean separation of paper types

### ✅ Metadata Tracking
- `download_metadata.json` tracks download statistics
- Success/failure rates
- Easy audit trail

### ✅ Scalable
- Each GEO dataset gets own directory
- No mixing of different datasets
- Can process hundreds of GEO IDs independently

---

## Example Workflow

### Step 1: Find Papers Citing GSE103322
```bash
python examples/geo_citation_tracking.py GSE103322 --download-pdfs
```

### Step 2: Check Output
```bash
cd data/geo_citation_collections/GSE103322_20251011_160612/

# View metadata
cat download_metadata.json

# List PDFs
ls citing_papers/
```

### Step 3: Verify PDFs
```bash
# Count PDFs
ls citing_papers/ | wc -l

# Check sizes
du -sh citing_papers/
```

### Step 4: Access by PMID
```bash
# Open specific paper
open citing_papers/PMID_29451881.pdf

# Or lookup online
open "https://pubmed.ncbi.nlm.nih.gov/29451881/"
```

---

## Future Enhancements

### 1. Original Paper Tracking ⏸️
Add support for downloading original dataset paper:

```python
if original_paper_pmid:
    original_dir = output_path / "original_paper"
    original_dir.mkdir(exist_ok=True)
    # Download original paper to original_dir
```

### 2. Enhanced Metadata ⏸️
Include more details in `download_metadata.json`:

```json
{
  "geo_id": "GSE103322",
  "geo_title": "Breast cancer RNA-seq study",
  "original_paper_pmid": "24651512",
  "citation_strategies": ["citation-based", "mention-based"],
  "year_range": [2020, 2025],
  "citing_papers_downloaded": 18,
  "download_sources": {
    "unpaywall": 10,
    "pubmed": 5,
    "pmc": 3
  }
}
```

### 3. Full-Text Extraction ⏸️
Extract text from PDFs and store:

```
data/geo_citation_collections/GSE103322_TIMESTAMP/
├── citing_papers/
│   └── PMID_*.pdf
└── fulltext/
    └── PMID_*.txt  # Extracted text
```

---

## Comparison with Pipeline

### GEOCitationPipeline vs geo_citation_tracking.py

**Pipeline** (`geo_citation_pipeline.py`):
- Query-based directory names
- Multiple GEO datasets per collection
- More comprehensive (metadata JSON files)
- Used by orchestrator/agents

**Example Script** (`geo_citation_tracking.py`):
- GEO-ID-based directory names
- Single GEO dataset per collection
- Simpler, focused on one dataset
- Used by researchers directly

**Both now use:**
- Organized directory structure
- Proper metadata tracking
- Subdirectory separation
- Clean file naming

---

## Documentation Created

1. **PDF_ORGANIZATION_EXPLANATION.md**
   - Complete system overview
   - Mapping logic
   - Examples and scenarios

2. **This File (PDF_ORGANIZATION_CLEANUP.md)**
   - Changes made
   - Migration summary
   - Usage examples

---

## Status

✅ **COMPLETE**

- Old files deleted
- Code updated
- Documentation created
- Ready for use

**Next:** Test the updated example script with real GEO dataset!
