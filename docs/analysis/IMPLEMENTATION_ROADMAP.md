# Implementation Roadmap: Smart Full-Text Cache System

**Date:** October 11, 2025  
**Goal:** Implement multi-level caching with local file checking before API calls

---

## Current State Analysis

### What We Have ✅

```python
# Current waterfall (manager.py lines 713-745)
sources = [
    ("cache", self._check_cache),              # ✅ Checks data/fulltext/pdf/{hash}.pdf
    ("institutional", self._try_institutional_access),
    ("unpaywall", self._try_unpaywall),
    ("core", self._try_core),
    ("openalex_oa", self._try_openalex_oa_url),
    ("crossref", self._try_crossref),
    ("biorxiv", self._try_biorxiv),
    ("arxiv", self._try_arxiv),
    ("scihub", self._try_scihub),
    ("libgen", self._try_libgen),
]
```

### Current Cache (lines 319-340)
```python
async def _check_cache(self, publication: Publication) -> FullTextResult:
    """Check if full-text is already cached."""
    cache_path = self._get_cache_path(publication)
    
    if cache_path.exists() and cache_path.stat().st_size > 0:
        logger.info(f"Found cached PDF for {publication.title[:50]}...")
        return FullTextResult(
            success=True,
            source=FullTextSource.CACHE,
            pdf_path=cache_path,
            metadata={"cached": True, "size": cache_path.stat().st_size},
        )
    
    return FullTextResult(success=False, error="Not in cache")
```

**Problem:** Only checks single location (`data/fulltext/pdf/{hash}.pdf`)

---

## What We Need 🎯

### Multi-Location File Check

Currently PDFs are saved in multiple locations:
```
data/fulltext/
├── pdf/
│   ├── {hash}.pdf              # Current cache location ✅
│   ├── arxiv/
│   │   └── {arxiv_id}.pdf      # Missing from check ❌
│   ├── pmc/
│   │   └── {pmc_id}.pdf        # Missing from check ❌
│   ├── publisher/              # Missing from check ❌
│   └── institutional/          # Missing from check ❌
├── xml/
│   └── pmc/
│       └── PMC{id}.nxml        # Not checked at all! ❌
└── parsed/                      # Doesn't exist yet ❌
    └── {id}.json               # Future: parsed cache
```

### Smart Source Classification

**Category A: Check local files BEFORE API**
- arXiv (might already be in data/fulltext/pdf/arxiv/)
- PMC (might already be in data/fulltext/xml/pmc/ OR data/fulltext/pdf/pmc/)
- bioRxiv (might already be in data/fulltext/pdf/biorxiv/)
- Publisher downloads (data/fulltext/pdf/publisher/)
- Institutional (data/fulltext/pdf/institutional/)

**Category B: API-only (no local files)**
- Unpaywall (just provides links)
- CORE (just provides links)
- OpenAlex (just provides links)
- Crossref (just provides links)
- Sci-Hub (downloads directly)
- LibGen (downloads directly)

---

## Implementation Plan

### Phase 1: Enhanced Local File Check (This Week) 🎯

**Goal:** Check ALL possible local file locations before hitting ANY API

**Files to Modify:**
1. `lib/fulltext/manager.py` - Enhance `_check_cache()`
2. Add `lib/fulltext/smart_cache.py` - Multi-level cache manager

**Implementation:**

