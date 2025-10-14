"""
URL Validator - Classify and validate URLs without downloading

This module provides URL classification and validation to determine
whether a URL is likely a direct PDF, HTML landing page, or fulltext HTML.

Key Features:
- Pattern-based classification (no HTTP requests)
- Domain-specific rules (arXiv, bioRxiv, PMC, etc.)
- Content-type inference from URL structure
- Skip known problematic URLs

Usage:
    >>> from omics_oracle_v2.lib.enrichment.fulltext.url_validator import URLValidator, URLType
    >>>
    >>> url = "https://arxiv.org/pdf/2401.12345.pdf"
    >>> url_type = URLValidator.classify_url(url)
    >>> print(url_type)  # URLType.PDF_DIRECT
    >>>
    >>> if URLValidator.is_likely_pdf(url):
    >>>     print("Direct PDF link - download immediately")

Created: October 13, 2025
"""

import logging
import re
from enum import Enum
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class URLType(str, Enum):
    """
    Type of URL based on content and structure.

    Used to optimize download strategy:
    - PDF_DIRECT: Download immediately (high priority)
    - HTML_FULLTEXT: Parse HTML for text extraction
    - LANDING_PAGE: Extract PDF link first, then download
    - DOI_RESOLVER: Resolve DOI redirect first
    - UNKNOWN: Try downloading, validate content type
    """

    PDF_DIRECT = "pdf_direct"  # Direct link to PDF file
    HTML_FULLTEXT = "html_fulltext"  # HTML page with full text
    LANDING_PAGE = "landing_page"  # Article landing page (needs extraction)
    DOI_RESOLVER = "doi_resolver"  # DOI.org resolver (redirects)
    UNKNOWN = "unknown"  # Cannot determine type


