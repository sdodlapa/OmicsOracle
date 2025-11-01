# OmicsOracle Documentation# OmicsOracle Documentation



**Last Updated:** October 8, 2025  **Last Updated:** October 6, 2025

**Current Phase:** Phase 5 - Frontend Excellence  **Status:** Production-Ready with Advanced Semantic Search

**Documentation Version:** 2.0 (Date-based organization)**Version:** 2.0



------



## 🎯 Quick Start## 🚀 Quick Start



### For New Developers**Get running in 5 minutes:**

1. Start with [Developer Guide](guides/DEVELOPER_GUIDE.md)

2. Read [System Architecture](current-2025-10/architecture/SYSTEM_ARCHITECTURE.md)1. **Install:** `pip install -r requirements.txt`

3. Review [API Reference](current-2025-10/api/API_REFERENCE.md)2. **Configure:** Copy `.env.example` to `.env` (add OPENAI_API_KEY for AI analysis)

4. Check [Startup Guide](guides/STARTUP_GUIDE.md)3. **Start:** `./start_dev_server.sh`

4. **Browse:** http://localhost:8000/static/semantic_search.html

### For Current Development

1. [Phase 5 Overview](phase5-2025-10-to-2025-12/00-overview/) - What we're building📖 **Detailed guide:** [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

2. [Current Sprint](phase5-2025-10-to-2025-12/01-sprint1-2025-10-08-to-10-22/) - Active work

3. [Architecture Updates](current-2025-10/architecture/) - System design---

4. [API Documentation](current-2025-10/api/) - Endpoints and contracts

## 📚 Documentation Index

---

### 🎯 Essential Guides (Start Here)

## 📂 Documentation Structure

- **[Current State](CURRENT_STATE.md)** - What works right now (October 2025)

### 🔵 Current (October 2025)- **[Quick Start Guide](STARTUP_GUIDE.md)** - Get up and running in 5 minutes

**Path:** `current-2025-10/`  - **[System Architecture](SYSTEM_ARCHITECTURE.md)** - How everything fits together

**Purpose:** Active reference documentation for current system state- **[API Reference](API_REFERENCE.md)** - REST API documentation



- **[Architecture](current-2025-10/architecture/)** - System design and data flow### 👥 For Users

- **[API](current-2025-10/api/)** - API documentation and specifications

- **[Features](current-2025-10/features/)** - Feature documentation- **[Web Interface Demo](WEB_INTERFACE_DEMO_GUIDE.md)** - UI walkthrough

- **[Integration](current-2025-10/integration/)** - Integration layer- **[Advanced Search Features](ADVANCED_SEARCH_FEATURES.md)** - Search capabilities

- **[AI Analysis Explained](AI_ANALYSIS_EXPLAINED.md)** - Understanding AI insights

### 🚀 Phase 5: Frontend Excellence (Oct-Dec 2025)

**Path:** `phase5-2025-10-to-2025-12/`  ### 🛠️ For Developers

**Status:** 🚧 Active - Sprint 1 of 4

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development setup and workflows

- **[00-overview](phase5-2025-10-to-2025-12/00-overview/)** - Phase 5 goals- **[Code Quality Guide](CODE_QUALITY_GUIDE.md)** - Standards and best practices

- **[01-sprint1 (Oct 8-22)](phase5-2025-10-to-2025-12/01-sprint1-2025-10-08-to-10-22/)** - GEO Features ⏳ Current- **[Agent Framework Guide](AGENT_FRAMEWORK_GUIDE.md)** - Multi-agent architecture

- **[02-sprint2 (Oct 23-Nov 6)](phase5-2025-10-to-2025-12/02-sprint2-2025-10-23-to-11-06/)** - UX Polish- **[Testing Hierarchy](TESTING_HIERARCHY.md)** - Test organization

- **[03-sprint3 (Nov 7-21)](phase5-2025-10-to-2025-12/03-sprint3-2025-11-07-to-11-21/)** - Performance- **[Test Templates](TEST_TEMPLATES.md)** - Writing tests

- **[04-sprint4 (Nov 22-Dec 6)](phase5-2025-10-to-2025-12/04-sprint4-2025-11-22-to-12-06/)** - Deployment

### 🚀 For Deployment

### 📚 Guides (Timeless)

**Path:** `guides/`- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment

- **[Authentication System](AUTH_SYSTEM.md)** - User management and security

- [Developer Guide](guides/DEVELOPER_GUIDE.md)- **[Rate Limiting](RATE_LIMITING.md)** - Quotas and rate limits

- [Startup Guide](guides/STARTUP_GUIDE.md)

