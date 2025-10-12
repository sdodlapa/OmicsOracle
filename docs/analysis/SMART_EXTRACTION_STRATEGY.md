# Smart Full-Text Extraction Strategy: Optimized Waterfall

**Date:** October 11, 2025  
**Goal:** Minimize API calls, maximize quality, optimize storage

---

## 🎯 Core Principle: "Best Quality, Least Effort"

**Priority Order:**
1. **Cache** (instant, free)
2. **Free permanent XML** (PMC, arXiv XML)
3. **Free permanent PDF** (arXiv, bioRxiv)
4. **Rate-limited APIs** (only if not cached)
5. **Slow/restricted sources** (institutional, Sci-Hub)

---

## Current Problem Analysis

### What We Have Now:
```python
async def get_fulltext(publication):
    # 1. Try institutional access (slow, session-based)
    # 2. Try PMC XML (good!)
    # 3. Try OpenAlex (just metadata)
    # 4. Try Unpaywall (API rate-limited)
    # 5. Try CORE (API rate-limited)
    # 6. Try bioRxiv (API rate-limited)
    # 7. Try arXiv (API rate-limited)
    # 8. Try Sci-Hub (slow, legal issues)
    # 9. Try LibGen (slow, legal issues)
```

### Problems:
1. ❌ **No cache check first** - Always hits APIs
2. ❌ **XML/PDF not differentiated** - Same priority regardless
3. ❌ **No local file check** - Might already have it!
4. ❌ **Rate limits hit unnecessarily** - Could check disk first
5. ❌ **Institutional always tried first** - Slow, session-dependent

---

## Optimized Strategy: Smart Waterfall

### Phase 1: Check What We Already Have (0ms, free) ✅

```python
async def get_fulltext_smart(publication):
    """
    Smart extraction with caching and prioritization.
    
    Key insight: Check local resources FIRST before hitting APIs.
    """
    
    # ========================================
    # PHASE 1: LOCAL CACHE (instant)
    # ========================================
    
    # 1.1: Check parsed content cache (fastest)
    cached_content = await cache.get_parsed(publication.id)
    if cached_content and not is_stale(cached_content):
        logger.info(f"✓ Cache hit (parsed): {publication.id}")
        return FullTextResult(
            success=True,
            source="cache",
            content=cached_content.text,
            structured_content=cached_content,
            metadata={'cache_hit': True}
        )
    
    # 1.2: Check local XML files (if exists)
    local_xml = check_local_xml(publication)
    if local_xml:
        logger.info(f"✓ Local XML found: {local_xml}")
        content = await extract_from_xml(local_xml)
        await cache.save_parsed(publication.id, content)
        return success_result(content, source="local_xml")
    
    # 1.3: Check local PDF files (if exists)
    local_pdf = check_local_pdf(publication)
    if local_pdf:
        logger.info(f"✓ Local PDF found: {local_pdf}")
        
        # Check if already parsed
        parsed_cache = await cache.get_pdf_parsed(publication.id)
        if parsed_cache:
            return success_result(parsed_cache, source="local_pdf_cached")
        
        # Parse PDF
        content = await parse_pdf(local_pdf)
        await cache.save_parsed(publication.id, content)
        return success_result(content, source="local_pdf")
    
    # Not in cache - proceed to acquisition
    logger.info(f"Not cached, acquiring: {publication.id}")
```

### Phase 2: Free, Permanent, High-Quality Sources ✅

