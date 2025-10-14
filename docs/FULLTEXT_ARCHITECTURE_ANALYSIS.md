# FULLTEXT SYSTEM ARCHITECTURE ANALYSIS

**Date:** October 13, 2025
**Purpose:** Identify redundant/duplicate code in URL collection and PDF downloading

## CRITICAL DISCOVERY: TWO PARALLEL FULLTEXT SYSTEMS

### 1. OLD SYSTEM: `lib/fulltext/`
Location: `/lib/fulltext/`

Files found:
- `manager_integration.py`
- `pdf_extractor.py`
- `pdf_downloader.py`
- `validators.py`
- `models.py`
- `content_fetcher.py`
- `content_extractor.py`

### 2. NEW SYSTEM: `omics_oracle_v2/lib/enrichment/fulltext/`
Location: `/omics_oracle_v2/lib/enrichment/fulltext/`

Files found:
- `manager.py` (main orchestrator)
- `download_manager.py` (PDF downloading)
- `url_validator.py`
- `sources/` (11+ source implementations)
- `cache_db.py`, `smart_cache.py`, `parsed_cache.py`
- `normalizer.py`
- `landing_page_parser.py`

## ANALYSIS PLAN

### Step 1: Identify Which System Is Active
- Check imports in `agents.py` and other active code
- Determine if old system is still used anywhere
- Map execution flow to confirm which system handles requests

### Step 2: URL Collection Analysis
- Map all methods that collect URLs
- Identify redundant URL collection logic
- Find unused source implementations

### Step 3: PDF Download Analysis
- Compare `lib/fulltext/pdf_downloader.py` vs `download_manager.py`
- Identify parallel implementations
- Find unused download methods

### Step 4: Clean Up Strategy
- Deprecate/remove unused implementations
- Consolidate overlapping functionality
- Update imports and documentation

## EXECUTION FLOW VERIFICATION

Need to trace:
1. `/enrich-fulltext` endpoint → which system?
2. URL collection: which sources are actually called?
3. PDF download: which methods are actually used?
4. Caching: which cache systems are active?

## FINDINGS TO UPDATE AS WE DISCOVER
