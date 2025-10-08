# 🧪 Testing and Quality Assurance Strategy

**Date**: June 25, 2025
**Status**: Implementation Ready
**Purpose**: Comprehensive testing strategy for consolidated interfaces and advanced module integration

---

## 🎯 **Testing Strategy Overview**

This document outlines a comprehensive testing and quality assurance strategy that ensures reliability, performance, and maintainability of the consolidated OmicsOracle system and its advanced modules.

---

## 📋 **Testing Pyramid Structure**

### **Unit Tests (Foundation - 70%)**

**Coverage Targets**:
- Code coverage: > 90%
- Branch coverage: > 85%
- Function coverage: > 95%

**Focus Areas**:
- Individual agent components
- Database models and queries
- API endpoint logic
- Utility functions and helpers

**Unit Test Framework**:
```python
# tests/unit/test_agents/test_text_extraction.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.omics_oracle.agents.text_extraction import TextExtractionAgent
from src.omics_oracle.models.extraction import ExtractionJob

class TestTextExtractionAgent:
    """Comprehensive unit tests for TextExtractionAgent"""

    @pytest.fixture
    def extraction_agent(self):
        return TextExtractionAgent("test-agent")

    @pytest.fixture
    def sample_pdf_content(self):
        return b"%PDF-1.4 sample content..."

    @pytest.mark.asyncio
    async def test_pdf_text_extraction(self, extraction_agent, sample_pdf_content):
        """Test PDF text extraction functionality"""
        with patch('src.omics_oracle.services.pdf_processor.extract_text') as mock_extract:
            mock_extract.return_value = "Extracted text content"

            result = await extraction_agent.extract_text_from_pdf(sample_pdf_content)

            assert result.success is True
            assert result.extracted_text == "Extracted text content"
            assert result.confidence_score > 0.8
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_extraction_error_handling(self, extraction_agent):
        """Test error handling in extraction process"""
        with patch('src.omics_oracle.services.pdf_processor.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("PDF parsing error")

            result = await extraction_agent.extract_text_from_pdf(b"invalid pdf")

            assert result.success is False
            assert "PDF parsing error" in result.error_message
            assert result.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_agent_message_processing(self, extraction_agent):
        """Test agent message processing workflow"""
        from src.omics_oracle.agents.base import AgentMessage

        message = AgentMessage(
            message_type="extract_text",
            payload={"document_id": "test-123", "content": b"sample content"},
            sender_id="test-sender"
        )

        with patch.object(extraction_agent, 'extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = Mock(success=True, extracted_text="Sample text")

            response = await extraction_agent.process_message(message)

            assert response.message_type == "extraction_complete"
            assert response.payload["success"] is True
            assert "Sample text" in response.payload["extracted_text"]
```

### **Integration Tests (Middle - 20%)**

**Scope**:
- Agent-to-agent communication
- Database integration workflows
- External service integrations
- API endpoint integration

**Integration Test Framework**:
```python
# tests/integration/test_agent_communication.py
import pytest
import asyncio
from src.omics_oracle.agents.text_extraction import TextExtractionAgent
from src.omics_oracle.agents.publication_discovery import PublicationDiscoveryAgent
from src.omics_oracle.agents.communication.message_broker import MessageBroker

class TestAgentCommunication:
    """Integration tests for agent communication workflows"""

    @pytest.fixture
    async def message_broker(self):
        broker = MessageBroker()
        await broker.start()
        yield broker
        await broker.stop()

    @pytest.fixture
    async def agents(self, message_broker):
        extraction_agent = TextExtractionAgent("extractor-1")
        discovery_agent = PublicationDiscoveryAgent("discovery-1")

        await message_broker.register_agent(extraction_agent)
        await message_broker.register_agent(discovery_agent)

        return extraction_agent, discovery_agent

    @pytest.mark.asyncio
    async def test_extraction_to_discovery_workflow(self, agents, message_broker):
        """Test complete workflow from extraction to discovery"""
        extraction_agent, discovery_agent = agents

        # Start both agents
        extraction_task = asyncio.create_task(extraction_agent.start())
        discovery_task = asyncio.create_task(discovery_agent.start())

        try:
            # Send document for extraction
            extraction_message = AgentMessage(
                message_type="extract_and_discover",
                payload={"document_content": "sample research paper content"},
                sender_id="test-orchestrator",
                target_id="extractor-1"
            )

            # Send message and wait for complete workflow
            await message_broker.send_message(extraction_message)

            # Wait for discovery results
            result = await message_broker.wait_for_message(
                message_type="discovery_complete",
                timeout=30.0
            )

            assert result is not None
            assert result.payload["extracted_text"] is not None
            assert len(result.payload["related_publications"]) > 0

        finally:
            extraction_task.cancel()
            discovery_task.cancel()
```

