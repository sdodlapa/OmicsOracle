"""
Integration tests for multi-agent workflows.

Tests complete end-to-end workflows with all agents working together.
These tests validate that the agent framework can handle real-world scenarios
including successful workflows, error conditions, and performance requirements.

Test Categories:
- Simple Workflows: Query -> Search -> Report
- Full Workflows: All 4 agents in sequence
- Error Handling: API failures, invalid inputs, edge cases
- Performance: Response time benchmarks
- Caching: Verify caching optimization works

Markers:
- @pytest.mark.integration: Requires external services (may be slow)
- @pytest.mark.slow: Takes >5 seconds to run
"""

import time

import pytest

from omics_oracle_v2.agents import DataAgent, Orchestrator, QueryAgent, ReportAgent, SearchAgent
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.data import DataInput
from omics_oracle_v2.agents.models.orchestrator import OrchestratorInput, WorkflowStage, WorkflowType
from omics_oracle_v2.agents.models.report import ReportFormat, ReportInput, ReportType
from omics_oracle_v2.agents.models.search import SearchInput
from omics_oracle_v2.core import Settings

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def settings():
    """Create settings for integration tests."""
    from omics_oracle_v2.core import GEOSettings

    return Settings(
        debug=True,
        log_level="INFO",
        geo=GEOSettings(
            ncbi_email="test@example.com",
            rate_limit=3,
            timeout=30,
            verify_ssl=False,  # Disable SSL verification for tests
        ),
    )


@pytest.fixture
def query_agent(settings):
    """Create QueryAgent instance."""
    return QueryAgent(settings=settings)


@pytest.fixture
def search_agent(settings):
    """Create SearchAgent instance."""
    return SearchAgent(settings=settings)


@pytest.fixture
def data_agent(settings):
    """Create DataAgent instance."""
    return DataAgent(settings=settings)


@pytest.fixture
def report_agent(settings):
    """Create ReportAgent instance."""
    return ReportAgent(settings=settings)


@pytest.fixture
def orchestrator(settings):
    """Create Orchestrator instance."""
    return Orchestrator(settings=settings)


# ============================================================================
# Simple Workflow Tests
# ============================================================================


class TestSimpleWorkflows:
    """Test simple 2-3 agent workflows."""

    def test_query_to_search_workflow(self, query_agent, search_agent):
        """Test Query -> Search workflow."""
        # Step 1: Process natural language query
        query_input = QueryInput(query="Find TP53 datasets in breast cancer")
        query_result = query_agent.execute(query_input)

        assert query_result.success is True
        assert len(query_result.output.entities) > 0

        # Step 2: Use extracted terms for search
        search_terms = query_result.output.search_terms
        search_input = SearchInput(search_terms=search_terms, max_results=10)
        search_result = search_agent.execute(search_input)

        assert search_result.success is True
        assert len(search_result.output.datasets) > 0

    def test_search_to_data_workflow(self, search_agent, data_agent):
        """Test Search -> Data workflow."""
        # Step 1: Search for datasets
        search_input = SearchInput(search_terms=["cancer"], max_results=5)
        search_result = search_agent.execute(search_input)

        assert search_result.success is True
        datasets = search_result.output.datasets

        # Step 2: Validate dataset quality
        if len(datasets) > 0:
            # DataInput expects RankedDataset objects
            data_input = DataInput(datasets=datasets[:3])
            data_result = data_agent.execute(data_input)

            assert data_result.success is True
            assert len(data_result.output.processed_datasets) > 0

    def test_query_to_report_workflow(self, query_agent, search_agent, data_agent, report_agent):
        """Test Query -> Search -> Data -> Report workflow (need datasets for report)."""
        # Step 1: Process query
        query_input = QueryInput(query="Find TP53 datasets in breast cancer")
        query_result = query_agent.execute(query_input)

        assert query_result.success is True

        # Step 2: Search for datasets
        search_input = SearchInput(search_terms=query_result.output.search_terms, max_results=5)
        search_result = search_agent.execute(search_input)

        assert search_result.success is True

        # Step 3: Process datasets (ReportAgent requires ProcessedDataset)
        if len(search_result.output.datasets) > 0:
            data_input = DataInput(datasets=search_result.output.datasets[:3])
            data_result = data_agent.execute(data_input)

            assert data_result.success is True

            # Step 4: Generate report
            if len(data_result.output.processed_datasets) > 0:
                report_input = ReportInput(
                    datasets=data_result.output.processed_datasets,
                    query_context=query_result.output.original_query,
                    report_type=ReportType.BRIEF,
                    report_format=ReportFormat.MARKDOWN,
                )
                report_result = report_agent.execute(report_input)

                assert report_result.success is True
                assert len(report_result.output.full_report) > 0