```python
    # ========================================
    # PHASE 2: FREE PERMANENT SOURCES (XML preferred)
    # ========================================
    
    # 2.1: PMC XML (free, permanent, highest quality)
    if publication.pmc_id:
        logger.info(f"Trying PMC XML: {publication.pmc_id}")
        xml_content = await fetch_pmc_xml(publication.pmc_id)
        
        if xml_content:
            # Save XML to disk (permanent)
            save_xml_to_disk(publication.pmc_id, xml_content)
            
            # Parse and cache
            content = await extract_from_xml(xml_content)
            await cache.save_parsed(publication.id, content)
            
            return success_result(content, source="pmc_xml")
    
    # 2.2: arXiv (free, permanent)
    if is_arxiv_paper(publication):
        # arXiv provides both PDF and source files
        
        # Try source files first (LaTeX, etc.) - best quality
        arxiv_source = await try_arxiv_source(publication)
        if arxiv_source:
            save_source_to_disk(publication.id, arxiv_source)
            content = await extract_from_source(arxiv_source)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="arxiv_source")
        
        # Fall back to PDF (still good)
        arxiv_pdf = await download_arxiv_pdf(publication)
        if arxiv_pdf:
            save_pdf_to_disk(publication.id, arxiv_pdf)
            content = await parse_pdf(arxiv_pdf)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="arxiv_pdf")
    
    # 2.3: bioRxiv/medRxiv (free, permanent, preprints)
    if is_biorxiv_paper(publication):
        # bioRxiv provides XML for many papers
        biorxiv_xml = await try_biorxiv_xml(publication)
        if biorxiv_xml:
            save_xml_to_disk(publication.id, biorxiv_xml)
            content = await extract_from_xml(biorxiv_xml)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="biorxiv_xml")
        
        # Fall back to PDF
        biorxiv_pdf = await download_biorxiv_pdf(publication)
        if biorxiv_pdf:
            save_pdf_to_disk(publication.id, biorxiv_pdf)
            content = await parse_pdf(biorxiv_pdf)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="biorxiv_pdf")
```

### Phase 3: Free APIs (rate-limited, prefer XML/PDF indication) ✅

```python
    # ========================================
    # PHASE 3: OPEN ACCESS APIS (rate-limited)
    # ========================================
    
    # 3.1: Unpaywall (OA aggregator, tells us XML vs PDF)
    unpaywall_result = await unpaywall_client.get_oa_location(publication.doi)
    if unpaywall_result and unpaywall_result.is_oa:
        best_location = unpaywall_result.best_oa_location
        
        # Prefer XML if available
        if best_location.url_for_xml:
            xml_content = await download_url(best_location.url_for_xml)
            save_xml_to_disk(publication.id, xml_content)
            content = await extract_from_xml(xml_content)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="unpaywall_xml")
        
        # PDF as fallback
        elif best_location.url_for_pdf:
            pdf_path = await download_pdf(best_location.url_for_pdf, publication.id)
            content = await parse_pdf(pdf_path)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="unpaywall_pdf")
    
    # 3.2: CORE (academic repository, often has full-text)
    core_result = await core_client.search_by_doi(publication.doi)
    if core_result and core_result.download_url:
        # CORE provides both XML and PDF
        if core_result.format == "xml":
            xml_content = await download_url(core_result.download_url)
            save_xml_to_disk(publication.id, xml_content)
            content = await extract_from_xml(xml_content)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="core_xml")
        else:
            pdf_path = await download_pdf(core_result.download_url, publication.id)
            content = await parse_pdf(pdf_path)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="core_pdf")
```

### Phase 4: Slow/Restricted Sources (last resort) ⚠️

```python
    # ========================================
    # PHASE 4: SLOW/RESTRICTED SOURCES (last resort)
    # ========================================
    
    # 4.1: Institutional Access (slow, session-based, prefer PDF)
    if institutional_access_enabled:
        logger.info("Trying institutional access (slow)...")
        
        # Institutional usually gives PDFs, not XML
        pdf_url = await institutional_client.get_pdf_url(publication)
        if pdf_url:
            pdf_path = await download_pdf(pdf_url, publication.id)
            content = await parse_pdf(pdf_path)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="institutional_pdf")
    
    # 4.2: Sci-Hub (legal gray area, always PDF)
    if scihub_enabled:
        logger.warning("Trying Sci-Hub (last resort)...")
        
        pdf_url = await scihub_client.get_pdf_url(publication.doi)
        if pdf_url:
            pdf_path = await download_pdf(pdf_url, publication.id)
            content = await parse_pdf(pdf_path)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="scihub_pdf")
    
    # 4.3: LibGen (legal gray area, always PDF)
    if libgen_enabled:
        logger.warning("Trying LibGen (last resort)...")
        
        pdf_url = await libgen_client.get_pdf_url(publication.doi)
        if pdf_url:
            pdf_path = await download_pdf(pdf_url, publication.id)
            content = await parse_pdf(pdf_path)
            await cache.save_parsed(publication.id, content)
            return success_result(content, source="libgen_pdf")
    
    # Nothing worked
    return FullTextResult(success=False, error="No sources available")
```

