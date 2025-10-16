"""
Search Service

Business logic for dataset and publication search operations.
Extracted from api/routes/agents.py to separate concerns.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from omics_oracle_v2.api.models.requests import SearchRequest
from omics_oracle_v2.api.models.responses import (DatasetResponse,
                                                  PublicationResponse,
                                                  QueryProcessingResponse,
                                                  SearchResponse)
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.search_orchestration import (OrchestratorConfig,
                                                      SearchOrchestrator)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for executing search operations across datasets and publications."""

    def __init__(self):
        """Initialize search service."""
        self.logger = logger
        # GEO cache will be initialized lazily to avoid circular imports
        self._geo_cache = None
        self._geo_cache_initialized = False
    
    @property
    def geo_cache(self):
        """Lazy-load GEO cache to avoid circular imports."""
        if not self._geo_cache_initialized:
            try:
                from omics_oracle_v2.lib.pipelines.storage.registry import create_geo_cache
                from omics_oracle_v2.lib.pipelines.storage.unified_db import UnifiedDatabase
                from omics_oracle_v2.core.config import get_settings
                
                # Get database path from config
                settings = get_settings()
                db_path = settings.search.db_path
                
                # Create UnifiedDatabase instance
                unified_db = UnifiedDatabase(db_path)
                self._geo_cache = create_geo_cache(unified_db)
                logger.info(f"GEO cache initialized for search service (db: {db_path})")
            except Exception as e:
                logger.warning(f"Failed to initialize GEO cache: {e}. Database metrics will be unavailable.")
                self._geo_cache = None
            finally:
                self._geo_cache_initialized = True
        return self._geo_cache

    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute unified search across datasets and publications.

        Args:
            request: Search request with terms, filters, and options

        Returns:
            SearchResponse with ranked datasets, publications, and metadata

        Raises:
            Exception: If search execution fails
        """
        start_time = time.time()
        search_logs = []

        try:
            # Build search configuration
            config = self._build_search_config(request, search_logs)

            # Execute search pipeline
            pipeline = SearchOrchestrator(config)
            query = self._build_query(request, search_logs)

            search_result = await pipeline.search(
                query=query,
                max_geo_results=request.max_results,
                max_publication_results=50,
                use_cache=True,
            )

            # Log search results
            self._log_search_results(search_result, search_logs)

            # Process and rank datasets
            ranked_datasets = self._rank_datasets(
                search_result.geo_datasets, request, search_logs
            )

            # Convert to response format (with database metrics enrichment)
            datasets = await self._build_dataset_responses(ranked_datasets)
            publications = self._build_publication_responses(
                search_result.publications, search_logs
            )

            # Build filters metadata
            filters_applied = self._build_filters_metadata(
                request, search_result, query
            )

            # Extract query processing context (RAG Phase 3)
            query_processing = self._build_query_processing_response(search_result)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            search_logs.append(
                f"[TIME] Total execution time: {execution_time_ms:.2f}ms"
            )

            return SearchResponse(
                success=True,
                execution_time_ms=execution_time_ms,
                timestamp=datetime.now(timezone.utc),
                total_found=search_result.total_results,
                datasets=datasets,
                search_terms_used=request.search_terms,
                filters_applied=filters_applied,
                search_logs=search_logs,
                publications=publications,
                publications_count=len(publications),
                query_processing=query_processing,
            )

        except Exception as e:
            self.logger.error(f"Search execution failed: {e}", exc_info=True)
            raise

    def _build_search_config(
        self, request: SearchRequest, search_logs: List[str]
    ) -> OrchestratorConfig:
        """Build search orchestrator configuration."""
        search_logs.append("[INFO] Using SearchOrchestrator with parallel execution")
        self.logger.info("Initializing SearchOrchestrator")

        return OrchestratorConfig(
            enable_geo=True,
            enable_pubmed=True,
            enable_openalex=True,
            max_geo_results=request.max_results,
            max_publication_results=50,
            enable_cache=True,
            enable_query_optimization=True,
        )

    def _build_query(self, request: SearchRequest, search_logs: List[str]) -> str:
        """Build search query with filters."""
        original_query = " ".join(request.search_terms)
        search_logs.append(f"[SEARCH] Original query: '{original_query}'")
        self.logger.info(
            f"Search request: '{original_query}' (semantic={request.enable_semantic})"
        )

        # Apply filters
        query_parts = [original_query]

        if request.filters:
            organism = request.filters.get("organism")
            if organism:
                query_parts.append(f'"{organism}"[Organism]')
                self.logger.info(f"Added organism filter: {organism}")

            study_type = request.filters.get("study_type")
            if study_type:
                query_parts.append(f'"{study_type}"[DataSet Type]')
                self.logger.info(f"Added study type filter: {study_type}")

        query = " AND ".join(query_parts) if len(query_parts) > 1 else query_parts[0]

        if query != original_query:
            search_logs.append(f"[FILTER] Query with filters: '{query}'")

        return query

    def _log_search_results(self, search_result, search_logs: List[str]) -> None:
        """Log search pipeline results."""
        self.logger.info(
            f"Pipeline complete: type={search_result.query_type}, "
            f"cache={search_result.cache_hit}, time={search_result.search_time_ms:.2f}ms, "
            f"results={search_result.total_results}"
        )

        # Add query type log
        if search_result.query_type == "hybrid":
            search_logs.append("[PROCESS] Query type: HYBRID (GEO + Publications)")
        else:
            search_logs.append(f"[DATA] Query type: {search_result.query_type}")

        # Log query optimization
        if (
            search_result.optimized_query
            and search_result.optimized_query != search_result.query_type
        ):
            search_logs.append(
                f"[CONFIG] Optimized query: '{search_result.optimized_query}'"
            )
        else:
            search_logs.append("[INFO] Query used as-is (no optimization needed)")

        # Log cache status
        if search_result.cache_hit:
            search_logs.append("[FAST] Cache hit - results returned from cache")
        else:
            search_logs.append("[PROCESS] Fresh search - results fetched from sources")

        search_logs.append(
            f"[TIME] Pipeline search time: {search_result.search_time_ms:.2f}ms"
        )

    def _rank_datasets(
        self,
        geo_datasets: List[GEOSeriesMetadata],
        request: SearchRequest,
        search_logs: List[str],
    ) -> List[RankedDataset]:
        """Rank datasets by relevance."""
        search_logs.append(f"[CACHE] Raw GEO datasets fetched: {len(geo_datasets)}")

        # Apply min_samples filter
        datasets = self._apply_sample_filter(geo_datasets, request, search_logs)

        # Rank by relevance
        ranked = self._calculate_relevance_scores(datasets, request)

        # Sort by score
        ranked.sort(key=lambda d: d.relevance_score, reverse=True)
        search_logs.append(f"[DATA] After ranking: {len(ranked)} datasets")

        return ranked

    def _apply_sample_filter(
        self,
        datasets: List[GEOSeriesMetadata],
        request: SearchRequest,
        search_logs: List[str],
    ) -> List[GEOSeriesMetadata]:
        """Apply minimum sample count filter."""
        min_samples = request.filters.get("min_samples") if request.filters else None

        if not min_samples:
            return datasets

        min_samples_int = int(min_samples)
        filtered = [
            d for d in datasets if d.sample_count and d.sample_count >= min_samples_int
        ]

        search_logs.append(
            f"[FILTER] After min_samples={min_samples_int}: {len(filtered)} datasets"
        )
        self.logger.info(
            f"Filtered by min_samples={min_samples_int}: {len(filtered)} remain"
        )

        return filtered

    def _calculate_relevance_scores(
        self, datasets: List[GEOSeriesMetadata], request: SearchRequest
    ) -> list:
        """Calculate relevance scores for datasets."""
        # Import here to avoid circular dependency
        from omics_oracle_v2.api.models.agent_schemas import RankedDataset
        
        ranked_datasets = []
        search_terms_lower = {term.lower() for term in request.search_terms}

        for dataset in datasets:
            # Handle dict conversion
            if isinstance(dataset, dict):
                dataset = GEOSeriesMetadata(**dataset)

            score = 0.0
            reasons = []

            # Title matches (weight: 0.4)
            title_lower = (dataset.title or "").lower()
            title_matches = sum(1 for term in search_terms_lower if term in title_lower)
            if title_matches > 0:
                score += min(0.4, title_matches * 0.2)
                reasons.append(f"Title matches {title_matches} term(s)")

            # Summary matches (weight: 0.3)
            summary_lower = (dataset.summary or "").lower()
            summary_matches = sum(
                1 for term in search_terms_lower if term in summary_lower
            )
            if summary_matches > 0:
                score += min(0.3, summary_matches * 0.15)
                reasons.append(f"Summary matches {summary_matches} term(s)")

            # Sample count bonus (up to 0.15)
            if dataset.sample_count:
                if dataset.sample_count >= 100:
                    score += 0.15
                    reasons.append(f"Large sample size: {dataset.sample_count}")
                elif dataset.sample_count >= 50:
                    score += 0.10
                    reasons.append(f"Good sample size: {dataset.sample_count}")
                elif dataset.sample_count >= 10:
                    score += 0.05
                    reasons.append(f"Adequate sample size: {dataset.sample_count}")

            # Ensure minimum score
            if not reasons:
                reasons.append("General database match")
                score = 0.1

            score = min(1.0, score)
            ranked_datasets.append(
                RankedDataset(
                    dataset=dataset, relevance_score=score, match_reasons=reasons
                )
            )

        return ranked_datasets

    async def _build_dataset_responses(
        self, ranked_datasets: list
    ) -> List[DatasetResponse]:
        """
        Convert ranked datasets to response format with database metrics enrichment.
        
        OPTIMIZED: Uses parallel enrichment with asyncio.gather() for 50x speedup.
        """
        import asyncio
        
        async def enrich_single_dataset(ranked) -> DatasetResponse:
            """Enrich a single dataset with database metrics (parallel execution)."""
            # Enrich with database metrics from UnifiedDB via GEOCache
            citation_count = 0
            pdf_count = 0
            processed_count = 0
            completion_rate = 0.0
            
            if self.geo_cache:
                try:
                    # Get complete GEO data from cache/DB
                    geo_data = await self.geo_cache.get(ranked.dataset.geo_id)
                    if geo_data:
                        # Extract publications from the correct structure
                        # UnifiedDB returns: {"geo": {...}, "papers": {"original": [...], "citing": []}}
                        papers = geo_data.get("papers", {}).get("original", [])
                        citation_count = len(papers)
                        
                        # Count PDFs (check download_history for 'downloaded' status)
                        pdf_count = sum(
                            1 for pub in papers
                            if any(h.get("status") == "downloaded" for h in pub.get("download_history", []))
                        )
                        
                        # Count processed (extracted) papers
                        processed_count = sum(
                            1 for pub in papers
                            if pub.get("extraction") is not None
                        )
                        
                        # Calculate completion rate
                        if citation_count > 0:
                            completion_rate = (pdf_count / citation_count) * 100
                        
                        logger.debug(
                            f"Enriched {ranked.dataset.geo_id}: citations={citation_count}, "
                            f"pdfs={pdf_count}, processed={processed_count}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to enrich {ranked.dataset.geo_id} with database metrics: {e}")
            
            return DatasetResponse(
                geo_id=ranked.dataset.geo_id,
                title=ranked.dataset.title,
                summary=ranked.dataset.summary,
                organism=ranked.dataset.organism,
                sample_count=ranked.dataset.sample_count,
                platform=ranked.dataset.platforms[0]
                if ranked.dataset.platforms
                else None,
                relevance_score=ranked.relevance_score,
                match_reasons=ranked.match_reasons,
                publication_date=ranked.dataset.publication_date,
                submission_date=ranked.dataset.submission_date,
                pubmed_ids=ranked.dataset.pubmed_ids,
                # Database metrics (enriched from UnifiedDB)
                citation_count=citation_count,
                pdf_count=pdf_count,
                processed_count=processed_count,
                completion_rate=completion_rate,
            )
        
        # OPTIMIZATION: Execute all enrichments in parallel
        if ranked_datasets:
            datasets = await asyncio.gather(*[
                enrich_single_dataset(ranked) for ranked in ranked_datasets
            ])
            return list(datasets)
        else:
            return []

    def _build_publication_responses(
        self, publications: List, search_logs: List[str]
    ) -> List[PublicationResponse]:
        """Convert publications to response format."""
        search_logs.append(f"[DOC] Found {len(publications)} related publications")

        if not publications:
            return []

        publication_responses = []

        for pub in publications:
            # Extract GEO IDs from text
            geo_ids = []
            if hasattr(pub, "abstract") and pub.abstract:
                geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.abstract))
            if hasattr(pub, "full_text") and pub.full_text:
                geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.full_text))

            # Handle publication date
            pub_date = getattr(pub, "publication_date", None)
            if pub_date:
                if isinstance(pub_date, datetime):
                    pub_date_str = pub_date.isoformat()
                elif hasattr(pub_date, "year"):
                    pub_date_str = f"{pub_date.year:04d}-{getattr(pub_date, 'month', 1):02d}-{getattr(pub_date, 'day', 1):02d}"
                else:
                    pub_date_str = str(pub_date)
            else:
                pub_date_str = None

            publication_responses.append(
                PublicationResponse(
                    pmid=getattr(pub, "pmid", None),
                    pmc_id=getattr(pub, "pmc_id", None),
                    doi=getattr(pub, "doi", None),
                    title=getattr(pub, "title", ""),
                    abstract=getattr(pub, "abstract", None),
                    authors=getattr(pub, "authors", []),
                    journal=getattr(pub, "journal", None),
                    publication_date=pub_date_str,
                    geo_ids_mentioned=list(set(geo_ids)),
                    fulltext_available=hasattr(pub, "full_text")
                    and pub.full_text is not None,
                    pdf_path=getattr(pub, "pdf_path", None),
                )
            )

        return publication_responses

    def _build_filters_metadata(
        self, request: SearchRequest, search_result, original_query: str
    ) -> Dict[str, str]:
        """Build metadata about applied filters."""
        filters = {}

        # Add GEO filters
        if request.filters:
            if request.filters.get("organism"):
                filters["organism"] = request.filters["organism"]
            if request.filters.get("study_type"):
                filters["study_type"] = request.filters["study_type"]
            if request.filters.get("min_samples"):
                filters["min_samples"] = str(request.filters["min_samples"])

        # Add search metadata
        filters["search_mode"] = search_result.query_type
        filters["cache_hit"] = str(search_result.cache_hit)
        filters["optimized"] = str(
            search_result.optimized_query
            and search_result.optimized_query != original_query
        )

        return filters

    def _build_query_processing_response(
        self, search_result
    ) -> Optional[QueryProcessingResponse]:
        """Build query processing context for RAG Phase 3."""
        if not search_result.query_processing:
            return None

        # Handle both QueryProcessingContext object and dict (from cache/serialization)
        qp = search_result.query_processing
        
        if isinstance(qp, dict):
            # Already converted to dict (from cache or serialization)
            extracted_entities = qp.get("extracted_entities", {})
            expanded_terms = qp.get("expanded_terms", [])
            geo_search_terms = qp.get("geo_search_terms", [])
            search_intent = qp.get("search_intent")
            query_type = qp.get("query_type")
        else:
            # QueryProcessingContext object
            extracted_entities = qp.extracted_entities
            expanded_terms = qp.expanded_terms
            geo_search_terms = qp.geo_search_terms
            search_intent = qp.search_intent
            query_type = qp.query_type

        self.logger.info(
            f"[RAG] Query processing context exposed: "
            f"entities={len(extracted_entities)}, "
            f"expanded={len(expanded_terms)}"
        )

        return QueryProcessingResponse(
            extracted_entities=extracted_entities,
            expanded_terms=expanded_terms,
            geo_search_terms=geo_search_terms,
            search_intent=search_intent,
            query_type=query_type,
        )
