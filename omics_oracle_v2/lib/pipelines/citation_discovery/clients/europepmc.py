"""
Europe PMC API Client

Europe PMC is a comprehensive life sciences literature database providing
access to 42+ million abstracts and 7+ million full-text articles.

API Features:
- Free and open access (no API key required)
- Rich citation data with context
- Full-text search capabilities
- Open Access content
- RESTful API with JSON responses

Rate Limits:
- No strict rate limits for reasonable use
- Recommended: ~3 requests/second

Official API Docs: https://europepmc.org/RestfulWebService
"""

import logging
import ssl
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import \
    EuropePMCConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.metadata_enrichment import \
    MetadataEnrichmentService
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication, PublicationSource)

logger = logging.getLogger(__name__)


class EuropePMCClient:
    """
    Client for Europe PMC API

    Features:
    - Find papers citing a given publication (by PMID, DOI, or PMC ID)
    - Search papers by text query
    - Get full-text content for Open Access articles
    - Rich metadata (abstract, citations, references, etc.)

    Examples:
        # Find papers citing a specific paper
        client = EuropePMCClient()
        citations = client.get_citing_papers(pmid="12345678")

        # Search for papers about a topic
        papers = client.search("GEO dataset GSE12345")
    """

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, config: Optional[EuropePMCConfig] = None):
        """
        Initialize Europe PMC client

        Args:
            config: Optional configuration
        """
        self.config = config or EuropePMCConfig()
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "OmicsOracle/2.0"

        # CRITICAL: Disable SSL verification at session level
        # This is required for institutional VPN/proxies that use self-signed certificates
        self.session.verify = False

        # Suppress SSL warnings (optional but cleaner logs)
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Rate limiting state
        self._last_request_time = 0.0
        self._min_interval = 1.0 / self.config.requests_per_second

        # Metadata enrichment service
        self.enrichment_service = MetadataEnrichmentService()

        logger.info(
            f"✓ Europe PMC client initialized (rate: {self.config.requests_per_second} req/s)"
        )

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request with retry logic

        Args:
            endpoint: API endpoint (e.g., "search")
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Always request JSON format with core result type for full metadata
        if params is None:
            params = {}
        params["format"] = "json"
        # Request core results to get fullTextUrlList field
        if "resulttype" not in params:
            params["resulttype"] = "core"

        for attempt in range(self.config.retries):
            try:
                self._rate_limit()
                response = self.session.get(
                    url, params=params, timeout=self.config.timeout
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2.0))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Handle errors
                if response.status_code != 200:
                    logger.error(
                        f"API error {response.status_code}: {response.text[:200]}"
                    )
                    return None

                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.config.retries})"
                )
                if attempt < self.config.retries - 1:
                    time.sleep(1.0 * (attempt + 1))
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None

        return None

    def get_citing_papers(
        self,
        pmid: Optional[str] = None,
        doi: Optional[str] = None,
        pmc_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Publication]:
        """
        Get papers citing a given publication

        Args:
            pmid: PubMed ID (e.g., "12345678")
            doi: DOI (e.g., "10.1234/example")
            pmc_id: PubMed Central ID (e.g., "PMC123456")
            max_results: Maximum results to return

        Returns:
            List of citing publications
        """
        # Build query for citations
        if pmid:
            query = f"CITES:{pmid}_MED"
        elif pmc_id:
            query = f"CITES:{pmc_id}_PMC"
        elif doi:
            query = f'CITES:"{doi}"'
        else:
            logger.error("Must provide PMID, DOI, or PMC ID")
            return []

        logger.info(f"Finding papers citing via Europe PMC: {query}")

        # Search for citing papers
        params = {
            "query": query,
            "pageSize": min(max_results, 1000),  # Europe PMC max is 1000
            "cursorMark": "*",  # Start from beginning
        }

        response = self._make_request("search", params)
        if not response:
            return []

        # Parse results
        result_list = response.get("resultList", {})
        results = result_list.get("result", [])

        logger.info(f"Found {len(results)} citing papers for {query}")

        # Convert to Publication objects
        publications = []
        for result in results:
            try:
                pub = self._parse_result(result)
                if pub:
                    publications.append(pub)
            except Exception as e:
                logger.debug(f"Failed to parse result: {e}")
                continue

        return publications

    def search(self, query: str, max_results: int = 100) -> List[Publication]:
        """
        Search for papers by text query

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of publications matching query
        """
        logger.info(f"Searching Europe PMC: {query}")

        params = {
            "query": query,
            "pageSize": min(max_results, 1000),
            "cursorMark": "*",
        }

        response = self._make_request("search", params)
        if not response:
            return []

        # Parse results
        result_list = response.get("resultList", {})
        results = result_list.get("result", [])

        logger.info(f"Found {len(results)} results")

        # Convert to Publication objects
        publications = []
        for result in results:
            try:
                pub = self._parse_result(result)
                if pub:
                    publications.append(pub)
            except Exception as e:
                logger.debug(f"Failed to parse result: {e}")
                continue

        return publications

    def _parse_result(self, result: Dict) -> Optional[Publication]:
        """
        Parse Europe PMC result into Publication object

        Args:
            result: Raw result from API

        Returns:
            Publication object or None if parsing fails
        """
        try:
            # Extract IDs
            pmid = result.get("pmid")
            doi = result.get("doi")
            pmc_id = result.get("pmcid")

            # Title and abstract
            title = result.get("title", "").strip()
            abstract = result.get("abstractText", "").strip()

            # ROBUSTNESS FIX: Handle missing titles via enrichment
            enrichment_metadata = {}
            if not title:
                logger.warning(
                    f"Europe PMC result missing title "
                    f"(DOI: {doi}, PMID: {pmid}, PMC: {pmc_id})"
                )

                # Attempt enrichment via Crossref if DOI available
                if doi:
                    logger.info(f"Attempting Crossref enrichment for DOI: {doi}")
                    enriched_data = self.enrichment_service.enrich_from_doi(doi)

                    if enriched_data and enriched_data.get("title"):
                        title = enriched_data["title"]
                        logger.info(f"✅ Enriched title from Crossref: {title[:60]}...")
                        enrichment_metadata = {
                            "enrichment_source": "crossref",
                            "enrichment_fields": ["title"],
                        }
                    else:
                        logger.warning(f"❌ Crossref enrichment failed for DOI: {doi}")
                        # Try PMID enrichment
                        if pmid:
                            logger.info(f"Attempting PMID enrichment: {pmid}")
                            enriched_data = self.enrichment_service.enrich_from_pmid(
                                pmid
                            )
                            if enriched_data and enriched_data.get("title"):
                                title = enriched_data["title"]
                                logger.info(
                                    f"✅ Enriched title from PubMed: {title[:60]}..."
                                )
                                enrichment_metadata = {
                                    "enrichment_source": "pubmed",
                                    "enrichment_fields": ["title"],
                                }

                # If still no title, skip (can't store without ANY identifier)
                if not title:
                    logger.error(
                        f"Cannot recover title for Europe PMC result "
                        f"(DOI: {doi}, PMID: {pmid}, PMC: {pmc_id}) - "
                        f"skipping (potential loss of {result.get('citedByCount', 0)} citation paper)"
                    )
                    return None

            # Authors
            author_list = result.get("authorList", {}).get("author", [])
            authors = []
            for author in author_list:
                # Handle different author formats
                if isinstance(author, dict):
                    full_name = author.get("fullName", "")
                    if not full_name:
                        # Build from parts
                        first = author.get("firstName", "")
                        last = author.get("lastName", "")
                        full_name = f"{first} {last}".strip()
                    if full_name:
                        authors.append(full_name)
                elif isinstance(author, str):
                    authors.append(author)

            # Publication date
            pub_date = None
            pub_year = result.get("pubYear")
            if pub_year:
                try:
                    pub_date = datetime(int(pub_year), 1, 1)
                except (ValueError, TypeError):
                    pass

            # Journal
            journal = result.get("journalTitle") or result.get("journalInfo", {}).get(
                "journal", {}
            ).get("title")

            # Citation count
            citation_count = result.get("citedByCount", 0)

            # URL - landing page
            url = None
            if doi:
                url = f"https://doi.org/{doi}"
            elif pmid:
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
            elif pmc_id:
                url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}"

            # URL OPTIMIZATION: Extract PDF/fulltext URLs from fullTextUrlList
            pdf_url = None
            fulltext_url = None
            oa_status = None

            fulltext_url_list = result.get("fullTextUrlList", {})
            if fulltext_url_list and isinstance(fulltext_url_list, dict):
                fulltext_urls = fulltext_url_list.get("fullTextUrl", [])

                # Priority order for PDF extraction:
                # 1. Europe PMC PDF (OA)
                # 2. PMC PDF (OA)
                # 3. Any other OA PDF
                # 4. Subscription PDFs (low priority)

                europepmc_pdf = None
                pmc_pdf = None
                other_oa_pdf = None
                subscription_pdf = None
                europepmc_html = None

                for ft_url in fulltext_urls:
                    if not isinstance(ft_url, dict):
                        continue

                    url_str = ft_url.get("url", "").strip()
                    availability_code = ft_url.get("availabilityCode", "")
                    doc_style = ft_url.get("documentStyle", "")
                    site = ft_url.get("site", "")

                    if not url_str:
                        continue

                    # Categorize URLs
                    is_oa = availability_code == "OA"
                    is_pdf = doc_style == "pdf"
                    is_html = doc_style == "html"

                    if is_pdf:
                        if site == "Europe_PMC" and is_oa:
                            europepmc_pdf = url_str
                        elif site in ["PubMed Central", "PMC"] and is_oa:
                            pmc_pdf = url_str
                        elif is_oa:
                            other_oa_pdf = url_str
                        else:
                            subscription_pdf = url_str
                    elif is_html and site == "Europe_PMC" and is_oa:
                        europepmc_html = url_str

                # Select best PDF URL
                if europepmc_pdf:
                    pdf_url = europepmc_pdf
                    oa_status = "gold"  # Europe PMC OA
                elif pmc_pdf:
                    pdf_url = pmc_pdf
                    oa_status = "gold"
                elif other_oa_pdf:
                    pdf_url = other_oa_pdf
                    oa_status = "gold"
                elif subscription_pdf:
                    # Still store it - might be accessible via institutional access
                    pdf_url = subscription_pdf
                    oa_status = "subscription"

                # Fulltext HTML as alternative
                if europepmc_html:
                    fulltext_url = europepmc_html

            # Fallback: Construct PMC PDF URL if we have PMC ID but no PDF from API
            if not pdf_url and pmc_id and result.get("isOpenAccess") == "Y":
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
                oa_status = "gold"
                logger.debug(f"Constructed PMC PDF URL: {pdf_url}")

            pub = Publication(
                pmid=pmid,
                doi=doi,
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date,
                journal=journal,
                url=url,
                pdf_url=pdf_url,  # NEW: PDF URL for optimization
                citations=citation_count,
                source=PublicationSource.EUROPEPMC,
            )

            # Add enrichment metadata if present
            if enrichment_metadata:
                pub.metadata.update(enrichment_metadata)

            # Always add Europe PMC ID
            pub.metadata["europepmc_id"] = result.get("id")

            # Store URL metadata for optimization
            if pdf_url:
                pub.metadata["epmc_pdf_url"] = pdf_url
                pub.metadata["epmc_oa_status"] = oa_status
                pub.metadata["epmc_url_source"] = "fullTextUrlList"

            if fulltext_url:
                pub.metadata["epmc_fulltext_url"] = fulltext_url

            # Store OA flags
            pub.metadata["epmc_is_open_access"] = result.get("isOpenAccess") == "Y"
            pub.metadata["epmc_in_pmc"] = result.get("inPMC") == "Y"
            pub.metadata["epmc_has_pdf"] = result.get("hasPDF") == "Y"

            return pub

        except Exception as e:
            logger.debug(f"Failed to parse Europe PMC result: {e}")
            return None
