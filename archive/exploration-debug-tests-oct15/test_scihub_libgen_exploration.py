"""
EXTENSIVE SCI-HUB & LIBGEN EXPLORATION

This script will:
1. Test multiple Sci-Hub mirrors with diverse papers
2. Test LibGen (Library Genesis) access patterns
3. Analyze ALL possible HTML patterns for PDF extraction
4. Test different identifier types (DOI, PMID, arXiv ID, ISBN)
5. Document all successful extraction patterns
6. Compare performance across mirrors

Goal: Maximize Sci-Hub/LibGen success rate by finding all possible patterns
"""

import asyncio
import logging
import os
import re
import ssl
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# SSL context
SSL_CONTEXT = ssl.create_default_context()
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE


@dataclass
class TestPaper:
    """Test paper with multiple identifiers."""

    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    year: Optional[int] = None
    publisher: Optional[str] = None
    expected_availability: str = "unknown"  # "scihub", "libgen", "both", "neither"


# Diverse test set covering different publishers, years, and types
TEST_PAPERS = [
    # Classic papers (should be in Sci-Hub)
    TestPaper(
        title="The sequence of the human genome",
        doi="10.1126/science.1058040",
        pmid="11235003",
        year=2001,
        publisher="Science",
        expected_availability="scihub",
    ),
    TestPaper(
        title="The hallmarks of aging",
        doi="10.1016/j.cell.2013.05.039",
        pmid="23746838",
        year=2013,
        publisher="Cell",
        expected_availability="scihub",
    ),
    TestPaper(
        title="A draft sequence of the human genome",
        doi="10.1038/35057062",
        pmid="11237011",
        year=2001,
        publisher="Nature",
        expected_availability="scihub",
    ),
    # Mid-range papers (2015-2020)
    TestPaper(
        title="CRISPR-Cas9",
        doi="10.1126/science.1258096",
        pmid="25430774",
        year=2014,
        publisher="Science",
        expected_availability="scihub",
    ),
    TestPaper(
        title="AlphaFold protein structure",
        doi="10.1038/s41586-021-03819-2",
        pmid="34265844",
        year=2021,
        publisher="Nature",
        expected_availability="scihub",
    ),
    # Recent papers (2022-2024)
    TestPaper(
        title="ChatGPT medical applications",
        doi="10.1038/s41591-023-02448-8",
        year=2023,
        publisher="Nature Medicine",
        expected_availability="scihub",
    ),
    TestPaper(
        title="COVID-19 vaccine efficacy",
        doi="10.1056/NEJMoa2034577",
        pmid="33301246",
        year=2020,
        publisher="NEJM",
        expected_availability="scihub",
    ),
    # arXiv papers
    TestPaper(
        title="Attention is all you need",
        doi="10.48550/arXiv.1706.03762",
        arxiv_id="1706.03762",
        year=2017,
        publisher="arXiv",
        expected_availability="both",
    ),
    # Open Access (control - should NOT need Sci-Hub)
    TestPaper(
        title="PLOS ONE paper",
        doi="10.1371/journal.pgen.1011043",
        year=2024,
        publisher="PLOS",
        expected_availability="neither",  # Should be OA
    ),
    # Books/Textbooks (for LibGen testing)
    TestPaper(
        title="Molecular Biology of the Cell",
        doi="10.1201/9781315735368",
        year=2014,
        publisher="Garland Science",
        expected_availability="libgen",
    ),
]

# Sci-Hub mirrors (updated October 2025)
SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.ren",
    "https://sci-hub.si",
    "https://sci-hub.wf",
    "https://sci-hub.shop",
    "https://sci-hub.ee",
]

# LibGen mirrors
LIBGEN_MIRRORS = [
    "https://libgen.is",
    "https://libgen.rs",
    "https://libgen.st",
]