### **End-to-End Tests (Top - 10%)**

**Coverage Areas**:
- Complete user workflows
- Interface integration
- Performance under load
- Real-world scenarios

**E2E Test Framework**:
```python
# tests/e2e/test_complete_workflows.py
import pytest
import asyncio
from playwright.async_api import async_playwright
from fastapi.testclient import TestClient
from src.omics_oracle.main import app

class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows"""

    @pytest.fixture
    async def browser_context(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            yield context
            await browser.close()

    @pytest.fixture
    def api_client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_document_upload_and_analysis_workflow(self, browser_context, api_client):
        """Test complete document upload and analysis workflow"""
        page = await browser_context.new_page()

        # Navigate to application
        await page.goto("http://localhost:8000")

        # Upload document
        await page.set_input_files('input[type="file"]', 'tests/fixtures/sample_paper.pdf')
        await page.click('button[data-testid="upload-button"]')

        # Wait for extraction to complete
        await page.wait_for_selector('[data-testid="extraction-complete"]', timeout=30000)

        # Verify extracted text is displayed
        extracted_text = await page.text_content('[data-testid="extracted-text"]')
        assert len(extracted_text) > 100

        # Trigger discovery process
        await page.click('button[data-testid="find-related"]')

        # Wait for related publications
        await page.wait_for_selector('[data-testid="related-publications"]', timeout=20000)
        related_pubs = await page.query_selector_all('[data-testid="publication-item"]')
        assert len(related_pubs) > 0

        # Trigger statistical analysis
        await page.click('button[data-testid="analyze-statistics"]')

        # Wait for statistical results
        await page.wait_for_selector('[data-testid="statistical-results"]', timeout=15000)
        stats_elements = await page.query_selector_all('[data-testid="statistic-item"]')
        assert len(stats_elements) > 0

        # Verify visualization renders
        await page.click('button[data-testid="show-visualization"]')
        await page.wait_for_selector('[data-testid="visualization-container"]', timeout=10000)

        # Take screenshot for visual regression testing
        await page.screenshot(path='tests/e2e/screenshots/complete_workflow.png')
```

---

## 🚀 **Advanced Testing Strategies**

### **Property-Based Testing**

**Hypothesis-Based Testing**:
```python
# tests/property/test_search_algorithms.py
from hypothesis import given, strategies as st
import pytest
from src.omics_oracle.services.search import SearchService

class TestSearchProperties:
    """Property-based tests for search functionality"""

    @given(
        query=st.text(min_size=1, max_size=100),
        limit=st.integers(min_value=1, max_value=100)
    )
    @pytest.mark.asyncio
    async def test_search_results_count_property(self, query, limit):
        """Property: Search results should never exceed the requested limit"""
        search_service = SearchService()
        results = await search_service.search(query, limit=limit)
        assert len(results) <= limit

    @given(
        query=st.text(min_size=1, max_size=50),
        filters=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=20),
            max_size=5
        )
    )
    @pytest.mark.asyncio
    async def test_search_filter_consistency(self, query, filters):
        """Property: Filtered results should be subset of unfiltered results"""
        search_service = SearchService()

        unfiltered_results = await search_service.search(query)
        filtered_results = await search_service.search(query, filters=filters)

        # Filtered results should be subset of unfiltered
        filtered_ids = {r['id'] for r in filtered_results}
        unfiltered_ids = {r['id'] for r in unfiltered_results}

        assert filtered_ids.issubset(unfiltered_ids)
```

### **Contract Testing**

