# OmicsOracle 🧬🔮

**AI-Powered Genomics Data Summary Agent**

OmicsOracle is an intelligent data summary agent designed to process, analyze, and summarize genomics and omics data, with a focus on GEO (Gene Expression Omnibus) metadata summarization. The system provides AI-driven insights, automated data processing, and comprehensive summaries for researchers and bioinformaticians.

📖 **For detailed system architecture and query processing flow, see [ARCHITECTURE.md](ARCHITECTURE.md)**

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd OmicsOracle

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode (recommended)
pip install -e .

# Install additional dependencies
pip install -r requirements-web.txt  # Web interface
pip install -r requirements-dev.txt  # Development tools

# Set up environment variables
cp .env.example .env

# Start the application (full-stack)
./start.sh

# Or start specific components:
./start.sh --backend-only    # API server only
./start.sh --frontend-only   # Web interface only
./start.sh --dev            # Development mode with hot reload
```

> **Note:** Phase 0 cleanup modernized the package structure. Use `pip install -e .` for proper import resolution and type checking support.

### 🌐 Access Points

After starting:
- **Web Interface**: http://localhost:8001 (futuristic enhanced UI)
- **API v2 (Recommended)**: http://localhost:8000/api/v2
- **API v1 (Maintenance)**: http://localhost:8000/api/v1 (deprecated April 2026)
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

> **API Versioning:** Phase 0 cleanup consolidated routes with clear v1/v2 separation. Use v2 endpoints for new development.

For detailed startup options, see [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

## 📋 Features

- **GEO Metadata Parser**: Intelligent parsing of GEO database entries
- **AI-Powered Summarization**: Automated generation of dataset summaries
- **Multi-format Support**: Support for various omics data formats
- **Pattern Recognition**: Identification of trends and patterns in metadata
- **Search & Discovery**: Advanced search capabilities across datasets
- **Batch Processing**: Efficient processing of multiple datasets
- **Real-time Monitoring**: Live updates on processing status
- **API Integration**: RESTful API for programmatic access

## 🧪 Testing and Validation Framework

OmicsOracle includes a comprehensive testing and validation framework that ensures the system functions correctly at each stage:

- **[Event Flow Visualization](/docs/EVENT_FLOW_README.md)**: Visual representation of system event flow and test coverage
- **[Event Flow and Validation Map](/docs/EVENT_FLOW_VALIDATION_MAP.md)**: Detailed mapping of events to test files
- **[Event Flow Charts](/docs/EVENT_FLOW_CHART.md)**: Simplified Mermaid diagrams of the system flow
- **[Search System Technical Documentation](/docs/SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md)**: Architecture and implementation details of the search system

### Comprehensive Testing Suite

The project includes a robust testing framework with several specialized tools:

```bash
# Run all comprehensive tests at once
./run_all_tests.sh

# Run specific test components
python test_endpoints_comprehensive.py  # Test all API endpoints
python validate_enhanced_query_handler.py  # Validate the enhanced query handling
python validate_advanced_search.py  # Validate advanced search features
python search_performance_monitor.py  # Monitor search system performance
python search_error_analyzer.py --logs server.log  # Analyze search system errors
```

### Query Tracing and Validation

OmicsOracle includes a sophisticated query tracing system that monitors and reports on query processing:

- **Component Extraction**: Identifies diseases, tissues, organisms, and data types in queries
- **Synonym Expansion**: Expands biomedical terms with common synonyms
- **Multi-Strategy Search**: Falls back to alternative queries when needed
- **Trace Reports**: Generates detailed reports of query processing in Markdown format
- **Performance Monitoring**: Tracks query execution time and resource usage
- **Error Analysis**: Identifies patterns in errors to guide improvements

### Advanced Search Features

The system includes advanced search capabilities for improved result quality:

- **Semantic Ranking**: Ranks results based on biomedical relevance to the query
- **Result Clustering**: Groups results into meaningful categories
- **Query Reformulation**: Suggests alternative query formulations to users
- **Context-Aware Filtering**: Filters results based on biomedical context

```bash
# Test the advanced search features
python integrate_search_enhancer.py --demo