class PDFPattern:
    """Track different PDF extraction patterns."""

    def __init__(self, name: str, regex: str, description: str):
        self.name = name
        self.regex = regex
        self.description = description
        self.successes = 0
        self.total_attempts = 0

    def try_extract(self, html: str, base_url: str = "") -> Optional[str]:
        """Try to extract PDF URL using this pattern."""
        self.total_attempts += 1
        match = re.search(self.regex, html, re.IGNORECASE | re.DOTALL)
        if match:
            url = match.group(1)
            self.successes += 1
            return self._normalize_url(url, base_url)
        return None

    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize relative URLs to absolute."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        elif url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            return base_url + url
        else:
            return base_url + "/" + url

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successes / self.total_attempts) * 100


# ALL possible PDF extraction patterns to test
PDF_PATTERNS = [
    # Pattern 1: embed tag with src
    PDFPattern(
        "embed_src", r'<embed[^>]+src="([^"]+)"', "Embed tag with src attribute"
    ),
    # Pattern 2: iframe with PDF
    PDFPattern(
        "iframe_pdf", r'<iframe[^>]+src="([^"]+\.pdf[^"]*)"', "Iframe with PDF in src"
    ),
    # Pattern 3: iframe (any)
    PDFPattern("iframe_any", r'<iframe[^>]+src="([^"]+)"', "Iframe with any src"),
    # Pattern 4: Direct download link
    PDFPattern(
        "download_link",
        r'<a[^>]+href="([^"]+\.pdf[^"]*)"[^>]*>(?:download|save|get)</a>',
        "Download link with PDF",
    ),
    # Pattern 5: Button onclick
    PDFPattern(
        "button_onclick",
        r'<button[^>]+onclick=["\']location\.href=["\']([^"\']+)',
        "Button with onclick location",
    ),
    # Pattern 6: Meta refresh
    PDFPattern(
        "meta_refresh", r'<meta[^>]+content="0;url=([^"]+)"', "Meta refresh redirect"
    ),
    # Pattern 7: JavaScript redirect
    PDFPattern(
        "js_redirect",
        r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)',
        "JavaScript location.href",
    ),
    # Pattern 8: window.open
    PDFPattern(
        "window_open",
        r'window\.open\(["\']([^"\']+\.pdf[^"\']*)',
        "JavaScript window.open",
    ),
    # Pattern 9: Any PDF link in href
    PDFPattern("any_pdf_href", r'href="([^"]+\.pdf[^"]*)"', "Any href with PDF"),
    # Pattern 10: Protocol-relative PDF URL
    PDFPattern(
        "protocol_relative",
        r'(?:src|href)="(//[^"]+\.pdf[^"]*)"',
        "Protocol-relative PDF URL",
    ),
    # Pattern 11: Absolute PDF URL anywhere in HTML
    PDFPattern(
        "absolute_pdf",
        r'(https?://[^\s"<>]+\.pdf[^\s"<>]*)',
        "Absolute PDF URL anywhere",
    ),
    # Pattern 12: PDF.js viewer URL
    PDFPattern(
        "pdfjs_viewer",
        r'(?:pdf\.js|viewer\.html)\?file=([^&"\s]+)',
        "PDF.js viewer URL",
    ),
    # Pattern 13: Data attribute
    PDFPattern(
        "data_attribute",
        r'data-(?:pdf|file|url)="([^"]+\.pdf[^"]*)"',
        "Data attribute with PDF",
    ),
    # Pattern 14: LibGen specific - download link
    PDFPattern(
        "libgen_download",
        r'<a[^>]+href="([^"]+)"[^>]*>(?:\[1\]|\[GET\]|download)',
        "LibGen download link",
    ),
    # Pattern 15: LibGen specific - direct link
    PDFPattern(
        "libgen_direct",
        r'<a[^>]+href="(http[^"]+/get\.php[^"]+)"',
        "LibGen direct download",
    ),
]


