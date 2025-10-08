# OmicsOracle Event Flow and Validation Framework

This document maps the flow of events in the OmicsOracle system from server startup to frontend display, along with the corresponding test/validation files for each step. The framework provides comprehensive coverage to ensure the system functions correctly at each stage.

## Visual Flow Diagram

A visual diagram representing the event flow and validation points can be found in:
- GraphViz DOT file: `docs/event_flow_validation.dot`
- To view the diagram, you can use GraphViz or any online DOT file renderer

## Event Flow and Validation Map

### 1. Server Initialization Phase

| Event/Step | Description | Test/Validation Files | Monitoring Components |
|------------|-------------|------------------------|----------------------|
| **Server Startup** | FastAPI server initialization | `tests/interface/test_server.py` | `src/omics_oracle/monitoring/api_monitor.py` |
| **Config Loading** | Loading system configuration | `tests/unit/test_core.py` | `tools/diagnostics/system_diagnostics.py` |
| **NCBI Email Config** | Setting up NCBI email for Entrez | `test_ncbi_config.py`, `validate_ncbi_config.py` | - |
| **Pipeline Initialization** | Creating OmicsOracle pipeline instance | `tests/pipeline/test_initialization.py`, `debug_pipeline.py` | `src/omics_oracle/monitoring/pipeline_monitor.py` |
| **Component Initialization** | Initializing GEO client, summarizer, etc. | `tests/geo_tools/test_geo_client.py`, `tests/services/test_summarizer.py` | - |
| **API Routes Setup** | Setting up FastAPI endpoints | `tests/interface/test_api_endpoints.py` | - |

### 2. Search Process Phase

| Event/Step | Description | Test/Validation Files | Monitoring Components |
|------------|-------------|------------------------|----------------------|
| **Search Request (UI)** | User submits search query | `tests/interface/test_api_endpoints.py` | `src/omics_oracle/monitoring/api_monitor.py` |
| **Query Parsing** | Extracting entities from query | `tests/unit/test_nlp.py`, `tests/unit/test_biomedical_nlp.py` | - |
| **GEO Database Search** | Searching NCBI GEO for datasets | `tests/geo_tools/test_geo_client.py`, `test_ncbi_connection.py` | `src/omics_oracle/monitoring/pipeline_monitor.py` |
| **Result Processing** | Processing raw GEO results | `tests/unit/test_pipeline.py` | - |
| **AI Summarization** | Generating AI summaries for datasets | `tests/services/test_summarizer.py` | - |
| **Result Formatting** | Formatting final results for display | `tests/e2e/test_search_pipeline.py` | - |

### 3. Frontend Rendering Phase

| Event/Step | Description | Test/Validation Files | Monitoring Components |
|------------|-------------|------------------------|----------------------|
| **WebSocket Connection** | Setting up WebSocket for live updates | `tests/interface/test_websocket.py` | `src/omics_oracle/monitoring/websocket_monitor.py` |
| **Progress Updates** | Sending real-time progress updates | `test_progress_events.py`, `test_progress_client.py` | - |
| **Results Display** | Rendering results in the UI | `tests/interface/test_frontend.py` | `tools/diagnostics/frontend_diagnostics.py` |
| **Error Handling** | Handling errors in the UI | `tests/unit/test_error_handling.py` | - |

### 4. End-to-End Tests

| Test Type | Description | Test Files |
|-----------|-------------|------------|
| **Search Pipeline E2E** | Complete flow from query to results | `tests/e2e/test_search_pipeline.py` |
| **Interface Integration** | Backend-frontend integration | `tests/e2e/test_interface_integration.py` |
| **Performance Testing** | System performance under load | `tests/performance/test_load_testing.py`, `tests/performance/test_performance_monitoring.py` |
| **Validation Testing** | Validating system architecture | `tests/validation/test_architecture.py` |

### 5. Monitoring and Diagnostic Framework

| Component | Description | Implementation Files |
|-----------|-------------|---------------------|
| **Pipeline Monitor** | Tracks pipeline execution steps | `src/omics_oracle/monitoring/pipeline_monitor.py` |
| **API Monitor** | Monitors API requests and responses | `src/omics_oracle/monitoring/api_monitor.py` |
| **WebSocket Monitor** | Tracks WebSocket messages | `src/omics_oracle/monitoring/websocket_monitor.py` |
| **Central Monitor** | Unified monitoring dashboard | `omics_monitor.py`, `monitoring_dashboard.py` |
| **System Diagnostics** | Server and system diagnostics | `tools/diagnostics/system_diagnostics.py` |
| **API Diagnostics** | API endpoint diagnostics | `tools/diagnostics/api_diagnostics.py` |
| **Frontend Diagnostics** | UI and frontend diagnostics | `tools/diagnostics/frontend_diagnostics.py` |

