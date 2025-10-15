"""
GEO Citation Discovery

Finds papers that cite GEO datasets using two strategies:
1. Papers citing the original publication (via PMID)
2. Papers mentioning the GEO ID in their text

No LLM analysis - pure citation discovery.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Set

from omics_oracle_v2.lib.search_engines.citations.config import PubMedConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.citations.openalex import (
    OpenAlexClient, OpenAlexConfig)
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


@dataclass
class CitationDiscoveryResult:
    """Results from citation discovery"""

    geo_id: str
    original_pmid: Optional[str]
    citing_papers: List[Publication]
    strategy_breakdown: dict  # Which papers came from which strategy


class GEOCitationDiscovery:
    """
    Discover papers citing GEO datasets.

    Strategies:
    1. OpenAlex: Papers citing original publication
    2. PubMed: Papers mentioning GEO ID
    """

    def __init__(
        self,
        openalex_client: Optional[OpenAlexClient] = None,
        pubmed_client: Optional[PubMedClient] = None,
        use_strategy_a: bool = True,  # Citation-based
        use_strategy_b: bool = True,  # Mention-based
    ):
        # Initialize OpenAlex client if not provided
        if openalex_client is None:
            openalex_config = OpenAlexConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"), enable=True
            )
            self.openalex = OpenAlexClient(config=openalex_config)
            logger.info("Initialized OpenAlex client for citation discovery")
        else:
            self.openalex = openalex_client

        # Initialize PubMed client if not provided
        if pubmed_client is None:
            pubmed_config = PubMedConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
                api_key=os.getenv("NCBI_API_KEY"),
                max_results=100,
            )
            self.pubmed_client = PubMedClient(pubmed_config)
        else:
            self.pubmed_client = pubmed_client

        self.use_strategy_a = use_strategy_a
        self.use_strategy_b = use_strategy_b

    async def find_citing_papers(
        self, geo_metadata: GEOSeriesMetadata, max_results: int = 100
    ) -> CitationDiscoveryResult:
        """
        Find all papers citing this GEO dataset.

        Args:
            geo_metadata: GEO dataset metadata
            max_results: Maximum papers to return

        Returns:
            CitationDiscoveryResult with citing papers
        """
        logger.info(f"Finding papers citing {geo_metadata.geo_id}")

        all_papers: Set[Publication] = set()
        strategy_breakdown = {"strategy_a": [], "strategy_b": []}

        # Strategy A: Papers citing original publication
        # Get first PMID if available
        original_pmid = geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else None

        if self.use_strategy_a and original_pmid:
            logger.info(f"Strategy A: Finding papers citing PMID {original_pmid}")
            citing_via_pmid = self._find_via_citation(
                pmid=original_pmid, max_results=max_results
            )
            for paper in citing_via_pmid:
                all_papers.add(paper)
                strategy_breakdown["strategy_a"].append(paper.pmid or paper.doi)
            logger.info(f"  Found {len(citing_via_pmid)} papers via citation")

        # Strategy B: Papers mentioning GEO ID
        if self.use_strategy_b:
            logger.info(f"Strategy B: Finding papers mentioning {geo_metadata.geo_id}")
            mentioning_geo = self._find_via_geo_mention(
                geo_id=geo_metadata.geo_id, max_results=max_results
            )
            for paper in mentioning_geo:
                if paper not in all_papers:
                    all_papers.add(paper)
                    strategy_breakdown["strategy_b"].append(paper.pmid or paper.doi)
            logger.info(f"  Found {len(mentioning_geo)} papers mentioning GEO ID")

        # Deduplicate and sort
        unique_papers = list(all_papers)
        logger.info(f"Total unique citing papers: {len(unique_papers)}")

        return CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            original_pmid=original_pmid,
            citing_papers=unique_papers[:max_results],
            strategy_breakdown=strategy_breakdown,
        )

    def _find_via_citation(self, pmid: str, max_results: int) -> List[Publication]:
        """Strategy A: Find papers citing the original publication"""
        if not self.openalex or not self.openalex.config.enable:
            logger.warning("OpenAlex not configured - cannot find citations")
            return []

        try:
            # First, fetch the full publication details from PubMed to get DOI
            logger.info(f"Fetching full publication details for PMID {pmid}")
            original_pub = self.pubmed_client.fetch_by_id(pmid)

            if not original_pub:
                logger.warning(f"Could not fetch details for PMID {pmid}")
                return []

            if not original_pub.doi:
                logger.warning(f"No DOI found for PMID {pmid} - cannot find citations")
                return []

            logger.info(
                f"Found original paper: {original_pub.title[:50]}... DOI: {original_pub.doi}"
            )

            # Find citing papers using OpenAlex directly
            citing_papers = self.openalex.get_citing_papers(
                doi=original_pub.doi, max_results=max_results
            )

            if citing_papers:
                logger.info(f"✓ Found {len(citing_papers)} citing papers from OpenAlex")
            else:
                logger.debug("No citing papers found in OpenAlex")

            return citing_papers

        except Exception as e:
            logger.error(f"OpenAlex citation search failed for PMID {pmid}: {e}")
            return []

    def _find_via_geo_mention(self, geo_id: str, max_results: int) -> List[Publication]:
        """Strategy B: Find papers mentioning GEO ID"""
        papers = []

        # Search PubMed for GEO ID mentions
        try:
            query = f"{geo_id}[All Fields]"
            # PubMed client search is synchronous
            pubmed_results = self.pubmed_client.search(
                query=query, max_results=max_results
            )
            papers.extend(pubmed_results)
            logger.info(f"  PubMed: {len(pubmed_results)} papers mentioning {geo_id}")
        except Exception as e:
            logger.warning(f"PubMed search failed for {geo_id}: {e}")

        return papers
