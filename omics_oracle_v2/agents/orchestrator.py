"""Orchestrator agent for coordinating multi-agent workflows."""

import asyncio
import logging
import time
from typing import List

from omics_oracle_v2.agents.base import Agent
from omics_oracle_v2.agents.data_agent import DataAgent
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.data import DataInput
from omics_oracle_v2.agents.models.orchestrator import (
    OrchestratorInput,
    OrchestratorOutput,
    WorkflowResult,
    WorkflowStage,
    WorkflowType,
)
from omics_oracle_v2.agents.models.report import ReportFormat, ReportInput, ReportType
from omics_oracle_v2.agents.models.search import RankedDataset, SearchInput, SearchOutput
from omics_oracle_v2.agents.query_agent import QueryAgent
from omics_oracle_v2.agents.report_agent import ReportAgent
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline, UnifiedSearchConfig

logger = logging.getLogger(__name__)


class Orchestrator(Agent[OrchestratorInput, OrchestratorOutput]):
    """Orchestrator for multi-agent biomedical research workflows.

    Coordinates QueryAgent, OmicsSearchPipeline, DataAgent, and ReportAgent to execute
    complete research workflows from user query to final report.

    Note: Previously used SearchAgent, now uses OmicsSearchPipeline directly for cleaner architecture.
    """

    def __init__(self, settings):
        """Initialize Orchestrator with all sub-agents and search pipeline."""
        super().__init__(settings)

        # Initialize query, data, and report agents
        self.query_agent = QueryAgent(settings)
        self.data_agent = DataAgent(settings)
        self.report_agent = ReportAgent(settings)

        # Initialize search pipeline (replaces SearchAgent)
        search_config = UnifiedSearchConfig(
            enable_geo_search=True,
            enable_publication_search=True,
            enable_query_optimization=True,
            enable_caching=True,
            max_geo_results=100,
            max_publication_results=50,
        )
        self.search_pipeline = OmicsSearchPipeline(search_config)
        logger.info("Orchestrator initialized with OmicsSearchPipeline")

    def cleanup(self) -> None:
        """Cleanup all sub-agents."""
        for agent in [self.query_agent, self.data_agent, self.report_agent]:
            try:
                agent.cleanup()
            except Exception:
                pass
        super().cleanup()

    def _validate_input(self, input_data: OrchestratorInput) -> OrchestratorInput:
        """Validate orchestrator input."""
        if not input_data.query or len(input_data.query.strip()) == 0:
            from omics_oracle_v2.agents.exceptions import AgentValidationError

            raise AgentValidationError("Query cannot be empty")
        return input_data

    def _process(self, input_data: OrchestratorInput, context) -> OrchestratorOutput:
        """Execute the workflow based on workflow type."""
        start_time = time.time()

        # Initialize output
        output = OrchestratorOutput(
            workflow_type=input_data.workflow_type,
            query=input_data.query,
            final_stage=WorkflowStage.INITIALIZED,
            success=False,
        )

        try:
            # Execute workflow based on type
            if input_data.workflow_type == WorkflowType.FULL_ANALYSIS:
                output = self._execute_full_analysis(input_data, output)
            elif input_data.workflow_type == WorkflowType.SIMPLE_SEARCH:
                output = self._execute_simple_search(input_data, output)
            elif input_data.workflow_type == WorkflowType.QUICK_REPORT:
                output = self._execute_quick_report(input_data, output)
            elif input_data.workflow_type == WorkflowType.DATA_VALIDATION:
                output = self._execute_data_validation(input_data, output)
            else:
                raise ValueError(f"Unsupported workflow type: {input_data.workflow_type}")

            # Mark as successful if workflow didn't explicitly fail
            if output.final_stage != WorkflowStage.FAILED:
                output.success = True

        except Exception as e:
            output.success = False
            output.error_message = str(e)
            output.final_stage = WorkflowStage.FAILED

        # Calculate total execution time
        output.total_execution_time_ms = (time.time() - start_time) * 1000
        output.stages_completed = len([r for r in output.stage_results if r.success])

        return output

    def _execute_full_analysis(
        self, input_data: OrchestratorInput, output: OrchestratorOutput
    ) -> OrchestratorOutput:
        """Execute full analysis workflow: Query -> Search -> Data -> Report."""
        # Stage 1: Query Processing
        query_result = self._execute_query_stage(input_data)
        output.stage_results.append(query_result)
        output.final_stage = WorkflowStage.QUERY_PROCESSING

        if not query_result.success:
            output.error_message = query_result.error
            return output

        # Stage 2: Dataset Search
        search_result = self._execute_search_stage(input_data, query_result)
        output.stage_results.append(search_result)
        output.final_stage = WorkflowStage.DATASET_SEARCH

        if not search_result.success:
            output.error_message = search_result.error
            return output

        output.total_datasets_found = len(search_result.output.datasets)

        # Stage 3: Data Validation
        data_result = self._execute_data_stage(input_data, search_result)
        output.stage_results.append(data_result)
        output.final_stage = WorkflowStage.DATA_VALIDATION

        if not data_result.success:
            output.error_message = data_result.error
            return output

        output.total_datasets_analyzed = len(data_result.output.processed_datasets)
        output.high_quality_datasets = sum(
            1 for d in data_result.output.processed_datasets if d.quality_score >= 0.75
        )

        # Stage 4: Report Generation
        report_result = self._execute_report_stage(input_data, query_result, data_result)
        output.stage_results.append(report_result)
        output.final_stage = WorkflowStage.REPORT_GENERATION

        if not report_result.success:
            output.error_message = report_result.error
            return output

        # Extract final report
        output.final_report = report_result.output.full_report
        output.report_title = report_result.output.title
        output.final_stage = WorkflowStage.COMPLETED

        return output

    def _execute_simple_search(
        self, input_data: OrchestratorInput, output: OrchestratorOutput
    ) -> OrchestratorOutput:
        """Execute simple search workflow: Query -> Search -> Report (skip data validation)."""
        # Stage 1: Query Processing
        query_result = self._execute_query_stage(input_data)
        output.stage_results.append(query_result)
        output.final_stage = WorkflowStage.QUERY_PROCESSING

        if not query_result.success:
            output.error_message = query_result.error
            return output

        # Stage 2: Dataset Search
        search_result = self._execute_search_stage(input_data, query_result)
        output.stage_results.append(search_result)
        output.final_stage = WorkflowStage.DATASET_SEARCH

        if not search_result.success:
            output.error_message = search_result.error
            return output

        output.total_datasets_found = len(search_result.output.datasets)

        # Stage 3: Report Generation (convert search results to data format)
        # Create simple processed datasets from search results
        from omics_oracle_v2.agents.models.data import DataQualityLevel, ProcessedDataset

        processed_datasets = []
        for ranked_ds in search_result.output.datasets:
            # Extract the actual dataset from RankedDataset
            ds = ranked_ds.dataset
            processed_datasets.append(
                ProcessedDataset(
                    geo_id=ds.geo_id,
                    title=ds.title,
                    summary=ds.summary or "",
                    organism=ds.organism or "Unknown",
                    sample_count=ds.sample_count or 0,
                    platform_count=1,
                    has_publication=bool(ds.pubmed_ids),  # pubmed_ids is a list
                    has_sra_data=ds.has_sra_data() if hasattr(ds, "has_sra_data") else False,
                    quality_score=ranked_ds.relevance_score,  # Use relevance as quality
                    quality_level=DataQualityLevel.FAIR,
                    relevance_score=ranked_ds.relevance_score,
                    metadata_completeness=0.5,
                )
            )

        # Create a fake data result for report stage
        from omics_oracle_v2.agents.models.data import DataOutput

        fake_data_result = WorkflowResult(
            stage=WorkflowStage.DATA_VALIDATION,
            success=True,
            agent_name="DataAgent",
            output=DataOutput(
                processed_datasets=processed_datasets,
                total_processed=len(processed_datasets),
                statistics={"quality_levels": {}},
            ),
        )

        report_result = self._execute_report_stage(input_data, query_result, fake_data_result)
        output.stage_results.append(report_result)
        output.final_stage = WorkflowStage.REPORT_GENERATION

        if not report_result.success:
            output.error_message = report_result.error
            return output

        output.total_datasets_analyzed = len(processed_datasets)
        output.final_report = report_result.output.full_report
        output.report_title = report_result.output.title
        output.final_stage = WorkflowStage.COMPLETED

        return output

    def _execute_quick_report(
        self, input_data: OrchestratorInput, output: OrchestratorOutput
    ) -> OrchestratorOutput:
        """Execute quick report workflow: Search -> Report (use query as dataset IDs)."""
        # Not fully implemented - would need dataset IDs in input
        output.error_message = "Quick report workflow not yet implemented"
        output.final_stage = WorkflowStage.FAILED
        output.success = False
        return output

    def _execute_data_validation(
        self, input_data: OrchestratorInput, output: OrchestratorOutput
    ) -> OrchestratorOutput:
        """Execute data validation workflow: Data -> Report (validate existing datasets).

        This workflow assumes the query contains GEO dataset IDs (e.g., GSE12345).
        It validates the datasets and generates a quality report.
        """
        # Stage 1: Extract dataset IDs from query
        output.final_stage = WorkflowStage.QUERY_PROCESSING
        query_result = self._execute_query_stage(input_data)
        output.stage_results.append(query_result)

        if not query_result.success:
            output.error_message = f"Query processing failed: {query_result.error}"
            output.final_stage = WorkflowStage.FAILED
            return output

        # Stage 2: Validate datasets
        output.final_stage = WorkflowStage.DATA_VALIDATION

        # Extract GEO IDs from query or use processed entities
        geo_ids = self._extract_geo_ids_from_query(input_data.query)

        if not geo_ids:
            # If no explicit IDs, treat query as search and validate results
            search_result = self._execute_search_stage(input_data, query_result.output)
            output.stage_results.append(search_result)

            if not search_result.success or not search_result.output:
                output.error_message = "No datasets found to validate"
                output.final_stage = WorkflowStage.FAILED
                return output

            geo_ids = search_result.output.get("dataset_ids", [])[:10]  # Limit to 10

        # Validate the datasets
        data_result = self._execute_data_validation_stage(geo_ids)
        output.stage_results.append(data_result)

        if not data_result.success:
            output.error_message = f"Data validation failed: {data_result.error}"
            output.final_stage = WorkflowStage.FAILED
            return output

        # Extract metrics
        validated_data = data_result.output or {}
        output.total_datasets_found = len(geo_ids)
        output.total_datasets_analyzed = len(validated_data.get("validated_datasets", []))
        output.high_quality_datasets = len(validated_data.get("high_quality_datasets", []))

        # Stage 3: Generate validation report
        output.final_stage = WorkflowStage.REPORT_GENERATION
        report_result = self._execute_report_stage(
            input_data,
            query_result.output,
            None,  # No search results
            validated_data,
        )
        output.stage_results.append(report_result)

        if not report_result.success:
            output.error_message = f"Report generation failed: {report_result.error}"
            output.final_stage = WorkflowStage.FAILED
            return output

        # Extract report
        report_data = report_result.output or {}
        output.final_report = report_data.get("report")
        output.report_title = report_data.get("title", "Dataset Validation Report")

        output.final_stage = WorkflowStage.COMPLETED
        return output

    def _extract_geo_ids_from_query(self, query: str) -> list:
        """Extract GEO dataset IDs from query string."""
        import re

        # Match patterns like GSE12345, GDS1234, GPL1234
        pattern = r"\b(GSE\d+|GDS\d+|GPL\d+)\b"
        matches = re.findall(pattern, query, re.IGNORECASE)
        return [m.upper() for m in matches]

    def _execute_data_validation_stage(self, dataset_ids: list) -> WorkflowResult:
        """Execute data validation on specific datasets."""
        start_time = time.time()

        try:
            data_input = DataInput(
                dataset_ids=dataset_ids,
                validate_metadata=True,
                validate_samples=True,
                validate_files=False,  # Skip file validation for speed
            )

            result = self.data_agent.execute(data_input)
            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.DATA_VALIDATION,
                success=result.success,
                agent_name="DataAgent",
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WorkflowResult(
                stage=WorkflowStage.DATA_VALIDATION,
                success=False,
                agent_name="DataAgent",
                output=None,
                error=str(e),
                execution_time_ms=execution_time,
            )

    def _execute_query_stage(self, input_data: OrchestratorInput) -> WorkflowResult:
        """Execute query processing stage."""
        start_time = time.time()

        try:
            query_input = QueryInput(
                query=input_data.query,
                max_entities=100,
                include_synonyms=True,
            )

            result = self.query_agent.execute(query_input)
            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.QUERY_PROCESSING,
                success=result.success,
                agent_name="QueryAgent",
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
                metadata=result.metadata,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WorkflowResult(
                stage=WorkflowStage.QUERY_PROCESSING,
                success=False,
                agent_name="QueryAgent",
                error=str(e),
                execution_time_ms=execution_time,
            )

    def _execute_search_stage(
        self, input_data: OrchestratorInput, query_result: WorkflowResult
    ) -> WorkflowResult:
        """Execute dataset search stage using OmicsSearchPipeline."""
        start_time = time.time()

        try:
            # Extract query from query results
            query = " ".join(query_result.output.search_terms)

            # Build query with GEO filters (organism, study_type)
            query_with_filters = self._build_search_query(query, input_data)

            logger.info(f"Orchestrator executing search: '{query_with_filters}'")

            # Execute search using pipeline
            search_result = asyncio.run(
                self.search_pipeline.search(
                    query=query_with_filters,
                    max_geo_results=input_data.max_results,
                    max_publication_results=50,
                    use_cache=True,
                )
            )

            # Apply min_samples filter if specified
            geo_datasets = search_result.geo_datasets
            if input_data.min_samples:
                geo_datasets = self._filter_datasets_by_samples(geo_datasets, input_data.min_samples)
                logger.info(
                    f"Filtered by min_samples={input_data.min_samples}: {len(geo_datasets)} datasets remain"
                )

            # Rank datasets by relevance
            ranked_datasets = self._rank_datasets(geo_datasets, query_result.output.search_terms)

            # Build SearchOutput to match expected format
            search_output = SearchOutput(
                datasets=ranked_datasets,
                total_found=len(ranked_datasets),
                search_terms_used=query_result.output.search_terms,
                filters_applied={
                    "search_mode": search_result.query_type,
                    "cache_hit": str(search_result.cache_hit),
                    "organism": input_data.organisms[0] if input_data.organisms else None,
                    "study_type": input_data.study_types[0] if input_data.study_types else None,
                    "min_samples": str(input_data.min_samples) if input_data.min_samples else None,
                },
                publications=search_result.publications,
                publications_count=len(search_result.publications),
            )

            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.DATASET_SEARCH,
                success=True,
                agent_name="OmicsSearchPipeline",
                output=search_output,
                error=None,
                execution_time_ms=execution_time,
                metadata={
                    "query_type": search_result.query_type,
                    "optimized_query": search_result.optimized_query,
                    "cache_hit": search_result.cache_hit,
                    "search_time_ms": search_result.search_time_ms,
                    "total_results": search_result.total_results,
                },
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Search stage failed: {e}", exc_info=True)
            return WorkflowResult(
                stage=WorkflowStage.DATASET_SEARCH,
                success=False,
                agent_name="OmicsSearchPipeline",
                error=str(e),
                execution_time_ms=execution_time,
            )

    def _execute_data_stage(
        self, input_data: OrchestratorInput, search_result: WorkflowResult
    ) -> WorkflowResult:
        """Execute data validation stage."""
        start_time = time.time()

        try:
            # Build data input from search results
            data_input = DataInput(
                datasets=search_result.output.datasets,
                min_quality_score=0.0,  # Accept all
            )

            result = self.data_agent.execute(data_input)
            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.DATA_VALIDATION,
                success=result.success,
                agent_name="DataAgent",
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
                metadata=result.metadata,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WorkflowResult(
                stage=WorkflowStage.DATA_VALIDATION,
                success=False,
                agent_name="DataAgent",
                error=str(e),
                execution_time_ms=execution_time,
            )

    def _execute_report_stage(
        self,
        input_data: OrchestratorInput,
        query_result: WorkflowResult,
        data_result: WorkflowResult,
    ) -> WorkflowResult:
        """Execute report generation stage."""
        start_time = time.time()

        try:
            # Map report type string to enum
            report_type_map = {
                "brief": ReportType.BRIEF,
                "comprehensive": ReportType.COMPREHENSIVE,
                "technical": ReportType.TECHNICAL,
                "executive": ReportType.EXECUTIVE,
            }
            report_type = report_type_map.get(input_data.report_type.lower(), ReportType.COMPREHENSIVE)

            # Map report format string to enum
            report_format_map = {
                "markdown": ReportFormat.MARKDOWN,
                "json": ReportFormat.JSON,
                "html": ReportFormat.HTML,
                "text": ReportFormat.TEXT,
            }
            report_format = report_format_map.get(input_data.report_format.lower(), ReportFormat.MARKDOWN)

            # Build report input from data results
            report_input = ReportInput(
                datasets=data_result.output.processed_datasets,
                query_context=input_data.query,
                report_type=report_type,
                report_format=report_format,
                include_quality_analysis=input_data.include_quality_analysis,
                include_recommendations=input_data.include_recommendations,
                max_datasets=min(20, len(data_result.output.processed_datasets)),
            )

            result = self.report_agent.execute(report_input)
            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.REPORT_GENERATION,
                success=result.success,
                agent_name="ReportAgent",
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
                metadata=result.metadata,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WorkflowResult(
                stage=WorkflowStage.REPORT_GENERATION,
                success=False,
                agent_name="ReportAgent",
                error=str(e),
                execution_time_ms=execution_time,
            )

    # Helper methods for search (migrated from SearchAgent)

    def _build_search_query(self, query: str, input_data: OrchestratorInput) -> str:
        """
        Build query string with GEO filters applied.

        Adds organism and study_type filters to the base query using GEO query syntax.

        Args:
            query: Base query string
            input_data: Orchestrator input with filters

        Returns:
            Query string with filters applied

        Example:
            >>> _build_search_query("diabetes", OrchestratorInput(organisms=["Homo sapiens"]))
            'diabetes AND "Homo sapiens"[Organism]'
        """
        query_parts = [query]

        # Add organism filter
        if input_data.organisms and len(input_data.organisms) > 0:
            organism = input_data.organisms[0]
            query_parts.append(f'"{organism}"[Organism]')
            logger.info(f"Added organism filter: {organism}")

        # Add study type filter
        if input_data.study_types and len(input_data.study_types) > 0:
            study_type = input_data.study_types[0]
            query_parts.append(f'"{study_type}"[DataSet Type]')
            logger.info(f"Added study type filter: {study_type}")

        # Combine with AND logic
        final_query = " AND ".join(query_parts) if len(query_parts) > 1 else query_parts[0]

        return final_query

    def _filter_datasets_by_samples(
        self, datasets: List[GEOSeriesMetadata], min_samples: int
    ) -> List[GEOSeriesMetadata]:
        """
        Filter datasets by minimum sample count.

        Args:
            datasets: List of GEO datasets
            min_samples: Minimum number of samples required

        Returns:
            Filtered list of datasets
        """
        return [d for d in datasets if d.sample_count and d.sample_count >= min_samples]

    def _rank_datasets(
        self, datasets: List[GEOSeriesMetadata], search_terms: List[str]
    ) -> List[RankedDataset]:
        """
        Rank datasets by relevance to search terms using simple keyword matching.

        Args:
            datasets: List of GEO datasets to rank
            search_terms: Search terms to match against

        Returns:
            List of ranked datasets with relevance scores
        """
        ranked = []
        search_terms_lower = {term.lower() for term in search_terms}

        for dataset in datasets:
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
            summary_matches = sum(1 for term in search_terms_lower if term in summary_lower)
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
            ranked.append(RankedDataset(dataset=dataset, relevance_score=score, match_reasons=reasons))

        # Sort by relevance (highest first)
        ranked.sort(key=lambda d: d.relevance_score, reverse=True)

        return ranked
