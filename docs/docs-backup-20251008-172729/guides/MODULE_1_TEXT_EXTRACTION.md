# 📄 Module 1: Full-Text Publication Extraction System

**Date**: December 28, 2024
**Module**: Text Extraction & Processing
**Priority**: High - Foundation for Advanced Analysis
**Estimated Timeline**: 6-8 weeks

---

## 🎯 **Module Overview**

The Full-Text Publication Extraction System is designed to automatically retrieve, process, and structure full-text content from biomedical publications associated with GEO datasets. This module serves as the foundation for advanced text analysis, statistical extraction, and publication relationship discovery.

### **Core Objectives**

1. **Comprehensive Text Retrieval**: Extract full-text content from multiple sources
2. **Quality Assurance**: Validate and score extraction quality
3. **Structured Processing**: Parse content into meaningful sections
4. **Scalable Architecture**: Handle thousands of publications efficiently
5. **Integration Ready**: Seamless integration with other OmicsOracle modules

---

## 🏗️ **System Architecture**

### **Component Structure**

```
src/omics_oracle/text_extraction/
├── __init__.py
├── orchestrator.py           # Main extraction orchestrator
├── sources/                  # Text source handlers
│   ├── __init__.py
│   ├── pubmed_central.py     # PMC full-text extraction
│   ├── doi_resolver.py       # DOI-based resolution
│   ├── pdf_processor.py      # PDF text extraction
│   ├── web_scraper.py        # Publisher website scraping
│   └── arxiv_processor.py    # arXiv preprint handling
├── processors/               # Content processing
│   ├── __init__.py
│   ├── text_cleaner.py       # Text cleaning and normalization
│   ├── section_parser.py     # Section identification
│   ├── figure_extractor.py   # Figure and caption extraction
│   ├── table_extractor.py    # Table extraction and parsing
│   └── reference_parser.py   # Citation and reference parsing
├── quality/                  # Quality assessment
│   ├── __init__.py
│   ├── validator.py          # Content validation
│   ├── scorer.py             # Quality scoring
│   └── metrics.py            # Quality metrics calculation
├── storage/                  # Storage management
│   ├── __init__.py
│   ├── manager.py            # Storage orchestration
│   ├── cache.py              # Caching layer
│   └── database.py           # Database operations
└── models/                   # Data models
    ├── __init__.py
    ├── publication.py        # Publication data models
    ├── content.py            # Content structure models
    └── extraction.py         # Extraction metadata models
```

---

## 🔧 **Core Components Implementation**

### **1. Text Source Handlers**

**PubMed Central (PMC) Handler**:
```python
# src/omics_oracle/text_extraction/sources/pubmed_central.py

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from ..models.content import FullTextContent
from ..models.extraction import ExtractionResult

class PMCExtractor:
    """Extract full-text content from PubMed Central"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = api_key
        self.rate_limit = 3 if api_key else 1  # requests per second
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def extract_by_pmcid(self, pmc_id: str) -> ExtractionResult:
        """Extract full text using PMC ID"""
        try:
            # Get PMC full-text XML
            xml_content = await self._fetch_pmc_xml(pmc_id)

            # Parse XML content
            parsed_content = await self._parse_pmc_xml(xml_content)

            # Create extraction result
            return ExtractionResult(
                source="pmc",
                success=True,
                content=parsed_content,
                extraction_method="pmc_api",
                confidence_score=0.95,
                processing_time=0.0,
                metadata={
                    "pmc_id": pmc_id,
                    "xml_size": len(xml_content),
                    "section_count": len(parsed_content.sections)
                }
            )

        except Exception as e:
            return ExtractionResult(
                source="pmc",
                success=False,
                error=str(e),
                extraction_method="pmc_api",
                confidence_score=0.0
            )

    async def _fetch_pmc_xml(self, pmc_id: str) -> str:
        """Fetch PMC XML content"""
        url = f"{self.base_url}efetch.fcgi"
        params = {
            "db": "pmc",
            "id": pmc_id,
            "retmode": "xml",
            "rettype": "full"
        }

        if self.api_key:
            params["api_key"] = self.api_key

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.text()

    async def _parse_pmc_xml(self, xml_content: str) -> FullTextContent:
        """Parse PMC XML into structured content"""
        from xml.etree import ElementTree as ET

        root = ET.fromstring(xml_content)

        # Extract basic metadata
        title = self._extract_title(root)
        abstract = self._extract_abstract(root)

        # Extract main sections
        sections = self._extract_sections(root)

        # Extract figures and tables
        figures = self._extract_figures(root)
        tables = self._extract_tables(root)

        # Extract references
        references = self._extract_references(root)

        return FullTextContent(
            title=title,
            abstract=abstract,
            sections=sections,
            figures=figures,
            tables=tables,
            references=references,
            full_text=self._combine_sections(sections),
            word_count=self._calculate_word_count(sections)
        )
```

