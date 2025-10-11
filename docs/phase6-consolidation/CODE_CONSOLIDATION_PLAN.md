# Code Consolidation & Deduplication Plan
**Date**: October 11, 2025
**Purpose**: Identify and archive duplicate/obsolete code before unified pipeline refactoring

## 🎯 Goals

1. **Identify** duplicate implementations (pre-unified vs unified pipeline)
2. **Verify** what's actually being used in production code
3. **Archive** obsolete code safely with full verification
4. **Refactor** to direct PDF downloads (eliminate two-phase approach)

## 📋 Phase 1: Discovery & Mapping

### Step 1: Find All Full-Text/PDF Related Code

```bash
# Search for full-text retrieval implementations
grep -r "class.*FullText" --include="*.py" omics_oracle_v2/
grep -r "def.*get_fulltext" --include="*.py" omics_oracle_v2/
grep -r "PDFDownload" --include="*.py" omics_oracle_v2/

# Find all citation discovery code
grep -r "class.*Citation.*Discovery" --include="*.py" omics_oracle_v2/
grep -r "class.*Citation.*Finder" --include="*.py" omics_oracle_v2/

# Find GEO-related clients
grep -r "class.*GEO.*Client" --include="*.py" omics_oracle_v2/
```

### Step 2: Map Import Dependencies

For each file found, trace:
- What imports it?
- What does it import?
- Is it used by unified pipeline?
- Is it used by examples/tests?

**Method**: Use `list_code_usages` tool to find all references

### Step 3: Identify Current Active Components

**Unified Search Pipeline Stack** (what we KNOW is active):
```
omics_oracle_v2/
├── unified_search_pipeline.py          # Main orchestrator
├── lib/fulltext/manager.py             # FullTextManager (URLs only)
├── lib/storage/pdf/download_manager.py # PDFDownloadManager (actual downloads)
├── lib/citations/discovery/finder.py   # GEOCitationDiscovery
├── lib/geo/client.py                   # GEOClient
└── agents/search_agent.py              # SearchAgent
```

### Step 4: Find Potential Duplicates

**Candidates for Archive** (need verification):
- Old PDF downloaders in `lib/publications/clients/`
- Deprecated citation discovery in `lib/archive/deprecated_*/`
- Individual full-text clients NOT used by FullTextManager
- Old GEO scrapers before GEOClient

## 📋 Phase 2: Verification Strategy

### A. Automated Verification

```python
# Script: scripts/verify_code_usage.py

import ast
import os
from pathlib import Path
from collections import defaultdict

def find_all_imports(file_path):
    """Parse file and extract all imports"""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    return imports

def build_dependency_graph():
    """Build full dependency graph"""
    graph = defaultdict(list)

    for py_file in Path("omics_oracle_v2").rglob("*.py"):
        imports = find_all_imports(py_file)
        for imp in imports:
            if imp.startswith("omics_oracle_v2"):
                graph[str(py_file)].append(imp)

    return graph

def find_orphaned_files():
    """Find files never imported by anything"""
    all_files = set(Path("omics_oracle_v2").rglob("*.py"))
    graph = build_dependency_graph()

    imported = set()
    for imports in graph.values():
        for imp in imports:
            # Convert import path to file path
            file_path = imp.replace(".", "/") + ".py"
            imported.add(file_path)

    orphaned = all_files - imported
    return orphaned
```

### B. Manual Verification Checklist

For each candidate file, verify:

- [ ] **Import Check**: Is it imported anywhere?
  - Search: `grep -r "from.*{module}" omics_oracle_v2/ examples/ tests/`
  - Search: `grep -r "import.*{module}" omics_oracle_v2/ examples/ tests/`

- [ ] **Usage Check**: Is it called/instantiated?
  - Use `list_code_usages` tool
  - Check class instantiation patterns

- [ ] **Test Coverage**: Does it have tests?
  - Search: `grep -r "{class_name}" tests/`
  - If tests exist but class unused → Archive tests too

- [ ] **Documentation**: Is it mentioned in docs?
  - Search: `grep -r "{class_name}" docs/`
  - Update docs to point to new implementation

- [ ] **Example Usage**: Used in examples?
  - Search: `grep -r "{class_name}" examples/`
  - Update examples or create new ones

### C. Verification Report Template

```markdown
## File: {path}

**Status**: [ACTIVE | CANDIDATE | ARCHIVE]

### Import Analysis
- Imported by: [list of files]
- Imports: [list of dependencies]

### Usage Analysis
- Used in unified pipeline: YES/NO
- Used in examples: YES/NO (list)
- Used in tests: YES/NO (list)
- Used in other components: YES/NO (list)

### Recommendation
- [ ] Keep (actively used)
- [ ] Archive (superseded by: {new_implementation})
- [ ] Delete (dead code, no functionality)

### Migration Path
If archiving:
1. What replaces it: {new_class/module}
2. Migration steps: {how to update imports}
3. Breaking changes: {what changes}
```

## 📋 Phase 3: Safe Archiving Process

### Step 1: Create Archive Structure

```
omics_oracle_v2/lib/archive/
├── pre_unified_pipeline_20251011/
│   ├── README.md                    # Why archived, what replaces it
│   ├── fulltext/                    # Old full-text implementations
│   ├── citations/                   # Old citation discovery
│   ├── pdf/                         # Old PDF downloaders
│   └── MIGRATION_GUIDE.md          # How to migrate to new code
```

### Step 2: Archive Workflow (Per File)

