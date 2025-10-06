# PDF Processing & Full-Text Extraction Specification

**Date:** October 6, 2025  
**Version:** 1.0  
**Module:** `omics_oracle_v2/lib/pdf/`  
**Priority:** High  
**Dependencies:** Publication Mining Module

---

## Overview

This specification details the PDF processing pipeline for downloading, parsing, and extracting structured content from scientific PDFs. The goal is to provide high-quality full-text extraction for biomedical publications.

---

## Module Architecture

```
omics_oracle_v2/lib/pdf/
├── __init__.py
├── models.py                 # PDF data models
├── downloader.py             # PDF acquisition
├── parser.py                 # PDF text extraction
├── grobid_client.py          # GROBID integration
├── section_extractor.py      # Section identification
├── reference_parser.py       # Citation extraction
├── figure_extractor.py       # Figure/table extraction
├── quality_assessor.py       # Extraction quality metrics
└── exceptions.py             # Custom exceptions
```

---

## Strategy: Multi-Method PDF Parsing

### Parsing Methods (Priority Order)

1. **GROBID** (Preferred) - Best quality for scientific PDFs
   - Extracts structured sections
   - High accuracy for references
   - Handles figures/tables metadata
   - Quality: 90-95%

2. **PMC XML** (When available) - Perfect quality
   - Already structured
   - No parsing errors
   - Complete metadata
   - Quality: 100%

3. **pdfminer.six** - Good fallback
   - Layout analysis
   - Better than PyPDF2
   - Quality: 70-80%

4. **PyPDF2** - Last resort
   - Simple text extraction
   - Fast but lossy
   - Quality: 50-60%

---

## Data Models

### PDF Models (`models.py`)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class PDFSource(str, Enum):
    """PDF acquisition source."""
    PMC = "pmc"
    UNPAYWALL = "unpaywall"
    PUBLISHER = "publisher"
    PREPRINT_SERVER = "preprint_server"
    UNKNOWN = "unknown"


class ParsingMethod(str, Enum):
    """PDF parsing method used."""
    GROBID = "grobid"
    PMC_XML = "pmc_xml"
    PDFMINER = "pdfminer"
    PYPDF2 = "pypdf2"


class SectionType(str, Enum):
    """Article section types."""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    MATERIALS_METHODS = "materials_and_methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    ACKNOWLEDGMENTS = "acknowledgments"
    SUPPLEMENTARY = "supplementary"
    OTHER = "other"


@dataclass
class PDFMetadata:
    """Metadata about a PDF file."""
    
    # Identifiers
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    
    # File info
    file_path: Optional[Path] = None
    file_size_bytes: int = 0
    file_hash: Optional[str] = None  # MD5/SHA256
    
    # Source
    source: PDFSource = PDFSource.UNKNOWN
    download_url: Optional[str] = None
    
    # Status
    downloaded_at: Optional[datetime] = None
    is_open_access: bool = False
    
    # Quality indicators
    page_count: int = 0
    is_scanned: bool = False  # Image-based PDF
    ocr_required: bool = False


@dataclass
class Figure:
    """Figure or image from PDF."""
    
    figure_id: str
    caption: str = ""
    page_number: int = 0
    coordinates: Optional[Dict[str, float]] = None  # x, y, width, height
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None  # png, jpg, etc.
    graphic_ref: Optional[str] = None  # Reference in text


@dataclass
class Table:
    """Table from PDF."""
    
    table_id: str
    caption: str = ""
    page_number: int = 0
    coordinates: Optional[Dict[str, float]] = None
    content: Optional[List[List[str]]] = None  # 2D array
    html: Optional[str] = None  # HTML representation


@dataclass
class Section:
    """Document section."""
    
    section_type: SectionType
    title: str = ""
    content: str = ""
    level: int = 1  # Heading level
    subsections: List['Section'] = field(default_factory=list)


@dataclass
class Citation:
    """Parsed citation/reference."""
    
    citation_id: str
    raw_text: str
    
    # Parsed fields
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    
    # Parsing metadata
    parsing_confidence: float = 0.0


