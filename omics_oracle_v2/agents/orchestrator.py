"""Orchestrator agent for coordinating multi-agent workflows."""

import time

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
from omics_oracle_v2.agents.models.search import SearchInput
from omics_oracle_v2.agents.query_agent import QueryAgent
from omics_oracle_v2.agents.report_agent import ReportAgent
from omics_oracle_v2.agents.search_agent import SearchAgent


class Orchestrator(Agent[OrchestratorInput, OrchestratorOutput]):
    """Orchestrator for multi-agent biomedical research workflows.

    Coordinates QueryAgent, SearchAgent, DataAgent, and ReportAgent to execute
    complete research workflows from user query to final report.
    """

    def __init__(self, settings):
        """Initialize Orchestrator with all sub-agents."""
        super().__init__(settings)

        # Initialize all sub-agents
        self.query_agent = QueryAgent(settings)
        self.search_agent = SearchAgent(settings)
        self.data_agent = DataAgent(settings)
        self.report_agent = ReportAgent(settings)

    def cleanup(self) -> None:
        """Cleanup all sub-agents."""
        for agent in [self.query_agent, self.search_agent, self.data_agent, self.report_agent]:
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
        for ds in search_result.output.datasets:
            processed_datasets.append(
                ProcessedDataset(
                    geo_id=ds.geo_id,
                    title=ds.title,
                    summary=ds.summary or "",
                    organism=ds.organism or "Unknown",
                    sample_count=ds.sample_count or 0,
                    platform_count=1,
                    has_publication=False,
                    has_sra_data=False,
                    quality_score=ds.relevance_score,  # Use relevance as quality
                    quality_level=DataQualityLevel.FAIR,
                    relevance_score=ds.relevance_score,
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
        """Execute data validation workflow: Data -> Report (validate existing datasets)."""
        # Not fully implemented - would need datasets in input
        output.error_message = "Data validation workflow not yet implemented"
        output.final_stage = WorkflowStage.FAILED
        output.success = False
        return output

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
        """Execute dataset search stage."""
        start_time = time.time()

        try:
            # Build search input from query results
            search_input = SearchInput(
                search_terms=query_result.output.search_terms,
                max_results=input_data.max_results,
                organisms=input_data.organisms,
                min_samples=input_data.min_samples,
                study_types=input_data.study_types,
            )

            result = self.search_agent.execute(search_input)
            execution_time = (time.time() - start_time) * 1000

            return WorkflowResult(
                stage=WorkflowStage.DATASET_SEARCH,
                success=result.success,
                agent_name="SearchAgent",
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
                metadata=result.metadata,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WorkflowResult(
                stage=WorkflowStage.DATASET_SEARCH,
                success=False,
                agent_name="SearchAgent",
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
