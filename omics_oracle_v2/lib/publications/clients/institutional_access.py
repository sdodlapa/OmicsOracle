"""
Institutional Access Manager for Journal Articles

This module provides mechanisms to access paywalled journal articles
through institutional subscriptions (Old Dominion University, Georgia Tech).

Methods supported:
1. EZProxy authentication (most common)
2. VPN/proxy routing
3. Shibboleth/SAML authentication
4. Library link resolvers (OpenURL)
5. Unpaywall/Open Access fallback
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode, urlparse

from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class InstitutionType(str, Enum):
    """Supported institutions."""

    OLD_DOMINION = "odu"
    GEORGIA_TECH = "gatech"


@dataclass
class InstitutionalConfig:
    """
    Configuration for institutional access.

    Attributes:
        institution: Institution type
        ezproxy_url: EZProxy server URL (most common method)
        vpn_proxy: VPN proxy server (if using VPN routing)
        shibboleth_idp: Shibboleth Identity Provider URL
        openurl_resolver: OpenURL link resolver
        credentials: Authentication credentials (if needed)
        prefer_open_access: Try open access first before institutional
    """

    institution: InstitutionType

    # EZProxy (most common)
    ezproxy_url: Optional[str] = None

    # VPN/Proxy routing
    vpn_proxy: Optional[str] = None
    vpn_enabled: bool = False

    # Shibboleth/SAML
    shibboleth_idp: Optional[str] = None

    # OpenURL resolver
    openurl_resolver: Optional[str] = None

    # Authentication
    credentials: Dict[str, str] = field(default_factory=dict)

    # Strategy
    prefer_open_access: bool = True
    fallback_methods: List[str] = field(default_factory=lambda: ["unpaywall", "ezproxy", "openurl", "direct"])


# Pre-configured institutional settings
INSTITUTIONAL_CONFIGS = {
    InstitutionType.OLD_DOMINION: InstitutionalConfig(
        institution=InstitutionType.OLD_DOMINION,
        ezproxy_url="https://proxy.lib.odu.edu/login?url=",
        openurl_resolver="https://odu.illiad.oclc.org/illiad/illiad.dll/OpenURL",
        shibboleth_idp="https://shib.odu.edu/idp/shibboleth",
        fallback_methods=["unpaywall", "ezproxy", "openurl", "direct"],
    ),
    InstitutionType.GEORGIA_TECH: InstitutionalConfig(
        institution=InstitutionType.GEORGIA_TECH,
        ezproxy_url="",  # Georgia Tech uses VPN, not EZProxy
        openurl_resolver="https://gatech-primo.hosted.exlibrisgroup.com/primo-explore/search",
        shibboleth_idp="https://login.gatech.edu/idp/shibboleth",
        fallback_methods=["unpaywall", "direct", "openurl"],  # Direct DOI/URL for VPN access
    ),
}


class InstitutionalAccessManager:
    """
    Manager for accessing journal articles through institutional subscriptions.

    This class provides multiple strategies to access paywalled content:
    1. Unpaywall API (free, legal OA versions)
    2. EZProxy URL rewriting (most common institutional access)
    3. OpenURL resolvers (library link resolvers)
    4. Direct publisher access (if institution has IP range access)

    Example:
        >>> manager = InstitutionalAccessManager(
        ...     institution=InstitutionType.GEORGIA_TECH
        ... )
        >>> url = manager.get_access_url(publication)
        >>> pdf_url = manager.get_pdf_url(publication)
    """

    def __init__(
        self,
        institution: InstitutionType = InstitutionType.GEORGIA_TECH,
        config: Optional[InstitutionalConfig] = None,
    ):
        """
        Initialize institutional access manager.

        Args:
            institution: Institution type (ODU or Georgia Tech)
            config: Custom configuration (uses defaults if not provided)
        """
        self.institution = institution

        # Use provided config or default
        if config:
            self.config = config
        else:
            self.config = INSTITUTIONAL_CONFIGS.get(institution)
            if not self.config:
                logger.warning(f"No config for {institution}, using Georgia Tech defaults")
                self.config = INSTITUTIONAL_CONFIGS[InstitutionType.GEORGIA_TECH]

        logger.info(f"InstitutionalAccessManager initialized for {institution.value}")

    def get_access_url(self, publication: Publication, prefer_method: Optional[str] = None) -> Optional[str]:
        """
        Get accessible URL for publication using institutional access.

        Tries multiple methods in order:
        1. Unpaywall (if prefer_open_access=True)
        2. EZProxy URL
        3. OpenURL resolver
        4. Direct URL

        Args:
            publication: Publication to access
            prefer_method: Preferred access method ("ezproxy", "openurl", etc.)

        Returns:
            Accessible URL or None if not available
        """
        # Determine method order
        if prefer_method:
            methods = [prefer_method] + [m for m in self.config.fallback_methods if m != prefer_method]
        else:
            methods = self.config.fallback_methods

        # Try each method
        for method in methods:
            try:
                if method == "unpaywall":
                    url = self._try_unpaywall(publication)
                elif method == "ezproxy":
                    url = self._try_ezproxy(publication)
                elif method == "openurl":
                    url = self._try_openurl(publication)
                elif method == "direct":
                    # For Georgia Tech VPN access, prefer DOI links
                    if self.config.institution == InstitutionType.GEORGIA_TECH and publication.doi:
                        url = f"https://doi.org/{publication.doi}"
                    else:
                        url = publication.url
                else:
                    continue

                if url:
                    logger.info(f"Found access via {method}: {url[:100]}...")
                    return url
            except Exception as e:
                logger.debug(f"Method {method} failed: {e}")
                continue

        logger.warning(f"No access method worked for {publication.title[:50]}...")
        return None

    def get_pdf_url(self, publication: Publication, prefer_method: Optional[str] = None) -> Optional[str]:
        """
        Get direct PDF URL using institutional access.

        Args:
            publication: Publication to get PDF for
            prefer_method: Preferred access method

        Returns:
            PDF URL or None
        """
        # First try: existing PDF URL through EZProxy
        if publication.pdf_url:
            if self.config.ezproxy_url:
                return self._ezproxy_rewrite_url(publication.pdf_url)
            return publication.pdf_url

        # Second try: PMC full text
        if publication.pmcid:
            pmc_pdf = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication.pmcid}/pdf/"
            return pmc_pdf

        # Third try: Unpaywall
        unpaywall_url = self._try_unpaywall(publication)
        if unpaywall_url and unpaywall_url.endswith(".pdf"):
            return unpaywall_url

        # Fourth try: DOI-based PDF (common publishers)
        if publication.doi:
            # Try common publisher PDF patterns
            pdf_patterns = self._get_publisher_pdf_patterns(publication.doi)
            for pdf_url in pdf_patterns:
                if self.config.ezproxy_url:
                    return self._ezproxy_rewrite_url(pdf_url)
                return pdf_url

        return None

    def _try_unpaywall(self, publication: Publication) -> Optional[str]:
        """
        Try to get open access version via Unpaywall API.

        Unpaywall is a database of free, legal OA articles.
        API: https://unpaywall.org/products/api

        Args:
            publication: Publication to check

        Returns:
            OA URL or None
        """
        if not publication.doi:
            return None

        # Unpaywall API endpoint
        email = "omicsoracle@example.com"  # Replace with your email
        api_url = f"https://api.unpaywall.org/v2/{publication.doi}?email={email}"

        try:
            import requests

            response = requests.get(api_url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # Check if OA available
                if data.get("is_oa"):
                    # Prefer publisher PDF
                    best_oa = data.get("best_oa_location")
                    if best_oa:
                        pdf_url = best_oa.get("url_for_pdf")
                        if pdf_url:
                            logger.info(f"Found OA PDF via Unpaywall: {pdf_url}")
                            return pdf_url

                        landing_url = best_oa.get("url")
                        if landing_url:
                            logger.info(f"Found OA landing page via Unpaywall: {landing_url}")
                            return landing_url

        except Exception as e:
            logger.debug(f"Unpaywall lookup failed: {e}")

        return None

    def _try_ezproxy(self, publication: Publication) -> Optional[str]:
        """
        Generate EZProxy URL for institutional access.

        For Georgia Tech: Returns direct DOI/URL (access via VPN)
        For other institutions: Generates EZProxy wrapped URL

        Args:
            publication: Publication to access

        Returns:
            EZProxy URL, direct URL (if GT), or None
        """
        # Georgia Tech uses VPN instead of EZProxy
        if self.config.institution == InstitutionType.GEORGIA_TECH:
            # Return direct DOI or publisher URL
            # User needs to connect via VPN first
            if publication.doi:
                return f"https://doi.org/{publication.doi}"
            elif publication.url:
                return publication.url
            else:
                return None
        
        # Other institutions: use EZProxy if configured
        if not self.config.ezproxy_url:
            return None

        # Get target URL (DOI resolver or direct URL)
        target_url = None

        if publication.doi:
            target_url = f"https://doi.org/{publication.doi}"
        elif publication.url:
            target_url = publication.url
        else:
            return None

        # Generate EZProxy URL
        ezproxy_url = self._ezproxy_rewrite_url(target_url)

        return ezproxy_url

    def _ezproxy_rewrite_url(self, url: str) -> str:
        """
        Rewrite URL to go through EZProxy.

        Args:
            url: Original URL

        Returns:
            EZProxy-wrapped URL
        """
        if not self.config.ezproxy_url:
            return url

        # EZProxy format: https://proxy.lib.odu.edu/login?url=TARGET_URL
        return f"{self.config.ezproxy_url}{quote(url, safe='')}"

    def _try_openurl(self, publication: Publication) -> Optional[str]:
        """
        Generate OpenURL link resolver URL.

        OpenURL resolvers help find article access through library subscriptions.

        Args:
            publication: Publication to resolve

        Returns:
            OpenURL resolver link or None
        """
        if not self.config.openurl_resolver:
            return None

        # Build OpenURL context object (COinS format)
        params = {}

        # Required
        params["ctx_ver"] = "Z39.88-2004"
        params["rft_val_fmt"] = "info:ofi/fmt:kev:mtx:journal"

        # Article metadata
        if publication.title:
            params["rft.atitle"] = publication.title
        if publication.journal:
            params["rft.jtitle"] = publication.journal
        if publication.authors:
            params["rft.au"] = publication.authors[0]
        if publication.publication_date:
            params["rft.date"] = publication.publication_date.strftime("%Y")

        # Identifiers
        if publication.doi:
            params["rft_id"] = f"info:doi/{publication.doi}"
        if publication.pmid:
            params["rft_id"] = f"info:pmid/{publication.pmid}"

        # Build URL
        query_string = urlencode(params)
        openurl = f"{self.config.openurl_resolver}?{query_string}"

        return openurl

    def _get_publisher_pdf_patterns(self, doi: str) -> List[str]:
        """
        Generate likely PDF URLs based on DOI and publisher patterns.

        Args:
            doi: DOI of publication

        Returns:
            List of possible PDF URLs
        """
        pdf_urls = []

        # Extract publisher from DOI prefix
        doi_prefix = doi.split("/")[0]

        # Common publisher PDF patterns
        patterns = {
            # Elsevier/ScienceDirect
            "10.1016": f"https://www.sciencedirect.com/science/article/pii/{doi.split('/')[-1]}/pdfft",
            # Springer
            "10.1007": f"https://link.springer.com/content/pdf/{doi}.pdf",
            # Nature
            "10.1038": f"https://www.nature.com/articles/{doi.split('/')[-1]}.pdf",
            # Wiley
            "10.1002": f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
            # PLOS
            "10.1371": f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable",
            # Oxford Academic
            "10.1093": f"https://academic.oup.com/view-large/article/{doi.split('/')[-1]}/pdf",
        }

        # Check for matching pattern
        for prefix, pattern in patterns.items():
            if doi_prefix.startswith(prefix):
                pdf_urls.append(pattern)

        # Generic DOI resolver (always add as fallback)
        pdf_urls.append(f"https://doi.org/{doi}")

        return pdf_urls

    def check_access_status(self, publication: Publication) -> Dict[str, bool]:
        """
        Check which access methods are available for a publication.

        Args:
            publication: Publication to check

        Returns:
            Dictionary of {method: available}
        """
        status = {}

        # Check each method
        status["unpaywall"] = bool(self._try_unpaywall(publication))
        
        # For Georgia Tech, check if VPN access is possible (DOI or URL exists)
        # For other institutions, check EZProxy
        if self.config.institution == InstitutionType.GEORGIA_TECH:
            status["vpn"] = bool(publication.doi or publication.url)
            status["ezproxy"] = False  # GT doesn't use EZProxy
        else:
            status["ezproxy"] = bool(self.config.ezproxy_url and (publication.doi or publication.url))
            status["vpn"] = False
            
        status["openurl"] = bool(self.config.openurl_resolver and publication.title)
        status["direct"] = bool(publication.url)
        status["pmc"] = bool(publication.pmcid)

        return status

    def get_access_instructions(self, publication: Publication) -> Dict[str, str]:
        """
        Get human-readable instructions for accessing publication.

        Args:
            publication: Publication to access

        Returns:
            Dictionary with access instructions
        """
        instructions = {}

        # Check Unpaywall
        unpaywall_url = self._try_unpaywall(publication)
        if unpaywall_url:
            instructions["open_access"] = f"✅ Free open access version available: {unpaywall_url}"

        # EZProxy
        if self.config.ezproxy_url:
            ezproxy_url = self._try_ezproxy(publication)
            if ezproxy_url:
                instructions["institutional"] = (
                    f"🏛️ Access via {self.institution.value.upper()} library: {ezproxy_url}\n"
                    f"Note: You may need to login with your university credentials."
                )

        # OpenURL
        if self.config.openurl_resolver:
            openurl = self._try_openurl(publication)
            if openurl:
                instructions["link_resolver"] = f"🔗 Find full text via library resolver: {openurl}"

        # PMC
        if publication.pmcid:
            instructions["pmc"] = (
                f"📖 Free full text on PubMed Central: "
                f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication.pmcid}/"
            )

        return instructions


def create_institutional_manager(institution: str = "gatech") -> InstitutionalAccessManager:
    """
    Factory function to create institutional access manager.

    Args:
        institution: "odu" or "gatech"

    Returns:
        Configured InstitutionalAccessManager
    """
    inst_type = (
        InstitutionType.GEORGIA_TECH if institution.lower() == "gatech" else InstitutionType.OLD_DOMINION
    )
    return InstitutionalAccessManager(institution=inst_type)
