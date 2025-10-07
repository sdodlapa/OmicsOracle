# 🧬 OmicsOracle

**AI-Powered Biomedical Dataset Discovery Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-220+-green.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📖 Overview

OmicsOracle is a **production-ready** platform that revolutionizes biomedical research by combining AI agents, semantic search, and comprehensive GEO dataset analysis. Find and analyze relevant genomic datasets in **seconds instead of hours**.

### 🎯 Key Features

✅ **Intelligent Search**
- Keyword-based search with 7-dimensional quality scoring
- **Semantic search** (95% complete) with query expansion
- Hybrid search combining TF-IDF and vector similarity
- Advanced filtering by organism, sample count, study type

✅ **AI-Powered Analysis**
- GPT-4 dataset insights with beautiful markdown rendering
- Automatic quality assessment
- Export to JSON and CSV

✅ **Production Features**
- JWT authentication with tiered access control
- Redis-powered rate limiting and quotas
- Comprehensive test coverage (220+ tests)
- RESTful API with OpenAPI documentation

✅ **Enterprise Ready**
- Clean, modular architecture (122 Python files)
- 85%+ test coverage
- Zero technical debt markers
- Docker deployment ready

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Redis (optional, for caching)
- OpenAI API key (for AI analysis)
- NCBI API key (for PubMed access)

### Installation

```bash
# Clone the repository
git clone https://github.com/sdodlapati3/OmicsOracle.git
cd OmicsOracle

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   - NCBI_EMAIL (required)
#   - NCBI_API_KEY (required)
#   - OPENAI_API_KEY (required for AI features)
```

### Start OmicsOracle

**🎯 SINGLE STARTUP METHOD (Use This!)**

```bash
# Start both API server and Dashboard with SSL bypass
# (Required for Georgia Tech/institutional networks)
./start_omics_oracle_ssl_bypass.sh
```

**What it does:**
1. ✅ Activates virtual environment automatically
2. ✅ Configures SSL bypass for institutional networks
3. ✅ Starts API server (port 8000)
4. ✅ Starts Dashboard (port 8502)
5. ✅ Monitors both services and auto-restarts if needed

**To stop:** Press `CTRL+C` (stops both services cleanly)

> ⚠️ **DO NOT** use other startup scripts - they're deprecated and may cause issues!

### Access Points

After starting:

- **📊 Streamlit Dashboard**: http://localhost:8502 ← **Primary Interface**
- **🔌 API Server**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/docs
- **❤️  Health Check**: http://localhost:8000/health

**View Logs:**
```bash
# API logs
tail -f /tmp/omics_api.log

# Dashboard logs
tail -f /tmp/omics_dashboard.log
```

📖 **Detailed guide:** [docs/STARTUP_GUIDE.md](docs/STARTUP_GUIDE.md)

---

## 💡 Usage Examples

### Web Interface (Recommended)

1. Open http://localhost:8000/static/semantic_search.html
2. Enter a search query (e.g., "breast cancer RNA-seq")
3. Apply filters (organism, sample count, etc.)
4. Click "Analyze with AI" for GPT-4 insights
5. Export results to JSON or CSV

### API Example

```bash
# Execute a search
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": "breast cancer",
    "organism": "Homo sapiens",
    "min_samples": 10,
    "enable_semantic": false
  }'
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "accession": "GSE123456",
      "title": "Gene expression in breast cancer...",
      "organism": "Homo sapiens",
      "sample_count": 50,
      "quality_score": 0.85,
      "summary": "..."
    }
  ],
  "execution_time": 0.234
}
```