---

## Optimized Decision Tree

```
START: get_fulltext(publication)
│
├─ CACHE CHECK (0ms)
│  ├─ Parsed content cached? ──YES──> Return (instant) ✅
│  ├─ Local XML exists? ──YES──> Parse → Cache → Return ✅
│  └─ Local PDF exists? ──YES──> Parse → Cache → Return ✅
│
├─ FREE PERMANENT SOURCES (1-3s)
│  ├─ PMC ID? ──YES──> Fetch XML → Save → Parse → Cache → Return ✅
│  ├─ arXiv ID? ──YES──> Download PDF → Save → Parse → Cache → Return ✅
│  └─ bioRxiv DOI? ──YES──> Download → Save → Parse → Cache → Return ✅
│
├─ FREE APIS (2-5s, rate-limited)
│  ├─ Unpaywall OA? ──YES──> Download → Save → Parse → Cache → Return ⚠️
│  ├─ CORE available? ──YES──> Download → Save → Parse → Cache → Return ⚠️
│  └─ Crossref link? ──YES──> Download → Save → Parse → Cache → Return ⚠️
│
└─ RESTRICTED SOURCES (5-30s, slow)
   ├─ Institutional? ──YES──> Download PDF → Save → Parse → Cache → Return 🐌
   ├─ Sci-Hub? ──YES──> Download PDF → Save → Parse → Cache → Return 🐌
   └─ LibGen? ──YES──> Download PDF → Save → Parse → Cache → Return 🐌
   
   FAIL: No sources available ❌
```

---

## Smart Source Classification

### Category A: Extract Full-Text Immediately (XML preferred)
**Characteristics:** Free, permanent, API-accessible, often has XML

```python
CATEGORY_A_SOURCES = {
    'pmc': {
        'format': 'xml',
        'speed': 'fast',
        'quality': 'excellent',
        'permanent': True,
        'api_limit': '10/sec with key',
        'action': 'fetch_and_save_xml'
    },
    'arxiv': {
        'format': 'pdf',  # Also has LaTeX source
        'speed': 'fast',
        'quality': 'good',
        'permanent': True,
        'api_limit': '1/3sec',
        'action': 'download_and_save_pdf'
    },
    'biorxiv': {
        'format': 'pdf',  # Some have XML
        'speed': 'fast',
        'quality': 'good',
        'permanent': True,
        'api_limit': 'generous',
        'action': 'download_and_save_pdf'
    },
    'unpaywall': {
        'format': 'varies',  # Points to XML or PDF
        'speed': 'medium',
        'quality': 'varies',
        'permanent': 'depends',
        'api_limit': '100k/day',
        'action': 'follow_link_and_save'
    },
    'core': {
        'format': 'varies',
        'speed': 'medium',
        'quality': 'good',
        'permanent': True,
        'api_limit': 'with key',
        'action': 'download_and_save'
    }
}
```

### Category B: Download PDF Only (no API, or temporary access)
**Characteristics:** Requires authentication, session-based, or legal gray area

```python
CATEGORY_B_SOURCES = {
    'institutional': {
        'format': 'pdf',
        'speed': 'slow',
        'quality': 'excellent',
        'permanent': False,  # Session-based
        'api_limit': None,
        'action': 'download_pdf_save_only',
        'reason': 'Session expires, must save PDF'
    },
    'scihub': {
        'format': 'pdf',
        'speed': 'slow',
        'quality': 'good',
        'permanent': False,  # Mirror may disappear
        'api_limit': None,
        'action': 'download_pdf_save_only',
        'reason': 'Legal gray area, availability varies'
    },
    'libgen': {
        'format': 'pdf',
        'speed': 'slow',
        'quality': 'good',
        'permanent': False,  # Mirror may disappear
        'api_limit': None,
        'action': 'download_pdf_save_only',
        'reason': 'Legal gray area, availability varies'
    },
    'publisher_direct': {
        'format': 'pdf',
        'speed': 'varies',
        'quality': 'excellent',
        'permanent': False,  # May be paywalled later
        'api_limit': None,
        'action': 'download_pdf_save_only',
        'reason': 'Access may change, save while available'
    }
}
```