@dataclass
class ParsedPDF:
    """Complete parsed PDF document."""
    
    # Metadata
    metadata: PDFMetadata
    
    # Content
    full_text: str = ""
    sections: List[Section] = field(default_factory=list)
    
    # Structured elements
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    
    # Parsing metadata
    parsing_method: ParsingMethod = ParsingMethod.PYPDF2
    parsed_at: datetime = field(default_factory=datetime.now)
    parsing_time: float = 0.0
    quality_score: float = 0.0  # 0-1
    
    # Raw data
    raw_xml: Optional[str] = None  # GROBID/PMC XML
    raw_json: Optional[Dict[str, Any]] = None


@dataclass
class ExtractionQuality:
    """Quality metrics for extraction."""
    
    overall_score: float  # 0-1
    
    # Component scores
    text_quality: float = 0.0
    section_detection: float = 0.0
    reference_parsing: float = 0.0
    figure_detection: float = 0.0
    
    # Indicators
    has_complete_sections: bool = False
    has_parsed_references: bool = False
    has_figures: bool = False
    has_tables: bool = False
    
    # Issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
```

---

## PDF Downloader (`downloader.py`)

### Implementation

```python
import aiohttp
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import PDFMetadata, PDFSource
from .exceptions import PDFDownloadError, PDFNotAvailableError


logger = logging.getLogger(__name__)