📖 **Full API docs:** [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## 🏗️ Architecture

```
OmicsOracle/
├── omics_oracle_v2/        # Main package
│   ├── agents/             # Agent framework (Search, Data, Query, Report)
│   ├── api/                # FastAPI application
│   │   ├── routes/         # API endpoints
│   │   ├── static/         # Web UI
│   │   └── models/         # Request/response schemas
│   ├── lib/                # Core libraries (7,643 LOC)
│   │   ├── ai/             # LLM integration
│   │   ├── embeddings/     # Text embeddings
│   │   ├── geo/            # GEO database client
│   │   ├── nlp/            # NLP utilities
│   │   ├── ranking/        # Quality scoring
│   │   ├── rag/            # RAG pipeline
│   │   ├── search/         # Hybrid search
│   │   └── vector_db/      # FAISS vector database
│   ├── auth/               # Authentication
│   ├── cache/              # Caching layer
│   └── database/           # Data persistence
├── tests/                  # 220+ tests
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

**Learn more:** [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=omics_oracle_v2 --cov-report=html

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Run comprehensive test suite
./scripts/comprehensive_test_suite.py
```

**Test Coverage:** 85%+ in core modules
**Total Tests:** 220+

📖 **Testing guide:** [docs/testing/AUTOMATED_TESTING_GUIDE.md](docs/testing/AUTOMATED_TESTING_GUIDE.md)

---

## 📚 Documentation

### Essential Guides

- **[Current State](docs/CURRENT_STATE.md)** - What works right now (October 2025)
- **[Quick Start](docs/STARTUP_GUIDE.md)** - Get up and running
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** - How it all fits together
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation

### For Developers

- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup
- **[Code Quality Guide](docs/CODE_QUALITY_GUIDE.md)** - Standards and best practices
- **[Agent Framework](docs/AGENT_FRAMEWORK_GUIDE.md)** - Multi-agent architecture
- **[Testing Guide](docs/testing/AUTOMATED_TESTING_GUIDE.md)** - Writing tests

### For Deployment

- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Authentication System](docs/AUTH_SYSTEM.md)** - User management
- **[Rate Limiting](docs/RATE_LIMITING.md)** - Quotas and limits

📖 **Full documentation:** [docs/README.md](docs/README.md)

---

## 🎯 Current Status (October 2025)

### Production-Ready Features ✅

- ✅ GEO dataset search with quality scoring
- ✅ AI-powered analysis with GPT-4
- ✅ JWT authentication and authorization
- ✅ Rate limiting with Redis
- ✅ 220+ tests passing
- ✅ Clean, modular architecture

### Advanced Features (95% Complete) ⚠️

- ✅ Semantic search infrastructure built
- ✅ Query expansion with biomedical synonyms
- ✅ Hybrid search (TF-IDF + vector similarity)
- ✅ Cross-encoder reranking
- ✅ RAG pipeline for natural language Q&A
- ❌ GEO dataset embeddings (10-min task with API key)

**Status:** All code is built and integrated. Only dataset embeddings are missing.

### Roadmap 🚀

**This Week:**
- Generate GEO dataset embeddings (enable semantic search)
- Complete documentation consolidation

**Week 2:**
- Multi-agent architecture design
- Publication mining specification
- GPU deployment planning (A100/H100)

**Weeks 3-10:**
- Smart hybrid orchestrator (20% GPT-4, 80% BioMedLM)
- Publication mining with citation networks
- Multi-model integration on GPUs

📖 **Detailed roadmap:** [COMPLETION_PLAN.md](COMPLETION_PLAN.md)

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11+** - Modern Python features
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - Database ORM
- **Redis** - Caching and rate limiting

### AI/ML
- **OpenAI API** - GPT-4 for analysis
- **Sentence Transformers** - Cross-encoder reranking
- **FAISS** - Vector similarity search
- **OpenAI Embeddings** - text-embedding-3-small

### Frontend
- **Vanilla JavaScript** - Lightweight and fast
- **Chart.js** - Interactive visualizations
- **Marked.js** - Markdown rendering

---

## 📊 Code Quality

- **122 Python files** - Clean, modular architecture
- **7,643 lines** in core libraries
- **220+ tests** - Comprehensive coverage (85%+)
- **Zero TODO/FIXME** - No technical debt markers
- **Pre-commit hooks** - Black, isort, flake8

---

## 🤝 Contributing

We welcome contributions! Please:

1. Read [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
2. Check [docs/CODE_QUALITY_GUIDE.md](docs/CODE_QUALITY_GUIDE.md)
3. Review [docs/TEST_TEMPLATES.md](docs/TEST_TEMPLATES.md)
4. Fork the repository
5. Create a feature branch
6. Write tests for new features
7. Ensure all tests pass
8. Submit a pull request

---

## 📝 Recent Updates

### October 6, 2025
- ✅ Comprehensive code audit completed
- ✅ Phase 1 semantic search verified (95% complete)
- ✅ Documentation cleanup (22 files archived)
- ✅ Created sample datasets for testing
- 📝 Multi-agent architecture analysis

### October 5, 2025
- ✅ AI analysis markdown rendering fixed
- ✅ Phase 0 configurable ranking complete
- ✅ Authentication system deployed
- ✅ Redis-based rate limiting active

---

## 📧 Support

For issues or questions:
- Check [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)
- Review [docs/README.md](docs/README.md)
- Create an issue on GitHub

---

## 📄 License

[Add license information here]

---

**OmicsOracle** - Intelligent Biomedical Dataset Discovery
*Built with ❤️ for the research community*
