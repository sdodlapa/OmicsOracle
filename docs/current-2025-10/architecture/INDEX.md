# OmicsOracle Documentation Index

## Quick Links

### Essential Documentation
- **[README.md](../README.md)** - Project overview and quick start
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture
- **[PHASE_0_CLEANUP_SUMMARY.md](PHASE_0_CLEANUP_SUMMARY.md)** - Phase 0 cleanup details and migration guide

### Phase 0 Documentation (October 2025)
- **[PHASE_0_CLEANUP_SUMMARY.md](PHASE_0_CLEANUP_SUMMARY.md)** - Complete Phase 0 cleanup summary
- **[PACKAGE_STRUCTURE.md](PACKAGE_STRUCTURE.md)** - Package organization and type checking
- **[ROUTE_CONSOLIDATION.md](ROUTE_CONSOLIDATION.md)** - API route consolidation and versioning
- **[TEST_ORGANIZATION.md](TEST_ORGANIZATION.md)** - Test structure and fixtures guide

### Developer Guides
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Development setup and guidelines
- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - Application startup guide
- **[CODE_QUALITY_GUIDE.md](CODE_QUALITY_GUIDE.md)** - Code quality standards

### Architecture & Design
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - System architecture overview
- **[ARCHITECTURE_IMPROVEMENT_PLAN.md](ARCHITECTURE_IMPROVEMENT_PLAN.md)** - Architecture improvement roadmap
- **[ARCHITECTURAL_ANALYSIS.md](ARCHITECTURAL_ANALYSIS.md)** - Architecture analysis
- **[CRITICAL_ARCHITECTURE_EVALUATION.md](CRITICAL_ARCHITECTURE_EVALUATION.md)** - Architecture evaluation

### Search System
- **[SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md](SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md)** - Search system technical details
- **[SEARCH_SYSTEM_CASE_STUDY.md](SEARCH_SYSTEM_CASE_STUDY.md)** - Real-world search examples
- **[ADVANCED_SEARCH_FEATURES.md](ADVANCED_SEARCH_FEATURES.md)** - Advanced search capabilities

### Testing
- **[TEST_ORGANIZATION.md](TEST_ORGANIZATION.md)** - Test structure, fixtures, and markers
- **[TESTING_HIERARCHY.md](TESTING_HIERARCHY.md)** - Testing hierarchy and strategy
- **[TEST_TEMPLATES.md](TEST_TEMPLATES.md)** - Test templates and examples

### Event Flow & Validation
- **[EVENT_FLOW_README.md](EVENT_FLOW_README.md)** - Event flow visualization
- **[EVENT_FLOW_VALIDATION_MAP.md](EVENT_FLOW_VALIDATION_MAP.md)** - Event to test mapping
- **[EVENT_FLOW_CHART.md](EVENT_FLOW_CHART.md)** - Event flow diagrams
- **[COMPREHENSIVE_EVENT_FLOW_IMPLEMENTATION.md](COMPREHENSIVE_EVENT_FLOW_IMPLEMENTATION.md)** - Complete event flow

### Deployment & Operations
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[WEB_INTERFACE_DEMO_GUIDE.md](WEB_INTERFACE_DEMO_GUIDE.md)** - Web interface guide

### API Documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - API reference documentation
- **Interactive API Docs**: http://localhost:8000/docs (when server is running)

---

## Directory Structure

### Phase 0 Documentation (`docs/`)
- **PHASE_0_CLEANUP_SUMMARY.md** - ✨ NEW: Complete Phase 0 cleanup summary
- **PACKAGE_STRUCTURE.md** - ✨ NEW: Package organization details
- **ROUTE_CONSOLIDATION.md** - ✨ NEW: Route consolidation guide
- **TEST_ORGANIZATION.md** - ✨ NEW: Test organization guide

