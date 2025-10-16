-- Unified Database Schema for OmicsOracle
-- GEO-Centric Design: All data organized by GEO dataset ID
-- Version: 1.0.0
-- Created: 2025-10-14

-- =============================================================================
-- TABLE 1: Universal Identifiers (Central Hub)
-- =============================================================================
-- Links GEO datasets to publications with all possible identifiers
-- Uses auto-incrementing ID as PRIMARY KEY to support papers without PMID
-- At least one identifier (pmid, doi, pmc_id, arxiv_id) must be present
CREATE TABLE IF NOT EXISTS universal_identifiers (
    -- Auto-incrementing primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- GEO dataset reference
    geo_id TEXT NOT NULL,
    
    -- Publication identifiers (at least one should be present)
    pmid TEXT,  -- Optional - not all papers have PMIDs (preprints, DOI-only, etc.)
    doi TEXT,
    pmc_id TEXT,
    arxiv_id TEXT,

    -- Publication metadata
    title TEXT NOT NULL,  -- Every paper MUST have a title (fallback identifier)
    authors TEXT,  -- JSON array of author objects
    journal TEXT,
    publication_year INTEGER,
    publication_date TEXT,  -- ISO 8601 format

    -- Timestamps
    first_discovered_at TEXT NOT NULL,  -- ISO 8601 format
    last_updated_at TEXT NOT NULL,      -- ISO 8601 format

    -- Ensure at least one identifier OR title exists (title is always present, so this is always satisfied)
    CHECK (pmid IS NOT NULL OR doi IS NOT NULL OR pmc_id IS NOT NULL OR arxiv_id IS NOT NULL OR title IS NOT NULL),
    
    -- Prevent duplicate entries for same paper
    UNIQUE(geo_id, pmid, doi)
);

CREATE INDEX IF NOT EXISTS idx_ui_geo_id ON universal_identifiers(geo_id);
CREATE INDEX IF NOT EXISTS idx_ui_pmid ON universal_identifiers(pmid);
CREATE INDEX IF NOT EXISTS idx_ui_doi ON universal_identifiers(doi);
CREATE INDEX IF NOT EXISTS idx_ui_year ON universal_identifiers(publication_year);
-- Composite index for common JOIN pattern in get_complete_geo_data()
CREATE INDEX IF NOT EXISTS idx_ui_geo_pmid_composite ON universal_identifiers(geo_id, pmid);


