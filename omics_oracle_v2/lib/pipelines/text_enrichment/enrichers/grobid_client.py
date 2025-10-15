"""
GROBID Client (Optional Enhanced Extraction)

GROBID (GeneRation Of BIbliographic Data) is a machine learning library for
extracting structured information from scholarly documents.

This is an OPTIONAL enricher - requires external GROBID service.
Falls back to pypdf if GROBID unavailable.

Installation:
    1. Docker: docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
    2. Or install locally: https://grobid.readthedocs.io/

Usage:
    >>> client = GROBIDClient(service_url="http://localhost:8070")
    >>> if await client.is_available():
    ...     result = await client.process_pdf(pdf_path)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class GROBIDSection:
    """Structured section from GROBID."""

    heading: str
    content: str
    level: int = 1


@dataclass
class GROBIDResult:
    """GROBID processing result."""

    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[str] = None
    sections: List[GROBIDSection] = None
    references: List[Dict] = None
    raw_tei_xml: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class GROBIDClient:
    """
    Client for GROBID service.

    Note: This is OPTIONAL - requires external GROBID service running.
    System will fall back to pypdf if GROBID unavailable.
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8070",
        timeout: int = 60,
    ):
        """
        Initialize GROBID client.

        Args:
            service_url: GROBID service URL
            timeout: Request timeout in seconds
        """
        self.service_url = service_url.rstrip("/")
        self.timeout = timeout
        self._is_available = None  # Cached availability

    async def is_available(self) -> bool:
        """Check if GROBID service is available."""
        if self._is_available is not None:
            return self._is_available

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.service_url}/api/isalive",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    self._is_available = response.status == 200
                    return self._is_available
        except Exception as e:
            logger.debug(f"GROBID service not available: {e}")
            self._is_available = False
            return False

    async def process_pdf(self, pdf_path: Path) -> GROBIDResult:
        """
        Process PDF with GROBID.

        Args:
            pdf_path: Path to PDF file

        Returns:
            GROBIDResult with structured extraction
        """
        if not await self.is_available():
            return GROBIDResult(
                success=False,
                error="GROBID service not available",
            )

        try:
            # Prepare file upload
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            data = aiohttp.FormData()
            data.add_field("input", pdf_data, filename=pdf_path.name, content_type="application/pdf")

            # Call GROBID processFulltextDocument endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.service_url}/api/processFulltextDocument",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        return GROBIDResult(
                            success=False,
                            error=f"GROBID returned status {response.status}",
                        )

                    tei_xml = await response.text()

                    # Parse TEI XML (simplified - would need proper XML parsing)
                    result = self._parse_tei_xml(tei_xml)
                    result.raw_tei_xml = tei_xml
                    result.success = True

                    return result

        except Exception as e:
            logger.error(f"GROBID processing failed for {pdf_path}: {e}")
            return GROBIDResult(success=False, error=str(e))

    def _parse_tei_xml(self, tei_xml: str) -> GROBIDResult:
        """
        Parse GROBID TEI XML output.

        Note: This is a simplified version. Production would use lxml or xml.etree.
        """
        # TODO: Implement proper TEI XML parsing
        # For now, return empty result
        logger.warning("TEI XML parsing not implemented - use GROBID Python client for full support")

        return GROBIDResult(
            title=None,
            abstract=None,
            authors=[],
            sections=[],
            references=[],
        )


# Note: For production use, consider using the official grobid-client-python:
# https://github.com/kermitt2/grobid-client-python
# pip install grobid-client-python