```python
# NEW: lib/fulltext/smart_cache.py

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LocalFileResult:
    """Result from local file search."""
    found: bool
    file_path: Optional[Path] = None
    file_type: Optional[str] = None  # 'pdf', 'xml', 'nxml'
    source: Optional[str] = None     # 'arxiv', 'pmc', 'institutional', etc.
    size_bytes: Optional[int] = None


class SmartCache:
    """
    Multi-level cache manager for full-text content.
    
    Checks:
    1. Parsed JSON cache (fastest)
    2. Local XML files (high quality)
    3. Local PDF files (multiple locations)
    """
    
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path("data/fulltext")
        
        self.base_dir = base_dir
        self.pdf_dir = base_dir / "pdf"
        self.xml_dir = base_dir / "xml"
        self.parsed_dir = base_dir / "parsed"
        
        # Ensure directories exist
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.xml_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
    
    def find_local_file(self, publication) -> LocalFileResult:
        """
        Search for any locally stored file for this publication.
        
        Priority:
        1. XML files (best quality for parsing)
        2. PDF files (multiple possible locations)
        
        Returns:
            LocalFileResult with file info if found
        """
        
        # Extract identifiers
        doi = publication.doi
        pmid = publication.pmid
        pmc_id = publication.pmc_id
        title = publication.title
        
        # Generate possible IDs
        ids_to_check = []
        
        if pmc_id:
            ids_to_check.append(('pmc', pmc_id))
            ids_to_check.append(('pmc', f'PMC{pmc_id}'))
        
        if pmid:
            ids_to_check.append(('pmid', pmid))
        
        if doi:
            # DOI might be used as filename (sanitized)
            sanitized_doi = doi.replace('/', '_').replace('.', '_')
            ids_to_check.append(('doi', sanitized_doi))
            
            # Check if arXiv
            if 'arxiv' in doi.lower():
                arxiv_id = doi.split('/')[-1]
                ids_to_check.append(('arxiv', arxiv_id))
        
        # 1. CHECK XML FILES FIRST (best quality)
        xml_result = self._check_xml_files(ids_to_check)
        if xml_result.found:
            return xml_result
        
        # 2. CHECK PDF FILES (multiple locations)
        pdf_result = self._check_pdf_files(ids_to_check, publication)
        if pdf_result.found:
            return pdf_result
        
        # Not found
        return LocalFileResult(found=False)
    
    def _check_xml_files(self, ids_to_check: List[tuple]) -> LocalFileResult:
        """Check for XML files."""
        
        # PMC XML files
        pmc_xml_dir = self.xml_dir / "pmc"
        if pmc_xml_dir.exists():
            for id_type, id_value in ids_to_check:
                if id_type in ['pmc', 'pmid']:
                    # Try various naming patterns
                    patterns = [
                        f"{id_value}.nxml",
                        f"{id_value}.xml",
                        f"PMC{id_value}.nxml",
                    ]
                    
                    for pattern in patterns:
                        xml_path = pmc_xml_dir / pattern
                        if xml_path.exists() and xml_path.stat().st_size > 0:
                            logger.info(f"✓ Found local XML: {xml_path}")
                            return LocalFileResult(
                                found=True,
                                file_path=xml_path,
                                file_type='nxml',
                                source='pmc_xml',
                                size_bytes=xml_path.stat().st_size
                            )
        
        return LocalFileResult(found=False)
    
    def _check_pdf_files(self, ids_to_check: List[tuple], publication) -> LocalFileResult:
        """
        Check for PDF files in multiple possible locations.
        
        Locations:
        - data/fulltext/pdf/arxiv/
        - data/fulltext/pdf/pmc/
        - data/fulltext/pdf/institutional/
        - data/fulltext/pdf/publisher/
        - data/fulltext/pdf/scihub/
        - data/fulltext/pdf/{hash}.pdf (current cache)
        """
        
        # Define search locations
        pdf_locations = [
            ('arxiv', self.pdf_dir / 'arxiv'),
            ('pmc', self.pdf_dir / 'pmc'),
            ('institutional', self.pdf_dir / 'institutional'),
            ('publisher', self.pdf_dir / 'publisher'),
            ('scihub', self.pdf_dir / 'scihub'),
            ('biorxiv', self.pdf_dir / 'biorxiv'),
            ('cache', self.pdf_dir),  # Root cache directory
        ]
        
        # Check each location
        for source, location in pdf_locations:
            if not location.exists():
                continue
            
            # Try each identifier
            for id_type, id_value in ids_to_check:
                # Skip irrelevant combinations
                if source == 'arxiv' and id_type != 'arxiv':
                    continue
                if source == 'pmc' and id_type not in ['pmc', 'pmid']:
                    continue
                
                # Try file
                pdf_path = location / f"{id_value}.pdf"
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    logger.info(f"✓ Found local PDF: {pdf_path}")
                    return LocalFileResult(
                        found=True,
                        file_path=pdf_path,
                        file_type='pdf',
                        source=source,
                        size_bytes=pdf_path.stat().st_size
                    )
        
        # Check hash-based cache (current system)
        hash_path = self._get_hash_cache_path(publication)
        if hash_path and hash_path.exists() and hash_path.stat().st_size > 0:
            logger.info(f"✓ Found cached PDF: {hash_path}")
            return LocalFileResult(
                found=True,
                file_path=hash_path,
                file_type='pdf',
                source='cache',
                size_bytes=hash_path.stat().st_size
            )
        
        return LocalFileResult(found=False)
    
    def _get_hash_cache_path(self, publication) -> Optional[Path]:
        """Get hash-based cache path (current system)."""
        try:
            import hashlib
            
            # Generate hash from DOI or title
            if publication.doi:
                hash_input = publication.doi
            elif publication.title:
                hash_input = publication.title
            else:
                return None
            
            file_hash = hashlib.md5(hash_input.encode()).hexdigest()
            return self.pdf_dir / f"{file_hash}.pdf"
        except:
            return None
    
    def save_file(
        self,
        content: bytes,
        publication,
        source: str,
        file_type: str = 'pdf'
    ) -> Path:
        """
        Save downloaded file to appropriate location.
        
        Args:
            content: File content as bytes
            publication: Publication object
            source: Source name ('arxiv', 'pmc', 'institutional', etc.)
            file_type: File type ('pdf', 'xml', 'nxml')
        
        Returns:
            Path where file was saved
        """
        
        # Determine save location
        if file_type in ['xml', 'nxml']:
            base_dir = self.xml_dir / source
        else:
            base_dir = self.pdf_dir / source
        
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename
        if publication.pmc_id and source == 'pmc':
            filename = f"{publication.pmc_id}.{file_type}"
        elif publication.doi and 'arxiv' in publication.doi.lower():
            arxiv_id = publication.doi.split('/')[-1]
            filename = f"{arxiv_id}.{file_type}"
        elif publication.doi:
            sanitized = publication.doi.replace('/', '_').replace('.', '_')
            filename = f"{sanitized}.{file_type}"
        else:
            # Fallback to hash
            import hashlib
            hash_val = hashlib.md5(publication.title.encode()).hexdigest()
            filename = f"{hash_val}.{file_type}"
        
        # Save file
        file_path = base_dir / filename
        file_path.write_bytes(content)
        
        logger.info(f"💾 Saved {file_type} to: {file_path} ({len(content)} bytes)")
        
        return file_path
```

