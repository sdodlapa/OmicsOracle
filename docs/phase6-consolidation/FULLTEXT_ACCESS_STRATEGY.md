# Comprehensive Full-Text & PDF Access Strategy for OmicsOracle

**Date**: October 9, 2025
**Current Status**: Partial PDF access via institutional/OA sources
**Goal**: Comprehensive full-text access for biomedical literature analysis

---

## Current State Assessment

### ✅ What We Have (Implemented in Week 4)

**1. Legal/Institutional Sources** (IMPLEMENTED)
- ✅ PubMed Central (PMC) - Open Access PDFs
- ✅ Unpaywall API - Open Access discovery
- ✅ Institutional access via Georgia Tech VPN/Proxy
- ✅ Europe PMC - Additional OA content
- ✅ PDF Download & extraction infrastructure

**Coverage**: ~40-50% of biomedical literature
- PMC OA: ~6 million articles
- Unpaywall: ~30 million articles
- Institutional subscriptions: Variable

**Files Implemented**:
```
omics_oracle_v2/lib/publications/
├── pdf_downloader.py          (✅ Downloads from known URLs)
├── fulltext_extractor.py      (✅ Extracts text from PDFs)
├── institutional_access.py    (✅ GT proxy/VPN integration)
└── unpaywall.py               (✅ OA discovery)
```

### ❌ What We Don't Have

**Missing Coverage**: ~50-60% of literature
- Paywalled journals without institutional access
- Recent publications not yet in PMC
- Journals not covered by GT subscriptions
- Older pre-digital literature

**Gaps**:
- No Sci-Hub integration (legal gray area)
- No LibGen integration (legal concerns)
- No bulk torrent access (infrastructure needed)
- Limited access to non-OA preprints

---

## Proposed Solutions (Ranked by Legality & Feasibility)

### 🟢 SOLUTION 1: Expand Legal Open Access Sources (RECOMMENDED)

**Approach**: Maximize coverage through legal channels

**Implementation Priority: HIGH**
**Legal Risk: NONE**
**Effort: Medium**
**Coverage Gain: +15-20%**

#### Components:

**1.1 Additional OA Repositories**

```python
# New integrations to add:
sources = {
    "CORE": {  # 200M+ OA papers
        "api": "https://api.core.ac.uk/v3",
        "coverage": "45M+ full texts",
        "cost": "Free API key"
    },
    "arXiv": {  # Preprints
        "api": "http://export.arxiv.org/api/query",
        "coverage": "2M+ preprints",
        "cost": "Free"
    },
    "bioRxiv/medRxiv": {  # Biomedical preprints
        "api": "https://api.biorxiv.org",
        "coverage": "200K+ preprints",
        "cost": "Free"
    },
    "Crossref": {  # Publisher metadata + some full texts
        "api": "https://api.crossref.org",
        "coverage": "130M+ records, ~30M full texts",
        "cost": "Free"
    },
    "DOAJ": {  # Directory of OA Journals
        "api": "https://doaj.org/api/v2",
        "coverage": "2M+ OA articles",
        "cost": "Free"
    },
    "PubMed Central OA Subset": {  # Bulk download
        "ftp": "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/",
        "coverage": "6M+ full texts",
        "cost": "Free (FTP)"
    }
}
```

**Implementation**:
```python
# omics_oracle_v2/lib/publications/oa_aggregator.py

class OpenAccessAggregator:
    """Aggregate full-text access from multiple OA sources."""

    def __init__(self):
        self.sources = {
            'pmc': PMCClient(),
            'unpaywall': UnpaywallClient(),
            'core': COREClient(),  # NEW
            'arxiv': ArXivClient(),  # NEW
            'biorxiv': BioRxivClient(),  # NEW
            'crossref': CrossrefClient(),  # NEW
        }

    async def find_fulltext(self, doi: str, pmid: str = None) -> FullTextResult:
        """Try all sources in priority order."""
        # Try institutional first (best quality)
        # Then PMC (high quality, validated)
        # Then Unpaywall (good quality)
        # Then preprint servers (may be preprint version)
        # Then CORE (aggregated, variable quality)
```