- [Deployment Guide](guides/DEPLOYMENT_GUIDE.md)### 📊 Architecture & Design

- [Code Quality Guide](guides/CODE_QUALITY_GUIDE.md)

📂 **[architecture/](architecture/)** - Detailed architecture documents

### 📦 Archive (Historical)- Ranking system design

**Path:** `archive/`- Search pipeline architecture

- Event flow validation

- **[Phase 4 (Sep-Oct 2025)](archive/phase4-2025-09-to-10/)** - Production Features ✅ Complete- Interface analysis

- **[Sessions (Aug-Oct 2025)](archive/sessions-2025-08-to-10/)** - Session summaries

- **[Tasks (Sep-Oct 2025)](archive/tasks-2025-09-to-10/)** - Completed tasks### 🧪 Testing



---📂 **[testing/](testing/)** - Testing documentation

- **[Automated Testing Guide](testing/AUTOMATED_TESTING_GUIDE.md)**

## 📊 Project Timeline- Test templates and examples

- Coverage reports

```

Aug 2025        Sep 2025        Oct 2025        Nov 2025        Dec 2025### 📦 Archive

   |               |               |               |               |

Phase 0         Phase 1-3       Phase 4         Phase 5 (Active)📂 **[archive/](archive/)** - Historical documentation

Cleanup        Foundation     Production      Frontend Excellence- **[Phase Plans (2025-10)](archive/phase-plans-2025-10/)** - Archived phase plans

   ✅              ✅              ✅              🚧 In Progress- **[Analysis Reports (2025-10)](archive/analysis-reports-2025-10/)** - Archived analyses

```- Old session notes and debugging docs



------



## 🎯 Current Status (October 8, 2025)## ✨ What's Working (Production-Ready)



### ✅ Completed### ✅ GEO Dataset Search

- **Phase 0-4:** Complete (100%)- Keyword-based search with intelligent query parsing

- **19,000+ lines** of code- 7-dimensional quality scoring (96% test coverage)

- **5 AI Agents** operational- Advanced filters (organism, sample count, study type)

- **GPT-4 integration** working- 220+ tests passing

- **Complete authentication**

- **Beautiful dashboard**### ✅ AI-Powered Analysis

- GPT-4 dataset insights with markdown rendering

### 🚧 Active Work- Automatic quality assessment

- **Phase 5 Sprint 1:** GEO Features Enhancement- Export capabilities (JSON, CSV)

- **Focus:** Advanced filtering, dataset comparison- Cost: ~$0.03 per analysis

- **Timeline:** Oct 8-22, 2025

### ✅ Semantic Search (95% Complete)

---**Code Status:** All infrastructure built and integrated

- Query expansion with biomedical synonyms

## 📖 Key Documents- Hybrid search (TF-IDF 40% + semantic 60%)

- Cross-encoder reranking for precision

### Architecture- RAG pipeline for natural language Q&A

1. [System Architecture](current-2025-10/architecture/SYSTEM_ARCHITECTURE.md)

2. [Complete Overview](current-2025-10/architecture/COMPLETE_ARCHITECTURE_OVERVIEW.md)**Integration:** ✅ SearchAgent, ✅ API, ✅ UI toggle

3. [Backend-Frontend Contract](current-2025-10/architecture/BACKEND_FRONTEND_CONTRACT.md)**Missing:** Dataset embeddings (10-min task with OpenAI API key)

4. [Data Flow Map](current-2025-10/architecture/DATA_FLOW_INTEGRATION_MAP.md)

### ✅ Authentication & Authorization

### API- JWT-based authentication

1. [API Reference](current-2025-10/api/API_REFERENCE.md)- Tiered access control (Free, Pro, Enterprise)

2. [API V2 Reference](current-2025-10/api/API_V2_REFERENCE.md)- API key management

3. [Endpoint Mapping](current-2025-10/api/API_ENDPOINT_MAPPING.md)- User registration and login



### Features### ✅ Rate Limiting & Quotas

1. [Authentication System](current-2025-10/features/AUTH_SYSTEM.md)- Redis-powered rate limiting

2. [Agent Framework](current-2025-10/features/AGENT_FRAMEWORK_GUIDE.md)- Per-user quotas with tiers

3. [AI Analysis](current-2025-10/features/AI_ANALYSIS_EXPLAINED.md)- Usage tracking and analytics

- Sliding window algorithm

### Guides

1. [Developer Guide](guides/DEVELOPER_GUIDE.md)---

2. [Startup Guide](guides/STARTUP_GUIDE.md)

3. [Deployment Guide](guides/DEPLOYMENT_GUIDE.md)## 🏗️ Architecture Overview



### Phase 4 (Complete)```

