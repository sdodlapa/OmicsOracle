# 🧬 OmicsOracle# OmicsOracle 🧬🔮



**AI-Powered Biomedical Research Platform for Genomic Data Discovery****AI-Powered Genomics Data Summary Agent**



[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)OmicsOracle is an intelligent data summary agent designed to process, analyze, and summarize genomics and omics data, with a focus on GEO (Gene Expression Omnibus) metadata summarization. The system provides AI-driven insights, automated data processing, and comprehensive summaries for researchers and bioinformaticians.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)📖 **For detailed system architecture and query processing flow, see [ARCHITECTURE.md](ARCHITECTURE.md)**

[![Tests](https://img.shields.io/badge/tests-59%25-yellow.svg)](tests/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)## 🚀 Quick Start



---```bash

# Clone the repository

## 📖 Overviewgit clone <repository-url>

cd OmicsOracle

OmicsOracle is a production-ready platform that revolutionizes biomedical research by combining AI agents, natural language processing, and comprehensive genomic databases to help researchers discover and analyze relevant datasets in seconds instead of hours.

# Set up virtual environment

### 🎯 Key Featurespython -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

- **🤖 AI-Powered Query Processing** - Natural language understanding for biomedical queries

- **🔍 Intelligent Search** - Smart ranking and filtering of NCBI GEO datasets# Install package in development mode (recommended)

- **✅ Quality Validation** - Automated dataset quality assessment and scoringpip install -e .

- **📊 Automated Reporting** - AI-generated research reports with insights

- **🔐 Enterprise Security** - JWT authentication with tier-based access control# Install additional dependencies

- **⚡ High Performance** - Async architecture with multi-layer cachingpip install -r requirements-web.txt  # Web interface

- **🚀 Production Ready** - Docker deployment with comprehensive monitoringpip install -r requirements-dev.txt  # Development tools



---# Set up environment variables

cp .env.example .env

## 🚀 Quick Start

# Start the application (full-stack)

### Prerequisites./start.sh



- Python 3.11 or higher# Or start specific components:

- pip (Python package manager)./start.sh --backend-only    # API server only

- Git./start.sh --frontend-only   # Web interface only

./start.sh --dev            # Development mode with hot reload

### Installation```



```bash> **Note:** Phase 0 cleanup modernized the package structure. Use `pip install -e .` for proper import resolution and type checking support.

# 1. Clone the repository

git clone https://github.com/yourusername/OmicsOracle.git### 🌐 Access Points

cd OmicsOracle

After starting:

# 2. Create virtual environment- **Web Interface**: http://localhost:8001 (futuristic enhanced UI)

python -m venv venv- **API v2 (Recommended)**: http://localhost:8000/api/v2

source venv/bin/activate  # On Windows: venv\Scripts\activate- **API v1 (Maintenance)**: http://localhost:8000/api/v1 (deprecated April 2026)

- **API Documentation**: http://localhost:8000/docs

# 3. Install dependencies- **Health Check**: http://localhost:8000/health

pip install -r requirements.txt

> **API Versioning:** Phase 0 cleanup consolidated routes with clear v1/v2 separation. Use v2 endpoints for new development.

# 4. Set up environment variables

cp .env.example .envFor detailed startup options, see [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

# Edit .env with your configuration (API keys, database URL, etc.)

## 📋 Features

# 5. Start the development server

uvicorn omics_oracle_v2.api.main:app --reload- **GEO Metadata Parser**: Intelligent parsing of GEO database entries

```- **AI-Powered Summarization**: Automated generation of dataset summaries

- **Multi-format Support**: Support for various omics data formats

The API will be available at `http://localhost:8000`- **Pattern Recognition**: Identification of trends and patterns in metadata

- **Search & Discovery**: Advanced search capabilities across datasets

**API Documentation:** `http://localhost:8000/docs` (Swagger UI)- **Batch Processing**: Efficient processing of multiple datasets

- **Real-time Monitoring**: Live updates on processing status

---- **API Integration**: RESTful API for programmatic access



## 💡 Usage Examples## 🧪 Testing and Validation Framework



### Example 1: Natural Language QueryOmicsOracle includes a comprehensive testing and validation framework that ensures the system functions correctly at each stage:



```bash- **[Event Flow Visualization](/docs/EVENT_FLOW_README.md)**: Visual representation of system event flow and test coverage

# Register a user- **[Event Flow and Validation Map](/docs/EVENT_FLOW_VALIDATION_MAP.md)**: Detailed mapping of events to test files

curl -X POST http://localhost:8000/api/v2/auth/register \- **[Event Flow Charts](/docs/EVENT_FLOW_CHART.md)**: Simplified Mermaid diagrams of the system flow

  -H "Content-Type: application/json" \- **[Search System Technical Documentation](/docs/SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md)**: Architecture and implementation details of the search system

  -d '{

    "email": "researcher@example.com",### Comprehensive Testing Suite

    "password": "SecurePassword123!",

    "full_name": "Dr. Jane Smith"The project includes a robust testing framework with several specialized tools:

  }'

```bash

# Login to get token# Run all comprehensive tests at once

curl -X POST http://localhost:8000/api/v2/auth/login \./run_all_tests.sh

  -H "Content-Type: application/json" \

  -d '{# Run specific test components

    "email": "researcher@example.com",python test_endpoints_comprehensive.py  # Test all API endpoints

    "password": "SecurePassword123!"python validate_enhanced_query_handler.py  # Validate the enhanced query handling

  }'python validate_advanced_search.py  # Validate advanced search features

python search_performance_monitor.py  # Monitor search system performance

# Use the returned token for authenticated requestspython search_error_analyzer.py --logs server.log  # Analyze search system errors

TOKEN="your-jwt-token-here"```



# Execute a natural language query### Query Tracing and Validation

curl -X POST http://localhost:8000/api/v1/agents/query \

  -H "Authorization: Bearer $TOKEN" \OmicsOracle includes a sophisticated query tracing system that monitors and reports on query processing:

  -H "Content-Type: application/json" \

  -d '{- **Component Extraction**: Identifies diseases, tissues, organisms, and data types in queries

    "query": "Find breast cancer datasets with gene expression data"- **Synonym Expansion**: Expands biomedical terms with common synonyms

  }'- **Multi-Strategy Search**: Falls back to alternative queries when needed

```- **Trace Reports**: Generates detailed reports of query processing in Markdown format

- **Performance Monitoring**: Tracks query execution time and resource usage

**Response:**- **Error Analysis**: Identifies patterns in errors to guide improvements

```json

{### Advanced Search Features

  "success": true,

  "original_query": "Find breast cancer datasets with gene expression data",The system includes advanced search capabilities for improved result quality:

  "intent": "dataset_search",

  "confidence": 0.95,- **Semantic Ranking**: Ranks results based on biomedical relevance to the query

  "entities": [- **Result Clustering**: Groups results into meaningful categories

    {- **Query Reformulation**: Suggests alternative query formulations to users

      "text": "breast cancer",- **Context-Aware Filtering**: Filters results based on biomedical context

      "entity_type": "disease",

      "confidence": 0.98```bash

    },# Test the advanced search features

    {python integrate_search_enhancer.py --demo

      "text": "gene expression",

      "entity_type": "data_type",# Run the advanced search feature validation

      "confidence": 0.96python validate_advanced_search.py

    }```

  ],

  "search_terms": ["breast cancer", "gene expression", "microarray"],This framework provides complete observability from server startup to frontend display, with appropriate tests for each component.

  "execution_time_ms": 234

}## 🛠️ Technology Stack

```