**Advantages**:
- ✅ 100% legal
- ✅ High quality, peer-reviewed content
- ✅ Sustainable long-term
- ✅ No ethical concerns
- ✅ Can be openly documented

**Disadvantages**:
- ❌ Still won't cover all paywalled content
- ❌ Multiple API integrations needed
- ❌ Varying API quality/reliability

---

### 🟡 SOLUTION 2: Sci-Hub Torrents (Library Genesis) - GRAY AREA

**Approach**: Use Sci-Hub corpus via torrents (not live scraping)

**Implementation Priority: MEDIUM**
**Legal Risk: MODERATE-HIGH**
**Effort: High**
**Coverage Gain: +40-45%**

#### Why Torrents > Live Scraping:

**Advantages of Torrent Approach**:
1. **No server load** on Sci-Hub infrastructure
2. **Better privacy** - P2P vs centralized requests
3. **Offline capability** - Pre-download corpus
4. **More ethical** toward Sci-Hub (community preservation)
5. **Faster access** - Local lookup vs network requests
6. **Bulk processing** - Can download entire datasets

**The Sci-Hub Rescue Mission**:
- 85+ million papers (as of 2021)
- Organized in ~15,000 torrents by DOI prefix
- Maintained by DataHoarder community
- Total size: ~77 TB (can download selectively)

#### Implementation Strategy:

**Option 2A: Selective Torrent Downloads** (RECOMMENDED if pursuing this)

```python
# omics_oracle_v2/lib/publications/scihub_torrent.py

from typing import Optional
import libtorrent as lt
import sqlite3

class SciHubTorrentClient:
    """
    Access Sci-Hub papers via LibGen torrents.

    LEGAL WARNING: Using this may violate copyright law in many jurisdictions.
    Intended for academic research only. Check local laws before use.
    """

    def __init__(self, torrent_dir: Path, enable: bool = False):
        """
        Args:
            torrent_dir: Directory to store torrents
            enable: Explicit opt-in required (default: False)
        """
        if not enable:
            raise ValueError(
                "Sci-Hub torrent access is disabled by default. "
                "Set enable=True only if you understand the legal implications."
            )

        self.torrent_dir = Path(torrent_dir)
        self.metadata_db = self._load_metadata()
        self.active_torrents = {}

    def _load_metadata(self) -> sqlite3.Connection:
        """Load Sci-Hub metadata SQLite database."""
        # Database available at:
        # https://academictorrents.com/details/4b13244559282f9650a382f70506dc4c516215e2
        db_path = self.torrent_dir / "scihub_metadata.db"
        return sqlite3.connect(db_path)

    def find_paper_torrent(self, doi: str) -> Optional[str]:
        """Find which torrent contains a paper by DOI."""
        cursor = self.metadata_db.execute(
            "SELECT torrent_name FROM papers WHERE doi = ?", (doi,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def download_torrent(self, torrent_name: str, priority: bool = False):
        """Download a specific torrent containing papers."""
        # Use libtorrent for efficient downloading
        # Can prioritize specific DOI prefixes (e.g., biomedical journals)
        pass

    def get_paper_path(self, doi: str) -> Optional[Path]:
        """Get local path to paper if available."""
        torrent = self.find_paper_torrent(doi)
        if not torrent or torrent not in self.active_torrents:
            return None

        # Return path to PDF in torrent directory
        return self.torrent_dir / torrent / f"{doi.replace('/', '_')}.pdf"
```

**Using libgen-seedtools** (from the research):
```bash
# Install
pip install libgen-seedtools

# Download specific torrents for biomedical papers
from libgen_seedtools import search_torrents, download_torrent

# Search for torrents containing biomedical DOI prefixes
bio_torrents = search_torrents(doi_prefix="10.1038/")  # Nature papers
download_torrent(bio_torrents[0], output_dir="data/torrents/")
```