**API Contract Testing**:
```python
# tests/contract/test_api_contracts.py
import pytest
from pact import Consumer, Provider
from src.omics_oracle.api.v1.endpoints.search import router

class TestAPIContracts:
    """Contract tests for API endpoints"""

    @pytest.fixture
    def pact_consumer(self):
        return Consumer('omics-oracle-frontend').has_pact_with(
            Provider('omics-oracle-api')
        )

    def test_search_endpoint_contract(self, pact_consumer):
        """Test search endpoint contract"""
        (pact_consumer
         .given('search index contains documents')
         .upon_receiving('a search request')
         .with_request('POST', '/api/v1/search')
         .will_respond_with(200, body={
             'results': [
                 {
                     'id': '123',
                     'title': 'Sample Paper',
                     'authors': ['Author 1'],
                     'abstract': 'Sample abstract',
                     'score': 0.95
                 }
             ],
             'total_count': 1,
             'page': 1,
             'limit': 10
         }))

        with pact_consumer:
            # Make actual API call and verify contract
            response = self.make_search_request()
            assert response.status_code == 200
            assert 'results' in response.json()
```

### **Mutation Testing**

**Code Quality Validation**:
```python
# tests/mutation/test_mutation_coverage.py
import subprocess
import pytest

class TestMutationCoverage:
    """Mutation testing to validate test quality"""

    def test_mutation_score_threshold(self):
        """Ensure mutation testing score meets threshold"""
        result = subprocess.run([
            'mutmut', 'run',
            '--paths-to-mutate', 'src/omics_oracle',
            '--tests-dir', 'tests/unit'
        ], capture_output=True, text=True)

        # Parse mutation score
        output_lines = result.stdout.split('\n')
        score_line = [line for line in output_lines if 'mutation score' in line.lower()]

        if score_line:
            # Extract score percentage
            score = float(score_line[0].split(':')[-1].strip().rstrip('%'))
            assert score >= 80.0, f"Mutation score {score}% below threshold of 80%"
```

---

## 🔍 **Specialized Testing Areas**

### **Agent System Testing**

**Agent Behavior Verification**:
```python
# tests/agents/test_agent_behaviors.py
import pytest
import asyncio
from unittest.mock import Mock
from src.omics_oracle.agents.base import BaseAgent, AgentMessage

class MockAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.processed_messages = []

    async def process_message(self, message: AgentMessage):
        self.processed_messages.append(message)
        return AgentMessage(
            message_type="mock_response",
            payload={"processed": True},
            sender_id=self.agent_id
        )

class TestAgentBehaviors:
    """Test agent system behaviors and patterns"""

    @pytest.mark.asyncio
    async def test_agent_message_ordering(self):
        """Test that agents process messages in correct order"""
        agent = MockAgent("test-agent")

        # Send multiple messages
        messages = [
            AgentMessage("msg1", {"order": 1}, "sender"),
            AgentMessage("msg2", {"order": 2}, "sender"),
            AgentMessage("msg3", {"order": 3}, "sender")
        ]

        # Process messages
        tasks = []
        for msg in messages:
            await agent.message_queue.put(msg)

        # Start agent processing
        agent_task = asyncio.create_task(agent.start())

        # Wait for processing
        await asyncio.sleep(0.1)
        agent_task.cancel()

        # Verify order
        assert len(agent.processed_messages) == 3
        for i, msg in enumerate(agent.processed_messages):
            assert msg.payload["order"] == i + 1

    @pytest.mark.asyncio
    async def test_agent_error_recovery(self):
        """Test agent error handling and recovery"""
        agent = MockAgent("test-agent")

        # Mock processing to raise error
        original_process = agent.process_message
        async def error_process(message):
            if message.message_type == "error_msg":
                raise Exception("Test error")
            return await original_process(message)

        agent.process_message = error_process

        # Send error message followed by normal message
        await agent.message_queue.put(AgentMessage("error_msg", {}, "sender"))
        await agent.message_queue.put(AgentMessage("normal_msg", {}, "sender"))

        # Verify agent continues processing after error
        agent_task = asyncio.create_task(agent.start())
        await asyncio.sleep(0.1)
        agent_task.cancel()

        # Should have processed the normal message despite error
        normal_messages = [m for m in agent.processed_messages if m.message_type == "normal_msg"]
        assert len(normal_messages) == 1
```

