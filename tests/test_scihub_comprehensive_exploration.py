"""
COMPREHENSIVE SCI-HUB EXPLORATION

This test will:
1. Test ALL known Sci-Hub mirrors
2. Try 100 diverse papers
3. Record ALL HTML response patterns
4. Extract ALL PDF URL patterns
5. Measure success rate per mirror
6. Identify best mirrors and patterns

Total tests: ~900 (100 papers × 9 mirrors)
Estimated time: 45-60 minutes with rate limiting
"""

import asyncio
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the dataset
import importlib.util

spec = importlib.util.spec_from_file_location(
    "diverse_papers", Path(__file__).parent / "test_datasets" / "100_diverse_papers.py"
)
diverse_papers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diverse_papers)
COMPREHENSIVE_100_PAPERS = diverse_papers.COMPREHENSIVE_100_PAPERS

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# EXPANDED SCI-HUB MIRROR LIST
# ============================================================================
SCIHUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.ren",
    "https://sci-hub.si",
    "https://sci-hub.ee",  # NEW
    "https://sci-hub.wf",  # NEW
    "https://sci-hub.tf",  # NEW
    "https://sci-hub.mksa.top",  # NEW - rotating mirror
]


class PDFPattern:
    """Represents a PDF URL extraction pattern."""

    def __init__(self, name: str, regex: str, description: str):
        self.name = name
        self.regex = regex
        self.description = description
        self.compiled = re.compile(regex, re.IGNORECASE)
        self.successes = 0
        self.failures = 0


# ============================================================================
# COMPREHENSIVE PDF EXTRACTION PATTERNS
# ============================================================================
PDF_PATTERNS = [
    # Pattern 1: embed tag with any src
    PDFPattern("embed_any_src", r'<embed[^>]+src="([^"]+)"', "Embed tag with any src attribute"),
    # Pattern 2: embed tag with PDF in src
    PDFPattern("embed_pdf_src", r'<embed[^>]+src="([^"]+\.pdf[^"]*)"', "Embed tag with .pdf in src"),
    # Pattern 3: iframe with any src
    PDFPattern("iframe_any_src", r'<iframe[^>]+src="([^"]+)"', "iFrame with any src attribute"),
    # Pattern 4: iframe with PDF in src
    PDFPattern("iframe_pdf_src", r'<iframe[^>]+src="([^"]+\.pdf[^"]*)"', "iFrame with .pdf in src"),
    # Pattern 5: Meta redirect
    PDFPattern("meta_redirect", r'<meta[^>]+content="0;url=([^"]+)"', "Meta tag redirect"),
    # Pattern 6: JavaScript location redirect
    PDFPattern(
        "js_location",
        r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
        "JavaScript location.href redirect",
    ),
    # Pattern 7: Button onclick
    PDFPattern(
        "button_onclick",
        r'<button[^>]+onclick="[^"]*location\.href\s*=\s*["\']([^"\']+)["\']',
        "Button with onclick location.href",
    ),
    # Pattern 8: Download link
    PDFPattern("download_link", r'<a[^>]+download[^>]*href="([^"]+\.pdf[^"]*)"', "Download link with href"),
    # Pattern 9: Protocol-relative URL (// prefix)
    PDFPattern(
        "protocol_relative",
        r'(?:src|href)="(//[^"]+\.pdf[^"]*)"',
        "Protocol-relative URL (//domain/path.pdf)",
    ),
    # Pattern 10: Absolute HTTPS URL
    PDFPattern("absolute_https", r'https://[^"\s<>]+\.pdf[^"\s<>]*', "Absolute HTTPS URL anywhere in HTML"),
    # Pattern 11: Absolute HTTP URL
    PDFPattern("absolute_http", r'http://[^"\s<>]+\.pdf[^"\s<>]*', "Absolute HTTP URL anywhere in HTML"),
    # Pattern 12: PDF in id or data attribute
    PDFPattern("data_attribute", r'data-[^=]+=\s*"([^"]+\.pdf[^"]*)"', "Data attribute with PDF"),
    # Pattern 13: PDF.js viewer
    PDFPattern("pdfjs_viewer", r'viewer\.html\?file=([^"&\s]+)', "PDF.js viewer with file parameter"),
    # Pattern 14: Direct download parameter
    PDFPattern(
        "download_param",
        r'download\?[^"]*(?:file|url|path)=([^"&\s]+\.pdf[^"&\s]*)',
        "Download URL with file parameter",
    ),
]