**PDF Processor**:
```python
# src/omics_oracle/text_extraction/sources/pdf_processor.py

import asyncio
import aiofiles
from typing import List, Optional, Dict, Any
import fitz  # PyMuPDF
import pdfplumber
from tika import parser as tika_parser
from ..models.content import FullTextContent
from ..models.extraction import ExtractionResult

class PDFProcessor:
    """Multi-strategy PDF text extraction"""

    def __init__(self):
        self.extractors = [
            self._extract_with_pymupdf,
            self._extract_with_pdfplumber,
            self._extract_with_tika
        ]

    async def extract_from_url(self, pdf_url: str) -> ExtractionResult:
        """Extract text from PDF URL"""
        try:
            # Download PDF
            pdf_content = await self._download_pdf(pdf_url)

            # Try multiple extraction methods
            best_result = None
            best_score = 0.0

            for extractor in self.extractors:
                try:
                    result = await extractor(pdf_content)
                    score = self._calculate_extraction_quality(result)

                    if score > best_score:
                        best_result = result
                        best_score = score

                except Exception as e:
                    continue

            if best_result:
                return ExtractionResult(
                    source="pdf",
                    success=True,
                    content=best_result,
                    extraction_method=f"pdf_multi_strategy",
                    confidence_score=best_score,
                    metadata={
                        "pdf_url": pdf_url,
                        "pdf_size": len(pdf_content),
                        "extraction_quality": best_score
                    }
                )
            else:
                raise Exception("All PDF extraction methods failed")

        except Exception as e:
            return ExtractionResult(
                source="pdf",
                success=False,
                error=str(e),
                extraction_method="pdf_multi_strategy",
                confidence_score=0.0
            )

    async def _extract_with_pymupdf(self, pdf_content: bytes) -> FullTextContent:
        """Extract using PyMuPDF"""
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        sections = {}
        figures = []
        tables = []

        full_text = ""
        for page_num in range(doc.page_count):
            page = doc[page_num]

            # Extract text
            text = page.get_text()
            full_text += text + "\n"

            # Extract images (figures)
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                figures.append({
                    "page": page_num + 1,
                    "index": img_index,
                    "bbox": img[:4] if len(img) >= 4 else None
                })

        doc.close()

        # Parse sections from full text
        sections = self._parse_sections_from_text(full_text)

        return FullTextContent(
            title=self._extract_title_from_text(full_text),
            abstract=sections.get("abstract", ""),
            sections=sections,
            figures=figures,
            tables=tables,
            full_text=full_text,
            word_count=len(full_text.split())
        )

    def _calculate_extraction_quality(self, content: FullTextContent) -> float:
        """Calculate extraction quality score"""
        score = 0.0

        # Text length score (0-0.3)
        text_length = len(content.full_text)
        if text_length > 10000:
            score += 0.3
        elif text_length > 5000:
            score += 0.2
        elif text_length > 1000:
            score += 0.1

        # Section structure score (0-0.3)
        section_count = len(content.sections)
        if section_count >= 5:
            score += 0.3
        elif section_count >= 3:
            score += 0.2
        elif section_count >= 1:
            score += 0.1

        # Content quality score (0-0.4)
        if content.abstract and len(content.abstract) > 100:
            score += 0.1
        if any("method" in section.lower() for section in content.sections.keys()):
            score += 0.1
        if any("result" in section.lower() for section in content.sections.keys()):
            score += 0.1
        if any("conclusion" in section.lower() for section in content.sections.keys()):
            score += 0.1

        return min(score, 1.0)
```

---

## 📊 **Data Models**

### **Core Data Structures**