- **Backend**: Python 3.11+, FastAPI, LangChain

### Example 2: Full Analysis Workflow- **AI/ML**: OpenAI API, scikit-learn, BioPython

- **Databases**: MongoDB, ChromaDB, Redis

```bash- **Frontend**: React.js / Streamlit

# Execute complete workflow: Query → Search → Validate → Report- **DevOps**: Docker, Kubernetes, GitHub Actions

curl -X POST http://localhost:8000/api/v1/workflows/execute \

  -H "Authorization: Bearer $TOKEN" \## 📁 Project Structure

  -H "Content-Type: application/json" \

  -d '{```

    "workflow_type": "full_analysis",OmicsOracle/

    "query": "cancer immunotherapy response biomarkers",├── src/omics_oracle/          # Main application code (installed package)

    "max_results": 10│   ├── core/                  # Core models, config, exceptions

  }'│   ├── pipeline/              # Search and processing pipeline

```│   ├── geo_tools/             # GEO data retrieval

│   ├── nlp/                   # NLP processing

**Response:**│   ├── services/              # Business logic services

```json│   ├── search/                # Search functionality

{│   └── presentation/          # API, CLI, Web interfaces

  "workflow_type": "full_analysis",│       ├── web/               # FastAPI application

  "status": "completed",│       │   └── routes/        # API routes (v1, v2, health, ui)

  "steps_completed": ["query", "search", "validate", "report"],│       ├── cli/               # Command-line interface

  "datasets_found": 8,│       └── api/               # API utilities

  "high_quality_datasets": 5,├── tests/                     # Test suites

  "report": {│   ├── unit/                  # Fast unit tests

    "summary": "Found 8 relevant datasets for cancer immunotherapy biomarkers...",│   ├── integration/           # Integration tests

    "key_findings": [│   ├── e2e/                   # End-to-end tests

      "5 datasets with high-quality gene expression data",│   └── conftest.py            # Shared test fixtures

      "3 datasets include clinical outcome data",├── docs/                      # Documentation

      "Recent publications (2020-2024) available for 6 datasets"│   ├── PHASE_0_CLEANUP_SUMMARY.md  # Cleanup summary

    ],│   ├── PACKAGE_STRUCTURE.md   # Package structure details

    "recommendations": [│   ├── ROUTE_CONSOLIDATION.md # Route organization

      "GSE123456: Highest relevance score (0.94), includes RNA-seq data",│   └── TEST_ORGANIZATION.md   # Test organization guide

      "GSE234567: Large sample size (n=500), published in Nature 2023"├── scripts/                   # Utility scripts

    ]├── config/                    # Configuration files

  },└── pyproject.toml            # Package configuration (PEP 621)

  "execution_time_ms": 4521```

}

```> **Recent Changes:** Phase 0 cleanup modernized the structure with proper package organization, consolidated routes, and enhanced test fixtures. See [docs/PHASE_0_CLEANUP_SUMMARY.md](docs/PHASE_0_CLEANUP_SUMMARY.md) for details.



### Example 3: List Available Agents## 📚 Documentation



```bashOmicsOracle's documentation is organized in the `docs/` directory:

curl -X GET http://localhost:8000/api/v1/agents \

  -H "Authorization: Bearer $TOKEN"### Core Documentation

```- **[Documentation Index](/docs/README.md)**: Complete listing of all available documentation

- **[Architecture Overview](ARCHITECTURE.md)**: System architecture and design patterns

**Response:**- **[Developer Guide](/docs/DEVELOPER_GUIDE.md)**: Development setup and guidelines

```json

{### Phase 0 Cleanup Documentation

  "agents": [- **[Phase 0 Cleanup Summary](/docs/PHASE_0_CLEANUP_SUMMARY.md)**: Complete Phase 0 cleanup details and migration guide

    {- **[Package Structure](/docs/PACKAGE_STRUCTURE.md)**: Package organization and type checking

      "id": "query",- **[Route Consolidation](/docs/ROUTE_CONSOLIDATION.md)**: API route organization and versioning

      "name": "Query Agent",- **[Test Organization](/docs/TEST_ORGANIZATION.md)**: Test structure and fixture guide

      "description": "Process natural language queries and extract biomedical entities",

      "category": "NLP Processing",### Search System Documentation

      "capabilities": ["Entity Recognition", "Intent Detection", "Search Term Generation"],- **[Search System Technical Documentation](/docs/SEARCH_SYSTEM_TECHNICAL_DOCUMENTATION.md)**: Query handling and search system details

      "endpoint": "/api/v1/agents/query"- **[Search System Case Study](/docs/SEARCH_SYSTEM_CASE_STUDY.md)**: Real-world examples and effectiveness

    },- **[Event Flow Visualization](/docs/EVENT_FLOW_README.md)**: System event flow and test coverage

    {

      "id": "search",### API Documentation

      "name": "Search Agent",For interactive API documentation, visit when the server is running:

      "description": "Search and rank GEO datasets based on relevance",- **v2 API (Recommended)**: http://localhost:8000/docs

      "category": "Data Discovery",- **Health & Monitoring**: http://localhost:8000/health

      "capabilities": ["GEO Database Search", "Relevance Ranking", "Dataset Filtering"],

      "endpoint": "/api/v1/agents/search"## 🧪 Development

    }

  ]### Prerequisites

}

```- Python 3.11 or higher

- Node.js 18+ (for frontend)

---- Docker and Docker Compose

- Git

## 🏗️ Architecture

### Setup Development Environment

### System Overview

```bash

```# Install package in development mode (important!)

┌─────────────────────────────────────────────────────────────┐pip install -e .

│                     OmicsOracle Platform                    │

├─────────────────────────────────────────────────────────────┤# Install development dependencies

│                                                             │pip install -r requirements-dev.txt

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │

│  │ Query Agent  │  │ Search Agent │  │  Data Agent  │    │# Set up pre-commit hooks

│  │    (NLP)     │→ │  (GEO API)   │→ │ (Validation) │    │pre-commit install

│  └──────────────┘  └──────────────┘  └──────────────┘    │

│         │                  │                  │           │# Run tests

│         └──────────────────┴──────────────────┘           │pytest

│                          │                                │

│                   ┌──────▼──────┐                         │# Run specific test categories (Phase 0 enhancement)

│                   │   Report    │                         │pytest -m unit              # Fast unit tests only

│                   │    Agent    │                         │pytest -m integration       # Integration tests

│                   └─────────────┘                         │pytest -m "not slow"        # Skip slow tests

│                                                            │

├────────────────────────────────────────────────────────────┤# Start development server (full-stack with hot reload)

│                  FastAPI REST API                          │./start.sh --dev

│  Authentication │ Rate Limiting │ Caching │ Monitoring    │

└────────────────────────────────────────────────────────────┘# Or start individual components:

```./start.sh --backend-only     # Backend API only

./start.sh --frontend-only    # Frontend UI only

### Tech Stack```



- **Backend Framework:** FastAPI (async Python web framework)> **Development Mode:** The `-e` flag installs the package in editable mode, allowing changes to be immediately reflected without reinstallation. This is essential after Phase 0 cleanup.

- **Database:** SQLAlchemy 2.0 with async support

- **NLP:** ScispaCy, BioBERT, Transformers### Running Tests

- **AI:** OpenAI GPT-4, LangChain

- **External APIs:** NCBI Entrez, PubMed, GEO```bash

- **Caching:** In-memory (production: Redis)# Run all tests

- **Testing:** pytest, pytest-asyncio, httpxpytest

- **Deployment:** Docker, Docker Compose, Nginx

# Run with coverage

---pytest --cov=src/omics_oracle --cov-report=html



## 📂 Project Structure# Run specific test suites

pytest tests/unit/          # Fast unit tests (20+ files)

```pytest tests/integration/   # Integration tests (42+ files)

OmicsOracle/pytest tests/e2e/           # End-to-end tests (2 files)

├── omics_oracle_v2/              # Main application

│   ├── agents/                   # AI agents (Query, Search, Data, Report)# Run by marker (Phase 0 enhancement)

│   ├── api/                      # FastAPI application & routespytest -m unit              # Only unit tests

│   ├── auth/                     # Authentication & authorizationpytest -m integration       # Only integration tests

│   ├── core/                     # Business logic & orchestrationpytest -m "not slow"        # Skip slow tests

│   ├── database/                 # Database models & sessionspytest -m "not requires_network"  # Skip network tests

│   ├── lib/                      # External integrations (GEO, OpenAI, NLP)

│   ├── middleware/               # Rate limiting, error handling# Run specific test file

│   └── cache/                    # Caching layerpytest tests/unit/test_cache_disabling.py -v

├── tests/                        # Test suite (59% coverage)

│   ├── api/                      # API endpoint tests# Run with verbose output and print statements

│   └── unit/                     # Unit testspytest -v -s tests/unit/

├── docs/                         # Documentation```

├── config/                       # Configuration files

├── scripts/                      # Utility scripts> **Test Organization:** Phase 0 cleanup enhanced test structure with shared fixtures and markers. See [docs/TEST_ORGANIZATION.md](docs/TEST_ORGANIZATION.md) for details.

└── docker-compose.yml            # Docker orchestration

```## 🔧 Configuration



See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.Copy `.env.example` to `.env` and configure the following:



---```bash

# API Configuration

## 🧪 TestingOPENAI_API_KEY=your_openai_api_key

MONGODB_URL=mongodb://localhost:27017

### Run TestsREDIS_URL=redis://localhost:6379



```bash# Application Settings

# All testsDEBUG=true

pytestLOG_LEVEL=INFO

MAX_WORKERS=4

# API tests only```

pytest tests/api/

## 🐳 Docker

# With coverage report

pytest --cov=omics_oracle_v2 --cov-report=html```bash

# Build and run with Docker Compose

# Fast tests (skip slow integration tests)docker-compose up --build

pytest -m "not slow"

```# Run in production mode

docker-compose -f docker-compose.prod.yml up

### Test Coverage```



Current: **59.4% (41/69 tests passing)**## 📊 Current Status



**By Category:****Development Phase**: Phase 0 Cleanup (5 of 7 tasks complete)

- ✅ **Health:** 3/3 (100%)**Version**: 0.1.1-dev (setuptools_scm managed)

- ✅ **Authentication:** 14/14 (100%)**Branch**: phase-0-cleanup

- ✅ **User Quotas:** 6/6 (100%)**Last Updated**: October 2, 2025

- ✅ **Workflows:** 8/9 (89%)

- ⚠️ **Agents:** 7/14 (50%)### Recent Achievements (Phase 0)

- ⚠️ **Batch Processing:** 2/8 (25%)

✅ **Backup Removal** - Removed 365MB of redundant backups

See [docs/testing/](docs/testing/) for detailed test reports.✅ **Import Structure** - Eliminated 146 sys.path manipulations, proper package structure

✅ **Route Consolidation** - 7 route files → 4 organized files with clear v1/v2 versioning

---✅ **Package Structure** - Added PEP 561 type checking support, explicit __all__ exports

✅ **Test Organization** - Enhanced fixtures, test markers, 93+ tests collecting successfully

## 🐳 Docker Deployment

### Next Steps

### Development

⏳ **Documentation Update** - Update all project documentation (current task)

```bash⏳ **Final Review** - Verification and merge to main

# Build and start all services

docker-compose up --buildSee [docs/PHASE_0_CLEANUP_SUMMARY.md](docs/PHASE_0_CLEANUP_SUMMARY.md) for complete details.



# Services:## 🤝 Contributing

# - API: http://localhost:8000

# - Docs: http://localhost:8000/docs1. Fork the repository

# - Database: PostgreSQL on port 54322. Create a feature branch (`git checkout -b feature/amazing-feature`)

```3. Commit your changes (`git commit -m 'Add amazing feature'`)

4. Push to the branch (`git push origin feature/amazing-feature`)

### Production5. Open a Pull Request



```bash## 📄 License

# Build production image

docker build -f Dockerfile.production -t omicsoracle:latest .This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



# Run with production settings## 🙏 Acknowledgments

docker run -p 8000:8000 \

  -e DATABASE_URL="postgresql://..." \- GEO Database team for providing comprehensive genomics data

  -e OPENAI_API_KEY="sk-..." \- BioPython community for excellent bioinformatics tools

  omicsoracle:latest- OpenAI for advanced language model capabilities

```- The broader genomics and bioinformatics research community



See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed deployment instructions.## 📞 Support



---- **Documentation**: [docs/](docs/)

- **Issues**: [GitHub Issues](https://github.com/your-org/OmicsOracle/issues)

## 🔐 Security- **Discussions**: [GitHub Discussions](https://github.com/your-org/OmicsOracle/discussions)



### Authentication---



- **JWT-based authentication** with refresh tokens**Built with ❤️ for the genomics research community**

- **Password hashing** using bcrypt
- **Tier-based access control** (Free, Pro, Enterprise)
- **Rate limiting** per user tier

### API Security

- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention
- XSS protection

### Environment Variables

Never commit sensitive data! Use `.env` file:

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost/omics_oracle
OPENAI_API_KEY=sk-your-openai-key
SECRET_KEY=your-secret-key-for-jwt

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 📊 API Reference

### Base URLs

- **Development:** `http://localhost:8000`
- **Production:** `https://api.omicsoracle.com`

### Authentication

All endpoints (except `/health` and `/auth/*`) require authentication:

```bash
Authorization: Bearer <your-jwt-token>
```

### Endpoints

#### Health & Monitoring
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics

#### Authentication (v2)
- `POST /api/v2/auth/register` - Register new user
- `POST /api/v2/auth/login` - Login and get JWT token
- `POST /api/v2/auth/refresh` - Refresh access token
- `GET /api/v2/auth/me` - Get current user info

#### Agents (v1)
- `GET /api/v1/agents` - List available agents
- `POST /api/v1/agents/query` - Execute query agent
- `POST /api/v1/agents/search` - Execute search agent
- `POST /api/v1/agents/validate` - Execute data validation agent
- `POST /api/v1/agents/report` - Execute report agent

#### Workflows (v1)
- `GET /api/v1/workflows` - List available workflows
- `POST /api/v1/workflows/execute` - Execute workflow

#### Quotas (v2)
- `GET /api/v2/quotas/me` - Get my quota
- `GET /api/v2/quotas/me/history` - Get usage history

See full API documentation at `/docs` (Swagger UI) when server is running.

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code quality checks
black omics_oracle_v2/          # Format code
flake8 omics_oracle_v2/         # Lint
mypy omics_oracle_v2/           # Type check
```

### Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **mypy** for type checking
- **isort** for import sorting

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create pull request
git push origin feature/your-feature-name
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

---

## 📈 Roadmap

### ✅ Phase 1: Core Infrastructure (Complete)
- ✅ Agent architecture
- ✅ FastAPI application
- ✅ Database layer
- ✅ Basic NLP processing

### ✅ Phase 2: Authentication & Security (Complete)
- ✅ JWT authentication
- ✅ User management
- ✅ Rate limiting
- ✅ Tier-based quotas

### ✅ Phase 3: Testing & Quality (Complete)
- ✅ Automated test suite
- ✅ 59% test coverage
- ✅ CI/CD pipeline
- ✅ Documentation

### 🔄 Phase 4: Production Features (In Progress)
- 🔄 Advanced search features
- 🔄 Batch processing workflows
- 🔄 Export functionality
- 🔄 Performance optimization

### 📅 Phase 5: Advanced Features (Planned)
- 📅 Real-time collaboration
- 📅 Workflow scheduling
- 📅 Analytics dashboard
- 📅 Custom agent creation API

### 📅 Phase 6: ML/AI Improvements (Future)
- 📅 Fine-tuned biomedical models
- 📅 Automated dataset curation
- 📅 Predictive analytics
- 📅 Knowledge graph integration

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add some amazing feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow the existing code style
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

**Sanjeeva Dodlapati**
- GitHub: [@sdodlapati3](https://github.com/sdodlapati3)
- Email: support@omicsoracle.com

---

## 🙏 Acknowledgments

- **NCBI** for providing the GEO database and Entrez API
- **OpenAI** for GPT-4 API
- **ScispaCy** team for biomedical NLP models
- **FastAPI** community for excellent framework and documentation
- **Pydantic** for data validation
- All contributors and users of OmicsOracle

---

## 📞 Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/yourusername/OmicsOracle/issues)
- **Email:** support@omicsoracle.com

---

## 📊 Project Status

- **Version:** 2.1.0
- **Status:** Production Ready
- **Test Coverage:** 59.4%
- **Last Updated:** October 5, 2025

---

**Made with ❤️ for biomedical researchers worldwide**