-- =============================================================================
-- TABLE 2: GEO Datasets
-- =============================================================================
-- Metadata and statistics for each GEO dataset
CREATE TABLE IF NOT EXISTS geo_datasets (
    geo_id TEXT PRIMARY KEY,

    -- GEO metadata
    title TEXT,
    summary TEXT,
    organism TEXT,
    platform TEXT,

    -- Statistics (auto-computed)
    publication_count INTEGER DEFAULT 0,
    pdfs_downloaded INTEGER DEFAULT 0,
    pdfs_extracted INTEGER DEFAULT 0,
    avg_extraction_quality REAL DEFAULT 0.0,  -- 0.0 to 1.0

    -- Timestamps
    created_at TEXT NOT NULL,
    last_processed_at TEXT NOT NULL,

    -- Processing status
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, failed
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_geo_organism ON geo_datasets(organism);
CREATE INDEX IF NOT EXISTS idx_geo_status ON geo_datasets(status);


-- =============================================================================
-- TABLE 3: URL Discovery (Pipeline 2 Results)
-- =============================================================================
-- Stores URLs found from all sources (PubMed, Unpaywall, Europe PMC, etc.)
CREATE TABLE IF NOT EXISTS url_discovery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign keys
    geo_id TEXT NOT NULL,
    pmid TEXT,  -- Optional - paper might only have DOI

    -- Discovery results
    urls_json TEXT NOT NULL,  -- JSON array of URL objects with metadata
    sources_queried TEXT NOT NULL,  -- JSON array of source names
    url_count INTEGER DEFAULT 0,

    -- Source breakdown
    pubmed_urls INTEGER DEFAULT 0,
    unpaywall_urls INTEGER DEFAULT 0,
    europepmc_urls INTEGER DEFAULT 0,
    other_urls INTEGER DEFAULT 0,

    -- Quality metrics
    has_pdf_url BOOLEAN DEFAULT 0,
    has_html_url BOOLEAN DEFAULT 0,
    best_url_type TEXT,  -- 'pdf', 'html', 'xml', 'none'

    -- Timestamps
    discovered_at TEXT NOT NULL,

    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX IF NOT EXISTS idx_url_geo_pmid ON url_discovery(geo_id, pmid);
CREATE INDEX IF NOT EXISTS idx_url_has_pdf ON url_discovery(has_pdf_url);


-- =============================================================================
-- TABLE 4: PDF Acquisition (Pipeline 3 Results)
-- =============================================================================
-- Tracks PDF downloads and file locations
CREATE TABLE IF NOT EXISTS pdf_acquisition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign keys
    geo_id TEXT NOT NULL,
    pmid TEXT,  -- Optional - paper might only have DOI

    -- File metadata
    pdf_path TEXT NOT NULL,  -- Relative path: by_geo/{geo_id}/pmid_{pmid}.pdf
    pdf_hash_sha256 TEXT NOT NULL,  -- For integrity verification
    pdf_size_bytes INTEGER,

    -- Download metadata
    source_url TEXT,
    source_type TEXT,  -- 'pubmed', 'unpaywall', 'europepmc', 'manual'
    download_method TEXT,  -- 'direct', 'selenium', 'manual'

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, downloaded, verified, failed
    error_message TEXT,

    -- Timestamps
    downloaded_at TEXT NOT NULL,
    verified_at TEXT,

    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX IF NOT EXISTS idx_pdf_geo_pmid ON pdf_acquisition(geo_id, pmid);
CREATE INDEX IF NOT EXISTS idx_pdf_status ON pdf_acquisition(status);
CREATE INDEX IF NOT EXISTS idx_pdf_hash ON pdf_acquisition(pdf_hash_sha256);


-- =============================================================================
-- TABLE 5: Content Extraction (Pipeline 4 Basic Extraction)
-- =============================================================================
-- Basic text extraction results from PDFs
CREATE TABLE IF NOT EXISTS content_extraction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign keys
    geo_id TEXT NOT NULL,
    pmid TEXT,  -- Optional - paper might only have DOI

    -- Extracted content
    full_text TEXT,
    page_count INTEGER,
    word_count INTEGER,
    char_count INTEGER,

    -- Extraction metadata
    extractor_used TEXT,  -- 'pypdf', 'pdfplumber', 'grobid', etc.
    extraction_method TEXT,  -- 'text', 'ocr', 'hybrid'

    -- Quality metrics
    extraction_quality REAL,  -- 0.0 to 1.0
    extraction_grade TEXT,    -- 'A', 'B', 'C', 'D', 'F'
    has_readable_text BOOLEAN DEFAULT 0,
    needs_ocr BOOLEAN DEFAULT 0,

    -- Timestamps
    extracted_at TEXT NOT NULL,

    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX IF NOT EXISTS idx_extract_geo_pmid ON content_extraction(geo_id, pmid);
CREATE INDEX IF NOT EXISTS idx_extract_quality ON content_extraction(extraction_quality);
CREATE INDEX IF NOT EXISTS idx_extract_grade ON content_extraction(extraction_grade);


-- =============================================================================
-- TABLE 6: Enriched Content (Pipeline 4 Advanced Features)
-- =============================================================================
-- Advanced enrichment: sections, tables, references, etc.
CREATE TABLE IF NOT EXISTS enriched_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign keys
    geo_id TEXT NOT NULL,
    pmid TEXT,  -- Optional - paper might only have DOI

    -- Enriched data (all JSON)
    sections_json TEXT,      -- Detected sections (abstract, methods, results, etc.)
    tables_json TEXT,        -- Extracted tables with structure
    references_json TEXT,    -- Parsed references
    figures_json TEXT,       -- Figure captions and metadata

    -- ChatGPT formatting
    chatgpt_prompt TEXT,     -- Formatted prompt for ChatGPT
    chatgpt_metadata TEXT,   -- JSON metadata about formatting

    -- GROBID results (if available)
    grobid_xml TEXT,
    grobid_tei_json TEXT,

    -- Enrichment metadata
    enrichers_applied TEXT,  -- JSON array of enricher names
    enrichment_quality REAL, -- 0.0 to 1.0

    -- Timestamps
    enriched_at TEXT NOT NULL,

    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX IF NOT EXISTS idx_enriched_geo_pmid ON enriched_content(geo_id, pmid);


-- =============================================================================
-- TABLE 7: Processing Log (Audit Trail)
-- =============================================================================
-- Tracks all processing events across all pipelines
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Context
    geo_id TEXT NOT NULL,
    pmid TEXT,  -- Nullable for GEO-level events

    -- Event details
    pipeline TEXT NOT NULL,  -- 'P1', 'P2', 'P3', 'P4', 'system'
    event_type TEXT NOT NULL,  -- 'start', 'success', 'error', 'retry', 'skip'
    message TEXT,

    -- Performance metrics
    duration_ms INTEGER,
    memory_mb REAL,

    -- Error tracking
    error_type TEXT,
    error_traceback TEXT,

    -- Timestamp
    logged_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_log_geo_id ON processing_log(geo_id);
CREATE INDEX IF NOT EXISTS idx_log_pipeline ON processing_log(pipeline);
CREATE INDEX IF NOT EXISTS idx_log_event_type ON processing_log(event_type);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON processing_log(logged_at);


-- =============================================================================
-- TABLE 8: Cache Metadata
-- =============================================================================
-- Tracks all cache files (citations, URLs, PDFs, parsed content)
CREATE TABLE IF NOT EXISTS cache_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Cache identification
    cache_key TEXT NOT NULL UNIQUE,
    cache_type TEXT NOT NULL,  -- 'citation', 'url', 'pdf', 'parsed', 'enriched'

    -- Associated identifiers
    geo_id TEXT,
    pmid TEXT,

    -- File metadata
    file_path TEXT,
    file_size_bytes INTEGER,
    file_hash_sha256 TEXT,

    -- Cache policy
    ttl_days INTEGER DEFAULT 30,
    expires_at TEXT,

    -- Status
    is_valid BOOLEAN DEFAULT 1,
    last_accessed_at TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_metadata(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_type ON cache_metadata(cache_type);
CREATE INDEX IF NOT EXISTS idx_cache_geo_pmid ON cache_metadata(geo_id, pmid);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_metadata(expires_at);


-- =============================================================================
-- VIEWS: Convenient Query Helpers
-- =============================================================================

-- View: Complete publication info (universal_identifiers + all pipeline results)
CREATE VIEW IF NOT EXISTS v_complete_publications AS
SELECT
    ui.*,
    ud.url_count,
    ud.has_pdf_url,
    pa.pdf_path,
    pa.pdf_size_bytes,
    pa.status as pdf_status,
    ce.extraction_quality,
    ce.extraction_grade,
    ce.word_count,
    ec.chatgpt_prompt IS NOT NULL as has_chatgpt_prompt
FROM universal_identifiers ui
LEFT JOIN url_discovery ud ON ui.geo_id = ud.geo_id AND ui.pmid = ud.pmid
LEFT JOIN pdf_acquisition pa ON ui.geo_id = pa.geo_id AND ui.pmid = pa.pmid
LEFT JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
LEFT JOIN enriched_content ec ON ui.geo_id = ec.geo_id AND ui.pmid = ec.pmid;


-- View: GEO dataset statistics (aggregated from all tables)
CREATE VIEW IF NOT EXISTS v_geo_statistics AS
SELECT
    g.geo_id,
    g.title,
    g.organism,
    COUNT(DISTINCT ui.pmid) as publication_count,
    COUNT(DISTINCT pa.pmid) as pdfs_downloaded,
    COUNT(DISTINCT ce.pmid) as pdfs_extracted,
    AVG(ce.extraction_quality) as avg_quality,
    COUNT(DISTINCT CASE WHEN ce.extraction_grade IN ('A', 'B') THEN ce.pmid END) as high_quality_count
FROM geo_datasets g
LEFT JOIN universal_identifiers ui ON g.geo_id = ui.geo_id
LEFT JOIN pdf_acquisition pa ON g.geo_id = pa.geo_id
LEFT JOIN content_extraction ce ON g.geo_id = ce.geo_id
GROUP BY g.geo_id;