class PDFDownloader:
    """
    Download PDFs from various sources.
    
    Tries multiple sources in priority order:
    1. PubMed Central (PMC) - Best quality, always OA
    2. Unpaywall - OA copies from publishers/repositories
    3. Preprint servers - bioRxiv, medRxiv
    4. Publisher (if URL provided)
    """
    
    PMC_FTP = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
    UNPAYWALL_API = "https://api.unpaywall.org/v2/{doi}?email={email}"
    
    def __init__(
        self,
        storage_dir: Path,
        email: str,
        max_size_mb: int = 50,
    ):
        """
        Initialize PDF downloader.
        
        Args:
            storage_dir: Directory to store downloaded PDFs
            email: Email for Unpaywall API
            max_size_mb: Maximum PDF size to download
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.email = email
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def download(
        self,
        pmid: Optional[str] = None,
        pmcid: Optional[str] = None,
        doi: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[PDFMetadata]:
        """
        Download PDF from best available source.
        
        Args:
            pmid: PubMed ID
            pmcid: PubMed Central ID
            doi: DOI
            url: Direct URL to PDF
        
        Returns:
            PDF metadata with file path, or None if not available
        
        Raises:
            PDFDownloadError: If download fails after retries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Try PMC first (best quality)
        if pmcid:
            logger.info(f"Attempting PMC download: {pmcid}")
            if pdf_meta := await self._download_from_pmc(pmcid):
                return pdf_meta
        
        # Try Unpaywall (OA copies)
        if doi:
            logger.info(f"Attempting Unpaywall download: {doi}")
            if pdf_meta := await self._download_from_unpaywall(doi):
                return pdf_meta
        
        # Try direct URL
        if url:
            logger.info(f"Attempting direct download: {url}")
            if pdf_meta := await self._download_from_url(url):
                return pdf_meta
        
        logger.warning(f"PDF not available for: PMID={pmid}, DOI={doi}")
        return None
    
    async def _download_from_pmc(self, pmcid: str) -> Optional[PDFMetadata]:
        """Download PDF from PubMed Central."""
        # Ensure PMC prefix
        if not pmcid.startswith("PMC"):
            pmcid = f"PMC{pmcid}"
        
        url = self.PMC_FTP.format(pmcid=pmcid)
        
        try:
            pdf_data = await self._fetch_pdf(url)
            if not pdf_data:
                return None
            
            # Save to disk
            file_path = self.storage_dir / f"{pmcid}.pdf"
            file_path.write_bytes(pdf_data)
            
            return PDFMetadata(
                pmcid=pmcid,
                file_path=file_path,
                file_size_bytes=len(pdf_data),
                file_hash=hashlib.md5(pdf_data).hexdigest(),
                source=PDFSource.PMC,
                download_url=url,
                is_open_access=True,
            )
            
        except Exception as e:
            logger.warning(f"PMC download failed for {pmcid}: {e}")
            return None
    
    async def _download_from_unpaywall(self, doi: str) -> Optional[PDFMetadata]:
        """Download PDF via Unpaywall (OA aggregator)."""
        url = self.UNPAYWALL_API.format(doi=doi, email=self.email)
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Check if OA available
                if not data.get("is_oa"):
                    logger.info(f"No OA version available for {doi}")
                    return None
                
                # Get best OA location
                best_oa = data.get("best_oa_location")
                if not best_oa or not best_oa.get("url_for_pdf"):
                    return None
                
                pdf_url = best_oa["url_for_pdf"]
                
                # Download PDF
                pdf_data = await self._fetch_pdf(pdf_url)
                if not pdf_data:
                    return None
                
                # Save to disk
                safe_doi = doi.replace("/", "_")
                file_path = self.storage_dir / f"{safe_doi}.pdf"
                file_path.write_bytes(pdf_data)
                
                return PDFMetadata(
                    doi=doi,
                    file_path=file_path,
                    file_size_bytes=len(pdf_data),
                    file_hash=hashlib.md5(pdf_data).hexdigest(),
                    source=PDFSource.UNPAYWALL,
                    download_url=pdf_url,
                    is_open_access=True,
                )
                
        except Exception as e:
            logger.warning(f"Unpaywall download failed for {doi}: {e}")
            return None
    
    async def _download_from_url(self, url: str) -> Optional[PDFMetadata]:
        """Download PDF from direct URL."""
        try:
            pdf_data = await self._fetch_pdf(url)
            if not pdf_data:
                return None
            
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
            file_path = self.storage_dir / f"pdf_{url_hash}.pdf"
            file_path.write_bytes(pdf_data)
            
            return PDFMetadata(
                file_path=file_path,
                file_size_bytes=len(pdf_data),
                file_hash=hashlib.md5(pdf_data).hexdigest(),
                source=PDFSource.PUBLISHER,
                download_url=url,
            )
            
        except Exception as e:
            logger.warning(f"Direct download failed for {url}: {e}")
            return None
    
    async def _fetch_pdf(self, url: str) -> Optional[bytes]:
        """Fetch PDF data from URL."""
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None
                
                # Check size
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_size_bytes:
                    logger.warning(f"PDF too large: {content_length} bytes")
                    return None
                
                # Check content type
                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower():
                    logger.warning(f"Not a PDF: {content_type}")
                    return None
                
                pdf_data = await response.read()
                
                # Verify it's actually a PDF
                if not pdf_data.startswith(b"%PDF"):
                    logger.warning("Invalid PDF signature")
                    return None
                
                return pdf_data
                
        except Exception as e:
            logger.error(f"Failed to fetch PDF from {url}: {e}")
            return None
    
    async def check_availability(
        self,
        pmid: Optional[str] = None,
        pmcid: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Check PDF availability without downloading.
        
        Returns:
            Dict with availability status for each source
        """
        availability = {
            "pmc": False,
            "unpaywall": False,
            "any": False,
        }
        
        # Check PMC
        if pmcid:
            pmcid = pmcid if pmcid.startswith("PMC") else f"PMC{pmcid}"
            url = self.PMC_FTP.format(pmcid=pmcid)
            try:
                async with self.session.head(url) as response:
                    availability["pmc"] = response.status == 200
            except:
                pass
        
        # Check Unpaywall
        if doi:
            url = self.UNPAYWALL_API.format(doi=doi, email=self.email)
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        availability["unpaywall"] = data.get("is_oa", False)
            except:
                pass
        
        availability["any"] = any([
            availability["pmc"],
            availability["unpaywall"],
        ])
        
        return availability
```

---

## GROBID Integration (`grobid_client.py`)

### Implementation

```python
import aiohttp
import logging
from typing import Optional
from pathlib import Path

from .models import ParsedPDF, ParsingMethod, Section, Citation, Figure, Table
from .exceptions import GROBIDError


logger = logging.getLogger(__name__)


class GROBIDClient:
    """
    Client for GROBID (GeneRation Of BIbliographic Data) service.
    
    GROBID is a machine learning library for extracting,
    parsing and restructuring raw documents (especially PDFs).
    
    Best quality for scientific PDFs.
    
    Setup:
    1. Self-host: https://grobid.readthedocs.io/
    2. Docker: grobid/grobid:0.7.3
    3. API endpoint: http://localhost:8070
    """
    
    def __init__(self, base_url: str = "http://localhost:8070"):
        """
        Initialize GROBID client.
        
        Args:
            base_url: GROBID service URL
        """
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def parse_pdf(
        self,
        pdf_path: Path,
    ) -> ParsedPDF:
        """
        Parse PDF using GROBID.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Parsed PDF with sections, references, etc.
        
        Raises:
            GROBIDError: If parsing fails
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/processFulltextDocument"
        
        try:
            # Read PDF
            pdf_data = pdf_path.read_bytes()
            
            # Send to GROBID
            data = aiohttp.FormData()
            data.add_field(
                "input",
                pdf_data,
                filename=pdf_path.name,
                content_type="application/pdf",
            )
            data.add_field("consolidateHeader", "1")
            data.add_field("consolidateCitations", "1")
            data.add_field("includeRawCitations", "1")
            
            async with self.session.post(url, data=data, timeout=60) as response:
                if response.status != 200:
                    raise GROBIDError(f"GROBID returned {response.status}")
                
                tei_xml = await response.text()
            
            # Parse TEI XML
            parsed_pdf = self._parse_tei_xml(tei_xml, pdf_path)
            parsed_pdf.parsing_method = ParsingMethod.GROBID
            
            return parsed_pdf
            
        except Exception as e:
            logger.error(f"GROBID parsing failed: {e}")
            raise GROBIDError(f"GROBID parsing failed: {e}") from e
    
    def _parse_tei_xml(
        self,
        tei_xml: str,
        pdf_path: Path,
    ) -> ParsedPDF:
        """Parse GROBID TEI XML output."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(tei_xml, "xml")
        
        # Extract full text
        body = soup.find("body")
        full_text = body.get_text(separator="\n") if body else ""
        
        # Extract sections
        sections = self._extract_sections(soup)
        
        # Extract citations/references
        citations = self._extract_citations(soup)
        
        # Extract figures
        figures = self._extract_figures(soup)
        
        return ParsedPDF(
            metadata=PDFMetadata(file_path=pdf_path),
            full_text=full_text,
            sections=sections,
            citations=citations,
            figures=figures,
            raw_xml=tei_xml,
        )
    
    def _extract_sections(self, soup) -> List[Section]:
        """Extract sections from TEI XML."""
        sections = []
        
        # Find all div elements with type attribute
        for div in soup.find_all("div"):
            section_type = div.get("type", "other")
            head = div.find("head")
            title = head.get_text() if head else ""
            
            # Get section text
            paragraphs = div.find_all("p")
            content = "\n\n".join(p.get_text() for p in paragraphs)
            
            section = Section(
                section_type=self._map_section_type(section_type),
                title=title,
                content=content,
            )
            sections.append(section)
        
        return sections
    
    def _extract_citations(self, soup) -> List[Citation]:
        """Extract citations from TEI XML."""
        citations = []
        
        # Find bibliography
        bib_struct = soup.find_all("biblStruct")
        
        for idx, bib in enumerate(bib_struct, 1):
            citation = Citation(
                citation_id=f"ref{idx}",
                raw_text=bib.get_text(),
            )
            
            # Extract structured fields
            if title := bib.find("title"):
                citation.title = title.get_text()
            
            if date := bib.find("date"):
                try:
                    citation.year = int(date.get("when", "").split("-")[0])
                except:
                    pass
            
            # Extract authors
            authors = []
            for author in bib.find_all("author"):
                if persname := author.find("persName"):
                    surname = persname.find("surname")
                    forename = persname.find("forename")
                    if surname:
                        name = surname.get_text()
                        if forename:
                            name = f"{forename.get_text()} {name}"
                        authors.append(name)
            citation.authors = authors
            
            citations.append(citation)
        
        return citations
    
    def _extract_figures(self, soup) -> List[Figure]:
        """Extract figure metadata from TEI XML."""
        figures = []
        
        for idx, fig in enumerate(soup.find_all("figure"), 1):
            figure = Figure(
                figure_id=fig.get("xml:id", f"fig{idx}"),
            )
            
            # Extract caption
            if head := fig.find("head"):
                figure.caption = head.get_text()
            
            # Extract graphic reference
            if graphic := fig.find("graphic"):
                figure.graphic_ref = graphic.get("url")
            
            figures.append(figure)
        
        return figures
    
    @staticmethod
    def _map_section_type(grobid_type: str) -> SectionType:
        """Map GROBID section type to our enum."""
        mapping = {
            "abstract": SectionType.ABSTRACT,
            "introduction": SectionType.INTRODUCTION,
            "methods": SectionType.METHODS,
            "results": SectionType.RESULTS,
            "discussion": SectionType.DISCUSSION,
            "conclusion": SectionType.CONCLUSION,
            "references": SectionType.REFERENCES,
            "acknowledgments": SectionType.ACKNOWLEDGMENTS,
        }
        return mapping.get(grobid_type.lower(), SectionType.OTHER)
```

---

## Testing

```python
# tests/unit/lib/pdf/test_downloader.py

import pytest
from pathlib import Path
from omics_oracle_v2.lib.pdf import PDFDownloader


@pytest.mark.asyncio
async def test_download_from_pmc():
    """Test downloading PDF from PMC."""
    downloader = PDFDownloader(
        storage_dir=Path("tests/data/pdfs"),
        email="test@example.com",
    )
    
    async with downloader:
        # Use known OA article
        metadata = await downloader.download(pmcid="PMC5536800")
        
        assert metadata is not None
        assert metadata.file_path.exists()
        assert metadata.file_size_bytes > 0
        assert metadata.source == PDFSource.PMC


@pytest.mark.asyncio
async def test_grobid_parsing():
    """Test GROBID PDF parsing."""
    client = GROBIDClient(base_url="http://localhost:8070")
    
    pdf_path = Path("tests/data/sample.pdf")
    parsed = await client.parse_pdf(pdf_path)
    
    assert parsed.full_text
    assert len(parsed.sections) > 0
    assert len(parsed.citations) > 0
    assert parsed.parsing_method == ParsingMethod.GROBID
```

---

## Deployment

### GROBID Setup (Docker)

```bash
# Pull and run GROBID service
docker run -d \\
  --name grobid \\
  -p 8070:8070 \\
  -v /path/to/grobid-home:/opt/grobid/grobid-home \\
  grobid/grobid:0.7.3

# Health check
curl http://localhost:8070/api/isalive
```

### Configuration

```yaml
# config/production.yml

pdf:
  downloader:
    storage_dir: "data/publications/pdfs"
    email: "your-email@example.com"
    max_size_mb: 50
  
  grobid:
    base_url: "http://grobid:8070"
    timeout: 60
  
  cache:
    enabled: true
    ttl_days: 30
```

---

## Performance

| Operation | Target | Notes |
|-----------|--------|-------|
| Download (PMC) | < 5s | Typical 2-5MB PDF |
| Download (Unpaywall) | < 10s | Varies by source |
| GROBID parsing | < 30s | 10-20 pages |
| pdfminer parsing | < 10s | Fallback |
| Section extraction | < 5s | After parsing |

---

## Next Steps

1. ✅ Set up GROBID service
2. ⏭️ Implement PDF downloader
3. ⏭️ Integrate GROBID client
4. ⏭️ Add fallback parsers
5. ⏭️ Quality assessment
6. ⏭️ Integration tests

---

**Status:** ✅ Specification Complete  
**Ready for:** Phase 2 Implementation
