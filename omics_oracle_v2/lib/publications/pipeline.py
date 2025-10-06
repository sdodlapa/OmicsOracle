"""
Publication Search Pipeline - Main orchestration following golden pattern.

This pipeline follows the AdvancedSearchPipeline pattern with:
- Feature toggles for incremental adoption
- Conditional initialization
- Configuration-driven design
"""

import logging
import time
from typing import List, Optional

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import (
    Publication,
    PublicationResult,
    PublicationSearchResult,
)
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType,
)
from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker


logger = logging.getLogger(__name__)


class PublicationSearchPipeline:
    """
    Main pipeline for publication search and analysis.
    
    This pipeline follows the golden pattern from AdvancedSearchPipeline:
    - Feature toggles in configuration
    - Conditional initialization based on enabled features
    - Conditional execution in search flow
    
    Week 1-2 Features:
    - PubMed search (enable_pubmed)
    - Basic ranking
    
    Week 3 Features (TODO):
    - Google Scholar (enable_scholar)
    - Citation analysis (enable_citations)
    
    Week 4 Features (TODO):
    - PDF download (enable_pdf_download)
    - Full-text extraction (enable_fulltext)
    
    Example:
        >>> config = PublicationSearchConfig(
        ...     enable_pubmed=True,
        ...     pubmed_config=PubMedConfig(email="user@example.com")
        ... )
        >>> pipeline = PublicationSearchPipeline(config)
        >>> results = pipeline.search("cancer genomics", max_results=50)
    """
    
    def __init__(self, config: PublicationSearchConfig):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Publication search configuration
        """
        self.config = config
        self._initialized = False
        
        # Conditional initialization based on feature toggles
        # Week 1-2: Only PubMed
        if config.enable_pubmed:
            logger.info("Initializing PubMed client")
            self.pubmed_client = PubMedClient(config.pubmed_config)
        else:
            self.pubmed_client = None
        
        # Week 3: Google Scholar (disabled for now)
        if config.enable_scholar:
            logger.info("Google Scholar client not yet implemented (Week 3)")
            self.scholar_client = None  # TODO: Week 3
        else:
            self.scholar_client = None
        
        # Week 3: Citation analysis (disabled for now)
        if config.enable_citations:
            logger.info("Citation analyzer not yet implemented (Week 3)")
            self.citation_analyzer = None  # TODO: Week 3
        else:
            self.citation_analyzer = None
        
        # Week 4: PDF processing (disabled for now)
        if config.enable_pdf_download:
            logger.info("PDF downloader not yet implemented (Week 4)")
            self.pdf_downloader = None  # TODO: Week 4
        else:
            self.pdf_downloader = None
        
        # Week 4: Full-text extraction (disabled for now)
        if config.enable_fulltext:
            logger.info("Full-text extractor not yet implemented (Week 4)")
            self.fulltext_extractor = None  # TODO: Week 4
        else:
            self.fulltext_extractor = None
        
        # Week 4: Institutional access (NEW)
        if config.enable_institutional_access:
            logger.info(f"Initializing institutional access: {config.primary_institution}")
            # Primary institution
            primary_inst = (
                InstitutionType.GEORGIA_TECH 
                if config.primary_institution.lower() == "gatech" 
                else InstitutionType.OLD_DOMINION
            )
            self.institutional_manager = InstitutionalAccessManager(primary_inst)
            
            # Secondary/fallback institution
            if config.secondary_institution:
                secondary_inst = (
                    InstitutionType.GEORGIA_TECH 
                    if config.secondary_institution.lower() == "gatech" 
                    else InstitutionType.OLD_DOMINION
                )
                self.institutional_manager_fallback = InstitutionalAccessManager(secondary_inst)
            else:
                self.institutional_manager_fallback = None
        else:
            self.institutional_manager = None
            self.institutional_manager_fallback = None
        
        # Core components (always initialized)
        self.ranker = PublicationRanker(config)
        
        logger.info(
            f"PublicationSearchPipeline initialized with features: "
            f"pubmed={config.enable_pubmed}, "
            f"scholar={config.enable_scholar}, "
            f"citations={config.enable_citations}, "
            f"pdf={config.enable_pdf_download}, "
            f"fulltext={config.enable_fulltext}"
        )
    
    def initialize(self) -> None:
        """Initialize pipeline resources."""
        if self._initialized:
            return
        
        # Initialize clients that support it
        if self.pubmed_client:
            self.pubmed_client.initialize()
        
        self._initialized = True
        logger.info("PublicationSearchPipeline initialized")
    
    def cleanup(self) -> None:
        """Clean up pipeline resources."""
        if not self._initialized:
            return
        
        # Cleanup clients
        if self.pubmed_client:
            self.pubmed_client.cleanup()
        
        self._initialized = False
        logger.info("PublicationSearchPipeline cleaned up")
    
    def search(
        self, 
        query: str, 
        max_results: int = 50,
        min_relevance_score: float = None,
        **kwargs
    ) -> PublicationResult:
        """
        Search for publications across enabled sources.
        
        This follows the conditional execution pattern:
        - Check each feature toggle
        - Execute component if enabled
        - Aggregate results
        - Rank and return
        
        Args:
            query: Search query
            max_results: Maximum total results to return
            min_relevance_score: Minimum relevance score filter
            **kwargs: Additional search parameters
            
        Returns:
            PublicationResult with ranked publications
        """
        start_time = time.time()
        
        # Ensure initialized
        if not self._initialized:
            self.initialize()
        
        logger.info(f"Searching publications for: '{query}'")
        
        # Step 1: Search enabled sources
        all_publications = []
        sources_used = []
        
        # 1a. PubMed search (conditional execution)
        if self.pubmed_client:
            try:
                logger.info("Searching PubMed...")
                pubmed_results = self.pubmed_client.search(
                    query, 
                    max_results=max_results,
                    **kwargs
                )
                all_publications.extend(pubmed_results)
                sources_used.append("pubmed")
                logger.info(f"PubMed returned {len(pubmed_results)} results")
            except Exception as e:
                logger.error(f"PubMed search failed: {e}")
        
        # 1b. Google Scholar search (Week 3 - conditional execution)
        if self.scholar_client:
            try:
                logger.info("Searching Google Scholar...")
                scholar_results = self.scholar_client.search(query, max_results)
                all_publications.extend(scholar_results)
                sources_used.append("google_scholar")
                logger.info(f"Scholar returned {len(scholar_results)} results")
            except Exception as e:
                logger.error(f"Google Scholar search failed: {e}")
        
        # Step 2: Deduplicate (if enabled)
        if self.config.deduplication and len(all_publications) > 0:
            all_publications = self._deduplicate_publications(all_publications)
            logger.info(f"After deduplication: {len(all_publications)} publications")
        
        # Step 3: Enrich with institutional access info (Week 4 - NEW)
        if self.institutional_manager and len(all_publications) > 0:
            try:
                logger.info("Enriching with institutional access information...")
                for pub in all_publications:
                    # Check access status
                    access_status = self.institutional_manager.check_access_status(pub)
                    
                    # Try fallback institution if primary doesn't have access
                    if not any(access_status.values()) and self.institutional_manager_fallback:
                        access_status = self.institutional_manager_fallback.check_access_status(pub)
                    
                    # Add to metadata
                    pub.metadata['access_status'] = access_status
                    pub.metadata['has_access'] = any(access_status.values())
                    
                    # Get access URL if available
                    access_url = self.institutional_manager.get_access_url(pub)
                    if not access_url and self.institutional_manager_fallback:
                        access_url = self.institutional_manager_fallback.get_access_url(pub)
                    
                    if access_url:
                        pub.metadata['access_url'] = access_url
                        
            except Exception as e:
                logger.error(f"Institutional access enrichment failed: {e}")
        
        # Step 4: Rank publications
        ranked_results = self.ranker.rank(
            all_publications, 
            query,
            top_k=max_results
        )
        
        # Step 5: Citation analysis (Week 3 - conditional execution)
        if self.citation_analyzer and ranked_results:
            try:
                logger.info("Enriching with citation data...")
                ranked_results = self._enrich_citations(ranked_results)
            except Exception as e:
                logger.error(f"Citation enrichment failed: {e}")
        
        # Step 6: PDF download (Week 4 - conditional execution)
        if self.pdf_downloader and ranked_results:
            try:
                logger.info("Downloading PDFs...")
                self._download_pdfs(ranked_results)
            except Exception as e:
                logger.error(f"PDF download failed: {e}")
        
        # Step 7: Full-text extraction (Week 4 - conditional execution)
        if self.fulltext_extractor and ranked_results:
            try:
                logger.info("Extracting full text...")
                ranked_results = self._extract_fulltext(ranked_results)
            except Exception as e:
                logger.error(f"Full-text extraction failed: {e}")
        
        # Step 8: Filter by minimum score (if specified)
        if min_relevance_score is not None:
            ranked_results = self.ranker.filter_by_score(
                ranked_results, 
                min_relevance_score
            )
        elif self.config.min_relevance_score > 0:
            ranked_results = self.ranker.filter_by_score(
                ranked_results,
                self.config.min_relevance_score
            )
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        # Build result
        result = PublicationResult(
            query=query,
            publications=ranked_results,
            total_found=len(all_publications),
            sources_used=sources_used,
            search_time_ms=search_time_ms,
            metadata={
                "config": {
                    "pubmed_enabled": self.config.enable_pubmed,
                    "scholar_enabled": self.config.enable_scholar,
                    "citations_enabled": self.config.enable_citations,
                    "pdf_enabled": self.config.enable_pdf_download,
                    "fulltext_enabled": self.config.enable_fulltext,
                    "institutional_access_enabled": self.config.enable_institutional_access,
                    "primary_institution": self.config.primary_institution if self.config.enable_institutional_access else None,
                },
                "ranking_weights": self.config.ranking_weights,
            }
        )
        
        logger.info(
            f"Search complete: {len(ranked_results)} ranked results "
            f"from {len(all_publications)} total in {search_time_ms:.2f}ms"
        )
        
        return result
    
    def _deduplicate_publications(
        self, 
        publications: List[Publication]
    ) -> List[Publication]:
        """
        Remove duplicate publications based on primary identifiers.
        
        Args:
            publications: List of publications
            
        Returns:
            Deduplicated list
        """
        seen_ids = set()
        unique_pubs = []
        
        for pub in publications:
            pub_id = pub.primary_id
            if pub_id not in seen_ids:
                seen_ids.add(pub_id)
                unique_pubs.append(pub)
        
        duplicates_removed = len(publications) - len(unique_pubs)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate publications")
        
        return unique_pubs
    
    def _enrich_citations(
        self,
        results: List[PublicationSearchResult]
    ) -> List[PublicationSearchResult]:
        """
        Enrich results with citation data (Week 3).
        
        Args:
            results: Publication results
            
        Returns:
            Enriched results
        """
        # TODO: Week 3 implementation
        logger.warning("Citation enrichment not yet implemented (Week 3)")
        return results
    
    def _download_pdfs(
        self,
        results: List[PublicationSearchResult]
    ) -> None:
        """
        Download PDFs for publications (Week 4).
        
        Uses institutional access to get PDFs from paywalled sources.
        
        Args:
            results: Publication results
        """
        for result in results:
            pub = result.publication
            
            try:
                # Try to get PDF URL via institutional access
                pdf_url = None
                
                # Try primary institution
                if self.institutional_manager:
                    pdf_url = self.institutional_manager.get_pdf_url(pub)
                    if pdf_url:
                        logger.info(f"PDF found via {self.config.primary_institution}: {pdf_url[:80]}...")
                
                # Try fallback institution
                if not pdf_url and self.institutional_manager_fallback:
                    pdf_url = self.institutional_manager_fallback.get_pdf_url(pub)
                    if pdf_url:
                        logger.info(f"PDF found via {self.config.secondary_institution}: {pdf_url[:80]}...")
                
                # Store PDF URL in metadata
                if pdf_url:
                    pub.metadata['institutional_pdf_url'] = pdf_url
                    # TODO: Actual download logic when PDFDownloader is implemented
                    logger.info(f"PDF URL ready for download: {pub.title[:50]}...")
                else:
                    logger.debug(f"No PDF access for: {pub.title[:50]}...")
                    
            except Exception as e:
                logger.warning(f"Failed to get PDF for {pub.title[:50]}...: {e}")
    
    def _extract_fulltext(
        self,
        results: List[PublicationSearchResult]
    ) -> List[PublicationSearchResult]:
        """
        Extract full text from PDFs (Week 4).
        
        Args:
            results: Publication results
            
        Returns:
            Results with full text
        """
        # TODO: Week 4 implementation
        logger.warning("Full-text extraction not yet implemented (Week 4)")
        return results
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
    
    @property
    def is_initialized(self) -> bool:
        """Check if pipeline is initialized."""
        return self._initialized
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled features.
        
        Returns:
            List of feature names
        """
        features = []
        if self.config.enable_pubmed:
            features.append("pubmed")
        if self.config.enable_scholar:
            features.append("google_scholar")
        if self.config.enable_citations:
            features.append("citations")
        if self.config.enable_pdf_download:
            features.append("pdf_download")
        if self.config.enable_fulltext:
            features.append("fulltext_extraction")
        if self.config.enable_institutional_access:
            features.append(f"institutional_access_{self.config.primary_institution}")
        return features