async def test_scihub_mirror(
    mirror: str,
    paper: TestPaper,
    session: aiohttp.ClientSession,
    patterns: List[PDFPattern],
) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Test a single Sci-Hub mirror with a paper.

    Returns:
        (success, pdf_url, pattern_name, html_snippet)
    """
    # Try different identifiers
    identifiers = []
    if paper.doi:
        identifiers.append(("DOI", paper.doi))
    if paper.pmid:
        identifiers.append(("PMID", paper.pmid))
    if paper.arxiv_id:
        identifiers.append(("arXiv", paper.arxiv_id))

    for id_type, identifier in identifiers:
        url = f"{mirror}/{quote(identifier)}"

        try:
            async with session.get(url, timeout=15, ssl=SSL_CONTEXT) as response:
                if response.status != 200:
                    continue

                html = await response.text()

                # Try all patterns
                for pattern in patterns:
                    pdf_url = pattern.try_extract(html, mirror)
                    if pdf_url and ".pdf" in pdf_url.lower():
                        # Found it!
                        snippet = html[:500] if len(html) > 500 else html
                        return True, pdf_url, f"{pattern.name} ({id_type})", snippet

        except Exception as e:
            logger.debug(f"Error testing {mirror} with {identifier}: {e}")
            continue

    return False, None, None, ""


async def test_libgen_mirror(
    mirror: str,
    paper: TestPaper,
    session: aiohttp.ClientSession,
    patterns: List[PDFPattern],
) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Test LibGen mirror with a paper.

    Returns:
        (success, pdf_url, pattern_name, html_snippet)
    """
    if not paper.doi:
        return False, None, None, ""

    # LibGen search by DOI
    search_url = f"{mirror}/scimag/?q={quote(paper.doi)}"

    try:
        async with session.get(search_url, timeout=15, ssl=SSL_CONTEXT) as response:
            if response.status != 200:
                return False, None, None, ""

            html = await response.text()

            # Try all patterns
            for pattern in patterns:
                pdf_url = pattern.try_extract(html, mirror)
                if pdf_url:
                    snippet = html[:500] if len(html) > 500 else html
                    return True, pdf_url, pattern.name, snippet

    except Exception as e:
        logger.debug(f"Error testing LibGen {mirror} with {paper.doi}: {e}")

    return False, None, None, ""