# Run the advanced search feature validation
python validate_advanced_search.py
```

This framework provides complete observability from server startup to frontend display, with appropriate tests for each component.

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, LangChain
- **AI/ML**: OpenAI API, scikit-learn, BioPython
- **Databases**: MongoDB, ChromaDB, Redis
- **Frontend**: React.js / Streamlit
- **DevOps**: Docker, Kubernetes, GitHub Actions

## 📁 Project Structure

```
OmicsOracle/
├── src/omics_oracle/          # Main application code (installed package)
│   ├── core/                  # Core models, config, exceptions
│   ├── pipeline/              # Search and processing pipeline
│   ├── geo_tools/             # GEO data retrieval
│   ├── nlp/                   # NLP processing
│   ├── services/              # Business logic services
│   ├── search/                # Search functionality
│   └── presentation/          # API, CLI, Web interfaces
│       ├── web/               # FastAPI application
│       │   └── routes/        # API routes (v1, v2, health, ui)
│       ├── cli/               # Command-line interface
│       └── api/               # API utilities
├── tests/                     # Test suites
│   ├── unit/                  # Fast unit tests
│   ├── integration/           # Integration tests
│   ├── e2e/                   # End-to-end tests
│   └── conftest.py            # Shared test fixtures
├── docs/                      # Documentation
│   ├── PHASE_0_CLEANUP_SUMMARY.md  # Cleanup summary
│   ├── PACKAGE_STRUCTURE.md   # Package structure details
│   ├── ROUTE_CONSOLIDATION.md # Route organization
│   └── TEST_ORGANIZATION.md   # Test organization guide
├── scripts/                   # Utility scripts
├── config/                    # Configuration files
└── pyproject.toml            # Package configuration (PEP 621)
```

> **Recent Changes:** Phase 0 cleanup modernized the structure with proper package organization, consolidated routes, and enhanced test fixtures. See [docs/PHASE_0_CLEANUP_SUMMARY.md](docs/PHASE_0_CLEANUP_SUMMARY.md) for details.

## 📚 Documentation

OmicsOracle's documentation is organized in the `docs/` directory:

### Core Documentation
- **[Documentation Index](/docs/README.md)**: Complete listing of all available documentation
- **[Architecture Overview](ARCHITECTURE.md)**: System architecture and design patterns
- **[Developer Guide](/docs/DEVELOPER_GUIDE.md)**: Development setup and guidelines

### Phase 0 Cleanup Documentation
- **[Phase 0 Cleanup Summary](/docs/PHASE_0_CLEANUP_SUMMARY.md)**: Complete Phase 0 cleanup details and migration guide
- **[Package Structure](/docs/PACKAGE_STRUCTURE.md)**: Package organization and type checking
- **[Route Consolidation](/docs/ROUTE_CONSOLIDATION.md)**: API route organization and versioning
- **[Test Organization](/docs/TEST_ORGANIZATION.md)**: Test structure and fixture guide

### Search System Documentation
- **[Search System Technical Documentation](/docs/SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md)**: Query handling and search system details
- **[Search System Case Study](/docs/SEARCH_SYSTEM_CASE_STUDY.md)**: Real-world examples and effectiveness
- **[Event Flow Visualization](/docs/EVENT_FLOW_README.md)**: System event flow and test coverage

### API Documentation
For interactive API documentation, visit when the server is running:
- **v2 API (Recommended)**: http://localhost:8000/docs
- **Health & Monitoring**: http://localhost:8000/health

## 🧪 Development

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend)
- Docker and Docker Compose
- Git

### Setup Development Environment

```bash
# Install package in development mode (important!)
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run specific test categories (Phase 0 enhancement)
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests
pytest -m "not slow"        # Skip slow tests

# Start development server (full-stack with hot reload)
./start.sh --dev

# Or start individual components:
./start.sh --backend-only     # Backend API only
./start.sh --frontend-only    # Frontend UI only
```

> **Development Mode:** The `-e` flag installs the package in editable mode, allowing changes to be immediately reflected without reinstallation. This is essential after Phase 0 cleanup.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/omics_oracle --cov-report=html

# Run specific test suites
pytest tests/unit/          # Fast unit tests (20+ files)
pytest tests/integration/   # Integration tests (42+ files)
pytest tests/e2e/           # End-to-end tests (2 files)

# Run by marker (Phase 0 enhancement)
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "not slow"        # Skip slow tests
pytest -m "not requires_network"  # Skip network tests

# Run specific test file
pytest tests/unit/test_cache_disabling.py -v

# Run with verbose output and print statements
pytest -v -s tests/unit/
```

> **Test Organization:** Phase 0 cleanup enhanced test structure with shared fixtures and markers. See [docs/TEST_ORGANIZATION.md](docs/TEST_ORGANIZATION.md) for details.

## 🔧 Configuration

Copy `.env.example` to `.env` and configure the following:

```bash
# API Configuration
OPENAI_API_KEY=your_openai_api_key
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
MAX_WORKERS=4
```

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in production mode
docker-compose -f docker-compose.prod.yml up
```

## 📊 Current Status

**Development Phase**: Phase 0 Cleanup (5 of 7 tasks complete)
**Version**: 0.1.1-dev (setuptools_scm managed)
**Branch**: phase-0-cleanup
**Last Updated**: October 2, 2025

### Recent Achievements (Phase 0)

✅ **Backup Removal** - Removed 365MB of redundant backups
✅ **Import Structure** - Eliminated 146 sys.path manipulations, proper package structure
✅ **Route Consolidation** - 7 route files → 4 organized files with clear v1/v2 versioning
✅ **Package Structure** - Added PEP 561 type checking support, explicit __all__ exports
✅ **Test Organization** - Enhanced fixtures, test markers, 93+ tests collecting successfully

### Next Steps

⏳ **Documentation Update** - Update all project documentation (current task)
⏳ **Final Review** - Verification and merge to main

See [docs/PHASE_0_CLEANUP_SUMMARY.md](docs/PHASE_0_CLEANUP_SUMMARY.md) for complete details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GEO Database team for providing comprehensive genomics data
- BioPython community for excellent bioinformatics tools
- OpenAI for advanced language model capabilities
- The broader genomics and bioinformatics research community

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/OmicsOracle/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/OmicsOracle/discussions)

---

**Built with ❤️ for the genomics research community**
