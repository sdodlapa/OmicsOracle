# OmicsOracle Architecture Documentation# 🏗️ OmicsOracle Architecture Overview



**Version:** 2.1.0  ## 🎯 System Purpose

**Last Updated:** October 5, 2025  OmicsOracle is a genomics data analysis platform that processes natural language queries to retrieve and summarize relevant research data from NCBI GEO (Gene Expression Omnibus).

**Status:** Production-Ready (Phase 4)

---

---

## 🔄 Core Query Processing Flow

## Table of Contents

```mermaid

1. [System Overview](#system-overview)graph TD

2. [Architecture Principles](#architecture-principles)    A[User Query] --> B[Web Interface]

3. [Project Structure](#project-structure)    B --> C[Enhanced Query Handler]

4. [Core Components](#core-components)    C --> D[Prompt Interpreter]

5. [API Architecture](#api-architecture)    D --> E[Advanced Search Enhancer]

6. [Agent System](#agent-system)    E --> F[Pipeline Orchestrator]

7. [Authentication & Security](#authentication--security)    F --> G[GEO Client]

8. [Data Flow](#data-flow)    F --> H[AI Summary Manager]

9. [Database Schema](#database-schema)    G --> I[NCBI GEO Database]

10. [Testing Strategy](#testing-strategy)    H --> J[OpenAI API]

11. [Deployment Architecture](#deployment-architecture)    I --> K[Raw GEO Data]

12. [Development Workflow](#development-workflow)    J --> L[AI Summary]

    K --> M[Summarizer]

---    L --> N[Final Response]

    M --> N

## System Overview    N --> O[Web Response]

```

### What is OmicsOracle?

---

OmicsOracle is an AI-powered biomedical research platform that helps researchers discover, analyze, and validate genomic datasets from the NCBI Gene Expression Omnibus (GEO) database.

## 📁 Core Architecture Components

### Key Capabilities

### **🌐 Presentation Layer**

- **Intelligent Query Processing** - Natural language understanding for biomedical queries```

- **Multi-Agent Orchestration** - Coordinated agents for query, search, validation, and reporting  src/omics_oracle/presentation/web/

- **RESTful API** - Complete REST API for programmatic access├── main.py              # FastAPI application entry point

- **Authentication & Authorization** - JWT-based auth with tier-based quotas├── dependencies.py      # Dependency injection setup

- **Real-time Workflows** - End-to-end research workflows from query to report├── routes/

- **Caching & Performance** - Multi-layer caching for optimal performance│   ├── query.py        # Main query endpoint (/query)

│   ├── health.py       # Health check endpoints

### Technology Stack│   └── summary.py      # Summary endpoints

├── middleware/

```│   ├── cors.py         # CORS configuration

Backend:        Python 3.11+, FastAPI, Pydantic│   ├── logging.py      # Request/response logging

Database:       SQLite (dev), PostgreSQL (prod)│   └── error_handler.py # Global error handling

NLP:            ScispaCy, BioBERT, Transformers└── websockets.py       # Real-time communication

AI/ML:          OpenAI GPT-4, LangChain```

External APIs:  NCBI Entrez, PubMed, GEO

Caching:        In-memory + Redis (optional)### **🔍 Search & Query Processing**

Testing:        pytest, pytest-asyncio, httpx```

Deployment:     Docker, Docker Compose, Nginxsrc/omics_oracle/search/

```├── enhanced_query_handler.py    # Main query coordinator

└── advanced_search_enhancer.py  # Query optimization & enhancement

---```



## Architecture Principles### **🧠 Natural Language Processing**

```

### 1. Clean Architecture (Layered Design)src/omics_oracle/nlp/

├── prompt_interpreter.py       # Query intent understanding

```└── biomedical_ner.py          # Biomedical entity recognition

┌─────────────────────────────────────────┐```

│         API Layer (FastAPI)             │  ← HTTP endpoints, request validation

├─────────────────────────────────────────┤### **⚙️ Processing Pipeline**

│      Business Logic (Agents)            │  ← Core algorithms, workflows```

├─────────────────────────────────────────┤src/omics_oracle/pipeline/

│    Infrastructure (Database, Cache)     │  ← Data persistence, external services└── pipeline.py                 # Main orchestration pipeline

