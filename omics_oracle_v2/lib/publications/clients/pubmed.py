"""
PubMed client using Biopython's Entrez interface.

This client provides access to PubMed and PubMed Central databases
through NCBI's E-utilities API.
"""

import logging
import os
import ssl
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Disable SSL verification if environment variable is set (for institutional networks)
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    from Bio import Entrez, Medline

    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("Biopython not available. PubMed client will not function.")

from omics_oracle_v2.lib.publications.clients.base import BasePublicationClient, FetchError, SearchError
from omics_oracle_v2.lib.publications.config import PubMedConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logger = logging.getLogger(__name__)

# Log SSL bypass status after logger is defined
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    logger.info("SSL verification disabled for PubMed (PYTHONHTTPSVERIFY=0)")


class PubMedClient(BasePublicationClient):
    """
    PubMed client using NCBI Entrez E-utilities.

    Features:
    - Search PubMed by query
    - Fetch publications by PMID
    - Support for MeSH terms
    - Automatic rate limiting
    - Batch fetching for efficiency

    Example:
        >>> config = PubMedConfig(email="user@example.com")
        >>> client = PubMedClient(config)
        >>> results = client.search("cancer genomics", max_results=10)
    """

    def __init__(self, config: PubMedConfig):
        """
        Initialize PubMed client.

        Args:
            config: PubMed configuration

        Raises:
            ImportError: If Biopython is not available
        """
        if not BIOPYTHON_AVAILABLE:
            raise ImportError(
                "Biopython is required for PubMed client. " "Install with: pip install biopython"
            )

        super().__init__(config)

        # Configure Entrez
        Entrez.email = config.email
        if config.api_key:
            Entrez.api_key = config.api_key
        Entrez.tool = config.tool_name

        # Rate limiting
        self._last_request_time = 0.0
        self._min_interval = 1.0 / config.requests_per_second

        logger.info(
            f"PubMed client initialized (email={config.email}, " f"rate={config.requests_per_second} req/s)"
        )

    @property
    def source_name(self) -> str:
        """Get source name."""
        return "pubmed"

    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _search_pubmed(self, query: str, max_results: int = 100, retstart: int = 0) -> List[str]:
        """
        Search PubMed and return list of PMIDs.

        Args:
            query: Search query
            max_results: Maximum results
            retstart: Starting index for pagination

        Returns:
            List of PMIDs

        Raises:
            SearchError: If search fails
        """
        try:
            self._rate_limit()

            # Perform search
            handle = Entrez.esearch(
                db=self.config.database,
                term=query,
                retmax=max_results,
                retstart=retstart,
                usehistory="y" if self.config.use_history else "n",
            )

            results = Entrez.read(handle)
            handle.close()

            pmids = results.get("IdList", [])
            logger.info(f"PubMed search found {len(pmids)} results for query: {query}")

            return pmids

        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            raise SearchError(f"Failed to search PubMed: {e}") from e

    def _fetch_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch publication details for list of PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of publication records

        Raises:
            FetchError: If fetch fails
        """
        if not pmids:
            return []

        try:
            # Fetch in batches
            records = []
            batch_size = min(self.config.batch_size, len(pmids))

            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i : i + batch_size]

                self._rate_limit()

                # Fetch batch
                handle = Entrez.efetch(
                    db=self.config.database,
                    id=batch_pmids,
                    rettype=self.config.return_type,
                    retmode="text",
                )

                # Parse Medline format
                batch_records = list(Medline.parse(handle))
                handle.close()

                records.extend(batch_records)

                logger.debug(f"Fetched batch {i//batch_size + 1}: " f"{len(batch_records)} records")

            logger.info(f"Fetched {len(records)} publication details")
            return records

        except Exception as e:
            logger.error(f"PubMed fetch error: {e}")
            raise FetchError(f"Failed to fetch PubMed details: {e}") from e

    def _parse_medline_record(self, record: Dict[str, Any]) -> Publication:
        """
        Parse Medline record to Publication model.

        Args:
            record: Medline record dictionary

        Returns:
            Publication object
        """
        # Extract basic fields
        pmid = record.get("PMID", "")
        title = record.get("TI", "")
        abstract = record.get("AB", "")

        # Authors
        authors = record.get("AU", [])
        if isinstance(authors, str):
            authors = [authors]

        # Journal
        journal = record.get("JT", record.get("TA", ""))

        # Publication date
        pub_date_str = record.get("DP", "")
        pub_date = self._parse_publication_date(pub_date_str)

        # MeSH terms
        mesh_terms = record.get("MH", [])
        if isinstance(mesh_terms, str):
            mesh_terms = [mesh_terms]

        # Keywords
        keywords = record.get("OT", [])
        if isinstance(keywords, str):
            keywords = [keywords]

        # DOI
        doi = None
        aid_list = record.get("AID", [])
        if isinstance(aid_list, str):
            aid_list = [aid_list]
        for aid in aid_list:
            if "[doi]" in aid.lower():
                doi = aid.replace("[doi]", "").strip()
                break

        # PMC ID
        pmc = record.get("PMC", "")

        # Build URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

        # PDF URL (if PMC available)
        pdf_url = None
        if pmc:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/"

        return Publication(
            pmid=pmid,
            pmcid=pmc if pmc else None,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            publication_date=pub_date,
            source=PublicationSource.PUBMED,
            mesh_terms=mesh_terms,
            keywords=keywords,
            url=url,
            pdf_url=pdf_url,
            metadata={
                "medline_record": record,
                "database": self.config.database,
            },
        )

    def _parse_publication_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse publication date from various formats.

        Args:
            date_str: Date string from Medline record

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        # Try common formats
        formats = [
            "%Y %b %d",  # 2023 Jan 15
            "%Y %b",  # 2023 Jan
            "%Y",  # 2023
            "%Y-%m-%d",  # 2023-01-15
            "%Y/%m/%d",  # 2023/01/15
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        # Try extracting just year
        try:
            year = int(date_str.split()[0])
            return datetime(year, 1, 1)
        except (ValueError, IndexError):
            pass

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search PubMed for publications.

        Args:
            query: Search query (supports PubMed query syntax)
            max_results: Maximum number of results
            **kwargs: Additional parameters (retstart for pagination)

        Returns:
            List of Publication objects

        Raises:
            SearchError: If search fails
        """
        retstart = kwargs.get("retstart", 0)

        # Search for PMIDs
        pmids = self._search_pubmed(query, max_results, retstart)

        if not pmids:
            return []

        # Fetch details
        records = self._fetch_details(pmids)

        # Parse to Publication objects
        publications = []
        for record in records:
            try:
                pub = self._parse_medline_record(record)
                publications.append(pub)
            except Exception as e:
                logger.warning(f"Failed to parse record {record.get('PMID', 'unknown')}: {e}")
                continue

        return publications

    def fetch_by_id(self, pmid: str) -> Optional[Publication]:
        """
        Fetch a single publication by PMID.

        Args:
            pmid: PubMed ID

        Returns:
            Publication object or None if not found
        """
        try:
            records = self._fetch_details([pmid])
            if records:
                return self._parse_medline_record(records[0])
            return None
        except Exception as e:
            logger.error(f"Failed to fetch PMID {pmid}: {e}")
            return None

    def search_with_filters(
        self,
        query: str,
        max_results: int = 100,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        article_types: Optional[List[str]] = None,
        **kwargs,
    ) -> List[Publication]:
        """
        Search with additional filters.

        Args:
            query: Base search query
            max_results: Maximum results
            date_from: Start date (YYYY/MM/DD)
            date_to: End date (YYYY/MM/DD)
            article_types: List of article types (e.g., ["Review", "Clinical Trial"])
            **kwargs: Additional parameters

        Returns:
            List of Publication objects
        """
        # Build filtered query
        filtered_query = query

        # Add date range
        if date_from or date_to:
            date_filter = f"({date_from or '1900'}:{date_to or '3000'}[dp])"
            filtered_query = f"{filtered_query} AND {date_filter}"

        # Add article types
        if article_types:
            type_filters = " OR ".join([f"{t}[pt]" for t in article_types])
            filtered_query = f"{filtered_query} AND ({type_filters})"

        logger.info(f"Filtered query: {filtered_query}")

        return self.search(filtered_query, max_results, **kwargs)
