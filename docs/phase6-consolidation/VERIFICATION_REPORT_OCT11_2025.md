# Code Verification Report
**Date**: October 11, 2025
**Analyst**: AI Assistant
**Purpose**: Identify duplicate/obsolete code before unified pipeline refactoring

---

## 📊 Executive Summary

**Total Files Analyzed**: 221 Python files
**Orphaned Files Found**: 36 candidates
**Duplicate Classes**: 19 classes with multiple implementations
**High Priority for Archive**: 8 files
**Requires Review**: 15 files

---

## 🎯 Key Findings

### 1. PDF Download Infrastructure - DUPLICATE CONFIRMED ✅

#### Current Active (KEEP):
```
omics_oracle_v2/lib/storage/pdf/download_manager.py
├── Class: PDFDownloadManager
├── Imported by: 5 files
│   ├── unified_search_pipeline.py ✅
│   ├── geo_citation_pipeline.py ✅
│   ├── publication_pipeline.py ✅
│   └── storage/__init__.py ✅
├── Used in: test_unified_pipeline_validation.py ✅
└── Status: ACTIVELY USED - Current implementation
```

#### Deprecated (ARCHIVE):
```
omics_oracle_v2/lib/archive/deprecated_20251010/pdf_downloader.py
├── Class: PDFDownloader (OLD)
├── Imported by: 1 file (test_integration.py - OLD TEST)
├── Used in: old tests/examples
└── Status: ⚠️ ALREADY ARCHIVED - Safe to ignore
```

**Decision**: ✅ Already properly archived. Update old tests to use new implementation.

---

### 2. Full-Text Retrieval - ACTIVE (Review for refactoring)

```
omics_oracle_v2/lib/fulltext/manager.py
├── Class: FullTextManager
├── Purpose: URL discovery (Phase 1)
├── Issue: Returns URLs, not PDFs
└── TODO: Refactor to download immediately
```

**Decision**: 🔧 REFACTOR - Make it download PDFs directly, not just URLs

---

### 3. Duplicate Model Classes - CONSOLIDATION NEEDED

#### SearchResult (4 implementations!) ⚠️

1. **omics_oracle_v2/lib/geo/models.py**
   - GEO-specific search results
   - Fields: `geo_ids`, `total_found`
   - Used by: GEOClient

2. **omics_oracle_v2/lib/pipelines/unified_search_pipeline.py**
   - Unified pipeline results
   - Fields: `geo_datasets`, `publications`, `total_results`
   - Used by: UnifiedSearchPipeline ✅

3. **omics_oracle_v2/lib/search/advanced.py**
   - Advanced search results
   - Legacy implementation

4. **omics_oracle_v2/lib/search/hybrid.py**
   - Hybrid search results
   - Legacy implementation

**Decision**:
- ✅ KEEP: unified_search_pipeline.py version (current)
- ✅ KEEP: geo/models.py version (specific to GEO)
- ⚠️ REVIEW: advanced.py and hybrid.py (check if used)

---

### 4. Integration Layer - ORPHANED FILES

All files in `omics_oracle_v2/integration/` are orphaned:

```
omics_oracle_v2/integration/
├── adapters.py           - No usage found ❌
├── analysis_client.py    - No usage found ❌
├── base_client.py        - No usage found ❌
├── data_transformer.py   - No usage found ❌
├── ml_client.py          - No usage found ❌
├── search_client.py      - No usage found ❌
├── auth.py              - Used in 52 tests ⚠️
└── models.py            - Duplicate models ⚠️
```

**Decision**:
- ❌ ARCHIVE: adapters.py, analysis_client.py, base_client.py, data_transformer.py, ml_client.py, search_client.py
- ⚠️ REVIEW: auth.py (used in tests - check if still needed)
- ⚠️ CONSOLIDATE: models.py (merge with main models)

---

## 📋 Detailed Analysis

### High Priority - Archive Immediately

| File | Reason | Imported By | Action |
|------|--------|-------------|--------|
| `integration/adapters.py` | No usage found | None | ARCHIVE |
| `integration/analysis_client.py` | No usage found | None | ARCHIVE |
| `integration/base_client.py` | No usage found | None | ARCHIVE |
| `integration/data_transformer.py` | No usage found | None | ARCHIVE |
| `integration/ml_client.py` | No usage found | None | ARCHIVE |
| `integration/search_client.py` | No usage found | None | ARCHIVE |

### Medium Priority - Review Before Archive

| File | Reason | Used In | Action |
|------|--------|---------|--------|
| `integration/auth.py` | Used in 52 tests | Old auth tests | Review tests, then archive |
| `integration/models.py` | Duplicate models | Old integration layer | Consolidate, then archive |
| `tests/api/test_main.py` | No usage | None | Archive with test cleanup |
| `tests/api/test_websockets.py` | No usage | None | Archive with test cleanup |
| `tests/api/test_workflows.py` | No usage | None | Archive with test cleanup |