**Update manager.py:**

```python
# In manager.py, update _check_cache()

async def _check_cache(self, publication: Publication) -> FullTextResult:
    """
    Check if full-text is already available locally.
    
    ENHANCED (Oct 11, 2025):
    - Checks ALL possible local file locations
    - Prioritizes XML over PDF (better quality)
    - Checks multiple naming patterns
    """
    from omics_oracle_v2.lib.fulltext.smart_cache import SmartCache
    
    cache = SmartCache()
    result = cache.find_local_file(publication)
    
    if result.found:
        logger.info(
            f"✓ Found local {result.file_type.upper()}: "
            f"{result.file_path.name} "
            f"({result.size_bytes // 1024} KB, source: {result.source})"
        )
        
        return FullTextResult(
            success=True,
            source=FullTextSource.CACHE,
            pdf_path=result.file_path if result.file_type == 'pdf' else None,
            metadata={
                'cached': True,
                'file_type': result.file_type,
                'source': result.source,
                'size': result.size_bytes,
                'path': str(result.file_path)
            },
        )
    
    logger.debug("No local files found, will try remote sources")
    return FullTextResult(success=False, error="Not in cache")
```

### Phase 2: Save Files by Source (Next Week) 📋

**Goal:** When downloading from API, save to source-specific directory

**Update each source method to save files:**

```python
# Example: Update _try_arxiv() to save downloaded PDFs

async def _try_arxiv(self, publication: Publication) -> FullTextResult:
    """Try to get full-text from arXiv."""
    if not self.config.enable_arxiv or not self.arxiv_client:
        return FullTextResult(success=False, error="arXiv disabled")
    
    try:
        # ... existing code to get PDF URL ...
        
        if pdf_url:
            # Download PDF
            pdf_content = await download_file(pdf_url)
            
            # Save to arxiv-specific directory
            from omics_oracle_v2.lib.fulltext.smart_cache import SmartCache
            cache = SmartCache()
            saved_path = cache.save_file(
                content=pdf_content,
                publication=publication,
                source='arxiv',
                file_type='pdf'
            )
            
            return FullTextResult(
                success=True,
                source=FullTextSource.ARXIV,
                url=pdf_url,
                pdf_path=saved_path,  # ← Return saved path
                metadata={'arxiv_id': arxiv_id, 'saved_to': str(saved_path)}
            )
    
    except Exception as e:
        logger.warning(f"arXiv error: {e}")
        return FullTextResult(success=False, error=str(e))
```

**Repeat for:**
- `_try_institutional_access()` → save to `institutional/`
- `_try_biorxiv()` → save to `biorxiv/`
- `_try_scihub()` → save to `scihub/`
- `_try_libgen()` → save to `libgen/`

### Phase 3: Parsed Content Cache (Week 3) 🚀

**Goal:** Cache parsed JSON to avoid re-parsing PDFs