**Selective Download Strategy**:
1. Identify ~500-1000 most important biomedical journals
2. Download only torrents containing those DOI prefixes
3. Storage: ~2-5 TB (manageable on modern systems)
4. Covers ~70% of biomedical literature from major publishers

**Option 2B: On-Demand Live Scraping** (NOT RECOMMENDED)

Using `scihub.py` library:
```python
# LEGAL WARNING: This directly scrapes Sci-Hub servers
# May be illegal in your jurisdiction
# Puts load on Sci-Hub infrastructure

from scihub import SciHub

class SciHubLiveClient:
    """
    WARNING: Direct Sci-Hub scraping may be illegal.
    Recommend using torrents instead.
    """

    def __init__(self, enable_live_scraping: bool = False):
        if not enable_live_scraping:
            raise ValueError("Live Sci-Hub scraping disabled by default")

        self.sh = SciHub()

    def download_paper(self, doi: str, output_path: Path) -> bool:
        """Download single paper (puts load on Sci-Hub servers)."""
        try:
            result = self.sh.download(doi, path=str(output_path))
            return result is not None
        except Exception as e:
            logger.error(f"Sci-Hub download failed: {e}")
            return False
```

**Why NOT Recommended**:
- ❌ Puts load on Sci-Hub servers
- ❌ More easily tracked by authorities
- ❌ Rate limiting issues
- ❌ Less reliable (Sci-Hub domains change)
- ❌ Harder to justify ethically

#### Legal & Ethical Considerations:

**Legal Risks**:
1. **Copyright infringement** in most jurisdictions
2. **CFAA violations** (US) - unauthorized access
3. **Institutional policy violations** - most universities prohibit
4. **Civil liability** - publishers could sue

**When It Might Be Defensible**:
1. **Fair Use** (US):
   - Research/education purpose ✓
   - Transformational use (text mining) ✓
   - No market harm (already paywalled) ?
   - Limited portions (metadata only) ?

2. **Research Exception** (EU):
   - Text and data mining directive
   - Must have legal access to corpus
   - Must be for research purposes

3. **Academic Freedom**:
   - Knowledge should be free
   - Advancing science/medicine
   - No commercial use

**Recommendation**:
- **DO NOT implement** unless:
  1. You have institutional legal review
  2. Usage is strictly for research (not commercial)
  3. You're in a jurisdiction with TDM exceptions
  4. You use torrents (not live scraping)
  5. You implement strict access controls

**Implementation Safeguards** (if proceeding):
```python
# omics_oracle_v2/lib/publications/config.py

class SciHubConfig(BaseModel):
    """Configuration for Sci-Hub access (DISABLED BY DEFAULT)."""

    enable_scihub: bool = False  # Must be explicitly enabled
    use_torrents: bool = True  # Prefer torrents over live scraping
    enable_live_scraping: bool = False  # Explicitly opt-in to scraping
    require_legal_review: bool = True  # Force legal review
    log_all_access: bool = True  # Audit trail
    max_requests_per_day: int = 100  # Rate limiting

    # User must acknowledge legal risk
    legal_acknowledgment: Optional[str] = None

    def validate_enable(self):
        if self.enable_scihub:
            if not self.legal_acknowledgment:
                raise ValueError(
                    "Sci-Hub access requires legal_acknowledgment. "
                    "This feature may be illegal in your jurisdiction."
                )
            logger.warning(
                "Sci-Hub access ENABLED. User acknowledges legal risks. "
                "This may violate copyright law."
            )
```

---

### 🟡 SOLUTION 3: Hybrid Waterfall Approach (RECOMMENDED OVERALL)

**Approach**: Try legal sources first, fall back to gray area only if necessary

**Implementation Priority: HIGH**
**Legal Risk: LOW-MODERATE (user-configurable)**
**Effort: High**
**Coverage Gain: +40-50%**

#### Architecture:

