# OmicsOracle Documentation

**Last Updated:** October 6, 2025  
**Status:** Production-Ready with Advanced Semantic Search  
**Version:** 2.0

---

## 🚀 Quick Start

**Get running in 5 minutes:**

1. **Install:** `pip install -r requirements.txt`
2. **Configure:** Copy `.env.example` to `.env` (add OPENAI_API_KEY for AI analysis)
3. **Start:** `./start_dev_server.sh`
4. **Browse:** http://localhost:8000/static/semantic_search.html

📖 **Detailed guide:** [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

---

## 📚 Documentation Index

### 🎯 Essential Guides (Start Here)

- **[Current State](CURRENT_STATE.md)** - What works right now (October 2025)
- **[Quick Start Guide](STARTUP_GUIDE.md)** - Get up and running in 5 minutes
- **[System Architecture](SYSTEM_ARCHITECTURE.md)** - How everything fits together
- **[API Reference](API_REFERENCE.md)** - REST API documentation

### 👥 For Users

- **[Web Interface Demo](WEB_INTERFACE_DEMO_GUIDE.md)** - UI walkthrough
- **[Advanced Search Features](ADVANCED_SEARCH_FEATURES.md)** - Search capabilities
- **[AI Analysis Explained](AI_ANALYSIS_EXPLAINED.md)** - Understanding AI insights

### 🛠️ For Developers

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development setup and workflows
- **[Code Quality Guide](CODE_QUALITY_GUIDE.md)** - Standards and best practices
- **[Agent Framework Guide](AGENT_FRAMEWORK_GUIDE.md)** - Multi-agent architecture
- **[Testing Hierarchy](TESTING_HIERARCHY.md)** - Test organization
- **[Test Templates](TEST_TEMPLATES.md)** - Writing tests

### 🚀 For Deployment

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Authentication System](AUTH_SYSTEM.md)** - User management and security
- **[Rate Limiting](RATE_LIMITING.md)** - Quotas and rate limits

### 📊 Architecture & Design

📂 **[architecture/](architecture/)** - Detailed architecture documents
- Ranking system design
- Search pipeline architecture
- Event flow validation
- Interface analysis

### 🧪 Testing

📂 **[testing/](testing/)** - Testing documentation
- **[Automated Testing Guide](testing/AUTOMATED_TESTING_GUIDE.md)**
- Test templates and examples
- Coverage reports

### 📦 Archive

📂 **[archive/](archive/)** - Historical documentation
- **[Phase Plans (2025-10)](archive/phase-plans-2025-10/)** - Archived phase plans
- **[Analysis Reports (2025-10)](archive/analysis-reports-2025-10/)** - Archived analyses
- Old session notes and debugging docs

---

## ✨ What's Working (Production-Ready)

### ✅ GEO Dataset Search
- Keyword-based search with intelligent query parsing
- 7-dimensional quality scoring (96% test coverage)
- Advanced filters (organism, sample count, study type)
- 220+ tests passing

### ✅ AI-Powered Analysis
- GPT-4 dataset insights with markdown rendering
- Automatic quality assessment
- Export capabilities (JSON, CSV)
- Cost: ~$0.03 per analysis

### ✅ Semantic Search (95% Complete)
**Code Status:** All infrastructure built and integrated
- Query expansion with biomedical synonyms
- Hybrid search (TF-IDF 40% + semantic 60%)
- Cross-encoder reranking for precision
- RAG pipeline for natural language Q&A

**Integration:** ✅ SearchAgent, ✅ API, ✅ UI toggle  
**Missing:** Dataset embeddings (10-min task with OpenAI API key)

### ✅ Authentication & Authorization
- JWT-based authentication
- Tiered access control (Free, Pro, Enterprise)
- API key management
- User registration and login

### ✅ Rate Limiting & Quotas
- Redis-powered rate limiting
- Per-user quotas with tiers
- Usage tracking and analytics
- Sliding window algorithm

---

## 🏗️ Architecture Overview

```
omics_oracle_v2/
├── agents/           # Agent framework (Search, Data, Query, Report)
├── api/              # FastAPI REST API
│   ├── routes/       # API endpoints
│   ├── static/       # Web UI (semantic_search.html)
│   └── models/       # Request/response schemas
├── lib/              # Core libraries (7,643 LOC)
│   ├── ai/           # LLM integration (GPT-4)
│   ├── embeddings/   # Text embedding service
│   ├── geo/          # GEO database client
│   ├── nlp/          # NLP utilities (NER, query expansion)
│   ├── ranking/      # Result ranking & scoring
│   ├── rag/          # RAG pipeline
│   ├── search/       # Hybrid search engine
│   └── vector_db/    # FAISS vector database
├── auth/             # Authentication & authorization
├── cache/            # Caching layer (Redis)
└── database/         # SQLite database
```

**Details:** [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

---

## 📊 Code Quality

- **122 Python files** - Well-organized modular architecture
- **7,643 lines** in library modules
- **220+ tests** - Comprehensive test coverage (85%+)
- **Zero TODO/FIXME** markers in source code
- **Pre-commit hooks** - Automated quality checks

---

## 📖 How to Use This Documentation

### New Users (5 minutes)
1. [CURRENT_STATE.md](CURRENT_STATE.md) - What works right now
2. [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Get the server running
3. [WEB_INTERFACE_DEMO_GUIDE.md](WEB_INTERFACE_DEMO_GUIDE.md) - Try the UI

### Developers (30 minutes)
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development setup
2. [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - System design
3. [CODE_QUALITY_GUIDE.md](CODE_QUALITY_GUIDE.md) - Standards
4. [testing/AUTOMATED_TESTING_GUIDE.md](testing/AUTOMATED_TESTING_GUIDE.md) - Testing

### API Integration (15 minutes)
1. [API_REFERENCE.md](API_REFERENCE.md) - Complete API docs
2. [RATE_LIMITING.md](RATE_LIMITING.md) - Quotas and limits
3. [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - Authentication

### Deployment (1 hour)
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
2. [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - User management
3. [RATE_LIMITING.md](RATE_LIMITING.md) - Rate limit configuration

---

## 🎯 Current Focus (October 2025)

### ✅ Completed This Week
- Comprehensive code audit (verified 95% Phase 1 completion)
- Documentation cleanup (22 files archived)
- Sample dataset creation (10 biomedical datasets)
- Strategic assessment and planning

### ⏭️ This Week
- Generate GEO dataset embeddings (enable semantic search)
- Complete documentation consolidation (330 → 50 files)
- Create comprehensive user guides

### 📋 Week 2: Multi-Agent Planning
- Design smart hybrid orchestrator (20% GPT-4, 80% BioMedLM)
- Specify publication mining modules
- Plan GPU deployment (A100 on-prem, H100 on GCP)
- Create 8-week implementation roadmap

**Details:** See [COMPLETION_PLAN.md](../COMPLETION_PLAN.md)

---

## 🗂️ Documentation Standards

- **Markdown format** for all documentation
- **Clear headings** with emoji navigation
- **Code examples** where applicable
- **Diagrams** in `images/` folder
- **Archive old docs** to `archive/` before major updates
- **Update this README** when adding new documentation

---

**OmicsOracle** - Intelligent Biomedical Dataset Discovery  
*Built with ❤️ for the research community*

Last Updated: October 6, 2025