class SciHubExplorer:
    """Comprehensive Sci-Hub exploration class."""

    def __init__(self):
        self.session = None
        self.ssl_context = None
        self.results = {
            "mirrors": {},  # mirror -> stats
            "patterns": {},  # pattern -> stats
            "papers": {},  # doi -> results
            "html_samples": [],  # Sample HTML responses
            "errors": defaultdict(int),
        }
        self.start_time = None

    async def __aenter__(self):
        import os
        import ssl

        import aiohttp

        self.ssl_context = ssl.create_default_context()
        if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

        # Add proper headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(headers=headers, connector=connector)
        self.start_time = datetime.now()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _normalize_url(self, url: str, mirror: str) -> str:
        """Normalize URL to absolute HTTPS."""
        if url.startswith("https://") or url.startswith("http://"):
            return url
        elif url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            return mirror + url
        else:
            return mirror + "/" + url

    async def test_mirror_accessibility(self, mirror: str) -> bool:
        """Test if a mirror is accessible."""
        try:
            async with self.session.get(mirror, timeout=15) as response:
                # Accept 200 or 301/302 redirects as "accessible"
                return response.status in [200, 301, 302]
        except Exception as e:
            logger.debug(f"Mirror {mirror} not accessible: {e}")
            return False

    async def get_html_response(self, mirror: str, doi: str) -> Optional[Dict]:
        """Get HTML response from Sci-Hub mirror."""
        from urllib.parse import quote

        url = f"{mirror}/{quote(doi)}"

        try:
            async with self.session.get(url, timeout=20) as response:
                # Follow redirects and accept 200/301/302
                if response.status not in [200, 301, 302]:
                    logger.debug(f"Unexpected status {response.status} from {mirror}/{doi}")
                    return None

                html = await response.text()

                return {
                    "status": response.status,
                    "html": html,
                    "length": len(html),
                    "content_type": response.headers.get("content-type", ""),
                    "has_captcha": "captcha" in html.lower(),
                    "has_cloudflare": "cloudflare" in html.lower(),
                    "has_pdf_ref": ".pdf" in html.lower(),
                }
        except asyncio.TimeoutError:
            self.results["errors"]["timeout"] += 1
            return None
        except Exception as e:
            self.results["errors"][type(e).__name__] += 1
            logger.debug(f"Error getting HTML from {mirror}/{doi}: {e}")
            return None

    def try_all_patterns(self, html: str, mirror: str) -> Optional[Dict]:
        """Try all PDF extraction patterns on HTML."""
        for pattern in PDF_PATTERNS:
            match = pattern.compiled.search(html)
            if match:
                url = match.group(1) if match.groups() else match.group(0)

                # Verify it looks like a PDF URL
                if ".pdf" in url.lower():
                    normalized_url = self._normalize_url(url, mirror)
                    pattern.successes += 1

                    return {
                        "pattern": pattern.name,
                        "url": normalized_url,
                        "raw_url": url,
                    }

        # No pattern matched
        for pattern in PDF_PATTERNS:
            pattern.failures += 1

        return None

    async def test_paper_on_mirror(self, mirror: str, paper: Dict, save_html_samples: bool = False) -> Dict:
        """Test a single paper on a single mirror."""
        doi = paper["doi"]

        # Get HTML response
        response = await self.get_html_response(mirror, doi)

        if not response:
            return {
                "mirror": mirror,
                "doi": doi,
                "success": False,
                "error": "No response",
            }

        # Try all extraction patterns
        pdf_result = self.try_all_patterns(response["html"], mirror)

        result = {
            "mirror": mirror,
            "doi": doi,
            "success": pdf_result is not None,
            "status": response["status"],
            "html_length": response["length"],
            "has_captcha": response["has_captcha"],
            "has_cloudflare": response["has_cloudflare"],
            "has_pdf_ref": response["has_pdf_ref"],
        }

        if pdf_result:
            result.update(
                {
                    "pattern": pdf_result["pattern"],
                    "pdf_url": pdf_result["url"],
                    "raw_url": pdf_result["raw_url"],
                }
            )
        else:
            result["error"] = "No pattern matched"

        # Save HTML samples
        if save_html_samples and len(self.results["html_samples"]) < 20:
            self.results["html_samples"].append(
                {
                    "mirror": mirror,
                    "doi": doi,
                    "html": response["html"][:2000],  # First 2000 chars
                    "full_length": response["length"],
                    "success": pdf_result is not None,
                }
            )

        return result

    async def test_all_papers_on_mirror(
        self, mirror: str, papers: List[Dict], rate_limit_delay: float = 2.0
    ) -> List[Dict]:
        """Test all papers on a single mirror."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing mirror: {mirror}")
        logger.info(f"{'='*80}")

        # Check if mirror is accessible
        if not await self.test_mirror_accessibility(mirror):
            logger.warning(f"⚠️  Mirror {mirror} is not accessible, skipping...")
            return []

        logger.info(f"✓ Mirror {mirror} is accessible")

        results = []
        for i, paper in enumerate(papers, 1):
            result = await self.test_paper_on_mirror(
                mirror, paper, save_html_samples=(i <= 5)  # Save first 5 samples per mirror
            )
            results.append(result)

            # Progress logging
            if i % 10 == 0 or i == len(papers):
                success_count = sum(1 for r in results if r["success"])
                logger.info(
                    f"  Progress: {i}/{len(papers)} papers tested, "
                    f"{success_count} found ({success_count/i*100:.1f}%)"
                )

            # Rate limiting
            await asyncio.sleep(rate_limit_delay)

        return results

    def compile_statistics(self):
        """Compile final statistics."""
        logger.info(f"\n{'='*80}")
        logger.info("COMPILING STATISTICS")
        logger.info(f"{'='*80}")

        # Mirror statistics
        for mirror, papers_results in self.results["mirrors"].items():
            success_count = sum(1 for r in papers_results if r["success"])
            total = len(papers_results)

            self.results["mirrors"][mirror] = {
                "total": total,
                "success": success_count,
                "failed": total - success_count,
                "success_rate": (success_count / total * 100) if total > 0 else 0,
                "patterns_used": defaultdict(int),
            }

            # Count patterns used
            for r in papers_results:
                if r["success"] and "pattern" in r:
                    self.results["mirrors"][mirror]["patterns_used"][r["pattern"]] += 1

        # Pattern statistics
        for pattern in PDF_PATTERNS:
            self.results["patterns"][pattern.name] = {
                "description": pattern.description,
                "successes": pattern.successes,
                "failures": pattern.failures,
                "success_rate": (
                    pattern.successes / (pattern.successes + pattern.failures) * 100
                    if (pattern.successes + pattern.failures) > 0
                    else 0
                ),
            }

        # Paper statistics (which papers found on which mirrors)
        all_results = []
        for mirror_results in self.results["mirrors"].values():
            all_results.extend(mirror_results) if isinstance(mirror_results, list) else None

        paper_stats = defaultdict(lambda: {"found_on": [], "not_found_on": []})
        for result in all_results:
            if isinstance(result, dict) and "doi" in result:
                doi = result["doi"]
                mirror = result["mirror"]
                if result["success"]:
                    paper_stats[doi]["found_on"].append(mirror)
                else:
                    paper_stats[doi]["not_found_on"].append(mirror)

        self.results["papers"] = dict(paper_stats)

    def save_results(self, output_file: str):
        """Save results to JSON file."""
        # Convert defaultdicts to regular dicts for JSON serialization
        output = {
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "duration_minutes": (
                (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else None
            ),
            "mirrors": dict(self.results["mirrors"]),
            "patterns": dict(self.results["patterns"]),
            "papers": dict(self.results["papers"]),
            "html_samples": self.results["html_samples"],
            "errors": dict(self.results["errors"]),
        }

        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        logger.info(f"\n✓ Results saved to: {output_file}")

    def print_summary(self):
        """Print summary of results."""
        print("\n" + "=" * 80)
        print("SCI-HUB EXPLORATION SUMMARY")
        print("=" * 80)

        # Mirror performance
        print("\nMIRROR PERFORMANCE:")
        print("-" * 80)
        mirror_stats = []
        for mirror, stats in self.results["mirrors"].items():
            if isinstance(stats, dict) and "success_rate" in stats:
                mirror_stats.append((mirror, stats))

        for mirror, stats in sorted(mirror_stats, key=lambda x: x[1]["success_rate"], reverse=True):
            print(f"{mirror:30} → {stats['success']}/{stats['total']} ({stats['success_rate']:.1f}%)")
            if stats["patterns_used"]:
                top_patterns = sorted(stats["patterns_used"].items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"  Top patterns: {', '.join(f'{p}({c})' for p, c in top_patterns)}")

        # Pattern performance
        print("\nPATTERN PERFORMANCE:")
        print("-" * 80)
        pattern_stats = sorted(
            self.results["patterns"].items(), key=lambda x: x[1]["success_rate"], reverse=True
        )
        for pattern_name, stats in pattern_stats[:10]:  # Top 10
            print(f"{pattern_name:25} → {stats['successes']:3} successes " f"({stats['success_rate']:5.1f}%)")

        # Coverage by paper type
        print("\nCOVERAGE BY PAPER TYPE:")
        print("-" * 80)
        type_stats = defaultdict(lambda: {"total": 0, "found": 0})
        for paper in COMPREHENSIVE_100_PAPERS:
            doi = paper["doi"]
            ptype = paper.get("type", "unknown")
            type_stats[ptype]["total"] += 1
            if doi in self.results["papers"] and self.results["papers"][doi]["found_on"]:
                type_stats[ptype]["found"] += 1

        for ptype, stats in sorted(type_stats.items(), key=lambda x: x[0]):
            rate = (stats["found"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"{ptype:15} → {stats['found']:2}/{stats['total']:2} ({rate:5.1f}%)")

        # Errors
        if self.results["errors"]:
            print("\nERRORS:")
            print("-" * 80)
            for error_type, count in sorted(self.results["errors"].items(), key=lambda x: x[1], reverse=True):
                print(f"{error_type:30} → {count}")


async def run_comprehensive_exploration():
    """Run comprehensive Sci-Hub exploration."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE SCI-HUB EXPLORATION")
    logger.info("=" * 80)
    logger.info(f"Total papers: {len(COMPREHENSIVE_100_PAPERS)}")
    logger.info(f"Total mirrors: {len(SCIHUB_MIRRORS)}")
    logger.info(f"Total patterns: {len(PDF_PATTERNS)}")
    logger.info(f"Estimated tests: {len(COMPREHENSIVE_100_PAPERS) * len(SCIHUB_MIRRORS)}")
    logger.info("=" * 80)

    async with SciHubExplorer() as explorer:
        # Test each mirror with all papers
        for mirror in SCIHUB_MIRRORS:
            results = await explorer.test_all_papers_on_mirror(
                mirror, COMPREHENSIVE_100_PAPERS, rate_limit_delay=1.5  # 1.5s between requests
            )
            explorer.results["mirrors"][mirror] = results

        # Compile statistics
        explorer.compile_statistics()

        # Save results
        output_file = "scihub_exploration_results.json"
        explorer.save_results(output_file)

        # Print summary
        explorer.print_summary()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_exploration())