```python
# omics_oracle_v2/lib/publications/fulltext_manager.py

class FullTextManager:
    """Intelligent full-text acquisition with waterfall strategy."""

    def __init__(self, config: FullTextConfig):
        self.config = config

        # Legal sources (always enabled)
        self.legal_sources = [
            InstitutionalAccessManager(),
            PMCClient(),
            UnpaywallClient(),
            COREClient(),
            ArXivClient(),
            BioRxivClient(),
        ]

        # Gray area sources (opt-in only)
        self.gray_sources = []
        if config.enable_scihub_torrents:
            self.gray_sources.append(SciHubTorrentClient())

    async def get_fulltext(
        self,
        doi: str,
        pmid: str = None,
        prefer_legal: bool = True
    ) -> FullTextResult:
        """
        Acquire full text using waterfall strategy.

        Strategy:
        1. Try institutional access (best quality, legal)
        2. Try PMC (peer-reviewed, legal)
        3. Try Unpaywall (legal)
        4. Try other OA sources (legal)
        5. Try preprint servers (legal, may be preprint)
        6. If enabled and not found: Try Sci-Hub torrents (GRAY AREA)

        Args:
            doi: Paper DOI
            pmid: Optional PubMed ID
            prefer_legal: If False and gray sources enabled, skip legal sources

        Returns:
            FullTextResult with source attribution
        """
        attempts = []

        # Phase 1: Legal sources
        for source in self.legal_sources:
            try:
                result = await source.get_fulltext(doi, pmid)
                if result.success:
                    result.source_type = "legal"
                    result.attempts = attempts
                    return result
                attempts.append({
                    "source": source.name,
                    "status": "not_found"
                })
            except Exception as e:
                attempts.append({
                    "source": source.name,
                    "status": "error",
                    "error": str(e)
                })

        # Phase 2: Gray area sources (only if enabled)
        if self.gray_sources and self.config.allow_gray_sources:
            logger.warning(
                f"Legal sources exhausted for {doi}. "
                f"Trying gray area sources (user-enabled)."
            )

            for source in self.gray_sources:
                try:
                    result = await source.get_fulltext(doi, pmid)
                    if result.success:
                        result.source_type = "gray_area"
                        result.legal_warning = (
                            "This content was obtained from a gray-area source. "
                            "Usage may violate copyright law in your jurisdiction."
                        )
                        result.attempts = attempts

                        # Log for audit
                        self._log_gray_access(doi, source.name)

                        return result
                except Exception as e:
                    attempts.append({
                        "source": source.name,
                        "status": "error",
                        "error": str(e)
                    })

        # Not found anywhere
        return FullTextResult(
            success=False,
            source_type="none",
            attempts=attempts,
            message=f"Full text not found in {len(attempts)} sources"
        )

    def _log_gray_access(self, doi: str, source: str):
        """Log access to gray area sources for audit."""
        logger.warning(
            f"GRAY_AREA_ACCESS: doi={doi}, source={source}, "
            f"timestamp={datetime.now()}, user={os.getenv('USER')}"
        )

        # Append to audit log
        with open("data/logs/gray_area_access.log", "a") as f:
            f.write(f"{datetime.now()},{doi},{source}\n")

    def get_statistics(self) -> Dict:
        """Get coverage statistics by source."""
        return {
            "legal_sources": {
                source.name: source.get_stats()
                for source in self.legal_sources
            },
            "gray_sources": {
                source.name: source.get_stats()
                for source in self.gray_sources
            } if self.gray_sources else {},
            "coverage": self._calculate_coverage()
        }
```

**Configuration**:
```python
# config/fulltext_config.yaml

fulltext:
  # Legal sources (always enabled)
  enable_institutional: true
  enable_pmc: true
  enable_unpaywall: true
  enable_core: true  # NEW
  enable_arxiv: true  # NEW
  enable_biorxiv: true  # NEW

  # Gray area sources (disabled by default)
  enable_scihub_torrents: false  # Must explicitly enable
  enable_live_scraping: false  # NOT RECOMMENDED

  # Access control
  allow_gray_sources: false  # Master kill switch
  require_legal_acknowledgment: true
  max_gray_requests_per_day: 100
  log_all_gray_access: true

  # Waterfall strategy
  prefer_legal: true
  timeout_per_source: 10  # seconds
  max_concurrent_sources: 3
```

