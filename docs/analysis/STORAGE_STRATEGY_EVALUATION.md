# Critical Evaluation: PDF Storage & Parsing Strategy

**Date:** October 11, 2025
**Question:** Should we parse PDFs and save extracted text, or save PDFs locally then parse?

---

## TL;DR Recommendation

**🎯 HYBRID APPROACH (Best of Both Worlds):**
1. ✅ **Save PDF files locally** (raw source of truth)
2. ✅ **Cache parsed structured content** (for performance)
3. ✅ **Parse on-demand with caching** (flexible, efficient)

**Why:** Balances storage costs, performance, flexibility, and data integrity.

---

## Option 1: Parse & Save Text Only (Discard PDFs)

### Architecture:
```
Download PDF → Parse → Save structured text → Delete PDF
                ↓
        Database/JSON storage
        - tables.json
        - text.txt
        - metadata.json
```

### ✅ Advantages:

1. **Lower Storage Costs**
   - PDFs: ~500KB-5MB each
   - Parsed text: ~50-500KB each
   - **Savings:** 80-90% disk space

2. **Faster Queries**
   - Text already extracted
   - No parsing overhead at query time
   - Direct database access

3. **Simpler Deployment**
   - No PDF viewer needed
   - Just serve text/JSON
   - Easier caching

4. **Better Search Performance**
   - Full-text indexes on extracted content
   - No need to re-parse for search

### ❌ Disadvantages:

1. **❌ CRITICAL: Loss of Source Truth**
   - Can't re-parse if extraction improves
   - Can't verify extraction accuracy
   - Permanent data loss if parser has bugs

2. **❌ CRITICAL: No Error Recovery**
   ```
   Scenario: Parser bug found in tables
   With PDFs:  Re-run parser → Fixed ✅
   Without PDFs: Data lost forever ❌
   ```

3. **❌ CRITICAL: Can't Handle New Requirements**
   ```
   Future needs:
   - Extract images? → Need PDF
   - Extract equations? → Need PDF
   - OCR scanned sections? → Need PDF
   - Different table format? → Need PDF
   ```

4. **❌ Version Control Problems**
   - Extraction quality improves over time
   - Can't upgrade without re-downloading
   - Downloads may fail (papers removed, paywalled)

5. **❌ Legal/Compliance Issues**
   - Some licenses require keeping originals
   - Can't prove extraction fidelity
   - Audit trail broken

### Real-World Impact:
```
Example: We improve table extraction from 95% → 99% accuracy
With PDFs:    Re-parse 10,000 papers in 1 hour ✅
Without PDFs: Re-download? Many failed, paywalled, or gone ❌
              Lost data forever ❌
```

---

## Option 2: Save PDFs Locally, Parse On-Demand

### Architecture:
```
Download PDF → Save to disk → Parse when needed
       ↓              ↓              ↓
   permanent    data/pdfs/    Temporary cache
    storage                   (Redis/memory)
```

### ✅ Advantages:

1. **✅ CRITICAL: Source of Truth Preserved**
   - Can always re-parse
   - Can verify extraction accuracy
   - Can recover from parser bugs

2. **✅ Future-Proof**
   ```
   2025: Extract tables with camelot
   2026: New AI model extracts equations
   2027: Better OCR for figures
   → Same PDFs, better extraction! ✅
   ```

3. **✅ Error Recovery**
   ```python
   if table_extraction_failed:
       # Try different method
       tables = extract_with_pdfplumber(pdf)

   if parser_bug_found:
       # Re-parse all affected papers
       for pdf in affected_pdfs:
           content = new_parser.parse(pdf)
   ```

4. **✅ Legal Compliance**
   - Keep original source
   - Prove extraction fidelity
   - Audit trail intact

5. **✅ Flexible Extraction**
   - Different outputs for different users
   - API can request tables-only, text-only, etc.
   - On-the-fly format conversion

### ❌ Disadvantages:

1. **Higher Storage Costs**
   - 10,000 PDFs × 2MB = 20GB
   - Plus cached extractions
   - **But:** Disk is cheap (~$20/TB)

2. **Parsing Overhead**
   - 3-8 seconds per PDF first time
   - **But:** Cache results after first parse

3. **More Complex System**
   - Need file management
   - Need cache invalidation
   - Need disk space monitoring