└─────────────────────────────────────────┘```

```

### **🔗 External Data Integration**

**Benefits:**```

- Clear separation of concernssrc/omics_oracle/geo_tools/

- Easy to test each layer independently└── geo_client.py               # NCBI GEO API client

- Flexible to swap implementations```

- Scalable and maintainable

### **🤖 AI Services**

### 2. Agent-Based Architecture```

src/omics_oracle/services/

Each agent is a self-contained module responsible for a specific task:├── ai_summary_manager.py       # OpenAI integration

├── summarizer.py              # Data summarization

```python├── cost_manager.py            # API cost tracking

Agent (Abstract Base)└── cache.py                   # System-level caching (non-user-facing)

├── QueryAgent      → NLP processing, entity extraction```

├── SearchAgent     → GEO database search, ranking

├── DataAgent       → Quality validation, data assessment### **🛠️ Core Infrastructure**

└── ReportAgent     → Report generation, visualization```

```src/omics_oracle/core/

├── config.py                  # Configuration management

**Benefits:**├── models.py                  # Data models & schemas

- Single Responsibility Principle├── logging.py                 # Logging configuration

- Easy to add new agents└── exceptions.py              # Custom exceptions

- Testable in isolation```

- Composable into workflows

---

### 3. Dependency Injection

## 🔄 Detailed Query Processing Flow

Using FastAPI's built-in DI system:

### **1. Query Reception** 📨

```python- **Entry Point**: `POST /query` endpoint in `routes/query.py`

@router.post("/query")- **Input**: Natural language query from user

async def execute_query(- **Output**: Query object with metadata

    request: QueryRequest,

    current_user: User = Depends(get_current_user),### **2. Query Enhancement** 🚀

    agent: QueryAgent = Depends(get_query_agent),- **Component**: `enhanced_query_handler.py`

):- **Process**:

    # All dependencies injected automatically  - Validates and preprocesses query

    pass  - Coordinates with other components

```  - Manages query lifecycle

- **Output**: Enhanced query object

**Benefits:**

- Loose coupling### **3. Intent Understanding** 🧠

- Easy mocking for tests- **Component**: `prompt_interpreter.py`

- Configuration flexibility- **Process**:

- Reduced boilerplate  - Analyzes query intent and context

  - Extracts biomedical entities

### 4. Async-First Design  - Determines search strategy

- **Output**: Structured query parameters

All I/O operations are asynchronous:

### **4. Search Optimization** 🔍

```python- **Component**: `advanced_search_enhancer.py`

# Database- **Process**:

async def get_user(db: AsyncSession, user_id: int) -> User:  - Refines search terms

    result = await db.execute(select(User).where(User.id == user_id))  - Applies domain-specific knowledge

    return result.scalar_one_or_none()  - Optimizes for GEO database structure

- **Output**: Optimized search parameters

# HTTP

async with httpx.AsyncClient() as client:### **5. Pipeline Orchestration** ⚙️

    response = await client.get(url)- **Component**: `pipeline.py`

```- **Process**:

  - Coordinates data retrieval and processing

**Benefits:**  - Manages parallel operations

- High concurrency  - Handles error recovery

- Efficient resource usage- **Output**: Orchestrated data flow

- Better scalability

- Non-blocking I/O### **6. Data Retrieval** 📊

- **Component**: `geo_client.py`

---- **Process**:

  - Connects to NCBI GEO API

## Project Structure  - Retrieves relevant datasets

  - Handles API rate limiting

```- **Output**: Raw GEO dataset information

OmicsOracle/

├── omics_oracle_v2/              # Main application package### **7. AI Summarization** 🤖

│   ├── __init__.py- **Components**: `ai_summary_manager.py` + `summarizer.py`

│   ├── agents/                   # Agent implementations- **Process**:

│   │   ├── __init__.py  - Sends data to OpenAI API

│   │   ├── base.py              # Abstract base agent  - Generates human-readable summaries

│   │   ├── query_agent.py       # NLP query processing  - Manages API costs and usage

│   │   ├── search_agent.py      # GEO search- **Output**: Structured summaries

│   │   ├── data_agent.py        # Data validation

│   │   └── report_agent.py      # Report generation### **8. Response Assembly** 📋

