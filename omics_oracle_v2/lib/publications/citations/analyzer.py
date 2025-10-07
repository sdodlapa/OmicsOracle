"""
Citation analyzer - extracts citations and citing papers.

Uses Google Scholar to find papers that cite a given publication.
"""

import logging
from typing import List, Optional

from omics_oracle_v2.lib.publications.citations.models import CitationContext
from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class CitationAnalyzer:
    """
    Analyze citations for a publication.

    Uses Google Scholar to:
    - Find papers that cite a given publication
    - Extract citation contexts
    - Get metadata for citing papers

    Example:
        >>> analyzer = CitationAnalyzer(scholar_client)
        >>> citing_papers = analyzer.get_citing_papers(publication)
        >>> contexts = analyzer.get_citation_contexts(publication, citing_papers[0])
    """

    def __init__(self, scholar_client: GoogleScholarClient):
        """
        Initialize citation analyzer.

        Args:
            scholar_client: Google Scholar client for API access
        """
        self.scholar = scholar_client

    def get_citing_papers(self, publication: Publication, max_results: int = 100) -> List[Publication]:
        """
        Get papers that cite this publication.

        Args:
            publication: Publication to find citations for
            max_results: Maximum citing papers to retrieve

        Returns:
            List of citing publications
        """
        logger.info(f"Finding papers that cite: {publication.title}")

        # Try to get citations using Scholar client
        try:
            citing_papers = self.scholar.get_citations(publication.title, max_results=max_results)

            logger.info(f"Found {len(citing_papers)} citing papers")
            return citing_papers

        except Exception as e:
            logger.error(f"Failed to get citing papers: {e}")
            return []

    def get_citation_contexts(
        self, cited_publication: Publication, citing_publication: Publication
    ) -> List[CitationContext]:
        """
        Extract citation contexts from a citing paper.

        Citation context = text around where the paper is cited.

        Args:
            cited_publication: Paper being cited
            citing_publication: Paper doing the citing

        Returns:
            List of citation contexts
        """
        contexts = []

        # Google Scholar provides snippets in search results
        # These are the citation contexts
        if hasattr(citing_publication, "snippet") and citing_publication.snippet:
            context = CitationContext(
                citing_paper_id=citing_publication.doi or citing_publication.title,
                cited_paper_id=cited_publication.doi or cited_publication.title,
                context_text=citing_publication.snippet,
                sentence=citing_publication.snippet,
            )
            contexts.append(context)

        # If no snippet, use abstract as context
        elif citing_publication.abstract:
            context = CitationContext(
                citing_paper_id=citing_publication.doi or citing_publication.title,
                cited_paper_id=cited_publication.doi or cited_publication.title,
                context_text=citing_publication.abstract,
                paragraph=citing_publication.abstract,
                section="abstract",
            )
            contexts.append(context)

        return contexts

    def analyze_citation_network(self, publication: Publication, depth: int = 1) -> dict:
        """
        Analyze citation network (who cites this, who do they cite, etc.).

        Args:
            publication: Starting publication
            depth: How many citation levels to explore

        Returns:
            Citation network data
        """
        network = {"root": publication, "citing_papers": [], "depth": depth}

        # Get first-level citations
        level1_citing = self.get_citing_papers(publication, max_results=50)
        network["citing_papers"] = level1_citing

        # If depth > 1, get second-level citations
        if depth > 1:
            network["second_level"] = []
            for paper in level1_citing[:10]:  # Limit for performance
                second_level = self.get_citing_papers(paper, max_results=20)
                network["second_level"].extend(second_level)

        return network

    def get_citation_statistics(self, publication: Publication) -> dict:
        """
        Get citation statistics.

        Args:
            publication: Publication to analyze

        Returns:
            Citation stats (total, by year, etc.)
        """
        stats = {
            "total_citations": 0,
            "citations_by_year": {},
            "highly_cited_papers": [],  # Papers citing this with high citation counts
        }

        # Get citing papers
        citing_papers = self.get_citing_papers(publication, max_results=200)
        stats["total_citations"] = len(citing_papers)

        # Group by year
        for paper in citing_papers:
            if paper.publication_date:
                year = paper.publication_date.year
                stats["citations_by_year"][year] = stats["citations_by_year"].get(year, 0) + 1

        # Find highly cited papers
        highly_cited = [p for p in citing_papers if p.citations and p.citations > 50]
        highly_cited.sort(key=lambda p: p.citations or 0, reverse=True)
        stats["highly_cited_papers"] = highly_cited[:10]

        return stats