class URLValidator:
    """
    Validate and classify URLs for optimal download strategy.

    This class uses pattern matching and domain knowledge to classify
    URLs without making HTTP requests. This saves bandwidth and reduces
    latency by allowing smart prioritization.

    Classification Strategy:
    1. Check domain-specific patterns (arXiv, bioRxiv, PMC)
    2. Check file extensions (.pdf, .html)
    3. Check path patterns (/pdf/, /fulltext/, /article/)
    4. Fall back to UNKNOWN if no patterns match

    Example:
        >>> # PDF URLs - download immediately
        >>> URLValidator.classify_url("https://arxiv.org/pdf/2401.12345.pdf")
        # URLType.PDF_DIRECT

        >>> # Landing pages - extract PDF link first
        >>> URLValidator.classify_url("https://doi.org/10.1234/abc")
        # URLType.DOI_RESOLVER

        >>> # Quick check
        >>> URLValidator.is_likely_pdf("https://example.com/paper.pdf")
        # True
    """

    # ===================================================================
    # PDF PATTERNS (Highest Priority)
    # ===================================================================

    PDF_PATTERNS = [
        # Domain-specific PDF patterns (most reliable)
        (r"arxiv\.org/pdf/[\d\.]+v?\d*\.pdf$", URLType.PDF_DIRECT),
        (r"biorxiv\.org/content/.*\.full\.pdf$", URLType.PDF_DIRECT),
        (r"medrxiv\.org/content/.*\.full\.pdf$", URLType.PDF_DIRECT),
        (r"ncbi\.nlm\.nih\.gov/pmc/articles/PMC\d+/pdf/", URLType.PDF_DIRECT),
        (r"ftp\.ncbi\.nlm\.nih\.gov/.*\.pdf$", URLType.PDF_DIRECT),
        # Generic PDF patterns
        (r"\.pdf(\?.*)?$", URLType.PDF_DIRECT),  # Ends with .pdf (with optional query)
        (r"\.pdf#", URLType.PDF_DIRECT),  # .pdf# (PDF with anchor)
        (r"/pdf/[^/]+\.pdf$", URLType.PDF_DIRECT),  # /pdf/filename.pdf
        (r"/download/[^/]*\.pdf$", URLType.PDF_DIRECT),  # /download/*.pdf
        # Path-based PDF indicators
        (r"/pdf/", URLType.PDF_DIRECT),  # /pdf/ anywhere in path
        (r"/pdfs/", URLType.PDF_DIRECT),  # /pdfs/ plural
    ]

    # ===================================================================
    # LANDING PAGE PATTERNS
    # ===================================================================

    LANDING_PATTERNS = [
        # DOI resolvers (always redirect)
        (r"^https?://doi\.org/", URLType.DOI_RESOLVER),
        (r"^https?://dx\.doi\.org/", URLType.DOI_RESOLVER),
        # Article landing pages
        (r"/article[\?/]", URLType.LANDING_PAGE),  # /article? or /article/
        (r"/articles/", URLType.LANDING_PAGE),
        (r"/view/", URLType.LANDING_PAGE),
        (r"/abs/", URLType.LANDING_PAGE),
        (r"/abstract/", URLType.LANDING_PAGE),
        (r"/content/", URLType.LANDING_PAGE),  # Publisher landing pages
        (r"/paper/", URLType.LANDING_PAGE),
        # Known publisher patterns
        (r"sciencedirect\.com/science/article/", URLType.LANDING_PAGE),
        (r"springer\.com/article/", URLType.LANDING_PAGE),
        (r"nature\.com/articles/", URLType.LANDING_PAGE),
        (r"wiley\.com/doi/", URLType.LANDING_PAGE),
        (r"tandfonline\.com/doi/", URLType.LANDING_PAGE),
        (r"plos\.org/.*article\?", URLType.LANDING_PAGE),  # PLOS journals
    ]

    # ===================================================================
    # HTML FULLTEXT PATTERNS
    # ===================================================================

    HTML_PATTERNS = [
        (r"/fulltext/", URLType.HTML_FULLTEXT),
        (r"/full/", URLType.HTML_FULLTEXT),
        (r"/html/", URLType.HTML_FULLTEXT),
        (r"\.html?(\?.*)?$", URLType.HTML_FULLTEXT),  # Ends with .html
        (r"\.htm(\?.*)?$", URLType.HTML_FULLTEXT),  # Ends with .htm
    ]

    # ===================================================================
    # SKIP PATTERNS (Known Problematic URLs)
    # ===================================================================

    SKIP_DOMAINS = [
        "google.com",  # Google Scholar search results
        "scholar.google.com",
        "facebook.com",
        "twitter.com",
        "linkedin.com",
        "researchgate.net",  # Paywalled, requires login
        "academia.edu",  # Requires login
    ]

    # ===================================================================
    # CLASSIFICATION METHODS
    # ===================================================================

    @classmethod
    def classify_url(cls, url: str) -> URLType:
        """
        Classify URL type without making HTTP requests.

        Uses pattern matching and domain knowledge to determine
        whether a URL points to a PDF, HTML page, or landing page.

        Args:
            url: URL to classify

        Returns:
            URLType enum indicating the URL type

        Example:
            >>> URLValidator.classify_url("https://arxiv.org/pdf/2401.12345.pdf")
            URLType.PDF_DIRECT

            >>> URLValidator.classify_url("https://doi.org/10.1234/abc")
            URLType.DOI_RESOLVER
        """
        if not url:
            return URLType.UNKNOWN

        url_lower = url.lower().strip()

        # Check if should skip
        if cls.should_skip(url_lower):
            logger.debug(f"Skipping problematic URL: {url}")
            return URLType.UNKNOWN

        # Priority 1: Check PDF patterns (highest priority)
        for pattern, url_type in cls.PDF_PATTERNS:
            if re.search(pattern, url_lower):
                logger.debug(f"Classified as {url_type.value}: {url[:80]}")
                return url_type

        # Priority 2: Check HTML fulltext patterns
        for pattern, url_type in cls.HTML_PATTERNS:
            if re.search(pattern, url_lower):
                logger.debug(f"Classified as {url_type.value}: {url[:80]}")
                return url_type

        # Priority 3: Check landing page patterns
        for pattern, url_type in cls.LANDING_PATTERNS:
            if re.search(pattern, url_lower):
                logger.debug(f"Classified as {url_type.value}: {url[:80]}")
                return url_type

        # Priority 4: Domain-specific classification
        parsed = urlparse(url_lower)

        # Known PDF domains
        if parsed.netloc in ["arxiv.org", "biorxiv.org", "medrxiv.org"]:
            if "/pdf/" in url_lower:
                return URLType.PDF_DIRECT
            else:
                return URLType.LANDING_PAGE

        # PMC - depends on path
        if "ncbi.nlm.nih.gov" in parsed.netloc:
            if "/pdf/" in url_lower or url_lower.endswith(".pdf"):
                return URLType.PDF_DIRECT
            else:
                return URLType.LANDING_PAGE

        # Default: Unknown (will need content-type check)
        logger.debug(f"Could not classify URL: {url[:80]}")
        return URLType.UNKNOWN

    @classmethod
    def is_likely_pdf(cls, url: str) -> bool:
        """
        Quick check if URL is likely a direct PDF link.

        Useful for prioritization - direct PDFs should be tried first.

        Args:
            url: URL to check

        Returns:
            True if URL is likely a direct PDF

        Example:
            >>> URLValidator.is_likely_pdf("https://arxiv.org/pdf/2401.12345.pdf")
            True

            >>> URLValidator.is_likely_pdf("https://doi.org/10.1234/abc")
            False
        """
        return cls.classify_url(url) == URLType.PDF_DIRECT

    @classmethod
    def is_landing_page(cls, url: str) -> bool:
        """
        Check if URL is a landing page (needs extraction).

        Args:
            url: URL to check

        Returns:
            True if URL is a landing page
        """
        url_type = cls.classify_url(url)
        return url_type in [URLType.LANDING_PAGE, URLType.DOI_RESOLVER]

    @classmethod
    def should_skip(cls, url: str) -> bool:
        """
        Check if URL should be skipped (known to not work).

        Args:
            url: URL to check

        Returns:
            True if URL should be skipped

        Example:
            >>> URLValidator.should_skip("https://scholar.google.com/...")
            True
        """
        if not url:
            return True

        url_lower = url.lower()
        parsed = urlparse(url_lower)

        # Check skip domains
        for domain in cls.SKIP_DOMAINS:
            if domain in parsed.netloc:
                return True

        # Check for obvious non-PDF schemes
        if parsed.scheme not in ["http", "https", "ftp"]:
            return True

        return False

    @classmethod
    def get_priority_boost(cls, url: str) -> int:
        """
        Get priority adjustment based on URL type.

        Direct PDFs get negative boost (higher priority),
        landing pages get positive boost (lower priority).

        Args:
            url: URL to evaluate

        Returns:
            Priority adjustment (-2 to +3)

        Example:
            >>> URLValidator.get_priority_boost("https://arxiv.org/pdf/2401.12345.pdf")
            -2  # Higher priority

            >>> URLValidator.get_priority_boost("https://doi.org/10.1234/abc")
            +3  # Lower priority
        """
        url_type = cls.classify_url(url)

        if url_type == URLType.PDF_DIRECT:
            return -2  # Much higher priority
        elif url_type == URLType.HTML_FULLTEXT:
            return +1  # Slightly lower priority
        elif url_type == URLType.LANDING_PAGE:
            return +2  # Lower priority
        elif url_type == URLType.DOI_RESOLVER:
            return +3  # Lowest priority (slow redirects)
        else:
            return 0  # No adjustment

    @classmethod
    def extract_domain(cls, url: str) -> Optional[str]:
        """
        Extract domain from URL for logging/stats.

        Args:
            url: URL to parse

        Returns:
            Domain name or None
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None

    @classmethod
    def validate_url_format(cls, url: str) -> Tuple[bool, Optional[str]]:
        """
        Basic URL format validation.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return (False, "Empty URL")

        if not isinstance(url, str):
            return (False, "URL must be string")

        if len(url) > 2000:
            return (False, "URL too long (>2000 chars)")

        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                return (False, "Missing URL scheme")

            if parsed.scheme not in ["http", "https", "ftp"]:
                return (False, f"Invalid scheme: {parsed.scheme}")

            if not parsed.netloc:
                return (False, "Missing domain")

            return (True, None)

        except Exception as e:
            return (False, f"Parse error: {e}")


