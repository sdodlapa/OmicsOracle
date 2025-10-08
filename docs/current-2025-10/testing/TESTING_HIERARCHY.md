# OmicsOracle Testing Hierarchy

This document outlines the hierarchical organization of all test, validation, and monitoring files for the OmicsOracle system. It provides a structured view of how different test types relate to one another and how they cover various aspects of the system.

## 1. Testing Hierarchy Overview

```
OmicsOracle Tests
├── Unit Tests (Component-Level Testing)
│   ├── Core Components
│   ├── Pipeline Components
│   ├── GEO Tools
│   ├── NLP Components
│   ├── Services
│   ├── Web Server
│   ├── Interface
│   └── Error Handling
│
├── Integration Tests (Component Interaction Testing)
│   ├── Pipeline-GEO Integration
│   ├── GEO-Summarizer Integration
│   ├── API-WebSocket Integration
│   ├── Frontend-API Integration
│   └── Monitoring System Integration
│
├── End-to-End Tests (Full System Testing)
│   ├── Search Pipeline E2E
│   └── Interface Integration E2E
│
├── Performance Tests (System Performance Testing)
│   ├── Load Testing
│   ├── Component Performance Testing
│   ├── Resource Usage Testing
│   └── Response Time Testing
│
└── Validation Tests (System Validation Testing)
    ├── Architecture Validation
    ├── Requirement Validation
    ├── Security Validation
    └── Accessibility Validation
```

## 2. Unit Tests

Unit tests focus on testing individual components in isolation.

### 2.1 Core Components

- `tests/unit/test_core.py` - Tests for core functionality
- `tests/unit/test_config.py` - Tests for configuration loading
- `tests/unit/test_logging.py` - Tests for logging functionality
- `tests/unit/test_exceptions.py` - Tests for exception handling
- `tests/utils/test_environment_variables.py` - Tests for environment variable handling

### 2.2 Pipeline Components

- `tests/pipeline/test_initialization.py` - Tests for pipeline initialization
- `tests/pipeline/test_query_processing.py` - Tests for query processing
- `tests/pipeline/test_result_processing.py` - Tests for result processing
- `tests/pipeline/test_progress_tracking.py` - Tests for progress tracking
- `tests/unit/test_pipeline.py` - General pipeline unit tests

### 2.3 GEO Tools

- `tests/geo_tools/test_geo_client.py` - Tests for GEO client
- `tests/geo_tools/test_geo_client_init.py` - Tests for GEO client initialization
- `tests/geo_tools/test_ncbi_client.py` - Tests for NCBI client
- `test_ncbi_connection.py` - Tests for NCBI connection
- `test_ncbi_config.py` - Tests for NCBI configuration
- `validate_ncbi_config.py` - Validation for NCBI configuration

### 2.4 NLP Components

- `tests/unit/test_nlp.py` - General NLP tests
- `tests/nlp/test_entity_extraction.py` - Tests for entity extraction
- `tests/nlp/test_query_expansion.py` - Tests for query expansion
- `tests/unit/test_biomedical_nlp.py` - Tests for biomedical NLP

### 2.5 Services

- `tests/services/test_summarizer.py` - Tests for summarizer
- `tests/services/test_summarizer_init.py` - Tests for summarizer initialization
- `tests/services/test_openai_integration.py` - Tests for OpenAI integration
- `tests/services/test_cache_handling.py` - Tests for cache handling

### 2.6 Web Server

- `tests/unit/test_web_server.py` - Tests for web server
- `tests/interface/test_server.py` - Tests for server initialization
- `tests/interface/test_api_endpoints.py` - Tests for API endpoints

### 2.7 Interface

- `tests/interface/test_frontend.py` - Tests for frontend
- `tests/interface/test_ui_rendering.py` - Tests for UI rendering
- `tests/interface/test_websocket.py` - Tests for WebSocket
- `tests/interface/test_websocket_handler.py` - Tests for WebSocket handler
- `tests/interface/test_ui_interaction.py` - Tests for UI interaction

### 2.8 Error Handling

- `tests/unit/test_error_handling.py` - Tests for error handling
- `tests/unit/test_error_cases.py` - Tests for error cases
- `tests/unit/test_fallbacks.py` - Tests for fallback mechanisms
- `tests/unit/test_cache_bypass.py` - Tests for cache bypass

## 3. Integration Tests

Integration tests focus on testing interactions between components.

### 3.1 Pipeline-GEO Integration

- `tests/integration/test_pipeline_geo.py` - Tests for pipeline-GEO integration
- `tests/integration/test_geo_pipeline.py` - Tests for GEO-pipeline integration

### 3.2 GEO-Summarizer Integration

- `tests/integration/test_geo_summarizer.py` - Tests for GEO-summarizer integration
- `tests/integration/test_summarizer_pipeline.py` - Tests for summarizer-pipeline integration

### 3.3 API-WebSocket Integration

- `tests/integration/test_api_websocket.py` - Tests for API-WebSocket integration
- `test_progress_events.py` - Tests for progress events
- `test_progress_client.py` - Tests for progress client

### 3.4 Frontend-API Integration

- `tests/integration/test_frontend_api.py` - Tests for frontend-API integration
- `tests/integration/test_websocket_frontend.py` - Tests for WebSocket-frontend integration

### 3.5 Monitoring System Integration

- `tests/integration/test_monitoring_system.py` - Tests for monitoring system integration
- `tests/integration/test_dashboard_integration.py` - Tests for dashboard integration