```python
# smart_cache.py - Add methods

async def get_parsed_content(self, publication) -> Optional[Dict]:
    """Get cached parsed content."""
    
    # Determine cache filename
    cache_file = self.parsed_dir / f"{publication.id}.json"
    
    if cache_file.exists():
        import json
        data = json.loads(cache_file.read_text())
        
        # Check if stale (90 days)
        from datetime import datetime, timedelta
        cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at < timedelta(days=90):
            logger.info(f"✓ Parsed cache hit: {cache_file.name}")
            return data
    
    return None

async def save_parsed_content(self, publication, parsed_data: Dict):
    """Save parsed content to cache."""
    import json
    from datetime import datetime
    
    cache_file = self.parsed_dir / f"{publication.id}.json"
    
    data_with_metadata = {
        'publication_id': publication.id,
        'cached_at': datetime.now().isoformat(),
        'parsed_data': parsed_data
    }
    
    cache_file.write_text(json.dumps(data_with_metadata, indent=2))
    logger.info(f"💾 Saved parsed content: {cache_file}")
```

### Phase 4: Database Metadata Index (Week 4) 📊

**Goal:** Quick search without parsing files

```sql
-- New table: fulltext_cache

CREATE TABLE fulltext_cache (
    publication_id TEXT PRIMARY KEY,
    has_fulltext BOOLEAN DEFAULT FALSE,
    source_type TEXT,  -- 'xml', 'pdf'
    source TEXT,       -- 'pmc', 'arxiv', 'institutional', etc.
    file_path TEXT,
    file_size_bytes INTEGER,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,
    table_count INTEGER DEFAULT 0,
    has_tables BOOLEAN DEFAULT FALSE,
    quality_score REAL,
    word_count INTEGER,
    INDEX idx_has_fulltext (has_fulltext),
    INDEX idx_source (source),
    INDEX idx_has_tables (has_tables)
);
```

---

## Expected Performance Improvements

### Before (Current):
```
Request for arXiv paper (already downloaded):
1. Check cache (data/fulltext/pdf/{hash}.pdf) ❌ Not there
2. Try institutional (5s timeout) ❌
3. Try unpaywall API (2s) ❌
4. Try CORE API (2s) ❌
5. Try OpenAlex API (2s) ❌
6. Try Crossref API (2s) ❌
7. Try bioRxiv API (2s) ❌
8. Try arXiv API (2s) ✅ Returns URL
9. Download PDF again (wasted bandwidth)

Total: ~19 seconds + duplicate download
```

### After (Phase 1):
```
Request for arXiv paper (already downloaded):
1. Check smart cache:
   - Check data/fulltext/pdf/{hash}.pdf ❌
   - Check data/fulltext/pdf/arxiv/{arxiv_id}.pdf ✅ FOUND!

Total: <10ms (1900x faster!)
```

### After (Phase 3 - with parsed cache):
```
Request for any paper (parsed before):
1. Check parsed JSON cache ✅ FOUND!

Total: <5ms (instant structure access!)
```

---

## Migration Plan

### Step 1: Deploy smart_cache.py
```bash
# Create new file
touch omics_oracle_v2/lib/fulltext/smart_cache.py

# Copy implementation above
```

### Step 2: Update manager.py
```bash
# Backup current version
cp omics_oracle_v2/lib/fulltext/manager.py omics_oracle_v2/lib/fulltext/manager.py.backup

# Apply changes to _check_cache()
```

### Step 3: Test
```bash
# Run existing tests
pytest tests/lib/fulltext/test_manager.py -v

# Add new tests for smart cache
pytest tests/lib/fulltext/test_smart_cache.py -v
```

### Step 4: Monitor
```bash
# Check logs for cache hits
grep "Found local" logs/fulltext.log

# Should see significant increase in cache hits!
```

---

## Success Metrics

**Week 1 (Smart Cache):**
- [ ] Cache hit rate: 30% → 60% (2x improvement)
- [ ] Average query time: 5s → 2s (2.5x faster)
- [ ] API calls: 100/day → 40/day (60% reduction)

**Week 2 (Source-Specific Storage):**
- [ ] Cache hit rate: 60% → 75%
- [ ] Zero duplicate downloads
- [ ] Clear source attribution

**Week 3 (Parsed Cache):**
- [ ] Parse time: 2s → 10ms (200x faster for cached)
- [ ] Repeated queries: instant
- [ ] Cache hit rate: 75% → 90%

**Week 4 (Database Index):**
- [ ] Searchable metadata
- [ ] Bulk queries efficient
- [ ] Analytics enabled

---

## Next Steps

1. **TODAY:** Create `smart_cache.py` ✅
2. **TODAY:** Update `manager.py` `_check_cache()` 🎯
3. **TODAY:** Write tests for smart cache 📋
4. **TOMORROW:** Update source methods to save files
5. **NEXT WEEK:** Add parsed content caching
6. **WEEK 4:** Add database metadata

Ready to implement Phase 1?
