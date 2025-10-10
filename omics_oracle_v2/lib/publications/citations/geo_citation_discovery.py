"""
GEO Citation Discovery

Finds papers that cite GEO datasets using two strategies:
1. Papers citing the original publication (via PMID)
2. Papers mentioning the GEO ID in their text

No LLM analysis - pure citation discovery.
"""

import logging
import os
from typing import List, Set, Optional
from dataclasses import dataclass

from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
from omics_oracle_v2.lib.publications.citations.citation_finder import CitationFinder
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.publications.config import PubMedConfig

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
    1. OpenAlex/Semantic Scholar: Papers citing original publication
    2. PubMed/Google Scholar: Papers mentioning GEO ID
    """
    
    def __init__(
        self,
        citation_finder: Optional[CitationFinder] = None,
        pubmed_client: Optional[PubMedClient] = None,
        use_strategy_a: bool = True,  # Citation-based
        use_strategy_b: bool = True,  # Mention-based
    ):
        self.citation_finder = citation_finder or CitationFinder()
        
        # Create PubMedClient with config from environment if not provided
        if pubmed_client is None:
            pubmed_config = PubMedConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
                api_key=os.getenv("NCBI_API_KEY"),
                max_results=100
            )
            self.pubmed_client = PubMedClient(pubmed_config)
        else:
            self.pubmed_client = pubmed_client
            
        self.use_strategy_a = use_strategy_a
        self.use_strategy_b = use_strategy_b
    
    async def find_citing_papers(
        self,
        geo_metadata: GEOSeriesMetadata,
        max_results: int = 100
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
            citing_via_pmid = await self._find_via_citation(
                pmid=original_pmid,
                max_results=max_results
            )
            for paper in citing_via_pmid:
                all_papers.add(paper)
                strategy_breakdown["strategy_a"].append(paper.pmid or paper.doi)
            logger.info(f"  Found {len(citing_via_pmid)} papers via citation")
        
        # Strategy B: Papers mentioning GEO ID
        if self.use_strategy_b:
            logger.info(f"Strategy B: Finding papers mentioning {geo_metadata.geo_id}")
            mentioning_geo = await self._find_via_geo_mention(
                geo_id=geo_metadata.geo_id,
                max_results=max_results
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
            strategy_breakdown=strategy_breakdown
        )
    
    async def _find_via_citation(
        self,
        pmid: str,
        max_results: int
    ) -> List[Publication]:
        """Strategy A: Find papers citing the original publication"""
        try:
            # Use existing citation finder (OpenAlex, Semantic Scholar)
            # Note: find_citing_papers needs a Publication object
            # For now, create minimal Publication with PMID
            from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
            temp_pub = Publication(
                pmid=pmid,
                title="",  # Will be enriched by citation finder
                doi=None,
                source=PublicationSource.PUBMED  # Required field
            )
            citing_papers = self.citation_finder.find_citing_papers(
                publication=temp_pub,
                max_results=max_results
            )
            return citing_papers
        except Exception as e:
            logger.warning(f"Citation strategy failed for PMID {pmid}: {e}")
            return []
    
    async def _find_via_geo_mention(
        self,
        geo_id: str,
        max_results: int
    ) -> List[Publication]:
        """Strategy B: Find papers mentioning GEO ID"""
        papers = []
        
        # Search PubMed for GEO ID mentions
        try:
            query = f"{geo_id}[All Fields]"
            # PubMed client search is synchronous, not async
            pubmed_results = self.pubmed_client.search(
                query=query,
                max_results=max_results
            )
            papers.extend(pubmed_results)
            logger.info(f"  PubMed: {len(pubmed_results)} papers mentioning {geo_id}")
        except Exception as e:
            logger.warning(f"PubMed search failed for {geo_id}: {e}")
        
        return papers