│   │- **Component**: Query handler coordination

│   ├── api/                      # FastAPI application- **Process**:

│   │   ├── __init__.py  - Combines data and summaries

│   │   ├── main.py              # App entry point  - Formats for web response

│   │   ├── dependencies.py      # Shared dependencies  - Adds metadata and timing

│   │   ├── routes/              # API endpoints- **Output**: Final JSON response

│   │   │   ├── health.py        # Health checks

│   │   │   ├── auth.py          # Authentication---

│   │   │   ├── agents.py        # Agent execution

│   │   │   ├── workflows.py     # Workflow orchestration## 🔧 Key Design Principles

│   │   │   ├── quotas.py        # Quota management

│   │   │   └── batch.py         # Batch processing### **1. Direct Data Flow** 🎯

│   │   └── schemas/             # Pydantic models- No user-facing caching - all results are fresh from source

│   │       ├── agents.py- Linear processing pipeline for predictability

│   │       ├── workflows.py- Clear separation of concerns

│   │       └── common.py

│   │### **2. Fail-Safe Architecture** 🛡️

│   ├── auth/                     # Authentication system- Graceful degradation when external APIs fail

│   │   ├── __init__.py- Comprehensive error handling and logging

│   │   ├── models.py            # User, APIKey models- Timeout protection for all external calls

│   │   ├── schemas.py           # Auth request/response schemas

│   │   ├── security.py          # Password hashing, JWT### **3. Scalable Design** 📈

│   │   ├── dependencies.py      # get_current_user, etc.- Stateless components for horizontal scaling

│   │   └── quota.py             # Rate limiting, quotas- Async/await patterns for concurrent processing

│   │- Configurable rate limiting and resource management

│   ├── core/                     # Core business logic

│   │   ├── __init__.py### **4. Maintainable Code** 🧹

│   │   ├── orchestrator.py      # Workflow orchestration- Single responsibility principle

│   │   ├── config.py            # Configuration- Clear dependency injection

│   │   └── exceptions.py        # Custom exceptions- Comprehensive logging and monitoring

│   │

│   ├── database/                 # Database layer---

│   │   ├── __init__.py

│   │   ├── base.py              # SQLAlchemy base## 🌍 External Dependencies

│   │   └── session.py           # Session management

│   │### **Required Services**

│   ├── lib/                      # External integrations- **NCBI GEO API**: Primary data source for genomics datasets

│   │   ├── ai/                  # OpenAI integration- **OpenAI API**: AI-powered summarization and analysis

│   │   │   ├── client.py- **FastAPI**: Web framework for REST API

│   │   │   └── models.py

│   │   ├── geo/                 # NCBI GEO integration### **Configuration**

│   │   │   ├── client.py- Environment-based configuration (dev/test/prod)

│   │   │   └── models.py- API keys managed via environment variables

│   │   └── nlp/                 # NLP processing- Docker support for containerized deployment

│   │       ├── client.py

│   │       └── models.py---

│   │

│   ├── middleware/               # FastAPI middleware## 🚀 Getting Started

│   │   ├── __init__.py

│   │   ├── error_handler.py     # Global error handling### **Quick Start**

│   │   ├── rate_limit.py        # Rate limiting```bash

│   │   └── metrics.py           # Prometheus metrics# Install dependencies

│   │pip install -r requirements.txt

│   └── cache/                    # Caching layer

│       ├── __init__.py# Set environment variables

│       └── memory.py            # In-memory cachecp .env.example .env

│# Edit .env with your API keys

├── tests/                        # Test suite

│   ├── conftest.py              # Shared fixtures# Start the application

│   ├── api/                     # API endpoint tests./start.sh

│   │   ├── test_health.py```

│   │   ├── test_auth.py

│   │   ├── test_agents.py### **Development**

│   │   ├── test_workflows.py```bash

│   │   ├── test_quotas.py# Start with development features

│   │   └── test_batch.py./start.sh --dev

│   └── unit/                    # Unit tests

│       ├── test_agents.py# Backend only

│       └── test_nlp.py./start.sh --backend-only

│

├── docs/                         # Documentation# Run tests

│   ├── API_REFERENCE.mdpytest tests/