---

## Smart Caching Strategy

### Multi-Level Cache System

```python
class SmartCache:
    """
    Multi-level caching for full-text content.
    
    Levels:
    1. Memory cache (instant, volatile)
    2. Parsed JSON cache (fast, 90 days TTL)
    3. Local files (permanent, source of truth)
    4. Database metadata (for search)
    """
    
    def __init__(self):
        self.memory_cache = {}  # Recent papers in RAM
        self.json_cache_dir = Path("data/fulltext/parsed")
        self.xml_dir = Path("data/fulltext/xml")
        self.pdf_dir = Path("data/fulltext/pdf")
        self.db = Database()
    
    async def get_fulltext(self, publication_id: str) -> Optional[FullTextContent]:
        """
        Check cache hierarchy before fetching.
        
        Priority:
        1. Memory (instant)
        2. Parsed JSON (fast)
        3. Local XML (parse once)
        4. Local PDF (parse once)
        5. None (need to fetch)
        """
        
        # Level 1: Memory cache (instant)
        if publication_id in self.memory_cache:
            logger.debug(f"Memory cache hit: {publication_id}")
            return self.memory_cache[publication_id]
        
        # Level 2: Parsed JSON cache (fast)
        parsed = await self._load_parsed_cache(publication_id)
        if parsed and not self._is_stale(parsed):
            logger.debug(f"JSON cache hit: {publication_id}")
            self.memory_cache[publication_id] = parsed  # Promote to L1
            return parsed
        
        # Level 3: Local XML (parse once, cache)
        xml_path = self._find_local_xml(publication_id)
        if xml_path:
            logger.info(f"Local XML found: {xml_path}")
            content = await self._extract_and_cache(xml_path, 'xml')
            self.memory_cache[publication_id] = content
            return content
        
        # Level 4: Local PDF (parse once, cache)
        pdf_path = self._find_local_pdf(publication_id)
        if pdf_path:
            logger.info(f"Local PDF found: {pdf_path}")
            content = await self._extract_and_cache(pdf_path, 'pdf')
            self.memory_cache[publication_id] = content
            return content
        
        # Not cached - need to fetch
        return None
    
    def _find_local_xml(self, publication_id: str) -> Optional[Path]:
        """Find XML file in local storage."""
        # Check multiple possible locations
        possible_paths = [
            self.xml_dir / "pmc" / f"{publication_id}.nxml",
            self.xml_dir / "pmc" / f"PMC{publication_id}.nxml",
            self.xml_dir / f"{publication_id}.xml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _find_local_pdf(self, publication_id: str) -> Optional[Path]:
        """Find PDF file in local storage."""
        # Check multiple possible locations
        possible_paths = [
            self.pdf_dir / "arxiv" / f"{publication_id}.pdf",
            self.pdf_dir / "pmc" / f"{publication_id}.pdf",
            self.pdf_dir / "publisher" / f"{publication_id}.pdf",
            self.pdf_dir / "institutional" / f"{publication_id}.pdf",
            self.pdf_dir / f"{publication_id}.pdf",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    async def _extract_and_cache(
        self,
        file_path: Path,
        file_type: str
    ) -> FullTextContent:
        """Extract content and cache it."""
        
        # Extract based on type
        if file_type == 'xml':
            from lib.fulltext.content_extractor import ContentExtractor
            extractor = ContentExtractor()
            content = extractor.extract_structured_content(
                file_path.read_text(),
                source_path=str(file_path)
            )
        else:  # pdf
            from lib.fulltext.pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            content = extractor.extract_structured_content(file_path)
        
        # Save to JSON cache
        await self._save_parsed_cache(file_path.stem, content)
        
        # Store metadata in DB
        await self.db.upsert_paper_metadata(
            id=file_path.stem,
            title=content.title,
            has_fulltext=True,
            source_type=file_type,
            source_path=str(file_path),
            table_count=len(content.tables),
            parsed_at=datetime.now()
        )
        
        return content
    
    async def save_file(
        self,
        publication_id: str,
        content: bytes,
        file_type: str,
        source: str
    ) -> Path:
        """
        Save downloaded file to appropriate location.
        
        Organization:
        data/fulltext/
        ├── xml/
        │   ├── pmc/
        │   └── biorxiv/
        └── pdf/
            ├── arxiv/
            ├── institutional/
            ├── publisher/
            └── scihub/
        """
        
        # Determine save location based on source
        if file_type == 'xml':
            base_dir = self.xml_dir / source
        else:
            base_dir = self.pdf_dir / source
        
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = base_dir / f"{publication_id}.{file_type}"
        file_path.write_bytes(content)
        
        logger.info(f"Saved {file_type} to: {file_path} ({len(content)} bytes)")
        
        return file_path
```

