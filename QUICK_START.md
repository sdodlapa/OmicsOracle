# 🚀 OmicsOracle Quick Start Guide

**Last Updated:** October 7, 2025 (Week 4 - Frontend Consolidation)

---

## TL;DR - Get Started in 30 Seconds

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start everything
./start_omics_oracle.sh

# 3. Open in browser
# Dashboard: http://localhost:8502
# API Docs:  http://localhost:8000/docs
```

**That's it!** 🎉

---

## What Just Started?

### 1. **FastAPI API Server** (Port 8000)
- RESTful API endpoints
- Authentication & rate limiting
- Database connections
- Background task processing

### 2. **Streamlit Dashboard** (Port 8502)
- **Primary user interface** ← Use this!
- Search publications (PubMed + Google Scholar)
- 7 visualization types
- Search history & preferences
- Analytics & insights

---

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **📊 Dashboard** | http://localhost:8502 | **Main interface - Use this!** |
| **🔌 API** | http://localhost:8000 | Backend API (for developers) |
| **📖 API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **❤️ Health** | http://localhost:8000/health | System health check |
| **🐛 Debug** | http://localhost:8000/debug/dashboard | Debug panel (developer tool) |

---

## Common Commands

### Start/Stop

```bash
# Start everything (recommended)
./start_omics_oracle.sh

# Stop everything
# Press CTRL+C in the terminal

# Or manually kill processes
pkill -f "omics_oracle_v2.api.main"
pkill -f "run_dashboard.py"
```

### Individual Services

```bash
# Start only API server (port 8000)
./start_dev_server.sh

# Start only Dashboard (port 8502)
python scripts/run_dashboard.py --port 8502
```

### Logs

```bash
# View API logs
tail -f /tmp/omics_api.log

# View Dashboard logs
tail -f /tmp/omics_dashboard.log

# Check for errors
grep -i error /tmp/omics_api.log
grep -i error /tmp/omics_dashboard.log
```

---

## Environment Setup

### Required Environment Variables

Create `.env` file with:

```bash
# NCBI API (Required for PubMed)
NCBI_EMAIL=your.email@example.com
NCBI_API_KEY=your_ncbi_api_key

# OpenAI API (Required for AI features)
OPENAI_API_KEY=sk-...your-key...

# Database (Optional - defaults to SQLite)
OMICS_DB_URL=sqlite+aiosqlite:///./omics_oracle.db

# Rate Limiting (Optional - defaults to in-memory)
OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=true
```

### Get API Keys

- **NCBI API Key**: https://www.ncbi.nlm.nih.gov/account/settings/
- **OpenAI API Key**: https://platform.openai.com/api-keys

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -Pi :8000 -sTCP:LISTEN  # API port
lsof -Pi :8502 -sTCP:LISTEN  # Dashboard port

# Kill the process
kill -9 <PID>
```

### Dashboard Not Loading

```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Restart dashboard
pkill -f streamlit
python scripts/run_dashboard.py --port 8502
```

### API Errors

```bash
# Check API logs
tail -f /tmp/omics_api.log

# Test API health
curl http://localhost:8000/health

# Test API docs
open http://localhost:8000/docs
```

### Database Issues

```bash
# Check if database exists
ls -lh omics_oracle.db

# Reset database (WARNING: deletes all data)
rm omics_oracle.db
# Restart server to recreate
```

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│                                         │
│         User Browser                    │
│                                         │
└────────────┬────────────────────────────┘
             │
             ├──────────────┐
             │              │
             ▼              ▼
    ┌────────────────┐  ┌──────────────┐
    │   Dashboard    │  │  API Server  │
    │  (Streamlit)   │  │  (FastAPI)   │
    │   Port 8502    │  │  Port 8000   │
    └────────────────┘  └───────┬──────┘
             │                  │
             │                  ▼
             │          ┌───────────────┐
             │          │   Database    │
             │          │   (SQLite)    │
             │          └───────────────┘
             │
             ▼
    ┌─────────────────────────────┐
    │  External APIs              │
    │  - PubMed (NCBI)           │
    │  - Google Scholar          │
    │  - OpenAI GPT-4            │
    └─────────────────────────────┘
```

---

## What's New in Week 4?

✅ **Frontend Consolidation:**
- Removed deprecated interfaces (3+ old frontends)
- Streamlit Dashboard is now the **primary interface**
- Unified startup script (`start_omics_oracle.sh`)
- Clear documentation

✅ **Dashboard Enhancements:**
- 7 visualization types (network, trends, heatmap, Sankey, word cloud, etc.)
- Search history with persistence
- User preferences system
- Enhanced analytics panel

✅ **API Improvements:**
- Pydantic warning fixed
- Better error handling
- Improved startup logs

---

## Next Steps

### For Users:
1. **Start the system:** `./start_omics_oracle.sh`
2. **Open Dashboard:** http://localhost:8502
3. **Search publications** about your research topic
4. **Explore visualizations** and analytics

### For Developers:
1. **API Docs:** http://localhost:8000/docs
2. **Debug Panel:** http://localhost:8000/debug/dashboard
3. **Run Tests:** `pytest tests/`
4. **Check Coverage:** `pytest --cov=omics_oracle_v2`

---

## Support

- **Documentation:** `/docs/` directory
- **Architecture:** `docs/SYSTEM_ARCHITECTURE.md`
- **API Reference:** `docs/API_REFERENCE.md`
- **Issues:** Create GitHub issue

---

**Happy Researching! 🧬**
