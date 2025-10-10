"""
Citation Finder - discovers papers that cite a given publication.

Uses multiple sources to find papers that cite a given publication:
1. OpenAlex (primary) - Free, official API, sustainable
2. Google Scholar (fallback) - More comprehensive but may be blocked
3. Semantic Scholar (enrichment) - Citation counts and metrics

Multi-source approach ensures robustness and maximum coverage.

NOTE: This class performs pure data retrieval via APIs - NO LLM analysis.
For LLM-based citation content analysis, see CitationContentAnalyzer (Phase 7).
"""

import logging
from typing import List, Optional

from omics_oracle_v2.lib.publications.citations.models import CitationContext
from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient
from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.clients.semantic_scholar import SemanticScholarClient
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class CitationFinder:
    """
    Find papers that cite a given publication using multiple API sources.

    This class performs PURE DATA RETRIEVAL - no LLM analysis.
    It discovers citing papers via APIs and web scraping only.

    Source Priority:
    1. OpenAlex - Primary source (free, reliable, no scraping)
    2. Google Scholar - Fallback (comprehensive but may be blocked)
    3. Semantic Scholar - Enrichment only (citation counts, metrics)

    Features:
    - Find papers that cite a given publication
    - Extract citation contexts from abstracts/full-text
    - Get metadata for citing papers
    - Citation network discovery
    - Citation statistics

    Example:
        >>> finder = CitationFinder(
        ...     openalex_client=openalex,
        ...     scholar_client=scholar,  # Optional
        ...     semantic_scholar_client=ss  # Optional
        ... )
        >>> citing_papers = finder.find_citing_papers(publication)
        >>> contexts = finder.get_citation_contexts(publication, citing_papers[0])
    """

    def __init__(
        self,
        openalex_client: Optional[OpenAlexClient] = None,
        scholar_client: Optional[GoogleScholarClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
    ):
        """
        Initialize citation finder with multiple sources.

        Args:
            openalex_client: OpenAlex client (primary source)
            scholar_client: Google Scholar client (fallback)
            semantic_scholar_client: Semantic Scholar client (enrichment)
        """
        self.openalex = openalex_client
        self.scholar = scholar_client
        self.semantic_scholar = semantic_scholar_client

        # Log available sources
        sources = []
        if self.openalex:
            sources.append("OpenAlex (primary)")
        if self.scholar:
            sources.append("Google Scholar (fallback)")
        if self.semantic_scholar:
            sources.append("Semantic Scholar (enrichment)")

        logger.info(f"CitationFinder initialized with sources: {', '.join(sources)}")

        if not any([self.openalex, self.scholar]):
            logger.warning("No citation sources configured - citation discovery will be limited")

    def find_citing_papers(self, publication: Publication, max_results: int = 100) -> List[Publication]:
        """
        Initialize citation analyzer with multiple sources.

        Args:
            openalex_client: OpenAlex client (primary source)
            scholar_client: Google Scholar client (fallback)
            semantic_scholar_client: Semantic Scholar client (enrichment)
        """
        self.openalex = openalex_client
        self.scholar = scholar_client
        self.semantic_scholar = semantic_scholar_client

        # Log available sources
        sources = []
        if self.openalex:
            sources.append("OpenAlex (primary)")
        if self.scholar:
            sources.append("Google Scholar (fallback)")
        if self.semantic_scholar:
            sources.append("Semantic Scholar (enrichment)")

        logger.info(f"CitationFinder initialized with sources: {', '.join(sources)}")

        if not any([self.openalex, self.scholar]):
            logger.warning("No citation sources configured - citation analysis will be limited")

    def find_citing_papers(self, publication: Publication, max_results: int = 100) -> List[Publication]:
        """
        Find papers that cite this publication.

        Multi-source approach with fallback:
        1. Try OpenAlex (primary - free, reliable)
        2. Fall back to Google Scholar if OpenAlex fails
        3. Enrich results with Semantic Scholar metrics

        Args:
            publication: Publication to find citations for
            max_results: Maximum citing papers to retrieve

        Returns:
            List of citing publications
        """
        logger.info(f"Finding papers that cite: {publication.title}")
        citing_papers = []
        source_used = None

        # Try OpenAlex first (primary source)
        if self.openalex and self.openalex.config.enable:
            try:
                logger.debug("Attempting OpenAlex citation search...")
                citing_papers = self.openalex.get_citing_papers(doi=publication.doi, max_results=max_results)

                if citing_papers:
                    source_used = "OpenAlex"
                    logger.info(f"✓ Found {len(citing_papers)} citing papers from OpenAlex")
                else:
                    logger.debug("No citing papers found in OpenAlex")

            except Exception as e:
                logger.warning(f"OpenAlex citation search failed: {e}")

        # Fall back to Google Scholar if OpenAlex didn't work
        if not citing_papers and self.scholar:
            try:
                logger.debug("Falling back to Google Scholar citation search...")
                citing_papers = self.scholar.get_citations(publication.title, max_results=max_results)

                if citing_papers:
                    source_used = "Google Scholar"
                    logger.info(f"✓ Found {len(citing_papers)} citing papers from Google Scholar")
                else:
                    logger.debug("No citing papers found in Google Scholar")

            except Exception as e:
                logger.warning(f"Google Scholar citation search failed: {e}")

        # Enrich with Semantic Scholar metrics if available
        if citing_papers and self.semantic_scholar:
            try:
                logger.debug("Enriching citing papers with Semantic Scholar metrics...")
                citing_papers = self.semantic_scholar.enrich_publications(citing_papers)
            except Exception as e:
                logger.debug(f"Semantic Scholar enrichment failed: {e}")

        # Log results
        if citing_papers:
            logger.info(f"✓ Citation search complete: {len(citing_papers)} papers found via {source_used}")
        else:
            logger.warning("No citing papers found from any source")

        return citing_papers

    def get_citation_contexts(
        self, cited_publication: Publication, citing_publication: Publication
    ) -> List[CitationContext]:
        """
        Extract citation contexts from a citing paper.

        Citation context = text around where the paper is cited.

        Multi-source context extraction:
        1. Google Scholar snippets (if available)
        2. OpenAlex abstract (fallback)
        3. Citing paper abstract (final fallback)
        4. Full-text PDF extraction (future enhancement)

        Args:
            cited_publication: Paper being cited
            citing_publication: Paper doing the citing

        Returns:
            List of citation contexts
        """
        contexts = []

        # Try Google Scholar snippets first (most precise)
        snippet = citing_publication.metadata.get("snippet") if citing_publication.metadata else None
        if snippet:
            context = CitationContext(
                citing_paper_id=citing_publication.doi or citing_publication.title,
                cited_paper_id=cited_publication.doi or cited_publication.title,
                context_text=snippet,
                sentence=snippet,
                source="scholar_snippet",
            )
            contexts.append(context)
            logger.debug("Using Google Scholar snippet as citation context")

        # Try OpenAlex citation contexts
        elif self.openalex and cited_publication.doi and citing_publication.doi:
            try:
                openalex_contexts = self.openalex.get_citation_contexts(
                    cited_doi=cited_publication.doi, citing_doi=citing_publication.doi
                )
                for ctx in openalex_contexts:
                    context = CitationContext(
                        citing_paper_id=citing_publication.doi,
                        cited_paper_id=cited_publication.doi,
                        context_text=ctx,
                        paragraph=ctx,
                        section="abstract",
                        source="openalex",
                    )
                    contexts.append(context)
                if openalex_contexts:
                    logger.debug("Using OpenAlex contexts")
            except Exception as e:
                logger.debug(f"Could not get OpenAlex contexts: {e}")

        # Fall back to citing paper abstract
        if not contexts and citing_publication.abstract:
            context = CitationContext(
                citing_paper_id=citing_publication.doi or citing_publication.title,
                cited_paper_id=cited_publication.doi or cited_publication.title,
                context_text=citing_publication.abstract,
                paragraph=citing_publication.abstract,
                section="abstract",
                source="abstract",
            )
            contexts.append(context)
            logger.debug("Using citing paper abstract as context")

        return contexts

    def find_citation_network(self, publication: Publication, depth: int = 1) -> dict:
        """
        Discover citation network (who cites this, who do they cite, etc.).

        Args:
            publication: Starting publication
            depth: How many citation levels to explore

        Returns:
            Citation network data
        """
        network = {"root": publication, "citing_papers": [], "depth": depth}

        # Get first-level citations
        level1_citing = self.find_citing_papers(publication, max_results=50)
        network["citing_papers"] = level1_citing

        # If depth > 1, get second-level citations
        if depth > 1:
            network["second_level"] = []
            for paper in level1_citing[:10]:  # Limit for performance
                second_level = self.find_citing_papers(paper, max_results=20)
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
        citing_papers = self.find_citing_papers(publication, max_results=200)
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