│   ├── DEPLOYMENT_GUIDE.md```

│   ├── DEVELOPER_GUIDE.md

│   └── testing/---

│       ├── DAY1_FINAL_STATUS.md

│       └── DAY2_FIXES_COMPLETE.md## 📊 Performance Characteristics

│

├── config/                       # Configuration files- **Query Response Time**: ~2-10 seconds (depending on data complexity)

│   ├── development.yml- **Concurrent Users**: Scales with container resources

│   ├── production.yml- **API Rate Limits**: Managed automatically with backoff strategies

│   └── nginx.conf- **Memory Usage**: ~100-500MB per instance

│- **Storage**: Minimal (no persistent user data caching)

├── scripts/                      # Utility scripts

│   ├── deploy.sh---

│   └── monitor.sh

│**🔍 For detailed implementation information, see the source code in `src/omics_oracle/`**

├── .github/                      # GitHub workflows
│   └── workflows/
│       └── tests.yml            # CI/CD pipeline
│
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Production image
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
├── mkdocs.yml                   # Documentation config
└── README.md                    # Project overview
```

---

## Core Components

### Ranking System

**Status:** ✅ Production Ready (Phase 0 Complete)
**Coverage:** 96.5% (58/58 tests passing)
**Documentation:** [Ranking System Architecture](docs/architecture/RANKING_SYSTEM.md)

The ranking system provides configurable, transparent dataset ranking:

- **KeywordRanker** - Keyword relevance scoring (97% coverage)
  - Title/summary matching with configurable weights
  - Organism matching bonus
  - Sample count bonuses
  - 280 lines, 23 tests

- **QualityScorer** - Dataset quality assessment (96% coverage)
  - Sample count scoring (25 points)
  - Title/summary quality (20 points)
  - Publications (20 points)
  - SRA data availability (15 points)
  - Recency scoring (10 points)
  - Metadata completeness (10 points)
  - 454 lines, 35 tests

**Key Benefits:**
- ✅ 88-95% code reduction in agents (155 lines removed)
- ✅ Fully configurable via `RankingConfig` and `QualityConfig`
- ✅ Transparent scoring with issue/strength reporting
- ✅ Production-ready with comprehensive test coverage

See full architecture document for detailed component descriptions.

---

## API Architecture

### Endpoint Structure

```
/api/v1/                          # Version 1 API
├── health                        # System health
├── agents/                       # Agent execution
│   ├── /                        # GET - List available agents
│   ├── query                    # POST - Execute query agent
│   ├── search                   # POST - Execute search agent
│   ├── validate                 # POST - Execute data agent
│   └── report                   # POST - Execute report agent
├── workflows/                    # Workflow orchestration
│   ├── /                        # GET - List workflows
│   └── execute                  # POST - Execute workflow
└── batch/                        # Batch processing
    ├── jobs                     # POST - Create batch job
    ├── jobs/{id}                # GET - Get job status
    └── jobs                     # GET - List jobs

/api/v2/                          # Version 2 API (auth-focused)
├── auth/                         # Authentication
│   ├── register                 # POST - User registration
│   ├── login                    # POST - User login
│   ├── refresh                  # POST - Refresh token
│   └── me                       # GET - Current user info
└── quotas/                       # Quota management
    ├── me                       # GET - My quota
    ├── me/history               # GET - Usage history
    └── {user_id}                # GET - User quota (admin)
```

---

## Testing Strategy

### Test Coverage

Current: **59.4% (41/69 tests passing)**

**Coverage by Category:**
- ✅ Health: 3/3 (100%)
- ✅ Auth: 14/14 (100%)
- ✅ User Quotas: 6/6 (100%)
- ✅ Workflows: 8/9 (89%)
- ⚠️ Agents: 7/14 (50%)
- ⚠️ Batch: 2/8 (25%)

See `docs/testing/` for detailed test reports.

---

## Development Workflow

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/OmicsOracle.git
cd OmicsOracle

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Start development server
uvicorn omics_oracle_v2.api.main:app --reload
```

### Running Tests

```bash
# All tests
pytest

# API tests only
pytest tests/api/

# With coverage
pytest --cov=omics_oracle_v2
```

---

For complete architecture documentation, see the full ARCHITECTURE.md file.

*Last updated: October 5, 2025*
*Version: 2.1.0*
*Status: Production Ready*