---

## Performance Optimization

### Batch Pre-Caching

```python
async def precache_popular_papers(limit: int = 1000):
    """
    Pre-cache popular papers for instant access.
    
    Run this periodically (nightly) to warm cache.
    """
    
    # Get most-cited/accessed papers
    popular = await db.get_popular_papers(limit=limit)
    
    logger.info(f"Pre-caching {len(popular)} popular papers...")
    
    for paper in popular:
        # Check if already cached
        if await cache.has_fulltext(paper.id):
            continue
        
        # Fetch and cache
        try:
            result = await get_fulltext_smart(paper)
            if result.success:
                logger.debug(f"✓ Cached: {paper.id}")
            else:
                logger.warning(f"✗ Failed: {paper.id}")
        except Exception as e:
            logger.error(f"Error caching {paper.id}: {e}")
    
    logger.info("Pre-caching complete")
```

### Cache Hit Rate Monitoring

```python
class CacheMonitor:
    """Monitor cache performance."""
    
    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'memory_hits': 0,
            'json_hits': 0,
            'xml_hits': 0,
            'pdf_hits': 0,
            'api_fetches': 0,
            'failures': 0
        }
    
    def record_hit(self, source: str):
        """Record cache hit."""
        self.stats['total_requests'] += 1
        self.stats[f'{source}_hits'] += 1
    
    def record_miss(self):
        """Record cache miss (API fetch needed)."""
        self.stats['total_requests'] += 1
        self.stats['api_fetches'] += 1
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.stats['total_requests'] == 0:
            return 0.0
        
        hits = (
            self.stats['memory_hits'] +
            self.stats['json_hits'] +
            self.stats['xml_hits'] +
            self.stats['pdf_hits']
        )
        
        return hits / self.stats['total_requests']
    
    def print_report(self):
        """Print cache performance report."""
        total = self.stats['total_requests']
        if total == 0:
            print("No requests yet")
            return
        
        print("\n=== Cache Performance Report ===")
        print(f"Total Requests: {total}")
        print(f"Memory Hits: {self.stats['memory_hits']} ({self.stats['memory_hits']/total*100:.1f}%)")
        print(f"JSON Hits: {self.stats['json_hits']} ({self.stats['json_hits']/total*100:.1f}%)")
        print(f"XML Hits: {self.stats['xml_hits']} ({self.stats['xml_hits']/total*100:.1f}%)")
        print(f"PDF Hits: {self.stats['pdf_hits']} ({self.stats['pdf_hits']/total*100:.1f}%)")
        print(f"API Fetches: {self.stats['api_fetches']} ({self.stats['api_fetches']/total*100:.1f}%)")
        print(f"Overall Hit Rate: {self.get_hit_rate()*100:.1f}%")
```

---

## Recommended Implementation

### Phase 1: Add Smart Cache Check (Week 1) 🎯

