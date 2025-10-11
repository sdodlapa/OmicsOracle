# Deprecated Code Archive - October 10, 2025

This directory contains code that has been deprecated and replaced with better implementations.

## Files in This Archive

### `pdf_downloader.py` (Deprecated: Oct 10, 2025)

**Original Location:** `omics_oracle_v2/lib/publications/pdf_downloader.py`

**Replaced By:** `omics_oracle_v2/lib/storage/pdf/download_manager.py` (PDFDownloadManager)

**Reason for Deprecation:**
- Synchronous implementation (requests + ThreadPoolExecutor)
- Less robust error handling
- No validation support
- Replaced with async PDFDownloadManager which has:
  - Async implementation (aiohttp, aiofiles)
  - Better error handling and retry logic
  - PDF validation
  - Progress tracking with DownloadReport
  - More efficient concurrent downloads

**Migration Guide:**
```python
# OLD (deprecated):
from omics_oracle_v2.lib.publications.pdf_downloader import PDFDownloader
downloader = PDFDownloader(download_dir, institutional_manager)
result = downloader.download(pdf_url, identifier, source)

# NEW (recommended):
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager
manager = PDFDownloadManager(max_concurrent=5, max_retries=3, validate_pdf=True)
result = await manager.download_single(publication, output_dir)
```

**Last Used In:**
- `omics_oracle_v2/lib/pipelines/publication_pipeline.py` (updated Oct 10, 2025)

---

## Archive Policy

- **Retention:** Keep archived code for 6 months minimum
- **Review:** Review archived code quarterly for permanent removal
- **Documentation:** Each archived file must have migration guide above
- **Git History:** All moves use `git mv` to preserve history

---

**Archive Created:** October 10, 2025
**Next Review:** April 10, 2026