async def comprehensive_exploration():
    """Run comprehensive exploration of Sci-Hub and LibGen."""

    print("=" * 80)
    print("COMPREHENSIVE SCI-HUB & LIBGEN EXPLORATION")
    print("=" * 80)
    print(f"Testing {len(TEST_PAPERS)} papers across:")
    print(f"  - {len(SCIHUB_MIRRORS)} Sci-Hub mirrors")
    print(f"  - {len(LIBGEN_MIRRORS)} LibGen mirrors")
    print(f"  - {len(PDF_PATTERNS)} extraction patterns")
    print()

    results = {
        "scihub": {},
        "libgen": {},
        "patterns": PDF_PATTERNS,
    }

    async with aiohttp.ClientSession() as session:
        # Test Sci-Hub
        print("\n" + "=" * 80)
        print("TESTING SCI-HUB MIRRORS")
        print("=" * 80)

        for mirror in SCIHUB_MIRRORS:
            print(f"\nMirror: {mirror}")
            print("-" * 60)

            mirror_results = []

            for paper in TEST_PAPERS:
                success, pdf_url, pattern, snippet = await test_scihub_mirror(
                    mirror, paper, session, PDF_PATTERNS
                )

                mirror_results.append(
                    {
                        "paper": paper.title[:40],
                        "success": success,
                        "pdf_url": pdf_url[:60] if pdf_url else None,
                        "pattern": pattern,
                    }
                )

                if success:
                    print(f"  [OK] {paper.title[:40]:40} via {pattern}")
                else:
                    print(f"  [--] {paper.title[:40]:40}")

                await asyncio.sleep(2)  # Rate limiting

            results["scihub"][mirror] = mirror_results

            success_count = sum(1 for r in mirror_results if r["success"])
            print(
                f"\nMirror Success Rate: {success_count}/{len(TEST_PAPERS)} ({success_count/len(TEST_PAPERS)*100:.1f}%)"
            )

        # Test LibGen
        print("\n\n" + "=" * 80)
        print("TESTING LIBGEN MIRRORS")
        print("=" * 80)

        for mirror in LIBGEN_MIRRORS:
            print(f"\nMirror: {mirror}")
            print("-" * 60)

            mirror_results = []

            for paper in TEST_PAPERS:
                success, pdf_url, pattern, snippet = await test_libgen_mirror(
                    mirror, paper, session, PDF_PATTERNS
                )

                mirror_results.append(
                    {
                        "paper": paper.title[:40],
                        "success": success,
                        "pdf_url": pdf_url[:60] if pdf_url else None,
                        "pattern": pattern,
                    }
                )

                if success:
                    print(f"  [OK] {paper.title[:40]:40} via {pattern}")
                else:
                    print(f"  [--] {paper.title[:40]:40}")

                await asyncio.sleep(2)

            results["libgen"][mirror] = mirror_results

            success_count = sum(1 for r in mirror_results if r["success"])
            print(
                f"\nMirror Success Rate: {success_count}/{len(TEST_PAPERS)} ({success_count/len(TEST_PAPERS)*100:.1f}%)"
            )

    # Analysis
    print("\n\n" + "=" * 80)
    print("PATTERN ANALYSIS")
    print("=" * 80)

    print(f"\n{'Pattern Name':30} {'Successes':>10} {'Attempts':>10} {'Success %':>12}")
    print("-" * 80)

    for pattern in sorted(PDF_PATTERNS, key=lambda p: p.success_rate(), reverse=True):
        if pattern.total_attempts > 0:
            print(
                f"{pattern.name:30} {pattern.successes:>10} {pattern.total_attempts:>10} {pattern.success_rate():>11.1f}%"
            )

    # Best patterns
    print("\n\nMOST SUCCESSFUL PATTERNS:")
    print("-" * 60)
    working_patterns = [p for p in PDF_PATTERNS if p.successes > 0]
    for pattern in sorted(working_patterns, key=lambda p: p.successes, reverse=True)[
        :5
    ]:
        print(f"  {pattern.successes:2}x  {pattern.name:25} - {pattern.description}")

    # Mirror comparison
    print("\n\n" + "=" * 80)
    print("MIRROR PERFORMANCE COMPARISON")
    print("=" * 80)

    print("\nSci-Hub Mirrors:")
    for mirror, mirror_results in results["scihub"].items():
        success_count = sum(1 for r in mirror_results if r["success"])
        print(
            f"  {mirror:30} {success_count:>2}/{len(TEST_PAPERS)} ({success_count/len(TEST_PAPERS)*100:>5.1f}%)"
        )

    print("\nLibGen Mirrors:")
    for mirror, mirror_results in results["libgen"].items():
        success_count = sum(1 for r in mirror_results if r["success"])
        print(
            f"  {mirror:30} {success_count:>2}/{len(TEST_PAPERS)} ({success_count/len(TEST_PAPERS)*100:>5.1f}%)"
        )

    # Recommendations
    print("\n\n" + "=" * 80)
    print("RECOMMENDATIONS FOR IMPLEMENTATION")
    print("=" * 80)

    best_patterns = sorted(working_patterns, key=lambda p: p.successes, reverse=True)[
        :3
    ]

    print("\n1. IMPLEMENT THESE PATTERNS (in order):")
    for i, pattern in enumerate(best_patterns, 1):
        print(f"   {i}. {pattern.name:25} - {pattern.description}")
        print(f"      Regex: {pattern.regex[:70]}...")

    best_scihub = max(
        results["scihub"].items(), key=lambda x: sum(1 for r in x[1] if r["success"])
    )
    print(f"\n2. BEST SCI-HUB MIRROR: {best_scihub[0]}")

    if results["libgen"]:
        best_libgen = max(
            results["libgen"].items(),
            key=lambda x: sum(1 for r in x[1] if r["success"]),
        )
        print(f"\n3. BEST LIBGEN MIRROR: {best_libgen[0]}")

    print("\n4. RECOMMENDED WATERFALL ORDER:")
    print("   1. Sci-Hub (most comprehensive)")
    print("   2. LibGen (good for books/textbooks)")
    print("   3. Use best working mirrors first")

    return results


if __name__ == "__main__":
    asyncio.run(comprehensive_exploration())