## Test and Validation File Overview

### Core Test Runner

- `run_tests.py`: Comprehensive test runner that orchestrates all tests and generates reports
- `tests/run_comprehensive_tests_simple.py`: Simplified test runner for quick testing

### Unit Test Files

- `tests/unit/test_core.py`: Tests for core functionality
- `tests/unit/test_nlp.py`: Tests for NLP components
- `tests/unit/test_biomedical_nlp.py`: Tests for biomedical NER
- `tests/unit/test_pipeline.py`: Tests for pipeline components
- `tests/unit/test_geo_client.py`: Tests for GEO client
- `tests/unit/test_web_server.py`: Tests for web server
- `tests/unit/test_web_interface_unit.py`: Tests for web interface components
- `tests/unit/test_error_handling.py`: Tests for error handling
- `tests/unit/test_simple_api.py`: Tests for simple API endpoints
- `tests/unit/integrations/test_pubmed_integration.py`: Tests for PubMed integration
- `tests/unit/integrations/test_citation_managers.py`: Tests for citation managers

### End-to-End Test Files

- `tests/e2e/test_search_pipeline.py`: E2E tests for search pipeline
- `tests/e2e/test_interface_integration.py`: E2E tests for interface integration

### Performance Test Files

- `tests/performance/test_load_testing.py`: Tests for system under load
- `tests/performance/test_performance_monitoring.py`: Tests for performance monitoring
- `tests/performance/simple_load_test.py`: Simple load testing script

### Diagnostic Tools

- `debug_pipeline.py`: Diagnostic tool for pipeline issues
- `validate_ncbi_config.py`: Validation tool for NCBI configuration
- `test_ncbi_connection.py`: Test tool for NCBI connection
- `test_progress_events.py`: Test tool for progress events
- `test_progress_client.py`: Test tool for progress client
- `test_honest_results.py`: Test tool for validating result honesty (no cache/fake data)

### Monitoring Components

- `src/omics_oracle/monitoring/pipeline_monitor.py`: Pipeline monitoring component
- `src/omics_oracle/monitoring/api_monitor.py`: API monitoring component
- `src/omics_oracle/monitoring/websocket_monitor.py`: WebSocket monitoring component
- `omics_monitor.py`: Central monitoring orchestrator
- `monitoring_dashboard.py`: Web dashboard for monitoring

## Validation Strategy for Key Events

### 1. Server Startup Validation

- **Server Process**: Validate server starts with correct configuration
- **Pipeline Initialization**: Ensure pipeline is properly initialized
- **Error Handling**: Test recovery from initialization failures

### 2. Search Process Validation

- **Query Processing**: Validate extraction of entities and intent
- **GEO Search**: Test NCBI/GEO connectivity and search functionality
- **Result Processing**: Validate proper filtering and no caching/fake data
- **Summarization**: Test AI summary generation and inclusion in results

### 3. Frontend Validation

- **WebSocket**: Test WebSocket connections and message handling
- **Progress Updates**: Validate progress event flow and display
- **Results Rendering**: Test proper rendering of search results
- **Error Handling**: Validate user-friendly error messages

## Implementation Status

| Component | Status | Next Steps |
|-----------|--------|------------|
| Server Tests | Implemented | Expand coverage |
| Pipeline Tests | Implemented | Add more edge cases |
| GEO Client Tests | Implemented | Add more mock responses |
| Summarizer Tests | Implemented | Add more test scenarios |
| Frontend Tests | Partially Implemented | Complete UI testing |
| End-to-End Tests | Implemented | Expand test cases |
| Pipeline Monitor | Implemented | Integrate with dashboard |
| API Monitor | Implemented | Add metrics collection |
| WebSocket Monitor | Implemented | Improve error tracking |
| Central Monitor | Partially Implemented | Complete dashboard UI |
| Diagnostics | Partially Implemented | Complete all diagnostic tools |

## Best Practices for Test Execution

1. **Server Initialization Tests**: Run before deployment to ensure proper startup
2. **Component Tests**: Run after any component changes
3. **End-to-End Tests**: Run before release and after significant changes
4. **Performance Tests**: Run periodically to detect performance regressions
5. **Continuous Monitoring**: Run monitoring components during operation

## Extending the Framework

To add tests for new features:

1. Add unit tests for individual components
2. Update end-to-end tests to include the new feature
3. Add monitoring for the new components
4. Update the event flow diagram and this documentation

---

This comprehensive test, validation, and monitoring framework ensures the reliability, observability, and maintainability of the OmicsOracle system across its entire event flow.
