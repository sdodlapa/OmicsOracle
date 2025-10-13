"""
PDF content extractor for scientific articles.

This module extracts structured content from PDF files using multiple libraries:
- camelot-py: High-accuracy table extraction (99-100%)
- PyMuPDF (fitz): Fast text and image extraction
- pdfplumber: Fallback for simple tables

Example:
    >>> from lib.fulltext.pdf_extractor import PDFExtractor
    >>>
    >>> extractor = PDFExtractor()
    >>> content = extractor.extract_structured_content("paper.pdf")
    >>> print(f"Found {len(content.tables)} tables")
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.fulltext.models import Figure, FullTextContent, Section, Table

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract structured content from PDF files.

    Uses multiple libraries for best results:
    - camelot-py: Table extraction (stream + lattice methods)
    - PyMuPDF (fitz): Text and image extraction
    - pdfplumber: Simple table fallback

    Priority for tables:
    1. camelot stream (borderless tables, 99-100% accuracy)
    2. camelot lattice (bordered tables, 99-100% accuracy)
    3. pdfplumber (simple tables, 60-80% accuracy)
    """

    def __init__(self):
        """Initialize PDF extractor with library availability checks."""
        # Check camelot availability
        try:
            import camelot

            self.camelot_available = True
            self.camelot = camelot
            logger.debug("camelot-py available for table extraction")
        except ImportError:
            self.camelot_available = False
            self.camelot = None
            logger.warning("camelot-py not available - table extraction limited")

        # Check PyMuPDF availability
        try:
            import fitz

            self.pymupdf_available = True
            self.fitz = fitz
            logger.debug("PyMuPDF available for text/image extraction")
        except ImportError:
            self.pymupdf_available = False
            self.fitz = None
            logger.warning("PyMuPDF not available - text/image extraction disabled")

        # Check pdfplumber availability
        try:
            import pdfplumber

            self.pdfplumber_available = True
            self.pdfplumber = pdfplumber
            logger.debug("pdfplumber available as fallback")
        except ImportError:
            self.pdfplumber_available = False
            self.pdfplumber = None
            logger.warning("pdfplumber not available")

        logger.info("PDFExtractor initialized")

    def extract_tables(
        self,
        pdf_path: Path,
        method: str = "auto",
        pages: str = "all",
    ) -> List[Table]:
        """
        Extract tables from PDF using best available method.

        Args:
            pdf_path: Path to PDF file
            method: Extraction method ('auto', 'stream', 'lattice', 'pdfplumber')
            pages: Pages to process ('all', '1', '1-3', etc.)

        Returns:
            List of Table objects with structured data
        """
        if not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return []

        tables = []

        # Try camelot stream first (best for borderless tables)
        if self.camelot_available and method in ["auto", "stream"]:
            try:
                logger.debug(f"Trying camelot stream on {pdf_path.name}")
                camelot_tables = self.camelot.read_pdf(
                    str(pdf_path), flavor="stream", pages=pages, suppress_stdout=True
                )

                if camelot_tables and len(camelot_tables) > 0:
                    tables.extend(self._convert_camelot_tables(camelot_tables, "stream"))
                    logger.info(f"Camelot stream: Found {len(camelot_tables)} tables in {pdf_path.name}")
                    return tables  # Success, stop here

            except Exception as e:
                logger.debug(f"Camelot stream failed: {e}")

        # Try camelot lattice (best for bordered tables)
        if not tables and self.camelot_available and method in ["auto", "lattice"]:
            try:
                logger.debug(f"Trying camelot lattice on {pdf_path.name}")
                camelot_tables = self.camelot.read_pdf(
                    str(pdf_path), flavor="lattice", pages=pages, suppress_stdout=True
                )

                if camelot_tables and len(camelot_tables) > 0:
                    tables.extend(self._convert_camelot_tables(camelot_tables, "lattice"))
                    logger.info(f"Camelot lattice: Found {len(camelot_tables)} tables in {pdf_path.name}")
                    return tables

            except Exception as e:
                logger.debug(f"Camelot lattice failed: {e}")

        # Fallback to pdfplumber
        if not tables and self.pdfplumber_available and method in ["auto", "pdfplumber"]:
            try:
                logger.debug(f"Trying pdfplumber on {pdf_path.name}")
                tables = self._extract_tables_pdfplumber(pdf_path, pages)

                if tables:
                    logger.info(f"pdfplumber: Found {len(tables)} tables in {pdf_path.name}")

            except Exception as e:
                logger.debug(f"pdfplumber failed: {e}")

        if not tables:
            logger.warning(f"No tables found in {pdf_path.name}")

        return tables

    def _convert_camelot_tables(self, camelot_tables, method: str) -> List[Table]:
        """
        Convert camelot TableList to our Table model.

        Args:
            camelot_tables: camelot.core.TableList object
            method: 'stream' or 'lattice'

        Returns:
            List of Table objects
        """
        tables = []

        for i, tbl in enumerate(camelot_tables):
            # Get table as pandas DataFrame
            df = tbl.df

            # Extract headers (first row)
            headers = df.iloc[0].tolist() if len(df) > 0 else []

            # Extract data rows (skip header row)
            rows = []
            for _, row in df.iloc[1:].iterrows():
                rows.append(row.tolist())

            # Create Table object
            table = Table(
                id=f"table_p{tbl.page}_{i+1}",
                label=f"Table {len(tables)+1}",
                caption="",  # PDFs don't have structured captions
                html_content=tbl.df.to_html(),
                table_columns=headers,
                table_values=rows,
            )

            # Add metadata
            table.metadata = {
                "page": tbl.page,
                "accuracy": tbl.accuracy,
                "method": method,
                "shape": tbl.shape,
            }

            tables.append(table)

        return tables

    def _extract_tables_pdfplumber(self, pdf_path: Path, pages: str = "all") -> List[Table]:
        """
        Extract tables using pdfplumber (fallback method).

        Args:
            pdf_path: Path to PDF file
            pages: Pages to process

        Returns:
            List of Table objects
        """
        tables = []

        try:
            with self.pdfplumber.open(str(pdf_path)) as pdf:
                # Parse pages parameter
                if pages == "all":
                    page_list = pdf.pages
                else:
                    # TODO: Parse '1-3' style ranges
                    page_list = pdf.pages

                for page_num, page in enumerate(page_list):
                    page_tables = page.extract_tables()

                    for i, tbl in enumerate(page_tables):
                        if not tbl or len(tbl) == 0:
                            continue

                        # First row is headers
                        headers = tbl[0] if len(tbl) > 0 else []
                        rows = tbl[1:] if len(tbl) > 1 else []

                        table = Table(
                            id=f"table_p{page_num+1}_{i+1}",
                            label=f"Table {len(tables)+1}",
                            caption="",
                            html_content="",
                            table_columns=headers,
                            table_values=rows,
                        )

                        table.metadata = {"page": page_num + 1, "method": "pdfplumber"}

                        tables.append(table)

        except Exception as e:
            logger.error(f"pdfplumber extraction error: {e}")

        return tables

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from PDF using PyMuPDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        if not self.pymupdf_available:
            logger.error("PyMuPDF not available for text extraction")
            return ""

        if not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return ""

        try:
            text_parts = []
            doc = self.fitz.open(str(pdf_path))

            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} chars from {len(text_parts)} pages in {pdf_path.name}")

            return full_text

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    def extract_images(self, pdf_path: Path, output_dir: Optional[Path] = None) -> List[Figure]:
        """
        Extract embedded images from PDF using PyMuPDF.

        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images

        Returns:
            List of Figure objects with image references
        """
        if not self.pymupdf_available:
            logger.error("PyMuPDF not available for image extraction")
            return []

        if not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return []

        figures = []

        try:
            doc = self.fitz.open(str(pdf_path))

            for page_num, page in enumerate(doc):
                images = page.get_images()

                for img_idx, img in enumerate(images):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)

                        # Save image if output_dir provided
                        img_path = None
                        if output_dir:
                            output_dir.mkdir(parents=True, exist_ok=True)
                            img_filename = f"page{page_num+1}_img{img_idx+1}.{base_image['ext']}"
                            img_path = output_dir / img_filename

                            with open(img_path, "wb") as f:
                                f.write(base_image["image"])

                        # Create Figure object
                        figure = Figure(
                            id=f"fig_p{page_num+1}_{img_idx+1}",
                            label=f"Figure {len(figures)+1}",
                            caption="",  # PDFs don't have structured captions
                            graphic_ref=str(img_path) if img_path else "",
                        )

                        figure.metadata = {
                            "page": page_num + 1,
                            "width": base_image.get("width"),
                            "height": base_image.get("height"),
                            "format": base_image.get("ext"),
                            "size": len(base_image["image"]),
                        }

                        figures.append(figure)

                    except Exception as e:
                        logger.debug(f"Failed to extract image {img_idx} from page {page_num+1}: {e}")

            doc.close()

            logger.info(f"Extracted {len(figures)} images from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Image extraction failed: {e}")

        return figures

    def _parse_sections_from_text(self, text: str) -> List[Section]:
        """
        Parse sections from plain text using heuristics.

        This is a basic implementation that splits on common section headers.
        More sophisticated methods could use ML-based section detection.

        Args:
            text: Full text of PDF

        Returns:
            List of Section objects
        """
        sections = []

        # Common section headers (case-insensitive)
        section_headers = [
            "abstract",
            "introduction",
            "background",
            "methods",
            "methodology",
            "materials and methods",
            "results",
            "discussion",
            "conclusion",
            "conclusions",
            "references",
            "acknowledgments",
            "acknowledgements",
        ]

        # Split text into lines
        lines = text.split("\n")

        current_section = None
        current_paragraphs = []

        for line in lines:
            line_lower = line.strip().lower()

            # Check if line is a section header
            is_header = False
            for header in section_headers:
                if line_lower.startswith(header) and len(line.strip()) < 50:
                    # Save previous section
                    if current_section:
                        sections.append(
                            Section(
                                id=f"sec{len(sections)+1}",
                                title=current_section,
                                level=1,
                                paragraphs=current_paragraphs,
                            )
                        )

                    # Start new section
                    current_section = line.strip()
                    current_paragraphs = []
                    is_header = True
                    break

            # Add to current section if not a header
            if not is_header and line.strip():
                current_paragraphs.append(line.strip())

        # Add final section
        if current_section:
            sections.append(
                Section(
                    id=f"sec{len(sections)+1}",
                    title=current_section,
                    level=1,
                    paragraphs=current_paragraphs,
                )
            )

        # If no sections found, create single "Body" section
        if not sections:
            sections.append(
                Section(id="sec1", title="Body", level=1, paragraphs=[text] if text.strip() else [])
            )

        logger.debug(f"Parsed {len(sections)} sections from text")
        return sections

    def extract_structured_content(
        self,
        pdf_path: Path,
        extract_tables: bool = True,
        extract_images: bool = False,
        image_output_dir: Optional[Path] = None,
    ) -> FullTextContent:
        """
        Extract all content into unified FullTextContent structure.

        This mirrors ContentExtractor.extract_structured_content() for XML,
        but works with PDFs. Provides structured data when PMC XML unavailable.

        Args:
            pdf_path: Path to PDF file
            extract_tables: Whether to extract tables (slower)
            extract_images: Whether to extract images
            image_output_dir: Directory to save extracted images

        Returns:
            FullTextContent object with all extracted content
        """
        if not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)

        logger.info(f"Extracting structured content from {pdf_path.name}")

        # Extract text (always)
        full_text = self.extract_text(pdf_path)

        # Parse sections from text
        sections = self._parse_sections_from_text(full_text)

        # Extract tables (optional, slower)
        tables = []
        if extract_tables:
            logger.debug("Extracting tables...")
            tables = self.extract_tables(pdf_path)

        # Extract images (optional)
        figures = []
        if extract_images:
            logger.debug("Extracting images...")
            figures = self.extract_images(pdf_path, output_dir=image_output_dir)

        # Extract abstract (from sections)
        abstract = ""
        for section in sections:
            if section.title.lower().startswith("abstract"):
                abstract = "\n".join(section.paragraphs)
                break

        # Create FullTextContent
        content = FullTextContent(
            title="",  # PDFs don't have structured title metadata
            abstract=abstract,
            keywords=[],
            authors=[],
            sections=sections,
            figures=figures,
            tables=tables,
            references=[],  # Could parse from References section
            journal="",
            publication_year="",
            doi="",
            pmid="",
            pmc="",
        )

        # Add source metadata
        content.metadata = {
            "source": "pdf",
            "pdf_path": str(pdf_path),
            "extracted_tables": len(tables),
            "extracted_images": len(figures),
            "total_sections": len(sections),
        }

        logger.info(
            f"Extraction complete: {len(sections)} sections, " f"{len(tables)} tables, {len(figures)} images"
        )

        return content

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get extractor capabilities based on installed libraries.

        Returns:
            Dict of capability flags
        """
        return {
            "camelot_available": self.camelot_available,
            "pymupdf_available": self.pymupdf_available,
            "pdfplumber_available": self.pdfplumber_available,
            "can_extract_tables": self.camelot_available or self.pdfplumber_available,
            "can_extract_text": self.pymupdf_available,
            "can_extract_images": self.pymupdf_available,
        }


# Convenience functions
def extract_tables_from_pdf(pdf_path: Path, method: str = "auto") -> List[Table]:
    """
    Quick function to extract tables from PDF.

    Args:
        pdf_path: Path to PDF file
        method: Extraction method ('auto', 'stream', 'lattice', 'pdfplumber')

    Returns:
        List of Table objects
    """
    extractor = PDFExtractor()
    return extractor.extract_tables(pdf_path, method=method)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Quick function to extract text from PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text
    """
    extractor = PDFExtractor()
    return extractor.extract_text(pdf_path)


__all__ = [
    "PDFExtractor",
    "extract_tables_from_pdf",
    "extract_text_from_pdf",
]