### Low Priority - Document & Monitor

| File | Reason | Status | Action |
|------|--------|--------|--------|
| `agents/orchestrator.py` | Used in examples only | Low usage | Monitor, document |
| `api/health.py` | Used in many tests | Active but legacy | Consider refactor |
| `scripts/embed_geo_datasets.py` | Used in 1 test | Specialized | Keep, document |

---

## 🔍 Verification Methodology

### Tools Used

1. **verify_code_usage.py** (Created today)
   - AST parsing for import analysis
   - Dependency graph building
   - Orphan file detection
   - Duplicate class finding

2. **grep Search Patterns**
   ```bash
   grep -r "from.*{module}" omics_oracle_v2/ tests/ examples/
   grep -r "import.*{module}" omics_oracle_v2/ tests/ examples/
   ```

3. **list_code_usages Tool**
   - Find all references to classes/functions
   - Verify actual usage vs imports

### Verification Checklist (Per File)

- [x] Import analysis via AST parsing
- [x] Reverse dependency graph
- [x] Test file scanning
- [x] Example file scanning
- [x] Documentation grep
- [x] Manual code review for ambiguous cases

---

## 📦 Archive Plan

### Phase 1: Immediate Archive (High Confidence)

**Target**: Files with ZERO usage

```bash
# Create archive directory
mkdir -p omics_oracle_v2/lib/archive/orphaned_integration_20251011

# Move files
git mv omics_oracle_v2/integration/adapters.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/
git mv omics_oracle_v2/integration/analysis_client.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/
git mv omics_oracle_v2/integration/base_client.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/
git mv omics_oracle_v2/integration/data_transformer.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/
git mv omics_oracle_v2/integration/ml_client.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/
git mv omics_oracle_v2/integration/search_client.py \
       omics_oracle_v2/lib/archive/orphaned_integration_20251011/

# Run tests
pytest tests/ -v

# Commit if tests pass
git commit -m "archive: Move orphaned integration layer files

- No imports found in codebase
- No usage in tests or examples
- Verified with verify_code_usage.py
- All tests passing"
```

### Phase 2: Review & Consolidate

**Target**: Duplicate models in integration/models.py

```python
# Before archiving, extract any unique models
# Merge into appropriate locations:
# - Publication -> lib/publications/models.py
# - SearchRequest/Response -> api/models/
# - Recommendation -> lib/ml/
```

### Phase 3: Test Cleanup

**Target**: Orphaned test files

```bash
# Archive old test files
mkdir -p omics_oracle_v2/lib/archive/orphaned_tests_20251011
git mv omics_oracle_v2/tests/api/test_main.py \
       omics_oracle_v2/lib/archive/orphaned_tests_20251011/
# etc.
```

---

## 🎯 Refactoring Plan: Direct PDF Downloads

### Current Problem (Two-Phase Approach)

```python
# Phase 1: Get URL only (FullTextManager)
fulltext_mgr = FullTextManager(download_pdfs=False)
result = await fulltext_mgr.get_fulltext(pub)
pub.pdf_url = result.url  # ← URL might expire

# Phase 2: Download later (PDFDownloadManager)
downloader = PDFDownloadManager()
report = await downloader.download_batch(publications, ...)
# ← URL might be expired, session lost, redirects broken
```

**Issues**:
- ❌ URLs expire between phases
- ❌ Session cookies lost
- ❌ DOI redirects may change
- ❌ HTTP 403 errors from changing User-Agent
- ❌ Extra network round-trips

### Proposed Solution (Single-Phase Approach)

**Option A: Enhance FullTextManager**

```python
# FullTextManager downloads immediately
class FullTextManager:
    async def get_fulltext(
        self,
        publication: Publication,
        download_immediately: bool = True
    ) -> FullTextResult:
        """
        Get full-text and optionally download PDF immediately.

        If download_immediately=True:
        - Finds URL
        - Downloads PDF in SAME session
        - Returns FullTextResult with pdf_path populated

        If download_immediately=False:
        - Just returns URL (current behavior)
        """
        for source in self.sources:
            url = await source.get_pdf_url(publication)
            if url:
                if download_immediately:
                    # Download NOW while session is active
                    pdf_path = await self._download_pdf(
                        url=url,
                        publication=publication,
                        session=source.session  # Reuse same session!
                    )
                    return FullTextResult(
                        success=True,
                        url=url,
                        pdf_path=pdf_path,  # ← Actual file!
                        source=source
                    )
                else:
                    # Old behavior: just URL
                    return FullTextResult(success=True, url=url, source=source)

        return FullTextResult(success=False)

    async def _download_pdf(
        self,
        url: str,
        publication: Publication,
        session: aiohttp.ClientSession
    ) -> Path:
        """Download PDF using existing session (preserves cookies/headers)"""
        # Reuse PDFDownloadManager logic but with session
        # Add User-Agent headers
        # Handle redirects
        # Validate PDF
        ...
```