## 4. End-to-End Tests

End-to-end tests focus on testing the complete system flow.

### 4.1 Search Pipeline E2E

- `tests/e2e/test_search_pipeline.py` - Tests for search pipeline E2E
- `test_honest_results.py` - Tests for result honesty (no cache/fake data)

### 4.2 Interface Integration E2E

- `tests/e2e/test_interface_integration.py` - Tests for interface integration E2E
- `tests/e2e/test_user_scenarios.py` - Tests for user scenarios

## 5. Performance Tests

Performance tests focus on testing system performance.

### 5.1 Load Testing

- `tests/performance/test_load_testing.py` - Tests for system under load
- `tests/performance/simple_load_test.py` - Simple load testing

### 5.2 Component Performance Testing

- `tests/performance/test_performance.py` - General performance tests
- `tests/performance/test_pipeline_performance.py` - Tests for pipeline performance
- `tests/performance/test_geo_client_performance.py` - Tests for GEO client performance
- `tests/performance/test_summarizer_performance.py` - Tests for summarizer performance

### 5.3 Resource Usage Testing

- `tests/performance/test_memory_usage.py` - Tests for memory usage
- `tests/performance/test_cpu_usage.py` - Tests for CPU usage

### 5.4 Response Time Testing

- `tests/performance/test_response_time.py` - Tests for response time
- `tests/performance/test_performance_monitoring.py` - Tests for performance monitoring

## 6. Validation Tests

Validation tests focus on validating the system against requirements.

### 6.1 Architecture Validation

- `tests/validation/test_architecture.py` - Tests for architecture validation
- `tests/validation/test_system_design.py` - Tests for system design validation

### 6.2 Requirement Validation

- `tests/validation/test_requirements.py` - Tests for requirement validation
- `tests/validation/test_acceptance_criteria.py` - Tests for acceptance criteria validation

### 6.3 Security Validation

- `tests/validation/test_security.py` - Tests for security validation
- `tests/validation/test_data_privacy.py` - Tests for data privacy validation

### 6.4 Accessibility Validation

- `tests/validation/test_accessibility.py` - Tests for accessibility validation
- `tests/validation/test_usability.py` - Tests for usability validation

## 7. Diagnostic Tools

Diagnostic tools provide focused debugging capabilities for specific components.

### 7.1 Pipeline Diagnostics

- `debug_pipeline.py` - Debug pipeline issues
- `debug_pipeline_init.py` - Debug pipeline initialization issues
- `quick_test_pipeline.py` - Quick pipeline testing

### 7.2 GEO Client Diagnostics

- `tools/diagnostics/geo_client_diagnostics.py` - GEO client diagnostics
- `tools/diagnostics/ncbi_diagnostics.py` - NCBI diagnostics

### 7.3 Summarizer Diagnostics

- `tools/diagnostics/summarizer_diagnostics.py` - Summarizer diagnostics
- `tools/diagnostics/openai_diagnostics.py` - OpenAI diagnostics

### 7.4 Server Diagnostics

- `tools/diagnostics/system_diagnostics.py` - System diagnostics
- `tools/diagnostics/api_diagnostics.py` - API diagnostics

### 7.5 Frontend Diagnostics

- `tools/diagnostics/frontend_diagnostics.py` - Frontend diagnostics
- `tools/diagnostics/ui_diagnostics.py` - UI diagnostics

## 8. Monitoring Components

Monitoring components provide real-time system monitoring.

### 8.1 Core Monitoring

- `omics_monitor.py` - Central monitoring orchestrator
- `monitoring_dashboard.py` - Web dashboard for monitoring

### 8.2 Component Monitoring

- `src/omics_oracle/monitoring/pipeline_monitor.py` - Pipeline monitoring
- `src/omics_oracle/monitoring/geo_client_monitor.py` - GEO client monitoring
- `src/omics_oracle/monitoring/summarizer_monitor.py` - Summarizer monitoring
- `src/omics_oracle/monitoring/api_monitor.py` - API monitoring
- `src/omics_oracle/monitoring/websocket_monitor.py` - WebSocket monitoring
- `interfaces/futuristic/static/js/monitoring.js` - Frontend monitoring

## 9. Test Execution and Reporting

### 9.1 Test Runners

- `run_tests.py` - Main test runner
- `tests/run_comprehensive_tests_simple.py` - Simple comprehensive test runner

### 9.2 Test Reports

- `test_results.html` - HTML test reports
- `test_results.json` - JSON test reports
- `coverage_report.html` - Coverage reports

## 10. Test Implementation Strategy

1. **Start with Unit Tests**: Implement unit tests for all components
2. **Add Integration Tests**: Implement integration tests for component interactions
3. **Develop E2E Tests**: Implement end-to-end tests for complete workflows
4. **Add Performance Tests**: Implement performance tests to benchmark the system
5. **Validate the System**: Implement validation tests to ensure requirements are met

## 11. Best Practices

1. **Test Isolation**: Ensure tests are isolated and don't depend on each other
2. **Mock External Services**: Use mocks for external services (NCBI, OpenAI)
3. **Test Coverage**: Aim for high test coverage (>80%)
4. **Continuous Testing**: Run tests continuously during development
5. **Test Reporting**: Generate and analyze test reports regularly

---

This testing hierarchy provides a comprehensive framework for ensuring the reliability, performance, and correctness of the OmicsOracle system. By following this hierarchy, we can systematically test all aspects of the system from individual components to the complete end-to-end flow.