### **Performance Testing Framework**

**Load and Stress Testing**:
```python
# tests/performance/test_load_scenarios.py
import pytest
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import statistics

class TestPerformanceScenarios:
    """Performance testing for various load scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_search_requests(self):
        """Test system under concurrent search load"""
        base_url = "http://localhost:8000"
        concurrent_users = 50
        requests_per_user = 10

        response_times = []

        async def user_simulation(session, user_id):
            user_times = []
            for i in range(requests_per_user):
                start_time = asyncio.get_event_loop().time()

                async with session.post(
                    f"{base_url}/api/v1/search",
                    json={"query": f"test query {user_id}-{i}"}
                ) as response:
                    await response.json()

                end_time = asyncio.get_event_loop().time()
                user_times.append(end_time - start_time)

                # Realistic user delay
                await asyncio.sleep(0.1)

            return user_times

        async with aiohttp.ClientSession() as session:
            tasks = [
                user_simulation(session, user_id)
                for user_id in range(concurrent_users)
            ]

            user_results = await asyncio.gather(*tasks)

        # Flatten response times
        for user_times in user_results:
            response_times.extend(user_times)

        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        assert avg_response_time < 0.5, f"Average response time {avg_response_time:.2f}s too high"
        assert p95_response_time < 1.0, f"95th percentile {p95_response_time:.2f}s too high"

    @pytest.mark.asyncio
    async def test_agent_processing_throughput(self):
        """Test agent message processing throughput"""
        from src.omics_oracle.agents.text_extraction import TextExtractionAgent

        agent = TextExtractionAgent("perf-test-agent")
        message_count = 100

        # Create test messages
        messages = [
            AgentMessage(
                "extract_text",
                {"content": f"test content {i}"},
                "perf-tester"
            )
            for i in range(message_count)
        ]

        start_time = asyncio.get_event_loop().time()

        # Process messages
        tasks = [agent.process_message(msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        end_time = asyncio.get_event_loop().time()

        # Calculate throughput
        processing_time = end_time - start_time
        throughput = message_count / processing_time

        assert throughput > 10, f"Throughput {throughput:.2f} messages/sec too low"
        assert all(r is not None for r in results), "Some messages failed to process"
```

### **Security Testing**

**Security Vulnerability Testing**:
```python
# tests/security/test_security_vulnerabilities.py
import pytest
import requests
from sqlalchemy import text

class TestSecurityVulnerabilities:
    """Security testing for common vulnerabilities"""

    def test_sql_injection_protection(self, api_client):
        """Test protection against SQL injection attacks"""
        # SQL injection attempts
        malicious_queries = [
            "'; DROP TABLE documents; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]

        for query in malicious_queries:
            response = api_client.post(
                "/api/v1/search",
                json={"query": query}
            )

            # Should not return 500 error or expose database structure
            assert response.status_code in [200, 400]
            assert "DROP TABLE" not in response.text
            assert "UNION SELECT" not in response.text

    def test_xss_protection(self, api_client):
        """Test protection against XSS attacks"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]

        for payload in xss_payloads:
            response = api_client.post(
                "/api/v1/search",
                json={"query": payload}
            )

            # Response should escape or sanitize dangerous content
            assert "<script>" not in response.text
            assert "javascript:" not in response.text

    def test_file_upload_security(self, api_client):
        """Test file upload security measures"""
        # Test malicious file uploads
        malicious_files = [
            ("shell.php", b"<?php system($_GET['cmd']); ?>"),
            ("script.js", b"alert('xss')"),
            ("large.txt", b"A" * (10 * 1024 * 1024))  # 10MB file
        ]

        for filename, content in malicious_files:
            response = api_client.post(
                "/api/v1/upload",
                files={"file": (filename, content)}
            )

            # Should reject dangerous files or oversized uploads
            if filename.endswith(('.php', '.js')):
                assert response.status_code == 400
            elif len(content) > 5 * 1024 * 1024:  # > 5MB
                assert response.status_code == 413
```

---

## 📊 **Quality Metrics and Reporting**

### **Automated Quality Gates**