```python
# src/omics_oracle/text_extraction/models/content.py

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class Figure:
    """Represents a figure in a publication"""
    id: str
    caption: str
    page_number: Optional[int] = None
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2]
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    figure_type: Optional[str] = None  # plot, diagram, photo, etc.

@dataclass
class Table:
    """Represents a table in a publication"""
    id: str
    caption: str
    headers: List[str]
    rows: List[List[str]]
    page_number: Optional[int] = None
    bbox: Optional[List[float]] = None
    table_type: Optional[str] = None  # data, summary, comparison, etc.

@dataclass
class Reference:
    """Represents a citation/reference"""
    id: str
    authors: List[str]
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None

@dataclass
class FullTextContent:
    """Complete extracted text content"""
    title: str
    abstract: str
    sections: Dict[str, str]  # section_name -> content
    figures: List[Figure]
    tables: List[Table]
    references: List[Reference]
    full_text: str
    word_count: int

    # Metadata
    authors: List[str] = None
    journal: str = None
    publication_date: Optional[datetime] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc_id: Optional[str] = None

    # Processing metadata
    extraction_timestamp: datetime = None
    processing_notes: List[str] = None

@dataclass
class ExtractionResult:
    """Result of text extraction attempt"""
    source: str  # pmc, pdf, web, etc.
    success: bool
    content: Optional[FullTextContent] = None
    error: Optional[str] = None
    extraction_method: str = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.extraction_timestamp is None:
            self.extraction_timestamp = datetime.utcnow()
```

---

## ⚙️ **Processing Pipeline**

### **Extraction Orchestrator**

```python
# src/omics_oracle/text_extraction/orchestrator.py

import asyncio
from typing import List, Optional, Dict, Any
from .sources.pubmed_central import PMCExtractor
from .sources.pdf_processor import PDFProcessor
from .sources.doi_resolver import DOIResolver
from .sources.web_scraper import WebScraper
from .models.content import FullTextContent
from .models.extraction import ExtractionResult
from .quality.validator import ContentValidator
from .storage.manager import StorageManager

class TextExtractionOrchestrator:
    """Main orchestrator for text extraction"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pmc_extractor = PMCExtractor(config.get("ncbi_api_key"))
        self.pdf_processor = PDFProcessor()
        self.doi_resolver = DOIResolver()
        self.web_scraper = WebScraper()
        self.validator = ContentValidator()
        self.storage = StorageManager(config.get("storage"))

        # Extraction strategies in order of preference
        self.strategies = [
            self._extract_from_pmc,
            self._extract_from_doi,
            self._extract_from_pdf,
            self._extract_from_web
        ]

    async def extract_publication_text(self,
                                     publication_id: str,
                                     pmid: Optional[str] = None,
                                     pmc_id: Optional[str] = None,
                                     doi: Optional[str] = None,
                                     pdf_url: Optional[str] = None) -> ExtractionResult:
        """Extract full text for a publication using multiple strategies"""

        # Check if already extracted and cached
        cached_result = await self.storage.get_cached_extraction(publication_id)
        if cached_result and cached_result.confidence_score > 0.8:
            return cached_result

        # Try extraction strategies
        best_result = None
        best_score = 0.0

        extraction_context = {
            "publication_id": publication_id,
            "pmid": pmid,
            "pmc_id": pmc_id,
            "doi": doi,
            "pdf_url": pdf_url
        }

        for strategy in self.strategies:
            try:
                result = await strategy(extraction_context)

                if result.success:
                    # Validate content quality
                    validation_score = await self.validator.validate_content(result.content)
                    result.confidence_score = min(result.confidence_score, validation_score)

                    if result.confidence_score > best_score:
                        best_result = result
                        best_score = result.confidence_score

                    # If we have high-quality result, stop trying
                    if result.confidence_score > 0.9:
                        break

            except Exception as e:
                self.logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue

        # Store result in cache
        if best_result:
            await self.storage.cache_extraction_result(publication_id, best_result)

        return best_result or ExtractionResult(
            source="none",
            success=False,
            error="All extraction strategies failed",
            confidence_score=0.0
        )

    async def _extract_from_pmc(self, context: Dict[str, Any]) -> ExtractionResult:
        """Extract using PMC API"""
        pmc_id = context.get("pmc_id")
        if not pmc_id:
            # Try to resolve PMC ID from PMID
            pmid = context.get("pmid")
            if pmid:
                pmc_id = await self.doi_resolver.pmid_to_pmc(pmid)

        if pmc_id:
            async with self.pmc_extractor as extractor:
                return await extractor.extract_by_pmcid(pmc_id)

        raise Exception("No PMC ID available")

    async def _extract_from_pdf(self, context: Dict[str, Any]) -> ExtractionResult:
        """Extract from PDF"""
        pdf_url = context.get("pdf_url")
        if not pdf_url:
            # Try to resolve PDF URL from DOI
            doi = context.get("doi")
            if doi:
                pdf_url = await self.doi_resolver.resolve_pdf_url(doi)

        if pdf_url:
            return await self.pdf_processor.extract_from_url(pdf_url)

        raise Exception("No PDF URL available")

    async def batch_extract(self,
                          publications: List[Dict[str, Any]],
                          max_concurrent: int = 5) -> List[ExtractionResult]:
        """Extract text from multiple publications concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(pub_data):
            async with semaphore:
                return await self.extract_publication_text(**pub_data)

        tasks = [extract_single(pub) for pub in publications]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ExtractionResult(
                    source="batch",
                    success=False,
                    error=str(result),
                    confidence_score=0.0,
                    metadata={"publication_index": i}
                ))
            else:
                processed_results.append(result)

        return processed_results
```