**Benefits**:
- ✅ Session preserved (cookies, auth)
- ✅ User-Agent consistent
- ✅ Redirects followed properly
- ✅ Immediate validation
- ✅ No URL expiration

**Option B: Wrapper Class**

```python
class IntegratedFullTextDownloader:
    """Combines FullTextManager + PDFDownloadManager"""

    def __init__(self):
        self.fulltext_mgr = FullTextManager()
        self.pdf_downloader = PDFDownloadManager()

    async def get_and_download(
        self,
        publication: Publication,
        output_dir: Path
    ) -> DownloadResult:
        """One-shot: Find URL + Download PDF"""

        # Get URL with session preserved
        result = await self.fulltext_mgr.get_fulltext(publication)

        if result.success and result.url:
            # Download IMMEDIATELY using same session
            pdf_path = await self.pdf_downloader.download_single(
                url=result.url,
                publication=publication,
                output_dir=output_dir,
                session=self.fulltext_mgr.session  # ← Shared session!
            )

            return DownloadResult(
                publication=publication,
                success=pdf_path is not None,
                pdf_path=pdf_path,
                url=result.url,
                source=result.source
            )

        return DownloadResult(publication=publication, success=False)
```

### Implementation Steps

1. **Add User-Agent Headers** (IMMEDIATE FIX)
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 (compatible; OmicsOracle/1.0; +https://github.com/yourusername/omicsoracle)'
   }
   ```

2. **Handle Redirects** (IMMEDIATE FIX)
   ```python
   async with session.get(url, allow_redirects=True) as response:
       # Follow DOI redirects to actual PDF
       final_url = str(response.url)
   ```

3. **Session Preservation** (REFACTOR)
   - Make FullTextManager keep session alive
   - Pass session to download function
   - Reuse cookies/auth

4. **Enhanced Validation** (IMPROVEMENT)
   - Check Content-Type header
   - Validate PDF magic bytes
   - Handle HTML landing pages

---

## 🎬 Execution Plan

### This Week (Oct 11-15, 2025)

**Day 1 (Today)**: ✅ COMPLETE
- [x] Run verification scripts
- [x] Generate this report
- [x] Identify archive candidates

**Day 2 (Oct 12)**: Archive orphaned files
- [ ] Archive integration layer orphans
- [ ] Run full test suite
- [ ] Commit if tests pass

**Day 3 (Oct 13)**: Quick fixes
- [ ] Add User-Agent headers to PDFDownloadManager
- [ ] Handle redirects properly
- [ ] Test with current pipeline

**Day 4 (Oct 14)**: Refactor planning
- [ ] Review Option A vs Option B
- [ ] Create refactor branch
- [ ] Start implementation

**Day 5 (Oct 15)**: Testing
- [ ] Test direct downloads
- [ ] Measure success rate improvement
- [ ] Update documentation

### Next Week (Oct 18-22, 2025)

- Complete refactoring
- Update all examples
- Archive old test files
- Final validation

---

## ✅ Success Metrics

### Code Cleanup
- [x] Identified 36 orphaned files
- [x] Identified 19 duplicate classes
- [ ] Archive 6+ high-confidence orphans
- [ ] Consolidate 3+ duplicate models
- [ ] All tests passing after archiving

### PDF Download Improvement
- Current: 1/5 PDFs downloaded (20% success)
- Target: 4/5 PDFs downloaded (80% success)
- Measure: Run test_unified_pipeline_validation.py

### Code Quality
- Reduce: Total Python files by 10%
- Improve: Import graph clarity
- Remove: All duplicate model classes
- Document: What was archived and why

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Create backup branch before archiving
- Run full test suite after each move
- Keep archive directory for rollback

### Risk 2: Hidden Dependencies
**Mitigation**:
- Use verification script
- Manual code review
- Gradual archiving (not bulk)

### Risk 3: Test Failures
**Mitigation**:
- Update tests before archiving
- Check examples for usage
- Document breaking changes

---

## 📝 Next Actions

**IMMEDIATE** (Today):
1. Review this report with team/user
2. Get approval for archive list
3. Create backup branch

**THIS WEEK**:
1. Execute Phase 1 archiving
2. Implement quick PDF download fixes
3. Test and measure improvement

**NEXT WEEK**:
1. Refactor to direct downloads
2. Complete consolidation
3. Update all documentation

---

**Report Status**: ✅ READY FOR REVIEW
**Confidence Level**: HIGH (verified with automated tools)
**Recommendation**: Proceed with Phase 1 archiving