4. **Slower Cold Start**
   - First query requires parsing
   - **But:** Pre-warm cache for popular papers

---

## Option 3: HYBRID (Recommended) ⭐

### Architecture:
```
Download PDF
    ↓
Save to disk (permanent)
    ↓
Parse on first access
    ↓
Cache structured content (temporary)
    ↓
Serve from cache (fast)
```

### Implementation:
```python
class FullTextStorage:
    def __init__(self):
        self.pdf_dir = Path("data/pdfs")           # Permanent
        self.cache_dir = Path("data/parsed")       # Cache
        self.db = Database()                       # Metadata only

    async def get_fulltext(self, paper_id: str):
        """Get full-text with smart caching."""

        # 1. Check cache first (fast path)
        cached = await self._check_cache(paper_id)
        if cached and not self._is_stale(cached):
            logger.info(f"✓ Cache hit: {paper_id}")
            return cached

        # 2. Check if PDF exists
        pdf_path = self.pdf_dir / f"{paper_id}.pdf"
        if not pdf_path.exists():
            # Download PDF
            pdf_path = await self._download_pdf(paper_id)

        # 3. Parse PDF (first time or cache stale)
        logger.info(f"Parsing PDF: {paper_id}")
        content = await self._parse_pdf(pdf_path)

        # 4. Cache results
        await self._cache_content(paper_id, content)

        # 5. Store metadata in DB (for search)
        await self.db.store_metadata(
            paper_id,
            title=content.title,
            abstract=content.abstract,
            table_count=len(content.tables),
            pdf_path=str(pdf_path),
            parsed_at=datetime.now()
        )

        return content

    async def _cache_content(self, paper_id: str, content):
        """Cache parsed content."""
        cache_file = self.cache_dir / f"{paper_id}.json"

        # Store structured content as JSON
        with open(cache_file, 'w') as f:
            json.dump({
                'tables': [t.to_dict() for t in content.tables],
                'sections': [s.to_dict() for s in content.sections],
                'metadata': {
                    'cached_at': datetime.now().isoformat(),
                    'parser_version': '1.0',
                    'table_count': len(content.tables),
                }
            }, f)

    def _is_stale(self, cached) -> bool:
        """Check if cache needs refresh."""
        # Refresh if:
        # - Older than 30 days
        # - Parser version changed
        # - Manual invalidation flag
        age = datetime.now() - cached['metadata']['cached_at']
        return age.days > 30
```

### Storage Strategy:
```
data/
├── pdfs/                    # Permanent PDF storage
│   ├── arxiv/
│   │   └── 056d82...pdf    (2.1 MB)
│   ├── pmc/
│   │   └── PMC3166277.pdf  (1.5 MB)
│   └── publisher/
│       └── doi_10.1234.pdf (3.2 MB)
│
├── parsed/                  # Cached extractions
│   ├── 056d82...json       (150 KB) ← Fast access
│   └── PMC3166277.json     (200 KB)
│
└── xml/                     # Original XML (when available)
    └── PMC3166277.nxml     (250 KB)
```

### Cache Invalidation Strategy:
```python
class CacheManager:
    def should_reparse(self, paper_id: str) -> bool:
        """Decide if PDF needs re-parsing."""

        cached = self.get_cached(paper_id)

        # No cache → parse
        if not cached:
            return True

        # Parser upgraded → re-parse
        if cached['parser_version'] < CURRENT_PARSER_VERSION:
            return True

        # Cache too old → re-parse (optional)
        if (datetime.now() - cached['cached_at']).days > 90:
            return True

        # User requested fresh parse → re-parse
        if self.manual_invalidation_flag(paper_id):
            return True

        return False
```

---

## Critical Evaluation: Real-World Scenarios

### Scenario 1: Initial System Build (10,000 papers)

**Approach 1 (Text Only):**
```
Download 10,000 PDFs → Parse → Save text → Delete PDFs
Storage: 1GB (text only)
Query time: 50ms (pre-parsed)
Re-parse ability: ❌ Lost forever
```

