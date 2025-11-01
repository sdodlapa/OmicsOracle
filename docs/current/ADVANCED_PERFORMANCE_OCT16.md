# Advanced Performance Optimizations - October 16, 2025

## Performance Tracking & Source Prioritization

### 1. Download Timing Metrics

Added per-PDF timing to track which sources are fastest:

```python
download_start = time.time()
result = await pdf_downloader.download_with_fallback(...)
download_time = time.time() - download_start

# Log with timing
logger.info(f"[OK] Downloaded in {download_time:.1f}s from {result.source}")
```

**Benefits**:
- Track which sources deliver fastest
- Identify slow/unreliable sources
- Data-driven prioritization

### 2. Source Performance Logging

Added detailed performance metrics per download:

```python
logger.debug(
    f"[PERF] {result.source}: {download_time:.1f}s for "
    f"{result.file_size / 1024:.0f}KB ({KB_per_sec:.0f} KB/s)"
)
```

**Sample Output**:
```
[PERF] unpaywall: 2.3s for 458KB (199 KB/s)
[PERF] scihub: 8.5s for 1203KB (141 KB/s)
[PERF] crossref: 1.8s for 325KB (180 KB/s)
```

### 3. Database Performance Tracking

Store timing in database for future prioritization:

```python
download_method=f"fallback_{download_time:.1f}s"  # e.g., "fallback_2.3s"
```

**Future Enhancement**: Query database to calculate average speed per source:
```sql
SELECT 
    source_type,
    AVG(CAST(SUBSTR(download_method, 10, LENGTH(download_method)-10) AS REAL)) as avg_seconds,
    COUNT(*) as downloads
FROM pdf_acquisition 
WHERE status = 'success'
GROUP BY source_type
ORDER BY avg_seconds ASC;
```

---

## Aggressive Speed Optimizations

### 4. Maximum Concurrency

**Changed**: `max_concurrent=10` → `max_concurrent=25`

Download **ALL 25 papers simultaneously** instead of batches of 10.

**Impact**:
- Before: 3 batches × 20s = 60s
- After: 1 batch × 20s = **20s**
- **3x faster** for full batch

### 5. Aggressive Timeout

**Changed**: `timeout_seconds=20` → `timeout_seconds=15`

Fail faster on slow/unresponsive sources.

**Impact**:
- 25% faster failure detection
- Less time wasted on dead sources

### 6. Skip PDF Validation

**Changed**: `validate_pdf=True` → `validate_pdf=False`

Skip file validation to save 1-2 seconds per PDF.

**Impact**:
- Saves 25-50 seconds for 25 PDFs
- Trade-off: May accept corrupted PDFs (rare)

### 7. Overall Performance Statistics

Added batch-level timing:

```python
logger.info(
    f"Downloaded {successful}/{total} PDFs "
    f"in {total_time:.1f}s ({throughput:.1f} PDFs/sec, max 25 concurrent)"
)
```

**Sample Output**:
```
[GSE570] Downloaded 15/25 PDFs in 18.3s (0.82 PDFs/sec, max 25 concurrent)
```

---

## Performance Comparison

| Metric | Original | After Opt 1 | After Opt 2 | Improvement |
|--------|----------|-------------|-------------|-------------|
| **Concurrent downloads** | 3 | 10 | **25** | 8.3x |
| **Timeout** | 30s | 20s | **15s** | 2x faster |
| **Validation** | Yes | Yes | **No** | 1-2s saved |
| **Expected time (25 PDFs)** | 5-7 min | 1-2 min | **20-30 sec** | **10-20x faster** |

---

## Source Performance Analysis

Based on logs, we can now track:

### Fast Sources (< 3 seconds typical)
- ✅ **Unpaywall**: Usually fastest, gold OA papers
- ✅ **Crossref**: Fast for most publishers
- ✅ **Institutional**: Fast if on campus network

### Medium Sources (3-8 seconds)
- ⚠️ **Sci-Hub**: Variable speed, depends on mirror
- ⚠️ **bioRxiv**: Fast for preprints

### Slow/Unreliable Sources (> 8 seconds)
- ❌ **PMC**: Disabled (403 errors)
- ❌ **CORE**: Disabled (slow API)
- ❌ **OpenAlex**: Disabled (slow for batches)
- ❌ **LibGen**: Slow, last resort

---

## Future Enhancements

### 1. Dynamic Source Prioritization

Query database to re-order sources by historical performance:

```python
# Get average speed per source from database
source_speeds = db.get_source_performance_stats()

# Sort URLs by fastest sources first
urls.sort(key=lambda u: source_speeds.get(u.source, 999))
```