1. [Phase 4 Summary](archive/phase4-2025-09-to-10/00-overview/PHASE4_COMPLETE.md)omics_oracle_v2/

2. [Daily Progress](archive/phase4-2025-09-to-10/01-daily-progress/)├── agents/           # Agent framework (Search, Data, Query, Report)

├── api/              # FastAPI REST API

---│   ├── routes/       # API endpoints

│   ├── static/       # Web UI (semantic_search.html)

## 🔍 Finding Documents│   └── models/       # Request/response schemas

├── lib/              # Core libraries (7,643 LOC)

### By Topic│   ├── ai/           # LLM integration (GPT-4)

- **Architecture?** → `current-2025-10/architecture/`│   ├── embeddings/   # Text embedding service

- **API Docs?** → `current-2025-10/api/`│   ├── geo/          # GEO database client

- **Features?** → `current-2025-10/features/`│   ├── nlp/          # NLP utilities (NER, query expansion)

- **Phase 5?** → `phase5-2025-10-to-2025-12/`│   ├── ranking/      # Result ranking & scoring

- **Phase 4?** → `archive/phase4-2025-09-to-10/`│   ├── rag/          # RAG pipeline

│   ├── search/       # Hybrid search engine

### By Date│   └── vector_db/    # FAISS vector database

- **Current (Oct 2025)** → `current-2025-10/`├── auth/             # Authentication & authorization

- **Sprint 1 (Oct 8-22)** → `phase5-2025-10-to-2025-12/01-sprint1-2025-10-08-to-10-22/`├── cache/            # Caching layer (Redis)

- **Phase 4 Day 8 (Oct 7)** → `archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/`└── database/         # SQLite database

```

---

**Details:** [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

## 📚 Documentation Standards

---

### Folder Naming

- **Current:** `current-YYYY-MM/`## 📊 Code Quality

- **Phases:** `phaseN-YYYY-MM-to-YYYY-MM/`

- **Sprints:** `NN-sprintN-YYYY-MM-DD-to-MM-DD/`- **122 Python files** - Well-organized modular architecture

- **Daily:** `dayN-YYYY-MM-DD/`- **7,643 lines** in library modules

- **220+ tests** - Comprehensive test coverage (85%+)

### When to Update- **Zero TODO/FIXME** markers in source code

- **current/** - Monthly or major changes- **Pre-commit hooks** - Automated quality checks

- **phase5/** - Active sprint work

- **archive/** - When phase/sprint completes---



---## 📖 How to Use This Documentation



## 🎉 Recent Updates### New Users (5 minutes)

1. [CURRENT_STATE.md](CURRENT_STATE.md) - What works right now

**October 8, 2025:**2. [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Get the server running

- ✅ Completed Phase 4 (100%)3. [WEB_INTERFACE_DEMO_GUIDE.md](WEB_INTERFACE_DEMO_GUIDE.md) - Try the UI

- ✅ Reorganized docs with date-based structure

- ✅ Created Phase 5 sprint folders### Developers (30 minutes)

- ✅ Archived all Phase 4 documentation1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development setup

- ✅ Ready for Phase 5!2. [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - System design

3. [CODE_QUALITY_GUIDE.md](CODE_QUALITY_GUIDE.md) - Standards

**Backup Location:** `../docs-backup-20251008-172729/`4. [testing/AUTOMATED_TESTING_GUIDE.md](testing/AUTOMATED_TESTING_GUIDE.md) - Testing



---### API Integration (15 minutes)

1. [API_REFERENCE.md](API_REFERENCE.md) - Complete API docs

## 📞 Contact & Support2. [RATE_LIMITING.md](RATE_LIMITING.md) - Quotas and limits

3. [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - Authentication

### Questions?

1. Check `current-2025-10/` for current system### Deployment (1 hour)

2. Review `guides/` for how-tos1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment

3. See `archive/` for historical context2. [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - User management

3. [RATE_LIMITING.md](RATE_LIMITING.md) - Rate limit configuration

### Contributing?

1. Read [Developer Guide](guides/DEVELOPER_GUIDE.md)---

2. Follow [Code Quality Guide](guides/CODE_QUALITY_GUIDE.md)

3. Update docs when making changes## 🎯 Current Focus (October 2025)



---### ✅ Completed This Week

- Comprehensive code audit (verified 95% Phase 1 completion)

**Documentation Status:** ✅ Organized, Dated, Ready!- Documentation cleanup (22 files archived)

- Sample dataset creation (10 biomedical datasets)

**Structure Version:** 2.0 (Date-based)  - Strategic assessment and planning

**Total Active Documents:** ~100

**Total Archived:** 400+### ⏭️ This Week

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