**Approach 3 (Hybrid):**
```
Download 10,000 PDFs → Save PDFs → Parse on access → Cache results
Storage: 20GB (PDFs) + 1GB (cache) = 21GB
First query: 5 seconds (parse + cache)
Subsequent queries: 50ms (cache hit)
Re-parse ability: ✅ Anytime
Cost: $0.50/month extra storage
```

**Winner:** Hybrid (+$0.50/month for unlimited re-parsing)

### Scenario 2: Parser Bug Found (affects 1,000 papers)

**Approach 1 (Text Only):**
```
Options:
1. Re-download PDFs → 30% fail (paywalled/removed)
2. Keep bad extractions → Bad data forever
3. Manual fixes → Weeks of work

Impact: Permanent data loss ❌
```

**Approach 3 (Hybrid):**
```
Fix bug → Re-parse 1,000 PDFs → Update cache
Time: 2 hours
Impact: All data corrected ✅
```

**Winner:** Hybrid (2 hours vs weeks/impossible)

### Scenario 3: Feature Upgrade (add equation extraction)

**Approach 1 (Text Only):**
```
Need PDFs → Re-download 10,000 papers
Success rate: 70% (3,000 lost)
Cost: Days of downloading + Lost data

Impact: Feature only works for 70% ❌
```

**Approach 3 (Hybrid):**
```
Add equation extractor → Re-parse existing PDFs
Time: 1 day
Impact: Feature works for 100% ✅
```

**Winner:** Hybrid (1 day vs days + 30% loss)

### Scenario 4: Scale to 1 Million Papers

**Approach 1 (Text Only):**
```
Storage: 50GB (text)
Cost: $1/month
Query speed: 50ms
Flexibility: ❌ None
```

**Approach 3 (Hybrid):**
```
Storage: 2TB (PDFs) + 50GB (cache) = 2.05TB
Cost: $40/month
Query speed: 50ms (cached) / 5s (first time)
Flexibility: ✅ Unlimited

Cache strategy:
- Popular papers: Always cached (fast)
- Rare papers: Parse on-demand
- Cache hit rate: 95% after 1 month
```

**Winner:** Hybrid ($40/month for flexibility worth it at scale)

---

## Storage Cost Analysis

### Current State (10,000 papers):
```
PDFs (average 2MB):       20 GB
Cached JSON (avg 150KB):  1.5 GB
Total:                    21.5 GB

Cost (AWS S3):
- PDFs (infrequent):      $0.50/month
- Cache (standard):       $0.03/month
- Total:                  $0.53/month
```

### At Scale (1 million papers):
```
PDFs:                     2,000 GB (2TB)
Cached JSON:              150 GB
Total:                    2,150 GB

Cost (AWS S3):
- PDFs (infrequent):      $26/month
- Cache (standard):       $3.50/month
- Total:                  $29.50/month

Alternative (local disk):
- 4TB drive:              $100 one-time
- Monthly equivalent:     $4/month (2-year lifespan)
```

**Verdict:** Storage is cheap. Flexibility is priceless.

---

## Performance Comparison

### Query Latency:

| Approach | First Query | Subsequent | Cache Hit Rate |
|----------|-------------|------------|----------------|
| **Text Only** | 50ms | 50ms | 100% (always pre-parsed) |
| **Parse On-Demand** | 5000ms | 5000ms | 0% (always parse) |
| **Hybrid** | 5000ms | 50ms | 95% (after warmup) |

### Optimization Strategies for Hybrid:

1. **Pre-warm Cache for Popular Papers**
   ```python
   # Parse top 1000 most-cited papers at night
   async def warmup_cache():
       popular_papers = get_top_cited(limit=1000)
       for paper in popular_papers:
           await get_fulltext(paper.id)  # Parse & cache
   ```

2. **Background Parsing**
   ```python
   # Parse new papers in background
   async def on_pdf_downloaded(pdf_path):
       asyncio.create_task(parse_and_cache(pdf_path))
       # User doesn't wait
   ```

3. **Smart Caching**
   ```python
   # Cache based on access patterns
   if access_count > 10:
       cache_ttl = 90_days  # Popular papers
   else:
       cache_ttl = 30_days  # Rare papers
   ```

4. **Progressive Caching**
   ```python
   # Cache levels
   Level 1: Metadata only (title, abstract) → 10KB
   Level 2: + Tables → 100KB
   Level 3: + Full text → 500KB
   Level 4: + Images → 5MB

   # Most queries only need Level 1-2
   ```