**Usage**:
```python
from omics_oracle_v2.lib.publications import FullTextManager

manager = FullTextManager(config)

# Try to get full text (legal sources only by default)
result = await manager.get_fulltext(
    doi="10.1038/s41586-023-06670-3"
)

if result.success:
    print(f"Found in: {result.source_name}")
    print(f"Quality: {result.source_type}")  # "legal" or "gray_area"
    print(f"Path: {result.pdf_path}")

    if result.legal_warning:
        print(f"WARNING: {result.legal_warning}")
else:
    print(f"Not found. Tried {len(result.attempts)} sources:")
    for attempt in result.attempts:
        print(f"  - {attempt['source']}: {attempt['status']}")
```

---

### 🔴 SOLUTION 4: LibGen Direct API (NOT RECOMMENDED)

**Approach**: Direct API access to Library Genesis

**Implementation Priority: LOW**
**Legal Risk: HIGH**
**Effort: Low**
**Coverage Gain: +40%**

**Why NOT Recommended**:
- Similar legal risks to Sci-Hub
- Less community support than torrents
- API reliability issues
- No ethical advantage over torrents

**If Pursuing**: Use same safeguards as Sci-Hub (opt-in, logging, legal review)

---

## Recommended Implementation Plan

### Phase 1: Expand Legal Coverage (IMMEDIATE - 2 weeks)

**Priority: HIGH | Risk: NONE | Cost: FREE**

1. **Week 1: Additional OA Sources**
   - Implement CORE API client
   - Implement arXiv API client
   - Implement bioRxiv/medRxiv API client
   - Implement Crossref full-text links
   - Add PMC bulk FTP option

2. **Week 2: Integration & Testing**
   - Integrate into FullTextManager waterfall
   - Test coverage improvements
   - Benchmark performance
   - Document all sources

**Expected Outcome**: +15-20% coverage (legal)

### Phase 2: Torrent Infrastructure (OPTIONAL - 3-4 weeks)

**Priority: MEDIUM | Risk: MODERATE | Cost: Storage (2-5 TB)**

**Only if**:
- Legal review completed
- Institutional approval obtained
- Strict research-only use
- Non-commercial deployment

1. **Week 1: Research & Planning**
   - Legal review with university counsel
   - Identify critical journal DOI prefixes
   - Calculate storage requirements
   - Set up access controls

2. **Week 2: Metadata Setup**
   - Download Sci-Hub metadata DB
   - Build DOI → Torrent lookup
   - Identify biomedical subset (~500 journals)
   - Priority ranking system

3. **Week 3: Torrent Client**
   - Implement libgen-seedtools wrapper
   - Selective torrent downloading
   - Background seeding
   - Local storage management

4. **Week 4: Integration**
   - Add to FullTextManager as fallback
   - Implement strict logging
   - Add legal warnings
   - Comprehensive testing

**Expected Outcome**: +40-45% coverage (gray area)

### Phase 3: Monitoring & Compliance (ONGOING)

1. **Usage Monitoring**
   - Track source usage statistics
   - Monitor legal source coverage
   - Audit gray area access (if enabled)
   - Regular compliance reviews

2. **Documentation**
   - Clear legal disclaimers
   - Source attribution
   - Usage guidelines
   - Institutional policies

3. **Community Contribution**
   - Seed torrents if using
   - Contribute to OA indices
   - Report broken links
   - Share metadata improvements

---

## Technical Implementation Priority

### Must-Have (Phase 1 - Legal Only)

