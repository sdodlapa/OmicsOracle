# Integration Guide: OmicsOracle Pipeline Architecture

**Date:** October 14, 2024  
**Version:** v2.0.0  
**Status:** ✅ Complete

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Integration Contracts](#integration-contracts)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Performance Guidelines](#performance-guidelines)
7. [Common Patterns](#common-patterns)
8. [Migration Guide](#migration-guide)

---

## Overview

Omics Oracle uses a **4-stage pipeline architecture** where each pipeline has a single, well-defined responsibility. This guide shows how to integrate these pipelines correctly.

### The Four Pipelines

| Pipeline | Name | Responsibility | Input | Output |
|----------|------|----------------|-------|--------|
| **P1** | Citation Discovery | Find publications from GEO datasets | GEO ID (e.g., GSE12345) | List of PMIDs/DOIs |
| **P2** | URL Discovery | Find all possible PDF/fulltext URLs | Publication metadata (PMID/DOI) | List of candidate URLs |
| **P3** | PDF Acquisition | Download PDFs using URL fallback strategy | URLs + metadata | Local PDF file |
| **P4** | Content Extraction | Parse and enrich PDF content | PDF file path + metadata | Structured content |

### 🎯 Key Naming Clarity

**Why "Discovery" vs "Collection" vs "Acquisition"?**

- **P1 - Citation Discovery:** You *discover* which papers exist (searching/finding)
- **P2 - URL Discovery:** You *discover* where PDFs might be located (searching/finding URLs, NO downloading)
- **P3 - PDF Acquisition:** You *acquire* the actual file (downloading/retrieving)
- **P4 - Content Extraction:** You *extract* structured data (parsing/enriching)

**The Critical Distinction:**
- **P2 does NOT download** - It only finds URLs and returns a list
- **P3 does the downloading** - It takes the URL list and actually fetches files

Think of it like:
- P2 = "Here are 10 addresses where the book might be available"
- P3 = "Let me go to those addresses and actually get you the book"

### Key Principle: **Single Responsibility**

✅ **CORRECT:** Each pipeline does ONE thing well  
❌ **INCORRECT:** Pipelines mixing responsibilities (downloading + parsing)

**Visual Analogy:**
```
P1: Citation Discovery    = "Find the book titles you need"
                             📚 → [Book1, Book2, Book3]

P2: URL Discovery        = "Find addresses where books are sold"
                             📚 → [Store1 URL, Store2 URL, Library URL]
                             ⚠️  NO BUYING YET - just making a list!

P3: PDF Acquisition      = "Go to stores and buy the books"
                             [URLs] → 📦 (actual file downloaded)
                             ✅ Now you have the physical book!

P4: Content Extraction   = "Read and summarize the book"
                             📦 → 📝 (sections, tables, references)
```

---

## Pipeline Architecture

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OMICSORAL PIPELINE FLOW                       │
└─────────────────────────────────────────────────────────────────────┘

 INPUT: GEO Dataset ID (e.g., "GSE12345")
   │
   ▼
┌──────────────────────────────────────────┐
│  PIPELINE 1: Citation Discovery          │
│  - Query GEO database                    │
│  - Extract PMIDs/DOIs from citations     │
│  - Return publication identifiers        │
└──────────────────────────────────────────┘
   │
   │ OUTPUT: [PMID:12345678, DOI:10.1234/...]
   │         (Publication metadata objects)
   ▼
┌──────────────────────────────────────────┐
│  PIPELINE 2: URL Discovery               │
│  - Query 10+ sources in PARALLEL         │
│  - PMC, Unpaywall, CORE, Sci-Hub, etc.   │
│  - Find ALL possible PDF URLs            │
│  - NO downloading - just collect URLs!   │
└──────────────────────────────────────────┘
   │
   │ OUTPUT: [URL1, URL2, URL3, ...]
   │         (Sorted by priority/source)
   ▼
┌──────────────────────────────────────────┐
│  PIPELINE 3: PDF Acquisition             │
│  - Try each URL in fallback order        │
│  - Validate PDF (magic bytes check)      │
│  - Save to local storage                 │
│  - Stop at first successful download     │
└──────────────────────────────────────────┘
   │
   │ OUTPUT: Path("data/pdfs/12345678.pdf")
   │         (Local file on disk)
   ▼
┌──────────────────────────────────────────┐
│  PIPELINE 4: Content Extraction          │
│  - Parse PDF text (pypdf)                │
│  - Detect sections (7 canonical)         │
│  - Extract tables and references         │
│  - Format for ChatGPT analysis           │
│  - Calculate quality score (A-F)         │
└──────────────────────────────────────────┘
   │
   │ OUTPUT: {
   │   "sections": {...},
   │   "tables": [...],
   │   "references": [...],
   │   "quality_score": 0.85,
   │   "chatgpt_prompt": "..."
   │ }
   ▼
 RESULT: Structured, enriched content ready for analysis
```

---

## Integration Contracts

### Contract 1: P1 → P2 (Citation Discovery → URL Discovery)

**P1 Output Format:**
```python
{
    "geo_id": "GSE12345",
    "pmids": ["12345678", "87654321"],
    "dois": ["10.1234/example", "10.5678/another"],
    "publications": [Publication(...), Publication(...)]
}
```

**P2 Input Requirements:**
```python
# P2 needs a Publication object with at least one identifier
Publication(
    pmid="12345678",              # Preferred
    doi="10.1234/example",        # Alternative
    title="Research Paper Title"  # Fallback for searching
)
```

**Integration Example:**
```python
from omics_oracle_v2.lib.pipelines import GEOCitationCollector
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager

# P1: Discover citations from GEO dataset
geo_collector = GEOCitationCollector()
citations = geo_collector.collect(geo_id="GSE12345")

# P2: Discover URLs for each publication (NO downloading yet!)
url_manager = FullTextManager()
await url_manager.initialize()

for publication in citations["publications"]:
    result = await url_manager.get_all_fulltext_urls(publication)
    if result.success:
        print(f"Found {len(result.all_urls)} URLs for {publication.pmid}")
        print(f"  Sources: {', '.join(result.metadata.get('source_counts', {}).keys())}")

await url_manager.cleanup()
```

---

### Contract 2: P2 → P3 (URL Discovery → PDF Acquisition)

**P2 Output Format:**
```python
FullTextResult(
    success=True,
    all_urls=[
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/",
        "https://unpaywall.org/...",
        "https://core.ac.uk/download/pdf/...",
    ],
    metadata={
        "pmc_id": "PMC123456",
        "source_counts": {"pmc": 1, "unpaywall": 1, "core": 1}
    }
)
```

**P3 Input Requirements:**
```python
# P3 needs:
# 1. Publication object (for metadata/filename)
# 2. List of URLs to try
# 3. Output directory

await pdf_manager.download_with_fallback(
    publication=publication,      # From P1/P2
    urls=result.all_urls,         # From P2
    output_dir=Path("data/pdfs")  # Where to save
)
```

**Integration Example:**
```python
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from pathlib import Path

# P2: Discover all possible URLs (NO downloading!)
url_manager = FullTextManager()
await url_manager.initialize()
urls_result = await url_manager.get_all_fulltext_urls(publication)

if urls_result.success:
    print(f"P2: Discovered {len(urls_result.all_urls)} candidate URLs")
    
    # P3: Actually download the PDF (tries URLs with smart fallback)
    pdf_manager = PDFDownloadManager(
        max_concurrent=5,
        validate_pdf=True,
        max_retries=3
    )
    
    pdf_path = await pdf_manager.download_with_fallback(
        publication=publication,
        urls=urls_result.all_urls,
        output_dir=Path("data/pdfs")
    )
    
    if pdf_path:
        print(f"P3: Acquired PDF: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")

await url_manager.cleanup()
```

---

### Contract 3: P3 → P4 (PDF Acquisition → Content Extraction)

**P3 Output Format:**
```python
# Returns Path object to local PDF file
Path("data/pdfs/12345678.pdf")
```

**P4 Input Requirements:**
```python
# P4 needs:
# 1. Path to PDF file
# 2. Optional metadata for enrichment

extractor.extract_text(
    pdf_path=Path("data/pdfs/12345678.pdf"),  # From P3
    metadata={                                 # Optional but recommended
        "pmid": "12345678",
        "doi": "10.1234/example",
        "title": "Research Paper",
        "authors": "Smith J, et al.",
        "journal": "Nature",
        "year": 2024
    }
)
```

**Integration Example:**
```python
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
from pathlib import Path

# P3: Download PDF
pdf_manager = PDFDownloadManager()
pdf_path = await pdf_manager.download_with_fallback(
    publication, urls, Path("data/pdfs")
)

if pdf_path and pdf_path.exists():
    # P4: Extract and enrich content
    extractor = PDFExtractor(enable_enrichment=True)
    
    enriched = extractor.extract_text(
        pdf_path=pdf_path,
        metadata={
            "pmid": publication.pmid,
            "doi": publication.doi,
            "title": publication.title,
            "authors": publication.authors,
            "journal": publication.journal,
            "year": publication.year
        }
    )
    
    print(f"Quality Score: {enriched['quality_score']:.2f}")
    print(f"Sections: {list(enriched['sections'].keys())}")
    print(f"Tables: {enriched['table_count']}")
    print(f"References: {enriched['reference_count']}")
    print(f"DOIs found: {len(enriched['dois_found'])}")
```

---

## Complete Examples

### Example 1: Single Publication (P1→P2→P3→P4)

```python
import asyncio
from pathlib import Path

from omics_oracle_v2.lib.pipelines import GEOCitationCollector
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor


async def process_single_geo_publication(geo_id: str):
    """Complete pipeline: Citation Discovery → URL Discovery → PDF Acquisition → Content Extraction."""
    
    # P1: Discover citations from GEO
    print(f"\n{'='*60}")
    print(f"PIPELINE 1: CITATION DISCOVERY - Finding publications from {geo_id}")
    print(f"{'='*60}")
    
    geo_collector = GEOCitationCollector()
    citations = geo_collector.collect(geo_id=geo_id)
    
    if not citations["publications"]:
        print(f"❌ No publications found for {geo_id}")
        return None
    
    publication = citations["publications"][0]  # Take first publication
    print(f"✅ Discovered publication: {publication.title[:60]}...")
    print(f"   PMID: {publication.pmid}, DOI: {publication.doi}")
    
    # P2: Discover fulltext URLs (NO downloading yet!)
    print(f"\n{'='*60}")
    print(f"PIPELINE 2: URL DISCOVERY - Finding PDF locations (not downloading)")
    print(f"{'='*60}")
    
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    try:
        urls_result = await url_manager.get_all_fulltext_urls(publication)
        
        if not urls_result.success:
            print(f"❌ No URLs found")
            return None
        
        print(f"✅ Discovered {len(urls_result.all_urls)} candidate URLs:")
        for i, url in enumerate(urls_result.all_urls[:5], 1):
            print(f"   {i}. {url[:80]}...")
        print(f"   ⚠️  URLs found, but NOT downloaded yet!")
        
        # P3: Acquire the actual PDF file
        print(f"\n{'='*60}")
        print(f"PIPELINE 3: PDF ACQUISITION - Downloading from discovered URLs")
        print(f"{'='*60}")
        
        pdf_manager = PDFDownloadManager(
            max_concurrent=5,
            validate_pdf=True,
            max_retries=3,
            timeout_seconds=30
        )
        
        output_dir = Path("data/pdfs")
        pdf_path = await pdf_manager.download_with_fallback(
            publication=publication,
            urls=urls_result.all_urls,
            output_dir=output_dir
        )
        
        if not pdf_path:
            print(f"❌ PDF acquisition failed from all {len(urls_result.all_urls)} URLs")
            return None
        
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"✅ Acquired PDF: {pdf_path.name} ({file_size_mb:.2f} MB)")
        print(f"   ✅ File saved locally - now we have the actual PDF!")
        
        # P4: Extract and enrich content
        print(f"\n{'='*60}")
        print(f"PIPELINE 4: CONTENT EXTRACTION - Parsing and enriching PDF")
        print(f"{'='*60}")
        
        extractor = PDFExtractor(enable_enrichment=True)
        
        enriched = extractor.extract_text(
            pdf_path=pdf_path,
            metadata={
                "pmid": publication.pmid,
                "doi": publication.doi,
                "title": publication.title,
                "authors": publication.authors,
                "journal": publication.journal,
                "year": publication.year
            }
        )
        
        print(f"✅ Extraction complete!")
        print(f"\n📊 Content Statistics:")
        print(f"   - Pages: {enriched['page_count']}")
        print(f"   - Text length: {enriched['text_length']:,} chars")
        print(f"   - Quality score: {enriched['quality_score']:.2f}")
        print(f"   - Sections: {len(enriched.get('sections', {}))}")
        print(f"   - Tables: {enriched.get('table_count', 0)}")
        print(f"   - References: {enriched.get('reference_count', 0)}")
        print(f"   - DOIs found: {len(enriched.get('dois_found', []))}")
        print(f"   - PMIDs found: {len(enriched.get('pmids_found', []))}")
        
        if enriched.get('sections'):
            print(f"\n📚 Sections detected:")
            for section_name in enriched.get('section_order', []):
                print(f"   - {section_name}")
        
        return enriched
        
    finally:
        await url_manager.cleanup()


# Run the example
if __name__ == "__main__":
    result = asyncio.run(process_single_geo_publication("GSE12345"))
```

---

### Example 2: Batch Processing (100 Papers)

```python
import asyncio
from pathlib import Path
from typing import List

from omics_oracle_v2.lib.pipelines import GEOCitationCollector
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import process_pdfs_batch, QualityScorer


async def process_geo_batch(geo_ids: List[str], max_papers: int = 100):
    """Process multiple GEO datasets through complete pipeline."""
    
    all_publications = []
    
    # P1: Collect citations from all GEO datasets
    print(f"PIPELINE 1: Collecting citations from {len(geo_ids)} GEO datasets")
    geo_collector = GEOCitationCollector()
    
    for geo_id in geo_ids:
        citations = geo_collector.collect(geo_id=geo_id)
        all_publications.extend(citations["publications"])
        
        if len(all_publications) >= max_papers:
            break
    
    all_publications = all_publications[:max_papers]
    print(f"✅ Collected {len(all_publications)} publications")
    
    # P2: Collect URLs for all publications (in parallel)
    print(f"\nPIPELINE 2: Collecting URLs for {len(all_publications)} publications")
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    try:
        # Collect URLs for all publications in batch
        url_tasks = [
            url_manager.get_all_fulltext_urls(pub)
            for pub in all_publications
        ]
        url_results = await asyncio.gather(*url_tasks)
        
        # Filter successful results
        successful_urls = [
            (pub, result.all_urls)
            for pub, result in zip(all_publications, url_results)
            if result.success and result.all_urls
        ]
        
        print(f"✅ Found URLs for {len(successful_urls)}/{len(all_publications)} publications")
        
        # P3: Download PDFs in batch
        print(f"\nPIPELINE 3: Downloading {len(successful_urls)} PDFs")
        pdf_manager = PDFDownloadManager(
            max_concurrent=10,
            validate_pdf=True,
            max_retries=3
        )
        
        output_dir = Path("data/pdfs")
        download_tasks = [
            pdf_manager.download_with_fallback(pub, urls, output_dir)
            for pub, urls in successful_urls
        ]
        
        pdf_paths = await asyncio.gather(*download_tasks)
        
        # Filter successful downloads
        successful_pdfs = [
            path for path in pdf_paths
            if path and path.exists()
        ]
        
        print(f"✅ Downloaded {len(successful_pdfs)}/{len(successful_urls)} PDFs")
        
        # P4: Batch process all PDFs with enrichment
        print(f"\nPIPELINE 4: Processing {len(successful_pdfs)} PDFs")
        
        batch_result = await process_pdfs_batch(
            pdf_paths=successful_pdfs,
            max_concurrent=10,
            enable_enrichment=True,
            timeout_per_pdf=120,
            output_dir=Path("data/enriched")
        )
        
        print(f"\n{'='*60}")
        print(f"FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Total publications: {len(all_publications)}")
        print(f"URLs found: {len(successful_urls)} ({len(successful_urls)/len(all_publications)*100:.1f}%)")
        print(f"PDFs downloaded: {len(successful_pdfs)} ({len(successful_pdfs)/len(all_publications)*100:.1f}%)")
        print(f"Enrichment success: {batch_result.successful}/{batch_result.total_pdfs} ({batch_result.success_rate:.1f}%)")
        print(f"Processing time: {batch_result.processing_time:.1f}s")
        print(f"Avg time per PDF: {batch_result.processing_time/batch_result.total_pdfs:.1f}s")
        
        # Quality distribution
        if batch_result.results:
            grades = {}
            for item in batch_result.results:
                enriched = item["enrichment"]
                metrics = QualityScorer.score_content(enriched)
                grades[metrics.grade] = grades.get(metrics.grade, 0) + 1
            
            print(f"\nQuality Distribution:")
            for grade in ["A", "B", "C", "D", "F"]:
                count = grades.get(grade, 0)
                if count > 0:
                    print(f"   Grade {grade}: {count} papers ({count/batch_result.successful*100:.1f}%)")
        
        # Filter high-quality results
        high_quality = QualityScorer.filter_by_quality(
            enriched_list=batch_result.results,
            min_score=0.7,
            min_grade="B"
        )
        
        print(f"\nHigh-quality papers (≥B grade): {len(high_quality)}/{batch_result.successful} ({len(high_quality)/batch_result.successful*100:.1f}%)")
        
        return batch_result
        
    finally:
        await url_manager.cleanup()


# Run batch processing
if __name__ == "__main__":
    geo_ids = ["GSE12345", "GSE67890", "GSE11111"]  # Add your GEO IDs
    result = asyncio.run(process_geo_batch(geo_ids, max_papers=100))
```

---

## Error Handling

### Pattern 1: Graceful Degradation

```python
async def process_with_fallback(publication):
    """Process publication with graceful fallback at each stage."""
    
    # P2: Try to get URLs
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    try:
        urls_result = await url_manager.get_all_fulltext_urls(publication)
        
        if not urls_result.success:
            logger.warning(f"No URLs found for {publication.pmid}")
            return None  # Can't proceed without URLs
        
        # P3: Try to download PDF
        pdf_manager = PDFDownloadManager()
        pdf_path = await pdf_manager.download_with_fallback(
            publication, urls_result.all_urls, output_dir
        )
        
        if not pdf_path:
            logger.warning(f"PDF download failed for {publication.pmid}")
            return None  # Can't proceed without PDF
        
        # P4: Try to extract content
        try:
            extractor = PDFExtractor(enable_enrichment=True)
            enriched = extractor.extract_text(pdf_path, metadata={...})
            
            # Check quality
            if enriched['quality_score'] < 0.3:
                logger.warning(f"Low quality extraction for {publication.pmid}")
                # Still return result but flag it
                enriched['quality_warning'] = True
            
            return enriched
            
        except Exception as e:
            logger.error(f"Extraction failed for {publication.pmid}: {e}")
            # Return basic info even if enrichment fails
            return {
                "pmid": publication.pmid,
                "pdf_path": str(pdf_path),
                "error": str(e),
                "fallback": True
            }
    
    finally:
        await url_manager.cleanup()
```

### Pattern 2: Retry Logic

```python
async def process_with_retry(publication, max_retries: int = 3):
    """Process publication with retry logic."""
    
    for attempt in range(max_retries):
        try:
            result = await process_publication(publication)
            return result  # Success!
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
    
    return None  # All retries failed
```

---

## Performance Guidelines

### Concurrency Settings

| Pipeline | Recommended max_concurrent | Reasoning |
|----------|---------------------------|-----------|
| **P2** (URL Collection) | 20-50 | IO-bound, many APIs tolerate high concurrency |
| **P3** (PDF Download) | 5-10 | Bandwidth-limited, be respectful to servers |
| **P4** (Text Enrichment) | 10-20 | CPU-bound but async IO for file operations |

### Timeout Settings

| Operation | Recommended Timeout | Reasoning |
|-----------|-------------------|-----------|
| **URL API call** | 10s | Most APIs respond <5s |
| **PDF download** | 30s | Large files need time |
| **PDF parsing** | 120s | Complex PDFs can take time |
| **Batch processing** | No timeout | Let individual timeouts handle it |

### Caching Strategy

```python
# P2: URL caching (save API calls)
url_manager = FullTextManager(
    config=FullTextManagerConfig(
        enable_cache=True,
        cache_ttl_days=30  # URLs rarely change
    )
)

# P4: Parsed content caching (save parsing time)
extractor = PDFExtractor(enable_enrichment=True)
# Caching is automatic - parsed content cached for 90 days
```

---

## Common Patterns

### Pattern 1: Process Publications from CSV

```python
import pandas as pd
from pathlib import Path

async def process_from_csv(csv_path: Path):
    """Process publications from CSV file."""
    
    # Load publications
    df = pd.read_csv(csv_path)
    publications = [
        Publication(
            pmid=row['pmid'],
            doi=row.get('doi'),
            title=row['title']
        )
        for _, row in df.iterrows()
    ]
    
    # Process through pipelines
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    results = []
    
    for pub in publications:
        # P2→P3→P4
        result = await process_publication(pub)
        if result:
            results.append(result)
    
    await url_manager.cleanup()
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv("results.csv", index=False)
```

### Pattern 2: Incremental Processing with Checkpoint

```python
import json
from pathlib import Path

async def process_with_checkpoint(publications: List, checkpoint_file: Path):
    """Process publications with checkpointing for resumability."""
    
    # Load checkpoint
    processed_pmids = set()
    if checkpoint_file.exists():
        checkpoint = json.loads(checkpoint_file.read_text())
        processed_pmids = set(checkpoint.get('processed', []))
        print(f"Resuming from checkpoint: {len(processed_pmids)} already processed")
    
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    try:
        for i, pub in enumerate(publications):
            # Skip if already processed
            if pub.pmid in processed_pmids:
                continue
            
            # Process
            result = await process_publication(pub)
            
            # Update checkpoint
            processed_pmids.add(pub.pmid)
            
            # Save checkpoint every 10 publications
            if (i + 1) % 10 == 0:
                checkpoint_file.write_text(json.dumps({
                    'processed': list(processed_pmids),
                    'total': len(publications),
                    'progress': (i + 1) / len(publications)
                }))
                print(f"Checkpoint saved: {i + 1}/{len(publications)}")
    
    finally:
        await url_manager.cleanup()
```

---

## Migration Guide

### Migrating from Old Approach (Deprecated)

**OLD APPROACH (Deprecated - Mixed Responsibilities):**
```python
# ❌ BAD: P2 doing P3+P4 work
manager = FullTextManager()
await manager.initialize()

# This violates pipeline separation!
content = await manager.get_parsed_content(publication)  # Downloads AND parses

await manager.cleanup()
```

**NEW APPROACH (Correct - Clean Separation):**
```python
# ✅ GOOD: Each pipeline does its job
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor

# P2: Collect URLs ONLY
url_manager = FullTextManager()
await url_manager.initialize()
urls_result = await url_manager.get_all_fulltext_urls(publication)

# P3: Download PDF ONLY
pdf_manager = PDFDownloadManager()
pdf_path = await pdf_manager.download_with_fallback(
    publication, urls_result.all_urls, output_dir
)

# P4: Parse and enrich ONLY
extractor = PDFExtractor(enable_enrichment=True)
content = extractor.extract_text(pdf_path, metadata={...})

await url_manager.cleanup()
```

### Why the Change?

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Responsibilities** | P2 does URLs + Download + Parse | Each pipeline has ONE job |
| **Testability** | Hard to test individual steps | Easy to test each pipeline |
| **Flexibility** | Can't use PDF without parsing | Can download without parsing |
| **Performance** | Sequential (slow) | Parallel where possible (fast) |
| **Maintainability** | Changes affect multiple concerns | Changes isolated to one pipeline |
| **Error Handling** | Unclear where failures occur | Clear pipeline boundaries |

---

## Summary

### Key Takeaways

1. ✅ **Use ALL four pipelines** - Don't skip steps or mix responsibilities
2. ✅ **P2 collects URLs** - Use `get_all_fulltext_urls()` for maximum coverage
3. ✅ **P3 downloads PDFs** - Use `download_with_fallback()` for smart retry
4. ✅ **P4 enriches content** - Use `PDFExtractor(enable_enrichment=True)` for structured data
5. ✅ **Handle errors gracefully** - Each pipeline can fail independently
6. ✅ **Use async/await** - Maximize concurrency for better performance
7. ✅ **Cache aggressively** - URLs and parsed content are expensive to generate

### Quick Reference

```python
# COMPLETE PIPELINE (Copy-paste template)
import asyncio
from pathlib import Path

from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor

async def process_complete(publication):
    # P2: URLs
    url_manager = FullTextManager()
    await url_manager.initialize()
    urls = await url_manager.get_all_fulltext_urls(publication)
    
    # P3: PDF
    pdf_manager = PDFDownloadManager()
    pdf_path = await pdf_manager.download_with_fallback(
        publication, urls.all_urls, Path("data/pdfs")
    )
    
    # P4: Enrich
    extractor = PDFExtractor(enable_enrichment=True)
    content = extractor.extract_text(pdf_path, metadata={...})
    
    await url_manager.cleanup()
    return content

# Run
result = asyncio.run(process_complete(publication))
```

---

**Questions?** See:
- `docs/PIPELINE2_CLEANUP_PLAN.md` - Deprecation details
- `docs/PIPELINE4_IMPLEMENTATION_COMPLETE.md` - P4 features
- `docs/WATERFALL_FIX_COMPLETE.md` - P3 download strategy
- `README.md` - Project overview

**Last Updated:** October 14, 2024