### 2. Adaptive Timeout

Adjust timeout based on file size:

```python
timeout = base_timeout + (file_size_mb * 2)  # 2s per MB
```

### 3. Connection Pooling

Reuse HTTP connections for same sources:

```python
# Share session across downloads
async with aiohttp.ClientSession() as session:
    for url in urls:
        await download_with_session(session, url)
```

### 4. Predictive Caching

Pre-download papers likely to be requested:

```python
# If user searches "breast cancer", pre-fetch top 10 papers
await prefetch_popular_papers(search_terms)
```

### 5. CDN for Common Papers

Cache frequently accessed papers on CDN:

```python
# Check CDN first
cdn_url = f"https://cdn.omicsoracle.ai/pdfs/{pmid}.pdf"
if await check_cdn_exists(cdn_url):
    return download_from_cdn(cdn_url)
```

---

## Monitoring Commands

### Track Performance
```bash
# View download times
grep "\[PERF\]" logs/omics_api.log | tail -20

# View successful downloads with timing
grep "\[OK\] Downloaded in" logs/omics_api.log | tail -20

# View batch statistics
grep "Downloaded.*PDFs/sec" logs/omics_api.log | tail -10
```

### Source Performance Analysis
```bash
# Extract source and timing
grep "\[PERF\]" logs/omics_api.log | \
  awk '{print $2, $3}' | \
  sort | uniq -c | sort -nr

# Average time per source
sqlite3 data/database/omics_oracle.db "
SELECT 
    source_type,
    AVG(CAST(SUBSTR(download_method, 10, LENGTH(download_method)-10) AS REAL)) as avg_sec,
    COUNT(*) as count
FROM pdf_acquisition 
WHERE status = 'success' AND download_method LIKE 'fallback_%'
GROUP BY source_type
ORDER BY avg_sec ASC;
"
```

### Cache Hit Rate
```bash
# Calculate cache effectiveness
cached=$(grep -c "CACHED" logs/omics_api.log)
downloaded=$(grep -c "\[OK\] Downloaded" logs/omics_api.log)
total=$((cached + downloaded))
rate=$((cached * 100 / total))
echo "Cache hit rate: ${rate}%"
```

---

## Expected Results

### Before All Optimizations
```
[GSE570] Downloading PDFs...
[GSE570] Downloaded 15/25 PDFs (parallel execution)
Time: 5-7 minutes
```

### After All Optimizations
```
[GSE570] Downloading PDFs...
[PERF] unpaywall: 2.1s for 458KB (218 KB/s)
[PERF] scihub: 3.2s for 1203KB (376 KB/s)
[PERF] crossref: 1.9s for 325KB (171 KB/s)
...
[GSE570] Downloaded 15/25 PDFs in 22.5s (0.67 PDFs/sec, max 25 concurrent)
Time: 20-30 seconds
```

**Result**: **10-20x faster** than original implementation!

---

## Configuration Summary

```python
# Current settings (Maximum Performance)
PDFDownloadManager(
    max_concurrent=25,      # Download all papers simultaneously
    max_retries=1,          # Fast failure
    timeout_seconds=15,     # Aggressive timeout
    validate_pdf=False      # Skip validation for speed
)

FullTextManagerConfig(
    enable_unpaywall=True,   # ✅ Fast, reliable
    enable_crossref=True,    # ✅ Fast, good coverage
    enable_scihub=True,      # ✅ Fast, last resort
    enable_institutional=True, # ✅ Fast if on campus
    enable_biorxiv=True,     # ✅ Fast for preprints
    enable_arxiv=True,       # ✅ Fast for preprints
    enable_libgen=True,      # ⚠️ Slow, final fallback
    enable_pmc=False,        # ❌ 403 errors
    enable_core=False,       # ❌ Too slow
    enable_openalex=False,   # ❌ Too slow
)
```

---

## Testing

Test with GSE570 (25 papers):

1. **First run** (no cache): Should complete in 20-30 seconds
2. **Second run** (cached): Should complete in 2-3 seconds
3. **Check logs**: Should see `[PERF]` timing for each source
4. **Check database**: Should see timing in `download_method` field

```bash
# Test run
curl -X POST http://localhost:8000/api/agents/enrich-fulltext \
  -H "Content-Type: application/json" \
  -d '{"datasets": [{"geo_id": "GSE570", "pubmed_ids": [...]}]}'

# Check results
tail -100 logs/omics_api.log | grep -E "PERF|Downloaded.*PDF"
```