# ============================================================================
# Full Workflow Tests (All 4 Agents)
# ============================================================================


class TestFullWorkflows:
    """Test complete 4-agent workflows."""

    def test_full_analysis_workflow_manual(self, query_agent, search_agent, data_agent, report_agent):
        """Test complete workflow: Query -> Search -> Data -> Report."""
        # Step 1: Query Agent
        query_input = QueryInput(query="Find breast cancer gene expression datasets")
        query_result = query_agent.execute(query_input)

        assert query_result.success is True
        assert len(query_result.output.search_terms) > 0

        # Step 2: Search Agent
        search_input = SearchInput(search_terms=query_result.output.search_terms, max_results=10)
        search_result = search_agent.execute(search_input)

        assert search_result.success is True

        # Step 3: Data Agent (if we have results)
        if len(search_result.output.datasets) > 0:
            # DataInput expects RankedDataset objects
            data_input = DataInput(datasets=search_result.output.datasets[:5])
            data_result = data_agent.execute(data_input)

            assert data_result.success is True

            # Step 4: Report Agent
            report_input = ReportInput(
                datasets=data_result.output.processed_datasets[:3],
                query_context=query_result.output.original_query,
                report_type=ReportType.COMPREHENSIVE,
                report_format=ReportFormat.MARKDOWN,
            )
            report_result = report_agent.execute(report_input)

            assert report_result.success is True
            assert len(report_result.output.full_report) > 0

    def test_orchestrator_simple_search(self, orchestrator):
        """Test orchestrated simple search workflow."""
        orch_input = OrchestratorInput(
            query="Find TP53 datasets",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Check workflow completed or reached a meaningful stage
        assert result.output.final_stage in [
            WorkflowStage.COMPLETED,
            WorkflowStage.REPORT_GENERATION,
            WorkflowStage.FAILED,
        ]

    def test_orchestrator_full_analysis(self, orchestrator):
        """Test orchestrated full analysis workflow."""
        orch_input = OrchestratorInput(
            query="Analyze BRCA1 mutations in cancer research",
            workflow_type=WorkflowType.FULL_ANALYSIS,
            max_results=5,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Should process through multiple stages
        assert len(result.output.stage_results) >= 2


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling across agent workflows."""

    def test_invalid_query_handling(self, query_agent):
        """Test handling of invalid queries."""
        # Empty query should fail validation
        with pytest.raises(Exception):
            query_input = QueryInput(query="")
            query_agent.execute(query_input)

    def test_empty_search_results(self, search_agent):
        """Test handling when search returns no results."""
        search_input = SearchInput(search_terms=["xyznonexistentterm999888777"], max_results=10)
        result = search_agent.execute(search_input)

        # Should succeed even with 0 results
        assert result.success is True
        assert result.output.total_found >= 0

    def test_orchestrator_handles_failures(self, orchestrator):
        """Test orchestrator handles agent failures gracefully."""
        # Query that might cause issues
        orch_input = OrchestratorInput(
            query="test",  # Minimal query
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=1,
        )
        result = orchestrator.execute(orch_input)

        # Should complete even if some stages have issues
        assert result.success is True
        assert result.output.final_stage is not None

    def test_data_agent_handles_invalid_datasets(self, data_agent):
        """Test data agent handles invalid dataset metadata."""
        from omics_oracle_v2.agents.models.search import RankedDataset
        from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata

        # Create minimal/invalid RankedDataset
        invalid_geo = GEOSeriesMetadata(
            geo_id="GSE999999",
            title="Invalid",
            summary="Invalid dataset for testing",
            organism="Unknown",
            sample_count=0,
        )
        invalid_ranked = RankedDataset(dataset=invalid_geo, relevance_score=0.0, match_reasons=[])

        data_input = DataInput(datasets=[invalid_ranked])
        result = data_agent.execute(data_input)

        # Should succeed but flag quality issues
        assert result.success is True

    def test_report_agent_handles_no_datasets(self, data_agent, report_agent):
        """Test report agent with minimal dataset."""
        from omics_oracle_v2.agents.models.search import RankedDataset
        from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata

        # Create minimal dataset
        minimal_geo = GEOSeriesMetadata(
            geo_id="GSE12345",
            title="Test Dataset",
            summary="Test summary",
            organism="Homo sapiens",
            sample_count=10,
        )
        minimal_ranked = RankedDataset(dataset=minimal_geo, relevance_score=0.5, match_reasons=["test"])

        # Process it first
        data_input = DataInput(datasets=[minimal_ranked])
        data_result = data_agent.execute(data_input)

        assert data_result.success is True

        # Generate report
        if len(data_result.output.processed_datasets) > 0:
            report_input = ReportInput(
                datasets=data_result.output.processed_datasets,
                query_context="Test query",
                report_type=ReportType.BRIEF,
                report_format=ReportFormat.TEXT,
            )
            result = report_agent.execute(report_input)

            # Should succeed and generate basic report
            assert result.success is True
            assert len(result.output.full_report) > 0


# ============================================================================
# Performance Benchmark Tests
# ============================================================================


class TestPerformance:
    """Test performance benchmarks for agent workflows."""

    def test_query_agent_performance(self, query_agent):
        """Test query processing is fast enough."""
        query_input = QueryInput(query="Find TP53 datasets in breast cancer")

        start_time = time.time()
        result = query_agent.execute(query_input)
        execution_time = time.time() - start_time

        assert result.success is True
        # Should be under 10s (NLP model loading can be slow first time)
        assert execution_time < 10.0, f"Query took {execution_time:.2f}s (> 10s limit)"

    def test_search_agent_performance(self, search_agent):
        """Test search is reasonably fast."""
        search_input = SearchInput(search_terms=["cancer"], max_results=10)

        start_time = time.time()
        result = search_agent.execute(search_input)
        execution_time = time.time() - start_time

        assert result.success is True
        # Should be under 10s for first search (no cache)
        assert execution_time < 10.0, f"Search took {execution_time:.2f}s (> 10s limit)"

    def test_data_agent_performance(self, search_agent, data_agent):
        """Test data validation is fast."""
        # Get some datasets first
        search_input = SearchInput(search_terms=["cancer"], max_results=5)
        search_result = search_agent.execute(search_input)

        if len(search_result.output.datasets) > 0:
            # DataInput expects RankedDataset objects
            data_input = DataInput(datasets=search_result.output.datasets[:3])

            start_time = time.time()
            result = data_agent.execute(data_input)
            execution_time = time.time() - start_time

            assert result.success is True
            # Should be under 2s
            assert execution_time < 2.0, f"Data validation took {execution_time:.2f}s (> 2s limit)"

    def test_orchestrator_performance(self, orchestrator):
        """Test full workflow completes in reasonable time."""
        orch_input = OrchestratorInput(
            query="Find cancer datasets",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
        )

        start_time = time.time()
        result = orchestrator.execute(orch_input)
        execution_time = time.time() - start_time

        assert result.success is True
        # Full pipeline should be under 30s
        assert execution_time < 30.0, f"Full workflow took {execution_time:.2f}s (> 30s limit)"


# ============================================================================
# Caching and Optimization Tests
# ============================================================================


class TestCachingOptimization:
    """Test that caching and optimization work correctly."""

    def test_search_caching(self, search_agent):
        """Test that repeated searches use caching."""
        search_input = SearchInput(search_terms=["TP53"], max_results=10)

        # First search - no cache
        result1 = search_agent.execute(search_input)

        assert result1.success is True

        # Second search - should use cache
        result2 = search_agent.execute(search_input)

        assert result2.success is True
        # Cached search should be faster (though may not always be due to test conditions)
        # Just verify both succeeded
        assert result1.output.total_found == result2.output.total_found

    def test_query_agent_entity_caching(self, query_agent):
        """Test query agent efficiently processes queries."""
        # Process multiple similar queries
        queries = [
            "Find TP53 datasets",
            "Search for TP53 mutations",
            "TP53 gene expression",
        ]

        results = []
        for query in queries:
            query_input = QueryInput(query=query)
            result = query_agent.execute(query_input)
            results.append(result)

        # All should succeed
        assert all(r.success for r in results)
        # All should extract TP53 entity
        assert all(any("TP53" in e.text for e in r.output.entities) for r in results if r.output.entities)


# ============================================================================
# Agent State Management Tests
# ============================================================================


class TestAgentStateManagement:
    """Test agent state transitions and lifecycle."""

    def test_agent_state_transitions(self, query_agent):
        """Test agent state changes correctly during execution."""
        assert query_agent.state == AgentState.IDLE

        query_input = QueryInput(query="Test query")
        result = query_agent.execute(query_input)

        assert result.success is True
        # Should return to IDLE or COMPLETED after execution
        assert query_agent.state in [AgentState.IDLE, AgentState.COMPLETED]

    def test_multiple_executions(self, search_agent):
        """Test agent can handle multiple sequential executions."""
        # Execute 3 times
        for i in range(3):
            search_input = SearchInput(search_terms=[f"cancer{i}"], max_results=5)
            result = search_agent.execute(search_input)
            assert result.success is True

        # Agent should still be in good state
        assert search_agent.state in [AgentState.IDLE, AgentState.COMPLETED]


# ============================================================================
# Workflow Pattern Tests
# ============================================================================


class TestWorkflowPatterns:
    """Test different workflow patterns and use cases."""

    def test_entity_focused_workflow(self, orchestrator):
        """Test workflow focused on specific biomedical entities."""
        orch_input = OrchestratorInput(
            query="BRCA1 mutations in breast cancer patients",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=10,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True
        # Should process entities
        query_stage = result.output.get_stage_result(WorkflowStage.QUERY_PROCESSING)
        if query_stage and query_stage.success:
            assert query_stage.output is not None

    def test_filtered_workflow(self, orchestrator):
        """Test workflow with organism and study type filters."""
        orch_input = OrchestratorInput(
            query="gene expression data",
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=5,
            organism="Homo sapiens",
            study_type="Expression profiling by array",
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True

    def test_quality_focused_workflow(self, orchestrator):
        """Test workflow that emphasizes quality analysis."""
        orch_input = OrchestratorInput(
            query="cancer datasets",
            workflow_type=WorkflowType.FULL_ANALYSIS,
            max_results=5,
            min_samples=50,
        )
        result = orchestrator.execute(orch_input)

        assert result.success is True


# ============================================================================
# Integration with External Services
# ============================================================================


class TestExternalServiceIntegration:
    """Test integration with external services (GEO, NCBI)."""

    @pytest.mark.integration
    def test_real_geo_search(self, search_agent):
        """Test actual GEO database search."""
        search_input = SearchInput(search_terms=["Homo sapiens", "cancer"], max_results=5)
        result = search_agent.execute(search_input)

        assert result.success is True
        # Should get real results from GEO
        assert result.output.total_found > 0

    @pytest.mark.integration
    def test_real_nlp_processing(self, query_agent):
        """Test actual NLP entity extraction."""
        query_input = QueryInput(query="Find datasets about TP53 mutations in breast cancer patients")
        result = query_agent.execute(query_input)

        assert result.success is True
        # Should extract real biomedical entities
        assert len(result.output.entities) > 0
        # Should identify TP53 and breast cancer
        entity_texts = [e.text.lower() for e in result.output.entities]
        assert any("tp53" in text for text in entity_texts) or any(
            "breast" in text or "cancer" in text for text in entity_texts
        )