```python
# Update manager_integration.py

async def get_fulltext_enhanced(self, publication):
    """Enhanced with smart caching."""
    
    if not self.initialized:
        await self.initialize()
    
    # NEW: Check cache first
    cache_manager = SmartCache()
    cached = await cache_manager.get_fulltext(publication.id)
    if cached:
        return FullTextResult(
            success=True,
            source="cache",
            content=cached.get_full_text()[:10000],
            metadata={'structured_content': cached}
        )
    
    # Try PMC XML (if available)
    if publication.pmc_id and hasattr(self, '_try_pmc_xml'):
        result = await self._try_pmc_xml(publication)
        if result.success:
            # Save XML to disk
            await cache_manager.save_file(
                publication.pmc_id,
                result.content,
                'xml',
                'pmc'
            )
            return result
    
    # Try original waterfall
    result = await original_get_fulltext(publication)
    
    # If PDF obtained, save and parse
    if result.success and result.pdf_path:
        parsed = await self._try_pdf_parse(Path(result.pdf_path))
        if parsed.success:
            result.metadata.update(parsed.metadata)
    
    return result
```

### Phase 2: Optimize Source Priority (Week 2) 📋

```python
# Reorder waterfall based on speed/quality

OPTIMIZED_WATERFALL = [
    # Tier 1: Free permanent (fast)
    ('pmc_xml', self._try_pmc_xml),            # 1-2s, XML
    ('arxiv_pdf', self._try_arxiv),            # 1-3s, PDF
    ('biorxiv_pdf', self._try_biorxiv),        # 1-3s, PDF
    
    # Tier 2: Free APIs (medium speed, rate-limited)
    ('unpaywall', self._try_unpaywall),        # 2-5s
    ('core', self._try_core),                  # 2-5s
    ('openalex', self._try_openalex_oa_url),  # 2-5s
    
    # Tier 3: Slow/restricted (last resort)
    ('institutional', self._try_institutional), # 5-30s
    ('scihub', self._try_scihub),              # 5-30s
    ('libgen', self._try_libgen),              # 5-30s
]
```

### Phase 3: Add Pre-Caching (Week 3) 🚀

```python
# Background job to warm cache

async def warm_cache_job():
    """Run nightly to pre-cache popular papers."""
    
    while True:
        # Run at 2 AM
        await asyncio.sleep(until_2am())
        
        logger.info("Starting cache warming...")
        
        # Get papers to cache
        papers_to_cache = await get_papers_needing_cache()
        
        # Process in batches
        for batch in chunks(papers_to_cache, 100):
            await precache_batch(batch)
        
        logger.info("Cache warming complete")
```

---

## Expected Performance Improvements

### Before Optimization:
```
Request 1 (PMC paper):
  1. Try institutional (5s timeout) ❌
  2. Try PMC (2s) ✅
  Total: 7 seconds

Request 2 (same paper):
  1. Try institutional (5s timeout) ❌
  2. Try PMC (2s) ✅
  Total: 7 seconds (no cache!)
```

### After Optimization:
```
Request 1 (PMC paper):
  1. Check cache ❌ (0ms)
  2. Check local files ❌ (1ms)
  3. Try PMC (2s) ✅
  4. Save to cache
  Total: 2 seconds (5s saved!)

Request 2 (same paper):
  1. Check cache ✅ (0ms)
  Total: <10ms (700x faster!)

Request 100 (different paper, popular):
  1. Check cache ✅ (pre-warmed)
  Total: <10ms
```

### Cache Hit Rate Projections:

```
Day 1:   10% hit rate
Week 1:  50% hit rate
Month 1: 85% hit rate (popular papers cached)
Month 3: 95% hit rate (most papers cached)

Impact:
- 95% of queries: <10ms (cache)
- 5% of queries: 2-10s (API fetch)
- Average: ~500ms (vs 5-7s before)

API calls reduced by 95%!
```

---

## Conclusion

### 🎯 Key Recommendations:

1. **✅ CHECK CACHE FIRST** - Avoid API calls for cached content
2. **✅ PRIORITIZE XML > PDF** - Better structure, easier parsing
3. **✅ SAVE EVERYTHING** - Storage cheap, re-fetching expensive
4. **✅ TIER SOURCES** - Free/permanent first, slow/restricted last
5. **✅ PRE-CACHE POPULAR** - Warm cache for instant access

### Implementation Priority:

**Week 1:** ✅ Add SmartCache check before waterfall  
**Week 2:** 📋 Reorder sources (XML first, slow sources last)  
**Week 3:** 🚀 Add pre-caching for popular papers  
**Week 4:** 📊 Add monitoring and metrics  

This will give you **~10x performance improvement** and **~95% reduction in API calls**!