---

## Recommended Implementation

### Phase 1: MVP (Current State) ✅
```python
# What we have now
✅ PDF downloads to data/pdfs/
✅ Parse on-demand
❌ No caching yet
❌ No database metadata

Result: Works, but slow repeated queries
```

### Phase 2: Add Caching (Next Step) 🎯
```python
# Add simple JSON cache
class FullTextManager:
    async def get_fulltext(self, publication):
        # Check JSON cache
        cached = self._load_cache(publication.id)
        if cached:
            return cached

        # Get PDF (download or from disk)
        pdf_path = await self._get_pdf(publication)

        # Parse PDF
        content = await self._parse_pdf(pdf_path)

        # Save to cache
        self._save_cache(publication.id, content)

        return content
```

### Phase 3: Add Database Metadata (Future)
```python
# Store searchable metadata in DB
class MetadataStore:
    def index_paper(self, paper_id, content):
        self.db.execute("""
            INSERT INTO papers (
                id, title, abstract,
                table_count, has_tables,
                parsed_at, pdf_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id,
            content.title,
            content.abstract,
            len(content.tables),
            len(content.tables) > 0,
            datetime.now(),
            str(pdf_path)
        ))
```

### Phase 4: Background Processing (Future)
```python
# Process PDFs asynchronously
class BackgroundParser:
    async def queue_parsing(self, pdf_path):
        # Add to queue
        await self.queue.put({
            'pdf_path': pdf_path,
            'priority': 'low',
            'scheduled_at': datetime.now()
        })

    async def worker(self):
        while True:
            task = await self.queue.get()
            content = await parse_pdf(task['pdf_path'])
            await cache_content(content)
```

---

## Decision Matrix

| Criterion | Text Only | PDF + Parse | Hybrid | Weight | Winner |
|-----------|-----------|-------------|--------|--------|--------|
| **Storage Cost** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 2x | Text Only |
| **Query Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | 5x | Hybrid |
| **Future-Proof** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 10x | Hybrid |
| **Error Recovery** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 10x | Hybrid |
| **Flexibility** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 8x | Hybrid |
| **Simplicity** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 3x | Text Only |
| **Legal Safety** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 7x | Hybrid |
| **Scalability** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 6x | Hybrid |

**Weighted Score:**
- Text Only: 114 points
- PDF + Parse: 230 points
- **Hybrid: 257 points** ⭐ **WINNER**

---

## Final Recommendation

### 🎯 **IMPLEMENT HYBRID APPROACH**

**Why:**
1. ✅ **Future-Proof:** Can upgrade extraction anytime
2. ✅ **Error Recovery:** Can fix parser bugs
3. ✅ **Legal Safety:** Preserve source of truth
4. ✅ **Performance:** Cache gives text-only speed
5. ✅ **Flexibility:** Support new features (equations, OCR, etc.)
6. ✅ **Cost-Effective:** Storage is cheap ($30/month for 1M papers)

**Implementation Priority:**
```
Phase 1 (Week 1): ✅ DONE - PDFs saved, parse on-demand
Phase 2 (Week 2): 🎯 ADD - JSON cache for parsed content
Phase 3 (Week 3): 📋 ADD - Database metadata for search
Phase 4 (Week 4): 🚀 ADD - Background parsing queue
```

**Storage Strategy:**
```
Keep forever:
  ✅ Original PDFs (source of truth)
  ✅ Original XML (when available)

Cache (with TTL):
  ✅ Parsed JSON (90 days, refresh if parser upgraded)
  ✅ Extracted tables (90 days)
  ✅ Extracted images (30 days, if enabled)

Never save:
  ❌ Intermediate parsing artifacts
  ❌ Temporary files
```

---

## Code Example (Recommended Pattern)