---

## 🎯 **Implementation Timeline**

### **Phase 1: Foundation (Weeks 1-2)**

**Week 1: Core Infrastructure**
- [ ] Set up module structure and base classes
- [ ] Implement PMC API integration
- [ ] Create basic data models
- [ ] Set up storage layer

**Week 2: PDF Processing**
- [ ] Implement multi-strategy PDF extraction
- [ ] Add quality assessment framework
- [ ] Create extraction validation system
- [ ] Basic error handling and logging

### **Phase 2: Enhancement (Weeks 3-4)**

**Week 3: Advanced Features**
- [ ] DOI resolution system
- [ ] Web scraping capabilities
- [ ] Section parsing and structure detection
- [ ] Figure and table extraction

**Week 4: Quality & Performance**
- [ ] Advanced quality scoring
- [ ] Caching and optimization
- [ ] Batch processing capabilities
- [ ] Performance monitoring

### **Phase 3: Integration (Weeks 5-6)**

**Week 5: System Integration**
- [ ] Integration with existing GEO system
- [ ] API endpoints for text retrieval
- [ ] Background task processing
- [ ] Error recovery mechanisms

**Week 6: Testing & Optimization**
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Production deployment preparation

---

## 📋 **Success Metrics**

### **Technical Metrics**
- **Extraction Success Rate**: 95%+ for PMC articles, 80%+ for PDFs
- **Processing Speed**: <30 seconds average per publication
- **Quality Score**: 90%+ of extractions score >0.7 quality
- **Cache Hit Rate**: 85%+ for repeat requests

### **Content Quality Metrics**
- **Section Detection**: 90%+ accuracy for major sections
- **Text Completeness**: 95%+ of original text preserved
- **Structure Preservation**: 85%+ of formatting maintained
- **Reference Extraction**: 90%+ of citations captured

### **System Performance Metrics**
- **Throughput**: 100+ publications per hour
- **Memory Usage**: <2GB per extraction worker
- **Error Rate**: <5% system errors
- **Availability**: 99.9% uptime

---

## 🔗 **Integration Points**

### **With Other OmicsOracle Modules**

1. **GEO Tools**: Receive publication metadata from GEO datasets
2. **NLP Processing**: Provide full text for analysis and summarization
3. **Publication Discovery**: Supply content for citation analysis
4. **Statistics Extraction**: Provide structured text for statistical parsing
5. **Visualization**: Feed extracted content to dashboard components

### **External Dependencies**

1. **NCBI APIs**: PubMed Central, E-utilities
2. **Publisher APIs**: Crossref, DOI resolution services
3. **PDF Processing**: PyMuPDF, PDFPlumber, Apache Tika
4. **Storage**: SQLite, file system, optional cloud storage
5. **Caching**: Redis (optional), in-memory caching

---

This detailed specification provides the foundation for implementing the Full-Text Publication Extraction System. The modular design ensures scalability and maintainability while providing high-quality text extraction capabilities essential for advanced biomedical research analysis.
