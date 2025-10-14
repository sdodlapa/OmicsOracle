"""
HTML Landing Page Parser for PDF Downloads

Extracts direct PDF download links from publisher landing pages when DOI redirects
fail to provide the actual PDF file.

Supports:
- Nature/Springer (nature.com, springer.com, biomedcentral.com)
- Elsevier/ScienceDirect
- Wiley
- PLOS
- Generic PDF meta tags
"""

import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LandingPageParser:
    """Extract PDF download links from publisher HTML landing pages"""

    # Publisher-specific selectors for PDF download links
    SELECTORS = {
        # Nature/Springer/BMC
        "nature": [
            "a.c-pdf-download__link",
            "a.c-pdf-button__link",
            'a[data-track-action="download pdf"]',
            'a[href*="/pdf/"]',
        ],
        # Elsevier/ScienceDirect
        "elsevier": [
            "a.PdfDropDownMenu",
            "a#pdfLink",
            'a[data-aa-name="download-pdf"]',
            'a[href*="pdfft"]',
        ],
        # Wiley
        "wiley": [
            "a.pdf-download",
            'a[title*="PDF"]',
            'a[href*="/doi/pdf/"]',
        ],
        # PLOS
        "plos": [
            'a[data-doi*="download"]',
            "a.download",
            'a[href*="/article/file"]',
        ],
        # Generic fallbacks
        "generic": [
            'a[href$=".pdf"]',
            'link[type="application/pdf"]',
            'meta[name="citation_pdf_url"]',
            'meta[property="og:url"][content$=".pdf"]',
        ],
    }

    def __init__(self):
        """Initialize the parser"""

    def detect_publisher(self, url: str, html: str) -> str:
        """
        Detect publisher from URL or HTML content

        Args:
            url: Landing page URL
            html: HTML content

        Returns:
            Publisher name ('nature', 'elsevier', 'wiley', 'plos', 'generic')
        """
        domain = urlparse(url).netloc.lower()

        # Check domain patterns
        if any(p in domain for p in ["nature.com", "springer.com", "biomedcentral.com"]):
            return "nature"
        elif any(p in domain for p in ["sciencedirect.com", "elsevier.com"]):
            return "elsevier"
        elif "wiley.com" in domain or "onlinelibrary.wiley.com" in domain:
            return "wiley"
        elif "plos.org" in domain or "plosone.org" in domain:
            return "plos"

        # Check HTML meta tags
        soup = BeautifulSoup(html, "html.parser")
        meta_publisher = soup.find("meta", attrs={"name": "citation_publisher"})
        if meta_publisher:
            publisher = meta_publisher.get("content", "").lower()
            if "springer" in publisher or "nature" in publisher:
                return "nature"
            elif "elsevier" in publisher:
                return "elsevier"
            elif "wiley" in publisher:
                return "wiley"
            elif "plos" in publisher:
                return "plos"

        return "generic"

    def extract_pdf_url(self, html: str, base_url: str) -> Optional[str]:
        """
        Extract PDF download URL from HTML landing page

        Args:
            html: HTML content of landing page
            base_url: Base URL for resolving relative links

        Returns:
            Absolute PDF URL or None if not found
        """
        soup = BeautifulSoup(html, "html.parser")
        publisher = self.detect_publisher(base_url, html)

        logger.debug(f"Detected publisher: {publisher} from {base_url}")

        # Try publisher-specific selectors first
        selectors = self.SELECTORS.get(publisher, [])
        selectors.extend(self.SELECTORS["generic"])  # Add generic fallbacks

        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("link[") or selector.startswith("meta["):
                    # Meta tag or link tag
                    element = soup.select_one(selector)
                    if element:
                        url = element.get("content") or element.get("href")
                        if url:
                            abs_url = urljoin(base_url, url)
                            logger.info(f"Found PDF URL via {selector}: {abs_url}")
                            return abs_url
                else:
                    # Regular anchor tag
                    link = soup.select_one(selector)
                    if link and link.get("href"):
                        href = link["href"]
                        abs_url = urljoin(base_url, href)

                        # Validate it looks like a PDF URL
                        if self._is_valid_pdf_url(abs_url):
                            logger.info(f"Found PDF URL via {selector}: {abs_url}")
                            return abs_url
                        else:
                            logger.debug(f"Rejected non-PDF URL: {abs_url}")
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        logger.warning(f"No PDF URL found in landing page from {base_url}")
        return None

    def _is_valid_pdf_url(self, url: str) -> bool:
        """
        Check if URL likely points to a PDF

        Args:
            url: URL to validate

        Returns:
            True if URL likely points to PDF
        """
        url_lower = url.lower()

        # Must contain 'pdf' somewhere
        if "pdf" not in url_lower:
            return False

        # Reject obviously wrong URLs
        if any(bad in url_lower for bad in ["?format=xml", "format=epub", ".htm"]):
            return False

        # Reject social/share links
        if any(social in url_lower for social in ["facebook", "twitter", "linkedin", "email"]):
            return False

        return True


# Singleton instance for reuse
_parser_instance = None


def get_parser() -> LandingPageParser:
    """Get singleton parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = LandingPageParser()
    return _parser_instance