```python
"""
Hybrid storage pattern - Best of both worlds.
"""

from pathlib import Path
import json
from datetime import datetime, timedelta

class FullTextStorageManager:
    """
    Manages full-text storage with hybrid approach.

    Strategy:
    1. Save PDFs permanently (source of truth)
    2. Cache parsed content (performance)
    3. Re-parse when needed (flexibility)
    """

    def __init__(
        self,
        pdf_dir: Path = Path("data/fulltext/pdf"),
        cache_dir: Path = Path("data/fulltext/parsed"),
        cache_ttl_days: int = 90
    ):
        self.pdf_dir = pdf_dir
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(days=cache_ttl_days)

        # Ensure directories exist
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_fulltext(
        self,
        paper_id: str,
        force_reparse: bool = False
    ) -> FullTextContent:
        """
        Get full-text content with smart caching.

        Flow:
        1. Check cache (fast path)
        2. Check PDF exists
        3. Parse PDF if needed
        4. Update cache
        5. Return content
        """

        # Step 1: Check cache (unless force_reparse)
        if not force_reparse:
            cached = await self._load_from_cache(paper_id)
            if cached and not self._is_cache_stale(cached):
                logger.debug(f"✓ Cache hit: {paper_id}")
                return cached

        # Step 2: Get PDF path
        pdf_path = await self._get_pdf_path(paper_id)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {paper_id}")

        # Step 3: Parse PDF
        logger.info(f"Parsing PDF: {paper_id}")
        from lib.fulltext.pdf_extractor import PDFExtractor

        extractor = PDFExtractor()
        content = extractor.extract_structured_content(
            pdf_path,
            extract_tables=True,
            extract_images=False  # Optional, saves disk
        )

        # Step 4: Cache results
        await self._save_to_cache(paper_id, content)

        return content

    async def _load_from_cache(self, paper_id: str) -> Optional[FullTextContent]:
        """Load parsed content from cache."""
        cache_file = self.cache_dir / f"{paper_id}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Reconstruct FullTextContent
            content = FullTextContent.from_dict(data['content'])
            content.metadata = data['metadata']

            return content

        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            return None

    def _is_cache_stale(self, content: FullTextContent) -> bool:
        """Check if cached content needs refresh."""
        cached_at = datetime.fromisoformat(
            content.metadata.get('cached_at', '2000-01-01')
        )

        age = datetime.now() - cached_at

        # Refresh if older than TTL
        if age > self.cache_ttl:
            logger.info("Cache stale (age)")
            return True

        # Refresh if parser version changed
        cached_version = content.metadata.get('parser_version', '0.0')
        if cached_version < CURRENT_PARSER_VERSION:
            logger.info("Cache stale (parser upgraded)")
            return True

        return False

    async def _save_to_cache(
        self,
        paper_id: str,
        content: FullTextContent
    ):
        """Save parsed content to cache."""
        cache_file = self.cache_dir / f"{paper_id}.json"

        data = {
            'content': content.to_dict(),
            'metadata': {
                'cached_at': datetime.now().isoformat(),
                'parser_version': CURRENT_PARSER_VERSION,
                'table_count': len(content.tables),
                'section_count': len(content.sections),
            }
        }

        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Cached: {paper_id} ({cache_file.stat().st_size} bytes)")

    async def _get_pdf_path(self, paper_id: str) -> Path:
        """Get path to PDF file."""
        # Check multiple possible locations
        possible_paths = [
            self.pdf_dir / "arxiv" / f"{paper_id}.pdf",
            self.pdf_dir / "pmc" / f"{paper_id}.pdf",
            self.pdf_dir / "publisher" / f"{paper_id}.pdf",
            self.pdf_dir / f"{paper_id}.pdf",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        raise FileNotFoundError(f"PDF not found for {paper_id}")

    async def invalidate_cache(self, paper_id: str):
        """Manually invalidate cache for a paper."""
        cache_file = self.cache_dir / f"{paper_id}.json"
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Cache invalidated: {paper_id}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))

        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'cached_papers': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
        }
```

---

## Conclusion

**Don't fall into the "save space, lose flexibility" trap.**

At scale, the difference is:
- **Text Only:** $1/month storage, zero flexibility, permanent data loss risk
- **Hybrid:** $30/month storage, unlimited flexibility, full error recovery

**For $29/month, you get:**
- ✅ Future-proof architecture
- ✅ Error recovery capability
- ✅ Feature upgrade flexibility
- ✅ Legal compliance
- ✅ Same query performance (with cache)

**The real question isn't "can we afford storage?" but "can we afford to NOT have our source files?"**

🎯 **Recommendation: HYBRID APPROACH with JSON caching**
