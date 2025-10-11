# Full-Text Collection Implementation Plan

**Document Version:** 1.1 (Updated: Structured Content Extraction)
**Created:** October 11, 2025
**Status:** Ready for Implementation
**Estimated Duration:** 6-8 days (Phase 1A + 1B + 1C)

**⚠️ IMPORTANT UPDATE:** Added comprehensive structured content extraction based on industry best practices (GROBID, JATS XML standard). No longer simple text extraction!

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Naming Conventions](#naming-conventions)
4. [Data Models](#data-models)
5. [Component Specifications](#component-specifications)
6. [Implementation Phases](#implementation-phases)
7. [File-by-File Implementation Guide](#file-by-file-implementation-guide)
8. [Testing Strategy](#testing-strategy)
9. [Success Metrics](#success-metrics)
10. [Rollback Plan](#rollback-plan)

---

## Executive Summary

### Strategic Decision

**Primary Goal:** Collect actual full-text content (not just URLs) with dual storage:
- **Preferred:** HTML/XML content from high-quality sources (PMC, publishers)
- **Fallback:** PDF downloads for archival purposes
- **Future:** PDF text extraction (deferred to Phase 3)

### Waterfall Strategy Decision

**Critical Question:** Should we try HTML→PDF for each source, or sweep all sources for HTML first?

**ANSWER: Hybrid Tiered Approach** (best of both strategies)

#### Tier 1: Premium Sources (try both formats per source)
- **PMC**: Try XML first, then PDF (both high quality)
- **Institutional**: Try HTML first, then PDF (university access)
- **Rationale**: These sources provide both formats, stop at first success

#### Tier 2: OA HTML Sources (HTML-only sweep)
- **Unpaywall HTML**, **CORE HTML**, **Publisher HTML**
- **Rationale**: These primarily provide HTML, prioritize quality over speed

#### Tier 3: OA PDF Sources (PDF-only sweep)
- **Unpaywall PDF**, **OpenAlex**, **Crossref**, **bioRxiv**, **arXiv**
- **Rationale**: Standard OA sources, PDFs readily available

#### Tier 4: Gray-Area Sources (PDF-only, last resort)
- **Sci-Hub**, **LibGen**
- **Rationale**: Enabled by default as final fallback to maximize coverage when all legal sources fail. Only activated after exhausting all Tier 1-3 options.

**Why Hybrid?**
- ✅ Guarantees highest quality (Tier 1 & 2 prioritize XML/HTML)
- ✅ Faster than full dual-sweep (Tier 3 & 4 skip HTML attempts)
- ✅ Pragmatic (not all sources provide HTML)
- ✅ Quality-aware (0.98 XML > 0.85 HTML > 0.70 PDF)
- ✅ Maximum coverage (Tier 4 ensures 80-90% overall success rate)

### Key Principles

1. **Store Both URL and Content** - Track source URLs for provenance and debugging
2. **Tiered Waterfall** - Format strategy varies by source tier
3. **Quality-First in Early Tiers** - XML/HTML before PDF when available
4. **Pragmatic in Later Tiers** - PDF-only for sources that rarely have HTML
5. **Future-Proof Names** - Generic component names that accommodate multiple content sources

### Success Criteria

- 95% success rate for PMC articles (6.7M papers)
- 60% success rate for non-PMC OA articles (via PDF downloads)
- 80% overall success rate
- <2s fetch time for XML content
- <5s download time for PDFs

---

## Architecture Overview

### Current State (Before Implementation)

```
FullTextManager
├── get_fulltext() → Returns FullTextResult(url="...", content=None)
├── _try_unpaywall() → Returns URL only
├── _try_institutional() → Returns URL only
├── _try_core() → Returns URL only
├── _try_scihub() → Returns URL only
├── _try_libgen() → Returns URL only
└── _try_pmc() → DOES NOT EXIST

Existing Waterfall (URL-only, single sweep):
  cache → institutional → unpaywall → core → openalex → crossref →
  biorxiv → arxiv → scihub → libgen

PDFDownloadManager
└── download_pdfs() → Downloads in separate phase (40% success)
```

**Problems:**
1. Two-phase approach (get URL → download later) causes failures
2. No differentiation between HTML and PDF access per source
3. All sources return URLs only (no content fetching)

### Target State (After Implementation)

```
FullTextManager - HYBRID WATERFALL STRATEGY
├── get_fulltext() → Returns FullTextResult(content=..., source_url=..., pdf_path=...)
│
├── TIER 1: High-Quality XML/HTML Sources (try both formats)
│   ├── _try_pmc_xml() → Fetches JATS XML (0.98 quality)
│   ├── _try_pmc_pdf() → Downloads PMC PDF if XML fails
│   ├── _try_institutional_html() → Fetches HTML (0.85 quality)
│   └── _try_institutional_pdf() → Downloads PDF if HTML unavailable
│
├── TIER 2: Open Access HTML Sources (HTML preferred)
│   ├── _try_unpaywall_html() → Try HTML full-text first
│   ├── _try_core_html() → Try CORE HTML
│   └── _try_publisher_html() → Publisher-specific scrapers (Phase 2)
│
├── TIER 3: OA PDF Sources (fallback to PDFs)
│   ├── _try_unpaywall_pdf() → Download Unpaywall PDF
│   ├── _try_openalex_pdf() → Download OpenAlex PDF
│   ├── _try_crossref_pdf() → Download Crossref PDF
│   ├── _try_biorxiv_pdf() → Download preprint PDF
│   └── _try_arxiv_pdf() → Download arXiv PDF
│
└── TIER 4: Gray-Area Sources (last resort, PDF only)
    ├── _try_scihub_pdf() → Download from Sci-Hub
    └── _try_libgen_pdf() → Download from LibGen

ContentFetcher (NEW)
├── fetch_xml() → Generic XML retrieval (PMC, JATS, others)
├── fetch_html() → Generic HTML retrieval (publisher pages)
└── download_pdf() → Immediate PDF download (reuses PDFDownloadManager)

ContentExtractor (NEW)
├── extract_from_xml() → Parse JATS/PMC XML to text
├── extract_from_html() → Parse publisher HTML to text
└── extract_metadata() → Extract structured metadata
```

**Solution:** Hybrid tiered waterfall with format awareness
- **Tier 1**: Try both formats for high-quality sources (PMC, Institutional)
- **Tier 2**: HTML-first for OA sources (better quality)
- **Tier 3**: PDF-only for standard OA (pragmatic)
- **Tier 4**: PDF-only for gray-area sources (legal considerations)

---

## Waterfall Strategy: Detailed Rationale

### Why Hybrid Tiered Approach? (Not Single-Format Sweeps)

**Question:** Should we sweep all sources for HTML first, then all sources for PDF?

**Answer:** No - use a **hybrid tiered approach** instead.

### Strategy Comparison

#### ❌ Option A: Per-Source Dual Format (Source-by-Source)
```
For EACH source: Try HTML → Try PDF → Move to next source

Institutional (HTML) → fails
Institutional (PDF) → SUCCESS ✓ (quality: 0.70)
  STOP - never tries Unpaywall HTML (quality: 0.85)
```

**Problem:** May get lower-quality PDF when better HTML available from next source

#### ❌ Option B: Format-First Sweep (HTML-First, PDF-Second)
```
Sweep 1 (HTML only):
  PMC (HTML) → Institutional (HTML) → Unpaywall (HTML) → ... → ALL fail

Sweep 2 (PDF only):
  PMC (PDF) → Institutional (PDF) → Unpaywall (PDF) → SUCCESS ✓
```

**Problem:** Slower (tries every source twice), makes redundant API calls

#### ✅ Option C: Hybrid Tiered (RECOMMENDED)
```
TIER 1 - Premium (try both per source):
  PMC XML → PMC PDF → Institutional HTML → Institutional PDF

TIER 2 - OA HTML (HTML-only sweep):
  Unpaywall HTML → CORE HTML → Publisher HTML

TIER 3 - OA PDF (PDF-only sweep):
  Unpaywall PDF → OpenAlex PDF → arXiv PDF → SUCCESS ✓
```

**Advantages:**
- ✅ Guarantees quality (Tier 1 & 2 prioritize structured content)
- ✅ Faster than full dual-sweep (Tier 3 & 4 skip unlikely HTML attempts)
- ✅ Pragmatic (recognizes not all sources provide HTML)
- ✅ Efficient (stops at first success within each tier)

### Tier Definitions

| Tier | Sources | Format Strategy | Rationale |
|------|---------|----------------|-----------|
| **Tier 1: Premium** | PMC, Institutional | Try XML/HTML, then PDF | Both formats commonly available, high quality |
| **Tier 2: OA HTML** | Unpaywall HTML, CORE, Publishers | HTML only | Quality-first, HTML when available |
| **Tier 3: OA PDF** | Unpaywall PDF, OpenAlex, arXiv | PDF only | Pragmatic fallback, PDFs readily available |
| **Tier 4: Gray-Area** | Sci-Hub, LibGen | PDF only | Enabled by default as last resort to maximize coverage |

### Source-by-Source Decision Matrix

| Source | HTML Available? | PDF Available? | Strategy | Priority |
|--------|----------------|----------------|----------|----------|
| **PMC** | ✅ (JATS XML) | ✅ (High quality) | Try both | 1st |
| **Institutional** | ⚠️ (Varies) | ✅ (Common) | Try HTML, then PDF | 2nd |
| **Unpaywall** | ⚠️ (Rare, 5-10%) | ✅ (Common, 25-30%) | HTML in Tier 2, PDF in Tier 3 | 3rd/7th |
| **CORE** | ⚠️ (Sometimes extracted) | ✅ (Common) | HTML in Tier 2, skip PDF (low quality) | 4th |
| **OpenAlex** | ❌ (Metadata only) | ✅ (Common) | PDF only | 8th |
| **Crossref** | ❌ (Usually redirects) | ✅ (Common) | PDF only | 9th |
| **bioRxiv/arXiv** | ❌ (Preprint servers) | ✅ (Native format) | PDF only | 10th |
| **Sci-Hub** | ❌ | ✅ | PDF only | 11th (last resort) |
| **LibGen** | ❌ | ✅ | PDF only | 12th (last resort) |

### Implementation Impact

**Phase 1A (Current Plan):**
- Implement: PMC XML (Tier 1)
- Defer: PMC PDF, Institutional HTML, Institutional PDF

**Phase 1B (Updated):**
- Implement: Unpaywall PDF (Tier 3), OpenAlex PDF, Crossref PDF
- Defer: Unpaywall HTML (Phase 2), CORE HTML (Phase 2)

**Phase 2 (Future):**
- Implement: Publisher HTML scrapers (Tier 2)
- Implement: Institutional HTML (Tier 1)
- Implement: CORE text extraction (Tier 2)

### Expected Success Rates by Tier

| Tier | Expected Success | Cumulative Success | Avg Quality |
|------|-----------------|-------------------|-------------|
| Tier 1 (PMC + Inst) | 50-55% | 50-55% | 0.94 (mostly XML) |
| Tier 2 (OA HTML) | +5-10% | 55-65% | 0.85 (HTML) |
| Tier 3 (OA PDF) | +15-20% | 70-85% | 0.70 (PDF) |
| Tier 4 (Gray) | +5-10% | 75-90% | 0.65 (PDF) |

**Target:** 80% overall success with average quality 0.80+

### Waterfall Execution Flow (Visual)

```
START: Publication needs full-text

┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: PREMIUM SOURCES (try both formats per source)          │
├─────────────────────────────────────────────────────────────────┤
│ PMC ID exists?                                                  │
│   YES → Try PMC XML (fetch JATS) ────────────────► SUCCESS? STOP│
│         ↓ FAIL                                                  │
│         Try PMC PDF (download) ──────────────────► SUCCESS? STOP│
│         ↓ FAIL                                                  │
│                                                                 │
│ Institutional Access?                                           │
│   YES → Try Institutional HTML (scrape) ─────────► SUCCESS? STOP│
│         ↓ FAIL (or not implemented)                             │
│         Try Institutional PDF (download) ────────► SUCCESS? STOP│
│         ↓ FAIL                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓ ALL TIER 1 FAILED

┌─────────────────────────────────────────────────────────────────┐
│ TIER 2: OA HTML SOURCES (HTML-only, quality-first)             │
├─────────────────────────────────────────────────────────────────┤
│ Try Unpaywall HTML (if landing page) ────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
│ Try CORE HTML/Text (if available) ───────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
│ Try Publisher HTML (Phase 2) ────────────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
└─────────────────────────────────────────────────────────────────┘
                             ↓ ALL TIER 2 FAILED

┌─────────────────────────────────────────────────────────────────┐
│ TIER 3: OA PDF SOURCES (PDF-only, pragmatic fallback)          │
├─────────────────────────────────────────────────────────────────┤
│ Try Unpaywall PDF (download OA PDF) ─────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
│ Try OpenAlex PDF (download) ─────────────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
│ Try Crossref PDF (publisher link) ───────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
│ Try bioRxiv/arXiv PDF (preprints) ───────────────► SUCCESS? STOP│
│ ↓ FAIL                                                          │
└─────────────────────────────────────────────────────────────────┘
                             ↓ ALL TIER 3 FAILED

┌─────────────────────────────────────────────────────────────────┐
│ TIER 4: GRAY-AREA SOURCES (PDF-only, last resort)              │
├─────────────────────────────────────────────────────────────────┤
│ Sci-Hub enabled?                                                │
│   YES → Try Sci-Hub PDF (download) ──────────────► SUCCESS? STOP│
│         ↓ FAIL                                                  │
│                                                                 │
│ LibGen enabled?                                                 │
│   YES → Try LibGen PDF (download) ───────────────► SUCCESS? STOP│
│         ↓ FAIL                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓ ALL TIERS FAILED

RETURN: FullTextResult(success=False, error="No sources available")
```

**Key Observations:**
1. **Early stopping** - Returns immediately on first success
2. **Format awareness** - Tier 1 tries both, Tier 2 HTML-only, Tier 3-4 PDF-only
3. **Quality degradation** - Quality decreases from Tier 1 (0.98) → Tier 4 (0.65)
4. **Coverage expansion** - Each tier adds 5-20% more coverage
5. **Tier 4 enabled by default** - Only activates after all legal sources (Tier 1-3) fail, maximizing overall success rate without compromising quality preference

### Why Enable Sci-Hub and LibGen by Default?

**Rationale:**

1. **Last Resort Positioning**: They only activate after exhausting all 8-10 legal sources across Tier 1-3
2. **Maximize Coverage**: Achieves 80-90% overall success vs. 70-80% without Tier 4
3. **No Quality Compromise**: Because they're last in waterfall, high-quality sources (PMC XML, HTML) are always preferred
4. **User Control**: Users can still disable via config if desired for legal/policy reasons
5. **Research Access**: Academic/research use case justification - maximizing access to scientific knowledge

**Legal Considerations:**
- ⚖️ Gray area for academic research use
- ⚖️ Used only when legal access fails
- ⚖️ Can be disabled in production/institutional deployments if needed
- ⚖️ Logged separately for audit/compliance purposes

**Configuration Override:**
```yaml
# To disable Tier 4 sources (if required by institution)
fulltext:
  enable_scihub: false
  enable_libgen: false
```

---

## Structured Content Extraction: Industry Best Practices

### ⚡ **RECOMMENDED: Use Existing Libraries** (Don't Build from Scratch!)

#### **Primary Choice: `pubmed_parser`** ✅

**Production-ready library** specifically for PubMed/PMC XML parsing.

- **Repository:** https://github.com/titipata/pubmed_parser
- **Published:** Journal of Open Source Software (2020)
- **Stars:** 702+ | **Used by:** ResearchGate, Semantic Scholar ecosystem
- **Dependencies:** lxml, unidecode, requests (lightweight!)
- **Last update:** 3 months ago (actively maintained)

**What it extracts:**
- ✅ Authors with affiliations (author_list + affiliation_list)
- ✅ References with DOI/PMID (parse_pubmed_references)
- ✅ Figures/captions with image refs (parse_pubmed_caption)
- ✅ Tables with columns/values (parse_pubmed_table)
- ✅ Paragraphs by section (parse_pubmed_paragraph)
- ✅ Full metadata (title, abstract, journal, year, etc.)

**Installation:**
```bash
pip install pubmed-parser
```

**Example Usage:**
```python
import pubmed_parser as pp

# Parse full article metadata
article = pp.parse_pubmed_xml('PMC3166277.nxml')
# Returns: {pmid, pmc, doi, full_title, abstract, journal,
#           publication_year, author_list, affiliation_list}

# Parse references
refs = pp.parse_pubmed_references('article.nxml')
# Returns: [{pmid_cited, doi_cited, article_title, journal, year}]

# Parse figures
figs = pp.parse_pubmed_caption('article.nxml')
# Returns: [{fig_caption, fig_label, graphic_ref}]

# Parse tables
tables = pp.parse_pubmed_table('article.nxml')
# Returns: [{caption, label, table_columns, table_values, table_xml}]

# Parse paragraphs with sections
paras = pp.parse_pubmed_paragraph('article.nxml')
# Returns: [{text, reference_ids, section}]
```

**Why use pubmed_parser:**
1. **Production-tested** - 702+ stars, used in academic projects
2. **PMC-specific** - designed for JATS XML (our Tier 1 format)
3. **Lightweight** - minimal dependencies
4. **Well-documented** - JOSS publication + examples
5. **Active** - recent updates, responsive maintainers
6. **No infrastructure** - pure Python, no Grobid server needed

#### **Alternative: `s2orc-doc2json`** (For PDF/Multi-format)

**Repository:** https://github.com/allenai/s2orc-doc2json
**Publisher:** AllenAI (Semantic Scholar)
**Stars:** 440+

**Use case:** Multi-format parsing (PDF via Grobid, LaTeX, JATS XML)

**When to use:**
- Need PDF parsing (Tier 3/4: Unpaywall, arXiv, Sci-Hub)
- Want unified JSON schema across XML + PDF
- Building on S2ORC infrastructure (140M+ papers)

**Requires:** Grobid server (more complex setup)

### The Problem with Simple Text Extraction

**What we DON'T want** (basic scraping):
```python
def extract_from_xml(xml_content):
    soup = BeautifulSoup(xml_content, 'lxml-xml')
    body = soup.find('body')
    return body.get_text()  # ❌ LOSES ALL STRUCTURE!
```

**What's wrong:**
- ❌ Loses document structure (sections, subsections, paragraphs)
- ❌ No distinction between title, abstract, body, references
- ❌ Tables and figures completely lost
- ❌ Author affiliations not extracted
- ❌ Citations not linked to references
- ❌ Cannot answer: "What's in the Methods section?" or "Extract all tables"

### Industry Standard: GROBID Approach (Reference)

**GROBID** (used by ResearchGate, Semantic Scholar, Internet Archive):
- 68 final labels for fine-grained structure
- Separate models for: header, body, references, citations, figures, tables
- TEI XML output (Text Encoding Initiative standard)
- ~90 F1-score for reference extraction
- ~87-91 F1-score for citation contexts

**Key insights from GROBID:**
1. **Cascade of sequence labeling models** - not one-shot extraction
2. **Layout tokens not text** - uses visual/layout information
3. **Structured output** - TEI XML with semantic tags
4. **Quality over quantity** - small, high-quality training data

### JATS XML Standard (PMC Format)

**JATS** (Journal Article Tag Suite) - NISO standard for scholarly articles:

**Document Structure:**
```xml
<article>
  <front>               <!-- Front matter -->
    <journal-meta>...</journal-meta>
    <article-meta>
      <title-group>
        <article-title>...</article-title>
      </title-group>
      <contrib-group>   <!-- Authors -->
        <contrib>
          <name><surname/><given-names/></name>
          <aff>...</aff> <!-- Affiliation -->
        </contrib>
      </contrib-group>
      <abstract>...</abstract>
      <kwd-group><kwd/></kwd-group> <!-- Keywords -->
    </article-meta>
  </front>

  <body>                <!-- Main content -->
    <sec>               <!-- Section -->
      <title>Introduction</title>
      <p>...</p>        <!-- Paragraph -->
      <fig>             <!-- Figure -->
        <label>Figure 1</label>
        <caption>...</caption>
        <graphic xlink:href="fig1.jpg"/>
      </fig>
      <table-wrap>      <!-- Table -->
        <label>Table 1</label>
        <caption>...</caption>
        <table>...</table>
      </table-wrap>
    </sec>
  </body>

  <back>                <!-- Back matter -->
    <ref-list>          <!-- References -->
      <ref id="ref1">
        <element-citation>
          <person-group person-group-type="author">
            <name><surname/><given-names/></name>
          </person-group>
          <article-title>...</article-title>
          <source>...</source>
          <year>...</year>
          <pub-id pub-id-type="doi">...</pub-id>
        </element-citation>
      </ref>
    </ref-list>
  </back>
</article>
```

**JATS Coverage** (from PMC):
- ✅ Title, abstract, keywords
- ✅ Authors with affiliations and ORCID
- ✅ Structured sections (Introduction, Methods, Results, Discussion)
- ✅ Paragraphs with citation callouts `<xref ref-type="bibr">`
- ✅ Figures with captions and file links
- ✅ Tables with full HTML structure
- ✅ References with DOI, PMID, authors, year, venue
- ✅ Funding information
- ✅ Data availability statements

### Revised Data Model: FullTextContent

**New comprehensive model** (replaces simple string content):

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

@dataclass
class Author:
    """Author information"""
    given_names: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None
    affiliations: List[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        if self.given_names and self.surname:
            return f"{self.given_names} {self.surname}"
        return self.surname or self.given_names or "Unknown"

@dataclass
class Figure:
    """Figure with caption and reference"""
    id: str
    label: Optional[str] = None  # "Figure 1"
    caption: Optional[str] = None
    image_path: Optional[str] = None  # Local path or URL
    graphic_ref: Optional[str] = None  # Original xlink:href

@dataclass
class Table:
    """Table with caption and content"""
    id: str
    label: Optional[str] = None  # "Table 1"
    caption: Optional[str] = None
    html_content: Optional[str] = None  # Full HTML table
    csv_data: Optional[str] = None  # Extracted CSV (Phase 2)

@dataclass
class Reference:
    """Bibliographic reference"""
    id: str
    authors: List[str] = field(default_factory=list)
    title: Optional[str] = None
    source: Optional[str] = None  # Journal name
    year: Optional[int] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None

@dataclass
class Section:
    """Document section (hierarchical)"""
    id: Optional[str] = None
    title: Optional[str] = None
    level: int = 1  # 1=top-level, 2=subsection, etc.
    paragraphs: List[str] = field(default_factory=list)
    subsections: List['Section'] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)

    def get_all_text(self) -> str:
        """Recursively get all text from section and subsections"""
        text = "\n\n".join(self.paragraphs)
        for subsec in self.subsections:
            text += "\n\n" + subsec.get_all_text()
        return text

@dataclass
class FullTextContent:
    """Complete structured document content"""

    # Metadata
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    authors: List[Author] = field(default_factory=list)

    # Content structure
    sections: List[Section] = field(default_factory=list)

    # Figures and tables (flattened for easy access)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)

    # References
    references: List[Reference] = field(default_factory=list)

    # Additional metadata
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc_id: Optional[str] = None

    # Data availability (Phase 2)
    data_availability: Optional[str] = None
    funding: List[str] = field(default_factory=list)

    # Quality indicators
    has_structured_abstract: bool = False
    has_methods_section: bool = False
    citation_count: int = 0  # Number of citations in text

    def get_section_by_title(self, title_pattern: str) -> Optional[Section]:
        """Find section by title (case-insensitive regex)"""
        import re
        pattern = re.compile(title_pattern, re.IGNORECASE)
        for section in self.sections:
            if section.title and pattern.search(section.title):
                return section
        return None

    def get_methods_text(self) -> Optional[str]:
        """Extract Methods/Materials section text"""
        methods = self.get_section_by_title(r"methods?|materials?")
        return methods.get_all_text() if methods else None

    def get_full_text(self) -> str:
        """Get complete full-text (all sections)"""
        parts = []
        if self.title:
            parts.append(f"# {self.title}\n")
        if self.abstract:
            parts.append(f"## Abstract\n{self.abstract}\n")
        for section in self.sections:
            if section.title:
                parts.append(f"## {section.title}\n")
            parts.append(section.get_all_text())
        return "\n\n".join(parts)
```

### Updated ContentExtractor with Structured Parsing

**Phase 1A: Basic JATS XML parsing** (implement now):

```python
class ContentExtractor:
    """Extract structured content from JATS XML"""

    def extract_structured_content(
        self,
        xml_content: str
    ) -> FullTextContent:
        """
        Extract fully structured content from JATS XML.

        Returns comprehensive FullTextContent object, not just plain text.
        """
        soup = BeautifulSoup(xml_content, 'lxml-xml')
        article = soup.find('article')

        if not article:
            raise ValueError("No <article> tag found in XML")

        content = FullTextContent()

        # Extract front matter
        front = article.find('front')
        if front:
            content = self._extract_front_matter(front, content)

        # Extract body (sections)
        body = article.find('body')
        if body:
            content.sections = self._extract_sections(body)

        # Extract back matter (references)
        back = article.find('back')
        if back:
            content.references = self._extract_references(back)

        # Extract figures and tables (flatten from sections)
        content.figures = self._flatten_figures(content.sections)
        content.tables = self._flatten_tables(content.sections)

        # Quality indicators
        content.has_methods_section = content.get_methods_text() is not None
        content.citation_count = self._count_citations(soup)

        return content

    def _extract_front_matter(
        self,
        front: Tag,
        content: FullTextContent
    ) -> FullTextContent:
        """Extract title, abstract, authors, keywords"""

        article_meta = front.find('article-meta')
        if not article_meta:
            return content

        # Title
        title_tag = article_meta.find('article-title')
        if title_tag:
            content.title = title_tag.get_text(strip=True)

        # Abstract
        abstract_tag = article_meta.find('abstract')
        if abstract_tag:
            # Check if structured abstract
            if abstract_tag.find('sec'):
                content.has_structured_abstract = True
                # Extract structured parts
                parts = []
                for sec in abstract_tag.find_all('sec'):
                    title = sec.find('title')
                    if title:
                        parts.append(f"{title.get_text()}: ")
                    parts.append(sec.get_text(strip=True))
                content.abstract = " ".join(parts)
            else:
                content.abstract = abstract_tag.get_text(separator=' ', strip=True)

        # Keywords
        kwd_group = article_meta.find('kwd-group')
        if kwd_group:
            content.keywords = [
                kwd.get_text(strip=True)
                for kwd in kwd_group.find_all('kwd')
            ]

        # Authors
        contrib_group = article_meta.find('contrib-group')
        if contrib_group:
            for contrib in contrib_group.find_all('contrib', {'contrib-type': 'author'}):
                author = self._extract_author(contrib)
                if author:
                    content.authors.append(author)

        # Publication metadata
        journal_meta = front.find('journal-meta')
        if journal_meta:
            journal_title = journal_meta.find('journal-title')
            if journal_title:
                content.journal = journal_title.get_text(strip=True)

        # Year
        pub_date = article_meta.find('pub-date')
        if pub_date:
            year_tag = pub_date.find('year')
            if year_tag:
                try:
                    content.year = int(year_tag.get_text(strip=True))
                except ValueError:
                    pass

        # DOI, PMID
        for article_id in article_meta.find_all('article-id'):
            id_type = article_id.get('pub-id-type')
            value = article_id.get_text(strip=True)
            if id_type == 'doi':
                content.doi = value
            elif id_type == 'pmid':
                content.pmid = value
            elif id_type == 'pmc':
                content.pmc_id = f"PMC{value}"

        return content

    def _extract_author(self, contrib: Tag) -> Optional[Author]:
        """Extract author information"""
        name_tag = contrib.find('name')
        if not name_tag:
            return None

        author = Author()

        surname = name_tag.find('surname')
        if surname:
            author.surname = surname.get_text(strip=True)

        given_names = name_tag.find('given-names')
        if given_names:
            author.given_names = given_names.get_text(strip=True)

        # Email
        email_tag = contrib.find('email')
        if email_tag:
            author.email = email_tag.get_text(strip=True)

        # ORCID
        orcid_tag = contrib.find('contrib-id', {'contrib-id-type': 'orcid'})
        if orcid_tag:
            author.orcid = orcid_tag.get_text(strip=True)

        # Affiliations (via xref)
        aff_refs = contrib.find_all('xref', {'ref-type': 'aff'})
        for ref in aff_refs:
            rid = ref.get('rid')
            if rid:
                # Find affiliation by id
                aff = contrib.find_parent().find('aff', {'id': rid})
                if aff:
                    author.affiliations.append(aff.get_text(strip=True))

        return author

    def _extract_sections(
        self,
        body: Tag,
        level: int = 1
    ) -> List[Section]:
        """Recursively extract sections and subsections"""
        sections = []

        for sec_tag in body.find_all('sec', recursive=False):
            section = Section(level=level)

            # Section ID
            section.id = sec_tag.get('id')

            # Section title
            title_tag = sec_tag.find('title', recursive=False)
            if title_tag:
                section.title = title_tag.get_text(strip=True)

            # Paragraphs (direct children only)
            for p in sec_tag.find_all('p', recursive=False):
                section.paragraphs.append(p.get_text(separator=' ', strip=True))

            # Figures
            for fig in sec_tag.find_all('fig', recursive=False):
                section.figures.append(self._extract_figure(fig))

            # Tables
            for table_wrap in sec_tag.find_all('table-wrap', recursive=False):
                section.tables.append(self._extract_table(table_wrap))

            # Subsections (recursive)
            subsec_tags = sec_tag.find_all('sec', recursive=False)
            if subsec_tags:
                section.subsections = self._extract_sections(sec_tag, level + 1)

            sections.append(section)

        return sections

    def _extract_figure(self, fig_tag: Tag) -> Figure:
        """Extract figure metadata"""
        figure = Figure(id=fig_tag.get('id', ''))

        label = fig_tag.find('label')
        if label:
            figure.label = label.get_text(strip=True)

        caption = fig_tag.find('caption')
        if caption:
            figure.caption = caption.get_text(separator=' ', strip=True)

        graphic = fig_tag.find('graphic')
        if graphic:
            figure.graphic_ref = graphic.get('xlink:href')

        return figure

    def _extract_table(self, table_wrap: Tag) -> Table:
        """Extract table metadata and content"""
        table_obj = Table(id=table_wrap.get('id', ''))

        label = table_wrap.find('label')
        if label:
            table_obj.label = label.get_text(strip=True)

        caption = table_wrap.find('caption')
        if caption:
            table_obj.caption = caption.get_text(separator=' ', strip=True)

        table = table_wrap.find('table')
        if table:
            table_obj.html_content = str(table)

        return table_obj

    def _extract_references(self, back: Tag) -> List[Reference]:
        """Extract bibliographic references"""
        references = []

        ref_list = back.find('ref-list')
        if not ref_list:
            return references

        for ref_tag in ref_list.find_all('ref'):
            ref = Reference(id=ref_tag.get('id', ''))

            # Find element-citation or mixed-citation
            citation = ref_tag.find('element-citation') or ref_tag.find('mixed-citation')
            if not citation:
                continue

            # Authors
            person_group = citation.find('person-group', {'person-group-type': 'author'})
            if person_group:
                for name in person_group.find_all('name'):
                    surname = name.find('surname')
                    given = name.find('given-names')
                    if surname:
                        author_name = surname.get_text(strip=True)
                        if given:
                            author_name = f"{given.get_text(strip=True)} {author_name}"
                        ref.authors.append(author_name)

            # Title
            article_title = citation.find('article-title')
            if article_title:
                ref.title = article_title.get_text(strip=True)

            # Source (journal)
            source = citation.find('source')
            if source:
                ref.source = source.get_text(strip=True)

            # Year
            year_tag = citation.find('year')
            if year_tag:
                try:
                    ref.year = int(year_tag.get_text(strip=True))
                except ValueError:
                    pass

            # Volume, pages
            volume = citation.find('volume')
            if volume:
                ref.volume = volume.get_text(strip=True)

            fpage = citation.find('fpage')
            lpage = citation.find('lpage')
            if fpage and lpage:
                ref.pages = f"{fpage.get_text()}-{lpage.get_text()}"
            elif fpage:
                ref.pages = fpage.get_text(strip=True)

            # DOI, PMID
            for pub_id in citation.find_all('pub-id'):
                id_type = pub_id.get('pub-id-type')
                value = pub_id.get_text(strip=True)
                if id_type == 'doi':
                    ref.doi = value
                elif id_type == 'pmid':
                    ref.pmid = value

            references.append(ref)

        return references

    def _flatten_figures(self, sections: List[Section]) -> List[Figure]:
        """Collect all figures from all sections"""
        figures = []
        for section in sections:
            figures.extend(section.figures)
            figures.extend(self._flatten_figures(section.subsections))
        return figures

    def _flatten_tables(self, sections: List[Section]) -> List[Table]:
        """Collect all tables from all sections"""
        tables = []
        for section in sections:
            tables.extend(section.tables)
            tables.extend(self._flatten_tables(section.subsections))
        return tables

    def _count_citations(self, soup: Tag) -> int:
        """Count citation callouts in text"""
        return len(soup.find_all('xref', {'ref-type': 'bibr'}))
```

### Updated FullTextResult Model

**Store structured content** instead of plain text:

```python
@dataclass
class FullTextResult:
    """Result of full-text retrieval attempt"""

    # Status
    success: bool = False
    error_message: Optional[str] = None

    # Content (NEW: structured!)
    structured_content: Optional[FullTextContent] = None  # NEW: Full structure
    plain_text: Optional[str] = None  # Fallback for non-structured sources
    pdf_path: Optional[Path] = None

    # Provenance
    source_url: Optional[str] = None
    source_type: Optional[SourceType] = None
    content_type: Optional[ContentType] = None

    # Quality metrics
    quality_score: float = 0.0
    word_count: int = 0
    has_sections: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    fetch_timestamp: Optional[str] = None
    is_cached: bool = False
    validation_errors: list = field(default_factory=list)

    def get_text(self) -> Optional[str]:
        """Get text content (structured or plain)"""
        if self.structured_content:
            return self.structured_content.get_full_text()
        return self.plain_text
```

### Implementation Strategy

**Phase 1A** (Current - Basic extraction):
- ✅ Extract plain text from XML (as planned)
- ✅ Extract basic metadata (title, abstract, keywords)
- ✅ Quality scoring

**Phase 1B** (Add structured parsing):
- ✅ Implement FullTextContent model
- ✅ Implement structured JATS XML parsing
- ✅ Extract sections, figures, tables
- ✅ Extract references with full metadata
- ✅ Extract authors with affiliations

**Phase 2** (Advanced features):
- ⏳ Citation context extraction (link citations to references)
- ⏳ Table parsing to CSV
- ⏳ Figure download and analysis
- ⏳ Data availability statement extraction
- ⏳ Funding information extraction

**Phase 3** (Publisher HTML parsing):
- ⏳ Publisher-specific HTML scrapers (Nature, Elsevier, Wiley)
- ⏳ HTML-to-JATS conversion
- ⏳ PDF parsing with GROBID integration (optional)

###Usage Examples

```python
# Get structured content from PMC
result = await manager.get_fulltext(publication)

if result.success and result.structured_content:
    content = result.structured_content

    # Access metadata
    print(f"Title: {content.title}")
    print(f"Authors: {', '.join(a.full_name for a in content.authors)}")
    print(f"Keywords: {', '.join(content.keywords)}")

    # Get specific section
    methods = content.get_methods_text()
    print(f"Methods: {methods[:500]}...")

    # Access figures
    for fig in content.figures:
        print(f"{fig.label}: {fig.caption}")

    # Access tables
    for table in content.tables:
        print(f"{table.label}: {table.caption}")
        # Can parse table.html_content with pandas

    # Access references
    print(f"References ({len(content.references)}):")
    for ref in content.references[:5]:
        print(f"  {ref.authors[0]} et al. ({ref.year}). {ref.title}. {ref.source}")

    # Get full text (for downstream analysis)
    full_text = content.get_full_text()
```

### Benefits of Structured Extraction

1. **Downstream Analysis**: Can analyze specific sections (Methods, Results)
2. **Citation Analysis**: Link citations in text to full references
3. **Table Extraction**: Extract data from tables for reanalysis
4. **Figure Analysis**: Download and analyze figures
5. **Metadata Enrichment**: Authors, affiliations, keywords for search
6. **Quality Assessment**: Check if paper has Methods, structured abstract
7. **Reproducibility**: Extract data availability statements
8. **Funding Analysis**: Track funding sources

---

### Component Names (Generic, Future-Proof)

| Component | Name | Why Generic? |
|-----------|------|--------------|
| XML Fetcher | `ContentFetcher` | Supports PMC, Europe PMC, PubMed, JATS archives |
| HTML Parser | `ContentExtractor` | Supports PMC XML, publisher HTML, preprint servers |
| XML Content | `ContentType.XML` | Not "PMC_XML" - supports multiple XML sources |
| HTML Content | `ContentType.HTML` | Supports any HTML source |
| Storage Path | `data/fulltext/xml/` | Not "pmc/" - accommodates all XML sources |

### File Naming (Progressive Addition)

**Phase 1A:** PMC implementation
- `lib/fulltext/content_fetcher.py` - Start with PMC, add others later
- `lib/fulltext/content_extractor.py` - Start with JATS XML, add HTML later

**Phase 2:** Additional sources
- Same files, add methods: `fetch_europepmc_xml()`, `extract_from_publisher_html()`

**Phase 3:** Advanced features
- Same files, add methods: `extract_sections()`, `extract_formulas()`

### Method Naming Pattern

```python
# Generic pattern: action_from_source_format()
async def fetch_xml(source: str, identifier: str) -> Optional[str]
async def fetch_html(url: str) -> Optional[str]

# Specific implementations (private methods)
async def _fetch_pmc_xml(pmc_id: str) -> Optional[str]
async def _fetch_europepmc_xml(pmcid: str) -> Optional[str]
```

---

## Data Models

### Enhanced FullTextResult

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path

class ContentType(Enum):
    """Content format types"""
    XML = "xml"           # JATS XML (PMC, Europe PMC, etc.)
    HTML = "html"         # Publisher HTML pages
    PDF = "pdf"           # PDF files (stored, not extracted)
    TEXT = "text"         # Plain text (future)
    UNKNOWN = "unknown"

class SourceType(Enum):
    """Content source providers"""
    PMC = "pmc"                      # PubMed Central
    EUROPE_PMC = "europepmc"         # Europe PMC
    UNPAYWALL = "unpaywall"          # Unpaywall OA
    INSTITUTIONAL = "institutional"   # University access
    CROSSREF = "crossref"            # Crossref TDM
    ARXIV = "arxiv"                  # arXiv preprints
    BIORXIV = "biorxiv"              # bioRxiv preprints
    PUBLISHER = "publisher"          # Direct from publisher
    SCIHUB = "scihub"                # Sci-Hub
    LIBGEN = "libgen"                # Library Genesis
    CACHE = "cache"                  # Local cache

@dataclass
class FullTextResult:
    """Result of full-text retrieval attempt"""

    # Status
    success: bool = False
    error_message: Optional[str] = None

    # Content (at least one should be populated)
    content: Optional[str] = None              # Actual text content (XML/HTML/text)
    pdf_path: Optional[Path] = None            # Path to downloaded PDF

    # Provenance (ALWAYS populate for debugging)
    source_url: Optional[str] = None           # Original URL (HTML page or PDF link)
    source_type: Optional[SourceType] = None   # Which service provided it
    content_type: Optional[ContentType] = None # Format of content

    # Quality metrics
    quality_score: float = 0.0                 # 0.0-1.0 (0.98 for XML, 0.70 for PDF)
    word_count: int = 0                        # Approximate content length
    has_sections: bool = False                 # Structured content detected

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)  # Source-specific metadata
    fetch_timestamp: Optional[str] = None      # ISO 8601 timestamp

    # Validation
    is_cached: bool = False                    # Retrieved from cache
    validation_errors: list = field(default_factory=list)  # Any issues detected
```

### Storage Organization

```
data/fulltext/
├── xml/                    # XML content (JATS, PMC, etc.)
│   ├── pmc/               # PMC XML files
│   │   └── PMC1234567.xml
│   ├── europepmc/         # Europe PMC XML files
│   └── arxiv/             # arXiv XML files
├── html/                  # HTML content (publisher pages)
│   ├── nature/
│   ├── elsevier/
│   └── wiley/
├── pdf/                   # PDF downloads (organized by source)
│   ├── unpaywall/
│   ├── institutional/
│   └── scihub/
└── cache.db              # SQLite cache index
```

---

## Component Specifications

### Component 1: ContentFetcher

**File:** `lib/fulltext/content_fetcher.py`
**Purpose:** Fetch content from various sources (XML, HTML, PDF)
**Dependencies:** aiohttp, aiofiles, asyncio

```python
"""
Content fetcher for retrieving full-text from various sources.
Supports XML (PMC, JATS), HTML (publishers), and PDF downloads.
"""

import asyncio
import aiohttp
import ssl
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of a content fetch operation"""
    success: bool
    content: Optional[str] = None
    content_type: str = "unknown"  # "xml", "html", "pdf_path"
    source_url: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ContentFetcher:
    """
    Fetches full-text content from multiple sources.

    Design Principles:
    - Generic methods (fetch_xml, fetch_html) for reusability
    - Source-specific private methods (_fetch_pmc_xml, etc.)
    - Async/await for performance
    - Comprehensive error handling
    """

    # NCBI E-utilities endpoints
    PMC_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    PMC_EFETCH = PMC_BASE_URL + "efetch.fcgi"

    # Rate limiting
    PMC_REQUESTS_PER_SECOND = 3  # NCBI allows 3/sec without API key

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize content fetcher.

        Args:
            config: Configuration dict with:
                - ncbi_api_key: Optional NCBI API key (10 req/sec if provided)
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Max retry attempts (default: 3)
                - output_dir: Base directory for downloads (default: data/fulltext)
        """
        self.config = config
        self.ncbi_api_key = config.get("ncbi_api_key")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.output_dir = Path(config.get("output_dir", "data/fulltext"))

        # Rate limiting (increase if API key provided)
        self.rate_limit = (
            10 if self.ncbi_api_key
            else self.PMC_REQUESTS_PER_SECOND
        )
        self._last_request_time = 0

        # SSL context (reuse pattern from PDFDownloadManager)
        self.ssl_context = ssl.create_default_context()
        # Allow self-signed certificates for institutional access
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Session (created on first use)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            )
        return self._session

    async def _rate_limit(self):
        """Enforce rate limiting"""
        import time
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        self._last_request_time = time.time()

    async def fetch_xml(
        self,
        source: str,
        identifier: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch XML content from specified source.

        Args:
            source: Source type ("pmc", "europepmc", "arxiv", etc.)
            identifier: Source-specific ID (PMC ID, DOI, etc.)
            **kwargs: Source-specific parameters

        Returns:
            FetchResult with XML content or error
        """
        # Route to source-specific method
        if source == "pmc":
            return await self._fetch_pmc_xml(identifier, **kwargs)
        elif source == "europepmc":
            return await self._fetch_europepmc_xml(identifier, **kwargs)
        elif source == "arxiv":
            return await self._fetch_arxiv_xml(identifier, **kwargs)
        else:
            return FetchResult(
                success=False,
                error=f"Unsupported XML source: {source}"
            )

    async def _fetch_pmc_xml(
        self,
        pmc_id: str,
        retries: int = 0
    ) -> FetchResult:
        """
        Fetch XML from PubMed Central.

        Args:
            pmc_id: PMC identifier (e.g., "PMC1234567" or "1234567")
            retries: Current retry attempt

        Returns:
            FetchResult with XML content
        """
        # Clean PMC ID (accept with or without "PMC" prefix)
        clean_id = pmc_id.replace("PMC", "").strip()

        try:
            await self._rate_limit()

            # Build request parameters
            params = {
                "db": "pmc",
                "id": clean_id,
                "retmode": "xml",
            }
            if self.ncbi_api_key:
                params["api_key"] = self.ncbi_api_key

            session = await self._get_session()

            logger.debug(f"Fetching PMC XML for ID: {pmc_id}")

            async with session.get(
                self.PMC_EFETCH,
                params=params
            ) as response:

                if response.status == 200:
                    xml_content = await response.text()

                    # Validate XML (basic check)
                    if not xml_content or len(xml_content) < 100:
                        return FetchResult(
                            success=False,
                            error="Empty or invalid XML response"
                        )

                    if "error" in xml_content.lower()[:200]:
                        return FetchResult(
                            success=False,
                            error="PMC returned error response"
                        )

                    # Success!
                    return FetchResult(
                        success=True,
                        content=xml_content,
                        content_type="xml",
                        source_url=str(response.url),
                        metadata={
                            "pmc_id": pmc_id,
                            "format": "jats_xml",
                            "size_bytes": len(xml_content)
                        }
                    )

                elif response.status == 429:  # Rate limited
                    if retries < self.max_retries:
                        await asyncio.sleep(2 ** retries)  # Exponential backoff
                        return await self._fetch_pmc_xml(pmc_id, retries + 1)
                    return FetchResult(
                        success=False,
                        error="Rate limited by NCBI"
                    )

                else:
                    return FetchResult(
                        success=False,
                        error=f"HTTP {response.status}: {response.reason}"
                    )

        except asyncio.TimeoutError:
            if retries < self.max_retries:
                return await self._fetch_pmc_xml(pmc_id, retries + 1)
            return FetchResult(success=False, error="Request timeout")

        except Exception as e:
            logger.error(f"Error fetching PMC XML: {e}")
            return FetchResult(success=False, error=str(e))

    async def _fetch_europepmc_xml(
        self,
        identifier: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch XML from Europe PMC (future implementation).

        Args:
            identifier: Europe PMC ID or DOI

        Returns:
            FetchResult (currently not implemented)
        """
        return FetchResult(
            success=False,
            error="Europe PMC fetching not yet implemented"
        )

    async def _fetch_arxiv_xml(
        self,
        identifier: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch XML from arXiv (future implementation).

        Args:
            identifier: arXiv ID

        Returns:
            FetchResult (currently not implemented)
        """
        return FetchResult(
            success=False,
            error="arXiv fetching not yet implemented"
        )

    async def fetch_html(
        self,
        url: str,
        **kwargs
    ) -> FetchResult:
        """
        Fetch HTML content from URL (future Phase 2).

        Args:
            url: Full URL to HTML page
            **kwargs: Optional parameters (headers, cookies, etc.)

        Returns:
            FetchResult with HTML content
        """
        # Future implementation for publisher HTML pages
        return FetchResult(
            success=False,
            error="HTML fetching not yet implemented (Phase 2)"
        )

    async def download_pdf(
        self,
        url: str,
        output_path: Path,
        **kwargs
    ) -> FetchResult:
        """
        Download PDF file (delegates to PDFDownloadManager).

        Args:
            url: PDF download URL
            output_path: Where to save PDF
            **kwargs: Optional download parameters

        Returns:
            FetchResult with pdf_path
        """
        # This will integrate with existing PDFDownloadManager
        # For now, placeholder
        return FetchResult(
            success=False,
            error="PDF download integration pending"
        )

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
```

**Key Design Decisions:**

1. **Generic `fetch_xml()` method** - Routes to source-specific implementations
2. **Stores source_url** - Always track where content came from
3. **Rate limiting** - Respects NCBI limits (3/sec or 10/sec with API key)
4. **Error handling** - Retry logic with exponential backoff
5. **Future-proof** - Placeholder methods for Europe PMC, arXiv, HTML

### Component 2: ContentExtractor

**File:** `lib/fulltext/content_extractor.py`
**Purpose:** Extract clean text from XML/HTML content
**Dependencies:** BeautifulSoup4, lxml

```python
"""
Content extractor for parsing XML/HTML to clean text.
Supports JATS XML (PMC), publisher HTML, and structured extraction.
"""

from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts clean text from various content formats.

    Design Principles:
    - Format-agnostic interface (extract_text)
    - Format-specific implementations (XML, HTML)
    - Optional structured extraction (sections, metadata)
    - Quality scoring
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize content extractor.

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.min_word_count = self.config.get("min_word_count", 100)

    def extract_text(
        self,
        content: str,
        content_type: str
    ) -> Optional[str]:
        """
        Extract clean text from content.

        Args:
            content: Raw content (XML or HTML)
            content_type: Format type ("xml", "html")

        Returns:
            Clean text or None if extraction fails
        """
        if content_type == "xml":
            return self.extract_from_xml(content)
        elif content_type == "html":
            return self.extract_from_html(content)
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            return None

    def extract_from_xml(
        self,
        xml_content: str,
        extract_sections: bool = False
    ) -> Optional[str]:
        """
        Extract text from JATS XML (PMC format).

        Args:
            xml_content: XML string
            extract_sections: If True, return structured dict (future)

        Returns:
            Clean text or None
        """
        try:
            # Parse XML with lxml parser (faster, better for XML)
            soup = BeautifulSoup(xml_content, 'lxml-xml')

            # Find article body
            body = soup.find('body')
            if not body:
                # Try alternative tags
                body = soup.find('article')

            if not body:
                logger.warning("No body/article tag found in XML")
                return None

            # Extract text with formatting
            text = body.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)

            # Validate minimum length
            word_count = len(text.split())
            if word_count < self.min_word_count:
                logger.warning(f"Text too short: {word_count} words")
                return None

            return text

        except Exception as e:
            logger.error(f"Error extracting from XML: {e}")
            return None

    def extract_from_html(
        self,
        html_content: str
    ) -> Optional[str]:
        """
        Extract text from HTML (publisher pages).
        Phase 2 implementation - currently placeholder.

        Args:
            html_content: HTML string

        Returns:
            Clean text or None
        """
        # Future: Publisher-specific extraction
        # For now, basic implementation
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script, style, nav, footer
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)

            return text if len(text.split()) >= self.min_word_count else None

        except Exception as e:
            logger.error(f"Error extracting from HTML: {e}")
            return None

    def extract_metadata(
        self,
        xml_content: str
    ) -> Dict[str, Any]:
        """
        Extract structured metadata from JATS XML.

        Args:
            xml_content: JATS XML string

        Returns:
            Dict with title, abstract, keywords, etc.
        """
        try:
            soup = BeautifulSoup(xml_content, 'lxml-xml')
            metadata = {}

            # Title
            title_tag = soup.find('article-title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)

            # Abstract
            abstract_tag = soup.find('abstract')
            if abstract_tag:
                metadata['abstract'] = abstract_tag.get_text(strip=True)

            # Keywords
            kwd_group = soup.find('kwd-group')
            if kwd_group:
                keywords = [kwd.get_text(strip=True) for kwd in kwd_group.find_all('kwd')]
                metadata['keywords'] = keywords

            # Authors (basic - can be enhanced)
            authors = []
            for contrib in soup.find_all('contrib', {'contrib-type': 'author'}):
                name_tag = contrib.find('name')
                if name_tag:
                    surname = name_tag.find('surname')
                    given = name_tag.find('given-names')
                    if surname:
                        author = surname.get_text(strip=True)
                        if given:
                            author = f"{given.get_text(strip=True)} {author}"
                        authors.append(author)
            metadata['authors'] = authors

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

    def calculate_quality_score(
        self,
        text: str,
        content_type: str,
        has_sections: bool = False
    ) -> float:
        """
        Calculate quality score for extracted text.

        Args:
            text: Extracted text
            content_type: Format type
            has_sections: Whether structured sections detected

        Returns:
            Quality score (0.0-1.0)
        """
        base_score = {
            "xml": 0.98,   # JATS XML is highly structured
            "html": 0.85,  # HTML quality varies by publisher
            "pdf": 0.70,   # PDF extraction has issues
        }.get(content_type, 0.50)

        # Adjust based on content characteristics
        word_count = len(text.split())
        if word_count < 500:
            base_score *= 0.8  # Very short
        elif word_count > 3000:
            base_score *= 1.0  # Good length

        if has_sections:
            base_score = min(1.0, base_score * 1.05)

        return round(base_score, 2)
```

**Key Design Decisions:**

1. **Format-agnostic interface** - `extract_text(content, content_type)`
2. **JATS XML focus** - Optimized for PMC XML structure
3. **Quality scoring** - Automatic quality assessment
4. **Metadata extraction** - Bonus feature for structured data
5. **Extensible** - Easy to add publisher-specific HTML parsers

### Component 3: Updated FullTextManager

**File:** `lib/fulltext/manager.py` (MODIFY EXISTING)
**Purpose:** Orchestrate content retrieval with new components
**Changes:** Integration with ContentFetcher and ContentExtractor

```python
# Add to imports at top of file
from .content_fetcher import ContentFetcher, FetchResult
from .content_extractor import ContentExtractor
from .models import FullTextResult, ContentType, SourceType

class FullTextManager:
    """
    UPDATED: Now fetches actual content, not just URLs
    """

    def __init__(self, config):
        self.config = config

        # NEW: Initialize content components
        self.content_fetcher = ContentFetcher(config.get("fetcher", {}))
        self.content_extractor = ContentExtractor(config.get("extractor", {}))

        # Existing components (keep)
        self.pdf_download_manager = PDFDownloadManager(config)
        # ... other existing initializations

    async def get_fulltext(self, publication) -> FullTextResult:
        """
        UPDATED: Returns actual content, not just URLs.

        HYBRID TIERED WATERFALL STRATEGY:

        Tier 1: Premium sources (try both XML/HTML and PDF per source)
          - PMC: XML → PDF
          - Institutional: HTML → PDF

        Tier 2: OA HTML sources (HTML-only, quality-first)
          - Unpaywall HTML (if available)
          - CORE HTML
          - Publisher HTML (Phase 2)

        Tier 3: OA PDF sources (PDF-only, pragmatic)
          - Unpaywall PDF
          - OpenAlex PDF
          - Crossref PDF
          - bioRxiv/arXiv PDF

        Tier 4: Gray-area sources (PDF-only, last resort)
          - Sci-Hub PDF
          - LibGen PDF

        Returns:
            FullTextResult with content AND/OR pdf_path populated
        """
        # Try cache first (existing code - keep)
        if self.config.get("enable_cache"):
            cached = await self._check_cache(publication)
            if cached.success:
                return cached

        # ============================================================
        # TIER 1: PREMIUM SOURCES (try both formats per source)
        # ============================================================

        # PMC: Try XML first (0.98 quality), then PDF (0.90 quality from PMC)
        if publication.pmc_id and self.config.get("enable_pmc", True):
            # Try PMC XML (preferred)
            result = await self._try_pmc_xml(publication)
            if result.success:
                await self._cache_result(publication, result)
                return result

            # Try PMC PDF (fallback)
            result = await self._try_pmc_pdf(publication)
            if result.success:
                await self._cache_result(publication, result)
                return result

        # Institutional: Try HTML first, then PDF
        if self.config.get("enable_institutional", True):
            # Try institutional HTML (if provider supports it)
            result = await self._try_institutional_html(publication)
            if result.success:
                await self._cache_result(publication, result)
                return result

            # Try institutional PDF
            result = await self._try_institutional_pdf(publication)
            if result.success:
                await self._cache_result(publication, result)
                return result

        # ============================================================
        # TIER 2: OA HTML SOURCES (HTML-only, quality-first)
        # ============================================================

        # Try OA sources for HTML full-text
        html_sources = []

        if self.config.get("enable_unpaywall", True):
            html_sources.append(("unpaywall_html", self._try_unpaywall_html))

        if self.config.get("enable_core", True):
            html_sources.append(("core_html", self._try_core_html))

        # Phase 2: Publisher-specific HTML scrapers
        # if self.config.get("enable_publisher_html", False):
        #     html_sources.append(("publisher_html", self._try_publisher_html))

        for source_name, source_func in html_sources:
            try:
                result = await source_func(publication)
                if result.success:
                    await self._cache_result(publication, result)
                    return result
            except Exception as e:
                logger.warning(f"Error with {source_name}: {e}")

        # ============================================================
        # TIER 3: OA PDF SOURCES (PDF-only, pragmatic fallback)
        # ============================================================

        # Try OA sources for PDF downloads
        pdf_sources = [
            ("unpaywall_pdf", self._try_unpaywall_pdf),
            ("openalex_pdf", self._try_openalex_pdf),
            ("crossref_pdf", self._try_crossref_pdf),
            ("biorxiv_pdf", self._try_biorxiv_pdf),
            ("arxiv_pdf", self._try_arxiv_pdf),
        ]

        for source_name, source_func in pdf_sources:
            if not self.config.get(f"enable_{source_name.split('_')[0]}", True):
                continue

            try:
                result = await source_func(publication)
                if result.success:
                    await self._cache_result(publication, result)
                    return result
            except Exception as e:
                logger.warning(f"Error with {source_name}: {e}")

        # ============================================================
        # TIER 4: GRAY-AREA SOURCES (PDF-only, last resort)
        # ============================================================

        # Sci-Hub (enabled by default as final fallback)
        if self.config.get("enable_scihub", True):  # Changed: True by default
            try:
                result = await self._try_scihub_pdf(publication)
                if result.success:
                    await self._cache_result(publication, result)
                    return result
            except Exception as e:
                logger.warning(f"Error with scihub_pdf: {e}")

        # LibGen (enabled by default as final fallback)
        if self.config.get("enable_libgen", True):  # Changed: True by default
            try:
                result = await self._try_libgen_pdf(publication)
                if result.success:
                    await self._cache_result(publication, result)
                    return result
            except Exception as e:
                logger.warning(f"Error with libgen_pdf: {e}")

        # No source succeeded
        return FullTextResult(
            success=False,
            error_message="No full-text source available"
        )

    # ============================================================
    # TIER 1 METHODS: Premium Sources
    # ============================================================

    async def _try_pmc_xml(self, publication) -> FullTextResult:
        """
        NEW METHOD: Fetch and extract PMC XML content.

        Quality: 0.98 (highly structured JATS XML)
        Coverage: 6.7M papers
        """

        Args:
            publication: Publication object with pmc_id

        Returns:
            FullTextResult with XML content
        """
        try:
            # Fetch XML from PMC
            fetch_result = await self.content_fetcher.fetch_xml(
                source="pmc",
                identifier=publication.pmc_id
            )

            if not fetch_result.success:
                return FullTextResult(
                    success=False,
                    error_message=f"PMC fetch failed: {fetch_result.error}",
                    source_type=SourceType.PMC
                )

            # Extract clean text
            text_content = self.content_extractor.extract_from_xml(
                fetch_result.content
            )

            if not text_content:
                return FullTextResult(
                    success=False,
                    error_message="PMC XML extraction failed",
                    source_type=SourceType.PMC,
                    source_url=fetch_result.source_url
                )

            # Also extract metadata (optional, for enhancement)
            metadata = self.content_extractor.extract_metadata(
                fetch_result.content
            )

            # Calculate quality score
            quality_score = self.content_extractor.calculate_quality_score(
                text_content,
                content_type="xml",
                has_sections=bool(metadata.get("sections"))
            )

            # Save raw XML to disk (for future reference)
            xml_path = await self._save_xml_to_disk(
                publication,
                fetch_result.content,
                source="pmc"
            )

            # Return result with content
            return FullTextResult(
                success=True,
                content=text_content,  # Extracted text
                source_url=fetch_result.source_url,  # NCBI URL
                source_type=SourceType.PMC,
                content_type=ContentType.XML,
                quality_score=quality_score,
                word_count=len(text_content.split()),
                has_sections=bool(metadata.get("sections")),
                metadata={
                    **metadata,
                    "xml_path": str(xml_path),  # Raw XML location
                    "pmc_id": publication.pmc_id
                },
                fetch_timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Error in _try_pmc: {e}")
            return FullTextResult(
                success=False,
                error_message=str(e),
                source_type=SourceType.PMC
            )

    async def _try_pmc_pdf(self, publication) -> FullTextResult:
        """
        NEW METHOD: Download PDF from PMC (fallback if XML fails).

        Quality: 0.90 (PMC PDFs are well-formatted)
        Use case: XML parsing failed, user prefers PDF, or archival
        """
        try:
            # PMC PDF URL pattern: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/pdf/
            pmc_id = publication.pmc_id.replace("PMC", "")
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"

            # Download PDF
            output_dir = Path(self.config.get("output_dir", "data/fulltext")) / "pdf" / "pmc"
            output_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = output_dir / f"PMC{pmc_id}.pdf"

            # Use PDFDownloadManager
            success = await self.pdf_download_manager._download_single(
                publication=publication,
                url=pdf_url,
                output_dir=output_dir
            )

            if not success:
                return FullTextResult(
                    success=False,
                    error_message="PMC PDF download failed",
                    source_type=SourceType.PMC,
                    source_url=pdf_url
                )

            return FullTextResult(
                success=True,
                pdf_path=pdf_path,
                source_url=pdf_url,
                source_type=SourceType.PMC,
                content_type=ContentType.PDF,
                quality_score=0.90,  # PMC PDFs are high quality
                metadata={"pmc_id": publication.pmc_id},
                fetch_timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Error in _try_pmc_pdf: {e}")
            return FullTextResult(
                success=False,
                error_message=str(e),
                source_type=SourceType.PMC
            )

    async def _try_institutional_html(self, publication) -> FullTextResult:
        """
        NEW METHOD: Try to fetch HTML from institutional access.

        Quality: 0.85 (publisher HTML, varies by publisher)
        Coverage: Depends on institution (GT/ODU: ~45-50%)
        """
        # Phase 2 implementation
        # For now, return not implemented
        return FullTextResult(
            success=False,
            error_message="Institutional HTML not yet implemented (Phase 2)"
        )

    async def _try_institutional_pdf(self, publication) -> FullTextResult:
        """
        MODIFIED: Download PDF from institutional access.

        Quality: 0.70-0.85 (PDF quality varies)
        Coverage: ~45-50% for GT/ODU
        """
        # Leverage existing institutional access code
        # Modify to download immediately instead of returning URL
        try:
            # Check institutional access (existing code)
            access_info = await self._check_institutional_access(publication)

            if not access_info or not access_info.get("pdf_url"):
                return FullTextResult(
                    success=False,
                    error_message="No institutional access",
                    source_type=SourceType.INSTITUTIONAL
                )

            # Download PDF immediately
            output_dir = Path(self.config.get("output_dir", "data/fulltext")) / "pdf" / "institutional"
            output_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = output_dir / f"{publication.pmid or publication.doi.replace('/', '_')}.pdf"

            success = await self.pdf_download_manager._download_single(
                publication=publication,
                url=access_info["pdf_url"],
                output_dir=output_dir
            )

            if not success:
                return FullTextResult(
                    success=False,
                    error_message="Institutional PDF download failed",
                    source_type=SourceType.INSTITUTIONAL,
                    source_url=access_info["pdf_url"]
                )

            return FullTextResult(
                success=True,
                pdf_path=pdf_path,
                source_url=access_info["pdf_url"],
                source_type=SourceType.INSTITUTIONAL,
                content_type=ContentType.PDF,
                quality_score=0.75,  # Institutional PDFs, good quality
                metadata=access_info.get("metadata", {}),
                fetch_timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Error in _try_institutional_pdf: {e}")
            return FullTextResult(
                success=False,
                error_message=str(e),
                source_type=SourceType.INSTITUTIONAL
            )

    # ============================================================
    # TIER 2 METHODS: OA HTML Sources
    # ============================================================

    async def _try_unpaywall_html(self, publication) -> FullTextResult:
        """
        NEW METHOD: Try to get HTML full-text from Unpaywall.

        Quality: 0.85 (publisher HTML)
        Coverage: ~5-10% (most Unpaywall links are PDFs)
        Note: Phase 2 implementation when we add HTML scraping
        """
        # Future: Some Unpaywall URLs point to HTML landing pages
        # We can scrape these for full-text
        return FullTextResult(
            success=False,
            error_message="Unpaywall HTML scraping not yet implemented (Phase 2)"
        )

    async def _try_core_html(self, publication) -> FullTextResult:
        """
        NEW METHOD: Try to get HTML/text from CORE API.

        Quality: 0.80 (CORE extracts text from PDFs, varies)
        Coverage: ~10-15%
        """
        # Future: CORE API sometimes provides extracted text
        return FullTextResult(
            success=False,
            error_message="CORE HTML/text not yet implemented (Phase 2)"
        )

    # ============================================================
    # TIER 3 METHODS: OA PDF Sources
    # ============================================================

    async def _try_unpaywall_pdf(self, publication) -> FullTextResult:
        """
        MODIFIED: Now downloads PDF immediately (single-phase).

        Old behavior: Return URL
        New behavior: Download PDF and return path

        Args:
            publication: Publication object

        Returns:
            FullTextResult with pdf_path
        """
        try:
            # Get OA info from Unpaywall (existing code - keep)
            oa_info = await self._fetch_unpaywall_info(publication.doi)

            if not oa_info or not oa_info.get("is_oa"):
                return FullTextResult(
                    success=False,
                    error_message="Not open access",
                    source_type=SourceType.UNPAYWALL
                )

            # Get best OA location
            best_oa = oa_info.get("best_oa_location")
            if not best_oa:
                return FullTextResult(
                    success=False,
                    error_message="No OA location found",
                    source_type=SourceType.UNPAYWALL
                )

            pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")
            if not pdf_url:
                return FullTextResult(
                    success=False,
                    error_message="No PDF URL",
                    source_type=SourceType.UNPAYWALL
                )

            # NEW: Download PDF immediately (not later!)
            output_dir = Path(self.config.get("output_dir", "data/fulltext/pdf/unpaywall"))
            output_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = output_dir / f"{publication.pmid or publication.doi.replace('/', '_')}.pdf"

            # Use PDFDownloadManager (existing component)
            download_success = await self.pdf_download_manager._download_single(
                publication=publication,
                url=pdf_url,
                output_dir=output_dir
            )

            if not download_success:
                return FullTextResult(
                    success=False,
                    error_message="PDF download failed",
                    source_type=SourceType.UNPAYWALL,
                    source_url=pdf_url
                )

            # Return result with PDF path (NOT content - extraction deferred)
            return FullTextResult(
                success=True,
                pdf_path=pdf_path,  # PDF location
                source_url=pdf_url,  # Original URL
                source_type=SourceType.UNPAYWALL,
                content_type=ContentType.PDF,
                quality_score=0.70,  # PDF quality (not extracted yet)
                metadata={
                    "license": best_oa.get("license"),
                    "version": best_oa.get("version"),
                    "host_type": best_oa.get("host_type")
                },
                fetch_timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Error in _try_unpaywall_content: {e}")
            return FullTextResult(
                success=False,
                error_message=str(e),
                source_type=SourceType.UNPAYWALL
            )

    async def _save_xml_to_disk(
        self,
        publication,
        xml_content: str,
        source: str
    ) -> Path:
        """
        Save raw XML to disk for future reference.

        Args:
            publication: Publication object
            xml_content: Raw XML string
            source: Source name ("pmc", "europepmc", etc.)

        Returns:
            Path to saved XML file
        """
        output_dir = Path(self.config.get("output_dir", "data/fulltext")) / "xml" / source
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filename based on identifier
        if source == "pmc":
            filename = f"{publication.pmc_id}.xml"
        else:
            filename = f"{publication.pmid or publication.doi.replace('/', '_')}.xml"

        xml_path = output_dir / filename

        # Write asynchronously
        async with aiofiles.open(xml_path, 'w', encoding='utf-8') as f:
            await f.write(xml_content)

        logger.info(f"Saved {source} XML to {xml_path}")
        return xml_path
```

**Key Changes to FullTextManager:**

1. **New components initialized:** ContentFetcher, ContentExtractor
2. **`_try_pmc()` implemented:** Fetches XML, extracts text, saves raw XML
3. **`_try_unpaywall_content()` modified:** Downloads PDF immediately (single-phase)
4. **Returns actual content:** `FullTextResult.content` populated (not just URL)
5. **Dual storage:** Text content + source URL + optional PDF path

---

## Implementation Phases

### Phase 1A: PMC Content Retrieval (Days 1-2)

**Goal:** Fetch and extract PMC XML content with 95% success rate

**UPDATED BASED ON STRUCTURED EXTRACTION:**

**Tasks:**

1. **Create `lib/fulltext/models.py` - Data models** (2 hours)
   - Add `ContentType` and `SourceType` enums
   - Create `Author`, `Figure`, `Table`, `Reference`, `Section` dataclasses
   - Create `FullTextContent` dataclass (complete structured model)
   - Update `FullTextResult` dataclass (add `structured_content` field)

2. **Create `lib/fulltext/content_fetcher.py`** (2 hours)
   - Copy complete code from Component 1 specification above
   - Test NCBI API connectivity
   - Validate rate limiting (3 requests/sec)

3. **Create `lib/fulltext/content_extractor.py` - Basic version** (3 hours)
   - Implement `extract_text()` - simple text extraction (Phase 1A)
   - Implement `extract_from_xml()` - basic JATS XML parsing
   - Implement `extract_metadata()` - title, abstract, keywords only
   - Implement `calculate_quality_score()`
   - **Defer**: Full structured parsing to Phase 1B

4. **Update `lib/fulltext/manager.py`** (3 hours)
   - Add imports for new components
   - Initialize ContentFetcher and ContentExtractor in `__init__`
   - Implement `_try_pmc_xml()` method (fetch + basic extraction)
   - Implement `_save_xml_to_disk()` helper
   - Update `get_fulltext()` waterfall to call PMC first

5. **Create test suite** (2 hours)
   - `tests/fulltext/test_content_fetcher.py`
   - `tests/fulltext/test_content_extractor_basic.py`
   - `tests/fulltext/test_pmc_integration.py`

**Testing:**
- Unit tests: 10 PMC articles with known IDs
- Integration test: End-to-end PMC retrieval
- Performance test: 100 PMC articles (measure time)

**Success Criteria:**
- ✅ 95% success rate on 100 PMC articles
- ✅ <2s average fetch time
- ✅ Quality score 0.95+ for all successful fetches
- ✅ Basic metadata extracted (title, abstract, keywords)
- ✅ All tests passing

### Phase 1B: Structured Content Extraction (Days 3-4)

**Goal:** Extract fully structured content from PMC XML (not just plain text)

**UPDATED TO INCLUDE STRUCTURED PARSING:**

**Tasks:**

1. **Enhance `content_extractor.py` - Add structured parsing** (4 hours)
   - Implement `extract_structured_content()` method
   - Implement `_extract_front_matter()` - authors, affiliations, year, DOI
   - Implement `_extract_sections()` - recursive section parsing
   - Implement `_extract_figure()` and `_extract_table()` methods
   - Implement `_extract_references()` - full bibliographic data
   - Implement helper methods: `_flatten_figures()`, `_flatten_tables()`, `_count_citations()`

2. **Update `_try_pmc_xml()` in manager.py** (2 hours)
   - Call `extract_structured_content()` instead of `extract_text()`
   - Return `FullTextResult` with `structured_content` populated
   - Add quality indicators based on structure

3. **Create comprehensive test suite** (3 hours)
   - `tests/fulltext/test_structured_extraction.py` - test all structure elements
   - Test author extraction with affiliations and ORCID
   - Test section hierarchy (sections, subsections, paragraphs)
   - Test figure and table extraction
   - Test reference extraction with DOI/PMID
   - Test citation counting

4. **Add utility methods** (1 hour)
   - `FullTextContent.get_section_by_title()` - find sections by regex
   - `FullTextContent.get_methods_text()` - extract Methods section
   - `FullTextContent.get_full_text()` - flatten to plain text
   - `Section.get_all_text()` - recursive text extraction

5. **Integration testing** (2 hours)
   - Test on 50 PMC articles with known structure
   - Validate section extraction accuracy
   - Validate reference extraction accuracy
   - Measure structured vs. plain text quality

**Testing:**
- 50 PMC articles with verified structure
- Accuracy tests: Sections (>90%), Authors (>95%), References (>90%)
- Quality comparison: Structured (0.98) vs. Plain text (0.85)

**Success Criteria:**
- ✅ 90% accuracy for section detection
- ✅ 95% accuracy for author/affiliation extraction
- ✅ 90% accuracy for reference extraction with DOI/PMID
- ✅ Figures and tables correctly identified and extracted
- ✅ Citation callouts counted correctly
- ✅ Methods section detection works for 95% of papers
- ✅ All structured data tests passing

### Phase 1C: PDF Download Integration (Days 5-6)

**Goal:** Integrate reliable PDF downloads for Tier 2-4 sources

**⚠️ SIMPLIFIED APPROACH: Download PDFs, Defer Parsing**

**Philosophy:**
- **Download & Store** PDFs reliably for archival purposes
- **Defer Parsing Decision** until we can evaluate all options:
  - Traditional: GROBID, s2orc-doc2json, pdfplumber
  - Modern: LLM-based extraction (GPT-4V, Claude with vision)
  - Hybrid: LLM + traditional tools for validation
- **Avoid Complexity** at this phase - focus on reliable acquisition

**Tasks:**

1. **Update `_try_unpaywall_pdf()`** (2 hours)
   - Download PDF immediately (use existing PDFDownloadManager)
   - Return `FullTextResult` with `pdf_path` populated
   - Store URL for provenance
   - **NO TEXT EXTRACTION** - just download and save

2. **Update `_try_institutional_pdf()`** (2 hours)
   - Same pattern as Unpaywall
   - Download PDF if institutional access available
   - **NO TEXT EXTRACTION**

3. **Add `_try_arxiv_pdf()`, `_try_biorxiv_pdf()`** (3 hours)
   - Implement PDF download from preprint servers
   - Better success rate than publishers
   - **NO TEXT EXTRACTION**

4. **Enhance PDF download reliability** (2 hours)
   - Better retry logic with exponential backoff
   - Timeout handling (30s default)
   - Validation (check PDF signature: `%PDF-`)
   - Disk space checks

5. **Create integration tests** (2 hours)
   - `tests/fulltext/test_pdf_downloads.py`
   - Test download success rates
   - Test file validation
   - Test cache behavior

6. **End-to-end testing** (3 hours)
   - Test PMC XML → Unpaywall PDF fallback
   - Test publications without PMC ID
   - Measure overall success rate

**Testing:**
- 50 publications with PMC IDs → 95% success (XML)
- 50 publications without PMC → 60% success (PDF downloaded)
- Combined: 80% success rate

**Success Criteria:**
- ✅ 60% PDF download success on non-PMC OA articles
- ✅ 80% overall success rate (XML content + PDF files)
- ✅ <5s average PDF download time
- ✅ Proper file validation (PDF signature check)
- ✅ **NO PARSING ATTEMPTED** - just reliable downloads

**Phase 2 (Future): PDF Parsing Strategy**
- Research LLM-based extraction approaches
- Benchmark traditional tools vs. LLM extraction
- Decide on hybrid approach
- Implement in separate phase when ready

### Phase 2: Caching & Optimization (Week 2)

**Deferred to future:** Caching, quality scoring, advanced features

---

## File-by-File Implementation Guide

### Step 1: Create `lib/fulltext/models.py` Updates

**File:** `lib/fulltext/models.py`
**Action:** Add new enums and update FullTextResult
**Estimated Time:** 30 minutes

```python
# ADD these enums at the top (after imports)

from enum import Enum
from pathlib import Path

class ContentType(Enum):
    """Content format types"""
    XML = "xml"           # JATS XML (PMC, Europe PMC, etc.)
    HTML = "html"         # Publisher HTML pages
    PDF = "pdf"           # PDF files (stored, not extracted)
    TEXT = "text"         # Plain text (future)
    UNKNOWN = "unknown"

class SourceType(Enum):
    """Content source providers"""
    PMC = "pmc"                      # PubMed Central
    EUROPE_PMC = "europepmc"         # Europe PMC
    UNPAYWALL = "unpaywall"          # Unpaywall OA
    INSTITUTIONAL = "institutional"   # University access
    CROSSREF = "crossref"            # Crossref TDM
    ARXIV = "arxiv"                  # arXiv preprints
    BIORXIV = "biorxiv"              # bioRxiv preprints
    PUBLISHER = "publisher"          # Direct from publisher
    SCIHUB = "scihub"                # Sci-Hub
    LIBGEN = "libgen"                # Library Genesis
    CACHE = "cache"                  # Local cache
```

**UPDATE FullTextResult dataclass:**

```python
@dataclass
class FullTextResult:
    """Result of full-text retrieval attempt"""

    # Status
    success: bool = False
    error_message: Optional[str] = None

    # Content (NEW: at least one should be populated)
    content: Optional[str] = None              # NEW: Actual text content (XML/HTML/text)
    pdf_path: Optional[Path] = None            # NEW: Path to downloaded PDF

    # Provenance (NEW: ALWAYS populate for debugging)
    source_url: Optional[str] = None           # NEW: Original URL (HTML page or PDF link)
    source_type: Optional[SourceType] = None   # NEW: Which service provided it
    content_type: Optional[ContentType] = None # NEW: Format of content

    # Quality metrics (NEW)
    quality_score: float = 0.0                 # NEW: 0.0-1.0 (0.98 for XML, 0.70 for PDF)
    word_count: int = 0                        # NEW: Approximate content length
    has_sections: bool = False                 # NEW: Structured content detected

    # KEEP existing fields
    url: Optional[str] = None                  # DEPRECATED: Use source_url instead
    metadata: Dict[str, Any] = field(default_factory=dict)

    # NEW fields
    fetch_timestamp: Optional[str] = None      # NEW: ISO 8601 timestamp
    is_cached: bool = False                    # NEW: Retrieved from cache
    validation_errors: list = field(default_factory=list)  # NEW: Any issues detected
```

**Validation:** Run `python -m pytest tests/fulltext/test_models.py -v`

---

### Step 2: Create `lib/fulltext/content_fetcher.py`

**File:** `lib/fulltext/content_fetcher.py` (NEW FILE)
**Action:** Create complete ContentFetcher class
**Estimated Time:** 1 hour

**Full code provided in Component 1 specification above** - copy entire class.

**After creation:**
1. Create output directory: `mkdir -p data/fulltext/xml/pmc`
2. Test import: `python -c "from lib.fulltext.content_fetcher import ContentFetcher; print('OK')"`
3. Run basic test (see Testing Strategy section)

---

### Step 3: Create `lib/fulltext/content_extractor.py`

**File:** `lib/fulltext/content_extractor.py` (NEW FILE)
**Action:** Create complete ContentExtractor class
**Estimated Time:** 1 hour

**Full code provided in Component 2 specification above** - copy entire class.

**After creation:**
1. Install dependencies: `pip install beautifulsoup4 lxml`
2. Test import: `python -c "from lib.fulltext.content_extractor import ContentExtractor; print('OK')"`
3. Test with sample XML (see Testing Strategy section)

---

### Step 4: Update `lib/fulltext/manager.py`

**File:** `lib/fulltext/manager.py` (MODIFY EXISTING)
**Action:** Integrate new components
**Estimated Time:** 2 hours

**Step 4.1: Add imports** (top of file)

```python
# ADD these imports
from .content_fetcher import ContentFetcher, FetchResult
from .content_extractor import ContentExtractor
from .models import FullTextResult, ContentType, SourceType
from datetime import datetime
import aiofiles
```

**Step 4.2: Update `__init__` method**

Find the `__init__` method and ADD these lines:

```python
def __init__(self, config):
    self.config = config

    # NEW: Initialize content components
    fetcher_config = {
        "ncbi_api_key": config.get("ncbi_api_key"),
        "timeout": config.get("timeout", 30),
        "max_retries": config.get("max_retries", 3),
        "output_dir": config.get("output_dir", "data/fulltext")
    }
    self.content_fetcher = ContentFetcher(fetcher_config)

    extractor_config = {
        "min_word_count": config.get("min_word_count", 100)
    }
    self.content_extractor = ContentExtractor(extractor_config)

    # KEEP existing initializations
    self.pdf_download_manager = PDFDownloadManager(config)
    # ... rest of existing code
```

**Step 4.3: Update `get_fulltext()` method**

Find the `get_fulltext` method and MODIFY the waterfall to prioritize PMC:

```python
async def get_fulltext(self, publication) -> FullTextResult:
    """
    UPDATED: Returns actual content, not just URLs.
    """
    # Cache check (keep existing code)
    if self.config.get("enable_cache"):
        cached = await self._check_cache(publication)
        if cached.success:
            return cached

    # NEW: Try PMC first (highest quality)
    if publication.pmc_id and self.config.get("enable_pmc", True):
        result = await self._try_pmc(publication)
        if result.success:
            if self.config.get("enable_cache"):
                await self._cache_result(publication, result)
            return result

    # Continue with existing waterfall sources
    # MODIFY: Change method names to *_content (e.g., _try_unpaywall_content)
    sources = [
        ("institutional", self._try_institutional_content),
        ("unpaywall", self._try_unpaywall_content),
        # ... keep other sources with updated names
    ]

    # Rest of existing waterfall logic
    for source_name, source_func in sources:
        # ... existing code
```

**Step 4.4: Add `_try_pmc()` method** (NEW)

Add this complete method (code from Component 3 specification):

```python
async def _try_pmc(self, publication) -> FullTextResult:
    """NEW METHOD: Fetch and extract PMC XML content."""
    # Copy complete implementation from Component 3 above
    # (Lines 200-280 of Component 3 specification)
```

**Step 4.5: Add `_save_xml_to_disk()` helper** (NEW)

```python
async def _save_xml_to_disk(self, publication, xml_content: str, source: str) -> Path:
    """Save raw XML to disk for future reference."""
    # Copy complete implementation from Component 3 above
    # (Lines 350-370 of Component 3 specification)
```

**Step 4.6: Modify `_try_unpaywall()`** → **`_try_unpaywall_content()`**

RENAME method and UPDATE to download PDFs immediately:

```python
# OLD: async def _try_unpaywall(self, publication) -> FullTextResult:
# NEW: async def _try_unpaywall_content(self, publication) -> FullTextResult:

async def _try_unpaywall_content(self, publication) -> FullTextResult:
    """MODIFIED: Downloads PDF immediately (single-phase)."""
    # Copy complete implementation from Component 3 above
    # (Lines 282-348 of Component 3 specification)
```

**Validation:**
```bash
python -m pytest tests/fulltext/test_manager.py -v
python -c "from lib.fulltext.manager import FullTextManager; print('Import OK')"
```

---

### Step 5: Create Test Files

**Step 5.1: Create `tests/fulltext/test_content_fetcher.py`**

```python
"""Tests for ContentFetcher component"""

import pytest
import asyncio
from lib.fulltext.content_fetcher import ContentFetcher

@pytest.fixture
def fetcher():
    config = {
        "timeout": 30,
        "max_retries": 3,
        "output_dir": "data/fulltext"
    }
    return ContentFetcher(config)

@pytest.mark.asyncio
async def test_fetch_pmc_xml_success(fetcher):
    """Test successful PMC XML fetch"""
    # Known good PMC ID
    result = await fetcher.fetch_xml("pmc", "PMC2228570")

    assert result.success
    assert result.content is not None
    assert len(result.content) > 1000
    assert result.content_type == "xml"
    assert "PMC2228570" in result.metadata.get("pmc_id", "")

@pytest.mark.asyncio
async def test_fetch_pmc_xml_invalid_id(fetcher):
    """Test PMC fetch with invalid ID"""
    result = await fetcher.fetch_xml("pmc", "PMC99999999999")

    assert not result.success
    assert result.error is not None

@pytest.mark.asyncio
async def test_rate_limiting(fetcher):
    """Test rate limiting (should take ~1 second for 3 requests)"""
    import time
    start = time.time()

    tasks = [
        fetcher.fetch_xml("pmc", f"PMC{i}")
        for i in [2228570, 3148254, 3148255]
    ]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start
    # Should take at least 0.6 seconds (3 requests / 3 per sec)
    assert elapsed >= 0.6

# Add 5-10 more test cases covering edge cases
```

**Step 5.2: Create `tests/fulltext/test_content_extractor.py`**

```python
"""Tests for ContentExtractor component"""

import pytest
from lib.fulltext.content_extractor import ContentExtractor

@pytest.fixture
def extractor():
    return ContentExtractor({"min_word_count": 100})

def test_extract_from_pmc_xml(extractor):
    """Test extraction from PMC XML"""
    sample_xml = '''<?xml version="1.0"?>
    <article>
        <body>
            <sec>
                <title>Introduction</title>
                <p>This is a test paragraph with enough words to pass the minimum word count requirement for validation purposes.</p>
            </sec>
            <sec>
                <title>Methods</title>
                <p>More content here to ensure we have sufficient text for extraction and validation testing purposes in this unit test.</p>
            </sec>
        </body>
    </article>
    '''

    text = extractor.extract_from_xml(sample_xml)

    assert text is not None
    assert "Introduction" in text
    assert "Methods" in text
    assert len(text.split()) >= 100

def test_extract_metadata(extractor):
    """Test metadata extraction"""
    sample_xml = '''<?xml version="1.0"?>
    <article>
        <front>
            <article-meta>
                <title-group>
                    <article-title>Test Article Title</article-title>
                </title-group>
                <abstract>
                    <p>This is the abstract text.</p>
                </abstract>
                <kwd-group>
                    <kwd>keyword1</kwd>
                    <kwd>keyword2</kwd>
                </kwd-group>
            </article-meta>
        </front>
    </article>
    '''

    metadata = extractor.extract_metadata(sample_xml)

    assert metadata.get("title") == "Test Article Title"
    assert "abstract" in metadata
    assert len(metadata.get("keywords", [])) == 2

def test_quality_score_calculation(extractor):
    """Test quality score calculation"""
    text = "word " * 1000  # 1000 words

    score_xml = extractor.calculate_quality_score(text, "xml", has_sections=True)
    score_pdf = extractor.calculate_quality_score(text, "pdf", has_sections=False)

    assert score_xml > score_pdf
    assert 0.95 <= score_xml <= 1.0
    assert 0.60 <= score_pdf <= 0.75

# Add more test cases
```

**Step 5.3: Create `tests/fulltext/test_pmc_integration.py`**

```python
"""Integration tests for PMC full-text retrieval"""

import pytest
import asyncio
from lib.fulltext.manager import FullTextManager
from lib.publications.models import Publication

@pytest.fixture
def manager():
    config = {
        "enable_pmc": True,
        "enable_cache": False,
        "output_dir": "data/fulltext",
        "timeout": 30
    }
    return FullTextManager(config)

@pytest.mark.asyncio
async def test_end_to_end_pmc_retrieval(manager):
    """Test complete PMC retrieval workflow"""
    # Create test publication
    pub = Publication(
        pmid="18277380",
        pmc_id="PMC2228570",
        doi="10.1371/journal.pone.0001656",
        title="Test Article"
    )

    result = await manager.get_fulltext(pub)

    assert result.success
    assert result.content is not None
    assert result.source_type.value == "pmc"
    assert result.content_type.value == "xml"
    assert result.quality_score >= 0.95
    assert result.word_count > 100
    assert result.source_url is not None

@pytest.mark.asyncio
async def test_batch_pmc_retrieval(manager):
    """Test batch processing of multiple PMC articles"""
    test_pubs = [
        Publication(pmid="18277380", pmc_id="PMC2228570"),
        Publication(pmid="18274536", pmc_id="PMC3148254"),
        Publication(pmid="18274537", pmc_id="PMC3148255"),
    ]

    tasks = [manager.get_fulltext(pub) for pub in test_pubs]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r.success)
    assert success_count >= 2  # At least 2/3 should succeed

# Add performance tests, error handling tests, etc.
```

---

### Step 6: Configuration Updates

**File:** `config/development.yml`
**Action:** Add full-text configuration section

```yaml
fulltext:
  enable_pmc: true
  enable_unpaywall: true
  enable_institutional: true
  enable_cache: true

  # Tier 4 sources (enabled by default as last resort)
  enable_scihub: true   # Enabled: Only used after all Tier 1-3 sources fail
  enable_libgen: true   # Enabled: Final fallback to maximize coverage

  # NCBI API (optional - get from https://www.ncbi.nlm.nih.gov/account/)
  ncbi_api_key: null  # Set to increase rate limit from 3/sec to 10/sec

  # Timeouts
  timeout: 30
  max_retries: 3

  # Storage
  output_dir: data/fulltext

  # Quality
  min_word_count: 100

  # Content extraction
  extractor:
    min_word_count: 100
    extract_metadata: true
    extract_sections: false  # Phase 2 feature

  # PDF downloads
  pdf:
    max_concurrent: 5
    chunk_size: 8192
    validate_pdf: true
```

---

### Step 7: Directory Structure Setup

**Create required directories:**

```bash
# Run this from project root
mkdir -p data/fulltext/xml/pmc
mkdir -p data/fulltext/xml/europepmc
mkdir -p data/fulltext/xml/arxiv
mkdir -p data/fulltext/html/nature
mkdir -p data/fulltext/html/elsevier
mkdir -p data/fulltext/pdf/unpaywall
mkdir -p data/fulltext/pdf/institutional
mkdir -p data/fulltext/pdf/scihub

# Create .gitkeep files
find data/fulltext -type d -exec touch {}/.gitkeep \;
```

---

## Testing Strategy

### Unit Tests (Per Component)

**ContentFetcher Tests:**
- ✅ Successful PMC XML fetch
- ✅ Invalid PMC ID handling
- ✅ Rate limiting compliance
- ✅ Timeout handling
- ✅ Retry logic with exponential backoff
- ✅ SSL certificate handling
- ✅ Response validation

**ContentExtractor Tests:**
- ✅ JATS XML text extraction
- ✅ Metadata extraction (title, abstract, keywords)
- ✅ Quality score calculation
- ✅ Minimum word count validation
- ✅ Whitespace cleanup
- ✅ Malformed XML handling

**FullTextManager Tests:**
- ✅ PMC waterfall priority
- ✅ Fallback to PDF downloads
- ✅ Cache integration
- ✅ Error propagation
- ✅ Concurrent request handling

### Integration Tests

**Test Case 1: PMC Success**
```python
# Publication with PMC ID
pub = Publication(pmid="18277380", pmc_id="PMC2228570", doi="10.1371/journal.pone.0001656")

# Expected:
# - Fetch from PMC (success)
# - Extract text (success)
# - Save XML to data/fulltext/xml/pmc/PMC2228570.xml
# - Return FullTextResult with content populated
# - Quality score: 0.98
# - Time: <2s
```

**Test Case 2: PMC Unavailable, Unpaywall PDF Success**
```python
# Publication without PMC ID but with OA PDF
pub = Publication(pmid="12345678", doi="10.1234/example.doi")

# Expected:
# - Try PMC (skip - no PMC ID)
# - Try Unpaywall (success)
# - Download PDF to data/fulltext/pdf/unpaywall/12345678.pdf
# - Return FullTextResult with pdf_path populated
# - Quality score: 0.70
# - Time: <5s
```

**Test Case 3: All Sources Fail**
```python
# Publication with no OA availability
pub = Publication(pmid="99999999", doi="10.9999/closed.access")

# Expected:
# - Try all sources (all fail)
# - Return FullTextResult(success=False)
# - Error message: "No full-text source available"
```

### Performance Tests

**Batch Processing Test:**
```python
# 100 PMC articles
pubs = [Publication(pmc_id=f"PMC{i}") for i in test_ids]
start = time.time()
results = await asyncio.gather(*[manager.get_fulltext(p) for p in pubs])
elapsed = time.time() - start

# Targets:
# - Success rate: ≥95%
# - Average time: <2s per article
# - Total time: <200s for 100 articles
# - No rate limit errors
```

### Manual Testing Script

Create `scripts/test_fulltext_manual.py`:

```python
"""Manual testing script for full-text retrieval"""

import asyncio
from lib.fulltext.manager import FullTextManager
from lib.publications.models import Publication

async def main():
    config = {
        "enable_pmc": True,
        "output_dir": "data/fulltext",
        "timeout": 30
    }

    manager = FullTextManager(config)

    # Test PMC article
    print("Testing PMC retrieval...")
    pub1 = Publication(
        pmid="18277380",
        pmc_id="PMC2228570",
        doi="10.1371/journal.pone.0001656"
    )

    result = await manager.get_fulltext(pub1)

    if result.success:
        print(f"✓ Success!")
        print(f"  Source: {result.source_type.value}")
        print(f"  Content length: {len(result.content)} chars")
        print(f"  Word count: {result.word_count}")
        print(f"  Quality: {result.quality_score}")
        print(f"  URL: {result.source_url}")
    else:
        print(f"✗ Failed: {result.error_message}")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Run with: `python scripts/test_fulltext_manual.py`

---

## Success Metrics

### Coverage Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| PMC Articles Success Rate | ≥95% | Test on 100 random PMC IDs |
| Non-PMC OA Success Rate | ≥60% | Test on 50 Unpaywall OA articles |
| Overall Success Rate | ≥80% | Combined PMC + non-PMC test set |
| Cache Hit Rate | ≥70% | After initial retrieval (Phase 2) |

### Quality Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| PMC XML Quality Score | ≥0.95 | Automatic scoring via ContentExtractor |
| PDF Download Quality | ≥0.70 | Automatic scoring (no extraction yet) |
| Word Count Accuracy | ≥95% | Compare extracted word count to expected |
| Metadata Extraction | ≥90% | Title, abstract, keywords from PMC XML |

### Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| PMC Fetch Time | <2s | Average time for single PMC fetch |
| PDF Download Time | <5s | Average time for single PDF download |
| Batch Processing (10 articles) | <30s | Total time for 10 parallel fetches |
| Batch Processing (100 articles) | <200s | Total time for 100 parallel fetches |
| Rate Limit Compliance | 100% | No 429 errors from NCBI |

### Storage Metrics

| Metric | Expected Value | Notes |
|--------|---------------|-------|
| PMC XML Size | 200-500 KB/article | Raw JATS XML |
| PDF Size | 1-5 MB/article | Downloaded PDF files |
| Database Growth | ~50 KB/article | Cached results (Phase 2) |
| 1000 Articles Total | ~3-5 GB | Combined storage |

### Reliability Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Error Handling | 100% | All exceptions caught and logged |
| Retry Success Rate | ≥50% | Failed requests that succeed on retry |
| Timeout Handling | 100% | No hanging requests |
| Graceful Degradation | 100% | Fallback to next source on failure |

---

## Rollback Plan

### Pre-Implementation Backup

**Before starting implementation:**

```bash
# Create backup branch
git checkout -b backup-pre-fulltext-collection-$(date +%Y%m%d)
git push origin backup-pre-fulltext-collection-$(date +%Y%m%d)

# Tag current state
git tag -a fulltext-pre-implementation -m "State before full-text collection implementation"
git push origin fulltext-pre-implementation

# Backup critical files
mkdir -p backups/fulltext-$(date +%Y%m%d)
cp lib/fulltext/manager.py backups/fulltext-$(date +%Y%m%d)/
cp lib/fulltext/models.py backups/fulltext-$(date +%Y%m%d)/
```

### Rollback Triggers

**Rollback if any of these occur:**

1. **Critical Failure:** Success rate <50% on test set
2. **Performance Degradation:** >10s average fetch time
3. **Data Corruption:** Invalid content extracted
4. **System Instability:** Memory leaks, crashes
5. **Regression:** Existing functionality breaks

### Rollback Procedure

**Step 1: Stop All Running Processes**
```bash
# Stop any running full-text retrieval jobs
pkill -f "omics_oracle"
```

**Step 2: Restore Code**
```bash
# Restore from backup branch
git checkout backup-pre-fulltext-collection-YYYYMMDD

# Or restore individual files
cp backups/fulltext-YYYYMMDD/manager.py lib/fulltext/
cp backups/fulltext-YYYYMMDD/models.py lib/fulltext/
```

**Step 3: Remove New Files**
```bash
# Remove newly created files
rm lib/fulltext/content_fetcher.py
rm lib/fulltext/content_extractor.py
rm tests/fulltext/test_content_fetcher.py
rm tests/fulltext/test_content_extractor.py
rm tests/fulltext/test_pmc_integration.py
```

**Step 4: Clean Data**
```bash
# Optional: Remove fetched data (if corrupted)
rm -rf data/fulltext/xml/
rm -rf data/fulltext/pdf/

# Keep directory structure
mkdir -p data/fulltext/{xml,html,pdf}
```

**Step 5: Restore Configuration**
```bash
# Restore original config
git checkout backup-pre-fulltext-collection-YYYYMMDD -- config/development.yml
```

**Step 6: Validate Restoration**
```bash
# Run existing tests
python -m pytest tests/fulltext/test_manager.py -v

# Verify imports
python -c "from lib.fulltext.manager import FullTextManager; print('OK')"
```

### Partial Rollback (Disable Feature)

**If complete rollback not needed, disable via config:**

```yaml
# config/development.yml
fulltext:
  enable_pmc: false  # Disable PMC fetching
  enable_unpaywall: true  # Keep PDF downloads

  # Fallback to URL-only mode
  fetch_content: false  # NEW flag to disable content fetching
```

**Add feature flag to manager:**

```python
# In FullTextManager.__init__
self.fetch_content_enabled = config.get("fetch_content", True)

# In get_fulltext()
if not self.fetch_content_enabled:
    # Fallback to old URL-only behavior
    return await self._get_fulltext_urls_only(publication)
```

### Post-Rollback Analysis

**After rollback, document:**

1. **What went wrong?**
   - Specific error messages
   - Failed test cases
   - Performance metrics

2. **Root cause analysis**
   - Code review
   - Architecture review
   - Dependency issues

3. **Corrective action plan**
   - Fixes required
   - Additional testing needed
   - Timeline for retry

---

## Implementation Checklist

### Phase 1A: PMC Content Retrieval

**Day 1:**
- [ ] Create backup branch and tag
- [ ] Update `lib/fulltext/models.py` with new enums and FullTextResult fields
- [ ] Create `lib/fulltext/content_fetcher.py` (complete ContentFetcher class)
- [ ] Create `lib/fulltext/content_extractor.py` (complete ContentExtractor class)
- [ ] Install dependencies: `pip install beautifulsoup4 lxml aiofiles`
- [ ] Create directory structure: `mkdir -p data/fulltext/xml/pmc`
- [ ] Test imports: All new modules import successfully
- [ ] Create `tests/fulltext/test_content_fetcher.py`
- [ ] Create `tests/fulltext/test_content_extractor.py`
- [ ] Run unit tests: All tests pass

**Day 2:**
- [ ] Update `lib/fulltext/manager.py` - add imports
- [ ] Update `FullTextManager.__init__` - initialize new components
- [ ] Implement `_try_pmc()` method
- [ ] Implement `_save_xml_to_disk()` helper
- [ ] Update `get_fulltext()` waterfall - prioritize PMC
- [ ] Create `tests/fulltext/test_pmc_integration.py`
- [ ] Run integration tests: PMC retrieval end-to-end works
- [ ] Update `config/development.yml` - add fulltext section
- [ ] Create manual test script: `scripts/test_fulltext_manual.py`
- [ ] Run manual test: 10 PMC articles successfully retrieved
- [ ] Performance test: 100 PMC articles in <200s
- [ ] Success rate validation: ≥95% on 100 articles
- [ ] Documentation: Update CURRENT_STATUS.md with progress

### Phase 1B: PDF Download Integration

**Day 3:**
- [ ] Rename `_try_unpaywall()` to `_try_unpaywall_content()`
- [ ] Update `_try_unpaywall_content()` - download PDF immediately
- [ ] Update `_try_institutional()` to `_try_institutional_content()`
- [ ] Update waterfall in `get_fulltext()` - use new method names
- [ ] Create `tests/fulltext/test_pdf_downloads.py`
- [ ] Test PDF downloads: 50 Unpaywall articles
- [ ] Success rate validation: ≥60% on non-PMC OA articles

**Day 4:**
- [ ] Create `tests/fulltext/test_waterfall_integration.py`
- [ ] Integration test: PMC → Unpaywall fallback works
- [ ] End-to-end test: 100 mixed articles (PMC + non-PMC)
- [ ] Overall success rate: ≥80% achieved
- [ ] Performance validation: <5s average for PDFs
- [ ] Error handling review: All edge cases covered
- [ ] Documentation: Update implementation plan with results
- [ ] Code review: Review all changes
- [ ] Create PR: Submit for review
- [ ] Tag completion: `git tag fulltext-phase1-complete`

### Post-Implementation

- [ ] Monitor production: Track success rates
- [ ] Performance monitoring: Track fetch times
- [ ] Error logging: Identify common failures
- [ ] User feedback: Collect usage feedback
- [ ] Plan Phase 2: Caching and optimization

---

## Appendix A: Quick Reference

### Common Commands

```bash
# Run all tests
python -m pytest tests/fulltext/ -v

# Run specific test
python -m pytest tests/fulltext/test_content_fetcher.py::test_fetch_pmc_xml_success -v

# Run manual test
python scripts/test_fulltext_manual.py

# Check imports
python -c "from lib.fulltext.content_fetcher import ContentFetcher; print('OK')"
python -c "from lib.fulltext.content_extractor import ContentExtractor; print('OK')"

# Create directories
mkdir -p data/fulltext/{xml/{pmc,europepmc,arxiv},html/{nature,elsevier},pdf/{unpaywall,institutional}}

# Install dependencies
pip install beautifulsoup4 lxml aiofiles aiohttp

# Backup current state
git checkout -b backup-$(date +%Y%m%d)
```

### File Locations Summary

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `lib/fulltext/models.py` | Data models (FullTextResult, enums) | +50 | Modify |
| `lib/fulltext/content_fetcher.py` | Fetch XML/HTML/PDF from sources | 350 | Create |
| `lib/fulltext/content_extractor.py` | Extract text from XML/HTML | 250 | Create |
| `lib/fulltext/manager.py` | Orchestrate retrieval waterfall | +200 | Modify |
| `tests/fulltext/test_content_fetcher.py` | Unit tests for fetcher | 150 | Create |
| `tests/fulltext/test_content_extractor.py` | Unit tests for extractor | 120 | Create |
| `tests/fulltext/test_pmc_integration.py` | Integration tests | 100 | Create |
| `scripts/test_fulltext_manual.py` | Manual testing script | 50 | Create |
| `config/development.yml` | Configuration | +25 | Modify |

**Total New Code:** ~1,300 lines
**Modified Code:** ~300 lines
**Test Code:** ~420 lines

### Configuration Template

```yaml
fulltext:
  # Enable/disable sources
  enable_pmc: true
  enable_unpaywall: true
  enable_institutional: true
  enable_cache: true

  # Tier 4 sources (enabled by default as last resort)
  enable_scihub: true   # Enabled: Only used after all Tier 1-3 sources fail
  enable_libgen: true   # Enabled: Final fallback to maximize coverage

  # NCBI settings
  ncbi_api_key: null  # Optional: increases rate limit to 10/sec

  # Timeouts and retries
  timeout: 30
  max_retries: 3

  # Storage
  output_dir: data/fulltext

  # Quality thresholds
  min_word_count: 100
  min_quality_score: 0.50

  # Performance
  max_concurrent_fetches: 10
  rate_limit_requests_per_second: 3
```

### Typical FullTextResult Examples

**PMC Success:**
```python
FullTextResult(
    success=True,
    content="Introduction\nThis study investigates...",  # ~5000 words
    source_url="https://eutils.ncbi.nlm.nih.gov/...",
    source_type=SourceType.PMC,
    content_type=ContentType.XML,
    quality_score=0.98,
    word_count=5234,
    has_sections=True,
    metadata={
        "pmc_id": "PMC2228570",
        "xml_path": "data/fulltext/xml/pmc/PMC2228570.xml",
        "title": "Study Title",
        "abstract": "Study abstract..."
    },
    fetch_timestamp="2025-10-11T14:30:00Z"
)
```

**PDF Download Success:**
```python
FullTextResult(
    success=True,
    pdf_path=Path("data/fulltext/pdf/unpaywall/12345678.pdf"),
    source_url="https://doi.org/10.1234/example.pdf",
    source_type=SourceType.UNPAYWALL,
    content_type=ContentType.PDF,
    quality_score=0.70,
    metadata={
        "license": "cc-by",
        "version": "publishedVersion",
        "file_size_bytes": 2458631
    },
    fetch_timestamp="2025-10-11T14:30:05Z"
)
```

**Failure:**
```python
FullTextResult(
    success=False,
    error_message="No full-text source available",
    source_type=None,
    metadata={
        "attempted_sources": ["pmc", "institutional", "unpaywall"],
        "failure_reasons": {
            "pmc": "No PMC ID",
            "institutional": "Access denied",
            "unpaywall": "Not open access"
        }
    }
)
```

---

## Appendix B: Troubleshooting Guide

### Issue: PMC Fetch Returns Empty Content

**Symptoms:**
- `result.success = True` but `result.content` is None or very short
- No error message

**Diagnosis:**
```python
# Check raw XML
fetch_result = await content_fetcher.fetch_xml("pmc", "PMC1234567")
print(f"XML length: {len(fetch_result.content)}")
print(f"First 500 chars: {fetch_result.content[:500]}")
```

**Solutions:**
1. Invalid PMC ID - verify PMC ID exists in PubMed Central
2. XML parsing error - check for malformed XML
3. Network timeout - increase timeout in config
4. Rate limiting - check for 429 errors in logs

### Issue: PDF Downloads Failing

**Symptoms:**
- Success rate <40% for Unpaywall PDFs
- Timeout errors

**Diagnosis:**
```python
# Check URL validity
print(f"PDF URL: {pdf_url}")
curl -I {pdf_url}  # Check if URL returns PDF

# Check network
curl -v {pdf_url} > test.pdf
file test.pdf  # Should be "PDF document"
```

**Solutions:**
1. Landing page instead of PDF - parser needs enhancement
2. SSL certificate issues - already handled
3. Redirects not followed - already handled
4. Timeout too short - increase from 30s to 60s

### Issue: Rate Limiting from NCBI

**Symptoms:**
- 429 HTTP errors
- "Rate limited by NCBI" in logs

**Solutions:**
1. Decrease concurrent requests in config
2. Add NCBI API key (increases limit to 10/sec)
3. Increase delay between requests
4. Implement exponential backoff (already done)

### Issue: Memory Usage Growing

**Symptoms:**
- Memory usage increases over time
- OOM errors on large batches

**Solutions:**
1. Process in smaller batches (10-50 at a time)
2. Close aiohttp sessions: `await manager.content_fetcher.close()`
3. Clear cache periodically
4. Implement streaming for large XMLs (Phase 2)

---

## Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-11 | Initial implementation plan created | GitHub Copilot |

**END OF DOCUMENT**
