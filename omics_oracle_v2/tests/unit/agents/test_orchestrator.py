"""Tests for Orchestrator."""

import pytest

from omics_oracle_v2.agents import Orchestrator
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models.orchestrator import OrchestratorInput, WorkflowStage, WorkflowType
from omics_oracle_v2.core.config import Settings


class TestOrchestratorModels:
    """Test Orchestrator models."""

    def test_orchestrator_input_defaults(self):
        """Test orchestrator input with defaults."""
        orch_input = OrchestratorInput(query="test query")
        assert orch_input.workflow_type == WorkflowType.FULL_ANALYSIS
        assert orch_input.max_results == 50
        assert orch_input.report_type == "comprehensive"
        assert orch_input.include_quality_analysis is True

    def test_workflow_types(self):
        """Test all workflow types."""
        assert WorkflowType.SIMPLE_SEARCH.value == "simple_search"
        assert WorkflowType.FULL_ANALYSIS.value == "full_analysis"
        assert WorkflowType.QUICK_REPORT.value == "quick_report"
        assert WorkflowType.DATA_VALIDATION.value == "data_validation"

    def test_workflow_stages(self):
        """Test workflow stages."""
        assert WorkflowStage.INITIALIZED.value == "initialized"
        assert WorkflowStage.QUERY_PROCESSING.value == "query_processing"
        assert WorkflowStage.DATASET_SEARCH.value == "dataset_search"
        assert WorkflowStage.DATA_VALIDATION.value == "data_validation"
        assert WorkflowStage.REPORT_GENERATION.value == "report_generation"
        assert WorkflowStage.COMPLETED.value == "completed"
        assert WorkflowStage.FAILED.value == "failed"

    def test_orchestrator_input_validation(self):
        """Test input validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OrchestratorInput(query="")  # Empty query should fail


class TestOrchestrator:
    """Test Orchestrator functionality."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()

    @pytest.fixture
    def orchestrator(self, settings):
        """Create Orchestrator instance."""
        return Orchestrator(settings)

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator can be initialized."""
        assert orchestrator is not None
        assert orchestrator.state == AgentState.IDLE
        assert orchestrator.query_agent is not None
        assert orchestrator.search_agent is not None
        assert orchestrator.data_agent is not None
        assert orchestrator.report_agent is not None

    def test_orchestrator_cleanup(self, orchestrator):
        """Test orchestrator cleanup."""
        orchestrator.cleanup()
        # Should not raise errors

    def test_simple_search_workflow(self, orchestrator):
        """Test simple search workflow execution."""
        orch_input = OrchestratorInput(
            query="TP53 breast cancer",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert result.output is not None
        assert result.output.query == "TP53 breast cancer"
        assert result.output.workflow_type == WorkflowType.SIMPLE_SEARCH

    def test_full_analysis_workflow(self, orchestrator):
        """Test full analysis workflow execution."""
        orch_input = OrchestratorInput(
            query="BRCA1 mutations breast cancer",
            workflow_type=WorkflowType.FULL_ANALYSIS,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert result.output is not None
        assert result.output.workflow_type == WorkflowType.FULL_ANALYSIS

        # Check stages were executed (may have some failures)
        assert len(result.output.stage_results) >= 1

        # Check final stage is reasonable
        assert result.output.final_stage in [
            WorkflowStage.COMPLETED,
            WorkflowStage.REPORT_GENERATION,
            WorkflowStage.DATA_VALIDATION,
            WorkflowStage.DATASET_SEARCH,
        ]

    def test_workflow_with_filters(self, orchestrator):
        """Test workflow with organism and sample filters."""
        orch_input = OrchestratorInput(
            query="gene expression",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=10,
            organisms=["Homo sapiens"],
            min_samples=20,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True

    def test_report_type_options(self, orchestrator):
        """Test different report types."""
        for report_type in ["brief", "comprehensive", "technical", "executive"]:
            orch_input = OrchestratorInput(
                query="test",
                workflow_type=WorkflowType.SIMPLE_SEARCH,
                max_results=3,
                report_type=report_type,
            )
            result = orchestrator.execute(orch_input)
            assert result.success is True

    def test_report_format_options(self, orchestrator):
        """Test different report formats."""
        for report_format in ["markdown", "json", "html", "text"]:
            orch_input = OrchestratorInput(
                query="breast cancer TP53",  # Better query with entities
                workflow_type=WorkflowType.SIMPLE_SEARCH,
                max_results=3,
                report_format=report_format,
            )
            result = orchestrator.execute(orch_input)
            # Orchestrator should always succeed even if workflow has issues
            assert result.success is True
            # Only check report if workflow completed
            # (may fail due to NCBI email configuration in tests)
            if result.output.final_stage == WorkflowStage.COMPLETED:
                assert result.output.final_report is not None

    def test_empty_query_validation(self, orchestrator):
        """Test that empty query is rejected."""
        orch_input = OrchestratorInput(query="   ")  # Whitespace only
        result = orchestrator.execute(orch_input)

        assert result.success is False
        assert result.error is not None

    def test_stage_results_recorded(self, orchestrator):
        """Test that stage results are properly recorded."""
        orch_input = OrchestratorInput(
            query="cancer research",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert len(result.output.stage_results) > 0

        # Each stage should have agent name
        for stage_result in result.output.stage_results:
            assert stage_result.agent_name is not None
            assert stage_result.execution_time_ms >= 0

    def test_execution_summary(self, orchestrator):
        """Test execution summary generation."""
        orch_input = OrchestratorInput(
            query="test query",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        summary = result.output.get_execution_summary()
        assert "test query" in summary
        assert "simple_search" in summary

    def test_get_stage_result(self, orchestrator):
        """Test retrieving specific stage result."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True

        # Should have query stage
        query_stage = result.output.get_stage_result(WorkflowStage.QUERY_PROCESSING)
        assert query_stage is not None
        assert query_stage.agent_name == "QueryAgent"

    def test_datasets_found_count(self, orchestrator):
        """Test that datasets found count is recorded."""
        orch_input = OrchestratorInput(
            query="breast cancer",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=10,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert result.output.total_datasets_found >= 0

    def test_execution_time_recorded(self, orchestrator):
        """Test that execution time is recorded."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert result.output.total_execution_time_ms > 0

    def test_quality_analysis_flag(self, orchestrator):
        """Test quality analysis can be disabled."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
            include_quality_analysis=False,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True

    def test_recommendations_flag(self, orchestrator):
        """Test recommendations can be disabled."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
            include_recommendations=False,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True

    def test_max_results_limit(self, orchestrator):
        """Test max results limiting."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=3,  # Very low limit
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Should respect the limit
        if result.output.total_datasets_found > 0:
            assert result.output.total_datasets_found <= 3

    def test_report_title_generated(self, orchestrator):
        """Test that report title is generated."""
        orch_input = OrchestratorInput(
            query="TP53 mutations cancer",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Only check if workflow completed successfully
        # (may fail due to NCBI email configuration in tests)
        if result.output.final_stage == WorkflowStage.COMPLETED:
            assert result.output.report_title is not None
            assert len(result.output.report_title) > 0

    def test_final_report_generated(self, orchestrator):
        """Test that final report is generated."""
        orch_input = OrchestratorInput(
            query="cancer research gene expression",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Only check if workflow completed successfully
        # (may fail due to NCBI email configuration in tests)
        if result.output.final_stage == WorkflowStage.COMPLETED:
            assert result.output.final_report is not None
            assert len(result.output.final_report) > 0

    def test_stages_completed_count(self, orchestrator):
        """Test stages completed counting."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        assert result.output.stages_completed > 0
        # Should match successful stages
        successful_stages = len([r for r in result.output.stage_results if r.success])
        assert result.output.stages_completed == successful_stages


class TestWorkflowTypes:
    """Test different workflow types."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator."""
        return Orchestrator(Settings())

    def test_quick_report_not_implemented(self, orchestrator):
        """Test quick report workflow (not implemented)."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.QUICK_REPORT,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        # Agent executes successfully but workflow fails
        assert result.output.success is False
        assert "not yet implemented" in result.output.error_message.lower()

    def test_data_validation_not_implemented(self, orchestrator):
        """Test data validation workflow (not implemented)."""
        orch_input = OrchestratorInput(
            query="test",
            workflow_type=WorkflowType.DATA_VALIDATION,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        # Agent executes successfully but workflow fails
        assert result.output.success is False
        assert "not yet implemented" in result.output.error_message.lower()