# =======================================================================
# CONVENIENCE FUNCTIONS
# =======================================================================


def classify_url(url: str) -> URLType:
    """Convenience function for URL classification."""
    return URLValidator.classify_url(url)


def is_likely_pdf(url: str) -> bool:
    """Convenience function to check if URL is likely a PDF."""
    return URLValidator.is_likely_pdf(url)


def should_skip_url(url: str) -> bool:
    """Convenience function to check if URL should be skipped."""
    return URLValidator.should_skip(url)


# =======================================================================
# TESTING
# =======================================================================

if __name__ == "__main__":
    # Test cases
    print("=" * 80)
    print("URL Validator - Test Cases")
    print("=" * 80)

    test_urls = [
        # Direct PDFs
        ("https://arxiv.org/pdf/2401.12345.pdf", URLType.PDF_DIRECT),
        ("https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1.full.pdf", URLType.PDF_DIRECT),
        ("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/main.pdf", URLType.PDF_DIRECT),
        ("https://example.com/paper.pdf", URLType.PDF_DIRECT),
        ("https://publisher.com/pdf/article.pdf?download=true", URLType.PDF_DIRECT),
        # Landing pages
        ("https://doi.org/10.1234/abc", URLType.DOI_RESOLVER),
        ("https://www.nature.com/articles/nature12373", URLType.LANDING_PAGE),
        ("https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456", URLType.LANDING_PAGE),
        # HTML fulltext
        ("https://example.com/fulltext/article.html", URLType.HTML_FULLTEXT),
        ("https://publisher.com/full/paper.html", URLType.HTML_FULLTEXT),
        # Unknown
        ("https://example.com/download/paper", URLType.UNKNOWN),
    ]

    passed = 0
    failed = 0

    for url, expected_type in test_urls:
        result = URLValidator.classify_url(url)
        status = "PASS" if result == expected_type else "FAIL"

        if result == expected_type:
            passed += 1
        else:
            failed += 1

        print(f"{status} {result.value:15} | Expected: {expected_type.value:15} | {url[:60]}")

    print("=" * 80)
    print(f"Results: {passed}/{len(test_urls)} passed, {failed}/{len(test_urls)} failed")
    print("=" * 80)

    if failed == 0:
        print("All tests passed!")
    else:
        print(f"WARNING: {failed} tests failed")