```python
# omics_oracle_v2/lib/publications/oa_sources/
├── __init__.py
├── core_client.py           # NEW - CORE API
├── arxiv_client.py          # NEW - arXiv
├── biorxiv_client.py        # NEW - bioRxiv/medRxiv
├── crossref_client.py       # NEW - Crossref full text
├── pmc_bulk.py              # NEW - PMC FTP bulk download
└── base.py                  # Base class for all sources

# omics_oracle_v2/lib/publications/
├── fulltext_manager.py      # NEW - Orchestrates waterfall
├── fulltext_result.py       # NEW - Result model
└── config.py                # UPDATE - Add new source configs
```

### Optional (Phase 2 - Gray Area)

```python
# omics_oracle_v2/lib/publications/gray_area/
├── __init__.py
├── scihub_torrent.py        # OPTIONAL - Torrent access
├── metadata_db.py           # OPTIONAL - DOI lookup
└── audit_logger.py          # OPTIONAL - Compliance logging

# Requires:
├── data/torrents/           # 2-5 TB storage
├── data/logs/gray_access/   # Audit logs
└── config/legal/            # Legal acknowledgments
```

---

## Coverage Projection

| Strategy | Legal Coverage | Total Coverage | Legal Risk |
|----------|---------------|----------------|------------|
| **Current** | 40-50% | 40-50% | None |
| **Phase 1 (Legal OA)** | 60-70% | 60-70% | None |
| **Phase 1 + Institutional** | 70-80% | 70-80% | None |
| **Phase 2 (+ Torrents)** | 60-70% | 95-98% | Moderate-High |

---

## Recommendations Summary

### ✅ DO (Recommended):

1. ✅ **Expand legal OA sources** (CORE, arXiv, bioRxiv, Crossref)
2. ✅ **Improve institutional access** (Better VPN/proxy integration)
3. ✅ **Implement waterfall strategy** (Try legal sources first)
4. ✅ **Document all sources** (Clear attribution)
5. ✅ **Monitor coverage** (Track what works)

### ⚠️ MAYBE (With Caution):

6. ⚠️ **Sci-Hub torrents** (ONLY if):
   - Legal review completed
   - Institutional approval obtained
   - Strict research-only use
   - Comprehensive logging
   - User opt-in required
   - Non-commercial deployment

### ❌ DON'T DO:

7. ❌ **Live Sci-Hub scraping** (Too risky, less ethical)
8. ❌ **LibGen direct API** (Same risks, less community support)
9. ❌ **Unauthorized bulk downloads** (Copyright violation)
10. ❌ **Commercial use of gray sources** (Definitely illegal)

---

## Next Steps

### Immediate (This Week):
1. Implement CORE API client
2. Implement arXiv API client
3. Implement bioRxiv/medRxiv client
4. Test coverage improvements

### Short-term (Next 2 Weeks):
1. Build FullTextManager orchestrator
2. Integrate all legal sources
3. Benchmark performance
4. Document implementation

### Long-term (If Pursuing Gray Area):
1. Seek legal review
2. Get institutional approval
3. Implement strict safeguards
4. Limited pilot testing

---

## Legal Disclaimer Template

```
LEGAL NOTICE: Full-Text Access

OmicsOracle attempts to obtain full-text articles through the following methods:

LEGAL SOURCES (Always Enabled):
- PubMed Central (Open Access)
- Unpaywall (Open Access Discovery)
- Institutional subscriptions (Georgia Tech)
- CORE (Open Access aggregator)
- arXiv/bioRxiv (Preprint servers)
- Crossref (Publisher links)

GRAY AREA SOURCES (Disabled by Default):
- Sci-Hub torrents (May violate copyright law)
- Library Genesis (May violate copyright law)

WARNING: Gray area sources may be illegal in your jurisdiction.
Use is at your own risk. OmicsOracle developers assume no liability.

For research and educational purposes only.
Not for commercial use.

By enabling gray area sources, you acknowledge:
1. You have reviewed local copyright laws
2. Your use qualifies as fair use or research exception
3. You accept full legal responsibility
4. You will not use for commercial purposes
```

---

**Recommendation**: Start with Phase 1 (legal sources only). This gives you 60-70% coverage with zero legal risk. Evaluate coverage after Phase 1 before considering Phase 2.