### Planning Documents (`docs/planning/`)
- Phase development plans and completion summaries
- Implementation progress tracking
- Interface development and cleanup plans
- Environment consolidation plans
- Project status reports

### Reports (`docs/reports/`)
- Data integrity findings and reports
- GSE-specific investigation summaries
- Testing and monitoring summaries
- Search system enhancement reports

### Analysis (`docs/analysis/`)
- Advanced cleanup analysis
- System analysis documents

### Architecture (`docs/architecture/`)
- Architecture decision records
- Design documentation

### Testing (`docs/testing/`)
- Test documentation and guides

## Scripts Directory Structure

### Phase 0 Cleanup Scripts (`scripts/`) ✨ NEW
- **fix_imports_phase0.py** - Automated sys.path removal (Task 2)
- **consolidate_routes_phase0.py** - Route consolidation verification (Task 3)
- **organize_tests_phase0.py** - Test structure analysis (Task 5)
- **fix_test_imports.py** - Test import fixing (Task 5)

### Debug Scripts (`scripts/debug/`)
- debug_*.py - Pipeline and route debugging
- diagnose_*.py - System diagnostics
- check_*.py - Environment and configuration checks
- fix_*.py - Repair and fix utilities
- trace_*.py - Query flow tracing
- entrez_patch.py - NCBI Entrez patching utility

### Analysis Scripts (`scripts/analysis/`)
- analyze_traces.py - Trace analysis
- search_*_analyzer.py - Search performance analysis
- architecture_quality_analyzer.py - Code quality analysis
- generate_event_flow_visualization.py - Event flow visualization
- diagnostics.py - System diagnostics
- direct_gse_check.py - Direct GSE validation
- integrate_search_enhancer.py - Search enhancement integration
- omics_toolbox.py - General utilities

### Validation Scripts (`scripts/validation/`)
- validate_*.py - Various system validation scripts

### Monitoring Scripts (`scripts/monitoring/`)
- *monitor*.py - System monitoring utilities

### Utility Scripts (`scripts/`)
- cleanup_codebase.sh - Codebase cleanup script
- start_futuristic_enhanced.sh - Enhanced startup script

## Tests Directory Structure (Phase 0 Enhanced) ✨

### Test Configuration
- **conftest.py** - ✨ ENHANCED: Comprehensive shared fixtures and markers
  - test_config, mock_env_vars
  - mock_nlp_service, mock_cache, mock_geo_client
  - Pytest markers: unit, integration, e2e, slow, requires_api_key, requires_network

### Unit Tests (`tests/unit/`)
- 20+ unit test files - Fast, isolated tests with no external dependencies
- Run with: `pytest -m unit`

### Integration Tests (`tests/integration/`)
- 42+ integration test files - Component interaction tests
- comprehensive_test_runner.py - Main test runner
- run_*.py - Test execution scripts
- Run with: `pytest -m integration`

### End-to-End Tests (`tests/e2e/`)
- 2 e2e test files - Full system tests
- Run with: `pytest -m e2e`

### Performance Tests (`tests/performance/`)
- 3 performance test files
- Run with: `pytest -m slow`

### Security Tests (`tests/security/`)
- 6 security test files

### Other Test Categories
- tests/geo_tools/ - GEO client tests
- tests/pipeline/ - Pipeline tests
- tests/interface/ - Interface tests
- tests/validation/ - Validation tests
- tests/browser/ - Browser tests
- tests/mobile/ - Mobile tests
- tests/system/ - System tests

## Configuration Files (Root)
- .env.* - Environment configuration files
- Dockerfile* - Container configuration
- docker-compose.yml - Multi-container setup
- pyproject.toml - Python project configuration
- requirements*.txt - Dependency specifications
- Makefile - Build and development tasks
- mkdocs.yml - Documentation generation

## Main Application
- start.sh - Primary application startup script
- src/ - Main source code
- interfaces/ - User interface modules
- data/ - Data storage and cache
- logs/ - Application logs