**CI/CD Quality Checks**:
```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-checks:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install coverage pytest-cov bandit safety

    - name: Run unit tests with coverage
      run: |
        pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=90

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Security scan
      run: |
        bandit -r src/ -f json -o security-report.json
        safety check --json --output safety-report.json

    - name: Code quality analysis
      run: |
        pylint src/ --output-format=json > pylint-report.json
        mypy src/ --json-report mypy-report.json

    - name: Upload quality reports
      uses: actions/upload-artifact@v3
      with:
        name: quality-reports
        path: |
          coverage.xml
          security-report.json
          safety-report.json
          pylint-report.json
          mypy-report.json
```

### **Quality Dashboard**

**Metrics Collection and Visualization**:
```python
# src/omics_oracle/quality/dashboard.py
from dataclasses import dataclass
from typing import Dict, List
import json
from datetime import datetime

@dataclass
class QualityMetrics:
    test_coverage: float
    code_quality_score: float
    security_issues: int
    performance_score: float
    documentation_coverage: float
    timestamp: datetime

class QualityDashboard:
    """Quality metrics dashboard and reporting"""

    def __init__(self):
        self.metrics_history = []

    def collect_metrics(self) -> QualityMetrics:
        """Collect current quality metrics"""
        return QualityMetrics(
            test_coverage=self._get_test_coverage(),
            code_quality_score=self._get_code_quality_score(),
            security_issues=self._count_security_issues(),
            performance_score=self._get_performance_score(),
            documentation_coverage=self._get_doc_coverage(),
            timestamp=datetime.utcnow()
        )

    def generate_quality_report(self) -> Dict:
        """Generate comprehensive quality report"""
        current_metrics = self.collect_metrics()

        return {
            "summary": {
                "overall_score": self._calculate_overall_score(current_metrics),
                "test_coverage": current_metrics.test_coverage,
                "security_status": "PASS" if current_metrics.security_issues == 0 else "FAIL",
                "performance_grade": self._performance_grade(current_metrics.performance_score)
            },
            "details": {
                "unit_tests": self._get_unit_test_details(),
                "integration_tests": self._get_integration_test_details(),
                "security_scan": self._get_security_details(),
                "performance_benchmarks": self._get_performance_details()
            },
            "trends": self._generate_trend_analysis(),
            "recommendations": self._generate_recommendations(current_metrics)
        }

    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'test_coverage': 0.25,
            'code_quality': 0.25,
            'security': 0.30,
            'performance': 0.20
        }

        security_score = 100 if metrics.security_issues == 0 else max(0, 100 - metrics.security_issues * 10)

        return (
            metrics.test_coverage * weights['test_coverage'] +
            metrics.code_quality_score * weights['code_quality'] +
            security_score * weights['security'] +
            metrics.performance_score * weights['performance']
        )
```

---

## 🚀 **Testing Implementation Roadmap**

### **Phase 1: Foundation Testing (Week 1-2)**

- Set up testing infrastructure and CI/CD pipelines
- Implement comprehensive unit test suite
- Establish code coverage baselines
- Deploy automated quality gates

### **Phase 2: Integration and Performance Testing (Week 3-4)**

- Implement integration test framework
- Deploy performance testing suite
- Set up agent communication testing
- Establish performance benchmarks

### **Phase 3: Advanced Testing and Security (Week 5-6)**

- Implement property-based testing
- Deploy security testing framework
- Set up mutation testing
- Establish contract testing

### **Phase 4: Quality Monitoring and Optimization (Week 7-8)**

- Deploy quality dashboard
- Implement continuous monitoring
- Optimize test execution times
- Refine quality metrics and thresholds

---

## 📋 **Success Criteria**

**Quantitative Targets**:
- Unit test coverage: > 90%
- Integration test coverage: > 80%
- Security vulnerabilities: 0 critical, < 5 medium
- Performance regression: < 5% degradation

**Qualitative Goals**:
- Reliable CI/CD pipeline with minimal false positives
- Comprehensive test documentation
- Efficient test execution (< 15 minutes full suite)
- Clear quality metrics and reporting

---

*This testing strategy will evolve with the system and be continuously refined based on feedback and emerging requirements.*