```bash
# 1. Verify file is truly orphaned
python scripts/verify_code_usage.py check {file_path}

# 2. Run tests to ensure nothing breaks
pytest tests/ -v

# 3. Move to archive
mkdir -p omics_oracle_v2/lib/archive/pre_unified_pipeline_20251011/{dir}
git mv {file_path} omics_oracle_v2/lib/archive/pre_unified_pipeline_20251011/{dir}/

# 4. Update imports if any exist (should be none)
grep -r "from.*{module}" omics_oracle_v2/
# If found, update to new implementation

# 5. Run tests again
pytest tests/ -v

# 6. Commit with detailed message
git commit -m "archive: Move {file} to pre-unified archive

Reason: Superseded by {new_implementation}
Last used: {date or 'never in unified pipeline'}
Verified no imports: Yes
Tests passing: Yes"
```

### Step 3: Create Archive Documentation

```markdown
# Archive: Pre-Unified Pipeline (October 2025)

## Why This Code Was Archived

The unified search pipeline (`unified_search_pipeline.py`) consolidates
all search, citation, and full-text functionality into a single orchestrated
workflow. The code in this archive represents individual implementations
that were replaced by the unified approach.

## What Replaced What

| Archived Component | Replaced By | Notes |
|-------------------|-------------|-------|
| `old_pdf_downloader.py` | `storage/pdf/download_manager.py` | New async implementation |
| `old_fulltext_client.py` | `fulltext/manager.py` | Centralized source management |
| ... | ... | ... |

## Migration Guide

### If You Need Old Functionality

1. Check if unified pipeline supports it
2. If not, extract from archive and adapt
3. Consider contributing back to unified pipeline

### Import Changes

**Old**:
```python
from omics_oracle_v2.lib.publications.clients.pdf_downloader import PDFDownloader
```

**New**:
```python
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager
```
```

## 📋 Phase 4: Refactor to Direct Downloads

### Current Flow (Two-Phase - PROBLEMATIC)

```python
# Phase 1: Get URLs only
fulltext_mgr = FullTextManager(download_pdfs=False)
result = await fulltext_mgr.get_fulltext(pub)
pub.pdf_url = result.url  # Just the URL

# Phase 2: Download later (FAILS if URL changed/expired)
downloader = PDFDownloadManager()
await downloader.download_batch(publications, ...)
```

**Problems**:
- URLs can expire between phases
- DOI redirects may change
- Cookies/sessions lost
- Extra network round-trips

### Proposed Flow (Single-Phase - BETTER)

```python
# Option A: FullTextManager downloads directly
fulltext_mgr = FullTextManager(download_pdfs=True, pdf_dir=output_dir)
result = await fulltext_mgr.get_fulltext(pub)
# result.pdf_path is actual file (not None)
# result.url is backup

# Option B: Integrated approach
class IntegratedFullTextDownloader:
    """Combines URL discovery + immediate download"""

    async def get_and_download_fulltext(self, pub, output_dir):
        # Try each source in priority order
        for source in [Unpaywall, PMC, CORE, ...]:
            url = await source.get_pdf_url(pub)
            if url:
                # Download IMMEDIATELY while session active
                pdf_path = await self._download_from_url(url, output_dir)
                if pdf_path:
                    return FullTextResult(
                        success=True,
                        pdf_path=pdf_path,
                        url=url,
                        source=source
                    )
        return FullTextResult(success=False)
```

### Refactoring Steps

1. **Modify FullTextManager** to download immediately when `download_pdfs=True`
2. **Add session persistence** to preserve cookies/auth between URL discovery and download
3. **Handle redirects properly** - follow DOI redirects to final PDF
4. **Add User-Agent headers** - avoid bot detection
5. **Update tests** to verify direct downloads work

## 📊 Execution Timeline

### Week 1: Discovery & Verification
- [ ] Day 1: Run automated discovery scripts
- [ ] Day 2: Manual verification of top 20 candidates
- [ ] Day 3: Create verification reports
- [ ] Day 4: Review and approve archive list

### Week 2: Archiving
- [ ] Day 1: Archive first batch (verified orphans)
- [ ] Day 2: Update imports and tests
- [ ] Day 3: Archive second batch
- [ ] Day 4: Final verification, all tests passing

### Week 3: Refactoring
- [ ] Day 1-2: Refactor FullTextManager for direct downloads
- [ ] Day 3: Update tests and examples
- [ ] Day 4: Integration testing

## 🚨 Risk Mitigation

### Before Any Archive Operation

1. **Full test suite must pass**: `pytest tests/ -v`
2. **Create backup branch**: `git checkout -b backup-pre-archive-{date}`
3. **Document all changes**: Update CHANGELOG.md
4. **Verify no imports**: Use verification script
5. **Get review**: Don't archive alone, verify with team/peer

### Rollback Plan

If something breaks after archiving:
```bash
# 1. Identify what broke
pytest tests/ -v  # Find failing tests

# 2. Check if it was archived code
git log --all --oneline -- {file_path}

# 3. Restore from archive
git checkout backup-pre-archive-{date} -- {file_path}

# 4. Fix imports
grep -r "import.*{module}" omics_oracle_v2/

# 5. Verify tests pass
pytest tests/ -v
```

## 📝 Success Criteria

- [ ] All duplicate code identified and cataloged
- [ ] Verification reports complete for all candidates
- [ ] Archive structure created with documentation
- [ ] All tests passing after each archive operation
- [ ] Unified pipeline uses direct downloads (no two-phase)
- [ ] PDF download success rate improves (target: >80%)
- [ ] No import errors in codebase
- [ ] Examples updated to use new implementations
- [ ] Documentation updated

## 🎯 Next Actions

1. **Immediate**: Run discovery scripts to find all candidates
2. **Today**: Start verification of top 10 most likely duplicates
3. **This Week**: Archive first batch of verified orphans
4. **Next Week**: Refactor FullTextManager for direct downloads

---

**Prepared by**: AI Assistant
**Review Required**: Yes
**Approved by**: _____________
**Date**: _____________
